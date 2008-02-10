__version__ = "$Id$"

import Xt
from types import IntType
from XConstants import TRUE, FALSE, UNIT_MM, SINGLE, ReadMask, WriteMask, \
     _WAITING_CURSOR, _READY_CURSOR, error

class _Timer:
    def set(self, id):
        self.__id = id

    def get(self):
        return self.__id

    def destroy(self):
        self.__id = None

    def cb(self, client_data, id):
        self.__id = None
        apply(apply, client_data)
        toplevel.setready()

# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel:
    # this is a hack to delay initialization of the Toplevel until
    # we actually need it.
    __initialized = 0

    def __getattr__(self, attr):
        if not _Toplevel.__initialized:
            self._do_init()
            try:
                return self.__dict__[attr]
            except KeyError:
                pass
        raise AttributeError(attr)

    def __init__(self):
        if _Toplevel.__initialized:
            raise error, 'only one Toplevel allowed'
        _Toplevel.__initialize = 1

    def _do_init(self):
        import Xcursorfont, splash
        if _Toplevel.__initialized:
            raise error, 'can only initialize once'
        _Toplevel.__initialized = 1
        self._closecallbacks = []
        self._subwindows = []
        self._bgcolor = 255, 255, 255 # white
        self._fgcolor =   0,   0,   0 # black
        self._cursor = ''
        self._image_size_cache = {}
        self._image_cache = {}
        self._cm_cache = {}
        self._immediate = []
        # file descriptor handling
        self._fdiddict = {}
        items = splash.init()
        for key, val in items:
            setattr(self, '_' + key, val)
        dpy = self._dpy
        main = self._main
        self._delete_window = dpy.InternAtom('WM_DELETE_WINDOW', FALSE)
        self._compound_text = dpy.InternAtom('COMPOUND_TEXT', FALSE)
        self._netscape_url = dpy.InternAtom('_NETSCAPE_URL', FALSE)
        dt_netfile = dpy.InternAtom('_DT_NETFILE', TRUE)
        if dt_netfile:
            toplevel._dt_netfile = dt_netfile
        self._string = dpy.InternAtom('STRING', FALSE)
        self._default_colormap = main.DefaultColormapOfScreen()
        self._default_visual = main.DefaultVisualOfScreen()
