# Image channel

import MMExc
import MMAttrdefs

import gl
import DEVICE
import fl

import imgfile

from Channel import Channel
from ChannelWindow import ChannelWindow

def between(v, x0, x1):
	return ((x0 <= v and v <= x1) or (x1 <= v and v <= x0))

class ImageWindow(ChannelWindow):
	#
	# Initialization function.
	#
	def init(self, (title, attrdict, player)):
		self = ChannelWindow.init(self, title, attrdict)
		self.clear()
		self.setanchor = 0
		self.player = player
		return self
	#
	def show(self):
		if self.wid <> 0:
			self.setwin()
			return
		ChannelWindow.show(self)
		fl.qdevice(DEVICE.MOUSE3)
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
		if self.attrdict.has_key('hicolor'):
			self.hicolor = self.attrdict['hicolor']
		else:
			self.hicolor = 255, 0, 0
	#
	def mouse(self, (dev, val)):
		mx, my = fl.get_mouse()
		width, height = gl.getsize()
		x = int(width - self.xsize*self.scale) / 2
		y = int(height - self.ysize*self.scale) / 2
		mx, my = int(mx-x), int(my-y)
		if self.setanchor:
			# We're not playing, we're defining anchors
			if dev <> DEVICE.MOUSE3:
				gl.ringbell()
				return
			if val == 1:
				self.pm = (mx, my)
			else:
				self.anchors[0] = (self.anchors[0][0], \
					  [self.pm[0], self.pm[1], mx, my])
				self.redraw()
			return
		if (dev, val) <> (DEVICE.MOUSE3, 1):
			return
		if not self.node:
			print 'mouse: no current node'
			gl.ringbell()
			return
		if not self.anchors:
			print 'mouse: no anchors on this node'
		al2 = []
		for a in self.anchors:
			x0, y0, x1, y1 = a[1][0], a[1][1], a[1][2], a[1][3]
			if between(mx, x0, x1) and between(my, y0, y1):
				al2.append(a)
		if not al2:
			print 'Mouse: No anchor selected'
			gl.ringbell()
			return
		self.player.anchorfired(self.node, al2)
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
			self.pop()
			gl.winset(self.wid)
			self.render()
	def setanchors(self, anchors):
		self.anchors = anchors
		# NB: this routine must be called before showimage
	#
	# Start defining an anchor
	def setdefanchor(self, anchor):
		self.anchors = [anchor]
		self.setanchor = 1
		self.redraw()
	# Stop defining an anchor
	def getdefanchor(self):
		self.setanchor = 0
		return self.anchors[0]
	# Abort defining an anchor
	def enddefanchor(self, anchor):
		self.anchors = [anchor]
		self.setanchor = 0
		self.redraw()
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
			gl.RGBcolor(self.hicolor)
			for dummy, a in self.anchors:
				if len(a) <> 4: continue
				x0, y0, x1, y1 = a[0], a[1], a[2], a[3]
				x0 = int(x0 * self.scale + x)
				x1 = int(x1 * self.scale + x)
				y0 = int(y0 * self.scale + y)
				y1 = int(y1 * self.scale + y)
				gl.bgnclosedline()
				gl.v2i(x0, y0)
				gl.v2i(x0, y1)
				gl.v2i(x1, y1)
				gl.v2i(x1, y0)
				gl.endclosedline()

	#


# XXX Make the image channel class a derived class from ImageWindow?!

class ImageChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos', 'visible']
	node_attrs = ['file', 'duration', 'bgcolor', 'scale', 'arm_duration']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, name, attrdict, player)
		self.window = ImageWindow().init(name, attrdict, player)
		self.armed_node = 0
		return self
	#
	def show(self):
		if self.may_show():
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
		self.showanchors(node)
		self.window.showimage()
		Channel.play(self, node, callback, arg)
	def defanchor(self, node, anchor):
		self.arm(node)
		self.window.setdefanchor(anchor)
		self.window.showimage()

		import AdefDialog
		if AdefDialog.run('Select reactive area with mouse'):
			return self.window.getdefanchor()
		else:
			self.window.enddefanchor(anchor)
			return None
		
	def showanchors(self, node):
		try:
			alist = node.GetRawAttr('anchorlist')
		except MMExc.NoSuchAttrError:
			self.window.setanchors([])
			return
		al2 = []
		for a in alist:
			if len(a[1]) == 0: continue
			if len(a[1]) <> 4:
				print 'ImageChannel: funny-sized anchor'
			else:
				al2.append(a)
		self.window.setanchors(al2)
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
