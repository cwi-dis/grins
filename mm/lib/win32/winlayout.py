__version__ = "$Id$"

# std win32 modules
import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()


# selection modes
[SM_NONE, SM_MOVE, SM_SIZE, SM_NET] = range(4)

# select operation
[SO_REPLACE, SO_APPEND] = range(2)


# listeners should implement the interface
#class ListenerInterface:
# 	def onDSelChanged(self, selection): pass
# 	def onDSelMove(self, selection): pass
# 	def onDSelResize(self, selection): pass
#	def onDSelProperties(self, shape): pass

# shape factories should implement the interface
#class ShapeFactory:
#	def createObjectAt(self, point, strid): return None
#	def removeObject(self, obj): pass

class DrawContext:
	def __init__(self):
		self._moveRefPt = 0, 0
		self._selected = None
		self._selmode = SM_NONE
		self._ixDragHandle = 0
		self._capture = None
		self._listeners = []

		# for select, move and resize
		self._seltool = SelectTool(self)

		# new objects creation
		# we don't need this tool when
		# new objects creation is not allowed
		self._shapetool = ShapeTool(self)

		# set current tool
		self._curtool = self._seltool

		# DrawContext does not support multiple selections
		# use  MultiSelectDrawContext instead 
		self._muliselect = 0

		# and object responsible to create new shapes
		self._shapeFactory = None

	def reset(self):
		self._moveRefPt = 0, 0
		self._selected = None
		self._selmode = SM_NONE
		self._ixDragHandle = 0
		self._capture = None
		self._curtool = self._seltool
	
	def setCapture(self):
		self._capture = self

	def releaseCapture(self):
		self._capture = None

	def hasCapture(self):
		return self._capture

	def inSelectMode(self):
		return self._curtool == self._seltool

	def setcursor(self, strid):
		if strid=='arrow':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
		elif strid=='sizenwse':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_SIZENWSE)
		elif strid=='sizens':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_SIZENS)
		elif strid=='sizenesw':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_SIZENESW)
		elif strid=='sizewe':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_SIZEWE)
		elif strid=='cross':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_CROSS)
		else:
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
		Sdk.SetCursor(cursor)
			
	def getMouseTarget(self, point):
		return None
	
	def update(self, rc=None):
		pass
	
	# the entity registered through this method 
	# will receive update notifications 
	def addListener(self, entity):
		self._listeners.append(entity)

	#
	# update section
	#
	def moveSelectionTo(self, point):
		xp, yp = point
		xl, yl = self._moveRefPt
		if self._selected:
			self._selected.invalidateDragHandles()
			self._selected.moveBy((xp-xl, yp-yl))
			self._selected.invalidateDragHandles()
			for obj in self._listeners:
				obj.onDSelMove(self._selected)
	
	def moveSelectionHandleTo(self, point):
		if self._selected:
			self._selected.invalidateDragHandles()
			self._selected.moveDragHandleTo(self._ixDragHandle, point)
			self._selected.invalidateDragHandles()
			for obj in self._listeners:
				obj.onDSelResize(self._selected)

	def select(self, shape, mode=SO_REPLACE):
		if self._selected:
			self._selected.invalidateDragHandles()	
		self._selected = shape
		for obj in self._listeners:
			obj.onDSelChanged(self._selected)
	
	def showproperties(self):
		if self._selected:
			for obj in self._listeners:
				obj.onDSelProperties(self._selected)
	#
	# Mouse input
	#
	def onLButtonDown(self, flags, point):
		self._curtool.onLButtonDown(flags, point)

	def onLButtonUp(self, flags, point):
		self._curtool.onLButtonUp(flags, point)

	def onMouseMove(self, flags, point):
		self._curtool.onMouseMove(flags, point)
	
	def onLButtonDblClk(self, flags, point):
		self._curtool.onLButtonDblClk(flags, point)

	def onNCButton(self):
		self._moveRefPt = 0, 0
		self._selmode = SM_NONE
		self._ixDragHandle = 0
		self._capture = None

	# force selection
	def selectShape(self, shape):
		if self._selected:
			self._selected.invalidateDragHandles()
		self._selected = shape
		if self._selected:
			self._selected.invalidateDragHandles()

	#
	# Create new objects support
	# Do not implement if this support is not needed
	#
	def setShapeFactory(self, factory):
		self._shapeFactory = factory

	def createObject(self, strid=None):
		# create a new object
		# at self._downPt with zero dimensions
		newobj = None
		if self._shapeFactory:
			newobj = self._shapeFactory.createObjectAt(self._downPt, strid)
		self._curtool = self._seltool
		return newobj

	def removeObject(self, obj):
		# remove shape
		# used by shape tool to remove objects
		# with zero dimensions
		if self._shapeFactory:
			self._shapeFactory.removeObject(obj)


