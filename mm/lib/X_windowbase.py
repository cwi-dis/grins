import Xt, Xm, X, Xmd, Xtdefs, Xcursorfont, Xlib
import img, imgformat, imageop
import string, tempfile
import math
from EVENTS import *
from types import *

error = 'windowinterface.error'
FALSE, TRUE = X.FALSE, X.TRUE
ReadMask, WriteMask = 1, 2

Version = 'X'

# Colors
_DEF_BGCOLOR = 255,255,255		# white
_DEF_FGCOLOR =   0,  0,  0		# black

# These variables are filled in by the _Toplevel.__init__() method
# when the module is initialized.
_mscreenwidth = 0
_mscreenheight = 0
_screenwidth = 0
_screenheight = 0
_dpi_x = 0
_dpi_y = 0
_watchcursor = 0
_channelcursor = 0
_linkcursor = 0
_stopcursor = 0
_delete_window = 0

_image_cache = {}		# cache of prepared images
_cache_full = FALSE		# TRUE if we shouldn't cache more images
_image_size_cache = {}
_cm_cache = {}

def roundi(x):
	if x < 0:
		return roundi(x + 1024) - 1024
	return int(x + 0.5)

myxrgb8 = imgformat.xrgb8

def _colormask(mask):
	shift = 0
	while (mask & 1) == 0:
		shift = shift + 1
		mask = mask >> 1
	if mask < 0:
		width = 32 - i	# assume integers are 32 bits
	else:
		width = 0
		while mask != 0:
			width = width + 1
			mask = mask >> 1
	return shift, (1 << width) - 1

def _setupimg(rs, rm, gs, gm, bs, bm):
	global myxrgb8
	r, g, b = imgformat.xrgb8.descr['comp'][:3]
	xrs, xrm = r[0], (1 << r[1]) - 1
	xgs, xgm = g[0], (1 << g[1]) - 1
	xbs, xbm = b[0], (1 << b[1]) - 1
	c = []
	if (rm, gm, bm) != (xrm, xgm, xbm):
		for n in range(256):
			r = roundi(((n >> xrs) & xrm) / float(xrm) * rm)
			g = roundi(((n >> xgs) & xgm) / float(xgm) * gm)
			b = roundi(((n >> xbs) & xbm) / float(xbm) * bm)
			c.append((r << rs) | (g << gs) | (b << bs))
		lossy = 2
	elif (rs, gs, bs) == (xrs, xgs, xbs):
		# no need for extra conversion
		return
	else:
		for n in range(256):
			r = (n >> xrs) & xgm
			g = (n >> xgs) & xgm
			b = (n >> xbs) & xbm
			c.append((r << rs) | (g << gs) | (b << bs))
		lossy = 0
	import imgcolormap, imgconvert
	myxrgb8 = imgformat.new('myxrgb8', 'X 3:3:2 RGB top-to-bottom')
	cmap = imgcolormap.new(reduce(lambda x, y: x + '000' + chr(y), c, ''))
	imgconvert.addconverter(imgformat.xrgb8, imgformat.myxrgb8,
				lambda d, r, m=cmap: m.map8(d), lossy)

def _setcursor(form, cursor):
	if cursor == 'watch':
		form.DefineCursor(_watchcursor)
	elif cursor == 'channel':
		form.DefineCursor(_channelcursor)
	elif cursor == 'link':
		form.DefineCursor(_linkcursor)
	elif cursor == 'stop':
		form.DefineCursor(_stopcursor)
	elif cursor == '':
		form.UndefineCursor()
	else:
		raise error, 'unknown cursor glyph'

# three menu utility functions
def _generic_callback(widget, (func, arg), call_data):
	apply(func, arg)

def _create_menu(menu, list, acc = None):
	accelerator = None
	for entry in list:
		if entry is None:
			dummy = menu.CreateManagedWidget('separator',
							 Xm.SeparatorGadget,
							 {})
			continue
		if type(entry) is StringType:
			dummy = menu.CreateManagedWidget(
				'menuLabel', Xm.LabelGadget,
				{'labelString': entry})
			continue
		if acc is None:
			label, callback = entry
		else:
			accelerator, label, callback = entry
		if type(callback) is ListType:
			submenu = menu.CreatePulldownMenu('submenu', {})
			button = menu.CreateManagedWidget(
				'submenuLabel', Xm.CascadeButtonGadget,
				{'labelString': label, 'subMenuId': submenu})
			_create_menu(submenu, callback, acc)
		else:
			if type(callback) is not TupleType:
				callback = (callback, (label,))
			attrs = {'labelString': label}
			if accelerator:
				if type(accelerator) is not StringType or \
				   len(accelerator) != 1:
					raise error, 'menu accelerator must be single character'
				acc[accelerator] = callback
				attrs['acceleratorText'] = accelerator
			button = menu.CreateManagedWidget('menuLabel',
						Xm.PushButtonGadget, attrs)
			button.AddCallback('activateCallback',
					   _generic_callback, callback)

class _Toplevel:
	def __init__(self):
		global _mscreenwidth
		global _mscreenheight
		global _screenwidth
		global _screenheight
		global _dpi_x
		global _dpi_y
		global _watchcursor
		global _channelcursor
		global _linkcursor
		global _stopcursor
		global _delete_window
		self._toplevel = self
		import sys
		Xt.ToolkitInitialize()
		dpy = Xt.OpenDisplay(None, None, 'Windowinterface', [], sys.argv)
		_delete_window = dpy.InternAtom('WM_DELETE_WINDOW', FALSE)
		self._setupcolormap(dpy)
		self._main = Xt.CreateApplicationShell('shell',
					Xt.ApplicationShell,
					{'visual': self._visual,
					 'colormap': self._colormap,
					 'depth': self._depth,
					 'mappedWhenManaged': FALSE,
					 'x': 500,
					 'y': 500,
					 'width': 1,
					 'height': 1,
					 'input': TRUE})
		_mscreenwidth = self._main.WidthMMOfScreen()
		_mscreenheight = self._main.HeightMMOfScreen()
		_screenwidth = self._main.WidthOfScreen()
		_screenheight = self._main.HeightOfScreen()
		self._default_colormap = self._main.DefaultColormapOfScreen()
		self._default_visual = self._main.DefaultVisualOfScreen()
		_dpi_x = int(_screenwidth * 25.4 / _mscreenwidth + .5)
		_dpi_y = int(_screenheight * 25.4 / _mscreenheight + .5)
		self._parent_window = None
		self._subwindows = []
		self._fgcolor = _DEF_FGCOLOR
		self._bgcolor = _DEF_BGCOLOR
		self._cursor = ''
		_watchcursor = dpy.CreateFontCursor(Xcursorfont.watch)
		_channelcursor = dpy.CreateFontCursor(Xcursorfont.draped_box)
		_linkcursor = dpy.CreateFontCursor(Xcursorfont.hand1)
		_stopcursor = dpy.CreateFontCursor(Xcursorfont.pirate)
		self._main.RealizeWidget()
		self._fdmap = {}
		self._closecallbacks = []

	def _setupcolormap(self, dpy):
		visattr = {'class': X.TrueColor}
