__version__ = "$Id$"

# app constants
from appcon import *
from WMEVENTS import *

import ddraw

# for global toplevel
import __main__

# regions, RGB
import wingdi
import win32con

import win32transitions

import winstruct

import base_window

class Region(base_window.Window):
    def __init__(self, parent, coordinates, transparent, z, units, bgcolor):
        base_window.Window.__init__(self)

        # create the window
        self.create(parent, coordinates, units, z, transparent, bgcolor)

        # context os window
        if parent:
            self._ctxoswnd = self._topwindow.getContextOsWnd()

        # implementation specific
        self._oswnd = None
        self._redrawdds = None

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
        del self._redrawdds
        del self._drawsurf
        del self._fromsurf

    #
    # OS windows simulation support
    #
    def GetSafeHwnd(self):
        if self._oswnd:
            wnd = self._oswnd
        else:
            wnd = self._topwindow
        return wnd.GetSafeHwnd()

    def GetClientRect(self):
        x, y, w, h = self._rect
        return x, y, x+w, y+h

    def HookMessage(self, f, m):
        if self._oswnd: wnd = self._oswnd
        else: wnd = self._topwindow
        wnd.HookMessage(f,m)

    #
    # Foreign renderers support
    #
    def CreateOSWindow(self, rect=None, html=0, svg=0):
        if self._oswnd:
            return self._oswnd
        return None

    def hookOsWndMessages(self):
        if not self._oswnd: return
        self.HookMessage(self.onOsWndLButtonDown,win32con.WM_LBUTTONDOWN)
        self.HookMessage(self.onOsWndLButtonUp,win32con.WM_LBUTTONUP)
        self.HookMessage(self.onOsWndMouseMove,win32con.WM_MOUSEMOVE)

    def onOsWndLButtonDown(self, params):
        xr, yr = winstruct.Win32Msg(params).pos()
        x, y, w, h = self.getwindowpos()
        if self._topwindow:
            self._topwindow.onMouseEvent((x+xr, y+yr), Mouse0Press)

    def onOsWndLButtonUp(self, params):
        xr, yr = winstruct.Win32Msg(params).pos()
        x, y, w, h = self.getwindowpos()
        if self._topwindow:
            self._topwindow.onMouseEvent((x+xr, y+yr), Mouse0Release)

    def onOsWndMouseMove(self, params):
        xr, yr = winstruct.Win32Msg(params).pos()
        x, y, w, h = self.getwindowpos()
        if self._topwindow:
            self._topwindow.onMouseMove(0, (x+xr, y+yr))

    def DestroyOSWindow(self):
        if self._oswnd:
            self._oswnd.DestroyWindow()
            self._oswnd = None
            if not self.is_closed():
                self.update()
    #
    # HTML control support
    #
    def RetrieveUrl(self,fileOrUrl):
        if not self._oswnd:
            self.CreateOSWindow(self, html=1)
        self._oswnd.Navigate(fileOrUrl)

    def HasHtmlCtrl(self):
        if not self._oswnd: return 0
        return self._oswnd.HasHtmlCtrl()

    def CreateHtmlCtrl(self, which = 0):
        if self._oswnd:
            self._oswnd.UseHtmlCtrl(which)
            self._oswnd.CreateHtmlCtrl()

    def DestroyHtmlCtrl(self):
        if self._oswnd:
            self._oswnd.DestroyHtmlCtrl()

    def SetImmHtml(self, text):
        if self._oswnd:
            self._oswnd.SetImmHtml(text)
    #
    # SVG control support
    #
    # detect SVG support
    def HasSvgSupport(self):
        return 0

    # set SVG source URL
    def SetSvgSrc(self, fileOrUrl):
        if not self._oswnd:
            self.CreateOSWindow(self, svg=1)
        self._oswnd.SetSrc(fileOrUrl)

    # has the SVG control been created?
    def HasSvgCtrl(self):
        if not self._oswnd:
            return 0
        return self._oswnd.HasSvgCtrl()

    # create SVG control
    def CreateSvgCtrl(self, which = 0):
        if self._oswnd:
            self._oswnd.CreateSvgCtrl()

    # destroy SVG control
    def DestroySvgCtrl(self):
        if self._oswnd:
            self._oswnd.DestroySvgCtrl()

    # Called by the Html channel to set the callback to be called on cmif links
    # Part of WebBrowsing support
    def setanchorcallback(self,cb):
        self._anchorcallback=cb

    # Called by the HtmlWnd when a cmif anchor has fired. It is a callback but implemented
    # using the std windows message mechanism
    # Part of WebBrowsing support
    def onUserUrl(self,params):
        if self._oswnd:
            url=self._oswnd.GetForeignUrl()
            if hasattr(self,'_anchorcallback') and self._anchorcallback:
                self._anchorcallback(url)

    def show(self):
        self._isvisible = 1
        if self._oswnd:
            self._oswnd.ShowWindow(win32con.SW_SHOW)
        self.update()

    def hide(self):
        self._isvisible = 0
        if self._oswnd:
            self._oswnd.ShowWindow(win32con.SW_HIDE)
        self.update()

    def updateoswndpos(self):
        for w in self._subwindows:
            w.updateoswndpos()

        if self._oswnd:
            x, y, w, h = self.getwindowpos()
            self._oswnd.SetWindowPos(win32con.HWND_TOP, (x,y,w,h) ,
                    win32con.SWP_NOZORDER | win32con.SWP_ASYNCWINDOWPOS | win32con.SWP_DEFERERASE)

    #
    # Inage management
    #
    # Returns the size of the image
    def _image_size(self, file):
        return __main__.toplevel._image_size(file, self.getgrinsdoc())

    # Returns handle of the image
    def _image_handle(self, file):
        return __main__.toplevel._image_handle(file, self.getgrinsdoc())

    def getgrinsdoc(self):
        if self != self._topwindow:
            return self._topwindow.getgrinsdoc()
        else:
            print 'topwindow should override getgrinsdoc'

    #
    # Box creation section
    #
    def create_box(self, msg, callback, box = None, units = UNIT_SCREEN, modeless=0, coolmode=0):
        print 'create_box'

    def cancel_create_box(self):
        print 'cancel_create_box'

    #
    # Rendering section
    #

    def getClipRgn(self, rel=None):
        x, y, w, h = self.getwindowpos(rel)
        rgn = wingdi.CreateRectRgn((x,y,x+w,y+h))
        if rel==self: return rgn
        prgn = self._parent.getClipRgn(rel)
        rgn.CombineRgn(rgn, prgn, win32con.RGN_AND)
        prgn.DeleteObject()
        return rgn

    # get reg of children
    def getChildrenRgn(self, rel=None):
        rgn = wingdi.CreateRectRgn((0,0,0,0))
        for w in self._subwindows:
            x, y, w, h = w.getwindowpos(rel)
            newrgn = wingdi.CreateRectRgn((x,y,x+w,y+h))
            rgn.CombineRgn(rgn, newrgn, win32con.RGN_OR)
            newrgn.DeleteObject()
        # finally clip to this
        argn = self.getClipRgn(rel)
        rgn.CombineRgn(rgn,argn,win32con.RGN_AND)
        argn.DeleteObject()
        return rgn

    # get reg of this excluding children
    def getChildrenRgnComplement(self, rel=None):
        rgn = self.getClipRgn(rel)
        drgn = self.getChildrenRgn(rel)
        rgn.CombineRgn(rgn,drgn,win32con.RGN_DIFF)
        drgn.DeleteObject()
        return rgn

    def clipRect(self, rc, rgn):
        newrgn = wingdi.CreateRectRgn(self.ltrb(rc))
        newrgn.CombineRgn(rgn,newrgn,win32con.RGN_AND)
        ltrb = newrgn.GetRgnBox()
        newrgn.DeleteObject()
        return self.xywh(ltrb)

    def rectAnd(self, rc1, rc2):
        # until we make calcs
        rc,ans= wingdi.IntersectRect(self.ltrb(rc1),self.ltrb(rc2))
        if ans:
            return self.xywh(rc)
        return (0, 0, 0, 0)

    def rectOr(self, rc1, rc2):
        # until we make calcs
        rc, ans = wingdi.UnionRect(self.ltrb(rc1),self.ltrb(rc2))
        if ans:
            return self.xywh(rc)
        return (0, 0, 0, 0)


    # paint on surface dds only what this window is responsible for
    # i.e. self._active_displist and/or bgcolor
    # clip painting to argument rgn when given
    def _paintOnDDS(self, dds, dst, rgn=None):
        x, y, w, h = dst
        if w==0 or h==0:
            return

        if rgn:
            xc, yc, wc, hc = self.xywh(rgn.GetRgnBox())
        else:
            xc, yc, wc, hc = dst

        if wc==0 or hc==0:
            return

        if dds.IsLost():
            return

        if self._active_displist:
            entry = self._active_displist._list[0]
            bgcolor = None
            if entry[0] == 'clear' and entry[1]:
                bgcolor = entry[1]
            elif not self._transparent:
                bgcolor = self._bgcolor
            if bgcolor:
                r, g, b = bgcolor
                convbgcolor = dds.GetColorMatch((r,g,b))
                dds.BltFill((xc, yc, xc+wc, yc+hc), convbgcolor)
            if self._redrawdds:
                # get redraw dds info
                vdds, vrcDst, vrcSrc = self._redrawdds
                if self._mediadisplayrect:
                    vrcDst = self._mediadisplayrect

                # src rect taking into account fit
                ws, hs = vrcSrc[2:]
                vrcSrc = self._getmediacliprect(vrcSrc[2:], vrcDst, fit=self._fit)

                # split rects
                ls, ts, rs, bs = self.ltrb(vrcSrc)
                xd, yd, wd, hd = vrcDst
                ld, td, rd, bd = x+xd, y+yd, x+xd+wd, y+yd+hd

                # clip destination
                ldc, tdc, rdc, bdc = self.ltrb(self.rectAnd((xc, yc, wc, hc),
                        (ld, td, rd-ld, bd-td)))

                # find src clip ltrb given the destination clip
                lsc, tsc, rsc, bsc =  self._getsrcclip((ld, td, rd, bd), (ls, ts, rs, bs), (ldc, tdc, rdc, bdc))

                if self._canscroll:
                    dx, dy = self._scrollpos
                    lsc, tsc, rsc, bsc = lsc+dx, tsc+dy, rsc+dx, bsc+dy

                # we are ready, blit it
                if not vdds.IsLost():
                    dds.Blt((ldc, tdc, rdc, bdc), vdds, (lsc, tsc, rsc, bsc), ddraw.DDBLT_WAIT)
                else:
                    vdds.Restore()

            if self._active_displist._issimple:
                try:
                    self._active_displist._ddsrender(dds, dst, rgn, clear=0, mediadisplayrect = self._mediadisplayrect, fit=self._fit)
                except:
                    pass
            else:
                # draw display list but after clear
                try:
                    hdc = dds.GetDC()
                except ddraw.error, arg:
                    print arg
                    return

                dc = wingdi.CreateDCFromHandle(hdc)
                if rgn:
                    dc.SelectClipRgn(rgn)
                x0, y0 = dc.SetWindowOrg((-x,-y))

                try:
                    self._active_displist._render(dc, None, clear=0)
                except:
                    dc.Detach()
                    dds.ReleaseDC(hdc)
                    return

                if self._showing:
                    pass # FrameRect(dc, self._rect,self._showing)

                dc.SetWindowOrg((x0,y0))
                dc.Detach()
                dds.ReleaseDC(hdc)

            # if we have an os-subwindow invalidate its area
            # but do not update it since we want this to happen
            # after the surfaces flipping
            if self._oswnd:
                self._oswnd.InvalidateRect(self._oswnd.GetClientRect())

        elif self._transparent == 0 and self._bgcolor:
            if self._convbgcolor == None:
                r, g, b = self._bgcolor
                self._convbgcolor = dds.GetColorMatch((r,g,b))
            dds.BltFill((xc, yc, xc+wc, yc+hc), self._convbgcolor)


    # same as getwindowpos
    # but rel is not an ancestor
    def getrelativepos(self, rel):
        if rel == self:
            return self._rect
        rc1 = rel.getwindowpos()
        rc2 = self.getwindowpos()
        rc3 = self.rectAnd(rc1, rc2)
        return rc3[0]-rc1[0], rc3[1]-rc1[1], rc3[2], rc3[3]

    # same as getClipRgn
    # but rel is not an ancestor
    def getrelativeClipRgn(self, rel):
        x, y, w, h = self.getrelativepos(rel);
        return wingdi.CreateRectRgn((x,y,x+w,y+h))

    # paint on surface dds relative to ancestor rel
    def paintOnDDS(self, dds, rel=None, exclwnd=None):
        #print 'paintOnDDS', self, 'subwindows', len(self._subwindows), self._rect
        # first paint self
        rgn = self.getrelativeClipRgn(rel)
        dst = self.getrelativepos(rel)
        try:
            self._paintOnDDS(dds, dst, rgn)
        except ddraw.error, arg:
            print arg
        rgn.DeleteObject()

        # then paint children bottom up
        L = self._subwindows[:]
        L.reverse()
        for w in L:
            w.paintOnDDS(dds, rel, exclwnd)

        # then paint transition children bottom up
        if self._transition and self._transition._isrunning() and self._transition._ismaster(self):
            L = self._transition.windows[1:]
            L.reverse()
            for wnd in L:
                wnd.paintOnDDS(dds, rel, exclwnd)

    # get a copy of the screen area of this window
    def getBackDDS(self, exclwnd = None, dopaint = 1):
        dds = self.createDDS()
        bf = self._topwindow.getDrawBuffer()
        if bf.IsLost() and not bf.Restore():
            return dds
        x, y, w, h = self.getwindowpos()
        if dopaint:
            self._topwindow.paint(rc=(x, y, w, h), exclwnd=exclwnd)
            if bf.IsLost() and not bf.Restore():
                return dds
        try:
            dds.Blt((0,0,w,h), bf, (x, y, x+w, y+h), ddraw.DDBLT_WAIT)
        except ddraw.error, arg:
            print 'getBackDDS', arg
        return dds

    def updateBackDDS(self, dds, exclwnd=None):
        rc = x, y, w, h = self.getwindowpos()
        self._topwindow.paint(rc, exclwnd=exclwnd)
        bf = self._topwindow.getDrawBuffer()
        if bf.IsLost() and not bf.Restore():
            return dds
        try:
            dds.Blt((0,0,w,h), bf, (x, y, x+w, y+h), ddraw.DDBLT_WAIT)
        except ddraw.error, arg:
            print 'updateBackDDS', arg
        return dds

    def bltDDS(self, srfc):
        rc_dst = self.getwindowpos()
        src_w, src_h = srfc.GetSurfaceDesc().GetSize()
        rc_src = (0, 0, src_w, src_h)
        bf = self._topwindow.getDrawBuffer()
        if bf.IsLost() and not bf.Restore():
            return
        if rc_dst[2]!=0 and rc_dst[3]!=0:
            try:
                bf.Blt(self.ltrb(rc_dst), srfc, rc_src, ddraw.DDBLT_WAIT)
            except ddraw.error, arg:
                print arg

    def clearSurface(self, dds):
        w, h = dds.GetSurfaceDesc().GetSize()
        if self._convbgcolor == None:
            if self._bgcolor:
                r, g, b = self._bgcolor
            else:
                r, g, b = 0, 0, 0
            self._convbgcolor = dds.GetColorMatch((r,g,b))
        try:
            if not dds.IsLost():
                dds.BltFill((0, 0, w, h), self._convbgcolor)
        except ddraw.error, arg:
            print arg

    # normal painting
    def _paint_0(self, rc=None, exclwnd=None):
