__version__ = "$Id$"

""" @win32doc|DrawTk
The basic classes defined in this module are the DrawTool and the DrawObj.
The SelectTool and the RectTool are extensions to the DrawTool
The DrawRect is an extension to the DrawObj
The DrawLayer is a mixin class for windows
"""

# Win32 Drawing Toolkit

import win32ui,win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

import win32mu
from win32mu import Point,Size,Rect # shorcuts
from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL
import sysmetrics

# tools
[TOOL_SELECT,TOOL_RECT] = range(2)

# select modes
[SM_NONE, SM_NET, SM_MOVE, SM_SIZE]=range(4)

# Hints for update
[HINT_UPDATE_WINDOW, HINT_UPDATE_DRAWOBJ, HINT_UPDATE_SELECTION, HINT_DELETE_SELECTION] = range(4)

################################# DrawTool
# base class for drawing tools
class DrawTool:
	def __init__(self, wnd, toolType):
		self._wnd = wnd
		self._toolType=toolType
		self._client_units = 0

	def setunits(self, units):
		self._client_units = units

	def onLButtonDown(self, flags, point):
		wnd = self._wnd
		wnd.SetCapture()
		wnd.down_flags = flags
		wnd.down = point
		wnd.last = point

	def onLButtonUp(self, flags, point):
		wnd = self._wnd
		wnd.ReleaseCapture()
		if point.iseq(wnd.down):
			wnd.currentToolType = TOOL_SELECT

	def onMouseMove(self, flags, point):
		wnd = self._wnd
		wnd.last = point
		cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
		wnd.SetCursor(cursor)

	def onLButtonDblClk(self, flags, point):
		pass

	# cancel drawing
	def onCancel(self):
		self._wnd.currentToolType = TOOL_SELECT


################################# SelectTool

