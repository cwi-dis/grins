# Image channel

import MMExc
import MMAttrdefs

import gl
import DEVICE
import fl

import imgfile

from Channel import Channel
from ChannelWindow import ChannelWindow

from AnchorEdit import A_ID, A_TYPE, A_ARGS, ATYPE_NORMAL, ATYPE_PAUSE, \
	ATYPE_AUTO

import FileCache


def between(v, x0, x1):
	return ((x0 <= v and v <= x1) or (x1 <= v and v <= x0))

class ImageWindow(ChannelWindow):
	#
	# Initialization function.
	#
	def init(self, (name, attrdict, channel)):
		self = ChannelWindow.init(self, name, attrdict, channel)
		self.clear()
		self.setanchor = 0
		self.player = channel.player
		return self
	#
	def show(self):
		if self.is_showing():
			self.pop()
			return
		ChannelWindow.show(self)
		fl.qdevice(DEVICE.MOUSE3)
		self.render()
	#
	def redraw(self):
		if not self.is_showing():
			return
		gl.reshapeviewport()
		self.render()
	#
	def clear(self):
		self.node = None
		self.parray = None
		self.anchors = []
		self.xsize = self.ysize = 0
		self.setcolors()
		if self.is_showing():
			self.setwin()
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
		if dev == DEVICE.RIGHTMOUSE:
			ChannelWindow.mouse(self, (dev, val))
			return
		if not self.node:
			gl.ringbell()
			return
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
				a = self.anchors[0]
				self.anchors[0] = (a[0], a[1], \
					  [self.pm[0], self.pm[1], mx, my])
				self.redraw()
			return
		if (dev, val) <> (DEVICE.MOUSE3, 1):
			return
		if not self.anchors:
			print 'mouse: no anchors on this node'
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
		rv = self.player.anchorfired(self.node, al2)
		# If this was a paused anchor and it didn't fire
		# stop showing the node
		if rv == 0 and len(al2) == 1 and al2[0][A_TYPE] == ATYPE_PAUSE:
			self.channel.haspauseanchor = 0
			self.channel.done(0)
	#
	def armimage(self, (filename, node)):
		filename = rgbcache.get(filename)
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
		if self.is_showing():
			self.pop() # Implies gl.winset()
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
			for dummy, tp, a in self.anchors:
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
	node_attrs = ['file', 'duration', 'bgcolor', 'scale', 'arm_duration', \
		'hicolor']
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, name, attrdict, player)
		self.window = ImageWindow().init(name, attrdict, self)
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
	# clear is called by Channel.clearnode() to clear remains of
	# previous node.
	def clear(self):
		self.window.clear()
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
	#
	def defanchor(self, node, anchor):
		self.arm(node)
		self.window.setdefanchor(anchor)
		self.window.showimage()

		import AdefDialog
		try:
			rv = AdefDialog.run('Select reactive area with mouse')
			a = self.window.getdefanchor()
			if rv == 0:
				a = (a[0], a[1], [])
			return a
		except AdefDialog.cancel:
			self.window.enddefanchor(anchor)
			return None
	#
	def showanchors(self, node):
		try:
			alist = node.GetRawAttr('anchorlist')
		except MMExc.NoSuchAttrError:
			self.window.setanchors([])
			return
		al2 = []
		self.autoanchor = None
		self.haspauseanchor = 0
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
	def getfilename(self, node):
		return MMAttrdefs.getattr(node, 'file')
	#


temps = []

def makergbfile(filename):
	import imghdr
	import os
	uncompressed = None
	if filename[-2:] == '.Z':
		filename = uncompressed = conv('zcat <$1 >$2', filename)
	try:
		type = imghdr.what(filename)
	except IOError:
		type = None
	if type == 'pnm':
		res = conv('fromppm $1 $2', filename)
	elif type == 'gif':
		res = conv('fromgif $1 $2', filename)
	elif type == 'tiff':
		tempname = conv('tifftopnm <$1 >$2', filename)
		res = conv('fromppm $1 $2', tempname)
		os.unlink(tempname)
		temps.remove(tempname)
	elif type == 'rast':
		res = conv('fromsun $1 $2', filename)
	else:
		res = filename
	if None <> uncompressed <> res:
		os.unlink(uncompressed)
		temps.remove(uncompressed)
	return res

def conv(cmd, filename):
	import os
	import tempfile
	tempname = tempfile.mktemp()
	temps.append(tempname)
	cmd = 'set ' + filename + ' ' + tempname + '; ' + cmd
	print 'Executing:', cmd
	sts = os.system(cmd)
	if sts:
		print cmd
		print  'Exit status:', sts
	return tempname

def cleanup():
	import os
	rgbcache.flushall()
	for tempname in temps:
		try:
			os.unlink(tempname)
		except (os.error, IOError):
			pass
	temps[:] = []

rgbcache = FileCache.FileCache().init(makergbfile)
