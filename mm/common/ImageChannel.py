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
		self.process = None # Initially, no process
		self.filename = None # Nor a filename
		return ChannelWindow.init(self, (title, attrdict))
	#
	def show(self):
		if self.wid <> 0: return
		ChannelWindow.show(self)
		# Draw (clear) it immediately (looks better)
		self.render()
		# If there is a file, show it
		if self.filename <> None:
			self.showimage()
	#
	def hide(self):
		if self.wid <> 0:
			ChannelWindow.hide(self)
		if self.process <> None:
			self.process.kill()
			self.process = None
	#
	def clear(self):
		self.filename = None
		self.hideimage()
	#
	def redraw(self):
		if self.wid = 0: return
		old_geometry = self.last_geometry
		gl.reshapeviewport()
		self.render()
		self.get_geometry()
		if self.last_geometry <> old_geometry:
			self.moveimage()
	#
	def render(self):
		gl.RGBcolor(127, 127, 255) # Light blue?
		gl.clear()
	#
	def setimage(self, filename):
		self.clear()
		self.filename = filename
		if self.filename <> None and self.wid <> 0:
			self.showimage()
	#
	def moveimage(self):
		if self.filename <> None:
			self.hideimage()
			if self.wid <> 0:
				self.showimage()
	#
	def showimage(self):
		gl.winset(self.wid)
		(xorg, yorg), (xsize, ysize) = gl.getorigin(), gl.getsize()
		width, height = image.imgsize(self.filename)
		x = xorg + (xsize-width)/2
		y = yorg + (ysize-height)/2
		self.process = image.showimg(self.filename, (x, y))
	#
	def hideimage(self):
		if self.process <> None:
			self.process.kill()
			self.process = None
			# The redraw will come automatically...
	#


# XXX Make the image channel class a derived class from ImageWindow?!

class ImageChannel() = Channel():
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos']
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
	def done(self, (callback, arg)):
		self.reset()
		Channel.done(self, (callback, arg))
	#
	def showimage(self, node):
		self.window.setimage(self.getfilename(node))
	#
	def getfilename(self, node):
		# XXX Doesn't use self...
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			return MMAttrdefs.getattr(node, 'file')
	#
