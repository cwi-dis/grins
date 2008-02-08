__version__ = "$Id$"

import Xlib, Xt, Xm, X, Xmd
import sys, os
import math
import string
from types import TupleType
import img, imgconvert, imgformat
import imageop
from XTopLevel import toplevel
from XConstants import *
from XConstants import _WAITING_CURSOR, _READY_CURSOR, _WIDTH, _HEIGHT
from XAdornment import _AdornmentSupport, _CommandSupport
from XRubber import _RubberBand
from XDisplist import _DisplayList
from XDialog import showmessage
from XHelpers import _create_menu, _setcursor
import ToolTip
from WMEVENTS import *
import settings
no_canvas_resize = settings.get('no_canvas_resize')

import re
dtre = re.compile(r'LPATH=(?P<lpathstart>\d+)-(?P<lpathend>\d+):(?P<value>.*)')

class _Reader:
    def __init__(self, width, height, data, reader):
        self.width = width
        self.height = height
        self.data = data
        self.format = reader.format
        self.format_choices = (reader.format,)
        if hasattr(reader, 'colormap'):
            self.colormap = reader.colormap
        if hasattr(reader, 'transparent'):
            self.transparent = reader.transparent

    def read(self):
        return self.data

# string.translate table for reversing bits in bytes
revbits = '\000\200@\300 \240`\340\020\220P\3200\260p\360\010\210H\310(\250' \
          'h\350\030\230X\3308\270x\370\004\204D\304$\244d\344\024\224T\324' \
          '4\264t\364\014\214L\314,\254l\354\034\234\\\334<\274|\374\002\202' \
          'B\302"\242b\342\022\222R\3222\262r\362\012\212J\312*\252j\352\032' \
          '\232Z\332:\272z\372\006\206F\306&\246f\346\026\226V\3266\266v\366' \
          '\016\216N\316.\256n\356\036\236^\336>\276~\376\001\201A\301!\241a' \
          '\341\021\221Q\3211\261q\361\011\211I\311)\251i\351\031\231Y\3319' \
          '\271y\371\005\205E\305%\245e\345\025\225U\3255\265u\365\015\215M' \
          '\315-\255m\355\035\235]\335=\275}\375\003\203C\303#\243c\343\023' \
          '\223S\3233\263s\363\013\213K\313+\253k\353\033\233[\333;\273{\373' \
          '\007\207G\307\'\247g\347\027\227W\3277\267w\367\017\217O\317/\257' \
          'o\357\037\237_\337?\277\177\377'

