import Win
import Qd
import Dlg
import Ctl
import mac_image
import imgformat
import img
import imageop
import sys
import MenuTemplate
import usercmd

#
# Stuff we use from other mw_ modules
#
from WMEVENTS import *
import mw_globals
from mw_globals import error, Continue
from mw_globals import UNIT_MM, UNIT_SCREEN, UNIT_PXL
from mw_globals import RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH
from mw_globals import FALSE, TRUE
from mw_globals import _X, _Y, _WIDTH, _HEIGHT
import mw_displaylist
import mw_menucmd
import mw_widgets

#
# Cache for image sizes
#
_size_cache = {}

#
# Globals for create_box()
#
_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""
_rb_done = '_rb_done'			# exception to stop create_box loop
_in_create_box = None

class _WindowGroup:
	"""A windowgroup serves two purposes: it is an "invisible window",
	something that menu commands are attached to (which then become active
	if this group is active) and it is a grouping mechanism (each window
	belongs to a windowgroup). Together this has the effect of enabling
	the right commands for both the current, topmost, window and the
	document it belongs to"""
	
	def __init__(self, title, cmdlist):
		self._title = title
		self._cmds_toggled = {}
		self._dict = {}
		self.set_commandlist(cmdlist)
		
	def __repr__(self):
		return '<WindowGroup %s>'%self._title
	
	def settitle(self, title):
		self._title = title
		mw_globals.toplevel._changed_group_commands() # XXXX Is this good enough?
		
	def close(self):
		mw_globals.toplevel._close_windowgroup(self)
		del self._dict
		
	def pop(self):
		# NOTE: This method should only be called for groups, not windows
		mw_globals.toplevel._install_group_commands(self)
		
	def create_menu(self, menu, title):
		pass
		
	def set_dynamiclist(self, cmd, list):
		pass  # XXXX Not implemented yet.
		
	def set_toggle(self, cmd, onoff):
		self._cmds_toggled[cmd] = onoff
		mw_globals.toplevel._changed_group_commands()
		
	def get_toggle(self, cmd):
		if self._cmds_toggled.has_key(cmd):
			return self._cmds_toggled[cmd]
		return 0
		
	def toggle_toggle(self, cmd):
		old = self.get_toggle(cmd)
		self.set_toggle(cmd, not old)
		
	def _set_cmd_dict(self, dict):
		self._dict = dict
		mw_globals.toplevel._changed_group_commands()
		
	def set_commandlist(self, list):
		dict = {}
		for item in list:
			cmd = item.__class__
			if __debug__:
				if not mw_globals._all_commands.has_key(cmd):
					print 'Warning: user has no way to issue command', cmd
			dict[cmd] = item
		self._set_cmd_dict(dict)
		
	def has_command(self, cmd):
		return self._dict.has_key(cmd)
		
	def get_command_callback(self, cmd):
		if self._dict.has_key(cmd):
			return self._dict[cmd].callback
		return None

