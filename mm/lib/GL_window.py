__version__ = "$Id$"

from GL_windowbase import *
import GL_windowbase

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

import sys

import fl, glwindow
_last_forms = None

def startmonitormode():
	fl.deactivate_all_forms()
	glwindow.stop_callback_mode()

def endmonitormode():
	fl.activate_all_forms()
	glwindow.start_callback_mode()

def qread():
	global _last_forms
	toplevel._win_lock.acquire()
	while not _last_forms:
		_last_forms = fl.do_forms()
	dev, val = fl.qread()
	toplevel._win_lock.release()
	_last_forms = None
	return dev, val

def qtest():
	global _last_forms
	retval = None
	toplevel._win_lock.acquire()
	if not _last_forms:
		_last_forms = fl.check_forms()
	retval = fl.qtest()
	if retval:
		_last_forms = -1
	toplevel._win_lock.release()
	return retval

qdevice = fl.qdevice

GL_windowbase.startmonitormode = startmonitormode
GL_windowbase.endmonitormode = endmonitormode
GL_windowbase.qread = qread
GL_windowbase.qtest = qtest
GL_windowbase.qdevice = qdevice

class _Toplevel(GL_windowbase._Toplevel):
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE, pixmap = 0, units = UNIT_MM):
		if debug: print 'Toplevel.newwindow'+`x, y, w, h, title`
		window = _Window(1, self, x, y, w, h, title, units)
		event._qdevice()
		dummy = event.testevent()
		return window

	newcmwindow = newwindow

	def getsize(self):
		return _mscreenwidth, _mscreenheight

_box_message = """\
Use left mouse button to draw a box.
Click `Done' when ready or `Cancel' to cancel."""

# symbol used for returning
_box_finished = '_finished'

class _Boxes:
	def __init__(self, window, msg, callback, box):
		if len(box) == 1 and type(box) is TupleType:
			box = box[0]
		if len(box) not in (0, 4):
			raise TypeError, 'bad arguments'
		if len(box) == 0:
			self.box = None
		else:
			self.box = box
		self.window = window
		self.callback = callback
		self.old_display = window._active_display_list
		window.pop()
		window._close_subwins()
		win = window
		fa1 = []
		fa2 = []
		while win:
			try:
				fa = win.getregister(Mouse0Press)
			except error:
				fa = None
			else:
				win.unregister(Mouse0Press)
			fa1.append(fa)
			try:
				fa = win.getregister(Mouse0Release)
			except error:
				fa = None
			else:
				win.unregister(Mouse0Release)
			fa2.append(fa)
			win = win._parent_window
		self.fa1 = fa1
		self.fa2 = fa2
		if not self.box:
			window.register(Mouse0Press, self.first_press, None)
		else:
			window.register(Mouse0Press, self.press, None)
		if self.old_display and not self.old_display.is_closed():
			d = self.old_display.clone()
		else:
			d = window.newdisplaylist()
		for win in window._subwindows:
			b = win._sizes
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self.display = d.clone()
		d.fgcolor((255, 0, 0))
		if box:
			d.drawbox(box)
		d.render()
		self.cur_display = d
		if msg:
			msg = msg + '\n\n' + _box_message
		else:
			msg = _box_message
		self._looping = 0
		self.dialog = Dialog(
			[('', 'Done', (self.done_callback, ())),
			('', 'Cancel', (self.cancel_callback, ()))],
			title = None, prompt = msg, grab = 0, vertical = 0)

	def __del__(self):
		self.close()

	def close(self):
		self.window._open_subwins()
		if self.old_display and not self.old_display.is_closed():
			self.old_display.render()
		self.display.close()
		self.cur_display.close()
		self.dialog.close()

	def _size_cb(self, x, y, w, h):
		self.box = x, y, w, h

	def first_press(self, dummy, win, ev, val):
		win._sizebox((val[0], val[1], 0, 0), 0, 0, self._size_cb)
		win.register(Mouse0Press, self.press, None)
		self.after_press()

	def press(self, dummy, win, ev, val):
		x, y = val[0:2]
		b = self.box
		if b[0] + b[2]/4 < x < b[0] + b[2]*3/4:
			constrainx = 1
		else:
			constrainx = 0
		if b[1] + b[3]/4 < y < b[1] + b[3]*3/4:
			constrainy = 1
		else:
			constrainy = 0
		self.display.render()
		
		if constrainx and constrainy:
			self.box = win._movebox(b, 0, 0)
		else:
			if x < b[0] + b[2]/2:
				x0 = b[0] + b[2]
				w = -b[2]
			else:
				x0 = b[0]
				w = b[2]
			if y < b[1] + b[3]/2:
				y0 = b[1] + b[3]
				h = -b[3]
			else:
				y0 = b[1]
				h = b[3]
			win._sizebox((x0, y0, w, h),
				    constrainx, constrainy, self._size_cb)
		self.after_press()

	def after_press(self):
		d = self.display.clone()
		d.fgcolor((255, 0, 0))
		d.drawbox(self.box)
		d.render()
		self.cur_display.close()
		self.cur_display = d

	def loop(self):
		startmonitormode()
		self.window.setcursor('')
		try:
			try:
				self._looping = 1
				while 1:
					dummy = event.readevent()
			except _box_finished:
				return
		finally:
			endmonitormode()

	def done_callback(self):
		self.close()
		apply(self.callback, self.box)
		if self._looping:
			raise _box_finished

	def cancel_callback(self):
		self.close()
		apply(self.callback, ())
		if self._looping:
			raise _box_finished