#########################	
# For multi-selections use MSDrawContext instead of DrawContext
# Its interface for its clients is the same as that of DrawContext
# It offers the same functionality plus multi selection

# A client/notification listener is now required to implement
#class ListenerInterface:
# 	def onDSelChanged(self, selections): pass
# 	def onDSelMove(self, selections): pass
# 	def onDSelResize(self, selection): pass
#	def onDSelProperties(self, selection): pass
# where selections is the list of selected objects

# You can set the selections by calling 
# MSDrawContext.selectShapes(self, shapeList)

debugMSDrawContext = 0

class MSDrawContext(DrawContext):
	def __init__(self):
		DrawContext.__init__(self)
		
		# class supports multi-select
		self._muliselect = 1

		# list of selected shapes 
		# base class self._selected 
		# now becomes either the last selected shape
		# or the shape with the focus
		self._selections = []

		self._downPt = 0, 0
		self._lastPt = 0, 0
		self._focusdrawn = 0
	
	# force selection
	def selectShapes(self, shapeList):
		for shape in self._selections:
			shape.invalidateDragHandles()
		self._selections = shapeList[:]
		n = len(shapeList)
		if n:
			self._selected = shapeList[n-1]
		else:
			self._selected = None
		for shape in self._selections:
			shape.invalidateDragHandles()

	# force a move by
	def moveSelectionBy(self, dx, dy):
		for shape in self._selections:
			shape.invalidateDragHandles()
			shape.moveBy((dx, dy))
			shape.invalidateDragHandles()
		if self._selections:
			for obj in self._listeners:
				obj.onDSelMove(self._selections)
		
	def select(self, shape, mode=SO_REPLACE):
		# if we don't support multisel then set
		if not self._muliselect:
			mode=SO_REPLACE

		if debugMSDrawContext:
			if shape:
				print 'select', shape.getwindowpos(), 'mode=', mode
			else:
				print 'select None'
			
		# remove selections if shape is None
		if not shape:
			self._selected = None
			if self._selections:
				for sh in self._selections:
					sh.invalidateDragHandles()
				self._selections = []
		else:
			# set last selected shape
			self._selected = shape 
			# update selections
			if mode==SO_REPLACE:
				if self._selections:
					for sh in self._selections:
						sh.invalidateDragHandles()
				self._selections = [shape,]
			elif mode==SO_APPEND:
				if shape not in self._selections:
					self._selections.append(shape)
				else:
					self._selections.remove(shape)
					n = len(self._selections)
					if n:
						self._selected = self._selections[n-1]
					else:
						self._selected = None
			# update shape drag handles was either added or removed
			shape.invalidateDragHandles()
		for obj in self._listeners:
			obj.onDSelChanged(self._selections)
	
	def moveSelectionTo(self, point):
		xp, yp = point
		xl, yl = self._moveRefPt
		# Shapes in selections may have a parent child relationship.
		# If its so, remove from selection list those that
		# their movement will occur indirectly by an ancestor movement 
		selections = self._selections[:]
		for shape in selections[:]:
			L = shape.getAncestors()
			for ancshape in L:
				if ancshape in selections:
					selections.remove(shape)
					break
		for shape in selections:
			shape.invalidateDragHandles()
			shape.moveBy((xp-xl, yp-yl))
			shape.invalidateDragHandles()
		for obj in self._listeners:
			obj.onDSelMove(selections)

	def moveSelectionHandleTo(self, point):
		if self._selected:
			self._selected.invalidateDragHandles()
			self._selected.moveDragHandleTo(self._ixDragHandle, point)
			self._selected.invalidateDragHandles()
			for obj in self._listeners:
				obj.onDSelResize(self._selected)

	def reset(self):
		DrawContext.reset(self)
		self._selections = []

	def onNCButton(self):
		DrawContext.onNCButton(self)
		self._selections = []

	#
	# Multi-select support
	# Do not implement if this support is not needed
	#
	def drawFocusRect(self, rc):
		pass

	def selectWithinRect(self, rc):
		pass

	def drawFocus(self, pt1, pt2):
		self.drawFocusRect(self.__rectFromPoints(pt1, pt2))
				
	def selectWithin(self, pt1, pt2):
		self._selected = self.selectWithinRect(self.__rectFromPoints(pt1, pt2))

	def __rectFromPoints(self, pt1, pt2):
		x1, y1 = pt1
		x2, y2 = pt2
		if x1<=x2: 
			l = x1
			r = x2
		else:
			l = x2
			r = x1
		if y1<=y2: 
			t = y1
			b = y2
		else:
			t = y2
			b = y1
		return l, t, r-l, b-t

