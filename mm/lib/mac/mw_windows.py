__version__ = "$Id$"

from Carbon import Win
from Carbon import Windows
from Carbon import Qd
from Carbon import QuickDraw
from Carbon import Qdoffs
from Carbon import QDOffscreen
from Carbon import Dlg
from Carbon import Ctl
from Carbon import Controls
from Carbon import Events
from Carbon import Drag
from Carbon import Dragconst
import MacOS
import mac_image
import imgformat
import img
import imageop
import sys
import math
import MenuTemplate
import usercmd
import struct
import macfs
import string

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
from mw_globals import ARR_LENGTH, ARR_SLANT, ARR_HALFWIDTH
from mw_globals import BM_ONSCREEN, BM_DRAWING, BM_PASSIVE, BM_TEMP
import mw_displaylist
import mw_menucmd
import mw_widgets
import mw_transitions

#
# Scrollbar constants
#
SCROLLBARSIZE=16		# Full size, overlapping 1 pixel with window border
# Parts of the scrollbar we track:
TRACKED_PARTS=(Controls.inUpButton, Controls.inDownButton,
		Controls.inPageUp, Controls.inPageDown)


##PIXELFORMAT=imgformat.macrgb16
PIXELFORMAT=imgformat.macrgb

		
#
# The dragpoints of a box (lurven, in dutch:-)
#
LURF_TOPLEFT=0
LURF_TOPRIGHT=1
LURF_BOTLEFT=2
LURF_BOTRIGHT=3
LURF_MID=4
LURF_MIDLEFT=5
LURF_MIDRIGHT=6
LURF_TOPMID=7
LURF_BOTMID=8


#
# Cache for images and sizes
#
IMAGE_CACHE_SIZE=1000000
_image_cache = {}
_size_cache = {}

#
# Globals for create_box()
#
_rb_message = """\
Use mouse button to draw a box.
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
		self._dynamic_list_dict = {}
		self.set_commandlist(cmdlist)
		
	def __repr__(self):
		return '<WindowGroup %s>'%self._title
	
	def settitle(self, title):
		self._title = title
		mw_globals.toplevel._changed_group_commands() # XXXX Is this good enough?
		
	def close(self, closegroup=1):
		if closegroup:
			mw_globals.toplevel._close_windowgroup(self)
		self._dict = {}
		self._cmds_toggled = {}
		self._dynamic_list_dict = {}
		
	def pop(self):
		# NOTE: This method should only be called for groups, not windows
		mw_globals.toplevel._install_group_commands(self)
		
	def set_dynamiclist(self, cmd, list):
		self._dynamic_list_dict[cmd] = list
		mw_globals.toplevel._changed_group_commands()
		
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
		if __debug__:
			for i in dict.items():
				fun, arglist = i
		mw_globals.toplevel._changed_group_commands()
		
	def set_commandlist(self, list):
		dict = {}
		for item in list:
			cmd = item.__class__
### This code does not work anymore with per-window button commands.
### but we work around it by adding those commands to the UNUSED_COMMANDS
### set.
##			if __debug__:
##				if not mw_globals._all_commands.has_key(cmd):
##					print 'Warning: user has no way to issue command', cmd
			dict[cmd] = item
		self._set_cmd_dict(dict)
		
	def has_command(self, cmd):
		return self._dict.has_key(cmd)
		
	def get_command_callback(self, cmd):
		if self._dict.has_key(cmd):
			return self._dict[cmd].callback
		return None

	def call_command(self, cmd):
		callback = self.get_command_callback(cmd)
		if not callback:
			print 'No callback for command', cmd
		else:
			func, arglist = callback
			apply(func, arglist)
			
	def get_command_dynamic_list(self, cmd):
		if self._dynamic_list_dict.has_key(cmd):
			return self._dynamic_list_dict[cmd]
		return None
			
	def close_window_command(self):
		# If this is the last window promote to close document
		if self._parent and self._parent._is_last_in_group(self._onscreen_wid):
			if self._parent._call_optional_command(MenuTemplate.CLOSE):
				return 1
		# First see whether there's a WindowExit handler
		if self.has_command(MenuTemplate.CLOSE_WINDOW):
			self.call_command(MenuTemplate.CLOSE_WINDOW)
			return 1
		if self._eventhandlers.has_key(WindowExit):
			func, arg = self._eventhandlers[WindowExit]
			func(arg, self, WindowExit, (0, 0, 0))
			return 1
		return 0

class _CommonWindow:
	"""Code common to toplevel window and subwindow"""
		
	def __init__(self, parent, wid, z=0, bgcolor=None):
		self._parent = parent
		self._onscreen_wid = wid
		self._transition = None
		self._frozen = None
		self._subwindows = []
		self._displists = []
		if bgcolor is None:
			self._bgcolor = parent._bgcolor
		else:
			self._bgcolor = self._convert_color(bgcolor)
		self._fgcolor = parent._fgcolor
		self._clip = None
		self._clipincludingchildren = None
		self._redrawguarantee = None
		self._button_region = None
		self._active_displist = None
		self._eventhandlers = {}
		self._redrawfunc = None
		self._clickfunc = None
		self._accelerators = {}
		self._active_movie = 0
		self._menu = None		# Channel-window popup menu
		self._popupmenu = None	# View popup menu (template based)
		self._outline_color = None
		self._rb_dialog = None
		self._wtd_cursor = ''
		self._z = z
		self._updatezorder()
##		print 'Window opened', hex(id(self))
		
	def close(self):
		"""Close window and all subwindows"""
##		print 'Closing window', hex(id(self)), self.qdrect()
		if self._parent is None:
			return		# already closed
		if not self._istoplevel:
			self._parent._clipchanged()
		if _in_create_box is self:
			self.cancel_create_box()
		self._set_movie_active(0)
		if self._transition:
			self.endtransition()
		if self in self._parent._subwindows:
			self._parent._subwindows.remove(self)
		self._onscreen_wid.InvalWindowRect(self.qdrect())
		self._parent._close_wid(self._onscreen_wid)
		self._parent = None

		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()

		if self._clip:
			Qd.DisposeRgn(self._clip)
		if self._clipincludingchildren:
			Qd.DisposeRgn(self._clipincludingchildren)
		del self._clip
		del self._clipincludingchildren
		
		if self._button_region:
			Qd.DisposeRgn(self._button_region)
		del self._button_region
		
		del self._subwindows
		del self._displists
		del self._active_displist
		del self._eventhandlers
		del self._redrawfunc
		del self._clickfunc
		del self._onscreen_wid
		del self._accelerators
		del self._menu
		del self._popupmenu
		
	def _set_movie_active(self, isactive):
		if isactive == self._active_movie:
			return
		self._active_movie = isactive
		mw_globals.toplevel._set_movie_active(isactive, self)
			
	def _close_wid(self, wid):
		"""Called by children to close wid. Only implements real close
		at TopLevel"""
		pass

	# _clipchanged is different for subwindows and toplevel windows
	
	def _zapclip(self):
		if not self._parent or not self._onscreen_wid:
			return
		if self._clip:
			Qd.DisposeRgn(self._clip)
		self._clip = None
		if self._clipincludingchildren:
			Qd.DisposeRgn(self._clipincludingchildren)
		self._clipincludingchildren = None
		# And inform our children...
		for ch in self._subwindows:
			ch._zapclip()
			
	def _mac_getclip(self, includechildren=0):
		"""Get the clip region for ourselves, or for ourselves plus our children"""
		if not self._clip:
			self._mkclip()
		if includechildren:
			return self._clipincludingchildren
		else:
			return self._clip
			
	def _buttonschanged(self):
		"""Buttons have changed, zap the mouse region cache. This escalates upwards"""
		if not self._parent or not self._onscreen_wid or not self._button_region:
			return
		if self._button_region:
			Qd.DisposeRgn(self._button_region)
			self._button_region = None
		# And inform our parent...
		self._parent._buttonschanged()
		
	def _zapregions(self, recursive=1):
		"""Invalidate button regions because of mousemove. Escalates downwards"""
		if self._button_region:
			Qd.DisposeRgn(self._button_region)
			self._button_region = None
		for win in self._subwindows:
			win._zapregions()
		
	def is_closed(self):
		"""Return true if window is closed"""
		return self._parent is None
		
	def is_showing(self):
		return not self.is_closed()

	def newwindow(self, (x, y, w, h), pixmap = 0, transparent = 0, z=0,
		      units = None, bgcolor=None):
		"""Create a new subwindow"""
		rv = _SubWindow(self, self._onscreen_wid, (x, y, w, h), 0, pixmap,
				transparent, z, units, bgcolor)
		self._clipchanged()
		return rv
		
	newcmwindow = newwindow

	def fgcolor(self, color):
		"""Set foregroundcolor to 3-tuple 0..255"""
		self._fgcolor = self._convert_color(color)

	def bgcolor(self, color):
		"""Set backgroundcolor to 3-tuple 0..255"""
## XXXX Think about this a bit more
##		if color is None:
##			# Inherit
##			if self._parent._transparent:
##				color = 'transparent'
##			else:
##				color = self._parent._bgcolor  # XXXX Should do this lazy
##		if color == 'transparent':
##			self._transparent = 1
##			color = (0, 0, 0)
##		else:
##			self._transparent = 0
		self._bgcolor = self._convert_color(color)
		
	def showwindow(self, color=(255, 0, 0)):
		"""Highlight the window"""
		self._outline_color = self._convert_color(color)
		self._invalrectandborder()
		
	def dontshowwindow(self):
		"""Don't highlight the window"""
		if not self._outline_color is None:
			self._outline_color = None
			self._invalrectandborder()
			
	def _invalrectandborder(self):
##		Qd.SetPort(self._onscreen_wid)
		rect = self.qdrect()
		rect = Qd.InsetRect(rect, -2, -2)
		self.wid.InvalWindowRect(rect)

	# draw an XOR line from pt0 to pt1 (in pixels)
	def drawxorline(self, pt0, pt1):
		pass

	def setcursor(self, cursor):
		if cursor == 'watch':
			cursor = ''
		self._wtd_cursor = cursor
		## Warn parent? self._parent.setcursor(cursor)

	def newdisplaylist(self, bgcolor=None, units=UNIT_SCREEN):
		"""Return new, empty display list"""
		if bgcolor is None:
			if not self._transparent:
				bgcolor = self._bgcolor
		else:
			bgcolor = self._convert_color(bgcolor)
		return mw_displaylist._DisplayList(self, bgcolor, units)

	def setredrawfunc(self, func):
		if func is None or callable(func):
			self._redrawfunc = func
		else:
			raise error, 'invalid function'
		self._mac_setredrawguarantee(None)

	def setclickfunc(self, func):
		"""Intercept low-level mouse clicks (mac-specific)"""
		if func is None or callable(func):
			self._clickfunc = func
		else:
			raise error, 'invalid function'

	def register(self, event, func, arg):
		if func is None or callable(func):
			self._eventhandlers[event] = (func, arg)
			if event in (DropFile, DropURL):
				self._enable_drop(1)
		else:
			raise error, 'invalid function'

	def unregister(self, event):
		del self._eventhandlers[event]
		if event in (DropFile, DropURL):
			self._enable_drop(0)

	def destroy_menu(self):
		self._accelerators = {}
		self._menu = None
		pass

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

	def _prepare_image(self, file, crop, fit, center, coordinates, align, units):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes
		format = PIXELFORMAT
		depth = format.descr['size'] / 8
		reader = None
		if _size_cache.has_key(file):
			w, h = _size_cache[file]
			xsize = w
			ysize = h
		else:
			try:
				reader = img.reader(format, file)
			except (img.error, IOError), arg:
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
			x, y, width, height = self._convert_coordinates((0,0,1,1))
		else:
			x, y, width, height = self._convert_coordinates(coordinates, units=units)
		
		if fit == 'meet':
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif fit == 'slice':
			scale = max(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif fit == 'icon':
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
			if scale > 1:
				scale = 1
		else:
			# value not reconized. set scale to 1
			scale = 1
				    
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)

		key = '%s@%f' % (`file`, scale)
		try:
			image, w, h, mask = _image_cache[key]
		except:			# reading from cache failed
			if not reader:
				try:
					reader = img.reader(format, file)
				except (img.error, IOError), arg:
					raise error, arg
			if hasattr(reader, 'transparent'):
				r = img.reader(imgformat.xrgb8, file)
				for i in range(len(r.colormap)):
					r.colormap[i] = 255, 255, 255
				r.colormap[r.transparent] = 0, 0, 0
				try:
					image = r.read()
				except:
					raise error, 'unspecified error reading image'
				if scale != 1:
					w = int(xsize * scale + .5)
					h = int(ysize * scale + .5)
					try:
						image = imageop.scale(image, 1,
							xsize, ysize, w, h)
					except (imageop.error, MemoryError):
						raise error, 'Error scaling image'
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
				try:
					image = imageop.scale(image, depth,
						      xsize, ysize, w, h)
				except imageop.error:
					raise error, 'Error scaling image'
			#
			# Put it in the cache, possibly emptying other things
			#
			self._put_image_in_cache(key, image, w, h, mask)
		if align == 'topleft':
			pass
		elif align == 'centerleft':
			y = y + (height - (h - top - bottom)) / 2
		elif align == 'bottomleft':
			y = y + height - h
		elif align == 'topcenter':
			x = x + (width - (w - left - right)) / 2
		elif align == 'center':
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
		elif align == 'bottomcenter':
			x, y = x + (width - (w - left - right)) / 2, \
			       y + height - h
		elif align == 'topright':
			x = x + width - w
		elif align == 'centerright':
			x, y = x + width - w, \
			       y + (height - (h - top - bottom)) / 2
		elif align == 'bottomright':
			x, y = x + width - w, \
			       y + height - h
		elif center:
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
		xim = mac_image.mkpixmap(w, h, format, image)
		rvx0, rvy0, rvw, rvh = self._convert_qdcoords(
				(x, y, x + w - left - right, y + h - top - bottom), ignorescroll=1, units=units)
		return (xim, image), mask, left, top, rvx0, rvy0, rvw, rvh

	def _put_image_in_cache(self, key, image, w, h, mask):
		if len(image) > IMAGE_CACHE_SIZE/2:
			return	# Don't cache huge images
		size, xkey = self._image_cache_size()
		while len(image) + size > IMAGE_CACHE_SIZE:
			# Too big, delete biggest
