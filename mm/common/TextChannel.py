# Text channel

import string
import strop # String operations in C

from MMExc import *
import MMAttrdefs

import gl
import fl
import DEVICE
import fm

from Channel import Channel
from ChannelWindow import ChannelWindow

from ArmStates import *

from AnchorEdit import \
	A_ID, A_TYPE, A_ARGS, ATYPE_NORMAL, ATYPE_PAUSE, ATYPE_AUTO

# Find last occurence of space in string such that the size (according to some
# size calculating function) of the initial substring is smaller than a given
# number.  If there is no such substrings the first space in the string is
# returned (if any) otherwise the length of the string.
# Assume sizefunc() is additive: sizefunc(s + t) == sizefunc(s) + sizefunc(t)

def fitstring(s, sizefunc, limit):
	words = strop.splitfields(s, ' ')
	spw = sizefunc(' ')
	okcount = -1
	totsize = 0
	totcount = 0
	for w in words:
		if w:
			addsize = sizefunc(w)
			if totsize > 0 and totsize + addsize > limit:
				break
			totsize = totsize + addsize
			totcount = totcount + len(w)
			okcount = totcount
		# The space after the word
		totsize = totsize + spw
		totcount = totcount + 1
	if okcount < 0:
		return totcount
	else:
		return okcount

def between(v, x0, x1):
	return ((x0 <= v and v <= x1) or (x1 <= v and v <= x0))

