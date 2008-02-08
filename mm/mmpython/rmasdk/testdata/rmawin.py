
import win32ui,win32api,win32con
import traceback

Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

def SafeCallbackCaller(fn, args):
    try:
        return apply(fn, args)
    except SystemExit, rc:
        # We trap a system exit, and translate it to the "official" way to bring down a GUI.
        try:
            rc = int(rc[0])
        except (ValueError, TypeError):
            rc = 0
        import win32api
        win32api.PostQuitMessage(rc)
    except:
        # We trap all other errors, ensure the main window is shown, then
        # print the traceback.
        try:
            win32ui.GetMainFrame().ShowWindow(win32con.SW_SHOW)
        except win32ui.error:
            print "Cant show the main frame!"
        traceback.print_exc()
        return

win32ui.InstallCallbackCaller(SafeCallbackCaller)


class Win32Msg:
    def __init__(self,params):
        self._hwnd,self._message,self._wParam,self._lParam,self._time,self._pt=params
    def LOWORD_wParam(self):
        return win32api.LOWORD(self._wParam)
    def HIWORD_wParam(self):
        return win32api.HIWORD(self._wParam)
    def LOWORD_lParam(self):
        return win32api.LOWORD(self._lParam)
    def HIWORD_lParam(self):
        return win32api.HIWORD(self._lParam)

    def loword(self):
        return win32api.LOWORD(self._lParam)
    def hiword(self):
        return win32api.HIWORD(self._lParam)

    def width(self):
        return win32api.LOWORD(self._lParam)
    def height(self):
        return win32api.HIWORD(self._lParam)

    def hpos(self):
        return win32api.LOWORD(self._lParam)
    def vpos(self):
        return win32api.HIWORD(self._lParam)
    def pos(self):
        return (win32api.LOWORD(self._lParam),win32api.HIWORD(self._lParam))

    def sizeType(self):
        return self._wParam
    def keyFlags(self):
        return self._wParam

    def minimized(self):
        if (self._wParam & win32con.SIZE_MINIMIZED):
            return 1
        return 0
    def maximized(self):
        if (self._wParam & win32con.SIZE_MAXIMIZED):
            return 1
        return 0

    def cmdid(self): return self.LOWORD_wParam()

    def getcontrolid(self): return self.LOWORD_wParam()
    def getnmsg(self): return self.HIWORD_wParam()
    def gethandle(self): return self._lParam

    def nmhdr(self): return Sdk.CrackNMHDR(self._lParam)

    def __repr__(self):
        s='message=%d wparam=%d lparam=%d' % (self._message,self._wParam,self._lParam)
        return '<%s instance, %s>' % (self.__class__.__name__, s)


## ###########################
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


class ChildWindow(MfcOsWnd):
    """Generic ChildWindow class"""
    def __init__ (self):
        MfcOsWnd.__init__(self)
        self._clstyle=win32con.CS_DBLCLKS
        self._style=win32con.WS_CHILD |win32con.WS_CLIPSIBLINGS
        self._rect=(0,0,1,1)
        self._can_change_size=0
        self._show_frame=0

    def AllowResize(self,f):
        self._can_change_size=f

    def ShowFrame(self,f):
        self._show_frame=f

    def OnPaint(self):
        dc, paintStruct = self.BeginPaint()
        self.DoPaint(dc)
        self.EndPaint(paintStruct)

    def OnCreate(self,params):
        self._rect=self.GetClientRect();
        self.HookMessage(self.OnSize,win32con.WM_SIZE)

    def OnSize(self,params):
        if self._can_change_size: return
        msg=Win32Msg(params)
        l,t,r,b=self._rect
        self.SetWindowPos(self.GetSafeHwnd(),(0,0,r,b),
                win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)

    def DoPaint(self, dc):
        if not self._show_frame: return
        rc=self.GetClientRect()
        br=Sdk.CreateBrush(win32con.BS_SOLID,win32api.RGB(255,0,0),0)
        dc.FrameRectFromHandle(rc,br)
        Sdk.DeleteObject(br)

    def OnEraseBkgnd(self,dc):
        parent = self.GetParent()
        ptList=[(0,0),]
        ptOffset = self.MapWindowPoints(parent,ptList)[0]
        ptOldOrg=dc.OffsetWindowOrg(ptOffset)
        parent.SendMessage(win32con.WM_ERASEBKGND,dc.GetSafeHdc())
        dc.SetWindowOrg(ptOldOrg)
        return 1



def CreateTopLevelWnd(x,y,w,h,title='GRiNS Lab'):
    wnd=ToplevelWnd()
    wnd.setStockBrush(win32con.LTGRAY_BRUSH)
    #wnd.setIcon(Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED))
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create(title,x,y,w,h)
    wnd.ShowWindow(win32con.SW_SHOW)
    return wnd

def CreateChildWnd(parent,x,y,w,h,title='channel'):
    wnd=ChildWindow()
    wnd.setStockBrush(win32con.WHITE_BRUSH)
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create(title,x,y,x+w,y+h,parent)
    wnd.ShowWindow(win32con.SW_SHOW)
    return wnd


# real audio
url1="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/thanks3.ra"

# real video
url2="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/test.rv"

# real text
url3="file://D|/ufs/mm/cmif/mmpython/rmasdk/testdata/news.rt"

# real pixel
url4="file:///D|/ufs/mm/cmif/mmpython/rmasdk/testdata/fadein.rp"

player=None

def Test1():
    global player
    import rma
    player=rma.CreatePlayer()
    player.OpenURL(url2)
    player.Begin()

def Test2():
    wnd=CreateTopLevelWnd(50,50,400,400)
    childwnd=CreateChildWnd(wnd,50,50,50+200,50+200)

    childwnd.AllowResize(1)
    childwnd.ShowFrame(0)

    import rma
    global player
    player=rma.CreatePlayer()
    player.SetOsWindow(childwnd.GetSafeHwnd())
    # player.ShowInNewWindow(1)
    player.OpenURL(url4)
    player.Begin()


Test2()
