
from appcon import *
from WMEVENTS import *

import win32mu

from win32ig import win32ig
from win32displaylist import _DisplayList

# for global toplevel 
import __main__

# base class for subwindows
# defines the interface of subwindows
# implements the platform independent part of subwindows 
class Window:
	def __init__(self, parent, coordinates, units, z=0, transparent=0):
		self.__setparent(parent)
		self.__setcoordinates(coordinates, units)
		self.__set_z_order(z)
		self.__settransparent(transparent)
		self._subwindows = []
		self._displists = []
		self._active_displist = None
		self._redrawfunc = None
		self._callbacks = {}
		self._showing = None
		
	def __repr__(self):
		return '<Window instance at %x>' % id(self)

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	def bgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b

	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)

	def setredrawfunc(self, func):
		if func is None or callable(func):
			self._redrawfunc = func
		else:
			raise error, 'invalid function'

	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in (ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release):
			self._callbacks[event] = func, arg

	def unregister(self, event):
		try:
			del self._callbacks[event]
		except KeyError:
			pass

	# bring the subwindow infront of windows with the same z	
	def pop(self, poptop=1):
		# if poptop:
		#	self._topwindow.do_activate()
		parent = self._parent
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

	def dontshowwindow(self):
		if self._showing:
			self._showing = None

	def show(self):
		pass

	def hide(self):
		pass

	def setcursor(self, cursor):
		self._cursor = cursor

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return Window(self, coordinates, units, z, transparent)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return self.newwindow(coordinates, pixmap, transparent, z, type_channel, units)

	# return the coordinates of this window in units
	def getgeometry(self, units = UNIT_SCREEN):
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
	def _pxl2rel(self,coordinates,ref_rect=None):
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
		self.imgAddDocRef(file)
		return xsize, ysize

	# Prepare an image for display (load,crop,scale, etc)
	def _prepare_image(self, file, crop, scale, center, coordinates, clip):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes
		
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
			x, y, width, height = self._convert_coordinates(coordinates,self._canvas)
		# compute scale taking into account the hint (0,-1)
		if scale == 0:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -1:
			scale = max(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -2:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
			if scale > 1:
				scale = 1

		# scale crop sizes
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)

		image = __main__.toplevel._image_cache[file]
		mask=None
		w=xsize
		h=ysize
		if scale != 1:
			w = int(xsize * scale + .5)
			h = int(ysize * scale + .5)

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
		# image, mask
		# left,top  of crop rect
		# x,y left-top of display rect
		# w_img,h_img crop rect of  width and height
		# rcKeep  image keep unscaled rectangle

		return image, mask, left, top, x, y,\
			w - left - right, h - top - bottom,rcKeep

	# XXX: to be removed
	def imgAddDocRef(self,file):
		toplevel=__main__.toplevel
		w=self._topwindow
		frame=(w.GetParent()).GetMDIFrame()		
		doc = frame._cmifdoc
		if doc==None: doc="__Unknown"
		if toplevel._image_docmap.has_key(doc):
			if file not in toplevel._image_docmap[doc]:
				toplevel._image_docmap[doc].append(file)
		else:
			toplevel._image_docmap[doc]=[file,]

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

	def getwindowpos(self):
		X, Y, W, H = self._parent.getwindowpos()
		x, y, w, h = self._rectb
		return X+x, Y+y, w, h

	#
	# Private methods
	#
	def __setparent(self, parent):
		self._parent = parent
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor
		self._topwindow = parent._topwindow
		self._convert_color = parent._convert_color

	# update related coordinates members in a consistent way
	def __setcoordinates(self, coordinates, units):
		x, y, w, h = self._parent._convert_coordinates(coordinates,
					crop = 1, units = units)
		self._rect = 0, 0, w, h # client area in pixels
		self._canvas = 0, 0, w, h # client canvas in pixels
		self._rectb = x, y, w, h  # rect with respect to parent in pixels
		self._sizes = self._parent._pxl2rel(self._rectb) # rect relative to parent
		self._units = units

	# insert this window in parent._subwindows list at the correct z-order
	def __set_z_order(self, z):
		self._z = z
		parent = self._parent
		for i in range(len(parent._subwindows)):
			if self._z > parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)

	def __settransparent(self, transparent):
		parent = self._parent
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			if transparent not in (-1, 0, 1):
				raise error, 'invalid value for transparent arg'
			self._transparent = transparent


	#
	# Animations interface
	#
	def updatecoordinates(self, coordinates, units=UNIT_SCREEN):
		pass

	def updatezindex(self, z):
		pass

	def updatebgcolor(self, color):
		pass

	#
	# Transitions interface
	#
	def begintransition(self, inout, runit, dict):
		pass

	def endtransition(self):
		pass

	def changed(self):
		pass
		
	def settransitionvalue(self, value):
		pass
		
	def freeze_content(self, how):
		pass



########################################

# regions, 
import win32ui, win32con

import win32transitions

