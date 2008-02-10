__version__ = "$Id$"

import string
from types import StringType
from XTopLevel import toplevel
from XConstants import error

_fontmap = {
          'Times-Roman': '-*-times-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Times-Italic': '-*-times-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
          'Times-Bold': '-*-times-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Utopia': '-*-utopia-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Utopia-Italic': '-*-utopia-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
          'Utopia-Bold': '-*-utopia-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Palatino': '-*-palatino-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Palatino-Italic': '-*-palatino-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
          'Palatino-Bold': '-*-palatino-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Helvetica': '-*-helvetica-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Helvetica-Bold': '-*-helvetica-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Helvetica-Oblique': '-*-helvetica-medium-o-normal-*-*-*-*-*-*-*-iso8859-1',
          'Courier': '-*-courier-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Courier-Bold': '-*-courier-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
          'Courier-Oblique': '-*-courier-medium-o-normal-*-*-*-*-*-*-*-iso8859-1',
          'Courier-Bold-Oblique': '-*-courier-bold-o-normal-*-*-*-*-*-*-*-iso8859-1',
          'Greek': ['-*-arial-regular-r-*-*-*-*-*-*-p-*-iso8859-7',
                    '-*-*-medium-r-*--*-*-*-*-*-*-iso8859-7'],
          'Greek-Bold': ['-*-arial-bold-r-*--*-*-*-*-p-*-iso8859-7',
                         '-*-*-bold-r-*-*-*-*-*-*-*-*-iso8859-7'],
          'Greek-Italic': '-*-arial-regular-i-*-*-*-*-*-*-p-*-iso8859-7',
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
    try:
        fontnames = _fontmap[fontname]
    except KeyError:
        raise error, 'Unknown font ' + `fontname`
    if type(fontnames) is StringType:
        fontnames = [fontnames]
    fontlist = []
    for fontname in fontnames:
        fontlist = toplevel._main.ListFonts(fontname)
        if fontlist:
            break
    if not fontlist:
        # if no matching fonts, use Courier, same encoding
        parsedfont = _parsefontname(fontname)
        font = '-*-courier-*-r-*-*-*-*-*-*-*-*-%s-%s' % \
               (parsedfont[_REGISTRY], parsedfont[_ENCODING])
        fontlist = toplevel._main.ListFonts(font)
    if not fontlist:
        # if still no matching fonts, use any font, same encoding
        parsedfont = _parsefontname(fontname)
        font = '-*-*-*-*-*-*-*-*-*-*-*-*-%s-%s' % \
               (parsedfont[_REGISTRY], parsedfont[_ENCODING])
        fontlist = toplevel._main.ListFonts(font)
    if not fontlist:
        # if still no matching fonts, use Courier, any encoding
        fontlist = toplevel._main.ListFonts('-*-courier-*-r-*-*-*-*-*-*-*-*-*-*')
    if not fontlist:
        # if still no matching fonts, use any font, any encoding
        fontlist = toplevel._main.ListFonts('-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
    if not fontlist:
        # if no fonts at all, give up
        raise error, 'no fonts available'
    pixelsize = pointsize * toplevel._dpi_y / 72.0
    bestsize = 0
    psize = pointsize
    scfont = None
    thefont = None
    smsize = 9999                   # something big
    smfont = None
    for font in fontlist:
        try:
            parsedfont = _parsefontname(font)
        except:
            # XXX catch parsing errors from the mac
            continue
## scaled fonts don't look very nice, so this code is disabled
##         # scale the font if possible
##         if parsedfont[_PIXELS] == '0':
##             # scalable font
##             parsedfont[_PIXELS] = '*'
##             parsedfont[_POINTS] = `int(pointsize * 10)`
##             parsedfont[_RES_X] = `toplevel._dpi_x`
##             parsedfont[_RES_Y] = `toplevel._dpi_y`
##             parsedfont[_AVG_WIDTH] = '*'
##             thefont = _makefontname(parsedfont)
##             psize = pointsize
##             break
        # remember scalable font in case no other sizes available
        if parsedfont[_PIXELS] == '0':
            scfont = parsedfont
            continue
        p = string.atoi(parsedfont[_PIXELS])
        if p < smsize:
            smfont = font
        # either use closest, or use next smaller
        if abs(pixelsize - p) < abs(pixelsize - bestsize): # closest
##         if p <= pixelsize and p > bestsize: # biggest <= wanted
            bestsize = p
            thefont = font
            psize = p * 72.0 / toplevel._dpi_y
    if thefont is None:
        # didn't find a font
        if scfont is not None:
            # but we found a scalable font, so use it
            scfont[_PIXELS] = '*'
            scfont[_POINTS] = `int(pointsize * 10)`
            scfont[_RES_X] = `toplevel._dpi_x`
            scfont[_RES_Y] = `toplevel._dpi_y`
            scfont[_AVG_WIDTH] = '*'
            thefont = _makefontname(scfont)
            psize = pointsize
        elif smfont is not None:
            # nothing smaller, so take next bigger
            thefont = font
            psize = smsize * 72.0 / toplevel._dpi_y
        else:
            # no font available, complain.  Loudly.
            raise error, "can't find any fonts"
    fontobj = _Font(thefont, psize)
    _fontcache[key] = fontobj
    return fontobj

class _Font:
    def __init__(self, fontname, pointsize):
        self._font = toplevel._main.LoadQueryFont(fontname)
        self._pointsize = pointsize
        self._fontname = fontname
##         print 'Using', fontname

    def close(self):
        self._font = None

    def is_closed(self):
        return self._font is None

    def strsizePXL(self, str):
        strlist = string.splitfields(str, '\n')
        maxwidth = 0
        f = self._font
        maxheight = len(strlist) * (f.ascent + f.descent)
        for str in strlist:
            width = f.TextWidth(str)
            if width > maxwidth:
                maxwidth = width

        return maxwidth, maxheight

    def strsize(self, str):
        maxwidth, maxheight = self.strsizePXL(str)
        return float(maxwidth) / toplevel._hmm2pxl, \
               float(maxheight) / toplevel._vmm2pxl

    def baselinePXL(self):
        return self._font.ascent

    def baseline(self):
        return float(self.baselinePXL()) / toplevel._vmm2pxl

    def fontheightPXL(self):
        f = self._font
        return f.ascent + f.descent

    def fontheight(self):
        return float(self.fontheightPXL()) / toplevel._vmm2pxl

    def pointsize(self):
        return self._pointsize
