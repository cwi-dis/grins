# Image channel

import MMExc
import MMAttrdefs

import gl
import GL
import DEVICE
import fl

from Channel import Channel
from ChannelWindow import ChannelWindow

from ArmStates import *
from AnchorDefs import *

import FileCache
import pipes


def between(v, x0, x1):
	return ((x0 <= v and v <= x1) or (x1 <= v and v <= x0))

class ImageNodeInfo():
	def init(self):
		self.node = None
		self.parray = None
		self.error = None
		self.xsize = self.ysize = 0
		self.xcorner = self.ycorner = 0
		self.effscale = 1.0
		self.mousescale = 1.0
		return self

	def setcolors(self):
		if not self.node:
			raise 'setcolors without node'
		self.bgcolor = MMAttrdefs.getattr(self.node, 'bgcolor')
		self.hicolor = MMAttrdefs.getattr(self.node, 'hicolor')
		self.fgcolor = self.hicolor
		
	def setdefcolors(self, attrdict):
		if attrdict.has_key('bgcolor'):
			self.bgcolor = attrdict['bgcolor']
		else:
			self.bgcolor = 255, 255, 255

		if attrdict.has_key('hicolor'):
			self.hicolor = attrdict['hicolor']
		else:
			self.hicolor = 255, 0, 0

		self.fgcolor = self.hicolor
		