class _CommonWindow:
	"""Code common to toplevel window and subwindow"""
		
	def __init__(self, parent, wid, z=0):
		self._z = z
		for i in range(len(parent._subwindows)):
			if self._z >= parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)
		self._parent = parent
		self._wid = wid
		self._subwindows = []
		self._displists = []
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._clip = None
		self._active_displist = None
		self._eventhandlers = {}
		self._redrawfunc = None
		self._clickfunc = None
		self._accelerators = {}
		self._active_movie = 0
		
	def close(self):
		"""Close window and all subwindows"""
		if self._parent is None:
			return		# already closed
		self._set_movie_active(0)
		Qd.SetPort(self._wid)
		self._parent._subwindows.remove(self)
		Win.InvalRect(self.qdrect())
		self._parent._close_wid(self._wid)
		self._parent = None

		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		
		del self._subwindows
		del self._displists
		del self._parent
		del self._active_displist
		del self._eventhandlers
		del self._redrawfunc
		del self._clickfunc
		del self._wid
		del self._accelerators
		
	def _set_movie_active(self, isactive):
		if isactive == self._active_movie:
			return
		self._active_movie = isactive
		mw_globals.toplevel._set_movie_active(isactive)
			
	def _close_wid(self, wid):
		"""Called by children to close wid. Only implements real close
		at TopLevel"""
		pass

	def _clipchanged(self):
		"""Called when the clipping region is possibly changed"""
		if not self._parent or not self._wid:
			return
		if self._clip:
			Qd.DisposeRgn(self._clip)
		self._clip = None
		# And inform our children...
		for ch in self._subwindows:
			ch._clipchanged()
			
	def is_closed(self):
		"""Return true if window is closed"""
		return self._parent is None

	def newwindow(self, (x, y, w, h), pixmap = 0, transparent = 0, z=0,
		      type_channel = None):
		"""Create a new subwindow"""
		rv = _SubWindow(self, self._wid, (x, y, w, h), 0, pixmap,
				transparent, z)
		self._clipchanged()
		return rv

	def newcmwindow(self, (x, y, w, h), pixmap = 0, transparent = 0, z=0,
			type_channel = None):
		"""Create a new subwindow"""
		rv = _SubWindow(self, self._wid, (x, y, w, h), 1, pixmap,
				transparent, z)
		self._clipchanged()
		return rv

	def fgcolor(self, color):
		"""Set foregroundcolor to 3-tuple 0..255"""
		self._fgcolor = self._convert_color(color)

	def bgcolor(self, color):
		"""Set backgroundcolor to 3-tuple 0..255"""
		self._bgcolor = self._convert_color(color)
		
	def showwindow(self):
		"""Highlight the window"""
		pass
		
	def dontshowwindow(self):
		"""Don't highlight the window"""
		pass

	def setcursor(self, cursor):
		self._parent.setcursor(cursor)

	def newdisplaylist(self, *bgcolor):
		"""Return new, empty display list"""
		if bgcolor != ():
			bgcolor = self._convert_color(bgcolor[0])
		else:
			bgcolor = self._bgcolor
		return mw_displaylist._DisplayList(self, bgcolor)

	def setredrawfunc(self, func):
		if func is None or callable(func):
			self._redrawfunc = func
		else:
			raise error, 'invalid function'

	def setclickfunc(self, func):
		"""Intercept low-level mouse clicks (mac-specific)"""
		if func is None or callable(func):
			self._clickfunc = func
		else:
			raise error, 'invalid function'

	def register(self, event, func, arg):
		if func is None or callable(func):
			self._eventhandlers[event] = (func, arg)
		else:
			raise error, 'invalid function'

	def unregister(self, event):
		del self._eventhandlers[event]

	def destroy_menu(self):
		self._accelerators = {}
		self._popupmenu = None
		pass

	def create_menu(self, list, title = None):
		self._accelerators = {}
		self._popupmenu = mw_menucmd.FullPopupMenu(list, title,
						self._accelerators)

	def _image_size(self, file):
		"""Backward compatability: return wh of image given filename"""
		if _size_cache.has_key(file):
			return _size_cache[file]
		try:
			reader = img.reader(None, file)
		except img.error, arg:
			raise error, arg
		width = reader.width
		height = reader.height
		_size_cache[file] = width, height
		return width, height

	def _prepare_image(self, file, crop, scale, center, coordinates):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes
		oscale = scale
		format = imgformat.macrgb16
		depth = format.descr['size'] / 8

		try:
			reader = img.reader(format, file)
		except img.error, arg:
			raise error, arg
		w = xsize = reader.width
		h = ysize = reader.height
		_size_cache[file] = xsize, ysize
			
		top, bottom, left, right = crop
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

		
		if hasattr(reader, 'transparent'):
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
			mask = (mac_image.mkbitmap(w, h, imgformat.xbmpacked,
						   bitmap), bitmap)
		else:
			mask = None
		try:
			image = reader.read()
		except:
			raise error, 'unspecified error reading image'
		if scale != 1:
			w = int(xsize * scale + .5)
			h = int(ysize * scale + .5)
			image = imageop.scale(image, depth,
					      xsize, ysize, w, h)

		if center:
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
		xim = mac_image.mkpixmap(w, h, format, image)
		return (xim, image), mask, left, top, \
		       x, y, w - left - right, h - top - bottom

	def _convert_coordinates(self, coordinates):
		"""Convert fractional xywh in our space to pixel-xywh
		in toplevel-window relative pixels"""
		
		x, y = coordinates[:2]
