import Xlib, Xt, Xm, X, Xmd, XEvent, Xtdefs
from EVENTS import *

error = 'windowinterface.error'

# Colors
_DEF_BGCOLOR = 255,255,255		# white
_DEF_FGCOLOR =   0,  0,  0		# black

#from debug import debug
debug = 0

_mscreenwidth = 293
_mscreenheight = 234
_screenwidth = 1280
_screenheight = 1024
_dpi_x = 111
_dpi_y = 111

import imgfile
try:
	dummy = imgfile.ttob(1)
	del dummy
except AttributeError:
	pass

_image_cache = {}			# cache of prepared images
_cache_full = 0				# 1 if we shouldn't cache more images
_image_size_cache = {}

class _Toplevel:
	def __init__(self):
		if debug: print '_TopLevel.__init__() --> '+`self`
		self._toplevel = self
		self._win_lock = None
		import sys
		self._main = Xt.Initialize('Windowinterface', [], sys.argv)
		self._main.SetValues({'mappedWhenManaged': X.FALSE,
			  'x': 500, 'y': 500, 'width': 1, 'height': 1,
			  'input': X.TRUE})
		self._parent_window = None
		self._subwindows = []
		self._fgcolor = _DEF_FGCOLOR
		self._bgcolor = _DEF_BGCOLOR
		self._cursor = ''
		visuals = self._main.GetVisualInfo({'depth': 8,
			  'c_class': X.PseudoColor})
		if len(visuals) == 0:
			raise error, 'no proper visuals available'
		self._visual = visuals[0]
		self._colormap = self._main.CreateColormap(self._visual,
			  X.AllocNone)
		(plane_masks, pixels) = self._colormap.AllocColorCells(1, 8, 1)
		xcolors = []
		for n in range(256):
			# The colormap is set up so that the colormap
			# index has the meaning: rrrbbggg.
			xcolors.append((n+pixels[0],
				  int((float((n >> 5) & 7) / 7.) * 255.)<<8,
				  int((float(n & 7) / 7.) * 255.)<<8,
				  int((float((n >> 3) & 3) / 3.) * 255.)<<8,
				  X.DoRed|X.DoGreen|X.DoBlue))
		self._colormap.StoreColors(xcolors)
		self._main.RealizeWidget()
##		self._main.SetWindowColormap(self._colormap)

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
		window = _Window().init(self, x, y, w, h, title)
		window._parent_window = self
		return window

	def pop(self):
		pass

	def getsize(self):
		return _mscreenwidth, _mscreenheight

	def getmouse(self):
		return 0, 0

	def usewindowlock(self, lock):
		if debug: print 'Toplevel.usewindowlock()'
		self._win_lock = lock

class _Window:
	def init(self, parent, x, y, w, h, title):
		if debug: print '_Window.init() --> '+`self`
		self._parent_window = parent
		x = int(float(x)/_mscreenwidth*_screenwidth+0.5)
		y = int(float(y)/_mscreenheight*_screenheight+0.5)
		w = int(float(w)/_mscreenwidth*_screenwidth+0.5)
		h = int(float(h)/_mscreenheight*_screenheight+0.5)
		# XXX--somehow set the posiion
		geometry = '+%d+%d' % (x, y)
		if not title:
			title = ''
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		if debug: print 'CreatePopupShell, geometry:',geometry
		self._shell = parent._toplevel._main.CreatePopupShell(title,
			  Xt.ApplicationShell,
			  {'colormap': _toplevel._colormap,
			   'geometry': geometry})
		if debug: print 'CreatePopupShell done'
		self._shell.SetValues({'width': w, 'height': h})
		self._form = self._shell.CreateManagedWidget('drawingArea',
			  Xm.DrawingArea,
			  {'height': h, 'width': w,
			   'colormap': _toplevel._colormap})
		self._width = w
		self._height = h
		self._shell.Popup(0)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		return self._init2()

	def _init2(self):
		if debug: print `self`+'.init2()'
		self._bgcolor = self._parent_window._bgcolor
		self._fgcolor = self._parent_window._fgcolor
		self._xbgcolor = self._convert_color(self._bgcolor)
		self._xfgcolor = self._convert_color(self._fgcolor)
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._form.SetValues({'background': self._xbgcolor,
			  'foreground': self._xfgcolor,
			  'borderWidth': 0,
			  'marginWidth': 0,
			  'marginHeight': 0,
			  'marginTop': 0,
			  'marginBottom': 0,
			  'shadowThickness': 0})
		val = self._form.GetValues(['width', 'height'])
		self._width = val['width']
		self._height = val['height']
		self._subwindows = []
		self._displaylists = []
		self._active_display_list = None
		self._redraw_func = None
		self._parent_window._subwindows.append(self)
		self._toplevel = self._parent_window._toplevel
		self._gc = self._form.CreateGC({})
		self._form.RealizeWidget()