##			print 'Delete imgcache', xkey
			del _image_cache[xkey]
			size, xkey = self._image_cache_size()
##		print 'Store imgcache', key, len(image)
		_image_cache[key] = (image, w, h, mask)
		
	def _image_cache_size(self):
		size = 0
		max = -1
		xkey = None
		for key, (image, w, h, mask) in _image_cache.items():
			size = size + len(image)
			if len(image) > max:
				max = len(image)
				xkey = key
		return size, xkey
			
	def _convert_coordinates(self, coordinates, crop = 0, units = UNIT_SCREEN):
		"""Convert fractional xywh in our space to pixel-xywh
		in toplevel-window relative pixels"""
		# convert relative sizes to pixel sizes relative to
		# upper-left corner of the window
		# if crop is set, constrain the coordinates to the
		# area of the window
		# NOTE: does not work for millimeters, only pixels/relative
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		rx, ry, rw, rh = self._rect
		hf, vf = self._scrollsizefactors()
		rw, rh = rw*hf, rh*vf
##		if not (0 <= x <= 1 and 0 <= y <= 1):
##			raise error, 'coordinates out of bounds'
		if units == UNIT_PXL or (units is None and type(x) is type(0)):
			px = int(x)
			dx = 0
		else:
			px = int(rw * x + 0.5)
			dx = px - rw * x
		if units == UNIT_PXL or (units is None and type(y) is type(0)):
			py = int(y)
			dy = 0
		else:
			py = int(rh * y + 0.5)
			dy = py - rh * y
		pw = ph = 0
		if crop:
			if px < 0:
				px, pw = 0, px
			if px >= rw:
				px, pw = rw - 1, px - rw + 1
			if py < 0:
				py, ph = 0, py
			if py >= rh:
				py, ph = rh - 1, py - rh + 1
		if len(coordinates) == 2:
			return px+rx, py+ry
		if units == UNIT_PXL or (units is None and type(w) is type(0)):
			pw = int(w + pw - dx)
		else:
			pw = int(rw * w + 0.5 - dx) + pw
		if units == UNIT_PXL or (units is None and type(h) is type(0)):
			ph = int(h + ph - dy)
		else:
			ph = int(rh * h + 0.5 - dy) + ph
		if crop:
			if pw <= 0:
				pw = 1
			if px + pw > rw:
				pw = rw - px
			if ph <= 0:
				ph = 1
			if py + ph > rh:
				ph = rh - py
		return px+rx, py+ry, pw, ph
		
	def _scrolloffset(self):
		"""Return the x,y to be added to coordinates to convert them to QD
		values"""
		return 0, 0
		
	def _scrollsizefactors(self):
		"""Return the factor with which to multiply x/y sizes before returning
		them to upper layers, i.e. 1 divided by the amount of the window visible"""
		return 1, 1
		
	def _convert_qdcoords(self, coordinates, units = UNIT_SCREEN, ignorescroll=0):
		"""Convert QD coordinates to fractional xy or xywh coordinates"""
		x0, y0 = coordinates[:2]
		xscrolloff, yscrolloff = self._scrolloffset()
		if ignorescroll:
			x = x0
			y = y0
		else:
			x = x0-xscrolloff
			y = y0-yscrolloff
		if len(coordinates) == 2:
			coordinates = x, y
		else:
			x1, y1 = coordinates[2:]
			w, h = x1-x0, y1-y0
			coordinates = x, y, w, h
		if units == UNIT_PXL:
			return coordinates
		elif units == UNIT_SCREEN:
			return self._pxl2rel(coordinates)
		elif units == UNIT_MM:
			raise 'kaboo','kaboo'
		else:
			raise error, 'bad units specified'
		
	def _pxl2rel(self, coordinates):
		# XXXX incorrect for scrollable windows? Or does fixing the sizes
		# (rw, rh) do enough because x/y offsets are catered for by convert_qdcoords?
		px, py = coordinates[:2]
		rx, ry, rw, rh = self._rect
		wfactor, hfactor = self._scrollsizefactors()
		rw, rh = rw*wfactor, rh*hfactor
		x = float(px - rx) / rw
		y = float(py - ry) / rh
		if len(coordinates) == 2:
			return x, y
		pw, ph = coordinates[2:]
		w = float(pw) / rw
		h = float(ph) / rh
		return x, y, w, h
		
	def _convert_color(self, color):
		"""Convert 8-bit r,g,b tuple to 16-bit r,g,b tuple"""
		if type(color) == type(()):
			r, g, b = color
			return r*0x101, g*0x101, b*0x101
		else:
			print '_convert_color: funny color', color
			return color

	def qdrect(self):
		"""return our xywh rect (in pixels) as quickdraw ltrb style.
		This is the on-screen rectangle, not the full drawing area"""
		return self._rect[0], self._rect[1], \
		       self._rect[0]+self._rect[2], \
			self._rect[1]+self._rect[3]
			
	def _activate(self, active):
		for ch in self._subwindows:
			ch._activate(active)
		if self is _in_create_box:
			self._invalrectandborder()
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
		
	def _get_button_region(self):
		"""Return the region that contains all buttons, in global coordinates"""
		if not self._button_region:
			self._button_region = Qd.NewRgn()
			# Get all the children regions
			for ch in self._subwindows:
				rgn = ch._get_button_region()
				Qd.UnionRgn(self._button_region, rgn, self._button_region)
			if self._active_displist:
				# Get our own button region, and clip it to our clip region
				rgn = self._active_displist._get_button_region()
				clip = self._mac_getclip()
				Qd.SectRgn(rgn, clip, rgn)
				Qd.UnionRgn(self._button_region, rgn, self._button_region)
				Qd.DisposeRgn(rgn)
		return self._button_region
		
	def _iscontrolclick(self, down, where, event, double):
		# Overriden for toplevel window
		return 0
				
	def _contentclick(self, down, where, event, modifiers, double):
		"""A click in our content-region. Note: this method is extended
		for top-level windows (to do global-to-local coordinate
		transforms)"""
		#
		# If we are rubberbanding handle that first.
		#
		if (self is _in_create_box) and down:
				if self._rb_mousedown(where, modifiers):
					return
				# We are in create_box mode, but the mouse was way off.
				# If we are in modal create we beep, in modeless create we
				# abort
				if self._rb_dialog:
					MacOS.SysBeep()
					return
				self.cancel_create_box()
		#
		# First see whether the click is in any of our children
		#
		for ch in self._subwindows:
			if Qd.PtInRect(where, ch.qdrect()):
				try:
					ch._contentclick(down, where, event,
							 modifiers, double)
				except Continue:
					pass
				else:
					return
		#
		# Then, check for a click in a control
		#
		if self._iscontrolclick(down, where, event, double):
			return
		#
		# Next, check for popup menu, if we have one
		#
		if down and modifiers=='contextual':
			if self._menu or self._popupmenu:
				self._doclickcallback(Mouse0Press, where)
				self._contentpopupmenu(where, event)
				return
		else:
			if down and (self._menu or self._popupmenu):
				# Not rightclick, but we have a popup menu. Ask toplevel
				# to re-send the event in a short while
				mw_globals.toplevel.setmousetimer(self._contentpopupmenu, (where, event))
		
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
		if modifiers == 'contextual':
			if down:
				evttype = Mouse2Press
			else:
				evttype = Mouse2Release
		else:
			if down:
				evttype = Mouse0Press
			else:
				evttype = Mouse0Release
				
		self._doclickcallback(evttype, where, modifiers)
		
	def _doclickcallback(self, evttype, where, modifiers=None):
		try:
			func, arg = self._eventhandlers[evttype]
		except KeyError:
			sys.exc_traceback = None
			return # Not wanted
			
		x, y = self._convert_qdcoords(where)
		
		buttons = []
		if self._active_displist:
			for b in self._active_displist._buttons:
				if b._inside(x, y):
					buttons.append(b)
		try:
			func(arg, self, evttype, (x, y, buttons, modifiers))
		except Continue:
			pass
		else:
			return
		# XXX Not correct. We should check our redrawguarantee, I think...
		if self._transparent:
			raise Continue
		
	def _contentpopupmenu(self, where, event):
		mw_globals.toplevel.clearmousetimer()
		if self._menu:
			menu = self._menu
		elif self._popupmenu:
			menu = self._popupmenu
		else:
			return
		# Convert coordinates back to global
		Qd.SetPort(self._onscreen_wid)
		y, x = Qd.LocalToGlobal(where)
		menu.popup(x+2, y+2, event, window=self)
		
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
		
	def _do_move(self, deltax, deltay):
		# Move a window and it's subwindows. Note that this function does
		# not schedule redraws or invalidate clipping regions.
		x, y, w, h = self._rect
		self._rect = x+deltax, y+deltay, w, h
		if not self._istoplevel:
			self._sizes = self._parent._pxl2rel(self._rect)
		for w in self._subwindows:
			w._do_move(deltax, deltay)
		
	def _do_resize(self):
		"""The (sub)window has changed size through external means. Recompute
		everything for ourselves and our children"""
##		print 'resizing', self
		self._clipchanged()
		if not self._istoplevel:
			self._sizes = self._parent._pxl2rel(self._rect)
##			print 'sizes', self._sizes
		for d in self._displists[:]:
			d.close()
		self._do_resize0()
		
	def _do_resize0(self):
		"""Common code for resize and double width/height"""

		for w in self._subwindows:
			w._do_resize1()
		# call resize callbacks
		self._do_resize2()

	def _do_resize2(self):
		if self._transition:
			self._transition.move_resize()
		for w in self._subwindows:
			w._do_resize2()
		try:
			func, arg = self._eventhandlers[ResizeWindow]
		except KeyError:
			pass
		else:
