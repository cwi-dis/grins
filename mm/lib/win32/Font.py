__version__ = "$Id$"

import string
import win32ui
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

from sysmetrics import *

_fontmap = {
	'Arial': 'Arial',
	'Courier':'Courier',
	'Courier-Bold':'Courier Bold',
	'Courier-Bold-Oblique':'Courier Bold', 
	'Courier-Oblique':'Courier', 
	'Greek':'Arial',
	'Greek-Italic':'Arial Italic', 
	'Helvetica':'Helvetica',
	'Helvetica-Bold':'Helvetica Bold',
	'Helvetica-Oblique':'Helvetica Italic', 
	'Palatino':'Arial',
	'Palatino-Bold':'Arial Bold',
	'Palatino-Italic':'Arial Italic', 
	'Times-Bold':'Times New Roman Bold',
	'Times-Italic':'Times New Roman Italic',
	'Times-Roman':'Times New Roman', 
	'Utopia':'Arial',
	'Utopia-Bold':'Arial Bold',
	'Utopia-Italic':'Arial Italic',
	 }

fonts = _fontmap.keys()


def _parsefontname(fontname):
	list = string.splitfields(fontname, '-')
	if len(list) != 15:
		raise error, 'fontname not well-formed'
	return list

def _makefontname(font):
	return string.joinfields(font, '-')

_fontcache = {}

def findfont(fontname, pointsize):
	if type(pointsize)==type(''):
		pointsize=string.atoi(pointsize)
	pointsize=int(pointsize) # in case of float
	if fontname in fonts:
		fontname=_fontmap[fontname]

	key = '%s%d' % (fontname,pointsize)
	try:
		return _fontcache[key]
	except KeyError:
		pass
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
		if type(pointsize)==type(''):
			pointsize=string.atoi(pointsize)
		pointsize=int(pointsize)
		pointsize=pointsize*dpi_y/72 # screen correction
		self._fd={'name':fontname,'height':-pointsize,'weight':540}
		global user_charset
		self._hfont=Sdk.CreateFontIndirect(self._fd,user_charset)		
		self._tm=self.gettextmetrics()

	def __del__(self):
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
		ps=self._fd['height']
		if ps<0:ps=-ps
		return ps
		
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

# from WINGDI.H
ANSI_CHARSET            =0
DEFAULT_CHARSET         =1
SYMBOL_CHARSET          =2
SHIFTJIS_CHARSET        =128
HANGEUL_CHARSET         =129
HANGUL_CHARSET          =129
GB2312_CHARSET          =134
CHINESEBIG5_CHARSET     =136
OEM_CHARSET             =255
JOHAB_CHARSET           =130
HEBREW_CHARSET          =177
ARABIC_CHARSET          =178
GREEK_CHARSET           =161
TURKISH_CHARSET         =162
VIETNAMESE_CHARSET      =163
THAI_CHARSET            =222
EASTEUROPE_CHARSET      =238
RUSSIAN_CHARSET         =204
MAC_CHARSET             =77
BALTIC_CHARSET          =186

win32_charsets_list= [
'ANSI',
'DEFAULT',
'OEM',
'GREEK',
'MAC',
'RUSSIAN',
'EASTEUROPE',
'TURKISH',
'ARABIC',
'HEBREW',
'BALTIC',

'CHINESEBIG',
'GB2312',
'HANGUL',
'SHIFTJIS',
'SYMBOL',
'JOHAB',
'THAI',
]

win32_charsets= {
'ANSI':ANSI_CHARSET,
'DEFAULT':DEFAULT_CHARSET,
'OEM':OEM_CHARSET,
'EASTEUROPE':EASTEUROPE_CHARSET,
'GREEK':GREEK_CHARSET,
'MAC':MAC_CHARSET,

'BALTIC':BALTIC_CHARSET,
'CHINESEBIG':CHINESEBIG5_CHARSET,
'GB2312':GB2312_CHARSET,
'HANGUL':HANGUL_CHARSET,
'RUSSIAN':RUSSIAN_CHARSET,
'SHIFTJIS':SHIFTJIS_CHARSET,
'SYMBOL':SYMBOL_CHARSET,
'TURKISH':TURKISH_CHARSET,
'JOHAB':JOHAB_CHARSET,
'HEBREW':HEBREW_CHARSET,
'ARABIC':ARABIC_CHARSET,
'THAI':THAI_CHARSET,
}

user_charset=DEFAULT_CHARSET

def set_win32_charset(strid):
	global user_charset
	if strid in win32_charsets.keys():
		print 'setting charset to:',strid		
		user_charset=win32_charsets[strid]
		_fontcache.clear()
		
def get_win32_charset(strid):
	global user_charset
	return user_charset
		
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
