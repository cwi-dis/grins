__version__ = "$Id$"

# app constants
from appcon import *
from WMEVENTS import *

#
import base_window

class Region(base_window.Window):
    def __init__(self, parent, coordinates, transparent, z, units, bgcolor):
        base_window.Window.__init__(self)

        # create the window
        self.create(parent, coordinates, units, z, transparent, bgcolor)

    def __repr__(self):
        return '<Region instance at %x>' % id(self)

    def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
        return Region(self, coordinates, transparent, z, units, bgcolor)

    def close(self):
        if self._parent is None:
            return
        if self._transition:
            self._transition.endtransition()
        self._parent._subwindows.remove(self)
        self.updateMouseCursor()
        self._parent.update()
        self._parent = None
        for win in self._subwindows[:]:
            win.close()
        for dl in self._displists[:]:
            dl.close()
        del self._topwindow
        del self._convert_color
        del self._transition

## ###########################

class Viewport(Region):
    def __init__(self, context, coordinates, bgcolor):
        Region.__init__(self, None, coordinates, 0, 0, UNIT_PXL, bgcolor)

        # adjust some variables
        self._topwindow = self

        # viewport context (usually an os window)
        self._ctx = context

    def __repr__(self):
        return '<Viewport instance at %x>' % id(self)

    def _convert_color(self, color):
        return color

    def getwindowpos(self, rel=None):
        return self._rectb

    def pop(self, poptop = 1):
        pass

    def setcursor(self, strid):
        pass
##         print 'Viewport.setcursor', strid

    def close(self):
        if self._ctx is None:
            return
        for win in self._subwindows[:]:
            win.close()
        for dl in self._displists[:]:
            dl.close()
        del self._topwindow
        self._ctx = None

    def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
        return Region(self, coordinates, transparent, z, units, bgcolor)
    newcmwindow = newwindow

    #
    # Query section
    #
    def is_closed(self):
        return self._ctx is None

    def getContext(self):
        return self._ctx

    #
    # Painting section
    #
    def getBackBuffer(self):
        return None

    #
    # Mouse section
    #
    def updateMouseCursor(self):
        pass
##         print 'Viewport.updateMouseCursor'

    def onMouseEvent(self, point, event, params=None):
        for w in self._subwindows:
            if w.inside(point):
                if event == Mouse0Press:
                    w._onlbuttondown(point)
                elif event == Mouse0Release:
                    w._onlbuttonup(point)
                break
        return Region.onMouseEvent(self, point, event)

    def onMouseMove(self, point, params=None):
        # check subwindows first
        for w in self._subwindows:
            if w.inside(point):
                w._onmousemove(point)
                if w.setcursor_from_point(point):
                    return

        # not in a subwindow, handle it ourselves
        if self._active_displist:
            x, y, w, h = self.getwindowpos()
            xp, yp = point
            point = xp-x, yp-y
            x, y = self._pxl2rel(point,self._canvas)
            for button in self._active_displist._buttons:
                if button._inside(x,y):
                    self.setcursor('hand')
                    return
        self.setcursor(self._cursor)
