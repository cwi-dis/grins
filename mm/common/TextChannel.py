# Text channel

import string

from MMExc import *
import MMAttrdefs

import gl
import fm

from Channel import Channel
from ChannelWindow import ChannelWindow

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
		if s[i:i+1] = ' ':
			if sizefunc(s[0:i]) <= length:
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

MASK = 20

class TextWindow() = ChannelWindow():
	#
	def init(self, (title, attrdict)):
		self.text = [] # Initially, display no text
		return ChannelWindow.init(self, (title, attrdict))
	#
	def show(self):
		if self.wid <> 0: return
		self.resetfont()
		ChannelWindow.show(self)
		# Clear it immediately (looks better)
		gl.RGBcolor(255, 255, 255)
		gl.clear()
	#
	def resetfont(self):
		# Get the default font and point size for the window
		if self.attrdict.has_key('font'):
			fontspec = self.attrdict['font']
		else:
			fontspec = 'default'
		self.fontname, self.pointsize = mapfont(fontspec)
		if self.attrdict.has_key('pointsize'):
			ps = self.attrdict['pointsize']
			if ps <> 0: self.pointsize = ps
		# Create the default font object
		self.font1 = fm.findfont(self.fontname) # At 1 point...
		self.font = self.font1.scalefont(self.pointsize)
		# Find out some parameters of the font
		self.avgcharwidth, self.baseline, self.fontheight = \
			getfontparams(self.font)
	#
	# settext resets on a new screen
	def settext(self, text):
		# comment these two out if you want to see addtext feature
		self.text = [text]
		self.redraw()
		# to show addtext feature
		#self.addtext(text)
	#
	# addtext adds text to a screen with possible scroll
	def addtext(self, text):
		self.text.append(text)
		self.redraw()
	#
	# while addtext adds the additional text on a new line, appendtext
	# continues on the same line
	def appendtext(self, text):
		l = len(self.text) - 1
		if l >= 0:
			self.text[l] = self.text[l] + ' ' + text
		else:
			self.text = [text]
		self.redraw()
	#
	# a hack.  currently redraw recalculates everything.  when window size
	# is not changed it sould only calculate possibly added text.
	def redraw(self):
		if self.wid = 0: return
		gl.winset(self.wid)
		gl.reshapeviewport()
		x0, x1, y0, y1 = gl.getviewport()
		width, height = x1-x0, y1-y0
		gl.viewport(x0-MASK, x1+MASK, y0-MASK, y1+MASK)
		gl.scrmask(x0, x1, y0, y1)
		gl.ortho2(-MASK, width+MASK, height+MASK, -MASK)
		#
		gl.RGBcolor(255, 255, 255)
		gl.clear()
		#
		gl.RGBcolor(0, 0, 0)
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


# XXX Make the text channel class a derived class from TextWindow?!

class TextChannel() = Channel():
	#
	# Declaration of attributes that are relevant to this channel,
	# respectively to nodes belonging to this channel.
	#
	chan_attrs = ['winsize', 'winpos']
	node_attrs = \
		['font', 'pointsize', 'file', 'wait_for_close', 'duration']
	#
	# Initialization function.
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, (name, attrdict, player))
		self.window = TextWindow().init(name, attrdict)
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
		self.showtext(node)
		wait = MMAttrdefs.getattr(node, 'wait_for_close')
		if wait:
			self.player.pause() # Should have another interface
			now = self.player.timefunc()
			self.qid = self.player.enter(now + 0.001, 0, \
						self.done, (callback, arg))
		else:
			Channel.play(self, (node, callback, arg))
	#
	def reset(self):
		self.window.resetfont()
		self.window.settext('')
	#
	def showtext(self, node):
		self.window.settext(self.getstring(node))
	#
	def getstring(self, node):
		# XXX Doesn't use self...
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			file = MMAttrdefs.getattr(node, 'file')
			try:
				fp = open(file, 'r')
			except:
				print 'Cannot open text file', `file`
				return ''
			text = fp.read()
			if text[-1:] = '\n':
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
