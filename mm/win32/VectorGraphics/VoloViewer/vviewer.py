
import win32ui,win32con
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

# std mfc windows stuff
from pywin.mfc import window

import vview

class VViewer(window.Wnd):
    def __init__(self,parent,rc):
        vv=vview.CreateVViewer()
        vv.CreateWindow(parent.GetSafeHwnd())
        wnd=win32ui.CreateWindowFromHandle(vv.GetSafeHwnd())
        window.Wnd.__init__(self,wnd)
        wnd.SetWindowPos(0, rc, win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
        self._vvctrl=vv

    def SetSource(self,fn):
        if self._vvctrl:
            self._vvctrl.SetSource(fn)


if __name__ == '__main__':
    Afx.OleInit()
    import wndfw
    wnd=wndfw.ToplevelWnd()
    wnd.setStockBrush(win32con.LTGRAY_BRUSH)
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create('VViewer',0,0,400,300)
    viewer=VViewer(wnd,(0,0,400,300))
    viewer.SetSource('D:\\ufs\\mm\\cmif\\win32\\VectorGraphics\\VoloViewer\\vve.dxf')
    wnd.ShowWindow(win32con.SW_SHOW)
