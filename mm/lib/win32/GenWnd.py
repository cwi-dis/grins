__version__ = "$Id$"

# @win32doc|GenWnd
# A Generic win32-Mfc Wnd class

import win32ui,win32con
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()
from pywinlib.mfc import window

class GenWnd(window.Wnd):
    # Generic win32-Mfc Wnd class
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