class _Window(_AdornmentSupport, _RubberBand):
    # Instances of this class represent top-level windows.  This
    # class is also used as base class for subwindows, but then
    # some of the methods are overridden.
    #
    # The following instance variables are used.  Unless otherwise
    # noted, the variables are used both in top-level windows and
    # subwindows.
    # _shell: the Xt.ApplicationShell widget used for the window
    #       (top-level windows only)
    # _form: the Xm.DrawingArea widget used for the window
    # _scrwin: the Xm.ScrolledWindow widget used for scrolling the canvas
    # _clipcanvas: the Xm.DrawingArea widget used by the Xm.ScrolledWindow
    # _colormap: the colormap used by the window (top-level
    #       windows only)
    # _visual: the visual used by the window (top-level windows
    #       only)
    # _depth: the depth of the window in pixels (top-level windows
    #       only)
    # _pixmap: if present, the backing store pixmap for the window
    # _gc: the graphics context with which the window (or pixmap)
    #       is drawn
    # _title: the title of the window (top-level window only)
    # _topwindow: the top-level window
    # _subwindows: a list of subwindows.  This list is also the
    #       stacking order of the subwindows (top-most first).
    #       This list is manipulated by the subwindow.
    # _parent: the parent window (for top-level windows, this
    #       refers to the instance of _Toplevel).
    # _displists: a list of _DisplayList instances
    # _active_displist: the currently rendered _displayList
    #       instance or None
    # _bgcolor: background color of the window
    # _fgcolor: foreground color of the window
    # _transparent: 1 if window has a transparent background (if a
    #       window is transparent, all its subwindows should also
    #       be transparent) -1 if window should be transparent if
    #       there is no active display list
    # _sizes: the position and size of the window in fractions of
    #       the parent window (subwindows only)
    # _rect: the position and size of the window in pixels
    # _region: _rect as an X Region
    # _cursor: the desired cursor shape (only has effect for
    #       top-level windows)
    # _callbacks: a dictionary with callback functions and
    #       arguments
    # _accelerators: a dictionary of accelarators
    # _menu: the pop-up menu for the window
    # _showing: 1 if a box is shown to indicate the size of the
    #       window
    # _exp_reg: a region in which the exposed area is built up
    #       (top-level window only)
    def __init__(self, parent, x, y, w, h, title, defcmap, pixmap, units,
                 adornments, canvassize, commandlist, resizable, bgcolor):
        _AdornmentSupport.__init__(self)
        menubar = toolbar = shortcuts = None
        flags = 0xffff
        if adornments is not None:
            shortcuts = adornments.get('shortcuts')
            menubar = adornments.get('menubar')
            toolbar = adornments.get('toolbar')
            toolbarvertical = adornments.get('toolbarvertical', 0)
            flags = adornments.get('flags', flags)
            close = adornments.get('close', [])
            if close:
                self._set_deletecommands(close)
        if shortcuts is not None:
            self._create_shortcuts(shortcuts)
        self._title = title
        parent._subwindows.insert(0, self)
        self._do_init(parent)
        if bgcolor is not None:
            self._bgcolor = bgcolor
        # else already inherited from parent (i.e. toplevel)
        self._topwindow = self
        self._exp_reg = Xlib.CreateRegion()

        if parent._visual.c_class == X.TrueColor:
            defcmap = FALSE
        if defcmap:
            self._colormap = parent._default_colormap
            self._visual = parent._default_visual
        else:
            self._colormap = parent._colormap
            self._visual = parent._visual
        self._depth = self._visual.depth
        # convert to pixels
        if x < 0: x = None
        if y < 0: y = None
        if units == UNIT_MM:
            if x is not None:
                x = int(float(x) * toplevel._hmm2pxl + 0.5)
            if y is not None:
                y = int(float(y) * toplevel._vmm2pxl + 0.5)
            w = int(float(w) * toplevel._hmm2pxl + 0.5)
            h = int(float(h) * toplevel._vmm2pxl + 0.5)
        elif units == UNIT_SCREEN:
            if x is not None:
                x = int(float(x) * toplevel._screenwidth + 0.5)
            if y is not None:
                y = int(float(y) * toplevel._screenheight + 0.5)
            w = int(float(w) * toplevel._screenwidth + 0.5)
            h = int(float(h) * toplevel._screenheight + 0.5)
        elif units == UNIT_PXL:
            if x is not None:
                x = int(x)
            if y is not None:
                y = int(y)
            w = int(w)
            h = int(h)
        else:
            raise error, 'bad units specified'
        if not title:
            title = ''
        attrs = {'minWidth': min(w, 60),
                 'minHeight': min(h, 60),
                 'colormap': self._colormap,
                 'visual': self._visual,
                 'depth': self._depth,
                 'title': title}
        # set the position
        if x is not None and y is not None:
            attrs['geometry'] = '+%d+%d' % (x, y)
        if title:
            attrs['iconName'] = title
        shell = parent._main.CreatePopupShell(
                'toplevelShell', Xt.TopLevelShell, attrs)
        shell.AddCallback('destroyCallback', self._destroy_callback, None)
        shell.AddWMProtocolCallback(parent._delete_window,
                                    self._delete_callback, None)
        shell.deleteResponse = Xmd.DO_NOTHING
        self._shell = shell
        attrs = {'allowOverlap': 0}
        if not resizable:
            attrs['resizePolicy'] = Xmd.RESIZE_NONE
            attrs['noResize'] = 1
            attrs['resizable'] = 0
        form = shell.CreateManagedWidget('toplevelForm', Xm.Form,
                                         attrs)
        fg = self._convert_color(self._fgcolor)
        bg = self._convert_color(self._bgcolor)
        attrs = {'height': max(h, 60),
                 'width': max(w, 60),
                 'resizePolicy': Xmd.RESIZE_NONE,
                 'background': bg,
                 'foreground': fg,
                 'borderWidth': 0,
                 'marginWidth': 0,
                 'marginHeight': 0,
                 'marginTop': 0,
                 'marginBottom': 0,
                 'shadowThickness': 0,
                 'leftAttachment': Xmd.ATTACH_FORM,
                 'rightAttachment': Xmd.ATTACH_FORM,
                 'topAttachment': Xmd.ATTACH_FORM,
                 'bottomAttachment': Xmd.ATTACH_FORM}
        self._menubar = None
        if menubar is not None:
            mattrs = {'leftAttachment': Xmd.ATTACH_FORM,
                      'rightAttachment': Xmd.ATTACH_FORM,
                      'topAttachment': Xmd.ATTACH_FORM}
            if toolbar is None and (w == 0 or h == 0):
                mattrs['bottomAttachment'] = Xmd.ATTACH_FORM
            mb = form.CreateMenuBar('menubar', mattrs)
            mb.ManageChild()
            attrs['topAttachment'] = Xmd.ATTACH_WIDGET
            attrs['topWidget'] = mb
            self._create_menu(mb, menubar, flags)
            self._menubar = mb
        self._toolbar = None
        if toolbar is not None:
            # create a XmForm widget with 2 children:
            # an XmRowColumn widget for the toolbar and an
            # XmFrame widget to fill up the space.
            # The toolbar can be horizontal or vertical
            # depending on toolbarvertical.
            fattrs = {'leftAttachment': Xmd.ATTACH_FORM}
            tbattrs = {'marginWidth': 0,
                       'marginHeight': 0,
                       'spacing': 0,
                       'leftAttachment': Xmd.ATTACH_FORM,
                       'topAttachment': Xmd.ATTACH_FORM,
                       'navigationType': Xmd.NONE,
                       }
            if w == 0 or h == 0:
                fattrs['bottomAttachment'] = Xmd.ATTACH_FORM
                fattrs['rightAttachment'] = Xmd.ATTACH_FORM
            if toolbarvertical:
                tbattrs['orientation'] = Xmd.VERTICAL
                tbattrs['rightAttachment'] = Xmd.ATTACH_FORM
                fattrs['bottomAttachment'] = Xmd.ATTACH_FORM
            else:
                tbattrs['orientation'] = Xmd.HORIZONTAL
                tbattrs['bottomAttachment'] = Xmd.ATTACH_FORM
                fattrs['rightAttachment'] = Xmd.ATTACH_FORM
            if self._menubar is not None:
                fattrs['topAttachment'] = Xmd.ATTACH_WIDGET
                fattrs['topWidget'] = self._menubar
            else:
                fattrs['topAttachment'] = Xmd.ATTACH_FORM
                attrs['topAttachment'] = Xmd.ATTACH_WIDGET
            fr = form.CreateManagedWidget('toolform', Xm.Form,
                                          fattrs)
            tb = fr.CreateManagedWidget('toolbar', Xm.RowColumn,
                                        tbattrs)
            frattrs = {'rightAttachment': Xmd.ATTACH_FORM,
                       'bottomAttachment': Xmd.ATTACH_FORM,
                       'shadowType': Xmd.SHADOW_OUT}
            if toolbarvertical:
                frattrs['leftAttachment'] = Xmd.ATTACH_FORM
                frattrs['topAttachment'] = Xmd.ATTACH_WIDGET
                frattrs['topWidget'] = tb
                attrs['leftAttachment'] = Xmd.ATTACH_WIDGET
                attrs['leftWidget'] = fr
            else:
                frattrs['leftAttachment'] = Xmd.ATTACH_WIDGET
                frattrs['leftWidget'] = tb
                frattrs['topAttachment'] = Xmd.ATTACH_FORM
                attrs['topWidget'] = fr
            void = fr.CreateManagedWidget('toolframe', Xm.Frame,
                                          frattrs)
            self._toolbar = tb
            self._create_toolbar(tb, toolbar, toolbarvertical, flags)
        if canvassize is not None and \
           (menubar is None or (w > 0 and h > 0)):
            form = form.CreateScrolledWindow('scrolledWindow',
                    {'scrollingPolicy': Xmd.AUTOMATIC,
                     'scrollBarDisplayPolicy': Xmd.STATIC,
                     'spacing': 0,
                     'width': attrs['width'],
                     'height': attrs['height'],
                     'leftAttachment': Xmd.ATTACH_FORM,
                     'rightAttachment': Xmd.ATTACH_FORM,
                     'bottomAttachment': Xmd.ATTACH_FORM,
                     'topAttachment': attrs['topAttachment'],
                     'topWidget': attrs.get('topWidget',0)})
            form.ManageChild()
            self._scrwin = form
            if not no_canvas_resize:
                for w in form.children:
                    if w.Class() == Xm.DrawingArea:
                        w.AddCallback('resizeCallback',
                                self._scr_resize_callback,
                                form)
                        self._clipcanvas = w
                        break
            width, height = canvassize
            # convert to pixels
            if units == UNIT_MM:
                width = int(float(width) * toplevel._hmm2pxl + 0.5)
                height = int(float(height) * toplevel._vmm2pxl + 0.5)
            elif units == UNIT_SCREEN:
                width = int(float(width) * toplevel._screenwidth + 0.5)
                height = int(float(height) * toplevel._screenheight + 0.5)
            elif units == UNIT_PXL:
                width = int(width)
                height = int(height)
            attrs['width'] = 0
            attrs['height'] = 0
        self.setcursor(_WAITING_CURSOR)
        if commandlist is not None:
            self.set_commandlist(commandlist)
        if menubar is not None and w == 0 or h == 0:
            # no canvas (DrawingArea) needed
            self._form = None
            shell.Popup(0)
            self._rect = self._region = \
                         self._pixmap = self._gc = None
            return
        form = form.CreateManagedWidget('toplevel',
                                        Xm.DrawingArea, attrs)
        self._form = form
        shell.Popup(0)

        val = form.GetValues(['width', 'height'])
        w, h = val['width'], val['height']
        self._rect = 0, 0, w, h
        self._region = Xlib.CreateRegion()
        apply(self._region.UnionRectWithRegion, self._rect)
        if pixmap:
            self._pixmap = form.CreatePixmap()
            gc = self._pixmap.CreateGC({'foreground': bg,
                                        'background': bg})
            gc.FillRectangle(0, 0, w, h)
        else:
            self._pixmap = None
            gc = form.CreateGC({'background': bg})
        gc.foreground = fg
        self._gc = gc
        w = float(w) / toplevel._hmm2pxl
        h = float(h) / toplevel._vmm2pxl
        form.AddCallback('exposeCallback', self._expose_callback, None)
        form.AddCallback('resizeCallback', self._resize_callback, None)
        form.AddCallback('inputCallback', self._input_callback, None)
        self._motionhandlerset = 0
        if self._scrwin is not None:
            self.setcanvassize(RESET_CANVAS)

    def _setmotionhandler(self):
        set = not self._buttonregion.EmptyRegion()
        if self._motionhandlerset == set:
            return
        if set:
            func = self._form.AddEventHandler
        else:
            func = self._form.RemoveEventHandler
        func(X.PointerMotionMask, FALSE, self._motion_handler, None)
        self._motionhandlerset = set

    def __repr__(self):
        try:
            title = `self._title`
        except AttributeError:
            title = '<NoTitle>'
        try:
            parent = self._parent
        except AttributeError:
            parent = None
        if parent is None:
            closed = ' (closed)'
        else:
            closed = ''
        return '<_Window instance at %x; title = %s%s>' % \
                                (id(self), title, closed)

    def _do_init(self, parent):
        self._parent = parent
        self._subwindows = []
        self._displists = []
        self._active_displist = None
        self._bgcolor = parent._bgcolor
        self._fgcolor = parent._fgcolor
        self._cursor = parent._cursor
        self._curcursor = ''
        self._curpos = None
        self._buttonregion = Xlib.CreateRegion()
        self._callbacks = {}
        self._accelerators = {}
        self._menu = None               # Dynamically generated popup menu (channels)
        self._popupmenu = None  # Template-based popup menu (views)
        self._transparent = 0
        self._showing = None
        self._redrawfunc = None
        self._scrwin = None     # Xm.ScrolledWindow widget if any
        self._arrowcache = {}

    def close(self):
        if self._parent is None:
            return          # already closed
        _AdornmentSupport.close(self)
        self._parent._subwindows.remove(self)
        self._parent = None
        for win in self._subwindows[:]:
            win.close()
        for dl in self._displists[:]:
            dl.close()
        if self._shell:
            self._shell.DestroyWidget()
        del self._shell
        del self._form
        del self._topwindow
        del self._gc
        del self._pixmap
        del self._arrowcache

    def is_closed(self):
        return self._parent is None

    def showwindow(self, color = (255,0,0)):
        self._showing = color
        gc = self._gc
        gc.SetClipMask(None)
        gc.foreground = self._convert_color(color)
        x, y, w, h = self._rect
        # -2 because we want the bottom and right lines just
        # inside the window
        gc.DrawRectangle(x, y, w-1, h-1)
        if self._pixmap is not None:
            x, y, w, h = self._rect
            self._pixmap.CopyArea(self._form, gc,
                                  x, y, w, h, x, y)
        toplevel._main.UpdateDisplay()

    def dontshowwindow(self):
        if self._showing:
            self._showing = None
            x, y, w, h = self._rect
            r = Xlib.CreateRegion()
            r.UnionRectWithRegion(x, y, w, h)
            r1 = Xlib.CreateRegion()
            r1.UnionRectWithRegion(x+1, y+1, w-2, h-2)
            r.SubtractRegion(r1)
            self._topwindow._do_expose(r)
            if self._pixmap is not None:
                self._gc.SetRegion(r)
                self._pixmap.CopyArea(self._form, self._gc,
                                      x, y, w, h, x, y)

    # draw XOR line from pt0 to pt1 (in pixels)
    def drawxorline(self, pt0, pt1):
        pass

    def getgeometry(self, units = UNIT_MM):
        x, y = self._shell.TranslateCoords(0, 0)
        for w in self._shell.children[0].children:
            if w.Class() == Xm.ScrolledWindow:
                val = w.GetValues(['width', 'height'])
                w = val['width']
                h = val['height']
                break
        else:
            if self._rect is None:
                w = h = 0
            else:
                w, h = self._rect[2:]
        if units == UNIT_MM:
            return float(x) / toplevel._hmm2pxl, \
                   float(y) / toplevel._vmm2pxl, \
                   float(w) / toplevel._hmm2pxl, \
                   float(h) / toplevel._vmm2pxl
        elif units == UNIT_SCREEN:
            return float(x) / toplevel._screenwidth, \
                   float(y) / toplevel._screenheight, \
                   float(w) / toplevel._screenwidth, \
                   float(h) / toplevel._screenheight
        elif units == UNIT_PXL:
            return x, y, w, h
        else:
            raise error, 'bad units specified'

    def getcanvassize(self, units = UNIT_MM):
        if self._scrwin is None:
            raise error, 'no scrollable window'
        val = self._form.GetValues(['width', 'height'])
        width = val['width']
        height = val['height']
        if units == UNIT_MM:
            return float(width) / toplevel._hmm2pxl, \
                   float(height) / toplevel._vmm2pxl
        elif units == UNIT_SCREEN:
            return float(width) / toplevel._screenwidth, \
                   float(height) / toplevel._screenheight
        elif units == UNIT_PXL:
            return width, height
        else:
            raise error, 'bad units specified'

    def setcanvassize(self, code):
        if self._scrwin is None:
            raise error, 'no scrollable window'
        # this triggers a resizeCallback
        auto = self._scrwin.scrollBarDisplayPolicy == Xmd.AS_NEEDED
        val = self._scrwin.GetValues(['width', 'height'])
        swidth = val['width'] - 4 # whence 4?
        sheight = val['height'] - 4
        clipwin = self._scrwin.clipWindow
        val = clipwin.GetValues(['width', 'height'])
        cwidth = val['width']
        cheight = val['height']
        val = self._form.GetValues(['width', 'height'])
        fwidth = val['width']
        fheight = val['height']
        vs = self._scrwin.verticalScrollBar
        hs = self._scrwin.horizontalScrollBar
        hmargin = 2 * vs.shadowThickness + vs.width
        vmargin = 2 * hs.shadowThickness + hs.height
        if not auto:
            swidth = swidth - hmargin
            sheight = sheight - vmargin
            hmargin = vmargin = 0
        forceevent = 0
        if type(code) is type(()):
            units, width, height = code
            if units == UNIT_MM:
                width = int(float(width) * toplevel._hmm2pxl + 0.5)
                height = int(float(height) * toplevel._vmm2pxl + 0.5)
            elif units == UNIT_SCREEN:
                width = int(float(width) * toplevel._screenwidth + 0.5)
                height = int(float(height) * toplevel._screenheight + 0.5)
            elif units == UNIT_PXL:
                width = int(width)
                height = int(height)
            if not no_canvas_resize:
                if width < swidth - hmargin:
                    width = swidth - hmargin
                if height < sheight - vmargin:
                    height = sheight - vmargin
            attrs = {'width': width, 'height': height}
            if width == fwidth and height == fheight:
                forceevent = 1
        elif code == RESET_CANVAS:
            attrs = {'width': swidth, 'height': sheight}
        elif code == DOUBLE_HEIGHT:
            attrs = {'height': fheight * 2}
            if auto and cwidth == fwidth:
                # there will be a vertical scrollbar
                attrs['width'] = cwidth - hmargin
        elif code == DOUBLE_WIDTH:
            attrs = {'width': fwidth * 2}
            if auto and cheight == fheight:
                # there will be a horizontal scrollbar
                attrs['height'] = cheight - vmargin
        else:
            # unrecognized code
            return
        self._form.SetValues(attrs)
        if forceevent:
            self._resize_callback(self._form, 1, None)

    def getscrollposition(self, units=UNIT_PXL):
        assert units == UNIT_PXL
        return 0, 0, 0, 0 # XXXX To be implemented

    def scrollvisible(self, coordinates, units = UNIT_SCREEN):
        if self._scrwin is None:
            raise error, 'no scrollable window'
        box = self._convert_coordinates(coordinates, units=units)
        x, y = box[:2]
        if len(box) == 2:
            w = h = 0
        else:
            w, h = box[2:4]
        vs = self._scrwin.verticalScrollBar
        hs = self._scrwin.horizontalScrollBar
        val = self._scrwin.clipWindow.GetValues(['width', 'height'])
        cwidth = val['width']
        cheight = val['height']
        val = self._form.GetValues(['width', 'height'])
        fwidth = val['width']
        fheight = val['height']
        # cwidth, cheight: size of clipping window (i.e. visible size)
        # fwidth, fheight: size of canvas (i.e. total drawable size)
        if fwidth > cwidth:
            # drawable not completely visible in X direction
            # we may need to change the scroll position
            value, slider_size, increment, page_increment = hs.ScrollBarGetValues()
            # value: x coordinate of first visible pixel
            changed = 0
            if w < cwidth:
                # horizontal extent fits
                if value <= x:
                    if x + w > value + cwidth:
                        # left visible, right not
                        value = x + w - cwidth
                        changed = 1
                else:
                    value = x
                    changed = 1
            else:
                # too wide, make left edge visible
                if value != x:
                    value = x
                    changed = 1
            if changed:
                # do it for horizontal scrollbar
                hs.ScrollBarSetValues(value, slider_size, increment, page_increment, 1)
        if fheight > cheight:
            # drawable not completely visible in Y direction
            # we may need to change the scroll position
            value, slider_size, increment, page_increment = vs.ScrollBarGetValues()
            # value: y coordinate of first visible pixel
            changed = 0
            if h < cheight:
                # vertical extent fits
                if value <= y:
                    if y + h > value + cheight:
                        # top visible, bottom not
                        value = y + h - cheight
                        changed = 1
                else:
                    value = y
                    changed = 1
            else:
                # too high, make top edge visible
                if value != y:
                    value = y
                    changed = 1
            if changed:
                # do it for vertical scrollbar
                vs.ScrollBarSetValues(value, slider_size, increment, page_increment, 1)

    def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor = None):
        return _SubWindow(self, coordinates, 0, pixmap, transparent, z, units, bgcolor)

    def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor = None):
        return _SubWindow(self, coordinates, 1, pixmap, transparent, z, units, bgcolor)

    def fgcolor(self, color):
        r, g, b = color
        self._fgcolor = r, g, b

    def bgcolor(self, color):
        if self._topwindow is self and color is None:
            color = self._topwindow._bgcolor
        if color == self._bgcolor:
            return
        self._bgcolor = color
        # set window background if nothing displayed on it
        if self._topwindow is self and not self._active_displist and \
           not self._subwindows:
            self._form.background = self._convert_color(color)
        if not self._active_displist and self._transparent == 0:
            self._gc.SetRegion(self._getmyarea())
            self._gc.foreground = self._convert_color(color)
            x, y, w, h = self._rect
            self._gc.FillRectangle(x, y, w, h)
            if self._pixmap is not None:
                self._pixmap.CopyArea(self._form, self._gc,
                                      x, y, w, h, x, y)
            # we may have overwritten our transparent children
            r = Xlib.CreateRegion()
            for w in self._subwindows:
                if w._transparent == 1 or \
                   (w._transparent == -1 and not w._active_displist):
                    apply(r.UnionRectWithRegion, w._rect)
            if not r.EmptyRegion():
                self._do_expose(r)

    def setcursor(self, cursor):
        if cursor == _WAITING_CURSOR:
            cursor = 'watch'
        elif cursor == _READY_CURSOR:
            cursor = self._cursor
        elif cursor != 'hand':
            self._cursor = cursor
        if cursor == '' and self._curpos is not None and \
           apply(self._buttonregion.PointInRegion, self._curpos):
            cursor = 'hand'
        if toplevel._waiting:
            cursor = 'watch'
        _setcursor(self._shell, cursor)
        self._curcursor = cursor

    def newdisplaylist(self, bgcolor = None, units=UNIT_SCREEN):
        return _DisplayList(self, bgcolor, units)

    def settitle(self, title):
        self._shell.SetValues({'title': title, 'iconName': title})

    def pop(self, poptop=1):
        if poptop:
            self._shell.Popup(0)

    def push(self):
        self._form.LowerWindow()

    def setredrawfunc(self, func):
        if func is None or callable(func):
            self._redrawfunc = func
        else:
            raise error, 'invalid function'

    def register(self, event, func, arg):
        if func is None or callable(func):
            pass
        else:
            raise error, 'invalid function'
        if event in (ResizeWindow, KeyboardInput, Mouse0Press,
                     Mouse0Release, Mouse1Press, Mouse1Release,
                     Mouse2Press, Mouse2Release):
            self._callbacks[event] = func, arg
        elif event == WindowExit:
            try:
                widget = self._shell
            except AttributeError:
                raise error, 'only WindowExit event for top-level windows'
            widget.deleteResponse = Xmd.DO_NOTHING
            self._callbacks[event] = func, arg
        elif event in (DropFile, DropURL):
            if not self._callbacks.has_key(DropFile) and \
               not self._callbacks.has_key(DropURL):
                args = {'importTargets':
                                [toplevel._compound_text,
                                 toplevel._netscape_url],
                        'dropSiteOperations': Xmd.DROP_COPY,
                        'dropProc': self.__handle_drop}
                if hasattr(toplevel, '_dt_netfile'):
                    args['importTargets'].append(toplevel._dt_netfile)
                self._form.DropSiteRegister(args)
            self._callbacks[event] = func, arg
        else:
            raise error, 'Internal error'

    def unregister(self, event):
        try:
            del self._callbacks[event]
        except KeyError:
            pass
        else:
            if (event == DropFile and
                not self._callbacks.has_key(DropURL)) or \
               (event == DropURL and
                not self._callbacks.has_key(DropFile)):
                self._form.DropSiteUnregister()

    def __handle_drop(self, w, client_data, drop_data):
