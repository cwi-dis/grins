import Xlib, Xt, Xm, X, Xmd, XEvent, Xtdefs
from EVENTS import *
import time

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

_image_cache = {}			# cache of prepared images
_cache_full = 0				# 1 if we shouldn't cache more images
_image_size_cache = {}

have_cl = have_jpeg = 0
try:
	import cl, CL
	have_cl = 1
except ImportError:
	try:
		import jpeg
		have_jpeg = 1
	except ImportError:
		pass

try:
	import rgbimg
	dummy = rgbimg.ttob(1)
	del dummy
except ImportError:
	pass

class _Toplevel:
	def __init__(self):
		global _mscreenwidth
		global _mscreenheight
		global _screenwidth
		global _screenheight
		global _dpi_x
		global _dpi_y
		if debug: print '_TopLevel.__init__() --> '+`self`
		self._toplevel = self
		self._win_lock = None
		import sys
		self._main = Xt.Initialize('Windowinterface', [], sys.argv)
		self._main.SetValues({'mappedWhenManaged': X.FALSE,
			  'x': 500, 'y': 500, 'width': 1, 'height': 1,
			  'input': X.TRUE})
		_mscreenwidth = self._main.WidthMMOfScreen()
		_mscreenheight = self._main.HeightMMOfScreen()
		_screenwidth = self._main.WidthOfScreen()
		_screenheight = self._main.HeightOfScreen()
		_dpi_x = int(_screenwidth * 25.4 / _mscreenwidth + .5)
		_dpi_y = int(_screenheight * 25.4 / _mscreenheight + .5)
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
		window = _Window(1, self, x, y, w, h, title)
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
	def __init__(self, is_toplevel, parent, x, y, w, h, title):
		if debug: print '_Window.init() --> '+`self`
		self._parent_window = parent
		if not is_toplevel:
			return
		x = int(float(x)/_mscreenwidth*_screenwidth+0.5)
		y = int(float(y)/_mscreenheight*_screenheight+0.5)
		w = int(float(w)/_mscreenwidth*_screenwidth+0.5)
		h = int(float(h)/_mscreenheight*_screenheight+0.5)
		# XXX--somehow set the posiion
		geometry = '+%d+%d' % (x, y)
		if not title:
			title = ''
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		if debug: print 'CreatePopupShell, geometry:',geometry
		self._shell = parent._toplevel._main.CreatePopupShell(title,
			  Xt.ApplicationShell,
			  {'colormap': toplevel._colormap,
			   'geometry': geometry})
		if debug: print 'CreatePopupShell done'
		self._shell.SetValues({'width': w, 'height': h})
		self._form = self._shell.CreateManagedWidget('drawingArea',
			  Xm.DrawingArea,
			  {'height': h, 'width': w,
			   'colormap': toplevel._colormap,
			   'marginHeight': 0, 'marginWidth': 0})
		self._width = w
		self._height = h
		self._shell.Popup(0)
		if toplevel._win_lock:
			toplevel._win_lock.release()
		self._init2()

	def _init2(self):
		if debug: print `self`+'.init2()'
		self._bgcolor = self._parent_window._bgcolor
		self._fgcolor = self._parent_window._fgcolor
		self._xbgcolor = self._convert_color(self._bgcolor)
		self._xfgcolor = self._convert_color(self._fgcolor)
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
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
##		self._form.SetWindowColormap(toplevel._colormap)
		self._form.AddCallback('exposeCallback', self._expose_callback, None)
		self._form.AddCallback('resizeCallback', self._resize_callback, None)
		self._form.AddCallback('inputCallback', self._input_callback, None)
		if toplevel._win_lock:
			toplevel._win_lock.release()
		self._closecallbacks = []
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
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
		if toplevel._win_lock:
			toplevel._win_lock.release()
		# let our parent window inherit events meant for us