##		self._form.SetWindowColormap(_toplevel._colormap)
		self._form.AddCallback('exposeCallback', self._expose_callback, None)
		self._form.AddCallback('resizeCallback', self._resize_callback, None)
		self._form.AddCallback('inputCallback', self._input_callback, None)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		self._closecallbacks = []
		return self

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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._form.DestroyWidget()
		del self._form
		parent = self._parent_window
		if parent == _toplevel:
			self._shell.DestroyWidget()
			del self._shell
		parent._subwindows.remove(self)
		del self._parent_window
		del self._toplevel
		del self._gc
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		# let our parent window inherit events meant for us
##		dummy = testevent()	# read all pending events
##		q = []
##		for (win, ev, val) in _event._queue:
##			if win == self:
##				if parent in (None, _toplevel):
##					# delete event if we have no parent:
##					continue
##				win = parent
##			q.append((win, ev, val))
##		_event._queue = q

	def is_closed(self):
		return not hasattr(self, '_form')

	def _call_on_close(self, func):
		if not func in self._closecallbacks:
			self._closecallbacks.append(func)

	def _input_callback(self, widget, client_data, call_data, *rest):
		if debug: print `self`+'._input_callback()'
		import struct
		event = struct.unpack('i', call_data[4:8])[0]
		event = Xlib.getevent(event)	# KLUDGE!
		decoded_event = XEvent.mkevent(event)
		if decoded_event.type == X.KeyPress:
			if _toplevel._win_lock:
				_toplevel._win_lock.acquire()
			string = Xlib.LookupString(event)[0]
			if _toplevel._win_lock:
				_toplevel._win_lock.release()
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
					ev = Mouse2Press
				else:
					return	# unsupported mouse button
			else:
				if decoded_event.button == X.Button1:
					ev = Mouse0Release
				elif decoded_event.button == X.Button2:
					ev = Mouse1Release
				elif decoded_event.button == X.Button3:
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
		if call_data:
			import struct
			event = struct.unpack('i', call_data[4:8])[0]
			event = Xlib.getevent(event)
			decoded_event = XEvent.mkevent(event)
			if decoded_event.count > 0:
				if debug: print `self`+'._expose_callback() -- count > 0'
				return
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
			if _toplevel._win_lock:
				_toplevel._win_lock.acquire()
			self._gc.background = self._xbgcolor
			self._gc.foreground = self._xbgcolor
			self._gc.FillRectangle(0, 0, self._width, self._height)
			if _toplevel._win_lock:
				_toplevel._win_lock.release()

	def _do_resize(self):
		x, y, w, h = self._sizes
		x, y, w, h = self._parent_window._convert_coordinates(x, y, w, h)
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._form.SetValues({'width': w, 'height': h, 'x': x, 'y': y})
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def _resize_callback(self, *rest):
		if debug: print `self`+'._resize_callback()'
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		val = self._form.GetValues(['width', 'height'])
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		self._width = val['width']
		self._height = val['height']
		for displist in self._displaylists[:]:
			displist.close()
		for win in self._subwindows:
			win._do_resize()
		enterevent(self, ResizeWindow, None)

	def newwindow(self, *coordinates):
		if debug: print `self`+'.newwindow'+`coordinates`
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		x, y, w, h = self._convert_coordinates(x, y, w, h)
		newwin = _Window()
		newwin._sizes = coordinates
		newwin._parent_window = self
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		newwin._form = self._form.CreateManagedWidget('drawingArea',
			  Xm.DrawingArea,
			  {'width': w, 'height': h, 'x': x, 'y': y})
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		return newwin._init2()

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
		if not self._active_display_list:
			if _toplevel._win_lock:
				_toplevel._win_lock.acquire()
			self._form.SetValues({'background': self._xbgcolor})
			if _toplevel._win_lock:
				_toplevel._win_lock.release()

	def newdisplaylist(self, *bgcolor):
		list = _DisplayList(self)
		if len(bgcolor) == 1 and type(bgcolor[0]) == type(()):
			bgcolor = bgcolor[0]
		if len(bgcolor) == 3:
			list._bgcolor = list._curcolor = bgcolor
		elif len(bgcolor) != 0:
			raise TypeError, 'arg count mismatch'
		return list

	def settitle(self, title):
		if self._parent_window != _toplevel:
			raise error, 'can only settitle at top-level'
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._main.SetValues({'title': title})
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def pop(self):
		self._parent_window.pop()
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._form.RaiseWindow()
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def getgeometry(self):
		pass

	def setredrawfunc(self, func):
		if func:
			self._redraw_func = func
		else:
			self._redraw_func = None

	def _convert_color(self, color):
		r, g, b = color
		r = int(float(r) / 255. * 7. + .5)
		g = int(float(g) / 255. * 7. + .5)
		b = int(float(b) / 255. * 3. + .5)
		return (r << 5) | (g) | (b << 3)
