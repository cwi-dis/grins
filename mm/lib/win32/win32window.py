
# app constants
from appcon import *
from WMEVENTS import *

import win32mu

import win32api

from win32ig import win32ig
from win32displaylist import _DisplayList

import ddraw

import settings

# for global toplevel 
import __main__

# base class for subwindows
# defines the interface of subwindows
# implements the platform independent part of subwindows 
class Window:
	def __init__(self):
		self._parent = None
		self._bgcolor = (0, 0, 0)
		self._fgcolor = (255, 255, 255)
		self._cursor = ''
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
		self._curcursor = ''

		self._isvisible = 1

		self._convbgcolor = None

		# transition params
		self._transition = None
		self._fromsurf = None
		self._drawsurf = None
		self._outtrans = 0
		self._stdpaint = 1

		# scaling support
		self._device2logical = 1

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
		return '<Window instance at %x>' % id(self)

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	def bgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b
		self._convbgcolor = None

	def newdisplaylist(self, bgcolor = None, units=UNIT_SCREEN):
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor, units)

	def setredrawfunc(self, func):
		if func is None or callable(func):
			self._redrawfunc = func
		else:
			raise error, 'invalid function'

	#
	# WMEVENTS section
	#

	# Register user input callbacks
	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in(ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release, 
				 DropFile, PasteFile, DragFile,
				 DragNode, DropNode,
				 WindowExit, WindowContentChanged):
			self._callbacks[event] = func, arg
			if event in (DropFile, PasteFile, DragFile, DragNode, DropNode):
				self.registerDropTarget()
		else:
			raise error, 'Registering unknown event %d'%event

	# Unregister user input callbacks
	def unregister(self, event):
		try:
			del self._callbacks[event]
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
		try:
			func(arg, self, event, params)
		except Continue:
			return 0
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

	def onMouseEvent(self,point, ev):
		cont, stop = 0, 1
		if self.is_closed(): return cont
		point = self._DPtoLP(point)
		for wnd in self._subwindows:
			# test that point is inside the window (not the media space area)
			if wnd.inside(point):
				if wnd.onMouseEvent(point, ev):
					return stop
			
		disp = self._active_displist
		if disp:
			x, y, w, h = self.getwindowpos()
			xp, yp = point
			point= xp-x, yp-y
			x,y = self._pxl2rel(point,self._canvas)
			buttons = []
			for button in disp._buttons:
				if button._inside(x,y):
					buttons.append(button)
			if self.onEvent(ev,(x, y, buttons)):
				# a button has received event, so we have to stop
				return stop

		# at this point, we didn't find a "anchor button" associated to this event
		if self._transparent==0:
			# if window is not transparent, we have to stop to look for whichever the
			# display list (existing or not)
			return stop
		else:
			if disp:
				# if the channel is transparent, we have to check if the event location
				# is inside or outside the media. Note: the media area depend of media type
				# Currently, only win32displaylist give this information (it's at least the
				# case for images).
				if disp._insideMedia(x,y):
					# event inside the media, we have to stop
					return stop
				else:
					# outside the media, and transparent window. So check the next window
					return cont
			else:
				# not active display list and transparent window. So check the next window
				return cont

	def setcursor_from_point(self, point):
		cont, stop = 0, 1
		point = self._DPtoLP(point)
		for w in self._subwindows:
			if w.inside(point):
				if w.setcursor_from_point(point):
					return stop

		if self._active_displist:
			x, y, w, h = self.getwindowpos()
			xp, yp = point
			point = xp-x, yp-y
			x, y = self._pxl2rel(point,self._canvas)

			for button in self._active_displist._buttons:
				if button._inside(x,y):
					self.setcurcursor('hand')
					return stop
			
		# at this point, we don't find a "valid button"
		if self._transparent==0:
			# if window is not transparent, we have to stop to look for whichever the
			# display list
			self.setcurcursor('arrow')
			return stop
		else:
			if self._active_displist:
				# if the channel is transparent, we have to check if the event location
				# is inside or outside the media. Note: the media area depend of media type
				# Currently, only win32displaylist give this information (it's at least the
				# case for image).
				if self._active_displist._insideMedia(x,y):
					# event inside the media, we have to stop
					self.setcurcursor('arrow')
					return stop
				else:
					# outside the media, and transparent window. So check the next window
					return cont
			else:
				# not active display list and transparent window. So check the next window
				return cont 

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

	def setcursor(self, cursor):
		self._cursor = cursor

	def setcurcursor(self, strid):
		self._topwindow.setcursor(strid)
	
	def iscursor(self, strid):
		return self._topwindow._curcursor == strid

	def updateMouseCursor(self):
		self._topwindow.updateMouseCursor()

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return Window(self, coordinates, units, z, transparent)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return self.newwindow(coordinates, pixmap, transparent, z, type_channel, units)

	def ltrb(self, xywh):
		x,y,w,h = xywh
		return x, y, x+w, y+h

	def xywh(self, ltrb):
		l,t,r,b = ltrb
		return l, t, r-l, b-t

	# return the coordinates of this window in units
	def getgeometry(self, units = UNIT_MM):
		toplevel=__main__.toplevel
		if units == UNIT_PXL:
			return self._rectb
		elif units == UNIT_SCREEN:
			return self._sizes
		elif units == UNIT_MM:
			x, y, w, h = self._rectb
			return float(x) / toplevel._pixel_per_mm_x, \
			       float(y) / toplevel._pixel_per_mm_y, \
			       float(w) / toplevel._pixel_per_mm_x, \
			       float(h) / toplevel._pixel_per_mm_y
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
			toplevel=__main__.toplevel
			coord=self._pxltomm(coordinates)
			if precision<0: 
				return coord
			else:
				return self._coord_in_prec(coord, precision)
		else:
			raise error, 'bad units specified in inverse_coordinates'

	# convert coordinates in mm to pixel
	def _mmtopxl(self, coordinates, round=1):
		x, y = coordinates[:2]
		toplevel=__main__.toplevel
		if len(coordinates) == 2:
			if round:
				return int(x * toplevel._pixel_per_mm_x + 0.5), \
					int(y * toplevel._pixel_per_mm_y + 0.5)
			else:
				return x * toplevel._pixel_per_mm_x, \
					y * toplevel._pixel_per_mm_y
		w, h = coordinates[2:]
		if round:
			return int(x * toplevel._pixel_per_mm_x + 0.5), \
			   int(y * toplevel._pixel_per_mm_y + 0.5),\
			   int(w * toplevel._pixel_per_mm_x + 0.5), \
			   int(h * toplevel._pixel_per_mm_y + 0.5)
		else:
			return x * toplevel._pixel_per_mm_x, \
			   y * toplevel._pixel_per_mm_y,\
			   w * toplevel._pixel_per_mm_x, \
			   h * toplevel._pixel_per_mm_y

	# convert coordinates in mm to pixel coordinates
	def _pxltomm(self, coordinates):
		x, y = coordinates[:2]
		toplevel=__main__.toplevel
		if len(coordinates) == 2:
			return	float(x) / toplevel._pixel_per_mm_x, \
					float(y) / toplevel._pixel_per_mm_y
		w, h = coordinates[2:]
		return float(x) / toplevel._pixel_per_mm_x, \
			       float(y) / toplevel._pixel_per_mm_y, \
			       float(w) / toplevel._pixel_per_mm_x, \
			       float(h) / toplevel._pixel_per_mm_y
	
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

	# Returns the size of the image
	def _image_size(self, file):
		return 0, 0

	# Returns the handle of the image
	def _image_handle(self, file):
		return  -1

	# Prepare an image for display (load,crop,scale, etc)
	# Arguments:
	# 1. crop is a tuple of proportions (see computations)
	# 2. scale is a hint for scaling and can be 0, -1, -2, -3 or None (see computations)
	# 3. if center then do the obvious
	# 4. coordinates specify placement rect
	# 5. clip specifies the src rect
	def _prepare_image(self, file, crop, scale, center, coordinates, clip, units):
		
		# get image size. If it can't be found in the cash read it.
		xsize, ysize = self._image_size(file)
		
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
			x, y, width, height = self._convert_coordinates(coordinates,self._canvas, units=units)
		
		# compute scale taking into account the hint (0,-1,-2)
		if scale == 0:
			xscale = yscale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -1:
			xscale = yscale = max(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -2:
			xscale = yscale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
			if xscale > 1:
				xscale = yscale = 1
		elif scale == -3:
			xscale = float(width)/(xsize - left - right)
			yscale = float(height)/(ysize - top - bottom)
		else:
			# default rule
			xscale = yscale = scale

		# scale crop sizes
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)

		image = self._image_handle(file)
		mask=None

		if settings.get('no_image_cache'):
			try:
				del __main__.toplevel._image_cache[file]
			except:
				pass
			try:
				del __main__.toplevel._image_size_cache[file]
			except:
				pass

		# scale image sizes
		w=xsize
		h=ysize
		if xscale != 1:
			w = int(xsize * xscale + .5)
		if yscale != 1:
			h = int(ysize * yscale + .5)

		if center:
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
			clip = self._convert_coordinates(clip, self._canvas)
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
		sx, sy = self._convert_coordinates(src,self._canvas)
		dx, dy = self._convert_coordinates(dst,self._canvas)
		x, y = self._convert_coordinates(point,self._canvas)
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
		X, Y, W, H = self._parent.getwindowpos(rel)
		x, y, w, h = self._rectb
		return X+x, Y+y, w, h
				
	def inside(self, point):
		x, y, w, h = self.getwindowpos()
		l, t, r, b = x, y, x+w, y+h
		xp, yp = point
		if xp>=l and xp<r and yp>=t and yp<b:
			return 1
		return 0


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
		self._canvas = 0, 0, w, h # client canvas in pixels
		self._rectb = x, y, w, h  # rect with respect to parent in pixels
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
	def update(self, rc=None):
		self._topwindow.update(rc)

	#
	# Animations interface
	#
	def updatecoordinates(self, coordinates, units=UNIT_PXL, mediacoords=None):
		# first convert any coordinates to pixel
		if units != UNIT_PXL:
			coordinates = self._convert_coordinates(coordinates,units=units)
		
		if coordinates==self._rectb:
			return
		
		x, y, w, h = coordinates

		# keep old pos
		x0, y0, w0, h0 = self._rectb
		x1, y1, w1, h1 = self.getwindowpos()
		
							
		# resize/move
		self._rect = 0, 0, w, h # client area in pixels
		self._canvas = 0, 0, w, h # client canvas in pixels
		self._rectb = x, y, w, h  # rect with respect to parent in pixels
		if self._parent:
			self._sizes = self._parent._pxl2rel(self._rectb) # rect relative to parent
		else:
			self._sizes = 0, 0, 1, 1


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
	
	def updatebgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b
		if self._active_displist:
			self._active_displist.updatebgcolor(color)
		self.update()

	#
	# Transitions interface
	#
	def begintransition(self, inout, runit, dict, cb):
		if cb:
			apply(apply, cb)

	def endtransition(self):
		pass

	def changed(self):
		pass
		
	def settransitionvalue(self, value):
		pass
		
