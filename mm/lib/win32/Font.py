__version__ = "$Id$"

# @win32doc|Font
# It is a utility module with a standard interface
# offering fonts support to other modules
# The class _Font is a wrapper class for the platform
# font along with a standard query interface

import string
import win32ui
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

from sysmetrics import *

_POINTSIZEOFFSET=+1

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

# Parse a font name
def _parsefontname(fontname):
	list = string.splitfields(fontname, '-')
	if len(list) != 15:
		raise error, 'fontname not well-formed'
	return list

# Compose font name
def _makefontname(font):
	return string.joinfields(font, '-')

_fontcache = {}

# Find a font with font name at point size
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

def delfonts():
	for key in _fontcache.keys():
		_fontcache[key].close()
	_fontcache.clear()

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

# The Font is a wrapper class for an OS font
class _Font:
	def __init__(self, fontname, pointsize):
		if type(pointsize)==type(''):
			pointsize=string.atoi(pointsize)
		pointsize=int(pointsize+_POINTSIZEOFFSET)	# correction because of tiny fonts on Windows
		pointsize=(pointsize*dpi_y+36)/72 # screen correction
		global user_charset
		self._fd={'name':fontname,'height':-pointsize,'weight':540, 'charset':user_charset}
		self._hfont=Sdk.CreateFontIndirect(self._fd)		
		self._tm=self.gettextmetrics()

	# Delete the associated OS font
	def __del__(self):
		if self._hfont and Sdk:
			Sdk.DeleteObject(self._hfont)

	# Returns the handle to this font
	def handle(self):
		return self._hfont

	# Close this object and release resources
	def close(self):
		if self._hfont and Sdk:
			Sdk.DeleteObject(self._hfont)
			self._hfont = 0

	# Returns true if this is closed
	def is_closed(self):
		return self._hfont is 0

	# Returns this font name
	def fontname(self):
		return self._fd['name']	
			
	# Returns this font baseline
	def baselinePXL(self):
		# Wrong: return self._tm['tmAscent']+self._tm['tmDescent']
		# Put the leading on the top
		return self._tm['tmHeight']# +self._tm['tmExternalLeading']
	def baseline(self):
		return pxl2mm_y(self.baselinePXL())

	# Returns this font height
	def fontheightPXL(self):
		# Wrong: return self._tm['tmHeight']
		return self._tm['tmHeight'] + self._tm['tmExternalLeading']
	def fontheight(self):
		return pxl2mm_y(self.fontheightPXL())

	# Returns this font pointsize
	def pointsize(self):
		ps=self._fd['height']
		if ps<0:ps=-ps
		return ps
	
	# Returns the string size in mm	
	def strsizePXL(self,str):
		strlist = string.splitfields(str, '\n')
		wnd=Afx.GetMainWnd()
		dc=wnd.GetDC()
		self._hfont_org=dc.SelectObjectFromHandle(self._hfont)
		maxwidth = 0
		height = len(strlist) * self.fontheightPXL()
		for str in strlist:
			cx,cy=dc.GetTextExtent(str)
			if cx > maxwidth:
				maxwidth = cx
		dc.SelectObjectFromHandle(self._hfont_org)
		wnd.ReleaseDC(dc)
		return maxwidth, height
	def strsize(self,str):
		maxwidth, maxheight = self.strsizePXL(str)
		return pxl2mm_x(maxwidth),pxl2mm_y(maxheight)

	# Returns the text metrics structure
	def gettextmetrics(self):
		wnd=Afx.GetMainWnd()
		dc=wnd.GetDC()
		self._hfont_org=dc.SelectObjectFromHandle(self._hfont)
		
		tm=dc.GetTextMetrics()

		dc.SelectObjectFromHandle(self._hfont_org)
		wnd.ReleaseDC(dc)
		return tm
	
		
	# Returns the string size in pixel	
	def gettextextent(self,str):
		wnd=Afx.GetMainWnd()
		dc=wnd.GetDC()
		self._hfont_org=dc.SelectObjectFromHandle(self._hfont)
		
		cx,cy=dc.GetTextExtent(str)

		dc.SelectObjectFromHandle(self._hfont_org)
		wnd.ReleaseDC(dc)
		return (cx,cy)

	# Returns the string width in pixel	
	def TextWidth(self, str):
		return self.gettextextent(str)[1]
	# Returns the string size in pixel	
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

# set current windows char set
def set_win32_charset(strid):
	global user_charset
	if win32_charsets.has_key(strid):
		#print 'windows charset:',strid		
		user_charset=win32_charsets[strid]
		_fontcache.clear()
		
# get current windows char set
def get_win32_charset(strid):
	global user_charset
	return user_charset
		
# TextMetrics dict entries:
# tmHeight
# tmAscent
# tmDescent
# tmInternalLeading
# tmExternalLeading
# tmAveCharWidth
# tmMaxCharWidth
# tmWeight
# tmItalic
# tmUnderlined
# tmStruckOut
# tmFirstChar
# tmLastChar
# tmDefaultChar
# tmBreakChar
# tmPitchAndFamily
# tmCharSet
# tmOverhang
# tmDigitizedAspectX
# tmDigitizedAspectY
