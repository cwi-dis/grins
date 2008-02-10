__version__ = "$Id$"

import winuser, wingdi, win32con

class MainWndClass:
    wndclassname = 'MainWnd'
    winuser.RegisterClassEx(wndclassname)

class Wnd:
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
        exstyle = win32con.WS_EX_CLIENTEDGE
        style = win32con.WS_VISIBLE | win32con.WS_OVERLAPPEDWINDOW
        wnd = winuser.CreateWindowEx(exstyle, MainWndClass.wndclassname, self._title, style,
                (win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT), (320, 240))
        self.__dict__['_obj_'] = wnd
        self.HookMessage(self.OnDestroy, win32con.WM_DESTROY)

    def OnDestroy(self, params):
        print 'OnDestroy'
        del self.__dict__['_obj_']
        self.__dict__['_obj_'] = None
