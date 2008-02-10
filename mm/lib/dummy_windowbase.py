__version__ = "$Id$"

error = 'windowinterface.error'
FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2
SINGLE, HTM, TEXT, MPEG = 0, 1, 2, 3

_size_cache = {}

Version = 'dummy'

from WMEVENTS import *

# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel:
    def __init__(self):
        self._closecallbacks = []
        self._subwindows = []
        self._bgcolor = 255, 255, 255 # white
        self._fgcolor =   0,   0,   0 # black
        self._hfactor = self._vfactor = 1.0
        # timer handling
        self._timers = []
        self._timer_id = 0
        self._timerfunc = None
        import time
        self._time = time.time()
        # file descriptor handlin
        self._ifddict = {}
        self._ofddict = {}

    def close(self):
        for func, args in self._closecallbacks:
            apply(func, args)
        for win in self._subwindows[:]:
            win.close()
        self.__init__()         # clears all lists

    def addclosecallback(self, func, args):
        self._closecallbacks.append((func, args))

    def newwindow(self, x, y, w, h, title, pixmap = 0):
        return _Window(self, x, y, w, h, title, 0, pixmap, 0)

    def newcmwindow(self, x, y, w, h, title, pixmap = 0):
        return _Window(self, x, y, w, h, title, 1, pixmap, 0)

    def setcursor(self, cursor):
        for win in self._subwindows:
            win.setcursor(cursor)

    def pop(self):
        pass

    def push(self):
        pass

    def mainloop(self):
        import time, select
        while 1:
            while self._timers:
                t = time.time()
                sec, cb, tid = self._timers[0]
                sec = sec - (t - self._time)
                self._time = t
                if sec <= 0:
                    del self._timers[0]
                    func, args = cb
                    apply(func, args)
                else:
                    self._timers[0] = sec, cb, tid
                    break
            ifdlist = self._ifddict.keys()
            ofdlist = self._ofddict.keys()
            if self._timers:
                timeout = self._timers[0][0]
                ifdlist, ofdlist, efdlist = select.select(
                        ifdlist, ofdlist, [], timeout)
            else:
                ifdlist, ofdlist, efdlist = select.select(
                        ifdlist, ofdlist, [])
            for fd in ifdlist:
                try:
                    func, args = self._ifddict[fd]
                except KeyError:
                    pass
                else:
                    apply(func, args)
            for fd in ofdlist:
                try:
                    func, args = self._ofddict[fd]
                except KeyError:
                    pass
                else:
                    apply(func, args)

    # timer interface
    def settimer(self, sec, cb):
        import time
        t0 = time.time()
        if self._timers:
            t, a, i = self._timers[0]
            t = t - (t0 - self._time) # can become negative
            self._timers[0] = t, a, i
        self._time = t0
        self._timer_id = self._timer_id + 1
        t = 0
        for i in range(len(self._timers)):
            time, dummy, tid = self._timers[i]
            if t + time > sec:
                self._timers[i] = (time - sec + t, dummy, tid)
                self._timers.insert(i, (sec - t, cb, self._timer_id))
                return self._timer_id
            t = t + time
        self._timers.append((sec - t, cb, self._timer_id))
        return self._timer_id

    def canceltimer(self, id):
        for i in range(len(self._timers)):
            t, cb, tid = self._timers[i]
            if tid == id:
                del self._timers[i]
                if i < len(self._timers):
                    tt, cb, tid = self._timers[i]
                    self._timers[i] = (tt + t, cb, tid)
                return

    # file descriptor interface
    def select_setcallback(self, fd, func, args, mask = ReadMask):
        if type(fd) is not type(0):
            fd = fd.fileno()
        try:
            del self._ifddict[fd]
        except KeyError:
            pass
        try:
            del self._ofddict[fd]
        except KeyError:
            pass
        if mask & ReadMask:
            if func:
                self._ifddict[fd] = func, args
        if mask & WriteMask:
            if func:
                self._ofddict[fd] = func, args

class _Window:
    def __init__(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
                    transparent = 0):
        parent._subwindows.append(self)
        self._parent = parent
        self._subwindows = []
        self._displists = []
        self._bgcolor = parent._bgcolor
        self._fgcolor = parent._fgcolor
        # conversion factors to convert from mm to relative size
        # (this uses the fact that _hfactor == _vfactor == 1.0
        # in toplevel)
        self._hfactor = parent._hfactor / w
        self._vfactor = parent._vfactor / h
        self._rect = 0, 0, w, h

    def close(self):
        if self._parent is None:
            return          # already closed
        self._parent._subwindows.remove(self)
        self._parent = None
        for win in self._subwindows[:]:
            win.close()
        for dl in self._displists[:]:
            dl.close()

    def is_closed(self):
        return self._parent is None

    def newwindow(self, (x, y, w, h), pixmap = 0, transparent = 0):
        return _Window(self, x, y, w, h, '', 0, pixmap, transparent)

    def necmwwindow(self, (x, y, w, h), pixmap = 0, transparent = 0):
        return _Window(self, x, y, w, h, '', 1, pixmap, transparent)

    def showwindow(self):
        # Highlight the window
        pass

    def dontshowwindow(self):
        # Don't highlight the window
        pass

    def fgcolor(self, color):
        r, g, b = color
        self._fgcolor = r, g, b

    def bgcolor(self, color):
        r, g, b = color
        self._bgcolor = r, g, b

    def setcursor(self, cursor):
        for win in self._subwindows:
            win.setcursor(cursor)

    def newdisplaylist(self, *bgcolor):
        if bgcolor != ():
            bgcolor = bgcolor[0]
        else:
            bgcolor = self._bgcolor
        return _DisplayList(self, bgcolor)

    def settitle(self, title):
        if self._parent is not toplevel:
            raise error, 'can only settitle at top-level'
        pass

    def getgeometry(self):
        return self._rect

    def pop(self):
        pass

    def push(self):
        pass

    def setredrawfunc(self, func):
        if func is None or callable(func):
            pass
        else:
            raise error, 'invalid function'

    def register(self, event, func, arg):
        if func is None or callable(func):
            pass
        else:
            raise error, 'invalid function'

    def unregister(self, event):
        pass

    def destroy_menu(self):
        pass

    def _image_size(self, file):
        if _size_cache.has_key(file):
            return _size_cache[file]
        import img
        try:
            reader = img.reader(None, file)
        except img.error, arg:
            raise error, arg
        width = reader.width
        height = reader.height
        _size_cache[file] = width, height
        return width, height

