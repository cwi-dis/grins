
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

#############################			
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
		if (self._exstyle & WS_EX_CLIENTEDGE):
			dxe = 2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
			dye = 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		wi = (r1-l1) - (r2-l2)
		wp = w + wi + dxe
		hi = (b1-t1) - (b2-t2)
		hp = h + hi + dye
		flags=win32con.SWP_NOMOVE | win32con.SWP_NOZORDER 		
		self.SetWindowPos(0, (0,0,wp,hp), flags)



import commctrl

from TreeCtrl import TreeCtrl

def __test():
	wnd=ToplevelWnd()
	wnd.setStockBrush(win32con.WHITE_BRUSH)
	wnd.setStandardCursor(win32con.IDC_ARROW)
	wnd.create('GRiNS Lab',0,0,400,300)
	wnd.ShowWindow(win32con.SW_SHOW)
	tc = TreeCtrl()
	rc = wnd.GetClientRect()
	tc.create(wnd, rc, 101)
	hroot = tc.insertLabel('root', commctrl.TVI_ROOT, commctrl.TVI_LAST)
	hi = tc.insertLabel('child1', hroot, commctrl.TVI_LAST)
	hi = tc.insertLabel('child2', hroot, commctrl.TVI_LAST)

if __name__ == '__main__':
	__test()

