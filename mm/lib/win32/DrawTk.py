__version__ = "$Id$"

""" @win32doc|DrawTk
A general and extensible win32 drawing toolkit
In its current version although it has a general
and extensible structure the tools and the objects 
implemeted support only drawing/resizing/selecting rectangles
needed by the cmif application
The base classes defined in this module are the DrawTool,and DrawObj.
The SelectTool and the RectTool are extensions to the DrawTool
The DrawRect is one extension to the DrawObj
The DrawTk is a utility class 
The DrawLayer is a mixin class for windows that want to offer drawing facilities
"""

# Win32 Drawing Toolkit

import win32ui,win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

import win32mu
from win32mu import Point,Size,Rect # shorcuts
from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL


# Global Context 
drawTk = None 

################################# DrawTool
# base class for drawing tools
class DrawTool:
	def __init__(self,toolType):
		self._toolType=toolType

	def setunits(self, units):
		self._units = units

	def onLButtonDown(self,view,flags,point):
		drawTk.SetCapture(view)
		drawTk.down_flags = flags
		drawTk.down = point
		drawTk.last = point

	def onLButtonDblClk(self,view,flags,point):
		pass

	def onLButtonUp(self,view,flags,point):
		drawTk.ReleaseCapture(view)
		if point.iseq(drawTk.down):
			drawTk.currentToolType = drawTk.TOOL_SELECT

	def onMouseMove(self,view,flags,point):
		drawTk.last = point
		cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
		drawTk.SetCursor(view,cursor)

	# Cancel drawing
	def onCancel(self):
		drawTk.currentToolType = TOOL_SELECT



################################# SelectTool

