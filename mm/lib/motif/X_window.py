__version__ = "$Id$"

import X_windowbase
from X_windowbase import TRUE, FALSE, SINGLE, UNIT_MM

from types import *
import math

[_X, _Y, _WIDTH, _HEIGHT] = range(4)
_def_useGadget = 1

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""
_rb_done = '_rb_done'			# exception to stop create_box loop
_in_create_box = None

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

class _Toplevel(X_windowbase._Toplevel):
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = None, units = UNIT_MM,
		      menubar = None):
## 		if pixmap is None:
## 			pixmap = toplevel._depth <= 8
		return _Window(self, x, y, w, h, title, 0, pixmap, units, menubar)

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE,
			type_channel = SINGLE, pixmap = None, units = UNIT_MM,
			menubar = None):
## 		if pixmap is None:
## 			pixmap = toplevel._depth <= 8
		return _Window(self, x, y, w, h, title, 1, pixmap, units, menubar)

	def getsize(self):
		return toplevel._mscreenwidth, toplevel._mscreenheight

class _Window(X_windowbase._Window):
	def __init__(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
		     units = UNIT_MM, menubar = None):
		X_windowbase._Window.__init__(self, parent, x, y, w, h, title,
					      defcmap, pixmap, units, menubar)
		self.arrowcache = {}
		self._next_create_box = []

	def close(self):
		self.arrowcache = {}
		X_windowbase._Window.close(self)

	def newdisplaylist(self, *bgcolor):
		if bgcolor != ():
			bgcolor = bgcolor[0]
		else:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)

	def create_box(self, msg, callback, box = None):
		import Xcursorfont
		global _in_create_box
		if _in_create_box:
			_in_create_box._next_create_box.append((self, msg, callback, box))
			return
		if self.is_closed():
			apply(callback, ())
			return
		_in_create_box = self
		self.pop()
		if msg:
			msg = msg + '\n\n' + _rb_message
		else:
			msg = _rb_message
		self._rb_dl = self._active_displist
		if self._rb_dl:
			d = self._rb_dl.clone()
		else:
			d = self.newdisplaylist()
		self._rb_transparent = []
		sw = self._subwindows[:]
		sw.reverse()
		r = Xlib.CreateRegion()
		for win in sw:
			if not win._transparent:
				# should do this recursively...
				self._rb_transparent.append(win)
				win._transparent = 1
				d.drawfbox(win._bgcolor, win._sizes)
				apply(r.UnionRectWithRegion, win._rect)
		for win in sw:
			b = win._sizes
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self._rb_display = d.clone()
		d.fgcolor((255, 0, 0))
		if box:
			d.drawbox(box)
		if self._rb_transparent:
			self._mkclip()
			self._do_expose(r)
			self._rb_reg = r
		d.render()
		self._rb_curdisp = d
		self._rb_dialog = showmessage(
			msg, mtype = 'message', grab = 0,
			callback = (self._rb_done, ()),
			cancelCallback = (self._rb_cancel, ()))
		self._rb_callback = callback
		form = self._form
		form.AddEventHandler(X.ButtonPressMask, FALSE,
				     self._start_rb, None)
		form.AddEventHandler(X.ButtonMotionMask, FALSE,
				     self._do_rb, None)
		form.AddEventHandler(X.ButtonReleaseMask, FALSE,
				     self._end_rb, None)
		cursor = form.Display().CreateFontCursor(Xcursorfont.crosshair)
		form.GrabButton(X.AnyButton, X.AnyModifier, TRUE,
				X.ButtonPressMask | X.ButtonMotionMask
					| X.ButtonReleaseMask,
				X.GrabModeAsync, X.GrabModeAsync, form, cursor)
		v = form.GetValues(['foreground', 'background'])
		v['foreground'] = v['foreground'] ^ v['background']
		v['function'] = X.GXxor
		v['line_style'] = X.LineOnOffDash
		self._gc_rb = form.GetGC(v)
		self._rb_box = box
		if box:
			x, y, w, h = self._convert_coordinates(box)
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			self._rb_box = x, y, w, h
			self._rb_start_x = x
			self._rb_start_y = y
			self._rb_width = w
			self._rb_height = h
		else:
			self._rb_start_x, self._rb_start_y, self._rb_width, \
					  self._rb_height = self._rect
		try:
			Xt.MainLoop()
		except _rb_done:
			pass

	def hitarrow(self, point, src, dst):
		# return 1 iff (x,y) is within the arrow head
		sx, sy = self._convert_coordinates(src)
		dx, dy = self._convert_coordinates(dst)
		x, y = self._convert_coordinates(point)
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
			return FALSE
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return FALSE
		return TRUE

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, 0, pixmap, transparent, z)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, 1, pixmap, transparent, z)

	# have to override these for create_box
	def _input_callback(self, form, client_data, call_data):
		if _in_create_box:
			return
		X_windowbase._Window._input_callback(self, form, client_data,
						     call_data)

	def _resize_callback(self, form, client_data, call_data):
		self.arrowcache = {}
		w = _in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			try:
				w._rb_cancel()
			except _rb_done:
				pass
			w._next_create_box[0:0] = next_create_box
		X_windowbase._Window._resize_callback(self, form, client_data,
						      call_data)
		if w:
			w._rb_end()
			raise _rb_done

	def _delete_callback(self, form, client_data, call_data):
		self.arrowcache = {}
		w = _in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			try:
				w._rb_cancel()
			except _rb_done:
				pass
			w._next_create_box[0:0] = next_create_box
		X_windowbase._Window._delete_callback(self, form, client_data,
						      call_data)
		if w:
			w._rb_end()
			raise _rb_done

	# supporting methods for create_box
	def _rb_finish(self):
		global _in_create_box
		_in_create_box = None
		if self._rb_transparent:
			for win in self._rb_transparent:
				win._transparent = 0
			self._mkclip()
			self._do_expose(self._rb_reg)
			del self._rb_reg
		del self._rb_transparent
		form = self._form
		form.RemoveEventHandler(X.ButtonPressMask, FALSE,
					self._start_rb, None)
		form.RemoveEventHandler(X.ButtonMotionMask, FALSE,
					self._do_rb, None)
		form.RemoveEventHandler(X.ButtonReleaseMask, FALSE,
					self._end_rb, None)
		form.UngrabButton(X.AnyButton, X.AnyModifier)
		self._rb_dialog.close()
		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		self._rb_display.close()
		self._rb_curdisp.close()
		del self._rb_callback
		del self._rb_dialog
		del self._rb_dl
		del self._rb_display
		del self._gc_rb

	def _rb_cvbox(self):
		x0 = self._rb_start_x
		y0 = self._rb_start_y
		x1 = x0 + self._rb_width
		y1 = y0 + self._rb_height
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, width, height = self._rect
		if x0 < x: x0 = x
		if x0 >= x + width: x0 = x + width - 1
		if x1 < x: x1 = x
		if x1 >= x + width: x1 = x + width - 1
		if y0 < y: y0 = y
		if y0 >= y + height: y0 = y + height - 1
		if y1 < y: y1 = y
		if y1 >= y + height: y1 = y + height - 1
		return float(x0 - x) / (width - 1), \
		       float(y0 - y) / (height - 1), \
		       float(x1 - x0) / (width - 1), \
		       float(y1 - y0) / (height - 1)

	def _rb_done(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, self._rb_cvbox())
		self._rb_end()
		raise _rb_done

	def _rb_cancel(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())
		self._rb_end()
		raise _rb_done

	def _rb_end(self):
		# execute pending create_box calls
		next_create_box = self._next_create_box
		self._next_create_box = []
		for win, msg, cb, box in next_create_box:
			win.create_box(msg, cb, box)

	def _rb_draw(self):
		x = self._rb_start_x
		y = self._rb_start_y
		w = self._rb_width
		h = self._rb_height
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		self._gc_rb.DrawRectangle(x, y, w, h)

	def _rb_constrain(self, event):
		x, y, w, h = self._rect
		if event.x < x:
			event.x = x
		if event.x >= x + w:
			event.x = x + w - 1
		if event.y < y:
			event.y = y
		if event.y >= y + h:
			event.y = y + h - 1

	def _rb_common(self, event):
		if not hasattr(self, '_rb_cx'):
			self._start_rb(None, None, event)
		self._rb_draw()
		self._rb_constrain(event)
		if self._rb_cx and self._rb_cy:
			x, y, w, h = self._rect
			dx = event.x - self._rb_last_x
			dy = event.y - self._rb_last_y
			self._rb_last_x = event.x
			self._rb_last_y = event.y
			self._rb_start_x = self._rb_start_x + dx
			if self._rb_start_x + self._rb_width > x + w:
				self._rb_start_x = x + w - self._rb_width
			if self._rb_start_x < x:
				self._rb_start_x = x
			self._rb_start_y = self._rb_start_y + dy
			if self._rb_start_y + self._rb_height > y + h:
				self._rb_start_y = y + h - self._rb_height
			if self._rb_start_y < y:
				self._rb_start_y = y
		else:
			if not self._rb_cx:
				self._rb_width = event.x - self._rb_start_x
			if not self._rb_cy:
				self._rb_height = event.y - self._rb_start_y
		self._rb_box = 1

	def _start_rb(self, w, data, event):
		# called on mouse press
		self._rb_display.render()
		self._rb_curdisp.close()
		self._rb_constrain(event)
		if self._rb_box:
			x = self._rb_start_x
			y = self._rb_start_y
			w = self._rb_width
			h = self._rb_height
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			if