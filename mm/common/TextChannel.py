# Text channel

from Channel import Channel # the base class

import string
import gl, fm
from GL import *
from DEVICE import *
from glwindow import glwindow

class TextWindow() = glwindow():
	#
	def init(self, (name, attrdict)):
		self.text = '' # Initially, display no text
		gl.foreground() # Fight silly GL default
		# Get the default font and point size for the window
		if attrdict.has_key('font'):
			self.fontname, self.pointsize = \
				mapfont(attrdict['font'])
		else:
			self.fontname , self.pointsize = 'Times-Roman', 12
		if attrdict.has_key('pointsize'):
			self.pointsize = attrdict['pointsize']
		# Create the default font object
		self.font1 = fm.findfont(self.fontname) # At 1 point...
		self.font = self.font1.scalefont(self.pointsize)
		# Find out some parameters of the font
		self.avgcharwidth, self.baseline, self.fontheight = \
			getfontparams(self.font)
#		print 'avg char width:', self.avgcharwidth,
#		print 'baseline:', self.baseline,
#		print 'fontheight:', self.fontheight
		# Get the window size (given in lines and characters!)
		if attrdict.has_key('winsize'):
			width, height = attrdict['winsize']
			width = width * self.avgcharwidth
			height = height * self.fontheight
#			print 'winsize', (width, height)
		else:
			width, height = 0, 0
		# Get the preferred position (in pixels, "hv" coordinates)
		if attrdict.has_key('winpos'):
			# Make sure we have nonzero width and height
			if width <= 0: width = 400
			if height <= 0: height = 300
			h, v = attrdict['winpos']
#			print 'winpos', (h, v)
			scrwidth = gl.getgdesc(GD_XPMAX)
			scrheight = gl.getgdesc(GD_YPMAX)
			x, y = h, scrheight-v-height
#			print 'prefposition', (x, x+width-1, y, y+height-1)
			gl.prefposition(x, x+width-1, y, y+height-1)
		elif width <> 0 or height <> 0:
			# Make sure we have nonzero width and height
			if width <= 0: width = 400
			if height <= 0: height = 300
#			print 'prefsize', (width, height)
			gl.prefsize(width, height)
		# Actually create the window
		wid = gl.winopen(name)
		self.register(wid)
		# Clear it immediately (looks better)
		gl.color(WHITE)
		gl.clear()
		gl.winconstraints() # Let the user resize it
		return self
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
		gl.color(WHITE)
		gl.clear()
		#
		gl.color(BLACK)
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
		wait = node.GetInherAttrDef('wait_for_close', 0)
		if wait:
			# An approximation of infinity for the
			# time analysis algorithm
			return 1000000.0
		else:
			return Channel.getduration(self, node)
	#
	def play(self, (node, callback, arg)):
		self.showtext(node)
		wait = node.GetInherAttrDef('wait_for_close', 0)
		if wait:
			self.player.freeze() # Should have another interface
			now = self.player.queue.timefunc()
			self.qid = self.player.queue.enter(now + 0.001, 0, \
						self.done, (callback, arg))
		else:
			Channel.play(self, (node, callback, arg))
	#
	def showtext(self, node):
		self.window.settext(self.getstring(node))
		#
	def getstring(self, node):
		if node.type = 'imm':
			return string.join(node.GetValues())
		elif node.type = 'ext':
			file = node.GetInherAttrDef('file', '/dev/null')
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
	'':		('Times-Roman', 13), \
	'default':	('Times-Roman', 13), \
	'plain':	('Times-Roman', 13), \
	'italic':	('Times-Italic', 13), \
	'bold':		('Times-Bold', 13), \
	'courier':	('Courier', 13), \
	'bigbold':	('Times-Bold', 16), \
	'title':	('Times-Bold', 24), \
	  }

def mapfont(fontname):
#	print 'mapfont', fontname
	if fontmap.has_key(fontname):
		return fontmap[fontname]
	else:
		return fontname, 13
