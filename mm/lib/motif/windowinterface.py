__version__ = "$Id$"

import Xt, Xm, Xmd, Xlib, X, Xcursorfont
import string, sys
import math
import img

import splash
error = splash.error

Continue = 'Continue'

FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2
SINGLE, HTM, TEXT, MPEG = 0, 1, 2, 3

UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2

RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH = 0, 1, 2

Version = 'X'

_WAITING_CURSOR = '_callback'
_READY_CURSOR = '_endcallback'

toplevel = None

_def_useGadget = 1			# whether to use gadgets or not

from types import *
from WMEVENTS import *
r = Xlib.CreateRegion()
RegionType = type(r)
del r

[_X, _Y, _WIDTH, _HEIGHT] = range(4)

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""
_in_create_box = None

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

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
		raise AttributeError(attr)

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
		items = splash.init()
		for key, val in items:
			setattr(self, '_' + key, val)
		dpy = self._dpy
		main = self._main
		self._delete_window = dpy.InternAtom('WM_DELETE_WINDOW', FALSE)
		self._default_colormap = main.DefaultColormapOfScreen()
		self._default_visual = main.DefaultVisualOfScreen()
## 		self._default_colormap = self._colormap
## 		self._default_visual = self._visual
		self._mscreenwidth = main.WidthMMOfScreen()
		self._mscreenheight = main.HeightMMOfScreen()
		self._screenwidth = main.WidthOfScreen()
		self._screenheight = main.HeightOfScreen()
		self._hmm2pxl = float(self._screenwidth) / self._mscreenwidth
		self._vmm2pxl = float(self._screenheight) / self._mscreenheight
		self._dpi_x = int(25.4 * self._hmm2pxl + .5)
		self._dpi_y = int(25.4 * self._vmm2pxl + .5)
		self._handcursor = dpy.CreateFontCursor(Xcursorfont.hand2)
		self._watchcursor = dpy.CreateFontCursor(Xcursorfont.watch)
		self._channelcursor = dpy.CreateFontCursor(Xcursorfont.draped_box)
		self._linkcursor = dpy.CreateFontCursor(Xcursorfont.hand1)
		self._stopcursor = dpy.CreateFontCursor(Xcursorfont.pirate)
		main.RealizeWidget()

	def close(self):
		for cb in self._closecallbacks:
			apply(apply, cb)
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

	def newwindow(self, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1):
		return _Window(self, x, y, w, h, title, 0, pixmap, units,
			       adornments, canvassize, commandlist, resizable)

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE,
			type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
			adornments = None, canvassize = None,
			commandlist = None, resizable = 1):
		return _Window(self, x, y, w, h, title, 1, pixmap, units,
			       adornments, canvassize, commandlist, resizable)

##	__waiting = 0
	def setwaiting(self):
##		if self.__waiting:
##			return
##		self.__waiting = 1
		self.setcursor(_WAITING_CURSOR)

	def setready(self):
##		if not self.__waiting:
##			return
##		self.__waiting = 0
		self.setcursor(_READY_CURSOR)

	def setcursor(self, cursor):
		if cursor == 'watch' or cursor == '': return # XXXX
		for win in self._subwindows:
			win.setcursor(cursor)
		if cursor != _WAITING_CURSOR and cursor != _READY_CURSOR:
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
		id = _Timer()
		tid = Xt.AddTimeOut(int(sec * 1000), id.cb, cb)
		id.set(tid)
		return id

	def canceltimer(self, id):
		if id is not None:
			tid = id.get()
			if tid is not None:
				Xt.RemoveTimeOut(tid)
			else:
				print 'canceltimer of bad timer'
			id.destroy()

	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		import Xtdefs
		if type(fd) is not IntType:
			fd = fd.fileno()
		if self._fdiddict.has_key(fd):
			id = self._fdiddict[fd]
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
		apply(apply, client_data)

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

	def getscreensize(self):
		"""Return screen size in pixels"""
		return self._screenwidth, self._screenheight

	def getsize(self):
		return toplevel._mscreenwidth, toplevel._mscreenheight

	def getscreendepth(self):
		"""Return screen depth"""
		return self._visual.depth

class _Timer:
	def set(self, id):
		self.__id = id

	def get(self):
		return self.__id

	def destroy(self):
		self.__id = None

	def cb(self, client_data, id):
		self.__id = None
		apply(apply, client_data)
		toplevel.setready()

class _ToolTip:
	__popupwidget = None

	def __init__(self):
		self.__tid = None
		self.__tooltips = {}

	def close(self):
		self.__rmtt()
		del self.__tooltips

	def _addtthandler(self, widget, tooltip):
		self._deltthandler(widget)
		widget.AddEventHandler(X.EnterWindowMask|X.LeaveWindowMask, 0,
				       self.__tooltipeh, tooltip)
		self.__tooltips[widget] = tooltip
		for w in widget.children or []:
			if not w.IsSubclass(Xm.Gadget):
				self._addtthandler(w, tooltip)

	def _deltthandler(self, widget):
		self.__rmtt(widget)
		tt = self.__tooltips.get(widget)
		if tt is None:
			return
		del self.__tooltips[widget]
		widget.RemoveEventHandler(X.EnterWindowMask|X.LeaveWindowMask,
					  0, self.__tooltipeh, tt)

	def __rmtt(self, widget = None):
		if _ToolTip.__popupwidget is not None:
			popup, w = _ToolTip.__popupwidget
			if widget is None or w is widget:
				_ToolTip.__popupwidget = None
				popup.Popdown()
				popup.DestroyWidget()

	def __tooltipeh(self, widget, tooltip, event):
		if self.__tid is not None:
			Xt.RemoveTimeOut(self.__tid)
			self.__tid = None
		self.__rmtt()
		if event.type == X.EnterNotify:
			self.__tid = Xt.AddTimeOut(500, self.__tooltipto,
						   (tooltip, widget))

	def __tooltipto(self, (tooltip, widget), id):
		self.__tid = None
		try:
			x, y = widget.TranslateCoords(0, 0)
		except:
			# maybe widget was already destroyed
			return
		if not widget.IsRealized() or not widget.IsManaged():
			# widget not visible so don't display tooltip
			return
		if callable(tooltip):
			tooltip = tooltip()
		elif type(tooltip) is type(()):
			tooltip = apply(apply, tooltip)
		# else assume string
		popup = widget.CreatePopupShell('help_popup', Xt.OverrideShell,
				{'visual': toplevel._default_visual,
				 'colormap': toplevel._default_colormap,
				 'depth': toplevel._default_visual.depth})
		_ToolTip.__popupwidget = popup, widget
		label = popup.CreateManagedWidget('help_label', Xm.Label,
						  {'labelString': tooltip})
		# figure out placement
		val = widget.GetValues(['width', 'height'])
		w = val['width']
		h = val['height']
		# place below center of widget
		x = x+w/2
		y = y+h+5
		# see if it fits there
		val = label.GetValues(['width', 'height'])
		width = val['width']
		height = val['height']
		if x + width > toplevel._screenwidth:
			# too wide: extend to the left
			x = x - width
		if y + height > toplevel._screenheight:
			# too hight: place above widget
			y = y - h - 10 - height
		popup.SetValues({'x': x, 'y': y})
		popup.Popup(0)

