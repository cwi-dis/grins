import Xlib, Xt, Xm, X, Xmd, XEvent, Xtdefs, Xcursorfont
from EVENTS import *
import time

error = 'windowinterface.error'

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

_image_cache = {}			# cache of prepared images
_cache_full = 0				# 1 if we shouldn't cache more images
_image_size_cache = {}
_cm_cache = {}

_rb_message = """\
Use left mouse button to draw a box.
Click `Done' when ready or `Cancel' to cancel."""

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

def roundi(x):
	if x < 0:
		return roundi(x + 1024) - 1024
	return int(x + 0.5)

def _rgb2torgb8(data, reader):
	import imageop
	return imageop.rgb2rgb8(data, reader.width, reader.height)

import imgconvert, imgformat
imgconvert.addconverter(imgformat.rgb, imgformat.xrgb8, _rgb2torgb8, 2)

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
		if debug: print '_TopLevel.__init__() --> '+`self`
		self._win_lock = _DummyLock()
		self._toplevel = self
		import sys
		Xt.ToolkitInitialize()
		dpy = Xt.OpenDisplay(None, None, 'Windowinterface', [], sys.argv)
		self._setupcolormap(dpy)
		self._main = Xt.CreateApplicationShell('shell',
					Xt.ApplicationShell,
					{'visual': self._visual,
					 'colormap': self._colormap,
					 'depth': self._depth,
					 'mappedWhenManaged': X.FALSE,
					 'x': 500,
					 'y': 500,
					 'width': 1,
					 'height': 1,
					 'input': X.TRUE})
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

	def _colormask(self, mask):
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

	def _setupcolormap(self, dpy):
		visuals = dpy.GetVisualInfo({'c_class': X.TrueColor})
		if visuals:
			# found one, use the deepest
			v_best = visuals[0]
			for v in visuals:
				if v.depth > v_best.depth:
					v_best = v
			self._visual = v_best
			self._depth = v_best.depth
			self._red_shift, self._red_mask = \
					 self._colormask(v_best.red_mask)
			self._green_shift, self._green_mask = \
					   self._colormask(v_best.green_mask)
			self._blue_shift, self._blue_mask = \
					  self._colormask(v_best.blue_mask)
			self._colormap = v_best.CreateColormap(X.AllocNone)
			print 'Using TrueColor visual, depth = %d, masks = %x %x %x' % (v_best.depth, v_best.red_mask, v_best.green_mask, v_best.blue_mask)
			return
		visuals = dpy.GetVisualInfo({'depth': 8,
					     'c_class': X.PseudoColor})
		if len(visuals) == 0:
			raise error, 'no proper visuals available'
		self._visual = visuals[0]
		self._depth = self._visual.depth
		self._colormap = self._visual.CreateColormap(X.AllocNone)
		self._red_shift, self._red_mask = 5, 7
		self._green_shift, self._green_mask = 0, 7
		self._blue_shift, self._blue_mask = 3, 3
		(plane_masks, pixels) = self._colormap.AllocColorCells(1, 8, 1)
		xcolors = []
		for n in range(256):
			# The colormap is set up so that the colormap
			# index has the meaning: rrrbbggg.
			xcolors.append((n+pixels[0],
				  int((float((n >> self._red_shift) & self._red_mask) / float(self._red_mask)) * 255.)<<8,
				  int((float((n >> self._green_shift) & self._green_mask) / float(self._green_mask)) * 255.)<<8,
				  int((float((n >> self._blue_shift) & self._blue_mask) / float(self._blue_mask)) * 255.)<<8,
				  X.DoRed|X.DoGreen|X.DoBlue))
		self._colormap.StoreColors(xcolors)
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

	def newwindow(self, x, y, w, h, title):
		if debug: print 'Toplevel.newwindow'+`x, y, w, h, title`
		window = _Window(self, x, y, w, h, title, 0)
		return window

	def newcmwindow(self, x, y, w, h, title):
		if debug: print 'Toplevel.newcmwindow'+`x, y, w, h, title`
		window = _Window(self, x, y, w, h, title, 1)
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

