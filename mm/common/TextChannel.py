# Text channel
# XXX This channel doesn't do anything on arm() yet. Maybe it should.

import string

from MMExc import *
import MMAttrdefs

import gl
import fl
import DEVICE
import fm

from Channel import Channel
from ChannelWindow import ChannelWindow

from AnchorEdit import A_ID, A_TYPE, A_ARGS, ATYPE_NORMAL, ATYPE_PAUSE, \
	  ATYPE_AUTO

# find last occurence of space in string such that the size (according to some
# size calculating function) of the initial substring is smaller than a given
# number.  If there is no such substrings the first space in the string is
# returned (if any) otherwise the length of the string
nofit_error = 'no fitting substring'

def fitstring(s, sizefunc, length):
	l = len(s)
	if sizefunc(s) <= length:
		return l
	p = -1
	# would prefer a built-in index function to find the first occurrence
	# of a space character
	for i in range(l):
		if s[i] == ' ':
			if sizefunc(s[:i]) <= length:
				p = i
			else:
				l = i
				break
	if p >= 0:
		return p
	return l

# In this case the string *must* fit.
def mustfitstring(s, sizefunc, length):
	l = fitstring(s, sizefunc, length)
	if sizefunc(s[:l]) <= length:
		return l
	raise nofit_error, (s, length)

def between(v, x0, x1):
	return ((x0 <= v and v <= x1) or (x1 <= v and v <= x0))

class TextWindow(ChannelWindow):
	#
	def init(self, (name, attrdict, channel)):
		self = ChannelWindow.init(self, name, attrdict, channel)
		self.text = [] # Initially, display no text
		self.node = None
		self.vobj = None
		self.setanchor = 0
		self.anchors = []
		self.setcolors()
		return self
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
				a = self.anchors[0]
				self.anchors[0] = (a[0], a[1], \
					  [self.pm[0], self.pm[1], mx, my])
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
		self.fontname, self.pointsize = mapfont(fontspec)
		# Get the explicit point size, if any
		if self.node <> None:
			ps = MMAttrdefs.getattr(self.node, 'pointsize')
		elif self.attrdict.has_key('pointsize'):
			ps = self.attrdict['pointsize']
		else:
			ps = 0
		if ps <> 0: self.pointsize = ps
		try:
			self.font1 = fm.findfont(self.fontname) # At 1 point...
		except RuntimeError: # That's what fm raises...
			print 'Bad fontname', `self.fontname`,
			print '; using default', `mapfont('default')[0]`
			self.font1 = fm.findfont(mapfont('default')[0])
		self.font = self.font1.scalefont(self.pointsize)
		# Find out some parameters of the font
		self.avgcharwidth, self.baseline, self.fontheight = \
			getfontparams(self.font)
	#
	# settext resets on a new screen
	def settext(self, (text, node)):
		# comment these two out if you want to see addtext feature
		self.text = preptext(text)
		self.node = node
		self.resetfont()
		if text <> '':
			self.pop()
		self.redraw()
		# to show addtext feature
		#self.addtext(text)
	#
	# addtext adds text to a screen with possible scroll
	def addtext(self, text):
		self.text = self.text + preptext(text)
		self.redraw()
	#
	# while addtext adds the additional text on a new line, appendtext
	# continues on the same line
	def appendtext(self, text):
		lines = preptext(text)
		l = len(self.text) - 1 # Index of last item
		if l >= 0:
			self.text[l] = self.text[l] + ' ' + lines[0]
			self.text = self.text + lines[1:]
		else:
			self.text = lines
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
	# a hack.  currently redraw recalculates everything.  when window size
	# is not changed it should only calculate possibly added text.
	def redraw(self):
		if self.wid == 0: return
		gl.winset(self.wid)
		gl.reshapeviewport()
		x0, x1, y0, y1 = gl.getviewport()
		width, height = x1-x0, y1-y0
		MASK = 20
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
		gl.RGBcolor(self.bgcolor)
		gl.clear()
		#
		gl.RGBcolor(self.fgcolor)
		self.font.setfont()
		#
		curbase = self.baseline
		margin = int(self.avgcharwidth / 2)
		fmaxlines = height / self.fontheight
		maxlines = int(fmaxlines)
		if maxlines > fmaxlines:
			maxlines = maxlines - 1
		width = width - margin * 2
		textlist = []
		for toset in self.text:
			while toset <> '':
				ind = fitstring(toset, self.font.getstrwidth, \
					width)
				textlist.append(toset[:ind])
				toset = toset[ind+1:]
		lastline = len(textlist)
		if lastline < maxlines:
			firstline = 0
		else:
			firstline = lastline - maxlines
		for str in textlist[firstline:lastline]:
			gl.cmov2(margin,curbase)
			fm.prstr(str)
			curbase = curbase + self.fontheight
		# Draw the anchors.
		gl.RGBcolor(self.hicolor)
		for dummy, tp, a in self.anchors:
			if len(a) <> 4: continue
			gl.bgnclosedline()
			gl.v2i(a[0], a[1])
			gl.v2i(a[0], a[3])
			gl.v2i(a[2], a[3])
			gl.v2i(a[2], a[1])
			gl.endclosedline()


# Turn a text string into a list of strings, each representing a paragraph.
# Blank lines separate paragraphs; other newlines are replaced by spaces.

def preptext(text):
	lines = string.splitfields(text, '\n')
	result = []
	current = ''
	for line in lines:
		if line == '':
			if current == '': current = ' '
			result.append(current)
			current = ''
		if current: current = current + ' '
		current = current + line
	if current == '': current = ' '
	result.append(current)
	return result


# XXX Make the text channel class a derived class from TextWindow?!

class TextChannel(Channel):
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos', 'visible']
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
		self.showanchors(node)
		self.showtext(node)
		Channel.play(self, node, callback, arg)
	#
	def defanchor(self, node, anchor):
		self.showtext(node)
		self.window.setdefanchor(anchor)

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
	def showtext(self, node):
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
