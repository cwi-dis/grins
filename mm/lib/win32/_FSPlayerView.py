__version__ = "$Id$"


# Full screen player support

# For now:
# To test fullscreen mode set PlayerDialog.__show = 'fullscreen' and then play as usual.
# The player will work in full sceen mode untill PlayerDialog.__show  is set again to 'normal'.
# When in full screen mode press F1 to start playing
# When in full screen mode press ESC to return to normal mode


# Implementation note:
# Currently full screen mode is not otimized.
# We have to enumerate direct draw drivers
# and find the appropriate for hardware (video card) blitting.

# direct draw infrastructure module
import ddraw

import win32api, win32con, win32ui 
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()
import win32mu

from appcon import *
from WMEVENTS import *

import usercmd

# generic wnd class
from pywinlib.mfc import window

# cursors
import grinsRC

import win32window

# meta smil class
# container of ViewportWnd meta smil classes
# formal name: ViewportWndContainer

class _FSPlayerView(window.Wnd, win32window.DDWndLayer):
	def __init__ (self, frame, bgcolor):
		self._frame = frame
		window.Wnd.__init__(self,win32ui.CreateWnd())
		win32window.DDWndLayer.__init__(self, self, bgcolor)
		self._viewports = []
		self._curcursor = ''
		
	def create(self, title, x, y, w, h):
		clstyle = win32con.CS_HREDRAW | win32con.CS_VREDRAW | win32con.CS_DBLCLKS
		brush=Sdk.GetStockObject(win32con.WHITE_BRUSH)
		cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		icon=Afx.GetApp().LoadIcon(win32con.IDI_APPLICATION)
		strclass=Afx.RegisterWndClass(clstyle, cursor, brush, icon)

		exstyle = win32con.WS_EX_TOPMOST
		style = win32con.WS_POPUP  | win32con.WS_CLIPCHILDREN
		parent = None
		id = 0
		self.CreateWindowEx(exstyle, strclass, title, style, (x, y, w, h), parent, id)

	def OnCreate(self, params):
		self.createDDLayer()			
		self.hookMessages()
	
	def hookMessages(self):
		self.HookMessage(self.onKeyDown,win32con.WM_KEYDOWN)

		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		self.HookMessage(self.onLButtonDblClick,win32con.WM_LBUTTONDBLCLK)
				
	def OnDestroy(self, params):
		self.destroyDDLayer()
		self._frame.delFSPlayer()				
	
	# Set the cursor given its string id		
	def setcursor(self, strid):
		if self._curcursor==strid:
			return
		if strid=='hand':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_POINT_HAND)
		elif strid=='channel':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_DRAGMOVE)
		elif strid=='stop':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_STOP)
		elif strid=='link':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_DRAGLINK)
		elif strid=='' or strid=='arrow':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
			strid='arrow'
		elif strid=='draghand':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_DRAG_HAND)
		else:
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
			strid='arrow'

		self.SetWndCursor(cursor)
		self._curcursor = strid
	
	def SetWndCursor(self,cursor):
		if cursor!=Sdk.GetCursor():
			Sdk.SetClassLong(self.GetSafeHwnd(),win32con.GCL_HCURSOR,cursor)
						
	#
	#
	#
	def OnEraseBkgnd(self, params):
		return 1
		
	def OnPaint(self):
		from __main__ import toplevel
		toplevel.serve_events()
		win32ui.PumpWaitingMessages(win32con.WM_MOUSEFIRST,win32con.WM_MOUSELAST)
		win32api.Sleep(0)
		self.update()
	
	def paint(self):
		if not self._ddraw: return
		if self._backBuffer.IsLost():
			if not self._backBuffer.Restore():
				# and for this either
				# system should be out of memory
				return
		x, y, w, h = self.GetClientRect()

		# for full screen mode default to black if none is given
		ddcolor = self._backBuffer.GetColorMatch(self._bgcolor or (0,0,0))
		self._backBuffer.BltFill((0, 0, w, h), ddcolor)

		rv = self._viewports[:]
		rv.reverse()
		for v in rv:
			v.paint()
			v.flip()

	def update(self):
		self.paint()
		self.flip()

	#
	# implement IViewportContext
	#

	# insert viewport in viewports list 
	# higher z order comes first in list
	def insertViewport(self, viewport, z=0):
		viewport._z = z
		for i in range(len(self._viewports)):
			if z > self._viewports[i]._z:
				self._viewports.insert(i, viewport)
				break
		else:
			self._viewports.append(viewport)

	def onKeyDown(self, params):
		msg = win32mu.Win32Msg(params)
		if msg._wParam==win32con.VK_F1:
			self._frame.PostMessage(win32con.WM_COMMAND, self._frame.GetUserCmdId(usercmd.PLAY))
		if msg._wParam==win32con.VK_ESCAPE:
			self._frame.PostMessage(win32con.WM_COMMAND, 
				self._frame.GetUserCmdId(usercmd.HIDE_PLAYERVIEW))
			self._frame.delFSPlayer()
			self.PostMessage(win32con.WM_CLOSE)				
		
	def getSize(self):
		return self.GetClientRect()[2:]

	def imgAddDocRef(self,file):
		self._frame.imgAddDocRef(file)

	def updateMouseCursor(self):
		pass

	def closeViewport(self, viewport):
		self._viewports.remove(viewport)

	def getContextOsWnd(self):
		return self

	def onLButtonDown(self, params):	
		msg = win32mu.Win32Msg(params)
		flags = 0
		pt=msg.pos()
		L = self._viewports
		for v in self._viewports:
			if v.onLButtonDown(flags, pt):
				break

	def onLButtonUp(self, params):
		msg = win32mu.Win32Msg(params)
		flags = 0
		pt=msg.pos()
		for v in self._viewports:
			v.onLButtonUp(flags, pt)

	def onMouseMove(self, params):
		msg = win32mu.Win32Msg(params)
		flags = 0
		pt=msg.pos()
		for v in self._viewports:
			if v.onMouseMove(flags, pt):
				return
		self.setcursor('arrow')

	def onLButtonDblClick(self, params):
		msg = win32mu.Win32Msg(params)
		flags = 0
		pt=msg.pos()
		self._frame.PostMessage(win32con.WM_COMMAND, self._frame.GetUserCmdId(usercmd.PLAY))

	def newviewport(self, x, y, w, h, title, units = UNIT_MM, adornments=None, canvassize=None, commandlist=None, strid='cmifview_', bgcolor=None):
		return ViewportWnd(self, (x, y, w, h), title, bgcolor)