##         print drop_data.dragContext.exportTargets
        if drop_data.dropAction != Xmd.DROP or \
           drop_data.operation != Xmd.DROP_COPY:
            args = {'transferStatus': Xmd.TRANSFER_FAILURE}
        else:
            x = drop_data.x
            y = drop_data.y
            x, y = self._pxl2rel((x, y))
            transferList = []
            args = {'dropTransfers': transferList,
                    'transferProc': self.__handle_transfer}
            if toplevel._netscape_url in drop_data.dragContext.exportTargets:
                t = toplevel._netscape_url
                if not self._callbacks.has_key(DropURL):
                    args = {'transferStatus': Xmd.TRANSFER_FAILURE}
            elif hasattr(toplevel, '_dt_netfile') and \
                 toplevel._dt_netfile in drop_data.dragContext.exportTargets:
                t = toplevel._dt_netfile
                if not self._callbacks.has_key(DropFile):
                    args = {'transferStatus': Xmd.TRANSFER_FAILURE}
            else:
                t = toplevel._compound_text
                if not self._callbacks.has_key(DropFile):
                    args = {'transferStatus': Xmd.TRANSFER_FAILURE}
            transferList.append(((x, y), t))
        drop_data.dragContext.DropTransferStart(args)

    def __handle_transfer(self, w, (x,y), seltype, type, value, length, format):
        if type == toplevel._compound_text and \
           self._callbacks.has_key(DropFile):
            func, arg = self._callbacks[DropFile]
            func(arg, self, DropFile, (x, y, value))
        elif type == toplevel._string and \
             self._callbacks.has_key(DropFile):
            func, arg = self._callbacks[DropFile]
            res = dtre.search(value)
            if res is not None:
                start, end, value = res.group('lpathstart','lpathend','value')
                start = string.atoi(start)
                end = string.atoi(end)
                filename = value[start:end+1]
                func(arg, self, DropFile, (x, y, filename))
        elif type == toplevel._netscape_url and \
             self._callbacks.has_key(DropURL):
            func, arg = self._callbacks[DropURL]
            func(arg, self, DropURL, (x, y, value))

    def destroy_menu(self):
        if self._menu:
            self._menu.DestroyWidget()
            for key in self._menuaccel:
                del self._accelerators[key]
        self._menu = None

    def hitarrow(self, point, src, dst):
        # return 1 iff (x,y) is within the arrow head
        sx, sy = self._convert_coordinates(src)
        dx, dy = self._convert_coordinates(dst)
        x, y = self._convert_coordinates(point)
        lx = dx - sx
        ly = dy - sy
        if lx == ly == 0:
            angle = 0.0
        else:
            angle = math.atan2(lx, ly)
        cos = math.cos(angle)
        sin = math.sin(angle)
        # translate
        x, y = x - dx, y - dy
        # rotate
        nx = x * cos - y * sin
        ny = x * sin + y * cos
        # test
        if ny > 0 or ny < -ARR_LENGTH:
            return FALSE
        if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
            return FALSE
        return TRUE

    def _convert_color(self, color):
        return self._parent._convert_color(color,
                self._colormap is not self._parent._colormap)

    def _convert_coordinates(self, coordinates, crop = 0, units = UNIT_SCREEN):
        """Convert fractional xywh in our space to pixel-xywh
        in toplevel-window relative pixels"""
        # convert relative sizes to pixel sizes relative to
        # upper-left corner of the window
        # if crop is set, constrain the coordinates to the
        # area of the window
        # NOTE: does not work for millimeters, only pixels/relative
        x, y = coordinates[:2]
        if len(coordinates) > 2:
            w, h = coordinates[2:]
        else:
            w, h = 0, 0
        rx, ry, rw, rh = self._rect
