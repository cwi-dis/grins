__version__ = "$Id$"

# win32 libs
import win32ui, win32con

# app constants
from types import *
from WMEVENTS import *
from appcon import *

# win32 structures helpers
import win32mu

# usercmd
import usercmd, usercmdui, wndusercmd

import math

# drag & drop constants
import DropTarget

# base class
from win32dlview import DisplayListView

#################################################

class _StructView(DisplayListView):
	# Class contructor. initializes base classes
	def __init__(self, doc, bgcolor=None):
		DisplayListView.__init__(self,doc)

		# shortcut for GRiNS private clipboard format
		self.CF_NODE = self.getClipboardFormat('Node')
		self.CF_TOOL = self.getClipboardFormat('Tool')

		# enable or dissable node drag and drop
		self._enableNodeDragDrop = 1
			
		if self._enableNodeDragDrop:
			self._dropmap['Node']=(self.dragnode, self.dropnode)
			self._dropmap['Tool']=(self.dragtool, self.droptool)
			self._dragging = None

	def OnCreate(self,params):
		DisplayListView.OnCreate(self,params)
		# enable mechanism to accept paste files
		# when the event PasteFile is registered
		id=usercmdui.class2ui[wndusercmd.PASTE_FILE].id
		frame=self.GetParent().GetMDIFrame()
		frame.HookCommand(self.OnPasteFile,id)
		frame.HookCommandUpdate(self.OnUpdateEditPaste,id)

	def PaintOn(self,dc):
		# only paint the rect that needs repainting
		rect=win32mu.Rect(dc.GetClipBox())

		# draw to offscreen bitmap for fast looking repaints
		dcc=dc.CreateCompatibleDC()

		bmp=win32ui.CreateBitmap()
		bmp.CreateCompatibleBitmap(dc,rect.width(),rect.height())
		
		# called by win32ui
		#self.OnPrepareDC(dcc)
		
		# offset origin more because bitmap is just piece of the whole drawing
		dcc.OffsetViewportOrg((-rect.left, -rect.top))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.SetBrushOrg((rect.left % 8, rect.top % 8))
		dcc.IntersectClipRect(rect.tuple())

		# background decoration on dcc
		if self._active_displist:color=self._active_displist._bgcolor
		else: color=self._bgcolor
		dcc.FillSolidRect(rect.tuple(),win32mu.RGB(color))

		# draw objects on dcc
		if self._active_displist:
			self._active_displist._render(dcc,rect.tuple())

		# copy bitmap
		dcc.SetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		dcc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt(rect.pos(),rect.size(),dcc,(0, 0), win32con.SRCCOPY)

		# clean up
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC()
		del bmp

	def OnEraseBkgnd(self,dc):
		return 1

	# Response to left button double click
	def onLButtonDblClk(self, params):
		import usercmd, usercmdui
		#self._parent.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.INFO].id)
		callAttr=0
		for cmd in self._commandlist:
			if cmd.__class__==usercmd.INFO:
				self._parent.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.INFO].id)
				return
			if cmd.__class__==usercmd.ATTRIBUTES:
				callAttr=1
		if callAttr:
			self._parent.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.ATTRIBUTES].id)

	# Response to left button down
	def onLButtonDown(self, params, maystartdrag = 1):
		DisplayListView.onLButtonDown(self, params)
		if self._enableNodeDragDrop and maystartdrag:
			msgpos=win32mu.Win32Msg(params).pos()
			self._dragging = msgpos

	def onLButtonUp(self, params):
		DisplayListView.onLButtonUp(self, params)
		if self._enableNodeDragDrop:
			if self._dragging: 
				self._dragging = None

	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point=msg.pos()
		self.onEvent(MouseMove, point)
		if self._enableNodeDragDrop and self._dragging:
			xp, yp = self._dragging
			x, y =win32mu.Win32Msg(params).pos()
			if math.fabs(xp-x)>4 or math.fabs(yp-y)>4:
				str='%d %d' % (xp, yp)
				# Enter C++ code...
				# this is defined in docview.ScrollView, a superclass.
				# refer win32view.cpp in python/Extensions/PythonWin
				# DoDragDrop calls the C++ function "ui_view_do_drag_drop" in
				# python/Extensions/Pythonwin/win32view.cpp.
				# The returned value is whether the drop result was successful or not.
				# ***** DoDragDrop only needs to be called ONCE ***********
				self.DoDragDrop(self.CF_NODE, str) # Ignore the result.
				self._dragging = None

# OnDragLeave is a callback that is called when a dragging node leaves the current
# window.
##	def OnDragLeave(self):
##		self._dragging = None

	# we must return DROPEFFECT_NONE
	# when paste at x, y is not allowed
	def dragnode(self, dataobj, kbdstate, x, y):
		#print "DEBUG: dragging."
		#import traceback
		#traceback.print_stack()
		node=dataobj.GetGlobalData(self.CF_NODE)
		if node and self._dragging:
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)
			xf, yf = self._dragging
			xf, yf = self._DPtoLP((xf,yf))
			xf, yf = self._pxl2rel((xf, yf),self._canvas)
			if self.isShiftPressed(kbdstate):
				cmd = 'move'
			else:
				cmd = 'copy'
			#print "DEBUG: dragging node doing a self.onEventEx", DragNode
			return self.onEventEx(DragNode,(x, y, cmd, xf, yf))
		#print "DEBUG: dragging node not doing anything."
		return DropTarget.DROPEFFECT_NONE

	def dropnode(self, dataobj, effect, x, y):
		#print "DEBUG: dropped."
		DROP_FAILED, DROP_SUCCEEDED = 0, 1
		node = dataobj.GetGlobalData(self.CF_NODE) 
		if node and self._dragging:
			
			# the drag and drop cmd is:
			# copy or cut (according to arg effect)
			# the node at point self._dragging 
			# to position x, y
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)

			xf, yf = self._dragging
			xf, yf = self._DPtoLP((xf,yf))
			xf, yf = self._pxl2rel((xf, yf),self._canvas)

			self._dragging = None

			# if the operation can not be executed return DROP_FAILED
			# else return DROP_SUCCEEDED

			if effect == DropTarget.DROPEFFECT_MOVE:
				cmd = 'copy'
			else:
				cmd = 'move'

			return self.onEventEx(DropNode,(x, y, cmd, xf, yf))

		return DROP_FAILED
							
	def dragtool(self, dataobj, kbdstate, x, y):
		node=dataobj.GetGlobalData(self.CF_TOOL)
		if node:
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)
			return self.onEventEx(DragNode,(x, y, 'copy'))
		return DropTarget.DROPEFFECT_NONE

	def droptool(self, dataobj, effect, x, y):
		DROP_FAILED, DROP_SUCCEEDED = 0, 1
		tool = dataobj.GetGlobalData(self.CF_TOOL)
		if tool:
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)

			# if the operation can not be executed return DROP_FAILED
			# else return DROP_SUCCEEDED

			return DROP_SUCCEEDED

		return DROP_FAILED
