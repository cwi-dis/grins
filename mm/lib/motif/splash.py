__version__ = "$Id$"

import Xt, Xm, Xmd, sys, X, Xcursorfont

error = 'windowinterface.error'

# try these visuals in this order
tryvisuals = [
        (X.TrueColor, 24),
        (X.TrueColor, 32),
        (X.TrueColor, 16),
        (X.TrueColor, 15),
        (X.TrueColor, 8),
        (X.PseudoColor, 8),
        ]

resources = [
# fonts
'GRiNS*menuBar*fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*menubar*fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmLabel.fontList: -*-helvetica-bold-r-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmLabelGadget.fontList: -*-helvetica-bold-r-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmList.fontList: -*-helvetica-medium-r-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmCascadeButton.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmCascadeButtonGadget.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmLabel.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmLabelGadget.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmPushButton.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmPushButtonGadget.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmToggleButton.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmMenuShell*XmToggleButtonGadget.fontList: -*-helvetica-bold-o-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmPushButton.fontList: -*-helvetica-medium-r-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmPushButtonGadget.fontList: -*-helvetica-medium-r-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmScale*fontList: -*-helvetica-bold-r-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmText.fontList: -*-fixed-medium-r-normal--*-100-*-*-*-*-iso8859-1',
'GRiNS*XmTextField.fontList: -*-fixed-medium-r-normal--*-100-*-*-*-*-iso8859-1',
'GRiNS*XmToggleButton.fontList: -*-helvetica-medium-r-normal--*-120-*-*-*-*-iso8859-1',
'GRiNS*XmToggleButtonGadget.fontList: -*-helvetica-medium-r-normal--*-120-*-*-*-*-iso8859-1',
# colors
## 'GRiNS*XmDrawnButton.background: #999999',
## 'GRiNS*XmList.background: #999999',
'GRiNS*XmMenuShell*XmToggleButton.selectColor: #000000',
'GRiNS*XmMenuShell*background: #999999',
'GRiNS*help_label.foreground: #000000',
'GRiNS*help_label.background: #eedd82',
'GRiNS*XmMenuShell*help_label.background: #eedd82',
## 'GRiNS*XmPushButton.background: #999999',
'GRiNS*XmScale*foreground: #000000',
'GRiNS*XmScale.XmScrollBar.foreground: #999999',
'GRiNS*XmText.background: #b98e8e',
'GRiNS*XmTextField.background: #b98e8e',
'GRiNS*background: #999999',
'GRiNS*foreground: #000000',
        ]

splashfont = '-*-univers-medium-r-condensed-*-*-90-100-*-*-*-*-*'

def roundi(x):
    if x < 0:
        return roundi(x + 1024) - 1024
    return int(x + 0.5)

try:
    int(0x100000000L)
except OverflowError:
    _64bitint = 0
else:
    _64bitint = 1

def _colormask(mask):
    shift = 0
    while (mask & 1) == 0:
        shift = shift + 1
        mask = mask >> 1
    if mask < 0:
        if _64bitint:
            width = 64 - shift
        else:
            width = 32 - shift
    else:
        width = 0
        while mask != 0:
            width = width + 1
            mask = mask >> 1
    return shift, (1 << width) - 1