class _DisplayList(GL_windowbase._DisplayList):
	def clone(self):
		if debug: print `self`+'.clone()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		new = _DisplayList(self._window)
		new._displaylist = self._displaylist[:]
		new._fgcolor = self._fgcolor
		new._bgcolor = self._bgcolor
		new._curcolor = None
		new._font = self._font
		new._fontheight = self._fontheight
		new._baseline = self._baseline
		new._curfont = None
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._displaylist)
		return new

	def linewidth(self, width):	# XXX--should use a better unit
		self._linewidth = int(width)

	def drawfpolygon(self, color, points):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawfpolygon'+`points`
		d = self._displaylist
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		d.append(gl.bgnpolygon)
		for x, y in points:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			d.append(gl.v2f, (x, y))
		d.append(gl.endpolygon)

	def draw3dbox(self, cl, ct, cr, cb, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		l, b, r, t = window._convert_coordinates(x, y, w, h)
		l = l+1
		t = t-1
		r = r-1
		b = b+1
		l1 = l - 1
		t1 = t + 1
		r1 = r
		b1 = b
		ll = l + 2
		tt = t - 2
		rr = r - 2
		bb = b + 3
		if self._curcolor != cl:
			d.append(gl.RGBcolor, (cl))
			self._curcolor = cl
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (l1, t1))
		d.append(gl.v2i, (ll, tt))
		d.append(gl.v2i, (ll, bb))
		d.append(gl.v2i, (l1, b1))
		d.append(gl.endpolygon, ())
		if self._curcolor != ct:
			d.append(gl.RGBcolor, (ct))
			self._curcolor = ct
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (l1, t1))
		d.append(gl.v2i, (r1, t1))
		d.append(gl.v2i, (rr, tt))
		d.append(gl.v2i, (ll, tt))
		d.append(gl.endpolygon, ())
		if self._curcolor != cr:
			d.append(gl.RGBcolor, (cr))
			self._curcolor = cr
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (r1, t1))
		d.append(gl.v2i, (r1, b1))
		d.append(gl.v2i, (rr, bb))
		d.append(gl.v2i, (rr, tt))
		d.append(gl.endpolygon, ())
		if self._curcolor != cb:
			d.append(gl.RGBcolor, (cb))
			self._curcolor = cb
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (l1, b1))
		d.append(gl.v2i, (ll, bb))
		d.append(gl.v2i, (rr, bb))
		d.append(gl.v2i, (r1, b1))
		d.append(gl.endpolygon, ())

	def drawdiamond(self, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawfdiamond'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		x0, y0, x1, y1 = window._convert_coordinates(x, y, w, h)
		if self._curcolor != self._fgcolor:
			d.append(gl.RGBcolor, self._fgcolor)
			self._curcolor = self._fgcolor
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.bgnclosedline, ())
		d.append(gl.v2i, (x0, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y1))
		d.append(gl.v2i, (x1, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y0))
		d.append(gl.endclosedline, ())

	def drawfdiamond(self, color, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawfdiamond'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		x0, y0, x1, y1 = window._convert_coordinates(x, y, w, h)
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.bgnpolygon)
		d.append(gl.v2i, (x0, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y1))
		d.append(gl.v2i, (x1, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y0))
		d.append(gl.endpolygon)

	def draw3ddiamond(self, cl, ct, cr, cb, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		l, b, r, t = window._convert_coordinates(x, y, w, h)
		x = (l + r) / 2
		y = (t + b) / 2
		n = int(3.0 * (r-l) / (t-b) + 0.5)
		ll = l + n
		tt = t - 3
		rr = r - n
		bb = b + 3

		d.append(gl.RGBcolor, cl)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (l, y))
		d.append(gl.v2f, (x, t))
		d.append(gl.v2f, (x, tt))
		d.append(gl.v2f, (ll, y))
		d.append(gl.endpolygon, ())

		d.append(gl.RGBcolor, ct)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (x, t))
		d.append(gl.v2f, (r, y))
		d.append(gl.v2f, (rr, y))
		d.append(gl.v2f, (x, tt))
		d.append(gl.endpolygon, ())

		d.append(gl.RGBcolor, cr)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (r, y))
		d.append(gl.v2f, (x, b))
		d.append(gl.v2f, (x, bb))
		d.append(gl.v2f, (rr, y))
		d.append(gl.endpolygon, ())

		d.append(gl.RGBcolor, cb)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (l, y))
		d.append(gl.v2f, (ll, y))
		d.append(gl.v2f, (x, bb))
		d.append(gl.v2f, (x, b))
		d.append(gl.endpolygon, ())

