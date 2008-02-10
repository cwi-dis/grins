__version__ = "$Id$"

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