class SelectTool(DrawTool):
	def __init__(self):
		DrawTool.__init__(self,DrawTk.TOOL_SELECT)

	def onLButtonDown(self,view,flags,point):
		local = view.ClientToCanvas(point)

		drawObj=None
		drawTk.selectMode = drawTk.SM_NONE

		# Check for resizing (only allowed on single selections)
		if len(view._selection) == 1:
			drawObj = view._selection[0]
			drawTk.ixDragHandle = drawObj.hitTest(local,view,1)
			if drawTk.ixDragHandle != 0:
				drawTk.selectMode = drawTk.SM_SIZE
				# for smoother behavior set cursor here
				drawTk.SetCursor(view,drawObj.getHandleCursor(drawTk.ixDragHandle))

		# See if the click was on an object, select and start move if so
		if drawTk.selectMode == drawTk.SM_NONE:
			drawObj = view.ObjectAt(local);
			if drawObj:
				drawTk.selectMode = drawTk.SM_MOVE
				if not view.IsSelected(drawObj):
					view.Select(drawObj, (flags & win32con.MK_SHIFT))
				# Ctrl+Click clones the selection...
				if (flags & win32con.MK_CONTROL) != 0:
					view.CloneSelection()


		# Click on background, start a net-selection
		if drawTk.selectMode == drawTk.SM_NONE:
			if (flags & win32con.MK_SHIFT) == 0:
				view.Select(None)

			drawTk.selectMode = drawTk.SM_NET

			dc=view.GetDC()
			rect=Rect((point.x, point.y, point.x, point.y))
			rect.normalizeRect()
			dc.DrawFocusRect(rect.tuple())
			view.ReleaseDC(dc)

		drawTk.lastPoint = local
		DrawTool.onLButtonDown(self,view,flags, point);

	def onLButtonDblClk(self,view,flags,point):
		if (flags & win32con.MK_SHIFT) != 0:
			# Shift+DblClk deselects object...
			local=view.ClientToCanvas(point);
			drawObj = view.ObjectAt(local)
			if drawObj:
				view.Deselect(drawObj)
		else:
			# Normal DblClk opens properties
			if len(view._selection)==1:
				view._selection[0].onOpen(view)
		DrawTool.onLButtonDblClk(self,view,flags,point)


	def onLButtonUp(self,view,flags,point):
		if drawTk.MouseCaptured(view):
			if drawTk.selectMode == drawTk.SM_NET:
				dc=view.GetDC()
				rect=Rect((drawTk.down.x, drawTk.down.y, drawTk.last.x, drawTk.last.y))
				rect.normalizeRect();
				dc.DrawFocusRect(rect.tuple())
				view.ReleaseDC(dc)
				view.SelectWithinRect(rect,1)
			elif drawTk.selectMode != drawTk.SM_NONE:
				dc=view.GetDC()
				view.InvalidateRect()
				view.ReleaseDC(dc)
		DrawTool.onLButtonUp(self,view,flags,point)

	def onMouseMove(self,view,flags,point):
		if not drawTk.MouseCaptured(view):
			if drawTk.currentToolType == drawTk.TOOL_SELECT and len(view._selection) == 1:
				drawObj = view._selection[0]
				local=view.ClientToCanvas(point)
				nHandle = drawObj.hitTest(local,view, 1)
				if nHandle != 0:
					drawTk.SetCursor(view,drawObj.getHandleCursor(nHandle))
					return # bypass DrawTool
			if drawTk.currentToolType == drawTk.TOOL_SELECT:
				DrawTool.onMouseMove(self,view,flags,point)
			return

		if drawTk.selectMode == drawTk.SM_NET:
			dc=view.GetDC()
			rect=Rect((drawTk.down.x, drawTk.down.y, drawTk.last.x, drawTk.last.y))
			rect.normalizeRect()
			dc.DrawFocusRect(rect.tuple())
			rect.setRect(drawTk.down.x, drawTk.down.y, point.x, point.y)
			rect.normalizeRect()
			dc.DrawFocusRect(rect.tuple())
			view.ReleaseDC(dc)
			DrawTool.onMouseMove(self,view,flags,point)
			return

		local=view.ClientToCanvas(point)
		delta = Point.subtr(local,drawTk.lastPoint)
		for drawObj in view._selection:
			position = Rect(drawObj._position.tuple())
			if drawTk.selectMode == DrawTk.SM_MOVE:
				position.moveByPt(delta)
				drawObj.moveTo(position,view)
			elif drawTk.ixDragHandle != 0:
				drawObj.moveHandleTo(drawTk.ixDragHandle,local,view)

		drawTk.lastPoint = local

		if drawTk.selectMode == drawTk.SM_SIZE and drawTk.currentToolType == drawTk.TOOL_SELECT:
			drawTk.last = point
			cursor=view._selection[0].getHandleCursor(drawTk.ixDragHandle)
			drawTk.SetCursor(view,cursor)
			return # bypass DrawTool

		drawTk.last = point

		if drawTk.currentToolType == DrawTk.TOOL_SELECT:
			DrawTool.onMouseMove(self,view,flags,point)


class RectTool(DrawTool):
	def __init__(self):
		DrawTool.__init__(self,DrawTk.TOOL_RECT)

	def onLButtonDown(self,view,flags,point):
		DrawTool.onLButtonDown(self,view,flags,point)

		local=view.ClientToCanvas(point)
		drawObj = DrawRect(Rect((local.x,local.y,local.x,local.y)), units = self._units)
		view.Add(drawObj)
		view.Select(drawObj)

		drawTk.selectMode = DrawTk.SM_SIZE
		drawTk.ixDragHandle = 5
		drawTk.lastPoint = local

	def onLButtonDblClk(self,view,flags,point):
		DrawTool.onLButtonDblClk(self,view,flags,point)

	def onLButtonUp(self,view,flags,point):
		if point.iseq(drawTk.down):
			# don't create empty objects...
			if len(view._selection):
				drawObj = view._selection[len(view._selection)-1]
				view.Remove(drawObj);
				del drawObj
			drawTk.selectTool.onLButtonDown(view,flags,point) # try a select!
		drawTk.selectTool.onLButtonUp(view,flags,point)
		drawTk.OnNewRect(view)		

	def onMouseMove(self,view,flags,point):
		cursor=Sdk.LoadStandardCursor(win32con.IDC_CROSS)
		drawTk.SetCursor(view,cursor)
		drawTk.selectTool.onMouseMove(view,flags,point)

