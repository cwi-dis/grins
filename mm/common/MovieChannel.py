# Movie channel
# For now, plays only B/W movies recorded by Jack's "cam2" program

import posix
from stat import *

import MMExc
import MMAttrdefs

import gl

from Channel import Channel
from ChannelWindow import ChannelWindow

class MovieWindow() = ChannelWindow():
	#
	# Initialization function.
	#
	def init(self, (title, attrdict)):
		self.fp = None
		return ChannelWindow.init(self, (title, attrdict))
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
		self.fp = None
		gl.winset(self.wid)
		self.erase()
	#
	def erase(self):
		gl.RGBcolor(255, 255, 255)
		gl.clear()
	#
	def setfile(self, (filename, scale)):
		try:
			self.fp = open(filename, 'r')
		except:
			print 'Cannot open movie file', filename
			self.fp = None
			return
		line = self.fp.readline()
		if not line:
			print 'Empty movie file', filename
			self.fp = None
			return
		x = eval(line[:-1])
		if len(x) = 2:
			self.w, self.h = x
			self.pf = 2
		else:
			self.w, self.h, self.pf = x
	#
	def nextframe(self):
		if not self.fp:
			return
		line = self.fp.readline() # XXX Time code; ignore for now
		if not line:
			self.fp = None
			return
		data = self.fp.read(self.w*self.h/4)
		if self.wid <> 0:
			gl.winset(self.wid)
			if self.fp:
				data = gl.unpackrect(self.w, self.h,\
						self.pf, data)
			w, h = gl.getsize()
			x = (w-self.w)/2
			y = (h-self.h)/2
			gl.lrectwrite(x, y, x+self.w-1, y+self.h-1, data)
	#
	def done(self):
		return self.fp = None


# XXX Make the movie channel class a derived class from MovieWindow?!

class MovieChannel() = Channel():
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos', 'scale']
	node_attrs = ['file']
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
		scale = MMAttrdefs.getattr(node, 'scale')
		self.window.setfile(filename, scale)
		self.poll(callback, arg) # Put on the first image right now
	#
	def poll(self, cb_arg):
		self.qid = None
		self.window.nextframe()
		if self.window.done(): # Last frame
			callback, arg = cb_arg
			callback(arg)
			return
		else:
			self.qid = self.player.enter(0.1, 1, self.poll, cb_arg)
	#
	def reset(self):
		self.window.clear()
	#
	def getduration(self, node):
		filename = self.getfilename(node)
		try:
			fp = open(filename, 'r')
		except:
			print 'cannot get duration of movie', filename
			return MMAttrdefs.getattr(node, 'duration')
		line = fp.readline()
		if not line:
			print 'Empty movie file', filename
			self.fp = None
			return MMAttrdefs.getattr(node, 'duration')
		del fp
		x = eval(line[:-1])
		if len(x) = 2:
			w, h = x
			pf = 2
		else:
			w, h, pf = x
		if pf = 0:
			bytesperpixel = 4.0
		else:
			bytesperpixel = 1.0/pf/pf
		st = posix.stat(filename)
		size = st[ST_SIZE]
		nframes = size / (w*h*bytesperpixel)
		return nframes / 6.0 # Estimate for frames/sec
	#
	def getfilename(self, node):
		# XXX Doesn't use self...
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			return MMAttrdefs.getattr(node, 'file')
	#
