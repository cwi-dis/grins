__version__ = "$Id$"

# std win32 modules
import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

import win32window

from appcon import *

import math

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
# 	def onDSelMoved(self, selection): pass
# 	def onDSelResized(self, selection): pass

# shape containers should implement the interface
#class ShapeContainer:
#	def getMouseTarget(self, point): pass
#	def update(self, rc=None): pass
#   def setcursor(self, strid): pass

# shape factories should implement the interface
#class ShapeFactory:
#	def canCreateObjectAt(self, point, strid): return 0
#	def newObjectAt(self, point, strid): return None
#	def removeObject(self, obj): pass
#	def onNewObject(self, obj): pass

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

		#
		self._poschanged = 0
		self._sizechanged = 0
		self._creatingnew = 0

		# DrawContext does not support multiple selections
		# use  MSDrawContext instead 
		self._muliselect = 0

		#
		self._shapeContainer = None

		# an object responsible to create new shapes
		self._shapeFactory = None

	def setCapture(self):
		self._capture = self

	def releaseCapture(self):
		self._capture = None

	def hasCapture(self):
		return self._capture

	def inSelectMode(self):
		return self._curtool == self._seltool

	#
	#   shape container links
	#
	# forward target lookup to shapeContainer	
	def getMouseTarget(self, point):
		if self._shapeContainer:
			return self._shapeContainer.getMouseTarget(point)
		return None
	
	# forward area update to shapeContainer	
	def update(self, rc=None):
		if self._shapeContainer:
			return self._shapeContainer.update(rc)
	
	def setcursor(self, strid):
		if self._shapeContainer:
			self._shapeContainer.setcursor(strid)
		else:
			cursor = win32window.getcursorhandle(strid)
			Sdk.SetCursor(cursor)

	# the entity registered through this method 
	# will be asked for the mouse target 
	def setShapeContainer(self, entity):
		self._shapeContainer = entity

	#
	# update section
	# these methods are called by drawing tools
	# they manipulate shapes and notify listeners
	#

	# client registration
	# the entity registered through this method 
	# will receive update notifications 
	def addListener(self, entity):
		self._listeners.append(entity)

	def removeListener(self, entity):
		for ind in range(len(self._listeners)):
			if self._listeners[ind] is entity:
				del self._listeners[ind]
				break
			
	def moveSelectionTo(self, point):
		xp, yp = point
		xl, yl = self._moveRefPt
		dx, dy = xp-xl, yp-yl
		if dx!=0 or dy!=0 and self._selected:
			self._poschanged = 1
			self._selected.invalidateDragHandles()
			self._selected.moveBy((dx, dy))
			self._selected.invalidateDragHandles()
			for obj in self._listeners:
				obj.onDSelMove(self._selected)
	
	def moveSelectionHandleTo(self, point):
		if self._selected:
			self._sizechanged = 1
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

	def checkChanged(self):
		if self._sizechanged:
			for obj in self._listeners:
				obj.onDSelResized(self._selected)
		self._sizechanged = 0
		
		if self._poschanged:
			for obj in self._listeners:
				obj.onDSelMoved(self._selected)
		self._poschanged = 0

	#
	# Mouse input
	#
	def onLButtonDown(self, flags, point):
		if self._curtool:
			self._curtool.onLButtonDown(flags, point)

	def onLButtonUp(self, flags, point):
		if self._curtool:
			self._curtool.onLButtonUp(flags, point)

	def onMouseMove(self, flags, point):
		if self._curtool:
			self._curtool.onMouseMove(flags, point)
	
	def onLButtonDblClk(self, flags, point):
		if self._curtool:
			self._curtool.onLButtonDblClk(flags, point)

	# non client area hit
	def onNCButton(self):
		self._moveRefPt = 0, 0
		self._selmode = SM_NONE
		self._ixDragHandle = 0
		self._capture = None

	#
	#   Direct manipulation by clients
	#

	# force selection
	def selectShape(self, shape):
		if self._selected:
			self._selected.invalidateDragHandles()
		self._selected = shape
		if self._selected:
			self._selected.invalidateDragHandles()

	# force a move by
	def moveSelectionBy(self, dx, dy, notify=1):
		if self._selected:
			shape = self._selected
			shape.invalidateDragHandles()
			shape.moveBy((dx, dy))
			shape.invalidateDragHandles()
			if notify:
				for obj in self._listeners:
					obj.onDSelMove(self._selected)
					obj.onDSelMoved(self._selected)

	def reset(self):
		self._moveRefPt = 0, 0
		self._selected = None
		self._selmode = SM_NONE
		self._ixDragHandle = 0
		self._capture = None
		self._curtool = self._seltool
		self._poschanged = 0
		self._sizechanged = 0
		self._creatingnew = 0

	def selectTool(self, strid):
		if strid=='shape':
			self._curtool = self._shapetool
		elif strid=='select':
			self._curtool = self._seltool
		else:
			self._curtool = self._seltool

	#
	# Create new objects support
	#
	def setShapeFactory(self, factory):
		self._shapeFactory = factory

	def canCreateObjectAt(self, point, strid=None):
		if self._shapeFactory:
			return self._shapeFactory.canCreateObjectAt(point, strid)
		return 0

	def createObject(self, strid=None):
		# create a new object
		# at self._downPt with zero dimensions
		newobj = None
		if self._shapeFactory:
			newobj = self._shapeFactory.newObjectAt(self._downPt, strid)
		return newobj

	def removeObject(self, obj):
		# remove shape
		# used by shape tool to remove objects
		# with zero dimensions
		if self._shapeFactory:
			self._shapeFactory.removeObject(obj)
		assert obj == self._selected, 'target object not selected'
		self._selected = None

	def onNewObject(self, obj):
		self._curtool = self._seltool
		assert obj == self._selected, 'new object not selected'
		if self._shapeFactory:
			self._shapeFactory.onNewObject(obj)

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
# 	def onDSelMoved(self, selections): pass
# 	def onDSelResized(self, selection): pass
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
	
	#
	#   Direct manipulation by clients
	#

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
	def moveSelectionBy(self, dx, dy, notify=1):
		for shape in self._selections:
			shape.invalidateDragHandles()
			shape.moveBy((dx, dy))
			shape.invalidateDragHandles()
		if self._selections and notify:
			for obj in self._listeners:
				obj.onDSelMove(self._selections)
				obj.onDSelMoved(self._selections)

	def reset(self):
		DrawContext.reset(self)
		self._selections = []
		
	#
	# update section (overrides)
	# these methods are called by drawing tools
	# they manipulate shapes and notify listeners
	#

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
		dx, dy = xp-xl, yp-yl
		if dx==0 and dy==0:
			return
		self._poschanged = 1
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
			self._sizechanged = 1
			self._selected.invalidateDragHandles()
			self._selected.moveDragHandleTo(self._ixDragHandle, point)
			self._selected.invalidateDragHandles()
			for obj in self._listeners:
				obj.onDSelResize(self._selected)

	def checkChanged(self):
		if self._sizechanged:
			for obj in self._listeners:
				obj.onDSelResized(self._selected)
		self._sizechanged = 0
		
		if self._poschanged:
			for obj in self._listeners:
				obj.onDSelMoved(self._selections)
		self._poschanged = 0
		
	#
	# Mouse input (override)
	#
	def onNCButton(self):
		DrawContext.onNCButton(self)
		self._selections = []

	#	
	#  Net-multi-select mechanism 
	#  (select all objects that have intersection with the user drawn net rect)
	#  Do not implement if this support is not needed
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
# interface of shapes this framework can create/manipulate			

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
		return -1

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
		ctx._isdirty = 0
		canResize = not ctx._muliselect or len(ctx._selections)==1
		isAppend = ctx._muliselect and (flags & win32con.MK_CONTROL)
				 
		# if the click is within a drag handle enter SIZE mode and change cursor
		shape = ctx._selected
		if shape and canResize:
			ctx._ixDragHandle = shape.getDragHandleAt(point)
			if ctx._ixDragHandle>0 and shape.isResizeable():
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
		ctx.checkChanged()
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
				if ctx._ixDragHandle>0 and shape.isResizeable():
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

		if ctx._selmode == SM_SIZE: # and ctx.inSelectMode():
			ctx._lastPt = point
			if shape.isResizeable():
				ctx.setcursor(shape.getDragHandleCursor(ctx._ixDragHandle))
			return

		ctx._lastPt = point
		DrawTool.onMouseMove(self, flags, point)

	def onLButtonDblClk(self, flags, point):
		if self._ctx._selected:
			self._ctx.showproperties()