#################################			
class DrawObj:
	def __init__(self,rc):
		self._position=Rect(rc.tuple())
		self._shape=0
		self._pen = win32mu.Pen(win32con.PS_INSIDEFRAME,Size((1,1)),(0,0,0))
		self._brush=win32mu.Brush(win32con.BS_SOLID,(192, 192, 192),win32con.HS_HORIZONTAL)

	def __del__(self):
		# release resources
		pass
	# Return the number if handles 
	def getHandleCount(self):
		return 8

	# Return the bounding box
	def getbbox(self):
		return self._position.tuple()

	# Return the handle at index
	def getHandle(self,ix):
		"""returns logical coords of center of handle"""
	
		# this gets the center regardless of left/right and top/bottom ordering
		xCenter = self._position.left + self._position.width() / 2
		yCenter = self._position.top + self._position.height() / 2

		if ix== 1:
			x = self._position.left
			y = self._position.top
		elif ix== 2:
			x = xCenter;
			y = self._position.top
		elif ix== 3:
			x = self._position.right;
			y = self._position.top;
		elif ix== 4:
			x = self._position.right;
			y = yCenter;
		elif ix== 5:
			x = self._position.right;
			y = self._position.bottom;
		elif ix== 6:
			x = xCenter;
			y = self._position.bottom;
		elif ix== 7:
			x = self._position.left;
			y = self._position.bottom;
		elif ix== 8:
			x = self._position.left;
			y = yCenter;
		else:
			raise error, 'invalid handle'
		return Point((x, y))

	# Return handle's rectangle
	def getHandleRect(self,ix,view):
		"""return rectange of handle in logical coords"""
		if not view: return
		# get the center of the handle in logical coords
		point = self.getHandle(ix)
		# convert to device coords 
		# (not needed if logical coordinates in MM_TEXT )
		point=view.CanvasToClient(point)
		# return Rect of handle in device coords
		rect=Rect((point.x-3, point.y-3, point.x+3, point.y+3))
		return view.ClientToCanvasRect(rect)

	# Return the appropriate for the handle cursor
	def getHandleCursor(self,ix):
		if   ix==1 or ix==5:id = win32con.IDC_SIZENWSE
		elif ix==2 or ix==6:id = win32con.IDC_SIZENS
		elif ix==3 or ix==7:id = win32con.IDC_SIZENESW
		elif ix==4 or ix==8:id = win32con.IDC_SIZEWE
		else:raise error, 'invalid handle'
		return Sdk.LoadStandardCursor(id)

	def setLineColor(self,color):
		self._pen._color=color
		self.invalidate()
	def setFillColor(self,color):
		self._brush._color=color
		self.invalidate()

	# operations
	def draw(self,dc):
		# will be overwritten
		pass

	# Draw a small trag rect for each handle
	def drawTracker(self,dc,trackerState):
		if trackerState==DrawObj.normal:
			pass
		elif trackerState==DrawObj.selected or trackerState==DrawObj.active:
			nHandleCount = self.getHandleCount()		
			for nHandle in range(1,nHandleCount+1):
				handlept=self.getHandle(nHandle)
				dc.PatBlt((handlept.x - 3, handlept.y - 3), (7, 7), win32con.DSTINVERT);
		pass

	def moveTo(self,position,view=None):
		if position.iseq(self._position):
			return
		if not view:
			self.invalidate()
			self._position.setToRect(position)
			self.invalidate();
		else:
			view.InvalObj(self)
			self._position.setToRect(position)
			view.InvalObj(self)

	# Returns true if the point is within the object
	def hitTest(self,point,view,is_selected):
		"""
		Note: if isselected, hit-codes start at one for the top-left
		and increment clockwise, 0 means no hit.
		If not selected, 0 = no hit, 1 = hit (anywhere)
		point is in logical coordinates
		"""
		assert(view)

		if is_selected:
			nHandleCount = self.getHandleCount()
			for nHandle in range(1,nHandleCount+1):
				# GetHandleRect returns in logical coords
				rc = self.getHandleRect(nHandle,view)
				if rc.isPtInRect(point): 
					return nHandle
		else:
			if self._position.isPtInRect(point):return 1
		return 0

	# Returns true if the rect intersects the object
	def intersects(self,rect):
		"""rect must be in logical coordinates"""
		rect.normalizeRect()
		self._position.normalizeRect()
		return Rect.intersect(rect,self._position)

	def moveHandleTo(self,ixHandle,point,view = None):
		"""point must be in logical coordinates"""
		position = Rect(self._position.tuple())
		if	ixHandle== 1:
			position.left = point.x
			position.top = point.y
		elif ixHandle== 2:
			position.top = point.y
		elif ixHandle== 3:
			position.right = point.x
			position.top = point.y
		elif ixHandle== 4:
			position.right = point.x
		elif ixHandle== 5:
			position.right = point.x
			position.bottom = point.y
		elif ixHandle== 6:
			position.bottom = point.y
		elif ixHandle== 7:
			position.left = point.x
			position.bottom = point.y
		elif ixHandle== 8:
			position.left = point.x
		else:
			raise error, 'invalid handle'
		position.normalizeRect()
		self.moveTo(position,view)

	def invalidate(self):
		self.UpdateObj(DrawTk.HINT_UPDATE_DRAWOBJ,self)

	def clone(self,context=None):
		clone = DrawObj(self._position)
		clone._pen = self._pen
		clone._brush = self._brush
		if context:
			context.Add(clone);
		return clone

	# class attributes
	[normal, selected, active]=range(3)