##         if not (0 <= x <= 1 and 0 <= y <= 1):
##             raise error, 'coordinates out of bounds'
        if units == UNIT_PXL or (units is None and type(x) is type(0)):
            px = int(x)
            dx = 0
        else:
            px = int(rw * x + 0.5)
            dx = px - rw * x
        if units == UNIT_PXL or (units is None and type(y) is type(0)):
            py = int(y)
            dy = 0
        else:
            py = int(rh * y + 0.5)
            dy = py - rh * y
        pw = ph = 0
        if crop:
            if px < 0:
                px, pw = 0, px
            if px >= rw:
                px, pw = rw - 1, px - rw + 1
            if py < 0:
                py, ph = 0, py
            if py >= rh:
                py, ph = rh - 1, py - rh + 1
        if len(coordinates) == 2:
            return px+rx, py+ry
        if units == UNIT_PXL or (units is None and type(w) is type(0)):
            pw = int(w + pw - dx)
        else:
            pw = int(rw * w + 0.5 - dx) + pw
        if units == UNIT_PXL or (units is None and type(h) is type(0)):
            ph = int(h + ph -dy)
        else:
            ph = int(rh * h + 0.5 - dy) + ph
        if crop:
            if pw <= 0:
                pw = 1
            if px + pw > rw:
                pw = rw - px
            if ph <= 0:
                ph = 1
            if py + ph > rh:
                ph = rh - py
        return px+rx, py+ry, pw, ph

    def _pxl2rel(self, coordinates):
        """Convert pixel coordinates to fractional coordinates."""
        px, py = coordinates[:2]
        rx, ry, rw, rh = self._rect
        x = float(px - rx) / rw
        y = float(py - ry) / rh
        if len(coordinates) == 2:
            return x, y
        pw, ph = coordinates[2:]
        w = float(pw) / rw
        h = float(ph) / rh
        return x, y, w, h

    def _getmyarea(self):
        # return Region that we must overwrite on expose
        region = Xlib.CreateRegion()
        apply(region.UnionRectWithRegion, self._rect)
        # subtract area children will overwrite
        for w in self._subwindows:
            region.SubtractRegion(w._getcoverarea())
        # subtract area siblings will overwrite
        while self is not self._topwindow:
            i = self._parent._subwindows.index(self)
            for w in self._parent._subwindows[:i]:
                region.SubtractRegion(w._getcoverarea())
            self = self._parent
        return region

    def _getcoverarea(self):
        # return Region that we guarantee to overwrite on expose
        r = Xlib.CreateRegion()
        if self._transparent == 0 or \
           (self._transparent == -1 and self._active_displist):
            apply(r.UnionRectWithRegion, self._rect)
            return r
        for w in self._subwindows:
            r.UnionRegion(w._getcoverarea())
        if self._active_displist:
            r.UnionRegion(self._active_displist._getcoverarea())
        return r

    def _opaque_children(self):
        r = Xlib.CreateRegion()
        for w in self._subwindows:
            if w._transparent == 0 or \
               (w._transparent == -1 and w._active_displist):
                apply(r.UnionRectWithRegion, w._rect)
            else:
                r.UnionRegion(w._opaque_children())
        return r

    def _image_size(self, file):
        try:
            xsize, ysize = toplevel._image_size_cache[file]
        except KeyError:
            try:
                reader = img.reader(None, file)
            except img.error, arg:
                raise error, arg
            xsize = reader.width
            ysize = reader.height
            toplevel._image_size_cache[file] = xsize, ysize
        return xsize, ysize

    def _prepare_image(self, file, crop, fit, center, coordinates, align, units = UNIT_SCREEN):
        # width, height: width and height of window
        # xsize, ysize: width and height of unscaled (original) image
        # w, h: width and height of scaled (final) image
        # depth: depth of window (and image) in bytes
        tw = self._topwindow
        format = toplevel._imgformat
        reader = None
        if type(file) is not type(''):
            reader = file.reader()
            xsize = reader.width
            ysize = reader.height
        elif toplevel._image_size_cache.has_key(file):
            xsize, ysize = toplevel._image_size_cache[file]
        else:
            try:
                reader = img.reader(None, file)
            except (img.error, IOError), arg:
                raise error, arg
            xsize = reader.width
            ysize = reader.height
            toplevel._image_size_cache[file] = xsize, ysize
        top, bottom, left, right = crop
        if top + bottom >= 1.0 or left + right >= 1.0 or \
           top < 0 or bottom < 0 or left < 0 or right < 0:
            raise error, 'bad crop size'
        top = int(top * ysize + 0.5)
        bottom = int(bottom * ysize + 0.5)
        left = int(left * xsize + 0.5)
        right = int(right * xsize + 0.5)
        if coordinates is None:
            x, y, width, height = self._rect
        else:
            x, y, width, height = self._convert_coordinates(coordinates, units = units)
        if fit == 'meet':
            scale = min(float(width)/(xsize - left - right),
                        float(height)/(ysize - top - bottom))
        elif fit == 'slice':
            scale = max(float(width)/(xsize - left - right),
                        float(height)/(ysize - top - bottom))
        elif fit == 'icon':
            scale = min(float(width)/(xsize - left - right),
                        float(height)/(ysize - top - bottom))
            if scale > 1:
                scale = 1
        else:
            # value not reconized. Set scale to 1
            scale = 1

        top = int(top * scale + .5)
        bottom = int(bottom * scale + .5)
        left = int(left * scale + .5)
        right = int(right * scale + .5)
        try:
            if type(file) is type(''):
                key = '%s@%f' % (`file`, scale)
            else:
                key = '%s@%f' % (file.__name__, scale)
            cfile, w, h, mask = toplevel._image_cache[key]
            if type(file) is type(''):
                image = open(cfile, 'rb').read()
            else:
                image = cfile
        except:                 # reading from cache failed
            w, h = xsize, ysize
            if not reader:
                # we got the size from the cache, don't believe it
                del toplevel._image_size_cache[file]
                return self._prepare_image(file, crop, fit, center, coordinates, align, units = units)
            if hasattr(reader, 'transparent'):
                if type(file) is type(''):
                    r = img.reader(imgformat.xrgb8, file)
                else:
                    r = imgconvert.stackreader(imgformat.xrgb8, file.reader())
                for i in range(len(r.colormap)):
                    r.colormap[i] = 255, 255, 255
                r.colormap[r.transparent] = 0, 0, 0
                image = r.read()
                if scale != 1:
                    w = int(xsize * scale + .5)
                    h = int(ysize * scale + .5)
                    image = imageop.scale(image, 1,
                                    xsize, ysize, w, h)
                bitmap = ''
                for i in range(h):
                    # grey2mono doesn't pad lines :-(
                    bitmap = bitmap + imageop.grey2mono(
                            image[i*w:(i+1)*w], w, 1, 128)
                if tw._form.Display().BitmapBitOrder() == X.LSBFirst:
                    bitmap = string.translate(bitmap, revbits)
                mask = tw._visual.CreateImage(1, X.XYPixmap, 0,
                                        bitmap, w, h, 8, 0)
                # mask.byte_order doesn't matter
            else:
                mask = None
            if scale != 1:
                try:
                    image = reader.read()
                except:
                    raise error, sys.exc_value
                w = int(xsize * scale + .5)
                h = int(ysize * scale + .5)
                descr = reader.format.descr
                imalign = descr['align'] / 8
                size = descr['size'] / 8
                rowlen = xsize*size
                rowlenpad = ((rowlen+imalign-1)/imalign)*imalign
                if rowlen != rowlenpad:
                    # imageop.scale doesn't like padding
                    nimage = []
                    for i in range(0,len(image),rowlenpad):
                        nimage.append(image[i:i+rowlen])
                    image = string.join(nimage, '')
                    del nimage
                image = imageop.scale(image, reader.format.descr['size'] / 8,
                                      xsize, ysize, w, h)
                rowlen = w*size
                rowlenpad = ((rowlen+imalign-1)/imalign)*imalign
                if rowlen != rowlenpad:
                    # put padding back but using new size
                    nimage = []
                    pad = '\0' * (rowlenpad - rowlen)
                    for i in range(0,len(image), rowlen):
                        nimage.append(image[i:i+rowlen] + pad)
                    image = string.join(nimage, '')
                    del nimage
                reader = _Reader(w, h, image, reader)
            try:
                reader = imgconvert.stackreader(format, reader)
                image = reader.read()
            except:
                raise error, sys.exc_value
            if type(file) is type(''):
                try:
                    import tempfile
                    cfile = tempfile.mktemp()
                    open(cfile, 'wb').write(image)
                    toplevel._image_cache[key] = cfile, w, h, mask
                except:
                    print 'Warning: caching image failed'
                    try:
                        os.unlink(cfile)
                    except:
                        pass
            else:
                toplevel._image_cache[key] = image, w, h, mask
        # x -- left edge of window
        # y -- top edge of window
        # width -- width of window
        # height -- height of window
        # w -- width of image
        # h -- height of image
        # left, right, top, bottom -- part to be cropped
        if align == 'topleft':
            pass
        elif align == 'centerleft':
            y = y + (height - (h - top - bottom)) / 2
        elif align == 'bottomleft':
            y = y + height - h
        elif align == 'topcenter':
            x = x + (width - (w - left - right)) / 2
        elif align == 'center':
            x, y = x + (width - (w - left - right)) / 2, \
                   y + (height - (h - top - bottom)) / 2
        elif align == 'bottomcenter':
            x, y = x + (width - (w - left - right)) / 2, \
                   y + height - h
        elif align == 'topright':
            x = x + width - w
        elif align == 'centerright':
            x, y = x + width - w, \
                   y + (height - (h - top - bottom)) / 2
        elif align == 'bottomright':
            x, y = x + width - w, \
                   y + height - h
        elif center:
            x, y = x + (width - (w - left - right)) / 2, \
                   y + (height - (h - top - bottom)) / 2
        xim = tw._visual.CreateImage(tw._visual.depth, X.ZPixmap, 0, image,
                                     w, h, format.descr['align'], 0)
        xim.byte_order = toplevel._byteorder
        return xim, mask, left, top, x-self._rect[0], y-self._rect[1], w - left - right, h - top - bottom

    def _destroy_callback(self, form, client_data, call_data):
        self._shell = None
        self.close()

    def _delete_callback(self, form, client_data, call_data):
        ToolTip.rmtt()
        self._arrowcache = {}
        if not _CommandSupport._delete_callback(self, form,
                                                client_data, call_data):
            try:
                func, arg = self._callbacks[WindowExit]
            except KeyError:
                pass
            else:
                func(arg, self, WindowExit, None)
        toplevel.setready()

    def _input_callback(self, form, client_data, call_data):
        if self._in_create_box and \
           not self._in_create_box.is_closed() and \
           self._topwindow is self._in_create_box._topwindow and \
           not self._in_create_box._ignore_rb:
            return
        ToolTip.rmtt()
        if self._parent is None:
            return          # already closed
        try:
            self._do_input_callback(form, client_data, call_data)
        except Continue:
            pass
        toplevel.setready()

    def _do_input_callback(self, form, client_data, call_data):
        event = call_data.event
        x, y = event.x, event.y
        for w in self._subwindows:
            if w._region.PointInRegion(x, y):
                try:
                    w._do_input_callback(form, client_data, call_data)
                except Continue:
                    pass
                else:
                    return
        # not in a subwindow, handle it ourselves
        if event.type == X.KeyPress:
            string = Xlib.LookupString(event)[0]
            win = self
            while win is not toplevel:
                if win._accelerators.has_key(string):
                    apply(apply, win._accelerators[string])
                    return
                win = win._parent
            try:
                func, arg = self._callbacks[KeyboardInput]
            except KeyError:
                pass
            else:
                for c in string:
                    func(arg, self, KeyboardInput, c)
        elif event.type == X.KeyRelease:
            pass
        elif event.type in (X.ButtonPress, X.ButtonRelease):
            if event.type == X.ButtonPress:
                if event.button == X.Button1:
                    ev = Mouse0Press
                elif event.button == X.Button2:
                    ev = Mouse1Press
                elif event.button == X.Button3:
                    if self._callbacks.has_key(Mouse0Press):
                        func, arg = self._callbacks[Mouse0Press]
                        x, y, width, height = self._rect
                        x = float(event.x - x) / width
                        y = float(event.y - y) / height
                        func(arg, self, Mouse2Press, (x, y, [], ''))
                    menu = self._menu or self._popupmenu
                    if menu:
                        menu.MenuPosition(event)
                        menu.ManageChild()
                        return
                    ev = Mouse2Press
                else:
                    return  # unsupported mouse button
            else:
                if event.button == X.Button1:
                    ev = Mouse0Release
                elif event.button == X.Button2:
                    ev = Mouse1Release
                elif event.button == X.Button3:
                    if self._menu:
                        # ignore buttonrelease
                        # when we have a menu
                        return
                    ev = Mouse2Release
                else:
                    return  # unsupported mouse button
            try:
                func, arg = self._callbacks[ev]
            except KeyError:
                return
            x, y, width, height = self._rect
            x = float(event.x - x) / width
            y = float(event.y - y) / height
            buttons = []
            adl = self._active_displist
            if adl:
                for but in adl._buttons:
                    if but._inside(x, y):
                        buttons.append(but)
            func(arg, self, ev, (x, y, buttons, ''))
        else:
            print 'unknown event',`event.type`

    def _expose_callback(self, form, client_data, call_data):
        # no _setcursor during expose!
        if self._parent is None:
            return          # already closed
        e = call_data.event
        # collect redraw regions
        self._exp_reg.UnionRectWithRegion(e.x, e.y, e.width, e.height)
        if e.count == 0:
            # last of a series, do the redraw
            r = self._exp_reg
            self._exp_reg = Xlib.CreateRegion()
            pm = self._pixmap
            if pm is None:
                self._do_expose(r)
            else:
                self._gc.SetRegion(r)
                x, y, w, h = self._rect
                pm.CopyArea(form, self._gc, x, y, w, h, x, y)

    def _do_expose(self, region, recursive = 0, transparent = 1):
        if self._parent is None:
            return
        # check if there is any overlap of our window with the
        # area to be drawn
        r = Xlib.CreateRegion()
        r.UnionRegion(self._region)
        r.IntersectRegion(region)
        if r.EmptyRegion():
            # no overlap
            return
        # first redraw opaque subwindow, top-most first
        for w in self._subwindows:
            w._do_expose(region, 1, 0)
        if not transparent and \
           (self._transparent == 1 or
            (self._transparent == -1 and not self._active_displist)):
            return
        # then draw background window
        r = self._getmyarea()
        r.IntersectRegion(region)
        if not r.EmptyRegion():
            if not recursive and \
               (self._transparent == 1 or
                (self._transparent == -1 and
                 not self._active_displist)):
                self._parent._do_expose(r)
            elif self._active_displist:
                self._active_displist._render(r)
            elif self._bgcolor is not None: # not tranparent
                gc = self._gc
                gc.SetRegion(r)
                gc.foreground = self._convert_color(self._bgcolor)
                apply(gc.FillRectangle, self._rect)
            if self._redrawfunc:
                self._gc.SetRegion(r)
                self._redrawfunc()
        # finally draw transparent subwindow, bottom-most first
        sw = self._subwindows[:]
        sw.reverse()
        for w in sw:
            if w._transparent == 1 or \
               (w._transparent == -1 and not w._active_displist):
                w._do_expose(region, 1)
        if self._showing:
            self.showwindow(self._showing)

    def _scr_resize_callback(self, w, form, call_data):
        ToolTip.rmtt()
        if self.is_closed():
            return
        width = max(self._form.width, w.width)
        height = max(self._form.height, w.height)
        self._form.SetValues({'width': width, 'height': height})

    def _resize_callback(self, form, client_data, call_data):
        ToolTip.rmtt()
        val = self._form.GetValues(['width', 'height'])
        x, y = self._rect[:2]
        width, height = val['width'], val['height']
        if self._rect == (x, y, width, height) and client_data is None:
            return
        self._arrowcache = {}
        self._rect = x, y, width, height
        self._region = Xlib.CreateRegion()
        apply(self._region.UnionRectWithRegion, self._rect)
        # convert pixels to mm
        w = float(width) / toplevel._hmm2pxl
        h = float(height) / toplevel._vmm2pxl
        if self._pixmap is None:
            pixmap = None
        else:
            pixmap = form.CreatePixmap()
            self._pixmap = pixmap
            bg = self._convert_color(self._bgcolor)
            gc = pixmap.CreateGC({'foreground': bg,
                                  'background': bg})
            self._gc = gc
            gc.FillRectangle(0, 0, w, h)
        for d in self._displists[:]:
            d.close()
        for w in self._subwindows:
            w._do_resize1()
        self._do_expose(self._region)
        if pixmap is not None:
            gc.SetRegion(self._region)
            pixmap.CopyArea(form, gc, 0, 0, width, height, 0, 0)
        # call resize callbacks
        self._do_resize2()
        toplevel.setready()

    def _do_resize2(self):
        for w in self._subwindows:
            w._do_resize2()
        try:
            func, arg = self._callbacks[ResizeWindow]
        except KeyError:
            pass
        else:
            func(arg, self, ResizeWindow, None)

    def _motion_handler(self, form, client_data, event):
        x, y = self._curpos = event.x, event.y
        if self._buttonregion.PointInRegion(x, y):
            cursor = 'hand'
        else:
            cursor = self._cursor
        if self._curcursor != cursor:
            self.setcursor(cursor)

    def updatebgcolor(self, color):
        self.bgcolor(color)
        if self._active_displist:
            self._do_expose(self._getmyarea())

    # transition interface, placeholder

    def begintransition(self, inout, runit, dict, cb):
        print 'Transition', dict['trtype']
        if cb:
            apply(apply, cb)

    def endtransition(self):
        pass

    def jointransition(self, window, cb):
        pass

    def changed(self):
        pass

    def settransitionvalue(self, value):
        pass

    def freeze_content(self, how):
        # how is 'transition', 'hold' or None. Freeze the bits in the window
        # (unless how=None, which unfreezes them) and use for updates and as passive
        # source for next transition.
        pass