class _CommandSupport(_ToolTip):
	def __init__(self):
		self.__commandlist = []	# list of currently valid command insts
		self.__commanddict = {}	# mapping of command class to instance
		self.__widgetmap = {}	# mapping of command to list of widgets
		self.__accelmap = {}	# mapping of command to list of keys
		self.__togglelables = {}
		self.__delete_commands = []
		_ToolTip.__init__(self)

	def close(self):
		del self.__commandlist
		del self.__commanddict
		del self.__widgetmap
		del self.__accelmap
		del self.__togglelables
		del self.__delete_commands
		_ToolTip.close(self)

	def set_commandlist(self, list):
		oldlist = self.__commandlist
		olddict = self.__commanddict
		newlist = []
		newdict = {}
		for cmd in list:
			c = cmd.__class__
			newlist.append(c)
			newdict[c] = cmd
		if newlist != oldlist:
			# there are changes...
			# first remove old commands
			for c in oldlist:
				if not newdict.has_key(c):
					for w in self.__widgetmap.get(c, []):
						w.SetSensitive(0)
						self._deltthandler(w)
			# then add new commands
			for cmd in list:
				c = cmd.__class__
				if not olddict.has_key(c):
					for w in self.__widgetmap.get(c, []):
						w.SetSensitive(1)
						if cmd.help:
							self._addtthandler(w, cmd.help)
		# reassign callbacks for accelerators
		for c in oldlist:
			for key in self.__accelmap.get(c, []):
				del self._accelerators[key]
		for cmd in list:
			for key in self.__accelmap.get(cmd.__class__, []):
				self._accelerators[key] = cmd.callback
		self.__commandlist = newlist
		self.__commanddict = newdict

	def set_toggle(self, command, onoff):
		for widget in self.__widgetmap.get(command, []):
			if widget.ToggleButtonGetState() != onoff:
				widget.ToggleButtonSetState(onoff, 0)
				label = self.__togglelables.get(widget)
				if label is not None:
					widget.labelString = label[onoff]

	def __callback(self, widget, callback, call_data):
		if type(callback) is ClassType:
			callback = self.__commanddict.get(callback)
			if callback is not None:
				callback = callback.callback
		label = self.__togglelables.get(widget)
		if label is not None:
			widget.labelString = label[widget.ToggleButtonGetState()]
		if callback is not None:
			apply(apply, callback)
			toplevel.setready()

	def _set_callback(self, widget, callbacktype, callback):
		if callbacktype:
			widget.AddCallback(callbacktype, self.__callback,
					   callback)
		if type(callback) is ClassType:
			if not self.__widgetmap.has_key(callback):
				self.__widgetmap[callback] = []
			self.__widgetmap[callback].append(widget)

	def _delete_callback(self, widget, client_data, call_data):
		for c in self.__delete_commands:
			cmd = self.__commanddict.get(c)
			if cmd is not None and cmd.callback is not None:
				apply(apply, cmd.callback)
				return 1
		return 0

	def _set_deletecommands(self, deletecommands):
		self.__delete_commands = deletecommands

	def _set_togglelabels(self, widget, labels):
		self.__togglelables[widget] = labels
		widget.labelString = labels[widget.ToggleButtonGetState()]
		widget.inidcatorOn = 0
		widget.fillOnSelect = 0

	def _get_acceleratortext(self, callback):
		if self.__accelmap.has_key(callback):
			return string.join(self.__accelmap[callback], '|')

	def _get_commandinstance(self, command):
		return self.__commanddict.get(command)

	def _get_commandwidgets(self, command):
		return self.__widgetmap.get(command, [])

	def _create_shortcuts(self, shortcuts):
		for key, c in shortcuts.items():
			if not self.__accelmap.has_key(c):
				self.__accelmap[c] = []
			self.__accelmap[c].append(key)

class _ButtonSupport:
	# helper class to create a button
	# this class calls three methods that are not defined here:
	# _get_acceleratortext, _set_callback, and _set_togglelabels.

	__pixmapcache = {}
	__pixmaptypes = (
		'label',
		'labelInsensitive',
		'select',
		'selectInsensitive',
		'arm',
		)

	def _create_button(self, parent, visual, colormap, entry, extra_callback = None):
		btype = 'p'
		initial = 0
		if type(entry) is TupleType:
			label, callback = entry[:2]
			if len(entry) > 2:
				btype = entry[2]
				if type(btype) is TupleType:
					btype, initial = btype
		else:
			label, callback = entry, None
		if btype == 't':
			widgettype = Xm.ToggleButton
			callbacktype = 'valueChangedCallback'
			attrs = {'set': initial}
			if type(label) is DictType and label.has_key('select'):
				attrs['indicatorOn'] = 0
		else:
			widgettype = Xm.PushButton
			callbacktype = 'activateCallback'
			attrs = {}
		if type(callback) is ClassType:
			attrs['sensitive'] = 0
			acceleratorText = self._get_acceleratortext(callback)
			if acceleratorText:
				attrs['acceleratorText'] = acceleratorText
		button = parent.CreateManagedWidget('button', widgettype, attrs)
		if callback is not None:
			if type(callback) not in (ClassType, TupleType):
				callback = callback, (label,)
			self._set_callback(button, callbacktype, callback)
		if extra_callback is not None:
			self._set_callback(button, callbacktype, extra_callback)
		if type(label) is StringType:
			button.labelString = label
			return button
		if type(label) is TupleType:
			if btype != 't' or len(label) != 2:
				raise error, 'bad label for menu button'
			self._set_togglelabels(button, label)
			return button
		attrs = {'labelType': Xmd.PIXMAP,
			 'marginHeight': 0,
			 'marginWidth': 0}
		import imgconvert
		depth = toplevel._imgformat.descr['align'] / 8
		# calculate background RGB values in case (some)
		# images are transparent
		bg = button.background
		if visual.c_class == X.PseudoColor:
			r, g, b = colormap.QueryColor(bg)[1:4]
		else:
			s, m = splash._colormask(visual.red_mask)
			r = int(float((bg >> s) & m) / (m+1) * 256)
			s, m = splash._colormask(visual.green_mask)
			g = int(float((bg >> s) & m) / (m+1) * 256)
			s, m = splash._colormask(visual.blue_mask)
			b = int(float((bg >> s) & m) / (m+1) * 256)
		for pmtype in self.__pixmaptypes:
			rdr = label.get(pmtype)
			if rdr is None:
				continue
			if self.__pixmapcache.has_key(rdr):
				pixmap = self.__pixmapcache[rdr]
			else:
				rdr = imgconvert.stackreader(toplevel._imgformat, rdr)
				if hasattr(rdr, 'transparent'):
					rdr.colormap[rdr.transparent] = r, g, b
				data = rdr.read()
				pixmap = toplevel._main.CreatePixmap(rdr.width,
								     rdr.height)
				ximage = visual.CreateImage(
					visual.depth, X.ZPixmap, 0, data,
					rdr.width, rdr.height,
					depth * 8, rdr.width * depth)
				pixmap.CreateGC({}).PutImage(ximage, 0, 0, 0, 0,
							     rdr.width, rdr.height)
				self.__pixmapcache[label[pmtype]] = pixmap
			attrs[pmtype + 'Pixmap'] = pixmap
		button.SetValues(attrs)
		return button

