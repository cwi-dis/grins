__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex, cmifex2
import string

_screenwidth = cmifex.GetScreenWidth()
_screenheight = cmifex.GetScreenHeight()
_dpi_x = cmifex.GetScreenXDPI()
_dpi_y = cmifex.GetScreenYDPI()
_mscreenwidth = (float(_screenwidth)*25.4) / _dpi_x
_mscreenheight = (float(_screenheight)*25.4) / _dpi_y
_hmm2pxl = float(_screenwidth) / _mscreenwidth
_vmm2pxl = float(_screenheight) / _mscreenheight

_pt2mm = 25.4 / 96			# 1 inch == 96 points == 25.4 mm
							# original 72
_fontmap = {
	  'Times-Roman': 'Times New Roman',
	  'Times-Italic': 'Times New Roman',
	  'Times-Bold': 'Times New Roman',
	  'Utopia': 'System',
	  'Utopia-Italic': 'System',
	  'Utopia-Bold': 'System',
	  'Palatino': 'Century Schoolbook',
	  'Palatino-Italic': 'Century Schoolbook',
	  'Palatino-Bold': 'Century Schoolbook',
	  'Helvetica': 'Arial',
	  'Helvetica-Bold': 'Arial',
	  'Helvetica-Oblique': 'Arial',
	  'Courier': 'Courier New',
	  'Courier-Bold': 'Courier New',
	  'Courier-Oblique': 'Courier New',
	  'Courier-Bold-Oblique': 'Courier New',
	  'Greek': 'Arial',
	  'Greek-Italic': 'Arial',
	  }
fonts = _fontmap.keys()

_FOUNDRY = 1
_FONT_FAMILY = 2
_WEIGHT = 3
_SLANT = 4
_SET_WIDTH = 5
_PIXELS = 7
_POINTS = 8
_RES_X = 9
_RES_Y = 10
_SPACING = 11
_AVG_WIDTH = 12
_REGISTRY = 13
_ENCODING = 14

def _parsefontname(fontname):
	list = string.splitfields(fontname, '-')
	if len(list) != 15:
		raise error, 'fontname not well-formed'
	return list

def _makefontname(font):
	return string.joinfields(font, '-')

_fontcache = {}

def findfont(fontname, pointsize):
	key = fontname + `pointsize`
	fontobj = _Font(fontname, pointsize)
	_fontcache[key] = fontobj
	return fontobj	
	###########
	key = fontname + `pointsize`
	try:
		return _fontcache[key]
	except KeyError:
		pass
	try:
		fontnames = _fontmap[fontname]
	except KeyError:
		raise error, 'Unknown font ' + `fontname`
	fontname = 'Arial'
	pointsize = 12
	pixelsize = pointsize * _dpi_y / 96.0
	bestsize = 0
	fontobj = _Font(fontname, pointsize)
	_fontcache[key] = fontobj
	return fontobj	
	
class _Font:
	def __init__(self, fontname, pointsize):
		self._height, self._ascent, self._maxWidth, self._aveWidth = cmifex.GetTextMetrics()
		self._pointsize = pointsize
		self._fontname = fontname

	def close(self):
		self._font = None

	def is_closed(self):
		return self._font is None

	def strsize(self, str):
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		#maxheight = len(strlist) * (self._height)
		maxheight = len(strlist) * (self._pointsize)
		for str in strlist:
			#width = cmifex.GetTextWidth(str)
			#width = len(str)*self._maxWidth
			width = len(str)*self._aveWidth
			if width > maxwidth:
				maxwidth = width
		return float(maxwidth) / _hmm2pxl, \
		       float(maxheight) / _vmm2pxl

	def baseline(self):
		return float(self._ascent) / _vmm2pxl

	def fontheight(self):
		return float(self._height) / _vmm2pxl

	def pointsize(self):
		return self._pointsize
