# Movie channel

# For now, this play only movies recorded by Jack's "camcorder" program.
# The format is the following:
#	first line: "CMIF video 1.0"
#	second line: "(width, height, packfactor)"
#	each image:
#		one line: "(time, datasize)"
#		datasize bytes of binary data
# For compatibility with some old movies the header line, pack factor and
# data size are optional.  Default pack factor is 2; default data size is
# (width/2) * (height/2) if pack factor is nonzero, or width*height*4
# if it is zero (indicating a color movie).
# An EOF indicates the end of the file; 

import sys
sys.path.append('/ufs/guido/src/video')	# For VFile

import posix
from stat import *

import MMExc
import MMAttrdefs

import gl
import GL

import VFile

from Channel import Channel
from ChannelWindow import ChannelWindow

class MovieWindow() = ChannelWindow():
	#
	# Initialization function.
	#
	def init(self, (title, attrdict)):
		self = ChannelWindow.init(self, (title, attrdict))
		self.clear()
		return self
	#
	def show(self):
		if self.wid <> 0: return
		ChannelWindow.show(self)
		self.clear()
	#
	def redraw(self):
		if self.wid = 0: return
		gl.reshapeviewport()
		self.erase()
	#
	def clear(self):
		self.node = self.vfile = self.lookahead = None
		if self.wid <> 0:
			gl.winset(self.wid)
			gl.RGBmode()
			gl.gconfig()
			self.rgbmode = 1
			self.erase()
	#
	def erase(self):
		if self.node <> None:
			r, g, b = MMAttrdefs.getattr(self.node, 'bgcolor')
		elif self.attrdict.has_key('bgcolor'):
			r, g, b = self.attrdict['bgcolor']
		else:
			r, g, b = 255, 255, 255
		#
		if self.rgbmode:
			gl.RGBcolor(r, g, b)
		else:
			INDEX = 255
			gl.mapcolor(INDEX, r, g, b)
			gl.color(INDEX)
		#
		gl.clear()
		#
		if self.vfile <> None:
			self.centerimage()
	#
	def setfile(self, (filename, node)):
		self.clear()
		try:
			self.vfile = VFile.VinFile().init(filename)
		except EOFError:
			print 'Empty movie file', `filename`
			return
		except (VFile.Errror, posix.error, RuntimeError), msg:
			print 'Cannot open movie file', `filename`, ':', msg
			return
		except IOError, msg:
			print 'Cannot open movie file', `filename`, ':', msg
			return
		self.node = node
		self.vfile.magnify = MMAttrdefs.getattr(self.node, 'scale')
		dummy = self.peekaboo()
		if dummy <> None and self.wid <> None:
			gl.winset(self.wid)
			self.vfile.initcolormap()
			self.rgbmode = (self.vfile.format = 'rgb')
			self.erase()
	#
	def centerimage(self):
		w, h = self.vfile.width, self.vfile.height
		w, h = int(w*self.vfile.magnify), int(h*self.vfile.magnify)
		W, H = gl.getsize()
		self.vfile.xorigin, self.vfile.yorigin = (W-w)/2, (H-h)/2
	#
	def peekaboo(self):
		try:
			self.lookahead = self.vfile.getnextframeheader()
			return self.lookahead[0] * 0.001
		except (EOFError, VFile.Error):
			self.lookahead = None
			return 0.0
	#
	def done(self):
		return self.lookahead = None
	#
	def nextframe(self):
		if self.lookahead = None:
			return 0.0
		time, size, chromsize = self.lookahead
		if self.wid = 0:
			try:
				self.vfile.skipnextframedata(size, chromsize)
			except (VFile.Error, EOFError):
				return 0.0
		else:
			gl.winset(self.wid)
			try:
				data, chromdata = \
				  self.vfile.getnextframedata(size, chromsize)
				self.vfile.showframe(data, chromdata)
			except (VFile.Error, EOFError):
				return 0.0
		return self.peekaboo()


# XXX Make the movie channel class a derived class from MovieWindow?!

class MovieChannel() = Channel():
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos']
	node_attrs = ['file', 'scale', 'bgcolor']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, (name, attrdict, player))
		self.window = MovieWindow().init(name, attrdict)
		return self
	#
	def show(self):
		self.window.show()
	#
	def hide(self):
		self.window.hide()
	#
	def is_showing(self):
		return self.window.is_showing()
	#
	def destroy(self):
		self.window.destroy()
	#
	def save_geometry(self):
		self.window.save_geometry()
	#
	def play(self, (node, callback, arg)):
		filename = self.getfilename(node)
		self.window.setfile(filename, node)
		self.starttime = self.player.timefunc()
		self.poll(callback, arg) # Put on the first image right now
	#
	def poll(self, cb_arg):
		self.qid = None
		if self.window.done(): # Last frame
			callback, arg = cb_arg
			callback(arg)
			return
		else:
			t = self.window.nextframe()
			self.qid = self.player.enterabs(self.starttime + t, \
				1, self.poll, cb_arg)
	#
	def reset(self):
		self.window.clear()
	#
	def getduration(self, node):
		# To estimate the duration: read the header and the first
		# image; use stat to get the total file size; use this
		# to estimate the number of images; multiply this with
		# the time listed for the first image...
		filename = self.getfilename(node)
		totalsize = getfilesize(filename)
		try:
			vfile = VFile.VinFile().init(filename)
		except:
			print 'Cannot open movie file',
			print `filename`, 'to get duration'
			return 0.0
		pos1 = vfile.fp.tell()
		try:
			time = vfile.skipnextframe()
		except EOFError:
			return 0.0
		pos2 = vfile.fp.tell()
		imagesize = pos2 - pos1
		imagecount = (totalsize - pos1) / imagesize
		return 0.001 * time * imagecount
	#
	def getfilename(self, node):
		# XXX Doesn't use self...
		if node.type = 'ext':
			return MMAttrdefs.getattr(node, 'file')
		else:
			return None
	#


def getfilesize(filename):
	from stat import ST_SIZE
	try:
		st = posix.stat(filename)
		return st[ST_SIZE]
	except:
		return -1