##		if not (0 <= x <= 1 and 0 <= y <= 1):
##			raise error, 'coordinates out of bounds'
##		px = int((self._rect[_WIDTH] - 1) * x + 0.5) + self._rect[_X]
##		py = int((self._rect[_HEIGHT] - 1) * y + 0.5) + self._rect[_Y]
		px = int(self._rect[_WIDTH] * x) + self._rect[_X]
		py = int(self._rect[_HEIGHT] * y) + self._rect[_Y]
		if len(coordinates) == 2:
			return px, py
		w, h = coordinates[2:]
##		if not (0 <= w <= 1 and 0 <= h <= 1 and
##			0 <= x + w <= 1 and 0 <= y + h <= 1):
##			raise error, 'coordinates out of bounds'
##		pw = int((self._rect[_WIDTH] - 1) * w + 0.5)
##		ph = int((self._rect[_HEIGHT] - 1) * h + 0.5)
		pw = int(self._rect[_WIDTH] * w)
		ph = int(self._rect[_HEIGHT] * h)
		return px, py, pw, ph
		
	def _convert_color(self, (r, g, b)):
		"""Convert 8-bit r,g,b tuple to 16-bit r,g,b tuple"""
		return r*0x101, g*0x101, b*0x101


	def qdrect(self):
		"""return our xywh rect (in pixels) as quickdraw ltrb style"""
		return self._rect[0], self._rect[1], \
		       self._rect[0]+self._rect[2], \
			self._rect[1]+self._rect[3]
			
	def _goaway(self):
		"""User asked us to go away. Tell upper layers
		(but don't go yet)"""
		try:
			func, arg = self._eventhandlers[WindowExit]
		except KeyError:
			sys.exc_traceback = None
			return
		func(arg, self, WindowExit, (0, 0, 0))
		
	def _activate(self, active):
		for ch in self._subwindows:
			ch._activate(active)
		if active:
			evt = WindowActivate
		else:
			evt = WindowDeactivate
		try:
			func, arg = self._eventhandlers[evt]
		except KeyError:
			sys.exc_traceback = None
			return
		func(arg, self, (0, 0, 0))
		
	def _mouse_over_button(self, where):
		for ch in self._subwindows:
			if Qd.PtInRect(where, ch.qdrect()):
				try:
					return ch._mouse_over_button(where)
				except Continue:
					pass
		
		# XXXX Need to cater for html windows and such
		
		wx, wy, ww, wh = self._rect
		x, y = where
		x = float(x-wx)/ww
		y = float(y-wy)/wh

		if self._active_displist:
			for b in self._active_displist._buttons:
				if b._inside(x, y):
					return 1
		return 0
		
	def _contentclick(self, down, where, event, shifted):
		"""A click in our content-region. Note: this method is extended
		for top-level windows (to do global-to-local coordinate
		transforms)"""
		#
		# First see whether the click is in any of our children
		#
		for ch in self._subwindows:
			if Qd.PtInRect(where, ch.qdrect()):
				try:
					ch._contentclick(down, where, event,
							 shifted)
				except Continue:
					pass
				else:
					return
		#
		# Next, check for popup menu, if we have one
		#
		if shifted and self._popupmenu:
			# Convert coordinates back to global
			Qd.SetPort(self._wid)
			y, x = Qd.LocalToGlobal(where)
			self._popupmenu.popup(x, y, event, window=self)
			return
		#
		# It is really in our canvas. Do we have a low-level
		# click handler?
		#
		if self._clickfunc:
			self._clickfunc(down, where, event)
			return
		#
		# Convert to our type of event and call the
		# appropriate handler.
		#
		if not shifted:
			if down:
				evttype = Mouse0Press
			else:
				evttype = Mouse0Release
		else:
			if down:
				evttype = Mouse2Press
			else:
				evttype = Mouse2Release

		try:
			func, arg = self._eventhandlers[evttype]
		except KeyError:
			sys.exc_traceback = None
			return # Not wanted
			
		wx, wy, ww, wh = self._rect
		x, y = where
		x = float(x-wx)/ww
		y = float(y-wy)/wh
		
		buttons = []
		if self._active_displist:
			for b in self._active_displist._buttons:
				if b._inside(x, y):
					buttons.append(b)
				
		func(arg, self, evttype, (x, y, buttons))
		
	def _keyboardinput(self, char, where, event):
		#
		# First see whether position is in any of our children
		#
		for ch in self._subwindows:
			if Qd.PtInRect(where, ch.qdrect()):
				try:
					handled = ch._keyboardinput(char,
							      where, event)
				except Continue:
					pass
				else:
					return handled
		#
		# Next, check any popup menu accelerators
		#
		try:
			func, args = self._accelerators[char]
		except KeyError:
			pass
		else:
			apply(func, args)
			return 1
		#
		# Finally check for a KeyboardInput handler
		#
		try:
			func, arg = self._eventhandlers[KeyboardInput]
		except KeyError:
			return 0
		else:
			func(arg, self, KeyboardInput, char)
			return 1
		
	def _do_resize2(self):
		for w in self._subwindows:
			w._do_resize2()
		try:
			func, arg = self._eventhandlers[ResizeWindow]
		except KeyError:
			pass
		else:
			func(arg, self, ResizeWindow, None)
		
	def _redraw(self, rgn=None):
		"""Set clipping and color, redraw, redraw children"""
		if self._parent is None:
			return
		if not self._clip:
			self._mkclip()
			
		# First do opaque subwindows, topmost first
		still_to_do = []
		for child in self._subwindows:
			if child._transparent == 0 or \
			   (child._transparent == -1 and
			    child._active_displist):
				child._redraw(rgn)
			else:
				still_to_do.append(child)
		
		# Next do ourselves
		saveclip = Qd.NewRgn()
		Qd.GetClip(saveclip)
		Qd.SetClip(self._clip)
		Qd.RGBBackColor(self._bgcolor)
		Qd.RGBForeColor(self._fgcolor)
		if self._redrawfunc:
			self._redrawfunc()
		else:
			self._do_redraw()
		Qd.SetClip(saveclip)
		Qd.DisposeRgn(saveclip)
		
		# Finally do transparent children bottom-to-top
		still_to_do.reverse()
		for child in still_to_do:
					child._redraw(rgn)
					
	def _do_redraw(self):
		"""Do actual redraw"""
		if self._active_displist:
			self._active_displist._render()
		elif self._transparent == 0 or self._istoplevel:
			Qd.EraseRect(self.qdrect())
			
	def _macsetwin(self):
		"""Start drawing (by upper layer) in this window"""
		Qd.SetPort(self._wid)
		
		
