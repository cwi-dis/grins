import Xt, Xm, X, Xmd, Xtdefs, Xcursorfont
from EVENTS import *
from types import *
import time

_EndLoopEvent = 30			# event to end internal loops

error = 'windowinterface.error'
FALSE, TRUE = X.FALSE, X.TRUE
ReadMask, WriteMask = 1, 2

Version = 'X'

# Colors
_DEF_BGCOLOR = 255,255,255		# white
_DEF_FGCOLOR =   0,  0,  0		# black

import os
debug = os.environ.has_key('WINDOWDEBUG')

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
_delete_window = 0

_image_cache = {}		# cache of prepared images
_cache_full = FALSE		# TRUE if we shouldn't cache more images
_image_size_cache = {}
_cm_cache = {}

_rb_message = """\
Use left mouse button to draw a box.
Click `Done' when ready or `Cancel' to cancel."""
_rb_done = '_rb_done'			# exception to stop create_box loop

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

def roundi(x):
	if x < 0:
		return roundi(x + 1024) - 1024
	return int(x + 0.5)

import imgformat
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
	try:
		toplevel._win_lock.acquire()
		if cursor == 'watch':
			form.DefineCursor(_watchcursor)
		elif cursor == 'channel':
			form.DefineCursor(_channelcursor)
		elif cursor == 'link':
			form.DefineCursor(_linkcursor)
		elif cursor == '':
			form.UndefineCursor()
		else:
			raise error, 'unknown cursor glyph'
	finally:
		toplevel._win_lock.release()

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

class _DummyLock:
	def acquire(self):
		pass
	def release(self):
		pass

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
		global _delete_window
		if debug: print '_TopLevel.__init__() --> '+`self`
		self._win_lock = _DummyLock()
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
		self._main.RealizeWidget()
		self._timer_callback_func = None
		self._fdmap = {}

	def _setupcolormap(self, dpy):
		visattr = {'class': X.TrueColor}
##		visattr['depth'] = 8
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
		if debug: print 'Toplevel.close()'
		import posix
		global _image_cache
		for win in self._subwindows[:]:
			win.close()
		for key in _image_cache.keys():
			try:
				posix.unlink(_image_cache[key][-1])
			except posix.error:
				pass
		_image_cache = {}

	def newwindow(self, x, y, w, h, title, **options):
		if debug: print 'Toplevel.newwindow'+`x, y, w, h, title`
		window = apply(_Window, (self, x, y, w, h, title, FALSE), options)
		return window

	def newcmwindow(self, x, y, w, h, title, **options):
		if debug: print 'Toplevel.newcmwindow'+`x, y, w, h, title`
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

	def getsize(self):
		return _mscreenwidth, _mscreenheight

	def getmouse(self):
		return 0, 0

	def usewindowlock(self, lock):
		if debug: print 'Toplevel.usewindowlock()'
		if lock:
			self._win_lock = lock
		else:
			self._win_lock = _DummyLock()

	def mainloop(self):
		Xt.MainLoop()

	# timer interface
	def settimer(self, sec, arg):
		id = Xt.AddTimeOut(int(sec * 1000), self._timer_callback, arg)
		return id

	def canceltimer(self, id):
		if id is not None:
			Xt.RemoveTimeOut(id)

	def settimerfunc(self, func, arg):
		self._timer_callback_func = func, arg

	def _timer_callback(self, client_data, id):
		if self._timer_callback_func:
			func, arg = self._timer_callback_func
			func(arg, None, TimerEvent, client_data)

	# file descriptor interface
	def select_setcallback(self, fd, func, arg, mask = ReadMask):
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
					      (func, arg))

	def _input_callback(self, client_data, fd, id):
		func, arg = client_data
		func(arg)