##		visattr['depth'] = 8	# DEBUG--force 8-bit visual
		visuals = dpy.GetVisualInfo(visattr)
		if visuals:
			# found one, use the deepest
			v_best = visuals[0]
			for v in visuals:
				if v.depth > v_best.depth:
					v_best = v
			self._visual = v_best
			self._depth = v_best.depth
			self._red_shift, self._red_mask = \
					 _colormask(v_best.red_mask)
			self._green_shift, self._green_mask = \
					   _colormask(v_best.green_mask)
			self._blue_shift, self._blue_mask = \
					  _colormask(v_best.blue_mask)
			self._colormap = v_best.CreateColormap(X.AllocNone)
			if self._depth == 8:
				_setupimg(self._red_shift, self._red_mask,
					  self._green_shift, self._green_mask,
					  self._blue_shift, self._blue_mask)
			return
		visuals = dpy.GetVisualInfo({'depth': 8,
					     'class': X.PseudoColor})
		if len(visuals) == 0:
			raise error, 'no proper visuals available'
		self._visual = visuals[0]
		self._depth = self._visual.depth
		self._colormap = self._visual.CreateColormap(X.AllocNone)
		r, g, b = imgformat.xrgb8.descr['comp'][:3]
		self._red_shift,   self._red_mask   = r[0], (1 << r[1]) - 1
		self._green_shift, self._green_mask = g[0], (1 << g[1]) - 1
		self._blue_shift,  self._blue_mask  = b[0], (1 << b[1]) - 1
		(plane_masks, pixels) = self._colormap.AllocColorCells(1, 8, 1)
		xcolors = []
		for n in range(256):
			# The colormap is set up so that the colormap
			# index has the meaning: rrrbbggg (same as
			# imgformat.xrgb8).
			xcolors.append((n+pixels[0],
				  int((float((n >> self._red_shift) & self._red_mask) / float(self._red_mask)) * 255.)<<8,
				  int((float((n >> self._green_shift) & self._green_mask) / float(self._green_mask)) * 255.)<<8,
				  int((float((n >> self._blue_shift) & self._blue_mask) / float(self._blue_mask)) * 255.)<<8,
				  X.DoRed|X.DoGreen|X.DoBlue))
		self._colormap.StoreColors(xcolors)
		_setupimg(self._red_shift, self._red_mask,
			  self._green_shift, self._green_mask,
			  self._blue_shift, self._blue_mask)
		return

	def close(self):
		import os
		global _image_cache
		for func, args in self._closecallbacks:
			apply(func, args)
		self._closecallbacks = []
		for win in self._subwindows[:]:
			win.close()
		for key in _image_cache.keys():
			try:
				os.unlink(_image_cache[key][-1])
			except os.error:
				pass
		_image_cache = {}

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	def newwindow(self, x, y, w, h, title, **options):
		window = apply(_Window, (self, x, y, w, h, title, FALSE), options)
		return window

	def newcmwindow(self, x, y, w, h, title, **options):
		window = apply(_Window, (self, x, y, w, h, title, TRUE), options)
		return window

	def setcursor(self, cursor):
		for win in self._subwindows:
			win.setcursor(cursor)
		self._cursor = cursor

	def pop(self):
		pass

	def push(self):
		pass

	def usewindowlock(self, lock):
		pass

	def mainloop(self):
		Xt.MainLoop()

	# timer interface
	def settimer(self, sec, cb):
		id = Xt.AddTimeOut(int(sec * 1000), self._timer_callback, cb)
		return id

	def canceltimer(self, id):
		if id is not None:
			Xt.RemoveTimeOut(id)

	def _timer_callback(self, client_data, id):
		func, args = client_data
		apply(func, args)

	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		if type(fd) is not IntType:
			fd = fd.fileno()
		try:
			id = self._fdmap[fd]
		except KeyError:
			pass
		else:
			Xt.RemoveInput(id)
			del self._fdmap[fd]
		if func is None:
			return
		xmask = 0
		if mask & ReadMask:
			xmask = xmask | Xtdefs.XtInputReadMask
		if mask & WriteMask:
			xmask = xmask | Xtdefs.XtInputWriteMask
		self._fdmap[fd] = Xt.AddInput(fd, xmask, self._input_callback,
					      (func, args))

	def _input_callback(self, client_data, fd, id):
		func, args = client_data
		apply(func, args)

