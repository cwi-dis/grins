import Xt, Xm, Xmd, Xlib, X, Xcursorfont
import string, sys
import imgformat, img

error = 'windowinterface.error'
FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2

Version = 'X'

toplevel = None

from types import *
from WMEVENTS import *
r = Xlib.CreateRegion()
RegionType = type(r)
del r

[_X, _Y, _WIDTH, _HEIGHT] = range(4)

# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel:
	# this is a hack to delay initialization of the Toplevel until
	# we actually need it.
	def __getattr__(self, attr):
		if not self._initialized: # had better exist...
			self._do_init()
			try:
				return self.__dict__[attr]
			except KeyError:
				pass
		raise AttributeError, attr
	def __init__(self):
		self._initialized = 0
		global toplevel
		if toplevel:
			raise error, 'only one Toplevel allowed'
		toplevel = self

	def _do_init(self):
		if self._initialized:
			raise error, 'can only initialize once'
		self._initialized = 1
		self._closecallbacks = []
		self._subwindows = []
		self._bgcolor = 255, 255, 255 # white
		self._fgcolor =   0,   0,   0 # black
		self._hfactor = self._vfactor = 1.0
		self._cursor = ''
		self._image_size_cache = {}
		self._image_cache = {}
		self._cm_cache = {}
		self._immediate = []
		# file descriptor handling
		self._fdiddict = {}
		# window system initialization
		Xt.ToolkitInitialize()
		dpy = Xt.OpenDisplay(None, None, 'Windowinterface', [],
				     sys.argv)
		self._delete_window = dpy.InternAtom('WM_DELETE_WINDOW', FALSE)
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
		self._default_colormap = self._main.DefaultColormapOfScreen()
		self._default_visual = self._main.DefaultVisualOfScreen()
## 		self._default_colormap = self._colormap
## 		self._default_visual = self._visual
		self._mscreenwidth = self._main.WidthMMOfScreen()
		self._mscreenheight = self._main.HeightMMOfScreen()
		self._screenwidth = self._main.WidthOfScreen()
		self._screenheight = self._main.HeightOfScreen()
		self._hmm2pxl = float(self._screenwidth) / self._mscreenwidth
		self._vmm2pxl = float(self._screenheight) / self._mscreenheight
		self._dpi_x = int(25.4 * self._hmm2pxl + .5)
		self._dpi_y = int(25.4 * self._vmm2pxl + .5)
		self._watchcursor = dpy.CreateFontCursor(Xcursorfont.watch)
		self._channelcursor = dpy.CreateFontCursor(Xcursorfont.draped_box)
		self._linkcursor = dpy.CreateFontCursor(Xcursorfont.hand1)
		self._stopcursor = dpy.CreateFontCursor(Xcursorfont.pirate)
		self._main.RealizeWidget()

	def close(self):
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		self._closecallbacks = []
		self._subwindows = []
		import os
		for entry in self._image_cache.values():
			try:
				os.unlink(entry[0])
			except:
				pass
		self._image_cache = {}

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	def newwindow(self, x, y, w, h, title, pixmap = 0):
		return _Window(self, x, y, w, h, title, 0, pixmap)

	def newcmwindow(self, x, y, w, h, title, pixmap = 0):
		return _Window(self, x, y, w, h, title, 1, pixmap)

	def setcursor(self, cursor):
		for win in self._subwindows:
			win.setcursor(cursor)
		self._cursor = cursor
		self._main.Display().Flush()

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
		# sanity check
		func, args = cb
		if not callable(func):
			raise error, 'callback function not callable'
		id = Xt.AddTimeOut(int(sec * 1000), self._timer_callback, cb)
## 		if sec <= 0.001:
## 			self._immediate.append(id, cb)
		return id

	def canceltimer(self, id):
		if id is not None:
			Xt.RemoveTimeOut(id)
## 			for i in range(len(self._immediate)):
## 				if self._immediate[i][0] == id:
## 					del self._immediate[i]
## 					break

	def _timer_callback(self, client_data, id):
		func, args = client_data
## 		try:
## 			self._immediate.remove(id, client_data)
## 		except ValueError:
## 			pass
		apply(func, args)
## 		while self._immediate:
## 			id, (func, args) = self._immediate[0]
## 			del self._immediate[0]
## 			Xt.RemoveTimeOut(id)
## 			apply(func, args)

	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		import Xtdefs
		if type(fd) is not IntType:
			fd = fd.fileno()
		try:
			id = self._fdiddict[fd]
		except KeyError:
			pass
		else:
			Xt.RemoveInput(id)
			del self._fdiddict[fd]
		if func is None:
			return
		xmask = 0
		if mask & ReadMask:
			xmask = xmask | Xtdefs.XtInputReadMask
		if mask & WriteMask:
			xmask = xmask | Xtdefs.XtInputWriteMask
		self._fdiddict[fd] = Xt.AddInput(fd, xmask,
						 self._input_callback,
						 (func, args))

	def _input_callback(self, client_data, fd, id):
		func, args = client_data
		apply(func, args)

	# utility functions
	def _setupcolormap(self, dpy):
		# This method initializes the color system.  It
		# creates the attributes _visual, _depth, _colormap,
		# and for each of the color components red, green, and
		# blue: _color_shift and _color_mask.
		visattr = {'class': X.TrueColor}
## 		visattr['depth'] = 8	# DEBUG--force 8-bit visual
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
				self._setupimg()
##			print 'Using TrueColor visual of depth',self._depth
			return
		# no TrueColor visuals available, use a PseudoColor visual
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
			xcolors.append(
				(n+pixels[0],
				 int(float((n >> self._red_shift) & self._red_mask) / self._red_mask * 65535. + .5),
				 int(float((n >> self._green_shift) & self._green_mask) / self._green_mask * 65535. + .5),
				 int(float((n >> self._blue_shift) & self._blue_mask) / self._blue_mask * 65535. + .5),
				  X.DoRed|X.DoGreen|X.DoBlue))
		self._colormap.StoreColors(xcolors)
		self._setupimg()