class _Window:
	def __init__(self, parent, x, y, w, h, title, defcmap, **options):
		if debug: print '_Window.init() --> '+`self`
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
		if debug: print 'CreatePopupShell, geometry:',geometry
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
		toplevel._win_lock.acquire()
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
		toplevel._win_lock.release()
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
		if debug: print `self`+'.init2()'
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
		if debug: print `self`+'.close()'
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
		toplevel._win_lock.acquire()
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
		toplevel._win_lock.release()

	def is_closed(self):
		return not hasattr(self, '_form')

	def _close_win(self):
		# close the X window connected to this instance
		if self._parent_window == toplevel:
			raise error, 'can\'t close top-level window'
		self._close_subwins()
		menu_title = self._menu_title
		menu_list = self._menu_list
		self.destroy_menu()
		self._menu_title = menu_title
		self._menu_list = menu_list
		form = self._form
		if hasattr(self, '_pixmap'):
			self._pixmap = None
		form.RemoveCallback('exposeCallback', self._expose_callback,
				    None)
		form.RemoveCallback('resizeCallback', self._resize_callback,
				    None)
		form.RemoveCallback('inputCallback', self._input_callback,
				    None)
		form.UnmanageChild()
		form.DestroyWidget()
		self._form = None
		self._gc = None

	def _open_win(self):
		# re-open an X window for this instance
		if self.is_closed():
			raise error, 'window already closed'
		if self._form is not None:
			raise error, 'window not closed'
		pwin = self._parent_window
		x, y, w, h = self._sizes
		x, y, w, h = pwin._convert_coordinates(x, y, w, h)
		self._xbgcolor = self._convert_color(self._bgcolor)
		self._xfgcolor = self._convert_color(self._fgcolor)
		attrs = {'resizePolicy': Xmd.RESIZE_NONE,
			 'width': w, 'height': h, 'x': x, 'y': y,
			 'marginHeight': 0, 'marginWidth': 0,
			 'colormap': self._colormap,
			 'visual': self._visual,
			 'depth': self._depth}
		toplevel._win_lock.acquire()
		self._form = pwin._form.CreateManagedWidget('subwin',
			Xm.DrawingArea, attrs)
		toplevel._win_lock.release()
		self._do_open_win()
		if self._menu_title or self._menu_list:
			self.create_menu(self._menu_title, self._menu_list)
		self._open_subwins()

	def _do_open_win(self):
		form = self._form
		toplevel._win_lock.acquire()
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
		toplevel._win_lock.release()
		self.setcursor(self._cursor)

	def showwindow(self):
		# dummy for now
		pass

	def dontshowwindow(self):
		# dummy for now
		pass

	def _close_subwins(self):
		for win in self._subwindows:
			win._close_win()
		self._subwindows_closed = TRUE

	def _open_subwins(self):
		if self.is_closed():
			raise error, 'window already closed'
		for win in self._subwindows:
			if not win.is_closed():
				win._open_win()
		self._subwindows_closed = FALSE

	def _input_callback(self, widget, client_data, call_data):
		if self.is_closed():
			return
		if debug: print `self`+'._input_callback()'
		event = call_data.event
		if event.type == X.KeyPress:
			import Xlib
			toplevel._win_lock.acquire()
			string = Xlib.LookupString(event)[0]
			toplevel._win_lock.release()
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
		if debug: print `self`+'._expose_callback()'
		if not self._form:
			return		# why were we called anyway?
		if call_data:
			event = call_data.event
			toplevel._win_lock.acquire()
			if hasattr(self, '_pixmap'):
				self._pixmap.CopyArea(
					self._form, self._gc, event.x, event.y,
					event.width, event.height,
					event.x, event.y)
				return
			self._gc.FillRectangle(event.x, event.y, event.width, event.height)
			toplevel._win_lock.release()
			if event.count > 0:
				if debug: print `self`+'._expose_callback() -- count > 0'
				return
		if self._subwindows_closed:
			if debug: print 'draw subwindows'
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
			toplevel._win_lock.acquire()
			self._gc.FillRectangle(0, 0, self._width, self._height)
			toplevel._win_lock.release()

	def _do_resize(self):
		x, y, w, h = self._sizes
		x, y, w, h = self._parent_window._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		self._form.SetValues({'width': w, 'height': h, 'x': x, 'y': y})
		toplevel._win_lock.release()

	def _resize_callback(self, *rest):
		if self.is_closed():
			return
		if debug: print `self`+'._resize_callback()'
		toplevel._win_lock.acquire()
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
		toplevel._win_lock.release()
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

	def newwindow(self, *coordinates, **options):
		return apply(self._new_window, (coordinates, FALSE), options)

	def newcmwindow(self, *coordinates, **options):
		return apply(self._new_window, (coordinates, TRUE), options)
		
	def _new_window(self, coordinates, defcmap, **options):
		if debug: print `self`+'._new_window'+`coordinates`
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, ('arg count mismatch', `coordinates`)
		x, y, w, h = coordinates
		newwin = apply(_Window, (self, x, y, w, h, '', defcmap), options)
		return newwin

	def fgcolor(self, *color):
		if debug: print `self`+'.fgcolor()'
		if len(color) == 1 and type(color[0]) is TupleType:
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color
		self._xfgcolor = self._convert_color(self._fgcolor)

	def bgcolor(self, *color):
		if debug: print `self`+'.bgcolor()'
		if len(color) == 1 and type(color[0]) is TupleType:
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._bgcolor = color
		self._xbgcolor = self._convert_color(self._bgcolor)
		self._gc.background = self._gc.foreground = self._xbgcolor
		if not self._active_display_list:
			toplevel._win_lock.acquire()
			self._form.SetValues({'background': self._xbgcolor})
			toplevel._win_lock.release()

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
		toplevel._win_lock.acquire()
		self._shell.SetValues({'title': title, 'iconName': title})
		self._title = title
		toplevel._win_lock.release()

	def pop(self):