class _Window:
	def __init__(self, parent, x, y, w, h, title, defcmap, **options):
		try:
			pixmap = options['pixmap']
		except KeyError:
			pixmap = 0
		self._parent_window = parent
		self._origpos = x, y
		self._callbacks = {}
		if toplevel._visual.c_class == X.TrueColor:
			defcmap = FALSE
		if defcmap:
			self._colormap = toplevel._default_colormap
			self._visual = toplevel._default_visual
		else:
			self._colormap = toplevel._colormap
			self._visual = toplevel._visual
		self._depth = self._visual.depth
		if parent is not toplevel:
			# create a subwindow
			self._sizes = x, y, w, h
			x, y, w, h = parent._convert_coordinates(x, y, w, h)
			attrs = {'resizePolicy': Xmd.RESIZE_NONE,
				 'width': w, 'height': h, 'x': x, 'y': y,
				 'marginHeight': 0, 'marginWidth': 0,
				 'colormap': self._colormap,
				 'visual': self._visual,
				 'depth': self._depth}
			self._form = parent._form.CreateManagedWidget(
				'subwin', Xm.DrawingArea, attrs)
			self._init2(pixmap)
			return
		x = int(float(x)/_mscreenwidth*_screenwidth+0.5)
		y = int(float(y)/_mscreenheight*_screenheight+0.5)
		w = int(float(w)/_mscreenwidth*_screenwidth+0.5)
		h = int(float(h)/_mscreenheight*_screenheight+0.5)
		# XXX--somehow set the posiion
		geometry = '+%d+%d' % (x, y)
		if not title:
			title = ''
		attrs = {'geometry' : geometry,
			 'minWidth': min(w, 60),
			 'minHeight': min(h, 60),
			 'width': w, 'height': h,
			 'colormap': self._colormap,
			 'visual': self._visual,
			 'depth': self._depth,
			 'title': title}
		if title:
			attrs['iconName'] = title
		self._shell = parent._toplevel._main.CreatePopupShell(
			'toplevelShell', Xt.ApplicationShell, attrs)
		self._title = title
		attrs = {'resizePolicy': Xmd.RESIZE_NONE,
			 'height': h, 'width': w,
			 'marginHeight': 0, 'marginWidth': 0}
		self._form = self._shell.CreateManagedWidget('toplevel',
			Xm.DrawingArea, attrs)
		self._width = w
		self._height = h
		self._shell.Popup(0)
		self._shell.AddWMProtocolCallback(_delete_window,
						  self._delete_callback, None)
		self._init2(pixmap)
 
	def __repr__(self):
		s = '<_Window instance'
		if hasattr(self, '_parent_window'):
			if self._parent_window is toplevel:
				if hasattr(self, '_title'):
					s = s + ', title=' + `self._title`
				else:
					s = s + ', toplevel'
			else:
				s = s + ', parent=' + `self._parent_window`
		if self.is_closed():
			s = s + ' (closed)'
		s = s + ', instance at %x>' % id(self)
		return s

	def _init2(self, pixmap):
		self._bgcolor = self._parent_window._bgcolor
		self._fgcolor = self._parent_window._fgcolor
		self._xbgcolor = self._convert_color(self._bgcolor)
		self._xfgcolor = self._convert_color(self._fgcolor)
		self._subwindows = []
		self._subwindows_closed = FALSE
		self._displaylists = []
		self._active_display_list = None
		self._redraw_func = None
		self._parent_window._subwindows.append(self)
		self._toplevel = self._parent_window._toplevel
		self._menu = None
		self._menu_title = None
		self._menu_list = None
		self._accelerators = {}
		self.setcursor(self._parent_window._cursor)
		if pixmap:
			self._pixmap = None # force creation of pixmap later on
		self._do_open_win()

	def close(self):
		try:
			form = self._form
		except AttributeError:
			return		# already closed
		del self._form
		try:
			del self._pixmap
		except AttributeError:
			pass
		self._callbacks = {}
		for win in self._subwindows[:]:
			win.close()
		for displist in self._displaylists[:]:
			displist.close()
		del self._displaylists
		self.destroy_menu()
		if form:
			form.DestroyWidget()
		parent = self._parent_window
		if parent == toplevel:
			self._shell.DestroyWidget()
			del self._shell
		parent._subwindows.remove(self)
		del self._parent_window
		del self._toplevel
		del self._gc

	def is_closed(self):
		return not hasattr(self, '_form')

	def _do_open_win(self):
		form = self._form
		form.SetValues({'background': self._xbgcolor,
				'foreground': self._xfgcolor,
				'borderWidth': 0,
				'marginWidth': 0,
				'marginHeight': 0,
				'marginTop': 0,
				'marginBottom': 0,
				'shadowThickness': 0})
		val = form.GetValues(['width', 'height'])
		self._width = val['width']
		self._height = val['height']
		if hasattr(self, '_pixmap'):
			del self._pixmap # free old pixmap
			self._pixmap = form.CreatePixmap()
			self._gc = self._pixmap.CreateGC(
				{'background': self._xbgcolor,
				 'foreground': self._xbgcolor})
			self._gc.FillRectangle(0, 0, self._width, self._height)
		else:
			self._gc = form.CreateGC(
				{'background': self._xbgcolor,
				 'foreground': self._xbgcolor})
		form.RealizeWidget()
		form.AddCallback('exposeCallback', self._expose_callback, None)
		form.AddCallback('resizeCallback', self._resize_callback, None)
		form.AddCallback('inputCallback', self._input_callback, None)
		self.setcursor(self._cursor)

	def _input_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		event = call_data.event
		# this stuff is needed because events don't always
		# arrive at the correct window.  this is especially
		# true for menu button presses.