class SelectTool(DrawTool):
	def __init__(self, wnd):
		DrawTool.__init__(self, wnd, TOOL_SELECT)

	def onLButtonDown(self, flags, point):
		wnd = self._wnd
		local = wnd.ClientToCanvas(point)
		drawObj=None
		wnd.selectMode = SM_NONE

		# Check for resizing (only allowed on single selections)
		if len(wnd._selection) == 1:
			drawObj = wnd._selection[0]
			wnd.ixDragHandle = drawObj.hitTest(local,1)
			if wnd.ixDragHandle != 0:
				wnd.selectMode = SM_SIZE
				# for smoother behavior set cursor here
				wnd.SetCursor(drawObj.getHandleCursor(wnd.ixDragHandle))

		# See if the click was on an object, select and start move if so
		if wnd.selectMode == SM_NONE:
			drawObj = wnd.ObjectAt(local);
			if drawObj:
				wnd.selectMode = SM_MOVE
				if not wnd.IsSelected(drawObj):
					wnd.Select(drawObj, (flags & win32con.MK_SHIFT))
				# Ctrl+Click clones the selection...
				if (flags & win32con.MK_CONTROL) != 0:
					wnd.CloneSelection()

		# Click on background, start a net-selection
		if wnd.selectMode == SM_NONE:
			if (flags & win32con.MK_SHIFT) == 0:
				wnd.Select(None)

			wnd.selectMode = SM_NET

			dc=wnd.GetDC()
			rect=Rect((point.x, point.y, point.x, point.y))
			rect.normalizeRect()
			dc.DrawFocusRect(rect.tuple())
			wnd.ReleaseDC(dc)

		wnd.lastPoint = local
		DrawTool.onLButtonDown(self, flags, point)

	def onLButtonUp(self, flags, point):
		wnd = self._wnd
		if wnd.MouseCaptured():
			if wnd.selectMode == SM_NET:
				dc=wnd.GetDC()
				rect=Rect((wnd.down.x, wnd.down.y, wnd.last.x, wnd.last.y))
				rect.normalizeRect();
				dc.DrawFocusRect(rect.tuple())
				wnd.ReleaseDC(dc)
				wnd.SelectWithinRect(rect,1)
			elif wnd.selectMode != SM_NONE:
				dc=wnd.GetDC()
				wnd.InvalidateRect()
				wnd.ReleaseDC(dc)
		DrawTool.onLButtonUp(self, flags, point)

	def onMouseMove(self, flags, point):
		wnd = self._wnd
		if not wnd.MouseCaptured():
			if wnd.currentToolType == TOOL_SELECT and len(wnd._selection) == 1:
				drawObj = wnd._selection[0]
				local=wnd.ClientToCanvas(point)
				nHandle = drawObj.hitTest(local,1)
				if nHandle != 0:
					wnd.SetCursor(drawObj.getHandleCursor(nHandle))
					return # bypass DrawTool
			if wnd.currentToolType == TOOL_SELECT:
				DrawTool.onMouseMove(self,flags,point)
			return

		if wnd.selectMode == SM_NET:
			dc=wnd.GetDC()
			rect=Rect((wnd.down.x, wnd.down.y, wnd.last.x, wnd.last.y))
			rect.normalizeRect()
			dc.DrawFocusRect(rect.tuple())
			rect.setRect(wnd.down.x, wnd.down.y, point.x, point.y)
			rect.normalizeRect()
			dc.DrawFocusRect(rect.tuple())
			wnd.ReleaseDC(dc)
			DrawTool.onMouseMove(self,flags,point)
			return

		local=wnd.ClientToCanvas(point)
		delta = Point.subtr(local,wnd.lastPoint)
		for drawObj in wnd._selection:
			position = Rect(drawObj._position.tuple())
			if wnd.selectMode == SM_MOVE:
				position.moveByPt(delta)
				drawObj.moveTo(position)
				if delta.x+delta.y:wnd.SetDrawObjDirty(1)
			elif wnd.ixDragHandle != 0:
				drawObj.moveHandleTo(wnd.ixDragHandle,local)
				wnd.SetDrawObjDirty(1)

		wnd.lastPoint = local

		if wnd.selectMode == SM_SIZE and wnd.currentToolType == TOOL_SELECT:
			wnd.last = point
			cursor=wnd._selection[0].getHandleCursor(wnd.ixDragHandle)
			wnd.SetCursor(cursor)
			return # bypass DrawTool

		wnd.last = point

		if wnd.currentToolType == TOOL_SELECT:
			DrawTool.onMouseMove(self, flags, point)

	def onLButtonDblClk(self, flags, point):
		wnd = self._wnd
		if (flags & win32con.MK_SHIFT) != 0:
			# Shift+DblClk deselects object...
			local=wnd.ClientToCanvas(point);
			drawObj = wnd.ObjectAt(local)
			if drawObj:
				wnd.Deselect(drawObj)
		else:
			# Normal DblClk opens properties
			if len(wnd._selection)==1:
				wnd._selection[0].onOpen()
		DrawTool.onLButtonDblClk(self, flags, point)


class RectTool(DrawTool):
	def __init__(self, wnd):
		DrawTool.__init__(self, wnd, TOOL_RECT)

	def onLButtonDown(self, flags, point):
		wnd = self._wnd
		DrawTool.onLButtonDown(self, flags, point)
		local=wnd.ClientToCanvas(point)
		drawObj = DrawRect(wnd, Rect((local.x,local.y,local.x,local.y)), units = self._client_units)
		wnd.Add(drawObj)
		wnd.Select(drawObj)

		wnd.selectMode = SM_SIZE
		wnd.ixDragHandle = 5
		wnd.lastPoint = local

	def onLButtonDblClk(self, flags, point):
		DrawTool.onLButtonDblClk(self, flags, point)

	def onLButtonUp(self, flags, point):
		wnd = self._wnd
		if point.iseq(wnd.down):
			# don't create empty objects...
			if len(wnd._selection):
				drawObj = wnd._selection[len(wnd._selection)-1]
				wnd.Remove(drawObj);
				del drawObj
			wnd.selectTool.onLButtonDown(wnd,flags,point) # try a select!
		wnd.selectTool.onLButtonUp(flags, point)
		wnd.OnNewRect()		

	def onMouseMove(self, flags, point):
		wnd = self._wnd
		if not wnd.InDrawArea(point):
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
			wnd.SetCursor(cursor)
		else:
			cursor=Sdk.LoadStandardCursor(win32con.IDC_CROSS)
			wnd.SetCursor(cursor)
			wnd.selectTool.onMouseMove(flags, point)