##		name = '#%02x%02x%02x' % color
##		return self._form.Convert(name, 'Pixel')

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
				import imgfile
				image = imgfile.read(filename)
				return retval[:-1] + (image,)
			except:		# any error...
				del _image_cache[cachekey]
				import posix
				try:
					posix.unlink(filename)
				except posix.error:
					pass
		f = open(file, 'r')
		magic = f.read(4)
		retval = None
		if magic[:2] == '\001\332':
			f.close()
			f = None
			retval = self._prepare_RGB_image_from_file(file,
				  top, bottom, left, right)
		elif magic == '\377\330\377\340':
			f.seek(0)
			retval = self._prepare_JPEG_image_from_filep(file, f,
				  top, bottom, left, right)
			f.close()
			f = None
		if retval == None:
			if f:
				f.close()
			import torgb
			try:
				f = torgb.torgb(file)
			except torgb.error, msg:
				raise error, msg
			retval = self._prepare_RGB_image_from_file(f,
				  top, bottom, left, right)
			retval = retval[:-1] + (1,)
			if f != file:
				import os
				os.unlink(f)
		if not _cache_full and retval[-1]:
			import tempfile
			filename = tempfile.mktemp()
			try:
				import imgfile
				imgfile.write(filename, retval[10],
					  retval[6], retval[7], retval[8])
			except:		# any error...
				print 'Warning: caching image failed'
				import posix
				try:
					posix.unlink(filename)
				except posix.error:
					pass
				_cache_full = 1
				return retval[:-1]
			_image_cache[cachekey] = retval[:-2] + (filename,)
		return retval[:-1]

	def _prepare_RGB_image_from_file(self, file, top, bottom, left, right):
		import imgfile
		xsize, ysize, zsize = imgfile.getsizes(file)
		_image_size_cache[file] = (xsize, ysize)
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		width, height = self._width, self._height
		scale = min(float(width)/(xsize - left - right),
			    float(height)/(ysize - top - bottom))
		if scale == 1:
			image = imgfile.read(file)
			width, height = xsize, ysize
		else:
			width = int(xsize * scale)
			height = int(ysize * scale)
			image = imgfile.readscaled(file, width, height, 'box')
			top = int(top * scale)
			bottom = int(bottom * scale)
			left = int(left * scale)
			right = int(right * scale)
			scale = 1.0
		if zsize == 3:
			import imageop
			image = imageop.rgb2rgb8(image, width, height)
			zsize = 1
		x, y = (self._width-(width-left-right))/2, \
			  (self._height-(height-top-bottom))/2
		if xsize * ysize < width * height:
			do_cache = 0
		else:
			do_cache = 1
		return x, y, width - left - right, height - top - bottom, \
			  left, bottom, width, height, zsize, scale, \
			  image, do_cache

	def _prepare_JPEG_image_from_filep(self, file, filep, top, bottom, left, right):
		try:
			import cl, CL
		except ImportError:
			return None
		header = filep.read(16)
		filep.seek(0)
		scheme = cl.QueryScheme(header)
		decomp = cl.OpenDecompressor(scheme)
		header = filep.read(cl.QueryMaxHeaderSize(scheme))
		filep.seek(0)
		headersize = decomp.ReadHeader(header)
		xsize = decomp.GetParam(CL.IMAGE_WIDTH)
		ysize = decomp.GetParam(CL.IMAGE_HEIGHT)
		_image_size_cache[file] = (xsize, ysize)
		original_format = CL.RGB332
		zsize = 1
		params = [CL.ORIGINAL_FORMAT, original_format,
			  CL.ORIENTATION, CL.TOP_DOWN,
			  CL.FRAME_BUFFER_SIZE,
				 xsize*ysize*CL.BytesPerPixel(original_format)]
		decomp.SetParams(params)
		image = decomp.Decompress(1, filep.read())
		decomp.CloseDecompressor()

		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		width, height = self._width, self._height
		scale = min(float(width)/(xsize - left - right),
			  float(height)/(ysize - top - bottom))
		if scale != 1:
			import imageop
			width = int(xsize * scale)
			height = int(ysize * scale)
			image = imageop.scale(image, zsize, xsize, ysize, \
					      width, height)
			top = int(top * scale)
			bottom = int(bottom * scale)
			left = int(left * scale)
			right = int(right * scale)
			scale = 1.0
		else:
			width, height = xsize, ysize
		# here width and height are the width and height in
		# pixels of the scaled image, top, bottom, left, right
		# are the amount to crop off the image in pixels.
		x, y = (self._width-(width-left-right))/2, \
			  (self._height-(height-top-bottom))/2
		return x, y, width - left - right, height - top - bottom, \
			  left, bottom, width, height, zsize, scale, image, 1

	def _image_size(self, file):
		# XXX--assume that images was displayed at least once
		return _image_size_cache[file]