##		x, y = event.x, event.y
##		for w in self._subwindows:
##			v = w._form.GetValues(['x', 'y', 'width', 'height'])
##			fx, fy = v['x'], v['y']
##			fw, fh = v['width'], v['height']
##			if fx <= x < fx + fw and fy <= y < fy + fh:
##				event.x = x - fx
##				event.y = y - fy
##				w._input_callback(widget, client_data, call_data)
##				return
		if event.type == X.KeyPress:
			string = Xlib.LookupString(event)[0]
			if self._accelerators.has_key(string):
				f, a = self._accelerators[string]
				apply(f, a)
				return
			try:
				func, arg = self._callbacks[KeyboardInput]
			except KeyError:
				pass
			else:
				for c in string:
					func(arg, self, KeyboardInput, c)
		elif event.type == X.KeyRelease:
			pass
		elif event.type in (X.ButtonPress, X.ButtonRelease):
			if event.type == X.ButtonPress:
				if event.button == X.Button1:
					ev = Mouse0Press
				elif event.button == X.Button2:
					ev = Mouse1Press
				elif event.button == X.Button3:
					if self._menu:
						self._menu.MenuPosition(event)
						self._menu.ManageChild()
						return
					ev = Mouse2Press
				else:
					return	# unsupported mouse button
			else:
				if event.button == X.Button1:
					ev = Mouse0Release
				elif event.button == X.Button2:
					ev = Mouse1Release
				elif event.button == X.Button3:
					if self._menu:
						# ignore buttonrelease
						# when we have a menu
						return
					ev = Mouse2Release
				else:
					return	# unsupported mouse button
			x = float(event.x) / self._width
			y = float(event.y) / self._height
			buttons = []
			adl = self._active_display_list
			if adl:
				for but in adl._buttonlist:
					if but._inside(x, y):
						buttons.append(but)
			try:
				func, arg = self._callbacks[ev]
			except KeyError:
				pass
			else:
				func(arg, self, ev, (x, y, buttons))
		else:
			print 'unknown event',`event.type`

	def _expose_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		if not self._form:
			return		# why were we called anyway?
		if call_data:
			event = call_data.event
			if hasattr(self, '_pixmap'):
				self._pixmap.CopyArea(
					self._form, self._gc, event.x, event.y,
					event.width, event.height,
					event.x, event.y)
				return
			self._gc.FillRectangle(event.x, event.y, event.width, event.height)
			if event.count > 0:
				return
		if self._subwindows_closed:
			self._gc.FillRectangle(0, 0, self._width, self._height)
			for win in self._subwindows:
				x, y, w, h = win._sizes
				self._gc.DrawRectangle(x, y, w, h)
		if self._redraw_func:
			self._redraw_func()
		elif self._active_display_list:
			# re-render
			buttons = []
			for but in self._active_display_list._buttonlist:
				if but._highlighted:
					buttons.append(but)
			self._active_display_list.render(expose = 1)
			for but in buttons:
				but.highlight()
		elif not call_data:
			# clear the window
			self._gc.FillRectangle(0, 0, self._width, self._height)

	def _do_resize(self):
		x, y, w, h = self._sizes
		x, y, w, h = self._parent_window._convert_coordinates(x, y, w, h)
		self._form.SetValues({'width': w, 'height': h, 'x': x, 'y': y})

	def _resize_callback(self, *rest):
		if self.is_closed():
			return
		val = self._form.GetValues(['width', 'height'])
		self._width = val['width']
		self._height = val['height']
		if hasattr(self, '_pixmap'):
			del self._pixmap
			self._pixmap = self._form.CreatePixmap()
			self._gc = self._pixmap.CreateGC(
				{'background': self._xbgcolor,
				 'foreground': self._xbgcolor})
			self._gc.FillRectangle(0, 0, self._width, self._height)
		for displist in self._displaylists[:]:
			displist.close()
		for win in self._subwindows:
			win._do_resize()
		if hasattr(self, '_rb_dl'):
			self._rb_cancel()
		try:
			func, arg = self._callbacks[ResizeWindow]
		except KeyError:
			pass
		else:
			func(arg, self, ResizeWindow, None)

	def _delete_callback(self, widget, client_data, call_data):
		try:
			func, arg = self._callbacks[WindowExit]
		except KeyError:
			pass
		else:
			func(arg, self, WindowExit, None)

	def newwindow(self, coordinates, **options):
		return apply(self._new_window, (coordinates, FALSE), options)

	def newcmwindow(self, coordinates, **options):
		return apply(self._new_window, (coordinates, TRUE), options)
		
	def _new_window(self, coordinates, defcmap, **options):
		x, y, w, h = coordinates
		newwin = apply(_Window, (self, x, y, w, h, '', defcmap), options)
		return newwin

	def fgcolor(self, color):
		self._xfgcolor = self._convert_color(color)
		self._fgcolor = color

	def bgcolor(self, color):
		self._xbgcolor = self._convert_color(color)
		self._bgcolor = color
		self._gc.background = self._gc.foreground = self._xbgcolor
		if not self._active_display_list:
			self._form.SetValues({'background': self._xbgcolor})

	def setcursor(self, cursor):
		if not self.is_closed() and self._form:
			for win in self._subwindows:
				win.setcursor(cursor)
			_setcursor(self._form, cursor)
		self._cursor = cursor

	def newdisplaylist(self, *bgcolor):
		if len(bgcolor) == 1 and type(bgcolor[0]) is TupleType:
			bgcolor = bgcolor[0]
		if len(bgcolor) == 3:
			pass
		elif len(bgcolor) == 0:
			# inherit bgcolor from window
			bgcolor = self._bgcolor
		else:
			raise TypeError, 'arg count mismatch'
		return _DisplayList(self, bgcolor)

	def settitle(self, title):
		if self._parent_window != toplevel:
			raise error, 'can only settitle at top-level'
		self._shell.SetValues({'title': title, 'iconName': title})
		self._title = title

	def pop(self):
