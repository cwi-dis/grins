__version__ = "$Id$"

import Xlib
from XConstants import *
from XTopLevel import toplevel

class _Button:
	def __init__(self, dispobj, coordinates, z = 0):
		self._dispobj = dispobj
		self._z = z
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
		self._corners = x, y, x + w, y + h
		self._color = self._hicolor = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		self._newdispobj = None
		self._highlighted = 0
		x, y, w, h = window._convert_coordinates(coordinates)
		dispobj._buttonregion.UnionRectWithRegion(x, y, w, h)
		if self._color == dispobj._bgcolor:
			return
		dispobj.drawbox(coordinates)

	def close(self):
		if self._dispobj is None:
			return
		self._dispobj._buttons.remove(self)
		self._dispobj = None
		if self._newdispobj:
			self._newdispobj.close()
			self._newdispobj = None

	def is_closed(self):
		return self._dispobj is None

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, color):
		self._hicolor = color

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

	def _inside(self, x, y):
		# return 1 iff the given coordinates fall within the button
		if (self._corners[0] <= x <= self._corners[2]) and \
			  (self._corners[1] <= y <= self._corners[3]):
			return TRUE
		else:
			return FALSE