##		print 'Using PseudoColor visual of depth',self._depth

	def _setupimg(self):
		import imgcolormap, imgconvert
		imgconvert.setquality(0)
		rs, rm = self._red_shift, self._red_mask
		gs, gm = self._green_shift, self._green_mask
		bs, bm = self._blue_shift, self._blue_mask
		r, g, b = imgformat.xrgb8.descr['comp'][:3]
		xrs, xrm = r[0], (1 << r[1]) - 1
		xgs, xgm = g[0], (1 << g[1]) - 1
		xbs, xbm = b[0], (1 << b[1]) - 1
		c = []
		if (rm, gm, bm) != (xrm, xgm, xbm):
			# too many locals to use map()
			for n in range(256):
				r = roundi(((n>>xrs) & xrm) / float(xrm) * rm)
				g = roundi(((n>>xgs) & xgm) / float(xgm) * gm)
				b = roundi(((n>>xbs) & xbm) / float(xbm) * bm)
				c.append((r << rs) | (g << gs) | (b << bs))
			lossy = 2
		elif (rs, gs, bs) == (xrs, xgs, xbs):
			# no need for extra conversion
			self.myxrgb8 = imgformat.xrgb8
			return
		else:
			# too many locals to use map()
			for n in range(256):
				r = (n >> xrs) & xrm
				g = (n >> xgs) & xgm
				b = (n >> xbs) & xbm
				c.append((r << rs) | (g << gs) | (b << bs))
			lossy = 0
		self.myxrgb8 = imgformat.new('myxrgb8',
					'X 3:3:2 RGB top-to-bottom',
					{'type':'rgb', 'b2t':0, 'size':8,
					 'align':8,
					 # the 3,3,2 below are not
					 # necessarily correct, but they
					 # are not used anyway
					 'comp':((rs,3),(gs,3),(bs,2))})
		cmap = imgcolormap.new(reduce(lambda x, y: x + '000' + chr(y),
					      c, ''))
		imgconvert.addconverter(imgformat.xrgb8, imgformat.myxrgb8,
				lambda d, r, src, dst, m=cmap: m.map8(d),
				lossy)

	def _convert_color(self, color, defcm):
		r, g, b = color
		if defcm:
			if self._cm_cache.has_key(`r,g,b`):
				return self._cm_cache[`r,g,b`]
			ri = int(r / 255.0 * 65535.0)
			gi = int(g / 255.0 * 65535.0)
			bi = int(b / 255.0 * 65535.0)
			cm = self._default_colormap
			try:
				color = cm.AllocColor(ri, gi, bi)
			except RuntimeError:
				# can't allocate color; find closest one
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
			self._cm_cache[`r,g,b`] = color[0]
			return color[0]
		r = int(float(r) / 255. * float(self._red_mask) + .5)
		g = int(float(g) / 255. * float(self._green_mask) + .5)
		b = int(float(b) / 255. * float(self._blue_mask) + .5)
		c = (r << self._red_shift) | \
		    (g << self._green_shift) | \
		    (b << self._blue_shift)
		return c

