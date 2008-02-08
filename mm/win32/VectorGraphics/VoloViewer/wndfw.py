
import win32ui,win32api,win32con
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()
import os
import sys
import string
import win32api
from win32con import *
import win32ui
import traceback

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
            win32ui.GetMainFrame().ShowWindow(SW_SHOW)
        except win32ui.error:
            print "Cant show the main frame!"
        traceback.print_exc()
        return

win32ui.InstallCallbackCaller(SafeCallbackCaller)




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
        #self._exstyle=win32con.WS_EX_CONTROLPARENT

    def OnPaint(self):
        dc, paintStruct = self.BeginPaint()
        self.DoPaint(dc)
        self.EndPaint(paintStruct)

    def DoPaint(self, dc):
        rc=self.GetClientRect()
        br=Sdk.CreateBrush(win32con.BS_SOLID,win32api.RGB(255,0,0),0)
        dc.FrameRectFromHandle(rc,br)
        Sdk.DeleteObject(br)
        #imageex.display(dc.GetSafeHdc(),self._img,rc2)

    def OnEraseBkgnd(self,dc):
        parent = self.GetParent()
        ptList=[(0,0),]
        ptOffset = self.MapWindowPoints(parent,ptList)[0]
        ptOldOrg=dc.OffsetWindowOrg(ptOffset)
        parent.SendMessage(win32con.WM_ERASEBKGND,dc.GetSafeHdc())
        dc.SetWindowOrg(ptOldOrg)
        return 1

class ChildWindow2(MfcOsWnd):
    """Generic ChildWindow class"""
    def __init__ (self):
        MfcOsWnd.__init__(self)
        self._clstyle=win32con.CS_DBLCLKS
        self._style=win32con.WS_CHILD #|win32con.WS_CLIPSIBLINGS
        self._exstyle=win32con.WS_EX_CONTROLPARENT

    def OnPaint(self):
        dc, paintStruct = self.BeginPaint()
        self.DoPaint(dc)
        self.EndPaint(paintStruct)

    def DoPaint(self, dc):
        rc=self.GetClientRect()
        dc.SetBkMode(win32con.TRANSPARENT)
        dc.SetTextAlign(win32con.TA_BOTTOM)
        dc.SetTextColor(win32api.RGB(255,0,0))
        dc.TextOut(rc[0]+20,rc[1]+(rc[3]-rc[1])/2,"Python rules")

    def OnEraseBkgnd(self,dc):
        parent = self.GetParent()
        ptList=[(0,0),]
        ptOffset = self.MapWindowPoints(parent,ptList)[0]
        ptOldOrg=dc.OffsetWindowOrg(ptOffset)
        parent.SendMessage(win32con.WM_ERASEBKGND,dc.GetSafeHdc())
        dc.SetWindowOrg(ptOldOrg)
        return 1


def _test():
    wnd=ToplevelWnd()
    wnd.setStockBrush(win32con.LTGRAY_BRUSH)
    #wnd.setIcon(Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED))
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create('GRiNS',0,0,400,300)

    childwnd=ChildWindow()
    transparent=0
    if transparent:
        childwnd.setStockBrush(win32con.NULL_BRUSH)
        childwnd.setExstyle(win32con.WS_EX_TRANSPARENT)
    else:
        childwnd.setStockBrush(win32con.WHITE_BRUSH)
    childwnd.setStandardCursor(win32con.IDC_ARROW)

    childwnd.create('channel',100,50,300,200,wnd)

    wnd.ShowWindow(win32con.SW_SHOW)
    childwnd.ShowWindow(win32con.SW_SHOW)

if __name__ == '__main__':
    _test()




class MfcOsWnd2(window.Wnd):
    """Generic MfcOsWnd class"""
    def __init__ (self):
        window.Wnd.__init__(self,win32ui.CreateWnd())
        self._clstyle=0
        self._style=0
        self._exstyle=0
        self._icon=0
        self._cursor=0
        self._brush=0
        self._active_displist=None

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

    def setBrush(self,brush):
        self._brush=brush

    def setStockBrush(self,idbrush):
        self._brush=Sdk.GetStockObject(idbrush)

    def create(self,title,rc,parent=None,id=0):
        strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
        self.CreateWindowEx(self._exstyle,strclass,title,self._style,
                rc,parent,id)


class TransChildWindow(MfcOsWnd):
    """Generic TransChildWindow class"""
    def __init__ (self):
        MfcOsWnd.__init__(self)
        self._clstyle=win32con.CS_DBLCLKS
        self._style=win32con.WS_CHILD
        self._exstyle=win32con.WS_EX_TRANSPARENT
        self._brush=Sdk.GetStockObject(win32con.NULL_BRUSH)

    def OnEraseBkgnd(self,dc):
        parent = self.GetParent()
        ptList=[(0,0),]
        ptOffset = self.MapWindowPoints(parent,ptList)[0]
        ptOldOrg=dc.OffsetWindowOrg(ptOffset)
        parent.SendMessage(win32con.WM_ERASEBKGND,dc.GetSafeHdc())
        dc.SetWindowOrg(ptOldOrg)
        return 1



def createTopPyCWnd(type,title,trans,x,y,w,h,bgr):
    wnd=MfcOsWnd()
    wnd.setClstyle(win32con.CS_DBLCLKS)
    wnd.setStyle(win32con.WS_OVERLAPPEDWINDOW) #| win32con.WS_CLIPCHILDREN
    brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(bgr),0)
    wnd.setBrush(brush)
    wnd.setIcon(Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED))
    wnd.setStandardCursor(win32con.IDC_ARROW)
    wnd.create(title,(x, y, x+w, y+h),None)
    return wnd

def createChildPyCWnd(type,title,parent,trans,x,y,w,h,bgr):
    if trans==0:
        wnd=MfcOsWnd()
        brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(bgr),0)
        wnd.setBrush(brush)
        wnd.setStandardCursor(win32con.IDC_ARROW)
        wnd.setClstyle(win32con.CS_DBLCLKS)
        wnd.setStyle(win32con.WS_CHILD) #|win32con.WS_CLIPSIBLINGS)
        wnd.setExstyle(win32con.WS_EX_CONTROLPARENT)
        wnd.create(title,(x, y, x+w, y+h),parent)
    else:
        wnd=TransChildWindow()
        wnd.setStandardCursor(win32con.IDC_ARROW)
        wnd.create(title,(x, y, x+w, y+h),parent)
    return wnd