#################################			
class DrawObj:
	def __init__(self, wnd, rc, units=None):
		self._wnd = wnd
		self._position=Rect(rc.tuple())
		self._shape=0
		self._pen = win32mu.Pen(win32con.PS_INSIDEFRAME,Size((1,1)),(0,0,0))
		self._brush=win32mu.Brush(win32con.BS_SOLID,(192, 192, 192),win32con.HS_HORIZONTAL)
		self._client_units = units

	def setunits(self, units):
		self._client_units = units

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
	def getHandleRect(self, ix):
		"""return rectange of handle in logical coords"""
		wnd = self._wnd

		# get the center of the handle in logical coords
		point = self.getHandle(ix)
		# convert to device coords 
		# (not needed if logical coordinates in MM_TEXT )
		point=wnd.CanvasToClient(point)
		# return Rect of handle in device coords
		rect=Rect((point.x-3, point.y-3, point.x+3, point.y+3))
		return wnd.ClientToCanvasRect(rect)

	# Return the appropriate for the handle cursor
	def getHandleCursor(self, ix):
		if   ix==1 or ix==5:id = win32con.IDC_SIZENWSE
		elif ix==2 or ix==6:id = win32con.IDC_SIZENS
		elif ix==3 or ix==7:id = win32con.IDC_SIZENESW
		elif ix==4 or ix==8:id = win32con.IDC_SIZEWE
		else:raise error, 'invalid handle'
		return Sdk.LoadStandardCursor(id)

	def setLineColor(self, color):
		self._pen._color = color
		self.invalidate()

	def setFillColor(self, color):
		self._brush._color = color
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

	def moveTo(self, position):
		if position.iseq(self._position):
			return
		if not self._wnd.InDrawAreaRc(position):
			return
		if not self._wnd:
			self.invalidate()
			self._position.setToRect(position)
			self.invalidate();
		else:
			self._wnd.InvalObj(self)
			self._position.setToRect(position)
			self._wnd.InvalObj(self)

	# Returns true if the point is within the object
	def hitTest(self, point, is_selected):
		"""
		Note: if is selected, hit-codes start at one for the top-left
		and increment clockwise, 0 means no hit.
		If not selected, 0 = no hit, 1 = hit (anywhere)
		point is in logical coordinates
		"""
		wnd = self._wnd

		if is_selected:
			nHandleCount = self.getHandleCount()
			for nHandle in range(1,nHandleCount+1):
				# GetHandleRect returns in logical coords
				rc = self.getHandleRect(nHandle)
				if rc.isPtInRect(point): 
					return nHandle
		else:
			if self._position.isPtInRect(point):return 1
		return 0

	# Returns true if the rect intersects the object
	def intersects(self, rect):
		"""rect must be in logical coordinates"""
		rect.normalizeRect()
		self._position.normalizeRect()
		return Rect.intersect(rect,self._position)

	def moveHandleTo(self, ixHandle, point):
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
		self.moveTo(position)

	def invalidate(self):
		self.UpdateObj(HINT_UPDATE_DRAWOBJ,self)

	def clone(self, context=None):
		clone = DrawObj(self._position)
		clone._pen = self._pen
		clone._brush = self._brush
		clone._client_units= self._client_units
		if context:
			context.Add(clone);
		return clone

	# class attributes
	[normal, selected, active]=range(3)


#################
# A rectangle DrawObj