class SubWindow(Window):
	def __init__(self, parent, coordinates, transparent, z, units):
		Window.__init__(self, parent, coordinates, units, z, transparent)
		self._oswnd = None
		self.__init_transitions()

	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)
		
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return SubWindow(self, coordinates, transparent, z, units)

	def paintOn(self, dc, offsetOrg=1):
		# first paint opaque subwindows
		trsubwindows = []
		for w in self._subwindows:
			if w._transparent == 0 or \
			   (w._transparent == -1 and
			    w._active_displist):
				w.paintOn(dc)
			else:
				trsubwindows.append(w)
		
		# then paint self
		x, y, w, h = self.getwindowpos()
		if offsetOrg:
			x0, y0 = dc.SetWindowOrg((-x,-y))
		if self._active_displist:
			self._active_displist._render(dc,None)
		if self._redrawfunc:
			self._redrawfunc()
		if offsetOrg:
			dc.SetWindowOrg((x0,y0))

		# then paint transparent children
		trsubwindows.reverse()
		for w in trsubwindows:
			w.paintOn(dc)

		if self._showing:
			self.__showwindowOn(dc, self._showing)
		
		# debug:
		#self.__showwindowOn(dc, (255,0,0))

	def showwindow(self, color = (255,0,0)):
		dc=self._topwindow.GetDC()
		self.__showwindowOn(dc, color)
		self._topwindow.ReleaseDC(dc)

	def __showwindowOn(self, dc, color):
		self._showing = color
		x, y, w, h = self.getwindowpos()
		rc = (x, y, x+w, y+h)
		win32mu.FrameRect(dc,rc,self._showing)

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
		
	def Invalidate(self):
		x, y, w, h = self.getwindowpos()
		self._topwindow.InvalidateRect((x, y, x+w, y+h))			

	#
	# Animations interface
	#
	def updatecoordinates(self, coordinates, units=UNIT_SCREEN):
		# first convert any coordinates to pixel
		coordinates = self._convert_coordinates(coordinates,units=units)
		
		# keep old pos
		x0, y0, w0, h0 = self._rectb
		x1, y1 = self.getwindowpos()[:2]
		
		# move or/and resize window
		if len(coordinates)==2:
			x, y = coordinates[:2]
			w, h = w0, h0
		elif len(coordinates)==4:
			x, y, w, h = coordinates
		else:
			raise AssertionError

		# create new
		self._rect = 0, 0, w, h # client area in pixels
		self._canvas = 0, 0, w, h # client canvas in pixels
		self._rectb = x, y, w, h  # rect with respect to parent in pixels
		self._sizes = self._parent._pxl2rel(self._rectb) # rect relative to parent
		x2, y2 = self.getwindowpos()[:2]
		
		# update
		rgn1 = win32ui.CreateRgn()
		rgn1.CreateRectRgn((x1, y1, x1+w0, y1+h0))
		rgn2 = win32ui.CreateRgn()
		rgn2.CreateRectRgn((x2, y2, x2+w, y2+h))				
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((0, 0, 0, 0))
		rgn.CombineRgn(rgn1,rgn2,win32con.RGN_OR)
		flags = win32con.RDW_INVALIDATE | win32con.RDW_UPDATENOW | win32con.RDW_ERASE
		self._topwindow.RedrawWindow(None, rgn, flags)
		rgn1.DeleteObject()
		rgn2.DeleteObject()
		rgn.DeleteObject()

	def updatezindex(self, z):
		self._z = z
		parent = self._parent
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)):
			if self._z > parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)
		self.__invalidate()
	
	def updatebgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b
		if self._active_displist:
			self._active_displist.updatebgcolor(color)
			rgn1 = win32ui.CreateRgn()
			rgn1.CreateRectRgn(self.GetClientRect())			
			rgn2 = self._active_displist._win32rgn
			rgn  = win32ui.CreateRgn()
			rgn.CreateRectRgn((0,0,0,0))
			rgn.CombineRgn(rgn1,rgn2,win32con.RGN_DIFF)
			x, y, w, h = self.getwindowpos()
			rgn.OffsetRgn((x, y))
			flags = win32con.RDW_INVALIDATE | win32con.RDW_UPDATENOW # | RDW_ERASE
			self._topwindow.RedrawWindow(None, rgn, flags)			
			rgn1.DeleteObject()
			rgn.DeleteObject()

	#
	# Transitions interface
	#
	def __init_transitions(self):
		self._transition = None
		self._fromMemDC = None
		self._toMemDC = None

	def begintransition(self, inout, runit, dict):
		self._toMemDC = MemDC(self)
		factory = win32transitions.TransitionFactory(dict, self._fromMemDC, self._toMemDC)
		transinst = factory.getTransition()
		print transinst
		self._transition = win32transitions.TransitionEngine(transinst, dict)
		if runit:
			self._transition.begintransition()

	def endtransition(self):
		if self._transition:
			self._transition.endtransition()
			self._transition = None

	def changed(self):
		pass
		
	def settransitionvalue(self, value):
		if self._transition:
			self._transition.settransitionvalue(value)
		
	def freeze_content(self, how):
		# how is 'transition', 'hold' or None. Freeze the bits in the window
		# (unless how=None, which unfreezes them) and use for updates and as passive
		# source for next transition.
		print 'freeze_content',how
		if how:
			self._fromMemDC = MemDC(self)

	def close(self):
		Window.close(self)


# offscreen pixmap class
class MemDC:
	def __init__(self, wnd):
		self._wnd = wnd
		dc = wnd._topwindow.GetDC()
		dcc=dc.CreateCompatibleDC()
		bmp=win32ui.CreateBitmap()
		x, y, w, h = wnd.getwindowpos()
		bmp.CreateCompatibleBitmap(dc,w,h)
		dcc.SelectObject(bmp)
		wnd._topwindow.ReleaseDC(dc)
		self._dc = dcc
		self._bmp = bmp
		self.capture()

	def __del__(self):
		try: self._dc.DeleteDC()
		except:pass
		del self._bmp

	def __getattr__(self, attr):	
		try:	
			if attr != '__dict__':
				o = self.__dict__['_dc']
				if o:
					return getattr(o, attr)
		except KeyError:
			pass
		raise AttributeError, attr

	def capture(self):
		self._wnd.paintOn(self._dc, 0)

	def render(self):
		dc = self._wnd._topwindow.GetDC()
		x, y, w, h = self._wnd.getwindowpos()
		dc.BitBlt((x,y),(w,h),self._dc,(0, 0), win32con.SRCCOPY)
		self._wnd._topwindow.ReleaseDC(dc)



		 