#########################
# interface of acceptable objects			
class Shape:
	def getDragHandle(self, ix):
		return 3, 3

	def getDragHandleRect(self, ix):
		return 0, 0, 6, 6

	def getDragHandleCount(self):
		return 8

	def getDragHandleCursor(self, ix):
		return 'arrow'

	def getDragHandleAt(self, point):
		return 0

	def moveDragHandleTo(self, ixHandle, point):
		pass

	def moveBy(self, delta):
		pass

	def inside(self, point):
		return 0
	
	def invalidateDragHandles(self):
		pass
	
	def isResizeable(self):
		return 1

	def getAncestors(self):
		return []

# base class for all drawing tools										
class DrawTool:
	def __init__(self, ctx):
		self._ctx = ctx

	def onLButtonDown(self, flags, point):
		ctx = self._ctx
		ctx._downPt = point
		ctx._lastPt = point
		ctx.setCapture()

	def onLButtonUp(self, flags, point):
		ctx = self._ctx
		ctx.releaseCapture()
		if point == ctx._downPt:
			ctx._curtool = ctx._seltool

	def onMouseMove(self, flags, point):
		ctx = self._ctx
		ctx._lastPt = point
		ctx.setcursor('arrow')
	
	def onLButtonDblClk(self, flags, point):
		pass