##	def freeze_content(self, how):
##		pass


	#
	# Scaling support
	#
	def setDeviceToLogicalScale(self, scale):
		self._device2logical = scale

	def DPtoLP(self, pt):
		x, y = pt
		sc = self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5)

	def DRtoLR(self, rc):
		x, y, w, h = rc
		sc = self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5), int(sc*w+0.5), int(sc*h+0.5)

	def LPtoDP(self, pt):
		x, y = pt
		sc = 1.0/self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5)

	def LRtoDR(self, rc):
		x, y, w, h = rc
		sc = 1.0/self._device2logical
		return int(sc*x+0.5), int(sc*y+0.5), int(sc*w+0.5), int(sc*h+0.5)


	#
	# Drag & Resize interface
	#
	def getDragHandle(self, ix):
		x, y, w, h = self.getwindowpos()
		xc = x + w/2
		yc = y + h/2
		if ix == 1:
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
	def getDragHandleRect(self, ix, log=0):
		if log:
			x, y = self.getDragHandle(ix)
		else:	
			x, y = self.LPtoDP(self.getDragHandle(ix))
		return x-3, y-3, 6, 6

	def getDragHandleCount(self):
		return 8

	def getDragHandleCursor(self, ix):
		if   ix==1 or ix==5:id = 'sizenwse'
		elif ix==2 or ix==6:id = 'sizens'
		elif ix==3 or ix==7:id = 'sizenesw'
		elif ix==4 or ix==8:id = 'sizewe'
		else: id = 'arrow'
		return id

	def getDragHandleAt(self, point):
		xp, yp = point
		for ix in range(1,9):
			x, y, w, h = self.getDragHandleRect(ix, log=1)
			l, t, r, b = x, y, x+w, y+h
			if xp>=l and xp<r and yp>=t and yp<b:
				return ix
		return 0

	def moveDragHandleTo(self, ixHandle, point):
		xp, yp = point
		x, y, w, h = self.getwindowpos()
		l, t, r, b = x, y, x+w, y+h
		if	ixHandle== 1:
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
		dx, dy = delta
		xr, yr, w, h = self._rectb
		self.updatecoordinates((xr+dx, yr+dy, w, h), units=UNIT_PXL)
		
	def invalidateDragHandles(self):
		x, y, w, h  = self.LRtoDR(self.getwindowpos())
		delta = 4
		x = x-delta
		y = y-delta
		w = w+2*delta
		h = h+2*delta
		self.update((x, y, w, h))

	def isResizeable(self):
		return 1