##		d.append(gl.RGBcolor, (FOCUSBORDER))
##		d.append(gl.linewidth, (1))
##		d.append(gl.bgnclosedline, ())
##		d.append(gl.v2f, (l, y))
##		d.append(gl.v2f, (x, t))
##		d.append(gl.v2f, (r, y))
##		d.append(gl.v2f, (x, b))
##		d.append(gl.endclosedline, ())

	def drawarrow(self, color, sx, sy, dx, dy):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		d = self._displaylist
		sx, sy = window._convert_coordinates(sx, sy, 0, 0)[:2]
		dx, dy = window._convert_coordinates(dx, dy, 0, 0)[:2]
		lx = dx - sx
		ly = dy - sy
		if lx == ly == 0:
			angle = 0.0
		else:
			angle = math.atan2(ly, lx)
		rotation = 180 + angle * 180.0 / math.pi
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		# Draw the line from src to dst
		d.append(gl.linewidth, 2)
		d.append(gl.bgnline)
		d.append(gl.v2i, (sx, sy))
		d.append(gl.v2i, (dx, dy))
		d.append(gl.endline)
		# Draw the arrowhead
		# Translate so that the point of the arrowhead is (0, 0)
		# Rotate so that it comes in horizontally from the right
		d.append(gl.pushmatrix)
		d.append(gl.translate, (dx, dy, 0))
		d.append(gl.rot, (rotation, 'z'))
		d.append(gl.bgnpolygon)
		d.append(gl.v2f, (0, 0))
		d.append(gl.v2f, (ARR_LENGTH, ARR_HALFWIDTH))
		d.append(gl.v2f, (ARR_LENGTH, -ARR_HALFWIDTH))
		d.append(gl.endpolygon)
		d.append(gl.popmatrix)