#               if self._transition and self._transition._isrunning():
#                       print 'normal paint while in transition', self

        if exclwnd==self: return

        # first paint self
        dst = self.getwindowpos(self._topwindow)
        rgn = self.getClipRgn(self._topwindow)
        if rc:
            prgn = wingdi.CreateRectRgn(self.ltrb(rc))
            rgn.CombineRgn(rgn,prgn,win32con.RGN_AND)
            prgn.DeleteObject()

        buf = self._topwindow.getDrawBuffer()
        if buf.IsLost() and not buf.Restore():
            return
        try:
            self._paintOnDDS(buf, dst, rgn)
        except ddraw.error, arg:
            print arg

        rgn.DeleteObject()

        # then paint children bottom up
        L = self._subwindows[:]
        L.reverse()
        for w in L:
            if w!=exclwnd:
                w.paint(rc, exclwnd)

    # transition, multiElement==false
    # trans engine: calls self._paintOnDDS(self._drawsurf)
    # i.e. trans engine is responsible to paint only this
    def _paint_1(self, rc=None, exclwnd=None):
        #print 'transition, multiElement==false', self
        if exclwnd==self: return

        # first paint self transition surface
        self.bltDDS(self._drawsurf)

        # then paint children bottom up normally
        L = self._subwindows[:]
        L.reverse()
        for w in L:
            if w!=exclwnd:
                w.paint(rc, exclwnd)

    # transition, multiElement==true, childrenClip==false
    # trans engine: calls self.paintOnDDS(self._drawsurf, self)
    # i.e. trans engine responsible to paint correctly everything below
    def _paint_2(self, rc=None, exclwnd=None):
        #print 'transition, multiElement==true, childrenClip==false', self
        if exclwnd==self: return

        # paint transition surface
        self.bltDDS(self._drawsurf)

    # delta helpers for the next method
    def __getDC(self, dds):
        hdc = dds.GetDC()
        return wingdi.CreateDCFromHandle(hdc)

    def __releaseDC(self, dds, dc):
        hdc = dc.Detach()
        dds.ReleaseDC(hdc)

    # transition, multiElement==true, childrenClip==true
    # trans engine: calls self.paintOnDDS(self._drawsurf, self)
    # i.e. trans engine is responsible to paint correctly everything below
    def _paint_3(self, rc=None, exclwnd=None):
        #print 'transition, multiElement==true, childrenClip==true',self
        #print self._subwindows

        if exclwnd==self: return

        # 1. and then a _paint_2 but on ChildrenRgnComplement
        # use GDI to paint transition surface
        # (gdi supports clipping but surface bliting not)
        src = self._drawsurf
        dst = self._topwindow.getDrawBuffer()

        dstDC = self.__getDC(dst)
        srcDC = self.__getDC(src)

        rgn = self.getChildrenRgnComplement(self._topwindow)
        dstDC.SelectClipRgn(rgn)
        x, y, w, h = self.getwindowpos()
        try:
            dstDC.BitBlt((x, y),(w, h),srcDC,(0, 0), win32con.SRCCOPY)
        except ddraw.error, arg:
            print arg
        self.__releaseDC(dst,dstDC)
        self.__releaseDC(src,srcDC)
        rgn.DeleteObject()

        # 2. do a normal painting to paint children
        L = self._subwindows[:]
        L.reverse()
        for w in L:
            if w!=exclwnd:
                w.paint(rc, exclwnd)

        # what about other elements in transition?
        # this has to be resolved