#################################################
class DDWndLayer:
	def __init__(self, wnd, bgcolor = None):
		self._wnd = wnd
		self._ddraw = None
		self._frontBuffer = None
		self._backBuffer = None
		self._clipper = None
		self._bgcolor = bgcolor

	def	createDDLayer(self, w=0, h=0):
		self._ddraw = ddraw.CreateDirectDraw()
		self._ddraw.SetCooperativeLevel(self._wnd.GetSafeHwnd(), ddraw.DDSCL_NORMAL)

		# create front buffer (shared with GDI)
		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE)
		self._frontBuffer = self._ddraw.CreateSurface(ddsd)
			
		# size of back buffer
		# for now we create it at the size of the screen
		# to avoid resize manipulations
		from __main__ import toplevel
		W = toplevel._scr_width_pxl
		H = toplevel._scr_height_pxl
		if w==0 or h==0:
			w = W
			h = H
		if w>1600: w = 1600
		if h>1200: h = 1200

		# create back buffer 
		# we draw everything on this surface and 
		# then blit it to the front surface
		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
		ddsd.SetSize(w,h)
		try:
			self._backBuffer = self._ddraw.CreateSurface(ddsd)
		except ddraw.error, arg:
			print arg
			if self.fixDimensions(w, h, ddsd):
				print 'warning: viewport size too big'
				self._backBuffer = self._ddraw.CreateSurface(ddsd)
				
		self._clipper = self._ddraw.CreateClipper(self.GetSafeHwnd())
		self._frontBuffer.SetClipper(self._clipper)
		self._pxlfmt = self._frontBuffer.GetPixelFormat()

		# fill back buffer with default player background (white)
		ddcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255,255,255))
		self._backBuffer.BltFill((0, 0, w, h), ddcolor)

	def createFullScreenDDLayer(self):
		from __main__ import toplevel
		w = toplevel._scr_width_pxl
		h = toplevel._scr_height_pxl

		self._ddraw = ddraw.CreateDirectDraw()
		self._ddraw.SetCooperativeLevel(self._wnd.GetSafeHwnd(), 
			ddraw.DDSCL_EXCLUSIVE | ddraw.DDSCL_FULLSCREEN)
		self._ddraw.SetDisplayMode(800,600,16)

		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_CAPS | ddraw.DDSD_BACKBUFFERCOUNT)
		ddsd.SetCaps(ddraw.DDSCAPS_PRIMARYSURFACE | ddraw.DDSCAPS_FLIP | ddraw.DDSCAPS_COMPLEX)
		ddsd.SetBackBufferCount(1)
		self._frontBuffer = self._ddraw.CreateSurface(ddsd)

		self._backBuffer = self._frontBuffer.GetAttachedSurface(ddraw.DDSCAPS_BACKBUFFER)	
		self._pxlfmt = self._frontBuffer.GetPixelFormat()

		# fill back buffer with default player background (white)
		ddcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255,255,255))
		self._frontBuffer.BltFill((0, 0, w, h), ddcolor)
		self._backBuffer.BltFill((0, 0, w, h), ddcolor)
		
	def destroyDDLayer(self):
		if self._ddraw:
			del self._frontBuffer
			del self._backBuffer
			del self._clipper
			del self._ddraw
			self._ddraw = None

	def destroyFullScreenDDLayer(self):
		if self._ddraw:
			self._ddraw.RestoreDisplayMode()
			del self._frontBuffer
			del self._ddraw
			self._ddraw = None

	def getDirectDraw(self):
		return self._ddraw

	def getRGBBitCount(self):
		return self._pxlfmt[0]

	def getPixelFormat(self):
		return self._pxlfmt

	def getDrawBuffer(self):
		if not self._ddraw: return None
		if self._backBuffer.IsLost():
			if not self._backBuffer.Restore():
				return None
		return self._backBuffer

	def fixDimensions(self, w, h, ddsd):
		from __main__ import toplevel
		W = toplevel._scr_width_pxl
		H = toplevel._scr_height_pxl
		if w>W or h>H:
			if w>W: w = W
			if h>H: h = H
			ddsd.SetSize(w,h)
			return 1
		return 0

	def CreateSurface(self, w, h):
		if not self._ddraw: return None
		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
		ddsd.SetSize(w,h)
		dds = None
		while dds is None:
			try:
				dds = self._ddraw.CreateSurface(ddsd)
			except ddraw.error, arg:
				print arg
				dds = None
				if self.fixDimensions(w, h, ddsd):
					print 'warning: viewport size too big'
				win32api.Sleep(50)
		ddcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255,255,255))
		while 1:
			if dds.IsLost():
				win32api.Sleep(50)
			else:
				try:
					dds.BltFill((0, 0, w, h), ddcolor)
				except ddraw.error, arg:
					print arg
				else:
					break
		return dds

	def flip(self):
		if not self._ddraw:
			return
		rcBack = self._wnd.GetClientRect()
		rcFront = self._wnd.ClientToScreen(rcBack)
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
			else:
				# OK, backBuffer resored, paint it
				self.paint()
		try:
			self._frontBuffer.Blt(rcFront, self._backBuffer, rcBack)
		except ddraw.error, arg:
			print arg


	def flipFullScreen(self):
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
			else:
				# OK, backBuffer resored, paint it
				self.paint()
		self._frontBuffer.Flip(0, ddraw.DDFLIP_WAIT)

########################################

# regions, RGB 
import win32ui, win32con, win32api

import win32transitions