# A rectangle drawing tool

class DrawRect(DrawObj):
	def __init__(self,pos,units=None):
		self.__units = units
		DrawObj.__init__(self,pos)
	def getHandleCount(self):
		return DrawObj.getHandleCount(self)
	def getHandle(self,ix):
		return DrawObj.getHandle(self,ix)
	def getHandleCursor(self,ixHandle):
		return DrawObj.getHandleCursor(self,ixHandle)
	def moveHandleTo(self,ixHandle,point,view = None):
		return DrawObj.moveHandleTo(self,ixHandle,point,view)
	def intersects(self,rect):
		return DrawObj.intersects(self,rect)
	def clone(self,context=None):
		return DrawObj.clone(self,context)

	def draw(self,dc):
		# create pen and brush and select them in dc
		pen=Sdk.CreatePen(win32con.PS_SOLID,0,win32mu.RGB((255,0,0)))
		oldpen=dc.SelectObjectFromHandle(pen)
		#dc.Rectangle(self._position.tuple())
		#dc.FillSolidRect(self._position.tuple(),win32mu.RGB((0,255,0)))
		win32mu.FrameRect(dc,self._position.tuple(),(255,0,0))
		# write dimensions
		#s='(%d,%d,%d,%d)' % self._position.tuple() #pixels
		if self.__units == UNIT_PXL:
			s='(%d,%d,%d,%d)' % self._position.tuple_ps()
		elif self.__units == UNIT_SCREEN and drawTk._rel_coord_ref:
			s='(%.2f,%.2f,%.2f,%.2f)' % drawTk._rel_coord_ref.get_relative_coords100(self._position.tuple_ps())
		else:
			s=''
		if s:
			drawTk.SetSmallFont(dc)
			dc.SetBkMode(win32con.TRANSPARENT)
			dc.DrawText(s,self._position.tuple(),win32con.DT_SINGLELINE|win32con.DT_CENTER|win32con.DT_VCENTER)
		
		# if it is selected draw tracker
		#if self._is_selected:
		#	self.drawTracker(dc,DrawObj.selected)

#		drawTk.RestoreFont(dc)
		dc.SelectObjectFromHandle(oldpen)
		Sdk.DeleteObject(pen)
		# restore dc by selecting old pen and brush
	def GetRelCoord_X(self):
		rc_client=Rect(self._context._views[0].GetClientRect())
		x,y,w,h= drawTk.ToRelCoord(self._position,rc_client)
		return float(x)/100.0,float(y)/100.0,float(w)/100.0,float(h)/100.0