#               if self._transition:
#                       L = self._transition.windows[1:]
#                       L.reverse()
#                       for wnd in L:
#                               wnd._paint_0(rc, exclwnd)


    # paint while frozen
    def _paint_4(self, rc=None, exclwnd=None):
        #print 'paint while frozen'
        if exclwnd==self: return
        if not self._fromsurf.IsLost():
            self.bltDDS(self._fromsurf)

    def paint(self, rc=None, exclwnd=None):
        if not self._isvisible or exclwnd==self:
            return

        if self._transition and self._transition._isrunning():
            if self._transition._ismaster(self):
                if self._multiElement:
                    if self._childrenClip:
                        self._paint_3(rc, exclwnd)
                    else:
                        self._paint_2(rc, exclwnd)
                else:
                    self._paint_1(rc, exclwnd)
            return

        self._paint_0(rc, exclwnd)

    def createDDS(self, w=0, h=0):
        if w==0 or h==0:
            x, y, w, h = self._rect
        return self._topwindow.CreateSurface(w,h)

    def setvideo(self, dds, rcDst, rcSrc):
        self._redrawdds = dds, rcDst, rcSrc

    def removevideo(self):
        self._redrawdds = None

    def setredrawdds(self, dds, rcDst = None, rcSrc = None):
        if dds is None:
            self._redrawdds = None
        else:
            self._redrawdds = dds, rcDst, rcSrc

    #
    # Animations interface
    #
    def updatecoordinates(self, coordinates, units=UNIT_PXL, fit=None, mediacoords=None):
        # first convert any coordinates to pixel
        if units != UNIT_PXL:
            coordinates = self._convert_coordinates(coordinates, units=units)

        # keep old pos
        x1, y1, w1, h1 = self.getwindowpos()

        x, y, w, h = coordinates
        self.setmediadisplayrect(mediacoords)

        # resize/move
        self._rect = 0, 0, w, h # client area in pixels
        self._canvas = 0, 0, w, h # client canvas in pixels
        self._rectb = x, y, w, h  # rect with respect to parent in pixels
        self._sizes = self._parent._pxl2rel(self._rectb) # rect relative to parent

        # find update rc
        rc1 = x1, y1, w1, h1
        rc2 = self.getwindowpos()
        rc = self.rectOr(rc1, rc2)
        self._topwindow.update(rc=rc)

        # update the pos of any os subwindows
        self.updateoswndpos()

    def updatezindex(self, z):
        self._z = z
        parent = self._parent
        parent._subwindows.remove(self)
        for i in range(len(parent._subwindows)):
            if self._z >= parent._subwindows[i]._z:
                parent._subwindows.insert(i, self)
                break
        else:
            parent._subwindows.append(self)
        self._parent.update()

    def updatebgcolor(self, color):
        self.bgcolor(color)
        if self._active_displist:
            self._active_displist.updatebgcolor(color)
        self.update()

    #
    # Transitions interface
    #
    def begintransition(self, outtrans, runit, dict, cb):
        if self._transition:
            print 'Multiple Transitions!'
            if cb:
                apply(apply, cb)
            return
        if runit:
            self._multiElement = dict.get('coordinated')
            self._childrenClip = dict.get('clipBoundary', 'children') == 'children'
            self._transition = win32transitions.TransitionEngine(self, outtrans, runit, dict, cb)
            # uncomment the next line to freeze things
            # at the moment begintransition is called
            self._transition.begintransition()
        else:
            self._multiElement = 0
            self._childrenClip = 0
            self._transition = win32transitions.InlineTransitionEngine(self, outtrans, runit, dict, cb)
            self._transition.begintransition()

    def endtransition(self):
        if self._transition:
            #print 'endtransition', self
            self._transition.endtransition()
            self._transition = None

    def jointransition(self, window, cb):
        # Join the transition already created on "window".
        if not window._transition:
            print 'Joining without a transition', self, window, window._transition
            return
        if self._transition:
            print 'Multiple Transitions!'
            return
        ismaster = self._windowlevel() < window._windowlevel()
        self._transition = window._transition
        self._transition.join(self, ismaster, cb)

    def settransitionvalue(self, value):
        if self._transition:
            #print 'settransitionvalue', value
            self._transition.settransitionvalue(value)
        else:
            print 'settransitionvalue without a transition'

    def _windowlevel(self):
        # Returns 0 for toplevel windows, 1 for children of toplevel windows, etc
        prev = self
        count = 0
        while not prev==prev._topwindow:
            count = count + 1
            prev = prev._parent
        return count