# base class for shape creation tools
# its concrete and ready to be used for any one-kind shapes
class ShapeTool(DrawTool):
	def __init__(self, ctx):
		DrawTool.__init__(self, ctx)

	def onLButtonDown(self, flags, point):
		ctx = self._ctx
		if ctx.canCreateObjectAt(point):
			ctx._creatingnew = 1
			DrawTool.onLButtonDown(self, flags, point)
			ctx._selected = ctx.createObject()
			ctx._selmode = SM_SIZE
			ctx._moveRefPt = point

	def onLButtonUp(self, flags, point):
		ctx = self._ctx
		if not ctx._creatingnew:
			return
		if point == ctx._downPt:
			if ctx._selected:
				ctx.removeObject(ctx._selected)
				ctx._selected = None
				ctx.setcursor('cross')
				return
		ctx._seltool.onLButtonUp(flags, point)
		if ctx._selected:
			ctx.onNewObject(ctx._selected)
			ctx._creatingnew = 0

	def onMouseMove(self, flags, point):
		ctx = self._ctx
		if ctx.canCreateObjectAt(point):
			if not ctx._selected:
				ctx.setcursor('cross')
			else:
				ctx._seltool.onMouseMove(flags, point)


class Polyline:
	def __init__(self, wnd, points):
		self._wnd = wnd
		self._points = points
		self._device2logical = 1.0

	def getDevicePoints(self):
		x0, y0 = self._wnd.getwindowpos()[:2]
		points = []
		for pt in self._points:
			points.append(self.LPtoDP((x0 + pt[0], y0+pt[1]), round=1))
		return points

	# insert point nearest to pt (pt in device coordinates)
	def insertPoint(self, pt):
		projpt, index = self.projection(pt)
		x0, y0 = self._wnd.getwindowpos()[:2]
		if projpt is not None:
			projpt = self.DPtoLP(projpt)
			x, y = projpt
			self._points.insert(index, (x - x0, y - y0))
			self.update()
			d1 = self.__dist(index-1, index)
			d2 = self.__dist(index-1, index+1)
			prop = d1/d2
			return index, prop
		return -1, 0

	def __dist(self, ix1, ix2):
		x1, y1 = self._points[ix1]
		x2, y2 = self._points[ix2]
		dx = x2-x1
		dy = y2-y1
		return math.sqrt(dx*dx+dy*dy)
	#
	# Scaling support
	#
	def setDeviceToLogicalScale(self, d2lscale):
		if d2lscale<=0: d2lscale = 1.0
		self._device2logical = d2lscale

	def getDeviceToLogicalScale(self):
		return self._device2logical

	def DPtoLP(self, pt):
		x, y = pt
		sc = self._device2logical
		return sc*x, sc*y

	def DRtoLR(self, rc):
		x, y, w, h = rc
		sc = self._device2logical
		return sc*x, sc*y, sc*w, sc*h

	def LPtoDP(self, pt, round=0):
		x, y = pt
		sc = 1.0/self._device2logical
		if round:
			return int(sc*x+0.5), int(sc*y+0.5)
		return sc*x, sc*y

	def LRtoDR(self, rc, round=0):
		x, y, w, h = rc
		sc = 1.0/self._device2logical
		if round:
			return int(sc*x+0.5), int(sc*y+0.5), int(sc*w+0.5), int(sc*h+0.5)
		return sc*x, sc*y, sc*w, sc*h

	def LDtoDD(self, d):
		return d/self._device2logical

	def DDtoLD(self, d):
		return d*self._device2logical

	#
	# Drag & Resize interface
	#
	# return drag handle position in device coordinates
	def getDragHandle(self, ix):
		x0, y0 = self._wnd.getwindowpos()[:2]
		x, y = self._points[ix-1]
		return self.LPtoDP((x0+x,y0+y))

	# return drag handle rectangle in device coordinates
	def getDragHandleRect(self, ix):
		x0, y0 = self._wnd.getwindowpos()[:2]
		x, y = self._points[ix-1]
		x, y = self.LPtoDP((x0+x,y0+y))
		return x-3, y-3, 7, 7

	def getDragHandleCount(self):
		return len(self._points)

	def getDragHandleCursor(self, ix):
		return 'arrow'

	# return drag handle at device coordinates
	def getDragHandleAt(self, point):
		xp, yp = point
		for ix in range(1, len(self._points)+1):
			x, y, w, h = self.getDragHandleRect(ix)
			l, t, r, b = x, y, x+w, y+h
			if xp>=l and xp<r and yp>=t and yp<b:
				return ix
		return -1

	# move drag handle in device coordinates to point in device coordinates
	def moveDragHandleTo(self, ixHandle, point):
		x0, y0 = self._wnd.getwindowpos()[:2]
		xp, yp = self.DPtoLP(point)
		self._points[ixHandle-1] = xp - x0, yp - y0
		self.update()

	def moveBy(self, delta):
		dx, dy = self.DPtoLP(delta)
		points = []
		for pt in self._points:
			points.append((dx + pt[0], dy+pt[1]))
		self._points = points
		self.update()
		
	def invalidateDragHandles(self):
		self.update()

	def isResizeable(self):
		return 1
	
	def update(self):
		self._wnd.update()

	def getAncestors(self):
		return []

	#
	# metrics
	#

	# line through (x1,y1) and (x2,y2)
	# Ax+By+C=0 where A=y2-y1, B=-(x2-x1), C=y1*(x2-x1)-x1*(y2-y1)
	# distance of (x0, y0): 
	# d = (Ax0+By0+C)/sqrt(A*A+B*B)
	def distanceFromLineSegment(self, x0, y0, x1, y1, x2, y2):
		# degenerate line: return dist
		if x1 == x2 and y1 == y2:
			dx = x1 - x0
			dy = y1 - y0
			return math.sqrt(dx*dx+dy*dy), None

		# find parameter t of projection
		x12 = x2-x1
		y12 = y2-y1
		if y1==y2:
			t = (x0-x1)/ float(x2-x1)
		elif x1==x2:
			t = (y0-y1)/ float(y2-y1)
		else:
			t = ((x0-x1)*x12+(y0-y1)*y12)/float(x12*x12 + y12*y12)

		if	t>=0 and t<=1.0:
			# projection within seqment
			A = y12
			B = -x12
			C = y1*x12-x1*y12
			return math.fabs(A*x0+B*y0+C)/math.sqrt(A*A+B*B), t
		elif t<0.0:
			# projection before
			dx = x1-x0
			dy = y1-y0
			return math.sqrt(dx*dx+dy*dy), None
		else: #if(t>1.0)
			# projection after
			dx = x2-x0
			dy = y2-y0
			return math.sqrt(dx*dx+dy*dy), None
		 
	# point in device coordinates
	def inside(self, point, dist=4):
		x0, y0 = self.LPtoDP(point)
		points = self.getDevicePoints()
		n = len(points)
		d = 100000.0
		for i in range(1,n):
			x1, y1 = points[i-1]
			x2, y2 = points[i]
			dp, t = self.distanceFromLineSegment(x0, y0, x1, y1, x2, y2)
			d = min(d, dp)
		return d<=dist

	# point in device coordinates
	def projection(self, point, dist=4):
		x0, y0 = self.LPtoDP(point)
		points = self.getDevicePoints()
		n = len(points)
		d = 100000.0
		projpt = None
		index = -1
		for i in range(1,n):
			x1, y1 = points[i-1]
			x2, y2 = points[i]
			dp, t = self.distanceFromLineSegment(x0, y0, x1, y1, x2, y2)
			if t is not None and dp<d:
				d = dp
				projpt = x1 + t*(x2-x1), y1+t*(y2-y1)
				index = i
		if projpt is not None and d<=dist:
			return 	projpt, index
		return None, -1