class _SubWindow(_Window):
    def __init__(self, parent, coordinates, defcmap, pixmap, transparent, z, units, bgcolor):
        self._z = z
        x, y, w, h = parent._convert_coordinates(coordinates, crop = 1, units = units)
        self._rect = x, y, w, h
        self._sizes = parent._pxl2rel(self._rect)
        if w == 0 or h == 0:
            showmessage('Creating subwindow with zero dimension',
                        mtype = 'warning', parent = parent)

        self._convert_color = parent._convert_color
        for i in range(len(parent._subwindows)):
            if z >= parent._subwindows[i]._z:
                parent._subwindows.insert(i, self)
                break
        else:
            parent._subwindows.append(self)
        self._do_init(parent)
        if transparent == 1:
            self._bgcolor = None
        if bgcolor is not None:
            self._bgcolor = bgcolor
        self._motion_handler = parent._motion_handler
        if transparent not in (-1, 0, 1):
            raise error, 'invalid value for transparent arg'
        self._transparent = transparent
        self._topwindow = parent._topwindow

        self._form = parent._form
        self._gc = parent._gc
        self._visual = parent._visual
        self._colormap = parent._colormap
        self._pixmap = parent._pixmap

        self._region = Xlib.CreateRegion()
        apply(self._region.UnionRectWithRegion, self._rect)
        if self._transparent == 0:
            self._do_expose(self._region)
            if self._pixmap is not None:
                x, y, w, h = self._rect
                self._gc.SetRegion(self._region)
                self._pixmap.CopyArea(self._form, self._gc,
                                      x, y, w, h, x, y)

    def __repr__(self):
        return '<_SubWindow instance at %x>' % id(self)

    def close(self):
        parent = self._parent
        if parent is None:
            return          # already closed
        self._parent = None
        parent._subwindows.remove(self)
        for win in self._subwindows[:]:
            win.close()
        for dl in self._displists[:]:
            dl.close()
        parent._do_expose(self._region)
        if self._pixmap is not None:
            x, y, w, h = self._rect
            self._gc.SetRegion(self._region)
            self._pixmap.CopyArea(self._form, self._gc,
                                  x, y, w, h, x, y)
        del self._pixmap
        del self._form
        del self._topwindow
        del self._region
        del self._gc
        del self._convert_color
        del self._motion_handler
        del self._arrowcache

    def settitle(self, title):
        raise error, 'can only settitle at top-level'

    def getgeometry(self, units = UNIT_SCREEN):
        if units == UNIT_PXL:
            return self._rect
        elif units == UNIT_SCREEN:
            return self._sizes
        elif units == UNIT_MM:
            x, y, w, h = self._rect
            return float(x) / toplevel._hmm2pxl, \
                   float(y) / toplevel._vmm2pxl, \
                   float(w) / toplevel._hmm2pxl, \
                   float(h) / toplevel._vmm2pxl
        raise error, 'bad units specified'

    def setcursor(self, cursor):
        pass

    def pop(self, poptop=1):
        parent = self._parent
        # put self in front of all siblings with equal or lower z
        if self is not parent._subwindows[0]:
            parent._subwindows.remove(self)
            for i in range(len(parent._subwindows)):
                if self._z >= parent._subwindows[i]._z:
                    parent._subwindows.insert(i, self)
                    break
            else:
                parent._subwindows.append(self)
            # draw the window's contents
            if self._transparent == 0 or self._active_displist:
                self._do_expose(self._region)
                if self._pixmap is not None:
                    x, y, w, h = self._rect
                    self._gc.SetRegion(self._region)
                    self._pixmap.CopyArea(self._form,
                                          self._gc,
                                          x, y, w, h, x, y)
        parent.pop(poptop)

    def push(self):
        parent = self._parent
        # put self behind all siblings with equal or higher z
        if self is parent._subwindows[-1]:
            # already at the end
            return
        parent._subwindows.remove(self)
        for i in range(len(parent._subwindows)-1,-1,-1):
            if self._z <= parent._subwindows[i]._z:
                parent._subwindows.insert(i+1, self)
                break
        else:
            parent._subwindows.insert(0, self)
        # draw exposed windows
        for w in self._parent._subwindows:
            if w is not self:
                w._do_expose(self._region)
        if self._pixmap is not None:
            x, y, w, h = self._rect
            self._gc.SetRegion(self._region)
            self._pixmap.CopyArea(self._form, self._gc,
                                  x, y, w, h, x, y)

    def _do_resize1(self):
        # calculate new size of subwindow after resize
        # close all display lists
        parent = self._parent
        self._pixmap = parent._pixmap
        self._gc = parent._gc
        x, y, w, h = parent._convert_coordinates(self._sizes, crop = 1)
        if (x, y, w, h) == self._rect:
            # no change
            return
        self._rect = x, y, w, h
        w, h = self._sizes[2:]
        if w == 0:
            w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
        if h == 0:
            h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
        self._region = Xlib.CreateRegion()
        apply(self._region.UnionRectWithRegion, self._rect)
        self._active_displist = None
        for d in self._displists[:]:
            d.close()
        for w in self._subwindows:
            w._do_resize1()

    # Experimental animation interface
    def updatecoordinates(self, coordinates, units=UNIT_SCREEN, fit=None, mediacoords=None):
        parent = self._parent

        # first convert any coordinates to pixel
        coordinates = parent._convert_coordinates(coordinates,units=units)
        x, y = coordinates[:2]

        # move or/and resize window
        if len(coordinates)==2:
            w, h = self._rect[2:]
        elif len(coordinates)==4:
            w, h = coordinates[2:]
        else:
            raise error, 'invalid value for coordinates arg'

        px, py, pw, ph = parent._rect
        if x + w > px + pw:
            w = px + pw - x
        if y + h > py + ph:
            h = py + ph - y

        if (x, y, w, h) == self._rect:
            # nothing to do
            return

        r = Xlib.CreateRegion()
        r.UnionRegion(self._region)

        if (w,h) != self._rect[2:]:
            # resize
            resize = 1
            self._rect = x, y, w, h
            self._sizes = self._parent._pxl2rel(self._rect)
            self._region = Xlib.CreateRegion()
            apply(self._region.UnionRectWithRegion, self._rect)
            for d in self._displists[:]:
                d.close()
            for win in self._subwindows:
                win._do_resize1()
        else:
            resize = 0
            self._updcoords((x,y,w,h))

        r.UnionRegion(self._region)
        parent._do_expose(r)
        if resize:
            # call callback functions
            self._do_resize2()

    def _updcoords(self, coordinates):
        x, y, w, h = coordinates
        # do move
        ox, oy, ow, oh = self._rect
        self._rect = x, y, w, h
        self._sizes = self._parent._pxl2rel(self._rect)
        self._region = Xlib.CreateRegion()
        apply(self._region.UnionRectWithRegion, self._rect)
        for win in self._subwindows:
            sx, sy = win._rect[:2]
            win._updcoords((sx + x - ox, sy + y - oy, w, h))

    def updatezindex(self, z):
        self._z = z
        # do reorder subwindows
        print 'window.updatezindex',z

        parent = self._parent
        parent._subwindows.remove(self)
        for i in range(len(parent._subwindows)):
            if z >= parent._subwindows[i]._z:
                parent._subwindows.insert(i, self)
                break
        else:
            parent._subwindows.append(self)
        parent._do_expose(self._region)