##			print 'ResizeWindow for', self
			func(arg, self, ResizeWindow, None)
		
	def _redraw_now(self, rgn):
		"""Do a redraw of the specified region now. Escalated to our toplevel
		window, because we really need this region (so there may be bits from
		siblings or ancestors there)"""
		if self._parent is None:
			return
		self._parent._redraw_now(rgn)
		
	def _redraw(self, rgn=None):
		"""Set clipping and color, redraw, redraw children"""
		if self._parent is None:
			return
			
		olddrawenviron = self._mac_setwin()
		
		# First do opaque subwindows, topmost first
		still_to_do = []
		for child in self._subwindows:
			if not child._transparent:
				child._redraw(rgn)
			else:
				still_to_do.append(child)
		
		# Next do ourselves
		saveclip = Qd.NewRgn()
		Qd.GetClip(saveclip)
		clip = self._mac_getclip()
		if not Qd.EmptyRgn(clip):
			Qd.SetClip(clip)
			if not self._outline_color is None:
				Qd.RGBForeColor(self._outline_color)
				rect = self.qdrect()
				Qd.FrameRect(rect)
			Qd.RGBBackColor(self._bgcolor)
			Qd.RGBForeColor(self._fgcolor)
			if self._redrawfunc:
				if not self._transparent:
					# XXX This causes flashing in movie windows and such.
					Qd.EraseRect(self.qdrect())
				self._redrawfunc(rgn)
			else:
				self._do_redraw(rgn)
		
		# Then do transparent children bottom-to-top
		still_to_do.reverse()
		for child in still_to_do:
					child._redraw(rgn)
		# Then do the transition on our full clip (including children)
		# XXX should only be done in topmost window
		clipincludingchildren = self._mac_getclip(includechildren=1)
		Qd.SetClip(clipincludingchildren)
		if self._transition and self._transition.ismaster(self):
			self._transition.changed()
		Qd.SetClip(saveclip)
		Qd.DisposeRgn(saveclip)
					
		self._mac_unsetwin(olddrawenviron)
		
		# Last, do the rubber box, if rubberboxing
		if self is _in_create_box:
			self._rb_redraw()
					
	def _do_redraw(self, rgn=None):
		"""Do actual redraw"""
		if self._active_displist:
			self._active_displist._render(rgn=rgn)
		elif self._frozen and not self._transition:
##			self._mac_setwin(mw_globals.BM_ONSCREEN)
			Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
			Qd.RGBForeColor((0, 0, 0))
##			dst = self._mac_getoswindowpixmap(mw_globals.BM_ONSCREEN)
			dst = self._mac_getoswindowpixmap(mw_globals.BM_DRAWING)
			src = self._mac_getoswindowpixmap(mw_globals.BM_PASSIVE)
			rect = self.qdrect()
			Qd.CopyBits(src, dst, rect, rect, QuickDraw.srcCopy, None)
			self._mac_setwin() # Don't think this is needed...
		elif not self._transparent or self._istoplevel:
			Qd.EraseRect(self.qdrect())
			
	def _mac_getdrawingbitmapindex(self):
		"""Return either BM_DRAWING or BM_ONSCREEN depending on whether we're in a transition"""
		if self._transition:
			return BM_DRAWING
		else:
			return BM_ONSCREEN
			
	def _mac_setwin(self, which=None):
		"""Start drawing (by upper layer) in this window. This window decides whether
		to activate the onscreen or offscreen window and then recursively calls the
		parent to actually set the window."""
		if not self._parent:
			return
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		return self._parent._mac_setwin(which)
			
	def _mac_unsetwin(self, arg):
		"""Revert a previous _mac_setwin. The argument is the return value of _mac_setwin,
		which can be either a WindowPtr or a GrafPort, GDevice tuple."""
		if type(arg) == type(()):
			apply(Qdoffs.SetGWorld, arg)
		else:
			Qd.SetPort(arg)
		
	def _mac_invalwin(self):
		"""Schedule a full redraw for the area occupied by this window. This may cause
		siblings and parents and such to redraw too."""
		if self._onscreen_wid:
			self._onscreen_wid.InvalWindowRect(self.qdrect())
		
	def _mac_getoswindow(self, which=None):
		"""Return the WindowPtr or GrafPort of the current drawing window."""
		# XXXX I think this should be obsoleted by _mac_getoswindowport
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		return self._parent._mac_getoswindow(which)
		
	def _mac_getoswindowport(self, which=None):
		"""Return the GrafPort for the current drawing window."""
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		return self._parent._mac_getoswindowport(which)
			
	def _mac_getoswindowpixmap(self, which=None):
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		return self._parent._mac_getoswindowpixmap(which)
					
	def _mkclip(self):
		if not self._onscreen_wid or not self._parent:
			return
		if self._clip or self._clipincludingchildren:
			raise 'Clip already valid!'
		# create region for whole window
		self._clipincludingchildren = Qd.NewRgn()
		Qd.RectRgn(self._clipincludingchildren, self.qdrect())
##		print '_mkclip', self, self.qdrect()
##		self._clipvisible(self._clipincludingchildren)
		self._clipsubtractsiblings()
		# create region for the part of the window that _we_ (as opposed
		# to our children) have to redraw.
		self._clip = Qd.NewRgn()
		Qd.CopyRgn(self._clipincludingchildren, self._clip)
		#
		# subtract all subwindows, insofar they aren't transparent
		# at the moment
		#
		for w in self._subwindows:
			r = w._getredrawguarantee()
			if r:
				Qd.DiffRgn(self._clip, r, self._clip)
				Qd.DisposeRgn(r)
	
	def _clipsubtractsiblings(self):
		pass	# Only implemented for subwindows

	def _getredrawguarantee(self):
		"""Return the region that we will paint on (i.e. what our parent does not
		need to paint on)"""
		if not self._onscreen_wid or not self._parent:
			return
		# If we're transparent we give no guarantees whatsoever
		r = Qd.NewRgn()
		# If we're not transparent, or transparent-when-empty and non-empty
		# we redraw everything
		if not self._transparent:
##			print '_getredrawguarantee', self, self.qdrect()
			Qd.RectRgn(r, self.qdrect())
			return r
		didsome = 0
		if self._active_displist:
			r2 = self._active_displist._getredrawguarantee()
			if r2:
				Qd.UnionRgn(r, r2, r)
				Qd.DisposeRgn(r2)
				didsome = 1
		elif self._redrawguarantee != None:
##			print 'Pickup redraw guarantee', self._redrawguarantee, 'out of', self.qdrect() #DBG
			r2 = Qd.NewRgn()
			Qd.RectRgn(r2, self._redrawguarantee)
			Qd.UnionRgn(r, r2, r)
			Qd.DisposeRgn(r2)
			didsome = 1
		# The difficult case: we're not active, but our children may be.
		for w in self._subwindows:
			r2 = w._getredrawguarantee()
			if r2:
				Qd.UnionRgn(r, r2, r)
				Qd.DisposeRgn(r2)
				didsome = 1
		if not didsome:
			Qd.DisposeRgn(r)
			return
		r2 = Qd.NewRgn()
		Qd.RectRgn(r2, self.qdrect())
		Qd.SectRgn(r, r2, r)
		Qd.DisposeRgn(r2)
		return r
		
	def _mac_setredrawguarantee(self, box):