class _AdornmentSupport(_CommandSupport, _ButtonSupport):
	def __init__(self):
		_CommandSupport.__init__(self)
		self.__dynamicmenu = {}

	def close(self):
		_CommandSupport.close(self)
		del self.__dynamicmenu

	def set_dynamiclist(self, command, list):
		cmd = self._get_commandinstance(command)
		if cmd is None:
			return
		if not cmd.dynamiccascade:
			raise error, 'non-dynamic command in set_dynamiclist'
		callback = cmd.callback
		menu = []
		for entry in list:
			entry = (entry[0], (callback, entry[1])) + entry[2:]
			menu.append(entry)
		for widget in self._get_commandwidgets(command):
			if self.__dynamicmenu.get(widget) == menu:
				continue
			submenu = widget.subMenuId
			for w in submenu.children or []:
				w.DestroyWidget()
			if not list:
				if widget.sensitive:
					widget.SetSensitive(0)
				continue
			if not widget.sensitive:
				widget.SetSensitive(1)
			_create_menu(submenu, menu,
				     toplevel._default_visual,
				     toplevel._default_colormap)
			self.__dynamicmenu[widget] = menu

	def _create_menu(self, menu, list):
		if len(list) > 30:
			menu.numColumns = (len(list) + 29) / 30
			menu.packing = Xmd.PACK_COLUMN
		for entry in list:
			if entry is None:
				dummy = menu.CreateManagedWidget('separator',
						 Xm.SeparatorGadget, {})
				continue
## 			if type(entry) is StringType:
## 				dummy = menu.CreateManagedWidget(
## 					'menuLabel', Xm.Label,
## 					{'labelString': entry})
## 				continue
			label, callback = entry[:2]
			if type(callback) is ListType or \
			   callback.dynamiccascade:
				submenu = menu.CreatePulldownMenu('submenu',
					{'colormap': toplevel._default_colormap,
					 'visual': toplevel._default_visual,
					 'depth': toplevel._default_visual.depth,
					 'orientation': Xmd.VERTICAL,
					 'tearOffModel': Xmd.TEAR_OFF_ENABLED})
				button = menu.CreateManagedWidget(
					'submenuLabel', Xm.CascadeButton,
					{'labelString': label,
					 'subMenuId': submenu})
				if label == 'Help':
					menu.menuHelpWidget = button
				if type(callback) is ListType:
					self._create_menu(submenu, callback)
				else:
					button.SetSensitive(0)
					self._set_callback(button, None, callback)
			else:
				button = self._create_button(menu,
					self._visual, self._colormap, entry)

	def _create_toolbar(self, tb, list, vertical):
		for entry in list:
			if entry is None:
				if vertical:
					orientation = Xmd.HORIZONTAL
				else:
					orientation = Xmd.VERTICAL
				dummy = tb.CreateManagedWidget(
					'tbSeparator',
					Xm.SeparatorGadget,
					{'orientation': orientation})
				continue
			button = self._create_button(tb, self._visual,
						     self._colormap, entry)

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
			mb = form.CreateMenuBar(
				'menubar',
				{'leftAttachment': Xmd.ATTACH_FORM,
				 'rightAttachment': Xmd.ATTACH_FORM,
				 'topAttachment': Xmd.ATTACH_FORM})
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
			attrs['width'] = width - spacing
			attrs['height'] = height - spacing
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
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
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
		self._menu = None
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
		sp = self._scrwin.spacing
		w = self._scrwin.width
		h = self._scrwin.height
		if code == RESET_CANVAS:
			self._form.SetValues({'width': w-sp, 'height': h-sp})
		elif code == DOUBLE_HEIGHT:
			attrs = {'height': self._form.height * 2}
			if self._clipcanvas.width == self._form.width:
				attrs['width'] = self._form.width - 27
			self._form.SetValues(attrs)
		elif code == DOUBLE_WIDTH:
			attrs = {'width': self._form.width * 2}
			if self._clipcanvas.height == self._form.height:
				attrs['height'] = self._form.height - 27
			self._form.SetValues(attrs)

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, 0, pixmap, transparent, z)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, 1, pixmap, transparent, z)

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

	def create_box(self, msg, callback, box = None):
		import Xcursorfont
		global _in_create_box
		if _in_create_box:
			_in_create_box._next_create_box.append((self, msg, callback, box))
			return
		if self.is_closed():
			apply(callback, ())
			return
		toplevel.setcursor('stop')
		self._topwindow.setcursor('')
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
			except img.error, arg:
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
		self._arrowcache = {}
		w = _in_create_box
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
		if self._parent is None:
			return		# already closed
		if _in_create_box:
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
		if self.is_closed():
			return
		width = max(self._form.width, w.width)
		height = max(self._form.height, w.height)
		self._form.SetValues({'width': width, 'height': height})

	def _resize_callback(self, form, client_data, call_data):
		self._arrowcache = {}
		__w = _in_create_box
		if __w:
			next_create_box = __w._next_create_box
			__w._next_create_box = []
			__w._rb_cancel()
			__w._next_create_box[0:0] = next_create_box
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

class _SubWindow(_Window):
	def __init__(self, parent, coordinates, defcmap, pixmap, transparent, z):
		if z < 0:
			raise error, 'invalid z argument'
		self._z = z
		x, y, w, h = parent._convert_coordinates(coordinates, crop = 1)
		self._rect = x, y, w, h
		self._sizes = coordinates
		x, y, w, h = coordinates
		if w == 0 or h == 0:
			showmessage('Creating subwindow with zero dimension',
				    mtype = 'warning', parent = parent)
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

	def getgeometry(self, units = UNIT_MM):
		return self._sizes

	def setcursor(self, cursor):
		pass
## 		self._cursor = cursor
## 		if cursor == '' and self._curpos is not None and \
## 		   apply(self._buttonregion.PointInRegion, self._curpos):
## 			cursor = 'hand'
## 		_setcursor(self._form, cursor)
## 		self._curcursor = cursor

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
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
		self._region = Xlib.CreateRegion()
		apply(self._region.UnionRectWithRegion, self._rect)
		self._active_displist = None
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._do_resize1()