## ###########################

class Viewport(Region):
    def __init__(self, context, x, y, width, height, bgcolor):
        Region.__init__(self, None, (x,y,width, height), 0, 0, UNIT_PXL, bgcolor)

        # adjust some variables
        self._topwindow = self

        # cache for easy access
        self._width = width
        self._height = height

        self._ctx = context

    def __repr__(self):
        return '<Viewport instance at %x>' % id(self)

    def _convert_color(self, color):
        return color

    def getwindowpos(self, rel=None):
        return self._rectb

    def offsetospos(self, rc):
        x, y, w, h = rc
        X, Y, W, H = self._ctx.getwindowpos()
        return X+x, Y+y, w, h

    def CreateSurface(self, w, h):
        return self._ctx.CreateSurface(w, h)

    def pop(self, poptop=1):
        self._ctx.pop(poptop)

    def getContextOsWnd(self):
        try:
            return self._ctx.getContextOsWnd()
        except:
            return self._ctx

    def setcursor(self, strid):
        self._ctx.setcursor(strid)

    def close(self):
        if self._ctx is None:
            return
        for win in self._subwindows[:]:
            win.close()
        for dl in self._displists[:]:
            dl.close()
        del self._topwindow
        self._ctx.closeViewport(self)
        self._ctx = None

    def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
        return Region(self, coordinates, transparent, z, units, bgcolor)
    newcmwindow = newwindow

    #
    # Query section
    #
    def is_closed(self):
        return self._ctx is None

    def getClipRgn(self, rel=None):
        x, y, w, h = self._rectb
        return wingdi.CreateRectRgn((x,y,x+w,y+h))

    def getDrawBuffer(self):
        return self._ctx.getDrawBuffer()

    def getPixelFormat(self):
        return self._ctx.getPixelFormat()

    def getDirectDraw(self):
        return self._ctx.getDirectDraw()

    def getRGBBitCount(self):
        return self._ctx.getRGBBitCount()

    def getContext(self):
        return self._ctx
    #
    # Painting section
    #
    def update(self, rc=None, exclwnd=None):
        self._ctx.update(rc, exclwnd)

    def paint(self, rc=None, exclwnd=None):
        drawBuffer = self._ctx.getDrawBuffer()

        if rc is None:
            rcPaint = self._rectb
        else:
            rcPaint = self.rectAnd(rc, self._rectb)

        # check for empty update
        if rcPaint[2]==0 or rcPaint[3]==0:
            return

        # first paint self
        try:
            self._paintOnDDS(drawBuffer, rcPaint)
        except ddraw.error, arg:
            print arg
            return

        # then paint children bottom up
        L = self._subwindows[:]
        L.reverse()
        for w in L:
            if w!=exclwnd:
                w.paint(rc, exclwnd)

    #
    # Mouse section
    #
    def updateMouseCursor(self):
        self._ctx.updateMouseCursor()

    def getgrinsdoc(self):
        return self._ctx.getgrinsdoc()

    def onMouseEvent(self, point, event, params=None):
        import WMEVENTS
        for w in self._subwindows:
            if w.inside(point):
                if event == WMEVENTS.Mouse0Press:
                    w._onlbuttondown(point)
                elif event == WMEVENTS.Mouse0Release:
                    w._onlbuttonup(point)
                break
        return Region.onMouseEvent(self, point, event)

    def onMouseMove(self, flags, point):
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