##		print 'set redrawguarantee', self, box #DBG
		self._redrawguarantee = box
		self._clipchanged()
					
	def create_box(self, msg, callback, box = None, units = UNIT_SCREEN, modeless=0):
		global _in_create_box
		if _in_create_box:
			_in_create_box.cancel_create_box()
		if self.is_closed():
			apply(callback, ())
			return
		_in_create_box = self
		if box:
			# convert box to relative sizes if necessary
			box = self._pxl2rel(self._convert_coordinates(box, units = units))
		self.pop(poptop=0)
		self._rb_dl = self._active_displist
		if self._rb_dl:
			d = self._rb_dl.clone()
		else:
			d = self.newdisplaylist()
		self._rb_transparent = []
		sw = self._subwindows[:]
		sw.reverse()
		for win in sw:
			b = win._sizes
			b = self._pxl2rel(self._convert_coordinates(box, units = win._units))
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		d.render()
		self._rb_display = d
		if box:
			x0, y0, w, h = self._convert_coordinates(box)
			self._rb_box = (x0, y0, x0+w, y0+h)
		else:
			self._rb_box = None
		self._rb_dragpoint = None
		self._onscreen_wid.InvalWindowRect(self.qdrect())
		self._rb_callback = callback
		self._rb_units = units

		if modeless:
			self._rb_dialog = None
		else:
			if msg:
				msg = msg + '\n\n' + _rb_message
			else:
				msg = _rb_message

			self._rb_dialog = showmessage(
				msg, mtype = 'message', grab = 0,
				callback = (self._rb_done, ()),
				cancelCallback = (self.cancel_create_box, ()))
				
			mw_globals.toplevel.grabwids([self._rb_dialog._dialog, self._onscreen_wid])
			while _in_create_box is self:
				mw_globals.toplevel._eventloop(100)
			mw_globals.toplevel.grab(None)
		
	# supporting methods for create_box
	def _rb_cvbox(self, units = UNIT_SCREEN):
		if self._rb_box is None:
			return ()
		x0, y0, x1, y1 = self._rb_box
		xscrolloff, yscrolloff = self._scrolloffset()
		x0, y0 = x0+xscrolloff, y0+yscrolloff
		x1, y1 = x1+xscrolloff, y1+yscrolloff
		return self._convert_qdcoords((x0, y0, x1, y1), units = units)

	def _rb_done(self):
		"""callback for "done" button in dialog or any change in modeless create_box"""
		callback = self._rb_callback
		units = self._rb_units
		self._rb_finish()
		apply(callback, self._rb_cvbox(units))

	def cancel_create_box(self):
		if not (self is _in_create_box):
			raise 'Not _in_create_box', (self, _in_create_box)
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())

	def _rb_finish(self):
		"""Common code for done/cancel, clean everything up"""
		global _in_create_box
		_in_create_box = None
		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		self._rb_display.close()
		del self._rb_callback
		del self._rb_units
		if self._rb_dialog:
			self._rb_dialog.close()
		self._rb_dialog = None
		del self._rb_dl
		del self._rb_display

	def _rb_redraw(self):
		if not self._rb_box:
			return
		clipincludingchildren = self._mac_getclip(includechildren=1)
		Qd.SetClip(clipincludingchildren)
		if self._onscreen_wid == Win.FrontWindow():
			Qd.RGBForeColor((0xffff, 0, 0))
		else:
			Qd.RGBForeColor((0xc000, 0, 0))
		if not self._rb_dragpoint is None:
			port = self._onscreen_wid.GetWindowPort()
			oldmode = port.pnMode
			Qd.PenMode(QuickDraw.patXor)
		self._rb_doredraw()
		if not self._rb_dragpoint is None:
			Qd.PenMode(oldmode)
		
	def _rb_movebox(self, where, final=0):
		x, y = where
		xscrolloff, yscrolloff = self._scrolloffset()
		x, y = x-xscrolloff, y-yscrolloff
		x0, y0, x1, y1 = self._rb_box
		if self._rb_dragpoint == LURF_TOPLEFT:
			x0, y0 = x, y
		elif self._rb_dragpoint == LURF_TOPRIGHT:
			x0, y1 = x, y
		elif self._rb_dragpoint == LURF_BOTLEFT:
			x1, y0 = x, y
		elif self._rb_dragpoint == LURF_BOTRIGHT:
			x1, y1 = x, y
		elif self._rb_dragpoint == LURF_MID:
			# Constrain box size
			xmargin = (x1-x0)/2
			ymargin = (y1-y0)/2
			x, y = self._rb_constrain((x, y), xmargin, ymargin)
			oldx = (x0+x1)/2
			oldy = (y0+y1)/2
			diffx = x-oldx
			diffy = y-oldy
			x0 = x0 + diffx
			x1 = x1 + diffx
			y0 = y0 + diffy
			y1 = y1 + diffy
		elif self._rb_dragpoint == LURF_MIDLEFT:
			x0 = x
		elif self._rb_dragpoint == LURF_MIDRIGHT:
			x1 = x
		elif self._rb_dragpoint == LURF_TOPMID:
			y0 = y
		elif self._rb_dragpoint == LURF_BOTMID:
			y1 = y
		else:
			print 'funny dragpoint', self._rb_dragpoint
		x0, y0 = self._rb_constrain((x0, y0))
		x1, y1 = self._rb_constrain((x1, y1))
		#
		# New box computed. Return if same as old one.
		#
		if self._rb_box == (x0, y0, x1, y1):
			return
		#
		# Otherwise first erase old box, then draw the new one.
		#
		clipincludingchildren = self._mac_getclip(includechildren=1)
		Qd.SetClip(clipincludingchildren)
		port = self._onscreen_wid.GetWindowPort()
		oldmode = port.pnMode
		Qd.RGBForeColor((0xffff, 0, 0))
		Qd.PenMode(QuickDraw.patXor)

		self._rb_doredraw()
		if final:
			Qd.PenMode(oldmode)
			if x0 > x1:
				x0, x1 = x1, x0
			if y0 > y1:
				y0, y1 = y1, y0
		self._rb_box = x0, y0, x1, y1
		self._rb_doredraw()
		Qd.PenMode(oldmode)
		
	def _rb_doredraw(self):
		xscroll, yscroll = self._scrolloffset()
		x0, y0, x1, y1 = self._rb_box
		if x0 > x1: x0, x1 = x1, x0
		if y0 > y1: y0, y1 = y1, y0
		if x0 != x1 or y0 != y1:
			Qd.FrameRect((x0+xscroll, y0+yscroll, x1+xscroll, y1+yscroll))
		smallboxes = self._rb_smallboxes(scroll=1)
		for box in smallboxes:
			Qd.PaintRect(box)
			
	def _rb_smallboxes(self, scroll=0):
		x0, y0, x1, y1 = self._rb_box
		if scroll:
			xscroll, yscroll = self._scrolloffset()
			x0, y0 = x0+xscroll, y0+yscroll
			x1, y1 = x1+xscroll, y1+yscroll
		xh = (x0+x1)/2
		yh = (y0+y1)/2
		# These correspond to the LURF_* constants
		points = [
			(x0, y0),
			(x0, y1),
			(x1, y0),
			(x1, y1),
			(xh, yh),
			(x0, yh),
			(x1, yh),
			(xh, y0),
			(xh, y1),
			]
		smallboxes = []
		for x, y in points:
			smallboxes.append((x-2, y-2, x+2, y+2))
		return smallboxes

	def _rb_constrain(self, where, xmargin=0, ymargin=0):
		x0, y0, x1, y1 = self.qdrect()
		xscrolloff, yscrolloff = self._scrolloffset()
		x0, y0 = x0 - xscrolloff, y0 - yscrolloff
		x1, y1 = x1 - xscrolloff, y1 - yscrolloff
		x0 = x0 + xmargin
		x1 = x1 - xmargin
		y0 = y0 + ymargin
		y1 = y1 - ymargin
		x, y = where
		if x < x0: x = x0
		if x > x1: x = x1
		if y < y0: y = y0
		if y > y1: y = y1
		return x, y

	def _rb_mousedown(self, where, modifiers): # XXXXSCROLL
		# called on mouse press
		# XXXX I'm not sure that both the render and the invalrect are needed...
		self._rb_display.render()
		self._onscreen_wid.InvalWindowRect(self.qdrect())
		x, y = where
		xscrolloff, yscrolloff = self._scrolloffset()
		x, y = x - xscrolloff, y - yscrolloff
		dragpoint = None
		if self._rb_box:
			smallboxes = self._rb_smallboxes()
			for i in range(len(smallboxes)):
				x0, y0, x1, y1 = smallboxes[i]
				if x0 <= x <= x1 and y0 <= y <= y1:
					dragpoint = i
					break
			else:
				# We don't recognize the location.
				return 0
		if dragpoint is None:
			x, y = self._rb_constrain((x, y))
			self._rb_box = (x, y, x, y)
			dragpoint = LURF_BOTRIGHT
		self._rb_dragpoint = dragpoint
		mw_globals.toplevel.setmousetracker(self._rb_mousemove)
		return 1

	def _rb_mousemove(self, event):
		"""Called on mouse moved with button down and final mouseup"""
		what, message, when, where, modifiers = event
		Qd.SetPort(self._onscreen_wid)
		where = Qd.GlobalToLocal(where)
		if what == Events.mouseUp:
			self._rb_movebox(where, 1)
			self._rb_dragpoint = None
			mw_globals.toplevel.setmousetracker(None)
			self._onscreen_wid.InvalWindowRect(self.qdrect())
			if not self._rb_dialog:
				# Modeless create_box: do the callback
				self._rb_done()
		else:
			self._rb_movebox(where, 0)

	# Experimental animation interface
	def updatecoordinates(self, coordinates, units=UNIT_SCREEN, fit=None, mediacoords=None):
		# first convert any coordinates to pixel
		coordinates = self._parent._convert_coordinates(coordinates,units=units)
##		print 'window.updatecoordinates',coordinates, units
		
		x, y = coordinates[:2]

		# move or/and resize window
		if len(coordinates)==2:
			w, h = 0, 0
		elif len(coordinates)==4:
			w, h = coordinates[2:]
		else:
			raise AssertionError
		
		if units == self._units and (x, y, w, h) == self._rect:
			return
			
		Qd.SetPort(self._onscreen_wid)
		self._onscreen_wid.InvalWindowRect(self.qdrect())
		
		old_x, old_y, old_w, old_h = self._rect
		if units == self._units and w == old_w and h == old_h:
			self._clipchanged()
			self._do_move(x-old_x, y-old_y)
		else:
##			print 'OLD RECT', self._rect, self.qdrect()
			self._rect = x, y, w, h
			self._units = units
			self._do_resize()
##			print 'NEW RECT', self._rect, self.qdrect()
		self._onscreen_wid.InvalWindowRect(self.qdrect())

	def updatezindex(self, z):
		self._z = z
		self._updatezorder(redraw=1)
##		print 'window.updatezindex',z

	def updatebgcolor(self, color):
		self._bgcolor = self._convert_color(color)
		self._transparent = 0 # XXXX Correct?
		for dl in self._displists:
			dl.updatebgcolor(color)
##		print 'window.updatebgcolor',color, self
		self._onscreen_wid.InvalWindowRect(self.qdrect())

	# Experimental transition interface
	def begintransition(self, isouttransition, runit, dict, cb):
		if not self._transition_setup_before(isouttransition):
			if cb:
				apply(apply, cb)
			return
		self._transition = mw_transitions.TransitionEngine(self, isouttransition, runit, dict, cb)
		self._transition_setup_after()
		
	def jointransition(self, window, cb):
		# Join the transition already created on "window".
		if not window._transition:
			print 'Joining without a transition', self, window, window._transition
			return
		isouttransition = window._transition.isouttransition()
		if not self._transition_setup_before(isouttransition):
			return
		ismaster = self._windowlevel() < window._windowlevel()
		self._transition = window._transition
		self._transition.join(self, ismaster, cb)
		self._transition_setup_after()

	def endtransition(self):
		if not self._transition:
			return
		if not self._parent:
			print 'endtransition() called for a window that is not visible anymore!'
			return
##		has_tmp = self._transition.need_tmp_wid()
		has_tmp = 1
		self._transition.endtransition()
		self._transition = None
		if not self._parent:
			print 'endtransition() called for a window that is not visible anymore!'
			return
		self._mac_dispose_gworld(BM_DRAWING)
		self._mac_dispose_gworld(BM_PASSIVE)
		if has_tmp:
			self._mac_dispose_gworld(BM_TEMP)
##		self._mac_invalwin()
		# Tell upper layers, if they are interested
		if self._eventhandlers.has_key(OSWindowChanged):
			func, arg = self._eventhandlers[OSWindowChanged]
			func(arg, self, OSWindowChanged, (0, 0, 0))
		
	def changed(self):
		"""Called if upper layers have modified the drawing surface"""
		if self._transition:
			self._transition.changed()
		if self._eventhandlers.has_key(WindowContentChanged):
			func, arg = self._eventhandlers[WindowContentChanged]
			func(arg, self, WindowContentChanged, mw_globals.toplevel.getcurtime())
		
	def settransitionvalue(self, value):
		if self._transition:
			self._transition.settransitionvalue(value)
		else:
			print 'settransitionvalue without a transition'
			
	def freeze_content(self, how):
		"""Freeze the contents of the window, depending on how:
		how='transition' until the next transition,
		how='hold' forever,
		how=None clears a previous how='hold'. This basically means the next
		close() of a display list does not do an erase."""
		if how:
			if self._frozen:
				# Dispose possible old frozen bitmap
				self._mac_dispose_gworld(BM_PASSIVE)
			self._mac_create_gworld(BM_PASSIVE, 1, self.qdrect())
			self._frozen = how
		elif self._frozen:
##			print 'freeze_content(None)' # DBG
			self._mac_dispose_gworld(BM_PASSIVE)
			self._frozen = None
			self._mac_invalwin()
	
	def _windowlevel(self):
		"""Returns 0 for toplevel windows, 1 for children of toplevel windows, etc"""
		prev = self
		count = 0
		while not prev._istoplevel:
			count = count + 1
			prev = prev._parent
		return count
		
	def _transition_setup_before(self, isouttransition):
		"""Check that begintransition() is allowed, create the offscreen bitmaps 
		and set the event handler"""
		rect = self.qdrect()
		if self._transition:
			print 'Multiple Transitions!'
			return 0
		if self._frozen == 'transition':
			# We are frozen, so we have already saved the contents
			self._frozen = None
		elif isouttransition:
			self._mac_create_gworld(BM_PASSIVE, 0, rect)
		else:
			# Make sure our screen pixels reflect the actual current
			# situation, so we can grab them
			Qd.SetPort(self._onscreen_wid)
			updrgn = Qd.NewRgn()
			Qd.RectRgn(updrgn, rect)
			winupdrgn = Qd.NewRgn()
			self._onscreen_wid.GetWindowUpdateRgn(winupdrgn)
##			self._onscreen_wid.GetWindowRegion(Windows.kWindowUpdateRgn, winupdrgn)
			Qd.SectRgn(updrgn, winupdrgn, updrgn)
			if not Qd.EmptyRgn(updrgn):
				self._redraw_now(updrgn)
			Qd.DisposeRgn(updrgn)
			Qd.DisposeRgn(winupdrgn)
			del updrgn
			
			self._mac_create_gworld(BM_PASSIVE, 1, rect)
		self._mac_create_gworld(BM_DRAWING, isouttransition, rect)
		return 1
	
	def _transition_setup_after(self):
##		if self._transition.need_tmp_wid():
		if 1:
			self._mac_create_gworld(BM_TEMP, 0, self.qdrect())
		#
		# Tell upper layers, if they are interested (VideoChannels and such may have to
		# tell their underlying libraries)
		#
		if self._eventhandlers.has_key(OSWindowChanged):
			func, arg = self._eventhandlers[OSWindowChanged]
			func(arg, self, OSWindowChanged, (0, 0, 0))
	
	def _dump_bits(self, which):
		srcbits = self._mac_getoswindowpixmap(which)
		currect = srcbits
		old = Qd.GetPort()
		Qd.SetPort(self._onscreen_wid)
		Qd.CopyBits(srcbits, self._onscreen_wid.GetWindowPort().portBits, currect, currect, QuickDraw.srcCopy, None)
		Qd.SetPort(old)

	def _mac_create_gworld(self, which, copybits, area):
		self._parent._mac_create_gworld(which, copybits, area)
		
	def _mac_dispose_gworld(self, which):
		if self._parent:
			self._parent._mac_dispose_gworld(which)
		else:
			print "Cannot dispose GWorld when parent window no longer exists!"
		
	def dumpwindow(self, indent=0):
		if not self._subwindows and not self._active_displist and not self._redrawfunc:
			return
		print ' '*indent, self._onscreen_wid, self
		if self._redrawfunc or self._active_displist:
			print ' '*(indent+8), self.qdrect(), 'z=%d'%self._z
			print ' '*(indent+8), self._bgcolor, ["", "transparent"][self._transparent]
		if self._redrawfunc:
			print ' '*(indent+8), 'redrawfunc', self._redrawfunc
		if self._active_displist:
			print ' '*(indent+8), 'active displist length', len(self._active_displist._list)
		indent = indent + 2
		if self._subwindows:
			print ' '*(indent+8), len(self._subwindows), 'subwindows'
		for w in self._subwindows:
			w.dumpwindow(indent)