class _ScrollMixin:
	"""Mixin class for scrollable/resizable toplevel windows"""
	
	def __init__(self, width, height, canvassize=None):
		self._canvassize = canvassize
		self._canvaspos = (0, 0)
		self._barx = None
		self._bary = None
		return width, height
		
	def close(self):
		pass
		
	def _adjustwh(self, width, height):
		"""Add scrollbarsizes to w/h"""
		return width, height
		
	def _resizescrollbars(self, width, height):
		"""Move/resize scrollbars and return inner width/height""" 
		return width, height
		
	def _clipvisible(self, clip):
		"""AND the visible region into the region clip"""
		pass
		
	def _activate(self, onoff):
		if onoff:
			hilite = 0
		else:
			hilite = 255
		if self._barx:
			self._barx.HiliteControl(hilite)
		if self._bary:
			self._bary.HiliteControl(hilite)
		
	def setcanvassize(self, how):
		if self._canvassize is None:
			print 'setcanvassize call for non-resizable window!'
			return
		w, h = self._canvassize
		if how == DOUBLE_WIDTH:
			w = w * 2
		elif how == DOUBLE_HEIGHT:
			h = h * 2
		else:
			w, h = 1.0, 1.0
			self._canvaspos = (0, 0)
		self._canvassize = (w, h)
		print 'DBG: new canvassize', self._canvassize
		# XXXX set _rect
		# XXXX do the resize callback