class _DisplayList:
	def __init__(self, window, bgcolor):
		self._window = window
		window._displists.append(self)
		self._buttons = []
		self._buttonregion = Xlib.CreateRegion()
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._linewidth = 1
		self._gcattr = {'foreground': window._convert_color(self._fgcolor),
				'background': window._convert_color(bgcolor),
				'line_width': 1}
		self._list = []
		if window._transparent <= 0:
			self._list.append(('clear',
					self._window._convert_color(bgcolor)))
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
			win._buttonregion = Xlib.CreateRegion()
			r = win._region
			if win._transparent == -1 and win._parent is not None and \
			   win._topwindow is not win:
				win._parent._mkclip()
				win._parent._do_expose(r)
			else:
				win._do_expose(r)
			if win._pixmap is not None:
				x, y, w, h = win._rect
				win._gc.SetRegion(win._region)
				win._pixmap.CopyArea(win._form, win._gc,
						     x, y, w, h, x, y)
			if win._transparent == 0:
				w = win._parent
				while w is not None and w is not toplevel:
					w._buttonregion.SubtractRegion(
						win._clip)
					w = w._parent
			win._topwindow._setmotionhandler()
		del self._cloneof
		del self._optimdict
		del self._list
		del self._buttons
		del self._font
		del self._imagemask
		del self._buttonregion

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
			new._imagemask = self._imagemask
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def render(self):
		window = self._window
		if window._transparent == -1 and window._active_displist is None:
			window._active_displist = self
			window._parent._mkclip()
			window._active_displist = None
		for b in self._buttons:
			b._highlighted = 0
		region = window._clip
		# draw our bit
		self._render(region)
		# now draw transparent subwindows
		windows = window._subwindows[:]
		windows.reverse()
		for w in windows:
			if w._transparent and w._active_displist:
				w._do_expose(region, 1)
		# now draw transparent windows that lie on top of us
		if window._topwindow is not window:
			i = window._parent._subwindows.index(window)
			windows = window._parent._subwindows[:i]
			windows.reverse()
			for w in windows:
				if w._transparent and w._active_displist:
					w._do_expose(region, 1)
		# finally, re-highlight window
		if window._showing:
			window.showwindow(window._showing)
		if window._pixmap is not None:
			x, y, width, height = window._rect
			window._gc.SetRegion(window._clip)
			window._pixmap.CopyArea(window._form, window._gc,
						x, y, width, height, x, y)
		window._buttonregion = bregion = Xlib.CreateRegion()
		bregion.UnionRegion(self._buttonregion)
		bregion.IntersectRegion(window._clip)
		w = window._parent
		while w is not None and w is not toplevel:
			w._buttonregion.SubtractRegion(window._clip)
			w._buttonregion.UnionRegion(bregion)
			w = w._parent
		window._topwindow._setmotionhandler()
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
		gc = w._gc
		gc.ChangeGC(self._gcattr)
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
			gc.foreground = entry[1]
			apply(gc.FillRectangle, w._rect)
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
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			points = entry[3]
			x0, y0 = points[0]
			for x, y in points[1:]:
				gc.DrawLine(x0, y0, x, y)
				x0, y0 = x, y
		elif cmd == 'box':
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			apply(gc.DrawRectangle, entry[3])
		elif cmd == 'fbox':
			gc.foreground = entry[1]
			apply(gc.FillRectangle, entry[2])
		elif cmd == 'marker':
			gc.foreground = entry[1]
			x, y = entry[2]
			radius = 5 # XXXX
			gc.FillArc(x-radius, y-radius, 2*radius, 2*radius,
				   0, 360*64)
		elif cmd == 'text':
			gc.foreground = entry[1]
			gc.SetFont(entry[2])
			apply(gc.DrawString, entry[3:])
		elif cmd == 'fpolygon':
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

	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._fgcolor = color

	def linewidth(self, width):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._linewidth = width

	def newbutton(self, coordinates, z = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return _Button(self, coordinates, z)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0,
				    center = 1, coordinates = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       w._prepare_image(file, crop, scale, center, coordinates)
		if mask:
			self._imagemask = mask, src_x, src_y, dest_x, dest_y, width, height
		else:
			r = Xlib.CreateRegion()
			r.UnionRectWithRegion(dest_x, dest_y, width, height)
			self._imagemask = r
		self._list.append(('image', mask, image, src_x, src_y,
				   dest_x, dest_y, width, height))
		self._optimize((2,))
		x, y, w, h = w._rect
		return float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append(('line', w._convert_color(color),
				   self._linewidth, p))
		self._optimize((1,))

	def drawbox(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		self._list.append(('box', w._convert_color(self._fgcolor),
				   self._linewidth,
				   w._convert_coordinates(coordinates)))
		self._optimize((1,))

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		self._list.append(('fbox', w._convert_color(color),
				   w._convert_coordinates(coordinates)))
		self._optimize((1,))

	def drawmarker(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		self._list.append(('marker', w._convert_color(color),
				   w._convert_coordinates(coordinates)))

	def usefont(self, fontobj):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
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
			list.append('text', self._window._convert_color(self._fgcolor), self._font._font, x0, y0, str)
			self._optimize((1,))
			self._curpos = x + float(f.TextWidth(str)) / w._rect[_WIDTH], y
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, newy - oldy + height - base

	# Draw a string centered in a box, breaking lines if necessary
	def centerstring(self, left, top, right, bottom, str):
		fontheight = self.fontheight()
		baseline = self.baseline()
		width = right - left
		height = bottom - top
		curlines = [str]
		if height >= 2*fontheight:
			import StringStuff
			curlines = StringStuff.calclines([str], self.strsize, width)[0]
		nlines = len(curlines)
		needed = nlines * fontheight
		if nlines > 1 and needed > height:
			nlines = max(1, int(height / fontheight))
			curlines = curlines[:nlines]
			curlines[-1] = curlines[-1] + '...'
		x0 = (left + right) * 0.5	# x center of box
		y0 = (top + bottom) * 0.5	# y center of box
		y = y0 - nlines * fontheight * 0.5
		for i in range(nlines):
			str = string.strip(curlines[i])
			# Get font parameters:
			w = self.strsize(str)[0]	# Width of string
			while str and w > width:
				str = str[:-1]
				w = self.strsize(str)[0]
			x = x0 - 0.5*w
			y = y + baseline
			self.setpos(x, y)
			self.writestr(str)

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
		if not window._arrowcache.has_key((src,dst)):
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
			window._arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		nsx, nsy, ndx, ndy, points = window._arrowcache[(src,dst)]
		self._list.append(('arrow', color, self._linewidth,
				   (nsx, nsy, ndx, ndy), points))
		self._optimize((1,))

	def _optimize(self, ignore = ()):
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
	def __init__(self, dispobj, coordinates, z = 0):
		self._dispobj = dispobj
		self._z = z
		buttons = dispobj._buttons
		for i in range(len(buttons)):
			if buttons[i]._z <= z:
				buttons.insert(i, self)
				break
		else:
			buttons.append(self)
		window = dispobj._window
		self._coordinates = coordinates
		x, y, w, h = coordinates
		self._corners = x, y, x + w, y + h
		self._color = self._hicolor = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		self._newdispobj = None
		self._highlighted = 0
		x, y, w, h = window._convert_coordinates(coordinates)
		dispobj._buttonregion.UnionRectWithRegion(x, y, w, h)
		if self._color == dispobj._bgcolor:
			return
		dispobj.drawbox(coordinates)

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
		if window._pixmap is not None:
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
		if window._pixmap is not None:
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
	smsize = 9999			# something big
	smfont = None
	for font in fontlist:
		try:
			parsedfont = _parsefontname(font)
		except:
			# XXX catch parsing errors from the mac
			continue
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
		if p < smsize:
			smfont = font
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
		elif smfont is not None:
			# nothing smaller, so take next bigger
			thefont = font
			psize = smsize * 72.0 / toplevel._dpi_y
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
	_cursor = ''
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message', parent = None):
		if grab:
			dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
			if parent is None:
				parent = toplevel
			while 1:
				if hasattr(parent, '_shell'):
					parent = parent._shell
					break
				if hasattr(parent, '_main'):
					parent = parent._main
					break
				if hasattr(parent, '_parent'):
					parent = parent._parent
				else:
					parent = toplevel
		else:
			dialogStyle = Xmd.DIALOG_MODELESS
			parent = toplevel._main
		if mtype == 'error':
			func = parent.CreateErrorDialog
		elif mtype == 'warning':
			func = parent.CreateWarningDialog
		elif mtype == 'information':
			func = parent.CreateInformationDialog
		elif mtype == 'question':
			func = parent.CreateQuestionDialog
		else:
			func = parent.CreateMessageDialog
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
		self._main = w
		self.setcursor(_WAITING_CURSOR)
		toplevel._subwindows.append(self)
		if grab:
			toplevel.setready()
			while self._grab:
				Xt.DispatchEvent(Xt.NextEvent())

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			w = self._main
			self._main = None
			w.UnmanageChild()
			w.DestroyWidget()
		self._grab = 0

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		_setcursor(self._main, cursor)

	def is_closed(self):
		return self._main is None

	def _callback(self, widget, callback, call_data):
		if not self._main:
			return
		if _in_create_box and _in_create_box._rb_dialog is not self:
			return
		if callback:
			apply(apply, callback)
		if self._grab:
			self.close()
		toplevel.setready()

	def _destroy(self, widget, client_data, call_data):
		self._main = None

def beep():
	dpy = toplevel._main.Display()
	dpy.Bell(100)
	dpy.Flush()

def lopristarting():
	pass

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

def _generic_callback(widget, callback, call_data):
	apply(apply, callback)
	toplevel.setready()

def _create_menu(menu, list, visual, colormap, acc = None, widgets = {}):
	if len(list) > 30:
		menu.numColumns = (len(list) + 29) / 30
		menu.packing = Xmd.PACK_COLUMN
	if _def_useGadget:
		separator = Xm.SeparatorGadget
		label = Xm.LabelGadget
		cascade = Xm.CascadeButtonGadget
		toggle = Xm.ToggleButtonGadget
		pushbutton = Xm.PushButtonGadget
	else:
		separator = Xm.Separator
		label = Xm.Label
		cascade = Xm.CascadeButton
		toggle = Xm.ToggleButton
		pushbutton = Xm.PushButton
	accelerator = None
	for entry in list:
		if entry is None:
			dummy = menu.CreateManagedWidget('separator',
							 separator, {})
			continue
		if type(entry) is StringType:
			dummy = menu.CreateManagedWidget(
				'menuLabel', label,
				{'labelString': entry})
			widgets[entry] = dummy, None
			continue
		btype = 'p'		# default is pushbutton
		initial = 0
		if acc is None:
			labelString, callback = entry[:2]
			if len(entry) > 2:
				btype = entry[2]
				if len(entry) > 3:
					initial = entry[3]
		else:
			accelerator, labelString, callback = entry[:3]
			if len(entry) > 3:
				btype = entry[3]
				if len(entry) > 4:
					initial = entry[4]
		if type(callback) is ListType:
			submenu = menu.CreatePulldownMenu('submenu',
				{'colormap': colormap,
				 'visual': visual,
				 'depth': visual.depth,
				 'orientation': Xmd.VERTICAL,
				 'tearOffModel': Xmd.TEAR_OFF_ENABLED})
			button = menu.CreateManagedWidget(
				'submenuLabel', cascade,
				{'labelString': labelString, 'subMenuId': submenu})
			subwidgets = {}
			widgets[labelString] = button, subwidgets
			_create_menu(submenu, callback, visual, colormap, acc,
				     subwidgets)
		else:
			if type(callback) is not TupleType:
				callback = (callback, (labelString,))
			attrs = {'labelString': labelString}
			if accelerator:
				if type(accelerator) is not StringType or \
				   len(accelerator) != 1:
					raise error, 'menu accelerator must be single character'
				acc[accelerator] = callback
				attrs['acceleratorText'] = accelerator
			if btype == 't':
				attrs['set'] = initial
				button = menu.CreateManagedWidget('menuToggle',
						toggle, attrs)
				cbfunc = 'valueChangedCallback'
			else:
				button = menu.CreateManagedWidget('menuLabel',
						pushbutton, attrs)
				cbfunc = 'activateCallback'
			button.AddCallback(cbfunc, _generic_callback, callback)
			widgets[labelString] = button, None

def _setcursor(form, cursor):
	if not form.IsRealized():
		return
	if cursor == 'hand':
		form.DefineCursor(toplevel._handcursor)
	elif cursor == '':
		form.UndefineCursor()
	elif cursor == 'watch':
		form.DefineCursor(toplevel._watchcursor)
	elif cursor == 'channel':
		form.DefineCursor(toplevel._channelcursor)
	elif cursor == 'link':
		form.DefineCursor(toplevel._linkcursor)
	elif cursor == 'stop':
		form.DefineCursor(toplevel._stopcursor)
	else:
		raise error, 'unknown cursor glyph'

def roundi(x):
	if x < 0:
		return roundi(x + 1024) - 1024
	return int(x + 0.5)

class FileDialog:
	_cursor = ''
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel,
		     existing = 0, parent = None):
		import os
		self.cb_ok = cb_ok
		self.cb_cancel = cb_cancel
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth,
			 'width': 400}
		if parent is None:
			parent = toplevel
		while 1:
			if hasattr(parent, '_shell'):
				parent = parent._shell
				break
			if hasattr(parent, '_main'):
				parent = parent._main
				break
			parent = parent._parent
		if prompt:
			form = parent.CreateFormDialog('fileSelect', attrs)
			self._main = form
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
			dialog = parent.CreateFileSelectionDialog('fileSelect',
								  attrs)
			self._main = dialog
		self._dialog = dialog
		dialog.AddCallback('okCallback', self._ok_callback, existing)
		dialog.AddCallback('cancelCallback', self._cancel_callback,
				       None)
		self._main.Parent().AddWMProtocolCallback(
			toplevel._delete_window, self._cancel_callback, None)
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
		self._main.ManageChild()
		self.setcursor(_WAITING_CURSOR)
		toplevel._subwindows.append(self)

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			self._main.UnmanageChild()
			self._main.DestroyWidget()
			self._dialog = None
			self._main = None

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		_setcursor(self._main, cursor)

	def is_closed(self):
		return self._main is None

	def _cancel_callback(self, *rest):
		if _in_create_box or self.is_closed():
			return
		must_close = TRUE
		try:
			if self.cb_cancel:
				ret = self.cb_cancel()
				if ret:
					if type(ret) is StringType:
						showmessage(ret, parent = self)
					must_close = FALSE
					return
		finally:
			if must_close:
				self.close()
			toplevel.setready()

	def _ok_callback(self, widget, existing, call_data):
		if _in_create_box or self.is_closed():
			return
		self._do_ok_callback(widget, existing, call_data)
		toplevel.setready()

	def _do_ok_callback(self, widget, existing, call_data):
		import os
		filename = call_data.value
		dir = call_data.dir
		filter = call_data.pattern
		filename = os.path.join(dir, filename)
		if os.path.isdir(filename):
			filter = os.path.join(filename, filter)
			self._dialog.FileSelectionDoSearch(filter)
			return
		dir, file = os.path.split(filename)
		if not os.path.isdir(dir):
			showmessage("path to file `%s' does not exist or is not a directory" % filename, parent = self)
			return
		if existing:
			if not os.path.exists(filename):
				showmessage("file `%s' does not exist" % filename, parent = self)
				return
		else:
			if os.path.exists(filename):
				showmessage("file `%s' exists, use anyway?" % filename, mtype = 'question', callback = (self._confirm_callback, (filename,)), parent = self)
				return
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, parent = self)
				return
		self.close()

	def _confirm_callback(self, filename):
		if self.cb_ok:
			ret = self.cb_ok(filename)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, parent = self)
				return
		self.close()