################################

# std mfc windows stuf
from pywinlib.mfc import window, docview

import win32mu

class LayoutWnd:
	def __init__(self, drawContext):
		self._drawContext = drawContext
		self._bgcolor = None
		self._canvas = None

		self._device2logical = 1
		self._autoscale = 0
		self._cancroll = 0

		self._curcursor = 'arrow'

		fd = {'name':'Arial','height':10,'weight':700}
		self._hsmallfont = Sdk.CreateFontIndirect(fd)
				
		self._tipwnd = None
		self._lbuttondown = None
		self._lbuttondblclk = None
					
	def setAutoScale(self, autoscale):
		self._autoscale = autoscale
	
	def selectTool(self, strid):
		self._drawContext.selectTool(strid)

	def setCanvasSize(self, w, h):
		if self._cancroll:
			x1, y1, w1, h1 = self._canvas
			self._canvas = x1, y1, w, h
			self.SetScrollSizes(win32con.MM_TEXT, self._canvas[2:])

	def updateCanvasSize(self):
		self._canvas = 0, 0, int(1600/self._device2logical+0.5), int(1200/self._device2logical+0.5)
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
				self._canvas = 0, 0, 1600, 1200
			self.CreateWindow(parent)
			self.SetWindowPos(self.GetSafeHwnd(),rc,
				win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
			self.SetScrollSizes(win32con.MM_TEXT,self._canvas[2:])
			self.ShowWindow(win32con.SW_SHOW)
			self.UpdateWindow()		
	
	def createTipWindow(self):
		from components import TipWindow
		self._tipwnd = TipWindow(self)
		self._tipwnd.create()
		self._lbuttondown = None

	def OnCreate(self, params):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)
		self.HookMessage(self.onLButtonDblClk,win32con.WM_LBUTTONDBLCLK)
		
	def onKeyDown(self, params):
		key = params[2]
		dx, dy = 0, 0
		if key == win32con.VK_DOWN: dy = 1 
		elif key == win32con.VK_UP: dy = -1
		elif key == win32con.VK_RIGHT: dx = 1
		elif key == win32con.VK_LEFT: dx = -1
		elif key == win32con.VK_DELETE:
			parent = self.GetParent()
			if hasattr(parent, 'OnDelete'):
				parent.OnDelete()
		else:
			# continue normal processing
			return 1
		if dx or dy:
			# ensure that there will be at least one shift in the natural coordinate system
			# it's important when the zoom value is high
			minDx, minDy = self.NPtoLP((1,1))
			if dx and abs(dx) < minDx:
				if dx < 0:
					dx = -minDx
				else:
					dx = minDx
			if dy and abs(dy) < minDy:
				if dy < 0:
					dy = -minDy
				else:
					dy = minDy
			
			self._drawContext.moveSelectionBy(dx, dy)
		# absorb event
		return 0
	
	def OnDestroy(self, params):
		if self._hsmallfont:
			Sdk.DeleteObject(self._hsmallfont)
			self._hsmallfont = 0
		if self._tipwnd:
			self._tipwnd.DestroyWindow()
			self._tipwnd = None
	#
	#  DrawContext listener interface
	#
	def onDSelChanged(self, selection):
		pass

	def onDSelMove(self, selection):
		if self._lbuttondown is not None and self._tipwnd:
			sel = None
			argtype = type(selection)
			if argtype == type([1,]) or argtype == type((1,)):
				if len(selection)==1:
					sel = selection[0]
			else:
				sel = selection
			if sel:
				x, y, w, h = sel._rectb
				xs, ys = self.ClientToScreen(self._lbuttondown)
				self._tipwnd.moveTo((xs+8, ys), '%d, %d, %d, %d' % (x, y, w, h))
			
	def onDSelResize(self, selection):
		if self._lbuttondown is not None and self._tipwnd:
			x, y, w, h = selection._rectb
			xs, ys = self.ClientToScreen(self._lbuttondown)
			self._tipwnd.moveTo((xs+8, ys), '%d, %d, %d, %d' % (x, y, w, h))

	def onDSelMoved(self, selection):
		pass
			
	def onDSelResized(self, selection):
		pass

	def onDSelProperties(self, selection): 
		pass
	
	def getMouseTarget(self, point):
		return None

	#
	#  ShapeFactory interface implementation
	#	
	def newObjectAt(self, point, strid):
		return None

	def removeObject(self, obj):
		pass

	def onNewObject(self, obj):
		pass
	
	#
	#  ShapeContainer interface implementation
	#	
	def getMouseTarget(self, point):
		return None

	def setcursor(self, strid):
		if self._curcursor == strid:
			return
		self._curcursor = strid
		cursor = win32window.getcursorhandle(strid)
		Sdk.SetClassLong(self.GetSafeHwnd(),win32con.GCL_HCURSOR,cursor)
	#
	# Mouse response
	#
	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		self._lbuttondown = point
		point = self.DPtoLP(point)
		self._drawContext.onLButtonDown(flags, point)

	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		self._lbuttondown = None
		point = self.DPtoLP(point)
		self._drawContext.onLButtonUp(flags, point)
		if self._tipwnd:
			self._tipwnd.hide()

	def onMouseMove(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		x, y = point
		# x and y are signed number
		x = win32mu.UInt16ToInt(x)
		y = win32mu.UInt16ToInt(y)
		point = x,y
		
		if self._lbuttondown is not None:
			self._lbuttondown = point
		point = self.DPtoLP(point)
		self._drawContext.onMouseMove(flags, point)

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params)
		point, flags = msg.pos(), msg._wParam
		self._lbuttondblclk = point
		point = self.DPtoLP(point)
		self._drawContext.onLButtonDblClk(flags, point)

	def onNCLButton(self, params):
		self._drawContext.onNCButton()

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
		if self._tipwnd:
			self._tipwnd.RedrawWindow()

	def OnDraw(self, dc):
		hf = dc.SelectObjectFromHandle(self._hsmallfont)
		dc.SetBkMode(win32con.TRANSPARENT)
		self.OffscreenPaintOn(dc)
		dc.SelectObjectFromHandle(hf)
		if self._tipwnd:
			self._tipwnd.RedrawWindow()
	
	def getClipRgn(self, rel=None):
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn(self._canvas)
		return rgn

	def getCanvasClipRgn(self, rel=None):
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn(self._canvas)
		return rgn

	def OnEraseBkgnd(self,dc):
		return 1 # promise: we will paint our background
	
	# called by OnDraw or OnPaint
	def OffscreenPaintOn(self, dc):
		lc, tc, rc, bc = dc.GetClipBox()
		wc, hc = rc-lc, bc-tc
			
		# draw to offscreen bitmap for fast looking repaints

		dcc = dc.CreateCompatibleDC()

		bmp = win32ui.CreateBitmap()
		try:
			bmp.CreateCompatibleBitmap(dc, wc, hc)
		except:
			dc.FillSolidRect((lc, tc, rc, bc), win32mu.RGB(self._bgcolor or (255,255,255)))
			print 'Create offscreen bitmap %d x %d failed' % (wc, hc)
			return 

		# called by win32ui
		#self.OnPrepareDC(dcc)
		
		# offset origin more because bitmap is just piece of the whole drawing
		dcc.OffsetViewportOrg((-lc, -tc))
		dcc.SetWindowOrg((0,0))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.SetBrushOrg((lc % 8, tc % 8))
		dcc.IntersectClipRect((lc, tc, rc, bc))
		# dcc has now the same clip box as the original dc

		# draw objects on dcc
		self.paintOn(dcc)

		# copy bitmap
		dcc.SetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		dcc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt((lc,tc),(wc, hc), dcc, (0, 0), win32con.SRCCOPY)

		# clean up
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC()
		del bmp

	def paintOn(self, dc):
		lc, tc, rc, bc = dc.GetClipBox()
		dc.FillSolidRect((lc, tc, rc, bc), win32mu.RGB(self._bgcolor or (255,255,255)))

	#
	#   Scrolling/scaling support
	#
	#   Naming convention:
	#   display coordinate system is called 'Device' (D)   
	#   the canvas coordinate system is called 'Logical' (L) i.e. removing scrolling effect  
	#   the original coordinate system is called 'Natural' (N) i.e. removing scaling effect  

	#
	# Scrolling support
	#
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

	#
	# Scaling support
	# 
	def LPtoNP(self, pt):
		# scaling
		x, y = pt
		sc = self._device2logical
		return sc*x, sc*y

	def LRtoNR(self, rc, round=0):
		x, y = self.LPtoNP(rc[:2])
		w, h = self.LPtoNP(rc[2:])
		if round:
			if x < 0: x = x-0.5
			else: x = x+0.5
			if y < 0: y = y-0.5
			else: y = y+0.5
			return int(x), int(y), int(w+0.5), int(h+0.5)
		return x, y, w, h

	def NPtoLP(self, pt):
		x, y = pt
		sc = 1.0/self._device2logical
		return sc*x, sc*y

	def NRtoLR(self, rc, round=0):
		x, y = self.NPtoLP(rc[:2])
		w, h = self.NPtoLP(rc[2:])
		if round:
			if x < 0: x = x-0.5
			else: x = x+0.5
			if y < 0: y = y-0.5
			else: y = y+0.5
			return int(x), int(y), int(w+0.5), int(h+0.5)
		return x, y, w, h

	def DPtoNP(self, pt):
		return self.LPtoNP(self.DPtoLP(pt))

	def NPtoDP(self, pt):
		return self.LPtoDP(self.NPtoLP(pt))

	def DRtoNR(self, rc):
		return self.LRtoNR(self.DRtoLR(rc))

	def NRtoDR(self, rc):
		return self.LRtoDR(self.NRtoLR(rc, round=1))
							