def calc_extra_size(adornments, canvassize):
	"""Return the number of pixels needed for toolbar and scrollbars"""
	extraw = 0
	extrah = 0
	minw = 0
	minh = 0
	if adornments and adornments.has_key('toolbar'):
		resid, width, height = MenuTemplate.TOOLBAR
		extrah = extrah + height
		minw = width
	# XXXX Add scrollbar size if applicable
	if canvassize:
		extraw = extraw + SCROLLBARSIZE - 1
		extrah = extrah + SCROLLBARSIZE - 1
	return extraw, extrah, minw, minh
		
class _OffscreenMixin:
	def __init__(self):
		self.__wids = [None, None, None]
		self.__gworlds = [None, None, None]
		self.__bitmaps = [None, None, None]
		self.__refcounts = [0, 0, 0]

	def close(self):
		del self.__wids
		del self.__gworlds
		del self.__bitmaps

	def _mac_create_gworld(self, which, copybits, area):
##		print 'DBG: create_gworld', which, copybits, area
		if which < 0:
			raise 'Incorrect gworld indicator'
		cur_port, cur_dev = Qdoffs.GetGWorld()
		if self.__refcounts[which] == 0:
			#
			# No such offscreen bitmap yet. Create it.
			#
			cur_depth = 32
			cur_rect = self.qdrect()
			gworld = Qdoffs.NewGWorld(cur_depth,  cur_rect, None, None, QDOffscreen.keepLocal)
			grafptr = gworld.as_GrafPtr()
			Qdoffs.SetGWorld(grafptr, None)
			pixmap = gworld.GetGWorldPixMap()
			Qdoffs.LockPixels(pixmap)
			bitmap = Qd.RawBitMap(pixmap.data)
			Qd.RGBBackColor(self._bgcolor)
			Qd.EraseRect(cur_rect)
			created = 1
		else:
			#
			# We have this bitmap already.
			#
			self.__refcounts[which] = self.__refcounts[which] + 1
			grafptr = self.__wids[which]
			gworld = self.__gworlds[which]
			bitmap = self.__bitmaps[which]
			Qdoffs.SetGWorld(grafptr, None)
			created = 0
		#
		# Finally copy or erase the portion of the bitmap to be used.
		#
		if copybits:
			Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
			Qd.RGBForeColor((0,0,0))
			port = self._onscreen_wid.GetWindowPort()
			Qd.QDFlushPortBuffer(port, None)
			Qd.CopyBits(port.portBits, bitmap, area, area, QuickDraw.srcCopy, None)
## XXX Not sure whether this is correct: the whole offscreen bitmap has been cleared during
## creation (above), but should I re-clear here if I reuse it?
##		else:
##			Qd.RGBBackColor(self._bgcolor)
##			Qd.EraseRect(area)
		Qdoffs.SetGWorld(cur_port, cur_dev)
		if created:
			#
			# And store it.
			#
			self.__refcounts[which] = 1
			self.__wids[which] = grafptr
			self.__gworlds[which] = gworld
			self.__bitmaps[which] = bitmap
		
	def _mac_dispose_gworld(self, which):
		if which < 0:
			raise 'Incorrect gworld indicator'
		self.__refcounts[which] = self.__refcounts[which] - 1
		if self.__refcounts[which] < 0:
			raise 'gworld refcount < 0'
		if self.__refcounts[which]:
			return
		self.__wids[which] = None
		self.__bitmaps[which] = None
		self.__gworlds[which] = None

	def _mac_setwin(self, which=None):
		"""Start drawing (by upper layer) in this window. This window decides whether
		to activate the onscreen or offscreen window and then recursively calls the
		parent to actually set the window."""
		if not self._parent:
			return
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		if which == BM_DRAWING and self.__wids[BM_DRAWING] == None:
			which = BM_ONSCREEN
		if which == BM_ONSCREEN:
			rv = Qd.GetPort()
			Qd.SetPort(self._onscreen_wid)
		else:
			rv = Qdoffs.GetGWorld()
			Qdoffs.SetGWorld(self.__wids[which], None)
		return rv
			
	def _mac_getoswindow(self, which=None):
		"""Return the WindowPtr or GrafPort of the current drawing window."""
		# XXXX I think this should be obsoleted by _mac_getoswindowport
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		if which == BM_DRAWING and self.__wids[BM_DRAWING] == None:
			which = BM_ONSCREEN
		if which == BM_ONSCREEN:
			return self._onscreen_wid
		else:
			return self.__wids[which]
		
	def _mac_getoswindowport(self, which=None):
		"""Return the GrafPort for the current drawing window."""
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		if which == BM_DRAWING and self.__wids[BM_DRAWING] == None:
			which = BM_ONSCREEN
		if which == BM_ONSCREEN:
			return self._onscreen_wid.GetWindowPort()
		else:
			return self.__wids[which]
			
	def _mac_getoswindowpixmap(self, which=None):
		if which == None:
			which = self._mac_getdrawingbitmapindex()
		if which == BM_DRAWING and self.__wids[BM_DRAWING] == None:
			which = BM_ONSCREEN
		if which == BM_ONSCREEN:
			return self._onscreen_wid.GetWindowPort().portBits
		else:
			return self.__bitmaps[which]
			
class _ScrollMixin:
	"""Mixin class for scrollable/resizable toplevel windows"""
	
	def __init__(self, canvassize=None):
		self._canvassize = canvassize
		self._canvaspos = (0, 0)
		self._barx = None
		self._bary = None
		#
		if not canvassize:
			return
		#
		# Get measurements
		#
		horleft, verttop, vertright, horbot, vertleft, hortop = self._initscrollbarposition()
		#
		# Create vertical scrollbar
		#
		rect = vertleft, verttop, vertright, hortop+1
		self._bary = Ctl.NewControl(self._onscreen_wid, rect, "", 1, 0, 0, 0, 16, 0)
##		self._bary.HiliteControl(255)
		#
		# Create horizontal scrollbar
		#
		rect = horleft, hortop, vertleft+1, horbot
		self._barx = Ctl.NewControl(self._onscreen_wid, rect, "", 1, 0, 0, 0, 16, 0)
##		self._barx.HiliteControl(255)
		#
		# And install callbacks
		#
		self._add_control(self._barx, self._xscrollcallback, self._xscrollcallback)
		self._add_control(self._bary, self._yscrollcallback, self._yscrollcallback)
		#
		# And see whether we resize the drawable area on a window-resize
		#
		import settings
		self.no_canvas_resize = settings.get('no_canvas_resize')
		
	def close(self):
		if self._barx:
			self._del_control(self._barx)
			self._del_control(self._bary)
			del self._barx
			del self._bary
		
	def _xscrollcallback(self, bar, part):
		ten_percent = (self._rect[_WIDTH]/10)
		page = self._rect[_WIDTH]-ten_percent
		self._anyscrollcallback(bar, part, ten_percent, page)
		
	def _anyscrollcallback(self, bar, part, line, page):
		if line < 1: line = 1
		if page < 1: page = 1
		old_x, old_y = self._canvaspos
		value = bar.GetControlValue()
		if part == Controls.inUpButton:
			value = value - line
		elif part == Controls.inPageUp:
			value = value - page
		elif part == Controls.inDownButton:
			value = value + line
		elif part == Controls.inPageDown:
			value = value + page
		bar.SetControlValue(value)
		self._scrollupdate(old_x, old_y)
		
	def _scrollupdate(self, old_x, old_y):
		"""Update after a scroll from old_x, old_y"""
		new_x = self._barx.GetControlValue()
		new_y = self._bary.GetControlValue()
		Qd.SetPort(self._onscreen_wid)
		# See whether we can use scrollrect. Only possible if no updates pending.
		updrgn = Qd.NewRgn()
		self._onscreen_wid.GetWindowUpdateRgn(updrgn)