class _Window(GL_windowbase._Window):
	def newwindow(self, coordinates, type_channel = SINGLE, **options):
		if debug: print `self`+'.newwindow'+`coordinates`
		x, y, w, h = coordinates
		x0, y0, x1, y1 = self._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._toplevel._window_id)
		tx, ty = gl.getorigin()
		gl.winset(self._window_id)
		wx, wy = gl.getorigin()
		wx, wy = wx - tx, wy - ty
		x0, y0 = x0 + wx, y0 + wy
		x1, y1 = x1 + wx, y1 + wy
		new_window = _Window(0, self, 0, 0, 0, 0, 0, 0)
		new_window._window_id = gl.swinopen(self._window_id)
		gl.winposition(x0, x1, y0, y1)
		new_window._parent_window = self
		new_window._sizes = x, y, w, h
		new_window._toplevel = self._toplevel
		new_window._init2()
		dummy = event.testevent()
		return new_window

	newcmwindow = newwindow

	def _close_subwins(self):
		for win in self._subwindows:
			win._close_win()
		self._subwindows_closed = 1

	def _close_win(self):
		# close the GL window connected to this instance
		if debug: print `self`+'._close_win()'
		if self._parent_window is toplevel:
			raise error, 'can\'t close top-level window'
		self._close_subwins()
		gl.winclose(self._window_id)
		del _window_list[self._window_id]
		self._window_id = -1

	def _open_subwins(self):
		if self.is_closed():
			raise error, 'window already closed'
		for win in self._subwindows:
			if not win.is_closed():
				win._open_win()
		self._subwindows_closed = 0

	def _open_win(self):
		# re-open a GL window for this instance
		if self.is_closed():
			raise error, 'window already closed'
		if self._window_id != -1:
			raise error, 'window not closed'
		x, y, w, h = self._sizes
		x0, y0, x1, y1 = self._parent_window._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._toplevel._window_id)
		tx, ty = gl.getorigin()
		gl.winset(self._parent_window._window_id)
		wx, wy = gl.getorigin()
		wx, wy = wx - tx, wy - ty
		x0, y0 = x0 + wx, y0 + wy
		x1, y1 = x1 + wx, y1 + wy
		self._window_id = gl.swinopen(self._parent_window._window_id)
		gl.winposition(x0, x1, y0, y1)
		gl.RGBmode()
		gl.gconfig()
		gl.reshapeviewport()
		self._width, self._height = gl.getsize()
		gl.ortho2(-0.5, self._width-0.5, -0.5, self._height-0.5)
		toplevel._win_lock.release()
		_window_list[self._window_id] = self
		self.setcursor(self._cursor)
		self._open_subwins()

	def newdisplaylist(self, *bgcolor):
		if self.is_closed():
			raise error, 'window already closed'
		list = _DisplayList(self)
		if len(bgcolor) == 1 and type(bgcolor[0]) is TupleType:
			bgcolor = bgcolor[0]
		if len(bgcolor) == 3:
			list._bgcolor = list._curcolor = bgcolor
		elif len(bgcolor) != 0:
			raise TypeError, 'arg count mismatch'
		return list

	def create_box(self, msg, callback, *box):
		_Boxes(self, msg, callback, box).loop()

	def _sizebox(self, (x, y, w, h), constrainx, constrainy, callback):
		if debug: print `self`+'.sizebox()'
		if self.is_closed():
			raise error, 'window already closed'
		if constrainx and constrainy:
			raise error, 'can\'t constrain both X and Y directions'
		# we must invert y0 and y1 here because convert_coordinates
		# inverts them also and here it is important which coordinate
		# comes first but not which coordinate is the higher
		x0, y1, x1, y0 = self._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		if gl.getplanes() < 12:
			gl.drawmode(GL.PUPDRAW)
			gl.mapcolor(GL.RED, 255, 0, 0)
		else:
			gl.drawmode(GL.OVERDRAW)
		gl.qreset()
		gl.color(0)
		gl.clear()
		gl.color(GL.RED)
		gl.recti(x0, y0, x1, y1)
		screenx0, screeny0 = gl.getorigin()
		mx, my = x1, y1
		width, height = gl.getsize()
		toplevel._win_lock.release()
		while 1:
			while event.testevent() == 0:
				if not constrainx:
					mx = gl.getvaluator(DEVICE.MOUSEX) - \
						  screenx0
					if mx < 0:
						mx = 0
					if mx >= width:
						mx = width - 1
				if not constrainy:
					my = gl.getvaluator(DEVICE.MOUSEY) - \
						  screeny0
					if my < 0:
						my = 0
					if my >= height:
						my = height - 1
				if mx != x1 or my != y1:
					toplevel._win_lock.acquire()
					gl.winset(self._window_id)
					gl.color(0)
					gl.clear()
					x1, y1 = mx, my
					gl.color(GL.RED)
					gl.recti(x0, y0, x1, y1)
					toplevel._win_lock.release()
			w, e, v = event.readevent()
			if e == Mouse0Release:
				break
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.color(0)
		gl.clear()
		gl.drawmode(GL.NORMALDRAW)
		toplevel._win_lock.release()
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, w, h = float(x0) / (width - 1), \
			  float(height - y1 - 1) / (height - 1), \
			  float(x1 - x0) / (width - 1), \
			  float(y1 - y0) / (height - 1)
		# constrain coordinates to window
		if x < 0:
			x = 0
		if y < 0:
			y = 0
		if x + w > 1:
			w = 1 - x
		if y + h > 1:
			h = 1 - y
		apply(callback, (x, y, w, h))

	def _movebox(self, (x, y, w, h), constrainx, constrainy):
		if debug: print `self`+'.movebox()'
		if self.is_closed():
			raise error, 'window already closed'
		if constrainx and constrainy:
			raise error, 'can\'t constrain both X and Y directions'
		x0, y0, x1, y1 = self._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		if gl.getplanes() < 12:
			gl.drawmode(GL.PUPDRAW)
			gl.mapcolor(GL.RED, 255, 0, 0)
		else:
			gl.drawmode(GL.OVERDRAW)
		gl.color(0)
		gl.clear()
		gl.color(GL.RED)
		gl.recti(x0, y0, x1, y1)
		screenx0, screeny0 = gl.getorigin()
		omx = gl.getvaluator(DEVICE.MOUSEX) - screenx0
		omy = gl.getvaluator(DEVICE.MOUSEY) - screeny0
		width, height = gl.getsize()
		toplevel._win_lock.release()
		while 1:
			while event.testevent() == 0:
				if not constrainx:
					mx = gl.getvaluator(DEVICE.MOUSEX) - screenx0
				if not constrainy:
					my = gl.getvaluator(DEVICE.MOUSEY) - screeny0
				if mx != omx or my != omy:
					dx = mx - omx
					dy = my - omy
					toplevel._win_lock.acquire()
					gl.winset(self._window_id)
					gl.color(0)
					gl.clear()
					x0 = x0 + dx
					x1 = x1 + dx
					if x0 < 0:
						x1 = x1 - x0
						x0 = 0
					if x1 >= width:
						x0 = x0 - (x1 - width) - 1
						x1 = width - 1
					y0 = y0 + dy
					y1 = y1 + dy
					if y0 < 0:
						y1 = y1 - y0
						y0 = 0
					if y1 >= height:
						y0 = y0 - (y1 - height) - 1
						y1 = height - 1
					gl.color(GL.RED)
					gl.recti(x0, y0, x1, y1)
					omx, omy = mx, my
					toplevel._win_lock.release()
			w, e, v = event.readevent()
			if e == Mouse0Release:
				break
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.color(0)
		gl.clear()
		gl.drawmode(GL.NORMALDRAW)
		toplevel._win_lock.release()
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, w, h = float(x0) / (width - 1), \
			  float(height - y1 - 1) / (height - 1), \
			  float(x1 - x0) / (width - 1), \
			  float(y1 - y0) / (height - 1)
		# constrain coordinates to window
		if x < 0:
			x = 0
		if y < 0:
			y = 0
		if x + w > 1:
			w = 1 - x
		if y + h > 1:
			h = 1 - y
		return x, y, w, h

	def hitarrow(self, x, y, sx, sy, dx, dy):
		# return 1 iff (x,y) is within the arrow head
		if self.is_closed():
			raise error, 'window already closed'
		sx, sy = self._convert_coordinates(sx, sy, 0, 0)[:2]
		dx, dy = self._convert_coordinates(dx, dy, 0, 0)[:2]
		x, y = self._convert_coordinates(x, y, 0, 0)[:2]
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

