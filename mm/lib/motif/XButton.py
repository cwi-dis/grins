__version__ = "$Id$"

import Xlib
from XConstants import error, TRUE, FALSE
from XTopLevel import toplevel

#class _Button:
#	def __init__(self, dispobj, coordinates, z = 0, times = None):
#		self._dispobj = dispobj
#		self._z = z
#		self._times = times
#		buttons = dispobj._buttons
#		for i in range(len(buttons)):
#			if buttons[i]._z <= z:
#				buttons.insert(i, self)
#				break
#		else:
#			buttons.append(self)
#		window = dispobj._window
#		self._coordinates = coordinates
#		x, y, w, h = coordinates
#		self._corners = x, y, x + w, y + h
#		self._color = self._hicolor = dispobj._fgcolor
#		self._width = self._hiwidth = dispobj._linewidth
#		self._newdispobj = None
#		self._highlighted = 0
#		x, y, w, h = window._convert_coordinates(coordinates)
#		dispobj._buttonregion.UnionRectWithRegion(x, y, w, h)
#		if self._color == dispobj._bgcolor:
#			return
#		dispobj.drawbox(coordinates)

#	def close(self):
#		if self._dispobj is None:
#			return
#		self._dispobj._buttons.remove(self)
#		self._dispobj = None
#		if self._newdispobj:
#			self._newdispobj.close()
#			self._newdispobj = None

#	def is_closed(self):
#		return self._dispobj is None

#	def hiwidth(self, width):
#		self._hiwidth = width

#	def hicolor(self, color):
#		self._hicolor = color

#	def highlight(self):
#		dispobj = self._dispobj
#		if dispobj is None:
#			return
#		window = dispobj._window
#		if window._active_displist is not dispobj:
#			raise error, 'can only highlight rendered button'
#		# if button color and highlight color are all equal to
#		# the background color then don't draw the box (and
#		# don't highlight).
#		if self._color == dispobj._bgcolor and \
#		   self._hicolor == dispobj._bgcolor:
#			return
#		self._highlighted = 1
#		self._do_highlight()
#		if window._pixmap is not None:
#			x, y, w, h = window._rect
#			window._pixmap.CopyArea(window._form, window._gc,
#						x, y, w, h, x, y)
#		toplevel._main.UpdateDisplay()

#	def _do_highlight(self):
#		window = self._dispobj._window
#		gc = window._gc
#		gc.foreground = window._convert_color(self._hicolor)
#		gc.line_width = self._hiwidth
#		gc.SetRegion(window._clip)
#		apply(gc.DrawRectangle, window._convert_coordinates(self._coordinates))

#	def unhighlight(self):
#		dispobj = self._dispobj
#		if dispobj is None:
#			return
#		window = dispobj._window
#		if window._active_displist is not dispobj:
#			return
#		if not self._highlighted:
#			return
#		self._highlighted = 0
#		# calculate region to redisplay
#		x, y, w, h = window._convert_coordinates(self._coordinates)
#		lw = self._hiwidth / 2
#		r = Xlib.CreateRegion()
#		r.UnionRectWithRegion(x - lw, y - lw,
#				      w + 2*lw + 1, h + 2*lw + 1)
#		r1 = Xlib.CreateRegion()
#		r1.UnionRectWithRegion(x + lw + 1, y + lw + 1,
#				       w - 2*lw - 1, h - 2*lw - 1)
#		r.SubtractRegion(r1)
#		window._do_expose(r)
#		if window._pixmap is not None:
#			x, y, w, h = window._rect
#			window._pixmap.CopyArea(window._form, window._gc,
#						x, y, w, h, x, y)
#		toplevel._main.UpdateDisplay()

#	def _inside(self, x, y):
#		# return 1 iff the given coordinates fall within the button
#		bx0, by0, bx1, by1 = self._corners
#		if bx0 <= x < bx1 and by0 <= y < by1:
#			if self._times:
#				import time
#				curtime = time.time() - self._dispobj.starttime
#				t0, t1 = self._times
#				if (not t0 or t0 <= curtime) and \
#				   (not t1 or curtime < t1):
#					return 1
#				return 0
#			return 1
#		return 0

#	######################################
#	# Animation experimental methods

#	def updatecoordinates(self, coords):
#		print 'button.updatecoords',coords

#	# End of animation experimental methods
#	##########################################

class _Button:
	def __init__(self, dispobj, coordinates, z=0, times=None):
		self._coordinates = coordinates
		self._dispobj = dispobj
		self._z = z
		self._times = times
		buttons = dispobj._buttons
		for i in range(len(buttons)):
			if buttons[i]._z <= z:
				buttons.insert(i, self)
				break
		else:
			buttons.append(self)
		window = dispobj._window
		self._coordinates = coordinates
		x, y, w, h = coordinates
		self._color = self._hicolor = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		self._newdispobj = None
		self._highlighted = 0

	# Destroy button
	def close(self):
		if self._dispobj is None:
			return
		self._dispobj._buttons.remove(self)
		self._dispobj = None
		if self._newdispobj:
			self._newdispobj.close()
			self._newdispobj = None

	# Returns true if it is closed
	def is_closed(self):
		return self._dispobj is None

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, color):
		self._hicolor = color

	# Highlight box
	def highlight(self):
		pass
		
	# Unhighlight box
	def unhighlight(self):
		pass
		
	def _do_highlight(self):
		pass

	# Returns true if the time is inside the temporal space
	def _inside(self):
		if self._times:
			import time
			curtime = time.time() - self._dispobj.starttime
			t0, t1 = self._times
			if (not t0 or t0 <= curtime) and \
			   (not t1 or curtime < t1):
				return 1
			return 0
		return 1
		
	def _get_button_region(self):
		"""Return our region, in global coordinates, if we are active"""
