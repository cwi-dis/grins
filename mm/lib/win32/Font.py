__version__ = "$Id$"

import string
import win32ui
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

from sysmetrics import *


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
	  'Arial': 'Arial',
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
	try:
		return _fontcache[key]
	except KeyError:
		pass
# use fontcache but not fontmap. 
# leave the system to synthesize one
#	try:
#		fontname = _fontmap[fontname]
#	except KeyError:
#		raise error, 'Unknown font ' + `fontname`
#	fontname = 'Arial'
	fontobj = _Font(fontname, pointsize)
	_fontcache[key] = fontobj
	return fontobj	


# The methods of the font_object are:
#	close()
#		Close the font object and free its resources.
#
#	strsize(text) -> width, height
#		Return the dimensions in mm of the box that the given
#		text would occupy if displayed in the font the font
#		object represents.
#
#	baseline() -> baseline
#		Return the height of the baseline in mm.
#
#	fontheight() -> fontheight
#		Return the height of the font in mm.
#
#	pointsize() -> pointsize
#		Return the point size actually used in points.


class _Font:
	def __init__(self, fontname, pointsize):
		self._fd={'name':fontname,'size':pointsize,'weight':700}
		self._hfont=Sdk.CreateFontIndirect(self._fd)		
		self._tm=self.gettextmetrics()

	def __del__(self):
		print "font.__del__"
		if self._hfont != None:
			self.close()

	def handle(self):
		return self._hfont

	def close(self):
		Sdk.DeleteObject(self._hfont)
		self._hfont = 0

	def is_closed(self):
		return self._hfont is 0

	def fontname(self):
		return self._fd['name']	
			
	def baseline(self):
		return pxl2mm_y(self._tm['tmAscent']+self._tm['tmDescent'])

	def fontheight(self):
		return pxl2mm_y(self._tm['tmHeight'])

	def pointsize(self):
		return self._fd['size']
		


	def strsize(self,str):
		strlist = string.splitfields(str, '\n')
		wnd=Afx.GetMainWnd()
		dc=wnd.GetDC()
		self._hfont_org=dc.SelectObjectFromHandle(self._hfont)
		maxwidth = 0
		maxheight = len(strlist) * self.baseline()
		for str in strlist:
			cx,cy=dc.GetTextExtent(str)
			if cx > maxwidth:
				maxwidth = cx
		dc.SelectObjectFromHandle(self._hfont_org)
		wnd.ReleaseDC(dc)
		return pxl2mm_x(maxwidth),pxl2mm_y(maxheight)


	def gettextmetrics(self):
		wnd=Afx.GetMainWnd()
		dc=wnd.GetDC()
		self._hfont_org=dc.SelectObjectFromHandle(self._hfont)
		
		tm=dc.GetTextMetrics()

		dc.SelectObjectFromHandle(self._hfont_org)
		wnd.ReleaseDC(dc)
		return tm
	
		
	def gettextextent(self,str):
		wnd=Afx.GetMainWnd()
		dc=wnd.GetDC()
		self._hfont_org=dc.SelectObjectFromHandle(self._hfont)
		
		cx,cy=dc.GetTextExtent(str)

		dc.SelectObjectFromHandle(self._hfont_org)
		wnd.ReleaseDC(dc)
		return (cx,cy)

	def TextWidth(self, str):
		return self.gettextextent(str)[1]
	def TextSize(self, str):
		return self.gettextextent(str)


"""	
TextMetrics dict entries:
tmHeight
tmAscent
tmDescent
tmInternalLeading
tmExternalLeading
tmAveCharWidth
tmMaxCharWidth
tmWeight
tmItalic
tmUnderlined
tmStruckOut
tmFirstChar
tmLastChar
tmDefaultChar
tmBreakChar
tmPitchAndFamily
tmCharSet
tmOverhang
tmDigitizedAspectX
tmDigitizedAspectY
"""