class Region(Window):
	def __init__(self, parent, coordinates, transparent, z, units, bgcolor):
		Window.__init__(self)
		
		# create the window
		self.create(parent, coordinates, units, z, transparent, bgcolor)

		# context os window
		if parent:
			self._ctxoswnd = self._topwindow.getContextOsWnd()

		# implementation specific
		self._oswnd = None
		self._video = None

		# resizing
		self._resizing = 0
		self._mediacoords = None
		self._orgrect = self._rect
						
	def __repr__(self):
		return '<Region instance at %x>' % id(self)
		
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None, bgcolor=None):
		return Region(self, coordinates, transparent, z, units, bgcolor)

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
		del self._video 
		del self._drawsurf
		del self._fromsurf

	#
	# OS windows simulation support
	#
	def GetSafeHwnd(self):
		if self._oswnd: wnd = self._oswnd
		else: wnd = self._topwindow
		return wnd.GetSafeHwnd()
	
	def GetClientRect(self):
		x, y, w, h = self._rect
		return x, y, x+w, y+h

	def HookMessage(self, f, m):
		if self._oswnd: wnd = self._oswnd
		else: wnd = self._topwindow
		wnd.HookMessage(f,m)

	#
	# Foreign renderers support
	#
	def CreateOSWindow(self, rect=None, html=0):
		if self._oswnd:
			return self._oswnd
		from pywinlib.mfc import window
		Afx=win32ui.GetAfx()
		Sdk=win32ui.GetWin32Sdk()

		x, y, w, h = self.getwindowpos()
		if rect:
			xp, yp, wp, hp = rect
			x, y, w, h = x+xp, y+yp, wp, hp
		if html: obj = win32ui.CreateHtmlWnd()
		else: obj = win32ui.CreateWnd()
		wnd = window.Wnd(obj)
		color = self._bgcolor
		if not color:
			color = 0, 0, 0
		brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(color),0)
		cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		icon=0
		clstyle=win32con.CS_DBLCLKS
		style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS
		exstyle = 0
		title = '' 
		if self._transparent in (-1,1):
			exstyle=win32con.WS_EX_TRANSPARENT
		strclass=Afx.RegisterWndClass(clstyle,cursor,brush,icon)
		rc = self._topwindow.offsetospos((x,y,w,h))
		wnd.CreateWindowEx(exstyle,strclass,title,style,
			self.ltrb(rc),self._ctxoswnd,0)
		
		# put ddwnd below childwnd
		flags=win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOACTIVATE|win32con.SWP_ASYNCWINDOWPOS		
		self._ctxoswnd.SetWindowPos(wnd.GetSafeHwnd(), (0,0,0,0), flags)
		
		wnd.ShowWindow(win32con.SW_SHOW)

		if html:
			import settings
			wnd.UseHtmlCtrl(not settings.get('html_control'))
			wnd.HookMessage(self.onUserUrl,win32con.WM_USER)

		self._oswnd = wnd
		if not html:
			self.hookOsWndMessages()
		return wnd

	def hookOsWndMessages(self):
		if not self._oswnd: return
		self.HookMessage(self.onOsWndLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onOsWndLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onOsWndMouseMove,win32con.WM_MOUSEMOVE)
	
	def onOsWndLButtonDown(self, params):
		xr, yr = win32mu.Win32Msg(params).pos()
		x, y, w, h = self.getwindowpos()
		self._topwindow.onMouseEvent((x+xr, y+yr), Mouse0Press)

	def onOsWndLButtonUp(self, params):
		xr, yr = win32mu.Win32Msg(params).pos()
		x, y, w, h = self.getwindowpos()
		self._topwindow.onMouseEvent((x+xr, y+yr), Mouse0Release)

	def onOsWndMouseMove(self, params):
		xr, yr = win32mu.Win32Msg(params).pos()
		x, y, w, h = self.getwindowpos()
		self._topwindow.onMouseMove(0, (x+xr, y+yr))

	def DestroyOSWindow(self):
		if self._oswnd:
			self._oswnd.DestroyWindow()
			self._oswnd = None
			if not self.is_closed():
				self.update()

	def RetrieveUrl(self,fileOrUrl):
		if not self._oswnd:
			self.CreateOSWindow(self, html=1)	
		self._oswnd.Navigate(fileOrUrl)

	def HasHtmlCtrl(self):
		if not self._oswnd: return 0
		return self._oswnd.HasHtmlCtrl()
	
	def CreateHtmlCtrl(self):
		if self._oswnd:
			self._oswnd.CreateHtmlCtrl()

	def DestroyHtmlCtrl(self):
		if self._oswnd:
			self._oswnd.DestroyHtmlCtrl()
	def SetImmHtml(self, text):
		if self._oswnd:
			self._oswnd.SetImmHtml(text)
					
	# Called by the Html channel to set the callback to be called on cmif links
	# Part of WebBrowsing support
	def setanchorcallback(self,cb):
		self._anchorcallback=cb

	# Called by the HtmlWnd when a cmif anchor has fired. It is a callback but implemented
	# using the std windows message mechanism
	# Part of WebBrowsing support
	def onUserUrl(self,params):
		url=self.GetForeignUrl()
		if hasattr(self,'_anchorcallback') and self._anchorcallback:
			self._anchorcallback(url)

	def show(self):
		self._isvisible = 1
		if self._oswnd:
			self._oswnd.ShowWindow(win32con.SW_SHOW)
		self.update()

	def hide(self):
		self._isvisible = 0
		if self._oswnd:
			self._oswnd.ShowWindow(win32con.SW_HIDE)
		self.update()

	def updateoswndpos(self):
		for w in self._subwindows:
			w.updateoswndpos()
		
		if self._oswnd:
			x, y, w, h = self.getwindowpos()
			self._oswnd.SetWindowPos(win32con.HWND_TOP, (x,y,w,h) , 
				win32con.SWP_NOZORDER | win32con.SWP_ASYNCWINDOWPOS | win32con.SWP_DEFERERASE)

	#
	# Inage management
	#
	# Returns the size of the image
	def _image_size(self, file):
		toplevel=__main__.toplevel
		try:
			xsize, ysize = toplevel._image_size_cache[file]
		except KeyError:
			img = win32ig.load(file)
			xsize,ysize,depth=win32ig.size(img)
			toplevel._image_size_cache[file] = xsize, ysize
			toplevel._image_cache[file] = img
		self._topwindow.imgAddDocRef(file)
		return xsize, ysize

	# Returns handle of the image
	def _image_handle(self, file):
		return  __main__.toplevel._image_cache[file]


	#
	# Box creation section
	#
	def create_box(self, msg, callback, box = None, units = UNIT_SCREEN, modeless=0, coolmode=0):
		if self._topwindow!=self:
			self._topwindow.create_box(msg, callback, box, units, modeless, coolmode)

	def cancel_create_box(self):
		if self._topwindow!=self:
			self._topwindow.cancel_create_box()


	#
	# Rendering section
	#

	def getClipRgn(self, rel=None):
		x, y, w, h = self.getwindowpos(rel);
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		if rel==self: return rgn
		prgn = self._parent.getClipRgn(rel)
		rgn.CombineRgn(rgn,prgn,win32con.RGN_AND)
		prgn.DeleteObject()
		return rgn

	# get reg of children
	def getChildrenRgn(self, rel=None):
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((0,0,0,0))
		for w in self._subwindows:
			x, y, w, h = w.getwindowpos(rel);
			newrgn = win32ui.CreateRgn()
			newrgn.CreateRectRgn((x,y,x+w,y+h))
			rgn.CombineRgn(rgn,newrgn,win32con.RGN_OR)
			newrgn.DeleteObject()
		# finally clip to this
		argn = self.getClipRgn(rel)
		rgn.CombineRgn(rgn,argn,win32con.RGN_AND)
		argn.DeleteObject()
		return rgn

	# get reg of this excluding children
	def getChildrenRgnComplement(self, rel=None):
		rgn = self.getClipRgn(rel)
		drgn = self.getChildrenRgn(rel)
		rgn.CombineRgn(rgn,drgn,win32con.RGN_DIFF)
		drgn.DeleteObject()
		return rgn

	def clipRect(self, rc, rgn):
		newrgn = win32ui.CreateRgn()
		newrgn.CreateRectRgn(self.ltrb(rc))
		newrgn.CombineRgn(rgn,newrgn,win32con.RGN_AND)
		ltrb = newrgn.GetRgnBox()[1]
		newrgn.DeleteObject()
		return self.xywh(ltrb)
	
	def rectAnd(self, rc1, rc2):
		# until we make calcs
		rc,ans= win32ui.GetWin32Sdk().IntersectRect(self.ltrb(rc1),self.ltrb(rc2))
		if ans:
			return self.xywh(rc)
		return (0, 0, 0, 0)

	
	# paint on surface dds only what this window is responsible for
	# i.e. self._active_displist and/or bgcolor
	# clip painting to argument rgn when given
	def _paintOnDDS(self, dds, dst, rgn=None):
		x, y, w, h = dst
		if w==0 or h==0:
			return
		
		if rgn:
			xc, yc, wc, hc = self.xywh(rgn.GetRgnBox()[1])
		else:
			xc, yc, wc, hc = dst

		if wc==0 or hc==0:
			return
		
		if dds.IsLost():
			return

		if self._active_displist:
			entry = self._active_displist._list[0]
			if entry[0] == 'clear' and entry[1]:
				r, g, b = entry[1]
				convbgcolor = dds.GetColorMatch((r,g,b))
				dds.BltFill((xc, yc, xc+wc, yc+hc), convbgcolor)

			if self._video:
				# get video info
				vdds, vrcDst, vrcSrc = self._video
				xd, yd, wd, hd = vrcDst
				ld, td, rd, bd = x+xd, y+yd, x+xd+wd, y+yd+hd
				ls, ts, rs, bs = self.ltrb(vrcSrc)

				# clip destination
				ldc, tdc, rdc, bdc = self.ltrb(self.rectAnd((xc, yc, wc, hc), 
					(ld, td, rd-ld, bd-td)))
			
				# find part of source mapped to the clipped destination
				# apply linear afine transformation from destination -> source
				# x^p = ((x_2^p - x_1^p)*x + (x_1^p*x_2-x_2^p*x_1))/(x_2-x_1)
				# rem: primes represent source coordinates
				a = (rs-ls)/float(rd-ld);b=(ls*rd-rs*ld)/float(rd-ld)
				lsc = int(a*ldc + b + 0.5)
				rsc = int(a*rdc + b + 0.5)
				a = (bs-ts)/float(bd-td);b=(ts*bd-bs*td)/float(bd-td)
				tsc = int(a*tdc + b + 0.5)
				bsc = int(a*bdc + b + 0.5)
			
				# we are ready, blit it
				if not vdds.IsLost():
					dds.Blt((ldc, tdc, rdc, bdc), vdds, (lsc,tsc,rsc,bsc), ddraw.DDBLT_WAIT)
				else:
					vdds.Restore()

			# draw now the display list but after clear
			hdc = dds.GetDC()
			dc = win32ui.CreateDCFromHandle(hdc)
			if rgn:
				dc.SelectClipRgn(rgn)
			x0, y0 = dc.SetWindowOrg((-x,-y))

			self._active_displist._render(dc, None, clear=0)


			if self._showing:
				win32mu.FrameRect(dc,self._rect,self._showing)
			
			dc.SetWindowOrg((x0,y0))
			dc.Detach()
			dds.ReleaseDC(hdc)

			# if we have an os-subwindow invalidate its area
			# but do not update it since we want this to happen
			# after the surfaces flipping
			if self._oswnd:
				self._oswnd.InvalidateRect(self._oswnd.GetClientRect())
			
		elif self._transparent == 0 and self._bgcolor:
			if self._convbgcolor == None:
				r, g, b = self._bgcolor
				self._convbgcolor = dds.GetColorMatch((r,g,b))
			dds.BltFill((xc, yc, xc+wc, yc+hc), self._convbgcolor)

					
	# paint on surface dds relative to ancestor rel			
	def paintOnDDS(self, dds, rel=None, exclwnd=None):
		#print 'paintOnDDS', self, 'subwindows', len(self._subwindows), self._rect
		# first paint self
		rgn = self.getClipRgn(rel)
		dst = self.getwindowpos(rel)
		try:
			self._paintOnDDS(dds, dst, rgn)
		except ddraw.error, arg:
			print arg
		rgn.DeleteObject()
		
		# then paint children bottom up
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			w.paintOnDDS(dds, rel, exclwnd)

		# then paint transition children bottom up
		if self._transition and self._transition._isrunning() and self._transition._ismaster(self):
			L = self._transition.windows[1:]
			L.reverse()
			for wnd in L:
				wnd.paintOnDDS(dds, rel, exclwnd)

	# get a copy of the screen area of this window
	def getBackDDS(self, exclwnd=None):
		dds = self.createDDS()
		bf = self._topwindow.getDrawBuffer()
		while bf.IsLost():
			win32api.Sleep(50)
			bf.Restore()
		x, y, w, h = self.getwindowpos()
		self._topwindow.paint(exclwnd=exclwnd)
		try:
			dds.Blt((0,0,w,h), bf, (x, y, x+w, y+h), ddraw.DDBLT_WAIT)
		except ddraw.error, arg:
			print arg
		return dds

	def updateBackDDS(self, dds, exclwnd=None):
		bf = self._topwindow.getDrawBuffer()
		while bf.IsLost():
			win32api.Sleep(50)
			bf.Restore()
		x, y, w, h = self.getwindowpos()
		self._topwindow.paint(exclwnd=exclwnd)
		try:
			dds.Blt((0,0,w,h), bf, (x, y, x+w, y+h), ddraw.DDBLT_WAIT)
		except ddraw.error, arg:
			print arg
		return dds

	def bltDDS(self, srfc):
		rc_dst = self.getwindowpos()
		src_w, src_h = srfc.GetSurfaceDesc().GetSize()
		rc_src = (0, 0, src_w, src_h)
		buf = self._topwindow.getDrawBuffer()
		if rc_dst[2]!=0 and rc_dst[3]!=0:
			try:
				buf.Blt(self.ltrb(rc_dst), srfc, rc_src, ddraw.DDBLT_WAIT)
			except ddraw.error, arg:
				print arg			

	def clearSurface(self, dds):
		w, h = dds.GetSurfaceDesc().GetSize()
		if self._convbgcolor == None:
			if self._bgcolor:
				r, g, b = self._bgcolor
			else:
				r, g, b = 0, 0, 0
			self._convbgcolor = dds.GetColorMatch((r,g,b))
		try:
			if not dds.IsLost():
				dds.BltFill((0, 0, w, h), self._convbgcolor)
		except ddraw.error, arg:
			print arg			

	# normal painting
	def _paint_0(self, rc=None, exclwnd=None):