##		self._onscreen_wid.GetWindowRegion(Windows.kWindowUpdateRgn, updrgn)
		if Qd.EmptyRgn(updrgn):
			# Scroll, and get the new vacated region back
			Qd.ScrollRect(self.qdrect(), old_x-new_x, old_y-new_y, updrgn)
		else:
			# ok, update the whole window
			Qd.RectRgn(updrgn, self.qdrect())
		self._onscreen_wid.InvalWindowRgn(updrgn)
		Qd.DisposeRgn(updrgn)
		self._canvaspos = new_x, new_y
		
	def _yscrollcallback(self, bar, part):
		ten_percent = (self._rect[_HEIGHT]/10)
		page = self._rect[_HEIGHT]-ten_percent
		self._anyscrollcallback(bar, part, ten_percent, page)
		
	def _canscroll(self):
		"""Return true if this window may be scrolled"""
		return not not self._canvassize
		
	def _scrolloffset(self):
		if not self._canvassize:
			return 0, 0
		xoff, yoff = self._canvaspos
		return -xoff, -yoff
		
	def _needs_grow_cursor(self):
		if self._barx:
			return 0
		return self._resizable
		
	def _redraw(self):
		if self._barx:
			self._onscreen_wid.DrawGrowIcon()
		
	def _initscrollbarposition(self):
		l, t, w, h = self._rect
		r, b = l+w, t+h
		newr, newb = r - (SCROLLBARSIZE-1), b - (SCROLLBARSIZE-1)
		self._rect = l, t, newr-l, newb-t
		return l-1, t-1,  r+1, b+1, newr, newb
		
	def _resized(self):
		"""Move/resize scrollbars and update self._rect after a resize"""
		if not self._barx:
			return

		horleft, verttop, vertright, horbot, vertleft, hortop = self._initscrollbarposition()

		rect = vertleft, verttop, vertright, hortop+1
		self._movescrollbar(self._bary, rect)

		rect = horleft, hortop, vertleft+1, horbot
		self._movescrollbar(self._barx, rect)

	def _movescrollbar(self, bar, rect):
		l, t, r, b = rect
		bar.HideControl()
		bar.MoveControl(l, t)
		bar.SizeControl(r-l, (b-t))
		bar.ShowControl()
		
	def _clipvisible(self, clip):
		"""AND the visible region into the region clip"""
		pass
		
	def _activate(self, onoff):
		if not self._barx:
			return
		if onoff:
			self._barx.ActivateControl()
			self._bary.ActivateControl()
		else:
			self._barx.DeactivateControl()
			self._bary.DeactivateControl()
		self._onscreen_wid.DrawGrowIcon()
		
	def _scrollsizefactors(self):
		if self._canvassize is None:
			return 1, 1
		return self._canvassize
		
	def getscrollposition(self, units=UNIT_PXL):
		assert units == UNIT_PXL
		return self._canvaspos + self._rect[2:]

	def scrollvisible(self, coordinates, units = UNIT_MM):
		"""Try to make the area in coordinates visible. If it doesn't fit make
		at least the topleft corner visible"""
		if not self._barx:
			return
		box = self._convert_coordinates(coordinates, units=units)
		old_x, old_y = self._canvaspos
		w, h = self._rect[2:]
		x, y = box[:2]
		if len(box) > 2:
			wbox, hbox = box[2:]
			x1, y1 = x+wbox, y+hbox
			self._scrollto(self._barx, x1, w)
			self._scrollto(self._bary, y1, h)
		self._scrollto(self._barx, x, w)
		self._scrollto(self._bary, y, h)
		self._scrollupdate(old_x, old_y)
		
	def _scrollto(self, bar, pos, visiblesize):
		"""If pos isn't visible scroll there (minimum distance), without update"""
		cur = bar.GetControlValue()
		if pos < cur:
			bar.SetControlValue(pos)
		elif pos > cur+visiblesize:
			bar.SetControlValue(pos-visiblesize)

	def getcanvassize(self, units = UNIT_MM):
		if self._canvassize is None:
			raise error, 'getcanvassize call for non-resizable window!'
		wf, hf = self._canvassize
		rw, rh = self._rect[2:4]
		w = rw * wf
		h = rh * hf
		if units == UNIT_MM:
			_x_pixel_per_mm, _y_pixel_per_mm = \
					mw_globals.toplevel._getmmfactors()
			w = float(w)/_x_pixel_per_mm
			h = float(h)/_y_pixel_per_mm
		elif units == UNIT_PXL:
			w = int(w)
			h = int(h)
		elif units == UNIT_SCREEN:
			l, t, r, b = Qd.qd.screenBits.bounds
			t = t + _screen_top_offset
			scrw = r-l
			scrh = b-t
			w = float(w)/scrw
			h = float(h)/scrh
		else:
			raise error, 'bad units specified'
		return w, h

	def setcanvassize(self, how):
		if self._canvassize is None:
			print 'setcanvassize call for non-resizable window!'
			return
		w, h = self._canvassize
		if type(how) is type(()):
			units, width, height = how
			if units == UNIT_MM:
				_x_pixel_per_mm, _y_pixel_per_mm = \
					mw_globals.toplevel._getmmfactors()
				w = int(width*_x_pixel_per_mm)
				h = int(height*_y_pixel_per_mm)
			elif units == UNIT_PXL:
				w = int(width)
				h = int(height)
			elif units == UNIT_SCREEN:
				l, t, r, b = Qd.qd.screenBits.bounds
				t = t + _screen_top_offset
				scrw = r-l
				scrh = b-t
				w = int(width*scrw)
				h = int(height*scrh)
			else:
				raise error, 'bad units'
			# w,h are in pixels, convert to factors
			rw, rh = self._rect[2:4]
			w = float(w) / rw
			h = float(h) / rh
			if not self.no_canvas_resize:
				if w < 1: w = 1.0
				if h < 1: h = 1.0
		elif how == DOUBLE_WIDTH:
			w = w * 2
		elif how == DOUBLE_HEIGHT:
			h = h * 2
		else:
			w, h = 1.0, 1.0
		self.arrowcache = {}
		self._canvassize = (w, h)
		self._adjust_scrollbar_max()
		self._do_resize0()
		
	def mustadjustcanvasforresize(self, old_w, old_h):
		"""About to resize. Return 1 if the resize has to be handled by higher layers,
		0 if we can handle it by enabling scrollbars"""
		if not self._barx:
			return 1
		#
		# Compute old w/h multiplication factors and old virtual w/h
		#
		x, y, new_w, new_h = self._rect
		old_wf, old_hf = self._canvassize
		old_virtual_w, old_virtual_h = int(old_w*old_wf+0.5), int(old_h*old_hf+0.5)
		#
		# Use these to compute expected new w/h multiplciation factors, keeping
		# virtual size the same (if possible and wanted)
		#
		new_wf = float(old_virtual_w) / new_w
		new_hf = float(old_virtual_h) / new_h
		if not self.no_canvas_resize:
			if new_wf < 1: new_wf = 1
			if new_hf < 1: new_hf = 1
		self.arrowcache = {}
		self._canvassize = new_wf, new_hf
		#
		# Now we have to do scrollbar setting, as the 15-bit maxvalue may resize
		# our virtual sizes after all
		#
		self._adjust_scrollbar_max()
		new_wf, new_hf = self._canvassize
		new_virtual_w , new_virtual_h = int(new_w*new_wf+0.5), int(new_h*new_hf+0.5)
		if (old_virtual_w, old_virtual_h) != (new_virtual_w, new_virtual_h):
			return 1
		return 0
		
	def _adjust_scrollbar_max(self):
		"""Adjust scrollbar maximum for new window/canvassize. This may update
		the canvassize, because scrollbars cannot go beyond 32767"""
		# XXXX Keep x,y position
		# XXXX Check that canvassizes >= 1.0
		wwindow, hwindow = self._rect[2:]
		wfactor, hfactor = self._canvassize
		wcanvas, hcanvas = wfactor*wwindow, hfactor*hwindow
		if wcanvas > 32766:
			wcanvas = 32766
			wfactor = 32766.0/wwindow
		if hcanvas > 32766:
			hcanvas = 32766
			hfactor = 32766.0/hwindow
		self._canvassize = wfactor, hfactor
		self._adjustbar(self._barx, wwindow, wcanvas)
		self._adjustbar(self._bary, hwindow, hcanvas)
		self._canvaspos = self._barx.GetControlValue(), self._bary.GetControlValue()
		
	def _adjustbar(self, bar, windowsize, canvassize):
		"""Adjust a scrollbar for a new maximum"""
		if canvassize <= windowsize:
			bar.SetControlValue(0)
			bar.SetControlMaximum(0)
##			bar.HiliteControl(255)
		else:
			newmax = canvassize - windowsize
			oldvalue = bar.GetControlValue()
##			if oldvalue:
##				# XXXX Should be done better
##				oldmax = bar.GetControlMaximum()
##				factor = float(newmax)/oldmax
##				hw = windowsize/2
##				newvalue = int(oldvalue*factor+hw*factor-hw)
##			else:
##				newvalue = 0
			if oldvalue > newmax:
				newvalue = newmax
			else:
				newvalue = oldvalue
			bar.SetControlMaximum(newmax)
			bar.SetControlValue(newvalue)
##			bar.HiliteControl(0)

class _AdornmentsMixin:
	"""Class to handle toolbars and other adornments on toplevel windows"""
	def __init__(self, adornments):
		self.__rootctl = None
		self.__toolbarctl = None
		self._cmd_to_cntl = {}
		self._cntl_to_cmd = {}
		self._cntl_handlers = {}
		self._keyboard_shortcuts = {}
		self._doubleclick = None
		self._add_adornments(adornments)
		
	def _add_adornments(self, adornments):
		if not adornments:
			return
		if adornments.has_key('toolbar'):
			root = Ctl.CreateRootControl(self._onscreen_wid)
			self.__rootctl = root
			#
			# Create the toolbar
			#
			resid, width, height = MenuTemplate.TOOLBAR
			try:
				x, y, w, h = self._rect
				if width > w:
					w = width
				rect = (0, 0, w, height)
				toolbar = Ctl.NewControl(self._onscreen_wid, rect, '', 1, 0, 0, 0,
					Controls.kControlWindowHeaderProc, 0)
			except Ctl.Error, arg:
				print 'CNTL resource %d not found: %s'%(resid, arg)
			toolbar.EmbedControl(self.__rootctl)
			self.__toolbarctl = toolbar
			#
			# Create the buttons
			#
			for type, resid, cmd in adornments['toolbar']:
				try:
					cntl = Ctl.GetNewControl(resid, self._onscreen_wid)
				except Ctl.Error, arg:
					print 'CNTL resource %d not found: %s'%(resid, arg)
				else:
					self._add_control(cntl, self._toolbar_callback)
					self._cmd_to_cntl[cmd] = cntl
					self._cntl_to_cmd[cntl] = cmd
					cntl.EmbedControl(toolbar)
			#
			# Adjust window bounds
			#
			x, y, w, h = self._rect
			self._rect = x, y+height, w, h-height
		if adornments.has_key('shortcuts'):
			self._keyboard_shortcuts = adornments['shortcuts']
			for k in self._keyboard_shortcuts.keys():
				mw_globals._all_commands[k] = 1
		if adornments.has_key('doubleclick'):
			self._doubleclick = adornments['doubleclick']
			
	def close(self):
		del self._cmd_to_cntl
		del self._cntl_to_cmd
		del self._cntl_handlers
		del self._keyboard_shortcuts
		del self._doubleclick

	def _add_control(self, cntl, callback, trackhandler=None):
		self._cntl_handlers[cntl] = (callback, trackhandler)
			
	def _del_control(self, cntl):
		del self._cntl_handlers[cntl]
			
	def _resized(self):
		"""Adjust self._rect after a resize"""
		if not self._cmd_to_cntl:
			return
		x, y, w, h = self._rect
		resid, width, height = MenuTemplate.TOOLBAR
		self._rect = x, y+height, w, h-height
			
	def _iscontrolclick(self, down, local, event, double):
		if down:
			# Check for control
			ptype, ctl = Ctl.FindControl(local, self._onscreen_wid)
			if ptype and ctl and self._cntl_handlers.has_key(ctl):
				control_callback, track_callback = self._cntl_handlers[ctl]
				if ptype in TRACKED_PARTS and track_callback:
					dummy = ctl.TrackControl(local, track_callback)
				else:
					part = ctl.TrackControl(local)
					if part:
						control_callback(ctl, part)
				return 1
			# Not a control. Check for double-click
			if double and self._doubleclick_callback():
				return 1
		# Otherwise if the click is outside the real inner section we ignore it.
		if not Qd.PtInRect(local, self.qdrect()):
##			if down:
##				MacOS.SysBeep()
			return 1
		return 0
		
	def _toolbar_callback(self, ctl, part):
		cmd = self._cntl_to_cmd[ctl]
		self.call_command(cmd)
		
	def _doubleclick_callback(self):
		if self._doubleclick:
			self.call_command(self._doubleclick)
			return 1
		return 0
		
	def _check_for_shortcut(self, key):
		if self._keyboard_shortcuts.has_key(key):
			self.call_command(self._keyboard_shortcuts[key])
			return 1
		return 0
			
	def set_commandlist(self, cmdlist):
		enabled = {}
		# First pass: enable all commands featuring in cmdlist
		for item in cmdlist:
			cmd = item.__class__
			if self._cmd_to_cntl.has_key(cmd):
				cntl = self._cmd_to_cntl[cmd]
				cntl.ActivateControl()
				enabled[cmd] = 1
		# Second pass: disable the others
		for cmd in self._cmd_to_cntl.keys():
			if not enabled.has_key(cmd):
				cntl = self._cmd_to_cntl[cmd]
				cntl.DeactivateControl()
	
	def set_toggle(self, cmd, onoff):
		if self._cmd_to_cntl.has_key(cmd):
			cntl = self._cmd_to_cntl[cmd]
			value = cntl.GetControlMinimum() + onoff
			cntl.SetControlValue(value)

	def setpopupmenu(self, menutemplate):
		# Menutemplate is a MenuTemplate-style menu template.
		# It should be turned into an menu and put
		# into self._popupmenu.
		self._destroy_popupmenu()
		self._popupmenu = mw_menucmd.ContextualPopupMenu(menutemplate, self.call_command)
		self._popupmenu.update_menu_enabled(self.has_command)
		
	def _destroy_popupmenu(self):
		# Free resources held by self._popupmenu and set it to None
		if self._popupmenu:
			self._popupmenu.delete()
		self._popupmenu = None
		
class _Window(_ScrollMixin, _AdornmentsMixin, _OffscreenMixin, _WindowGroup, _CommonWindow):
	"""Toplevel window"""
	
	def __init__(self, parent, wid, x, y, w, h, defcmap = 0, pixmap = 0, 
			title="", adornments=None, canvassize = None, commandlist=None,
			resizable=1, bgcolor=None):