class DrawRect(DrawObj):
	def __init__(self, wnd, pos, units=None):
		DrawObj.__init__(self,wnd, pos, units)
	def getHandleCount(self):
		return DrawObj.getHandleCount(self)
	def getHandle(self,ix):
		return DrawObj.getHandle(self,ix)
	def getHandleCursor(self,ixHandle):
		return DrawObj.getHandleCursor(self,ixHandle)
	def moveHandleTo(self,ixHandle,point,wnd = None):
		return DrawObj.moveHandleTo(self,ixHandle,point)
	def intersects(self,rect):
		return DrawObj.intersects(self,rect)
	def clone(self,context=None):
		return DrawObj.clone(self,context)

	# fill with clr the dc outsite self._position
	def crcfill(self, dc, clr=(0,0,0)):
		cr = win32mu.RGB(clr)
		l,t,r,b = self._wnd._crect.tuple()
		li,ti,ri,bi = self._position.tuple()
		dc.FillSolidRect((l,t,li,b),cr)
		dc.FillSolidRect((l,t,r,ti),cr)
		dc.FillSolidRect((ri,t,r,b),cr)
		dc.FillSolidRect((l,bi,r,b),cr)

	# invert the dc outsite self._position
	def crcinvert(self, dc):
		l,t,r,b = self._wnd._crect.tuple()
		li,ti,ri,bi = self._position.tuple()
		dc.PatBlt((l,t),(r-l,b-t), win32con.DSTINVERT);
		dc.PatBlt((li,ti),(ri-li,bi-ti), win32con.DSTINVERT);
		
	def draw(self, dc):
		# create pen and brush and select them in dc
		pen=Sdk.CreatePen(win32con.PS_SOLID,0,win32mu.RGB((255,0,0)))
		oldpen=dc.SelectObjectFromHandle(pen)
		wnd = self._wnd

		if not wnd.InLayoutMode():
			if wnd._bkimg<0:
				clr=(0xC0, 0xC0, 0xC0)
				dc.FillSolidRect(self._position.tuple(),win32mu.RGB(clr))
			else:
				#self.crcfill(dc,(0,0,0))
				self.crcinvert(dc)

		win32mu.FrameRect(dc, self._position.tuple(), (255,0,0))
		
		if not wnd.InLayoutMode() and wnd._bkimg>=0:
			dc.SelectObjectFromHandle(oldpen)
			Sdk.DeleteObject(pen)
			return

		# write dimensions
		s=''
		str_units=''
		scale = wnd.GetScale()
		if scale:
			s, str_units = scale.orgrect_str(self._position,self._client_units)
		else:
			if self._client_units == UNIT_PXL:				
				s='(%d,%d,%d,%d)' % self._position.tuple_ps()
			elif self._client_units == UNIT_SCREEN and wnd._ref_wnd:
				s='(%.2f,%.2f,%.2f,%.2f)' % wnd._ref_wnd.inverse_coordinates(self._position.tuple_ps(),units=self._client_units)
			else:
				str_units='mm'
				s='(%.1f,%.1f,%.1f,%.1f)' % wnd._ref_wnd.inverse_coordinates(self._position.tuple_ps(),units=self._client_units)
		if s:
			wnd.SetSmallFont(dc)
			dc.SetBkMode(win32con.TRANSPARENT)
			dc.DrawText(s, self._position.tuple(), win32con.DT_SINGLELINE|win32con.DT_CENTER|win32con.DT_VCENTER)
			if str_units:
				rc=Rect(self._position.tuple())
				rc.moveByPt(Point((0,9)))
				dc.DrawText(str_units, rc.tuple(), win32con.DT_SINGLELINE|win32con.DT_CENTER|win32con.DT_VCENTER)
				
		# restore dc by selecting old pen and brush
		wnd.RestoreFont(dc)
		dc.SelectObjectFromHandle(oldpen)
		Sdk.DeleteObject(pen)