# The following statement was commented out because in the GL version
# it had the undesirable effect that when the second of two subwindows
# was popped, the first disappeared under its parent window.  It may
# be that the current situation also has undesirable side effects, but
# I haven't seen them yet.  --sjoerd
##		self._parent_window.pop()
		self._form.RaiseWindow()

	def push(self):
		self._form.LowerWindow()

	def setredrawfunc(self, func):
		if func:
			self._redraw_func = func
		else:
			self._redraw_func = None

	def _convert_color(self, color):
		r, g, b = color
		if self._colormap is toplevel._default_colormap:
			if _cm_cache.has_key(`r,g,b`):
				return _cm_cache[`r,g,b`]
			ri = int(r / 255.0 * 65535.0)
			gi = int(g / 255.0 * 65535.0)
			bi = int(b / 255.0 * 65535.0)
			try:
				color = self._colormap.AllocColor(ri, gi, bi)
			except RuntimeError:
				# can't allocate color; find closest one
				cm = self._colormap
				m = 0
				color = None
				# use floats to guard against overflow
				rf = float(ri)
				gf = float(gi)
				bf = float(bi)
				for c in cm.QueryColors(range(256)):
					# calculate distance
					d = (rf-c[1])*(rf-c[1]) + \
					    (gf-c[2])*(gf-c[2]) + \
					    (bf-c[3])*(bf-c[3])
					if color is None or d < m:
						# found one that's closer
						m = d
						color = c
				color = self._colormap.AllocColor(color[1],
							color[2], color[3])
				print "Warning: colormap full, using 'close' color",
				print 'original:',`r,g,b`,'new:',`int(color[1]/65535.0*255.0),int(color[2]/65535.0*255.0),int(color[3]/65535.0*255.0)`
			# cache the result
			_cm_cache[`r,g,b`] = color[0]
			return color[0]
		r = int(float(r) / 255. * float(toplevel._red_mask) + .5)
		g = int(float(g) / 255. * float(toplevel._green_mask) + .5)
		b = int(float(b) / 255. * float(toplevel._blue_mask) + .5)
		c = (r << toplevel._red_shift) | \
		       (g << toplevel._green_shift) | \
		       (b << toplevel._blue_shift)
		return c

	def _convert_coordinates(self, x, y, w, h):
		# convert relative sizes to pixel sizes relative to
		# upper-left corner of the window
		x = int((self._width - 1) * x + 0.5)
		y = int((self._height - 1) * y + 0.5)
		w = int((self._width - 1) * w + 0.5)
		h = int((self._height - 1) * h + 0.5)
		return x, y, w, h

	def _prepare_image_from_file(self, file, top, bottom, left, right):
		global _cache_full
		cachekey = `file`+':'+`self._width`+'x'+`self._height`
		if _image_cache.has_key(cachekey):
			retval = _image_cache[cachekey]
			filename = retval[-1]
			try:
				image = open(filename).read()
			except:		# any error...
				del _image_cache[cachekey]
				import os
				try:
					os.unlink(filename)
				except:
					pass
			else:
				return retval[:-1] + (image,)
		if self._depth == 8:
			format = myxrgb8
			depth = 1
		else:
			format = imgformat.rgb
			depth = 4
		try:
			reader = img.reader(format, file)
		except img.error, arg:
			raise error, arg
		xsize = reader.width
		ysize = reader.height
		try:
			image = reader.read()
		except: # XXXX This is lousy
			raise error, 'Unspecified error reading image'
		_image_size_cache[file] = (xsize, ysize)
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		width, height = self._width, self._height
		scale = min(float(width)/(xsize - left - right),
			    float(height)/(ysize - top - bottom))
		width, height = xsize, ysize
		if scale != 1:
			width = int(xsize * scale)
			height = int(ysize * scale)
			image = imageop.scale(image, depth, xsize, ysize,
				  width, height)
			top = int(top * scale)
			bottom = int(bottom * scale)
			left = int(left * scale)
			right = int(right * scale)
			scale = 1.0
		x, y = (self._width-(width-left-right))/2, \
			  (self._height-(height-top-bottom))/2
		retval = x, y, width - left - right, height - top - bottom, \
			 left, bottom, width, height, depth, scale, image
		if not _cache_full:
			filename = tempfile.mktemp()
			try:
				f = open(filename, 'wb')
				f.write(image)
			except:
				print 'Warning: caching image failed'
				import os
				try:
					os.unlink(filename)
				except:
					pass
				_cache_full = TRUE
			else:
				_image_cache[cachekey] = retval[:-1] + (filename,)
		return retval

	def _image_size(self, file):
		# XXX--assume that images was displayed at least once
		return _image_size_cache[file]

	def register(self, ev, func, arg):
		if ev in (ResizeWindow, KeyboardInput, Mouse0Press,
			  Mouse0Release, Mouse1Press, Mouse1Release,
			  Mouse2Press, Mouse2Release):
			self._callbacks[ev] = func, arg
		elif ev == WindowExit:
			self._callbacks[ev] = func, arg
			try:
				widget = self._shell
			except AttributeError:
				widget = self._main
			widget.deleteResponse = Xmd.DO_NOTHING
		else:
			raise error, 'Internal error'

	def unregister(self, ev):
		try:
			del self._callbacks[ev]
		except KeyError:
			pass

	def destroy_menu(self):
		if self._menu:
			self._menu.DestroyWidget()
		self._menu = None
		self._menu_title = None
		self._menu_list = None
		self._accelerators = {}

	def create_menu(self, list, title = None):
		self.destroy_menu()
		self._menu_title = title
		self._menu_list = list
		menu = self._form.CreatePopupMenu('menu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			dummy = menu.CreateManagedWidget('menuTitle',
							 Xm.LabelGadget, {})
			dummy.labelString = title
			dummy = menu.CreateManagedWidget('menuSeparator',
							 Xm.SeparatorGadget,
							 {})
		self._accelerators = {}
		_create_menu(menu, list, self._accelerators)
		self._menu = menu