class SelectionDialog:
	_cursor = ''
	def __init__(self, listprompt, selectionprompt, itemlist, default,
		     parent = None):
		attrs = {'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth,
			 'textString': default,
			 'autoUnmanage': FALSE}
		if parent is None:
			parent = toplevel
		while 1:
			if hasattr(parent, '_shell'):
				parent = parent._shell
				break
			if hasattr(parent, '_main'):
				parent = parent._main
				break
			parent = parent._parent
		if hasattr(self, 'NomatchCallback'):
			attrs['mustMatch'] = TRUE
		if listprompt:
			attrs['listLabelString'] = listprompt
		if selectionprompt:
			attrs['selectionLabelString'] = selectionprompt
		form = parent.CreateSelectionDialog('selectDialog', attrs)
		self._main = form
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
		self.setcursor(_WAITING_CURSOR)
		toplevel._subwindows.append(self)

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		_setcursor(self._main, cursor)

	def is_closed(self):
		return self._main is None

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			self._main.UnmanageChild()
			self._main.DestroyWidget()
			self._main = None

	def _nomatch_callback(self, widget, client_data, call_data):
		if _in_create_box or self.is_closed():
			return
		ret = self.NomatchCallback(call_data.value)
		if ret and type(ret) is StringType:
			showmessage(ret, mtype = 'error', parent = self)
		toplevel.setready()

	def _ok_callback(self, widget, client_data, call_data):
		if _in_create_box or self.is_closed():
			return
		try:
			func = self.OkCallback
		except AttributeError:
			pass
		else:
			ret = func(call_data.value)
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error',
						    parent = self)
				toplevel.setready()
				return
		self.close()
		toplevel.setready()

	def _cancel_callback(self, widget, client_data, call_data):
		if _in_create_box or self.is_closed():
			return
		try:
			func = self.CancelCallback
		except AttributeError:
			pass
		else:
			ret = func()
			if ret:
				if type(ret) is StringType:
					showmessage(ret, mtype = 'error',
						    parent = self)
				toplevel.setready()
				return
		self.close()
		toplevel.setready()


