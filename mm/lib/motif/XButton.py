__version__ = "$Id$"

import Xlib
from XConstants import error, TRUE, FALSE
from XTopLevel import toplevel

class _Button:
	def __init__(self, dispobj, coordinates, z, times, sensitive):
		self._coordinates = coordinates
		self._dispobj = dispobj
		self._z = z
		self._times = times
		self._sensitive = sensitive
		buttons = dispobj._buttons
		for i in range(len(buttons)):
			if buttons[i]._z <= z:
				buttons.insert(i, self)
				break
		else:
			buttons.append(self)
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

	def setsensitive(self, sensitive):
		self._sensitive = sensitive

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
		if not self._sensitive:
			return 0
		if self._times:
			import time
			curtime = time.time() - self._dispobj.starttime
			t0, t1 = self._times
			if (not t0 or t0 <= curtime) and \
			   (not t1 or curtime < t1):
				return 1
			return 0
		return 1
		
	######################################
	# Animation experimental methods

	def updatecoordinates(self, coords):
		print 'button.updatecoords',coords

	# End of animation experimental methods
	##########################################

class _ButtonRect(_Button):
	def __init__(self, dispobj, coordinates, z, times, sensitive):
		_Button.__init__(self, dispobj, coordinates, z, times, sensitive)
		x, y = coordinates[1:3]
		w = coordinates[3] - x
		h = coordinates[4] - y
		x, y, w, h = dispobj._window._convert_coordinates((x, y, w, h))
		dispobj._buttonregion.UnionRectWithRegion(x, y, w, h)
		if self._color == dispobj._bgcolor or self._color is None:
			return
		dispobj.drawbox((coordinates[1], coordinates[2],
				 coordinates[3]-coordinates[1],
				 coordinates[4]-coordinates[2]))

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
		if self._hicolor is None:
			return
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
		gc.SetRegion(window._getmyarea())
		x, y = self._coordinates[1:3]
		w = self._coordinates[3] - x
		h = self._coordinates[4] - y
		x, y, w, h = window._convert_coordinates((x, y, w, h))
		apply(gc.DrawRectangle, (x, y, w, h))

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
		x, y = self._coordinates[1:3]
		w = self._coordinates[3] - x
		h = self._coordinates[4] - y
		x, y, w, h = window._convert_coordinates((x, y, w, h))
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
		if not self._sensitive:
			return 0
		import CheckInsideArea
		type, bx1, by1, bx2, by2 = self._coordinates
		if CheckInsideArea.insideRect(x, y, bx1, by1, bx2, by2) and \
			_Button._inside(self):
				return 1
		return 0

class _ButtonPoly(_Button):
	def __init__(self, dispobj, coordinates, z, times, sensitive):
		_Button.__init__(self, dispobj, coordinates, z, times, sensitive)
		
	# Returns true if the point is inside the box	
	# Warning: this method is called by the window core management every time that you move the mouse
	# in order to change to graphic cursor mouse when the cursor is inside the area. And for each
	# area that you have defined in window.
	# For now, a not very efficient algo is implemented, but it should be better to use a system
	# call later if possible
	def _inside(self, x, y):
		if not self._sensitive:
			return 0
		import CheckInsideArea
		if CheckInsideArea.insidePoly(x, y, self._coordinates[1:]) and \
			_Button._inside(self):
				return 1
		return 0


class _ButtonCircle(_Button):
	def __init__(self, dispobj, coordinates, z, times, sensitive):
		_Button.__init__(self, dispobj, coordinates, z, times, sensitive)
		
	# Returns true if the point is inside the box	
	def _inside(self, x, y):
		if not self._sensitive:
			return 0
		# for now
		import CheckInsideArea
		type, cx, cy, rd = self._coordinates
		wx, wy, ww, wh = self._dispobj._window.getgeometry(UNIT_PXL)
		if CheckInsideArea.insideCircle(x*ww, y*wh, cx*ww, cy*wh, rd*ww) and \
			_Button._inside(self):
				return 1
		return 0

class _ButtonEllipse(_Button):
	def __init__(self, dispobj, coordinates, z, times, sensitive):
		_Button.__init__(self, dispobj, coordinates, z, times, sensitive)
		
	# Warning: this method is called by the window core management every time that you move the mouse
	# in order to change to graphic cursor mouse when the cursor is inside the area. And for each
	# area that you have defined in window.
	# For now, a not very efficient algo is implemented, but it should be better to use a system
	# call later if possible
	# Returns true if the point is inside the ellipse	
	def _inside(self, x, y):
		if not self._sensitive:
			return 0
		# for now
		import CheckInsideArea
		type, cx, cy, rdx, rdy = self._coordinates
		wx, wy, ww, wh = self._dispobj._window.getgeometry(UNIT_PXL)
		if CheckInsideArea.insideEllipse(x*ww, y*wh, cx*ww, cy*wh, rdx*ww, rdy*wh) and \
			_Button._inside(self):
				return 1
		return 0



