__version__ = "$Id$"

import win32ui, win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

import GenWnd
import usercmd, usercmdui	
	
WM_USER_OPEN = win32con.WM_USER+1
WM_USER_CLOSE = win32con.WM_USER+2
WM_USER_PLAY = win32con.WM_USER+3
WM_USER_STOP = win32con.WM_USER+4
WM_USER_PAUSE = win32con.WM_USER+5
WM_USER_GETSTATUS = win32con.WM_USER+6
WM_USER_SETHWND = win32con.WM_USER+7
WM_USER_UPDATE = win32con.WM_USER+8

class ListenerWnd(GenWnd.GenWnd):
	def __init__(self, toplevel):
		GenWnd.GenWnd.__init__(self)
		self._toplevel = toplevel
		self.create()
		self._docmap = {}
		self.HookMessage(self.OnOpen, WM_USER_OPEN)
		self.HookMessage(self.OnClose, WM_USER_CLOSE)
		self.HookMessage(self.OnPlay, WM_USER_PLAY)
		self.HookMessage(self.OnStop, WM_USER_STOP)
		self.HookMessage(self.OnPause, WM_USER_PAUSE)
		self.HookMessage(self.OnGetStatus, WM_USER_GETSTATUS)
		self.HookMessage(self.OnSetWindow, WM_USER_SETHWND)
		self.HookMessage(self.OnUpdate, WM_USER_UPDATE)

	def OnOpen(self, params):
		# lParam (params[3]) is a pointer to a c-string
		filename = Sdk.GetWMString(params[3])
		event = 'OnOpen'
		try:
			func, arg = self._toplevel.get_embedded(event)
			func(arg, self, event, filename)
			self._docmap[params[2]] = self._toplevel.get_most_recent_docframe()
		except:
			pass

	def OnClose(self, params):
		wnd = self._docmap.get(params[2])
		if wnd: wnd.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.CLOSE].id)

	def OnPlay(self, params):
		wnd = self._docmap.get(params[2])
		if wnd: wnd.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.PLAY].id)

	def OnStop(self, params):
		wnd = self._docmap.get(params[2])
		if wnd: wnd.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.STOP].id)

	def OnPause(self, params):
		wnd = self._docmap.get(params[2])
		if wnd: wnd.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.PAUSE].id)

	def OnGetStatus(self, params):
		print 'OnGetStatus'

	def OnSetWindow(self, params):
		self._toplevel.set_embedded_hwnd(params[2], params[3])

	def OnUpdate(self, params):
		wnd = self._toplevel.get_embedded_wnd(params[2])
		if wnd: wnd.update()

############################
import win32window
from pywinlib.mfc import window
from appcon import *
from WMEVENTS import *
import win32mu
import grinsRC