class ImageWindow(ChannelWindow):
	#
	# Initialization function.
	#
	def init(self, name, attrdict, channel):
		self = ChannelWindow.init(self, name, attrdict, channel)
		self.nonode_ninfo = ImageNodeInfo().init()
		self.nonode_ninfo.setdefcolors(attrdict)
		self.clear()
		self.player = channel.player
		return self
	#
	def __repr__(self):
		return '<ImageWindow instance, name=' + `self.name` + '>'
	#
	def show(self):
		if self.is_showing():
			self.pop()
			return
		ChannelWindow.show(self)
		fl.qdevice(DEVICE.LEFTMOUSE)
		self.render()
	#
	def redraw(self):
		if not self.is_showing():
			return
		gl.reshapeviewport()
		winwidth, winheight = gl.getsize()
		self.ninfo.xcorner = \
		     int(winwidth - self.ninfo.xsize*self.ninfo.effscale) / 2
		self.ninfo.ycorner = \
		     int(winheight - self.ninfo.ysize*self.ninfo.effscale) / 2
		gl.ortho2(-0.5, winwidth-0.5, -0.5, winheight-0.5)
		self.render()
	#
	def clear(self):
		self.anchors = []
		self.newanchor = None
		self.ninfo = self.nonode_ninfo
		if self.is_showing():
			self.setwin()
			gl.RGBcolor(self.ninfo.bgcolor)
			gl.clear()
	#
	def getmouse(self):
		mx, my = fl.get_mouse()
		return self.convmouse(mx, my)

	def convmouse(self, mx, my):
		mx = int((mx - self.ninfo.xcorner) / self.ninfo.mousescale)
		my = int((my - self.ninfo.ycorner) / self.ninfo.mousescale)
		return mx, my
	#
	def mouse(self, dev, val):
		if dev == DEVICE.RIGHTMOUSE or self.newanchor:
			self.node = self.ninfo.node # ChannelWindow needs it
			ChannelWindow.mouse(self, dev, val)
			return
		if (dev, val) <> (DEVICE.LEFTMOUSE, 1):
			return
		if not self.ninfo.node:
			gl.ringbell()
			return
		if (dev, val) <> (DEVICE.LEFTMOUSE, 1):
			return
		if not self.anchors:
			print 'mouse: no anchors on this node'

		mx, my = self.getmouse()
		al2 = []
		for a in self.anchors:
			args = a[A_ARGS]
			if not args:
				al2.append(a)
				continue
			x0, y0, x1, y1 = args[0], args[1], args[2], args[3]
			if between(mx, x0, x1) and between(my, y0, y1):
				al2.append(a)
		if not al2:
			print 'Mouse: No anchor selected'
			gl.ringbell()
			return
		rv = self.player.anchorfired(self.ninfo.node, al2)
		# If this was a paused anchor and it didn't fire
		# stop showing the node
		if rv == 0 and len(al2) == 1 and al2[0][A_TYPE] == ATYPE_PAUSE:
			self.channel.haspauseanchor = 0
			self.channel.done(0)
	#
	def armimage(self, filename_arg, node):
		self.arm_ninfo = ImageNodeInfo().init()
		# (Import imgfile here so if it doesn't exist we can
		# still play documents that don't contain images...)
		import imgfile
		filename = rgbcache.get(filename_arg)
		self.arm_ninfo.node = node
		self.arm_ninfo.setcolors()
		self.arm_ninfo.parray = None
		self.arm_ninfo.effscale = 1.0 # Scale for lrectwrite
		self.arm_ninfo.mousescale = 1.0 # Scale for mouse and anchors
		self.arm_ninfo.xcorner = 0
		self.arm_ninfo.ycorner = 0
		self.arm_ninfo.error = None
		try:
			self.arm_ninfo.xsize, self.arm_ninfo.ysize, dummy = \
				imgfile.getsizes(filename)
		except imgfile.error, msg:
			print 'Cannot get size of image file', filename_arg, \
				  ':', msg
			self.arm_ninfo.error = 'Bad or missing file ' + `filename_arg`
			return
		if self.is_showing():
			self.setwin()
			winwidth, winheight = gl.getsize()
		else:
			winwidth, winheight = 0, 0
		self.arm_ninfo.effscale = MMAttrdefs.getattr(node, 'scale')
		scalefilter = MMAttrdefs.getattr(node, 'scalefilter')
		if self.arm_ninfo.effscale <= 0.0:
			if not self.is_showing():
				self.arm_ninfo.effscale = 1.0
			else:
				self.arm_ninfo.effscale = \
					min(float(winwidth)/self.arm_ninfo.xsize, \
					    float(winheight)/self.arm_ninfo.ysize)
		self.arm_ninfo.mousescale = self.arm_ninfo.effscale
		try:
			if self.arm_ninfo.effscale == \
				  int(self.arm_ninfo.effscale):
				self.arm_ninfo.parray = imgfile.read(filename)
			else:
				width = int(self.arm_ninfo.xsize * \
					  self.arm_ninfo.effscale)
				height = int(self.arm_ninfo.ysize * \
					  self.arm_ninfo.effscale)
				if not scalefilter:
					self.arm_ninfo.parray = \
						  imgfile.readscaled(filename,\
						  width, height)
				else:
					self.arm_ninfo.parray = \
						  imgfile.readscaled(filename,\
						  width, height, scalefilter)
				self.arm_ninfo.effscale = 1.0
				self.arm_ninfo.xsize, self.arm_ninfo.ysize = \
					  width, height
		except imgfile.error, msg:
			print 'Cannot read image file', filename_arg, ':', msg
			self.arm_ninfo.error = 'Cannot read file ' + \
				  `filename_arg`
		self.arm_ninfo.xcorner = int(winwidth - \
			  self.arm_ninfo.xsize*self.arm_ninfo.effscale) / 2
		self.arm_ninfo.ycorner = int(winheight - \
			  self.arm_ninfo.ysize*self.arm_ninfo.effscale) / 2
	#
	def showimage(self, node):
		if node != self.arm_ninfo.node:
			raise 'Not the armed node'
		self.ninfo = self.arm_ninfo
		self.arm_ninfo = None
		if self.is_showing():
			self.pop() # Implies gl.winset()
			self.render()
	#
	def setanchors(self, anchors):
		self.anchors = anchors
		# NB: this routine must be called before showimage
	#
	# Start defining an anchor
	def setdefanchor(self, anchor):
		if anchor in self.anchors:
			self.saveanchor = anchor
			self.anchors.remove(anchor)
		else:
			self.saveanchor = None
		self.newanchor = anchor
		self.redraw()
		self.sqqstart(anchor[2])
	#
	# Stop defining an anchor
	def getdefanchor(self):
		x0, y0, x1, y1 = self.sqqend()
		x0, y0 = self.convmouse(x0, y0)
		x1, y1 = self.convmouse(x1, y1)
		res = (self.newanchor[0], self.newanchor[1], [x0,y0,x1,y1])
		self.anchors.append(res)
		self.saveanchor = None
		self.newanchor = None
		self.redraw()
		return res
	#
	# Abort defining an anchor
	def enddefanchor(self, anchor):
		dummy = self.sqqend()
		if self.saveanchor <> None:
			self.anchors.append(self.saveanchor)
			self.saveanchor = None
		self.newanchor = None
		self.redraw()
	#
	def render(self):
		gl.RGBcolor(self.ninfo.bgcolor)
		gl.clear()
		width, height = gl.getsize()
		if self.ninfo.parray:
			gl.rectzoom(self.ninfo.effscale, self.ninfo.effscale)
			gl.lrectwrite(self.ninfo.xcorner, self.ninfo.ycorner, \
				self.ninfo.xcorner+self.ninfo.xsize-1, \
				self.ninfo.ycorner+self.ninfo.ysize-1, \
				self.ninfo.parray)
		else:
			if self.ninfo.error:
				gl.RGBcolor(self.ninfo.fgcolor)
				width, height = gl.getsize()
				x, y = width/2, height/2
				sw = gl.strwidth(self.ninfo.error)
				sh = gl.getheight()
				x = max(0, x - sw/2)
				y = y + sh/2
				gl.cmov2(x, y)
				gl.charstr(self.ninfo.error)
		# Draw anchors even if the image can't be drawn
		if self.anchors:
			gl.RGBcolor(self.ninfo.hicolor)
			for dummy, tp, a in self.anchors:
				self.drawanchor(a)
		# And redraw current defining anchor, if needed
		if self.newanchor:
			self.sqqredraw()

	#
	# Subroutine to draw an anchor
	#
	def drawanchor(self, a):
		if len(a) <> 4:
			return
		x0, y0, x1, y1 = a[0], a[1], a[2], a[3]
		x0 = int(x0 * self.ninfo.mousescale + self.ninfo.xcorner)
		x1 = int(x1 * self.ninfo.mousescale + self.ninfo.xcorner)
		y0 = int(y0 * self.ninfo.mousescale + self.ninfo.ycorner)
		y1 = int(y1 * self.ninfo.mousescale + self.ninfo.ycorner)
		gl.bgnclosedline()
		gl.v2i(x0, y0)
		gl.v2i(x0, y1)
		gl.v2i(x1, y1)
		gl.v2i(x1, y0)
		gl.endclosedline()