class _Window:
	# Instances of this clas represent top-level windows.  This
	# class is also used as base class for subwindows, but then
	# some of the methods are overridden.
	#
	# The following instance variables are used.  Unless otherwise
	# noted, the variables are used both in top-level windows and
	# subwindows.
	# _shell: the Xt.ApplicationShell widget used for the window
	#	(top-level windows only)
	# _form: the Xm.DrawingArea widget used for the window
	# _colormap: the colormap used by the window (top-level
	#	windows only)
	# _visuel: the visual used by the window (top-level windows
	#	only)
	# _depth: the depth of the window in pixels (top-level windows
	#	only)
	# _pixmap: if present, the backing store pixmap for the window
	# _gc: the graphics context with which the window (or pixmap)
	#	is drawn
	# _title: the title of the window (top-level window only)
	# _topwindow: the top-level window
	# _subwindows: a list of subwindows.  This list is also the
	#	stacking order of the subwindows (top-most first).
	#	This list is manipulated by the subwindow.
	# _parent: the parent window (for top-level windows, this
	#	refers to the instance of _Toplevel).
	# _displists: a list of _DisplayList instances
	# _active_displist: the currently rendered _displayList
	#	instance or None
	# _bgcolor: background color of the window
	# _fgcolor: foreground color of the window
	# _transparent: 1 if window has a transparent background (if a
	#	window is transparent, all its subwindows should also
	#	be transparent)
	# _sizes: the position and size of the window in fractions of
	#	the parent window (subwindows only)
	# _rect: the position and size of the window in pixels
	# _region: _rect as an X Region
	# _clip: an X Region representing the visible area of the
	#	window
	# _hfactor: horizontal multiplication factor to convert pixels
	#	to relative sizes
	# _vfactor: vertical multipliction factor to convert pixels to
	#	relative sizes
	# _cursor: the desired cursor shape (only has effect for
	#	top-level windows)
	# _callbacks: a dictionary with callback functions and
	#	arguments
	# _accelerators: a dictionary of accelarators
	# _menu: the pop-up menu for the window
	# _showing: 1 if a box is shown to indicate the size of the
	#	window
	# _exp_reg: a region in which the exposed area is built up
	#	(top-level window only)
	def __init__(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0):
		self._title = title
		self._do_init(parent)
		self._topwindow = self
		self._exp_reg = Xlib.CreateRegion()

		if parent._visual.c_class == X.TrueColor:
			defcmap = FALSE
		if defcmap:
			self._colormap = parent._default_colormap
			self._visual = parent._default_visual
		else:
			self._colormap = parent._colormap
			self._visual = parent._visual
		self._depth = self._visual.depth
		# convert mm to pixels
		x = int(float(x) * toplevel._hmm2pxl + 0.5)
		y = int(float(y) * toplevel._vmm2pxl + 0.5)
		w = int(float(w) * toplevel._hmm2pxl + 0.5)
		h = int(float(h) * toplevel._vmm2pxl + 0.5)
		# XXX--somehow set the posiion
		geometry = '+%d+%d' % (x, y)
		if not title:
			title = ''
		attrs = {'geometry' : geometry,
			 'minWidth': min(w, 60),
			 'minHeight': min(h, 60),
			 'width': max(w, 60), 'height': max(h, 60),
			 'colormap': self._colormap,
			 'visual': self._visual,
			 'depth': self._depth,
			 'title': title}
		if title:
			attrs['iconName'] = title
		shell = parent._main.CreatePopupShell(
			'toplevelShell', Xt.ApplicationShell, attrs)
		shell.AddCallback('destroyCallback', self._destroy_callback, None)
		self._shell = shell
		fg = self._convert_color(self._fgcolor)
		bg = self._convert_color(self._bgcolor)
		attrs = {'height': max(h, 60),
			 'width': max(w, 60),
			 'resizePolicy': Xmd.RESIZE_NONE,
			 'background': bg,
			 'foreground': fg,
			 'borderWidth': 0,
			 'marginWidth': 0,
			 'marginHeight': 0,
			 'marginTop': 0,
			 'marginBottom': 0,
			 'shadowThickness': 0}
		form = shell.CreateManagedWidget('toplevel',
						 Xm.DrawingArea, attrs)
		self._form = form
		shell.Popup(0)
		shell.AddWMProtocolCallback(parent._delete_window,
					    self._delete_callback, None)

		val = form.GetValues(['width', 'height'])
		w, h = val['width'], val['height']
		self._rect = 0, 0, w, h
		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		w = float(w) / toplevel._hmm2pxl
		h = float(h) / toplevel._vmm2pxl
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
		self._clip = Xlib.CreateRegion()
		apply(self._clip.UnionRectWithRegion, self._rect)
		form.AddCallback('exposeCallback', self._expose_callback, None)
		form.AddCallback('resizeCallback', self._resize_callback, None)
		form.AddCallback('inputCallback', self._input_callback, None)
		self.setcursor(self._cursor)
		if pixmap:
			self._pixmap = form.CreatePixmap()
			gc = self._pixmap.CreateGC({'foreground': bg,
						    'background': bg})
			gc.FillRectangle(0, 0, w, h)
		else:
			gc = form.CreateGC({'background': bg})
		gc.foreground = fg
		self._gc = gc

	def __repr__(self):
		try:
			title = `self._title`
		except AttributeError:
			title = '<NoTitle>'
		try:
			parent = self._parent
		except AttributeError:
			parent = None
		if parent is None:
			closed = ' (closed)'
		else:
			closed = ''
		return '<_Window instance at %x; title = %s%s>' % \
					(id(self), title, closed)

	def _do_init(self, parent):
		parent._subwindows.insert(0, self)
		self._parent = parent
		self._subwindows = []
		self._displists = []
		self._active_displist = None
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor
		self._callbacks = {}
		self._accelerators = {}
		self._menu = None
		self._transparent = 0
		self._showing = 0

	def close(self):
		if self._parent is None:
			return		# already closed
		self._parent._subwindows.remove(self)
		self._parent = None
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		if self._shell:
			self._shell.DestroyWidget()
		del self._shell
		del self._form
		del self._clip
		del self._topwindow
		del self._gc
		try:
			del self._pixmap
		except AttributeError:
			pass

	def is_closed(self):
		return self._parent is None

	def showwindow(self):
		self._showing = 1
		gc = self._gc
		gc.SetClipMask(None)
		gc.foreground = self._convert_color((255,0,0))
		x, y, w, h = self._rect
		gc.DrawRectangle(x, y, w-1, h-1)
		if hasattr(self, '_pixmap'):
			x, y, w, h = self._rect
			self._pixmap.CopyArea(self._form, gc,
					      x, y, w, h, x, y)
		toplevel._main.UpdateDisplay()

	def dontshowwindow(self):
		if self._showing:
			self._showing = 0
			x, y, w, h = self._rect
			r = Xlib.CreateRegion()
			r.UnionRectWithRegion(x, y, w, h)
			r1 = Xlib.CreateRegion()
			r1.UnionRectWithRegion(x+1, y+1, w-2, h-2)
			r.SubtractRegion(r1)
			self._topwindow._do_expose(r)
			if hasattr(self, '_pixmap'):
				self._gc.SetRegion(r)
				self._pixmap.CopyArea(self._form, self._gc,
						      x, y, w, h, x, y)

	def getgeometry(self):
		x, y = self._form.TranslateCoords(0, 0)
		w, h = self._rect[2:]
		return float(x) / toplevel._hmm2pxl, y / toplevel._vmm2pxl, \
		       w / toplevel._hmm2pxl, h / toplevel._vmm2pxl

	def newwindow(self, coordinates, pixmap = 0, transparent = 0):
		return _SubWindow(self, coordinates, 0, pixmap, transparent)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0):
		return _SubWindow(self, coordinates, 1, pixmap, transparent)

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	def bgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b
		# set window background if nothing displayed on it
		if self._topwindow is self and not self._active_displist and \
		   not self._subwindows:
			self._form.background = self._convert_color(color)
		if not self._active_displist and not self._transparent:
			self._gc.SetRegion(self._clip)
			self._gc.foreground = self._convert_color(color)
			x, y, w, h = self._rect
			self._gc.FillRectangle(x, y, w, h)
			if hasattr(self, '_pixmap'):
				self._pixmap.CopyArea(self._form, self._gc,
						      x, y, w, h, x, y)

	def setcursor(self, cursor):
		self._cursor = cursor
		_setcursor(self._form, cursor)

	def newdisplaylist(self, *bgcolor):
		if bgcolor != ():
			bgcolor = bgcolor[0]
		else:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)

	def settitle(self, title):
		self._shell.SetValues({'title': title, 'iconName': title})

	def pop(self):
		self._shell.Popup(0)

	def push(self):
		self._form.LowerWindow()

	def setredrawfunc(self, func):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'

	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in (ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release):
			self._callbacks[event] = func, arg
		elif event == WindowExit:
			try:
				widget = self._shell
			except AttributeError:
				raise error, 'only WindowExit event for top-level windows'
			widget.deleteResponse = Xmd.DO_NOTHING
			self._callbacks[event] = func, arg
		else:
			raise error, 'Internal error'

	def unregister(self, event):
		try:
			del self._callbacks[event]
		except KeyError:
			pass

	def destroy_menu(self):
		if self._menu:
			self._menu.DestroyWidget()
		self._menu = None
		self._accelerators = {}

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = self._form.CreatePopupMenu('menu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			list = [title, None] + list
		_create_menu(menu, list, self._accelerators)
		self._menu = menu

	def _convert_color(self, color):
		return self._parent._convert_color(color,
			self._colormap is not self._parent._colormap)

	def _convert_coordinates(self, coordinates, crop = 0):
		# convert relative sizes to pixel sizes relative to
		# upper-left corner of the window
		# if crop is set, constrain the coordinates to the
		# area of the window
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		rx, ry, rw, rh = self._rect
##		if not (0 <= x <= 1 and 0 <= y <= 1):
##			raise error, 'coordinates out of bounds'
		px = int((rw - 1) * x + 0.5) + rx
		py = int((rh - 1) * y + 0.5) + ry
		pw = ph = 0
		if crop:
			if px < 0:
				px, pw = 0, px
			if px >= rx + rw:
				px, pw = rx + rw - 1, px - rx - rw + 1
			if py < 0:
				py, ph = 0, py
			if py >= ry + rh:
				py, ph = ry + rh - 1, py - ry - rh + 1
		if len(coordinates) == 2:
			return px, py
##		if not (0 <= w <= 1 and 0 <= h <= 1 and
##			0 <= x + w <= 1 and 0 <= y + h <= 1):
##			raise error, 'coordinates out of bounds'
		pw = int((rw - 1) * w + 0.5) + pw
		ph = int((rh - 1) * h + 0.5) + ph
		if crop:
			if pw <= 0:
				pw = 1
			if px + pw > rx + rw:
				pw = rx + rw - px
			if ph <= 0:
				ph = 1
			if py + ph > ry + rh:
				ph = ry + rh - py
		return px, py, pw, ph

	def _mkclip(self):
		if self._parent is None:
			return
		# create region for whole window
		self._clip = region = Xlib.CreateRegion()
		apply(region.UnionRectWithRegion, self._rect)
		# subtract all subwindows
		for w in self._subwindows:
			if not w._transparent:
				r = Xlib.CreateRegion()
				apply(r.UnionRectWithRegion, w._rect)
				region.SubtractRegion(r)
			w._mkclip()

	def _image_size(self, file):
		try:
			xsize, ysize = toplevel._image_size_cache[file]
		except KeyError:
			try:
				reader = img.reader(None, file)
			except img.error, arg:
				raise error, arg
			xsize = reader.width
			ysize = reader.height
			toplevel._image_size_cache[file] = xsize, ysize
		return xsize, ysize

	def _prepare_image(self, file, crop, scale):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes
		oscale = scale
		tw = self._topwindow
		if tw._depth == 8:
			format = toplevel.myxrgb8
		else:
			format = imgformat.rgb
		depth = format.descr['size'] / 8
		reader = None
		try:
			xsize, ysize = toplevel._image_size_cache[file]
		except KeyError:
			try:
				reader = img.reader(format, file)
			except img.error, arg:
				raise error, arg
			xsize = reader.width
			ysize = reader.height
			toplevel._image_size_cache[file] = xsize, ysize
		top, bottom, left, right = crop
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		x, y, width, height = self._rect
		if scale == 0:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)
		key = '%s@%f' % (`file`, scale)
		try:
			cfile, w, h, mask = toplevel._image_cache[key]
			image = open(cfile, 'rb').read()
		except:			# reading from cache failed
			w, h = xsize, ysize
			if not reader:
				# we got the size from the cache, don't believe it
				del toplevel._image_size_cache[file]
				return self._prepare_image(file, crop, oscale)
			if hasattr(reader, 'transparent'):
				import imageop
				r = img.reader(imgformat.xrgb8, file)
				for i in range(len(r.colormap)):
					r.colormap[i] = 255, 255, 255
				r.colormap[r.transparent] = 0, 0, 0
				image = r.read()
				if scale != 1:
					w = int(xsize * scale + .5)
					h = int(ysize * scale + .5)
					image = imageop.scale(image, 1,
							xsize, ysize, w, h)
				bitmap = ''
				for i in range(h):
					# grey2mono doesn't pad lines :-(
					bitmap = bitmap + imageop.grey2mono(
						image[i*w:(i+1)*w], w, 1, 128)
				mask = tw._visual.CreateImage(1, X.XYPixmap, 0,
							bitmap, w, h, 8, 0)
			else:
				mask = None
			try:
				image = reader.read()
			except:
				raise error, 'unspecified error reading image'
			if scale != 1:
				import imageop
				w = int(xsize * scale + .5)
				h = int(ysize * scale + .5)
				image = imageop.scale(image, depth,
						      xsize, ysize, w, h)
			try:
				import tempfile
				cfile = tempfile.mktemp()
				open(cfile, 'wb').write(image)
				toplevel._image_cache[key] = cfile, w, h, mask
			except:
				print 'Warning: caching image failed'
				try:
					import os
					os.unlink(cfile)
				except:
					pass
		x, y = x + (width - (w - left - right)) / 2, \
		       y + (height - (h - top - bottom)) / 2
		xim = tw._visual.CreateImage(tw._depth, X.ZPixmap, 0, image,
					     w, h, depth * 8, w * depth)
		return xim, mask, left, top, x, y, w - left - right, h - top - bottom

	def _destroy_callback(self, form, client_data, call_data):
		self._shell = None
		self.close()

	def _delete_callback(self, form, client_data, call_data):
		try:
			func, arg = self._callbacks[WindowExit]
		except KeyError:
			pass
		else:
			func(arg, self, WindowExit, None)

	def _input_callback(self, form, client_data, call_data):
		if self._parent is None:
			return		# already closed
		self._do_input_callback(form, client_data, call_data)

	def _do_input_callback(self, form, client_data, call_data):
		event = call_data.event
		x, y = event.x, event.y
		for w in self._subwindows:
			if w._region.PointInRegion(x, y):
				w._do_input_callback(form, client_data, call_data)
				return
		# not in a subwindow, handle it ourselves
		if event.type == X.KeyPress:
			string = Xlib.LookupString(event)[0]
			try:
				func, args = self._accelerators[string]
			except KeyError:
				pass
			else:
				apply(func, args)
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
			try:
				func, arg = self._callbacks[ev]
			except KeyError:
				return
			x, y, width, height = self._rect
			x = float(event.x - x) / width
			y = float(event.y - y) / height
			buttons = []
			adl = self._active_displist
			if adl:
				for but in adl._buttons:
					if but._inside(x, y):
						buttons.append(but)
			func(arg, self, ev, (x, y, buttons))
		else:
			print 'unknown event',`event.type`

	def _expose_callback(self, form, client_data, call_data):
		# no _setcursor during expose!
		if self._parent is None:
			return		# already closed
		e = call_data.event
		# collect redraw regions
		self._exp_reg.UnionRectWithRegion(e.x, e.y, e.width, e.height)
		if e.count == 0:
			# last of a series, do the redraw
			r = self._exp_reg
			self._exp_reg = Xlib.CreateRegion()
			try:
				pm = self._pixmap
			except AttributeError:
				self._do_expose(r)
			else:
				self._gc.SetRegion(r)
				x, y, w, h = self._rect
				pm.CopyArea(form, self._gc, x, y, w, h, x, y)

	def _do_expose(self, region, recursive = 0):
		if self._parent is None:
			return
		# check if there is any overlap of our window with the
		# area to be drawn
		r = Xlib.CreateRegion()
		r.UnionRegion(self._region)
		r.IntersectRegion(region)
		if r.EmptyRegion():
			# no overlap
			return
		# first redraw opaque subwindow, top-most first
		for w in self._subwindows:
			if not w._transparent:
				w._do_expose(region, 1)
		# then draw background window
		r = Xlib.CreateRegion()
		r.UnionRegion(self._clip)
		r.IntersectRegion(region)
		if not r.EmptyRegion():
			if self._transparent and not recursive:
				self._parent._do_expose(r)
			elif self._active_displist:
				self._active_displist._render(r)
			elif not self._transparent:
				gc = self._gc
				gc.SetRegion(r)
				gc.foreground = self._convert_color(self._bgcolor)
				apply(gc.FillRectangle, self._rect)
		# finally draw transparent subwindow, bottom-most first
		sw = self._subwindows[:]
		sw.reverse()
		for w in sw:
			if w._transparent:
				w._do_expose(region, 1)
		if self._showing:
			self.showwindow()

	def _resize_callback(self, form, client_data, call_data):
		val = self._form.GetValues(['width', 'height'])
		x, y = self._rect[:2]
		width, height = val['width'], val['height']
		self._rect = x, y, width, height
		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		# convert pixels to mm
		parent = self._parent
		w = float(width) / toplevel._hmm2pxl
		h = float(height) / toplevel._vmm2pxl
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
		try:
			del self._pixmap
		except AttributeError:
			pixmap = None
		else:
			pixmap = form.CreatePixmap()
			self._pixmap = pixmap
			bg = self._convert_color(self._bgcolor)
			gc = pixmap.CreateGC({'foreground': bg,
					      'background': bg})
			self._gc = gc
			gc.FillRectangle(0, 0, w, h)
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._do_resize1()
		self._mkclip()
		self._do_expose(self._region)
		if pixmap:
			gc.SetRegion(self._region)
			pixmap.CopyArea(form, gc, 0, 0, width, height, 0, 0)
		# call resize callbacks
		self._do_resize2()

	def _do_resize2(self):
		for w in self._subwindows:
			w._do_resize2()
		try:
			func, arg = self._callbacks[ResizeWindow]
		except KeyError:
			pass
		else:
			func(arg, self, ResizeWindow, None)