##		print 'DBG: mainwindow, coords=', (x, y, w, h)
		self._title = title
		self._istoplevel = 1
		self._resizable = resizable
		self._drop_enabled = 0
		_OffscreenMixin.__init__(self)
		_CommonWindow.__init__(self, parent, wid, 0, bgcolor)
		
		self._transparent = 0
		
		#
		# Note: the toplevel init routine is called with pixel coordinates,
		# not fractional coordinates
		#
		# Also, note the order here is important: the initializers modify
		# self._rect, and the toolbar has to span the window with the scroll
		# bars below it.
		#
		self._rect = 0, 0, w, h
		_AdornmentsMixin.__init__(self, adornments)
		#
		# Note: currently canvassize is always either None or (w, h). The (w,h)
		# is a bad choice (to be fixed), so we work around it.
		#
		if canvassize:
			_ScrollMixin.__init__(self, (1,1))
		else:
			_ScrollMixin.__init__(self, None)

		_x_pixel_per_mm, _y_pixel_per_mm = \
				 mw_globals.toplevel._getmmfactors()

		hf, vf = self._scrollsizefactors()
		_WindowGroup.__init__(self, title, commandlist)

		self.arrowcache = {}
	
	def __repr__(self):
		return '<Window %s>'%self._title
	
	def close(self):
		self._enable_drop(0)
		_ScrollMixin.close(self)
		_AdornmentsMixin.close(self)
		_CommonWindow.close(self)
		_OffscreenMixin.close(self)
		_WindowGroup.close(self, closegroup=0)
		self.arrowcache = {}
				
	def settitle(self, title):
		"""Set window title"""
		if not self._onscreen_wid:
			return  # Or raise error?
		_WindowGroup.settitle(self, title)
		if title == None:
			title = ''
		self._onscreen_wid.SetWTitle(title)
		
	def set_toggle(self, cmd, onoff):
		_AdornmentsMixin.set_toggle(self, cmd, onoff)
		_WindowGroup.set_toggle(self, cmd, onoff)
		
	def set_commandlist(self, cmdlist):
		_AdornmentsMixin.set_commandlist(self, cmdlist)
		_WindowGroup.set_commandlist(self, cmdlist)
		if self._popupmenu:
			self._popupmenu.update_menu_enabled(self.has_command)

	def getgeometry(self, units=UNIT_MM):
		if units != UNIT_PXL:
			print 'Warning: non-UNIT_PXL getgeometry() call'
		rect = self._onscreen_wid.GetWindowPort().portRect
		Qd.SetPort(self._onscreen_wid)
		x, y = Qd.LocalToGlobal((0,0))
		w, h = rect[2]-rect[0], rect[3]-rect[1]
		# Adjust for scrollbars
		if self._barx:
			w = w - (SCROLLBARSIZE - 1)
		if self._bary:
			h = h - (SCROLLBARSIZE - 1)
		# And for buttons along the top
		if self._cntl_to_cmd:
			dummy, dummy, extraheight = MenuTemplate.TOOLBAR
			h = h - extraheight
		_x_pixel_per_mm, _y_pixel_per_mm = \
				 mw_globals.toplevel._getmmfactors()
		_screen_top_offset = mw_globals.toplevel._getmbarheight()
		if units == UNIT_MM:
			rv = (float(x)/_x_pixel_per_mm,
			      float(y-_screen_top_offset)/_y_pixel_per_mm,
			      float(w)/_x_pixel_per_mm,
			      float(h)/_y_pixel_per_mm)
		elif units == UNIT_PXL:
			rv = x, y-_screen_top_offset, w, h
		elif units == UNIT_SCREEN:
			l, t, r, b = Qd.qd.screenBits.bounds
			scrw = r-l
			scrh = b-t-_screen_top_offset
			rv = (float(x)/scrw, float(y-_screen_top_offset)/scrh,
			      float(w)/scrw, float(h)/scrh)
		else:
			raise error, 'bad units specified'
		print 'DBG', self, units, rv
		return rv

	def pop(self, poptop=1):
		"""Pop window to top of window stack"""
		if not self._onscreen_wid or not self._parent or not poptop:
			return
		self._onscreen_wid.SelectWindow()
		mw_globals.toplevel._mouseregionschanged()

	def push(self):
		"""Push window to bottom of window stack"""
		if not self._onscreen_wid or not self._parent:
			return
		self._onscreen_wid.SendBehind(0)
		
	def _is_on_top(self):
		return 1
		
	def _clipchanged(self):
		"""Called when the clipping region is possibly changed"""
		if not self._parent or not self._onscreen_wid:
			return
		self._zapclip()
		self._buttonschanged()
		self._zapregions()
		
	def _updatezorder(self, redraw=0, tobottom=0):
		pass
		
	def _goaway(self):
		"""User asked us to go away. Tell upper layers
		(but don't go yet)"""
		if not self.close_window_command():
			print 'No way to close this window!', self
		
	def _contentclick(self, down, where, event, modifiers, double):
		"""A mouse click in our data-region"""
		if not self._onscreen_wid or not self._parent:
			return
		Qd.SetPort(self._onscreen_wid)
		where = Qd.GlobalToLocal(where)
		_CommonWindow._contentclick(self, down, where, event, modifiers, double)

	def _keyboardinput(self, char, where, event):
		"""A character typed in our data-region"""
		if not self._onscreen_wid or not self._parent:
			return
		if self._check_for_shortcut(char):
			return 1
		Qd.SetPort(self._onscreen_wid)
		where = Qd.GlobalToLocal(where)
		return _CommonWindow._keyboardinput(self, char, where, event)

	def _redraw(self, rgn=None):
		_CommonWindow._redraw(self, rgn)
		if rgn is None:
			rgn = self._onscreen_wid.GetWindowPort().visRgn
		Ctl.UpdateControls(self._onscreen_wid, rgn)
		_ScrollMixin._redraw(self)
		if self._eventhandlers.has_key(WindowContentChanged):
			func, arg = self._eventhandlers[WindowContentChanged]
			func(arg, self, WindowContentChanged, mw_globals.toplevel.getcurtime())
					
	def _redraw_now(self, rgn):
		"""Do a redraw of the specified region now"""
		self._redraw(rgn)
		if not rgn:
			rgn = self._onscreen_wid.GetWindowPort().visRgn
		self._onscreen_wid.ValidWindowRgn(rgn)

	def _activate(self, onoff):
		_CommonWindow._activate(self, onoff)
##		_WindowGroup._activate(self, onoff)
		_ScrollMixin._activate(self, onoff)

	def _resize_callback(self, width, height, x=None, y=None):
		self.arrowcache = {}
		if _in_create_box:
			_in_create_box.cancel_create_box()
			
		self._onscreen_wid.SizeWindow(width, height, 1)
		# XXXX Should also update size of offscreen maps?
		Qd.SetPort(self._onscreen_wid)
		self._onscreen_wid.InvalWindowRect(self.qdrect())

		old_x, old_y, old_w, old_h = self._rect
		if x is None:
			x = old_x
		if y is None:
			y = old_y
		self._rect = x, y, width, height
		_AdornmentsMixin._resized(self)
		_ScrollMixin._resized(self)
		mustresize = _ScrollMixin.mustadjustcanvasforresize(self, old_w, old_h)
		if mustresize:
			self._do_resize()
		else:
			self._clipchanged()
		
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
		
	def _enable_drop(self, onoff):
		if onoff == self._drop_enabled:
			return
		if onoff:
			Drag.InstallTrackingHandler(self._trackhandler, self._onscreen_wid)
			Drag.InstallReceiveHandler(self._receivehandler, self._onscreen_wid)
		else:
			Drag.RemoveTrackingHandler(self._onscreen_wid)
			Drag.RemoveReceiveHandler(self._onscreen_wid)
		self._drop_enabled = onoff
		
	def _trackhandler(self, message, dragref, wid):
		try:
			if not message in (Dragconst.kDragTrackingEnterWindow, 
					Dragconst.kDragTrackingLeaveWindow,
					Dragconst.kDragTrackingInWindow):
				return
			rect = None
			oldport = Qd.GetPort()
			Qd.SetPort(self._onscreen_wid)
			dummy, where = dragref.GetDragMouse()
			where = Qd.GlobalToLocal(where)
			x, y = self._convert_qdcoords(where)
			if message == Dragconst.kDragTrackingInWindow:
	 			# We're dragging through the window. Give the track
	 			# handler a chance to update the mouse, if wanted
				try:
					#
					# XXXX This is wrong: we should get the correct (DragFile or DragURL)
					# handler here.
					#
					func, arg = self._eventhandlers[DragFile]
				except KeyError:
					return
				dummy, where = dragref.GetDragMouse()
				Qd.SetPort(self._onscreen_wid)
				where = Qd.GlobalToLocal(where)
				x, y = self._convert_qdcoords(where)
				func(arg, self, DragFile, (x, y))
				return
	 			
	 		# We're entering or leaving the window. Draw or remove
	 		# the highlight.
	## 		if 0 < x < 1 and 0 < y < 1:
			if 1:
				rect = self.qdrect()
				rgn = Qd.NewRgn()
				Qd.RectRgn(rgn, rect)
				if message == Dragconst.kDragTrackingEnterWindow:
					dragref.ShowDragHilite(rgn, 1)
				else:
					dragref.HideDragHilite()
				Qd.DisposeRgn(rgn)
			Qd.SetPort(oldport)
		except:
			if hasattr(sys, 'exc_info'):
				exc_type, exc_value, exc_traceback = sys.exc_info()
			else:
				exc_type, exc_value, exc_traceback = sys.exc_type, sys.exc_value, sys.exc_traceback
			import traceback
			print 'Error in Drag Handler:'
			print
			traceback.print_exception(exc_type, exc_value, None)
			traceback.print_tb(exc_traceback)
					
		
	def _receivehandler(self, dragref, wid):
		try:
			dummy, where = dragref.GetDragMouse()
			Qd.SetPort(self._onscreen_wid)
			where = Qd.GlobalToLocal(where)
			x, y = self._convert_qdcoords(where)
			n = dragref.CountDragItems()
			for i in range(1, n+1):
				#
				# See which flavors are available for this drag
				#
				refnum = dragref.GetDragItemReferenceNumber(i)
				nflavor = dragref.CountDragItemFlavors(refnum)
				flavors = []
				for ii in range(1, nflavor+1):
					flavors.append(dragref.GetFlavorType(refnum, ii))
				#
				# And check whether we support any of them.
				#
				if 'hfs ' in flavors:
					try:
						fflags = dragref.GetFlavorFlags(refnum, 'hfs ')
					except Drag.Error:
						print 'Wrong type...', i, dragref.GetFlavorType(refnum, 1)
						MacOS.SysBeep()
						return
					datasize = dragref.GetFlavorDataSize(refnum, 'hfs ')
					data = dragref.GetFlavorData(refnum, 'hfs ', datasize, 0)
					tp, cr, flags, fss = self._decode_hfs_dropdata(data)
					fname = fss.as_pathname()
					try:
						func, arg = self._eventhandlers[DropFile]
					except KeyError:
						print 'No DropFile handler!'
						MacOS.SysBeep()
						return
					mw_globals.toplevel.settimer(0.1, (func, (arg, self, DropFile, (x, y, fname))))
				elif 'URLD' in flavors:
					try:
						fflags = dragref.GetFlavorFlags(refnum, 'URLD')
					except Drag.Error:
						print 'Wrong type...', i, dragref.GetFlavorType(refnum, 1)
						MacOS.SysBeep()
						return
					datasize = dragref.GetFlavorDataSize(refnum, 'URLD')
					data = dragref.GetFlavorData(refnum, 'URLD', datasize, 0)
					# Data is "url\rdescription"
					url = string.split(data, '\r')[0]
					try:
						func, arg = self._eventhandlers[DropURL]
					except KeyError:
						print 'No DropURL handler!'
						MacOS.SysBeep()
						return
					mw_globals.toplevel.settimer(0.1, (func, (arg, self, DropURL, (x, y, url))))
				else:
					print 'No supported flavors in drag item:', flavors
					MacOS.SysBeep()
					return
		except:
			if hasattr(sys, 'exc_info'):
				exc_type, exc_value, exc_traceback = sys.exc_info()
			else:
				exc_type, exc_value, exc_traceback = sys.exc_type, sys.exc_value, sys.exc_traceback
			import traceback
			print 'Error in Receive Handler:'
			print
			traceback.print_exception(exc_type, exc_value, None)
			traceback.print_tb(exc_traceback)

	def _decode_hfs_dropdata(self, data):
		tp = data[0:4]
		cr = data[4:8]
		flags = struct.unpack("h", data[8:10])
		fss = macfs.RawFSSpec(data[10:])
		return tp, cr, flags, fss
	