# XXX Make the image channel class a derived class from ImageWindow?!

class ImageChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['base_window', 'base_winoff']
	node_attrs = ['file', 'duration', 'scale', 'scalefilter', \
		 'bgcolor', 'hicolor']
##		 'bgcolor', 'fgcolor', 'hicolor']
	#
	def init(self, name, attrdict, player):
		self = Channel.init(self, name, attrdict, player)
		self.window = ImageWindow().init(name, attrdict, self)
		self.armed_node = None
		return self
	#
	def __repr__(self):
		return '<ImageChannel instance, name=' + `self.name` + '>'
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
	# clear is called by Channel.clearnode() to clear remains of
	# previous node.
	def clear(self):
		self.window.clear()
	#
	def play(self, node, callback, arg):
		self.node = node
		if not self.is_showing():
			apply(callback, arg)
			return
	        if node <> self.armed_node:
		    print 'ImageChannel: node not armed'
		    self.arm(node)
		self.armed_node = None
		self.showanchors(node)
		self.window.showimage(node)
		Channel.play(self, node, callback, arg)
	#
	def defanchor(self, node, anchor):
		self.arm(node)
		self.showanchors(node)
		self.window.setdefanchor(anchor)
		self.window.showimage(node)

		import AdefDialog
		try:
			rv = AdefDialog.anchor('Sweep anchor with mouse')
			a = self.window.getdefanchor()
			if rv == 0:
				a = (a[0], a[1], [])
			return a
		except AdefDialog.cancel:
			self.window.enddefanchor(anchor)
			return None
	#
	def showanchors(self, node):
		self.autoanchor = None
		self.haspauseanchor = 0
		try:
			alist = node.GetRawAttr('anchorlist')
		except MMExc.NoSuchAttrError:
			self.window.setanchors([])
			return
		al2 = []
		for a in alist:
			if a[A_TYPE] == ATYPE_AUTO:
				self.autoanchor = a
			if a[A_TYPE] == ATYPE_PAUSE:
				self.haspauseanchor = 1
			if a[A_TYPE] not in (ATYPE_NORMAL, ATYPE_PAUSE):
				continue
			if len(a[A_ARGS]) not in (0,4):
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
	def setwaiting(self):
		self.window.setwaiting()
	#
	def setready(self):
		self.window.setready()
	#


temps = []

def makergbfile(filename):
	import torgb
	try:
		result = torgb.torgb(filename)
	except torgb.error, msg:
		print torgb.error, msg
		return filename
	if result <> filename:
		temps.append(result)
	return result

def rmcache(original, cached):
	import os
	if cached != original:
		try:
			os.unlink(cached)
		except os.error:
			pass

def cleanup():
	import os
	rgbcache.flushall()
	for tempname in temps:
		try:
			os.unlink(tempname)
		except (os.error, IOError):
			pass
	temps[:] = []

rgbcache = FileCache.FileCache().init(makergbfile, rmcache)