#########################
# Final concrete classes 

# a layout window based on a generic MFC wnd
class LayoutOsWnd(window.Wnd, LayoutWnd):
	def __init__(self, drawContext):
		window.Wnd.__init__(self, win32ui.CreateWnd())
		LayoutWnd.__init__(self, drawContext)

# a layout window based on an MFC ScrollView
# the benefit of this is that scrolling is much more easier to handle
class LayoutScrollOsWnd(docview.ScrollView, LayoutWnd):
	def __init__(self, drawContext):
		doc = docview.Document(docview.DocTemplate())
		docview.ScrollView.__init__(self, doc)
		LayoutWnd.__init__(self, drawContext)
		self._cancroll = 1

#########################
# Utility classes 

# 1. Minimal concrete win32window.Window
# its not an os window
# can be used as a rich rect shape

class Region(win32window.Window):
	def __init__(self, parent, rc, scale, bgcolor, transparent):
		win32window.Window.__init__(self)
		self.create(parent, rc, UNIT_PXL, z=0, transparent=transparent, bgcolor=bgcolor)
		self.setDeviceToLogicalScale(scale)
		self._active_displist = self.newdisplaylist()

	# overide the default newdisplaylist method defined in win32window
	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return win32window._ResizeableDisplayList(self, bgcolor)
	
	def setImage(self, filename, fit = 'hidden', mediadisplayrect = None):
		if self._active_displist != None:
			self._active_displist.newimage(filename, fit, mediadisplayrect)

	def paintOn(self, dc, rc=None):
		ltrb = l, t, r, b = self.ltrb(self.LRtoDR(self.getwindowpos(), round=1))

		rgn = self.getClipRgn()

		dc.SelectClipRgn(rgn)
		x0, y0 = dc.SetWindowOrg((-l,-t))
		if self._active_displist:
			self._active_displist._render(dc, None)
		dc.SetWindowOrg((x0,y0))

		# draw subwindows
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc)

		# draw region frame
		dc.SelectClipRgn(rgn)
		br = Sdk.CreateBrush(win32con.BS_SOLID, win32api.RGB(0,0,0),0)	
		dc.FrameRectFromHandle(ltrb, br)
		Sdk.DeleteObject(br)

	def getClipRgn(self, rel=None):
		x, y, w, h = self.LRtoDR(self.getwindowpos(), round=1)
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		if rel==self: return rgn
		prgn = self._parent.getClipRgn(rel)
		rgn.CombineRgn(rgn,prgn,win32con.RGN_AND)
		prgn.DeleteObject()
		return rgn

	def getMouseTarget(self, point):
		for w in self._subwindows:
			target = w.getMouseTarget(point)
			if target:
				return target
		if self.inside(point):
			return self
		return None

