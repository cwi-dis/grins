__version__ = "$Id$"

import wingdi
import wincon

from sysmetrics import *

_POINTSIZEOFFSET=+1

pocket_pc_fonts = ['Tahoma', 'Bookdings', 'Courier New', 'Frutiger Linotype']
default_pocket_pc_font = 'Tahoma'

# we should enumarate installed fonts on the device and select one from the list
# there is an api for this
_fontmap = {
	'Times-Roman': default_pocket_pc_font,
	'Times-Italic': default_pocket_pc_font,
	'Times-Bold': default_pocket_pc_font,
	'Courier': default_pocket_pc_font,
	'Greek': default_pocket_pc_font,
	 }

fonts = _fontmap.keys()

# Parse a font name
def _parsefontname(fontname):
	list = fontname.split('-')
	if len(list) != 15:
		raise error, 'fontname not well-formed'
	return list

# Compose font name
def _makefontname(font):
	return '-'.join(font)

_fontcache = {}

# Find a font with font name at point size
def findfont(fontname, pointsize):
	if type(pointsize)==type(''):
		pointsize = int(pointsize)
	pointsize = int(pointsize) # in case of float
	if fontname in fonts:
		fontname = _fontmap[fontname]
	else:
		fontname = default_pocket_pc_font

	key = '%s%d' % (fontname, pointsize)
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
			pointsize=int(pointsize)
		pointsize = int(pointsize+_POINTSIZEOFFSET)	# correction because of tiny fonts on Windows
		#pointsize = (pointsize*dpi_y+36)/72 # screen correction
		global user_charset
		self._fd = {'name':fontname, 'height':-pointsize, 'weight':540}
##		self._hfont = wingdi.CreateFontIndirect(self._fd)
		self._hfont = wingdi.GetStockObject(wincon.SYSTEM_FONT)
		self._tm = self.gettextmetrics()

	# Delete the associated OS font
	def __del__(self):
		if self._hfont:
			wingdi.DeleteObject(self._hfont)

	# Returns the handle to this font
	def handle(self):
		return self._hfont

	# Close this object and release resources
	def close(self):
		if self._hfont:
			wingdi.DeleteObject(self._hfont)
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
		return self.fontheightPXL() / 12.0
	
	# Returns the string size in mm	
	def strsizePXL(self,str):
		strlist = str.split('\n')
		hdc = winuser.GetDC()
		dc = wingdi.CreateDCFromHandle(hdc)
		self._hfont_org = dc.SelectObject(self._hfont)
		maxwidth = 0
		height = len(strlist) * self.fontheightPXL()
		for str in strlist:
			cx, cy = dc.GetTextExtent(str)
			if cx > maxwidth:
				maxwidth = cx
		dc.SelectObject(self._hfont_org)
		dc.Detach()
		return maxwidth, height

	def strsize(self,str):
		maxwidth, maxheight = self.strsizePXL(str)
		return pxl2mm_x(maxwidth),pxl2mm_y(maxheight)

	# Returns the text metrics structure
	def gettextmetrics(self):
		hdc = winuser.GetDC()
		dc = wingdi.CreateDCFromHandle(hdc)
		self._hfont_org = dc.SelectObject(self._hfont)
		tm = dc.GetTextMetrics()
		dc.SelectObject(self._hfont_org)
		dc.Detach()
		return tm
	
	# Returns the string size in pixel	
	def gettextextent(self,str):
		hdc = winuser.GetDC()
		dc = wingdi.CreateDCFromHandle(hdc)
		self._hfont_org = dc.SelectObject(self._hfont)
		cx, cy = dc.GetTextExtent(str)
		dc.SelectObject(self._hfont_org)
		dc.Detach()
		if cy<0: cy = -cy
		return cx, cy

	# Returns the string width in pixel	
	def TextWidth(self, str):
		return self.gettextextent(str)[1]
	# Returns the string size in pixel	
	def TextSize(self, str):
		return self.gettextextent(str)