class _AdornmentsMixin:
	"""Class to handle toolbars and other adornments on toplevel windows"""
	def __init__(self):
		self._cmd_to_cntl = {}
		
	def _add_addornments(self, adornments):
		if not adornments:
			return
		if 0:
			x, y, w, h = self._rect
			xo, yo, wo, ho = adornments['offset']
			self._rect = x+xo, y+yo, w+wo, h+ho
		if adornments.has_key('toolbar'):
			#
			# Create the buttons
			#
			for type, resid, cmd in adornments['toolbar']:
				try:
					cntl = Ctl.GetNewControl(resid, self._wid)
				except Ctl.Error, arg:
					print 'CNTL resource %d not found: %s'%(resid, arg)
				else:
					self._cmd_to_cntl[cmd] = cntl
			#
			# Create the toolbar
			#
			resid, height = MenuTemplate.TOOLBAR
			try:
				cntl = Ctl.GetNewControl(resid, self._wid)
			except Ctl.Error, arg:
				print 'CNTL resource %d not found: %s'%(resid, arg)
			cntl.HiliteControl(255)
			self._cmd_to_cntl[None] = cntl
				
	def close(self):
		del self._cmd_to_cntl
			
	def set_commandlist(self, cmdlist):
		enabled = {}
		# First pass: enable all commands featuring in cmdlist
		for item in cmdlist:
			cmd = item.__class__
			if self._cmd_to_cntl.has_key(cmd):
				cntl = self._cmd_to_cntl[cmd]
				cntl.HiliteControl(0)
				enabled[cmd] = 1
		# Second pass: disable the others
		for cmd in self._cmd_to_cntl.keys():
			if not enabled.has_key(cmd):
				cntl = self._cmd_to_cntl[cmd]
				cntl.HiliteControl(255)

	def set_toggle(self, cmd, onoff):
		if self._cmd_to_cntl.has_key(cmd):
			cntl = self._cmd_to_cntl[cmd]
			value = cntl.GetControlMinimum() + onoff
			cntl.SetControlValue(value)
			print 'TOGGLE', cmd, value #DBG
		
class _Window(_CommonWindow, _WindowGroup, _ScrollMixin, _AdornmentsMixin):
	"""Toplevel window"""
	
	def __init__(self, parent, wid, x, y, w, h, defcmap = 0, pixmap = 0, 
			title="", adornments=None, canvassize = None, commandlist=None):
		
		self._istoplevel = 1
		_CommonWindow.__init__(self, parent, wid)
		
		self._transparent = 0
		
		# Note: the toplevel init routine is called with pixel coordinates,
		# not fractional coordinates
		# XXXX Should move down.
		w, h = _ScrollMixin.__init__(self, w, h, canvassize)
		self._rect = 0, 0, w, h
		_AdornmentsMixin.__init__(self)
		self._add_addornments(adornments)
		_x_pixel_per_mm, _y_pixel_per_mm = \
				 mw_globals.toplevel._getmmfactors()

		self._hfactor = parent._hfactor / (float(w) / _x_pixel_per_mm)
		self._vfactor = parent._vfactor / (float(h) / _y_pixel_per_mm)
		_WindowGroup.__init__(self, title, commandlist)

		self.arrowcache = {}
		self._next_create_box = []
	
	def close(self):
		_ScrollMixin.close(self)
		_AdornmentsMixin.close(self)
		_CommonWindow.close(self)
		self.arrowcache = {}
		# XXXX Not WindowGroup?
		
	def settitle(self, title):
		"""Set window title"""
		if not self._wid:
			return  # Or raise error?
		_WindowGroup.settitle(self, title)
		if title == None:
			title = ''
		self._wid.SetWTitle(title)
		
	def set_toggle(self, cmd, onoff):
		_AdornmentsMixin.set_toggle(self, cmd, onoff)
		_WindowGroup.set_toggle(self, cmd, onoff)
		
	def set_commandlist(self, cmdlist):
		_AdornmentsMixin.set_commandlist(self, cmdlist)
		_WindowGroup.set_commandlist(self, cmdlist)
		
	def getgeometry(self, units=UNIT_MM):
		rect = self._wid.GetWindowPort().portRect
		Qd.SetPort(self._wid)
		x, y = Qd.LocalToGlobal((0,0))
		w, h = rect[2]-rect[0], rect[3]-rect[1]
		_x_pixel_per_mm, _y_pixel_per_mm = \
				 mw_globals.toplevel._getmmfactors()
		_screen_top_offset = mw_globals.toplevel._getmbarheight()
		if units == UNIT_MM:
			rv = (float(x)/_x_pixel_per_mm,
			      float(y-_screen_top_offset)/_y_pixel_per_mm,
			      float(w)/_x_pixel_per_mm,
			      float(h)/_y_pixel_per_mm)
		elif units == UNIT_PXL:
			w, h = self._adjustwh(w, h)
			rv = x, y-_screen_top_offset, w, h
		elif units == UNIT_SCREEN:
			l, t, r, b = Qd.qd.screenBits.bounds
			scrw = r-l
			scrh = b-t-_screen_top_offset
			rv = (float(x)/scrw, float(y-_screen_top_offset)/scrh,
			      float(w)/scrw, float(h)/scrh)
		else:
			raise error, 'bad units specified'
		return rv

	def pop(self):
		"""Pop window to top of window stack"""
		if not self._wid or not self._parent:
			return
		self._wid.SelectWindow()

	def push(self):
		"""Push window to bottom of window stack"""
		if not self._wid or not self._parent:
			return
		self._wid.SendBehind(0)
		
	def _is_on_top(self):
		return 1
		
	def _contentclick(self, down, where, event, shifted):
		"""A mouse click in our data-region"""
		if not self._wid or not self._parent:
			return
		Qd.SetPort(self._wid)
		where = Qd.GlobalToLocal(where)
		_CommonWindow._contentclick(self, down, where, event, shifted)

	def _keyboardinput(self, char, where, event):
		"""A mouse click in our data-region"""
		if not self._wid or not self._parent:
			return
		Qd.SetPort(self._wid)
		where = Qd.GlobalToLocal(where)
		return _CommonWindow._keyboardinput(self, char, where, event)

	def _mkclip(self):
		if not self._wid or not self._parent:
			return
		if self._clip:
			raise 'Clip already valid!'
		# create region for whole window

		self._clip = Qd.NewRgn()
		Qd.RectRgn(self._clip, self.qdrect())
		self._clipvisible(self._clip)
		#
		# subtract all subwindows, insofar they aren't transparent
		# at the moment
		#
		for w in self._subwindows:
			if w._transparent == 0 or \
			   (w._transparent == -1 and w._active_displist):
				r = Qd.NewRgn()
				Qd.RectRgn(r, w.qdrect())
				Qd.DiffRgn(self._clip, r, self._clip)
				Qd.DisposeRgn(r)

	def _redraw(self, rgn=None):
		_CommonWindow._redraw(self, rgn)
		if rgn is None:
			rgn = self._wid.GetWindowPort().visRgn
		Ctl.UpdateControls(self._wid, rgn)
		
	def _activate(self, onoff):
		_CommonWindow._activate(self, onoff)