#		if self._transition and self._transition._isrunning():
#			print 'normal paint while in transition', self 

		if exclwnd==self: return

		# first paint self
		dst = self.getwindowpos(self._topwindow)
		rgn = self.getClipRgn(self._topwindow)
		if rc:
			prgn = win32ui.CreateRgn()
			prgn.CreateRectRgn(self.ltrb(rc))
			rgn.CombineRgn(rgn,prgn,win32con.RGN_AND)
			prgn.DeleteObject()
						
		buf = self._topwindow.getDrawBuffer()
		if buf.IsLost() and not buf.Restore():
			return
		try:
			self._paintOnDDS(buf, dst, rgn)
		except ddraw.error, arg:
			print arg
			
		rgn.DeleteObject()

		# then paint children bottom up
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			if w!=exclwnd:
				w.paint(rc, exclwnd)

	# transition, multiElement==false
	# trans engine: calls self._paintOnDDS(self._drawsurf)
	# i.e. trans engine is responsible to paint only this 
	def _paint_1(self, rc=None, exclwnd=None):
		# print 'transition, multiElement==false', self
		if exclwnd==self: return

		# first paint self transition surface
		self.bltDDS(self._drawsurf)
		
		# then paint children bottom up normally
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			if w!=exclwnd:
				w.paint(rc, exclwnd)

	# transition, multiElement==true, childrenClip==false
	# trans engine: calls self.paintOnDDS(self._drawsurf, self)
	# i.e. trans engine responsible to paint correctly everything below 
	def _paint_2(self, rc=None, exclwnd=None):
		#print 'transition, multiElement==true, childrenClip==false', self
		if exclwnd==self: return
		
		# paint transition surface
		self.bltDDS(self._drawsurf)
	
	# delta helpers for the next method
	def __getDC(self, dds):
		hdc = dds.GetDC()
		return win32ui.CreateDCFromHandle(hdc)
	def __releaseDC(self, dds, dc):
		hdc = dc.Detach()
		dds.ReleaseDC(hdc)

	# transition, multiElement==true, childrenClip==true
	# trans engine: calls self.paintOnDDS(self._drawsurf, self)
	# i.e. trans engine is responsible to paint correctly everything below
	def _paint_3(self, rc=None, exclwnd=None):
		# print 'transition, multiElement==true, childrenClip==true',self

		# 1. and then a _paint_2 but on ChildrenRgnComplement
		# use GDI to paint transition surface 
		# (gdi supports clipping but surface bliting not)
		src = self._drawsurf
		dst = self._topwindow.getDrawBuffer()

		dstDC = self.__getDC(dst)	
		srcDC = self.__getDC(src)	
		rgn = self.getChildrenRgnComplement(self._topwindow)
		dstDC.SelectClipRgn(rgn)
		x, y, w, h = self.getwindowpos()
		try:
			dstDC.BitBlt((x, y),(w, h),srcDC,(0, 0), win32con.SRCCOPY)
		except ddraw.error, arg:
			print arg			
		self.__releaseDC(dst,dstDC)
		self.__releaseDC(src,srcDC)
		rgn.DeleteObject()
				
		# 2. do a normal painting to paint children
		if self._transition:
			L = self._transition.windows[1:]
			L.reverse()
			for wnd in L:
				wnd._paint_0(rc, exclwnd)
	
	# paint while frozen
	def _paint_4(self, rc=None, exclwnd=None):
		#print 'paint while frozen'
		if exclwnd==self: return
		if not self._fromsurf.IsLost():
			self.bltDDS(self._fromsurf)

	# painting while resizing
	def _paint_5(self, rc=None, exclwnd=None):
		if exclwnd==self: return
		# lie for a moment 
		# we 'll restore truth before anybody notice it
		temp = self._rect
		self._rect = self._orgrect

		# first paint self but on org rect
		dst = self._orgrect
		dds = self.createDDS(dst[2],dst[3])
		self.clearSurface(dds)
		try:
			self._paintOnDDS(dds, dst)
		except ddraw.error, arg:
			print arg			

		# then paint children bottom up relative to us
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			try:
				w.paintOnDDS(dds, self)
			except ddraw.error, arg:
				print arg			

		# restore truth
		self._rect = temp

		# and scale to current rect
		self.bltDDS(dds)
		
	def paint(self, rc=None, exclwnd=None):
		if not self._isvisible or exclwnd==self:
			return

		if self._resizing and self._mediacoords:
			self._paint_5(rc, exclwnd)
			return

		if self._transition and self._transition._isrunning():
			if self._transition._ismaster(self):
				if self._multiElement:
					if self._childrenClip:
						self._paint_3(rc, exclwnd)
					else:
						self._paint_2(rc, exclwnd)
				else:
					self._paint_1(rc, exclwnd)
			return

		self._paint_0(rc, exclwnd)
		
	def createDDS(self, w=0, h=0):
		if w==0 or h==0:
			x, y, w, h = self._rect
		return self._topwindow.CreateSurface(w,h)

	def setvideo(self, dds, rcDst, rcSrc):
		self._video = dds, rcDst, rcSrc
	
	def removevideo(self):
		self._video = None

	#
	# Animations interface
	#
	def updatecoordinates(self, coordinates, units=UNIT_PXL, mediacoords=None):
		# first convert any coordinates to pixel
		if units != UNIT_PXL:
			coordinates = self._convert_coordinates(coordinates,units=units)
		
		if coordinates==self._rectb:
			return
		
		x, y, w, h = coordinates

		# keep old pos
		x0, y0, w0, h0 = self._rectb
		x1, y1, w1, h1 = self.getwindowpos()

		# sense a size change/restore
		if 0 and not self._resizing:
			if w!=w0 or h!=h0:
				self._resizing = 1
				self._mediacoords = mediacoords
				self._orgrect = self._rect
		elif w==w0 and h==h0:	
			self._resizing = 0
							
		# resize/move
		self._rect = 0, 0, w, h # client area in pixels
		self._canvas = 0, 0, w, h # client canvas in pixels
		self._rectb = x, y, w, h  # rect with respect to parent in pixels
		self._sizes = self._parent._pxl2rel(self._rectb) # rect relative to parent
		
		self._topwindow.update()

		# update the pos of any os subwindows
		self.updateoswndpos()

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
		if self._transition:
			print 'Multiple Transitions!'
			if cb:
				apply(apply, cb)
			return
		self._multiElement = dict.get('coordinated')
		self._childrenClip = dict.get('clipBoundary', 'children') == 'children'
		self._outtrans = outtrans
		self._transition = win32transitions.TransitionEngine(self, outtrans, runit, dict, cb)
		if runit:
			# uncommend the next line to freeze things
			# at the moment begintransition is called
			# win32ui.MessageBox('begintransition')
			self._transition.begintransition()
		else:
			print 'begintransition runit=',runit

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
			self._transition.settransitionvalue(value)
		else:
			print 'settransitionvalue without a transition'

	def _windowlevel(self):
		"""Returns 0 for toplevel windows, 1 for children of toplevel windows, etc"""
		prev = self
		count = 0
		while not prev==prev._topwindow:
			count = count + 1
			prev = prev._parent
		return count