class _Question(Dialog):
	def __init__(self, text):
		self._finish = None
		Dialog.__init__(self,
				[('y', 'Yes', (self._ok_callback, ())),
				 ('n', 'No', (self._cancel_callback, ()))],
				None, text, 1, 0)

	def run(self):
		self._loop()
		return self._finish

	def _ok_callback(self):
		self._finish = 1

	def _cancel_callback(self):
		self._finish = 0

def showquestion(text):
	d = _Question(text)
	return d.run()

def FileDialog(prompt, directory, filter, file, cb_ok, cb_cancel, existing=0):
	import fl
	filename = fl.show_file_selector(prompt, directory, filter, file)
	if filename:
		if cb_ok:
			cb_ok(filename)
	else:
		if cb_cancel:
			cb_cancel()

def InputDialog(prompt, default, cb):
	import fl
	value = fl.show_input(prompt, default)
	if value and cb is not None:
		cb(value)

class SelectionDialog:
	def __init__(self, listprompt, itemprompt, itemlist, default,
		     title = 'SelectionDialog'):
		import fl, FL
		self._title = title
		self._callbacks = {}

		self._form = fl.make_form(FL.FLAT_BOX, 300, 320)
		form = self._form

		x, y, w, h = 0, 0, 300, 250
		self._browser = form.add_browser(FL.HOLD_BROWSER, x, y, w, h,
						 listprompt)
		self._browser.set_call_back(self._browser_callback, None)

		buttonwidth = 300 / len(buttonlist)
		x, y, w, h = 0, 250, buttonwidth, 39
		buttonlist = ['Ok', 'Cancel']
		for entry in buttonlist:
			if type(entry) is TupleType:
				accelerator, label, callback = entry
			else:
				accelerator, label, callback = '', entry, None
			if callback and type(callback) is not TupleType:
				callback = (callback, (label,))
			button = form.add_button(FL.NORMAL_BUTTON, x, y, w, h,
						 label)
			button.set_call_back(self._callback, label)
			self._callbacks[label] = callback
			x = x + buttonwidth

		x, y, w, h = 50, 290, 250, 30
		if itemprompt is None:
			itemprompt = 'Selection'
		self.nameinput = form.add_input(FL.NORMAL_INPUT, x, y, w, h,
						itemprompt)
		self.nameinput.set_call_back(self.name_callback, None)

		for item in itemlist:
			self._browser.add_browser_line(item)

		form.show_form(FL.PLACE_SIZE, 1, self._title)
		self.showing = 1

	def close(self):
		self._browser = None
		self._form = None

	def getselection(self):
		return self.nameinput.get_input()

	def getselected(self):
		i = self._browser.get_browser()
		if i:
			return i - 1
		else:
			return None

	def getlistitem(self, pos):
		if pos < 0:
			pos = self._browser.get_browser_maxline()
		else:
			pos = pos + 1
		return self._browser.get_browser_line(pos)

	def addlistitem(self, item, pos):
		if pos < 0:
			self._browser.add_browser_line(item)
		else:
			self._browser.insert_browser_line(pos + 1, item)

	def dellistitem(self, pos):
		self._browser.delete_browser_line(pos + 1)

	def replacelistitem(self, pos, newitem):
		self._browser.replace_browser_line(pos + 1, newitem)

	def delalllistitems(self):
		self._browser.clear_browser()

	def selectitem(self, pos):
		if pos < 0:
			pos = self._browser.get_browser_maxline()
		else:
			pos = pos + 1
		self._browser.select_browser_line(pos)
		line = self._browser.get_browser_line(pos)
		self.nameinput.set_input(line)

	#
	# Various callbacks
	#
	def _browser_callback(self, obj, arg):
		# When an item is selected in the browser,
		# copy its name to the input box.
		i = self._browser.get_browser()
		if i == 0:
			return
		name = self._browser.get_browser_line(i)
		self.nameinput.set_input(name)

	def _callback(self, obj, arg):
		if arg == 'Ok':
			try:
				func = self.OkCallback
			except AttributeError:
				pass
			else:
				ret = func(self.nameinput.get_input())
				if ret:
					if type(ret) is StringType:
						showmessage(ret, mtype = 'error')
					return
		if arg == 'Cancel':
			try:
				func = self.CancelCallback
			except AttributeError:
				pass
			else:
				ret = func()
				if ret:
					if type(ret) is StringType:
						showmessage(ret, mtype = 'error')
					return
		self.close()

	def name_callback(self, obj, arg):
		# When the user presses TAB or RETURN,
		# search the browser for a matching name and select it.
		name = self.nameinput.get_input()
		for i in range(self._browser.get_browser_maxline()):
			if self._browser.get_browser_line(i+1) == name:
				self._browser.select_browser_line(i+1)
				break

toplevel = _Toplevel()
event = GL_windowbase._Event()

newwindow = toplevel.newwindow

newcmwindow = newwindow

close = toplevel.close

addclosecallback = toplevel.addclosecallback

setcursor = toplevel.setcursor

getsize = toplevel.getsize

beep = gl.ringbell

usewindowlock = toplevel.usewindowlock

getscreensize = toplevel.getscreensize
getscreendepth = toplevel.getscreendepth

settimer = event.settimer

select_setcallback = event.select_setcallback

mainloop = event.mainloop

canceltimer = event.canceltimer