##		_WindowGroup._activate(self, onoff)
		_ScrollMixin._activate(self, onoff)

	def _resize_callback(self, width, height):
		self.arrowcache = {}
		mycreatebox = _in_create_box
		if mycreatebox:
			next_create_box = mycreatebox._next_create_box
			mycreatebox._next_create_box = []
			try:
				mycreatebox._rb_cancel()
			except _rb_done:
				pass
			mycreatebox._next_create_box[0:0] = next_create_box
		x, y = self._rect[:2]
		width, height = self._resizescrollbars(width, height)
		self._rect = x, y, width, height
		# convert pixels to mm
		parent = self._parent
		_x_pixel_per_mm, _y_pixel_per_mm = \
				 mw_globals.toplevel._getmmfactors()
		self._hfactor = parent._hfactor / (float(width)
						   / _x_pixel_per_mm)
		self._vfactor = parent._vfactor / (float(height) /
						   _y_pixel_per_mm)
		for d in self._displists[:]:
			d.close()
		self._wid.SizeWindow(width, height, 1)
		self._clipchanged()
		for w in self._subwindows:
			w._do_resize1()
		# call resize callbacks
		self._do_resize2()
		if mycreatebox:
			mycreatebox._rb_end()
			raise _rb_done

	def create_box(self, msg, callback, box = None):
		showmessage("Channel coordinates unknown, set to full base window.\nChange in channel view")
		if box == None:
			box = (0, 0, 1, 1)
		apply(callback, box)
