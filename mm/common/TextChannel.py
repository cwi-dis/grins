# Text channel

import string
import regex

from MMExc import *
import MMAttrdefs

import gl
import fl
import DEVICE
import fm

import FontStuff

from Channel import Channel
from ChannelWindow import ChannelWindow

from AnchorDefs import *


# The text channel's *window* -- this is distinct from the *channel*
# (for better or for worse)

class TextWindow(ChannelWindow):
	#
	def init(self, name, attrdict, channel):
		self = ChannelWindow.init(self, name, attrdict, channel)
		self.parlist = [] # Initially, display no text
		self.taglist = []
		self.fontname = None
		self.pointsize = None
		self.node = None
		self.vobj = None
		self.curwidth = 0
		self.curlines = []
		self.partoline = []
		self.linetopar = []
		self.arm_node = None
		self.arm_parlist = None
		self.arm_taglist = None
		self.arm_curwidth = 0
		self.arm_curlines = []
		self.arm_partoline = []
		self.arm_linetopar = []
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
	def mouse(self, dev, val):
		#
		if (dev, val) == (DEVICE.RIGHTMOUSE, 1):
			ChannelWindow.mouse(self, dev, val)
			return
		#
		if (dev, val) <> (DEVICE.LEFTMOUSE, 0):
			return
		#
		# Now we know it's "left mouse button up"
		#
		if self.node == None:
			print 'TextChannel.mouse: no node'
			return
		#
		if not self.taglist:
			print 'TextChannel.mouse: node has no anchors'
			return
		#
		# Get the mouse position and transform its coordinates
		# (XXX Unfortunately this is not the position of the
		# click but where the mouse is currently)
		#
		mx, my = fl.get_mouse()
		mx, my = gl.mapw2(self.vobj, int(mx), int(my))
		mx, my = int(mx), int(my)
		#
		hits = self.which_tags(mx, my)
		#
		if not hits:
			print 'TextChannel.mouse: none of the anchors was hit'
			gl.ringbell()
			return
		#
		if len(hits) > 1:
			print 'TextChannel.mouse: more than one anchor was hit'
			gl.ringbell()
			return
		#
		self.draw_tag(hits[0], 1)  # Highlight the anchor
		name = hits[0][4]
		#
		al2 = []
		for a in self.anchors:
			if a[A_ID] == name:
				al2.append(a)
		rv = self.channel.player.anchorfired(self.node, al2)
		#
		# If this was a paused anchor and it didn't fire,
		# we're done playing the node
		#
		if rv == 0 and len(al2) == 1 and al2[0][A_TYPE] == ATYPE_PAUSE:
			self.channel.haspauseanchor = 0
			self.channel.pauseanchor_done(0)
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
	# set new text and node (don't redraw)
	def settext(self, text, node):
		self.node = node
		self.anchors = []
		self.parlist = extract_paragraphs(text)
		self.taglist = extract_taglist(self.parlist)
		fix_anchorlist(node, self.taglist)
		self.curlines = []
		self.curwidth = 0
		self.resetfont()
		if text <> '':
			self.pop()
	#
	# pass the list of relevant anchors from the channel
	def noteanchors(self, anchors):
		self.anchors = anchors
		validnames = []
		for aid, atype, args in anchors:
			if type(aid) == type(''): validnames.append(aid)
		for item in self.taglist[:]:
			if item[4] not in validnames:
				self.taglist.remove(item)
	#
	# work ahead for settext_arm
	# (XXX too much duplicated code from redraw)
	def arm(self, text, node):
		self.arm_parlist = extract_paragraphs(text)
		self.arm_taglist = extract_taglist(self.arm_parlist)
		fix_anchorlist(node, self.arm_taglist)
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
		self.arm_curlines, self.arm_partoline, self.arm_linetopar = \
			FontStuff.calclines( \
			  self.arm_parlist, font.getstrwidth, width)
	#
	# like settext but use pre-arm results
	def settext_arm(self, node):
		self.node = self.arm_node
		self.anchors = []
		self.parlist = self.arm_parlist
		self.taglist = self.arm_taglist
		self.curwidth = self.arm_curwidth
		self.curlines = self.arm_curlines
		self.partoline = self.arm_partoline
		self.linetopar = self.arm_linetopar
		self.arm_node = None
		self.arm_parlist = None
		self.arm_curwidth = 0
		self.arm_curlines = []
		self.resetfont()
		self.pop()
	#
	def clear(self):
		self.settext('', None)
		self.redraw()
	#
	def redraw(self):
		if not self.is_showing(): return
		#
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
			self.curlines, self.partoline, self.linetopar = \
				FontStuff.calclines( \
				  self.parlist, self.font.getstrwidth, width)
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
		#
		# Draw the tags (almost the same as the anchors but not quite)
		taglist = self.taglist
		for item in taglist:
			self.draw_tag(item, 0)
	#
	# Find which anchor items are hit by a given point (mx, my)
	def which_tags(self, mx, my):
		result = []
		taglist = self.taglist
		for item in taglist:
			if self.check_tag(mx, my, item):
				result.append(item)
		return result
	#
	# Check whether (mx, my) points into the given anchor item
	def check_tag(self, mx, my, item):
		boxes = self.tag_to_boxes(item)
		for (x0, y0, x1, y1) in boxes:
			if x0 <= mx <= x1 and y0 <= my <= y1:
				return 1
		return 0
	#
	# Draw the given anchor item
	def draw_tag(self, item, filled):
		boxes = self.tag_to_boxes(item)
		if filled:
			gl.linewidth(3)
		for (x0, y0, x1, y1) in boxes:
			gl.bgnclosedline()
			gl.v2i(x0, y0+1)
			gl.v2i(x1, y0+1)
			gl.v2i(x1, y1)
			gl.v2i(x0, y1)
			gl.endclosedline()
		if filled:
			gl.linewidth(1)
	#
	# Convert an anchor to a set of boxes
	def tag_to_boxes(self, item):
		f = self.font.getstrwidth
		par0, char0, par1, char1, name = item
		line0, char0 = self.map_parpos_to_linepos(par0, char0, 0)
		line1, char1 = self.map_parpos_to_linepos(par1, char1, 1)
		x0 = self.margin + f(self.curlines[line0][:char0])
		y0 = self.fontheight * line0
		boxes = []
		while line0 < line1:
			x1 = self.margin + f(self.curlines[line0])
			y1 = y0 + self.fontheight
			boxes.append((x0, y0, x1, y1))
			x0 = self.margin
			y0 = y1
			line0 = line0 + 1
		x1 = self.margin + f(self.curlines[line1][:char1])
		y1 = self.fontheight * (line1 + 1)
		boxes.append((x0, y0, x1, y1))
		return boxes
	#
	# Map a char position in a paragraph to one in a line.
	# Return a pair (lineno, charno)
	def map_parpos_to_linepos(self, parno, charno, last):
		# This works only if parno and charno are valid
		sublist = self.partoline[parno]
		for lineno, char0, char1 in sublist:
			if charno <= char1:
				i = max(0, charno-char0)
				if last:
					return lineno, i
				curline = self.curlines[lineno]
				n = len(curline)
				while i < n and curline[i] == ' ': i = i+1
				if i < n:
					return lineno, charno-char0
				charno = char1


