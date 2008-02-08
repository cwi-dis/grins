__version__ = "$Id$"

from Carbon import Qd
from Carbon import Fm
import string

#
# Stuff imported from other mw_ modules
#
import mw_globals
from mw_globals import error

#
# The fontfaces (which are unfortunately not defined in QuickDraw.py)
_qd_bold = 1
_qd_italic = 2


# Routines to save/restore complete textfont info
def _checkfontinfo(port, finfo):
    """Return true if font info different from args"""
    if not port:
        return 1
    curfinfo = (port.GetPortTextFont, port.GetPortTextFace(), port.GetPortTextSize())
    return finfo <> curfinfo

def _savefontinfo(port):
    """Return all font-pertaining info for a macos window"""
    if not port:
        return ()
    return port.GetPortTextFont(), port.GetPortTextFace(), port.GetPortTextMode(), \
            port.GetPortTextSize(), port.GetPortSpExtra()

def _restorefontinfo(port, (font, face, mode, size, spextra)):
    """Set all font-pertaining info for a macos window"""
    if not port:
        return
    old = Qd.GetPort()
    Qd.SetPort(port)
    Qd.TextFont(font)
    Qd.TextFace(face)
    Qd.TextMode(mode)
    Qd.TextSize(size)
    Qd.SpaceExtra(spextra)
    Qd.SetPort(old)


_pt2mm = 25.4 / 72                      # 1 inch == 72 points == 25.4 mm
_POINTSIZEOFFSET=+1
_fontmap = {
##       'Times-Roman': ('Times', 0),
##       'Times-Italic': ('Times', _qd_italic),
##       'Times-Bold': ('Times', _qd_bold),
          'Times-Roman': ('New York', 0),
          'Times-Italic': ('New York', _qd_italic),
          'Times-Bold': ('New York', _qd_bold),

          'Utopia': ('New York', 0),
          'Utopia-Italic': ('New York', _qd_italic),
          'Utopia-Bold': ('New York', _qd_bold),

          'Palatino': ('Palatino', 0),
          'Palatino-Italic': ('Palatino', _qd_italic),
          'Palatino-Bold': ('Palatino', _qd_bold),

##       'Helvetica': ('Helvetica', 0),
##       'Helvetica-Bold': ('Helvetica', _qd_bold),
##       'Helvetica-Oblique': ('Helvetica', _qd_italic),
          'Helvetica': ('Geneva', 0),
          'Helvetica-Bold': ('Geneva', _qd_bold),
          'Helvetica-Oblique': ('Geneva', _qd_italic),

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
        self._pointsize = pointsize + _POINTSIZEOFFSET
        self._inited = 0

    def _getinfo(self):
        """Get details of font (mac-only)"""
        return self._fontnum, self._fontface, self._pointsize

    def _setfont(self, port):
        """Set our font, saving the old one for later"""
        if port:
            Qd.SetPort(port)
        Qd.TextFont(self._fontnum)
        Qd.TextFace(self._fontface)
        Qd.TextSize(self._pointsize)

    def _checkfont(self, port):
        """Check whether our font needs to be installed in this grafport"""
        return _checkfontinfo(port, (self._fontnum, self._fontface, self._pointsize))

    def _initparams(self, port=None):
        """Obtain font params like ascent/descent, if needed"""
        if self._inited:
            return
        self._inited = 1
        if port:
            old_fontinfo = _savefontinfo(port)
        self._setfont(port)
        self.ascent, self.descent, widMax, self.leading = Qd.GetFontInfo()
        # XXXX leading gives too much space. An experiment: zap it.
        self.leading = 0
        if port:
            _restorefontinfo(port, old_fontinfo)

    def close(self):
        pass

    def is_closed(self):
        return 0

    def strsizePXL(self, str, port=None):
        self._initparams(port)
        strlist = string.splitfields(str, '\n')
        maxwidth = 0
        maxheight = len(strlist) * (self.ascent + self.descent + self.leading)
        old_fontinfo = None
        if self._checkfont(port):
            old_fontinfo = _savefontinfo(port)
        self._setfont(port)
        for str in strlist:
            width = Qd.TextWidth(str, 0, len(str))
            if width > maxwidth:
                maxwidth = width
        if old_fontinfo:
            _restorefontinfo(port, old_fontinfo)
        return maxwidth, maxheight

    def strsize(self, str):
        _x_pixel_per_mm, _y_pixel_per_mm = \
                         mw_globals.toplevel._getmmfactors()
        maxw, maxh = self.strsizePXL(str)
        return float(maxw) / _x_pixel_per_mm, \
               float(maxh) / _y_pixel_per_mm


    def baselinePXL(self):
        self._initparams()
        return self.ascent+self.leading

    def baseline(self):
        _x_pixel_per_mm, _y_pixel_per_mm = \
                         mw_globals.toplevel._getmmfactors()
        return float(self.baselinePXL()) / _y_pixel_per_mm

    def fontheightPXL(self):
        self._initparams()
        return self.ascent + self.descent + self.leading

    def fontheight(self):
        _x_pixel_per_mm, _y_pixel_per_mm = \
                         mw_globals.toplevel._getmmfactors()
        return float(self.fontheightPXL()) / _y_pixel_per_mm

    def pointsize(self):
        return self._pointsize