##		dummy = testevent()	# read all pending events
##		q = []
##		for (win, ev, val) in event._queue:
##			if win == self:
##				if parent in (None, toplevel):
##					# delete event if we have no parent:
##					continue
##				win = parent
##			q.append((win, ev, val))
##		event._queue = q

	def is_closed(self):
		return not hasattr(self, '_form')

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
			if toplevel._win_lock:
				toplevel._win_lock.acquire()
			string = Xlib.LookupString(ev)[0]
			if toplevel._win_lock:
				toplevel._win_lock.release()
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
			if toplevel._win_lock:
				toplevel._win_lock.acquire()
			self._gc.background = self._xbgcolor
			self._gc.foreground = self._xbgcolor
			self._gc.FillRectangle(0, 0, self._width, self._height)
			if toplevel._win_lock:
				toplevel._win_lock.release()

	def _do_resize(self):
		x, y, w, h = self._sizes
		x, y, w, h = self._parent_window._convert_coordinates(x, y, w, h)
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._form.SetValues({'width': w, 'height': h, 'x': x, 'y': y})
		if toplevel._win_lock:
			toplevel._win_lock.release()

	def _resize_callback(self, *rest):
		if debug: print `self`+'._resize_callback()'
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		val = self._form.GetValues(['width', 'height'])
		if toplevel._win_lock:
			toplevel._win_lock.release()
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
		newwin = _Window(0, self, 0, 0, 0, 0, 0)
		newwin._sizes = coordinates
		newwin._parent_window = self
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		newwin._form = self._form.CreateManagedWidget('drawingArea',
			  Xm.DrawingArea,
			  {'width': w, 'height': h, 'x': x, 'y': y,
			   'marginHeight': 0, 'marginWidth': 0})
		if toplevel._win_lock:
			toplevel._win_lock.release()
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
		if not self._active_display_list:
			if toplevel._win_lock:
				toplevel._win_lock.acquire()
			self._form.SetValues({'background': self._xbgcolor})
			if toplevel._win_lock:
				toplevel._win_lock.release()

	def setcursor(self, cursor):
		pass

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
		if self._parent_window != toplevel:
			raise error, 'can only settitle at top-level'
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._main.SetValues({'title': title})
		if toplevel._win_lock:
			toplevel._win_lock.release()

	def pop(self):
		self._parent_window.pop()
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._form.RaiseWindow()
		if toplevel._win_lock:
			toplevel._win_lock.release()

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
				import rgbimg
				image = rgbimg.longimagedata(filename)
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
				import rgbimg
				rgbimg.longstoimage(retval[10],
					  retval[6], retval[7], 3,
					  filename)
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
		import rgbimg, imageop
		xsize, ysize = rgbimg.sizeofimage(file)
		_image_size_cache[file] = (xsize, ysize)
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		width, height = self._width, self._height
		scale = min(float(width)/(xsize - left - right),
			    float(height)/(ysize - top - bottom))
		image = rgbimg.longimagedata(file)
		width, height = xsize, ysize
		image = imageop.rgb2rgb8(image, xsize, ysize)
		if scale != 1:
			width = int(xsize * scale)
			height = int(ysize * scale)
			image = imageop.scale(image, 1, xsize, ysize,
				  width, height)
			top = int(top * scale)
			bottom = int(bottom * scale)
			left = int(left * scale)
			right = int(right * scale)
			scale = 1.0
		x, y = (self._width-(width-left-right))/2, \
			  (self._height-(height-top-bottom))/2
		return x, y, width - left - right, height - top - bottom, \
			  left, bottom, width, height, 1, scale, \
			  image, 0

	def _prepare_JPEG_image_from_filep_with_cl(self, filep):
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
		return image, xsize, ysize, zsize

	def _prepare_JPEG_image_from_filep_with_jpeg(self, filep):
		return jpeg.decompress(filep.read())

	def _prepare_JPEG_image_from_filep(self, file, filep, top, bottom, left, right):
		if have_cl:
			image, xsize, ysize, zsize = self._prepare_JPEG_image_from_filep_with_cl(filep)
		elif have_jpeg:
			image, xsize, ysize, zsize = self._prepare_JPEG_image_from_filep_with_jpeg(filep)
		else:
			return None

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
			image = imageop.scale(image, zsize, xsize, ysize,
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
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
		if toplevel._win_lock:
			toplevel._win_lock.release()

	def close(self):
		if debug: print `self`+'.close()'
		if self.is_closed():
			return
		for but in self._buttonlist[:]:
			but.close()
		window = self._window
		window._displaylists.remove(self)
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		if window._active_display_list == self:
			window._active_display_list = None
			window._expose_callback(None, None, None)
		del self._window
		del self._buttonlist
		del self._gc
		del self._pixmap
		del self._font
		if toplevel._win_lock:
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._pixmap.CopyArea(w._form, None, 0, 0, w._width, w._height, 0, 0)
		if toplevel._win_lock:
			toplevel._win_lock.release()

	def clone(self):
		if debug: print `self`+'.clone()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		w = self._window
		new = _DisplayList(w)
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._pixmap.CopyArea(new._pixmap, None, 0, 0, w._width, w._height, 0, 0)
		# somehow copy GC too
		for name in self._gc.__members__:
			eval('new._gc.' + name + ' = self._gc.' + name)
		if toplevel._win_lock:
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._gc.foreground = self._xfgcolor
		if toplevel._win_lock:
			toplevel._win_lock.release()

	def linewidth(self, width):
		if debug: print `self`+'.linewidth()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._linewidth = width
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._gc.line_width = width
		if toplevel._win_lock:
			toplevel._win_lock.release()

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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._gc.DrawRectangle(x, y, w, h)
		if toplevel._win_lock:
			toplevel._win_lock.release()

	def usefont(self, fontobj):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		self._gc.SetFont(fontobj._font.fid)
		if toplevel._win_lock:
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		for str in strlist:
			x0, y0, w, h = \
				  self._window._convert_coordinates(x, y, 0, 0)
			self._gc.DrawString(x0, y0, str)
			self._curpos = x + float(self._font._font.TextWidth(str)) / window._width, y
			x = self._xpos
			y = y + self._fontheight
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		if toplevel._win_lock:
			toplevel._win_lock.release()
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		xim = toplevel._visual.CreateImage(8, X.ZPixmap, 0, image,
			  im_w, im_h, 8, 0)
		self._gc.PutImage(xim, im_x, im_y, win_x, win_y, win_w, win_h)
		if toplevel._win_lock:
			toplevel._win_lock.release()
		return float(win_x) / window._width, \
			  float(win_y) / window._height, \
			  float(win_w) / window._width, \
			  float(win_h) / window._height

	def drawline(self, color, points):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawline'+`points`

		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		color = self._window._convert_color(color)
		self._gc.foreground = color

		x0, y0 = points[0]
		x0, y0, h, w = window._convert_coordinates(x0, y0, 0, 0)
		for x, y in points[1:]:
			x, y, h, w = window._convert_coordinates(x, y, 0, 0)
			self._gc.DrawLine(x0, y0, x, y)
			x0, y0 = x, y
		self._gc.foreground = self._xfgcolor
		if toplevel._win_lock:
			toplevel._win_lock.release()

	def drawfbox(self, color, *coordinates):
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		color = self._window._convert_color()
		self._gc.foreground = color
		self._gc.FillRectangle(x, y, w, h)
		self._gc.foreground = self._xfgcolor
		if toplevel._win_lock:
			toplevel._win_lock.release()


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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		dispobj._gc.DrawRectangle(self._coordinates)
		if toplevel._win_lock:
			toplevel._win_lock.release()
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		window._gc.background = dispobj._xbgcolor
		window._gc.foreground = self._xhicolor
		window._gc.line_width = self._hiwidth
		window._gc.DrawRectangle(self._coordinates)
		if toplevel._win_lock:
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
		self._timeout_called = 1
##		Xlib.PutBackEvent(toplevel._main.Display(), '\0'*96)

	def _input_callback(self, client_data, fd, id):
		self.entereventunique(None, FileEvent, fd)
		Xt.RemoveInput(self._fdlist[fd])
		del self._fdlist[fd]
		self._savefds.append(fd)

	def _getevent(self, timeout):
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		for fd in self._savefds:
			self._fdlist[fd] = Xt.AddInput(fd,
				  Xtdefs.XtInputReadMask, self._input_callback,
				  None)
		self._savefds = []
		if timeout != None and timeout > 0.001:
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
				if toplevel._win_lock:
					toplevel._win_lock.release()
				event = Xt.ProcessEvent(Xtdefs.XtIMAll)
				if toplevel._win_lock:
					toplevel._win_lock.acquire()
				qtest = Xt.Pending()
			# if there were any for us, return
			if self._queue:
				if not self._timeout_called:
					Xt.RemoveTimeOut(id)
				if toplevel._win_lock:
					toplevel._win_lock.release()
				return 1
			# if we shouldn't block, return
			if timeout != None:
				if self._timeout_called:
					if toplevel._win_lock:
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
				return 0
		if event == FileEvent:
			if self._select_dict.has_key(value):
				del self._queue[0]
				func, arg = self._select_dict[value]
				apply(func, arg)
				return 1
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

	def remove_window_callbacks(self, window):
		# called when window closes
		for (w, e) in self._windows.keys():
			if w == window:
				self.unregister(w, e)

	def setcallback(self, event, func, arg):
		self.register(None, event, func, arg)

	def clean_callbacks(self):
		for (win, event) in self._windows.keys():
			if win and win.is_closed():
				self.register(win, event, None, None)

	def select_setcallback(self, fd, cb, arg):
		if cb == None:
			self._select_fdlist.remove(fd)
			del self._select_dict[fd]
			self.rmfd(fd)
			return
		if not self._select_dict.has_key(fd):
			self._select_fdlist.append(fd)
		self._select_dict[fd] = (cb, arg)
		self.setfd(fd)

	def startmodal(self):
		self._modal = 1

	def endmodal(self):
		self._modal = 0

	def mainloop(self):
		self._looping = 1
		t = 0
		for (time, arg, tid) in self._timers:
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
		if toplevel._win_lock:
			toplevel._win_lock.acquire()
		for str in strlist:
			width = self._font.TextWidth(str)
			if width > maxwidth:
				maxwidth = width
		if toplevel._win_lock:
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
	  }