def findformat(dpy, visual):
    import imgformat
    cmap = visual.CreateColormap(X.AllocNone)
    if visual.c_class == X.PseudoColor:
        r, g, b = imgformat.xrgb8.descr['comp'][:3]
        red_shift,   red_mask   = r[0], (1 << r[1]) - 1
        green_shift, green_mask = g[0], (1 << g[1]) - 1
        blue_shift,  blue_mask  = b[0], (1 << b[1]) - 1
        (plane_masks, pixels) = cmap.AllocColorCells(1, 8, 1)
        xcolors = []
        for n in range(256):
            # The colormap is set up so that the colormap
            # index has the meaning: rrrbbggg (same as
            # imgformat.xrgb8).
            xcolors.append(
                    (n+pixels[0],
                     int(float((n >> red_shift) & red_mask) / red_mask * 65535. + .5),
                     int(float((n >> green_shift) & green_mask) / green_mask * 65535. + .5),
                     int(float((n >> blue_shift) & blue_mask) / blue_mask * 65535. + .5),
                      X.DoRed|X.DoGreen|X.DoBlue))
        cmap.StoreColors(xcolors)
    else:
        red_shift, red_mask = _colormask(visual.red_mask)
        green_shift, green_mask = _colormask(visual.green_mask)
        blue_shift, blue_mask = _colormask(visual.blue_mask)
    if visual.depth == 8:
        import imgcolormap, imgconvert
        imgconvert.setquality(0)
        r, g, b = imgformat.xrgb8.descr['comp'][:3]
        xrs, xrm = r[0], (1 << r[1]) - 1
        xgs, xgm = g[0], (1 << g[1]) - 1
        xbs, xbm = b[0], (1 << b[1]) - 1
        c = []
        if (red_mask,green_mask,blue_mask) != (xrm,xgm,xbm):
            for n in range(256):
                r = roundi(((n>>xrs) & xrm) /
                            float(xrm) * red_mask)
                g = roundi(((n>>xgs) & xgm) /
                            float(xgm) * green_mask)
                b = roundi(((n>>xbs) & xbm) /
                            float(xbm) * blue_mask)
                c.append((r << red_shift) |
                         (g << green_shift) |
                         (b << blue_shift))
            lossy = 2
        elif (red_shift,green_shift,blue_shift)==(xrs,xgs,xbs):
            # no need for extra conversion
            myxrgb8 = imgformat.xrgb8
        else:
            for n in range(256):
                r = (n >> xrs) & xrm
                g = (n >> xgs) & xgm
                b = (n >> xbs) & xbm
                c.append((r << red_shift) |
                         (g << green_shift) |
                         (b << blue_shift))
            lossy = 0
        if c:
            myxrgb8 = imgformat.new('myxrgb8',
                    'X 3:3:2 RGB top-to-bottom',
                    {'type': 'rgb',
                     'b2t': 0,
                     'size': 8,
                     'align': 8,
                     # the 3,3,2 below are not
                     # necessarily correct, but they
                     # are not used anyway
                     'comp': ((red_shift, 3),
                              (green_shift, 3),
                              (blue_shift, 2))})
            cm = imgcolormap.new(
                    reduce(lambda x, y: x + '000' + chr(y), c, ''))
            imgconvert.addconverter(
                    imgformat.xrgb8,
                    imgformat.myxrgb8,
                    lambda d, r, src, dst, m=cm: m.map8(d),
                    lossy)
        format = myxrgb8
    else:
        # find an imgformat that corresponds with our visual and
        # with the available pixmap formats
        formats = []
        for pmf in dpy.ListPixmapFormats():
            if pmf[0] == visual.depth:
                formats.append(pmf)
        if not formats:
            raise error, 'no matching Pixmap formats found'
        for name, format in imgformat.__dict__.items():
            if type(format) is not type(imgformat.rgb):
                continue
            descr = format.descr
            if descr['type'] != 'rgb' or descr['b2t'] != 0:
                continue
            for pmf in formats:
                if descr['size'] == pmf[1] and \
                   descr['align'] == pmf[2]:
                    break
            else:
                continue
            r, g, b = descr['comp'][:3]
            if visual.red_mask   == ((1<<r[1])-1) << r[0] and \
               visual.green_mask == ((1<<g[1])-1) << g[0] and \
               visual.blue_mask  == ((1<<b[1])-1) << b[0]:
                break
        else:
            raise error, 'no proper imgformat available'
    return format, cmap, red_shift, red_mask, green_shift, green_mask, blue_shift, blue_mask

class _Splash:
    def __init__(self):
        self.main = None
        self.__initialized = 0
        self.__exposed = 0

    def splash(self, version = None):
        self.wininit()
        if self.visual.depth < 24:
            return 0
        try:
            import splashimg
        except ImportError:
            return 0
        import imgconvert
        try:
            rdr = imgconvert.stackreader(self.imgformat, splashimg.reader())
        except imgconvert.unsupported_error:
            return 0
        main = self.main
        data = rdr.read()
        width = rdr.width
        height = rdr.height
        swidth = main.WidthOfScreen()
        sheight = main.HeightOfScreen()
        shell = main.CreatePopupShell('splash', Xt.TopLevelShell,
                                      {'visual': self.visual,
                                       'depth': self.visual.depth,
                                       'colormap': self.colormap,
                                       'mwmDecorations': 0,
                                       'x': (swidth-width)/2,
                                       'y': (sheight-height)/2})
        self.shell = shell