# the selection tool										
class SelectTool(DrawTool):
	def __init__(self, ctx):
		DrawTool.__init__(self, ctx)

	def onLButtonDown(self, flags, point):
		ctx = self._ctx
		ctx._selmode = SM_NONE
		canResize = not ctx._muliselect or len(ctx._selections)==1
		isAppend = ctx._muliselect and (flags & win32con.MK_CONTROL)
				 
		# if the click is within a drag handle enter SIZE mode and change cursor
		shape = ctx._selected
		if shape and canResize:
			ctx._ixDragHandle = shape.getDragHandleAt(point)
			if ctx._ixDragHandle and shape.isResizeable():
				ctx._selmode = SM_SIZE
				ctx.setcursor(shape.getDragHandleCursor(ctx._ixDragHandle))
		
		# if the click is within a shape select it and enter MOVE mode
		if ctx._selmode == SM_NONE:
			shape = ctx.getMouseTarget(point)
			if shape:
				if isAppend:
					ctx.select(shape, mode=SO_APPEND)
					ctx._selmode = SM_MOVE
				else:
					if ctx._muliselect and shape in ctx._selections:
						ctx._selmode = SM_MOVE
					else:
						ctx.select(shape)
						ctx._selmode = SM_MOVE

		# if the click is on the background remove selection
		if ctx._selmode == SM_NONE and not isAppend:
			ctx.select(None)
			ctx.update()
			if ctx._muliselect:
				ctx._selmode = SM_NET

		ctx._moveRefPt = point
		DrawTool.onLButtonDown(self, flags, point)
	
	def onLButtonUp(self, flags, point):
		ctx = self._ctx
		if ctx.hasCapture():
			if ctx._selmode == SM_NET:
				if ctx._focusdrawn:
					ctx.drawFocus(ctx._downPt, ctx._lastPt)
					ctx._focusdrawn = 0
				ctx.selectWithin(ctx._downPt, ctx._lastPt)
			elif ctx._selmode != SM_NONE:
				ctx.update()
		DrawTool.onLButtonUp(self, flags, point)

	def onMouseMove(self, flags, point):
		ctx = self._ctx
		shape = ctx._selected

		if not ctx.hasCapture():
			if shape and ctx.inSelectMode():
				ctx._ixDragHandle = shape.getDragHandleAt(point)
				if ctx._ixDragHandle and shape.isResizeable():
					ctx.setcursor(shape.getDragHandleCursor(ctx._ixDragHandle))
					return
			if ctx.inSelectMode():
				DrawTool.onMouseMove(self, flags, point)
			return
		
		# nulti-select if enabled
		if ctx._selmode == SM_NET:
			if ctx._focusdrawn:
				ctx.drawFocus(ctx._downPt, ctx._lastPt)
			ctx.drawFocus(ctx._downPt, point)
			ctx._focusdrawn = 1
			DrawTool.onMouseMove(self, flags, point)
			return
		
		# move selected
		if shape or (ctx._muliselect and ctx._selections):		
			if ctx._selmode == SM_MOVE:
				ctx.moveSelectionTo(point)
			elif ctx._ixDragHandle:
				ctx.moveSelectionHandleTo(point)

		ctx._moveRefPt = point

		if ctx._selmode == SM_SIZE and ctx.inSelectMode():
			ctx._lastPt = point
			if shape.isResizeable():
				ctx.setcursor(shape.getDragHandleCursor(ctx._ixDragHandle))
			return

		ctx._lastPt = point
		DrawTool.onMouseMove(self, flags, point)

	def onLButtonDblClk(self, flags, point):
		if self._ctx._selected:
			self._ctx.showproperties()


# Tool to create new shapes
class ShapeTool(DrawTool):
	def __init__(self, ctx):
		DrawTool.__init__(self, ctx)

	def onLButtonDown(self, flags, point):
		DrawTool.onLButtonDown(self, flags, point)
		ctx = self._ctx
		ctx._selected = ctx.createObject()
		ctx._selmode = SM_SIZE
		ctx._moveRefPt = point

	def onLButtonUp(self, flags, point):
		ctx = self._ctx
		if point==ctx._downPt:
			if ctx._selected:
				ctx.removeObject(ctx._selected)
				ctx._selected = None
			ctx._seltool.onLButtonDown(self, flags, point)
		ctx._seltool.onLButtonDown(self, flags, point)

	def onMouseMove(self, flags, point):
		ctx = self._ctx
		ctx.setcursor('cross')


################################

# std mfc windows stuf
from pywinlib.mfc import window, docview

import win32mu