############################################
# meta smil class
# each ViewportWnd contains one smil20 viewport
class ViewportWnd:
	def __init__(self, ctx, rc, title, bgcolor=None):
		self._ctx = ctx
		self.CreateSurface = ctx.CreateSurface
		self._dh = dh = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
		self._dm = dm = 1
		x, y, w, h = rc
		self._viewport = win32window.Viewport(self, dm, dh, w, h, bgcolor)

		self._title = title
		self._z = 0
		self.insertAt(self._z)

		self._rect = self._canvas = 0, 0, w+2*dm, h+dh+dm
		self._rectb = x, y, w+2*dm, h+dh
		self._bgcolor = bgcolor
				
		self.__drawBuffer = self._ctx.CreateSurface(w+2*dm, h+dh+dm)

		self._convbgcolor = self.__drawBuffer.GetColorMatch(bgcolor or (255,255,255))
		self.__drawBuffer.BltFill(self._rect, self._convbgcolor)
		
		# draw not viewport area
		self.__metaPaintOnDDS()
		
		# Tragging support
		self._offset = 0, 0
		self._tragged = 0 

	def getCaptionPos(self):
		x, y, w, h = self._rectb
		return x, y, w, self._dh

	def getClientPos(self):
		x, y, w, h = self._rectb
		return x+self._dm, y+self._dh, w-2*self._dm, h-self._dh-self._dm
		
	def pointInCaption(self, point):
		x, y, w, h = self.getCaptionPos()
		xp, yp = point
		return x<=xp and xp<=x+w and y<=yp and yp<=y+h

	def pointInClient(self, point):
		x, y, w, h = self.getClientPos()
		xp, yp = point
		return x<=xp and xp<=x+w and y<=yp and yp<=y+h

	def pointInRect(self, point):
		x, y, w, h = self._rectb
		xp, yp = point
		return x<=xp and xp<=x+w and y<=yp and yp<=y+h

	def ltrb(self, xywh):
		x,y,w,h = xywh
		return x, y, x+w, y+h

	def xywh(self, ltrb):
		l,t,r,b = ltrb
		return l, t, r-l, b-t

	def closeViewport(self, viewport):
		self._ctx._viewports.remove(self)
		self._viewport = None

	def imgAddDocRef(self,file):
		self._ctx.imgAddDocRef(file)

	def updateMouseCursor(self):
		pass

	def setcursor(self, strid):
		self._ctx.setcursor(strid)

	def getContextOsWnd(self):
		return self._ctx.getContextOsWnd()

	def getwindowpos(self, rel=None):
		return self.getClientPos()

	def getDrawBuffer(self):
		if self.__drawBuffer.IsLost():
			if not self.__drawBuffer.Restore():
				return None
		return self.__drawBuffer
		
	def getDirectDraw(self):
		return self._ctx.getDirectDraw()

	def getRGBBitCount(self):
		return self._ctx.getRGBBitCount()

	def __metaPaintOnDDS(self):
		dds = self.getDrawBuffer()
		if not dds: return

		w, dh = self._rect[2], self._dh
		convtbgcolor = dds.GetColorMatch((128, 128, 255))
		dds.BltFill((0, 0, w, dh), convtbgcolor)

		hdc = dds.GetDC()
		dc = win32ui.CreateDCFromHandle(hdc)

		dc.SetBkMode(win32con.TRANSPARENT)
		dc.SetTextAlign(win32con.TA_BOTTOM)
		clr_org=dc.SetTextColor(win32api.RGB(255,255,255))
		dc.TextOut(4,dh-2,self._title)
		dc.SetTextColor(clr_org)

		dc.Detach()
		dds.ReleaseDC(hdc)
		
		self.draw3dRect(self.__drawBuffer, self._rect, (225,225,225), (200,200,200))

	def update(self):
		self.paint()
		self.flip()
		self._ctx.flip()

	def paint(self):
		if self._viewport:	
			self._viewport.paint()
			self._viewport.flip()

	def flip(self):
		ctxDrawBuffer = self._ctx.getDrawBuffer()
		if not ctxDrawBuffer: return

		dds = self.getDrawBuffer()
		if not dds: return

		ctxDrawBuffer.Blt(self.ltrb(self._rectb), dds, self.ltrb(self._rect))

	def onLButtonDown(self, flags, point):
		isTarget = self.pointInRect(point)
		if isTarget:
			self.pop()
			
		if self.pointInCaption(point):
			x, y, w, h = self._rectb
			xp, yp = point
			self._offset = x - xp, y - yp
			self._tragged = 1
		
		if self.pointInClient(point):
			x, y, w, h = self._rectb
			xp, yp = point
			self._viewport.onMouseEvent((xp-x-self._dm,yp-y-self._dh),Mouse0Press)

		return isTarget

	def onLButtonUp(self, flags, point):
		if self._tragged: 
			self._tragged = 0
		if self.pointInClient(point):
			x, y, w, h = self._rectb
			xp, yp = point
			self._viewport.onMouseEvent((xp-x-self._dm,yp-y-self._dh),Mouse0Release)

	def onMouseMove(self, flags, point):
		if self._tragged:
			x, y, w, h = self._rectb
			xp, yp = point
			xo, yo = self._offset
			self._rectb = xp + xo, yp + yo, w, h
		if self.pointInClient(point):
			x, y, w, h = self._rectb
			xp, yp = point
			self._viewport.onMouseMove(flags, (xp-x-self._dm,yp-y-self._dh))
		return self.pointInRect(point)

	def __getPaintRects(self):
		W, H = self._ctx.getSize()
		xd, yd = self._rectb[:2]
		ls, ts, ws, hs = self._rect
		rs = ls + ws
		bs = ts + hs
		if xd<0:
			ls = ls - xd
			xd = 0
		elif xd+ws > W:
			rs = ls + (W-xd)
		if yd<0:
			ts = ts - yd
			yd = 0
		elif yd + hs > H:
			bs = ts + (H -yd)
		return (xd, yd, rs-ls, bs-ts), (ls, ts, rs-ls, bs-ts)

	def insertAt(self, z=0):
		self._z = z
		for i in range(len(self._ctx._viewports)):
			if z > self._ctx._viewports[i]._z:
				self._ctx._viewports.insert(i, self)
				break
		else:
			self._ctx._viewports.append(self)

	def pop(self, poptop=1):
		# put self in front of all siblings with equal or lower z
		if self is not self._ctx._viewports[0]:
			self._ctx._viewports.remove(self)
			for i in range(len(self._ctx._viewports)):
				if self._z >= self._ctx._viewports[i]._z:
					self._ctx._viewports.insert(i, self)
					break
			else:
				self._ctx._viewports.append(self)

	def getClientRect(self):
		x, y, w, h = self._rect
		return x, y, w, h - self._dh

	def fillRect(self, dds, rc, rgb):
		ddcolor = dds.GetColorMatch(rgb)
		dds.BltFill(self.ltrb(rc), ddcolor)

	def fill(self, dds, x, y, w, h, rgb):
		ddcolor = dds.GetColorMatch(rgb)
		dds.BltFill((x, y, x+w, y+h), ddcolor)

	def draw3dRect(self, dds, rc, rgbTopLeft, rgbBottomRight):
		x, y, w, h = rc
		self.fill(dds, x, y, w - 1, 1, rgbTopLeft)
		self.fill(dds, x, y, 1, h - 1, rgbTopLeft)
		self.fill(dds, x + w-1, y, 1, h, rgbBottomRight)
		self.fill(dds, x, y + h-1, w, 1, rgbBottomRight)