class _Window:
	def __init__(self, parent, x, y, w, h, title, defcmap):
		if debug: print '_Window.init() --> '+`self`
		self._parent_window = parent
		self._origpos = x, y
		if toplevel._visual.c_class == X.TrueColor:
			defcmap = 0
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
			 'width': w, 'height': h,
			 'colormap': self._colormap,
			 'visual': self._visual,
			 'depth': self._depth,
			 'title': title}
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
		toplevel._win_lock.release()
		self._init2()
 
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

	def _init2(self):
		if debug: print `self`+'.init2()'
		self._bgcolor = self._parent_window._bgcolor
		self._fgcolor = self._parent_window._fgcolor
		self._xbgcolor = self._convert_color(self._bgcolor)
		self._xfgcolor = self._convert_color(self._fgcolor)
		self._subwindows = []
		self._subwindows_closed = 0
		self._displaylists = []
		self._active_display_list = None
		self._redraw_func = None
		self._parent_window._subwindows.append(self)
		self._toplevel = self._parent_window._toplevel
		self._menu = None
		self._menu_title = None
		self._menu_list = None
		self._accelerators = {}
		self._closecallbacks = []
		self.setcursor(self._parent_window._cursor)
		toplevel._win_lock.acquire()
		self._do_open_win()
		toplevel._win_lock.release()
		return

	def close(self):
		if debug: print `self`+'.close()'
		if self.is_closed():
			return
		for func in self._closecallbacks[:]:
			func(self)
		for win in self._subwindows[:]:
			win.close()
		for displist in self._displaylists[:]:
			displist.close()
		del self._displaylists
		toplevel._win_lock.acquire()
		if self._form:
			self._form.DestroyWidget()
		del self._form
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
		self._form = pwin._form.CreateManagedWidget('subwin',
			Xm.DrawingArea, attrs)
		self._do_open_win()
		if self._menu_title or self._menu_list:
			self.create_menu(self._menu_title, self._menu_list)
		self._open_subwins()

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
		self._gc = form.CreateGC({'background': self._xbgcolor,
					  'foreground': self._xbgcolor})
		form.RealizeWidget()
		toplevel._win_lock.release()
		form.AddCallback('exposeCallback', self._expose_callback, None)
		form.AddCallback('resizeCallback', self._resize_callback, None)
		form.AddCallback('inputCallback', self._input_callback, None)
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
		self._subwindows_closed = 1

	def _open_subwins(self):
		if self.is_closed():
			raise error, 'window already closed'
		for win in self._subwindows:
			if not win.is_closed():
				win._open_win()
		self._subwindows_closed = 0

	def _call_on_close(self, func):
		if not func in self._closecallbacks:
			self._closecallbacks.append(func)

	def _input_callback(self, widget, client_data, call_data, *rest):
		if debug: print `self`+'._input_callback()'
		import struct
		ev = struct.unpack('i', call_data[4:8])[0]
		ev = Xlib.getevent(ev)	# KLUDGE!
		decoded_event = XEvent.mkevent(ev)
		if decoded_event.type == X.KeyPress:
			toplevel._win_lock.acquire()
			string = Xlib.LookupString(ev)[0]
			toplevel._win_lock.release()
			if self._accelerators.has_key(string):
				f, a = self._accelerators[string]
				apply(f, a)
				return
			for i in range(len(string)):
				enterevent(self, KeyboardInput, string[i])
		elif decoded_event.type == X.KeyRelease:
			pass
		elif decoded_event.type in (X.ButtonPress, X.ButtonRelease):
			if decoded_event.type == X.ButtonPress:
				if decoded_event.button == X.Button1:
					ev = Mouse0Press
				elif decoded_event.button == X.Button2:
					ev = Mouse1Press
				elif decoded_event.button == X.Button3:
					if self._menu:
						self._menu.MenuPosition(ev)
						self._menu.ManageChild()
						return
					ev = Mouse2Press
				else:
					return	# unsupported mouse button
			else:
				if decoded_event.button == X.Button1:
					ev = Mouse0Release
				elif decoded_event.button == X.Button2:
					ev = Mouse1Release
				elif decoded_event.button == X.Button3:
					if self._menu:
						# ignore buttonrelease
						# when we have a menu
						return
					ev = Mouse2Release
				else:
					return	# unsupported mouse button
			x = float(decoded_event.x) / self._width
			y = float(decoded_event.y) / self._height
			buttons = []
			adl = self._active_display_list
			if adl:
				for but in adl._buttonlist:
					if but._inside(x, y):
						buttons.append(but)
			enterevent(self, ev, (x, y, buttons))
		else:
			print 'unknown event',`decoded_event.type`

	def _expose_callback(self, widget, client_data, call_data, *rest):
		if debug: print `self`+'._expose_callback()'
		if not self._form:
			return		# why were we called anyway?
		if call_data:
			import struct
			event = struct.unpack('i', call_data[4:8])[0]
			event = Xlib.getevent(event)
			decoded_event = XEvent.mkevent(event)
			if decoded_event.count > 0:
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
			self._active_display_list.render()
			for but in buttons:
				but.highlight()
		else:
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
		if debug: print `self`+'._resize_callback()'
		toplevel._win_lock.acquire()
		val = self._form.GetValues(['width', 'height'])
		toplevel._win_lock.release()
		self._width = val['width']
		self._height = val['height']
		for displist in self._displaylists[:]:
			displist.close()
		for win in self._subwindows:
			win._do_resize()
		if hasattr(self, '_rb_dl'):
			self._rb_cancel()
		enterevent(self, ResizeWindow, None)

	def newwindow(self, *coordinates):
		return self._new_window(coordinates, 0)

	def newcmwindow(self, *coordinates):
		return self._new_window(coordinates, 1)
		
	def _new_window(self, coordinates, defcmap):
		if debug: print `self`+'._new_window'+`coordinates`
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, ('arg count mismatch', `coordinates`)
		x, y, w, h = coordinates
		newwin = _Window(self, x, y, w, h, '', defcmap)
		newwin._init2()
		return newwin

	def fgcolor(self, *color):
		if debug: print `self`+'.fgcolor()'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color
		self._xfgcolor = self._convert_color(self._fgcolor)

	def bgcolor(self, *color):
		if debug: print `self`+'.bgcolor()'
		if len(color) == 1 and type(color[0]) == type(()):
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
		if not self.is_closed() or not self._form:
			for win in self._subwindows:
				win.setcursor(cursor)
			try:
				toplevel._win_lock.acquire()
				if cursor == 'watch':
					self._form.DefineCursor(_watchcursor)
				elif cursor == 'channel':
					self._form.DefineCursor(_channelcursor)
				elif cursor == 'link':
				        self._form.DefineCursor(_linkcursor)
				elif cursor == '':
					self._form.UndefineCursor()
				else:
					raise error, 'unknown cursor glyph'
			except:
				toplevel._win_lock.release()
		self._cursor = cursor

	def newdisplaylist(self, *bgcolor):
		if len(bgcolor) == 1 and type(bgcolor[0]) == type(()):
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
		self._shell.SetValues({'title': title})
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
##		global _cache_full
##		cachekey = `file`+':'+`self._width`+'x'+`self._height`
##		if _image_cache.has_key(cachekey):
##			retval = _image_cache[cachekey]
##			filename = retval[-1]
##			try:
##				import rgbimg
##				image = rgbimg.longimagedata(filename)
##				return retval[:-1] + (image,)
##			except:		# any error...
##				del _image_cache[cachekey]
##				import posix
##				try:
##					posix.unlink(filename)
##				except posix.error:
##					pass
		import img, imgformat
		if self._depth == 8:
			format = imgformat.xrgb8
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
		return x, y, width - left - right, height - top - bottom, \
			  left, bottom, width, height, depth, scale, \
			  image

	def _image_size(self, file):
		# XXX--assume that images was displayed at least once
		return _image_size_cache[file]

	def register(self, ev, func, arg):
		event.register(self, ev, func, arg)

	def unregister(self, ev):
		event.unregister(self, ev)

	def sizebox(self, (x, y, w, h), constrainx, constrainy, callback):
		showmessage('windowinterface.sizebox not implmented')
		return (x, y, w, h)

	def _rb_finish(self):
		form = self._form
		form.RemoveEventHandler(X.ButtonPressMask, X.FALSE,
					self._start_rb, None)
		form.RemoveEventHandler(X.ButtonMotionMask, X.FALSE,
					self._do_rb, None)
		form.RemoveEventHandler(X.ButtonReleaseMask, X.FALSE,
					self._do_rb, None)
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

	def _rb_cancel(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())

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
			if type(box) != type(()) or len(box) != 4:
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
		self._rb_dialog = Dialog(None, msg, 0, 0,
				[('', 'Done', (self._rb_done, ())),
				 ('', 'Cancel', (self._rb_cancel, ()))])
		self._rb_callback = callback
		form = self._form
		form.AddEventHandler(X.ButtonPressMask, X.FALSE,
				     self._start_rb, None)
		form.AddEventHandler(X.ButtonMotionMask, X.FALSE,
				     self._do_rb, None)
		form.AddEventHandler(X.ButtonReleaseMask, X.FALSE,
				     self._end_rb, None)
		cursor = form.Display().CreateFontCursor(Xcursorfont.crosshair)
		form.GrabButton(X.AnyButton, X.AnyModifier, X.TRUE,
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

	def _start_rb(self, w, data, event):
		self._rb_display.render()
		self._rb_curdisp.close()
		e = XEvent.mkevent(event)
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
		e = XEvent.mkevent(event)
		self._rb_common(e)
		self._rb_draw()

	def _end_rb(self, w, data, event):
		e = XEvent.mkevent(event)
		self._rb_common(e)
		self._rb_curdisp = self._rb_display.clone()
		self._rb_curdisp.fgcolor(255, 0, 0)
		self._rb_curdisp.drawbox(self._rb_cvbox())
		self._rb_curdisp.render()

	def movebox(self, coordinates, constrainx, constrainy):
		showmessage('windowinterface.movebox not implmented')
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
			return 0
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return 0
		return 1

	def destroy_menu(self):
		if self._menu:
			self._menu.DestroyWidget()
		self._menu = None
		self._menu_title = None
		self._menu_list = None
		self._accelerators = {}

	def create_menu(self, title, list):
		self.destroy_menu()
		self._menu_title = title
		self._menu_list = list
		menu = self._form.CreatePopupMenu('menu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			dummy = menu.CreateManagedWidget('menuTitle',
							 Xm.Label, {})
			dummy.labelString = title
			dummy = menu.CreateManagedWidget('menuSeparator',
							 Xm.Separator, {})
		self._accelerators = {}
		_create_menu(menu, self._accelerators, list)
		self._menu = menu

# three menu utility functions
def _menu_callback(widget, (func, arg), call_data):
	apply(func, arg)

def _create_menu(menu, acc, list):
	accelerator = None
	for entry in list:
		if entry is None:
			dummy = menu.CreateManagedWidget('separator',
							 Xm.Separator, {})
			continue
		if acc is None:
			label, callback = entry
		else:
			accelerator, label, callback = entry
		if type(callback) is type([]):
			button = menu.CreateManagedWidget('submenuLabel',
							  Xm.CascadeButton, {})
			button.labelString = label
			submenu = menu.CreatePulldownMenu('submenu', {})
			button.subMenuId = submenu
			_create_menu(submenu, acc, callback)
		else:
			if type(callback) is not type(()):
				callback = (callback, (label,))
			if accelerator:
				if type(accelerator) is not type('') or \
				   len(accelerator) != 1:
					raise error, 'menu accelerator must be single character'
				acc[accelerator] = callback
			button = menu.CreateManagedWidget('menuLabel',
						Xm.PushButtonGadget, {})
			button.labelString = label
			button.AddCallback('activateCallback', _menu_callback,
					   callback)
			if accelerator:
				button.acceleratorText = accelerator

class _DisplayList:
	def __init__(self, window, bgcolor):
		if debug: print '_DisplayList.init('+`window`+') --> '+`self`
		self._window = window
		self._rendered = 0
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
		toplevel._win_lock.acquire()
		self._pixmap = window._form.CreatePixmap(window._width,
							 window._height,
							 window._depth)
		# reversed foreground and background for clearing
		self._gc = self._pixmap.CreateGC({
			  'background': self._xbgcolor,
			  'foreground': self._xbgcolor,
			  'line_width': 1})
		# clear pixmap since it may contain garbage
		self._gc.FillRectangle(0, 0, window._width, window._height)
		# set foreground and background properly
		self._gc.background = self._xbgcolor
		self._gc.foreground = self._xfgcolor
		self._gc.line_width = self._linewidth
		toplevel._win_lock.release()

	def close(self):
		if debug: print `self`+'.close()'
		if self.is_closed():
			return
		for but in self._buttonlist[:]:
			but.close()
		window = self._window
		window._displaylists.remove(self)
		toplevel._win_lock.acquire()
		if window._active_display_list == self:
			window._active_display_list = None
			window._expose_callback(None, None, None)
		del self._window
		del self._buttonlist
		del self._gc
		del self._pixmap
		del self._font
		toplevel._win_lock.release()

	def is_closed(self):
		return not hasattr(self, '_window')

	def render(self):
		if debug: print `self`+'.render()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		self._rendered = 1
		w = self._window
		if w._active_display_list:
			for but in w._active_display_list._buttonlist:
				but._highlighted = 0
		w._active_display_list = self
		toplevel._win_lock.acquire()
		self._pixmap.CopyArea(w._form, self._gc, 0, 0, w._width, w._height, 0, 0)
		toplevel._win_lock.release()

	def clone(self):
		if debug: print `self`+'.clone()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		w = self._window
		new = _DisplayList(w, self._bgcolor)
		ngc = new._gc
		ogc = self._gc
		toplevel._win_lock.acquire()
		self._pixmap.CopyArea(new._pixmap, self._gc, 0, 0, w._width, w._height, 0, 0)
		# somehow copy GC too
		ngc.foreground = ogc.foreground
		ngc.line_width = ogc.line_width
		if self._font:
			ngc.SetFont(self._font._font)
		toplevel._win_lock.release()
		# copy all instance variables
		new._fgcolor = self._fgcolor
		new._xfgcolor = self._xfgcolor
		new._bgcolor = self._bgcolor
		new._xbgcolor = self._xbgcolor
		new._linewidth = self._linewidth
		new._font = self._font
		new._fontheight = self._fontheight
		new._baseline = self._baseline
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
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color
		self._xfgcolor = self._window._convert_color(self._fgcolor)
		toplevel._win_lock.acquire()
		self._gc.foreground = self._xfgcolor
		toplevel._win_lock.release()

	#
	# Buttons
	#
	def newbutton(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
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
		self._gc.PutImage(xim, im_x, im_y, win_x, win_y, win_w, win_h)
		toplevel._win_lock.release()
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
		toplevel._win_lock.acquire()
		self._gc.line_width = width
		toplevel._win_lock.release()

	def drawline(self, color, points):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawline'+`points`

		window = self._window
		color = self._window._convert_color(color)
		self._gc.foreground = color

		toplevel._win_lock.acquire()
		x0, y0 = points[0]
		x0, y0 = window._convert_coordinates(x0, y0, 0, 0)[:2]
		for x, y in points[1:]:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			self._gc.DrawLine(x0, y0, x, y)
			x0, y0 = x, y
		self._gc.foreground = self._xfgcolor
		toplevel._win_lock.release()

	def drawfpolygon(self, color, points):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawfpolygon'+`points`
		window = self._window
		gc = self._gc
		color = window._convert_color(color)
		p = []
		for x, y in points:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			p.append(x, y)
		toplevel._win_lock.acquire()
		gc.foreground = color
		gc.FillPolygon(p, X.Convex, X.CoordModeOrigin)
		gc.foreground = self._xfgcolor
		toplevel._win_lock.release()

	def drawbox(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
		window = self._window
		x, y, w, h = coordinates
		x, y, w, h = window._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		self._gc.DrawRectangle(x, y, w, h)
		toplevel._win_lock.release()

	def drawfbox(self, color, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
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
		toplevel._win_lock.acquire()
		self._gc.foreground = color
		self._gc.FillRectangle(x, y, w, h)
		self._gc.foreground = self._xfgcolor
		toplevel._win_lock.release()

	def draw3dbox(self, cl, ct, cr, cb, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		window = self._window
		gc = self._gc
		x, y, w, h = coordinates
		l, t, w, h = window._convert_coordinates(x, y, w, h)
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
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		toplevel._win_lock.acquire()
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
		toplevel._win_lock.release()

	def drawdiamond(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
		window = self._window
		x, y, w, h = coordinates
		x, y, w, h = window._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		self._gc.DrawLines([(x, y + h/2),
				    (x + w/2, y),
				    (x + w, y + h/2),
				    (x + w/2, y + h),
				    (x, y + h/2)],
				   X.CoordModeOrigin)
		toplevel._win_lock.release()

	def drawfdiamond(self, color, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
		window = self._window
		gc = self._gc
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		x, y, w, h = window._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gc.foreground = window._convert_color(color)
		gc.FillPolygon([(x, y + h/2),
				(x + w/2, y),
				(x + w, y + h/2),
				(x + w/2, y + h),
				(x, y + h/2)],
			       X.Convex, X.CoordModeOrigin)
		gc.foreground = self._xfgcolor
		toplevel._win_lock.release()

	def draw3ddiamond(self, cl, ct, cr, cb, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		window = self._window
		gc = self._gc
		x, y, w, h = coordinates
		l, t, w, h = window._convert_coordinates(x, y, w, h)
		r = l + w
		b = t + h
		x = l + w/2
		y = t + h/2
		n = int(3.0 * w / h + 0.5)
		ll = l + n
		tt = t + 3
		rr = r - n
		bb = b - 3

		toplevel._win_lock.acquire()
		gc.foreground = window._convert_color(cl)
		gc.FillPolygon([(l, y), (x, t), (x, tt), (ll, y)],
			       X.Convex, X.CoordModeOrigin)
		gc.foreground = window._convert_color(ct)
		gc.FillPolygon([(x, t), (r, y), (rr, y), (x, tt)],
			       X.Convex, X.CoordModeOrigin)
		gc.foreground = window._convert_color(cr)
		gc.FillPolygon([(r, y), (x, b), (x, bb), (rr, y)],
			       X.Convex, X.CoordModeOrigin)
		gc.foreground = window._convert_color(cb)
		gc.FillPolygon([(l, y), (ll, y), (x, bb), (x, b)],
			       X.Convex, X.CoordModeOrigin)
		gc.foreground = self._xfgcolor
		toplevel._win_lock.release()

	def drawarrow(self, color, sx, sy, dx, dy):
		import math
		if debug: print `self`+'.drawarrow'+`color, sx, sy, dx, dy`
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		gc = self._gc
		sx, sy = window._convert_coordinates(sx, sy, 0, 0)[:2]
		dx, dy = window._convert_coordinates(dx, dy, 0, 0)[:2]
		color = self._window._convert_color(color)
		lx = dx - sx
		ly = dy - sy
		if lx == ly == 0:
			angle = 0.0
		else:
			angle = math.atan2(ly, lx)
		rotation = math.pi + angle
		cos = math.cos(rotation)
		sin = math.sin(rotation)
		points = [(dx, dy)]
		points.append(roundi(dx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
			      roundi(dy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos))
		points.append(roundi(dx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
			      roundi(dy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos))
		toplevel._win_lock.acquire()
		gc.foreground = color
		gc.DrawLine(sx, sy, dx, dy)
		gc.FillPolygon(points, X.Convex, X.CoordModeOrigin)
		gc.foreground = self._xfgcolor
		toplevel._win_lock.release()

	#
	# Font and text handling
	#
	def usefont(self, fontobj):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
		toplevel._win_lock.acquire()
		self._gc.SetFont(fontobj._font)
		toplevel._win_lock.release()
		f = float(_screenheight) / _mscreenheight / self._window._height
		self._baseline = fontobj.baseline() * f
		self._fontheight = fontobj.fontheight() * f
		if debug: print `self`+'.usefont('+`fontobj`+') --> '+`self._baseline,self._fontheight,fontobj.pointsize()`
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
		firsttime = 1
		height = fontobj.fontheight() * _screenheight / _mscreenheight
		while firsttime or height > window._height*mfac:
			firsttime = 0
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
			self._gc.DrawString(x0, y0, str)
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
		self._coordinates = window._convert_coordinates(x, y, w, h)
		self._color = dispobj._fgcolor
		self._hicolor = dispobj._fgcolor
		self._xcolor = dispobj._xfgcolor
		self._xhicolor = dispobj._xfgcolor
		self._linewidth = dispobj._linewidth
		self._hiwidth = self._linewidth
		self._highlighted = 0
		dispobj._buttonlist.append(self)
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		toplevel._win_lock.acquire()
		dispobj._gc.DrawRectangle(self._coordinates)
		toplevel._win_lock.release()

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
			return 1
		else:
			return 0

	def getwindow(self):
		if self.is_closed():
			raise error, 'button already closed'
		return self._dispobj._window

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, *color):
		if self.is_closed():
			raise error, 'button already closed'
		if len(color) == 1 and type(color[0]) == type(()):
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
		gc.DrawRectangle(self._coordinates)
		gc.background = window._xbgcolor
		gc.foreground = window._xbgcolor
		toplevel._win_lock.release()
		self._highlighted = 1

	def unhighlight(self):
		if self.is_closed():
			raise error, 'button already closed'
		dispobj = self._dispobj
		if dispobj._window._active_display_list != dispobj:
			raise error, 'can only unhighlight rendered button'
		if self._highlighted:
			self._highlighted = 0
			self._dispobj.render()

class _Event:
	def __init__(self):
		self._queue = []
		self._timeout_called = 0
		self._fdlist = {}
		self._savefds = []
		self._timers = []
		self._callbacks = {}
		self._windows = {}
		self._select_fdlist = []
		self._select_dict = {}
		self._timenow = time.time()
		self._timerid = 0
		self._modal = 0
		self._looping = 0

	def _checktime(self):
		if self._modal:
			return
		timenow = time.time()
		timediff = timenow - self._timenow
		while self._timers:
			(t, arg, tid) = self._timers[0]
			t = t - timediff
			if t > 0:
				self._timers[0] = (t, arg, tid)
				self._timenow = timenow
				return
			# Timer expired, enter it in event queue.
			# Also, check next timer in timer queue (by looping).
			del self._timers[0]
			self._queue.append((None, TimerEvent, arg))
			timediff = -t	# -t is how much too late we were
		self._timenow = timenow # Fix by Jack
		if self._looping:
			self._loop()

	def _looping_timeout_callback(self, client_data, id):
		if debug: print 'event._looping_timeout_callback'
		self._checktime()

	def settimer(self, sec, arg):
		self._checktime()
		if self._looping:
			id = Xt.AddTimeOut(int(sec * 1000),
				  self._looping_timeout_callback, None)
		t = 0
		self._timerid = self._timerid + 1
		for i in range(len(self._timers)):
			time, dummy, tid = self._timers[i]
			if t + time > sec:
				self._timers[i] = (time - sec + t, dummy, tid)
				self._timers.insert(i, (sec - t, arg, self._timerid))
				return self._timerid
			t = t + time
		self._timers.append(sec - t, arg, self._timerid)
		return self._timerid

	def canceltimer(self, id):
		for i in range(len(self._timers)):
			t, arg, tid = self._timers[i]
			if tid == id:
				del self._timers[i]
				if i < len(self._timers):
					tt, arg, tid = self._timers[i]
					self._timers[i] = (tt + t, arg, tid)
				return
##		raise error, 'unknown timer id'

	def entereventunique(self, win, event, arg):
		if (win, event, arg) not in self._queue:
			self._queue.append((win, event, arg))
			if self._looping:
				self._loop()

	def enterevent(self, win, event, arg):
		self._checktime()
		self._queue.append((win, event, arg))
		if self._looping:
			self._loop()

	def _timeout_callback(self, client_data, id):
		if debug: print 'event._timeout_callback'
		self._timeout_called = 1

	def _input_callback(self, client_data, fd, id):
		if debug: print 'event._input_callback'
		self.entereventunique(None, FileEvent, fd)
		if not self._looping:
			Xt.RemoveInput(self._fdlist[fd])
			del self._fdlist[fd]
			self._savefds.append(fd)

	def _getevent(self, timeout):
		toplevel._win_lock.acquire()
		for fd in self._savefds:
			self._fdlist[fd] = Xt.AddInput(fd,
				  Xtdefs.XtInputReadMask, self._input_callback,
				  None)
		self._savefds = []
		if timeout is not None and timeout > 0.001:
			if debug: print '_getevent: timeout:',`timeout`
			self._timeout_called = 0
			id = Xt.AddTimeOut(int(timeout * 1000),
				  self._timeout_callback, None)
		else:
			if debug: print '_getevent: no timeout'
			self._timeout_called = 1
		qtest = Xt.Pending()
		while 1:
			# get all pending events
			while qtest:
				toplevel._win_lock.release()
				event = Xt.ProcessEvent(Xtdefs.XtIMAll)
				toplevel._win_lock.acquire()
				qtest = Xt.Pending()
			# if there were any for us, return
			if self._queue:
				if not self._timeout_called:
					Xt.RemoveTimeOut(id)
				toplevel._win_lock.release()
				return 1
			# if we shouldn't block, return
			if timeout is not None:
				if self._timeout_called:
					toplevel._win_lock.release()
					return 0
			# block on next iteration
			qtest = 1

	def _trycallback(self):
		if not self._queue:
			raise error, 'internal error: event expected'
		window, event, value = self._queue[0]
		if self._modal:
			if event != ResizeWindow:
				if debug: print 'event._trycallback: modal, no resize'
				return 0
		if event == FileEvent:
			if self._select_dict.has_key(value):
				if debug: print 'event._trycallback: FileEvent: callback'
				del self._queue[0]
				func, arg = self._select_dict[value]
				apply(func, arg)
				return 1
			if debug: print 'event._trycallback: FileEvent: no callback'
		if window and window.is_closed():
			return 0
		for w in [window, None]:
			while 1:
				for key in [(w, event), (w, None)]:
					if self._windows.has_key(key):
						del self._queue[0]
						func, arg = self._windows[key]
						apply(func, (arg, window,
							  event, value))
						return 1
				if not w:
					break
				w = w._parent_window
				if w == toplevel:
					break
		return 0

	def _loop(self):
		while self._queue:
			if not self._trycallback():
				del self._queue[0]

	def testevent(self):
		while 1:
			self._checktime()
			if self._getevent(0):
				if not self._trycallback():
					# get here if the first event
					# in the queue does not cause
					# a callback
					return 1
				continue
			# get here only when there are no pending events
			return 0

	def peekevent(self):
		if self.testevent():
			return self._queue[0]
		else:
			return None

	def readevent_timeout(self, timeout):
		if self._getevent(timeout):
			event = self._queue[0]
			del self._queue[0]
			return event
		else:
			return None

	def waitevent_timeout(self, timeout):
		dummy = self._getevent(timeout)

	def waitevent(self):
		self.waitevent_timeout(None)

	def readevent(self):
		while 1:
			if self.testevent():
				return self.readevent_timeout(None)
			modal = self._modal
			if not modal and self._timers:
				(t, arg, tid) = self._timers[0]
				t0 = time.time()
			else:
				t = None
			self.waitevent_timeout(t)
			if not modal and self._timers:
				t1 = time.time()
				dt = t1 - t0
				self._timers[0] = (t - dt, arg, tid)

	def pollevent(self):
		if self.testevent():
			return self.readevent()
		else:
			return None

	def setfd(self, fd):
		if debug: print 'setfd',`fd`
		if type(fd) <> type(1):
			fd = fd.fileno()
		self._fdlist[fd] = Xt.AddInput(fd, Xtdefs.XtInputReadMask,
			  self._input_callback, None)

	def rmfd(self, fd):
		if self._fdlist.has_key(fd):
			id = self._fdlist[fd]
			Xt.RemoveInput(id)
			del self._fdlist[fd]
		if fd in self._savefds:
			self._savefds.remove(fd)

	def getfd(self):
		return -1		# for now...

	def register(self, win, event, func, arg):
		key = (win, event)
		if func:
			self._windows[key] = (func, arg)
			if win:
				win._call_on_close(self.remove_window_callbacks)
		elif self._windows.has_key(key):
			del self._windows[key]
		else:
			raise error, 'not registered'

	def unregister(self, win, event):
		try:
			self.register(win, event, None, None)
		except error:
			pass

	def getregister(self, win, event):
		try:
			return self._windows[(win, event)]
		except KeyError:
			raise error, 'not registered'

	def remove_window_callbacks(self, window):
		# called when window closes
		for w, e in self._windows.keys():
			if w == window:
				self.unregister(w, e)

	def setcallback(self, event, func, arg):
		self.register(None, event, func, arg)

	def clean_callbacks(self):
		for win, event in self._windows.keys():
			if win and win.is_closed():
				self.register(win, event, None, None)

	def select_setcallback(self, fd, cb, arg):
		if type(fd) <> type(1):
			fd = fd.fileno()
		if cb is None:
			self._select_fdlist.remove(fd)
			del self._select_dict[fd]
			self.rmfd(fd)
			return
		if not self._select_dict.has_key(fd):
			self._select_fdlist.append(fd)
		self._select_dict[fd] = (cb, arg)
		self.setfd(fd)

	def startmodal(self, window):
		self._modal = 1

	def endmodal(self):
		self._modal = 0

	def mainloop(self):
		self._looping = 1
		t = 0
		for time, arg, tid in self._timers:
			time = time + t
			t = time
			id = Xt.AddTimeOut(int(time * 1000),
				  self._looping_timeout_callback, None)
		Xt.MainLoop()

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
event = _Event()

def newwindow(x, y, w, h, title):
	return toplevel.newwindow(x, y, w, h, title)

def newcmwindow(x, y, w, h, title):
	return toplevel.newcmwindow(x, y, w, h, title)

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

def readevent():
	return event.readevent()

def readevent_timeout(timeout):
	return event.readevent_timeout(timeout)

def pollevent():
	return event.pollevent()

def waitevent():
	event.waitevent()

def waitevent_timeout(timeout):
	event.waitevent_timeout(timeout)

def peekevent():
	return event.peekevent()

def testevent():
	return event.testevent()

def enterevent(win, ev, arg):
	event.enterevent(win, ev, arg)

def setfd(fd):
	event.setfd(fd)

def rmfd(fd):
	event.rmfd(fd)

def getfd():
	return -1

def findfont(fontname, pointsize):
	return _Font(fontname, pointsize)

def beep():
	pass				# for now...

def startmonitormode():
	pass

def endmonitormode():
	pass

def settimer(sec, arg):
	return event.settimer(sec, arg)

def setcallback(ev, func, arg):
	event.setcallback(ev, func, arg)

def register(win, ev, func, arg):
	event.register(win, ev, func, arg)

def unregister(win, ev):
	event.unregister(win, ev)

def getregister(win, ev):
	event.getregister(win, ev)

def clean_callbacks():
	event.clean_callbacks()

def select_setcallback(fd, cb, arg):
	event.select_setcallback(fd, cb, arg)

def startmodal(window):
	event.startmodal(window)

def endmodal():
	event.endmodal()

def mainloop():
	event.mainloop()

def canceltimer(id):
	event.canceltimer(id)

class Dialog:
	def __init__(self, title, prompt, grab, vertical, list, *coordinates):
		# the optional coordinates are ignored for now
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) == 4:
			self._geometry = coordinates
		elif len(coordinates) != 0:
			raise TypeError, 'arg count mismatch'
		self._menu = None
		self._grab = grab
		if not title:
			title = ''
		if grab:
			attrs = {'allowOverlap': 0,
				 'dialogStyle':
					Xmd.DIALOG_PRIMARY_APPLICATION_MODAL,
				 'title': title,
				 'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth}
			if debug: print `self` + '.CreateFormDialog()'
			self._form = toplevel._main.CreateFormDialog(
							 'grabDialog', attrs)
		else:
			if debug: print `self` + '.CreatePopupShell()'
			shell = toplevel._main.CreatePopupShell('dialogShell',
				Xt.ApplicationShell,
				{'title': title,
				 'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
			if debug: print `self` + '.CreateManagedWidget()'
			self._form = shell.CreateManagedWidget('dialogForm',
						Xm.Form, {'allowOverlap': 0})
			self._shell = shell
		self._form.AddEventHandler(X.ButtonPressMask, X.FALSE,
					   self._post_menu, None)
		attrs = {'leftAttachment': Xmd.ATTACH_FORM,
			 'rightAttachment': Xmd.ATTACH_FORM,
			 'entryAlignment': Xmd.ALIGNMENT_CENTER}
		if prompt:
			label = self._form.CreateManagedWidget('dialogPrompt',
					Xm.Label,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_FORM})
			label.labelString = prompt
			label.alignment = Xmd.ALIGNMENT_CENTER
			attrs['topAttachment'] = Xmd.ATTACH_WIDGET
			attrs['topWidget'] = label
		else:
			attrs['topAttachment'] = Xmd.ATTACH_FORM
		if not vertical:
			attrs['orientation'] = Xmd.HORIZONTAL
			attrs['packing'] = Xmd.PACK_COLUMN
		rowcolumn = self._form.CreateManagedWidget('dialogRowcolumn',
							   Xm.RowColumn, attrs)
		for entry in list:
			if entry is None:
				if vertical:
					dummy = rowcolumn.CreateManagedWidget(
						'dialogSeparator',
						Xm.Separator, {})
				continue
			if type(entry) == type(()):
				accelerator, label, callback = entry
			else:
				accelerator, label, callback = '', entry, None
			if callback and type(callback) is not type(()):
				callback = (callback, (label,))
			button = rowcolumn.CreateManagedWidget('dialogButton',
					Xm.PushButtonGadget,
					{'labelString': label})
			button.AddCallback('activateCallback',
					   self._callback, callback)
		self._form.ManageChild()
		if not grab:
			if debug: print `self` + '.RealizeWidget()'
			shell.RealizeWidget()
			if debug: print `self` + '.Popup()'
			shell.Popup(0)

	def __del__(self):
		self.close()

	def getgeometry(self):
##		# this is waht we should do, if we wanted to actually
##		# return the coordinates that we are using
##		x, y = self._form.TranslateCoords(0, 0)
##		v = self._form.GetValues(['width', 'height'])
##		w = v['width']
##		h = v['height']
##		xf = float(_mscreenheight) / _screenheight
##		yf = float(_mscreenwidth) / _screenwidth
##		return x * xf, y * yf, w * xf, h * yf
		# instead we just return the coordinates that we were
		# given and which we don't actually use
		return self._geometry

	def _post_menu(self, w, client_data, call_data):
		if not self._menu:
			return
		decoded_event = XEvent.mkevent(call_data)
		if decoded_event.button == X.Button3:
			self._menu.MenuPosition(call_data)
			self._menu.ManageChild()

	def _callback(self, w, callback, call_data):
		if self._grab:
			self.close()
		if callback:
			apply(callback[0], callback[1])

	def create_menu(self, title, list):
		menu = self._form.CreatePopupMenu('dialogMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			dummy = menu.CreateManagedWidget('menuTitle',
							 Xm.Label, {})
			dummy.labelString = title
			dummy = menu.CreateManagedWidget('menuSeparator',
							 Xm.Separator, {})
		self._accelerators = {}
		_create_menu(menu, self._accelerators, list)
		self._menu = menu

	def settitle(self, title):
		self._form.dialogTitle = title

	def close(self):
		if hasattr(self, '_shell') and self._shell:
			self._shell.UnmanageChild()
			self._shell.DestroyWidget()
			self._shell = None
			self._form = None
		if self._form:
			self._form.UnmanageChild()
			self._form.DestroyWidget()
			self._form = None
		self._menu = None

	def is_closed(self):
		return self._form is None

def showmessage(text):
	dummy = Dialog(None, text, 1, 0, ['Done'])

_dialog_end = '_dialog_end'		# used for breaking out of a loop

class _Question(Dialog):
	def __init__(self, text):
		self.looping = 0
		self.answer = None
		Dialog.__init__(self, None, text, 1, 0,
				[('', 'Yes', (self.callback, (1,))),
				 ('', 'No', (self.callback, (0,)))])

	def run(self):
		try:
			event.startmodal(None)
			try:
				self.looping = 1
				while self.answer is None:
					dummy = event.readevent()
			except _dialog_end:
				import sys
				sys.last_traceback = sys.exc_traceback = None
		finally:
			event.endmodal()
		return self.answer

	def callback(self, answer):
		self.answer = answer
		if self.looping:
			raise _dialog_end

def showquestion(text):
	return _Question(text).run()

class _MultChoice(Dialog):
	def __init__(self, prompt, msg_list, defindex):
		self.looping = 0
		self.answer = None
		self.msg_list = msg_list
		list = []
		for msg in msg_list:
			list.append('', msg, (self.callback, (msg,)))
		Dialog.__init__(self, None, prompt, 1, 0, list)

	def run(self):
		try:
			event.startmodal(None)
			try:
				self.looping = 1
				while self.answer is None:
					dummy = event.readevent()
			except _dialog_end:
				import sys
				sys.last_traceback = sys.exc_traceback = None
		finally:
			event.endmodal()
		return self.answer

	def callback(self, msg):
		for i in range(len(self.msg_list)):
			if msg == self.msg_list[i]:
				self.answer = i
				if self.looping:
					raise _dialog_end
				return

def multchoice(prompt, list, defindex):
	return _MultChoice(prompt, list, defindex).run()

class FileDialog:
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel):
		import os
		self.cb_ok = cb_ok
		self.cb_cancel = cb_cancel
		attrs = {'dialogStyle': Xmd.DIALOG_PRIMARY_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth}
		if prompt:
			form = toplevel._main.CreateFormDialog(
						   'fileSelect', attrs)
			self._form = form
			label = form.CreateManagedWidget('filePrompt',
					Xm.Label,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_FORM})
			label.labelString = prompt
			dialog = form.CreateManagedWidget('fileSelect',
					Xm.FileSelectionBox,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_WIDGET,
					 'topWidget': label})
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
		if not filter:
			filter = '*'
		self.filter = filter
		filter = os.path.join(directory, filter)
		dialog.FileSelectionDoSearch(filter)
		text = dialog.FileSelectionBoxGetChild(Xmd.DIALOG_TEXT)
		text.value = file
		self._form.ManageChild()

	def close(self):
		if self._form:
			self._form.UnmanageChild()
			self._form.DestroyWidget()
			self._dialog = None
			self._form = None

	def is_closed(self):
		return self._form is None

	def _cancel_callback(self, *rest):
		must_close = 1
		try:
			if self.cb_cancel:
				ret = self.cb_cancel()
				if ret:
					if type(ret) == type(''):
						showmessage(ret)
					must_close = 0
					return
		finally:
			if must_close:
				self.close()

	def _ok_callback(self, widget, client_data, call_data):
		import os
		text = self._dialog.FileSelectionBoxGetChild(
						   Xmd.DIALOG_TEXT)
		filename = text.TextGetString()
		text = self._dialog.FileSelectionBoxGetChild(
						   Xmd.DIALOG_FILTER_TEXT)
		filter = text.TextGetString()
		dir, filter = os.path.split(filter)
		filename = os.path.join(dir, filename)
		if not os.path.isfile(filename):
			if os.path.isdir(filename):
				filter = os.path.join(filename, filter)
				self._dialog.FileSelectionDoSearch(filter)
				return
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) == type(''):
					showmessage(ret)
				return
		self.close()

class InputDialog:
	def __init__(self, prompt, default, cb):
		attrs = {'dialogStyle': Xmd.DIALOG_PRIMARY_APPLICATION_MODAL,
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

	def _ok(self, w, client_data, call_data):
		text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		value = text.TextGetString()
		self.close()
		if client_data:
			client_data(value)

	def _cancel(self, w, client_data, call_data):
		self.close()

	def close(self):
		if self._form:
			self._form.UnmanageChild()
			self._form.DestroyWidget()
			self._form = None

	def is_closed(self):
		return self._form is None

_apply_error = 'windowinterface._apply_error'

class AttrDialog:
	def __init__(self, title, prompt, list, cb_apply, cb_close):
		self._cb_apply = cb_apply
		self._cb_close = cb_close
		if not title:
			title = ''
		self._title = title
		self._shell = toplevel._main.CreatePopupShell('attrDialog',
				Xt.ApplicationShell,
				{'title': title,
				 'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		self._form = self._shell.CreateManagedWidget('attrForm',
						Xm.Form, {'allowOverlap': 0})
		attrs = {'leftAttachment': Xmd.ATTACH_FORM,
			 'rightAttachment': Xmd.ATTACH_FORM,
			 'numColumns': len(list),
			 'packing': Xmd.PACK_COLUMN,
			 'orientation': Xmd.HORIZONTAL}
		if prompt:
			label = self._form.CreateManagedWidget('attrPrompt',
					Xm.Label,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_FORM})
			label.labelString = prompt
			label.alignment = Xmd.ALIGNMENT_CENTER
			attrs['topAttachment'] = Xmd.ATTACH_WIDGET
			attrs['topWidget'] = label
		else:
			attrs['topAttachment'] = Xmd.ATTACH_FORM
		rowcolumn = self._form.CreateManagedWidget('attrRowcolumn',
							   Xm.RowColumn, attrs)
		self.entries = []
		for entry in list:
			name, label, help, bclass, b = entry[:5]
			if len(entry) > 5:
				list = entry[5]
			else:
				list = None
			button = rowcolumn.CreateManagedWidget('attrButton',
						Xm.PushButtonGadget, {})
			button.labelString = label
			button.AddCallback('activateCallback',
					   self._buttonhelp, help)
			C = bclass(name, label, rowcolumn, b, list)
			self.entries.append(C)
		attrs = {'leftAttachment': Xmd.ATTACH_FORM,
			 'rightAttachment': Xmd.ATTACH_FORM,
			 'topAttachment': Xmd.ATTACH_WIDGET,
			 'topWidget': rowcolumn}
		separator = self._form.CreateManagedWidget('attrSeparator',
							   Xm.Separator, attrs)
		attrs['topWidget'] = separator
		attrs['rightAttachment'] = Xmd.ATTACH_NONE
		cancel = self._form.CreateManagedWidget('attrCancelButton',
						Xm.PushButtonGadget, attrs)
		cancel.labelString = 'Cancel'
		cancel.AddCallback('activateCallback', self._cancel, None)
		attrs['leftAttachment'] = Xmd.ATTACH_WIDGET
		attrs['leftWidget'] = cancel
		restore = self._form.CreateManagedWidget('attrRestoreButton',
						Xm.PushButtonGadget, attrs)
		restore.labelString = 'Restore'
		restore.AddCallback('activateCallback', self.restore, None)
		attrs['leftWidget'] = restore
		apply = self._form.CreateManagedWidget('attrApplyButton',
						Xm.PushButtonGadget, attrs)
		apply.labelString = 'Apply'
		apply.AddCallback('activateCallback', self._apply, None)
		attrs['leftWidget'] = apply
		ok = self._form.CreateManagedWidget('attrOkButton',
						Xm.PushButtonGadget, attrs)
		ok.labelString = 'OK'
		ok.AddCallback('activateCallback', self._ok, None)
		self._form.ManageChild()
		self._shell.RealizeWidget()
		self._shell.Popup(0)

	def __del__(self):
		self.close()

	def __repr__(self):
		return '<AttrDialog instance at %x' % id(self) + \
		       ', title=' + `self._title` + '>'

	def close(self):
		if self._shell:
			self._shell.UnmanageChild()
			self._shell.DestroyWidget()
			self._shell = None
			self._form = None
			self.entries = None
			if self._cb_close:
				self._cb_close()

	def restore(self, *rest):
		for w in self.entries:
			w.restore()

	def settitle(self, title):
		self._shell.title = title
		self._title = title

	def do_apply(self):
		dict = {}
		for w in self.entries:
			name = w.getname()
			try:
				value = w.getvalue()
			except _apply_error:
				return 0
			# only return changed values
			if value != w.item.getcurrent():
				try:
					dict[name] = w.item.parsevalue(value)
				except:
					showmessage('%s: parsing value failed' % name)
					return 0
		if self._cb_apply:
			self._cb_apply(dict)
		return 1		# success

	def _buttonhelp(self, widget, client_data, call_data):
		showmessage(client_data)

	def _cancel(self, *rest):
		self.close()

	def _apply(self, *rest):
		dummy = self.do_apply()

	def _ok(self, *rest):
		if not self.do_apply():
			return
		self.close()

class _C:
	def __init__(self, name, label, parent, item, dummy):
		self.name = name
		self.label = label
		self.parent = parent
		self.item = item
		self.form = parent.CreateForm('attrForm', {'allowOverlap': 0})
		self.form.ManageChild()
		self.button = self.form.CreateManagedWidget('attrResetButton',
					Xm.PushButtonGadget,
					{'topAttachment': Xmd.ATTACH_FORM,
					 'bottomAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM})
		self.button.labelString = 'Reset'
		self.button.AddCallback('activateCallback', self._reset, None)

	def __del__(self):
		self.close()

	def _reset(self, w, client_data, call_data):
		self.reset()

	def close(self):
		if self.form:
			self.form.UnmanageChild()
			self.form.DestroyWidget()
			self.form = None

	def is_closed(self):
		return self.form is None

	def getname(self):
		return self.name

	def getvalue(self):
		return self.item.getcurrent()

	def getdefaultvalue(self):
		return self.item.getdefault()

	def restore(self):
		# restore values to initial value
		pass

	def reset(self):
		# reset values to default value
		pass

class AttrOption(_C):
	def __init__(self, name, label, parent, item, list):
		if len(list) == 0:
			raise error, 'option list must contain elements'
		_C.__init__(self, name, label, parent, item, list)
		initbut, menu_pane = self._docreatemenu(list)
		self.widget = self.form.CreateOptionMenu('attrOptionMenu',
					{'menuHistory': initbut,
					 'subMenuId': menu_pane,
					 'leftAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_FORM,
					 'bottomAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_WIDGET,
					 'rightWidget': self.button})
		self.widget.OptionLabelGadget().UnmanageChild()
		self.widget.ManageChild()

	def _cb(self, widget, value, call_data):
		self.new_value = value

	def _newmenu(self):
		different = 0
		list = self.item.choices()
		if len(list) != len(self._list):
			different = 1
		else:
			for i in range(len(list)):
				if list[i] != self._list[i]:
					different = 1
					break
		if not different:
			return
		initbut, menu_pane = self._docreatemenu(list)
		self.widget.subMenuId.DestroyWidget()
		self.widget.SetValues({'menuHistory': initbut,
				       'subMenuId': menu_pane})

	def _docreatemenu(self, list):
		self.buttons = {}
		menu_pane = self.form.CreatePulldownMenu('attrOption', {})
		self.def_but = initbut = None
		value = self.item.getcurrent()
		default = self.item.getdefault()
		self._list = list
		for item in list:
			but = menu_pane.CreatePushButton('attrOptionButton',
						  {'labelString': item})
			but.AddCallback('activateCallback', self._cb, item)
			but.ManageChild()
			if self.def_but is None or default == item:
				self.def_but = but
			if initbut is None or value == item:
				initbut = but
				self.new_value = item
			self.buttons[item] = but
		return initbut, menu_pane

	def reset(self):
		value = self.item.getdefault()
		if self.buttons.has_key(value):
			self.widget.menuHistory = self.buttons[value]
			self.new_value = value

	def restore(self):
		self._newmenu()
		value = self.item.getcurrent()
		if self.buttons.has_key(value):
			self.widget.menuHistory = self.buttons[value]
			self.new_value = value

	def getvalue(self):
		return self.new_value

class AttrString(_C):
	def __init__(self, name, label, parent, item, dummy):
		_C.__init__(self, name, label, parent, item, dummy)
		self.widget = self.form.CreateManagedWidget('attrText',
					Xm.TextField,
					{'leftAttachment': Xmd.ATTACH_FORM,
					 'topAttachment': Xmd.ATTACH_FORM,
					 'bottomAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_WIDGET,
					 'rightWidget': self.button})
		self.widget.value = item.getcurrent()

	def __del__(self):
		self.widget.UnmanageChild()
		self.widget.DestroyWidget()
		self.widget = None

	def getvalue(self):
		return self.widget.TextFieldGetString()

	def reset(self):
		self.widget.value = self.item.getdefault()

	def restore(self):
		self.widget.value = self.item.getcurrent()

class AttrInt(AttrString):
	def __init__(self, name, label, parent, item, dummy):
		AttrString.__init__(self, name, label, parent, item, dummy)

class AttrFloat(AttrString):
	def __init__(self, name, label, parent, item, dummy):
		AttrString.__init__(self, name, label, parent, item, dummy)

class AttrFile(_C):
	def __init__(self, name, label, parent, item, dummy):
		_C.__init__(self, name, label, parent, item, dummy)
		attrs = {'leftAttachment': Xmd.ATTACH_FORM,
			 'topAttachment': Xmd.ATTACH_FORM,
			 'bottomAttachment': Xmd.ATTACH_FORM}
		self.widget = self.form.CreateManagedWidget('attrFileText',
							  Xm.TextField, attrs)
		self.widget.value = item.getcurrent()
		attrs['leftAttachment'] = Xmd.ATTACH_WIDGET
		attrs['leftWidget'] = self.widget
		attrs['rightAttachment'] = Xmd.ATTACH_WIDGET
		attrs['rightWidget'] = self.button
		button = self.form.CreateManagedWidget('attrBrowserButton',
						Xm.PushButtonGadget, attrs)
		button.labelString = 'Brwsr'
		button.AddCallback('activateCallback', self.browser, None)

	def reset(self):
		self.widget.value = self.item.getdefault()

	def restore(self):
		self.widget.value = self.item.getcurrent()

	def getvalue(self):
		return self.widget.TextFieldGetString()

	def browser(self, *rest):
		import os
		file = self.getvalue()
		if file == '' or file == '/dev/null':
			dir, file = '.', ''
		else:
			if os.path.isdir(file):
				dir, file = file, '.'
			else:
				dir, file = os.path.split(file)
		FileDialog('Choose File for ' + self.label, dir, '*', file,
			   self._ok_cb, None)

	def _ok_cb(self, filename):
		import os
		cwd = os.getcwd()
		if filename[:len(cwd)] == cwd:
			filename = filename[len(cwd):]
			if filename and filename[0] != '/':
				filename = cwd + filename
			elif filename:
				filename = filename[1:]
			else:
				filename = '.'
		self.widget.value = filename

class _Widget:
	def __init__(self, widget):
		self._showing = 0
		self._form = widget
		self.show()

	def show(self):
		if debug: print `self` + '.ManageChild()'
		self._form.ManageChild()
		self._showing = 1

	def hide(self):
		if debug: print `self` + '.UnmanageChild()'
		self._form.UnmanageChild()
		self._showing = 0

	def is_showing(self):
		return self._showing

	def close(self):
		if hasattr(self, '_form'):
			self.hide()
			if debug: print `self` + '.DestroyWidget()'
			self._form.DestroyWidget()
			del self._form

	def is_closed(self):
		return not hasattr(self, '_form')

	# support methods, only used by derived classes
	def _attachments(self, attrs, position):
		for pos in position.keys():
			widget = position[pos]
			if pos in ('left', 'top', 'right', 'bottom'):
				if widget:
					attrs[pos + 'Attachment'] = \
						  Xmd.ATTACH_WIDGET
					attrs[pos + 'Widget'] = widget._form
				else:
					attrs[pos + 'Attachment'] = \
						  Xmd.ATTACH_FORM
			else:
				raise error, 'bad position key'

class Label(_Widget):
	def __init__(self, parent, text, position):
		attrs = {}
		self._attachments(attrs, position)
		if debug: print `self` + '.create()'
		label = parent._form.CreateManagedWidget('windowLabel',
							 Xm.Label, attrs)
		label.labelString = text
		_Widget.__init__(self, label)

	def setlabel(self, text):
		self._form.labelString = text

class OptionMenu(_Widget):
	def __init__(self, parent, label, optionlist, startpos, cb, position):
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		if debug: print `self` + '.CreatePulldownMenu()'
		menu, initbut = self._do_setoptions(parent._form, optionlist,
						    startpos)
		attrs = {'menuHistory': initbut, 'subMenuId': menu}
		self._attachments(attrs, position)
		option = parent._form.CreateOptionMenu('windowOptionMenu',
						       attrs)
		if label is not None:
			option.labelString = label
		else:
			l = option.OptionLabelGadget()
			l.UnmanageChild()
		self._callback = cb
		self._parentform = parent._form
		_Widget.__init__(self, option)

	def _cb(self, widget, value, call_data):
		self._value = value
		if self._callback:
			f, a = self._callback
			apply(f, a)

	def getpos(self):
		return self._value

	def getvalue(self):
		return self._optionlist[self._value]

	def setpos(self, pos):
		self._form.menuHistory = self._buttons[pos]
		self._value = pos

	def _do_setoptions(self, form, optionlist, startpos):
		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		menu = form.CreatePulldownMenu('windowOption', {})
		self._optionlist = optionlist
		self._value = startpos
		self._buttons = []
		for i in range(len(optionlist)):
			item = optionlist[i]
			button = menu.CreatePushButton('windowOptionButton',
						       {'labelString': item})
			button.AddCallback('activateCallback', self._cb, i)
			button.ManageChild()
			if startpos == i:
				initbut = button
			self._buttons.append(button)
		return menu, initbut

	def setoptions(self, optionlist, startpos):
		menu, initbut = self._do_setoptions(self._parentform,
						    optionlist, startpos)
		self._form.subMenuId = menu
		self._form.menuHistory = initbut

class PulldownMenu(_Widget):
	def __init__(self, parent, menulist, position):
		attrs = {}
		self._attachments(attrs, position)
		menubar = parent._form.CreateMenuBar('windowMenubar', attrs)
		for item, list in menulist:
			button = menubar.CreateManagedWidget(
				'windowMenuButton', Xm.CascadeButton, {})
			button.labelString = item
			menu = menubar.CreatePulldownMenu('windowMenu', {})
			button.subMenuId = menu
			_create_menu(menu, None, list)
		_Widget.__init__(self, menubar)

class Selection(_Widget):
	def __init__(self, parent, listprompt, itemprompt, itemlist, sel_cb, position):
		attrs = {}
		self._attachments(attrs, position)
		if debug: print `self` + '.CreateSelectionBox()'
		selection = parent._form.CreateSelectionBox('windowSelection',
						  attrs)
		list = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST)
		self._list = list
		list.selectionPolicy = Xmd.SINGLE_SELECT
		list.listSizePolicy = Xmd.CONSTANT
		for i in range(len(itemlist)):
			list.ListAddItem(itemlist[i], i + 1)
		self._itemlist = itemlist
		for widget in Xmd.DIALOG_APPLY_BUTTON, \
		    Xmd.DIALOG_CANCEL_BUTTON, Xmd.DIALOG_DEFAULT_BUTTON, \
		    Xmd.DIALOG_HELP_BUTTON, Xmd.DIALOG_OK_BUTTON, \
		    Xmd.DIALOG_SEPARATOR:
			w = selection.SelectionBoxGetChild(widget)
			w.UnmanageChild()
		w = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		if listprompt is None:
			w.UnmanageChild()
		else:
			w.labelString = listprompt
		w = selection.SelectionBoxGetChild(
					    Xmd.DIALOG_SELECTION_LABEL)
		if itemprompt is None:
			w.UnmanageChild()
		else:
			w.labelString = itemprompt
		if sel_cb:
			list.AddCallback('singleSelectionCallback',
					 self._callback, sel_cb)
		_Widget.__init__(self, selection)

	def _callback(self, w, (func, arg), call_data):
		apply(func, arg)

	def close(self):
		if hasattr(self, '_form'):
			del self._itemlist
			del self._list
			_Widget.close(self)

	def setlabel(self, label):
		w = selection.SelectionBoxGetChild(Xmd.DIALOG_LIST_LABEL)
		w.labelString = label

	def getselection(self):
		text = self._form.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		return text.TextGetString()

	def getselected(self):
		pos = self._list.ListGetSelectedPos()
		if pos:
			return pos[0] - 1
		else:
			return None

	def getlistitem(self, pos):
		return self._itemlist[pos]

	def addlistitem(self, item, pos):
		if pos < 0:
			pos = len(self._itemlist)
		self._list.ListAddItem(item, pos + 1)
		self._itemlist.insert(pos, item)

	def dellistitem(self, pos):
		del self._itemlist[pos]
		self._list.ListDeletePos(pos + 1)

	def replacelistitem(self, pos, newitem):
		self._itemlist[pos] = newitem
		self._list.ListDeleteItem(item)
		self._list.ListAddItem(newitem, pos + 1)

	def delalllistitems(self):
		self._itemlist = []
		self._list.ListDeleteAllItems()

	def selectitem(self, pos):
		if pos < 0:
			pos = len(self._itemlist) - 1
		self._list.ListSelectPos(pos + 1, X.TRUE)

class List(_Widget):
	def __init__(self, parent, listprompt, itemlist, sel_cb, position):
		attrs = {'resizePolicy': Xmd.RESIZE_NONE}
		self._attachments(attrs, position)
		if listprompt is not None:
			form = parent._form.CreateManagedWidget(
				'windowListForm', Xm.Form, attrs)
			label = form.CreateManagedWidget('windowListLabel',
					Xm.Label,
					{'topAttachment': Xmd.ATTACH_FORM,
					 'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM})
			self._label = label
			label.labelString = listprompt
			list = form.CreateScrolledList('windowList',
					{'topAttachment': Xmd.ATTACH_WIDGET,
					 'topWidget': label,
					 'leftAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM,
					 'bottomAttachment': Xmd.ATTACH_FORM,
					 'visibleItemCount': 10,
					 'selectionPolicy': Xmd.SINGLE_SELECT,
					 'listSizePolicy': Xmd.CONSTANT})
			list.ManageChild()
			widget = form
		else:
			attrs['visibleItemCount'] = 10
			attrs['selectionPolicy'] = Xmd.SINGLE_SELECT
			attrs['listSizePolicy'] = Xmd.CONSTANT
			list = parent._form.CreateScrolledList('windowList',
						     attrs)
			widget = list
		self._list = list
		for i in range(len(itemlist)):
			list.ListAddItem(itemlist[i], i + 1)
		self._itemlist = itemlist
		if sel_cb:
			list.AddCallback('singleSelectionCallback',
					 self._callback, sel_cb)
		_Widget.__init__(self, widget)

	def _callback(self, w, (func, arg), call_data):
		apply(func, arg)

	def close(self):
		if hasattr(self, '_form'):
			del self._itemlist
			del self._list
			_Widget.close(self)

	def setlabel(self, label):
		if not hasattr(self, '_label'):
			raise error, 'List created without label'
		self._label.labelString = label

	def getselected(self):
		pos = self._list.ListGetSelectedPos()
		if pos:
			return pos[0] - 1
		else:
			return None

	def getlistitem(self, pos):
		return self._itemlist[pos]

	def addlistitem(self, item, pos):
		if pos < 0:
			pos = len(self._itemlist)
		self._list.ListAddItem(item, pos + 1)
		self._itemlist.insert(pos, item)

	def dellistitem(self, pos):
		if pos < 0:
			pos = len(self._itemlist) - 1
		del self._itemlist[pos]
		self._list.ListDeletePos(pos + 1)

	def replacelistitem(self, pos, newitem):
		self._itemlist[pos] = newitem
		self._list.ListDeleteItem(item)
		self._list.ListAddItem(newitem, pos + 1)

	def delalllistitems(self):
		self._itemlist = []
		self._list.ListDeleteAllItems()

	def selectitem(self, pos):
		if pos < 0:
			pos = len(self._itemlist) - 1
		self._list.ListSelectPos(pos + 1, X.TRUE)

class TextInput(_Widget):
	def __init__(self, parent, prompt, inittext, cb, position):
		attrs = {}
		self._attachments(attrs, position)
		if prompt is not None:
			form = parent._form.CreateManagedWidget(
				'windowTextfieldForm', Xm.Form, attrs)
			label = form.CreateManagedWidget(
				'windowTextfieldLabel', Xm.Label,
				{'topAttachment': Xmd.ATTACH_FORM,
				 'leftAttachment': Xmd.ATTACH_FORM,
				 'bottomAttachment': Xmd.ATTACH_FORM})
			self._label = label
			label.labelString = prompt
			text = form.CreateTextField('windowTextfield',
					{'topAttachment': Xmd.ATTACH_FORM,
					 'leftAttachment': Xmd.ATTACH_WIDGET,
					 'leftWidget': label,
					 'bottomAttachment': Xmd.ATTACH_FORM,
					 'rightAttachment': Xmd.ATTACH_FORM})
			text.ManageChild()
			widget = form
		else:
			text = parent._form.CreateTextField('windowTextfield',
							    attrs)
			widget = text
		self._text = text
		text.value = inittext
		if cb:
			text.AddCallback('activateCallback', self._callback,
					 cb)
		_Widget.__init__(self, widget)

	def _callback(self, w, (func, arg), call_data):
		apply(func, arg)

	def setlabel(self, label):
		if not hasattr(self, '_label'):
			raise error, 'TextInput create without label'
		self._label.labelString = label

	def gettext(self):
		return self._text.TextGetString()

	def settext(self, text):
		self._text.value = text

class TextEdit(_Widget):
	def __init__(self, parent, inittext, cb, position):
		attrs = {'editMode': Xmd.MULTI_LINE_EDIT,
			 'editable': X.TRUE,
			 'rows': 10}
		self._attachments(attrs, position)
		text = parent._form.CreateScrolledText('windowText', attrs)
		text.value = inittext
		if cb:
			text.AddCallback('activateCallback', self._callback,
					 cb)
		_Widget.__init__(self, text)

	def _callback(self, w, (func, arg), call_data):
		apply(func, arg)

	def settext(self, text):
		import string
		if type(text) == type([]):
			text = string.joinfields(text, '\n')
		self._form.value = text

	def gettext(self):
		return self._form.TextGetString()

	def getlines(self):
		import string
		text = self.gettext()
		text = string.splitfields(text, '\n')
		if len(text) > 0 and text[-1] == '':
			del text[-1]
		return text

class Separator(_Widget):
	def __init__(self, parent, position):
		attrs = {}
		self._attachments(attrs, position)
		separator = parent._form.CreateManagedWidget('windowSeparator',
							Xm.Separator, attrs)
		_Widget.__init__(self, separator)

class ButtonRow(_Widget):
	def __init__(self, parent, vertical, buttonlist, position):
		attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
			 'packing': Xmd.PACK_COLUMN}
		if not vertical:
			attrs['orientation'] = Xmd.HORIZONTAL
		self._attachments(attrs, position)
		rowcolumn = parent._form.CreateManagedWidget('windowRowcolumn',
							Xm.RowColumn, attrs)
		self._buttons = []
		for entry in buttonlist:
			if type(entry) == type(()):
				accelerator, label, callback = entry
			else:
				accelerator, label, callback = '', entry, None
			if callback and type(callback) is not type(()):
				callback = (callback, (label,))
			button = rowcolumn.CreateManagedWidget('windowButton',
					Xm.PushButtonGadget,
					{'labelString': label})
			button.AddCallback('activateCallback',
					   self._callback, callback)
			self._buttons.append(button)
		_Widget.__init__(self, rowcolumn)

	def _callback(self, widget, callback, call_data):
		if callback:
			apply(callback[0], callback[1])

	def hide(self, *opt_button):
		if len(opt_button) == 0:
			_Widget.hide(self)
			return
		if len(opt_button) == 1:
			button = opt_button[0]
			if not 0 <= button < len(self._buttons):
				raise error, 'button number out of range'
			self._buttons[button].UnmanageChild()
			return
		raise error, 'too many arguments'

	def show(self, *opt_button):
		if len(opt_button) == 0:
			_Widget.show(self)
			return
		if len(opt_button) == 1:
			button = opt_button[0]
			if not 0 <= button < len(self._buttons):
				raise error, 'button number out of range'
			self._buttons[button].ManageChild()
			return
		raise error, 'too many arguments'

class Slider(_Widget):
	def __init__(self, parent, prompt, vertical, minimum, initial, maximum, cb, position):
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
			 'showValue': X.TRUE,
			 'value': initial}
		self._attachments(attrs, position)
		scale = parent._form.CreateScale('windowScale', attrs)
		scale.AddCallback('valueChangedCallback', self._callback, cb)
		if prompt is None:
			prompt = ''
		scale.titleString = prompt
		_Widget.__init__(self, scale)

	def _callback(self, widget, callback, call_data):
		if callback:
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
		if type(0.0) in [type(minimum), type(maximum)]:
			factor = 1.0
		while 0 < range <= 10:
			range = range * 10
			decimal = decimal + 1
			factor = factor * 10
		self._factor = factor
		return direction, int(minimum * factor + .5), \
		       int(initial * factor + .5), \
		       int(maximum * factor + .5), decimal, factor

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

class _WindowHelpers:
	def __init__(self):
		self._fixkids = []
		self._fixed = 0

	# items with which a window can be filled in
	def Label(self, text, position):
		return Label(self, text, position)
	def OptionMenu(self, label, optionlist, startpos, cb, position):
		return OptionMenu(self, label, optionlist, startpos, cb,
				  position)
	def PulldownMenu(self, menulist, position):
		return PulldownMenu(self, menulist, position)
	def Selection(self, listprompt, itemprompt, itemlist, sel_cb,
		      position):
		return Selection(self, listprompt, itemprompt, itemlist,
				 sel_cb, position)
	def List(self, listprompt, itemlist, sel_cb, position):
		return List(self, listprompt, itemlist, sel_cb, position)
	def TextInput(self, prompt, inittext, cb, position):
		return TextInput(self, prompt, inittext, cb, position)
	def TextEdit(self, inittext, cb, position):
		return TextEdit(self, inittext, cb, position)
	def Separator(self, position):
		return Separator(self, position)
	def ButtonRow(self, vertical, buttonlist, position):
		return ButtonRow(self, vertical, buttonlist, position)
	def Slider(self, prompt, vertical, minimum, initial, maximum, cb,
		   position):
		return Slider(self, prompt, vertical, minimum, initial,
			      maximum, cb, position)
	def SubWindow(self, position):
		return SubWindow(self, position)
	def AlternateSubWindow(self, position):
		return AlternateSubWindow(self, position)

class SubWindow(_Widget, _WindowHelpers):
	def __init__(self, parent, position):
		attrs = {'resizePolicy': Xmd.RESIZE_NONE}
		self._attachments(attrs, position)
		form = parent._form.CreateManagedWidget('windowSubwindow',
							Xm.Form, attrs)
		_WindowHelpers.__init__(self)
		_Widget.__init__(self, form)
		parent._fixkids.append(self)

	def fix(self):
		for w in self._fixkids:
			w.fix()
		if debug: print `self` + '.ManageChild()'
		self._form.ManageChild()
		self._fixed = 1

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
	def __init__(self, parent):
		self._parent = parent
		SubWindow.__init__(self, parent, {'left': None, 'right': None,
						  'top': None, 'bottom': None})

	def show(self):
		for w in self._parent._windows:
			w.hide()
		SubWindow.show(self)

class AlternateSubWindow(_Widget):
	def __init__(self, parent, position):
		attrs = {'resizePolicy': Xmd.RESIZE_NONE,
			 'allowOverlap': X.TRUE}
		self._attachments(attrs, position)
		form = parent._form.CreateManagedWidget(
			'windowAlternateSubwindow', Xm.Form, attrs)
		self._windows = []
		_Widget.__init__(self, form)
		parent._fixkids.append(self)
		self._fixkids = []

	def SubWindow(self):
		widget = _SubWindow(self)
		for w in self._windows:
			w.hide()
		self._windows.append(widget)
		return widget

	def fix(self):
		for w in self._fixkids:
			w.fix()
		for w in self._windows:
			w._form.ManageChild()

class Window(_WindowHelpers):
	def __init__(self, title):
		if not title:
			title = ''
		self._title = title
		self._shell = toplevel._main.CreatePopupShell('windowShell',
				Xt.ApplicationShell,
				{'title': title,
				 'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		self._form = self._shell.CreateManagedWidget('windowForm',
					Xm.Form,
					{'allowOverlap': 0,
					 'noResize': X.TRUE,
					 'resizable': X.FALSE,
					 'resizePolicy': Xmd.RESIZE_NONE})
		self._showing = 0
		_WindowHelpers.__init__(self)

	def __repr__(self):
		s = '<Window instance'
		if hasattr(self, '_title'):
			s = s + ', title=' + `self._title`
		if self.is_closed():
			s = s + ' (closed)'
		elif self._showing:
			s = s + ' (showing)'
		s = s + ', id=' + `id(self)` + '>'
		return s

	def __del__(self):
		self.close()

	def fix(self):
		for w in self._fixkids:
			w.fix()
		if debug: print `self` + '.RealizeWidget()'
		self._form.ManageChild()
		self._shell.RealizeWidget()
		self._fixed = 1

	def close(self):
		if hasattr(self, '_form'):
			self.hide()
			self._form.DestroyWidget()
			del self._form

	def is_closed(self):
		return not hasattr(self, '_form')

	def show(self):
		if not self._fixed:
			self.fix()
		self._shell.Popup(0)
		self._showing = 1
		for w in self._fixkids:
			if w.is_showing():
				w.show()
			else:
				w.hide()
		self._fixkids = []

	def hide(self):
		self._shell.Popdown()
		self._showing = 0

	def is_showing(self):
		return self._showing

	def settitle(self, title):
		if self._title != title:
			self._form.dialogTitle = title
			self._title = title

	def pop(self):
		pass