class _DisplayList:
    def __init__(self, window, bgcolor):
        r, g, b = bgcolor
        self._window = window
        window._displists.append(self)
        self._buttons = []

    def close(self):
        if self._window is None:
            return
        for b in self._buttons[:]:
            b.close()
        self._window._displists.remove(self)
        self._window = None

    def is_closed(self):
        return self._window is None

    def render(self):
        pass

    def fgcolor(self, color):
        r, g, b = color

    def newbutton(self, coordinates, z = 0, times = None):
        return _Button(self, coordinates)

    def display_image_from_file(self, file, crop = (0,0,0,0), fit = 'meet',
                                center = 1):
        return 0.0, 0.0, 1.0, 1.0

    def drawline(self, color, points):
        r, g, b = color
        for x, y in points:
            pass

    def drawbox(self, coordinates):
        x, y, w, h = coordinates

    def drawfbox(self, color, coordinates):
        r, g, b = color
        x, y, w, h = coordinates

    def drawmarker(self, color, coordinates):
        r, g, b = color
        x, y, w, h = coordinates

    def usefont(self, fontobj):
        self._font = fontobj
        return self.baseline(), self.fontheight(), self.pointsize()

    def setfont(self, font, size):
        return self.usefont(findfont(font, size))

    def fitfont(self, fontname, str, margin = 0):
        return self.usefont(findfont(fontname, 10))

    def baseline(self):
        return self._font.baseline() * self._window._vfactor

    def fontheight(self):
        return self._font.fontheight() * self._window._vfactor

    def pointsize(self):
        return self._font.pointsize()

    def strsize(self, str):
        width, height = self._font.strsize(str)
        return float(width) * self._window._hfactor, \
               float(height) * self._window._vfactor

    def setpos(self, x, y):
        self._curpos = x, y

    def writestr(self, str):
        x, y = self._curpos
        width, height = self.strsize(str)
        return x, y, width, height

class _Button:
    def __init__(self, dispobj, coordinates):
        x, y, w, h = coordinates
        self._dispobj = dispobj
        dispobj._buttons.append(self)

    def close(self):
        if self._dispobj is None:
            return
        self._dispobj._buttons.remove(self)
        self._dispobj = None

    def is_closed(self):
        return self._dispobj is None

    def hiwidth(self, width):
        pass

    def hicolor(self, color):
        r, g, b = color

    def highlight(self):
        pass

    def unhighlight(self):
        pass

_pt2mm = 25.4 / 72                      # 1 inch == 72 points == 25.4 mm

class findfont:
    def __init__(self, fontname, pointsize):
        self._pointsize = pointsize

    def close(self):
        pass

    def is_closed(self):
        return 0

    def strsize(self, str):
        import string
        strlist = string.splitfields(str, '\n')
        maxlen = 0
        for str in strlist:
            l = len(str)
            if l > maxlen:
                maxlen = l
        return maxlen * self._pointsize * .7 * _pt2mm, \
               len(strlist) * self.fontheight()

    def baseline(self):
        return self._pointsize * _pt2mm

    def fontheight(self):
        return self._pointsize * 1.2 * _pt2mm

    def pointsize(self):
        return self._pointsize

fonts = [
        'Times-Roman',
        'Times-Italic',
        'Times-Bold',
        'Utopia-Bold',
        'Palatino-Bold',
        'Helvetica',
        'Helvetica-Bold',
        'Helvetica-Oblique',
        'Courier',
        'Courier-Bold',
        'Courier-Oblique',
        'Courier-Bold-Oblique',
        ]

class showmessage:
    def __init__(self, text, mtype = 'message', grab = 1, callback = None,
                 cancelCallback = None, name = 'message',
                 title = 'message', parent = None):
        pass

    def close(self):
        pass

class Dialog:
    def __init__(self, list, title = None, prompt = None, grab = 1,
                 vertical = 1, parent = None):
        pass

    def close(self):
        pass

    def destroy_menu(self):
        pass

    def getbutton(self, button):
        return set

    def setbutton(self, button, onoff = 1):
        pass

class MainDialog(Dialog):
    pass

def multchoice(prompt, list, defindex, parent = None):
    return defindex

def GetYesNoCancel(prompt, parent = None):
    return multchoice(prompt, ["Yes", "No", "Cancel"], 0)

def GetOKCancel(prompt, parent = None):
    return multchoice(prompt, ["OK", "Cancel"], 0)

def beep():
    import sys
    sys.stderr.write('\7')
