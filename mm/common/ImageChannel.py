# Image channel

import MMExc
import MMAttrdefs

import gl

import image

from Channel import Channel
from ChannelWindow import ChannelWindow

class ImageWindow() = ChannelWindow():
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
		self.render()
	#
	def redraw(self):
		if self.wid = 0: return
		gl.reshapeviewport()
		self.render()
	#
	def clear(self):
		self.node = None
		self.parray = None
		self.xsize = self.ysize = 0
		self.setcolors()
		if self.wid <> 0:
			gl.winset(self.wid)
			gl.RGBcolor(self.bgcolor)
			gl.clear()
	#
	def setcolors(self):
		if self.attrdict.has_key('bgcolor'):
			self.bgcolor = self.attrdict['bgcolor']
		else:
			self.bgcolor = 255, 255, 255
	#
	def setimage(self, (filename, node)):
		self.parray = None
		try:
			self.xsize, self.ysize = image.imgsize(filename)
		except:
			print 'Cannot get size of image file', `filename`
			return
		self.node = node
		self.scale = MMAttrdefs.getattr(node, 'scale')
		self.bgcolor = MMAttrdefs.getattr(node, 'bgcolor')
		tempfile = image.cachefile(filename)
		f = open(tempfile, 'r')
		f.seek(8192)
		self.parray = f.read()
		if self.wid:
			gl.winset(self.wid)
			self.render()
	#
	def render(self):
		gl.RGBcolor(self.bgcolor)
		gl.clear()
		if self.parray:
			width, height = gl.getsize()
			x = int(width - self.xsize*self.scale) / 2
			y = int(height - self.ysize*self.scale) / 2
			gl.rectzoom(self.scale, self.scale)
			gl.lrectwrite(x, y, x+self.xsize-1, y+self.ysize-1, \
					self.parray)
	#


# XXX Make the image channel class a derived class from ImageWindow?!

class ImageChannel() = Channel():
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos']
	node_attrs = ['file', 'duration', 'bgcolor', 'scale']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, (name, attrdict, player))
		self.window = ImageWindow().init(name, attrdict)
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
	def getduration(self, node):
		wait = MMAttrdefs.getattr(node, 'wait_for_close')
		if wait:
			# An approximation of infinity for the
			# time analysis algorithm
			return 1000000.0
		else:
			return Channel.getduration(self, node)
	#
	def play(self, (node, callback, arg)):
		self.showimage(node)
		wait = MMAttrdefs.getattr(node, 'wait_for_close')
		if wait:
			self.player.freeze() # Should have another interface
			now = self.player.timefunc()
			self.qid = self.player.enter(now + 0.001, 0, \
						self.done, (callback, arg))
		else:
			Channel.play(self, (node, callback, arg))
	#
	def reset(self):
		self.window.clear()
	#
	def showimage(self, node):
		self.window.setimage(self.getfilename(node), node)
	#
	def getfilename(self, node):
		# XXX Doesn't use self...
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			return MMAttrdefs.getattr(node, 'file')
	#
