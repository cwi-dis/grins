# Image channel

from MMExc import *
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
		self.parray = None
		self.xsize = self.ysize = 0
		return ChannelWindow.init(self, (title, attrdict))
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
		self.parray = None
		self.xsize = self.ysize = 0
		gl.winset(self.wid)
		gl.RGBcolor(255, 255, 255)
		gl.clear()
	#
	def setimage(self, (filename, scale)):
		self.parray = None
		self.xsize, self.ysize = image.imgsize(filename)
		self.scale = scale
		tempfile = image.cachefile(filename)
		f = open(tempfile, 'r')
		f.seek(8192)
		self.parray = f.read()
		if self.wid:
			gl.winset(self.wid)
			self.render()
	#
	def render(self):
		gl.RGBcolor(255, 255, 255)
		gl.clear()
		if self.parray:
			width, height = gl.getsize()
			x = (width - self.xsize*self.scale) / 2
			y = (height - self.ysize*self.scale) / 2
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
	chan_attrs = ['winsize', 'winpos', 'scale']
	node_attrs = ['file', 'wait_for_close', 'duration']
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
		scale = MMAttrdefs.getattr(node, 'scale')
		self.window.setimage(self.getfilename(node), scale)
	#
	def getfilename(self, node):
		# XXX Doesn't use self...
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			return MMAttrdefs.getattr(node, 'file')
	#