##		global _in_create_box
##		if _in_create_box:
##			_in_create_box._next_create_box.append((self, msg, callback, box))
##			return
##		if self.is_closed():
##			apply(callback, ())
##			return
##		_in_create_box = self
##		self.pop()
##		if msg:
##			msg = msg + '\n\n' + _rb_message
##		else:
##			msg = _rb_message
##		self._rb_dl = self._active_displist
##		if self._rb_dl:
##			d = self._rb_dl.clone()
##		else:
##			d = self.newdisplaylist()
##		self._rb_transparent = []
##		sw = self._subwindows[:]
##		sw.reverse()
##		r = Xlib.CreateRegion()
##		for win in sw:
##			if not win._transparent:
##				# should do this recursively...
##				self._rb_transparent.append(win)
##				win._transparent = 1
##				d.drawfbox(win._bgcolor, win._sizes)
##				apply(r.UnionRectWithRegion, win._rect) # XXXX
##		for win in sw:
##			b = win._sizes
##			if b != (0, 0, 1, 1):
##				d.drawbox(b)
##		self._rb_display = d.clone()
##		d.fgcolor((255, 0, 0))
##		if box:
##			d.drawbox(box)
##		if self._rb_transparent:
##			self._mkclip()
##			self._do_expose(r)
##			self._rb_reg = r
##		d.render()
##		self._rb_curdisp = d
##		self._rb_dialog = showmessage(
##			msg, mtype = 'message', grab = 0,
##			callback = (self._rb_done, ()),
##			cancelCallback = (self._rb_cancel, ()))
##		self._rb_callback = callback
##		raise 'not implemented'
##		form = self._form
##		form.AddEventHandler(X.ButtonPressMask, FALSE,
##				     self._start_rb, None)
##		form.AddEventHandler(X.ButtonMotionMask, FALSE,
##				     self._do_rb, None)
##		form.AddEventHandler(X.ButtonReleaseMask, FALSE,
##				     self._end_rb, None)
##		cursor = form.Display().CreateFontCursor(Xcursorfont.crosshair)
##		form.GrabButton(X.AnyButton, X.AnyModifier, TRUE,
##				X.ButtonPressMask | X.ButtonMotionMask
##					| X.ButtonReleaseMask,
##				X.GrabModeAsync, X.GrabModeAsync, form, cursor)
##		v = form.GetValues(['foreground', 'background'])
##		v['foreground'] = v['foreground'] ^ v['background']
##		v['function'] = X.GXxor
##		v['line_style'] = X.LineOnOffDash
##		self._gc_rb = form.GetGC(v)
##		self._rb_box = box
##		if box:
##			x, y, w, h = self._convert_coordinates(box)
##			if w < 0:
##				x, w = x + w, -w
##			if h < 0:
##				y, h = y + h, -h
##			self._rb_box = x, y, w, h
##			self._rb_start_x = x
##			self._rb_start_y = y
##			self._rb_width = w
##			self._rb_height = h
##		else:
##			self._rb_start_x, self._rb_start_y, self._rb_width, \
##					  self._rb_height = self._rect
##		try:
##			Xt.MainLoop()
##		except _rb_done:
##			pass

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

##	# have to override these for create_box
##	def _input_callback(self, form, client_data, call_data):
##		if _in_create_box:
##			return
##		mac_windowbase._Window._input_callback(self, form, client_data,
##						     call_data)
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
		raise 'not yet implemented'
##		form = self._form
##		form.RemoveEventHandler(X.ButtonPressMask, FALSE,
##					self._start_rb, None)
##		form.RemoveEventHandler(X.ButtonMotionMask, FALSE,
##					self._do_rb, None)
##		form.RemoveEventHandler(X.ButtonReleaseMask, FALSE,
##					self._end_rb, None)
##		form.UngrabButton(X.AnyButton, X.AnyModifier)
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
		raise 'not yet implemented'
##		self._gc_rb.DrawRectangle(x, y, w, h)

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

