# Text channel

import string

import gl, fm
from GL import *
from DEVICE import *

import glwindow

from MMExc import *
import MMAttrdefs

from Channel import Channel # the base class

class TextWindow() = (glwindow.glwindow)():
	#
	def init(self, (name, attrdict)):
		self.name = name
		self.attrdict = attrdict
		self.text = '' # Initially, display no text
		gl.foreground() # Fight silly GL default
		self.resetfont()
		# Get the window size (given in lines and characters!)
		if self.attrdict.has_key('winsize'):
			width, height = attrdict['winsize']
			width = width * self.avgcharwidth
			height = height * self.fontheight
		else:
			width, height = 0, 0
		# Get the preferred position (in pixels, "hv" coordinates)
		if attrdict.has_key('winpos'):
			h, v = attrdict['winpos']
		else:
			h, v = 0, 0
		glwindow.setgeometry(h, v, width, height)
		# Actually create the window
		wid = gl.winopen(name)
		# Immediately register it with the main loop
		self.register(wid)
		# Let the user resize it
		gl.winconstraints()
		# Use RGB mode; in colormap mode FORMS sometimes
		# messes up our colormap ?!?
		gl.RGBmode()
		gl.gconfig()
		# Clear it immediately (looks better)
		gl.RGBcolor(255, 255, 255)
		gl.clear()
		return self
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
	def settext(self, text):
		self.text = text
		self.redraw()
	#
	def redraw(self):
		gl.winset(self.wid)
		gl.reshapeviewport()
		x0, x1, y0, y1 = gl.getviewport()
		width, height = x1-x0, y1-y0
		MASK = 20
		gl.viewport(x0-MASK, x1+MASK, y0-MASK, y1+MASK)
		gl.scrmask(x0, x1, y0, y1)
		gl.ortho2(-MASK, width+MASK, height+MASK, -MASK)
		#
		gl.RGBcolor(255, 255, 255)
		gl.clear()
		#
		gl.RGBcolor(0, 0, 0)
		gl.cmov2(0, self.baseline)
		self.font.setfont()
		fm.prstr(self.text)
	#

class TextChannel() = Channel():
	#
	def init(self, (name, attrdict, player)):
		self = Channel.init(self, (name, attrdict, player))
		self.window = TextWindow().init(name, attrdict)
		return self
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
			self.player.freeze() # Should have another interface
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
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			file = MMAttrdefs.getattr(node, 'file')
			try:
				fp = open(file, 'r')
			except:
				print 'Cannot open file:', `file`
				return
			text = fp.read()
			if text[-1:] = '\n':
				text = text[:-1]
			return text
		elif node.type = 'grp':
			return '<group text not yet implemented>'
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
