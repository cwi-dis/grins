# Image channel

import MMExc
import MMAttrdefs

import posix
import gl

import imgfile

from Channel import Channel
from ChannelWindow import ChannelWindow

class ImageWindow(ChannelWindow):
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
		if self.wid == 0: return
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
	def armimage(self, (filename, node)):
		self.parray = None
		try:
			self.xsize, self.ysize, dummy = imgfile.getsizes(filename)
		except imgfile.error, msg:
			print 'Cannot get size of image file', filename, \
				  ':', msg
			return
		self.node = node
		self.scale = MMAttrdefs.getattr(node, 'scale')
		self.bgcolor = MMAttrdefs.getattr(node, 'bgcolor')
		try:
			self.parray = imgfile.read(filename)
		except imgfile.error, msg:
			print 'Cannot read image file', filename, ':', msg
	def showimage(self):
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

class ImageChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos', 'visible', 'border']
	node_attrs = ['file', 'duration', 'bgcolor', 'scale', 'arm_duration']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, (name, attrdict, player))
		self.window = ImageWindow().init(name, attrdict)
		self.armed_node = 0
		return self
	#
	def show(self):
		if self.may_show():
			self.window.show()
			if self.no_border():
				gl.noborder()
				gl.winconstraints()
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
		return Channel.getduration(self, node)
	#
	def play(self, (node, callback, arg)):
		if not self.is_showing():
			callback(arg)
			return
	        if node <> self.armed_node:
		    print 'ImageChannel: node not armed'
		    self.arm(node)
		self.armed_node = None
		self.window.showimage()
		Channel.play(self, (node, callback, arg))
	#
	def reset(self):
		self.window.clear()
	#
	def arm(self, node):
		if not self.is_showing():
			return
		self.window.armimage(self.getfilename(node), node)
		self.armed_node = node
	#
	def getfilename(self, node):
		return MMAttrdefs.getattr(node, 'file')
	#
