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
		      menubar = None, canvassize = None):
## 		if pixmap is None:
## 			pixmap = toplevel._depth <= 8
		return _Window(self, x, y, w, h, title, 0, pixmap, units, menubar, canvassize)

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE,
			type_channel = SINGLE, pixmap = None, units = UNIT_MM,
			menubar = None, canvassize = None):
## 		if pixmap is None:
## 			pixmap = toplevel._depth <= 8
		return _Window(self, x, y, w, h, title, 1, pixmap, units, menubar, canvassize)

	def getsize(self):
		return toplevel._mscreenwidth, toplevel._mscreenheight

class _Window(X_windowbase._Window):
	def __init__(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
		     units = UNIT_MM, menubar = None, canvassize = None):
		X_windowbase._Window.__init__(self, parent, x, y, w, h, title,
					      defcmap, pixmap, units, menubar,
					      canvassize)
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

class _SubWindow(X_windowbase._BareSubWindow, _Window):
	def __init__(self, parent, coordinates, defcmap, pixmap, transparent, z):
		X_windowbase._BareSubWindow.__init__(self, parent, coordinates,
						     defcmap, pixmap,
						     transparent, z)
		self.arrowcache = {}
		self._next_create_box = []

class _DisplayList(X_windowbase._DisplayList):
	def _do_render(self, entry, region):
		cmd = entry[0]
		w = self._window
		gc = w._gc
		if cmd == 'fpolygon':
			gc.foreground = entry[1]
			gc.FillPolygon(entry[2], X.Convex,
				       X.CoordModeOrigin)
		elif cmd == '3dbox':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]
			r, b = l + w, t + h
			l = l+1
			t = t+1
			r = r-1
			b = b-1
			l1 = l - 1
			t1 = t - 1
			r1 = r
			b1 = b
			ll = l + 2
			tt = t + 2
			rr = r - 2
			bb = b - 3
			gc.foreground = cl
			gc.FillPolygon([(l1, t1), (ll, tt), (ll, bb), (l1, b1)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = ct
			gc.FillPolygon([(l1, t1), (r1, t1), (rr, tt), (ll, tt)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cr
			gc.FillPolygon([(r1, t1), (r1, b1), (rr, bb), (rr, tt)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cb
			gc.FillPolygon([(l1, b1), (ll, bb), (rr, bb), (r1, b1)],
				       X.Convex, X.CoordModeOrigin)
		elif cmd == 'diamond':
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			x, y, w, h = entry[3]
			gc.DrawLines([(x, y + h/2),
				      (x + w/2, y),
				      (x + w, y + h/2),
				      (x + w/2, y + h),
				      (x, y + h/2)],
				     X.CoordModeOrigin)
		elif cmd == 'fdiamond':
			gc.foreground = entry[1]
			x, y, w, h = entry[2]
			gc.FillPolygon([(x, y + h/2),
					(x + w/2, y),
					(x + w, y + h/2),
					(x + w/2, y + h),
					(x, y + h/2)],
				       X.Convex, X.CoordModeOrigin)
		elif cmd == '3ddiamond':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]
			r = l + w
			b = t + h
			x = l + w/2
			y = t + h/2
			n = int(3.0 * w / h + 0.5)
			ll = l + n
			tt = t + 3
			rr = r - n
			bb = b - 3
			gc.foreground = cl
			gc.FillPolygon([(l, y), (x, t), (x, tt), (ll, y)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = ct
			gc.FillPolygon([(x, t), (r, y), (rr, y), (x, tt)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cr
			gc.FillPolygon([(r, y), (x, b), (x, bb), (rr, y)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cb
			gc.FillPolygon([(l, y), (ll, y), (x, bb), (x, b)],
				       X.Convex, X.CoordModeOrigin)
		elif cmd == 'arrow':
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			apply(gc.DrawLine, entry[3])
			gc.FillPolygon(entry[4], X.Convex,
				       X.CoordModeOrigin)
		else:
			X_windowbase._DisplayList._do_render(self, entry, region)

	def clone(self):
		w = self._window
		new = _DisplayList(w, self._bgcolor)
		# copy all instance variables
		new._list = self._list[:]
		new._font = self._font
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def drawfpolygon(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append(('fpolygon', color, p))
		self._optimize((1,))

	def draw3dbox(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		coordinates = window._convert_coordinates(coordinates)
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append(('3dbox', (cl, ct, cr, cb), coordinates))
		self._optimize((1,))

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		self._list.append(('diamond',
				   self._window._convert_color(self._fgcolor),
				   self._linewidth, coordinates))
		self._optimize((1,))

	def drawfdiamond(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		coordinates = window._convert_coordinates((x, y, w, h))
		color = window._convert_color(color)
		self._list.append(('fdiamond', color, coordinates))
		self._optimize((1,))

	def draw3ddiamond(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		coordinates = window._convert_coordinates(coordinates)
		self._list.append(('3ddiamond', (cl, ct, cr, cb), coordinates))
		self._optimize((1,))

	def drawarrow(self, color, src, dst):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		color = self._window._convert_color(color)
		if not window.arrowcache.has_key((src,dst)):
			sx, sy = src
			dx, dy = dst
			nsx, nsy = window._convert_coordinates((sx, sy))
			ndx, ndy = window._convert_coordinates((dx, dy))
			if nsx == ndx and sx != dx:
				if sx < dx:
					nsx = nsx - 1
				else:
					nsx = nsx + 1
			if nsy == ndy and sy != dy:
				if sy < dy:
					nsy = nsy - 1
				else:
					nsy = nsy + 1
			lx = ndx - nsx
			ly = ndy - nsy
			if lx == ly == 0:
				angle = 0.0
			else:
				angle = math.atan2(ly, lx)
			rotation = math.pi + angle
			cos = math.cos(rotation)
			sin = math.sin(rotation)
			points = [(ndx, ndy)]
			points.append(roundi(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
				      roundi(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos))
			points.append(roundi(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
				      roundi(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos))
			window.arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		nsx, nsy, ndx, ndy, points = window.arrowcache[(src,dst)]
		self._list.append(('arrow', color, self._linewidth,
				   (nsx, nsy, ndx, ndy), points))
		self._optimize((1,))

toplevel = _Toplevel()
from X_windowbase import *

class FileDialog:
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel,
		     existing=0):
		import os
		self.cb_ok = cb_ok
		self.cb_cancel = cb_cancel
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth,
			 'width': 400}
		if prompt:
			form = toplevel._main.CreateFormDialog(
						   'fileSelect', attrs)
			self._form = form
			label = form.CreateManagedWidget('filePrompt',
					Xm.LabelGadget,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_FORM})
			label.labelString = prompt
			dialog = form.CreateManagedWidget('fileSelect',
					Xm.FileSelectionBox,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_WIDGET,
					 'topWidget': label,
					 'width': 400})
		else:
			dialog = toplevel._main.CreateFileSelectionDialog(
							  'fileSelect', attrs)
			self._form = dialog
		self._dialog = dialog
		dialog.AddCallback('okCallback', self._ok_callback, None)
		dialog.AddCallback('cancelCallback', self._cancel_callback,
				       None)
		helpb = dialog.FileSelectionBoxGetChild(
						    Xmd.DIALOG_HELP_BUTTON)
		helpb.UnmanageChild()
		if not directory:
			directory = '.'
		try:
			if os.stat(directory) == os.stat('/'):
				directory = '/'
		except os.error:
			pass
		if not filter:
			filter = '*'
		self.filter = filter
		filter = os.path.join(directory, filter)
		dialog.FileSelectionDoSearch(filter)
		text = dialog.FileSelectionBoxGetChild(Xmd.DIALOG_TEXT)
		text.value = file
		self._form.ManageChild()
		toplevel._subwindows.append(self)

	def close(self):
		if self._form:
			toplevel._subwindows.remove(self)
			self._form.UnmanageChild()
			self._form.DestroyWidget()
			self._dialog = None
			self._form = None

	def setcursor(self, cursor):
		X_windowbase._setcursor(self._form, cursor)

	def is_closed(self):
		return self._form is None

	def _cancel_callback(self, *rest):
		if self.is_closed():
			return
		must_close = TRUE
		try:
			if self.cb_cancel:
				ret = self.cb_cancel()
				if ret:
					if type(ret) is StringType:
						showmessage(ret)
					must_close = FALSE
					return
		finally:
			if must_close:
				self.close()

	def _ok_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		import os
		filename = call_data.value
		dir = call_data.dir
		filter = call_data.pattern
		filename = os.path.join(dir, filename)
		if not os.path.isfile(filename):
			if os.path.isdir(filename):
				filter = os.path.join(filename, filter)
				self._dialog.FileSelectionDoSearch(filter)
				return
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) is StringType:
					showmessage(ret)
				return
		self.close()

class SelectionDialog:
	def __init__(self, listprompt, selectionprompt, itemlist, default):
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth,
			 'textString': default,
			 'autoUnmanage': FALSE}
		if hasattr(self, 'NomatchCallback'):
			attrs['mustMatch'] = TRUE
		if listprompt:
			attrs['listLabelString'] = listprompt
		if selectionprompt:
			attrs['selectionLabelString'] = selectionprompt
		form = toplevel._main.CreateSelectionDialog('selectDialog',
							    attrs)
		self._form = form
		form.AddCallback('okCallback', self._ok_callback, None)
		form.AddCallback('cancelCallback', self._cancel_callback, None)
		if hasattr(self, 'NomatchCallback'):
			form.AddCallback('noMatchCallback',
					 self._nomatch_callback, None)
		for b in [Xmd.DIALOG_APPLY_BUTTON, Xmd.DIALOG_HELP_BUTTON]:
			form.SelectionBoxGetChild(b).UnmanageChild()
		list = form.SelectionBoxGetChild(Xmd.DIALOG_LIST)
		list.ListAddItems(itemlist, 1)
		form.ManageChild()
		toplevel._subwindows.append(self)

	def setcursor(self, cursor):
		X_windowbase._setcursor(self._form, cursor)

	def is_closed(self):
		return self._form is None

	def close(self):
		if self._form:
			toplevel._subwindows.remove(self)
			self._form.UnmanageChild()
			self._form.DestroyWidget()
			self._form = None

	def _nomatch_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		ret = self.NomatchCallback(call_data.value)
		if ret and type(ret) is StringType:
			showmessage(ret, mtype = 'error')

	def _ok_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		try:
			func = self.OkCallback
		except AttributeError:
			pass
		else:
			ret = func(call_data.value)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error')
				return
		self.close()

	def _cancel_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
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

class InputDialog:
	def __init__(self, prompt, default, cb):
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth}
		self._form = toplevel._main.CreatePromptDialog(
						   'inputDialog', attrs)
		self._form.AddCallback('okCallback', self._ok, cb)
		self._form.AddCallback('cancelCallback', self._cancel, None)
		helpb = self._form.SelectionBoxGetChild(
						Xmd.DIALOG_HELP_BUTTON)
		helpb.UnmanageChild()
		sel = self._form.SelectionBoxGetChild(
					      Xmd.DIALOG_SELECTION_LABEL)
		sel.labelString = prompt
		text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		text.value = default
		self._form.ManageChild()
		toplevel._subwindows.append(self)

	def _ok(self, w, client_data, call_data):
		if self.is_closed():
			return
		value = call_data.value
		self.close()
		if client_data:
			client_data(value)

	def _cancel(self, w, client_data, call_data):
		if self.is_closed():
			return
		self.close()

	def setcursor(self, cursor):
		X_windowbase._setcursor(self._form, cursor)

	def close(self):
		if self._form:
			toplevel._subwindows.remove(self)
			self._form.UnmanageChild()
			self._form.DestroyWidget()
			self._form = None

	def is_closed(self):
		return self._form is None

[TOP, CENTER, BOTTOM] = range(3)

class _MenuSupport:
	'''Support methods for a pop up menu.'''
	def __init__(self):
		self._menu = None

	def close(self):
		'''Close the menu.'''
		self.destroy_menu()

	def create_menu(self, list, title = None):
		'''Create a popup menu.

		TITLE is the title of the menu.  If None or '', the
		menu will not have a title.  LIST is a list with menu
		entries.  Each entry is either None to get a
		separator, a string to get a label, or a tuple of two
		elements.  The first element is the label in the menu,
		the second argument is either a callback which is
		called when the menu entry is selected or a list which
		defines a cascading submenu.  A callback is either a
		callable object or a tuple consisting of a callable
		object and a tuple.  If the callback is just a
		callable object, it is called without arguments; if
		the callback is a tuple consisting of a callable
		object and a tuple, the object is called using apply
		with the tuple as argument.'''

		if self._form.IsSubclass(Xm.Gadget):
			raise error, 'cannot create popup menus on gadgets'
		self.destroy_menu()
		menu = self._form.CreatePopupMenu('dialogMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			list = [title, None] + list
		X_windowbase._create_menu(menu, list, toplevel._default_visual,
					  toplevel._default_colormap)
		self._menu = menu
		self._form.AddEventHandler(X.ButtonPressMask, FALSE,
					   self._post_menu, None)

	def destroy_menu(self):
		'''Destroy the pop up menu.

		This function is called automatically when a new menu
		is created using create_menu, or when the window
		object is closed.'''

		menu = self._menu
		self._menu = None
		if menu:
			self._form.RemoveEventHandler(X.ButtonPressMask, FALSE,
						      self._post_menu, None)
			menu.DestroyWidget()

	# support methods, only used by derived classes
	def _post_menu(self, w, client_data, call_data):
		if not self._menu:
			return
		if call_data.button == X.Button3:
			self._menu.MenuPosition(call_data)
			self._menu.ManageChild()

	def _destroy(self):
		self._menu = None

class _Widget(_MenuSupport):
	'''Support methods for all window objects.'''
	def __init__(self, parent, widget):
		self._parent = parent
		parent._children.append(self)
		self._showing = TRUE
		self._form = widget
		widget.ManageChild()
		_MenuSupport.__init__(self)
		self._form.AddCallback('destroyCallback', self._destroy, None)

	def __repr__(self):
		return '<_Widget instance at %x>' % id(self)

	def close(self):
		'''Close the window object.'''
		try:
			form = self._form
		except AttributeError:
			pass
		else:
			del self._form
			_MenuSupport.close(self)
			form.DestroyWidget()
		if self._parent:
			self._parent._children.remove(self)
		self._parent = None

	def is_closed(self):
		'''Returns true if the window is already closed.'''
		return not hasattr(self, '_form')

	def _showme(self, w):
		self._parent._showme(w)

	def _hideme(self, w):
		self._parent._hideme(w)

	def show(self):
		'''Make the window visible.'''
		self._parent._showme(self)
		self._showing = TRUE

	def hide(self):
		'''Make the window invisible.'''
		self._parent._hideme(self)
		self._showing = FALSE

	def is_showing(self):
		'''Returns true if the window is visible.'''
		return self._showing

	# support methods, only used by derived classes
	def _attachments(self, attrs, options):
		'''Calculate the attachments for this window.'''
		for pos in ['left', 'top', 'right', 'bottom']:
			attachment = pos + 'Attachment'
			try:
				widget = options[pos]
			except:
				pass
			else:
				if type(widget) in (FloatType, IntType):
					attrs[attachment] = \
						Xmd.ATTACH_POSITION
					attrs[pos + 'Position'] = \
						int(widget * 100 + .5)
				elif widget:
					attrs[pos + 'Attachment'] = \
						  Xmd.ATTACH_WIDGET
					attrs[pos + 'Widget'] = widget._form
				else:
					attrs[pos + 'Attachment'] = \
						  Xmd.ATTACH_FORM

	def _destroy(self, widget, client_data, call_data):
		'''Destroy callback.'''
		try:
			del self._form
		except AttributeError:
			return
		if self._parent:
			self._parent._children.remove(self)
		self._parent = None
		_MenuSupport._destroy(self)

class Label(_Widget):
	'''Label window object.'''
	def __init__(self, parent, text, useGadget = _def_useGadget,
		     name = 'windowLabel', **options):
		'''Create a Label subwindow.

		PARENT is the parent window, TEXT is the text for the
		label.  OPTIONS is an optional dictionary with
		options.  The only options recognized are the
		attachment options.'''
		attrs = {}
		self._attachments(attrs, options)
		if useGadget:
			label = Xm.LabelGadget
		else:
			label = Xm.Label
		label = parent._form.CreateManagedWidget(name, label, attrs)
		label.labelString = text
		self._text = text
		_Widget.__init__(self, parent, label)

	def __repr__(self):
		return '<Label instance at %x, text=%s>' % (id(self), self._text)

	def setlabel(self, text):
		'''Set the text of the label to TEXT.'''
		self._form.labelString = text
		self._text = text

class Button(_Widget):
	'''Button window object.'''
	def __init__(self, parent, label, callback, useGadget = _def_useGadget,
		     name = 'windowButton', **options):
		'''Create a Button subwindow.

		PARENT is the parent window, LABEL is the label on the
		button, CALLBACK is the callback function that is
		called when the button is activated.  The callback is
		a tuple consiting of a callable object and an argument
		tuple.'''
		self._text = label
		attrs = {'labelString': label}
		self._attachments(attrs, options)
		if useGadget:
			button = Xm.PushButtonGadget
		else:
			button = Xm.PushButton
		button = parent._form.CreateManagedWidget(name, button, attrs)
		if callback:
			button.AddCallback('activateCallback',
					   self._callback, callback)
		_Widget.__init__(self, parent, button)

	def __repr__(self):
		return '<Button instance at %x, text=%s>' % (id(self), self._text)

	def setlabel(self, text):
		self._form.labelString = text
		self._text = text

	def setsensitive(self, sensitive):
		self._form.sensitive = sensitive

	def _callback(self, widget, callback, call_data):
		if self.is_closed():
			return
		apply(callback[0], callback[1])

class OptionMenu(_Widget):
	'''Option menu window object.'''
	def __init__(self, parent, label, optionlist, startpos, cb,
		     useGadget = _def_useGadget, name = 'windowOptionMenu',
		     **options):
		'''Create an option menu window object.

		PARENT is the parent window, LABEL is a label for the
		option menu, OPTIONLIST is a list of options, STARTPOS
		gives the initial selected option, CB is the callback
		that is to be called when the option is changed,
		OPTIONS is an optional dictionary with options.
		If label is None, the label is not shown, otherwise it
		is shown to the left of the option menu.
		The optionlist is a list of strings.  Startpos is the
		index in the optionlist of the initially selected
		option.  The callback is either None, or a tuple of
		two elements.  If None, no callback is called when the
		option is changed, otherwise the the first element of
		the tuple is a callable object, and the second element
		is a tuple giving the arguments to the callable
		object.'''

		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		self._useGadget = useGadget
		initbut = self._do_setoptions(parent._form, optionlist,
					      startpos)
		attrs = {'menuHistory': initbut,
			 'subMenuId': self._omenu,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth}
		self._attachments(attrs, options)
		option = parent._form.CreateOptionMenu(name, attrs)
		if label is None:
			option.OptionLabelGadget().UnmanageChild()
			self._text = '<None>'
		else:
			option.labelString = label
			self._text = label
		self._callback = cb
		_Widget.__init__(self, parent, option)

	def __repr__(self):
		return '<OptionMenu instance at %x, label=%s>' % (id(self), self._text)

	def close(self):
		_Widget.close(self)
		self._callback = self._value = self._optionlist = \
				 self._buttons = None

	def getpos(self):
		'''Get the index of the currently selected option.'''
		return self._value

	def getvalue(self):
		'''Get the value of the currently selected option.'''
		return self._optionlist[self._value]

	def setpos(self, pos):
		'''Set the currently selected option to the index given by POS.'''
		if pos == self._value:
			return
		self._form.menuHistory = self._buttons[pos]
		self._value = pos

	def setsensitive(self, pos, sensitive):
		if 0 <= pos < len(self._buttons):
			self._buttons[pos].sensitive = sensitive
		else:
			raise error, 'pos out of range'

	def setvalue(self, value):
		'''Set the currently selected option to VALUE.'''
		self.setpos(self._optionlist.index(value))

	def setoptions(self, optionlist, startpos):
		'''Set new options.

		OPTIONLIST and STARTPOS are as in the __init__ method.'''

		if optionlist != self._optionlist:
			if self._useGadget:
				createfunc = self._omenu.CreatePushButtonGadget
			else:
				createfunc = self._omenu.CreatePushButton
			# reuse old menu entries or create new ones
			for i in range(len(optionlist)):
				item = optionlist[i]
				if i == len(self._buttons):
					button = createfunc(
						'windowOptionButton',
						{'labelString': item})
					button.AddCallback('activateCallback',
							   self._cb, i)
					button.ManageChild()
					self._buttons.append(button)
				else:
					button = self._buttons[i]
					button.labelString = item
			# delete superfluous menu entries
			n = len(optionlist)
			while len(self._buttons) > n:
				self._buttons[n].DestroyWidget()
				del self._buttons[n]
			self._optionlist = optionlist
		# set the start position
		self.setpos(startpos)

	def _do_setoptions(self, form, optionlist, startpos):
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		menu = form.CreatePulldownMenu('windowOption',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		self._omenu = menu
		self._optionlist = optionlist
		self._value = startpos
		self._buttons = []
		if self._useGadget:
			createfunc = menu.CreatePushButtonGadget
		else:
			createfunc = menu.CreatePushButton
		for i in range(len(optionlist)):
			item = optionlist[i]
			button = createfunc('windowOptionButton',
					    {'labelString': item})
			button.AddCallback('activateCallback', self._cb, i)
			button.ManageChild()
			if startpos == i:
				initbut = button
			self._buttons.append(button)
		return initbut

	def _cb(self, widget, value, call_data):
		if self.is_closed():
			return
		self._value = value
		if self._callback:
			f, a = self._callback
			apply(f, a)

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._omenu
		del self._optionlist
		del self._buttons
		del self._callback

class PulldownMenu(_Widget):
	'''Menu bar window object.'''
	def __init__(self, parent, menulist, useGadget = _def_useGadget,
		     name = 'menuBar', **options):
		'''Create a menu bar window object.

		PARENT is the parent window, MENULIST is a list giving
		the definition of the menubar, OPTIONS is an optional
		dictionary of options.
		The menulist is a list of tuples.  The first elements
		of the tuples is the name of the pulldown menu, the
		second element is a list with the definition of the
		pulldown menu.'''

		attrs = {}
		self._attachments(attrs, options)
		if useGadget:
			cascade = Xm.CascadeButtonGadget
		else:
			cascade = Xm.CascadeButton
		menubar = parent._form.CreateMenuBar(name, attrs)
		buttons = []
		for item, list in menulist:
			menu = menubar.CreatePulldownMenu('windowMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
			button = menubar.CreateManagedWidget(
				'windowMenuButton', cascade,
				{'labelString': item,
				 'subMenuId': menu})
			X_windowbase._create_menu(menu, list,
						  toplevel._default_visual,
						  toplevel._default_colormap)
			buttons.append(button)
		_Widget.__init__(self, parent, menubar)
		self._buttons = buttons

	def __repr__(self):
		return '<PulldownMenu instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._buttons = None

	def setmenu(self, pos, list):
		if not 0 <= pos < len(self._buttons):
			raise error, 'position out of range'
		button = self._buttons[pos]
		menu = self._form.CreatePulldownMenu('windowMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		X_windowbase._create_menu(menu, list,
					  toplevel._default_visual,
					  toplevel._default_colormap)
		omenu = button.subMenuId
		button.subMenuId = menu
		omenu.DestroyWidget()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons

# super class for Selection and List
class _List:
	def __init__(self, list, itemlist, initial, sel_cb):
		self._list = list
		list.ListAddItems(itemlist, 1)
		self._itemlist = itemlist
		if type(sel_cb) is ListType:
			if len(sel_cb) >= 1 and sel_cb[0]:
				list.AddCallback('singleSelectionCallback',
						 self._callback, sel_cb[0])
			if len(sel_cb) >= 2 and sel_cb[1]:
				list.AddCallback('defaultActionCallback',
						 self._callback, sel_cb[1])
		elif sel_cb:
			list.AddCallback('singleSelectionCallback',
					 self._callback, sel_cb)
		if itemlist:
			self.selectitem(initial)

	def close(self):
		self._itemlist = None
		self._list = None

	def getselected(self):
		pos = self._list.ListGetSelectedPos()
		if pos:
			return pos[0] - 1
		else:
			return None

	def getlistitem(self, pos):
		return self._itemlist[pos]

	def getlist(self):
		return self._itemlist

	def addlistitem(self, item, pos):
		if pos < 0:
			pos = len(self._itemlist)
		self._list.ListAddItem(item, pos + 1)
		self._itemlist.insert(pos, item)

	def addlistitems(self, items, pos):
		if pos < 0:
			pos = len(self._itemlist)
		self._list.ListAddItems(items, pos + 1)
		self._itemlist[pos:pos] = items

	def dellistitem(self, pos):
		del self._itemlist[pos]
		self._list.ListDeletePos(pos + 1)

	def dellistitems(self, poslist):
		self._list.ListDeletePositions(map(lambda x: x+1, poslist))
		list = poslist[:]
		list.sort()
		list.reverse()
		for pos in list:
			del self._itemlist[pos]

	def replacelistitem(self, pos, newitem):
		self.replacelistitems(pos, [newitem])

	def replacelistitems(self, pos, newitems):
		self._itemlist[pos:pos+len(newitems)] = newitems
		self._list.ListReplaceItemsPos(newitems, pos + 1)

	def delalllistitems(self):
		self._itemlist = []
		self._list.ListDeleteAllItems()

	def selectitem(self, pos):
		if pos is None:
			self._list.ListDeselectAllItems()
			return
		if pos < 0:
			pos = len(self._itemlist) - 1
		self._list.ListSelectPos(pos + 1, TRUE)

	def is_visible(self, pos):
		if pos < 0:
			pos = len(self._itemlist) - 1
		top = self._list.topItemPosition - 1
		vis = self._list.visibleItemCount
		return top <= pos < top + vis

	def scrolllist(self, pos, where):
		if pos < 0:
			pos = len(self._itemlist) - 1
		if where == TOP:
			self._list.ListSetPos(pos + 1)
		elif where == BOTTOM:
			self._list.ListSetBottomPos(pos + 1)
		elif where == CENTER:
			vis = self._list.visibleItemCount
			toppos = pos - vis / 2 + 1
			if toppos + vis > len(self._itemlist):
				toppos = len(self._itemlist) - vis + 1
			if toppos <= 0:
				toppos = 1
			self._list.ListSetPos(toppos)
		else:
			raise error, 'bad argument for scrolllist'


	def _callback(self, w, (func, arg), call_data):
		if self.is_closed():
			return
		apply(func, arg)

	def _destroy(self):
		del self._itemlist
		del self._list

class Selection(_Widget, _List):
	def __init__(self, parent, listprompt, itemprompt, itemlist, initial,
		     sel_cb, name = 'windowSelection', **options):
		attrs = {}
		self._attachments(attrs, options)
		selection = parent._form.CreateSelectionBox(name, attrs)
		for widget in Xmd.DIALOG_APPLY_BUTTON, \
		    Xmd.DIALOG_CANCEL_BUTTON, Xmd.DIALOG_DEFAULT_BUTTON, \
		    Xmd.DIALOG_HELP_BUTTON, Xmd.DIALOG_OK_BUTTON, \
		    Xmd.DIALOG_SEPARATOR:
			selection.SelectionBoxGetChild(widget).UnmanageChild()
		w = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		if listprompt is None:
			w.UnmanageChild()
			self._text = '<None>'
		else:
			w.labelString = listprompt
			self._text = listprompt
		w = selection.SelectionBoxGetChild(Xmd.DIALOG_SELECTION_LABEL)
		if itemprompt is None:
			w.UnmanageChild()
		else:
			w.labelString = itemprompt
		list = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST)
		list.selectionPolicy = Xmd.SINGLE_SELECT
		list.listSizePolicy = Xmd.CONSTANT
		if options.has_key('enterCallback'):
			cb = options['enterCallback']
			txt = selection.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
			txt.AddCallback('activateCallback', self._callback, cb)
		if options.has_key('changeCallback'):
			cb = options['changeCallback']
			txt = selection.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
			txt.AddCallback('valueChangedCallback', self._callback, cb)
		_List.__init__(self, list, itemlist, initial, sel_cb)
		_Widget.__init__(self, parent, selection)

	def __repr__(self):
		return '<Selection instance at %x; label=%s>' % (id(self), self._text)

	def close(self):
		_List.close(self)
		_Widget.close(self)

	def setlabel(self, label):
		w = self._form.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		w.labelString = label

	def getselection(self):
		text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		if hasattr(text, 'TextFieldGetString'):
			return text.TextFieldGetString()
		else:
			return text.TextGetString()

	def seteditable(self, editable):
		text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		text.editable = editable

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

class List(_Widget, _List):
	def __init__(self, parent, listprompt, itemlist, sel_cb,
		     rows = 10, useGadget = _def_useGadget,
		     name = 'windowList', **options):
		attrs = {'resizePolicy': parent.resizePolicy}
		self._attachments(attrs, options)
		if listprompt is not None:
			if useGadget:
				labelwidget = Xm.LabelGadget
			else:
				labelwidget = Xm.Label
			form = parent._form.CreateManagedWidget(
				'windowListForm', Xm.Form, attrs)
			label = form.CreateManagedWidget(name + 'Label',
					labelwidget,
					{'topAttachment': Xmd.ATTACH_FORM,
					 'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM})
			self._label = label
			label.labelString = listprompt
			attrs = {'topAttachment': Xmd.ATTACH_WIDGET,
				 'topWidget': label,
				 'leftAttachment': Xmd.ATTACH_FORM,
				 'rightAttachment': Xmd.ATTACH_FORM,
				 'bottomAttachment': Xmd.ATTACH_FORM,
				 'visibleItemCount': rows,
				 'selectionPolicy': Xmd.SINGLE_SELECT}
			if options.has_key('width'):
				attrs['width'] = options['width']
			if parent.resizePolicy == Xmd.RESIZE_ANY:
				attrs['listSizePolicy'] = \
							Xmd.RESIZE_IF_POSSIBLE
			else:
				attrs['listSizePolicy'] = Xmd.CONSTANT
			list = form.CreateScrolledList(name, attrs)
			list.ManageChild()
			widget = form
			self._text = listprompt
		else:
			attrs['visibleItemCount'] = rows
			attrs['selectionPolicy'] = Xmd.SINGLE_SELECT
			if parent.resizePolicy == Xmd.RESIZE_ANY:
				attrs['listSizePolicy'] = \
							Xmd.RESIZE_IF_POSSIBLE
			else:
				attrs['listSizePolicy'] = Xmd.CONSTANT
			if options.has_key('width'):
				attrs['width'] = options['width']
			list = parent._form.CreateScrolledList(name, attrs)
			widget = list
			self._text = '<None>'
		_List.__init__(self, list, itemlist, 0, sel_cb)
		_Widget.__init__(self, parent, widget)

	def __repr__(self):
		return '<List instance at %x; label=%s>' % (id(self), self._text)

	def close(self):
		_List.close(self)
		_Widget.close(self)

	def setlabel(self, label):
		try:
			self._label.labelString = label
		except AttributeError:
			raise error, 'List created without label'
		else:
			self._text = label

	def _destroy(self, widget, value, call_data):
		try:
			del self._label
		except AttributeError:
			pass
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

class TextInput(_Widget):
	def __init__(self, parent, prompt, inittext, chcb, accb,
		     useGadget = _def_useGadget, name = 'windowTextfield',
		     modifyCB = None,
		     **options):
		attrs = {}
		self._attachments(attrs, options)
		if prompt is not None:
			if useGadget:
				labelwidget = Xm.LabelGadget
			else:
				labelwidget = Xm.Label
			form = parent._form.CreateManagedWidget(
				name + 'Form', Xm.Form, attrs)
			label = form.CreateManagedWidget(
				name + 'Label', labelwidget,
				{'topAttachment': Xmd.ATTACH_FORM,
				 'leftAttachment': Xmd.ATTACH_FORM,
				 'bottomAttachment': Xmd.ATTACH_FORM})
			self._label = label
			label.labelString = prompt
			attrs = {'topAttachment': Xmd.ATTACH_FORM,
				 'leftAttachment': Xmd.ATTACH_WIDGET,
				 'leftWidget': label,
				 'bottomAttachment': Xmd.ATTACH_FORM,
				 'rightAttachment': Xmd.ATTACH_FORM}
			widget = form
		else:
			form = parent._form
			widget = None
		if options.has_key('columns'):
			attrs['columns'] = options['columns']
		attrs['value'] = inittext
		if options.has_key('editable'):
			attrs['editable'] = options['editable']
		self._text = text = form.CreateTextField(name, attrs)
		text.ManageChild()
		if not widget:
			widget = text
		if chcb:
			text.AddCallback('valueChangedCallback',
					 self._callback, chcb)
		if accb:
			text.AddCallback('activateCallback',
					 self._callback, accb)
		if modifyCB:
			text.AddCallback('modifyVerifyCallback',
					 self._modifyCB, modifyCB)
		_Widget.__init__(self, parent, widget)

	def __repr__(self):
		return '<TextInput instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._text = None

	def setlabel(self, label):
		if not hasattr(self, '_label'):
			raise error, 'TextInput create without label'
		self._label.labelString = label

	def gettext(self):
		return self._text.TextFieldGetString()

	def settext(self, text):
		self._text.value = text

	def setfocus(self):
		self._text.ProcessTraversal(Xmd.TRAVERSE_CURRENT)

	def _callback(self, w, (func, arg), call_data):
		if self.is_closed():
			return
		apply(func, arg)

	def _modifyCB(self, w, func, call_data):
		text = func(call_data.text)
		if text is not None:
			call_data.text = text

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		try:
			del self._label
		except AttributeError:
			pass
		del self._text

class TextEdit(_Widget):
	def __init__(self, parent, inittext, cb, name = 'windowText',
		     **options):
		attrs = {'editMode': Xmd.MULTI_LINE_EDIT,
			 'editable': TRUE,
			 'rows': 10}
		for option in ['editable', 'rows', 'columns']:
			if options.has_key(option):
				attrs[option] = options[option]
		if not attrs['editable']:
			attrs['cursorPositionVisible'] = FALSE
		self._attachments(attrs, options)
		text = parent._form.CreateScrolledText(name, attrs)
		if cb:
			text.AddCallback('activateCallback', self._callback,
					 cb)
		_Widget.__init__(self, parent, text)
		self.settext(inittext)

	def __repr__(self):
		return '<TextEdit instance at %x>' % id(self)

	def settext(self, text):
		if type(text) is ListType:
			text = string.joinfields(text, '\n')
		self._form.TextSetString(text)
		self._linecache = None

	def gettext(self):
		return self._form.TextGetString()

	def getlines(self):
		text = self.gettext()
		text = string.splitfields(text, '\n')
		if len(text) > 0 and text[-1] == '':
			del text[-1]
		return text

	def _mklinecache(self):
		text = self.getlines()
		self._linecache = c = []
		pos = 0
		for line in text:
			c.append(pos)
			pos = pos + len(line) + 1

	def getline(self, line):
		lines = self.getlines()
		if line < 0 or line >= len(lines):
			line = len(lines) - 1
		return lines[line]

	def scrolltext(self, line, where):
		if not self._linecache:
			self._mklinecache()
		if line < 0 or line >= len(self._linecache):
			line = len(self._linecache) - 1
		if where == TOP:
			pass
		else:
			rows = self._form.rows
			if where == BOTTOM:
				line = line - rows + 1
			elif where == CENTER:
				line = line - rows/2 + 1
			else:
				raise error, 'bad argument for scrolltext'
			if line < 0:
				line = 0
		self._form.TextSetTopCharacter(self._linecache[line])

	def selectchars(self, line, start, end):
		if not self._linecache:
			self._mklinecache()
		if line < 0 or line >= len(self._linecache):
			line = len(self._linecache) - 1
		pos = self._linecache[line]
		self._form.TextSetSelection(pos + start, pos + end, 0)

	def _callback(self, w, (func, arg), call_data):
		if self.is_closed():
			return
		apply(func, arg)

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._linecache

class Separator(_Widget):
	def __init__(self, parent, useGadget = _def_useGadget,
		     name = 'windowSeparator', **options):
		attrs = {}
		self._attachments(attrs, options)
		if useGadget:
			separator = Xm.SeparatorGadget
		else:
			separator = Xm.Separator
		separator = parent._form.CreateManagedWidget(name, separator,
							     attrs)
		_Widget.__init__(self, parent, separator)

	def __repr__(self):
		return '<Separator instance at %x>' % id(self)

class ButtonRow(_Widget):
	def __init__(self, parent, buttonlist,
		     vertical = 1, callback = None,
		     buttontype = 'pushbutton', useGadget = _def_useGadget,
		     name = 'windowRowcolumn', **options):
		attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
			 'traversalOn': FALSE}
		if not vertical:
			attrs['orientation'] = Xmd.HORIZONTAL
		if options.get('tight', 0):
			attrs['packing'] = Xmd.PACK_COLUMN
		self._cb = callback
		if useGadget:
			separator = Xm.SeparatorGadget
			cascadebutton = Xm.CascadeButtonGadget
			pushbutton = Xm.PushButtonGadget
			togglebutton = Xm.ToggleButtonGadget
		else:
			separator = Xm.Separator
			cascadebutton = Xm.CascadeButton
			pushbutton = Xm.PushButton
			togglebutton = Xm.ToggleButton
		self._attachments(attrs, options)
		rowcolumn = parent._form.CreateManagedWidget(name,							Xm.RowColumn, attrs)
		self._buttons = []
		for entry in buttonlist:
			if entry is None:
				if vertical:
					attrs = {'orientation': Xmd.HORIZONTAL}
				else:
					attrs = {'orientation': Xmd.VERTICAL}
				dummy = rowcolumn.CreateManagedWidget(
					'buttonSeparator', separator, attrs)
				continue
			btype = buttontype
			if type(entry) is TupleType:
				label, callback = entry[:2]
				if len(entry) > 2:
					btype = entry[2]
			else:
				label, callback = entry, None
			if type(callback) is ListType:
				menu = rowcolumn.CreateMenuBar('submenu', {})
				submenu = menu.CreatePulldownMenu(
					'submenu',
					{'colormap': toplevel._default_colormap,
					'visual': toplevel._default_visual,
					 'depth': toplevel._default_visual.depth})
				button = menu.CreateManagedWidget(
					'submenuLabel', cascadebutton,
					{'labelString': label,
					 'subMenuId': submenu})
				X_windowbase._create_menu(submenu, callback,
					  toplevel._default_visual,
					  toplevel._default_colormap)
				menu.ManageChild()
				continue
			if callback and type(callback) is not TupleType:
				callback = (callback, (label,))
			if btype[0] in ('b', 'p'): # push button
				gadget = pushbutton
				battrs = {}
				callbackname = 'activateCallback'
			elif btype[0] == 't': # toggle button
				gadget = togglebutton
				battrs = {'indicatorType': Xmd.N_OF_MANY}
				callbackname = 'valueChangedCallback'
			elif btype[0] == 'r': # radio button
				gadget = togglebutton
				battrs = {'indicatorType': Xmd.ONE_OF_MANY}
				callbackname = 'valueChangedCallback'
			else:
				raise error, 'bad button type'
			battrs['labelString'] = label
			button = rowcolumn.CreateManagedWidget('windowButton',
					gadget, battrs)
			if callback or self._cb:
				button.AddCallback(callbackname,
						   self._callback, callback)
			self._buttons.append(button)
		_Widget.__init__(self, parent, rowcolumn)

	def __repr__(self):
		return '<ButtonRow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._buttons = None
		self._cb = None

	def hide(self, button = None):
		if button is None:
			_Widget.hide(self)
			return
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		self._buttons[button].UnmanageChild()

	def show(self, button = None):
		if button is None:
			_Widget.show(self)
			return
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		self._buttons[button].ManageChild()

	def getbutton(self, button):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		return self._buttons[button].set

	def setbutton(self, button, onoff = 1):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		button = self._buttons[button]
		button.set = onoff

	def setsensitive(self, button, sensitive):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		self._buttons[button].sensitive = sensitive

	def _callback(self, widget, callback, call_data):
		if self.is_closed():
			return
		if self._cb:
			apply(self._cb[0], self._cb[1])
		if callback:
			apply(callback[0], callback[1])

	def _popup(self, widget, submenu, call_data):
		submenu.ManageChild()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons
		del self._cb

class Slider(_Widget):
	def __init__(self, parent, prompt, minimum, initial, maximum, cb,
		     vertical = 0, showvalue = 1, name = 'windowScale',
		     **options):
		if vertical:
			orientation = Xmd.VERTICAL
		else:
			orientation = Xmd.HORIZONTAL
		self._orientation = orientation
		direction, minimum, initial, maximum, decimal, factor = \
			   self._calcrange(minimum, initial, maximum)
		attrs = {'minimum': minimum,
			 'maximum': maximum,
			 'processingDirection': direction,
			 'decimalPoints': decimal,
			 'orientation': orientation,
			 'showValue': showvalue,
			 'value': initial}
		self._attachments(attrs, options)
		scale = parent._form.CreateScale(name, attrs)
		if cb:
			scale.AddCallback('valueChangedCallback',
					  self._callback, cb)
		if prompt is None:
			for w in scale.GetChildren():
				if w.Name() == 'Title':
					w.UnmanageChild()
					break
		else:
			scale.titleString = prompt
		_Widget.__init__(self, parent, scale)

	def __repr__(self):
		return '<Slider instance at %x>' % id(self)

	def getvalue(self):
		return self._form.ScaleGetValue() / self._factor

	def setvalue(self, value):
		value = int(value * self._factor + .5)
		self._form.ScaleSetValue(value)

	def setrange(self, minimum, maximum):
		direction, minimum, initial, maximum, decimal, factor = \
			   self._calcrange(minimum, self.getvalue(), maximum)
		self._form.SetValues({'minimum': minimum,
				      'maximum': maximum,
				      'processingDirection': direction,
				      'decimalPoints': decimal,
				      'value': initial})

	def getrange(self):
		return self._minimum, self._maximum

	def _callback(self, widget, callback, call_data):
		if self.is_closed():
			return
		apply(callback[0], callback[1])

	def _calcrange(self, minimum, initial, maximum):
		self._minimum, self._maximum = minimum, maximum
		range = maximum - minimum
		if range < 0:
			if self._orientation == Xmd.VERTICAL:
				direction = Xmd.MAX_ON_BOTTOM
			else:
				direction = Xmd.MAX_ON_LEFT
			range = -range
			minimum, maximum = maximum, minimum
		else:
			if self._orientation == Xmd.VERTICAL:
				direction = Xmd.MAX_ON_TOP
			else:
				direction = Xmd.MAX_ON_RIGHT
		decimal = 0
		factor = 1
		if FloatType in [type(minimum), type(maximum)]:
			factor = 1.0
		while 0 < range <= 10:
			range = range * 10
			decimal = decimal + 1
			factor = factor * 10
		self._factor = factor
		return direction, int(minimum * factor + .5), \
		       int(initial * factor + .5), \
		       int(maximum * factor + .5), decimal, factor

class _WindowHelpers:
	def __init__(self):
		self._fixkids = []
		self._fixed = FALSE
		self._children = []

	def close(self):
		self._fixkids = None
		for w in self._children[:]:
			w.close()

	# items with which a window can be filled in
	def Label(self, text, **options):
		return apply(Label, (self, text), options)
	def Button(self, label, callback, **options):
		return apply(Button, (self, label, callback), options)
	def OptionMenu(self, label, optionlist, startpos, cb, **options):
		return apply(OptionMenu,
			     (self, label, optionlist, startpos, cb),
			     options)
	def PulldownMenu(self, menulist, **options):
		return apply(PulldownMenu, (self, menulist), options)
	def Selection(self, listprompt, itemprompt, itemlist, initial, sel_cb,
		      **options):
		return apply(Selection,
			     (self, listprompt, itemprompt, itemlist, initial,
			      sel_cb),
			     options)
	def List(self, listprompt, itemlist, sel_cb, **options):
		return apply(List,
			     (self, listprompt, itemlist, sel_cb), options)
	def TextInput(self, prompt, inittext, chcb, accb, **options):
		return apply(TextInput,
			     (self, prompt, inittext, chcb, accb), options)
	def TextEdit(self, inittext, cb, **options):
		return apply(TextEdit, (self, inittext, cb), options)
	def Separator(self, **options):
		return apply(Separator, (self,), options)
	def ButtonRow(self, buttonlist, **options):
		return apply(ButtonRow, (self, buttonlist), options)
	def Slider(self, prompt, minimum, initial, maximum, cb, **options):
		return apply(Slider,
			     (self, prompt, minimum, initial, maximum, cb),
			     options)
	def SubWindow(self, **options):
		return apply(SubWindow, (self,), options)
	def AlternateSubWindow(self, **options):
		return apply(AlternateSubWindow, (self,), options)

class SubWindow(_Widget, _WindowHelpers):
	def __init__(self, parent, name = 'windowSubwindow', **options):
		attrs = {'resizePolicy': parent.resizePolicy}
		self.resizePolicy = parent.resizePolicy
		self._attachments(attrs, options)
		form = parent._form.CreateManagedWidget(name, Xm.Form, attrs)
		_WindowHelpers.__init__(self)
		_Widget.__init__(self, parent, form)
		parent._fixkids.append(self)

	def __repr__(self):
		return '<SubWindow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		_WindowHelpers.close(self)

	def fix(self):
		for w in self._fixkids:
			w.fix()
		self._form.ManageChild()
		self._fixed = TRUE

	def show(self):
		_Widget.show(self)
		if self._fixed:
			for w in self._fixkids:
				if w.is_showing():
					w.show()
				else:
					w.hide()
			self._fixkids = []

class _AltSubWindow(SubWindow):
	def __init__(self, parent, name):
		self._parent = parent
		SubWindow.__init__(self, parent, left = None, right = None,
				   top = None, bottom = None, name = name)

	def show(self):
		for w in self._parent._windows:
			w.hide()
		SubWindow.show(self)

class AlternateSubWindow(_Widget):
	def __init__(self, parent, name = 'windowAlternateSubwindow',
		     **options):
		attrs = {'resizePolicy': parent.resizePolicy,
			 'allowOverlap': TRUE}
		self.resizePolicy = parent.resizePolicy
		self._attachments(attrs, options)
		form = parent._form.CreateManagedWidget(name, Xm.Form, attrs)
		self._windows = []
		_Widget.__init__(self, parent, form)
		parent._fixkids.append(self)
		self._fixkids = []
		self._children = []

	def __repr__(self):
		return '<AlternateSubWindow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._windows = None
		self._fixkids = None

	def SubWindow(self, name = 'windowSubwindow'):
		widget = _AltSubWindow(self, name = name)
		for w in self._windows:
			w.hide()
		self._windows.append(widget)
		return widget

	def fix(self):
		for w in self._fixkids:
			w.fix()
		for w in self._windows:
			w._form.ManageChild()

class Window(_WindowHelpers, _MenuSupport):
	def __init__(self, title, resizable = 0, grab = 0,
		     Name = 'windowShell', Class = None, **options):
		if not resizable:
			self.resizePolicy = Xmd.RESIZE_NONE
		else:
			self.resizePolicy = Xmd.RESIZE_ANY
		if not title:
			title = ''
		self._title = title
		wattrs = {'title': title,
			  'minWidth': 60, 'minHeight': 60,
			  'colormap': toplevel._default_colormap,
			  'visual': toplevel._default_visual,
			  'depth': toplevel._default_visual.depth}
		attrs = {'allowOverlap': FALSE,
			 'resizePolicy': self.resizePolicy}
		if not resizable:
			attrs['noResize'] = TRUE
			attrs['resizable'] = FALSE
		if grab:
			attrs['dialogStyle'] = \
					     Xmd.DIALOG_FULL_APPLICATION_MODAL
			for key, val in wattrs.items():
				attrs[key] = val
			self._form = toplevel._main.CreateFormDialog(
				'grabDialog', attrs)
		else:
			wattrs['iconName'] = title
			self._shell = toplevel._main.CreatePopupShell(Name,
				Xt.ApplicationShell, wattrs)
			self._form = self._shell.CreateManagedWidget(
				'windowForm', Xm.Form, attrs)
			if options.has_key('deleteCallback'):
				deleteCallback = options['deleteCallback']
				self._shell.AddWMProtocolCallback(
					toplevel._delete_window,
					self._delete_callback,
					deleteCallback)
				self._shell.deleteResponse = Xmd.DO_NOTHING
		self._showing = FALSE
		self._not_shown = []
		self._shown = []
		_WindowHelpers.__init__(self)
		_MenuSupport.__init__(self)
		toplevel._subwindows.append(self)

	def __repr__(self):
		s = '<Window instance at %x' % id(self)
		if hasattr(self, '_title'):
			s = s + ', title=' + `self._title`
		if self.is_closed():
			s = s + ' (closed)'
		elif self._showing:
			s = s + ' (showing)'
		s = s + '>'
		return s

	def close(self):
		try:
			form = self._form
		except AttributeError:
			return
		try:
			shell = self._shell
		except AttributeError:
			shell = None
		toplevel._subwindows.remove(self)
		del self._form
		form.DestroyWidget()
		del form
		if shell:
			shell.UnmanageChild()
			shell.DestroyWidget()
			del self._shell
			del shell
		_WindowHelpers.close(self)
		_MenuSupport.close(self)

	def is_closed(self):
		return not hasattr(self, '_form')

	def setcursor(self, cursor):
		X_windowbase._setcursor(self._form, cursor)

	def fix(self):
		for w in self._fixkids:
			w.fix()
		self._form.ManageChild()
		try:
			self._shell.RealizeWidget()
		except AttributeError:
			pass
		self._fixed = TRUE

	def _showme(self, w):
		if self.is_closed():
			return
		if self.is_showing():
			if not w._form.IsSubclass(Xm.Gadget):
				w._form.MapWidget()
		elif w in self._not_shown:
			self._not_shown.remove(w)
		elif w not in self._shown:
			self._shown.append(w)

	def _hideme(self, w):
		if self.is_closed():
			return
		if self.is_showing():
			if not w._form.IsSubclass(Xm.Gadget):
				w._form.UnmapWidget()
		elif w in self._shown:
			self._shown.remove(w)
		elif w not in self._not_shown:
			self._not_shown.append(w)

	def show(self):
		if not self._fixed:
			self.fix()
		try:
			self._shell.Popup(0)
		except AttributeError:
			pass
		self._showing = TRUE
		for w in self._not_shown:
			if not w.is_closed() and \
			   not w._form.IsSubclass(Xm.Gadget):
				w._form.UnmapWidget()
		for w in self._shown:
			if not w.is_closed() and \
			   not w._form.IsSubclass(Xm.Gadget):
				w._form.MapWidget()
		self._not_shown = []
		self._shown = []
		for w in self._fixkids:
			if w.is_showing():
				w.show()
			else:
				w.hide()
		self._fixkids = []

	def hide(self):
		try:
			self._shell.Popdown()
		except AttributeError:
			pass
		self._showing = FALSE

	def is_showing(self):
		return self._showing

	def settitle(self, title):
		if self._title != title:
			try:
				self._shell.title = title
				self._shell.iconName = title
			except AttributeError:
				self._form.dialogTitle = title
			self._title = title

	def getgeometry(self):
		if self.is_closed():
			raise error, 'window already closed'
		x, y  = self._form.TranslateCoords(0, 0)
		val = self._form.GetValues(['width', 'height'])
		w = val['width']
		h = val['height']
		return x / toplevel._hmm2pxl, y / toplevel._vmm2pxl, \
		       w / toplevel._hmm2pxl, h / toplevel._vmm2pxl

	def pop(self):
		try:
			self._shell.Popup(0)
		except AttributeError:
			pass

	def _delete_callback(self, widget, client_data, call_data):
		if type(client_data) is StringType:
			if client_data == 'hide':
				self.hide()
			elif client_data == 'close':
				self.close()
			else:
				raise error, 'bad deleteCallback argument'
			return
		func, args = client_data
		apply(func, args)

def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1):
	w = Window(title, grab = grab)
	options = {'top': None, 'left': None, 'right': None}
	if prompt:
		l = apply(w.Label, (prompt,), options)
		options['top'] = l
	options['vertical'] = vertical
	if grab:
		options['callback'] = (lambda w: w.close(), (w,))
	b = apply(w.ButtonRow, (list,), options)
	w.buttons = b
	w.show()
	return w

_end_loop = '_end_loop'			# exception for ending a loop

class _Question:
	def __init__(self, text):
		self.looping = FALSE
		self.answer = None
		showmessage(text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)))

	def run(self):
		try:
			self.looping = TRUE
			Xt.MainLoop()
		except _end_loop:
			pass
		return self.answer

	def callback(self, answer):
		self.answer = answer
		if self.looping:
			raise _end_loop

def showquestion(text):
	return _Question(text).run()

class _MultChoice:
	def __init__(self, prompt, msg_list, defindex):
		self.looping = FALSE
		self.answer = None
		self.msg_list = msg_list
		list = []
		for msg in msg_list:
			list.append(msg, (self.callback, (msg,)))
		self.dialog = Dialog(list, title = None, prompt = prompt,
				     grab = TRUE, vertical = FALSE)

	def run(self):
		try:
			self.looping = TRUE
			Xt.MainLoop()
		except _end_loop:
			pass
		return self.answer

	def callback(self, msg):
		for i in range(len(self.msg_list)):
			if msg == self.msg_list[i]:
				self.answer = i
				if self.looping:
					raise _end_loop
				return

def multchoice(prompt, list, defindex):
	return _MultChoice(prompt, list, defindex).run()

fonts = X_windowbase.fonts

X_windowbase.toplevel = toplevel

newwindow = toplevel.newwindow

newcmwindow = toplevel.newcmwindow

close = toplevel.close

addclosecallback = toplevel.addclosecallback

setcursor = toplevel.setcursor

getsize = toplevel.getsize

usewindowlock = toplevel.usewindowlock

settimer = toplevel.settimer

select_setcallback = toplevel.select_setcallback

mainloop = toplevel.mainloop

canceltimer = toplevel.canceltimer

getscreensize = toplevel.getscreensize

getscreendepth = toplevel.getscreendepth

lopristarting = X_windowbase.lopristarting