class EmbeddedWnd(window.Wnd, win32window.Window, win32window.DDWndLayer):
	def __init__(self, wnd, w, h, units, bgcolor, hwnd=0, title='', id=0):
		self._cmdframe = wnd
		self._peerid = id
		self._destroywnd = 0
		if hwnd:
			window.Wnd.__init__(self, win32ui.CreateWindowFromHandle(hwnd))
		else:
			window.Wnd.__init__(self, win32ui.CreateWnd())
			self.createOsWnd( (0,0,w,h), bgcolor, title)
			self._destroywnd = 1
					
		win32window.Window.__init__(self)
		self.create(None, (0,0,w,h), units, 0, 0, bgcolor)

		win32window.DDWndLayer.__init__(self, self, bgcolor)

		self.createDDLayer(w, h)
		self._viewport = win32window.Viewport(self, 0, 0, w, h, bgcolor)

		self.imgAddDocRef = wnd.imgAddDocRef
		self.__lastMouseMoveParams = None
		if not hwnd: self.setClientRect(w, h)
		else: 
			from __main__ import commodule
			commodule.AdviceSetSize(id, w, h)

	def OnCreate(self, params):
		self.HookMessage(self.onLButtonDown, win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp, win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove, win32con.WM_MOUSEMOVE)				

	def OnDestroy(self, msg):
		self.destroyDDLayer()		

	def OnClose(self):
		self._cmdframe.PostMessage(win32con.WM_COMMAND, usercmdui.class2ui[usercmd.CLOSE].id)

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None, bgcolor=None):
		return self._viewport.newwindow(coordinates, pixmap, transparent, z, type_channel, units, bgcolor)
		
	def pop(self, poptop=1):
		pass

	def is_closed(self):
		return not self._obj_ or not self.IsWindow()

	def closeViewport(self, viewport):
		self.destroyDDLayer()
		if self._destroywnd:
			self.DestroyWindow()
	
	def settitle(self,title):
		import urllib
		title=urllib.unquote(title)
		self._title=title
		self.SetWindowText(title)

	#
	# Mouse input
	#
	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Press)

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Release)

	def updateMouseCursor(self):
		self.onMouseMove()

	def onMouseMove(self, params=None):
		if not params and not self.__lastMouseMoveParams:
			return
		if not params: params = self.__lastMouseMoveParams
		else: self.__lastMouseMoveParams = params
		msg=win32mu.Win32Msg(params)
		flags = 0
		point=msg.pos()	
		self._viewport.onMouseMove(flags, point)

	def onMouseEvent(self, point, ev):
		return  self._viewport.onMouseEvent(point, ev)


	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		self.update()
		self.EndPaint(paintStruct)
			
	def update(self, rc=None, exclwnd=None):
		if self.is_closed(): return
		if not self._ddraw or not self._frontBuffer or not self._backBuffer:
			return
		if self._frontBuffer.IsLost():
			if not self._frontBuffer.Restore():
				# we can't do anything for this
				# system is busy with video memory
				self.InvalidateRect(self.GetClientRect())
				return
		if self._backBuffer.IsLost():
			if not self._backBuffer.Restore():
				# and for this either
				# system should be out of memory
				self.InvalidateRect(self.GetClientRect())
				return
		
		# do we have anything to update?
		if rc and (rc[2]==0 or rc[3]==0): 
			return 

		self.paint(rc, exclwnd)
		
		if rc is None:
			x, y, w, h = self._viewport._rect
			rcBack = x, y, x+w, y+h
		else:
			rc = self.rectAnd(rc, self._viewport._rect)
			rcBack = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]
		
		rcFront = self.ClientToScreen(rcBack)
		try:
			self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)
		except ddraw.error, arg:
			print 'EmbeddedWnd.update', arg
	
	def getContextOsWnd(self):
		return self

	def getwindowpos(self, rel=None):
		return self._rect

	def paint(self, rc=None, exclwnd=None):
		if rc is None:
			x, y, w, h = self._viewport._rect
			rcPaint = x, y, x+w, y+h
		else:
			rc = self.rectAnd(rc, self._viewport._rect)
			rcPaint = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3] 

		if self._convbgcolor == None:
			self._convbgcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255, 255, 255) )
		try:
			self._backBuffer.BltFill(rcPaint, self._convbgcolor)
		except ddraw.error, arg:
			print 'EmbeddedWnd.paint',arg
			return

		if self._viewport:
			self._viewport.paint(rc, exclwnd)

	def rectAnd(self, rc1, rc2):
		# until we make calcs
		import win32ui
		rc, ans= win32ui.GetWin32Sdk().IntersectRect(self.ltrb(rc1),self.ltrb(rc2))
		if ans:
			return self.xywh(rc)
		return 0, 0, 0, 0

	def setClientRect(self, w, h):
		l1, t1, r1, b1 = self.GetWindowRect()
		l2, t2, r2, b2 = self.GetClientRect()
		dxe = dye = 0
		#if (self._exstyle & WS_EX_CLIENTEDGE):
		#	dxe = 2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)
		#	dye = 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)
		wi = (r1-l1) - (r2-l2)
		wp = w + wi + dxe
		hi = (b1-t1) - (b2-t2)
		hp = h + hi + dye
		flags=win32con.SWP_NOMOVE | win32con.SWP_NOZORDER 		
		self.SetWindowPos(0, (0,0,wp,hp), flags)

	def createOsWnd(self, rect, color, title='Viewport'):
		brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(color),0)
		cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		icon=Afx.GetApp().LoadIcon(grinsRC.IDR_GRINSED)
		clstyle=win32con.CS_DBLCLKS
		style=win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
		exstyle = 0
		strclass=Afx.RegisterWndClass(clstyle,cursor,brush,icon)
		self.CreateWindowEx(exstyle,strclass,title,style,
			self.ltrb(rect), None, 0)		
		#self.ShowWindow(win32con.SW_SHOW)





