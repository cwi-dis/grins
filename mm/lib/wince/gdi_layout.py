__version__ = "$Id$"

# app constants
from appcon import *
from WMEVENTS import *

# windows
import winuser, wingdi, wincon
import winstruct
import gdi_displist
import base_transitions

#
import base_window

class Region(base_window.Window):
	def __init__(self, parent, coordinates, transparent, z, units, bgcolor):
		base_window.Window.__init__(self)
		
		# create the window
		self.create(parent, coordinates, units, z, transparent, bgcolor)
		if self._topwindow:
			self._canvas = self._topwindow.LRtoDR(self._canvas, round = 1)
						
	def __repr__(self):
		return '<Region instance at %x>' % id(self)
		
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
		return Region(self, coordinates, transparent, z, units, bgcolor)
	
	def newdisplaylist(self, bgcolor = None, units = UNIT_SCREEN):
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return gdi_displist.DisplayList(self, bgcolor, units)

	def close(self):
		if self._parent is None:
			return
		if self._transition:
			self._transition.endtransition()
		self._parent._subwindows.remove(self)
		self.updateMouseCursor()
		self._parent.update()
		self._parent = None
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		del self._topwindow
		del self._convert_color
		del self._transition

	def update(self, rc = None):
		if self._topwindow and self._topwindow != self:
			if rc is None:
				rc = self.getwindowpos()
			self._topwindow.update(rc)

	def updateNow(self, rc = None):
		if self._topwindow and self._topwindow != self:
			if rc is None:
				rc = self.getwindowpos()
			self._topwindow.updateNow(rc)
	
	def getDR(self):
		rc = self.getwindowpos()
		return self._topwindow.LRtoDR(rc, round = 1)

	def getClipDR(self, dc):
		# dc box
		ltrb1 = dc.GetClipBox()

		# clip to parent
		ltrb2a = winstruct.ltrb(self.getwindowpos())
		ltrb2b = winstruct.ltrb(self._parent.getwindowpos())
		ltrb2 = winstruct.rectAnd(ltrb2a, ltrb2b)
		if ltrb2 is None: return None
		ltrb2 = self._topwindow.LRtoDR(ltrb2, round = 1)

		# common box
		return winstruct.rectAnd(ltrb1, ltrb2)

	def _paintOnSurf(self, surf):
		wnd = self._topwindow.getContext()
		wnd_dc = wingdi.CreateDCFromHandle(wnd.GetDC())
		dc = wnd_dc.CreateCompatibleDC()
		oldsurf = dc.SelectObject(surf)

		xywh_dst = ltrb = self._topwindow.LRtoDR(self._rect, round = 1)
		if self._active_displist:
			entry = self._active_displist._list[0]
			bgcolor = None
			if entry[0] == 'clear' and entry[1]:
				bgcolor = entry[1]
			elif not self._transparent:
				bgcolor = self._bgcolor
			if bgcolor:
				brush = wingdi.CreateSolidBrush(bgcolor)
				old_brush = dc.SelectObject(brush)
				dc.Rectangle(ltrb)
				dc.SelectObject(old_brush)
				wingdi.DeleteObject(brush)
			self._active_displist._render(dc, ltrb, xywh_dst, start=1)
			if self._showing:
				brush =  wingdi.CreateSolidBrush((255, 0, 0))
				dc.FrameRect(ltrb, brush)
				wingdi.DeleteObject(brush)

		elif self._transparent == 0 and self._bgcolor:
			brush = wingdi.CreateSolidBrush(self._bgcolor)
			old_brush = dc.SelectObject(brush)
			dc.Rectangle(ltrb)
			dc.SelectObject(old_brush)
			wingdi.DeleteObject(brush)

		dc.SelectObject(oldsurf)
		dc.DeleteDC()
		wnd.ReleaseDC(wnd_dc.Detach())
		
	# dc origin is viewport origin
	def _paintOnDC(self, dc):
		ltrb = self.getClipDR(dc)
		if ltrb is None:
			return
		if self._active_displist:
			entry = self._active_displist._list[0]
			bgcolor = None
			if entry[0] == 'clear' and entry[1]:
				bgcolor = entry[1]
			elif not self._transparent:
				bgcolor = self._bgcolor
			if bgcolor:
				brush = wingdi.CreateSolidBrush(bgcolor)
				old_brush = dc.SelectObject(brush)
				dc.Rectangle(ltrb)
				dc.SelectObject(old_brush)
				wingdi.DeleteObject(brush)
			self._active_displist._render(dc, ltrb, self.getDR(), start = 1)
			if self._showing:
				brush =  wingdi.CreateSolidBrush((255, 0, 0))
				dc.FrameRect(ltrb, brush)
				wingdi.DeleteObject(brush)

		elif self._transparent == 0 and self._bgcolor:
			brush = wingdi.CreateSolidBrush(self._bgcolor)
			old_brush = dc.SelectObject(brush)
			dc.Rectangle(ltrb)
			dc.SelectObject(old_brush)
			wingdi.DeleteObject(brush)

	# normal painting
	def _paint_0(self, dc, exclwnd = None):
		self._paintOnDC(dc)

		# then paint children bottom up
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paint(dc, exclwnd)

	# transition, multiElement==false
	# trans engine: calls self.paintOn(dc)
	# i.e. trans engine is responsible to paint only this region
	def _paint_1(self, dc, exclwnd = None):
		# first paint self transition surface
		self._topwindow.blitSurfaceOn(dc, self._drawsurf, self.getwindowpos())
		
		# then paint children bottom up normally
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paint(rc, exclwnd)

	# transition, multiElement==true, childrenClip==false
	# trans engine: calls self.paintOnDDS(self._drawsurf, self)
	# i.e. trans engine responsible to paint correctly everything below 
	def _paint_2(self, dc, exclwnd = None):
		pass

	# transition, multiElement==true, childrenClip==true
	# trans engine: calls self.paintOnDDS(self._drawsurf, self)
	# i.e. trans engine is responsible to paint correctly everything below
	def _paint_3(self, dc, exclwnd = None):
		pass
		
	def paint(self, dc, exclwnd = None):
		if not self._isvisible or exclwnd == self:
			return

		if self._transition and self._transition._isrunning():
			if self._transition._ismaster(self):
				if self._multiElement:
					if self._childrenClip:
						self._paint_3(dc, exclwnd)
					else:
						self._paint_2(dc, exclwnd)
				else:
					self._paint_1(dc, exclwnd)
			return

		self._paint_0(dc, exclwnd)


	#
	# Transitions helpers
	#		
	# get a copy of the screen area of this window
	def cloneBackSurf(self, exclwnd = None, dopaint = 1):
		return self._topwindow.cloneSurface(self, exclwnd, dopaint)

	def updateBackSurf(self, surf, exclwnd = None):
		return self._topwindow.updateSurface(surf, self, exclwnd)

	# used by multiElement transition
	# paint on surface dds relative to ancestor rel			
	def paintOnSurf(self, surf, rel = None, exclwnd = None):
		pass

	#
	# Transitions interface implementation
	#		
	def begintransition(self, outtrans, runit, dict, cb):
		if self._transition:
			print 'Multiple Transitions!'
			if cb:
				apply(apply, cb)
			return
		if runit:
			self._multiElement = dict.get('coordinated')
			self._childrenClip = dict.get('clipBoundary', 'children') == 'children'
			self._transition = base_transitions.TransitionEngine(self, outtrans, runit, dict, cb)
			# uncomment the next line to freeze things
			# at the moment begintransition is called
			self._transition.begintransition()
		else:
			self._multiElement = 0
			self._childrenClip = 0
			self._transition = None # base_transitions.InlineTransitionEngine(self, outtrans, runit, dict, cb)
			self._transition.begintransition()

	def endtransition(self):
		if self._transition:
			#print 'endtransition', self
			self._transition.endtransition()
			self._transition = None

	def jointransition(self, window, cb):
		# Join the transition already created on "window".
		if not window._transition:
			print 'Joining without a transition', self, window, window._transition
			return
		if self._transition:
			print 'Multiple Transitions!'
			return
		ismaster = self._windowlevel() < window._windowlevel()
		self._transition = window._transition
		self._transition.join(self, ismaster, cb)
		
	def settransitionvalue(self, value):
		if self._transition:
			#print 'settransitionvalue', value
			self._transition.settransitionvalue(value)
		else:
			print 'settransitionvalue without a transition'

	def _windowlevel(self):
		# Returns 0 for toplevel windows, 1 for children of toplevel windows, etc
		prev = self
		count = 0
		while not prev==prev._topwindow:
			count = count + 1
			prev = prev._parent
		return count