class LayoutWndContext:
	def __init__(self, base):
		self._drawContextBase = base
		self._bgcolor = None
		self._canvas = None

		self._device2logical = 1
		self._autoscale = 0

		fd = {'name':'Arial','height':10,'weight':700}
		self._hsmallfont = Sdk.CreateFontIndirect(fd)		
			
	def setAutoScale(self, autoscale):
		self._autoscale = autoscale
	
	def setCanvasSize(self, w, h):
		if self._cancroll:
			x1, y1, w1, h1 = self._canvas
			self._canvas = x1, y1, w, h
			self.SetScrollSizes(win32con.MM_TEXT,self._canvas[2:])

	def setDeviceToLogicalScale(self, device2logical):
		self._device2logical = device2logical

	def createWindow(self, parent, rc, bgcolor, canvas=None):
		self._parent = parent
		self._rectb = rc
		self._bgcolor = bgcolor
		self._rect = 0, 0, rc[2], rc[3]
		self._canvas = canvas

		if not self._cancroll:
			if canvas is None:
				self._canvas = self._rect
			self.OnPaint = self._OnPaint
			brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(bgcolor),0)
			cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
			icon=0
			clstyle=win32con.CS_DBLCLKS
			style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS
			exstyle = 0
			title = ''
			strclass=Afx.RegisterWndClass(clstyle, cursor, brush, icon)
			self.CreateWindowEx(exstyle,strclass, title, style,
				(rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3]),parent,0)
			self.ShowWindow(win32con.SW_SHOW)
			self.UpdateWindow()
		else:
			if canvas is None:
				self._canvas = 0, 0, 1280, 1024
			self.CreateWindow(parent)
			self.SetWindowPos(self.GetSafeHwnd(),rc,
				win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
			self.SetScrollSizes(win32con.MM_TEXT,self._canvas[2:])
			self.ShowWindow(win32con.SW_SHOW)
			self.UpdateWindow()		
	
	def OnCreate(self, params):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		self.HookMessage(self.onLButtonDblClk,win32con.WM_LBUTTONDBLCLK)
		self.HookMessage(self.onKeyDown, win32con.WM_KEYDOWN)
		
	def onKeyDown(self, params):
		key = params[2]
		dx, dy = 0, 0
		if key == win32con.VK_DOWN: dy = 1 
		elif key == win32con.VK_UP: dy = -1
		elif key == win32con.VK_RIGHT: dx = 1
		elif key == win32con.VK_LEFT: dx = -1
		if dx or dy:
			self._drawContextBase.moveSelectionBy(self, dx, dy)
		return 1
	
	def OnDestroy(self, params):
		if self._hsmallfont:
			Sdk.DeleteObject(self._hsmallfont)

	#
	#  MSDrawContext listener interface
	#
	def onDSelChanged(self, selection):
		pass

	def onDSelMove(self, selection):
		pass
			
	def onDSelResize(self, selection):
		pass

	def onDSelProperties(self, selection): 
		pass
	
	def getMouseTarget(self, point):
		return None

	#
	# Mouse response
	#
	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLSP(point)
		self._drawContextBase.onLButtonDown(self, flags, point)

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLSP(point)
		self._drawContextBase.onLButtonUp(self, flags, point)
	
	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLSP(point)
		self._drawContextBase.onMouseMove(self, flags, point)

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		point = self.DPtoLSP(point)
		self._drawContextBase.onLButtonDblClk(self, flags, point)

	def onNCLButton(self, params):
		self._drawContextBase.onNCButton(self)

	#
	# Painting
	#
	def _OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		
		hf = dc.SelectObjectFromHandle(self._hsmallfont)
		dc.SetBkMode(win32con.TRANSPARENT)

		self.OffscreenPaintOn(dc)
		
		dc.SelectObjectFromHandle(hf)
		
		# paint frame decoration
		if not self._cancroll: 
			br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
			dc.FrameRectFromHandle(self.GetClientRect(),br)
			Sdk.DeleteObject(br)

		self.EndPaint(paintStruct)

	def OnDraw(self, dc):
		hf = dc.SelectObjectFromHandle(self._hsmallfont)
		dc.SetBkMode(win32con.TRANSPARENT)
		self.OffscreenPaintOn(dc)
		dc.SelectObjectFromHandle(hf)
	
	def getClipRgn(self, rel=None):
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn(self._canvas)
		return rgn

	def OnEraseBkgnd(self,dc):
		return 1
	
	# called by OnDraw or OnPaint
	def OffscreenPaintOn(self, dc):
		l, t, w, h = self._canvas
		r, b = l+w, t+h

		# draw to offscreen bitmap for fast looking repaints
		dcc = dc.CreateCompatibleDC()

		bmp = win32ui.CreateBitmap()
		bmp.CreateCompatibleBitmap(dc, w, h)
		
		# called by win32ui
		#self.OnPrepareDC(dcc)
		
		# offset origin more because bitmap is just piece of the whole drawing
		dcc.OffsetViewportOrg((-l, -t))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.SetBrushOrg((l % 8, t % 8))
		dcc.IntersectClipRect((l, t, r, b))

		# draw objects on dcc
		self.paintOn(dcc)

		# copy bitmap
		dcc.SetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		dcc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt((l,t),(w, h),dcc,(0, 0), win32con.SRCCOPY)

		# clean up
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC()
		del bmp

	def paintOn(self, dc):
		l, t, w, h = self._canvas
		r, b = l+w, t+h
		dc.FillSolidRect((l, t, r, b),win32mu.RGB(self._bgcolor or (255,255,255)))

	#
	# Scaling/scrolling support
	#
	def DPtoSP(self, pt):
		# scaling
		x, y = pt
		sc = self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5)

	def DRtoSR(self, rc):
		x, y = self.DPtoSP(rc[:2])
		w, h = self.DPtoSP(rc[2:])
		return x, y, w, h


	def DPtoLP(self, pt):
		if not self._cancroll: 
			return pt
		dc=self.GetDC()
		pt = dc.DPtoLP(pt)
		self.ReleaseDC(dc)
		return pt

	def DRtoLR(self, rc):
		x, y = self.DPtoLP(rc[:2])
		w, h = self.DPtoLP(rc[2:])
		return x, y, w, h


	def SPtoDP(self, pt):
		x, y = pt
		sc = 1.0/self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5)

	def SRtoDR(self, rc):
		x, y = self.SPtoDP(rc[:2])
		w, h = self.SPtoDP(rc[2:])
		return x, y, w, h


	def LPtoDP(self, pt):
		if not self._cancroll: 
			return pt
		dc=self.GetDC()
		pt = dc.LPtoDP(pt)
		self.ReleaseDC(dc)
		return pt

	def LRtoDR(self, rc):
		x, y = self.LPtoDP(rc[:2])
		w, h = self.LPtoDP(rc[2:])
		return x, y, w, h

	def DPtoLSP(self, pt):
		return self.DPtoLP(self.DPtoSP(pt))

	def LSPtoDP(self, pt):
		return self.LPtoDP(self.SPtoDP(pt))
							
#########################
# Final concrete classes 

class LayoutOsWnd(window.Wnd, LayoutWndContext, DrawContext):
	def __init__(self):
		window.Wnd.__init__(self, win32ui.CreateWnd())
		DrawContext.__init__(self)
		LayoutWndContext.__init__(self, DrawContext)

		DrawContext.addListener(self, self) 
		self._cancroll = 0

class LayoutScrollOsWnd(docview.ScrollView, LayoutWndContext, DrawContext):
	def __init__(self):
		doc = docview.Document(docview.DocTemplate())
		docview.ScrollView.__init__(self, doc)
		DrawContext.__init__(self)
		LayoutWndContext.__init__(self, DrawContext)

		DrawContext.addListener(self, self) 
		self._cancroll = 1

class MSLayoutScrollOsWnd(docview.ScrollView, LayoutWndContext, MSDrawContext):
	def __init__(self):
		doc = docview.Document(docview.DocTemplate())
		docview.ScrollView.__init__(self, doc)
		MSDrawContext.__init__(self)
		LayoutWndContext.__init__(self, MSDrawContext)

		MSDrawContext.addListener(self, self) 
		self._cancroll = 1