class _DisplayList:
	def __init__(self, window):
		if debug: print '_DisplayList.init('+`window`+') --> '+`self`
		self._window = window
		self._rendered = 0
		# color support
		self._bgcolor = window._bgcolor
		self._fgcolor = window._fgcolor
		self._xbgcolor = window._xbgcolor
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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._pixmap = window._form.CreatePixmap(window._width,
			  window._height)
		# reversed foreground and background for clearing
		self._gc = self._pixmap.CreateGC({
			  'background': self._xfgcolor,
			  'foreground': self._xbgcolor,
			  'line_width': 1})
		# clear pixmap since it may contain garbage
		self._gc.FillRectangle(0, 0, window._width, window._height)
		# set foreground and background properly
		self._gc.background = self._xbgcolor
		self._gc.foreground = self._xfgcolor
		self._gc.line_width = self._linewidth
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def close(self):
		if debug: print `self`+'.close()'
		if self.is_closed():
			return
		for but in self._buttonlist[:]:
			but.close()
		window = self._window
		window._displaylists.remove(self)
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		if window._active_display_list == self:
			window._active_display_list = None
			window._expose_callback(None, None, None)
		del self._window
		del self._buttonlist
		del self._gc
		del self._pixmap
		del self._font
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._pixmap.CopyArea(w._form, None, 0, 0, w._width, w._height, 0, 0)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def clone(self):
		if debug: print `self`+'.clone()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		w = self._window
		new = _DisplayList(w)
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._pixmap.CopyArea(new._pixmap, None, 0, 0, w._width, w._height, 0, 0)
		# somehow copy GC too
		for name in self._gc.__members__:
			eval('new._gc.' + name + ' = self._gc.' + name)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._gc.foreground = self._xfgcolor
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def linewidth(self, width):
		if debug: print `self`+'.linewidth()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._linewidth = width
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._gc.line_width = width
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

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

	def drawbox(self, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
		x, y, w, h = coordinates
		x, y, w, h = window._convert_coordinates(x, y, w, h)
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._gc.DrawRectangle(x, y, w, h)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def usefont(self, fontobj):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		self._gc.SetFont(fontobj._font.fid)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		for str in strlist:
			x0, y0, w, h = \
				  self._window._convert_coordinates(x, y, 0, 0)
			self._gc.DrawString(x0, y0, str)
			self._curpos = x + float(self._font._font.TextWidth(str)) / window._width, y
			x = self._xpos
			y = y + self._fontheight
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		newx, newy = self._curpos
		if debug: print `self`+'.writestr('+`str`+') --> '+`oldx,oldy,maxx-oldx,newy-oldy+self._fontheight-self._baseline`
		return oldx, oldy, maxx - oldx, \
			  newy - oldy + self._fontheight - self._baseline

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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		xim = _toplevel._visual.CreateImage(8, X.ZPixmap, 0, image,
			  im_w, im_h, 8, 0)
		self._gc.PutImage(xim, im_x, im_y, win_x, win_y, win_w, win_h)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		return float(win_x) / window._width, \
			  float(win_y) / window._height, \
			  float(win_w) / window._width, \
			  float(win_h) / window._height

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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		dispobj._gc.DrawRectangle(self._coordinates)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		dispobj._buttonlist.append(self)

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
		if window._active_display_list != dispobj:
			raise error, 'can only highlight rendered button'
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		window._gc.background = dispobj._xbgcolor
		window._gc.foreground = self._xhicolor
		window._gc.line_width = self._hiwidth
		window._gc.DrawRectangle(self._coordinates)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
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

	def _getevent(self, timeout):
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		for fd in self._savefds:
			self._fdlist[fd] = Xt.AddInput(fd,
				  Xtdefs.XtInputReadMask, self._input_callback,
				  None)
		self._savefds = []
		if timeout != None and timeout > 0.001:
			if debug: print '_getevent: timeout:',`timeout`
			self._timeout_called = 0
			id = Xt.AddTimeOut(int
(timeout * 1000),
				  self._timeout_callback, None)
		else:
			if debug: print '_getevent: no timeout'
			self._timeout_called = 1
		qtest = Xt.Pending()
		while 1:
			# get all pending events
			while qtest:
				if _toplevel._win_lock:
					_toplevel._win_lock.release()
				event = Xt.ProcessEvent(Xtdefs.XtIMAll)
				if _toplevel._win_lock:
					_toplevel._win_lock.acquire()
				qtest = Xt.Pending()
			# if there were any for us, return
			if self._queue:
				if not self._timeout_called:
					Xt.RemoveTimeOut(id)
				if _toplevel._win_lock:
					_toplevel._win_lock.release()
				return 1
			# if we shouldn't block, return
			if timeout != None:
				if self._timeout_called:
					if _toplevel._win_lock:
						_toplevel._win_lock.release()
					return 0
			# block on next iteration
			qtest = 1

	def _timeout_callback(self, client_data, id):
		self._timeout_called = 1
##		Xlib.PutBackEvent(_toplevel._main.Display(), '\0'*96)

	def enterevent(self, win, event, arg):
		self._queue.append((win, event, arg))

	def entereventunique(self, win, event, arg):
		if (win, event, arg) not in self._queue:
			self._queue.append((win, event, arg))

	def readevent(self):
		return self.readevent_timeout(None)

	def readevent_timeout(self, timeout):
		if self._getevent(timeout):
			event = self._queue[0]
			del self._queue[0]
			return event
		else:
			return None

	def testevent(self):
		return self._getevent(0)

	def pollevent(self):
		if self.testevent():
			return self.readevent()
		else:
			return None

	def peekevent(self):
		if self.testevent():
			return self._queue[0]
		else:
			return None

	def waitevent(self):
		self.waitevent_timeout(None)

	def waitevent_timeout(self, timeout):
		dummy = self._getevent(timeout)

	def _input_callback(self, client_data, fd, id):
		self.entereventunique(None, FileEvent, fd)
		Xt.RemoveInput(self._fdlist[fd])
		del self._fdlist[fd]
		self._savefds.append(fd)

	def setfd(self, fd):
		self._fdlist[fd] = Xt.AddInput(fd, Xtdefs.XtInputReadMask,
			  self._input_callback, None)

	def rmfd(self, fd):
		if self._fdlist.has_key(fd):
			id = self._fdlist[fd]
			Xt.RemoveInput(id)
			del self._fdlist[fd]
		if fd in self._savefds:
			self._savefds.remove(fd)

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
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		for str in strlist:
			width = self._font.TextWidth(str)
			if width > maxwidth:
				maxwidth = width
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
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
_WIGHT = 3
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
	fontlist = _toplevel._main.ListFonts(fontname)
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
	return thefont, psize, _toplevel._main.LoadQueryFont(thefont)

_fontmap = {
	  'Times-Roman':	'-*-times-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Times-Italic':	'-*-times-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Times-Bold':		'-*-times-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Utopia-Bold':	'-*-utopia-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Palatino-Bold':	'-*-palatino-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  }

_toplevel = _Toplevel()
_event = _Event()

def newwindow(x, y, w, h, title):
	return _toplevel.newwindow(x, y, w, h, title)

def close():
	_toplevel.close()

def setcursor(cursor):
	pass				# for now...

def getsize():
	return _toplevel.getsize()

def readevent():
	return _event.readevent()

def readevent_timeout(timeout):
	return _event.readevent_timeout(timeout)

def pollevent():
	return _event.pollevent()

def waitevent():
	_event.waitevent()

def waitevent_timeout(timeout):
	_event.waitevent_timeout(timeout)

def peekevent():
	return _event.peekevent()

def testevent():
	return _event.testevent()

def enterevent(win, event, arg):
	_event.enterevent(win, event, arg)

def setfd(fd):
	_event.setfd(fd)

def rmfd(fd):
	_event.rmfd(fd)

def getfd():
	return -1

def findfont(fontname, pointsize):
	return _Font(fontname, pointsize)

def beep():
	pass				# for now...

def usewindowlock(lock):
	_toplevel.usewindowlock(lock)

def getmouse():
	return _toplevel.getmouse()

def startmonitormode():
	pass

def endmonitormode():
	pass
