__version__ = "$Id$"

# win32 constants
import win32con

# app constants
from appcon import *

# kick toplevel.serve_events()
import __main__

# win32 structures helpers
import win32mu

# base class and mixins
from win32dlview import DisplayListView
import win32window

# ddraw.error
import ddraw

import wmwriter
import time

class _PlayerView(DisplayListView, win32window.DDWndLayer):
	def __init__(self,doc,bgcolor=None):
		DisplayListView.__init__(self,doc)
		self._canclose=1
		self._tid=None
		self.__lastMouseMoveParams = None

		self._usesLightSubWindows = 1

		win32window.DDWndLayer.__init__(self, self, bgcolor)

		self._viewport = None
		self._writer = None	

	def init(self, rc, title='View', units= UNIT_MM, adornments=None, canvassize=None, commandlist=None, bgcolor=None):
		DisplayListView.init(self, rc, title=title, units=units, adornments=adornments, canvassize=canvassize,
			commandlist=commandlist, bgcolor=bgcolor)
		x, y, w, h = rc
		self.createDDLayer(w, h)
		self._viewport = win32window.Viewport(self, 0, 0, w, h, bgcolor)

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None, bgcolor=None):
		return self._viewport.newwindow(coordinates, pixmap, transparent, z, type_channel, units, bgcolor)

	def closeViewport(self, viewport):
		DisplayListView.close(self)

	def OnCreate(self,params):
		DisplayListView.OnCreate(self, params)
#		self.createDDLayer()

	def OnDestroy(self, msg):		
		if self._usesLightSubWindows:
			self.destroyDDLayer()
		DisplayListView.OnDestroy(self, msg)

	def OnInitialUpdate(self):
		DisplayListView.OnInitialUpdate(self)
		self.HookMessage(self.onCreateBoxOK,WM_USER_CREATE_BOX_OK)
		self.HookMessage(self.onCreateBoxCancel,WM_USER_CREATE_BOX_CANCEL)

	# Do not close and recreate topwindow, due to flushing screen
	# and loose of focus. 
	# Nobody would excpect to destroy a window by resizing it!
	def close(self):
		if self._canclose:
			DisplayListView.close(self)
					
	# The response of the view for the WM_SIZE (Resize) message						
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return

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
		if self.in_create_box_mode() and self.get_box_modal_wnd()==self:
			self.notifyListener('OnDraw',dc)
			return
		if not self._usesLightSubWindows:
			DisplayListView.OnDraw(self,dc)
		else:
			self.update()

	def onMouseEvent(self, point, ev):
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
		
		if not self._usesLightSubWindows or self.in_create_box_mode():
			DisplayListView.onMouseMove(self, params)
		
		msg=win32mu.Win32Msg(params)
		flags = 0
		point=msg.pos()
		point = self._DPtoLP(point)
		
		self._viewport.onMouseMove(flags, point)

	def OnEraseBkgnd(self,dc):
		if not self._usesLightSubWindows or not self._active_displist:
			return DisplayListView.OnEraseBkgnd(self,dc)
		win32mu.DrawRectangle(dc, self.GetClientRect(), self._bgcolor or (255, 255, 255))
		return 1
		
	def update(self, rc=None):
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

		self.paint(rc)
		
		if rc is None:
			x, y, w, h = self._viewport._rect
			rcBack = x, y, x+w, y+h
		else:
			rcBack = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]
		
		rcFront = self.ClientToScreen(rcBack)
		try:
			self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)
		except ddraw.error, arg:
			print arg
	
	def getDrawBuffer(self):
		return self._backBuffer

	def getContextOsWnd(self):
		return self

	def getwindowpos(self, rel=None):
		return self._rect

	def paint(self, rc=None):
		if rc is None:
			x, y, w, h = self._viewport._rect
			rcPaint = x, y, x+w, y+h
		else:
			rcPaint = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3] 
		if self._convbgcolor == None:
			self._convbgcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255, 255, 255) )
		try:
			self._backBuffer.BltFill(rcPaint, self._convbgcolor)
		except ddraw.error, arg:
			print arg
			return

		if self._viewport:
			self._viewport.paint(rc)
	
	def beginWriting(self):
		self.HookMessage(self.onTimer,win32con.WM_TIMER)
		self.__timer_id = self.SetTimer(1,200)
	
	def onTimer(self, params):
		if not self._writer:
			self._writer = wmwriter.WMWriter(self._backBuffer, profile=20)
			self._writer.setOutputFilename('output.wmv')
			self._start = time.time()
			self._writer.beginWriting()
			print 'beginWriting'
		else:
			dt = time.time() - self._start
			self._writer.update(dt)

	def endWriting(self):
		self.KillTimer(self.__timer_id)
		if self._writer:
			self._writer.endWriting()
			self._writer = None	
			print 'endWriting'