class InputDialog:
	_cursor = ''
	def __init__(self, prompt, default, cb, cancelCallback = None,
		     parent = None):
		import time
		attrs = {'textString': default or '',
			 'selectionLabelString': prompt or '',
			 'dialogStyle': Xmd.DIALOG_FULL_APPLICATION_MODAL,
			 'colormap': toplevel._default_colormap,
			 'visual': toplevel._default_visual,
			 'depth': toplevel._default_visual.depth}
		if parent is None:
			parent = toplevel._main
		else:
			while 1:
				if hasattr(parent, '_shell'):
					parent = parent._shell
					break
				elif hasattr(parent, '_main'):
					parent = parent._main
					break
				parent = parent._parent
		self._main = parent.CreatePromptDialog('inputDialog', attrs)
		self._main.AddCallback('okCallback', self._ok, cb)
		self._main.AddCallback('cancelCallback', self._cancel,
				       cancelCallback)
		self._main.Parent().AddWMProtocolCallback(
			toplevel._delete_window, self._cancel, cancelCallback)
		self._main.SelectionBoxGetChild(
			Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		self._main.ManageChild()
		if default:
			self._main.SelectionBoxGetChild(
				Xmd.DIALOG_TEXT).TextFieldSetSelection(
					0, len(default), 0)
		toplevel._subwindows.append(self)
		self.setcursor(_WAITING_CURSOR)

	def _ok(self, w, client_data, call_data):
		if _in_create_box or self.is_closed():
			return
		value = call_data.value
		self.close()
		if client_data:
			client_data(value)
			toplevel.setready()

	def _cancel(self, w, client_data, call_data):
		if _in_create_box or self.is_closed():
			return
		self.close()
		if client_data:
			apply(apply, client_data)
			toplevel.setready()

	def setcursor(self, cursor):
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		_setcursor(self._main, cursor)

	def close(self):
		if self._main:
			toplevel._subwindows.remove(self)
			self._main.UnmanageChild()
			self._main.DestroyWidget()
			self._main = None

	def is_closed(self):
		return self._main is None

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
		_create_menu(menu, list, toplevel._default_visual,
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
		if _in_create_box or not self._menu:
			return
		if call_data.button == X.Button3:
			self._menu.MenuPosition(call_data)
			self._menu.ManageChild()

	def _destroy(self):
		self._menu = None

class _Widget(_MenuSupport, _ToolTip):
	'''Support methods for all window objects.'''
	def __init__(self, parent, widget, tooltip = None):
		self._parent = parent
		parent._children.append(self)
		self._showing = TRUE
		self._form = widget
		widget.ManageChild()
		_MenuSupport.__init__(self)
		self._form.AddCallback('destroyCallback', self._destroy, None)
		_ToolTip.__init__(self)
		if tooltip is not None:
			self._addtthandler(widget, tooltip)

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

	def _get_acceleratortext(self, callback):
		return self._parent._get_acceleratortext(callback)

	def _set_callback(self, widget, callbacktype, callback):
		self._parent._set_callback(widget, callbacktype, callback)

	def _set_togglelabels(self, widget, labels):
		self._parent._set_togglelabels(widget, labels)

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
			widget = options.get(pos, ())
			if widget != ():
				if type(widget) in (FloatType, IntType):
					attrs[pos + 'Attachment'] = \
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
			offset = options.get(pos + 'Offset')
			if offset is None:
				offset = options.get('offset')
			if offset is not None:
				attrs[pos + 'Offset'] = offset

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
		     name = 'windowLabel', tooltip = None, **options):
		'''Create a Label subwindow.

		PARENT is the parent window, TEXT is the text for the
		label.  OPTIONS is an optional dictionary with
		options.  The only options recognized are the
		attachment options.'''
		attrs = {}
		self._attachments(attrs, options)
		if useGadget and tooltip is None:
			label = Xm.LabelGadget
		else:
			label = Xm.Label
		label = parent._form.CreateManagedWidget(name, label, attrs)
		label.labelString = text
		self._text = text
		_Widget.__init__(self, parent, label, tooltip)

	def __repr__(self):
		return '<Label instance at %x, text=%s>' % (id(self), self._text)

	def setlabel(self, text):
		'''Set the text of the label to TEXT.'''
		self._form.labelString = text
		self._text = text

class Button(_Widget):
	'''Button window object.'''
	def __init__(self, parent, label, callback, useGadget = _def_useGadget,
		     name = 'windowButton', tooltip = None, **options):
		'''Create a Button subwindow.

		PARENT is the parent window, LABEL is the label on the
		button, CALLBACK is the callback function that is
		called when the button is activated.  The callback is
		a tuple consiting of a callable object and an argument
		tuple.'''
		self.__text = label
		attrs = {'labelString': label}
		self._attachments(attrs, options)
		if useGadget and tooltip is None:
			button = Xm.PushButtonGadget
		else:
			button = Xm.PushButton
		button = parent._form.CreateManagedWidget(name, button, attrs)
		if callback:
			button.AddCallback('activateCallback',
					   self.__callback, callback)
		_Widget.__init__(self, parent, button, tooltip)

	def __repr__(self):
		return '<Button instance at %x, text=%s>' % (id(self), self.__text)

	def setlabel(self, text):
		self._form.labelString = text
		self.__text = text

	def setsensitive(self, sensitive):
		self._form.sensitive = sensitive

	def __callback(self, widget, callback, call_data):
		if _in_create_box or self.is_closed():
			return
		apply(apply, callback)
		toplevel.setready()

class OptionMenu(_Widget):
	'''Option menu window object.'''
	def __init__(self, parent, label, optionlist, startpos, cb,
		     useGadget = _def_useGadget, name = 'windowOptionMenu',
		     tooltip = None, **options):
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
		self._buttons = []
		self._optionlist = []
		self._value = -1
		menu = parent._form.CreatePulldownMenu('windowOption',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth,
				 'orientation': Xmd.VERTICAL})
		self._omenu = menu
		attrs = {'subMenuId': menu,
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
		_Widget.__init__(self, parent, option, tooltip)
		self.setoptions(optionlist, startpos)

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
		if 0 <= pos < len(self._optionlist):
			pass
		else:
			raise error, 'pos out of range'
		if self._optionlist[pos] is None:
			raise error, 'pos points to separator'
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

		if 0 <= startpos < len(optionlist):
			pass
		else:
			raise error, 'startpos out of range'
		if optionlist[startpos] is None:
			raise error, 'startpos points to separator'
		if optionlist != self._optionlist:
			menu = self._omenu
			for b in self._buttons:
				b.DestroyWidget()
			self._buttons = []
			if len(optionlist) > 30:
				menu.numColumns = (len(optionlist) + 29) / 30
				menu.packing = Xmd.PACK_COLUMN
			else:
				menu.numColumns = 1
				menu.packing = Xmd.PACK_TIGHT
			if self._useGadget:
				cbutton = menu.CreatePushButtonGadget
				cseparator = menu.CreateSeparatorGadget
			else:
				cbutton = menu.CreatePushButton
				cseparator = menu.CreateSeparator
			for i in range(len(optionlist)):
				item = optionlist[i]
				if item is None:
					button = cseparator(
						'windowOptionSeparator', {})
				else:
					button = cbutton('windowOptionButton',
							 {'labelString': item})
					button.AddCallback('activateCallback',
							   self._cb, i)
				button.ManageChild()
				self._buttons.append(button)
			self._optionlist = optionlist
		# set the start position
		self.setpos(startpos)

	def _cb(self, widget, value, call_data):
		if _in_create_box or self.is_closed():
			return
		self._value = value
		if self._callback:
			apply(apply, self._callback)
			toplevel.setready()

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
		widgets = []
		for item, list in menulist:
			menu = menubar.CreatePulldownMenu('windowMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
			button = menubar.CreateManagedWidget(
				'windowMenuButton', cascade,
				{'labelString': item,
				 'subMenuId': menu})
			widgets.append({})
			_create_menu(menu, list, toplevel._default_visual,
				     toplevel._default_colormap,
				     widgets = widgets[-1])
			buttons.append(button)
		_Widget.__init__(self, parent, menubar)
		self._buttons = buttons
		self._widgets = widgets

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
		widgets = {}
		_create_menu(menu, list, toplevel._default_visual,
			     toplevel._default_colormap, widgets = widgets)
		self._widgets[pos] = widgets
		omenu = button.subMenuId
		button.subMenuId = menu
		omenu.DestroyWidget()

	def setmenuentry(self, pos, path, onoff = None, sensitive = None):
		if not 0 <= pos < len(self._buttons):
			raise error, 'position out of range'
		dict = self._widgets[pos]
		for p in path:
			w = dict.get(p, (None, None))[0]
			while w is None:
				w = dict.get(p, (None, None))[0]
		if onoff is not None:
			w.set = onoff
		if sensitive is not None:
			w.sensitive = sensitive

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
			if len(sel_cb) >= 1 and sel_cb[0] is not None:
				list.AddCallback('singleSelectionCallback',
						 self._callback, sel_cb[0])
			if len(sel_cb) >= 2 and sel_cb[1] is not None:
				list.AddCallback('defaultActionCallback',
						 self._callback, sel_cb[1])
		elif sel_cb is not None:
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
		self._list.ListSelectPos(pos + 1, 0)

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


	def _callback(self, w, callback, call_data):
		if _in_create_box or self.is_closed():
			return
		apply(apply, callback)
		toplevel.setready()

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
		txt = selection.SelectionBoxGetChild(Xmd.DIALOG_TEXT)
		self._text = txt
		if options.has_key('enterCallback'):
			cb = options['enterCallback']
			txt.AddCallback('activateCallback', self._callback, cb)
		if options.has_key('changeCallback'):
			cb = options['changeCallback']
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
		if hasattr(self._text, 'TextFieldGetString'):
			return self._text.TextFieldGetString()
		else:
			return self._text.TextGetString()

	def seteditable(self, editable):
		if hasattr(self._text, 'TextFieldSetEditable'):
			self._text.TextFieldSetEditable(editable)
		else:
			self._text.TextSetEditable(editable)

	def selectitem(self, pos):
		_List.selectitem(self, pos)
		pos = self.getselected()
		if pos is None:
			text = ''
		else:
			text = self.getlistitem(pos)
		self._text.TextFieldSetString(text)
		if text:
			self._text.TextFieldSetSelection(0, len(text), 0)

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		_List._destroy(self)

class List(_Widget, _List):
	def __init__(self, parent, listprompt, itemlist, sel_cb,
		     rows = 10, useGadget = _def_useGadget,
		     name = 'windowList', tooltip = None, **options):
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
		_Widget.__init__(self, parent, widget, tooltip)

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
		     modifyCB = None, tooltip = None, **options):
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
		editable = options.get('editable', 1)
		if not editable:
			attrs['editable'] = 0
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
		_Widget.__init__(self, parent, widget, tooltip)

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

	def _callback(self, w, callback, call_data):
		if _in_create_box or self.is_closed():
			return
		apply(apply, callback)
		toplevel.setready()

	def _modifyCB(self, w, func, call_data):
		if _in_create_box:
			return
		text = func(call_data.text)
		if text is not None:
			call_data.text = text
		toplevel.setready()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		try:
			del self._label
		except AttributeError:
			pass
		del self._text

class TextEdit(_Widget):
	def __init__(self, parent, inittext, cb, name = 'windowText',
		     tooltip = None, **options):
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
		_Widget.__init__(self, parent, text, tooltip)
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

	def _callback(self, w, callback, call_data):
		if _in_create_box or self.is_closed():
			return
		apply(apply, callback)
		toplevel.setready()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._linecache

class Separator(_Widget):
	def __init__(self, parent, useGadget = _def_useGadget,
		     name = 'windowSeparator', vertical = 0,
		     tooltip = None, **options):
		attrs = {}
		if vertical:
			attrs['orientation'] = Xmd.VERTICAL
		else:
			attrs['orientation'] = Xmd.HORIZONTAL
		self._attachments(attrs, options)
		if useGadget and tooltip is None:
			separator = Xm.SeparatorGadget
		else:
			separator = Xm.Separator
		separator = parent._form.CreateManagedWidget(name, separator,
							     attrs)
		_Widget.__init__(self, parent, separator, tooltip)

	def __repr__(self):
		return '<Separator instance at %x>' % id(self)

class ButtonRow(_Widget, _ButtonSupport):
	def __init__(self, parent, buttonlist,
		     vertical = 1, callback = None,
		     useGadget = _def_useGadget,
		     name = 'windowRowcolumn', **options):
		attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
			 'traversalOn': FALSE}
		if not vertical:
			attrs['orientation'] = Xmd.HORIZONTAL
		if options.get('tight', 0):
			attrs['packing'] = Xmd.PACK_COLUMN
		if useGadget:
			separator = Xm.SeparatorGadget
		else:
			separator = Xm.Separator
		self._attachments(attrs, options)
		rowcolumn = parent._form.CreateManagedWidget(name,
							Xm.RowColumn, attrs)
		_Widget.__init__(self, parent, rowcolumn)
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
			if type(entry) is TupleType and len(entry) > 3:
				entry = entry[0], entry[1], entry[2:]
			button = self._create_button(rowcolumn, toplevel.
				_default_visual, toplevel._default_colormap,
				entry, callback)
			self._buttons.append(button)

	def __repr__(self):
		return '<ButtonRow instance at %x>' % id(self)

	def close(self):
		_Widget.close(self)
		self._buttons = None

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

	def _popup(self, widget, submenu, call_data):
		submenu.ManageChild()

	def _destroy(self, widget, value, call_data):
		_Widget._destroy(self, widget, value, call_data)
		del self._buttons