#############################

class Viewport(Region):
	def __init__(self, context, coordinates, bgcolor):
		Region.__init__(self, None, coordinates, 0, 0, UNIT_PXL, bgcolor)
		
		# adjust some variables
		self._topwindow = self
		self._canvas = self.LRtoDR(self._canvas, round = 1)

		# viewport context (here an os window) 
		self._ctx = context
		
		# scaling
		self._device2logical = self._ctx._d2l
			
		self._bgbrush = wingdi.CreateSolidBrush(bgcolor)
			
		# init bmp 
		wd, hd = self.LPtoDP(coordinates[2:])
		self._backBuffer = self.createSurface(wd, hd, bgcolor)
			
	def __repr__(self):
		return '<Viewport instance at %x>' % id(self)

	def _convert_color(self, color):
		return color 

	def getwindowpos(self, rel=None):
		return self._rectb

	def pop(self, poptop = 1):
		pass

	def setcursor(self, strid):
		pass
##		print 'Viewport.setcursor', strid

	def close(self):
		if self._ctx is None:
			return
		ctx = self._ctx
		self._ctx = None
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		del self._topwindow
		ctx.update()

		#
		if self._bgbrush:
			wingdi.DeleteObject(self._bgbrush)
		self._bgbrush = 0


	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
		return Region(self, coordinates, transparent, z, units, bgcolor)
	newcmwindow = newwindow

	# 
	# Query section
	# 
	def is_closed(self):
		return self._ctx is None
		
	def getContext(self):
		return self._ctx

	# 
	# Painting section
	#
	def createSurface(self, w, h, bgcolor):
		if self.is_closed(): return
		wnd = self._ctx
		dc = wingdi.CreateDCFromHandle(wnd.GetDC())
		surf = wingdi.CreateDIBSurface(dc, w, h, bgcolor)
		wnd.ReleaseDC(dc.Detach())
		return surf
	
	def getBackBuffer(self):
		return self._backBuffer

	def update(self, rc=None):
		if self._ctx is None or self._backBuffer is None: 
			return
		if rc is None:
			rc = self._viewport.getwindowpos()
		self._ctx.update(rc)

	def updateNow(self, rc = None):
		wnd = self._ctx

		# create wnd dc
		dc = wingdi.CreateDCFromHandle(wnd.GetDC())

		# clip to rc
		xywh_dev = wnd.LRtoDR(rc, round = 1)
		ltrb_dev = self.ltrb(xywh_dev)
		rgn = wingdi.CreateRectRgn(ltrb_dev)
		dc.SelectClipRgn(rgn)
		rgn.DeleteObject()

		# do paint
		self._ctx.paintOn(dc)

	def paint(self, dc, exlwnd = None):
		ltrb = dc.GetClipBox()
		old_brush = dc.SelectObject(self._bgbrush)
		dc.Rectangle(ltrb)
		dc.SelectObject(old_brush)
		
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paint(dc, exlwnd)

	def paintSurfAt(self, dc, surf, pos):
		dcc = dc.CreateCompatibleDC()
		bmp = dcc.SelectObject(surf)
		dc.BitBlt(pos, surf.GetSize(), dcc, (0, 0), wincon.SRCCOPY)
		dcc.SelectObject(bmp)
		dcc.DeleteDC()
	
	def cloneSurface(self, region, exclwnd = None, dopaint = 1):
		# what rect to clone
		rcd = xd, yd, wd, hd = self.LRtoDR(region.getwindowpos(), round = 1)

		wnd = self._ctx
		dc = wingdi.CreateDCFromHandle(wnd.GetDC())
		
		dcBack = dc.CreateCompatibleDC()
		oldBack = dcBack.SelectObject(self._backBuffer)

		if dopaint:
			rgn = wingdi.CreateRectRgn(rcd)
			dcBack.SelectClipRgn(rgn)
			rgn.DeleteObject()
			self.paint(dcBack, exlwnd = exclwnd)

		dcReg = dcBack.CreateCompatibleDC()
		regSurf = wingdi.CreateDIBSurface(dc, wd, hd)
		oldReg = dcReg.SelectObject(regSurf)

		# copy back to reg
		dcReg.BitBlt((0, 0), (wd, hd), dcBack, (xd, yd), wincon.SRCCOPY)

		# cleanup
		dcReg.SelectObject(oldReg)
		dcReg.DeleteDC()
		dcBack.SelectObject(oldBack)
		dcBack.DeleteDC()
		wnd.ReleaseDC(dc.Detach())
		
		# return region clone
		return regSurf

	def updateSurface(self, surf, region, exclwnd = None):
		# what rect to update
		rcd = xd, yd, wd, hd = self.LRtoDR(region.getwindowpos(), round = 1)

		wnd = self._ctx
		dc = wingdi.CreateDCFromHandle(wnd.GetDC())
		
		dcBack = dc.CreateCompatibleDC()
		oldBack = dcBack.SelectObject(self._backBuffer)

		rgn = wingdi.CreateRectRgn(rcd)
		dcBack.SelectClipRgn(rgn)
		rgn.DeleteObject()
		self.paint(dcBack, exlwnd = exclwnd)

		dcReg = dcBack.CreateCompatibleDC()
		oldReg = dcReg.SelectObject(surf)

		# copy back to reg
		dcReg.BitBlt((0, 0), (wd, hd), dcBack, (xd, yd), wincon.SRCCOPY)

		# cleanup
		dcReg.SelectObject(oldReg)
		dcReg.DeleteDC()
		dcBack.SelectObject(oldBack)
		dcBack.DeleteDC()
		wnd.ReleaseDC(dc.Detach())

	def blitSurfaceOn(self, dc, surf, rc):
		# what rect to blit
		rc_dst = xd, yd, wd, hd = self.LRtoDR(rc, round = 1)

		dcc = dc.CreateCompatibleDC()
		oldsurf = dcc.SelectObject(surf)

		# copy back to reg
		dc.BitBlt((xd, yd), (wd, hd), dcc, (0, 0), wincon.SRCCOPY)
		#dc.StretchBlt(rc_dst, dcc, (0, 0, wd, hd), wincon.SRCCOPY)

		# cleanup
		dcc.SelectObject(oldsurf)
		dcc.DeleteDC()

	# 
	# Mouse section
	# 
	def updateMouseCursor(self):
		pass

	def onMouseEvent(self, point, event, params=None):
		for w in self._subwindows:
			if w.inside(point):
				if event == Mouse0Press:
					w._onlbuttondown(point)
				elif event == Mouse0Release:
					w._onlbuttonup(point)
				break		
		return Region.onMouseEvent(self, point, event)

	def onMouseMove(self, point, params=None):
		# check subwindows first
		for w in self._subwindows:
			if w.inside(point):
				w._onmousemove(point)
				if w.setcursor_from_point(point):
					return

		# not in a subwindow, handle it ourselves
		if self._active_displist:
			x, y, w, h = self.getwindowpos()
			xp, yp = point
			point = xp-x, yp-y
			x, y = self._pxl2rel(point,self._canvas)
			for button in self._active_displist._buttons:
				if button._inside(x,y):
					self.setcursor('hand')
					return
		self.setcursor(self._cursor)


	
