import Qd
import Fm
import string

#
# Stuff imported from other mw_ modules
#
from mw_globals import error

#
# The fontfaces (which are unfortunately not defined in QuickDraw.py)
_qd_bold = 1
_qd_italic = 2


# Routines to save/restore complete textfont info
def _checkfontinfo(wid, finfo):
	"""Return true if font info different from args"""
	port = wid.GetWindowPort()
	curfinfo = (port.txFont, port.txFace, port.txSize)
	return finfo <> curfinfo
	
def _savefontinfo(wid):
	"""Return all font-pertaining info for a macos window"""
	port = wid.GetWindowPort()
	return port.txFont, port.txFace, port.txMode, port.txSize, port.spExtra
	
def _restorefontinfo(wid, (font, face, mode, size, spextra)):
	"""Set all font-pertaining info for a macos window"""
	old = Qd.GetPort()
	Qd.SetPort(wid)
	Qd.TextFont(font)
	Qd.TextFace(face)
	Qd.TextMode(mode)
	Qd.TextSize(size)
	Qd.SpaceExtra(spextra)
	Qd.SetPort(old)


_pt2mm = 25.4 / 72			# 1 inch == 72 points == 25.4 mm

_fontmap = {
	  'Times-Roman': ('Times', 0),
	  'Times-Italic': ('Times', _qd_italic),
	  'Times-Bold': ('Times', _qd_bold),

	  'Utopia': ('New York', 0),
	  'Utopia-Italic': ('New York', _qd_italic),
	  'Utopia-Bold': ('New York', _qd_bold),

	  'Palatino': ('Palatino', 0),
	  'Palatino-Italic': ('Palatino', _qd_italic),
	  'Palatino-Bold': ('Palatino', _qd_bold),

	  'Helvetica': ('Helvetica', 0),
	  'Helvetica-Bold': ('Helvetica', _qd_bold),
	  'Helvetica-Oblique': ('Helvetica', _qd_italic),

	  'Courier': ('Courier', 0),
	  'Courier-Bold': ('Courier', _qd_bold),
	  'Courier-Oblique': ('Courier', _qd_italic),
	  'Courier-Bold-Oblique': ('Courier', _qd_italic+_qd_bold),
	  
	  'Greek': ('GrHelvetica', 0),
	  'Greek-Bold': ('GrHelvetica', _qd_bold),
	  'Greek-Italic': ('GrHelvetica', _qd_italic),
	  }
	  
fonts = _fontmap.keys()

class findfont:
	def __init__(self, fontname, pointsize):
		if not _fontmap.has_key(fontname):
			raise error, 'Font not found: '+fontname
		self._fontnum = Fm.GetFNum(_fontmap[fontname][0])
		self._fontface = _fontmap[fontname][1]
		self._pointsize = pointsize
		self._inited = 0
		
	def _getinfo(self):
		"""Get details of font (mac-only)"""
		return self._fontnum, self._fontface, self._pointsize
		
	def _setfont(self, wid):
		"""Set our font, saving the old one for later"""
		Qd.SetPort(wid)
		Qd.TextFont(self._fontnum)
		Qd.TextFace(self._fontface)
		Qd.TextSize(self._pointsize)
		
	def _checkfont(self, wid):
		"""Check whether our font needs to be installed in this wid"""
		return _checkfontinfo(wid, (self._fontnum, self._fontface, self._pointsize))
		
	def _initparams(self, wid):
		"""Obtain font params like ascent/descent, if needed"""
		if self._inited:
			return
		self._inited = 1
		old_fontinfo = _savefontinfo(wid)
		self._setfont(wid)
		self.ascent, self.descent, widMax, self.leading = Qd.GetFontInfo()
		_restorefontinfo(wid, old_fontinfo)

	def close(self):
		pass

	def is_closed(self):
		return 0

	def strsize(self, wid, str):
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * (self.ascent + self.descent + self.leading)
		old_fontinfo = None
		if self._checkfont(wid):
			old_fontinfo = _savefontinfo(wid)
		self._setfont(wid)
		for str in strlist:
			width = Qd.TextWidth(str, 0, len(str))
			if width > maxwidth:
				maxwidth = width
		if old_fontinfo:
			_restorefontinfo(wid, old_fontinfo)
		return float(maxwidth) / _x_pixel_per_mm, \
		       float(maxheight) / _y_pixel_per_mm

	def baseline(self):
		return float(self.ascent+self.leading) / _y_pixel_per_mm

	def fontheight(self):
		return float(self.ascent + self.descent + self.leading) \
			/ _y_pixel_per_mm

	def pointsize(self):
		return self._pointsize