# Turn a text string into a list of strings, each representing a paragraph.
# Tabs are expanded to spaces (since the font mgr doesn't handle tabs),
# but this only works well at the start of a line or in a monospaced font.
# Blank lines and lines starting with whitespace separate paragraphs.

def extract_paragraphs(text):
	lines = string.splitfields(text, '\n')
	parlist = []
	par = []
	for line in lines:
		if '\t' in line: line = string.expandtabs(line, 8)
		i = len(line) - 1
		while i >= 0 and line[i] == ' ': i = i-1
		line = line[:i+1]
		if not line or line[0] in ' \t':
			parlist.append(string.join(par))
			par = []
		if line:
			par.append(line)
	if par: parlist.append(string.join(par))
	return parlist


# Extract anchor tags from a list of paragraphs.
#
# An anchor starts with "<A NAME=...>" and ends with "</A>".
# These tags are case independent; whitespace is significant.
# Anchors may span paragraphs but an anchor tag must be contained in
# one paragraph.  Other occurrences of < are left in the text.
#
# The list of paragraps is modified in place (the tags are removed).
# The return value is a list giving the start and end position
# of each anchor and its name.  Start and end positions are given as
# paragraph_number, character_offset.

def extract_taglist(parlist):
	# (1) Extract the raw tags, removing them from the text
	pat = regex.compile('<[Aa] +[Nn][Aa][Mm][Ee]=\([a-zA-Z_]+\)>\|</[Aa]>')
	rawtaglist = []
	for i in range(len(parlist)):
		par = parlist[i]
		j = 0
		while pat.search(par, j) >= 0:
			regs = pat.regs
			a, b = regs[0]
			tag = par[a:b]
			par = par[:a] + par[b:]
			j = a
			if tag[:2] != '</':
				a, b = regs[1]
				name = tag[a-j:b-j]
			else:
				name = None
			rawtaglist.append((i, j, name))
		parlist[i] = par
	# (2) Parse the raw taglist, picking up the valid patterns
	# (a begin tag immediately followed by an end tag)
	taglist = []
	last = None
	for item in rawtaglist:
		if item[2] is not None:
			last = item
		elif last:
			taglist.append(last[:2] + item[:2] + last[2:3])
			last = None
	return taglist


