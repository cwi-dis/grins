import ddraw

# init COM libs
ddraw.CoInitialize()

from wincr import *
import gear32sd

class DDWnd(MfcOsWnd):
    def __init__ (self):
        MfcOsWnd.__init__(self)
        self._clstyle=win32con.CS_DBLCLKS
        self._style=win32con.WS_CHILD |win32con.WS_CLIPSIBLINGS

    def OnCreate(self, params):
        self.__ddraw = ddraw.CreateDirectDraw()

        self.__ddraw.SetCooperativeLevel(self.GetSafeHwnd(), ddraw.DDSCL_NORMAL)

        self.__frontBuffer = self.__ddraw.CreateSurface()
        self.__backBuffer = self.__ddraw.CreateSurface(400,300)

        self.__clipper = self.__ddraw.CreateClipper(self.GetSafeHwnd())
        self.__frontBuffer.SetClipper(self.__clipper)

        self.__init_it()
        self.HookMessage(self.OnTimer,win32con.WM_TIMER)
        self.__timer_id = self.SetTimer(1,20)

    def OnDestroy(self, params):
        self.KillTimer(self.__timer_id)
        del self.__objBuffer
        del self.__frontBuffer
        del self.__backBuffer
        del self.__clipper
        del self.__ddraw

    def OnEraseBkgnd(self, params):
        return 1

    def OnTimer(self, params):
        sd = self.__backBuffer.GetSurfaceDesc()
        w, h = sd.GetSize()

        hdc = self.__backBuffer.GetDC()
        dc = win32ui.CreateDCFromHandle(hdc)
        dc.PatBlt( (0, 0), (w, h), win32con.BLACKNESS)
        dc.Detach()
        self.__backBuffer.ReleaseDC(hdc)

        rc = self.__x, self.__y, self.__x + self.__cx, self.__y + self.__cy
        flags = ddraw.DDBLT_WAIT | ddraw.DDBLT_KEYSRC
        self.__backBuffer.Blt(rc, self.__objBuffer, (0, 0, self.__cx, self.__cy), flags)

        rcFront = self.GetClientRect()
        rcFront = self.ClientToScreen(rcFront)
        rcBack = (0, 0, w, h)

        self.__frontBuffer.Blt(rcFront, self.__backBuffer, rcBack)
        self.__advance(rcBack)

    def __init_it(self):
        self.__x = 0
        self.__y = 0
        self.__vx = 4 # horiz velocity
        self.__vy = 4 # vert velocity

        # init animated object
        filename = r'D:\ufs\mm\cmif\win32\DXMedia\ddraw\test\mark.bmp'
        self.__img = gear32sd.load_file(filename)
        if self.__img:
            self.__cx, self.__cy, depth = gear32sd.image_dimensions_get(self.__img)

        self.__objBuffer = self.__ddraw.CreateSurface(self.__cx, self.__cy)
        hdc = self.__objBuffer.GetDC()
        if self.__img>=0:
            rc = (0, 0, self.__cx, self.__cy)
            gear32sd.device_rect_set(self.__img,rc)
            gear32sd.display_desktop_pattern_set(self.__img,0)
            gear32sd.display_image(self.__img,hdc)
        self.__objBuffer.ReleaseDC(hdc)

        # set source colorkey to black
        self.__objBuffer.SetColorKey(ddraw.DDCKEY_SRCBLT, (0, 0))

    def __advance(self, rc):
        x, y, vx, vy = self.__x, self.__y,self.__vx, self.__vy
        x  = x + vx
        if vx > 0:
            if x + self.__cx > rc[2]:
                vx = -vx
                x = rc[2] - self.__cx
        else:
            if x < 0:
                vx = -vx
                x = 0
        y = y + vy;
        if vy > 0:
            if y + self.__cy > rc[3]:
                vy = -vy
                y = rc[3] - self.__cy
        else:
            if y < 0:
                vy = -vy
                y = 0
        self.__x, self.__y,self.__vx, self.__vy = x, y, vx, vy


def __test():
    wnd = ToplevelWnd()
    wnd.setStockBrush(win32con.WHITE_BRUSH)
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create('GRiNS Lab',0,0,400,300)

    childwnd=DDWnd()
    childwnd.setStockBrush(win32con.WHITE_BRUSH)
    childwnd.setStandardCursor(win32con.IDC_ARROW)
    childwnd.create('ddchannel',0,0,400,300, wnd)

    wnd.ShowWindow(win32con.SW_SHOW)
    childwnd.ShowWindow(win32con.SW_SHOW)
    wnd.UpdateWindow()

if __name__ == '__main__':
    __test()
