__version__ = "$Id$"

import Xlib, X
import string, math
from types import ListType
RegionType = type(Xlib.CreateRegion())
from XTopLevel import toplevel
from XConstants import TRUE, FALSE, error, ARR_HALFWIDTH, ARR_LENGTH, UNIT_SCREEN, UNIT_PXL
from XFont import findfont
from XButton import _Button, _ButtonRect, _ButtonPoly, _ButtonCircle
from splash import roundi

# mapping from icon name to module
_iconmap = {
        '': 'emptyicon',
        'ref': 'reficon',
        'text': 'texticon',
        'html': 'texticon',
        'image': 'imageicon',
        'video': 'videoicon',
        'sound': 'soundicon',
        'audio': 'soundicon',
        'animation': 'animationicon',
        'svg': 'animationicon',
        'browseranchor': 'browseranchoricon',
        'contextanchor': 'contextanchoricon',
        'node': 'nodeicon',
        'imm': 'nodeicon',
        'ext': 'nodeicon',
        'animate': 'animateicon',
        'brush': 'brushicon',
        'mediaopen': 'mediaopenicon',
        'media': 'mediaopenicon',
        'mediaclosed': 'mediaclosedicon',
        'paropen': 'paropenicon',
        'par': 'paropenicon',
        'parclosed': 'parclosedicon',
        'seqopen': 'seqopenicon',
        'seq': 'seqopenicon',
        'seqclosed': 'seqclosedicon',
        'exclopen': 'exclopenicon',
        'excl': 'exclopenicon',
        'exclclosed': 'exclclosedicon',
        'switchopen': 'switchopenicon',
        'switch': 'switchopenicon',
        'switchclosed': 'switchclosedicon',
        'prioopen': 'prioopenicon',
        'prio': 'prioopenicon',
        'prioclosed': 'prioclosedicon',
        'viewport': 'viewporticon',
        'region': 'regionicon',
        'closed': 'closedicon',
        'open': 'openicon',
        'bandwidthgood': 'bandwidthgoodicon',
        'bandwidthbad': 'bandwidthbadicon',
        'error': 'erroricon',
        'linksrc': 'linksrcicon',
        'anchor': 'linksrcicon',
        'linkdst': 'linkdsticon',
        'danglingevent': 'danglingeventicon',
        'danglinganchor': 'danglinganchoricon',
        'transin': 'transinicon',
        'transout': 'transouticon',
        'beginevent': 'begineventicon',
        'endevent': 'endeventicon',
        'activateevent': 'activateeventicon',
        'causeevent': 'causeeventicon',
        'duration': 'durationicon',
        'focusin': 'focusinicon',
        'happyface': 'happyfaceicon',
        'repeat': 'repeaticon',
        'wallclock': 'wallclockicon',
        'pausing': 'pausingicon',
        'waitstop': 'waitstopicon',
        'idle': 'idleicon',
        'properties': 'propertiesicon',
        'unknown': 'unknownicon',
        }

