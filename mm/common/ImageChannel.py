# Image channel

import gl
from GL import *
from DEVICE import *

import glwindow

from MMExc import *
import MMAttrdefs

import image

from Channel import Channel # the base class

class ImageWindow() = (glwindow.glwindow)():
	#
	def init(self, (name, attrdict)):
		self.name = name
		self.attrdict = attrdict
		self.process = None # Initially, no process
		self.filename = None # Nor a filename
		self.wid = 0 # Nor a window
		return self
	#
	def show(self):
		# Get the window size
		if self.attrdict.has_key('winsize'):
			width, height = self.attrdict['winsize']
		else:
			width, height = 0, 0
		# Get the preferred position (in pixels, "hv" coordinates)
		if self.attrdict.has_key('winpos'):
			h, v = self.attrdict['winpos']
		else:
			h, v = -1, -1
		glwindow.setgeometry(h, v, width, height)
		# Actually create the window
		self.wid = gl.winopen(self.name)
		# Remember its origin and size
		self.geometry = gl.getorigin(), gl.getsize()
		# Immediately register it with the main loop
		self.register(self.wid)
		# Let the user resize it
		gl.winconstraints()
		# Use RGB mode; in colormap mode FORMS sometimes
		# messes up our colormap ?!?
		gl.RGBmode()
		gl.gconfig()
		# Draw (clear) it immediately (looks better)
		self.render()
		# If there is a file, show it
		if self.filename <> None:
			self.showimage()
	#
	def hide(self):
		if self.wid <> 0:
			self.unregister()
			gl.winclose(self.wid)
			self.wid = 0
		if self.process <> None:
			self.process.kill()
			self.process = None
	#
	def destroy(self):
		self.hide()
	#
	def clear(self):
		self.filename = None
		self.hideimage()
	#
	def redraw(self):
		if self.wid = 0: return
		gl.winset(self.wid)
		gl.reshapeviewport()
		self.render()
		newgeometry = gl.getorigin(), gl.getsize()
		if newgeometry <> self.geometry:
			self.geometry = newgeometry
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
		(xorg, yorg), (xsize, ysize) = self.geometry
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

class ImageChannel() = Channel():
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
