# rbtk: rb toolkit

# supporting methods for create_box

_rb_done = '_rb_done' # exception to stop create_box loop

_in_create_box = None

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""

import AppMessages

class _rbtk:
	def __init__(self):
		self.box_created = 0     # indicates wheather box has been created or not
		self.box_started = 0     # indicates wheather create_box procedure has begun
		self._next_create_box = []

	def create_box(self, msg, callback, box = None):
		showmessage("Channel coordinates unknown, set to full base window.\nChange in channel view")
		if box == None:
			box = (0, 0, 1, 1)
		apply(callback, box)
##		global _in_create_box
##		if _in_create_box:
##			_in_create_box._next_create_box.append((self, msg, callback, box))
##			return
##		if self.is_closed():
##			apply(callback, ())
##			return
##		_in_create_box = self
##		self.pop()
##		if msg:
##			msg = msg + '\n\n' + _rb_message
##		else:
##			msg = _rb_message
##		self._rb_dl = self._active_displist
##		if self._rb_dl:
##			d = self._rb_dl.clone()
##		else:
##			d = self.newdisplaylist()
##		self._rb_transparent = []
##		sw = self._subwindows[:]
##		sw.reverse()
##		r = Xlib.CreateRegion()
##		for win in sw:
##			if not win._transparent:
##				# should do this recursively...
##				self._rb_transparent.append(win)
##				win._transparent = 1
##				d.drawfbox(win._bgcolor, win._sizes)
##				apply(r.UnionRectWithRegion, win._rect) # XXXX
##		for win in sw:
##			b = win._sizes
##			if b != (0, 0, 1, 1):
##				d.drawbox(b)
##		self._rb_display = d.clone()
##		d.fgcolor((255, 0, 0))
##		if box:
##			d.drawbox(box)
##		if self._rb_transparent:
##			self._mkclip()
##			self._do_expose(r)
##			self._rb_reg = r
##		d.render()
##		self._rb_curdisp = d
##		self._rb_dialog = showmessage(
##			msg, mtype = 'message', grab = 0,
##			callback = (self._rb_done, ()),
##			cancelCallback = (self._rb_cancel, ()))
##		self._rb_callback = callback
##		raise 'not implemented'
##		form = self._form
##		form.AddEventHandler(X.ButtonPressMask, FALSE,
##				     self._start_rb, None)
##		form.AddEventHandler(X.ButtonMotionMask, FALSE,
##				     self._do_rb, None)
##		form.AddEventHandler(X.ButtonReleaseMask, FALSE,
##				     self._end_rb, None)
##		cursor = form.Display().CreateFontCursor(Xcursorfont.crosshair)
##		form.GrabButton(X.AnyButton, X.AnyModifier, TRUE,
##				X.ButtonPressMask | X.ButtonMotionMask
##					| X.ButtonReleaseMask,
##				X.GrabModeAsync, X.GrabModeAsync, form, cursor)
##		v = form.GetValues(['foreground', 'background'])
##		v['foreground'] = v['foreground'] ^ v['background']
##		v['function'] = X.GXxor
##		v['line_style'] = X.LineOnOffDash
##		self._gc_rb = form.GetGC(v)
##		self._rb_box = box
##		if box:
##			x, y, w, h = self._convert_coordinates(box)
##			if w < 0:
##				x, w = x + w, -w
##			if h < 0:
##				y, h = y + h, -h
##			self._rb_box = x, y, w, h
##			self._rb_start_x = x
##			self._rb_start_y = y
##			self._rb_width = w
##			self._rb_height = h
##		else:
##			self._rb_start_x, self._rb_start_y, self._rb_width, \
##					  self._rb_height = self._rect
##		try:
##			Xt.MainLoop()
##		except _rb_done:
##			pass

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
		raise 'not yet implemented'
##		form = self._form
##		form.RemoveEventHandler(X.ButtonPressMask, FALSE,
##					self._start_rb, None)
##		form.RemoveEventHandler(X.ButtonMotionMask, FALSE,
##					self._do_rb, None)
##		form.RemoveEventHandler(X.ButtonReleaseMask, FALSE,
##					self._end_rb, None)
##		form.UngrabButton(X.AnyButton, X.AnyModifier)
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
		raise 'not yet implemented'
##		self._gc_rb.DrawRectangle(x, y, w, h)

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
			if x + w/4 < event.x < x + w*3/4:
				self._rb_cx = 1
			else:
				self._rb_cx = 0
				if event.x >= x + w*3/4:
					x, w = x + w, -w
			if y + h/4 < event.y < y + h*3/4:
				self._rb_cy = 1
			else:
				self._rb_cy = 0
				if event.y >= y + h*3/4:
					y, h = y + h, -h
			if self._rb_cx and self._rb_cy:
				self._rb_last_x = event.x
				self._rb_last_y = event.y
				self._rb_start_x = x
				self._rb_start_y = y
				self._rb_width = w
				self._rb_height = h
			else:
				if not self._rb_cx:
					self._rb_start_x = x + w
					self._rb_width = event.x - self._rb_start_x
				if not self._rb_cy:
					self._rb_start_y = y + h
					self._rb_height = event.y - self._rb_start_y
		else:
			self._rb_start_x = event.x
			self._rb_start_y = event.y
			self._rb_width = self._rb_height = 0
			self._rb_cx = self._rb_cy = 0
		self._rb_draw()

	def _do_rb(self, w, data, event):
		# called on mouse drag
		self._rb_common(event)
		self._rb_draw()

	def _end_rb(self, w, data, event):
		# called on mouse release
		self._rb_common(event)
		self._rb_curdisp = self._rb_display.clone()
		self._rb_curdisp.fgcolor((255, 0, 0))
		self._rb_curdisp.drawbox(self._rb_cvbox())
		self._rb_curdisp.render()
		del self._rb_cx
		del self._rb_cy

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
		#self._wnd._delete_callback(self, form, client_data,call_data)
		if w:
			w._rb_end()
			raise _rb_done

	def _input_callback(self, form, client_data, call_data):
		pass

