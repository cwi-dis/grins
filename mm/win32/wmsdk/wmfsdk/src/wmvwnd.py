__version__ = "$Id$"

# WMP Export Sample
# export a quite complex scene with video and animation to wmv

# direct draw infrastructure module
import ddraw

# init COM libs
ddraw.CoInitialize()

import win32ui,win32api,win32con
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

# for now we use CDC methods instead of win32 SDK
import win32ui

# image format lib
import gear32sd

# directx media module
import dshow

import win32dxm
audiofg = win32dxm.GraphBuilder()
audiofile = r'D:\ufs\mmdocuments\interop2\interop2\sounds\english.wav'

#
import wmwriter

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

class MMStream:
    def __init__(self, ddobj):
        mmstream = dshow.CreateMultiMediaStream()
        mmstream.Initialize()
        mmstream.AddPrimaryVideoMediaStream(ddobj)
        mmstream.AddPrimaryAudioMediaStream()
        self._mmstream = mmstream
        self._mstream = None
        self._ddstream = None
        self._sample = None
        self._dds = None
        self._rect = None
        self._parsed = 0

    def open(self, url):
        print 'open', url
        mmstream =      self._mmstream
        try:
            self._mmstream.OpenFile(url)
        except:
            print 'failed to render', url
            self._parsed = 0
            return 0
        self._parsed = 1
        self._mstream = self._mmstream.GetPrimaryVideoMediaStream()
        self._ddstream = self._mstream.QueryIDirectDrawMediaStream()
        self._sample = self._ddstream.CreateSample()
        self._dds = ddraw.CreateSurfaceObject()
        self._rect = self._sample.GetSurface(self._dds)
        return 1

    def __del__(self):
        del self._mstream
        del self._ddstream
        del self._sample
        del self._mmstream

    def run(self):
        if self._parsed:
            self._mmstream.SetState(1)

    def stop(self):
        if self._parsed:
            self._mmstream.SetState(0)

    def update(self):
        if not self._parsed: return 0
        return self._sample.Update()

    def seek(self, secs):
        if not self._parsed: return
        if secs==0.0:
            v = dshow.large_int(0)
        else:
            msecs = dshow.large_int(int(secs*1000+0.5))
            f = dshow.large_int('10000')
            v = msecs * f
        try:
            self._mmstream.Seek(v)
        except:
            print 'seek not supported for media type'

    def getDuration(self):
        if not self._parsed: return
        d = self._mmstream.GetDuration()
        f = dshow.large_int('10000')
        v = d / f
        secs = 0.001*float(v)
        return secs

    def getTime(self):
        if not self._parsed: return
        d = self._mmstream.GetTime()
        f = dshow.large_int('10000')
        v = d / f
        secs = 0.001*float(v)
        return secs

import time

class DDWnd(MfcOsWnd):
    def __init__ (self):
        MfcOsWnd.__init__(self)
        self._clstyle=win32con.CS_DBLCLKS
        self._style=win32con.WS_CHILD |win32con.WS_CLIPSIBLINGS | win32con.WS_VISIBLE

        self._mmstream = None

        self._writer = None
        self._start = None
        self._recorded = 0

        self.__ddraw = None
        self.__frontBuffer = None
        self.__backBuffer = None
        self.__clipper = None
        self.__objBuffer = None

        self._w, self._h = 400, 300
        self.__timer_id = 0
        self._audiofg = None

    def OnCreate(self, params):
        w, h = self._w, self._h

        self.__ddraw = ddraw.CreateDirectDraw()
        self.__ddraw.SetCooperativeLevel(self.GetSafeHwnd(), ddraw.DDSCL_NORMAL)

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
        self.__frontBuffer = self.__ddraw.CreateSurface(ddsd)

        self.__clipper = self.__ddraw.CreateClipper(self.GetSafeHwnd())
        self.__frontBuffer.SetClipper(self.__clipper)

        self._pxlfmt = self.__frontBuffer.GetPixelFormat()

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(w, h)
        self.__backBuffer = self.__ddraw.CreateSurface(ddsd)


        url=r'D:\ufs\mm\cmif\Build\common\testdoc\testdatampg.mpg'
        self._mmstream = MMStream(self.__ddraw)
        self._mmstream.open(url)
        self._mmstream.run()


        self.__init_it()
        self.HookMessage(self.OnTimer,win32con.WM_TIMER)
        self.__timer_id = self.SetTimer(1,50)

    def OnDestroy(self, params):
        if self.__timer_id:
            self.KillTimer(self.__timer_id)
        del self._mmstream
        del self.__objBuffer
        del self.__frontBuffer
        del self.__backBuffer
        del self.__clipper
        del self.__ddraw

    def getPixelFormat(self):
        return self._pxlfmt

    def getDrawBuffer(self):
        return self.__backBuffer

    def getClientRect(self):
        l, t, r, b = self.GetClientRect()
        return l, t, r-l, b-t

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

        self._mmstream.update()
        rc = self._mmstream._rect
        self.__backBuffer.Blt((100,100,100+rc[2],100+rc[3]), self._mmstream._dds, rc, ddraw.DDBLT_WAIT)

        rcFront = self.GetClientRect()
        rcFront = self.ClientToScreen(rcFront)
        rcBack = (0, 0, w, h)

        self.__frontBuffer.Blt(rcFront, self.__backBuffer, rcBack)
        self.__advance(rcBack)

        if not self._writer and not self._recorded:
            self._writer = wmwriter.WMWriter(self, self.__backBuffer, profile=20)
            self._writer.setOutputFilename('grsim.wmv')
            self._writer.setAudioFormatFromFile(audiofile)
            self._start = time.time()
            self._writer.beginWriting()
        elif self._writer:
            dt = time.time() - self._start
            self._writer.update(dt)
            if dt>5 and not self._audiofg:
                audiofg.RenderFile(audiofile, self)
                audiofg.Run()
                self._audiofg = audiofg
            if dt>20:
                if self._audiofg:
                    self._audiofg.Stop()
                    self._audiofg = None
                self._writer.endWriting()
                self._writer = None
                self._recorded = 1

    # exporter interface
    def getWriter(self):
        return self._writer

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

        ddsd = ddraw.CreateDDSURFACEDESC()
        ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
        ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
        ddsd.SetSize(self.__cx, self.__cy)
        self.__objBuffer = self.__ddraw.CreateSurface(ddsd)
        hdc = self.__objBuffer.GetDC()
        if self.__img>=0:
            rc = (0, 0, self.__cx, self.__cy)
            gear32sd.device_rect_set(self.__img,rc)
            gear32sd.display_desktop_pattern_set(self.__img,0)
            gear32sd.display_image(self.__img, hdc)
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

def __WMPExport():
    wnd = ToplevelWnd()
    wnd.setStockBrush(win32con.WHITE_BRUSH)
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create('GRiNS Lab',win32con.CW_USEDEFAULT,win32con.CW_USEDEFAULT,400,300)
    wnd.setClientRect(400, 300)

    ddchildwnd = DDWnd()
    ddchildwnd.setStockBrush(win32con.WHITE_BRUSH)
    ddchildwnd.setStandardCursor(win32con.IDC_ARROW)
    ddchildwnd.create('ddchannel',0,0,400,300, wnd)

    wnd.ShowWindow(win32con.SW_SHOW)
    wnd.UpdateWindow()

if __name__ == '__main__':
    __WMPExport()
