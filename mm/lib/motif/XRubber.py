__version__ = "$Id$"

import Xlib, Xt, Xm, X, Xmd
from XTopLevel import toplevel
from XConstants import *
from XDialog import showmessage

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""

SELCOLOR = 255, 0, 0                    # red
SZ = 6                                  # size in pixels of dragpoints
SZ2 = SZ / 2

class _RubberBand:
    _in_create_box = None

    def create_box(self, msg, callback, box = None, units = UNIT_SCREEN, modeless = 0):
        import Xcursorfont
        if modeless:
            if not box:
                raise error, 'can only be modeless with box'
        if self._in_create_box and not self._in_create_box.is_closed():
            self._in_create_box.cancel_create_box()
        if self.is_closed():
            apply(callback, ())
            return
        _RubberBand._in_create_box = self
        self._ignore_rb = 0
        self.pop(poptop = 0)
        self.__dl = self._active_displist
        if self.__dl:
            d = self.__dl.clone()
        else:
            d = self.newdisplaylist()
        self.__transparent = []
        sw = self._subwindows[:]
        sw.reverse()
        r = Xlib.CreateRegion()
        for win in sw:
            if not win._transparent:
                # should do this recursively...
                self.__transparent.append(win)
                win._transparent = 1
                d.drawfbox(win._bgcolor, win._sizes)
                apply(r.UnionRectWithRegion, win._rect)
        for win in sw:
            b = win._sizes
            if b != (0, 0, 1, 1):
                d.drawbox(b)
        self.__display = d.clone()
        if box:
            self.__drawbox(d, SELCOLOR, box, units)
        if self.__transparent:
            self._do_expose(r)
            self.__reg = r
        d.render()
        self.__curdisp = d
        if msg:
            msg = msg + '\n\n' + _rb_message
        else:
            msg = _rb_message
        self.__callback = callback
        self.__units = units
        form = self._form
        cursor = form.Display().CreateFontCursor(Xcursorfont.crosshair)
        if not modeless:
            self.__dialog = showmessage(
                    msg, mtype = 'message', grab = 0,
                    callback = (self.__done, ()),
                    cancelCallback = (self.cancel_create_box, ()))
            self.__dialog._main.AddGrab(1, 0)
            form.AddGrab(0, 0)
            toplevel.setcursor('stop')
            self._topwindow.setcursor('')
            self.__dialog.setcursor('')
        else:
            self.__dialog = None
        form.RemoveEventHandler(X.PointerMotionMask, FALSE,
                                self._motion_handler, None)
        form.AddEventHandler(X.ButtonPressMask, FALSE,
                             self.__start, None)
        form.AddEventHandler(X.ButtonMotionMask, FALSE,
                             self.__do, None)
        form.AddEventHandler(X.ButtonReleaseMask, FALSE,
                             self.__end, None)
        form.GrabButton(X.AnyButton, X.AnyModifier, TRUE,
                        X.ButtonPressMask | X.ButtonMotionMask
                                | X.ButtonReleaseMask,
                        X.GrabModeAsync, X.GrabModeAsync, form, cursor)
        v = form.GetValues(['foreground', 'background'])
        v['foreground'] = v['foreground'] ^ v['background']
        v['function'] = X.GXxor
        v['line_style'] = X.LineOnOffDash
        self.__gc = form.GetGC(v)
        if box:
            x, y, w, h = self._convert_coordinates(box, units = units)
            if w < 0:
                x, w = x + w, -w
            if h < 0:
                y, h = y + h, -h
            self.__box = 1
            self.__start_x = x
            self.__start_y = y
            self.__width = w
            self.__height = h
        else:
            self.__start_x, self.__start_y, self.__width, \
                              self.__height = self._rect
            self.__box = 0
        self.__looping = 1
        toplevel.setready()
        if not modeless:
            while self.__looping:
                Xt.DispatchEvent(Xt.NextEvent())

    def cancel_create_box(self):
        if self._in_create_box is None:
            return
        if self._in_create_box is not self:
            raise error, 'cancel_create_box while not in create_box'
        callback = self.__callback
        self.__finish()
        apply(callback, ())
        self.__looping = 0
        _RubberBand._in_create_box = None

    # supporting methods for create_box
    def __finish(self):
        if self.__transparent:
            for win in self.__transparent:
                win._transparent = 0
            self._do_expose(self.__reg)
            del self.__reg
        del self.__transparent
        form = self._form
        form.RemoveEventHandler(X.ButtonPressMask, FALSE,
                                self.__start, None)
        form.RemoveEventHandler(X.ButtonMotionMask, FALSE,
                                self.__do, None)
        form.RemoveEventHandler(X.ButtonReleaseMask, FALSE,
                                self.__end, None)
        form.UngrabButton(X.AnyButton, X.AnyModifier)
        form.AddEventHandler(X.PointerMotionMask, FALSE,
                                self._motion_handler, None)
        if self.__dialog is not None:
            self.__dialog.close()
        if self.__dl and not self.__dl.is_closed():
            self.__dl.render()
        self.__display.close()
        self.__curdisp.close()
        toplevel.setcursor('')
        del self.__callback
        del self.__dialog
        del self.__dl
        del self.__display
        del self.__gc

    def __cvbox(self, units = UNIT_SCREEN):
        x0 = self.__start_x
        y0 = self.__start_y
        x1 = x0 + self.__width - 1
        y1 = y0 + self.__height - 1
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        x, y, width, height = self._rect
        if x0 < x: x0 = x
        if x0 >= x + width: x0 = x + width - 1
        if x1 < x: x1 = x
        if x1 >= x + width: x1 = x + width - 1
        if y0 < y: y0 = y
        if y0 >= y + height: y0 = y + height - 1
        if y1 < y: y1 = y
        if y1 >= y + height: y1 = y + height - 1
        if units == UNIT_SCREEN:
            return float(x0 - x) / width, \
                   float(y0 - y) / height, \
                   float(x1 - x0 + 1) / width, \
                   float(y1 - y0 + 1) / height
        elif units == UNIT_PXL:
            return x0 - x, y0 - y, x1 - x0 + 1, y1 - y0 + 1
        elif units == UNIT_MM:
            return float(x0 - x) / toplevel._hmm2pxl, \
                   float(y0 - y) / toplevel._vmm2pxl, \
                   float(x1 - x0 + 1) / toplevel._hmm2pxl, \
                   float(y1 - y0 + 1) / topevel._vmm2pxl
        else:
            raise error, 'bad units specified'

    def __done(self):
        _RubberBand._in_create_box = None
        callback = self.__callback
        units = self.__units
        self.__finish()
        self.__looping = 0
        apply(callback, self.__cvbox(units))

    def __draw(self):
        x = self.__start_x
        y = self.__start_y
        w = self.__width
        h = self.__height
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        self.__gc.DrawRectangle(x, y, w-1, h-1)

    def __constrain(self, event):
        x, y, w, h = self._rect
        if event.x < x:
            event.x = x
        if event.x >= x + w:
            event.x = x + w - 1
        if event.y < y:
            event.y = y
        if event.y >= y + h:
            event.y = y + h - 1

    def __common(self, event):
        try:
            cx = self.__cx
        except AttributeError:
            self.__start(None, None, event)
        if self._ignore_rb:
            return
        self.__draw()
        self.__constrain(event)
        if self.__cx and self.__cy:
            x, y, w, h = self._rect
            dx = event.x - self.__last_x
            dy = event.y - self.__last_y
            self.__last_x = event.x
            self.__last_y = event.y
            self.__start_x = self.__start_x + dx
            if self.__start_x + self.__width > x + w:
                self.__start_x = x + w - self.__width
            if self.__start_x < x:
                self.__start_x = x
            self.__start_y = self.__start_y + dy
            if self.__start_y + self.__height > y + h:
                self.__start_y = y + h - self.__height
            if self.__start_y < y:
                self.__start_y = y
        else:
            if not self.__cx:
                self.__width = event.x - self.__start_x
            if not self.__cy:
                self.__height = event.y - self.__start_y
        self.__box = 1

    def __start(self, w, data, event):
        # called on mouse press
        self._ignore_rb = 0
        self.__constrain(event)
        if self.__box:
            x = self.__start_x
            y = self.__start_y
            w = self.__width
            h = self.__height
            if w < 0:
                x, w = x + w, -w
            if h < 0:
                y, h = y + h, -h
            if self.__dialog is None:
                w2 = w/2
                h2 = h/2
                if (x <= event.x <= x + SZ or
                    x + w2 - SZ2 <= event.x <= x + w2 + SZ2 or
                    x + w - SZ <= event.x <= x + w) and \
                   (y <= event.y <= y + SZ or
                    y + h2 - SZ2 <= event.y <= y + h2 + SZ2 or
                    y + h - SZ <= event.y <= y + h):
                    self._ignore_rb = 0
                else:
                    self._ignore_rb = 1
                    return
            if x + w/4 < event.x < x + w*3/4:
                self.__cx = 1
            else:
                self.__cx = 0
                if event.x >= x + w*3/4:
                    x, w = x + w, -w
            if y + h/4 < event.y < y + h*3/4:
                self.__cy = 1
            else:
                self.__cy = 0
                if event.y >= y + h*3/4:
                    y, h = y + h, -h
            if self.__cx and self.__cy:
                self.__last_x = event.x
                self.__last_y = event.y
                self.__start_x = x
                self.__start_y = y
                self.__width = w
                self.__height = h
            else:
                if not self.__cx:
                    self.__start_x = x + w
                    self.__width = event.x - self.__start_x
                if not self.__cy:
                    self.__start_y = y + h
                    self.__height = event.y - self.__start_y
        else:
            self.__start_x = event.x
            self.__start_y = event.y
            self.__width = self.__height = 0
            self.__cx = self.__cy = 0
        self.__display.render()
        self.__curdisp.close()
        self.__draw()

    def __do(self, w, data, event):
        # called on mouse drag
        self.__common(event)
        if self._ignore_rb:
            return
        self.__draw()

    def __end(self, w, data, event):
        # called on mouse release
        self.__common(event)
        if self._ignore_rb:
            return
        self.__curdisp = d = self.__display.clone()
        self.__drawbox(self.__curdisp, SELCOLOR, self.__cvbox(units = UNIT_PXL), UNIT_PXL)
        d.render()
        del self.__cx
        del self.__cy
        if self.__dialog is None:
            self.__done()

    def __drawbox(self, d, color, box, units):
        d.fgcolor(color)
        x, y, w, h = self._convert_coordinates(box, units = units)
        rx, ry = self._rect[:2]
        x = x - rx
        y = y - ry
        w2 = w/2
        h2 = h/2
        d.drawbox((x, y, w, h), units = UNIT_PXL)
        d.drawfbox(color, (x, y, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x, y+h2-SZ2, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x, y+h-SZ, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x+w2-SZ2, y, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x+w2-SZ2, y+h2-SZ2, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x+w2-SZ2, y+h-SZ, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x+w-SZ, y, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x+w-SZ, y+h2-SZ2, SZ, SZ), units = UNIT_PXL)
        d.drawfbox(color, (x+w-SZ, y+h-SZ, SZ, SZ), units = UNIT_PXL)
        d.drawline(color, [(x,y),(x+w,y+h)], units = UNIT_PXL)
        d.drawline(color, [(x+w,y),(x,y+h)], units = UNIT_PXL)