class _DisplayList:
    def __init__(self, window, bgcolor, units):
        self.__units = units
        self.starttime = 0
        self._window = window
        window._displists.append(self)
        self._buttons = []
        self._buttonregion = Xlib.CreateRegion()
        self._fgcolor = window._fgcolor
        self._bgcolor = bgcolor
        self._linewidth = 1
        self._gcattr = {'foreground': window._convert_color(self._fgcolor),
                        'line_width': 1}
        self._list = []
        self._list.append(('clear',))
        self._optimdict = {}
        self._cloneof = None
        self._clonestart = 0
        self._rendered = FALSE
        self._font = None
        self._imagemask = None
        self._coverarea = Xlib.CreateRegion()

        # associate cmd names with list indices
        # used by animation experimental methods
        self.__cmddict = {}
        self.__butdict = {}

    def close(self):
        win = self._window
        if win is None:
            return
        for b in self._buttons[:]:
            b.close()
        win._displists.remove(self)
        self._window = None
        for d in win._displists:
            if d._cloneof is self:
                d._cloneof = None
        if win._active_displist is self:
            win._active_displist = None
            win._buttonregion = Xlib.CreateRegion()
            r = win._region
            if win._transparent == -1 and win._parent is not None and \
               win._topwindow is not win:
                win._parent._do_expose(r)
            else:
                win._do_expose(r)
            if win._pixmap is not None:
                x, y, w, h = win._rect
                win._gc.SetRegion(win._region)
                win._pixmap.CopyArea(win._form, win._gc,
                                     x, y, w, h, x, y)
            w = win._parent
            if win._transparent == 0 and w is not None:
                region = win._getmyarea()
                while w is not None and w is not toplevel:
                    w._buttonregion.SubtractRegion(
                            region)
                    w = w._parent
            win._topwindow._setmotionhandler()
        del self._cloneof
        del self._optimdict
        del self._list
        del self._buttons
        del self._font
        del self._imagemask
        del self._buttonregion
        del self._coverarea

    def is_closed(self):
        return self._window is None

    def clone(self):
        w = self._window
        new = _DisplayList(w, self._bgcolor, self.__units)
        # copy all instance variables
        new._list = self._list[:]
        new._font = self._font
        new._coverarea = Xlib.CreateRegion()
        new._coverarea.UnionRegion(self._coverarea)
        if self._rendered:
            new._cloneof = self
            new._clonestart = len(self._list)
            new._imagemask = self._imagemask
        for key, val in self._optimdict.items():
            new._optimdict[key] = val
        return new

    def render(self):
        import time
        self.starttime = time.time()
        window = self._window
        if window._transparent == -1 and window._active_displist is None:
            window._active_displist = self
            window._active_displist = None
        for b in self._buttons:
            b._highlighted = 0
        # figure out which part we must write
        region = window._getmyarea()
        # draw our bit
        self._render(region)
        # now draw transparent subwindows
        windows = window._subwindows[:]
        windows.reverse()
        for w in windows:
            if w._transparent and w._active_displist:
                w._do_expose(region, 1)
        # now draw transparent windows that lie on top of us
        if window._topwindow is not window:
            i = window._parent._subwindows.index(window)
            windows = window._parent._subwindows[:i]
            windows.reverse()
            for w in windows:
                if w._transparent and w._active_displist:
                    w._do_expose(region, 1)
        # finally, re-highlight window
        if window._showing:
            window.showwindow(window._showing)
        if window._pixmap is not None:
            x, y, width, height = window._rect
            window._gc.SetRegion(region)
            window._pixmap.CopyArea(window._form, window._gc,
                                    x, y, width, height, x, y)
        window._buttonregion = bregion = Xlib.CreateRegion()
        bregion.UnionRegion(self._buttonregion)
        bregion.IntersectRegion(region)
        w = window._parent
        while w is not None and w is not toplevel:
            w._buttonregion.SubtractRegion(region)
            w._buttonregion.UnionRegion(bregion)
            w = w._parent
        window._topwindow._setmotionhandler()
        toplevel._main.UpdateDisplay()

    def _render(self, region):
        self._rendered = TRUE
        w = self._window
        clonestart = self._clonestart
        if not self._cloneof or \
           self._cloneof is not w._active_displist:
            clonestart = 0
        if w._active_displist and self is not w._active_displist and \
           w._transparent and clonestart == 0:
            w._active_displist = None
            w._do_expose(region)
        gc = w._gc
        gcattr = self._gcattr.copy()
        bgcolor = self._bgcolor
        if bgcolor is None and w._transparent != 1:
            bgcolor = w._bgcolor
        if bgcolor is None:
            bgcolor = 255,255,255
        gcattr['background'] = w._convert_color(bgcolor)
        gc.ChangeGC(self._gcattr)
        gc.SetRegion(region)
        if clonestart == 0 and self._imagemask:
            # restrict to drawing outside the image
            if type(self._imagemask) is RegionType:
                imagemask = Xlib.CreateRegion()
                imagemask.UnionRegion(self._imagemask)
                imagemask.OffsetRegion(w._rect[0], w._rect[1])
                r = Xlib.CreateRegion()
                r.UnionRegion(region)
                r.SubtractRegion(imagemask)
                gc.SetRegion(r)
            else:
                width, height = w._topwindow._rect[2:]
                r = w._form.CreatePixmap(width, height, 1)
                g = r.CreateGC({'foreground': 0})
                g.FillRectangle(0, 0, width, height)
                g.SetRegion(region)
                g.foreground = 1
                g.FillRectangle(0, 0, width, height)
                g.function = X.GXcopyInverted
                mask, src_x, src_y, dest_x, dest_y, width, height = self._imagemask
                g.PutImage(mask, src_x, src_y, dest_x+w._rect[0], dest_y+w._rect[1], width, height)
                gc.SetClipMask(r)
        for i in range(clonestart, len(self._list)):
            self._do_render(self._list[i], region)
        w._active_displist = self
        for b in self._buttons:
            if b._highlighted:
                b._do_highlight()

    def _do_render(self, entry, region):
        cmd = entry[0]
        window = self._window
        gc = window._gc
        if cmd == 'clear':
            color = self._bgcolor
            if color is None:
                color = window._bgcolor
            if color is not None:
                gc.foreground = window._convert_color(color)
                apply(gc.FillRectangle, window._rect)
        elif cmd == 'image':
            clip = entry[2]
            r = region
            if clip is not None:
                r = Xlib.CreateRegion()
                clip = window._convert_coordinates(clip)
                apply(r.UnionRectWithRegion, clip)
                r.IntersectRegion(region)

            mask = entry[1]
            src_x, src_y, dest_x, dest_y, width, height = entry[4:]
            dest_x = dest_x + window._rect[0]
            dest_y = dest_y + window._rect[1]
            if mask:
                # mask is clip mask for image
                width, height = window._topwindow._rect[2:]
                p = window._form.CreatePixmap(width, height, 1)
                g = p.CreateGC({'foreground': 0})
                g.FillRectangle(0, 0, width, height)
                g.SetRegion(r)
                g.foreground = 1
                g.FillRectangle(0, 0, width, height)
                g.PutImage(mask, src_x, src_y, dest_x, dest_y, width, height)
                gc.SetClipMask(p)
            else:
                gc.SetRegion(r)
            gc.PutImage(entry[3], src_x, src_y, dest_x, dest_y, width, height)
            if mask or clip:
                gc.SetRegion(region)
        elif cmd == 'line':
            gc.foreground = window._convert_color(entry[1])
            gc.line_width = entry[2]
            units = entry[3]
            points = entry[4]
            x0, y0 = window._convert_coordinates(points[0], units=units)
            for p in points[1:]:
                x, y = window._convert_coordinates(p, units=units)
                gc.DrawLine(x0, y0, x, y)
                x0, y0 = x, y
        elif cmd == '3dhline':
            color1, color2, x0, x1, y, units = entry[1:]
            x0, y = window._convert_coordinates((x0, y), units=units)
            x1, dummy = window._convert_coordinates((x1, y), units=units)
            gc.foreground = window._convert_color(color1)
            gc.DrawLine(x0, y, x1, y)
            gc.foreground = window._convert_color(color2)
            gc.DrawLine(x0, y+1, x1, y+1)
        elif cmd == 'box':
            gc.foreground = window._convert_color(entry[1])
            gc.line_width = entry[2]
            units = entry[5]
            x,y,w,h = window._convert_coordinates(entry[3], units=units)
            if entry[4]:
                clip = window._convert_coordinates(entry[4], units=units)
                r = Xlib.CreateRegion()
                apply(r.UnionRectWithRegion, clip)
                r.IntersectRegion(region)
                gc.SetRegion(r)
            gc.DrawRectangle(x,y,w-1,h-1)
            if entry[4]:
                gc.SetRegion(region)
        elif cmd == 'fbox':
            gc.foreground = window._convert_color(entry[1])
            box = window._convert_coordinates(entry[2], units=entry[3])
            apply(gc.FillRectangle, box)
        elif cmd == 'marker':
            gc.foreground =  window._convert_color(entry[1])
            x, y = window._convert_coordinates(entry[2], units=entry[3])
            radius = 5 # XXXX
            gc.FillArc(x-radius, y-radius, 2*radius, 2*radius,
                       0, 360*64)
        elif cmd == 'text':
            gc.foreground = window._convert_color(entry[1])
            gc.SetFont(entry[2])
            x, y = entry[3]
            gc.DrawString(x, y, entry[4])
        elif cmd == 'fpolygon':
            gc.foreground = window._convert_color(entry[1])
            p = []
            for point in entry[2]:
                p.append(window._convert_coordinates(point, units = entry[3]))
            gc.FillPolygon(p, X.Convex, X.CoordModeOrigin)
        elif cmd == '3dbox':
            cl, ct, cr, cb = entry[1]
            cl = window._convert_color(cl)
            ct = window._convert_color(ct)
            cr = window._convert_color(cr)
            cb = window._convert_color(cb)
            l, t, w, h = window._convert_coordinates(entry[2], units=entry[3])
            r, b = l + w, t + h
            # l, r, t, b are the corners
            l3 = l + 3
            t3 = t + 3
            r3 = r - 3
            b3 = b - 3
            # draw left side
            gc.foreground = cl
            gc.FillPolygon([(l, t), (l3, t3), (l3, b3), (l, b)],
                           X.Convex, X.CoordModeOrigin)
            # draw top side
            gc.foreground = ct
            gc.FillPolygon([(l, t), (r, t), (r3, t3), (l3, t3)],
                           X.Convex, X.CoordModeOrigin)
            # draw right side
            gc.foreground = cr
            gc.FillPolygon([(r3, t3), (r, t), (r, b), (r3, b3)],
                           X.Convex, X.CoordModeOrigin)
            # draw bottom side
            gc.foreground = cb
            gc.FillPolygon([(l3, b3), (r3, b3), (r, b), (l, b)],
                           X.Convex, X.CoordModeOrigin)
        elif cmd == 'diamond':
            gc.foreground = window._convert_color(entry[1])
            gc.line_width = entry[2]
            x, y, w, h = window._convert_coordinates(entry[3], units = entry[4])
            gc.DrawLines([(x, y + h/2),
                          (x + w/2, y),
                          (x + w, y + h/2),
                          (x + w/2, y + h),
                          (x, y + h/2)],
                         X.CoordModeOrigin)
        elif cmd == 'fdiamond':
            gc.foreground = window._convert_color(entry[1])
            x, y, w, h = window._convert_coordinates(entry[2], units = entry[3])
            gc.FillPolygon([(x, y + h/2),
                            (x + w/2, y),
                            (x + w, y + h/2),
                            (x + w/2, y + h),
                            (x, y + h/2)],
                           X.Convex, X.CoordModeOrigin)
        elif cmd == '3ddiamond':
            cl, ct, cr, cb = entry[1]
            cl = window._convert_color(cl)
            ct = window._convert_color(ct)
            cr = window._convert_color(cr)
            cb = window._convert_color(cb)
            l, t, w, h = window._convert_coordinates(entry[2], units = entry[3])
            r = l + w
            b = t + h
            x = l + w/2
            y = t + h/2
            n = int(3.0 * w / h + 0.5)
            ll = l + n
            tt = t + 3
            rr = r - n
            bb = b - 3
            gc.foreground = cl
            gc.FillPolygon([(l, y), (x, t), (x, tt), (ll, y)],
                           X.Convex, X.CoordModeOrigin)
            gc.foreground = ct
            gc.FillPolygon([(x, t), (r, y), (rr, y), (x, tt)],
                           X.Convex, X.CoordModeOrigin)
            gc.foreground = cr
            gc.FillPolygon([(r, y), (x, b), (x, bb), (rr, y)],
                           X.Convex, X.CoordModeOrigin)
            gc.foreground = cb
            gc.FillPolygon([(l, y), (ll, y), (x, bb), (x, b)],
                           X.Convex, X.CoordModeOrigin)
        elif cmd == 'arrow':
            gc.foreground = window._convert_color(entry[1])
            gc.line_width = entry[2]
            nsx, nsy, ndx, ndy, points = self._convert_arrow(entry[3], entry[4], entry[5])
            gc.DrawLine(nsx, nsy, ndx, ndy)
            gc.FillPolygon(points, X.Convex, X.CoordModeOrigin)

    def _getcoverarea(self):
        # return Region that we guarantee to overwrite on render
        w = self._window
        if self._bgcolor is not None or w._bgcolor is not None:
            r = Xlib.CreateRegion()
            apply(r.UnionRectWithRegion, w._rect)
            return r
        r = Xlib.CreateRegion()
        r.UnionRegion(self._coverarea)
        r.OffsetRegion(w._rect[0], w._rect[1])
        return r

    def fgcolor(self, color):
        if self._rendered:
            raise error, 'displaylist already rendered'
        self._fgcolor = color

    def linewidth(self, width):
        if self._rendered:
            raise error, 'displaylist already rendered'
        self._linewidth = width