class Slider(_Widget):
	def __init__(self, parent, prompt, minimum, initial, maximum, cb,
		     vertical = 0, showvalue = 1, name = 'windowScale',
		     tooltip = None, **options):
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
		_Widget.__init__(self, parent, scale, tooltip)

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
		if _in_create_box or self.is_closed():
			return
		apply(apply, callback)
		toplevel.setready()

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
		horizontalSpacing = options.get('horizontalSpacing')
		if horizontalSpacing is not None:
			attrs['horizontalSpacing'] = horizontalSpacing
		verticalSpacing = options.get('verticalSpacing')
		if verticalSpacing is not None:
			attrs['verticalSpacing'] = verticalSpacing
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

class Window(_WindowHelpers, _MenuSupport, _CommandSupport):
	_cursor = ''
	def __init__(self, title, resizable = 0, grab = 0,
		     Name = 'windowShell', Class = None, **options):
		_CommandSupport.__init__(self)
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
		width = options.get('width')
		if width is not None:
			wattrs['width'] = int(float(width) * toplevel._hmm2pxl + 0.5)
		height = options.get('height')
		if height is not None:
			wattrs['height'] = int(float(height) * toplevel._vmm2pxl + 0.5)
		x = options.get('x')
		y = options.get('y')
		if x is not None and y is not None:
			wattrs['geometry'] = '+%d+%d' % (int(float(x) * toplevel._hmm2pxl + 0.5), int(float(y) * toplevel._vmm2pxl + 0.5))
		attrs = {'allowOverlap': FALSE,
			 'resizePolicy': self.resizePolicy}
		if not resizable:
			attrs['noResize'] = TRUE
			attrs['resizable'] = FALSE
		horizontalSpacing = options.get('horizontalSpacing')
		if horizontalSpacing is not None:
			attrs['horizontalSpacing'] = horizontalSpacing
		verticalSpacing = options.get('verticalSpacing')
		if verticalSpacing is not None:
			attrs['verticalSpacing'] = verticalSpacing
		if grab:
			attrs['dialogStyle'] = \
					     Xmd.DIALOG_FULL_APPLICATION_MODAL
			parent = options.get('parent', toplevel)
			if parent is None:
				parent = toplevel
			while 1:
				if hasattr(parent, '_shell'):
					parent = parent._shell
					break
				if hasattr(parent, '_main'):
					parent = parent._main
					break
				if hasattr(parent, '_parent'):
					parent = parent._parent
				else:
					parent = toplevel
			for key, val in wattrs.items():
				attrs[key] = val
			self._form = parent.CreateFormDialog('grabDialog', attrs)
			self._main = self._form
		else:
			wattrs['iconName'] = title
			self._shell = toplevel._main.CreatePopupShell(Name,
				Xt.ApplicationShell, wattrs)
			self._form = self._shell.CreateManagedWidget(
				'windowForm', Xm.Form, attrs)
			if options.has_key('deleteCallback'):
				deleteCallback = options['deleteCallback']
				if type(deleteCallback) is ListType:
					self._set_deletecommands(deleteCallback)
					deleteCallback = None
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
		self.setcursor(_WAITING_CURSOR)

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
		_CommandSupport.close(self)
		try:
			shell = self._shell
		except AttributeError:
			shell = None
			del self._main
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
		if cursor == _WAITING_CURSOR:
			cursor = 'watch'
		elif cursor == _READY_CURSOR:
			cursor = self._cursor
		else:
			self._cursor = cursor
		_setcursor(self._form, cursor)

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
		if not _CommandSupport._delete_callback(self, widget,
						client_data, call_data):
			apply(apply, client_data)
		toplevel.setready()

