__version__ = "$Id$"

# win32 constants
import win32con

# app constants
from appcon import *
import grinsRC

# kick toplevel.serve_events()
import __main__

import win32ui, win32api

# win32 structures helpers
import win32mu

# base class and mixins
from win32dlview import DisplayListView
import win32window

# ddraw.error
import ddraw

class _PlayerView(DisplayListView, win32window.DDWndLayer):
	def __init__(self,doc,bgcolor=None):
		DisplayListView.__init__(self,doc)
		self._canclose=1
		self._tid=None
		self.__lastMouseMoveParams = None

		self._usesLightSubWindows = 1

		win32window.DDWndLayer.__init__(self, self, bgcolor)

		self._viewport = None
		self._ddmsgs = 0
		self._isminimized = 0

	def init(self, rc, title='View', units= UNIT_MM, adornments=None, canvassize=None, commandlist=None, bgcolor=None):
		DisplayListView.init(self, rc, title=title, units=units, adornments=adornments, canvassize=canvassize,
			commandlist=commandlist, bgcolor=bgcolor)
		w, h = rc[2:]
		self.createDDLayer(w, h)
		self._viewport = win32window.Viewport(self, 0, 0, w, h, bgcolor)
		mainframe = self.GetParent().GetMDIFrame()
		mainframe.assertPanelVisible()
			
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
		return self._viewport.newwindow(coordinates, pixmap, transparent, z, units, bgcolor)

	def closeViewport(self, viewport):
		self.GetParent().GetMDIFrame().registerPos(self)
		DisplayListView.close(self)

	def OnCreate(self,params):
		DisplayListView.OnCreate(self, params)
		self.GetParent().HookMessage(self.onParentSize, win32con.WM_SIZE)

	def OnDestroy(self, msg):		
		if self._usesLightSubWindows:
			self.destroyDDLayer()
		DisplayListView.OnDestroy(self, msg)

	def OnInitialUpdate(self):
		DisplayListView.OnInitialUpdate(self)
		self.HookMessage(self.onKeyDown, win32con.WM_KEYDOWN)

	def onKeyDown(self, params):
		from WMEVENTS import KeyboardInput
		c = win32ui.TranslateVirtualKey(params[2])
		self.onEvent(KeyboardInput, c)
		return 1 # allow accelerators do their job

	# Called when the view is activated 
	# Override since DisplayListView will set grinsRC.IDR_STRUCT_EDIT accelerator
	def activate(self):
		self._is_active = 1
		self._parent.set_commandlist(self._commandlist,self._strid)
		self.set_menu_state()
		self._parent.LoadAccelTable(grinsRC.IDR_GRINSED)

	# Called when the view is deactivated 
	def deactivate(self):
		self._is_active = 0
		self._parent.set_commandlist(None, self._strid)
		# restore accelarator
		# nothing since its already that of frame

	# Do not close and recreate topwindow, due to flushing screen
	# and loose of focus. 
	# Nobody would excpect to destroy a window by resizing it!
	def close(self):
		if self._canclose:
			DisplayListView.close(self)
	
	def onParentSize(self, params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): 
			self._isminimized = 1
			return
		self._isminimized = 0
		
	# The response of the view for the WM_SIZE (Resize) message						
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): 
			self._isminimized = 1
			return
		self._isminimized = 0

		# This historic function does not need to be
		# called since the channels are now destroyed
		# and re-created. The effect of calling it is
		# a flickering screen 
#		self._do_resize(msg.width(),msg.height())
		
		# destroy displists while dragging?
		# i.e repaint previous content while dragging?
		# Its a preference. 
#		self._destroy_displists_tree()

		# after _do_resize because it uses old self._rect
		self._rect=0,0,msg.width(),msg.height()
		self.fitCanvas(msg.width(),msg.height())

		# Do not use PostMessage. ChannelWindow.resize
		# fails to save_geometry if the sys attribute
		# 'Show Window Contents While Dragging' is set
		# since then this function is called to often
#		self.PostMessage(win32con.WM_USER)
		from __main__ import toplevel
		if self._tid:
			toplevel.canceltimer(self._tid)
		self._tid=toplevel.settimer(0.2,(self.onPostResize,()))

	def onPostResize(self,params=None):
		self._tid=None
		self._canclose=0
		if not self._usesLightSubWindows: 
			self._resize_tree()
		self._canclose=1

	def OnDraw(self, dc):
		self.update()

	def onMouseEvent(self, point, ev, params=None):
		cont, stop = 0, 1	
		if not self._usesLightSubWindows:
			if DisplayListView.onMouseEvent(self, point, ev):
				return stop
		action =  self._viewport.onMouseEvent(point, ev)

		# kick immediate responses
		__main__.toplevel.serve_events()

		return action

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
		point = self._DPtoLP(point)
		
		self._viewport.onMouseMove(flags, point)

	def OnEraseBkgnd(self,dc):
		if self._isminimized:
			return
		if not self._usesLightSubWindows or not self._active_displist:
			return DisplayListView.OnEraseBkgnd(self,dc)
		win32mu.DrawRectangle(dc, self.GetClientRect(), self._bgcolor or (255, 255, 255))
		return 1
	
	def rectAnd(self, rc1, rc2):
		# until we make calcs
		rc, ans= win32ui.GetWin32Sdk().IntersectRect(self.ltrb(rc1),self.ltrb(rc2))
		if ans:
			return self.xywh(rc)
		return 0, 0, 0, 0
		
	def update(self, rc=None, exclwnd=None):
		if self._isminimized:
			return

		if not self._ddraw or not self._frontBuffer or not self._backBuffer:
			return
		if not self.IsWindowVisible():
			return
		if self._frontBuffer.IsLost():
			win32api.Sleep(0)
			if not self._frontBuffer.Restore():
				# we can't do anything for this
				# system is busy with video memory
				self.InvalidateRect(self.GetClientRect())
				return
		if self._backBuffer.IsLost():
			win32api.Sleep(0)
			if not self._backBuffer.Restore():
				# and for this either
				# system should be out of memory
				self.InvalidateRect(self.GetClientRect())
				return
		
		# do we have anything to update?
		if rc and (rc[2]==0 or rc[3]==0): 
			return 

		if not self.paint(rc, exclwnd):
			self.InvalidateRect(self.GetClientRect())
			return	
		
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
			if self._ddmsgs < 10:
				print 'PlayerView.update', self._ddmsgs,  arg
			self._ddmsgs = self._ddmsgs + 1
			self.InvalidateRect(self.GetClientRect())
	
	def getDrawBuffer(self):
		return self._backBuffer

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
			if self._backBuffer.IsLost() and not self._backBuffer.Restore():
				return 0
			self._backBuffer.BltFill(rcPaint, self._convbgcolor)
		except ddraw.error, arg:
			if self._ddmsgs < 10:
				print 'PlayerView.paint',self._ddmsgs, arg
			self._ddmsgs = self._ddmsgs + 1
			return 0

		if self._viewport:
			self._viewport.paint(rc, exclwnd)

		return 1