#############################

class Viewport(Region):
	def __init__(self, context, x, y, width, height, bgcolor):
		Region.__init__(self, None, (x,y,width, height), 0, 0, UNIT_PXL, bgcolor)
		
		# adjust some variables
		self._topwindow = self
		
		# cache for easy access
		self._width = width
		self._height = height
		
		self._ctx = context
			
	def __repr__(self):
		return '<Viewport instance at %x>' % id(self)

	def _convert_color(self, color):
		return color 

	def getwindowpos(self, rel=None):
		return self._rectb

	def offsetospos(self, rc):
		x, y, w, h = rc
		X, Y, W, H = self._ctx.getwindowpos()
		return X+x, Y+y, w, h

	def CreateSurface(self, w, h):
		return self._ctx.CreateSurface(w, h)

	def pop(self, poptop=1):
		self._ctx.pop(poptop)

	def getContextOsWnd(self):
		return self._ctx.getContextOsWnd()

	def setcursor(self, strid):
		self._ctx.setcursor(strid)

	def close(self):
		if self._ctx is None:
			return
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		del self._topwindow
		self._ctx.closeViewport(self)
		self._ctx = None

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None, bgcolor=None):
		return Region(self, coordinates, transparent, z, units, bgcolor)
	
	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None, bgcolor=None):
		return newwindow(coordinates, pixmap, transparent, z, type_channel, units, bgcolor)	

	# 
	# Query section
	# 
	def is_closed(self):
		return self._ctx is None

	def getClipRgn(self, rel=None):
		x, y, w, h = self._rectb
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		return rgn

	def getDrawBuffer(self):
		return self._ctx.getDrawBuffer()

	def getPixelFormat(self):
		return self._ctx.getPixelFormat()

	def getDirectDraw(self):
		return self._ctx.getDirectDraw()

	def getRGBBitCount(self):
		return self._ctx.getRGBBitCount()
		
	def getContext(self):
		return self._ctx
	# 
	# Painting section
	# 
	def update(self, rc=None, exclwnd=None):
		self._ctx.update(rc, exclwnd)
		if self._callbacks.has_key(WindowContentChanged):
			func, arg = self._callbacks[WindowContentChanged]
			func(arg, self, WindowContentChanged, __main__.toplevel.getcurtime())

	def paint(self, rc=None, exclwnd=None):
		drawBuffer = self._ctx.getDrawBuffer()

		if rc is None:
			rcPaint = self._rectb
		else:
			rcPaint = self.rectAnd(rc, self._rectb)

		# check for empty update
		if rcPaint[2]==0 or rcPaint[3]==0:
			return

		# first paint self
		try:
			self._paintOnDDS(drawBuffer, rcPaint)
		except ddraw.error, arg:
			print arg
			return

		# then paint children bottom up
		L = self._subwindows[:]
		L.reverse()
		for w in L:
			if w!=exclwnd:
				w.paint(rc, exclwnd)

	# 
	# Mouse section
	# 
	def updateMouseCursor(self):
		self._ctx.updateMouseCursor()

	def imgAddDocRef(self, file):
		self._ctx.imgAddDocRef(file)

	def onMouseMove(self, flags, point):		
		# check subwindows first
		for w in self._subwindows:
			if w.inside(point):
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
					self.setcurcursor('hand')
					return
		self.setcurcursor('arrow')