def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1,
	   parent = None):
	w = Window(title, grab = grab, parent = parent)
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

class _Question:
	def __init__(self, text, parent = None):
		self.looping = FALSE
		self.answer = None
		showmessage(text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)),
			    parent = parent)

	def run(self):
		self.looping = TRUE
		toplevel.setready()
		while self.looping:
			event = Xt.NextEvent()
			Xt.DispatchEvent(event)
		return self.answer

	def callback(self, answer):
		if _in_create_box:
			return
		self.answer = answer
		self.looping = FALSE

def showquestion(text, parent = None):
	return _Question(text, parent = parent).run()

class _MultChoice:
	def __init__(self, prompt, msg_list, defindex, parent = None):
		self.looping = FALSE
		self.answer = None
		self.msg_list = msg_list
		list = []
		for msg in msg_list:
			list.append(msg, (self.callback, (msg,)))
		self.dialog = Dialog(list, title = None, prompt = prompt,
				     grab = TRUE, vertical = FALSE,
				     parent = parent)

	def run(self):
		self.looping = TRUE
		toplevel.setready()
		while self.looping:
			event = Xt.NextEvent()
			Xt.DispatchEvent(event)
		return self.answer

	def callback(self, msg):
		if _in_create_box:
			return
		for i in range(len(self.msg_list)):
			if msg == self.msg_list[i]:
				self.answer = i
				self.looping = FALSE
				return

def multchoice(prompt, list, defindex, parent = None):
	return _MultChoice(prompt, list, defindex, parent = parent).run()

def textwindow(text):
	w = Window('Source', resizable = 1, deleteCallback = 'hide')
	b = w.ButtonRow([('Close', (w.hide, ()))],
			top = None, left = None, right = None,
			vertical = 0)
	t = w.TextEdit(text, None, editable = 0,
		       top = b, left = None, right = None,
		       bottom = None, rows = 30, columns = 80)
	w.show()
	return w

toplevel = _Toplevel()

newwindow = toplevel.newwindow

newcmwindow = toplevel.newcmwindow

close = toplevel.close

addclosecallback = toplevel.addclosecallback

setcursor = toplevel.setcursor

setwaiting = toplevel.setwaiting

getsize = toplevel.getsize

usewindowlock = toplevel.usewindowlock

settimer = toplevel.settimer

select_setcallback = toplevel.select_setcallback

mainloop = toplevel.mainloop

canceltimer = toplevel.canceltimer

getscreensize = toplevel.getscreensize

getscreendepth = toplevel.getscreendepth