##         form = shell.CreateManagedWidget('form', Xm.Form,
##                          {'allowOverlap': 1})
        w = shell.CreateManagedWidget('image', Xm.DrawingArea,
                                      {'width': width,
                                       'height': height,
                                       'x': 0, 'y': 0})
        if version is not None:
            attrs = {'labelString': version,
                     'alignment': Xmd.ALIGNMENT_CENTER,
                     'x': 10,
                     'y': 260,
                     'width': width-20,
                     'background': 0xffffff,
                     'foreground': 0x061440}
            try:
                w.LoadQueryFont(splashfont)
            except:
                # can't find the font, so don't use it
                pass
            else:
                attrs['fontList'] = splashfont
            l = w.CreateManagedWidget('version', Xm.Label, attrs)
        shell.Popup(0)
        gc = w.CreateGC({})
        descr = rdr.format.descr
        image = self.visual.CreateImage(self.visual.depth, X.ZPixmap,
                        0, data, width, height, descr['align'], 0)
        image.byte_order = self.byteorder
        w.AddCallback('exposeCallback', self.expose,
                      (gc.PutImage, (image, 0, 0, 0, 0, width, height)))
        gc.PutImage(image, 0, 0, 0, 0, width, height)
        w.DefineCursor(self.watchcursor)
        self.dpy.Flush()
        import Xtdefs
        while not self.__exposed:
            # at least wait until we were exposed
            Xt.ProcessEvent(Xtdefs.XtIMAll)
        while Xt.Pending():
            # then wait until all pending events have been
            # processed
            Xt.ProcessEvent(Xtdefs.XtIMAll)
        return 1

    def wininit(self):
        if self.__initialized:
            return
        self.__initialized = 1
        import struct
        if struct.pack('i', 1)[:1] == '\001':
            # little endian
            self.byteorder = X.LSBFirst
        else:
            # big endian
            self.byteorder = X.MSBFirst
        Xt.ToolkitInitialize()
        Xt.SetFallbackResources(resources)
        try:
            self.dpy = dpy = Xt.OpenDisplay(None, None, 'GRiNS',
                                            [], sys.argv)
        except:
            print 'Cannot open display'
            sys.exit(1)
##         dpy.Synchronize(1)
        try:
            import glX, glXconst
            visual = dpy.ChooseVisual([glXconst.GLX_RGBA,
                                       glXconst.GLX_RED_SIZE, 1,
                                       glXconst.GLX_GREEN_SIZE, 1,
                                       glXconst.GLX_BLUE_SIZE, 1])
            visuals = [visual]
        except:
            for cl, dp in tryvisuals:
                visuals = dpy.GetVisualInfo({'class': cl,
                                             'depth': dp})
                if visuals:
                    break
            else:
                raise error, 'no proper visuals available'
        self.visual = visual = visuals[0]
        self.imgformat, self.colormap, \
                        self.red_shift, self.red_mask, \
                        self.green_shift, self.green_mask, \
                        self.blue_shift, self.blue_mask = \
                                findformat(dpy, visual)
        main = Xt.CreateApplicationShell('splash', Xt.ApplicationShell,
                                         {'visual': visual,
                                          'depth': visual.depth,
                                          'colormap': self.colormap,
                                          'mappedWhenManaged': X.FALSE,
                                          'input': X.TRUE,
                                          'x': 500, 'y': 500,
                                          'width':1, 'height':1})
        main.RealizeWidget()
        self.main = main
        self.watchcursor = dpy.CreateFontCursor(Xcursorfont.watch)

    def expose(self, w, (func, args), call_data):
        apply(func, args)
        self.__exposed = 1

    def close(self):
        if not self.main or not hasattr(self, 'shell'):
            return
        self.shell.DestroyWidget()
        del self.shell
##         self.main = None

_splash = _Splash()

def init():
    _splash.wininit()
    shell = None
    if hasattr(_splash, 'shell'):
        shell = _splash.shell
        del _splash.shell
    items = _splash.__dict__.items()
    if shell:
        _splash.shell = shell
    return items

splash = _splash.splash
unsplash = _splash.close