# Context class for draw toolkit

class DrawTk:
	# supported tools
	[TOOL_SELECT,TOOL_RECT] = range(2)

	# Hints for OnUpdate
	[	HINT_UPDATE_WINDOW,
		HINT_UPDATE_DRAWOBJ,
		HINT_UPDATE_SELECTION,
		HINT_DELETE_SELECTION,
	] = range(4)

	# select modes
	[	SM_NONE,
		SM_NET,
		SM_MOVE,
		SM_SIZE
	]=range(4)

	def __init__(self):
		self.tool={
			DrawTk.TOOL_SELECT:SelectTool(),
			DrawTk.TOOL_RECT:RectTool()}
		self.down=Point((0,0))
		self.down_flags=0
		self.last=Point((0,0))
		self.currentToolType=DrawTk.TOOL_RECT
		self.selectTool=self.tool[DrawTk.TOOL_SELECT]
		self.rectTool=self.tool[DrawTk.TOOL_RECT]
		self.selectMode = DrawTk.SM_NONE
		self.ixDragHandle=0
		self.lastPoint=Point()
		self._hsmallfont=0
		self._limit_rect=1 # for cmif app
		self._capture=None

	def __del__(self):
		if self._hsmallfont:
			Sdk.DeleteObject(self._hsmallfont)
			self._hsmallfont = 0

	def release(self):
		if self._hsmallfont:
			Sdk.DeleteObject(self._hsmallfont)
			self._hsmallfont = 0
		
	def SetCursor(self,view,cursor):
		if cursor!=Sdk.GetCursor():
			#Sdk.SetCursor(cursor)
			Sdk.SetClassLong(view.GetSafeHwnd(),win32con.GCL_HCURSOR,cursor)
			
	def SetCapture(self,wnd):
		self._capture=wnd
	def ReleaseCapture(self,view):
		self._capture=None
	def MouseCaptured(self,wnd):
		return (self._capture==wnd)

	def GetCurrentTool(self):
		return self.tool.get(self.currentToolType)

	def SelectTool(self,tool='select', units = None):
		if tool=='select':
			self.currentToolType=DrawTk.TOOL_SELECT
		elif tool=='rect':
			self.currentToolType=DrawTk.TOOL_RECT
		else:
			self.currentToolType=DrawTk.TOOL_SELECT
		self.tool[self.currentToolType].setunits(units)
	def LimitRects(self,num):
		self._limit_rect=num
	def OnNewRect(self,view):
		if hasattr(self,'_limit_rect'):
			if len(view._objects)>=self._limit_rect:
				self.currentToolType=DrawTk.TOOL_SELECT	
					
	def SetSmallFont(self,dc):
		if not self._hsmallfont:
			fd={'name':'Arial','height':10,'weight':700}
			self._hsmallfont=Sdk.CreateFontIndirect(fd)		
		self._hfont_org=dc.SelectObjectFromHandle(self._hsmallfont)
	def RestoreFont(self,dc):
		dc.SelectObjectFromHandle(self._hfont_org)

	def SetRelCoordRef(self,wnd):
		self._rel_coord_ref=wnd

	# Convert to relative coordinates
	def ToRelCoord(self,rc,rcref):
		x=int(100.0*float(rc.left)/rcref.width()+0.5)
		y=int(100.0*float(rc.top)/rcref.height()+0.5)
		w=int(100.0*float(rc.width())/rcref.width()+0.5)
		h=int(100.0*float(rc.height())/rcref.height()+0.5)
		return (x,y,w,h)


# Global Context 
drawTk=	DrawTk()

#########################	
# MFC View or Layer for other views
	