##########################
class ViewportContext:
	def __init__(self, wnd, w, h, units, bgcolor):
		
		# make viewport context size acceptable by wmf
		# until we know the rule for the aspect ratio
		# apply only the 16 boundaries rule
		# on my machine 4:3 always works best
		# but on Dick's this ratio is 3:4
		#wp, hp = self.__getBoundaries16(w, h)
		wp, hp = self.__getWMPViewport(w, h, 4, 3)
		
		print 'Exporting using surface: width=', wp, 'height=',hp

		self._viewport = Viewport(self, (wp-w)/2, (hp-h)/2, w, h, bgcolor)
		self._rect = 0, 0, wp, hp

		self._wnd = wnd
		self._bgcolor = (0, 0, 0) # should be always black for WMP

		# set a slow timer so that we get some progress feedback
		# when nothing is changing in the viewport
		self._timerid = wnd.SetTimer(2,500)
		wnd.HookMessage(self.onTimer, win32con.WM_TIMER)

		self._ddraw = ddraw.CreateDirectDraw()
		self._ddraw.SetCooperativeLevel(self._wnd.GetSafeHwnd(), ddraw.DDSCL_NORMAL)
		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
		ddsd.SetSize(wp, hp)
		self._backBuffer = self._ddraw.CreateSurface(ddsd)
		self._pxlfmt = self._backBuffer.GetPixelFormat()

		self._ddbgcolor = self._backBuffer.GetColorMatch(self._bgcolor or (255,255,255))
		self._backBuffer.BltFill((0, 0, wp, hp), self._ddbgcolor)

	def onTimer(self, params):
		self._viewport.update()

	def update(self, rc=None, exclwnd=None):
		if self._backBuffer.IsLost():
			if not self._backBuffer.Restore():
				return
		
		# do we have anything to update?
		if rc and (rc[2]==0 or rc[3]==0): 
			return 

		if rc is None:
			x, y, w, h = self._viewport._rectb
			rcPaint = x, y, x+w, y+h
		else:
			rcPaint = rc[0], rc[1], rc[0]+rc[2], rc[1]+rc[3] 
		try:
			self._backBuffer.BltFill(rcPaint, self._ddbgcolor)
		except ddraw.error, arg:
			print arg
			return

		if self._viewport:
			self._viewport.paint(rc, exclwnd)

	def setcursor(self, strid):
		pass

	def getRGBBitCount(self):
		return self._pxlfmt[0]

	def getPixelFormat(self):
		returnself._pxlfmt

	def getDirectDraw(self):
		return self._ddraw

	def getContextOsWnd(self):
		return self._wnd

	def pop(self, poptop=1):
		pass

	def getwindowpos(self):
		return self._viewport._rect

	def closeViewport(self, viewport):
		self._wnd.KillTimer(self._timerid)
		del viewport

	def getDrawBuffer(self):
		return self._backBuffer

	def updateMouseCursor(self):
		pass

	def imgAddDocRef(self, file):
		self._wnd.imgAddDocRef(file)

	def CreateSurface(self, w, h):
		ddsd = ddraw.CreateDDSURFACEDESC()
		ddsd.SetFlags(ddraw.DDSD_WIDTH | ddraw.DDSD_HEIGHT | ddraw.DDSD_CAPS)
		ddsd.SetCaps(ddraw.DDSCAPS_OFFSCREENPLAIN)
		ddsd.SetSize(w,h)
		dds = self._ddraw.CreateSurface(ddsd)
		dds.BltFill((0, 0, w, h), self._ddbgcolor)
		return dds

	def __getBoundaries16(self, w, h):
		wp = (w/16)*16
		if w % 16 !=0: wp = wp + 16
		hp = (h/16)*16
		if h % 16 !=0: hp = hp + 16
		return wp, hp

	# return covering rectangle with
	# 1. 16 pixels boundaries
	# 2. wr:hr(=4:3) aspect ratio
	def __getWMPViewport(self, w, h, wr=4, hr=3):
		n1 = int((wr*h)/float(hr*16.0)+0.5)
		n2 = int(w/16.0+0.5)
		if n1>n2: n=n1
		else: n=n2
		while (hr*n % wr)!=0: n = n + 1
		m = (hr*n)/wr
		return n*16, m*16