# 2. Minimal concrete layout control

class LayoutOsWndCtrl(LayoutOsWnd, win32window.Window):
	def __init__(self, host, scale, drawContext = None):
		if not drawContext: drawContext = DrawContext()
		LayoutOsWnd.__init__(self, drawContext)
		
		win32window.Window.__init__(self)
		self._topwindow = self
		self._transparent = 0
		self._active_displist = self.newdisplaylist((255,255,255))

		self._device2logical = scale
		
		# the control container 
		self._host = host

		# host notification flow control flag  
		self._updatehost = 0

		# we are all these
		self._drawContext.addListener(self) 
		self._drawContext.setShapeContainer(self)
		self._drawContext.setShapeFactory(self)
	
		# decor
		self._blackBrush = Sdk.CreateBrush(win32con.BS_SOLID, 0, 0)
		self._selPen = Sdk.CreatePen(win32con.PS_SOLID, 1, win32api.RGB(0,0,255))
		self._selPenDot = Sdk.CreatePen(win32con.PS_DOT, 1, win32api.RGB(0,0,255))

	def OnDestroy(self, params):
		LayoutOsWnd.OnDestroy(self, params)
		Sdk.DeleteObject(self._blackBrush)
		Sdk.DeleteObject(self._selPen)
		Sdk.DeleteObject(self._selPenDot)

	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return win32window._ResizeableDisplayList(self, bgcolor)
	
	def setImage(self, filename, fit='hidden', mediadisplayrect = None):
		if self._active_displist != None:
			self._active_displist.newimage(filename, fit, mediadisplayrect)

	#
	#  ShapeFactory interface implementation
	#	
	def canCreateObjectAt(self, point, strid):
		return 1

	def newObjectAt(self, point, strid):
		x, y = point
		region = Region(self, (x, y, 1, 1), self._device2logical, (255, 255, 255), transparent=1)
		# prepare a resize
		self._drawContext._ixDragHandle = 5
		self._updatehost = 0
		return region

	def removeObject(self, obj):
		if obj in self._subwindows:
			self._subwindows.remove(obj)	
		self.selectTool('shape')
		self.update()

	def onNewObject(self, obj):
		self.selectTool('select')
		x, y, w, h = obj.getwindowpos()
		self._host.updateBox(x, y, w, h)
		self._updatehost = 1
	
	#
	#  ShapeContainer interface implementation
	#	
	def getMouseTarget(self, point):
		# point is in logical coordinates
		# convert it to natural coordinates
		point = self.LPtoNP(point)
		for w in self._subwindows:
			target = w.getMouseTarget(point)
			if target:
				return target
		return None
	
	#
	#  Listener interface overrides
	#	
	def onDSelMove(self, selection):
		LayoutOsWnd.onDSelMove(self, selection)
		x, y, w, h = selection.getwindowpos()
		if self._updatehost:
			self._host.updateBox(x, y, w, h)

	def onDSelResize(self, selection):
		LayoutOsWnd.onDSelResize(self, selection)
		x, y, w, h = selection.getwindowpos()
		if self._updatehost:
			self._host.updateBox(x, y, w, h)
				 
	#
	#  Called by hosting environment to set an object 
	#	
	def setObject(self, rc, strid=None):
		self._drawContext.reset()
		self._subwindows = []
		region = Region(self, rc, self._device2logical, (255, 255, 255), transparent=1)
		self._drawContext.selectShape(region)
		self.update()
		self._updatehost = 1
		return region

	def removeObjects(self):
		self._drawContext.reset()
		self._subwindows = []
		self.update()
		self._updatehost = 1

	#
	#	win32window.Window overrides
	# 
	# win32window context update callback
	# rc is in win32window coordinates (N)
	def update(self, rc=None):
		if rc:
			x, y, w, h = rc
			rc = x, y, x+w, y+h
			# convert N (natural) coordinates to D (device)
			rc = self.NRtoDR(rc)
		try:
			self.InvalidateRect(rc or self.GetClientRect())
		except:
			# os window not alive
			pass

	def getwindowpos(self, rel=None):
		return self._rect

	#
	#	painting
	# 
	def paintOn(self, dc):
		if self._active_displist:
			self._active_displist._render(dc, None)

		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOn(dc)

		self.drawTracker(dc)

	def drawTracker(self, dc):
		wnd = self._drawContext._selected
		if not wnd: return
		
		# frame selection with self._selPen
		rc = wnd.LRtoDR(wnd.getwindowpos(), round=1)
		l, t, r, b = wnd.ltrb(rc)
		
		rgn = self.getCanvasClipRgn()
		dc.SelectClipRgn(rgn)	
		#oldpen = dc.SelectObjectFromHandle(self._selPenDot)
		#win32mu.DrawRectanglePath(dc, (l, t, r-1, b-1))
		#dc.SelectObjectFromHandle(oldpen)

		oldpen = dc.SelectObjectFromHandle(self._selPen)
		win32mu.DrawRectanglePath(dc, (l, t, r-1, b-1))
		dc.SelectObjectFromHandle(oldpen)

		nHandles = wnd.getDragHandleCount()
		for ix in range(1,nHandles+1):
			x, y, w, h = wnd.getDragHandleRect(ix)
			dc.FillSolidRect((x, y, x+w, y+h), win32api.RGB(255,127,80))
			dc.FrameRectFromHandle((x, y, x+w, y+h), self._blackBrush)
			#dc.PatBlt((x, y), (w, h), win32con.DSTINVERT);



 