toplevel = _Toplevel()
event = _Event()

def newwindow(x, y, w, h, title):
	return toplevel.newwindow(x, y, w, h, title)

def close():
	toplevel.close()

def setcursor(cursor):
	pass				# for now...

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

def clean_callbacks():
	event.clean_callbacks()

def select_setcallback(fd, cb, arg):
	event.select_setcallback(fd, cb, arg)

def startmodal():
	event.startmodal()

def endmodal():
	event.endmodal()

def mainloop():
	event.mainloop()

def canceltimer(id):
	event.canceltimer(id)

class _Dialogs:
	def __init__(self):
		self.answer = None

	def _callback(self):
		event.endmodal()
		event._checktime()
		event._queue.append((None, 0, None))
		dummy = Xt.AddTimeOut(0, event._timeout_callback, None)

	def _ok_callback(self, *args):
		self.answer = 1
		self._callback()

	def _cancel_callback(self, *args):
		self.answer = 0
		self._callback()

	def _after_create(self, text):
		self.dialog.SetValues({'messageString': text})
		Xm.MessageBoxGetChild(self.dialog, Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		self.dialog.AddCallback('okCallback', self._ok_callback, None)
		self.dialog.AddCallback('cancelCallback', self._cancel_callback, None)

	def _run(self):
		event.startmodal()
		self.dialog.ManageChild()
		while self.answer == None:
			dummy = event.readevent()
		return self.answer

	def showmessage(self, text):
		self.dialog = Xm.CreateErrorDialog(toplevel._main, 'popup', {})
		self._after_create(text)
		Xm.MessageBoxGetChild(self.dialog, Xmd.DIALOG_CANCEL_BUTTON).UnmanageChild()
		answer = self._run()

	def showquestion(self, text):
		self.dialog = Xm.CreateQuestionDialog(toplevel._main, 'popup', {})
		self._after_create(text)
		return self._run()
			
def showmessage(text):
	_Dialogs().showmessage(text)

def showquestion(text):
	return _Dialogs().showquestion(text)

class _MultChoice:
	def __init__(self, prompt, msg_list, defindex):
		self.answer = None
		self.form = Xm.CreateFormDialog(toplevel._main, 'popup',
			  {'allowOverlap': 0,
			   'dialogStyle': Xmd.DIALOG_PRIMARY_APPLICATION_MODAL})
		label = self.form.CreateManagedWidget('prompt', Xm.Label,
			  {'leftAttachment': Xmd.ATTACH_FORM,
			   'rightAttachment': Xmd.ATTACH_FORM,
			   'topAttachment': Xmd.ATTACH_FORM})
		label.labelString = prompt
		list = self.form.CreateManagedWidget('list', Xm.List,
			  {'leftAttachment': Xmd.ATTACH_FORM,
			   'rightAttachment': Xmd.ATTACH_FORM,
			   'topAttachment': Xmd.ATTACH_WIDGET,
			   'topWidget': label})
		list.SetValues({'selectionPolicy': Xmd.SINGLE_SELECT,
			  'visibleItemCount': len(msg_list)})
		for i in range(len(msg_list)):
			answer = list[i]
			if type(answer) == type(()):
				answer = answer[0]
			Xm.ListAddItem(list, answer, i+1)
		list.AddCallback('singleSelectionCallback',
			  self._sel_callback, msg_list)

	def multchoice(self):
		event.startmodal()
		self.form.ManageChild()
		while self.answer == None:
			dummy = event.readevent()
		return self.answer

	def _sel_callback(self, widget, msg_list, call_data):
		import struct
		fmt = 'illiiliii'
		size = struct.calcsize(fmt)
		reason, ev, xmitem, item_length, item_position, \
			  selected_items, selected_item_count, \
			  selected_item_positions, selection_type = \
			  struct.unpack(fmt, call_data[:size])
		self.answer = item_position - 1
		self.form.UnmanageChild()
		event.endmodal()
		event._checktime()
		event._queue.append((None, 0, None))
		dummy = Xt.AddTimeOut(0, event._timeout_callback, None)

def multchoice(prompt, list, defindex):
	return _MultChoice(prompt, list, defindex).multchoice()