#############################

# selection modes
[SM_NONE, SM_MOVE, SM_SIZE, SM_NET] = range(4)

Sdk = win32ui.GetWin32Sdk()
	 
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

		# muliselect support
		self._muliselect = 0
		self._downPt = 0, 0
		self._lastPt = 0, 0
		self._focusdrawn = 0

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
			self.__notifyListeners(self._selected)
	
	def moveSelectionHandleTo(self, point):
		if self._selected:
			self._selected.invalidateDragHandles()
			self._selected.moveDragHandleTo(self._ixDragHandle, point)
			self._selected.invalidateDragHandles()
			self.__notifyListeners(self._selected)

	def select(self, shape):
		if self._selected:
			self._selected.invalidateDragHandles()	
		self._selected = shape
		self.__notifyListeners(shape)
	
	def showproperties(self):
		if self._selected:
			for obj in self._listeners:
				obj.onProperties(self._selected)
	
	def __notifyListeners(self, shape):
		for obj in self._listeners:
			obj.onShapeChange(shape)

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

	#
	# Create new objects support
	# Do not implement if this support is not needed
	#
	def createObject(self):
		# create a new object
		# at self._downPt with zero dimensions
		pass

	def removeObject(self, shape):
		# remove shape
		# used by shape tool to remove objects
		# with zero dimensions
		self._curtool = self._seltool

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


class SelectTool(DrawTool):
	def __init__(self, ctx):
		DrawTool.__init__(self, ctx)

	def onLButtonDown(self, flags, point):
		ctx = self._ctx
		ctx._selmode = SM_NONE
		
		# resize
		shape = ctx._selected
		if shape:
			ctx._ixDragHandle = shape.getDragHandleAt(point)
			if ctx._ixDragHandle and shape.isResizeable():
				ctx._selmode = SM_SIZE
				ctx.setcursor(shape.getDragHandleCursor(ctx._ixDragHandle))
		
		# selection
		if ctx._selmode == SM_NONE:
			shape = ctx.getMouseTarget(point)
			if shape:
				ctx._selmode = SM_MOVE
				ctx.select(shape)

		# bgclick
		if ctx._selmode == SM_NONE:
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
		if shape:
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


#########################################
# Experimental resizeable DisplayList

from win32ig import win32ig
import gear32sd

class _ResizeableDisplayList(_DisplayList):
	def __init__(self, window, bgcolor):
		_DisplayList.__init__(self, window, bgcolor, UNIT_SCREEN)

	def _do_render(self, entry, dc, region):
		cmd = entry[0]
		wnd = self._window
		rc = x, y, w, h = wnd.LRtoDR(wnd._rect)
		ltrb = x, y, x+w, y+h
		if cmd == 'clear' and entry[1]:
			dc.FillSolidRect(rc,win32mu.RGB(entry[1]))
		elif cmd == 'image':
			imgid = entry[1]
			fit = entry[2]
			wi, hi, bpp = gear32sd.image_dimensions_get(imgid)
			wi, hi = wnd.LPtoDP((wi, hi))
			if fit=='fill':
				gear32sd.device_rect_set(imgid, ltrb)
			elif fit=='meet':
				lp, tp, rp, bp = gear32sd.display_adjust_aspect(imgid, ltrb, gear32sd.IG_ASPECT_DEFAULT)
				gear32sd.device_rect_set(imgid,(x,y,x+rp-lp,y+bp-tp))
			elif fit=='hidden':
				gear32sd.device_rect_set(imgid,(x,y,x+wi,y+hi))
			elif fit=='slice':
				wr = w/float(wi)
				hr = h/float(hi)
				if wr>hr: r = wr
				else: r = hr
				wp, hp = int(wi*r+0.5), int(hi*r+0.5)
				lp, tp, rp, bp = gear32sd.display_adjust_aspect(imgid, (x,y,x+wp,y+hp), gear32sd.IG_ASPECT_DEFAULT)
				gear32sd.device_rect_set(imgid,(x,y,x+rp-lp,y+bp-tp))
			elif fit=='scroll':
				gear32sd.device_rect_set(imgid,(x,y,x+wi,y+hi))
			gear32sd.display_desktop_pattern_set(imgid,0)
			gear32sd.display_image(imgid,dc.GetSafeHdc())
		elif cmd == 'label':
			str = entry[1]
			dc.SetBkMode(win32con.TRANSPARENT)
			dc.DrawText(str, ltrb, win32con.DT_SINGLELINE | win32con.DT_CENTER | win32con.DT_VCENTER)
		else:
			_DisplayList._do_render(self, entry, dc, region)

	scale2fit = {1:'hidden',0:'meet',-1:'slice',-2:'scroll',-3:'fill'}
	def newimage(self, filename, fit='hidden'):
		if self._rendered:
			raise error, 'displaylist already rendered'

		if type(fit) != type('') and _ResizeableDisplayList.scale2fit.has_key(fit):
			fit = _ResizeableDisplayList.scale2fit[fit]
		if fit not in _ResizeableDisplayList.scale2fit.values():
			raise error, 'invalid fit attribute'

		try:
			imgid = win32ig.load(filename)
		except:
			print 'failed to load', filename
			return
		self._list.append(('image', imgid, fit))

	def newlabel(self, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append(('label', str))
