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
import string

# drag & drop constants
import DropTarget

# base class
from win32dlview import DisplayListView

#################################################

class _StructView(DisplayListView):
	# Class contructor. initializes base classes
	def __init__(self, doc, bgcolor=None):
		DisplayListView.__init__(self,doc)

		# enable or disable node drag and drop
		self._enableNodeDragDrop = 1
			
		if self._enableNodeDragDrop:
			self._dropmap['Node']=(self.dragnode, self.dropnode)
			self._dropmap['Tool']=(self.dragtool, self.droptool)
			self._dropmap['NodeUID']=(self.dragnodeuid, self.dropnodeuid)
			self._dragging = None

		self._tooltip = None

	def OnCreate(self,params):
		DisplayListView.OnCreate(self,params)
		# enable mechanism to accept paste files
		# when the event PasteFile is registered
		id=usercmdui.class2ui[wndusercmd.PASTE_FILE].id
		frame=self.GetParent().GetMDIFrame()
		frame.HookCommand(self.OnPasteFile,id)
		frame.HookCommandUpdate(self.OnUpdateEditPaste,id)

##		import components
##		tooltip = components.Tooltip(parent = self, id = 0)
##		tooltip.createWindow()
##		tooltip.addTool(0, (0,0,600,400), 'Structure View')
##		self._tooltip = tooltip

	def OnDestroy(self, params):
		DisplayListView.OnDestroy(self, params)
		if self._tooltip is not None:
			self._tooltip.destroy()
			self._tooltip = None

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
		dcc.IntersectClipRect(rect.ltrb_tuple())

		# background decoration on dcc
		if self._active_displist:color=self._active_displist._bgcolor
		else: color=self._bgcolor
		dcc.FillSolidRect(rect.ltrb_tuple(),win32mu.RGB(color))

		# draw objects on dcc
		if self._active_displist:
			self._active_displist._render(dcc,rect.xywh_tuple())

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
	
	def notifyTooltipForMouseMove(self, params):
		if self._tooltip is None: 
			return
		msg=win32mu.Win32Msg(params)
		point=msg.pos()
		if self._active_displist and self._active_displist._inside_bbox(point):
			if 1: # over a tooltip source?
				self._tooltip.activate(1)
			else:
				self._tooltip.activate(0)
		else:
			self._tooltip.activate(0)
		self._tooltip.onMouseMove(params)

	def onMouseMove(self, params):
		if self._tooltip is not None:
			self.notifyTooltipForMouseMove(params)
		msg = win32mu.Win32Msg(params)
		point = msg.pos()
		point = self._DPtoLP(point)
		self.onEvent(MouseMove, point)
		if self._enableNodeDragDrop and self._dragging:
			xp, yp = self._dragging
			x, y = win32mu.Win32Msg(params).pos()
			if math.fabs(xp-x)>4 or math.fabs(yp-y)>4:
				# experimental: get node at xp, yp
				xp, yp = self._DPtoLP((xp,yp))
				xp, yp = self._pxl2rel((xp, yp),self._canvas)
				flavor, args = self.onEventEx(QueryNode,(xp, yp))
				flavorid, str = DropTarget.EncodeDragData(flavor, args)
				
				res = self.DoDragDrop(flavorid, str)
				self._dragging = None
				if not res:
					self.onEvent(DragEnd, point)

# OnDragLeave is a callback that is called when a dragging node leaves the current
# window.
##	def OnDragLeave(self):
##		self._dragging = None

	# we must return DROPEFFECT_NONE
	# when paste at x, y is not allowed
	def dragnode(self, dataobj, kbdstate, x, y):
		print 'DBG: outdated Node drag!'
		#print "DEBUG: dragging."
		#import traceback
		#traceback.print_stack()
		flavor, args = DropTarget.DecodeDragData(dataobj)
		assert flavor == 'Node'
		if self._dragging:
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)
			xf, yf = self._dragging
			xf, yf = self._DPtoLP((xf,yf))
			xf, yf = self._pxl2rel((xf, yf),self._canvas)
			if self.isControlPressed(kbdstate):
				cmd = 'copy'
			else:
				cmd = 'move'
			#print "DEBUG: dragging node doing a self.onEventEx", DragNode
			return self.onEventEx(DragNode,
					(x, y, cmd, usercmd.DRAG_NODE, (xf, yf)))
		#print "DEBUG: dragging node not doing anything."
		return DropTarget.DROPEFFECT_NONE

	def dropnode(self, dataobj, effect, x, y):
		#print "DEBUG: dropped."
		flavor, args = DropTarget.DecodeDragData(dataobj)
		assert flavor == 'Node'
		if self._dragging:
			
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

			if effect == DropTarget.DROPEFFECT_MOVE:
				cmd = 'move'
			else:
				cmd = 'copy'

			return self.onEventEx(DropNode,
					(x, y, cmd, usercmd.DRAG_NODE, (xf, yf)))

		return DropTarget.DROPEFFECT_NONE
							
	def dragtool(self, dataobj, kbdstate, x, y):
		flavor, ucmd = DropTarget.DecodeDragData(dataobj)
		assert flavor == 'Tool'
		if ucmd:
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)
			return self.onEventEx(DragNode,
					(x, y, 'copy', ucmd, None))
		return DropTarget.DROPEFFECT_NONE

	def droptool(self, dataobj, effect, x, y):
		flavor, ucmd = DropTarget.DecodeDragData(dataobj)
		assert flavor == 'Tool'
		if ucmd:
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)

			return self.onEventEx(DropNode,
					(x, y, 'copy', ucmd, None))
		return DropTarget.DROPEFFECT_NONE

	def dragnodeuid(self, dataobj, kbdstate, x, y):
		flavor, data = DropTarget.DecodeDragData(dataobj)
		assert flavor == 'NodeUID'
		if data:
			contextid, nodeuid = data
			ucmd = usercmd.DRAG_NODEUID
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)
			if self.isControlPressed(kbdstate):
				cmd = 'copy'
			else:
				cmd = 'move'
			return self.onEventEx(DragNode,
					(x, y, cmd, ucmd, (contextid, nodeuid)))
		return DropTarget.DROPEFFECT_NONE

	def dropnodeuid(self, dataobj, effect, x, y):
		flavor, data = DropTarget.DecodeDragData(dataobj)
		assert flavor == 'NodeUID'
		if data:
			contextid, nodeuid = data
			ucmd = usercmd.DRAG_NODEUID
			x, y = self._DPtoLP((x,y))
			x, y = self._pxl2rel((x, y),self._canvas)

			if effect == DropTarget.DROPEFFECT_MOVE:
				cmd = 'move'
			else:
				cmd = 'copy'

			return self.onEventEx(DropNode,
					(x, y, cmd, ucmd, (contextid, nodeuid)))

		return DropTarget.DROPEFFECT_NONE