## ########################
class DesktopViewportContext:
    def __init__(self, wnd, w, h, units, bgcolor):

        self._viewport = Viewport(self, 0, 0, w, h, bgcolor)
        self._rect = 0, 0, w, h

        self._wnd = wnd
        self._bgcolor = bgcolor or (0, 0, 0)

        import winuser
        desktop = winuser.GetDesktopWindow()

        self._ddraw = ddraw.CreateDirectDraw()
        self._ddraw.SetCooperativeLevel(desktop.GetSafeHwnd(), ddraw.DDSCL_NORMAL)

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
        self._frontBuffer = self._ddraw.CreateSurface(ddsd)
        self._pxlfmt = self._frontBuffer.GetPixelFormat()

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w, h)
        self._backBuffer = self._ddraw.CreateSurface(ddsd)

        self._ddbgcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255,255,255))
        self._backBuffer.BltFill((0, 0, w, h), self._ddbgcolor)

    def destroyDDLayer(self):
        if self._ddraw:
            del self._frontBuffer
            del self._backBuffer
            #del self._clipper
            del self._ddraw
            self._ddraw = None
        import winuser
        desktop = winuser.GetDesktopWindow()
        desktop.RedrawWindow(None, 0, 0)

    def update(self, rc=None, exclwnd=None):
        if self._backBuffer.IsLost():
            if not self._backBuffer.Restore():
                return

        # do we have anything to update?
        if rc and (rc[2]==0 or rc[3]==0):
            return

        if rc is None:
            x, y, w, h = self._viewport._rectb
            rcPaint = x, y, x+w, y+h
        else:
            rcPaint = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]
        try:
            self._backBuffer.BltFill(rcPaint, self._ddbgcolor)
        except ddraw.error, arg:
            print arg
            return

        if self._viewport:
            self._viewport.paint(rc, exclwnd)

        self.update_screen()

    def setcursor(self, strid):
        pass

    def getRGBBitCount(self):
        return self._pxlfmt[0]

    def getPixelFormat(self):
        returnself._pxlfmt

    def getDirectDraw(self):
        return self._ddraw

    def getContextOsWnd(self):
        return self._wnd

    def pop(self, poptop=1):
        pass

    def getwindowpos(self):
        return self._viewport._rect

    def closeViewport(self, viewport):
        del viewport
        self.destroyDDLayer()

    def getDrawBuffer(self):
        return self._backBuffer

    def updateMouseCursor(self):
        pass

    def getgrinsdoc(self):
        if self._wnd:
            return self._wnd.getgrinsdoc(file)

    def CreateSurface(self, w, h):
        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w,h)
        dds = self._ddraw.CreateSurface(ddsd)
        dds.BltFill((0, 0, w, h), self._ddbgcolor)
        return dds

    def update_screen(self):
        import winkernel
        if not self._ddraw or not self._frontBuffer or not self._backBuffer:
            return
        if self._frontBuffer.IsLost():
            winkernel.Sleep(0)
            if not self._frontBuffer.Restore():
                # we can't do anything for this
                # system is busy with video memory
                return
        if self._backBuffer.IsLost():
            winkernel.Sleep(0)
            if not self._backBuffer.Restore():
                # and for this either
                # system should be out of memory
                return
        rcFront = rcBack = self._rect
        try:
            self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)
        except ddraw.error, arg:
            print 'PlayerView.update', arg

