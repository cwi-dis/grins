__version__ = "$Id$"

import Xlib, Xt, Xm, X, Xmd
import math
from types import TupleType
import img
from XTopLevel import toplevel
from XConstants import *
from XConstants import _WAITING_CURSOR, _READY_CURSOR, _WIDTH, _HEIGHT
from XAdornment import _AdornmentSupport, _CommandSupport
from XDisplist import _DisplayList
from XDialog import showmessage
from XHelpers import _create_menu, _setcursor
import ToolTip
from WMEVENTS import *

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""

class _Window(_AdornmentSupport):
	# Instances of this class represent top-level windows.  This
	# class is also used as base class for subwindows, but then
	# some of the methods are overridden.
	#
	# The following instance variables are used.  Unless otherwise
	# noted, the variables are used both in top-level windows and
	# subwindows.
	# _shell: the Xt.ApplicationShell widget used for the window
	#	(top-level windows only)
	# _form: the Xm.DrawingArea widget used for the window
	# _scrwin: the Xm.ScrolledWindow widget used for scrolling the canvas
	# _clipcanvas: the Xm.DrawingArea widget used by the Xm.ScrolledWindow
	# _colormap: the colormap used by the window (top-level
	#	windows only)
	# _visual: the visual used by the window (top-level windows
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
	#	be transparent) -1 if window should be transparent if
	#	there is no active display list
	# _sizes: the position and size of the window in fractions of
	#	the parent window (subwindows only)
	# _rect: the position and size of the window in pixels
	# _region: _rect as an X Region
	# _clip: an X Region representing the visible area of the
	#	window
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
	def __init__(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
		     units = UNIT_MM, adornments = None,
		     canvassize = None, commandlist = None, resizable = 1):
		_AdornmentSupport.__init__(self)
		menubar = toolbar = shortcuts = None
		if adornments is not None:
			shortcuts = adornments.get('shortcuts')
			menubar = adornments.get('menubar')
			toolbar = adornments.get('toolbar')
			toolbarvertical = adornments.get('toolbarvertical', 0)
			close = adornments.get('close', [])
			if close:
				self._set_deletecommands(close)
		if shortcuts is not None:
			self._create_shortcuts(shortcuts)
		self._title = title
		parent._subwindows.insert(0, self)
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
		# convert to pixels
		if units == UNIT_MM:
			if x is not None:
				x = int(float(x) * toplevel._hmm2pxl + 0.5)
			if y is not None:
				y = int(float(y) * toplevel._vmm2pxl + 0.5)
			w = int(float(w) * toplevel._hmm2pxl + 0.5)
			h = int(float(h) * toplevel._vmm2pxl + 0.5)
		elif units == UNIT_SCREEN:
			if x is not None:
				x = int(float(x) * toplevel._screenwidth + 0.5)
			if y is not None:
				y = int(float(y) * toplevel._screenheight + 0.5)
			w = int(float(w) * toplevel._screenwidth + 0.5)
			h = int(float(h) * toplevel._screenheight + 0.5)
		elif units == UNIT_PXL:
			if x is not None:
				x = int(x)
			if y is not None:
				y = int(y)
			w = int(w)
			h = int(h)
		else:
			raise error, 'bad units specified'
		# XXX--somehow set the position
		if x is None or y is None:
			geometry = None
		else:
			geometry = '+%d+%d' % (x, y)
		if not title:
			title = ''
		attrs = {'minWidth': min(w, 60),
			 'minHeight': min(h, 60),
			 'colormap': self._colormap,
			 'visual': self._visual,
			 'depth': self._depth,
			 'title': title}
		if geometry:
			attrs['geometry'] = geometry
		if title:
			attrs['iconName'] = title
		shell = parent._main.CreatePopupShell(
			'toplevelShell', Xt.TopLevelShell, attrs)
		shell.AddCallback('destroyCallback', self._destroy_callback, None)
		shell.AddWMProtocolCallback(parent._delete_window,
					    self._delete_callback, None)
		shell.deleteResponse = Xmd.DO_NOTHING
		self._shell = shell
		attrs = {'allowOverlap': 0}
		if not resizable:
			attrs['resizePolicy'] = Xmd.RESIZE_NONE
			attrs['noResize'] = 1
			attrs['resizable'] = 0
		form = shell.CreateManagedWidget('toplevelForm', Xm.Form,
						 attrs)
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
			 'shadowThickness': 0,
			 'leftAttachment': Xmd.ATTACH_FORM,
			 'rightAttachment': Xmd.ATTACH_FORM,
			 'topAttachment': Xmd.ATTACH_FORM,
			 'bottomAttachment': Xmd.ATTACH_FORM}
		self._menubar = None
		if menubar is not None:
			mattrs = {'leftAttachment': Xmd.ATTACH_FORM,
				  'rightAttachment': Xmd.ATTACH_FORM,
				  'topAttachment': Xmd.ATTACH_FORM}
			if toolbar is None and (w == 0 or h == 0):
				mattrs['bottomAttachment'] = Xmd.ATTACH_FORM
			mb = form.CreateMenuBar('menubar', mattrs)
			mb.ManageChild()
			attrs['topAttachment'] = Xmd.ATTACH_WIDGET
			attrs['topWidget'] = mb
			self._create_menu(mb, menubar)
			self._menubar = mb
		self._toolbar = None
		if toolbar is not None:
			# create a XmForm widget with 2 children:
			# an XmRowColumn widget for the toolbar and an
			# XmFrame widget to fill up the space.
			# The toolbar can be horizontal or vertical
			# depending on toolbarvertical.
			fattrs = {'leftAttachment': Xmd.ATTACH_FORM}
			tbattrs = {'marginWidth': 0,
				   'marginHeight': 0,
				   'spacing': 0,
				   'leftAttachment': Xmd.ATTACH_FORM,
				   'topAttachment': Xmd.ATTACH_FORM,
				   'navigationType': Xmd.NONE,
				   }
			if w == 0 or h == 0:
				fattrs['bottomAttachment'] = Xmd.ATTACH_FORM
				fattrs['rightAttachment'] = Xmd.ATTACH_FORM
			if toolbarvertical:
				tbattrs['orientation'] = Xmd.VERTICAL
				tbattrs['rightAttachment'] = Xmd.ATTACH_FORM
				fattrs['bottomAttachment'] = Xmd.ATTACH_FORM
			else:
				tbattrs['orientation'] = Xmd.HORIZONTAL
				tbattrs['bottomAttachment'] = Xmd.ATTACH_FORM
				fattrs['rightAttachment'] = Xmd.ATTACH_FORM
			if self._menubar is not None:
				fattrs['topAttachment'] = Xmd.ATTACH_WIDGET
				fattrs['topWidget'] = self._menubar
			else:
				fattrs['topAttachment'] = Xmd.ATTACH_FORM
				attrs['topAttachment'] = Xmd.ATTACH_WIDGET
			fr = form.CreateManagedWidget('toolform', Xm.Form,
						      fattrs)
			tb = fr.CreateManagedWidget('toolbar', Xm.RowColumn,
						    tbattrs)
			frattrs = {'rightAttachment': Xmd.ATTACH_FORM,
				   'bottomAttachment': Xmd.ATTACH_FORM,
				   'shadowType': Xmd.SHADOW_OUT}
			if toolbarvertical:
				frattrs['leftAttachment'] = Xmd.ATTACH_FORM
				frattrs['topAttachment'] = Xmd.ATTACH_WIDGET
				frattrs['topWidget'] = tb
				attrs['leftAttachment'] = Xmd.ATTACH_WIDGET
				attrs['leftWidget'] = fr
			else:
				frattrs['leftAttachment'] = Xmd.ATTACH_WIDGET
				frattrs['leftWidget'] = tb
				frattrs['topAttachment'] = Xmd.ATTACH_FORM
				attrs['topWidget'] = fr
			void = fr.CreateManagedWidget('toolframe', Xm.Frame,
						      frattrs)
			self._toolbar = tb
			self._create_toolbar(tb, toolbar, toolbarvertical)
		if canvassize is not None and \
		   (menubar is None or (w > 0 and h > 0)):
			form = form.CreateScrolledWindow('scrolledWindow',
				{'scrollingPolicy': Xmd.AUTOMATIC,
				 'scrollBarDisplayPolicy': Xmd.STATIC,
				 'spacing': 0,
				 'width': attrs['width'],
				 'height': attrs['height'],
				 'leftAttachment': Xmd.ATTACH_FORM,
				 'rightAttachment': Xmd.ATTACH_FORM,
				 'bottomAttachment': Xmd.ATTACH_FORM,
				 'topAttachment': attrs['topAttachment'],
				 'topWidget': attrs.get('topWidget',0)})
			form.ManageChild()
			self._scrwin = form
			for w in form.children:
				if w.Class() == Xm.DrawingArea:
					w.AddCallback('resizeCallback',
						self._scr_resize_callback,
						form)
					self._clipcanvas = w
					break
			width, height = canvassize
			# convert to pixels
			if units == UNIT_MM:
				width = int(float(width) * toplevel._hmm2pxl + 0.5)
				height = int(float(height) * toplevel._vmm2pxl + 0.5)
			elif units == UNIT_SCREEN:
				width = int(float(width) * toplevel._screenwidth + 0.5)
				height = int(float(height) * toplevel._screenheight + 0.5)
			elif units == UNIT_PXL:
				width = int(width)
				height = int(height)
			spacing = form.spacing
			attrs['width'] = 0
			attrs['height'] = 0
		self.setcursor(_WAITING_CURSOR)
		if commandlist is not None:
			self.set_commandlist(commandlist)
		if menubar is not None and w == 0 or h == 0:
			# no canvas (DrawingArea) needed
			self._form = None
			shell.Popup(0)
			self._rect = self._region = self._clip = \
				     self._pixmap = self._gc = None
			return
		form = form.CreateManagedWidget('toplevel',
						Xm.DrawingArea, attrs)
		self._form = form
		shell.Popup(0)

		val = form.GetValues(['width', 'height'])
		w, h = val['width'], val['height']
		self._rect = 0, 0, w, h
		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		if pixmap:
			self._pixmap = form.CreatePixmap()
			gc = self._pixmap.CreateGC({'foreground': bg,
						    'background': bg})
			gc.FillRectangle(0, 0, w, h)
		else:
			self._pixmap = None
			gc = form.CreateGC({'background': bg})
		gc.foreground = fg
		self._gc = gc
		w = float(w) / toplevel._hmm2pxl
		h = float(h) / toplevel._vmm2pxl
		self._clip = Xlib.CreateRegion()
		apply(self._clip.UnionRectWithRegion, self._rect)
		form.AddCallback('exposeCallback', self._expose_callback, None)
		form.AddCallback('resizeCallback', self._resize_callback, None)
		form.AddCallback('inputCallback', self._input_callback, None)
		self._motionhandlerset = 0

	def _setmotionhandler(self):
		set = not self._buttonregion.EmptyRegion()
		if self._motionhandlerset == set:
			return
		if set:
			func = self._form.AddEventHandler
		else:
			func = self._form.RemoveEventHandler
		func(X.PointerMotionMask, FALSE, self._motion_handler, None)
		self._motionhandlerset = set

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
		self._parent = parent
		self._subwindows = []
		self._displists = []
		self._active_displist = None
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor
		self._curcursor = ''
		self._curpos = None
		self._buttonregion = Xlib.CreateRegion()
		self._callbacks = {}
		self._accelerators = {}
		self._menu = None		# Dynamically generated popup menu (channels)
		self._popupmenu = None	# Template-based popup menu (views)
		self._transparent = 0
		self._showing = None
		self._redrawfunc = None
		self._scrwin = None	# Xm.ScrolledWindow widget if any
		self._arrowcache = {}
		self._next_create_box = []

	def close(self):
		if self._parent is None:
			return		# already closed
		_AdornmentSupport.close(self)
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
		del self._pixmap
		del self._arrowcache

	def is_closed(self):
		return self._parent is None

	def showwindow(self, color = (255,0,0)):
		self._showing = color
		gc = self._gc
		gc.SetClipMask(None)
		gc.foreground = self._convert_color(color)
		x, y, w, h = self._rect
		gc.DrawRectangle(x, y, w-1, h-1)
		if self._pixmap is not None:
			x, y, w, h = self._rect
			self._pixmap.CopyArea(self._form, gc,
					      x, y, w, h, x, y)
		toplevel._main.UpdateDisplay()

	def dontshowwindow(self):
		if self._showing:
			self._showing = None
			x, y, w, h = self._rect
			r = Xlib.CreateRegion()
			r.UnionRectWithRegion(x, y, w, h)
			r1 = Xlib.CreateRegion()
			r1.UnionRectWithRegion(x+1, y+1, w-2, h-2)
			r.SubtractRegion(r1)
			self._topwindow._do_expose(r)
			if self._pixmap is not None:
				self._gc.SetRegion(r)
				self._pixmap.CopyArea(self._form, self._gc,
						      x, y, w, h, x, y)

	def getgeometry(self, units = UNIT_MM):
		x, y = self._shell.TranslateCoords(0, 0)
		for w in self._shell.children[0].children:
			if w.Class() == Xm.ScrolledWindow:
				val = w.GetValues(['width', 'height'])
				w = val['width']
				h = val['height']
				break
		else:
			if self._rect is None:
				w = h = 0
			else:
				w, h = self._rect[2:]
		if units == UNIT_MM:
			return float(x) / toplevel._hmm2pxl, \
			       float(y) / toplevel._vmm2pxl, \
			       float(w) / toplevel._hmm2pxl, \
			       float(h) / toplevel._vmm2pxl
		elif units == UNIT_SCREEN:
			return float(x) / toplevel._screenwidth, \
			       float(y) / toplevel._screenheight, \
			       float(w) / toplevel._screenwidth, \
			       float(h) / toplevel._screenheight
		elif units == UNIT_PXL:
			return x, y, w, h
		else:
			raise error, 'bad units specified'

	def setcanvassize(self, code):
		if self._scrwin is None:
			raise error, 'no scrollable window'
		# this triggers a resizeCallback
		auto = self._scrwin.scrollBarDisplayPolicy == Xmd.AS_NEEDED
		clipwin = self._scrwin.clipWindow
		if auto:
			val = clipwin.GetValues(['width', 'height'])
			cwidth = val['width']
			cheight = val['height']
			val = self._form.GetValues(['width', 'height'])
			fwidth = val['width']
			fheight = val['height']
		if code == RESET_CANVAS:
			if auto and cwidth < fwidth:
				# there is a vertical scrollbar which will go
				vs = self._scrwin.verticalScrollBar
				hmargin = vs.width + 2 * vs.shadowThickness
			else:
				hmargin = 0
			if auto and cheight < fheight:
				# there is a horizontal scrollbar which will go
				hs = self._scrwin.horizontalScrollBar
				vmargin = hs.height + 2 * hs.shadowThickness
			else:
				vmargin = 0
			self._form.SetValues({'width': clipwin.width + hmargin,
					      'height': clipwin.height + vmargin})
		elif code == DOUBLE_HEIGHT:
			attrs = {'height': self._form.height * 2}
			if auto and cwidth == fwidth:
				# there's will be a vertical scrollbar
				vs = self._scrwin.verticalScrollBar
				hmargin = vs.width + 2 * vs.shadowThickness
				attrs['width'] = cwidth - hmargin
			self._form.SetValues(attrs)
		elif code == DOUBLE_WIDTH:
			attrs = {'width': self._form.width * 2}
			if auto and cheight == fheight:
				# there's will be a horizontal scrollbar
				hs = self._scrwin.horizontalScrollBar
				vmargin = hs.height + 2 * hs.shadowThickness
				attrs['height'] = cheight - vmargin
			self._form.SetValues(attrs)

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return _SubWindow(self, coordinates, 0, pixmap, transparent, z, units)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return _SubWindow(self, coordinates, 1, pixmap, transparent, z, units)

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
		if not self._active_displist and self._transparent == 0:
			self._gc.SetRegion(self._clip)
			self._gc.foreground = self._convert_color(color)
			x, y, w, h = self._rect
			self._gc.FillRectangle(x, y, w, h)
			if self._pixmap is not None:
				self._pixmap.CopyArea(self._form, self._gc,
						      x, y, w, h, x, y)

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		elif cursor != 'hand':
			self._cursor = cursor
		if cursor == '' and self._curpos is not None and \
		   apply(self._buttonregion.PointInRegion, self._curpos):
			cursor = 'hand'
		if toplevel._waiting:
			cursor = 'watch'
		_setcursor(self._shell, cursor)
		self._curcursor = cursor

	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
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
			self._redrawfunc = func
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
			for key in self._menuaccel:
				del self._accelerators[key]
		self._menu = None

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = self._form.CreatePopupMenu('menu',
				{'colormap': self._colormap,
				 'visual': self._visual,
				 'depth': self._visual.depth})
		if self._visual.depth == 8:
			# make sure menu is readable, even on Suns
			menu.foreground = self._convert_color((0,0,0))
			menu.background = self._convert_color((255,255,255))
		if title:
			list = [title, None] + list
		_create_menu(menu, list, self._visual, self._colormap,
			     self._accelerators)
		self._menuaccel = []
		for entry in list:
			if type(entry) is TupleType:
				key = entry[0]
				if key:
					self._menuaccel.append(key)
		self._menu = menu
		
	def create_box(self, msg, callback, box = None, units = UNIT_SCREEN):
		import Xcursorfont
		if toplevel._in_create_box:
			toplevel._in_create_box._next_create_box.append((self, msg, callback, box, units))
			return
		if self.is_closed():
			apply(callback, ())
			return
		toplevel.setcursor('stop')
		self._topwindow.setcursor('')
		toplevel._in_create_box = self
		if box:
			# convert box to relative sizes if necessary
			box = self._pxl2rel(self._convert_coordinates(box, units = units))
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
		for win in toplevel._subwindows:
			if win is self._topwindow:
				continue
			if hasattr(win, '_shell'):
				win._shell.SetSensitive(0)
			elif hasattr(win, '_main'):
				win._main.SetSensitive(0)
		self._rb_dialog = showmessage(
			msg, mtype = 'message', grab = 0,
			callback = (self._rb_done, ()),
			cancelCallback = (self._rb_cancel, ()))
		self._rb_callback = callback
		self._rb_units = units
		form = self._form
		form.RemoveEventHandler(X.PointerMotionMask, FALSE,
					self._motion_handler, None)
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
		self._rb_dialog.setcursor('')
		self._rb_looping = 1
		toplevel.setready()
		while self._rb_looping:
			Xt.DispatchEvent(Xt.NextEvent())

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

	def _convert_color(self, color):
		return self._parent._convert_color(color,
			self._colormap is not self._parent._colormap)

	def _convert_coordinates(self, coordinates, crop = 0, units = UNIT_SCREEN):
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
		if units == UNIT_PXL or (units is None and type(x) is type(0)):
			px = int(x)
		else:
			px = int((rw - 1) * x + 0.5) + rx
		if units == UNIT_PXL or (units is None and type(y) is type(0)):
			py = int(y)
		else:
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
		if units == UNIT_PXL or (units is None and type(w) is type(0)):
			pw = int(w + pw)
		else:
			pw = int((rw - 1) * w + 0.5) + pw
		if units == UNIT_PXL or (units is None and type(h) is type(0)):
			ph = int(h + ph)
		else:
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

	def _pxl2rel(self, coordinates):
		px, py = coordinates[:2]
		rx, ry, rw, rh = self._rect
		x = float(px - rx) / (rw - 1)
		y = float(py - ry) / (rh - 1)
		if len(coordinates) == 2:
			return x, y
		pw, ph = coordinates[2:]
		w = float(pw) / (rw - 1)
		h = float(ph) / (rh - 1)
		return x, y, w, h

	def _mkclip(self):
		if self._parent is None:
			return
		# create region for whole window
		self._clip = region = Xlib.CreateRegion()
		apply(region.UnionRectWithRegion, self._rect)
		self._buttonregion = bregion = Xlib.CreateRegion()
		# subtract all subwindows
		for w in self._subwindows:
			if w._transparent == 0 or \
			   (w._transparent == -1 and w._active_displist):
				r = Xlib.CreateRegion()
				apply(r.UnionRectWithRegion, w._rect)
				region.SubtractRegion(r)
			w._mkclip()
			bregion.UnionRegion(w._buttonregion)
		# create region for all visible buttons
		if self._active_displist is not None:
			r = Xlib.CreateRegion()
			r.UnionRegion(self._clip)
			r.IntersectRegion(self._active_displist._buttonregion)
			bregion.UnionRegion(r)
		if self._topwindow is self:
			self._setmotionhandler()

	def _delclip(self, child, region):
		# delete child's overlapping siblings
		for w in self._subwindows:
			if w is child:
				break
			if w._transparent == 0 or \
			   (w._transparent == -1 and w._active_displist):
				r = Xlib.CreateRegion()
				apply(r.UnionRectWithRegion, w._rect)
				region.SubtractRegion(r)

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

	def _prepare_image(self, file, crop, scale, center, coordinates):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes
		oscale = scale
		tw = self._topwindow
		format = toplevel._imgformat
		depth = format.descr['align'] / 8
		reader = None
		if toplevel._image_size_cache.has_key(file):
			xsize, ysize = toplevel._image_size_cache[file]
		else:
			try:
				reader = img.reader(format, file)
			except (img.error, IOError), arg:
				raise error, arg
			xsize = reader.width
			ysize = reader.height
			toplevel._image_size_cache[file] = xsize, ysize
		top, bottom, left, right = crop
		if top + bottom >= 1.0 or left + right >= 1.0 or \
		   top < 0 or bottom < 0 or left < 0 or right < 0:
			raise error, 'bad crop size'
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		if coordinates is None:
			x, y, width, height = self._rect
		else:
			x, y, width, height = self._convert_coordinates(coordinates)
		if scale == 0:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -1:
			scale = max(float(width)/(xsize - left - right),
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
				return self._prepare_image(file, crop, oscale, center, coordinates)
			if hasattr(reader, 'transparent'):
				import imageop, imgformat
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
				import sys
				raise error, sys.exc_value
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
		# x -- left edge of window
		# y -- top edge of window
		# width -- width of window
		# height -- height of window
		# w -- width of image
		# h -- height of image
		# left, right, top, bottom -- part to be cropped
		if center:
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
		xim = tw._visual.CreateImage(tw._depth, X.ZPixmap, 0, image,
					     w, h, depth * 8, w * depth)
		return xim, mask, left, top, x, y, w - left - right, h - top - bottom

	def _destroy_callback(self, form, client_data, call_data):
		self._shell = None
		self.close()

	def _delete_callback(self, form, client_data, call_data):
		ToolTip.rmtt()
		self._arrowcache = {}
		w = toplevel._in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			w._rb_cancel()
			w._next_create_box[0:0] = next_create_box
		if not _CommandSupport._delete_callback(self, form,
							client_data, call_data):
			try:
				func, arg = self._callbacks[WindowExit]
			except KeyError:
				pass
			else:
				func(arg, self, WindowExit, None)
		if w:
			w._rb_end()
			self._rb_looping = 0
		toplevel.setready()

	def _input_callback(self, form, client_data, call_data):
		ToolTip.rmtt()
		if self._parent is None:
			return		# already closed
		if toplevel._in_create_box:
			return
		try:
			self._do_input_callback(form, client_data, call_data)
		except Continue:
			pass
		toplevel.setready()

	def _do_input_callback(self, form, client_data, call_data):
		event = call_data.event
		x, y = event.x, event.y
		for w in self._subwindows:
			if w._region.PointInRegion(x, y):
				try:
					w._do_input_callback(form, client_data, call_data)
				except Continue:
					pass
				else:
					return
		# not in a subwindow, handle it ourselves
		if event.type == X.KeyPress:
			string = Xlib.LookupString(event)[0]
			win = self
			while win is not toplevel:
				if win._accelerators.has_key(string):
					apply(apply, win._accelerators[string])
					return
				win = win._parent
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
					elif self._popupmenu:
						self._popupmenu.MenuPosition(event)
						self._popupmenu.ManageChild()
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
## 		print 'expose',`self`,e.x,e.y,e.width,e.height,e.count
		# collect redraw regions
		self._exp_reg.UnionRectWithRegion(e.x, e.y, e.width, e.height)
		if e.count == 0:
			# last of a series, do the redraw
			r = self._exp_reg
			self._exp_reg = Xlib.CreateRegion()
			pm = self._pixmap
			if pm is None:
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
			if w._transparent == 0 or \
			   (w._transparent == -1 and w._active_displist):
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
			elif self._transparent == 0 or self._topwindow is self:
				gc = self._gc
				gc.SetRegion(r)
				gc.foreground = self._convert_color(self._bgcolor)
				apply(gc.FillRectangle, self._rect)
			if self._redrawfunc:
				self._gc.SetRegion(r)
				self._redrawfunc()
		# finally draw transparent subwindow, bottom-most first
		sw = self._subwindows[:]
		sw.reverse()
		for w in sw:
			if w._transparent == 1 or \
			   (w._transparent == -1 and not w._active_displist):
				w._do_expose(region, 1)
		if self._showing:
			self.showwindow(self._showing)

	def _scr_resize_callback(self, w, form, call_data):
		ToolTip.rmtt()
		if self.is_closed():
			return
		width = max(self._form.width, w.width)
		height = max(self._form.height, w.height)
		self._form.SetValues({'width': width, 'height': height})

	def _resize_callback(self, form, client_data, call_data):
		ToolTip.rmtt()
		val = self._form.GetValues(['width', 'height'])
		x, y = self._rect[:2]
		width, height = val['width'], val['height']
		if self._rect == (x, y, width, height):
			return
		self._arrowcache = {}
		__w = toplevel._in_create_box
		if __w:
			next_create_box = __w._next_create_box
			__w._next_create_box = []
			__w._rb_cancel()
			__w._next_create_box[0:0] = next_create_box
		self._rect = x, y, width, height
		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		# convert pixels to mm
		parent = self._parent
		w = float(width) / toplevel._hmm2pxl
		h = float(height) / toplevel._vmm2pxl
		if self._pixmap is None:
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
		if pixmap is not None:
			gc.SetRegion(self._region)
			pixmap.CopyArea(form, gc, 0, 0, width, height, 0, 0)
		# call resize callbacks
		self._do_resize2()
		if __w:
			__w._rb_end()
			self._rb_looping = 0
		toplevel.setready()

	def _do_resize2(self):
		for w in self._subwindows:
			w._do_resize2()
		try:
			func, arg = self._callbacks[ResizeWindow]
		except KeyError:
			pass
		else:
			func(arg, self, ResizeWindow, None)

	def _motion_handler(self, form, client_data, event):
		x, y = self._curpos = event.x, event.y
		if self._buttonregion.PointInRegion(x, y):
			cursor = 'hand'
		else:
			cursor = self._cursor
		if self._curcursor != cursor:
			self.setcursor(cursor)

	# supporting methods for create_box
	def _rb_finish(self):
		toplevel._in_create_box = None
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
		form.AddEventHandler(X.PointerMotionMask, FALSE,
					self._motion_handler, None)
		self._rb_dialog.close()
		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		self._rb_display.close()
		self._rb_curdisp.close()
		for win in toplevel._subwindows:
			if win is self._topwindow:
				continue
			if hasattr(win, '_shell'):
				win._shell.SetSensitive(1)
			elif hasattr(win, '_main'):
				win._main.SetSensitive(1)
		toplevel.setcursor('')
		del self._rb_callback
		del self._rb_dialog
		del self._rb_dl
		del self._rb_display
		del self._gc_rb

	def _rb_cvbox(self, units = UNIT_SCREEN):
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
		if units == UNIT_SCREEN:
			return float(x0 - x) / (width - 1), \
			       float(y0 - y) / (height - 1), \
			       float(x1 - x0) / (width - 1), \
			       float(y1 - y0) / (height - 1)
		elif units == UNIT_PXL:
			return x0 - x, y0 - y, x1 - x0, y1 - y0
		elif units == UNIT_MM:
			return float(x0 - x) / toplevel._hmm2pxl, \
			       float(y0 - y) / toplevel._vmm2pxl, \
			       float(x1 - x0) / toplevel._hmm2pxl, \
			       float(y1 - y0) / topevel._vmm2pxl
		else:
			raise error, 'bad units specified'

	def _rb_done(self):
		callback = self._rb_callback
		units = self._rb_units
		self._rb_finish()
		apply(callback, self._rb_cvbox(units))
		self._rb_end()
		self._rb_looping = 0

	def _rb_cancel(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())
		self._rb_end()
		self._rb_looping = 0

	def _rb_end(self):
		# execute pending create_box calls
		next_create_box = self._next_create_box
		self._next_create_box = []
		for win, msg, cb, box, units in next_create_box:
			win.create_box(msg, cb, box, units)

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

class _SubWindow(_Window):
	def __init__(self, parent, coordinates, defcmap, pixmap, transparent, z, units):
		if z < 0:
			raise error, 'invalid z argument'
		self._z = z
		x, y, w, h = parent._convert_coordinates(coordinates, crop = 1, units = units)
		self._rect = x, y, w, h
		self._sizes = parent._pxl2rel(self._rect)
		if w == 0 or h == 0:
			showmessage('Creating subwindow with zero dimension',
				    mtype = 'warning', parent = parent)

		self._convert_color = parent._convert_color
		for i in range(len(parent._subwindows)):
			if self._z >= parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)
		self._do_init(parent)
		self._motion_handler = parent._motion_handler
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			if transparent not in (-1, 0, 1):
				raise error, 'invalid value for transparent arg'
			self._transparent = transparent
		self._topwindow = parent._topwindow

		self._form = parent._form
		self._gc = parent._gc
		self._visual = parent._visual
		self._colormap = parent._colormap
		self._pixmap = parent._pixmap

		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		parent._mkclip()
		if self._transparent == 0:
			self._do_expose(self._region)
			if self._pixmap is not None:
				x, y, w, h = self._rect
				self._gc.SetRegion(self._region)
				self._pixmap.CopyArea(self._form, self._gc,
						      x, y, w, h, x, y)

	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)

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
		if self._pixmap is not None:
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
		del self._motion_handler
		del self._arrowcache

	def settitle(self, title):
		raise error, 'can only settitle at top-level'

	def getgeometry(self, units = UNIT_SCREEN):
		if units == UNIT_PXL:
			return self._rect
		elif units == UNIT_SCREEN:
			return self._sizes
		elif units == UNIT_MM:
			x, y, w, h = self._rect
			return float(x) / toplevel._hmm2pxl, \
			       float(y) / toplevel._vmm2pxl, \
			       float(w) / toplevel._hmm2pxl, \
			       float(h) / toplevel._vmm2pxl
		raise error, 'bad units specified'

	def setcursor(self, cursor):
		pass

	def pop(self):
		parent = self._parent
		# put self in front of all siblings with equal or lower z
		if self is not parent._subwindows[0]:
			parent._subwindows.remove(self)
			for i in range(len(parent._subwindows)):
				if self._z >= parent._subwindows[i]._z:
					parent._subwindows.insert(i, self)
					break
			else:
				parent._subwindows.append(self)
			# recalculate clipping regions
			parent._mkclip()
			# draw the window's contents
			if self._transparent == 0 or self._active_displist:
				self._do_expose(self._region)
				if self._pixmap is not None:
					x, y, w, h = self._rect
					self._gc.SetRegion(self._region)
					self._pixmap.CopyArea(self._form,
							      self._gc,
							      x, y, w, h, x, y)
		parent.pop()

	def push(self):
		parent = self._parent
		# put self behind all siblings with equal or higher z
		if self is parent._subwindows[-1]:
			# already at the end
			return
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)-1,-1,-1):
			if self._z <= parent._subwindows[i]._z:
				parent._subwindows.insert(i+1, self)
				break
		else:
			parent._subwindows.insert(0, self)
		# recalculate clipping regions
		parent._mkclip()
		# draw exposed windows
		for w in self._parent._subwindows:
			if w is not self:
				w._do_expose(self._region)
		if self._pixmap is not None:
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
		self._parent._delclip(self, self._clip)

	def _delclip(self, child, region):
		_Window._delclip(self, child, region)
		self._parent._delclip(self, region)

	def _do_resize1(self):
		# calculate new size of subwindow after resize
		# close all display lists
		parent = self._parent
		self._pixmap = parent._pixmap
		self._gc = parent._gc
		x, y, w, h = parent._convert_coordinates(self._sizes, crop = 1)
		self._rect = x, y, w, h
		w, h = self._sizes[2:]
		if w == 0:
			w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
		if h == 0:
			h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		self._active_displist = None
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._do_resize1()