class _DisplayList:
	def __init__(self, window, bgcolor):
		self._window = window
		self._rendered = FALSE
		# color support
		self._bgcolor = bgcolor
		self._xbgcolor = window._convert_color(bgcolor)
		self._fgcolor = window._fgcolor
		self._xfgcolor = window._xfgcolor
		# line width
		self._linewidth = 1
		# buttons
		self._buttonlist = []
		# font support
		self._font = None
		self._fontheight = 0
		self._baseline = 0
		#
		window._displaylists.append(self)
		self._list = [('clear', self._xbgcolor, self._xfgcolor, self._linewidth)]
		self._cloneof = None
		self._clonestart = 0
		self._optimdict = {}

	def close(self):
		if self.is_closed():
			return
		for but in self._buttonlist[:]:
			but.close()
		window = self._window
		window._displaylists.remove(self)
		for d in window._displaylists:
			if d._cloneof is self:
				d._cloneof = None
		if window._active_display_list == self:
			window._active_display_list = None
			window._expose_callback(None, None, None)
		del self._window
		del self._buttonlist
		del self._font
		del self._list
		del self._cloneof
		del self._optimdict

	def is_closed(self):
		return not hasattr(self, '_window')

	def render(self, expose = 0):
		if self.is_closed():
			raise error, 'displaylist already closed'
		self._rendered = TRUE
		window = self._window
		if window._active_display_list:
			for but in window._active_display_list._buttonlist:
				but._highlighted = FALSE
		width, height = window._width, window._height
		if not self._cloneof or \
		   self._cloneof is not window._active_display_list or \
		   window._active_display_list._buttonlist:
			self._clonestart = 0
		if hasattr(window, '_pixmap'):
			gc = window._gc
		else:
			gc = window._form.CreateGC({})
		font = None
		fg = self._list[0][2]
		i = 1
		while i < self._clonestart:
			entry = self._list[i]
			if entry[0] == 'font':
				font = entry[1]
			elif entry[0] == 'fg':
				fg = entry[1]
			i = i + 1
		if fg is not None:
			gc.foreground = fg
		if font is not None:
			gc.SetFont(font)
		fg = gc.foreground
		for entry in self._list[self._clonestart:]:
			fg = self._do_render(entry, gc, fg, expose)
		window._active_display_list = self
		if hasattr(window, '_pixmap'):
			window._pixmap.CopyArea(window._form, gc, 0, 0,
						width, height, 0, 0)
		window._form.UpdateDisplay()

	def _do_render(self, entry, gc, fg, expose):
		cmd = entry[0]
		if cmd == 'clear':
			window = self._window
			if not expose or window._gc.foreground != entry[1]:
				gc.foreground = entry[1]
				gc.FillRectangle(0, 0,
						 window._width, window._height)
			gc.background = entry[1]
			gc.foreground = fg = entry[2]
			gc.line_width = entry[3]
		elif cmd == 'fg':
			gc.foreground = fg = entry[1]
		elif cmd == 'image':
			apply(gc.PutImage, entry[1:])
		elif cmd == 'line':
			gc.foreground = entry[1]
			points = entry[2]
			x0, y0 = points[0]
			for x, y in points[1:]:
				gc.DrawLine(x0, y0, x, y)
				x0, y0 = x, y
			gc.foreground = fg
		elif cmd == 'box':
			apply(gc.DrawRectangle, entry[1:])
		elif cmd == 'fbox':
			gc.foreground = entry[1]
			apply(gc.FillRectangle, entry[2:])
			gc.foreground = fg
		elif cmd == 'font':
			gc.SetFont(entry[1])
		elif cmd == 'text':
			apply(gc.DrawString, entry[1:])
		return fg

	def _optimize(self, ignore = []):
		if type(ignore) is IntType:
			ignore = [ignore]
		entry = self._list[-1]
		x = []
		for i in range(len(entry)):
			if i not in ignore:
				z = entry[i]
				if type(z) is type([]):
					z = tuple(z)
				x.append(z)
		x = tuple(x)
		try:
			i = self._optimdict[x]
		except KeyError:
			pass
		else:
			del self._list[i]
			del self._optimdict[x]
			if i < self._clonestart:
				self._clonestart = self._clonestart - 1
			for key, val in self._optimdict.items():
				if val > i:
					self._optimdict[key] = val - 1
		self._optimdict[x] = len(self._list) - 1

	#
	# Color handling
	#
	def fgcolor(self, color):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._xfgcolor = self._window._convert_color(color)
		self._fgcolor = color
		self._list.append('fg', self._xfgcolor)

	#
	# Buttons
	#
	def newbutton(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		button = _Button(self, x, y, w, h)
		return button

	#
	# Images
	#
	def display_image_from_file(self, file, *crop):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(crop) == 4:
			top, bottom, left, right = crop
			if top + bottom >= 1 or left + right >= 1:
				raise error, 'cannot crop more than 1'
		elif len(crop) == 0:
			top, bottom, left, right = 0, 0, 0, 0
		else:
			raise TypeError, 'arg count mismatch'
		window = self._window

		win_x, win_y, win_w, win_h, im_x, im_y, im_w, im_h, \
			  depth, scale, image = \
				  window._prepare_image_from_file(file,
					  top, bottom, left, right)
		xim = toplevel._visual.CreateImage(window._depth, X.ZPixmap, 0,
				image, im_w, im_h, depth * 8, im_w * depth)
		self._list.append('image', xim, im_x, im_y, win_x, win_y, win_w, win_h)
		self._optimize(1)
		return float(win_x) / window._width, \
			  float(win_y) / window._height, \
			  float(win_w) / window._width, \
			  float(win_h) / window._height

	#
	# Drawing methods
	#
	def drawline(self, color, points):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'

		window = self._window
		p = []
		for x, y in points:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			p.append(x, y)
		color = window._convert_color(color)
		self._list.append('line', color, p)

	def drawbox(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		x, y, w, h = self._window._convert_coordinates(x, y, w, h)
		self._list.append('box', x, y, w, h)
		self._optimize()

	def drawfbox(self, color, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		window = self._window
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		x, y, w, h = window._convert_coordinates(x, y, w, h)
		color = self._window._convert_color(color)
		self._list.append('fbox', color, x, y, w, h)
		self._optimize(1)

	#
	# Font and text handling
	#
	def usefont(self, fontobj):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
		f = float(_screenheight) / _mscreenheight / self._window._height
		self._baseline = fontobj.baseline() * f
		self._fontheight = fontobj.fontheight() * f
		self._list.append('font', fontobj._font)
		return self._baseline, self._fontheight, fontobj.pointsize()

	def setfont(self, font, size):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, margin = 0):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if margin < 0 or margin >= 1:
			raise error, 'rediculous margin: ' + `margin`
		mfac = 1 - margin
		window = self._window
		strlist = string.splitfields(str, '\n')
		nlines = len(strlist)
		fontobj = findfont(fontname, 100)
		firsttime = TRUE
		height = fontobj.fontheight() * _screenheight / _mscreenheight
		while firsttime or height > window._height*mfac:
			firsttime = FALSE
			ps = float(window._height*mfac*_mscreenheight*fontobj.pointsize())/\
				  float(nlines*fontobj.fontheight()*_screenheight)
			fontobj.close()
			if ps <= 0:
				raise error, 'string does not fit in window'
			fontobj = findfont(fontname, ps)
			height = fontobj.fontheight() * _screenheight / _mscreenheight
		for str in strlist:
			width, height = fontobj.strsize(str)
			width = width * _screenwidth / _mscreenwidth
			while width > window._width * mfac:
				ps = float(window._width) * mfac * fontobj.pointsize() / width
				if ps <= 0:
					raise error, 'string does not fit in window'
				fontobj.close()
				fontobj = findfont(fontname, ps)
				width, height = fontobj.strsize(str)
				width = width * _screenwidth / _mscreenwidth
		return self.usefont(fontobj)

	def baseline(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if not self._font:
			raise error, 'font not set'
		return self._baseline

	def fontheight(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if not self._font:
			raise error, 'font not set'
		return self._fontheight

	def pointsize(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if not self._font:
			raise error, 'font not set'
		return self._font.pointsize()

	def strsize(self, str):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		width, height = self._font.strsize(str)
		return float(width) * _screenwidth / _mscreenwidth / self._window._width, \
		       float(height) * _screenheight / _mscreenheight / self._window._height

	def setpos(self, x, y):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._curpos = x, y
		self._xpos = x

	def getpos(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self._curpos

	def writestr(self, str):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		window = self._window
		strlist = string.splitfields(str, '\n')
		oldx, oldy = x, y = self._curpos
		oldy = oldy - self._baseline
		maxx = oldx
		for str in strlist:
			x0, y0 = self._window._convert_coordinates(x, y, 0, 0)[:2]
			self._list.append('text', x0, y0, str)
			self._curpos = x + float(self._font._font.TextWidth(str)) / window._width, y
			x = self._xpos
			y = y + self._fontheight
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, \
			  newy - oldy + self._fontheight - self._baseline


class _Button:
	def __init__(self, dispobj, x, y, w, h):
		self._dispobj = dispobj
		window = dispobj._window
		self._corners = x, y, x + w, y + h
		self._coordinates = x, y, w, h = window._convert_coordinates(x, y, w, h)
		self._color = dispobj._fgcolor
		self._hicolor = dispobj._fgcolor
		self._xcolor = dispobj._xfgcolor
		self._xhicolor = dispobj._xfgcolor
		self._linewidth = dispobj._linewidth
		self._hiwidth = self._linewidth
		self._highlighted = FALSE
		dispobj._buttonlist.append(self)
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		dispobj._list.append('box', x, y, w, h)

	def close(self):
		if self.is_closed():
			return
		self._dispobj._buttonlist.remove(self)
		del self._dispobj

	def is_closed(self):
		return not hasattr(self, '_dispobj')

	def _inside(self, x, y):
		# return 1 iff the given coordinates fall within the button
		if (self._corners[0] <= x <= self._corners[2]) and \
			  (self._corners[1] <= y <= self._corners[3]):
			return TRUE
		else:
			return FALSE

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, color):
		if self.is_closed():
			raise error, 'button already closed'
		self._xhicolor = self._dispobj._window._convert_color(color)
		self._hicolor = color

	def highlight(self):
		if self.is_closed():
			raise error, 'button already closed'
		dispobj = self._dispobj
		window = dispobj._window
		gc = window._gc
		if window._active_display_list != dispobj:
			raise error, 'can only highlight rendered button'
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		gc.background = dispobj._xbgcolor
		gc.foreground = self._xhicolor
		gc.line_width = self._hiwidth
		apply(gc.DrawRectangle, self._coordinates)
		gc.background = window._xbgcolor
		gc.foreground = window._xbgcolor
		self._highlighted = TRUE

	def unhighlight(self):
		if self.is_closed():
			raise error, 'button already closed'
		dispobj = self._dispobj
		if dispobj._window._active_display_list != dispobj:
			raise error, 'can only unhighlight rendered button'
		if self._highlighted:
			self._highlighted = FALSE
			self._dispobj.render()

class findfont:
	def __init__(self, fontname, size):
		self._fontname = fontname
		self._xfont, self._size, self._font = _findfont(fontname, size)

	def close(self):
		del self._font

	def is_closed(self):
		return not hasattr(self, '_font')

	def strsize(self, str):
		if self.is_closed():
			raise error, 'font object already closed'
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * (self._font.ascent + self._font.descent)
		for str in strlist:
			width = self._font.TextWidth(str)
			if width > maxwidth:
				maxwidth = width
		return float(maxwidth) * _mscreenwidth / _screenwidth, \
			  float(maxheight) * _mscreenheight / _screenheight

	def baseline(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return float(self._font.ascent) * _mscreenheight / _screenheight

	def fontheight(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return float(self._font.ascent + self._font.descent) * _mscreenheight / _screenheight

	def pointsize(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return self._size

_FOUNDRY = 1
_FONT_FAMILY = 2
_WEIGHT = 3
_SLANT = 4
_SET_WIDTH = 5
_PIXELS = 7
_POINTS = 8
_RES_X = 9
_RES_Y = 10
_SPACING = 11
_AVG_WIDTH = 12
_REGISTRY = 13
_ENCODING = 14

def _parsefontname(fontname):
	list = string.splitfields(fontname, '-')
	if len(list) != 15:
		raise error, 'fontname not well-formed'
	return list

def _makefontname(font):
	return string.joinfields(font, '-')

_fontcache = {}
def _findfont(fontname, size):
	if not _fontmap.has_key(fontname):
		raise error, 'Unknown font ' + `fontname`
	key = fontname + `size`
	try:
		thefont, psize = _fontcache[key]
	except KeyError:
		fontname = _fontmap[fontname]
		parsedfontname = _parsefontname(fontname)
		fontlist = toplevel._main.ListFonts(fontname)
		pixelsize = size * _dpi_y / 72.0
		bestsize = 0
		psize = size
		for font in fontlist:
			parsedfont = _parsefontname(font)
			if parsedfont[_PIXELS] == '0':
				# scalable font
				parsedfont[_PIXELS] = '*'
				parsedfont[_POINTS] = `int(size * 10)`
				parsedfont[_RES_X] = `_dpi_x`
				parsedfont[_RES_Y] = `_dpi_y`
				parsedfont[_AVG_WIDTH] = '*'
				thefont = _makefontname(parsedfont)
				psize = size
				break
			p = string.atoi(parsedfont[_PIXELS])
			if p <= pixelsize and p > bestsize:
				bestsize = p
				thefont = font
				psize = p * 72.0 / _dpi_y
		_fontcache[key] = thefont, psize
	return thefont, psize, toplevel._main.LoadQueryFont(thefont)

_fontmap = {
	  'Times-Roman': '-*-times-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Times-Italic': '-*-times-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Times-Bold': '-*-times-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Utopia-Bold': '-*-utopia-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Palatino-Bold': '-*-palatino-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Helvetica': '-*-helvetica-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Helvetica-Bold': '-*-helvetica-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Helvetica-Oblique': '-*-helvetica-medium-o-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier': '-*-courier-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier-Bold': '-*-courier-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier-Oblique': '-*-courier-medium-o-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier-Bold-Oblique': '-*-courier-bold-o-normal-*-*-*-*-*-*-*-iso8859-1'
	  }
fonts = _fontmap.keys()

class showmessage:
	def __init__(self, text, type = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message'):
		if type == 'error':
			func = toplevel._main.CreateErrorDialog
		elif type == 'warning':
			func = toplevel._main.CreateWarningDialog
		elif type == 'information':
			func = toplevel._main.CreateInformationDialog
		elif type == 'question':
			func = toplevel._main.CreateQuestionDialog
		else:
			func = toplevel._main.CreateMessageDialog
		if grab:
			dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
		else:
			dialogStyle = Xmd.DIALOG_MODELESS
		self._grab = grab
		w = func(name, {'messageString': text,
				'title': title,
				'dialogStyle': dialogStyle,
				'resizePolicy': Xmd.RESIZE_NONE,
				'visual': toplevel._default_visual,
				'depth': toplevel._default_visual.depth,
				'colormap': toplevel._default_colormap})
		w.MessageBoxGetChild(Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		if type == 'question' or cancelCallback:
			w.AddCallback('cancelCallback',
				      self._callback, cancelCallback)
		else:
			w.MessageBoxGetChild(Xmd.DIALOG_CANCEL_BUTTON).UnmanageChild()
		w.AddCallback('okCallback', self._callback, callback)
		w.AddCallback('destroyCallback', self._destroy, None)
		w.ManageChild()
		self._widget = w

	def close(self):
		if self._widget:
			w = self._widget
			self._widget = None
			w.UnmanageChild()
			w.DestroyWidget()

	def _callback(self, widget, callback, call_data):
		if not self._widget:
			return
		if callback:
			apply(callback[0], callback[1])
		if self._grab:
			self.close()

	def _destroy(self, widget, client_data, call_data):
		self._widget = None

class Dialog:
	def __init__(self, list, title = '', prompt = None, grab = 1,
		     vertical = 1):
		if not title:
			title = ''
		if grab:
			dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
		else:
			dialogStyle = Xmd.DIALOG_MODELESS
		w = toplevel._main.CreateFormDialog('dialog',
				{'title': title,
				 'dialogStyle': dialogStyle,
				 'resizePolicy': Xmd.RESIZE_NONE,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth,
				 'colormap': toplevel._default_colormap})
		if vertical:
			orientation = Xmd.VERTICAL
		else:
			orientation = Xmd.HORIZONTAL
		attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
			 'traversalOn': FALSE,
			 'orientation': orientation,
			 'topAttachment': Xmd.ATTACH_FORM,
			 'leftAttachment': Xmd.ATTACH_FORM,
			 'rightAttachment': Xmd.ATTACH_FORM}
		if prompt:
			l = w.CreateManagedWidget('label', Xm.LabelGadget,
					{'labelString': prompt,
					 'topAttachment': Xmd.ATTACH_FORM,
					 'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM})
			sep = w.CreateManagedWidget('separator',
					Xm.SeparatorGadget,
					{'topAttachment': Xmd.ATTACH_WIDGET,
					 'topWidget': l,
					 'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM})
			attrs['topAttachment'] = Xmd.ATTACH_WIDGET
			attrs['topWidget'] = sep
		row = w.CreateManagedWidget('buttonrow', Xm.RowColumn, attrs)
		self._buttons = []
		for entry in list:
			if entry is None:
				if vertical:
					attrs = {'orientation': Xmd.HORIZONTAL}
				else:
					attrs = {'orientation': Xmd.VERTICAL}
				dummy = row.CreateManagedWidget('separator',
							Xm.SeparatorGadget,
							attrs)
				continue
			if type(entry) is TupleType:
				label, callback = entry[:2]
			else:
				label, callback = entry, None
			if callback and type(callback) is not TupleType:
				callback = (callback, (label,))
			b = row.CreateManagedWidget('button',
						    Xm.PushButtonGadget,
						    {'labelString': label})
			if callback:
				b.AddCallback('activateCallback',
					      self._callback, callback)
			self._buttons.append(b)
		self._widget = w
		self._menu = None
		w.AddCallback('destroyCallback', self._destroy, None)
		w.ManageChild()

	# destruction
	def _destroy(self, widget, client_data, call_data):
		self._widget = None
		self._menu = None
		self._buttons = []

	def close(self):
		w = self._widget
		self._widget = None
		w.UnmanageChild()
		w.DestroyWidget()

	# pop up menu
	def destroy_menu(self):
		if self._menu:
			self._menu.DestroyWidget()
		self._menu = None

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = self._widget.CreatePopupMenu('dialogMenu', {})
		if title:
			list = [title, None] + list
		_create_menu(menu, list)
		self._menu = menu
		self._widget.AddEventHandler(X.ButtonPressMask, FALSE,
					     self._post_menu, None)

	def _post_menu(self, widget, client_data, call_data):
		if not self._emnu:
			return
		if call_data.button == X.Button3:
			self._menu.MenuPosition(call_data)
			self._menu.ManageChild()

	# buttons
	def _callback(self, widget, callback, call_data):
		if callback:
			apply(callback[0], callback[1])

	def getbutton(self, button):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		return self._buttons[button].set

	def setbutton(self, button, onoff = 1):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		self._buttons[button].set = onoff

_end_loop = '_end_loop'			# exception for ending a loop
class _MultChoice(Dialog):
	def __init__(self, prompt, msg_list, defindex):
		self.looping = FALSE
		self.answer = None
		self.msg_list = msg_list
		list = []
		for msg in msg_list:
			list.append(msg, (self.callback, (msg,)))
		Dialog.__init__(self, list, title = None, prompt = prompt,
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
