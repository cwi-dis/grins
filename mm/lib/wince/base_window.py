__version__ = "$Id$"

# app constants
from appcon import *
from WMEVENTS import *

import math

import settings

import sysmetrics

import mediainterface


# base class for subwindows
# defines the interface of subwindows
# implements the platform independent part of subwindows 
class Window:
	def __init__(self):
		self._parent = None
		self._bgcolor = (0, 0, 0)
		self._fgcolor = (255, 255, 255)
		self._cursor = 'arrow'
		self._topwindow = None
		self._convert_color = None

		self._rect = 0, 0, 0, 0 # client area in pixels
		self._canvas = 0, 0, 0, 0 # client canvas in pixels
		self._rectb = 0, 0, 0, 0  # rect with respect to parent in pixels
		self._sizes = 0, 0, 0, 0 # rect relative to parent
		self._units = None

		self._z = 0

		self._transparent = 0

		self._subwindows = []
		self._displists = []
		self._active_displist = None
		self._redrawfunc = None
		self._callbacks = {}
		self._showing = None

		self._isvisible = 1

		self._convbgcolor = None

		# transition params
		self._transition = None
		self._fromsurf = None
		self._drawsurf = None

		# scaling support
		self._device2logical = 1

		# animation support
		self._mediadisplayrect = None
		self._fit = 'hidden'

		# scroll support
		self._canscroll = 0
		self._scrollpos = 0, 0

		# scroll implementation by dragging
		self._ptdown = None

	def create(self, parent, coordinates, units, z=0, transparent=0, bgcolor=None):
		self.__setparent(parent)
		self.__setcoordinates(coordinates, units)
		self.__set_z_order(z)
		self.__settransparent(transparent)
		if bgcolor:
			self._bgcolor = bgcolor
		elif parent:
			self._bgcolor = parent._bgcolor

	def __repr__(self):
		return '<%s instance at %x>' % (self.__class__.__name__, id(self))

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	def bgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b
		self._convbgcolor = None

	def newdisplaylist(self, bgcolor = None, units=UNIT_SCREEN):
		import base_displist
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return base_displist.DisplayList(self, bgcolor, units)

	def setredrawfunc(self, func):
		if func is None or callable(func):
			self._redrawfunc = func
		else:
			raise error, 'invalid function'
	
	# mediacoords in UNIT_PXL
	def setmediadisplayrect(self, rc):
		self._mediadisplayrect = rc
		self.checkscrolling()

	# fit: 'hidden':1, 'meet':0, 'slice':-1, ('meed_hidden'=-2,) 'fill':-3', 'scroll':-4
	def setmediafit(self, fit):
		self._fit = fit
		self.checkscrolling()
	
	#
	# Scrolling support
	#
	def checkscrolling(self):
		if not self._mediadisplayrect: 
			return
		wd, hd = self._rect[2:]
		ws, hs = self._mediadisplayrect[2:]
		if self._fit=='scroll' and (ws>wd or hs>hd):
			self._canscroll = 1	
			self.setdefaultcursor('draghand')

	def setscrollpos(self, pos):
		if not self._ptdown or not self._canscroll: return	
		x1, y1 = self._ptdown
		x2, y2 = pos
		self._ptdown = x2, y2
		dx = x2-x1
		dy = y2-y1
		x, y = self._scrollpos
		x, y = x-dx, y-dy
		wd, hd = self._rect[2:]
		ws, hs = self._mediadisplayrect[2:]
		if x>ws-wd: x = ws-wd
		if x<0: x=0
		if y>hs-hd: y = hs-hd
		if y<0: y=0
		self._scrollpos = x, y
		self.update(self.getwindowpos())

	def _onlbuttondown(self, point):
		for wnd in self._subwindows:
			if wnd.inside(point):
				wnd._onlbuttondown(point)
				return
		if self._canscroll:
			self._ptdown = point
		self.updateForeignObject(Mouse0Press, point)

	def _onlbuttonup(self, point):
		for wnd in self._subwindows:
			if wnd.inside(point):
				wnd._onlbuttonup(point)
				return
		if self._canscroll:
			self._ptdown = None
		self.updateForeignObject(Mouse0Release, point)

	def _onmousemove(self, point):
		for wnd in self._subwindows:
			if wnd.inside(point):
				wnd._onmousemove(point)
				return
		if self._canscroll and self._ptdown:	
			self.setscrollpos(point)
		self.updateForeignObject(MouseMove, point)

	def updateForeignObject(self, event, pt):
		callback =  self._callbacks.get(event)
		if not callback: return
		func, arg = callback
		if arg == 'foreignObject':
			x0, y0 = self.getwindowpos()[:2]
			x, y = pt
			self.onEvent(event, (x-x0, y-y0, None, None))
		
	#
	# WMEVENTS section
	#

	# Register user input callbacks
	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in (ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release, 
			     DropFile, PasteFile, DragFile,
				 DragURL, DropURL,
			     DragNode, DropNode,
			     WindowExit, WindowContentChanged,
			     MouseMove, DragEnd, QueryNode):
			self._callbacks[event] = func, arg
			if event in (DropFile, PasteFile, DragFile, DragURL, DropURL, DragNode, DropNode):
				self.registerDropTarget()
		else:
			raise error, 'Registering unknown event %d'%event

	# Unregister user input callbacks
	def unregister(self, event):
		try:
			del self._callbacks[event]
			# XXX Jack thinks the whole list above should feature here too
			if event == DropFile:
				self.revokeDropTarget()
		except KeyError:
			pass

	# Call registered callback
	def onEvent(self,event,params=None):
		if self._callbacks.has_key(event):
			func, arg = self._callbacks[event]
		elif hasattr(self, '_viewport') and self._viewport._callbacks.has_key(event):
			func, arg = self._viewport._callbacks[event]
		else:
			return 1
		func(arg, self, event, params)
		return 1
	
	# Call registered callback with return value
	def onEventEx(self,event,params=None):
		ret=None
		try:
			func, arg = self._callbacks[event]			
		except KeyError:
			pass
		else:
			try:
				ret=func(arg, self, event, params)
			except Continue:
				pass
		return ret


	#
	# Mouse and cursor related support
	#

	# convert device point to logical
	# may differ when self._rect != self._canvas
	def _DPtoLP(self, point):
		return point

	def onMouseEvent(self,point, ev, params=None):
		# Called from, for example, self.OnLButtonDown which is called from a view's mouse event.
		rv = self.__recurse(point)
		if type(rv) is type(()):
			wnd, (x, y, buttons) = rv
			wnd.onEvent(ev, (x, y, buttons, params))
			return 1
		return rv

	def onKeyboardEvent(self, key, ev):
		self.onEvent(ev, key)

	def setcursor_from_point(self, point):
		rv = self.__recurse(point)
		if type(rv) is type(()):
			wnd, (x, y, buttons) = rv
			if buttons:
				wnd.setcursor('hand')
			else:
				wnd.setcursor(wnd._cursor)
			# we handled it
			return 1
		return rv

	def __recurse(self, point):
		if self.is_closed(): return 0
		point = self._DPtoLP(point)
		for wnd in self._subwindows:
			# test that point is inside the window (not the media space area)
			if wnd.inside(point):
				rv = wnd.__recurse(point)
				if rv:
					return rv

		# convert point to subwindow coordinates
		x, y, w, h = self.getwindowpos()
		xp, yp = point
		point= xp-x, yp-y

		disp = self._active_displist
		if disp is not None and not disp.isTransparent(point):
			# we have an active display list, and it's not transparent
			# figure out the buttons
			x,y = self._pxl2rel(point,self._canvas)
			buttons = []
			for button in disp._buttons:
				if button._inside(x,y):
					buttons.append(button)
			# we're done
			return (self, (x, y, buttons))

		# there is no active display list, or it's transparent, so the window gets the click
		if self._transparent:
			# window is transparent, continue looking
			return 0
		# window is not transparent, we have to stop looking
		return 1

	# bring the subwindow infront of windows with the same z	
	def pop(self, poptop=1):
		parent = self._parent
		if parent == self._topwindow:
			if poptop:
				self._topwindow.pop(1)
		else:
			parent.pop(poptop)
		# put self in front of all siblings with equal or lower z
		if self is not parent._subwindows[0]:
			parent._subwindows.remove(self)
			for i in range(len(parent._subwindows)):
				if self._z >= parent._subwindows[i]._z:
					parent._subwindows.insert(i, self)
					break
			else:
				parent._subwindows.append(self)

	# send the subwindow back of the windows with the same z	
	def push(self):
		parent = self._parent
		# put self behind all siblings with equal or higher z
		if self is parent._subwindows[-1]:
			# already at the end
			return
		if self not in parent._subwindows:return
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)-1,-1,-1):
			if self._z <= parent._subwindows[i]._z:
				parent._subwindows.insert(i+1, self)
				break
		else:
			parent._subwindows.insert(0, self)

	def close(self):
		if self._parent is None:
			return
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

	def is_closed(self):
		return self._parent is None

	def showwindow(self, color = (255,0,0)):
		self._showing = color
		self.update()

	def dontshowwindow(self):
		if self._showing:
			self._showing = None

	# Return true if this window highlighted
	def is_showing(self):
		return self._showing

	def show(self):
		self._isvisible = 1
		self.update()

	def hide(self):
		self._isvisible = 0
		self.update()

	def setdefaultcursor(self, strid):
		self._cursor = strid

	def setcursor(self, strid):
		self._topwindow.setcursor(strid)
	
	def updateMouseCursor(self):
		self._topwindow.updateMouseCursor()

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
		wnd = Window()
		wnd.create(self, coordinates, units, z, transparent, bgcolor)
		return wnd
	newcmwindow = newwindow

	def ltrb(self, xywh):
		x,y,w,h = xywh
		return x, y, x+w, y+h

	def xywh(self, ltrb):
		l,t,r,b = ltrb
		return l, t, r-l, b-t

	def rectAnd(self, rc1, rc2):
		l1, t1, r1, b1 = self.ltrb(rc1)	
		l2, t2, r2, b2 = self.ltrb(rc2)
		l, r = max(l1, l2), min(r1, r2)
		t, b = max(t1, t2), min(b1, b2)
		return l, t, max(r-l, 0), max(b-t, 0)

	def rectOr(self, rc1, rc2):
		l1, t1, r1, b1 = self.ltrb(rc1)	
		l2, t2, r2, b2 = self.ltrb(rc2)
		l, t, r, b = min(l1, l2), min(t1, t2), max(r1, r2), max(b1, b2)
		return l, t, r-l, b-t

	# return the coordinates of this window in units
	def getgeometry(self, units = UNIT_MM):
		if units == UNIT_PXL:
			return self._rectb
		elif units == UNIT_SCREEN:
			return self._sizes
		elif units == UNIT_MM:
			x, y, w, h = self._rectb
			return float(x) / sysmetrics.pixel_per_mm_x, \
			       float(y) / sysmetrics.pixel_per_mm_y, \
			       float(w) / sysmetrics.pixel_per_mm_x, \
			       float(h) / sysmetrics.pixel_per_mm_y
		else:
			raise error, 'bad units specified'

	# convert any coordinates to pixel coordinates
	# ref_rect is the reference rect for relative coord
	def _convert_coordinates(self, coordinates, ref_rect = None, crop = 0,
				 units = UNIT_SCREEN, round=1):
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		if units==UNIT_MM:
			x,y,w,h = self._mmtopxl((x,y,w,h),round)
			units=UNIT_PXL

		if ref_rect:
			rx, ry, rw, rh = ref_rect
		else: 
			rx, ry, rw, rh = self._rect
		if units == UNIT_PXL or (units is None and type(x) is type(0)):
			if round: px = int(x)
			else: px= x
			dx = 0
		else:
			if round: px = int(rw * x + 0.5)
			else: px = rw * x
			dx = px - rw * x
		if units == UNIT_PXL or (units is None and type(y) is type(0)):
			if round: py = int(y)
			else: py=y
			dy = 0
		else:
			if round: py = int(rh * y + 0.5)
			else: py = rh * y
			dy = py - rh * y
		pw = ph = 0
		if crop:
			if px < 0:
				px, pw = 0, px
			if px >= rw:
				px, pw = rw - 1, px - rw + 1
			if py < 0:
				py, ph = 0, py
			if py >= rh:
				py, ph = rh - 1, py - rh + 1
		if len(coordinates) == 2:
			return px+rx, py+ry
		if units == UNIT_PXL or (units is None and type(w) is type(0)):
			if round: pw = int(w + pw - dx)
			else: pw = w + pw - dx
		else:
			if round: pw = int(rw * w + 0.5 - dx) + pw
			else: pw = (rw * w - dx) + pw
		if units == UNIT_PXL or (units is None and type(h) is type(0)):
			if round: ph = int(h + ph - dy)
			else: ph = h + ph - dy
		else:
			if round: ph = int(rh * h + 0.5 - dy) + ph
			else: ph = (rh * h - dy) + ph
		if crop:
			if pw <= 0:
				pw = 1
			if px + pw > rw:
				pw = rw - px
			if ph <= 0:
				ph = 1
			if py + ph > rh:
				ph = rh - py
		return px+rx, py+ry, pw, ph

	# convert pixel coordinates to relative coordinates
	def _pxl2rel(self, coordinates, ref_rect=None):
		px, py = coordinates[:2]

		if ref_rect:
			rx, ry, rw, rh = ref_rect
		else:
			rx, ry, rw, rh = self._rect

		x = float(px - rx) / rw
		y = float(py - ry) / rh
		if len(coordinates) == 2:
			return x, y

		pw, ph = coordinates[2:]
		w = float(pw) / rw
		h = float(ph) / rh
		return x, y, w, h

	# convert pixel coordinates to coordinates in units with precision
	# for relative cordinates is the same as _pxl2rel
	def inverse_coordinates(self, coordinates, ref_rect=None, units = UNIT_SCREEN, precision = -1):
		if units == UNIT_PXL:
			return coordinates
		elif units == UNIT_SCREEN:
			if not ref_rect: ref_rect=self._canvas
			coord=self._pxl2rel(coordinates, self._canvas)
			if precision<0: 
				return coord
			else:
				return self._coord_in_prec(coord, precision)
		elif units == UNIT_MM:
			coord= self._pxltomm(coordinates)
			if precision<0: 
				return coord
			else:
				return self._coord_in_prec(coord, precision)
		else:
			raise error, 'bad units specified in inverse_coordinates'

	# convert coordinates in mm to pixel
	def _mmtopxl(self, coordinates, round=1):
		x, y = coordinates[:2]
		if len(coordinates) == 2:
			if round:
				return int(x * sysmetrics.pixel_per_mm_x + 0.5), \
					int(y * sysmetrics.pixel_per_mm_y + 0.5)
			else:
				return x * sysmetrics.pixel_per_mm_x, \
					y * sysmetrics.pixel_per_mm_y
		w, h = coordinates[2:]
		if round:
			return int(x * sysmetrics.pixel_per_mm_x + 0.5), \
			   int(y * sysmetrics.pixel_per_mm_y + 0.5),\
			   int(w * sysmetrics.pixel_per_mm_x + 0.5), \
			   int(h * sysmetrics.pixel_per_mm_y + 0.5)
		else:
			return x * sysmetrics.pixel_per_mm_x, \
			   y * sysmetrics.pixel_per_mm_y,\
			   w * sysmetrics.pixel_per_mm_x, \
			   h * sysmetrics.pixel_per_mm_y

	# convert coordinates in mm to pixel coordinates
	def _pxltomm(self, coordinates):
		x, y = coordinates[:2]
		if len(coordinates) == 2:
			return	float(x) / sysmetrics.pixel_per_mm_x, \
					float(y) / sysmetrics.pixel_per_mm_y
		w, h = coordinates[2:]
		return float(x) / sysmetrics.pixel_per_mm_x, \
			       float(y) / sysmetrics.pixel_per_mm_y, \
			       float(w) / sysmetrics.pixel_per_mm_x, \
			       float(h) / sysmetrics.pixel_per_mm_y
	
	# return coordinates with precision 
	def _coord_in_prec(self, coordinates, precision=-1):
		x, y = coordinates[:2]
		if len(coordinates) == 2:
			if precision<0: 
				return x,y
			else:
				factor=float(pow(10,precision))
				return float(int(factor*x+0.5)/factor),float(int(factor*y+0.5)/factor)
		w, h = coordinates[2:]
		if precision<0: 
			return x,y,w,h
		else:
			factor=float(pow(10,precision))
			return float(int(factor*x+0.5)/factor), float(int(factor*y+0.5)/factor),\
				float(int(factor*w+0.5)/factor), float(int(factor*h+0.5)/factor)

	# returns the relative coordinates of a wnd with respect to its parent
	def getsizes(self):
		return self._sizes

	# Returns the relative coordinates of a wnd with respect to its parent with 2 decimal digits
	def getsizes100(self):
		ps=self.getsizes()
		return float(int(100.0*ps[0]+0.5)/100.0),float(int(100.0*ps[1]+0.5)/100.0),float(int(100.0*ps[2]+0.5)/100.0),float(int(100.0*ps[3]+0.5)/100.0)

	def _convert_color(self, color):
		return color 


	# mediasize: natural size of media
	# mediadisplayrect: computed layout rect according to smil rules 
	#					including regPoint/Align and fit (here is assumed correct)
	# fit: 'hidden':1, 'meet':0, 'slice':-1, ('meed_hidden'=-2,) 'fill':-3', 'scroll':-4
	# returns: source rect for blit operation
	def _getmediacliprect(self, mediasize, mediadisplayrect, fit='hidden'):
		wm, hm = mediasize
		x, y, w, h = mediadisplayrect

		if fit == 'hidden':
			return 0, 0, min(w, wm), min(h, hm)

		elif fit == 'meet':
			return 0, 0, wm, hm

		elif fit == 'slice':
			# we assume that mediadisplayrect is also correct here
			# i.e. is greater or equal to region rc
			return 0, 0, wm, hm

		elif fit == 'fill':
			return 0, 0, wm, hm

		elif fit == 'scroll':
			return 0, 0, min(w, wm), min(h, hm)
		
		return 0, 0, min(w, wm), min(h, hm)

	# return blit dst and src rects given that dst is clipped
	# we want to blit src -> dst but dst is clipped
	# so find part of source mapped to the clipped destination and return it
	def _getsrcclip(self, dst, src, dstclip):
		ld, td, rd, bd = dst
		ls, ts, rs, bs = src
		ldc, tdc, rdc, bdc = dstclip
		
		# find part of source mapped to the clipped destination
		# apply linear transformation from destination -> source
		# x^p = ((x_2^p - x_1^p)*x + (x_1^p*x_2-x_2^p*x_1))/(x_2-x_1)
		# rem: primes represent source coordinates
		a = (rs-ls)/float(rd-ld);b=(ls*rd-rs*ld)/float(rd-ld)
		lsc = int(a*ldc + b + 0.5)
		rsc = int(a*rdc + b + 0.5)
		a = (bs-ts)/float(bd-td);b=(ts*bd-bs*td)/float(bd-td)
		tsc = int(a*tdc + b + 0.5)
		bsc = int(a*bdc + b + 0.5)
		
		return lsc, tsc, rsc, bsc

	# Prepare an image for display (load,crop,fit, etc)
	# Arguments:
	# 1. crop is a tuple of proportions (see computations)
	# 2. fit is one of the fit attribute values
	# 3. if center then do the obvious
	# 4. coordinates specify placement rect
	# 5. clip specifies the src rect
	def _prepare_image(self, file, crop, fit, center, coordinates, clip, align, units):
		
		# get image size. If it can't be found in the cash read it.
		if type(file) == type(''):
			image = mediainterface.get_image(file)
		else:
			image = file
		xsize, ysize = image.GetSize()
		
		# check for valid crop proportions
		top, bottom, left, right = crop
		if top + bottom >= 1.0 or left + right >= 1.0 or \
		   top < 0 or bottom < 0 or left < 0 or right < 0:
			raise error, 'bad crop size'

		# convert the crop sizes (proportions of the image size) to pixels
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		rcKeep=left,top,xsize-right,ysize-bottom

		# get window sizes, and convert them to pixels
		if coordinates is None:
			x, y, width, height = self._canvas
		else:
			x, y, width, height = self._convert_coordinates(coordinates, self._canvas, units=units)

		# compute scale taking into account the hint (0,-1,-2)
		if fit == 'meet':
			xscale = yscale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif fit == 'slice':
			xscale = yscale = max(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif fit == 'icon':
			# a mix of meet and hidden
			# like meet  if scale <= 1
			# like hidden  if scale > 1
			xscale = yscale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
			if xscale > 1:
				xscale = yscale = 1
		elif fit == 'fill':
			xscale = float(width)/(xsize - left - right)
			yscale = float(height)/(ysize - top - bottom)
		elif fit == 'scroll':
			xscale = yscale = 1
		else:
			# default rule
			xscale = yscale = 1

		# scale crop sizes
		top = int(top * yscale + .5)
		bottom = int(bottom * yscale + .5)
		left = int(left * xscale + .5)
		right = int(right * xscale + .5)

		mask=None

		# scale image sizes
		w=xsize
		h=ysize
		if xscale != 1:
			w = int(xsize * xscale + .5)
		if yscale != 1:
			h = int(ysize * yscale + .5)

		if align == 'topleft':
			pass
		elif align == 'centerleft':
			y = y + (height - (h - top - bottom)) / 2
		elif align == 'bottomleft':
			y = y + height - h
		elif align == 'topcenter':
			x = x + (width - (w - left - right)) / 2
		elif align == 'center':
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
		elif align == 'bottomcenter':
			x, y = x + (width - (w - left - right)) / 2, \
			       y + height - h
		elif align == 'topright':
			x = x + width - w
		elif align == 'centerright':
			x, y = x + width - w, \
			       y + (height - (h - top - bottom)) / 2
		elif align == 'bottomright':
			x, y = x + width - w, \
			       y + height - h
		elif center:
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
	
		# x -- left edge of window (left edge of the display rect)
		# y -- top edge of window (top edge of the display rect)
		# width -- width of window
		# height -- height of window
		# w -- width of scaled image
		# h -- height of scaled image
		# left, right, top, bottom -- part to be cropped (offsets from edges)
		if clip is not None:
			clip = self._convert_coordinates(clip, self._canvas, units=units)
			if clip[0] <= x:
				# left edge visible
				if clip[0] + clip[2] <= x:
					# not visible at all
					rcKeep = rcKeep[0],rcKeep[1],0,0
				elif clip[0] + clip[2] < x + w:
					# clipped at right end
					rcKeep2 = rcKeep[2]
					delta = x + w - clip[0] - clip[2]
					right = right + delta
					rcKeep2 = rcKeep2 - int(rcKeep2 * float(delta)/w + .5)
					rcKeep = rcKeep[0],rcKeep[1],rcKeep2,rcKeep[3]
				else:
					# totally visible
					pass
			elif x < clip[0] < x + w:
				# left edge not visible
				if clip[0] + clip[2] < x + w:
					# only center visible
					rcKeep2 = rcKeep[2]
					delta = clip[0]-x
					x = x + delta
					left = left + delta
					delta = int(rcKeep2 * float(delta)/w + .5)
					rcKeep0 = rcKeep[0] + delta
					rcKeep2 = rcKeep2 - delta
					delta = x + w - clip[0] - clip[2]
					right = right + delta
					delta = int(rcKeep2 * float(delta)/w + .5)
					rcKeep2 = rcKeep2 - delta
					rcKeep = rcKeep0,rcKeep[1],rcKeep2,rcKeep[3]
				else:
					# clipped at left
					rcKeep2 = rcKeep[2]
					delta = clip[0]-x
					x = x + delta
					left = left + delta
					delta = int(rcKeep2 * float(delta)/w + .5)
					rcKeep0 = rcKeep[0] + delta
					rcKeep2 = rcKeep2 - delta
					rcKeep = rcKeep0,rcKeep[1],rcKeep2,rcKeep[3]
			else:
				# not visible at all
				rcKeep = rcKeep[0],rcKeep[1],0,0
			if clip[1] <= y:
				# top edge visible
				if clip[1] + clip[3] <= y:
					# not visible at all
					rcKeep = rcKeep[0],rcKeep[1],0,0
				elif clip[1] + clip[3] < y + h:
					# clipped at bottom end
					rcKeep3 = rcKeep[3]
					delta = y + h - clip[1] - clip[3]
					bottom = bottom + delta
					rcKeep3 = rcKeep3 - int(rcKeep3 * float(delta)/h + .5)
					rcKeep = rcKeep[0],rcKeep[1],rcKeep[2],rcKeep3
				else:
					# totally visible
					pass
			elif y < clip[1] < y + h:
				# top edge not visible
				if clip[1] + clip[3] < y + h:
					# only center visible
					rcKeep3 = rcKeep[3]
					delta = clip[1]-y
					y = y + delta
					top = top + delta
					delta = int(rcKeep3 * float(delta)/h + .5)
					rcKeep1 = rcKeep[1] + delta
					rcKeep3 = rcKeep3 - delta
					delta = y + h - clip[1] - clip[3]
					bottom = bottom + delta
					delta = int(rcKeep3 * float(delta)/h + .5)
					rcKeep3 = rcKeep3 - delta
					rcKeep = rcKeep[0],rcKeep1,rcKeep[2],rcKeep3
				else:
					# clipped at top
					rcKeep3 = rcKeep[3]
					delta = clip[1]-y
					y = y + delta
					top = top + delta
					delta = int(rcKeep3 * float(delta)/h + .5)
					rcKeep1 = rcKeep[1] + delta
					rcKeep3 = rcKeep3 - delta
					rcKeep = rcKeep[0],rcKeep1,rcKeep[2],rcKeep3
			else:
				# not visible at all
				rcKeep = rcKeep[0],rcKeep[1],0,0
		
		# return:
		# image attrs: image, mask
		# src left, top (unused)
		# dest rect
		# src rect (image crop rect)

		return image, mask, left, top, x, y,\
			w - left - right, h - top - bottom, rcKeep


	# return true if an arrow has been hit
	def hitarrow(self, point, src, dst):
		# return 1 iff (x,y) is within the arrow head
		# sx, sy = self._convert_coordinates(src,self._canvas)
		# dx, dy = self._convert_coordinates(dst,self._canvas)
		# x, y = self._convert_coordinates(point,self._canvas)
		sx, sy = src
		dx, dy = dst
		x,y = point
		lx = dx - sx
		ly = dy - sy
		if lx == ly == 0:
			angle = 0.0
		else:
			angle = math.atan2(lx, ly)
		cos = math.cos(angle)
		sin = math.sin(angle)
		# translate
		x, y = x - dx, y - dy
		# rotate
		nx = x * cos - y * sin
		ny = x * sin + y * cos
		# test
		if ny > 0 or ny < -ARR_LENGTH:
			return 0
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return 0
		return 1

	# call this method to set content canvas and enable dragging
	def setcontentcanvas(self, w, h, units = UNIT_SCREEN):
		pass

	def getwindowpos(self, rel=None):
		if rel==self:
			return self._rect
		if self._parent:
			X, Y, W, H = self._parent.getwindowpos(rel)
		else:
			X, Y, W, H = 0, 0, 0, 0
		x, y, w, h = self._rectb
		return int(X+x+0.5), int(Y+y+0.5), int(w+0.5), int(h+0.5)
				
	def inside(self, (xp, yp)):
		x, y, w, h = self.getwindowpos()
		return x <= xp < x + w and y <= yp < y + h
	
	#
	# Private methods
	#
	def __setparent(self, parent):
		self._parent = parent
		if parent:
			self._bgcolor = parent._bgcolor
			self._fgcolor = parent._fgcolor
			self._cursor = parent._cursor
			self._topwindow = parent._topwindow
			self._convert_color = parent._convert_color

	# update related coordinates members in a consistent way
	def __setcoordinates(self, coordinates, units):
		if self._parent:
			x, y, w, h = self._parent._convert_coordinates(coordinates, units = units)
		else:
			x, y, w, h = coordinates
			units = UNIT_PXL
		self._rect = 0, 0, w, h # client area in pixels
		self._rectb = x, y, w, h  # rect with respect to parent in pixels
		self._canvas = 0, 0, w, h # client canvas in pixels
		if self._parent:
			try:
				self._sizes = self._parent._pxl2rel(self._rectb) # rect relative to parent
			except:
				self._sizes = 0, 0, 1, 1
		else:
			self._sizes = 0, 0, 1, 1
		self._units = units

	# insert this window in parent._subwindows list at the correct z-order
	def __set_z_order(self, z):
		self._z = z
		if not self._parent: return
		parent = self._parent
		for i in range(len(parent._subwindows)):
			if self._z > parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)

	def __settransparent(self, transparent):
		if transparent not in (0, 1):
			raise error, 'invalid value for transparent arg'
		self._transparent = transparent

	# redraw this window and its childs
	def update(self, rc = None):
		pass

	def updateNow(self, rc = None):
		pass

	# return all ancestors of self including topwindow
	def getAncestors(self):
		if self == self._topwindow:
			return []
		L = []
		wnd = self._parent
		while wnd and wnd != self._topwindow:
			L.append(wnd)
			wnd = wnd._parent
		L.append(self._topwindow)
		return L
	#
	# Animations interface
	#
	def updatecoordinates(self, coordinates, units=UNIT_PXL, fit=None, mediacoords=None):
		# first convert any coordinates to pixel
		if units != UNIT_PXL:
			coordinates = self._convert_coordinates(coordinates, units=units)
		
		# keep old pos
		rc1 = self.getwindowpos()

		x, y, w, h = coordinates
		self.setmediadisplayrect(mediacoords)

		# resize/move
		self._rect = 0, 0, w, h # client area in pixels
		self._rectb = x, y, w, h  # rect with respect to parent in pixels
		self._canvas = self._topwindow.LRtoDR(self._rect) # client canvas in pixels
		self._sizes = self._parent._pxl2rel(self._rectb) # rect relative to parent
		
		# find rc = rc1 union rc2
		rc2 = self.getwindowpos()
		l1, t1, r1, b1 = rc1[0], rc1[1], rc1[0] + rc1[2], rc1[1] + rc1[3]
		l2, t2, r2, b2 = rc2[0], rc2[1], rc2[0] + rc2[2], rc2[1] + rc2[3]
		l, t, r, b = min(l1, l2), min(t1, t2), max(r1, r2), max(b1, b2)
		rc = l, t, r-l+4, b-t+4
		self.update(rc)

	def updatezindex(self, z):
		self._z = z
		parent = self._parent
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)):
			if self._z >= parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)
		self._parent.update()
	
	def updatebgcolor(self, color):
		self.bgcolor(color)
		if self._active_displist:
			self._active_displist.updatebgcolor(color)
		self.update()

	#
	# Transitions interface
	#
	def begintransition(self, outtrans, runit, dict, cb):
		pass

	def endtransition(self):
		pass

	def jointransition(self, window, cb):
		pass
				
	def settransitionvalue(self, value):
		pass
		
	#
	# Scaling support
	#
	# design decision:
	# window rectangles, the methods getwindowpos, inside, etc
	# are all kept in their original coordinate system (i.e. unscaled)
	
	# note that when there is scaling
	# window rectangles become floating tuples

	# naming convention:
	# the original system is called 'logical' (L)
	# the display system is called 'device' (D)

	def setDeviceToLogicalScale(self, d2lscale):
		if d2lscale<=0: d2lscale = 1.0
		self._device2logical = d2lscale
		for wnd in self._subwindows:
			wnd.setDeviceToLogicalScale(d2lscale)

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

	def LDtoDD(self, d, round=0):
		sc = 1.0/self._device2logical
		if round:
			return int(sc*d+0.5)
		return sc*d

	def DDtoLD(self, d):
		return d*self._device2logical

	#
	# Drag & Resize interface
	#

	# return drag handle position in device coordinates
	def getDragHandle(self, ix):
		rc = self.LRtoDR(self.getwindowpos(), round=1)
		x, y, w, h = rc
		w, h = w-1, h-1
		xc = x + w/2
		yc = y + h/2
		if ix == 0:
			x = x+w/2
			y = y+h/2
		elif ix == 1:
			x = x
			y = y
		elif ix == 2:
			x = xc
			y = y
		elif ix == 3:
			x = x+w
			y = y
		elif ix == 4:
			x = x+w
			y = yc
		elif ix == 5:
			x = x+w
			y = y+h
		elif ix == 6:
			x = xc
			y = y+h
		elif ix == 7:
			x = x
			y = y+h
		elif ix == 8:
			x = x
			y = yc
		return x, y

	# return drag handle rectangle in device coordinates
	def getDragHandleRect(self, ix):
		x, y = self.getDragHandle(ix)
		return x-3, y-3, 7, 7

	def getDragHandleCount(self):
		return 9

	def getDragHandleCursor(self, ix):
		if ix==0: id = 'arrow'
		elif ix==1 or ix==5:id = 'sizenwse'
		elif ix==2 or ix==6:id = 'sizens'
		elif ix==3 or ix==7:id = 'sizenesw'
		elif ix==4 or ix==8:id = 'sizewe'
		else: id = 'arrow'
		return id

	# return drag handle at device coordinates
	def getDragHandleAt(self, point):
		xp, yp = point
		for ix in range(9):
			x, y, w, h = self.getDragHandleRect(ix)
			l, t, r, b = x, y, x+w, y+h
			if xp>=l and xp<r and yp>=t and yp<b:
				return ix
		return -1

	# move drag handle in device coordinates to point in device coordinates
	def moveDragHandleTo(self, ixHandle, point):
		xp, yp = self.DPtoLP(point)
		x, y, w, h = self.getwindowpos()
		l, t, r, b = x, y, x+w, y+h
		if ixHandle == 0:
			return
		elif ixHandle == 1:
			l = xp
			t = yp
		elif ixHandle== 2:
			t = yp
		elif ixHandle== 3:
			r = xp
			t = yp
		elif ixHandle== 4:
			r = xp
		elif ixHandle== 5:
			r = xp
			b = yp
		elif ixHandle== 6:
			b = yp
		elif ixHandle== 7:
			l = xp
			b = yp
		elif ixHandle== 8:
			l = xp

		if self._parent:
			xr, yr = self._parent.getwindowpos()[:2]
			l, t, r, b = l-xr, t-yr, r-xr, b-yr
		self.updatecoordinates((l, t, r-l, b-t), units=UNIT_PXL)

	def moveBy(self, delta):
		dx, dy = self.DPtoLP(delta)
		xr, yr, w, h = self._rectb
		self.updatecoordinates((xr+dx, yr+dy, w, h), units=UNIT_PXL)
		
	def invalidateDragHandles(self):
		x, y, w, h  = self.getwindowpos()
		delta = self.DDtoLD(7)
		x = x-delta
		y = y-delta
		w = w+2*delta
		h = h+2*delta
		self.update((x, y, w, h))

	def isResizeable(self):
		return 1