#########################	
# Layer for windows with drawing cabs
	
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
		self._drawObjIsDirty=0

		# tk section
		self.tool={TOOL_SELECT:SelectTool(self), TOOL_RECT:RectTool(self)}
		self.down=Point((0,0))
		self.down_flags=0
		self.last=Point((0,0))
		self.currentToolType=TOOL_RECT
		self.selectTool=self.tool[TOOL_SELECT]
		self.rectTool=self.tool[TOOL_RECT]
		self.selectMode = SM_NONE
		self.ixDragHandle=0
		self.lastPoint=Point()
		self._hsmallfont=0
		self._hfont_org=0
		self._limit_rect=1 # number of rect allowed
		self._capture=None
	
		# layout page support
		self._layoutmode=1
		self._brect=None
		self._crect=None
		self._scale=None
		self._bkimg=-1

	def __del__(self):
		if self._hsmallfont:
			Sdk.DeleteObject(self._hsmallfont)
			self._hsmallfont = 0

	# std wnd stuff
	def OnUpdate(self, wndSender, hint=None, hintObj=None):
		if hint==HINT_UPDATE_WINDOW:   # redraw entire window
			self.InvalidateRect()
		elif hint==HINT_UPDATE_DRAWOBJ:   # a single object has changed
			self.InvalObj(hintObj)
		elif hint==HINT_UPDATE_SELECTION: # an entire selection list has changed
			if not hintObj:hintObj=self._selection
			for obj in hintObj:
				self.InvalObj(obj)
		elif hint==HINT_DELETE_SELECTION: # an entire selection has been removed
			if hintObj:
				for obj in hintObj:
					self.InvalObj(obj)
					self.Remove(obj)
		else:
			self.InvalidateRect()

	# Convert coordinates CanvasToClient
	def CanvasToClient(self, point):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		point=dc.LPtoDP(point.tuple())
		self.ReleaseDC(dc)
		return Point(point)

	# Convert coordinates CanvasToClient Rect
	def CanvasToClientRect(self, rect):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		pos=dc.LPtoDP(rect.pos())
		rb_pos=dc.LPtoDP(rect.rb_pos())
		self.ReleaseDC(dc)
		return Rect((pos[0],pos[1],rb_pos[0],rb_pos[1]))

	# Convert coordinates ClientToCanvas
	def ClientToCanvas(self, point):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		point=dc.DPtoLP(point.tuple());
		self.ReleaseDC(dc)
		return Point(point)

	# Convert coordinates ClientToCanvas rect
	def ClientToCanvasRect(self, rect):
		dc=self.GetDC()
		#self.OnPrepareDC(dc)
		pos=dc.DPtoLP(rect.pos())
		rb_pos=dc.DPtoLP(rect.rb_pos())
		self.ReleaseDC(dc)
		return Rect((pos[0],pos[1],rb_pos[0],rb_pos[1]))

	# Select the object
	def Select(self, drawObj, add = 0):
		if not add:
			self.OnUpdate(None,HINT_UPDATE_SELECTION,None)
			del self._selection
			self._selection=[]
		if not drawObj or self.IsSelected(drawObj):
			return
		self._selection.append(drawObj)
		#drawObj.select(1)
		self.InvalObj(drawObj)

	# Select objects within rect
	def SelectWithinRect(self, rect, add = 0):
		"""rect is in device coordinates"""
		if not add:
			self.Select(None)
		rect=self.ClientToCanvasRect(rect)
		objList = self._objects
		for obj in objList:
			if obj.intersects(rect):
				self.Select(obj,1)
				
	def Deselect(self, drawObj):
		for obj in self._selection:
			if obj==drawObj:
				self.InvalObj(drawObj)
				self._selection.remove(drawObj)
				break

	def CloneSelection(self):
		for ix in range(len(self._selection)):
			drawObj=self._selection[ix]
			drawObj.clone(drawObj._context)

	def InvalObj(self, drawObj):
		rect = Rect(drawObj._position.tuple())
		rect=self.CanvasToClientRect(rect);
		if self._active and self.IsSelected(drawObj):
			rect.left =rect.left-4;
			rect.top = rect.top-5;
			rect.right = rect.right+5;
			rect.bottom = rect.bottom+4;
		rect.inflateRect(1,1) 
		self.InvalidateRect(rect.tuple(),0)

	def Remove(self, drawObj):
		for obj in self._selection:
			if obj==drawObj:
				self._selection.remove(drawObj)
				break
	def IsSelected(self, drawObj):
		for obj in self._selection:
			if obj==drawObj:return 1
		return 0

	def onCancelEdit(self):
		"""
		The following command handler provides the standard keyboard
		user interface to cancel an in-place editing session.
		"""
		self.ReleaseCapture();

		drawTool = self.GetCurrentTool()
		if drawTool:
			drawTool.onCancel(self)
		self.currentToolType = TOOL_SELECT

	def onEditClear(self):
		# update all the wnds before the selection goes away
		self.UpdateObj(HINT_DELETE_SELECTION, self._selection)
		self.OnUpdate(None,HINT_UPDATE_SELECTION, None)

		# now remove the selection from the document
		for obj in self._selection:
			self.Remove(obj)
			del obj
		del self._selection
		self._selection=[]

	def OnInitialUpdate(self):
		self.currentToolType = TOOL_SELECT

	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam
		drawTool = self.GetCurrentTool()
		if drawTool:
			drawTool.onLButtonDown(flags, point)

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam
		drawTool = self.GetCurrentTool()
		if drawTool:
			drawTool.onLButtonUp(flags, point)

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam
		point_dp=self.ClientToCanvas(point)
		drawObj=self.ObjectAt(point_dp)
		if drawObj:
			s='rect: (%d,%d,%d,%d)' % drawObj._position.tuple()
			win32ui.MessageBox(s)
			return
		drawTool = self.GetCurrentTool()
		if drawTool:
			drawTool.onLButtonDblClk(flags, point);

	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point=Point(msg.pos());flags=msg._wParam
		drawTool = self.GetCurrentTool()
		if drawTool:
			drawTool.onMouseMove(flags, point)

	# Called when the activation changes
	def OnActivateView(self,activate,activeView,deactiveView):
		self._obj_.OnActivateView(activate,activeView,deactiveView)
		if self._active != activate:
			if activate:
				self._active = activate
		if	len(self._selection):
			self.OnUpdate(None, HINT_UPDATE_SELECTION, None);
		self._active = activate

	def onSize(self,params):
		pass

	# An optimized Drawing function while using the toolkit
	def DrawObjLayer(self, dc):
		# only paint the rect that needs repainting
		rect=self.CanvasToClientRect(Rect(dc.GetClipBox()))
		
		# draw to offscreen bitmap for fast looking repaints
		#dcc=win32ui.CreateDC()
		dcc=dc.CreateCompatibleDC()

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

		# show draw area
		if not self.InLayoutMode():
			l,t,w,h=self._canvas
			if self._bkimg<0:
				dcc.FillSolidRect((l,t,l+w,t+h),win32mu.RGB((0,0,0)))
				dcc.FillSolidRect(self._crect.tuple(),win32mu.RGB((200,200,0)))
				dcc.FillSolidRect(self._brect.tuple(),win32mu.RGB((255,255,255)))
				win32mu.FrameRect(dcc,self._crect.tuple(),(0,0,0))
				win32mu.FrameRect(dcc,self._brect.tuple(),(0,0,0))
			else:
				#ig = win32ui.Getig()
				import gear32sd
				ig = gear32sd
				img = self._bkimg
				ig.device_rect_set(img,(0,0,w,h))
				ig.display_desktop_pattern_set(img,0)
				ig.display_image(img,dcc.GetSafeHdc())

		# draw objects on dcc
		if self._active_displist:
			self._active_displist._render(dcc,rect.tuple())
		self.DrawObjectsOn(dcc)

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
	def UpdateObj(self, hint=None, hintObj=None):
		self.OnUpdate(sender, hint, hintObj)

	# draw support
	def ObjectAt(self, point):
		"""point is in logical coordinates"""
		rect=Rect((point.x,point.y,point.x+1,point.y+1))
		l=self._objects[:]
		l.reverse()
		for obj in l:
			if obj.intersects(rect):
				return obj
		return None

	def DrawObjectsOn(self, dc):
		for obj in self._objects:
			obj.draw(dc)
			if self.IsSelected(obj):
				obj.drawTracker(dc,DrawObj.selected)

	def Add(self, drawObj):
		self._objects.append(drawObj)

	def Remove(self, drawObj):
		for obj in self._objects:
			if obj==drawObj:	
				self._objects.remove(drawObj)
				break

	def DeleteContents(self):
		self._objects=[]

	def SetDrawObjDirty(self, f):
		self._drawObjIsDirty = f

	def IsDrawObjDirty(self):
		return self._drawObjIsDirty

	#############################
	# draw toolkit section
	def release(self):
		if self._hsmallfont:
			Sdk.DeleteObject(self._hsmallfont)
			self._hsmallfont = 0
		
	def SetCursor(self, cursor):
		if cursor!=Sdk.GetCursor():
			#Sdk.SetCursor(cursor)
			Sdk.SetClassLong(self.GetSafeHwnd(),win32con.GCL_HCURSOR,cursor)
			
	def SetCapture(self):
		self._capture=self

	def ReleaseCapture(self):
		self._capture=None

	def MouseCaptured(self):
		return (self._capture==self)

	def GetCurrentTool(self):
		return self.tool.get(self.currentToolType)

	def SelectTool(self, tool='select', units = 0):
		if tool=='select':
			self.currentToolType=TOOL_SELECT
		elif tool=='rect':
			self.currentToolType=TOOL_RECT
		else:
			self.currentToolType=TOOL_SELECT
		self.selectTool.setunits(units)
		self.rectTool.setunits(units)

	def LimitRects(self, num):
		self._limit_rect=num

	def OnNewRect(self):
		if hasattr(self,'_limit_rect'):
			if len(self._objects) >= self._limit_rect:
				self.currentToolType = TOOL_SELECT	
					
	def SetSmallFont(self, dc):
		if not self._hsmallfont:
			fd={'name':'Arial','height':10,'weight':700}
			self._hsmallfont = Sdk.CreateFontIndirect(fd)		
		self._hfont_org = dc.SelectObjectFromHandle(self._hsmallfont)

	def RestoreFont(self, dc):
		if self._hfont_org:
			dc.SelectObjectFromHandle(self._hfont_org)

	def SetRelCoordRef(self, wnd):
		self._ref_wnd = wnd
	
	######################

	# layout page support
	def SetLayoutMode(self, v):
		self._layoutmode = v

	def InLayoutMode(self):
		return self._layoutmode

	def	SetScale(self, scale):
		self._scale = scale

	def GetScale(self):
		if self.InLayoutMode():
			return None
		return self._scale

	def	SetBRect(self, rc):
		self._brect = Rect(rc)
	def	SetCRect(self, rc):
		self._crect = Rect(rc)
	def SetBkImg(self,img):
		self._bkimg = img

	def InDrawArea(self, point):
		if self.InLayoutMode():
			if point.x<0 or point.y<0:
				return 0
			else:
				return 1
		return self._brect.isPtInRectEq(point)

	def InDrawAreaRc(self, rc):
		if self.InLayoutMode():
			return 1
		return self._brect.isRectIn(rc)

	def SetUnits(self, units):
		self.selectTool.setunits(units)
		self.rectTool.setunits(units)
		objs=self._ref_wnd._objects
		if len(objs):objs[0].setunits(units)
		self._ref_wnd._rb_units=units

	def	RestoreState(self):
		self._scale=None
		self._layoutmode=1
		self._has_scale=0
		self._bkimg=-1