class _SubWindow(_CommonWindow):
	"""Window "living in" with a toplevel window"""

	def __init__(self, parent, wid, coordinates, defcmap = 0, pixmap = 0, 
			transparent = 0, z = 0):
		
		self._istoplevel = 0
		_CommonWindow.__init__(self, parent, wid, z)
		
		x, y, w, h = parent._convert_coordinates(coordinates)
		self._rect = x, y, w, h
		if w <= 0 or h <= 0:
			raise 'Empty subwindow', coordinates
		self._sizes = coordinates
		
		self._hfactor = parent._hfactor / self._sizes[_WIDTH]
		self._vfactor = parent._vfactor / self._sizes[_HEIGHT]
		
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			self._transparent = transparent
		
		self.arrowcache = {}
		self._next_create_box = []

		# XXXX pixmap to-be-done
		
		# XXXX Should we do redraw of parent or something??

	def settitle(self, title):
		"""Set window title"""
		raise error, 'can only settitle at top-level'
		
	def getgeometry(self, units=UNIT_MM):
		return self._sizes

	def pop(self):
		"""Pop to top of subwindow stack"""
		if not self._parent:
			return
		parent = self._parent
		if parent._subwindows[0] is self:
			return
		parent._subwindows.remove(self)
		
		for i in range(len(parent._subwindows)):
			if self._z >= parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)
		parent._clipchanged()
		Qd.SetPort(self._wid)
		if self._transparent <= 0:
			Win.InvalRect(self.qdrect())
		parent.pop()

	def push(self):
		"""Push to bottom of subwindow stack"""
		if not self._parent:
			return
		parent = self._parent
		if parent._subwindows[-1] is self:
			return
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)-1,-1,-1):
			if self._z <= parent._subwindows[i]._z:
				parent._subwindows.insert(i+1, self)
				break
		else:
			parent._subwindows.insert(0, self)
		parent._clipchanged()
		Qd.SetPort(self._wid)
		Win.InvalRect(self.qdrect())
		parent.push()
		
	def _is_on_top(self):
		"""Return true if no other subwindow overlaps us"""
		if not self._parent:
			return 0
		# XXXX This is not good enough, really...
		return (self._parent._subwindows[0] is self)

	def _mkclip(self):
		if not self._parent:
			return
		if self._clip:
			raise 'Clipregion already valid!'
			
		# create region for our subwindow
		self._clip = Qd.NewRgn()
		Qd.RectRgn(self._clip, self.qdrect())
		# subtract all our subsubwindows
		for w in self._subwindows:
			if w._transparent == 0 or \
			   (w._transparent == -1 and w._active_displist):
				r = Qd.NewRgn()
				Qd.RectRgn(r, w.qdrect())
				Qd.DiffRgn(self._clip, r, self._clip)
				Qd.DisposeRgn(r)
		# subtract our higher-stacked siblings
		for w in self._parent._subwindows:
			if w == self:
				# Stop when we meet ourselves
				break
			if w._transparent == 0 or \
			   (w._transparent == -1 and w._active_displist):
				r = Qd.NewRgn()
				Qd.RectRgn(r, w.qdrect())
				Qd.DiffRgn(self._clip, r, self._clip)
				Qd.DisposeRgn(r)

	def _do_resize1(self):
		# calculate new size of subwindow after resize
		# close all display lists
		parent = self._parent
		## XXXX Should have crop=1?
		x, y, w, h = parent._convert_coordinates(self._sizes)
		self._rect = x, y, w, h
		w, h = self._sizes[2:]
		if w == 0:
			w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
		if h == 0:
			h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
		# We don't have to clear _clip, our parent did that.
		self._active_displist = None
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._do_resize1()

class DialogWindow(_Window):
	def __init__(self, resid, title='Dialog'):
		wid = Dlg.GetNewDialog(resid, -1)
		x0, y0, x1, y1 = wid.GetWindowPort().portRect
		w, h = x1-x0, y1-y0
		cmdlist = [
			usercmd.COPY(callback=(wid.DialogCopy, ())),
			usercmd.PASTE(callback=(wid.DialogPaste, ())),
			usercmd.CUT(callback=(wid.DialogCut, ())),
			usercmd.DELETE(callback=(wid.DialogDelete, ())),
		]			
		_Window.__init__(self, mw_globals.toplevel, wid, 0, 0, w, h, commandlist=cmdlist)
		mw_globals.toplevel._register_wid(wid, self)
		Qd.SetPort(wid)
		self._widgetdict = {}
		self._is_shown = 0 # XXXX Is this always true??!?
		self.title = title
		
	def show(self):
		self.settitle(self.title)
		self._wid.ShowWindow()
		self._is_shown = 1
		
	def hide(self):
		self._wid.HideWindow()
		self.settitle(None)
		self._is_shown = 0
		
	def is_showing(self):
		return self._is_shown
		
	def close(self):
		self.hide()
		self._widgetdict = {}
		_Window.close(self)
		
	def addwidget(self, num, widget):
		self._widgetdict[num] = widget
		
	def do_itemhit(self, item, event):
		print 'Dialog %s item %d event %s'%(self, item, event)
		
	def do_itemdraw(self, item):
		try:
			w = self._widgetdict[item]
		except KeyError:
			print 'Unknown user item', item
		else:
			w._redraw()
		
	def _redraw(self, rgn):
		pass
			
	def _activate(self, onoff):
		for w in self._widgetdict.values():
			w._activate(onoff)
			
	def ListWidget(self, item, content=[]):
		widget = mw_widgets._ListWidget(self._wid, item, content)
		self.addwidget(item, widget)
		return widget