#       def newbutton(self, coordinates, z = 0, times = None, sensitive = 1):
#               if self._rendered:
#                       raise error, 'displaylist already rendered'
#               return _Button(self, coordinates, z, times, sensitive)

    # set the media sensitivity
    # value is percentage value (range 0-100); opaque=0, transparent=100
    def setAlphaSensitivity(self, value):
        self._alphaSensitivity = value

    # Define a new button. Coordinates are in window relatives
    def newbutton(self, coordinates, z = 0, times = None, sensitive = 1):
        if self._rendered:
            raise error, 'displaylist already rendered'

        # test of shape type
        if coordinates[0] == 'rect':
            return _ButtonRect(self, coordinates, z, times, sensitive)
        elif coordinates[0] == 'poly':
            return _ButtonPoly(self, coordinates, z, times, sensitive)
        elif coordinates[0] == 'circle':
            return _ButtonCircle(self, coordinates, z, times, sensitive)
        elif coordinates[0] == 'ellipse':
            return _ButtonEllipse(self, coordinates, z, times, sensitive)
        else:
            print 'Internal error: invalid shape type'
            return _ButtonRect(self, ['rect', 0.0, 0.0, 1.0, 1.0], z, times, sensitive)

    def display_image_from_file(self, file, crop = (0,0,0,0), fit = 'meet',
                                center = 1, coordinates = None,
                                clip = None, align = None, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        w = self._window
        image, mask, src_x, src_y, dest_x, dest_y, width, height = \
               w._prepare_image(file, crop, fit, center, coordinates, align, units)
        if mask:
            self._imagemask = mask, src_x, src_y, dest_x, dest_y, width, height
        else:
            r = Xlib.CreateRegion()
            r.UnionRectWithRegion(dest_x, dest_y, width, height)
            self._imagemask = r
            self._coverarea.UnionRegion(r)
        self._list.append(('image', mask, clip, image, src_x, src_y,
                           dest_x, dest_y, width, height))
        self._optimize((2,))
        x, y, w, h = w._rect
        if units == UNIT_PXL:
            return dest_x, dest_y, width, height
        else:
            return float(dest_x) / w, float(dest_y) / h, \
                   float(width) / w, float(height) / h

    def drawline(self, color, points, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        self._list.append(('line', color, self._linewidth, units,
                           points[:]))
        self._optimize((1,))

    def draw3dhline(self, color1, color2, x0, x1, y, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        self._list.append(('3dhline', color1, color2, x0, x1, y, units))
        self._optimize((1,))

    def drawbox(self, coordinates, clip = None, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if self._fgcolor is None:
            raise error, 'no fgcolor'
        if units is None:
            units = self.__units
        self._list.append(('box', self._fgcolor, self._linewidth,
                           coordinates, clip, units))
        self._optimize((1,))

    def drawfbox(self, color, coordinates, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        w = self._window
        self._list.append(('fbox', color, coordinates, units))
        box = w._convert_coordinates(coordinates, units = units)
        self._coverarea.UnionRectWithRegion(box[0]-w._rect[0],
                                            box[1]-w._rect[1],
                                            box[2], box[3])
        self._optimize((1,))
    def drawstipplebox(self, color, coordinates, units = None):
        # This should draw a hatched or stippled box.
        pass

    def drawmarker(self, color, coordinates, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        self._list.append(('marker', color, coordinates, units))

    def get3dbordersize(self):
        # This is the same "3" as in 3dbox bordersize
        return self._window._pxl2rel((0,0,3,3))[2:4]

    def usefont(self, fontobj):
        if self._rendered:
            raise error, 'displaylist already rendered'
        self._font = fontobj
        return self.baseline(), self.fontheight(), self.pointsize()

    def setfont(self, font, size):
        if self._rendered:
            raise error, 'displaylist already rendered'
        return self.usefont(findfont(font, size))

    def fitfont(self, fontname, str, margin = 0):
        if self._rendered:
            raise error, 'displaylist already rendered'
        return self.usefont(findfont(fontname, 10))

    def baseline(self, units = None):
        if units is None:
            units = self.__units
        baseline = self._font.baselinePXL()
        if units == UNIT_PXL:
            return baseline
        return self._window._pxl2rel((0,0,0,baseline))[3]

    def baselinePXL(self):
        return self._font.baselinePXL()

    def fontheight(self, units = None):
        if units is None:
            units = self.__units
        fontheight = self._font.fontheightPXL()
        if units == UNIT_PXL:
            return fontheight
        return self._window._pxl2rel((0,0,0,fontheight))[3]

    def fontheightPXL(self):
        return self._font.fontheightPXL()

    def pointsize(self):
        return self._font.pointsize()

    def strsize(self, str, units = None):
        if units is None:
            units = self.__units
        width, height = self._font.strsizePXL(str)
        if units == UNIT_PXL:
            return width, height
        return self._window._pxl2rel((0,0,width,height))[2:4]

    def strsizePXL(self, str):
        return self._font.strsize(str)

    def setpos(self, x, y, units = None):
        if units is None:
            units = self.__units
        x, y = self._window._convert_coordinates((x, y), units=units)
        self._curpos = x, y
        self._xpos = x

    def writestr(self, str, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if self._fgcolor is None:
            raise error, 'no fgcolor'
        if units is None:
            units = self.__units
        list = self._list
        f = self._font._font
        base = self.baseline(UNIT_PXL)
        height = self.fontheight(UNIT_PXL)
        strlist = string.splitfields(str, '\n')
        oldx, oldy = x, y = self._curpos
        if len(strlist) > 1 and oldx > self._xpos:
            oldx = self._xpos
        oldy = oldy - base
        maxx = oldx
        for str in strlist:
            list.append(('text', self._fgcolor, self._font._font, (x, y), str))
            self._optimize((1,))
            self._curpos = x + f.TextWidth(str), y
            x = self._xpos
            y = y + height
            if self._curpos[0] > maxx:
                maxx = self._curpos[0]
        newx, newy = self._curpos
        if units == UNIT_PXL:
            return oldx, oldy, maxx - oldx, newy - oldy + height - base
        else:
            return self._window._pxl2rel((oldx, oldy, maxx - oldx, newy - oldy + height - base))

    # Draw a string centered in a box, breaking lines if necessary
    def centerstring(self, left, top, right, bottom, str, units = None):
        if units is None:
            units = self.__units
        fontheight = self.fontheight(UNIT_PXL)
        baseline = self.baseline(UNIT_PXL)
        width = right - left
        height = bottom - top
        left, top, width, height = self._window._convert_coordinates((left, top, width, height), units=units)
        curlines = [str]
        if height >= 2*fontheight:
            import StringStuff
            curlines = StringStuff.calclines([str], self._font.strsizePXL, width)[0]
        nlines = len(curlines)
        needed = nlines * fontheight
        if nlines > 1 and needed > height:
            nlines = max(1, int(height / fontheight))
            curlines = curlines[:nlines]
            curlines[-1] = curlines[-1] + '...'
        x0 = left + width / 2   # x center of box
        y0 = top + height / 2   # y center of box
        y = y0 - nlines * fontheight * 0.5
        for i in range(nlines):
            str = string.strip(curlines[i])
            # Get font parameters:
            w = self._font.strsizePXL(str)[0] # Width of string
            while str and w > width:
                str = str[:-1]
                w = self._font.strsizePXL(str)[0]
            x = x0 - 0.5*w
            y = y + baseline
            self.setpos(x, y, UNIT_PXL)
            self.writestr(str, UNIT_PXL)

    def drawfpolygon(self, color, points, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        w = self._window
        self._list.append(('fpolygon', color, points, units))
        x0, y0 = w._rect[:2]
        p = []
        for point in points:
            x, y = w._convert_coordinates(point, units = units)
            p.append((x-x0, y-y0))
        r = Xlib.PolygonRegion(p, w._gc.fill_rule)
        self._coverarea.UnionRegion(r)
        self._optimize((1,))

    def draw3dbox(self, cl, ct, cr, cb, coordinates, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        self._list.append(('3dbox', (cl, ct, cr, cb), coordinates, units))
        self._optimize((1,))

    def drawdiamond(self, coordinates, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if self._fgcolor is None:
            raise error, 'no fgcolor'
        if units is None:
            units = self.__units
        self._list.append(('diamond',
                           self._fgcolor,
                           self._linewidth, coordinates, units))
        self._optimize((1,))

    def drawfdiamond(self, color, coordinates, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        window = self._window
        x, y, w, h = coordinates
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        coordinates = window._convert_coordinates((x, y, w, h), units = units)
        self._list.append(('fdiamond', color, (x, y, w, h), units))
        x, y, w, h = coordinates
        x0, y0 = w._rect[:2]
        r = Xlib.PolygonRegion([(x-x0, y + h/2 - y0),
                                (x + w/2 - x0, y - y0),
                                (x + w - x0, y + h/2 - y0),
                                (x + w/2 - x0, y + h - y0),
                                (x - x0, y + h/2 - y0)],
                               w._gc.fill_rule)
        self._coverarea.UnionRegion(r)
        self._optimize((1,))

    def draw3ddiamond(self, cl, ct, cr, cb, coordinates, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        self._list.append(('3ddiamond', (cl, ct, cr, cb), coordinates, units))
        self._optimize((1,))

    def drawicon(self, coordinates, icon, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        # Icon names needed:
        # '' is special: don't draw any icon (needed for removing icons in optimize)
        # 'closed' used for closed structure nodes
        # 'open': used for open structure nodes
        # 'bandwidthgood' used to show bandwidth usage is fine
        # 'bandwidthbad' too much banwidth used
        # 'error' Some error has occurred on the node
        w = self._window
        module = _iconmap.get(icon) or _iconmap['']
        reader = __import__(module)
        image, mask, src_x, src_y, dest_x, dest_y, width, height = \
               w._prepare_image(reader, (0,0,0,0), 'icon', 1, coordinates, 'center', units)
        if mask:
            self._imagemask = mask, src_x, src_y, dest_x, dest_y, width, height
        else:
            r = Xlib.CreateRegion()
            r.UnionRectWithRegion(dest_x, dest_y, width, height)
            self._imagemask = r
            self._coverarea.UnionRegion(r)
        self._list.append(('image', mask, None, image, src_x, src_y,
                           dest_x, dest_y, width, height))
        self._optimize((2,))

    def _convert_arrow(self, src, dst, units):
        if units is None:
            units = self.__units
        window = self._window
        if not window._arrowcache.has_key((src,dst)):
            sx, sy = src
            dx, dy = dst
            nsx, nsy = window._convert_coordinates((sx, sy), units = units)
            ndx, ndy = window._convert_coordinates((dx, dy), units = units)
            if nsx == ndx and sx != dx:
                if sx < dx:
                    nsx = nsx - 1
                else:
                    nsx = nsx + 1
            if nsy == ndy and sy != dy:
                if sy < dy:
                    nsy = nsy - 1
                else:
                    nsy = nsy + 1
            lx = ndx - nsx
            ly = ndy - nsy
            if lx == ly == 0:
                angle = 0.0
            else:
                angle = math.atan2(ly, lx)
            rotation = math.pi + angle
            cos = math.cos(rotation)
            sin = math.sin(rotation)
            points = [(ndx, ndy)]
            points.append((roundi(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
                           roundi(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos)))
            points.append((roundi(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
                           roundi(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos)))
            window._arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
        return window._arrowcache[(src,dst)]

    def drawarrow(self, color, src, dst, units = None):
        if self._rendered:
            raise error, 'displaylist already rendered'
        if units is None:
            units = self.__units
        self._list.append(('arrow', color, self._linewidth, src, dst, units))
        self._optimize((1,))

    def _optimize(self, ignore = ()):
        entry = self._list[-1]
        x = []
        for i in range(len(entry)):
            if i not in ignore:
                z = entry[i]
                if type(z) is ListType:
                    z = tuple(z)
                x.append(z)
        x = tuple(x)
        try:
            i = self._optimdict[x]
        except KeyError:
            pass
        else:
            del self._list[i]
            del self._optimdict[x]
            if i < self._clonestart:
                self._clonestart = self._clonestart - 1
            for key, val in self._optimdict.items():
                if val > i:
                    self._optimdict[key] = val - 1
        self._optimdict[x] = len(self._list) - 1


    ######################################
    # Animation experimental methods
    #

    # Update cmd with name from diff display list
    # we can get also update region from diff dl
    def update(self, name, diffdl):
        newcmd = diffdl.getcmd(name)
        if newcmd and self.__cmddict.has_key(name):
            ix = self.__cmddict[name]
            self._list[ix] = newcmd

    # Update cmd with name
    def updatecmd(self, name, newcmd):
        if self.__cmddict.has_key(name):
            ix = self.__cmddict[name]
            self._list[ix] = newcmd

    def getcmd(self, name):
        if self.__cmddict.has_key(name):
            ix = self.__cmddict[name]
            return self._list[ix]
        return None

    def knowcmd(self, name):
        self.__cmddict[name] = len(self._list)-1

    # Update background color
    def updatebgcolor(self, color):
        self._bgcolor = color

    #
    # End of animation experimental methods
    ##########################################