class DrawLayer:
	def __init__(self):
		self._dragPoint=Point() # current position
		self._dragSize=Size()   # size of dragged object
		self._dragOffset=Point()# offset between pt and drag object corner
		self._objects=[]
		self._selection=[]
		self._grid=1
		self._gridColor=(0, 0, 128)
		self._active=1

	# std view stuff
	def OnUpdate(self,viewSender,hint=None,hintObj=None):
		if hint==DrawTk.HINT_UPDATE_WINDOW:   # redraw entire window
			self.InvalidateRect()
		elif hint==DrawTk.HINT_UPDATE_DRAWOBJ:   # a single object has changed
			self.InvalObj(hintObj)
		elif hint==DrawTk.HINT_UPDATE_SELECTION: # an entire selection list has changed
			if not hintObj:hintObj=self._selection
			for obj in hintObj:
				self.InvalObj(obj)
		elif hint==DrawTk.HINT_DELETE_SELECTION: # an entire selection has been removed
			if hintObj:
				for obj in hintObj:
					self.InvalObj(obj)
					self.Remove(obj)
		else:
			self.InvalidateRect()

	# Convert coordinates CanvasToClient
	def CanvasToClient(self,point):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		point=dc.LPtoDP(point.tuple())
		self.ReleaseDC(dc)
		return Point(point)

	# Convert coordinates CanvasToClient Rect
	def CanvasToClientRect(self,rect):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		pos=dc.LPtoDP(rect.pos())
		rb_pos=dc.LPtoDP(rect.rb_pos())
		self.ReleaseDC(dc)
		return Rect((pos[0],pos[1],rb_pos[0],rb_pos[1]))


	# Convert coordinates ClientToCanvas
	def ClientToCanvas(self,point):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		point=dc.DPtoLP(point.tuple());
		self.ReleaseDC(dc)
		return Point(point)

	# Convert coordinates ClientToCanvas rect
	def ClientToCanvasRect(self,rect):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		pos=dc.DPtoLP(rect.pos())
		rb_pos=dc.DPtoLP(rect.rb_pos())
		self.ReleaseDC(dc)
		return Rect((pos[0],pos[1],rb_pos[0],rb_pos[1]))

	# Select the object
	def Select(self,drawObj,add = 0):
		if not add:
			self.OnUpdate(None,DrawTk.HINT_UPDATE_SELECTION,None)
			del self._selection
			self._selection=[]
		if not drawObj or self.IsSelected(drawObj):
			return
		self._selection.append(drawObj)
		#drawObj.select(1)
		self.InvalObj(drawObj)

	# Select objects within rect
	def SelectWithinRect(self,rect,add = 0):
		"""rect is in device coordinates"""
		if not add:
			self.Select(None)
		rect=self.ClientToCanvasRect(rect)
		objList = self._objects
		for obj in objList:
			if obj.intersects(rect):
				self.Select(obj,1)
				

	def Deselect(self,drawObj):
		for obj in self._selection:
			if obj==drawObj:
				self.InvalObj(drawObj)
				self._selection.remove(drawObj)
				break


	def CloneSelection(self):
		for ix in range(len(self._selection)):
			drawObj=self._selection[ix]
			drawObj.clone(drawObj._context)

	def InvalObj(self,drawObj):
		rect = Rect(drawObj._position.tuple())
		rect=self.CanvasToClientRect(rect);
		if self._active and self.IsSelected(drawObj):
			rect.left =rect.left-4;
			rect.top = rect.top-5;
			rect.right = rect.right+5;
			rect.bottom = rect.bottom+4;
		rect.inflateRect(1,1) 
		self.InvalidateRect(rect.tuple(),0)

	def Remove(self,drawObj):
		for obj in self._selection:
			if obj==drawObj:
				self._selection.remove(drawObj)
				break
	def IsSelected(self,drawObj):
		for obj in self._selection:
			if obj==drawObj:return 1
		return 0

	def onCancelEdit(self):
		"""
		The following command handler provides the standard keyboard
		user interface to cancel an in-place editing session.
		"""
		self.ReleaseCapture();

		drawTool = drawTk.GetCurrentTool()
		if drawTool:
			drawTool.onCancel()
		drawTk.currentToolType = drawTk.TOOL_SELECT

	def onEditClear(self):
		# update all the views before the selection goes away
		self.UpdateObj(DrawTk.HINT_DELETE_SELECTION,self._selection)
		self.OnUpdate(None,DrawTk.HINT_UPDATE_SELECTION,None)

		# now remove the selection from the document
		for obj in self._selection:
			self.Remove(obj)
			del obj
		del self._selection
		self._selection=[]

	def OnInitialUpdate(self):
		drawTk.currentToolType = drawTk.TOOL_SELECT


	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam
		drawTool = drawTk.GetCurrentTool()
		if drawTool:
			drawTool.onLButtonDown(self,flags,point);

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam
		drawTool = drawTk.GetCurrentTool()
		if drawTool:
			drawTool.onLButtonUp(self,flags,point);

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam

		point_dp=self.ClientToCanvas(point)
		drawObj=self.ObjectAt(point_dp)
		if drawObj:
			s='rect: (%d,%d,%d,%d)' % drawObj._position.tuple()
			win32ui.MessageBox(s)
			return
		drawTool = drawTk.GetCurrentTool()
		if drawTool:
			drawTool.onLButtonDblClk(self,flags,point);

	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam
		drawTool = drawTk.GetCurrentTool()
		if drawTool:
			drawTool.onMouseMove(self,flags,point)

	# Called when the activation changes
	def OnActivateView(self,activate,activeView,deactiveView):
		self._obj_.OnActivateView(activate,activeView,deactiveView)
		if self._active != activate:
			if activate:
				self._active = activate
		if	len(self._selection):
			self.OnUpdate(None, DrawTk.HINT_UPDATE_SELECTION, None);
		self._active = activate

	def onSize(self,params):
		pass

	# An optimized Drawing function while using the toolkit
	def DrawObjLayer(self,dc):
		# only paint the rect that needs repainting
		rect=self.CanvasToClientRect(Rect(dc.GetClipBox()))

		# draw to offscreen bitmap for fast looking repaints
		dcc=win32ui.CreateDC()
		dcc.CreateCompatibleDC(dc)

		bmp=win32ui.CreateBitmap()
		bmp.CreateCompatibleBitmap(dc,rect.width(),rect.height())
		
		#self.OnPrepareDC(dcc)
		
		# offset origin more because bitmap is just piece of the whole drawing
		dcc.OffsetViewportOrg((-rect.left, -rect.top))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.SetBrushOrg((rect.left % 8, rect.top % 8))
		dcc.IntersectClipRect(rect.tuple())

		# background decoration on dcc
		#dcc.FillSolidRect(rect.tuple(),win32mu.RGB((228,255,228)))
		dcc.FillSolidRect(rect.tuple(),win32mu.RGB(self._active_displist._bgcolor))

		# draw objects on dcc
		if self._active_displist:
			self._active_displist._render(dcc,rect.tuple())
		self.DrawObjectsOn(dcc)

		# show draw area
		#l,t,w,h=self._canvas
		#win32mu.FrameRect(dcc,(l,t,l+w,t+h),(255,0,0))

		# copy bitmap
		dc.SetViewportOrg((0, 0))
		dc.SetWindowOrg((0,0))
		dc.SetMapMode(win32con.MM_TEXT)
		dcc.SetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		dcc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt(rect.pos(),rect.size(),dcc,(0, 0), win32con.SRCCOPY)

		# clean up (revisit this)
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC() # needed?
		del bmp



	# Context behaviour
	def UpdateObj(self,hint=None,hintObj=None):
		self.OnUpdate(sender,hint,hintObj)

	# draw support
	def ObjectAt(self,point):
		"""point is in logical coordinates"""
		rect=Rect((point.x,point.y,point.x+1,point.y+1))
		l=self._objects[:]
		l.reverse()
		for obj in l:
			if obj.intersects(rect):
				return obj
		return None

	def DrawObjectsOn(self,dc):
		for obj in self._objects:
			obj.draw(dc)
			if self.IsSelected(obj):
				obj.drawTracker(dc,DrawObj.selected)

	def Add(self,drawObj):
		self._objects.append(drawObj)

	def Remove(self,drawObj):
		for obj in self._objects:
			if obj==drawObj:	
				self._objects.remove(drawObj)
				break

	def DeleteContents(self):
		self._objects=[]
