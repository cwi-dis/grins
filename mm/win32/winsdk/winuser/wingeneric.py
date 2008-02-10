__version__ = "$Id$"

import sys

import winuser, wingdi, win32con

class GenericWnd:
    def __init__(self):
        self.__dict__['_obj_'] = None
        self._title = 'GRiNS Lab'
        self._timer = 0

    def __getattr__(self, attr):
        try:
            if attr != '__dict__':
                o = self.__dict__['_obj_']
                if o:
                    return getattr(o, attr)
        except KeyError:
            pass
        raise AttributeError, attr

    def create(self):
        wndclassname = 'MainWnd'
        winuser.RegisterClassEx(wndclassname)

        exstyle = win32con.WS_EX_CLIENTEDGE
        style = win32con.WS_VISIBLE | win32con.WS_OVERLAPPEDWINDOW
        wnd = winuser.CreateWindowEx(exstyle, wndclassname, self._title, style, (0, 0), (400, 300))
        self.__dict__['_obj_'] = wnd

        menu = self.createMenu()
        self.SetMenu(menu)
        self.DrawMenuBar()

        self.HookMessages()

        self._timer = self.SetTimer(1, 1000)


    def HookMessages(self):
        self.HookMessage(self.OnLButtonDown, win32con.WM_LBUTTONDOWN)
        self.HookMessage(self.OnLButtonDblClk, win32con.WM_LBUTTONDBLCLK)
        self.HookMessage(self.OnRButtonDown, win32con.WM_RBUTTONDOWN)
        #self.HookMessage(self.OnMouseMove, win32con.WM_MOUSEMOVE)
        self.HookMessage(self.OnPaint, win32con.WM_PAINT)
        self.HookMessage(self.OnDestroy, win32con.WM_DESTROY)
        self.HookMessage(self.OnClose, win32con.WM_CLOSE)
        self.HookMessage(self.OnCommand, win32con.WM_COMMAND)
        self.HookMessage(self.OnTimer, win32con.WM_TIMER)

    def OnCommand(self, params):
        cmdid = Win32Msg(params).id()
        print 'OnCommand', cmdid
        if cmdid == 106: # CM_EXIT
            self.PostMessage(win32con.WM_CLOSE)

    def OnTimer(self, params):
        print 'OnTimer'

    def OnDestroy(self, params):
        print 'OnDestroy'
        if self._timer:
            self.KillTimer(self._timer)
        del self.__dict__['_obj_']
        self.__dict__['_obj_'] = None

    def OnClose(self, params):
        print 'OnClose'
        self.DestroyWindow()

    def OnLButtonDown(self, params):
        msg = Win32Msg(params)
        print 'OnLButtonDown', msg.pos()

    def OnLButtonDblClk(self, params):
        msg = Win32Msg(params)
        self.MessageBox("%d %d" % msg.pos(), self._title)

    def OnRButtonDown(self, params):
        msg = Win32Msg(params)
        print 'OnRButtonDown', msg.pos()

    def OnMouseMove(self, params):
        msg = Win32Msg(params)
        print msg.pos()

    def OnPaint(self, params):
        ps = self.BeginPaint()
        hdc = ps[0]
        rc = self.GetClientRect();
        wingdi.DrawText(hdc, "Python generic windows template", rc)
        self.EndPaint(ps)

    def createMenu(self):
        menu = winuser.CreateMenu()
        dropdowns = ('&File', '&View', '&Play', '&Help')
        for i in range(len(dropdowns)):
            submenu = winuser.CreateMenu()
            menu.InsertMenu(i, win32con.MF_BYPOSITION | win32con.MF_POPUP, submenu.GetHandle(), dropdowns[i])

        entries = ('&Open...\tCtrl+O', 'Open &URL...\tCtrl+L', 'Open &recent', 'R&eload',
                '&Preferences...', 'E&xit')
        flags = win32con.MF_STRING | win32con.MF_ENABLED
        submenu = menu.GetSubMenu(0)
        cmdid = 101
        for i in range(len(entries)):
            submenu.AppendMenu(flags, cmdid, entries[i])
            cmdid = cmdid + 1

        return menu

wnd = GenericWnd()
wnd.create()

########################
# helpers

def loword(v):
    return v & 0xFFFF

def hiword(v):
    return (v >> 16) & 0xFFFF

class Win32Msg:
    def __init__(self,params):
        self._hwnd,self._message,self._wParam,self._lParam,self._time,self._pt=params
    def pos(self):
        return loword(self._lParam), hiword(self._lParam)
    def id(self):
        return loword(self._wParam);