class _BareSubWindow:
	def __init__(self, parent, coordinates, defcmap, pixmap, transparent):
		x, y, w, h = parent._convert_coordinates(coordinates, crop = 1)
		self._rect = x, y, w, h
		self._sizes = coordinates
		x, y, w, h = coordinates
		if w == 0 or h == 0:
			showmessage('Creating subwindow with zero dimension',
				    mtype = 'warning')
		if w == 0:
			w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
		if h == 0:
			h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
		# conversion factors to convert from mm to relative size
		# (this uses the fact that _hfactor == _vfactor == 1.0
		# in toplevel)
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h

		self._convert_color = parent._convert_color
		self._do_init(parent)
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			self._transparent = transparent
		self._topwindow = parent._topwindow

		self._form = parent._form
		self._gc = parent._gc
		try:
			self._pixmap = parent._pixmap
		except AttributeError:
			have_pixmap = 0
		else:
			have_pixmap = 1

		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		parent._mkclip()
		if not self._transparent:
			self._do_expose(self._region)
			if have_pixmap:
				x, y, w, h = self._rect
				self._gc.SetRegion(self._region)
				self._pixmap.CopyArea(self._form, self._gc,
						      x, y, w, h, x, y)

	def __repr__(self):
		return '<_BareSubWindow instance at %x>' % id(self)

	def close(self):
		parent = self._parent
		if parent is None:
			return		# already closed
		self._parent = None
		parent._subwindows.remove(self)
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		parent._mkclip()
		parent._do_expose(self._region)
		if hasattr(self, '_pixmap'):
			x, y, w, h = self._rect
			self._gc.SetRegion(self._region)
			self._pixmap.CopyArea(self._form, self._gc,
					      x, y, w, h, x, y)
			del self._pixmap
		del self._form
		del self._clip
		del self._topwindow
		del self._region
		del self._gc
		del self._convert_color

	def settitle(self, title):
		raise error, 'can only settitle at top-level'

	def getgeometry(self):
		return self._sizes

	def pop(self):
		parent = self._parent
		# move self to front of _subwindows
		if self is not parent._subwindows[0]:
			parent._subwindows.remove(self)
			parent._subwindows.insert(0, self)
			# recalculate clipping regions
			parent._mkclip()
			# draw the window's contents
			if not self._transparent or self._active_displist:
				self._do_expose(self._region)
				if hasattr(self, '_pixmap'):
					x, y, w, h = self._rect
					self._gc.SetRegion(self._region)
					self._pixmap.CopyArea(self._form,
							      self._gc,
							      x, y, w, h, x, y)
		parent.pop()

	def push(self):
		parent = self._parent
		# move self to end of _subwindows
		if self is parent._subwindows[-1]:
			return		# no-op
		parent._subwindows.remove(self)
		parent._subwindows.append(self)
		# recalculate clipping regions
		parent._mkclip()
		# draw exposed windows
		for w in self._parent._subwindows:
			if w is not self:
				w._do_expose(self._region)
		if hasattr(self, '_pixmap'):
			x, y, w, h = self._rect
			self._gc.SetRegion(self._region)
			self._pixmap.CopyArea(self._form, self._gc,
					      x, y, w, h, x, y)

	def _mkclip(self):
		if self._parent is None:
			return
		_Window._mkclip(self)
		region = self._clip
		# subtract overlapping siblings
		for w in self._parent._subwindows:
			if w is self:
				break
			if not w._transparent:
				r = Xlib.CreateRegion()
				apply(r.UnionRectWithRegion, w._rect)
				region.SubtractRegion(r)

	def _do_resize1(self):
		# calculate new size of subwindow after resize
		# close all display lists
		parent = self._parent
		try:
			del self._pixmap
		except AttributeError:
			pass
		else:
			self._pixmap = parent._pixmap
		self._gc = parent._gc
		x, y, w, h = parent._convert_coordinates(self._sizes, crop = 1)
		self._rect = x, y, w, h
		w, h = self._sizes[2:]
		if w == 0:
			w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
		if h == 0:
			h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		self._active_displist = None
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._do_resize1()