##         self._default_colormap = self._colormap
##         self._default_visual = self._visual
        self._mscreenwidth = main.WidthMMOfScreen()
        self._mscreenheight = main.HeightMMOfScreen()
        self._screenwidth = main.WidthOfScreen()
        self._screenheight = main.HeightOfScreen()
        self._hmm2pxl = float(self._screenwidth) / self._mscreenwidth
        self._vmm2pxl = float(self._screenheight) / self._mscreenheight
        self._dpi_x = int(25.4 * self._hmm2pxl + .5)
        self._dpi_y = int(25.4 * self._vmm2pxl + .5)
        self._handcursor = dpy.CreateFontCursor(Xcursorfont.hand2)
        self._watchcursor = dpy.CreateFontCursor(Xcursorfont.watch)
        self._channelcursor = dpy.CreateFontCursor(Xcursorfont.draped_box)
        self._linkcursor = dpy.CreateFontCursor(Xcursorfont.hand1)
        self._stopcursor = dpy.CreateFontCursor(Xcursorfont.pirate)
        main.RealizeWidget()

    def close(self):
        for cb in self._closecallbacks:
            apply(apply, cb)
        for win in self._subwindows[:]:
            win.close()
        self._closecallbacks = []
        self._subwindows = []
        import os
        for entry in self._image_cache.values():
            try:
                os.unlink(entry[0])
            except:
                pass
        self._image_cache = {}

    def addclosecallback(self, func, args):
        self._closecallbacks.append((func, args))

    def newwindow(self, x, y, w, h, title,
                  pixmap = 0, units = UNIT_MM,
                  adornments = None, canvassize = None,
                  commandlist = None, resizable = 1, bgcolor = None):
        from XWindow import _Window
        return _Window(self, x, y, w, h, title, 0, pixmap, units,
                       adornments, canvassize, commandlist, resizable,
                       bgcolor)

    def newcmwindow(self, x, y, w, h, title,
                    pixmap = 0, units = UNIT_MM,
                    adornments = None, canvassize = None,
                    commandlist = None, resizable = 1, bgcolor = None):
        from XWindow import _Window
        return _Window(self, x, y, w, h, title, 1, pixmap, units,
                       adornments, canvassize, commandlist, resizable,
                       bgcolor)

    _waiting = 0
    def setwaiting(self):
        self._waiting = 1
        self.setcursor(_WAITING_CURSOR)

    def setready(self):
        self._waiting = 0
        self.setcursor(_READY_CURSOR)

    def setcursor(self, cursor):
        for win in self._subwindows:
            win.setcursor(cursor)
        if cursor != _WAITING_CURSOR and cursor != _READY_CURSOR:
            self._cursor = cursor
        self._main.Display().Flush()

    def pop(self):
        pass

    def push(self):
        pass

    def mainloop(self):
        self.setready()
        Xt.MainLoop()

    # timer interface
    def settimer(self, sec, cb):
        if __debug__:
            # sanity check
            func, args = cb
            if not callable(func):
                raise error, 'callback function not callable'
        id = _Timer()
        tid = Xt.AddTimeOut(int(sec * 1000), id.cb, cb)
        id.set(tid)
        return id

    def canceltimer(self, id):
        if id is not None:
            tid = id.get()
            if tid is not None:
                Xt.RemoveTimeOut(tid)
            else:
                print 'canceltimer of bad timer'
            id.destroy()

    # file descriptor interface
    def select_setcallback(self, fd, func, args, mask = ReadMask):
        import Xtdefs
        if type(fd) is not IntType:
            fd = fd.fileno()
        if self._fdiddict.has_key(fd):
            id = self._fdiddict[fd]
            Xt.RemoveInput(id)
            del self._fdiddict[fd]
        if func is None:
            return
        xmask = 0
        if mask & ReadMask:
            xmask = xmask | Xtdefs.XtInputReadMask
        if mask & WriteMask:
            xmask = xmask | Xtdefs.XtInputWriteMask
        self._fdiddict[fd] = Xt.AddInput(fd, xmask,
                                         self._input_callback,
                                         (func, args))

    def _input_callback(self, client_data, fd, id):
        apply(apply, client_data)

    def _convert_color(self, color, defcm):
        r, g, b = color
        if defcm:
            if self._cm_cache.has_key(`r,g,b`):
                return self._cm_cache[`r,g,b`]
            ri = int(r / 255.0 * 65535.0)
            gi = int(g / 255.0 * 65535.0)
            bi = int(b / 255.0 * 65535.0)
            cm = self._default_colormap
            try:
                color = cm.AllocColor(ri, gi, bi)
            except RuntimeError:
                # can't allocate color; find closest one
                m = 0
                color = None
                # use floats to guard against overflow
                rf = float(ri)
                gf = float(gi)
                bf = float(bi)
                for c in cm.QueryColors(range(256)):
                    # calculate distance
                    d = (rf-c[1])*(rf-c[1]) + \
                        (gf-c[2])*(gf-c[2]) + \
                        (bf-c[3])*(bf-c[3])
                    if color is None or d < m:
                        # found one that's closer
                        m = d
                        color = c
                color = self._colormap.AllocColor(color[1],
                                        color[2], color[3])
                print "Warning: colormap full, using 'close' color",
                print 'original:',`r,g,b`,'new:',`int(color[1]/65535.0*255.0),int(color[2]/65535.0*255.0),int(color[3]/65535.0*255.0)`
            # cache the result
            self._cm_cache[`r,g,b`] = color[0]
            return color[0]
        r = int(float(r) / 255. * float(self._red_mask) + .5)
        g = int(float(g) / 255. * float(self._green_mask) + .5)
        b = int(float(b) / 255. * float(self._blue_mask) + .5)
        c = (r << self._red_shift) | \
            (g << self._green_shift) | \
            (b << self._blue_shift)
        return c

    def getscreensize(self):
        """Return screen size in pixels"""
        return self._screenwidth, self._screenheight

    def getsize(self):
        return self._mscreenwidth, self._mscreenheight

    def getscreendepth(self):
        """Return screen depth"""
        return self._visual.depth

toplevel = _Toplevel()

newwindow = toplevel.newwindow
newcmwindow = toplevel.newcmwindow
close = toplevel.close
addclosecallback = toplevel.addclosecallback
setcursor = toplevel.setcursor
setwaiting = toplevel.setwaiting
getsize = toplevel.getsize
settimer = toplevel.settimer
select_setcallback = toplevel.select_setcallback
mainloop = toplevel.mainloop
canceltimer = toplevel.canceltimer
getscreensize = toplevel.getscreensize
getscreendepth = toplevel.getscreendepth
