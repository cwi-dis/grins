__version__ = "$Id$"


import win32con
from appcon import *

import win32mu

import win32window

from _CmifView import _CmifView

class _PlayerView(_CmifView, win32window.DDWndLayer):
	def __init__(self,doc,bgcolor=None):
		_CmifView.__init__(self,doc)
		self._canclose=1
		self._tid=None
		self.__lastMouseMoveParams = None

		self._usesLightSubWindows = 1

		win32window.DDWndLayer.__init__(self, self, bgcolor)

		self._viewport = None

	def init(self, rc, title='View', units= UNIT_MM, adornments=None, canvassize=None, commandlist=None, bgcolor=None):
		_CmifView.init(self, rc, title=title, units=units, adornments=adornments, canvassize=canvassize,
			commandlist=commandlist, bgcolor=bgcolor)
		x, y, w, h = rc
		self._viewport = win32window.Viewport(self, 0, 0, w, h, bgcolor)

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None, bgcolor=None):
		return self._viewport.newwindow(coordinates, pixmap, transparent, z, type_channel, units, bgcolor)

	def closeViewport(self, viewport):
		_CmifView.close(self)

	def OnCreate(self,params):
		_CmifView.OnCreate(self, params)
		if self._usesLightSubWindows:
			self.createDDLayer()

	def OnDestroy(self, msg):		
		if self._usesLightSubWindows:
			self.destroyDDLayer()
		_CmifView.OnDestroy(self, msg)

	def OnInitialUpdate(self):
		_CmifView.OnInitialUpdate(self)
		self.HookMessage(self.onCreateBoxOK,WM_USER_CREATE_BOX_OK)
		self.HookMessage(self.onCreateBoxCancel,WM_USER_CREATE_BOX_CANCEL)

	# Do not close and recreate topwindow, due to flushing screen
	# and loose of focus. 
	# Nobody would excpect to destroy a window by resizing it!
	def close(self):
		if self._canclose:
			_CmifView.close(self)
					
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

	def OnDraw(self,dc):
		if self.in_create_box_mode() and self.get_box_modal_wnd()==self:
			self.notifyListener('OnDraw',dc)
			return
		if not self._usesLightSubWindows:
			_CmifView.OnDraw(self,dc)
		else:
			self.update()

	def onMouseEvent(self, point, ev):
		cont, stop = 0, 1	
		
		if not self._usesLightSubWindows:
			if _CmifView.onMouseEvent(self, point, ev):
				return stop

		return self._viewport.onMouseEvent(point, ev)

	def updateMouseCursor(self):
		self.onMouseMove()

	def onMouseMove(self, params=None):
		if not params and not self.__lastMouseMoveParams:
			return
		if not params: params = self.__lastMouseMoveParams
		else: self.__lastMouseMoveParams = params
		
		if not self._usesLightSubWindows or self.in_create_box_mode():
			_CmifView.onMouseMove(self, params)
		
		msg=win32mu.Win32Msg(params)
		flags = 0
		point=msg.pos()
		point = self._DPtoLP(point)
		
		self._viewport.onMouseMove(flags, point)

	def OnEraseBkgnd(self,dc):
		if not self._usesLightSubWindows or not self._active_displist:
			return _CmifView.OnEraseBkgnd(self,dc)
		return 1
		
	def update(self):
		if not self._ddraw or not self._frontBuffer or not self._backBuffer:
			return
		if self._frontBuffer.IsLost():
			if not self._frontBuffer.Restore():
				# we can't do anything for this
				# system is busy with video memory
				return 
		if self._backBuffer.IsLost():
			if not self._backBuffer.Restore():
				# and for this either
				# system should be out of memory
				return
		self.paint()
		rcBack = self._wnd.GetClientRect()
		rcFront = self._wnd.ClientToScreen(rcBack)
		self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)

	def getDrawBuffer(self):
		return self._backBuffer

	def getContextOsWnd(self):
		return self

	def getwindowpos(self, rel=None):
		return self._rect

	def paint(self):
		# hack to avoid displaying random bits 
		# when the window has been resized
		# (site effect of current implementation)
		rc = self.GetClientRect()
		if self._convbgcolor == None:
			self._convbgcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255, 255, 255) )
		self._backBuffer.BltFill(rc, self._convbgcolor)
		
		if self._viewport:	
			self._viewport.paint()
			
##################################
			
