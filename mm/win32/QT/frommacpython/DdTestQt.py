# Qt sample using direct draw

import Qt

import sys
sys.path.append(r'D:\ufs\mm\cmif\lib\win32')
import winqtcon

import win32ui, win32api, win32con
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

import ddraw

from pywin.mfc import window

class MfcOsWnd(window.Wnd):
    """Generic MfcOsWnd class"""
    def __init__ (self):
        window.Wnd.__init__(self,win32ui.CreateWnd())
        self._clstyle=0
        self._style=0
        self._exstyle=0
        self._icon=0
        self._cursor=0
        self._brush=0

    def setClstyle(self,clstyle):
        self._clstyle=clstyle

    def setStyle(self,style):
        self._style=style

    def setExstyle(self,exstyle):
        self._exstyle=exstyle

    def setIcon(self,icon):
        self._icon=icon

    def setIconApplication(self):
        self._icon=Afx.GetApp().LoadIcon(win32con.IDI_APPLICATION)

    def setStandardCursor(self,cursor):
        self._cursor=Afx.GetApp().LoadStandardCursor(cursor)

    def setStockBrush(self,idbrush):
        self._brush=Sdk.GetStockObject(idbrush)
    def setBrush(self,brush):
        self._brush=brush

    def create(self,title='untitled',x=0,y=0,width=200,height=150,parent=None,id=0):
        # register
        strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
        # create
        self.CreateWindowEx(self._exstyle,strclass,title,self._style,
                (x, y, width, height),parent,id)

class ToplevelWnd(MfcOsWnd):
    """Generic ToplevelWnd class"""
    def __init__ (self):
        MfcOsWnd.__init__(self)
        self._clstyle=win32con.CS_DBLCLKS
        self._style=win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
        self._exstyle=win32con.WS_EX_CLIENTEDGE

    def setClientRect(self, w, h):
        l1, t1, r1, b1 = self.GetWindowRect()
        l2, t2, r2, b2 = self.GetClientRect()
        dxe = dye = 0
        if (self._exstyle & win32con.WS_EX_CLIENTEDGE):
            dxe = 2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
            dye = 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
        wi = (r1-l1) - (r2-l2)
        wp = w + wi + dxe
        hi = (b1-t1) - (b2-t2)
        hp = h + hi + dye
        flags=win32con.SWP_NOMOVE | win32con.SWP_NOZORDER
        self.SetWindowPos(0, (0,0,wp,hp), flags)

class QTWnd(MfcOsWnd):
    TIMER_TICK = 20

    def __init__ (self, bgcolor = (255, 0, 255)):
        MfcOsWnd.__init__(self, )
        self._clstyle=win32con.CS_DBLCLKS
        self._style = win32con.WS_CHILD |win32con.WS_CLIPSIBLINGS
        self.port = None
        self.movie = None
        self.ctrl = None
        self.__timer_id = 0

        self.__ddraw = None
        self.__frontBuffer = None
        self.__backBuffer = None
        self.__clipper = None
        self.__bgcolor = bgcolor

        self.__movieBuffer = None

        # movie position and size
        self._movieRect = 80, 60, 240, 180

    def OnCreate(self, params):
        # back buffer size
        w, h = self.GetClientRect()[2:]

        self.__ddraw = ddraw.CreateDirectDraw()

        self.__ddraw.SetCooperativeLevel(self.GetSafeHwnd(), ddraw.DDSCL_NORMAL)

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
        self.__frontBuffer = self.__ddraw.CreateSurface(ddsd)

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w,h)
        self.__backBuffer = self.__ddraw.CreateSurface(ddsd)

        self.__clipper = self.__ddraw.CreateClipper(self.GetSafeHwnd())
        self.__frontBuffer.SetClipper(self.__clipper)
        self._pxlfmt = self.__frontBuffer.GetPixelFormat()

        # clear back buffer
        ddcolor = self.__backBuffer.GetColorMatch(self.__bgcolor or (255, 255, 255) )
        self.__backBuffer.BltFill((0, 0, w, h), ddcolor)

        self.createDirectDrawQt(self.__ddraw, self._movieRect[2:])

        self.HookMessage(self.OnTimer,win32con.WM_TIMER)
        self.__timer_id = self.SetTimer(1, self.TIMER_TICK)

    def createDirectDrawQt(self, ddobj, size):
        w, h = size
        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w, h)
        self.__movieBuffer = ddobj.CreateSurface(ddsd)

        Qt.InitializeQTML()
        Qt.EnterMovies()
        Qt.SetDDObject(ddobj)
        Qt.SetDDPrimarySurface(self.__movieBuffer)

        fn = 'D:\\ufs\\mm\\cmif\\win32\\Qt\\media\\fashion.mov'
        try:
            movieResRef = Qt.OpenMovieFileWin(fn, 1)
        except Exception, arg:
            print arg
            return

        try:
            self.movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0, 0)
        except Exception, arg:
            print arg
        Qt.CloseMovieFile(movieResRef)

        print 'dur =', 0.001*self.movie.GetMovieDuration(), 'sec'
        print 'box =',  self.movie.GetMovieBox()

        self.movie.SetMovieBox((0, 0, w, h))
        self.movie.SetMovieActive(1)
        self.movie.StartMovie()

    def OnTimer(self, params):
        if self.movie:
            self.movie.MoviesTask(0)
            self.movie.UpdateMovie()

        # back buffer size
        sd = self.__backBuffer.GetSurfaceDesc()
        w, h = sd.GetSize()

        # clear back buffer
        ddcolor = self.__backBuffer.GetColorMatch(self.__bgcolor or (255, 255, 255) )
        self.__backBuffer.BltFill((0, 0, w, h), ddcolor)

        # plot movie buffer to back buffer
        flags = ddraw.DDBLT_WAIT
        mx, my, mw, mh = self._movieRect
        self.__backBuffer.Blt((mx, my, mx+mw, my+mh), self.__movieBuffer, (0, 0, mw, mh), flags)

        # flip
        rcFront = self.GetClientRect()
        rcFront = self.ClientToScreen(rcFront)
        rcBack = (0, 0, w, h)
        self.__frontBuffer.Blt(rcFront, self.__backBuffer, rcBack)

    def OnDestroy(self, params):
        if self.__timer_id:
            self.KillTimer(self.__timer_id)
        if self.movie:
            self.movie.StopMovie()
        del self.movie
        Qt.ExitMovies()
        Qt.TerminateQTML()
        del self.__movieBuffer
        del self.__frontBuffer
        del self.__backBuffer
        del self.__clipper
        del self.__ddraw

    def OnPaint(self):
        dc, paintStruct = self.BeginPaint()
        self.EndPaint(paintStruct)


def __test():
    wnd = ToplevelWnd()
    wnd.setStockBrush(win32con.WHITE_BRUSH)
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create('GRiNS Lab',win32con.CW_USEDEFAULT,win32con.CW_USEDEFAULT,400,300)

    w = 400
    h = 300
    wnd.setClientRect(w, h)

    childwnd = QTWnd()
    childwnd.setStockBrush(win32con.WHITE_BRUSH)
    childwnd.setStandardCursor(win32con.IDC_ARROW)
    childwnd.create('qtchannel',0,0,w,h, wnd)

    wnd.ShowWindow(win32con.SW_SHOW)
    childwnd.ShowWindow(win32con.SW_SHOW)
    wnd.UpdateWindow()

if __name__ == '__main__':
    __test()