class _SubWindow(_BareSubWindow, _Window):
	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)

class _DisplayList:
	def __init__(self, window, bgcolor):
		self._window = window
		window._displists.append(self)
		self._buttons = []
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._linewidth = 1
		self._gcattr = {'foreground': window._convert_color(self._fgcolor),
				'background': window._convert_color(bgcolor),
				'line_width': 1}
		self._list = []
		if not window._transparent:
			self._list.append(('clear',))
		self._optimdict = {}
		self._cloneof = None
		self._clonestart = 0
		self._rendered = FALSE
		self._font = None
		self._imagemask = None

	def close(self):
		win = self._window
		if win is None:
			return
		for b in self._buttons[:]:
			b.close()
		win._displists.remove(self)
		self._window = None
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			win._do_expose(win._region)
			if hasattr(win, '_pixmap'):
				x, y, w, h = win._rect
				win._gc.SetRegion(win._region)
				win._pixmap.CopyArea(win._form, win._gc,
						     x, y, w, h, x, y)
		del self._cloneof
		try:
			del self._clonedata
		except AttributeError:
			pass
		del self._optimdict
		del self._list
		del self._buttons
		del self._font
		del self._imagemask

	def is_closed(self):
		return self._window is None

	def clone(self):
		w = self._window
		new = _DisplayList(w, self._bgcolor)
		# copy all instance variables
		new._list = self._list[:]
		new._font = self._font
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
			new._clonedata = self._fgcolor, self._font
			new._imagemask = self._imagemask
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def render(self):
		window = self._window
		for b in self._buttons:
			b._highlighted = 0
		region = window._clip
		# draw our bit
		self._render(region)
		# now draw transparent subwindows
		windows = window._subwindows[:]
		windows.reverse()
		for w in windows:
			if w._transparent:
				w._do_expose(region, 1)
		# now draw transparent windows that lie on top of us
		if window._topwindow is not window:
			i = window._parent._subwindows.index(window)
			windows = window._parent._subwindows[:i]
			windows.reverse()
			for w in windows:
				if w._transparent:
					w._do_expose(region, 1)
		# finally, re-highlight window
		if window._showing:
			window.showwindow()
		if hasattr(window, '_pixmap'):
			x, y, width, height = window._rect
			window._pixmap.CopyArea(window._form, window._gc,
						x, y, width, height, x, y)
		toplevel._main.UpdateDisplay()
		
	def _render(self, region):
		self._rendered = TRUE
		w = self._window
		clonestart = self._clonestart
		if not self._cloneof or \
		   self._cloneof is not w._active_displist:
			clonestart = 0
		if w._active_displist and self is not w._active_displist and \
		   w._transparent and clonestart == 0:
			w._active_displist = None
			w._do_expose(region)
		try:
			pm = self._pixmap
		except AttributeError:
			have_pixmap = 0
		else:
			have_pixmap = 1
		gc = w._gc
		gc.ChangeGC(self._gcattr)
		if clonestart > 0:
			fg, font = self._clonedata
			gc.foreground = w._convert_color(fg)
			if font:
				gc.SetFont(font._font)
		gc.SetRegion(region)
		if clonestart == 0 and self._imagemask:
			# restrict to drawing outside the image
			if type(self._imagemask) is RegionType:
				r = Xlib.CreateRegion()
				r.UnionRegion(region)
				r.SubtractRegion(self._imagemask)
				gc.SetRegion(r)
			else:
				width, height = w._topwindow._rect[2:]
				r = w._form.CreatePixmap(width, height, 1)
				g = r.CreateGC({'foreground': 0})
				g.FillRectangle(0, 0, width, height)
				g.SetRegion(region)
				g.foreground = 1
				g.FillRectangle(0, 0, width, height)
				g.function = X.GXcopyInverted
				apply(g.PutImage, self._imagemask)
				gc.SetClipMask(r)
		for i in range(clonestart, len(self._list)):
			self._do_render(self._list[i], region)
		w._active_displist = self
		for b in self._buttons:
			if b._highlighted:
				b._do_highlight()

	def _do_render(self, entry, region):
		cmd = entry[0]
		w = self._window
		gc = w._gc
		if cmd == 'clear':
			fg = gc.foreground
			gc.foreground = gc.background
			apply(gc.FillRectangle, w._rect)
			gc.foreground = fg
		elif cmd == 'fg':
			gc.foreground = entry[1]
		elif cmd == 'image':
			mask = entry[1]
			if mask:
				# mask is clip mask for image
				width, height = w._topwindow._rect[2:]
				p = w._form.CreatePixmap(width, height, 1)
				g = p.CreateGC({'foreground': 0})
				g.FillRectangle(0, 0, width, height)
				g.SetRegion(region)
				g.foreground = 1
				g.FillRectangle(0, 0, width, height)
				apply(g.PutImage, (mask,) + entry[3:])
				gc.SetClipMask(p)
			else:
				gc.SetRegion(region)
			apply(gc.PutImage, entry[2:])
			if mask:
				gc.SetRegion(region)
		elif cmd == 'line':
			fg = gc.foreground
			gc.foreground = entry[1]
			points = entry[2]
			x0, y0 = points[0]
			for x, y in points[1:]:
				gc.DrawLine(x0, y0, x, y)
				x0, y0 = x, y
			gc.foreground = fg
		elif cmd == 'box':
			apply(gc.DrawRectangle, entry[1])
		elif cmd == 'fbox':
			fg = gc.foreground
			gc.foreground = entry[1]
			apply(gc.FillRectangle, entry[2])
			gc.foreground = fg
		elif cmd == 'marker':
			fg = gc.foreground
			gc.foreground = entry[1]
			x, y = entry[2]
			radius = 5 # XXXX
			gc.FillArc(x-radius, y-radius, 2*radius, 2*radius,
				   0, 360*64)
			gc.foreground = fg
		elif cmd == 'font':
			gc.SetFont(entry[1])
		elif cmd == 'text':
			apply(gc.DrawString, entry[1:])
		elif cmd == 'linewidth':
			gc.line_width = entry[1]

	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('fg', self._window._convert_color(color))
		self._fgcolor = color

	def linewidth(self, width):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('linewidth', width)
		self._linewidth = width

	def newbutton(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return _Button(self, coordinates)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       w._prepare_image(file, crop, scale)
		if mask:
			self._imagemask = mask, src_x, src_y, dest_x, dest_y, width, height
		else:
			r = Xlib.CreateRegion()
			r.UnionRectWithRegion(dest_x, dest_y, width, height)
			self._imagemask = r
		self._list.append('image', mask, image, src_x, src_y,
				  dest_x, dest_y, width, height)
		self._optimize(2)
		x, y, w, h = w._rect
		return float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append('line', color, p)

	def drawbox(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('box',
				self._window._convert_coordinates(coordinates))
		self._optimize()

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('fbox', self._window._convert_color(color),
				self._window._convert_coordinates(coordinates))
		self._optimize(1)

	def drawmarker(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('marker', self._window._convert_color(color),
				self._window._convert_coordinates(coordinates))

	def usefont(self, fontobj):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
		self._list.append('font', fontobj._font)
		return self.baseline(), self.fontheight(), self.pointsize()

	def setfont(self, font, size):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, margin = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(fontname, 10))

	def baseline(self):
		return self._font.baseline() * self._window._vfactor

	def fontheight(self):
		return self._font.fontheight() * self._window._vfactor

	def pointsize(self):
		return self._font.pointsize()

	def strsize(self, str):
		width, height = self._font.strsize(str)
		return float(width) * self._window._hfactor, \
		       float(height) * self._window._vfactor

	def setpos(self, x, y):
		self._curpos = x, y
		self._xpos = x

	def writestr(self, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		f = self._font._font
		base = self.baseline()
		height = self.fontheight()
		strlist = string.splitfields(str, '\n')
		oldx, oldy = x, y = self._curpos
		if len(strlist) > 1 and oldx > self._xpos:
			oldx = self._xpos
		oldy = oldy - base
		maxx = oldx
		for str in strlist:
			x0, y0 = w._convert_coordinates((x, y))
			list.append('text', x0, y0, str)
			self._curpos = x + float(f.TextWidth(str)) / w._rect[_WIDTH], y
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, newy - oldy + height - base

	def _optimize(self, ignore = []):
		if type(ignore) is IntType:
			ignore = [ignore]
		entry = self._list[-1]
		x = []
		for i in range(len(entry)):
			if i not in ignore:
				z = entry[i]
				if type(z) is ListType:
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

class _Button:
	def __init__(self, dispobj, coordinates):
		self._dispobj = dispobj
		dispobj._buttons.append(self)
		window = dispobj._window
		self._coordinates = coordinates
		x, y, w, h = coordinates
		self._corners = x, y, x + w, y + h
		self._color = self._hicolor = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		self._newdispobj = None
		self._highlighted = 0
		if self._color == dispobj._bgcolor:
			return
		dispobj.drawbox(self._coordinates)

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
		if hasattr(window, '_pixmap'):
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
		if hasattr(window, '_pixmap'):
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

_fontmap = {
	  'Times-Roman': '-*-times-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Times-Italic': '-*-times-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Times-Bold': '-*-times-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Utopia': '-*-utopia-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Utopia-Italic': '-*-utopia-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Utopia-Bold': '-*-utopia-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Palatino': '-*-palatino-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Palatino-Italic': '-*-palatino-medium-i-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Palatino-Bold': '-*-palatino-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Helvetica': '-*-helvetica-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Helvetica-Bold': '-*-helvetica-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Helvetica-Oblique': '-*-helvetica-medium-o-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier': '-*-courier-medium-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier-Bold': '-*-courier-bold-r-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier-Oblique': '-*-courier-medium-o-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Courier-Bold-Oblique': '-*-courier-bold-o-normal-*-*-*-*-*-*-*-iso8859-1',
	  'Greek': ['-*-arial-regular-r-*-*-*-*-*-*-p-*-iso8859-7',
		    '-*-*-medium-r-*--*-*-*-*-*-*-iso8859-7'],
	  'Greek-Bold': ['-*-arial-bold-r-*--*-*-*-*-p-*-iso8859-7',
			 '-*-*-bold-r-*-*-*-*-*-*-*-*-iso8859-7'],
	  'Greek-Italic': '-*-arial-regular-i-*-*-*-*-*-*-p-*-iso8859-7',
	  }
fonts = _fontmap.keys()

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

def findfont(fontname, pointsize):
	key = fontname + `pointsize`
	try:
		return _fontcache[key]
	except KeyError:
		pass
	try:
		fontnames = _fontmap[fontname]
	except KeyError:
		raise error, 'Unknown font ' + `fontname`
	if type(fontnames) is StringType:
		fontnames = [fontnames]
	fontlist = []
	for fontname in fontnames:
		fontlist = toplevel._main.ListFonts(fontname)
		if fontlist:
			break
	if not fontlist:
		# if no matching fonts, use Courier, same encoding
		parsedfont = _parsefontname(fontname)
		font = '-*-courier-*-r-*-*-*-*-*-*-*-*-%s-%s' % \
		       (parsedfont[_REGISTRY], parsedfont[_ENCODING])
		fontlist = toplevel._main.ListFonts(font)
	if not fontlist:
		# if still no matching fonts, use any font, same encoding
		parsedfont = _parsefontname(fontname)
		font = '-*-*-*-*-*-*-*-*-*-*-*-*-%s-%s' % \
		       (parsedfont[_REGISTRY], parsedfont[_ENCODING])
		fontlist = toplevel._main.ListFonts(font)
	if not fontlist:
		# if still no matching fonts, use Courier, any encoding
		fontlist = toplevel._main.ListFonts('-*-courier-*-r-*-*-*-*-*-*-*-*-*-*')
	if not fontlist:
		# if still no matching fonts, use any font, any encoding
		fontlist = toplevel._main.ListFonts('-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
	if not fontlist:
		# if no fonts at all, give up
		raise error, 'no fonts available'
	pixelsize = pointsize * toplevel._dpi_y / 72.0
	bestsize = 0
	psize = pointsize
	scfont = None
	thefont = None
	for font in fontlist:
		parsedfont = _parsefontname(font)
## scaled fonts don't look very nice, so this code is disabled
##		# scale the font if possible
##		if parsedfont[_PIXELS] == '0':
##			# scalable font
##			parsedfont[_PIXELS] = '*'
##			parsedfont[_POINTS] = `int(pointsize * 10)`
##			parsedfont[_RES_X] = `toplevel._dpi_x`
##			parsedfont[_RES_Y] = `toplevel._dpi_y`
##			parsedfont[_AVG_WIDTH] = '*'
##			thefont = _makefontname(parsedfont)
##			psize = pointsize
##			break
		# remember scalable font in case no other sizes available
		if parsedfont[_PIXELS] == '0':
			scfont = parsedfont
			continue
		p = string.atoi(parsedfont[_PIXELS])
		# either use closest, or use next smaller
		if abs(pixelsize - p) < abs(pixelsize - bestsize): # closest
##		if p <= pixelsize and p > bestsize: # biggest <= wanted
			bestsize = p
			thefont = font
			psize = p * 72.0 / toplevel._dpi_y
	if thefont is None:
		# didn't find a font
		if scfont is not None:
			# but we found a scalable font, so use it
			scfont[_PIXELS] = '*'
			scfont[_POINTS] = `int(pointsize * 10)`
			scfont[_RES_X] = `toplevel._dpi_x`
			scfont[_RES_Y] = `toplevel._dpi_y`
			scfont[_AVG_WIDTH] = '*'
			thefont = _makefontname(scfont)
			psize = pointsize
		else:
			# no font available, complain.  Loudly.
			raise error, "can't find any fonts"
	fontobj = _Font(thefont, psize)
	_fontcache[key] = fontobj
	return fontobj	
	
class _Font:
	def __init__(self, fontname, pointsize):
		self._font = toplevel._main.LoadQueryFont(fontname)
		self._pointsize = pointsize
		self._fontname = fontname
##		print 'Using', fontname

	def close(self):
		self._font = None

	def is_closed(self):
		return self._font is None

	def strsize(self, str):
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		f = self._font
		maxheight = len(strlist) * (f.ascent + f.descent)
		for str in strlist:
			width = f.TextWidth(str)
			if width > maxwidth:
				maxwidth = width
		return float(maxwidth) / toplevel._hmm2pxl, \
		       float(maxheight) / toplevel._vmm2pxl

	def baseline(self):
		return float(self._font.ascent) / toplevel._vmm2pxl

	def fontheight(self):
		f = self._font
		return float(f.ascent + f.descent) / toplevel._vmm2pxl

	def pointsize(self):
		return self._pointsize

class showmessage:
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message'):
		if grab:
			dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
			w = grab
			if type(w) is IntType:
				w = toplevel
			while 1:
				if hasattr(w, '_shell'):
					w = w._shell
					break
				if hasattr(w, '_main'):
					w = w._main
					break
				w = w._parent
		else:
			dialogStyle = Xmd.DIALOG_MODELESS
			w = toplevel._main
		if mtype == 'error':
			func = w.CreateErrorDialog
		elif mtype == 'warning':
			func = w.CreateWarningDialog
		elif mtype == 'information':
			func = w.CreateInformationDialog
		elif mtype == 'question':
			func = w.CreateQuestionDialog
		else:
			func = w.CreateMessageDialog
		self._grab = grab
		w = func(name, {'messageString': text,
				'title': title,
				'dialogStyle': dialogStyle,
				'resizePolicy': Xmd.RESIZE_NONE,
				'visual': toplevel._default_visual,
				'depth': toplevel._default_visual.depth,
				'colormap': toplevel._default_colormap})
		w.MessageBoxGetChild(Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		if mtype == 'question' or cancelCallback:
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
			self._widget.RemoveEventHandler(X.ButtonPressMask,
						FALSE, self._post_menu, None)
			self._menu.DestroyWidget()
		self._menu = None

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = self._widget.CreatePopupMenu('dialogMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			list = [title, None] + list
		_create_menu(menu, list)
		self._menu = menu
		self._widget.AddEventHandler(X.ButtonPressMask, FALSE,
					     self._post_menu, None)

	def _post_menu(self, widget, client_data, call_data):
		if not self._menu:
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
		
class MainDialog(Dialog):
	pass	# Same as Dialog, for X

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
		self.looping = TRUE
		while self.looping:
			event = Xt.NextEvent()
			Xt.DispatchEvent(event)
		return self.answer

	def callback(self, msg):
		for i in range(len(self.msg_list)):
			if msg is self.msg_list[i]:
				self.answer = i
				self.looping = FALSE
				return

def multchoice(prompt, list, defindex):
	return _MultChoice(prompt, list, defindex).run()

def beep():
	dpy = toplevel._main.Display()
	dpy.Bell(100)
	dpy.Flush()

def _colormask(mask):
	shift = 0
	while (mask & 1) == 0:
		shift = shift + 1
		mask = mask >> 1
	if mask < 0:
		width = 32 - shift	# assume integers are 32 bits
	else:
		width = 0
		while mask != 0:
			width = width + 1
			mask = mask >> 1
	return shift, (1 << width) - 1

def _generic_callback(widget, (func, args), call_data):
	apply(func, args)

def _create_menu(menu, list, acc = None):
	accelerator = None
	length = 0
	i = 0
	while i < len(list):
		entry = list[i]
		i = i + 1
		if entry is None:
			dummy = menu.CreateManagedWidget('separator',
							 Xm.SeparatorGadget,
							 {})
			continue
		if length == 20 and i < len(list) - 3:
			entry = ('More', list[i-1:])
			i = len(list)
			if acc is not None:
				entry = ('',) + entry
		length = length + 1
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
			submenu = menu.CreatePulldownMenu('submenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
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

def _setcursor(form, cursor):
	if cursor == 'watch':
		form.DefineCursor(toplevel._watchcursor)
	elif cursor == 'channel':
		form.DefineCursor(toplevel._channelcursor)
	elif cursor == 'link':
		form.DefineCursor(toplevel._linkcursor)
	elif cursor == 'stop':
		form.DefineCursor(toplevel._stopcursor)
	elif cursor == '':
		form.UndefineCursor()
	else:
		raise error, 'unknown cursor glyph'

def roundi(x):
	if x < 0:
		return roundi(x + 1024) - 1024
	return int(x + 0.5)