# The following statement was commented out because in the GL version
# it had the undesirable effect that when the second of two subwindows
# was popped, the first disappeared under its parent window.  It may
# be that the current situation also has undesirable side effects, but
# I haven't seen them yet.  --sjoerd
##		self._parent_window.pop()
		toplevel._win_lock.acquire()
		self._form.RaiseWindow()
		toplevel._win_lock.release()

	def push(self):
		toplevel._win_lock.acquire()
		self._form.LowerWindow()
		toplevel._win_lock.release()

	def getgeometry(self):
		if self.is_closed():
			raise error, 'window already closed'
		h = float(_mscreenheight) / _screenheight
		w = float(_mscreenwidth) / _screenwidth
		if not self._form:
			x, y = self._origpos
			return x, y, self._width * w, self._height * h
		toplevel._win_lock.acquire()
		x, y = self._form.TranslateCoords(0, 0)
		toplevel._win_lock.release()
		return float(x) * w, y * h, self._width * w, self._height * h

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
##		print 'convert_color',`color`,'%x'%c
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
		import img, imgformat
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
			import imageop
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
			import tempfile
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

	def sizebox(self, (x, y, w, h), constrainx, constrainy, callback):
		showmessage('windowinterface.sizebox not implmented',
			    type = 'error')
		return (x, y, w, h)

	def _rb_finish(self):
		form = self._form
		form.RemoveEventHandler(X.ButtonPressMask, FALSE,
					self._start_rb, None)
		form.RemoveEventHandler(X.ButtonMotionMask, FALSE,
					self._do_rb, None)
		form.RemoveEventHandler(X.ButtonReleaseMask, FALSE,
					self._end_rb, None)
		form.UngrabButton(X.AnyButton, X.AnyModifier)
		self._open_subwins()
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
		width = self._width
		height = self._height
		x, y, w, h = float(x0) / (width - 1), \
			  float(y0) / (height - 1), \
			  float(x1 - x0) / (width - 1), \
			  float(y1 - y0) / (height - 1)
		if x < 0: x = 0
		if y < 0: y = 0
		if x + w > 1: w = 1 - x
		if y + h > 1: h = 1 - y
		return x, y, w, h

	def _rb_done(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, self._rb_cvbox())
		raise _rb_done

	def _rb_cancel(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())
		raise _rb_done

	def _rb_draw(self):
		x = self._rb_start_x
		y = self._rb_start_y
		w = self._rb_width
		h = self._rb_height
		if w < 0:
			x = x + w
			w = -w
		if h < 0:
			y = y + h
			h = -h
		self._gc_rb.DrawRectangle(x, y, w, h)

	def create_box(self, msg, callback, *box):
		if self.is_closed():
			raise error, 'window already closed'
		if len(box) == 0:
			box = None
		elif len(box) == 1:
			box = box[0]
			if type(box) is not TupleType or len(box) != 4:
				raise TypeError, 'bad arguments'
		elif len(box) != 4:
			raise TypeError, 'bad arguments'

		if msg:
			msg = msg + '\n\n' + _rb_message
		else:
			msg = _rb_message
		self._close_subwins()
		self._rb_dl = self._active_display_list
		if self._rb_dl:
			d = self._rb_dl.clone()
		else:
			d = self.newdisplaylist()
		for win in self._subwindows:
			b = win._sizes
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self._rb_display = d.clone()
		d.fgcolor(255, 0, 0)
		if box:
			d.drawbox(box)
		d.render()
		self._rb_curdisp = d