class TextWindow(ChannelWindow):
	#
	def init(self, (name, attrdict, channel)):
		self = ChannelWindow.init(self, name, attrdict, channel)
		self.text = [] # Initially, display no text
		self.fontname = None
		self.pointsize = None
		self.node = None
		self.vobj = None
		self.setanchor = 0
		self.anchors = []
		self.curwidth = 0
		self.curlines = []
		self.arm_node = None
		self.arm_text = None
		self.arm_curwidth = 0
		self.arm_curlines = []
		self.setcolors()
		return self
	#
	def __repr__(self):
		return '<TextWindow instance, name=' + `self.name` + '>'
	#
	def setcolors(self):
		if self.attrdict.has_key('bgcolor'):
			self.bgcolor = self.attrdict['bgcolor']
		else:
			self.bgcolor = 255, 255, 255
		if self.attrdict.has_key('fgcolor'):
			self.fgcolor = self.attrdict['fgcolor']
		else:
			self.fgcolor = 0, 0, 0
		if self.attrdict.has_key('hicolor'):
			self.hicolor = self.attrdict['hicolor']
		else:
			self.hicolor = 255, 0, 0
	#
	def show(self):
		if self.is_showing():
			self.pop()
			return
		self.resetfont()
		ChannelWindow.show(self)
		fl.qdevice(DEVICE.LEFTMOUSE)
		# Clear it immediately (looks better)
		gl.RGBcolor(self.bgcolor)
		gl.clear()
	#
	def mouse(self, (dev, val)):
		if dev == DEVICE.RIGHTMOUSE:
			ChannelWindow.mouse(self, (dev, val))
			return
		if self.node == None:
			gl.ringbell()
			return
		mx, my = fl.get_mouse()
		mx, my = gl.mapw2(self.vobj, int(mx), int(my))
		mx, my = int(mx), int(my)
		if self.setanchor:
			# We're not playing, we're defining anchors
			if dev <> DEVICE.LEFTMOUSE:
				gl.ringbell()
				return
			if val == 1:
				self.pm = (mx, my)
			else:
				try:
					# Check if self.pm is set -- somehow
					# it is possible that the mouse-down
					# was never seen (e.g. down outside
					# the window and up inside it)
					pm = self.pm
				except AttributeError:
					gl.ringbell()
					return
				a = self.anchors[0]
				self.anchors[0] = (a[0], a[1], \
					  [pm[0], pm[1], mx, my])
				self.redraw()
			return
		if (dev, val) <> (DEVICE.LEFTMOUSE, 0):
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
		rv = self.channel.player.anchorfired(self.node, al2)
		# If this was a paused anchor and it didn't fire
		# stop showing the node
		if rv == 0 and len(al2) == 1 and al2[0][A_TYPE] == ATYPE_PAUSE:
			self.channel.haspauseanchor = 0
			self.channel.done(0)
	#
	def resetfont(self):
		# Get the default colors
		if self.node == None:
			self.setcolors()
		else:
			self.bgcolor = MMAttrdefs.getattr(self.node, 'bgcolor')
			self.fgcolor = MMAttrdefs.getattr(self.node, 'fgcolor')
			self.hicolor = MMAttrdefs.getattr(self.node, 'hicolor')
		# Get the default font and point size for the window
		if self.node <> None:
			fontspec = MMAttrdefs.getattr(self.node, 'font')
		elif self.attrdict.has_key('font'):
			fontspec = self.attrdict['font']
		else:
			fontspec = 'default'
		fontname, pointsize = mapfont(fontspec)
		# Get the explicit point size, if any
		if self.node <> None:
			ps = MMAttrdefs.getattr(self.node, 'pointsize')
		elif self.attrdict.has_key('pointsize'):
			ps = self.attrdict['pointsize']
		else:
			ps = 0
		if ps <> 0: pointsize = ps
		if fontname == self.fontname and pointsize == self.pointsize:
			return
		self.fontname = fontname
		self.pointsize = pointsize
		try:
			self.font = newfont(self.fontname, self.pointsize)
		except RuntimeError: # That's what fm raises...
			print 'Bad fontname', `self.fontname`,
			self.fontname = mapfont('default')[0]
			print '; using default', `self.fontname`
			self.font = newfont(self.fontname, self.pointsize)
		# Find out some parameters of the font
		self.avgcharwidth, self.baseline, self.fontheight = \
			getfontparams(self.font)
		self.margin = int(self.avgcharwidth / 2)
	#
	# settext resets on a new screen
	def settext(self, (text, node)):
		self.node = node
		self.text = preptext(text)
		self.curlines = []
		self.curwidth = 0
		self.resetfont()
		if text <> '':
			self.pop()
		self.redraw()
	#
	# arm works ahead for settext
	def arm(self, text, node):
		self.arm_text = preptext(text)
		self.arm_node = node
		if not self.is_showing():
			self.arm_curwidth = 0
			self.arm_curlines = []
			return
		self.setwin()
		gl.reshapeviewport()
		x0, x1, y0, y1 = gl.getviewport()
		width, height = x1-x0, y1-y0
		fontspec = MMAttrdefs.getattr(node, 'font')
		fontname, pointsize = mapfont(fontspec)
		ps = MMAttrdefs.getattr(node, 'pointsize')
		if ps <> 0: pointsize = ps
		if fontname == self.fontname and pointsize == self.pointsize:
			font = self.font
		else:
			try:
				font = newfont(fontname, pointsize)
			except RuntimeError: # That's what fm raises...
				fontname = mapfont('default')[0]
				font = newfont(fontname, pointsize)
		# Find out some parameters of the font
		avgcharwidth, baseline, fontheight =getfontparams(font)
		margin = int(avgcharwidth / 2)
		self.arm_curwidth = width
		width = width - 2*margin
		self.arm_curlines = calclines(self.arm_text, font, width)
	#
	def settext_arm(self, node):
		self.node = self.arm_node
		self.text = self.arm_text
		self.curwidth = self.arm_curwidth
		self.curlines = self.arm_curlines
		self.arm_node = None
		self.arm_text = None
		self.arm_curwidth = 0
		self.arm_curlines = []
		self.resetfont()
		self.pop()
		self.redraw()
	#
	# Set the anchor list.
	#
	def setanchors(self, anchors):
		self.anchors = anchors

	def clear(self):
		self.anchors = []
		self.settext('', None)
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
	def redraw(self):
		if not self.is_showing(): return

		self.setwin()
		gl.reshapeviewport()
		#
		x0, x1, y0, y1 = gl.getviewport()
		width, height = x1-x0, y1-y0
		MASK = 20
		#
		# Make a graphical object of the transformations
		# so we can use it to map mouse clicks
		if self.vobj == None:
			self.vobj = gl.genobj()
		gl.makeobj(self.vobj)
		gl.viewport(x0-MASK, x1+MASK, y0-MASK, y1+MASK)
		gl.scrmask(x0, x1, y0, y1)
		gl.ortho2(-MASK-0.5, width+MASK-0.5, \
			  height+MASK-0.5, -MASK-0.5)
		gl.closeobj()
		gl.callobj(self.vobj)
		#
		# Update the list of lines if necessary
		if self.curwidth <> width:
			self.curwidth = width
			width = width - 2*self.margin
			self.curlines = calclines(self.text, self.font, width)
		#
		# Clear the window in the background color
		gl.RGBcolor(self.bgcolor)
		gl.clear()
		#
		# Draw the lines
		maxlines = (height + self.fontheight - 1) / self.fontheight
		lastline = min(len(self.curlines), maxlines)
		gl.RGBcolor(self.fgcolor)
		self.font.setfont()
		x, y = self.margin, self.baseline
		for str in self.curlines[:lastline]:
			gl.cmov2(x, y)
			fm.prstr(str)
			y = y + self.fontheight
		#
		# Draw the anchors
		gl.RGBcolor(self.hicolor)
		for dummy, tp, a in self.anchors:
			if len(a) <> 4: continue
			gl.bgnclosedline()
			gl.v2i(a[0], a[1])
			gl.v2i(a[0], a[3])
			gl.v2i(a[2], a[3])
			gl.v2i(a[2], a[1])
			gl.endclosedline()