##		print 'getbuttonregion', self._dispobj._window._convert_coordinates(self._coordinates), self._times, time.time()-self._dispobj.starttime #DBG
		if self._times:
			curtime = time.time() - self._dispobj.starttime
			# Workaround for the fact that timers seem to fire early, some times:
			curtime = curtime + 0.05
			t0, t1 = self._times
			if curtime < t0 or (t1 and curtime >= t1):
				return None
		x0, y0, w, h = self._dispobj._window._convert_coordinates(self._coordinates)
		x1, y1 = x0+w, y0+h
		x0, y0 = Qd.LocalToGlobal((x0, y0))
		x1, y1 = Qd.LocalToGlobal((x1, y1))
		box = x0, y0, x1, y1
		rgn = Qd.NewRgn()
		Qd.RectRgn(rgn, box)
		return rgn
		
	######################################
	# Animation experimental methods

	def updatecoordinates(self, coords):
		print 'button.updatecoords',coords

	# End of animation experimental methods
	##########################################

class _ButtonRect(_Button):
	def __init__(self, dispobj, coordinates, z=0, times=None):
		_Button.__init__(self, dispobj, coordinates, z=0, times=None)
		if self._color == dispobj._bgcolor:
			return
		x, y, w, h = window._convert_coordinates(coordinates)
		dispobj._buttonregion.UnionRectWithRegion(x, y, w, h)
		if self._color == dispobj._bgcolor:
			return
		dispobj.drawbox(coordinates)

	def highlight(self):
		dispobj = self._dispobj
		if dispobj is None:
			return
		window = dispobj._window
		if window._active_displist is not dispobj:
			raise error, 'can only highlight rendered button'
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		self._highlighted = 1
		self._do_highlight()
		if window._pixmap is not None:
			x, y, w, h = window._rect
			window._pixmap.CopyArea(window._form, window._gc,
						x, y, w, h, x, y)
		toplevel._main.UpdateDisplay()

	def _do_highlight(self):
		window = self._dispobj._window
		gc = window._gc
		gc.foreground = window._convert_color(self._hicolor)
		gc.line_width = self._hiwidth
		gc.SetRegion(window._clip)
		apply(gc.DrawRectangle, window._convert_coordinates(self._coordinates))

	def unhighlight(self):
		dispobj = self._dispobj
		if dispobj is None:
			return
		window = dispobj._window
		if window._active_displist is not dispobj:
			return
		if not self._highlighted:
			return
		self._highlighted = 0
		# calculate region to redisplay
		x, y, w, h = window._convert_coordinates(self._coordinates)
		lw = self._hiwidth / 2
		r = Xlib.CreateRegion()
		r.UnionRectWithRegion(x - lw, y - lw,
				      w + 2*lw + 1, h + 2*lw + 1)
		r1 = Xlib.CreateRegion()
		r1.UnionRectWithRegion(x + lw + 1, y + lw + 1,
				       w - 2*lw - 1, h - 2*lw - 1)
		r.SubtractRegion(r1)
		window._do_expose(r)
		if window._pixmap is not None:
			x, y, w, h = window._rect
			window._pixmap.CopyArea(window._form, window._gc,
						x, y, w, h, x, y)
		toplevel._main.UpdateDisplay()

	# Returns true if the point is inside the box	
	def _inside(self, x, y):
		# for now
		import CheckInsideArea
		type, bx1, by1, bx2, by2 = self._coordinates
		if CheckInsideArea.insideRect(x, y, bx1, by1, bx2, by2) and \
			_Button._inside(self):
				return 1
		return 0

class _ButtonPoly(_Button):
	def __init__(self, dispobj, coordinates, z=0, times=None):
		_Button.__init__(self, dispobj, coordinates, z=0, times=None)
		
	# Returns true if the point is inside the box	
	# Warning: this method is called by the window core management every time that you move the mouse
	# in order to change to graphic cursor mouse when the cursor is inside the area. And for each
	# area that you have defined in window.
	# For now, a not very efficient algo is implemented, but it should be better to use a system
	# call later if possible
	def _inside(self, x, y):
		import CheckInsideArea
		if CheckInsideArea.insidePoly(x, y, self._coordinates[1:]) and \
			_Button._inside(self):
				return 1
		return 0


class _ButtonCircle(_Button):
	def __init__(self, dispobj, coordinates, z=0, times=None):
		_Button.__init__(self, dispobj, coordinates, z=0, times=None)
		
	# Returns true if the point is inside the box	
	def _inside(self, x, y):
		# for now
		import CheckInsideArea
		type, cx, cy, rd = self._coordinates
		wx, wy, ww, wh = self._dispobj._window.getgeometry(UNIT_PXL)
		if CheckInsideArea.insideCircle(x*ww, y*wh, cx*ww, cy*wh, rd*ww) and \
			_Button._inside(self):
				return 1
		return 0

class _ButtonElipse(_Button):
	def __init__(self, dispobj, coordinates, z=0, times=None):
		_Button.__init__(self, dispobj, coordinates, z=0, times=None)
		
	# Warning: this method is called by the window core management every time that you move the mouse
	# in order to change to graphic cursor mouse when the cursor is inside the area. And for each
	# area that you have defined in window.
	# For now, a not very efficient algo is implemented, but it should be better to use a system
	# call later if possible
	# Returns true if the point is inside the elipse	
	def _inside(self, x, y):
		# for now
		import CheckInsideArea
		type, cx, cy, rdx, rdy = self._coordinates
		wx, wy, ww, wh = self._dispobj._window.getgeometry(UNIT_PXL)
		if CheckInsideArea.insideElipse(x*ww, y*wh, cx*ww, cy*wh, rdx*ww, rdy*wh) and \
			_Button._inside(self):
				return 1
		return 0