##		self._rb_dialog = Dialog(None, msg, 0, 0,
##				[('Done', (self._rb_done, ())),
##				 ('Cancel', (self._rb_cancel, ()))])
		self._rb_dialog = showmessage(
			msg, type = 'message', grab = 0,
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
		v['line_style'] = X.LineOnOffDash
		self._gc_rb = form.GetGC(v)
		self._rb_box = box
		if box:
			x, y, w, h = self._convert_coordinates(box[0], box[1],
							       box[2], box[3])
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			self._rb_box = x, y, w, h
			self._rb_start_x = x
			self._rb_start_y = y
			self._rb_width = w
			self._rb_height = h
		# wait until box has been drawn or canceled
		try:
			Xt.MainLoop()
		except _rb_done:
			pass

	def _start_rb(self, w, data, e):
		self._rb_display.render()
		self._rb_curdisp.close()
		if self._rb_box:
			x = self._rb_start_x
			y = self._rb_start_y
			w = self._rb_width
			h = self._rb_height
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			if x + w/4 < e.x < x + w*3/4:
				self._rb_cx = 1
			else:
				self._rb_cx = 0
				if e.x >= x + w*3/4:
					x, w = x + w, -w
			if y + h/4 < e.y < y + h*3/4:
				self._rb_cy = 1
			else:
				self._rb_cy = 0
				if e.y >= y + h*3/4:
					y, h = y + h, -h
			if self._rb_cx and self._rb_cy:
				self._rb_last_x = e.x
				self._rb_last_y = e.y
			else:
				if not self._rb_cx:
					self._rb_start_x = x + w
					self._rb_width = e.x - self._rb_start_x
				if not self._rb_cy:
					self._rb_start_y = y + h
					self._rb_height = e.y - self._rb_start_y
		else:
			self._rb_start_x = e.x
			self._rb_start_y = e.y
			self._rb_width = self._rb_height = 0
			self._rb_cx = self._rb_cy = 0
		self._rb_draw()

	def _rb_common(self, e):
		self._rb_draw()
		if self._rb_cx and self._rb_cy:
			dx = e.x - self._rb_last_x
			dy = e.y - self._rb_last_y
			self._rb_last_x = e.x
			self._rb_last_y = e.y
			self._rb_start_x = self._rb_start_x + dx
			if self._rb_start_x + self._rb_width > self._width:
				self._rb_start_x = self._width - self._rb_width
			if self._rb_start_x < 0:
				self._rb_start_x = 0
			self._rb_start_y = self._rb_start_y + dy
			if self._rb_start_y + self._rb_height > self._height:
				self._rb_start_y = self._height - self._rb_height
			if self._rb_start_y < 0:
				self._rb_start_y = 0
		else:
			if not self._rb_cx:
				self._rb_width = e.x - self._rb_start_x
			if not self._rb_cy:
				self._rb_height = e.y - self._rb_start_y
		self._rb_box = 1

	def _do_rb(self, w, data, event):
		self._rb_common(event)
		self._rb_draw()

	def _end_rb(self, w, data, event):
		self._rb_common(event)
		self._rb_curdisp = self._rb_display.clone()
		self._rb_curdisp.fgcolor(255, 0, 0)
		self._rb_curdisp.drawbox(self._rb_cvbox())
		self._rb_curdisp.render()

	def movebox(self, coordinates, constrainx, constrainy):
		showmessage('windowinterface.movebox not implemented',
			    type = 'error')
		return coordinates

	def hitarrow(self, x, y, sx, sy, dx, dy):
		# return 1 iff (x,y) is within the arrow head
		import math
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
			return FALSE
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return FALSE
		return TRUE

	def destroy_menu(self):
		if self._menu:
			toplevel._win_lock.acquire()
			self._menu.DestroyWidget()
			toplevel._win_lock.release()
		self._menu = None
		self._menu_title = None
		self._menu_list = None
		self._accelerators = {}

	def create_menu(self, title, list):
		self.destroy_menu()
		self._menu_title = title
		self._menu_list = list
		toplevel._win_lock.acquire()
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
		toplevel._win_lock.release()
		self._menu = menu

class _DisplayList:
	def __init__(self, window, bgcolor):
		if debug: print '_DisplayList.init('+`window`+') --> '+`self`
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
		if debug: print `self`+'.close()'
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
		if debug: print `self`+'.render()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		self._rendered = TRUE
		window = self._window
		if window._active_display_list:
			for but in window._active_display_list._buttonlist:
				but._highlighted = FALSE
		toplevel._win_lock.acquire()
		width, height = window._width, window._height
		if not self._cloneof or \
		   self._cloneof is not window._active_display_list or \
		   window._active_display_list._buttonlist:
			self._clonestart = 0
		if hasattr(window, '_pixmap'):
			gc = window._gc
		else:
			gc = window._form.CreateGC({})
		font = fg = None
		i = 0
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
			cmd = entry[0]
			if cmd == 'clear':
				if not expose or window._gc.foreground != entry[1]:
					gc.foreground = entry[1]
					gc.FillRectangle(0, 0, width, height)
				gc.background = entry[1]
				gc.foreground = fg = entry[2]
				gc.line_width = entry[3]
			elif cmd == 'fg':
				gc.foreground = fg = entry[1]
			elif cmd == 'image':
				apply(gc.PutImage, entry[1:])
			elif cmd == 'linewidth':
				gc.line_width = entry[1]
			elif cmd == 'line':
				gc.foreground = entry[1]
				points = entry[2]
				x0, y0 = points[0]
				for x, y in points[1:]:
					gc.DrawLine(x0, y0, x, y)
					x0, y0 = x, y
				gc.foreground = fg
			elif cmd == 'fpolygon':
				gc.foreground = entry[1]
				gc.FillPolygon(entry[2], X.Convex, X.CoordModeOrigin)
				gc.foreground = fg
			elif cmd == 'box':
				apply(gc.DrawRectangle, entry[1:])
			elif cmd == 'fbox':
				gc.foreground = entry[1]
				apply(gc.FillRectangle, entry[2:])
				gc.foreground = fg
			elif cmd == '3dbox':
				cl, ct, cr, cb = entry[1:1+4]
				l, t, w, h = entry[5:5+4]
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
				gc.foreground = fg
			elif cmd == 'diamond':
				x, y, w, h = entry[1:]
				gc.DrawLines([(x, y + h/2),
					      (x + w/2, y),
					      (x + w, y + h/2),
					      (x + w/2, y + h),
					      (x, y + h/2)],
					     X.CoordModeOrigin)
			elif cmd == 'fdiamond':
				gc.foreground = entry[1]
				x, y, w, h = entry[2:]
				gc.FillPolygon([(x, y + h/2),
						(x + w/2, y),
						(x + w, y + h/2),
						(x + w/2, y + h),
						(x, y + h/2)],
					       X.Convex, X.CoordModeOrigin)
				gc.foreground = fg
			elif cmd == '3ddiamond':
				cl, ct, cr, cb = entry[1:1+4]
				l, t, w, h = entry[5:5+4]
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
				gc.foreground = fg
			elif cmd == 'arrow':
				gc.foreground = entry[1]
				apply(gc.DrawLine, entry[2:2+4])
				gc.FillPolygon(entry[6], X.Convex, X.CoordModeOrigin)
				gc.foreground = fg
			elif cmd == 'font':
				gc.SetFont(entry[1])
			elif cmd == 'text':
				apply(gc.DrawString, entry[1:])
		window._active_display_list = self
		if hasattr(window, '_pixmap'):
			window._pixmap.CopyArea(window._form, gc, 0, 0, width, height, 0, 0)
		window._form.UpdateDisplay()
		toplevel._win_lock.release()

	def _optimize(self, ignore = []):
		if type(ignore) is type(0):
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

	def clone(self):
		if debug: print `self`+'.clone()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		w = self._window
		new = _DisplayList(w, self._bgcolor)
		# copy all instance variables
		new._list = self._list[:]
		new._fgcolor = self._fgcolor
		new._xfgcolor = self._xfgcolor
		new._bgcolor = self._bgcolor
		new._xbgcolor = self._xbgcolor
		new._linewidth = self._linewidth
		new._font = self._font
		new._fontheight = self._fontheight
		new._baseline = self._baseline
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	#
	# Color handling
	#
	def fgcolor(self, *color):
		if debug: print `self`+'.fgcolor()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(color) == 1 and type(color[0]) is TupleType:
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color
		self._xfgcolor = self._window._convert_color(self._fgcolor)
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
		toplevel._win_lock.acquire()
		xim = toplevel._visual.CreateImage(window._depth, X.ZPixmap, 0,
				image, im_w, im_h, depth * 8, im_w * depth)
		toplevel._win_lock.release()
		self._list.append('image', xim, im_x, im_y, win_x, win_y, win_w, win_h)
		self._optimize(1)
		return float(win_x) / window._width, \
			  float(win_y) / window._height, \
			  float(win_w) / window._width, \
			  float(win_h) / window._height

	#
	# Drawing methods
	#
	def linewidth(self, width):
		if debug: print `self`+'.linewidth()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._linewidth = width
		self._list.append('linewidth', width)

	def drawline(self, color, points):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawline'+`points`

		window = self._window
		p = []
		for x, y in points:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			p.append(x, y)
		color = window._convert_color(color)
		self._list.append('line', color, p)

	def drawfpolygon(self, color, points):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawfpolygon'+`points`

		window = self._window
		p = []
		for x, y in points:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			p.append(x, y)
		color = window._convert_color(color)
		self._list.append('fpolygon', color, p)
		self._optimize(1)
		
	def drawbox(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
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
		if debug: print `self`+'.drawbox'+`coordinates`
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

	def draw3dbox(self, cl, ct, cr, cb, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		window = self._window
		x, y, w, h = coordinates
		l, t, w, h = window._convert_coordinates(x, y, w, h)
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append('3dbox', cl, ct, cr, cb, l, t, w, h)
		self._optimize(range(1,5))

	def drawdiamond(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
		window = self._window
		x, y, w, h = coordinates
		x, y, w, h = window._convert_coordinates(x, y, w, h)
		self._list.append('diamond', x, y, w, h)
		self._optimize()

	def drawfdiamond(self, color, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
		window = self._window
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		x, y, w, h = window._convert_coordinates(x, y, w, h)
		color = window._convert_color(color)
		self._list.append('fdiamond', color, x, y, w, h)
		self._optimize(1)

	def draw3ddiamond(self, cl, ct, cr, cb, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) is TupleType:
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		window = self._window
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		x, y, w, h = coordinates
		l, t, w, h = window._convert_coordinates(x, y, w, h)
		self._list.append('3ddiamond', cl, ct, cr, cb, l, t, w, h)
		self._optimize(range(1,5))

	def drawarrow(self, color, sx, sy, dx, dy):
		import math
		if debug: print `self`+'.drawarrow'+`color, sx, sy, dx, dy`
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		nsx, nsy = window._convert_coordinates(sx, sy, 0, 0)[:2]
		ndx, ndy = window._convert_coordinates(dx, dy, 0, 0)[:2]
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
		color = self._window._convert_color(color)
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
		self._list.append('arrow', color, nsx, nsy, ndx, ndy, points)
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
		if debug: print `self`+'.usefont('+`fontobj`+') --> '+`self._baseline,self._fontheight,fontobj.pointsize()`
		self._list.append('font', fontobj._font)
		return self._baseline, self._fontheight, fontobj.pointsize()

	def setfont(self, font, size):
		if debug: print `self`+'.setfont'+`font,size`
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, *opt_margin):
		if debug: print `self`+'.fitfont('+`fontname`+')'
		import string
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(opt_margin) == 0:
			margin = 0
		elif len(opt_margin) == 1:
			margin = opt_margin[0]
		else:
			raise error, 'too many arguments'
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
		import string
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = 0
		for str in strlist:
			width, height = self._font.strsize(str)
			width = width * _screenwidth / _mscreenwidth
			if width > maxwidth:
				maxwidth = width
			maxheight = maxheight + self._fontheight
		if debug: print `self`+'.strsize() --> '+`float(maxwidth)/self._window._width,maxheight`
		return float(maxwidth) / self._window._width, maxheight

	def strfit(self, text, width, height):
		if debug: print `self`+'.strfit()'
		# this could be made more efficient
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		for i in range(1, len(text)):
			w, h = self.strsize(text[:i])
			if w > width or h > height:
				return i - 1
		return len(text)

	def setpos(self, x, y):
		if debug: print `self`+'.setpos'+`x,y`
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
		import string
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
		toplevel._win_lock.acquire()
		for str in strlist:
			x0, y0 = self._window._convert_coordinates(x, y, 0, 0)[:2]
			self._list.append('text', x0, y0, str)
			self._curpos = x + float(self._font._font.TextWidth(str)) / window._width, y
			x = self._xpos
			y = y + self._fontheight
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		toplevel._win_lock.release()
		newx, newy = self._curpos
		if debug: print `self`+'.writestr('+`str`+') --> '+`oldx,oldy,maxx-oldx,newy-oldy+self._fontheight-self._baseline`
		return oldx, oldy, maxx - oldx, \
			  newy - oldy + self._fontheight - self._baseline


class _Button:
	def __init__(self, dispobj, x, y, w, h):
		if debug: print '_Button.init'+`dispobj,x,y,w,h`+' --> '+`self`
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
		if debug: print `self`+'.close()'
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

	def getwindow(self):
		if self.is_closed():
			raise error, 'button already closed'
		return self._dispobj._window

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, *color):
		if self.is_closed():
			raise error, 'button already closed'
		if len(color) == 1 and type(color[0]) is TupleType:
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._hicolor = color
		self._xhicolor = self._dispobj._window._convert_color(color)

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
		toplevel._win_lock.acquire()
		gc.background = dispobj._xbgcolor
		gc.foreground = self._xhicolor
		gc.line_width = self._hiwidth
		apply(gc.DrawRectangle, self._coordinates)
		gc.background = window._xbgcolor
		gc.foreground = window._xbgcolor
		toplevel._win_lock.release()
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

class _Font:
	def __init__(self, fontname, size):
		if debug: print '_Font.init'+`fontname,size`+' --> '+`self`
		self._fontname = fontname
		self._xfont, self._size, self._font = _findfont(fontname, size)

	def close(self):
		if debug: print `self`+'.close()'
		del self._font

	def is_closed(self):
		return not hasattr(self, '_font')

	def strsize(self, str):
		import string
		if self.is_closed():
			raise error, 'font object already closed'
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * (self._font.ascent + self._font.descent)
		toplevel._win_lock.acquire()
		for str in strlist:
			width = self._font.TextWidth(str)
			if width > maxwidth:
				maxwidth = width
		toplevel._win_lock.release()
		if debug: print `self`+'.strsize() --> '+`float(maxwidth)*_mscreenwidth/_screenwidth,float(maxheight)*_mscreenheight/_screenheight`
		return float(maxwidth) * _mscreenwidth / _screenwidth, \
			  float(maxheight) * _mscreenheight / _screenheight

	def baseline(self):
		if self.is_closed():
			raise error, 'font object already closed'
		if debug: print `self`+'.baseline() --> '+`float(self._font.ascent)*_mscreenheight/_screenheight`
		return float(self._font.ascent) * _mscreenheight / _screenheight

	def fontheight(self):
		if self.is_closed():
			raise error, 'font object already closed'
		if debug: print `self`+'.fontheight() --> '+`float(self._font.ascent+self._font.descent)*_mscreenheight/_screenheight`
		return float(self._font.ascent + self._font.descent) * _mscreenheight / _screenheight

	def pointsize(self):
		if self.is_closed():
			raise error, 'font object already closed'
		if debug: print `self`+'.pointsize() --> '+`self._size`
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
	import string
	list = string.splitfields(fontname, '-')
	if len(list) != 15:
		raise error, 'fontname not well-formed'
	return list

def _makefontname(font):
	import string
	return string.joinfields(font, '-')

def _findfont(fontname, size):
	import string
	if not _fontmap.has_key(fontname):
		raise error, 'Unknown font ' + `fontname`
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

toplevel = _Toplevel()

def newwindow(x, y, w, h, title, **options):
	return apply(toplevel.newwindow, (x, y, w, h, title), options)

def newcmwindow(x, y, w, h, title, **options):
	return apply(toplevel.newcmwindow, (x, y, w, h, title), options)

def close():
	toplevel.close()

def setcursor(cursor):
	toplevel.setcursor(cursor)

def getsize():
	return toplevel.getsize()

def usewindowlock(lock):
	toplevel.usewindowlock(lock)

def getmouse():
	return toplevel.getmouse()

def findfont(fontname, pointsize):
	return _Font(fontname, pointsize)

def beep():
	pass				# for now...

def startmonitormode():
	pass

def endmonitormode():
	pass

def settimer(sec, arg):
	return toplevel.settimer(sec, arg)

def settimerfunc(func, arg):
	toplevel.settimerfunc(func, arg)

def select_setcallback(fd, cb, arg, mask = ReadMask):
	toplevel.select_setcallback(fd, cb, arg, mask)

def mainloop():
	toplevel.mainloop()

def canceltimer(id):
	toplevel.canceltimer(id)

_end_loop = '_end_loop'			# exception for ending a loop

class _Question:
	def __init__(self, text):
		self.looping = FALSE
		self.answer = None
		showmessage(text, type = 'question',
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
		self.dialog = Dialog(None, prompt, TRUE, FALSE, list)

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

class FileDialog:
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel):
		import os
		self.cb_ok = cb_ok
		self.cb_cancel = cb_cancel
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth}
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
			attrs['width'] = 400
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
		if not self.is_closed():
			_setcursor(self._form, cursor)

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
		if not self.is_closed():
			_setcursor(self._form, cursor)

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
			showmessage(ret, type = 'error')

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
					showmessage(ret, type = 'error')
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
					showmessage(ret, type = 'error')
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
		if not self.is_closed():
			_setcursor(self._form, cursor)

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

	def create_menu(self, title, list):
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
		toplevel._win_lock.acquire()
		menu = self._form.CreatePopupMenu('dialogMenu', {})
		if title:
			list = [title, None] + list
		_create_menu(menu, list)
		self._menu = menu
		self._form.AddEventHandler(X.ButtonPressMask, FALSE,
					   self._post_menu, None)
		toplevel._win_lock.release()

	def destroy_menu(self):
		'''Destroy the pop up menu.

		This function is called automatically when a new menu
		is created using create_menu, or when the window
		object is closed.'''

		menu = self._menu
		self._menu = None
		if menu:
			toplevel._win_lock.acquire()
			menu.DestroyWidget()
			toplevel._win_lock.release()

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
				if type(widget) in (type(0.0), type(0)):
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
	def __init__(self, parent, text, useGadget = 1, name = 'windowLabel',
		     **options):
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
	def __init__(self, parent, label, callback, useGadget = 1,
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

	def _callback(self, widget, callback, call_data):
		if self.is_closed():
			return
		apply(callback[0], callback[1])

class OptionMenu(_Widget):
	'''Option menu window object.'''
	def __init__(self, parent, label, optionlist, startpos, cb,
		     useGadget = 1, name = 'windowOptionMenu', **options):
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
		attrs = {'menuHistory': initbut, 'subMenuId': self._omenu}
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
		self._form.menuHistory = self._buttons[pos]
		self._value = pos

	def setvalue(self, value):
		'''Set the currently selected option to VALUE.'''
		self.setpos(self._optionlist.index(value))

	def setoptions(self, optionlist, startpos):
		'''Set new options.

		OPTIONLIST and STARTPOS are as in the __init__ method.'''

		omenu = self._omenu
		initbut = self._do_setoptions(self._parent._form, optionlist,
					      startpos)
		self._form.subMenuId = self._omenu
		self._form.menuHistory = initbut
		omenu.DestroyWidget()

	def _do_setoptions(self, form, optionlist, startpos):
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		menu = form.CreatePulldownMenu('windowOption', {})
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
	def __init__(self, parent, menulist, useGadget = 1,
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
			menu = menubar.CreatePulldownMenu('windowMenu', {})
			button = menubar.CreateManagedWidget(
				'windowMenuButton', cascade,
				{'labelString': item,
				 'subMenuId': menu})
			_create_menu(menu, list)
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
		menu = self._form.CreatePulldownMenu('windowMenu', {})
		_create_menu(menu, list)
		omenu = button.subMenuId
		button.subMenuId = menu
		omenu.DestroyWidget()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons

# super class for Selection and List
class _List:
	def __init__(self, list, itemlist, sel_cb):
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
	def __init__(self, parent, listprompt, itemprompt, itemlist, sel_cb,
		     name = 'windowSelection', **options):
		attrs = {}
		self._attachments(attrs, options)
		selection = parent._form.CreateSelectionBox(name, attrs)
		for widget in Xmd.DIALOG_APPLY_BUTTON, \
		    Xmd.DIALOG_CANCEL_BUTTON, Xmd.DIALOG_DEFAULT_BUTTON, \
		    Xmd.DIALOG_HELP_BUTTON, Xmd.DIALOG_OK_BUTTON, \
		    Xmd.DIALOG_SEPARATOR:
			w = selection.SelectionBoxGetChild(widget)
			w.UnmanageChild()
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
		_List.__init__(self, list, itemlist, sel_cb)
		_Widget.__init__(self, parent, selection)

	def __repr__(self):
		return '<Selection instance at %x; label=%s>' % (id(self), self._text)

	def close(self):
		_List.close(self)
		_Widget.close(self)

	def setlabel(self, label):
		w = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		w.labelString = label

	def getselection(self):
		text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		if hasattr(text, 'TextFieldGetString'):
			return text.TextFieldGetString()
		else:
			return text.TextGetString()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

class List(_Widget, _List):
	def __init__(self, parent, listprompt, itemlist, sel_cb,
		     rows = 10, useGadget = 1, name = 'windowList', **options):
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
			try:
				attrs['width'] = options['width']
			except KeyError:
				pass
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
			try:
				attrs['width'] = options['width']
			except KeyError:
				pass
			list = parent._form.CreateScrolledList(name, attrs)
			widget = list
			self._text = '<None>'
		_List.__init__(self, list, itemlist, sel_cb)
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
	def __init__(self, parent, prompt, inittext, chcb, accb, useGadget = 1,
		     name = 'windowTextfield', **options):
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
		try:
			attrs['columns'] = options['columns']
		except KeyError:
			pass
		attrs['value'] = inittext
		try:
			attrs['editable'] = options['editable']
		except KeyError:
			pass
		text = form.CreateTextField(name, attrs)
		text.ManageChild()
		if not widget:
			widget = text
		if chcb:
			text.AddCallback('valueChangedCallback',
					 self._callback, chcb)
		if accb:
			text.AddCallback('activateCallback',
					 self._callback, accb)
		self._text = text
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

	def _callback(self, w, (func, arg), call_data):
		if self.is_closed():
			return
		apply(func, arg)

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
			try:
				attrs[option] = options[option]
			except KeyError:
				pass
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
		import string
		if type(text) is ListType:
			text = string.joinfields(text, '\n')
		self._form.TextSetString(text)
		self._linecache = None

	def gettext(self):
		return self._form.TextGetString()

	def getlines(self):
		import string
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
	def __init__(self, parent, useGadget = 1, name = 'windowSeparator',
		     **options):
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
		     vertical = TRUE, callback = None,
		     buttontype = 'pushbutton', useGadget = 1,
		     name = 'windowRowcolumn', **options):
		attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
			 'traversalOn': FALSE}
		if not vertical:
			attrs['orientation'] = Xmd.HORIZONTAL
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
					# sorry, no separators in horizontal
					# ButtonRows.
					dummy = rowcolumn.CreateManagedWidget(
						'buttonSeparator',
						separator, {})
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
					'submenu', {})
				button = menu.CreateManagedWidget(
					'submenuLabel', cascadebutton,
					{'labelString': label,
					 'subMenuId': submenu})
				_create_menu(submenu, callback)
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
		     vertical = FALSE, showvalue = TRUE, name = 'windowScale',
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
	def Selection(self, listprompt, itemprompt, itemlist, sel_cb,
		      **options):
		return apply(Selection,
			     (self, listprompt, itemprompt, itemlist, sel_cb),
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
	def Canvas(self, **options):
		from WindowCanvas import Canvas
		return apply(Canvas, (self,), options)
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

class _SubWindow(SubWindow):
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
		widget = _SubWindow(self, name = name)
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
	def __init__(self, title, resizable = FALSE, grab = FALSE,
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
			try:
				deleteCallback = options['deleteCallback']
			except KeyError:
				pass
			else:
				self._shell.AddWMProtocolCallback(
					_delete_window, self._delete_callback,
					deleteCallback)
				self._shell.deleteResponse = Xmd.DO_NOTHING
		self._showing = FALSE
		self._not_shown = []
		self._shown = []
		_WindowHelpers.__init__(self)
		_MenuSupport.__init__(self)

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
			shell = self._shell
		except AttributeError:
			shell = None
		try:
			form = self._form
		except AttributeError:
			pass
		else:
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
			self._show.remove(w)
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
		sw = float(_mscreenwidth) /  _screenwidth
		sh = float(_mscreenheight) /  _screenheight
		x, y  = self._form.TranslateCoords(0, 0)
		val = self._form.GetValues(['width', 'height'])
		w = val['width']
		h = val['height']
		return x * sw, y * sh, w * sw, h * sh

	def pop(self):
		pass

	def _delete_callback(self, widget, client_data, call_data):
		if type(client_data) == StringType:
			if client_data == 'hide':
				self.hide()
			elif client_data == 'close':
				self.close()
			else:
				raise error, 'bad deleteCallback argument'
			return
		func, args = client_data
		apply(func, args)

def Dialog(title, prompt, grab, vertical, list):
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