## ############

class ViewportContext:
    def __init__(self, wnd, w, h, units, bgcolor):

        self._viewport = Viewport(self, 0, 0, w, h, bgcolor)
        self._rect = 0, 0, w, h

        self._wnd = wnd
        self._bgcolor = bgcolor or (0, 0, 0)

        self._ddraw = ddraw.CreateDirectDraw()
        self._ddraw.SetCooperativeLevel(wnd.GetSafeHwnd(), ddraw.DDSCL_NORMAL)

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
        self._frontBuffer = self._ddraw.CreateSurface(ddsd)
        self._pxlfmt = self._frontBuffer.GetPixelFormat()

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w, h)
        self._backBuffer = self._ddraw.CreateSurface(ddsd)

        self._clipper = self._ddraw.CreateClipper(wnd.GetSafeHwnd())
        self._frontBuffer.SetClipper(self._clipper)

        self._ddbgcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255,255,255))
        self._backBuffer.BltFill((0, 0, w, h), self._ddbgcolor)

        self._wnd.HookMessage(self.OnPaint, win32con.WM_PAINT)

    def OnPaint(self, params):
        ps = self._wnd.BeginPaint()
        self._wnd.EndPaint(ps)
        self.update()

    def destroyDDLayer(self):
        if self._ddraw:
            del self._frontBuffer
            del self._backBuffer
            del self._clipper
            del self._ddraw
            self._ddraw = None

    def update(self, rc=None, exclwnd=None):
        if self._backBuffer.IsLost():
            if not self._backBuffer.Restore():
                return

        # do we have anything to update?
        if rc and (rc[2]==0 or rc[3]==0):
            return

        if rc is None:
            x, y, w, h = self._viewport._rectb
            rcPaint = x, y, x+w, y+h
        else:
            rcPaint = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]
        try:
            self._backBuffer.BltFill(rcPaint, self._ddbgcolor)
        except ddraw.error, arg:
            print arg
            return

        if self._viewport:
            self._viewport.paint(rc, exclwnd)

        self.update_screen()

    def setcursor(self, strid):
        pass

    def getRGBBitCount(self):
        return self._pxlfmt[0]

    def getPixelFormat(self):
        returnself._pxlfmt

    def getDirectDraw(self):
        return self._ddraw

    def getContextOsWnd(self):
        return self._wnd

    def pop(self, poptop=1):
        pass

    def getwindowpos(self):
        return self._viewport._rect

    def closeViewport(self, viewport):
        del viewport
        self.destroyDDLayer()

    def getDrawBuffer(self):
        return self._backBuffer

    def updateMouseCursor(self):
        pass

    def getgrinsdoc(self):
        return None

    def CreateSurface(self, w, h):
        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w,h)
        dds = self._ddraw.CreateSurface(ddsd)
        dds.BltFill((0, 0, w, h), self._ddbgcolor)
        return dds

    def update_screen(self):
        import winkernel
        if not self._ddraw or not self._frontBuffer or not self._backBuffer:
            return
        if self._frontBuffer.IsLost():
            winkernel.Sleep(0)
            if not self._frontBuffer.Restore():
                # we can't do anything for this
                # system is busy with video memory
                return
        if self._backBuffer.IsLost():
            winkernel.Sleep(0)
            if not self._backBuffer.Restore():
                # and for this either
                # system should be out of memory
                return

        rcBack = self._rect
        rcFront = self._wnd.ClientToScreen(rcBack)
        try:
            self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)
        except ddraw.error, arg:
            print 'ViewportContext.update', arg

## #######################
# helpers

import grinsRC
import winuser
from __main__ import resdll

def getcursorhandle(strid):
    if strid == 'hand':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_POINT_HAND)
    elif strid == 'darrow':
        cursor = winuser.LoadStandardCursor(win32con.IDC_SIZEWE)
    elif strid == 'channel':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_DRAGMOVE)
    elif strid == 'stop':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_STOP)
    elif strid == 'link':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_DRAGLINK)
    elif strid == 'draghand':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_DRAG_HAND)
    elif strid == 'sizenwse':
        cursor = winuser.LoadStandardCursor(win32con.IDC_SIZENWSE)
    elif strid == 'sizens':
        cursor = winuser.LoadStandardCursor(win32con.IDC_SIZENS)
    elif strid == 'sizenesw':
        cursor = winuser.LoadStandardCursor(win32con.IDC_SIZENESW)
    elif strid == 'sizewe':
        cursor = winuser.LoadStandardCursor(win32con.IDC_SIZEWE)
    elif strid == 'cross':
        cursor = winuser.LoadStandardCursor(win32con.IDC_CROSS)
    else:
        cursor = winuser.LoadStandardCursor(win32con.IDC_ARROW)
    return cursor