class _SubWindow(_CommonWindow):
	"""Window "living in" with a toplevel window"""

	def __init__(self, parent, wid, coordinates, defcmap = 0, pixmap = 0, 
			transparent = 0, z = 0, units = None, bgcolor=None):
		
		self._istoplevel = 0
		self._units = units
##		print 'DBG: subwindow, units=', units, 'coords=', coordinates
		_CommonWindow.__init__(self, parent, wid, z, bgcolor)
		
		x, y, w, h = parent._convert_coordinates(coordinates, units = units)
		xscrolloff, yscrolloff = parent._scrolloffset()
		x, y = x+xscrolloff, y+yscrolloff
		if parent._canscroll():
			raise 'Subwindow in scrollable parent not implemented'
		self._rect = x, y, w, h
		if w <= 0 or h <= 0:
			print 'Empty subwindow', coordinates
			coordinates = 0, 0, 1, 1
		self._sizes = coordinates
		
		self._transparent = transparent
		
		self.arrowcache = {}

		# XXXX pixmap to-be-done
		
		# XXXX Should we do redraw of parent or something??

	def settitle(self, title):
		"""Set window title"""
		raise error, 'can only settitle at top-level'
		
	def getgeometry(self, units=UNIT_MM):
		if units != self._units:
			print "getgeometry() with unexpected units:", units
		return self._sizes

	def _clipchanged(self):
		"""Called when the clipping region is possibly changed"""
		if not self._parent or not self._onscreen_wid:
			return
		self._parent._clipchanged()
		
	def _updatezorder(self, redraw=0, tobottom=0):
		"""Our Z-order has changed. Change the stacking order in our parent"""
		parent = self._parent
		if self in parent._subwindows:
			parent._subwindows.remove(self)
		if not tobottom:
			# Put at the top of our Z range
			for i in range(len(parent._subwindows)):
				if self._z >= parent._subwindows[i]._z:
					parent._subwindows.insert(i, self)
					break
			else:
				parent._subwindows.append(self)
		else:
			# Put at the bottom of our Z range
			for i in range(len(parent._subwindows)-1,-1,-1):
				if self._z <= parent._subwindows[i]._z:
					parent._subwindows.insert(i+1, self)
					break
			else:
				parent._subwindows.insert(0, self)		
		if redraw:
			parent._clipchanged()
			self._onscreen_wid.InvalWindowRect(self.qdrect())

	def pop(self, poptop=1):
		"""Pop to top of subwindow stack"""
		if not self._parent:
			return
		parent = self._parent
		if not parent._subwindows[0] is self:
			self._updatezorder(redraw=1)
		parent.pop(poptop)

	def push(self):
		"""Push to bottom of subwindow stack"""
		if not self._parent:
			return
		parent = self._parent
		if not parent._subwindows[-1] is self:
			self._updatezorderreverse(tobottom=1, redraw=1)
		parent.push()
		
	def _is_on_top(self):
		"""Return true if no other subwindow overlaps us"""
		if not self._parent:
			return 0
		# XXXX This is not good enough, really...
		return (self._parent._subwindows[0] is self)

	def _clipsubtractsiblings(self):
		# subtract our higher-stacked siblings and clip to our parent too
		if not self._parent:
			return
		# First clip ourselves to our parent.
		pclip = self._parent._mac_getclip(includechildren=1)
		Qd.SectRgn(self._clipincludingchildren, pclip, self._clipincludingchildren)
		# Next subtract our higher-stacked siblings recursively up
		ancestor = self
		while not ancestor._istoplevel:
			for w in ancestor._parent._subwindows:
				if w == ancestor:
					# Stop when we meet ourselves
					break
				r = w._getredrawguarantee()
				if r:
					Qd.DiffRgn(self._clipincludingchildren, r, self._clipincludingchildren)
					Qd.DisposeRgn(r)
			ancestor = ancestor._parent

	def _do_resize1(self):
		# calculate new size of subwindow after resize
		# close all display lists
		parent = self._parent
		## XXXX Should have crop=1?
		x, y, w, h = parent._convert_coordinates(self._sizes, units = self._units)
		xscrolloff, yscrolloff = parent._scrolloffset()
		x, y = x+xscrolloff, y+yscrolloff
		self._rect = x, y, w, h
##		w, h = self._sizes[2:]
##		if w == 0:
##			w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
##		if h == 0:
##			h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
##		hf, vf = self._scrollsizefactors()
		# We don't have to clear _clip, our parent did that.
		self._active_displist = None
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._do_resize1()
			
	def _add_control(self, ctl, callback, tracker=None):
		"""Add a control. Propagate up to the toplevel window"""
		self._parent._add_control(ctl, callback, tracker)
		
	def _del_control(self, ctl):
		"""Delete a control. Propagate up to the toplevel window"""
		self._parent._del_control(ctl)
		
	def _canscroll(self):
		"""Return true if this window or any of its ancestors is scrollable"""
		return self._parent._canscroll()

	def _enable_drop(self, onoff):
		raise 'Attempt to enable drop on subwindow'
		
class DialogWindow(_Window):
	def __init__(self, resid, title='', default=None, cancel=None,
				cmdbuttons=None, geometry=None):
		dlg = Dlg.GetNewDialog(resid, -1)
		wid = dlg.GetDialogWindow()
		self._dlg = dlg
		if cmdbuttons:
			self._item_to_cmd = cmdbuttons
		else:
			self._item_to_cmd = {}
		self._itemhandler = None
		if geometry:
			x, y, w, h = geometry
			print 'DialogWindow: move to', geometry, self
			# Magic mbarheight and titlebarheight. To be done better later.
			if x < 4: x = 4
			if y < 26 + 21: y = 26 + 21
			wid.MoveWindow(x, y, 0)
			# For dialogs we ignore w, h for now.
		else:
			x0, y0, x1, y1 = wid.GetWindowPort().portRect
			x, y, w, h = 0, 0, x1-x0, y1-y0
		cmdlist = [
			usercmd.COPY(callback=(dlg.DialogCopy, ())),
			usercmd.PASTE(callback=(dlg.DialogPaste, ())),
			usercmd.CUT(callback=(dlg.DialogCut, ())),
			usercmd.DELETE(callback=(dlg.DialogDelete, ())),
		]
		if not default is None:
			self._do_defaulthit = self._optional_defaulthit
			self.__default = default
			dlg.SetDialogDefaultItem(default)
		if callable(cancel):
			cmdlist.append(
				usercmd.CLOSE_WINDOW(callback=(cancel, ())))
		elif not cancel is None:
			self._do_cancelhit = self._optional_cancelhit
			self.__cancel = cancel
			cmdlist.append(
				usercmd.CLOSE_WINDOW(callback=(self._do_cancelhit, ())))
			dlg.SetDialogCancelItem(cancel)
		_Window.__init__(self, mw_globals.toplevel, wid, x, y, w, h, 
				commandlist=cmdlist, resizable=0)
		mw_globals.toplevel._register_wid(wid, self)
		Qd.SetPort(wid)
		self._widgetdict = {}
		self._is_shown = 0 # XXXX Is this always true??!?
		self.title = title
		
	def __repr__(self):
		return '<DialogWindow %s>'%self.title
	
	def show(self, geometry=None):
		if self.title:
			self.settitle(self.title)
		if geometry:
			x, y, w, h = geometry
			# Magic mbarheight and titlebarheight. To be done better later.
			if x < 4: x = 4
			if y < 26 + 21: y = 26 + 21
			self._onscreen_wid.MoveWindow(x, y, 0)
			# Ignore w, h for now
		self._dlg.AutoSizeDialog()	# Not sure whether this is a good idea for all dialogs...
		self._onscreen_wid.ShowWindow()
		self._onscreen_wid.SelectWindow() # test
		self._is_shown = 1
		
	def hide(self):
		self._onscreen_wid.HideWindow()
		self.grabdone()
		self.settitle(None)
		self._is_shown = 0
		
	def is_showing(self):
		return self._is_shown
		
	def close(self):
		# Note: there's something funny here. We should not close the widgets before
		# we close the window otherwise we get a crash later on in the program.
		# This is a bit funny, as the documentation and the MacPython implementation
		# suggests this could happen if we close the widgets _after_ the window.
		# (This is due to MacOS's ill-thought-out shortcut that a dispose of a window
		# will auto-dispose all controls in it).
		# So, the code here appears to work, but there may be a problem lurking here
		# somewhere.
		# XXXX Note: apparently the above isn't true, so the code is back to original.
		if not self._parent:
			return
		self.hide()
		widgets_to_close = self._widgetdict.values()
		for w in widgets_to_close:
			w.close()
		del widgets_to_close
		del self._widgetdict
		del self._item_to_cmd
		del self._itemhandler
		self._do_defaulthit = None
		self._do_cancelhit = None
		self.__default = None
		self.__cancel = None
		_Window.close(self)

	def getdialogwindowdialog(self):
		return self._dlg
		
	def grabdone(self):
		self.__grab_done = 1

	def rungrabbed(self):
		self.__grab_done = 0
		mw_globals.toplevel.grab(self)
		while not self.__grab_done:
			mw_globals.toplevel._eventloop(100)
		mw_globals.toplevel.grab(None)
		
	def addwidget(self, num, widget):
		self._widgetdict[num] = widget
		
	def set_itemhandler(self, handler):
		self._itemhandler = handler
		
	def do_itemhit(self, item, event):
		if self._item_to_cmd.has_key(item):
			self.call_command(self._item_to_cmd[item])
			return 1
		if self._itemhandler:
			if self._itemhandler(item, event):
				return 1
		print 'Dialog %s item %d event %s'%(self, item, event)
		return 0

	#
	# If the dialog has a default item the next method is copied to _do_defaulthit.
	# The event handling will then call this when return is pressed.
	#
	def _optional_defaulthit(self):
		ctl = self._dlg.GetDialogItemAsControl(self.__default)
		ctl.HiliteControl(Controls.inButton)
		self.do_itemhit(self.__default, None)
	#
	# Similarly for cancel, which is bound to close window (not to cmd-dot yet)
	#
	def _optional_cancelhit(self):
		ctl = self._dlg.GetDialogItemAsControl(self.__cancel)
		ctl.HiliteControl(Controls.inButton)
		self.do_itemhit(self.__cancel, None)
		
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
			
	def ListWidget(self, item, content=[], multi=0):
		widget = mw_widgets._ListWidget(self._dlg, item, content, multi)
##		self.addwidget(item, widget)
		return widget

	def ImageWidget(self, item, image=None):
		widget = mw_widgets._ImageWidget(self._dlg, item, image)
		self.addwidget(item, widget)
		return widget
		
	def SelectWidget(self, item, items=[], default=None, callback=None):
		widget = mw_widgets._SelectWidget(self._dlg, item, items, default, callback)
		self.addwidget(item, widget)
		return widget
		
	def AreaWidget(self, item, callback=None, scaleitem=None):
		widget = mw_widgets._AreaWidget(self._dlg, item, callback, scaleitem)
		self.addwidget(item, widget)
		return widget
	
	def set_commandlist(self, cmdlist):
		# First build the cmd->item mapping from the item->cmd mapping
		cmd_to_item = {}
		for item, cmd in self._item_to_cmd.items():
			cmd_to_item[cmd] = item
		# First pass: enable all commands featuring in cmdlist
		for item in cmdlist:
			cmd = item.__class__
			if cmd_to_item.has_key(cmd):
				item = cmd_to_item[cmd]
				cntl = self._dlg.GetDialogItemAsControl(item)
				cntl.ActivateControl()
				del cmd_to_item[cmd]
		# Second pass: disable the others
		for item in cmd_to_item.values():
			cntl = self._dlg.GetDialogItemAsControl(item)
			cntl.DeactivateControl()
		# And pass the command list on to the Window/Menu stuff
		_Window.set_commandlist(self, cmdlist)