# XXX THIS IS A HACK
# When we have extracted the anchors from a node's paragraph list,
# add them to the node's anchor list.
# This should be done differently, and doesn't even use the edit mgr,
# but as a compatibility hack it's probably OK...

def fix_anchorlist(node, taglist):
	if not taglist:
		return
	names_in_anchors = []
	names_in_taglist = []
	for item in taglist:
		names_in_anchors.append(item[4])
	oldanchors = MMAttrdefs.getattr(node, 'anchorlist')
	anchors = oldanchors[:]
	for i in range(len(anchors)):
		aid, atype, args = a = anchors[i]
		if type(aid) <> type(''):
			continue
		if aid not in names_in_anchors:
			print 'Remove text anchor from anchorlist:', a
			anchors.remove(a)
		else:
			names_in_taglist.append(aid)
	for item in taglist:
		name = item[4]
		if name not in names_in_taglist:
			print 'Add text anchor to anchorlist:', name
			anchors.append(name, ATYPE_NORMAL, [])
	if anchors <> oldanchors:
		print 'New anchors:', anchors
		node.SetAttr('anchorlist', anchors)
		MMAttrdefs.flushcache(node)


# The text *channel*.
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
	# Initialize the instance
	#
	def init(self, name, attrdict, player):
		self = Channel.init(self, name, attrdict, player)
		self.window = TextWindow().init(name, attrdict, self)
		self.arm_node = None
		return self
	#
	# Return a string representation for `self`
	#
	def __repr__(self):
		return '<TextChannel instance, name=' + `self.name` + '>'
	#
	# Standard calls from player
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
	#
	def clear(self):
		self.window.clear()
	#
	def did_prearm(self):
		return (self.arm_node <> None)
	#
	# Play a node (called from Player)
	#
	def play(self, node, callback, arg):
		self.node = node
		self.showtext(node)
		self.noteanchors(node)
		self.window.redraw()
		Channel.play(self, node, callback, arg)
	#
	# Define an anchor (called from AnchorEdit)
	#
	def defanchor(self, node, anchor):
		self.node = node
		self.arm_node = None
		self.showtext(node)
		##self.noteanchors(node)
		self.window.redraw()
		aid, atype, args = anchor
		if atype not in (ATYPE_NORMAL, ATYPE_PAUSE):
			return anchor
		if type(aid) == type(''):
			for item in self.window.taglist:
				if item[4] == aid:
					return anchor
			msg1 = 'Sorry, I can\'t find '+`aid`+' in the text.'
		else:
			msg1 = 'Sorry, you can\'t promote a ' + \
				'synthetic anchor to a labeled one.'
		fl.show_message(msg1, \
			'Please add labels to the text first, like this:', \
			'... <A NAME=mylabel> anchor text </A> ...')
		return None
	#
	# Internal: pass some anchors to the window
	#
	def noteanchors(self, node):
		self.autoanchor = None
		self.haspauseanchor = 0
		try:
			alist = node.GetRawAttr('anchorlist')
		except NoSuchAttrError:
			alist = []
		al2 = []
		for a in alist:
			if a[A_TYPE] == ATYPE_AUTO:
				self.autoanchor = a
			if a[A_TYPE] == ATYPE_PAUSE:
				self.haspauseanchor = 1
			if a[A_TYPE] in (ATYPE_NORMAL, ATYPE_PAUSE) and \
				type(a[A_ID]) == type(''):
				al2.append(a)
		self.window.noteanchors(al2)
	#
	# Reset the channel to a clear status
	#
	def reset(self):
		self.arm_node = None
		self.window.clear()
	#
	# Arm (called from Channel)
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
			self.arm_node = None
			if self.is_showing():
				print 'TextChannel '+self.name+\
					  ': node not armed'
			self.window.settext(self.getstring(node), node)
	#
	def getstring(self, node):
		if node.type == 'imm':
			return string.joinfields(node.GetValues(), '\n')
		elif node.type == 'ext':
			filename = self.player.toplevel.getattr(node, 'file')
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


# Get some numbers about a font that are needed for our calculations

def getfontparams(font):
	avgcharwidth = font.getstrwidth('m')
	(printermatched, fixed_width, xorig, yorig, xsize, ysize, \
			fontheight, nglyphs) = font.getfontinfo()
	baseline = fontheight - yorig
	return avgcharwidth, baseline, fontheight


# Map a possibly symbolic font name to a real font name and default point size

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