def calclines(text, font, width):
	curlines = []
	for par in text:
		while 1:
			i = fitstring(par, font.getstrwidth, width)
			curlines.append(par[:i])
			n = len(par)
			while i < n and par[i] == ' ': i = i+1
			par = par[i:]
			if not par: break
	return curlines


# Turn a text string into a list of strings, each representing a paragraph.
# Tabs are expanded to spaces (since the font mgr doesn't handle tabs),
# but this only works well at the start of a line or in a monospaced font.
# Blank lines and lines starting with whitespace separate paragraphs.

def preptext(text):
	lines = strop.splitfields(text, '\n')
	result = []
	par = []
	for line in lines:
		if '\t' in line: line = string.expandtabs(line, 8)
		i = len(line) - 1
		while i >= 0 and line[i] == ' ': i = i-1
		line = line[:i+1]
		if not line or line[0] in ' \t':
			result.append(string.join(par))
			par = []
		if line:
			par.append(line)
	if par: result.append(string.join(par))
	return result


# XXX Make the text channel class a derived class from TextWindow?!

class TextChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['base_window', 'base_winoff']
	node_attrs = \
		['font', 'pointsize', 'file', 'duration', 'fgcolor', \
		 'hicolor', 'bgcolor']
	#
	# Initialization function.
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, name, attrdict, player)
		self.window = TextWindow().init(name, attrdict, self)
		return self
	#
	def __repr__(self):
		return '<TextChannel instance, name=' + `self.name` + '>'
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
	# Called by Channel.clearnode to clear previous node
	def clear(self):
		self.window.clear()
	#
	def play(self, (node, callback, arg)):
		self.node = node
		self.showanchors(node)
		self.showtext(node)
		Channel.play(self, node, callback, arg)
		dummy = \
		    self.player.enter(0.001, 1, self.player.opt_prearm, node)
	#
	def defanchor(self, node, anchor):
		self.showtext(node)
		self.window.setdefanchor(anchor)

		import AdefDialog
		try:
			rv = AdefDialog.anchor( \
				'Select reactive area with mouse')
			a = self.window.getdefanchor()
			if rv == 0:
				a = (a[0], a[1], [])
			return a
		except AdefDialog.cancel:
			self.window.enddefanchor(anchor)
			return None
		
	def showanchors(self, node):
		try:
			alist = node.GetRawAttr('anchorlist')
		except NoSuchAttrError:
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
			if not a[A_TYPE] in (ATYPE_NORMAL, ATYPE_PAUSE):
				continue
			if len(a[A_ARGS]) not in (0,4):
				print 'TextChannel: funny-sized anchor'
			else:
				al2.append(a)
		self.window.setanchors(al2)
	#
	def reset(self):
		self.window.clear()
	#
	def arm(self, node):
		if not self.is_showing(): return
		self.arm_node = node
		self.window.arm(self.getstring(node), node)
	#
	def showtext(self, node):
		if node == self.arm_node:
			self.window.settext_arm(node)
			self.arm_node = None
		else:
			print 'TextChannel: node not armed'
			self.window.settext(self.getstring(node), node)
	#
	def getstring(self, node):
		if node.type == 'imm':
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = MMAttrdefs.getattr(node, 'file')
			try:
				fp = open(filename, 'r')
			except IOError:
				print 'Cannot open text file', `filename`
				return ''
			text = fp.read()
			fp.close()
			if text[-1:] == '\n':
				text = text[:-1]
			return text
		else:
			raise CheckError, \
				'gettext on wrong node type: ' +`node.type`
	#
	def setwaiting(self):
		self.window.setwaiting()
	#
	def setready(self):
		self.window.setready()
	#

def getfontparams(font):
	avgcharwidth = font.getstrwidth('m')
	(printermatched, fixed_width, xorig, yorig, xsize, ysize, \
			fontheight, nglyphs) = font.getfontinfo()
	baseline = fontheight - yorig
	return avgcharwidth, baseline, fontheight

fontmap = { \
	'':		('Times-Roman', 12), \
	'default':	('Times-Roman', 12), \
	'plain':	('Times-Roman', 12), \
	'italic':	('Times-Italic', 12), \
	'bold':		('Times-Bold', 12), \
	'courier':	('Courier', 12), \
	'bigbold':	('Times-Bold', 14), \
	'title':	('Times-Bold', 24), \
	  }

def mapfont(fontname):
#	print 'mapfont', fontname
	if fontmap.has_key(fontname):
		return fontmap[fontname]
	else:
		return fontname, 12


# Cache font objects, since each time you create a new one, the first
# call to f.getfontinfo() takes about half a second...

fontcache = {}

def newfont(name, size):
	key = name + `size`
	if fontcache.has_key(key):
		return fontcache[key]
	key1 = name + '1'
	if fontcache.has_key(key1):
		f1 = fontcache[key1]
	else:
		f1 = fontcache[key1] = fm.findfont(name)
	f = fontcache[key] = f1.scalefont(size)
	return f
