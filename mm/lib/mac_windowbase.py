__version__ = "$Id$"

import Win
import Qd
import Fm
import Dlg
import Evt
import Events
import Ctl
import Windows
import Menu
MenuMODULE=Menu  # Silly name clash with FrameWork.Menu
import MacOS
import string
import QuickDraw
import mac_image
import imgformat
import img
import imageop
import sys
from types import *

UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2

ENABLE_TRANSPARENT_IMAGES=1

# XXXX Or is it better to copy these?
from FrameWork import Menu, PopupMenu, MenuBar, AppleMenu, MenuItem, SubMenu
class MyMenuMixin:
	# We call our callbacks in a simpler way...
	def dispatch(self, id, item, window, event):
		title, shortcut, callback, type = self.items[item-1]
		if callback:
			apply(callback[0], callback[1])

class MyMenu(MyMenuMixin, Menu):
	pass

class MyPopupMenu(MyMenuMixin, PopupMenu):
	pass
	
class FullPopupMenu:
	def __init__(self, list, title = None, accelerators=None):
		self._themenu = toplevel._addpopup()
		self._fill_menu(self._themenu, list, accelerators)
		
	def delete(self):
		self._themenu.delete()
		self._themenu = None
		
	def _fill_menu(self, menu, list, accelerators):
		for item in list:
			if item is None:
				menu.addseparator()
			else:
				if len(item) == 3:
					char, itemstring, callback = item
				else:
					itemstring, callback = item
					char = ''
				if type(callback) == type([]):
					# Submenu
					m = menu.addsubmenu(itemstring)
					self._fill_menu(m, callback, accelerators)
				else:
					m = MenuItem(menu, itemstring, '', callback)
					if char and not accelerators is None:
						accelerators[char] = callback
						# We abuse the mark position for the shortcut (sigh...)
						m.setmark(ord(char))
						
	def popup(self, x, y, event, window=None):
		self._themenu.popup(x, y, event, window=window)

#
# The cursors we need
#
_arrow = Qd.qd.arrow
_watch = Qd.GetCursor(4).data

#
# ID's of resources
ABOUT_ID=512

#
# The fontfaces (which are unfortunately not defined in QuickDraw.py)
_qd_bold = 1
_qd_italic = 2

#
# Conversion factors for mm->pixels
#
_x_pixel_per_inch, _y_pixel_per_inch = Qd.ScreenRes()
_x_pixel_per_mm = _x_pixel_per_inch / 25.4
_y_pixel_per_mm = _y_pixel_per_inch / 25.4

#
# Height of menu bar and height of window title
#
_screen_top_offset = 26	# XXXX Should be gotten from GetMBarHeight()
_window_top_offset=18	# XXXX Is this always correct?

#
# Assorted constants
#
error = 'windowinterface.error'
Continue = 'Continue'
FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2
SINGLE, HTM, TEXT, MPEG = 0, 1, 2, 3

EVENTMASK=0xffff
MINIMAL_TIMEOUT=1	# How long we yield at the very least
TICKS_PER_SECOND=60.0	# Standard mac thing

_X=0
_Y=1
_WIDTH=2
_HEIGHT=3

_size_cache = {}

Version = 'mac'

from WMEVENTS import *

# Routines to save/restore complete textfont info
def checkfontinfo(wid, finfo):
	"""Return true if font info different from args"""
	port = wid.GetWindowPort()
	curfinfo = (port.txFont, port.txFace, port.txSize)
	return finfo <> curfinfo
	
def savefontinfo(wid):
	"""Return all font-pertaining info for a macos window"""
	port = wid.GetWindowPort()
	return port.txFont, port.txFace, port.txMode, port.txSize, port.spExtra
	
def restorefontinfo(wid, (font, face, mode, size, spextra)):
	"""Set all font-pertaining info for a macos window"""
	old = Qd.GetPort()
	Qd.SetPort(wid)
	Qd.TextFont(font)
	Qd.TextFace(face)
	Qd.TextMode(mode)
	Qd.TextSize(size)
	Qd.SpaceExtra(spextra)
	Qd.SetPort(old)

class _Event:
	"""This class is only used as a base-class for toplevel.
	the separation is for clarity only."""
	
	def __init__(self):
		# timer handling
		self.needmenubarredraw = 0
		self._timers = []
		self._timer_id = 0
		self._timerfunc = None
		self._time = Evt.TickCount()/TICKS_PER_SECOND
		self._idles = []
		l, t, r, b = Qd.qd.screenBits.bounds
		self._draglimit = l+4, t+4+_screen_top_offset, r-4, b-4
		self.removed_splash = 0

	def mainloop(self):
		while 1:
			while self._timers:
				t = Evt.TickCount()/TICKS_PER_SECOND
				sec, cb, tid = self._timers[0]
				sec = sec - (t - self._time)
				self._time = t
				# if sec <= 0:
				if sec <= 0.002:
					del self._timers[0]
					func, args = cb
					apply(func, args)
				else:
					self._timers[0] = sec, cb, tid
					break
					
			if self._idles:
				timeout = MINIMAL_TIMEOUT
			elif self._timers:
				timeout = int(self._timers[0][0]*TICKS_PER_SECOND)
			else:
				timeout = 100000
				
			if self.needmenubarredraw:
				MenuMODULE.DrawMenuBar()
				self.needmenubarredraw = 0
				
			# Clean up any stacktraces
			sys.exc_traceback = None
			sys.last_traceback = None
			
			if not self._eventloop(timeout):
				for rtn in self._idles:
					rtn()
								
	def _eventloop(self, timeout):
			if not self.removed_splash:
				import MacOS
				MacOS.splash()
				self.removed_splash = 1
			gotone, event = Evt.WaitNextEvent(EVENTMASK, timeout)
		
			if gotone:
				while gotone:
					self._handle_event(event)
					gotone, event = Evt.WaitNextEvent(EVENTMASK, 0)
				return 1
			return 0		
				
	def _handle_event(self, event):
		"""Handle a single MacOS event"""
		what, message, when, where, modifiers = event
		if what == Events.mouseDown:
			self._handle_mousedown(event)
		elif what == Events.mouseUp:
			self._handle_mouseup(event)
		elif what == Events.keyDown:
			self._handle_keydown(event)
		elif what == Events.updateEvt:
			wid = Win.WhichWindow(message)
			if not wid:
				MacOS.HandleEvent(event)
			else:
				ourwin = self._find_wid(wid)
				if not ourwin:
					MacOS.HandleEvent(event)
				else:
					Qd.SetPort(wid)
					wid.BeginUpdate()
					ourwin._redraw(wid.GetWindowPort().visRgn)
					wid.EndUpdate()
		elif what == Events.activateEvt:
			wid = Win.WhichWindow(message)
			if not wid:
				MacOS.HandleEvent(event)
			else:
				ourwin = self._find_wid(wid)
				if not ourwin:
					MacOS.HandleEvent(event)
				else:
					ourwin._activate(modifiers & 1)
		else:
			MacOS.HandleEvent(event)

	def _handle_mousedown(self, event):
		"""Handle a MacOS mouseDown event"""
		what, message, when, where, modifiers = event
		partcode, wid = Win.FindWindow(where)
		if partcode == Windows.inMenuBar:
			result = MenuMODULE.MenuSelect(where)
			id, item = (result>>16) & 0xffff, result & 0xffff
			self._menubar.dispatch(id, item, None, event)
			MenuMODULE.HiliteMenu(0)
			return
		if not wid:
			# It is not ours.
			MacOS.HandleEvent(event)
			return
		if partcode == Windows.inGrow:
			if modifiers & Events.controlKey:
				# Shift-click allows growing
				#wid.DrawGrowIcon()
				rv = wid.GrowWindow(where, (32, 32, 0x3fff, 0x3fff))
				neww, newh = (rv>>16) & 0xffff, rv & 0xffff
				print 'GROW RETURNED', neww, newh
				pass # XXXX find window, call resize, possibly send update?
			else:
				partcode = Windows.inContent
		if partcode == Windows.inContent:
			if wid == Win.FrontWindow():
				# Frontmost. Handle click.
				self._handle_contentclick(wid, 1, where, event, (modifiers & Events.shiftKey))
			else:
				# Not frontmost. Activate.
				wid.SelectWindow()
		elif partcode == Windows.inDrag:
			wid.DragWindow(where, self._draglimit)
		elif partcode == Windows.inGrow:
			pass # XXXX
		elif partcode == Windows.inGoAway:
			if not wid.TrackGoAway(where):
				return
			self._handle_goaway(wid)
		elif partcode == Windows.inZoomIn:
			pass # XXXX
		elif partcode == Windows.inZoomOut:
			pass # XXXX
		else:
			# In desk or syswindow. Pass on.
			MacOS.HandleEvent(event)

	def _handle_mouseup(self, event):
		"""Handle a MacOS mouseUp event"""
		what, message, when, where, modifiers = event
		partcode, wid = Win.FindWindow(where)
		if not wid:
			return
		if partcode == Windows.inContent:
			if wid == Win.FrontWindow():
				# Frontmost. Handle click.
				self._handle_contentclick(wid, 0, where, event, (modifiers & Events.shiftKey))

	def _handle_keydown(self, event):
		"""Handle a MacOS keyDown event"""
		(what, message, when, where, modifiers) = event
		c = chr(message & Events.charCodeMask)
		if modifiers & Events.cmdKey:
				result = MenuMODULE.MenuKey(ord(c))
				id = (result>>16) & 0xffff	# Hi word
				item = result & 0xffff		# Lo word
				if id:
					self._menubar.dispatch(id, item, None, event)
					return
#				elif c == 'w':
#					w = Win.FrontWindow()
#					if w:
#						self.do_close(w)
#					else:
#						if DEBUG: print 'Command-W without front window'
#				else:
#					if DEBUG: print "Command-" +`c`
		else:
			w = Win.FrontWindow()
			handled = self._handle_keyboardinput(w, c, where, event)
			if not handled:
				beep()
			return
		MacOS.HandleEvent(event)

	# timer interface
	def settimer(self, sec, cb):
		t0 = Evt.TickCount()/TICKS_PER_SECOND
		if self._timers:
			t, a, i = self._timers[0]
			t = t - (t0 - self._time) # can become negative
			self._timers[0] = t, a, i
		self._time = t0
		self._timer_id = self._timer_id + 1
		t = 0
		for i in range(len(self._timers)):
			time0, dummy, tid = self._timers[i]
			if t + time0 > sec:
				self._timers[i] = (time0 - sec + t, dummy, tid)
				self._timers.insert(i, (sec - t, cb, self._timer_id))
				return self._timer_id
			t = t + time0
		self._timers.append(sec - t, cb, self._timer_id)
		return self._timer_id

	def canceltimer(self, id):
		if id == None: return
		for i in range(len(self._timers)):
			t, cb, tid = self._timers[i]
			if tid == id:
				del self._timers[i]
				if i < len(self._timers):
					tt, cb, tid = self._timers[i]
					self._timers[i] = (tt + t, cb, tid)
				return
		raise 'unknown timer', id
				
	def setidleproc(self, cb):
		"""Adds an idle-loop callback"""
		self._idles.append(cb)
		
	def cancelidleproc(self, cb):
		"""Remove an idle-loop callback"""
		self._idles.remove(cb)

	def lopristarting(self):
		"""Called when the scheduler starts with low-priority activities, may be
		used to do some redraws, etc"""
		self._eventloop(0)
		
	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		raise error, 'No select_setcallback for the mac'

# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel(_Event):
	def __init__(self):
		_Event.__init__(self)
		self._closecallbacks = []
		self._subwindows = []
		self._wid_to_window = {}
		self._wid_to_title = {}
		self._bgcolor = 0xffff, 0xffff, 0xffff # white
		self._fgcolor =      0,      0,      0 # black
		self._hfactor = self._vfactor = 1.0
		self.defaultwinpos = 10	# 1 cm from topleft we open the first window

		self._initmenu()		
		MacOS.EnableAppswitch(0)
		
	def _initmenu(self):
		self._menubar = MenuBar(self)
		AppleMenu(self._menubar, "About CMIF...", self._mselect_about)
		self._menu_file = MyMenu(self._menubar, "File")
		self._mitem_quit = MenuItem(self._menu_file, "Quit", "Q", (self._mselect_quit, ()))
		self._mitem_abort = MenuItem(self._menu_file, "Abort", "", (self._mselect_abort, ()))
		self._mitem_debug = MenuItem(self._menu_file, "Debug", "", (self._mselect_debug, ()))
		self._menus = []
		
	def _addmenu(self, title):
		m = MyMenu(self._menubar, title)
		self._menus.append(m)
		return m
		
	def _addpopup(self):
		m = MyPopupMenu(self._menubar)
		return m
		
	def _mselect_quit(self):
		sys.exit(0)
		
	def _mselect_abort(self):
		raise 'User abort'
		
	def _mselect_debug(self):
		import pdb
		pdb.set_trace()

	def _mselect_about(self, *args):
		d = Dlg.GetNewDialog(ABOUT_ID, -1)
		if not d:
			return
		w = d.GetDialogWindow()
		port = w.GetWindowPort()
		l, t, r, b = port.portRect
		sl, st, sr, sb = Qd.qd.screenBits.bounds
		x = ((sr-sl) - (r-l)) / 2
		y = ((sb-st-16) - (b-t)) / 5
		w.MoveWindow(x, y, 0)
		w.ShowWindow()
		d.DrawDialog()
		while 1:
			n = Dlg.ModalDialog(None)
			if n == 1:
				return
		
	def close(self):
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		self.__init__()		# clears all lists
		MacOS.EnableAppswitch(1)

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	def newwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE,
				pixmap = 0, transparent = 0, units=UNIT_MM):
		wid, w, h = self._openwindow(x, y, w, h, title, units)
		rv = _Window(self, wid, 0, 0, w, h, 0, pixmap, transparent)
		self._register_wid(wid, rv, title)
		return rv

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE,
				pixmap = 0, transparent = 0, units=UNIT_MM):
		wid, w, h = self._openwindow(x, y, w, h, title, units)
		rv = _Window(self, wid, 0, 0, w, h, 1, pixmap, transparent)
		self._register_wid(wid, rv, title)
		return rv
		
	def _openwindow(self, x, y, w, h, title, units):
		"""Internal - Open window given xywh, title. Returns window-id"""
##		print 'TOPLEVEL WINDOW', x, y, w, h, title
		if w <= 0 or h <= 0:
			raise 'Illegal window size'
		if x is None or y is None:
			x = y = self.defaultwinpos
			self.defaultwinpos = self.defaultwinpos + 5
		if units == UNIT_MM:
			x = int(x*_x_pixel_per_mm)
			y = int(y*_y_pixel_per_mm) + _screen_top_offset
			w = int(w*_x_pixel_per_mm)
			h = int(h*_y_pixel_per_mm)
		elif units == UNIT_PXL:
			y = y + _screen_top_offset		# Keep room for the menubar
		elif units == UNIT_SCREEN:
			l, t, r, b = Qd.qd.screenBits.bounds
			t = t + _screen_top_offset
			scrw = r-l
			scrh = b-t
			x = int(x*scrw+0.5)
			y = int(y*scrh+0.5)+_screen_top_offset
			w = int(w*scrw)
			h = int(h*scrh)
		else:
			raise error, 'bad units specified'
			
		x1, y1 = x+w, y+h
		#
		# Check that it all fits
		#
		l, t, r, b = Qd.qd.screenBits.bounds
		if w >= (r-l)-8:
			w = (r-l)-8
		if h >= (b-t)-(_screen_top_offset + _window_top_offset + 4):
			h = (b-t)-(_screen_top_offset + _window_top_offset + 4)

		#
		# And force it on-screen.
		#
		x1, y1 = x+w, y+h

		if x < 4:
			diff = 4-x
			x, x1 = x + diff, x1 + diff
		if y < _screen_top_offset + _window_top_offset:
			diff = (_screen_top_offset + _window_top_offset) - y
			y, y1 = y+diff, y1+diff
		if x1 > r-4:
			diff = (r-4)-x1
			x, x1 = x+diff, x1+diff
		if y1 > b-4:
			diff = (b-4)-y1
			y, y1 = y+diff, y1+diff
			
		wid = Win.NewCWindow((x, y, x1, y1), title, 1, 0, -1, 1, 0 )
		
		return wid, w, h
		
	def _register_wid(self, wid, window, title):
		self._wid_to_window[wid] = window
		self._wid_to_title[wid] = title
		
	def _close_wid(self, wid):
		"""Close a MacOS window and remove references to it"""
		del self._wid_to_window[wid]
		del self._wid_to_title[wid]
		
	def _find_wid(self, wid):
		"""Map a MacOS window to our window object, or None"""
		if self._wid_to_window.has_key(wid):
			return self._wid_to_window[wid]
		return None
		
	def _handle_contentclick(self, wid, down, where, event, shifted):
		"""A mouse-click inside a window, dispatch to the correct window"""
		window = self._find_wid(wid)
		if not window:
			return
		window._contentclick(down, where, event, shifted)
		
	def _handle_keyboardinput(self, wid, char, where, event):
		window = self._find_wid(wid)
		if not window:
			return 0
		return window._keyboardinput(char, where, event)
		
	def _handle_goaway(self, wid):
		"""User asked to close a window. Dispatch to correct window"""
		window = self._find_wid(wid)
		if not window:
##			print 'No window for', wid #DBG
			return 0
		window._goaway()
		return 1

	def setcursor(self, cursor):
		if cursor == 'watch':
			Qd.SetCursor(_watch)
		else:
			Qd.SetCursor(_arrow)

	def pop(self):
		pass

	def push(self):
		pass

	def usewindowlock(self, lock):
		pass
		
	def getscreensize(self):
		l, t, r, b = Qd.qd.screenBits.bounds
		return (r-l), (b-t)
		
	def getscreendepth(self):
		# Unfortunately this is very difficult to get at...
		return 8
		
class _CommonWindow:
	"""Code common to toplevel window and subwindow"""
		
	def __init__(self, parent, wid, z=0):
		self._z = z
		for i in range(len(parent._subwindows)):
			if self._z >= parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.insert(0, self)
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
		
	def close(self):
		"""Close window and all subwindows"""
		if self._parent is None:
			return		# already closed
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

	def newwindow(self, (x, y, w, h), pixmap = 0, transparent = 0, z=0, type_channel = SINGLE):
		"""Create a new subwindow"""
		rv = _SubWindow(self, self._wid, (x, y, w, h), 0, pixmap, transparent, z)
		self._clipchanged()
		return rv

	def newcmwindow(self, (x, y, w, h), pixmap = 0, transparent = 0, z=0, type_channel = SINGLE):
		"""Create a new subwindow"""
		rv = _SubWindow(self, self._wid, (x, y, w, h), 1, pixmap, transparent, z)
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
		"""Return new, empty display list optionally specifying bgcolor"""
		if bgcolor != ():
			bgcolor = self._convert_color(bgcolor[0])
		else:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)

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
		self._popupmenu = FullPopupMenu(list, title, self._accelerators)

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

	def _prepare_image(self, file, crop, scale, center):
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
		x, y, width, height = self._rect
		
		if scale == 0:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
				    
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)

		
		if ENABLE_TRANSPARENT_IMAGES and hasattr(reader, 'transparent'):
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
			mask = (mac_image.mkbitmap(w, h, imgformat.xbmpacked, bitmap), bitmap)
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
		return (xim, image), mask, left, top, x, y, w - left - right, h - top - bottom

	def _convert_coordinates(self, coordinates):
		"""Convert fractional xywh in our space to pixel-xywh
		in toplevel-window relative pixels"""
		
		x, y = coordinates[:2]
##		if not (0 <= x <= 1 and 0 <= y <= 1):
##			raise error, 'coordinates out of bounds'
		px = int((self._rect[_WIDTH] - 1) * x + 0.5) + self._rect[_X]
		py = int((self._rect[_HEIGHT] - 1) * y + 0.5) + self._rect[_Y]
		if len(coordinates) == 2:
			return px, py
		w, h = coordinates[2:]
##		if not (0 <= w <= 1 and 0 <= h <= 1 and
##			0 <= x + w <= 1 and 0 <= y + h <= 1):
##			raise error, 'coordinates out of bounds'
		pw = int((self._rect[_WIDTH] - 1) * w + 0.5)
		ph = int((self._rect[_HEIGHT] - 1) * h + 0.5)
		return px, py, pw, ph
		
	def _convert_color(self, (r, g, b)):
		"""Convert 8-bit r,g,b tuple to 16-bit r,g,b tuple"""
		return r*0x101, g*0x101, b*0x101


	def qdrect(self):
		"""return our xywh rect (in pixels) as quickdraw ltrb style"""
		return self._rect[0], self._rect[1], self._rect[0]+self._rect[2], \
			self._rect[1]+self._rect[3]
			
	def _goaway(self):
		"""User asked us to go away. Tell upper layers (but don't go yet)"""
		try:
			func, arg = self._eventhandlers[WindowExit]
		except KeyError:
			sys.exc_traceback = None
##			print 'No WindowExit handler for', self #DBG
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
		
	def _contentclick(self, down, where, event, shifted):
		"""A click in our content-region. Note: this method is extended
		for top-level windows (to do global-to-local coordinate transforms)"""
		#
		# First see whether the click is in any of our children
		#
		for ch in self._subwindows:
			if Qd.PtInRect(where, ch.qdrect()):
				try:
					ch._contentclick(down, where, event, shifted)
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
		# It is really in our canvas. Do we have a low-level click handler?
		#
		if self._clickfunc:
			self._clickfunc(down, where, event)
			return
		#
		# Convert to our type of event and call the appropriate handler.
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
					handled = ch._keyboardinput(char, where, event)
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
					(child._transparent == -1 and child.active_displist):
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

class _Window(_CommonWindow):
	"""Toplevel window"""
	
	def __init__(self, parent, wid, x, y, w, h, defcmap = 0, pixmap = 0, 
			transparent = 0):
		
		self._istoplevel = 1
		_CommonWindow.__init__(self, parent, wid)
		
		if transparent:
			raise 'Error: transparent toplevel window'
		self._transparent = 0
		
		# Note: the toplevel init routine is called with pixel coordinates,
		# not fractional coordinates
		self._rect = 0, 0, w, h
		
		self._hfactor = parent._hfactor / (float(w) / _x_pixel_per_mm)
		self._vfactor = parent._vfactor / (float(h) / _y_pixel_per_mm)
		
	def settitle(self, title):
		"""Set window title"""
		if not self._wid:
			return  # Or raise error?
		self._wid.SetWTitle(title)
		
	def getgeometry(self, units=UNIT_MM):
		rect = self._wid.GetWindowPort().portRect
		Qd.SetPort(self._wid)
		x, y = Qd.LocalToGlobal((0,0))
		w, h = rect[2]-rect[0], rect[3]-rect[1]
		if units == UNIT_MM:
			rv = (float(x)/_x_pixel_per_mm, float(y-_screen_top_offset)/_y_pixel_per_mm,
				float(w)/_x_pixel_per_mm, float(h)/_y_pixel_per_mm)
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
		# subtract all subwindows, insofar they aren't transparent at the moment
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

class _SubWindow(_CommonWindow):
	"""Window "living in" with a toplevel window"""

	def __init__(self, parent, wid, coordinates, defcmap = 0, pixmap = 0, 
			transparent = 0, z = 0):
		
		self._istoplevel = 0
		_CommonWindow.__init__(self, parent, wid, z)
		
		x, y, w, h = parent._convert_coordinates(coordinates)
		self._rect = x, y, w, h
##		print 'subwin:', self._rect
		if w <= 0 or h <= 0:
			raise 'Empty subwindow', coordinates
		self._sizes = coordinates
		
		self._hfactor = parent._hfactor / self._sizes[_WIDTH]
		self._vfactor = parent._vfactor / self._sizes[_HEIGHT]
		
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			self._transparent = transparent
		
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
			parent._subwindows.insert(0, self)
		parent._clipchanged()
		Qd.SetPort(self._wid)
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
			parent._subwindows.append(self)
		parent._clipchanged()
		Qd.SetPort(self._wid)
		Win.InvalRect(self.qdrect())
		parent.push()

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

class _DisplayList:
	def __init__(self, window, bgcolor):
		self._window = window
		window._displists.append(self)
		self._bgcolor = bgcolor
		self._fgcolor = window._fgcolor
		self._linewidth = 1
		self._buttons = []
		self._list = []
		self._rendered = 0
		if self._window._transparent <= 0:
			self._list.append(('clear',))
		self._optimdict = {}
		self._cloneof = None
		self._clonestart = 0
		self._rendered = FALSE
		self._font = None
		self._old_fontinfo = None
		self._clonebboxes = []
		self._really_rendered = FALSE	# Set to true after the first real redraw
		
	def close(self):
		if self._window is None:
			return
		win = self._window
		for b in self._buttons[:]:
			b.close()
		win._displists.remove(self)
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			if win._transparent == -1 and win._parent:
				win._parent._clipchanged()
			if win._wid:
				Qd.SetPort(win._wid)
				Win.InvalRect(win.qdrect())
		self._window = None
		del self._cloneof
		try:
			del self._clonedata
		except AttributeError:
			pass
		del self._optimdict
		del self._list
		del self._buttons
		del self._font

	def is_closed(self):
		return self._window is None

	def clone(self):
		raise "Clone not implemented for mac_windowbase"
		
	def render(self):
		#
		# On the mac, we can only render after a full setup.
		# Hence, we schedule a redraw only
		#
		window = self._window
		self._rendered = 1
		# XXXX buttons?
		Qd.SetPort(window._wid)
		#
		# We make one optimization here: if we are a clone
		# and our parent is the current display list and
		# our parent has already been really rendered (i.e.
		# the update event has been received) we don't have
		# to send an InvalRect for the whole window area but
		# only for the bit that differs between clone and parent.
		#
		if self._cloneof and self._cloneof is window._active_displist \
				and self._cloneof._really_rendered and self._clonebboxes:
			for bbox in self._clonebboxes:
				Win.InvalRect(bbox)
			self._clonebboxes = []
		else:
			Win.InvalRect(window.qdrect())
		if window._transparent == -1:
			window._parent._clipchanged()
		window._active_displist = self
		
	def _render(self):
		self._really_rendered = 1
		self._window._active_displist = self
		Qd.RGBBackColor(self._bgcolor)
		Qd.RGBForeColor(self._fgcolor)
		Qd.EraseRect(self._window.qdrect())
		for i in self._list:
			self._render_one(i)
			
	def _render_one(self, entry):
		cmd = entry[0]
		window = self._window
		wid = window._wid
		
##		print '  ', cmd, entry[1:] #DBG
		if cmd == 'clear':
			Qd.EraseRect(window.qdrect())
##			print 'Erased', window.qdrect(),'to', wid.GetWindowPort().rgbBkColor
		elif cmd == 'fg':
			Qd.RGBForeColor(entry[1])
		elif cmd == 'font':
			entry[1]._setfont(wid)
		elif cmd == 'text':
			Qd.MoveTo(entry[1], entry[2])
			Qd.DrawString(entry[3]) # XXXX Incorrect for long strings
		elif cmd == 'image':
			mask, image, srcx, srcy, dstx, dsty, w, h = entry[1:]
			srcrect = srcx, srcy, srcx+w, srcy+h
			dstrect = dstx, dsty, dstx+w, dsty+h
##			print 'IMAGE', image[0], srcrect, dstrect
			Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
			if mask:
				Qd.CopyMask(image[0], mask[0], wid.GetWindowPort().portBits,
					srcrect, srcrect, dstrect)
			else:
				Qd.CopyBits(image[0], wid.GetWindowPort().portBits, srcrect, dstrect,
					QuickDraw.srcCopy+QuickDraw.ditherCopy, None)
			Qd.RGBBackColor(self._bgcolor)
		elif cmd == 'line':
			color = entry[1]
			points = entry[2]
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(color)
			apply(Qd.MoveTo, points[0])
			for np in points[1:]:
				apply(Qd.LineTo, np)
			Qd.RGBForeColor(fgcolor)
		elif cmd == 'box':
			x, y, w, h = entry[1]
			Qd.FrameRect((x, y, x+w, y+h))
		elif cmd == 'fbox':
			color = entry[1]
			x, y, w, h = entry[2]
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(color)
			Qd.PaintRect((x, y, x+w, y+h))
			Qd.RGBForeColor(fgcolor)
		elif cmd == 'linewidth':
			Qd.PenSize(entry[1], entry[1])
		else:
			raise 'Unknown displaylist command', cmd
						
	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		color = self._window._convert_color(color)
		self._list.append('fg', color)
		self._fgcolor = color


	def newbutton(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return _Button(self, coordinates)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0,
				    center = 1):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       w._prepare_image(file, crop, scale, center)
		if mask:
			self._imagemask = mask, src_x, src_y, dest_x, dest_y, width, height
		else:
##			raise 'kaboo kaboo'
##			r = Xlib.CreateRegion()
##			r.UnionRectWithRegion(dest_x, dest_y, width, height)
##			self._imagemask = r
			pass
		self._list.append('image', mask, image, src_x, src_y,
				  dest_x, dest_y, width, height)
		self._optimize(2)
##		print 'ADDED IMAGE', src_x, src_y, dest_x, dest_y, width, height
		self._update_bbox(dest_x, dest_y, dest_x+width, dest_y+height)
		x, y, w, h = w._rect
		return float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		xvalues = []
		yvalues = []
		for point in points:
			x, y = w._convert_coordinates(point)
			p.append(x,y)
			xvalues.append(x)
			yvalues.append(y)
		self._list.append('line', color, p)
		self._update_bbox(min(xvalues), min(yvalues), max(xvalues), max(yvalues))

	def drawbox(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._window._convert_coordinates(coordinates)
		self._list.append('box', (x, y, w, h))
		self._optimize()
		self._update_bbox(x, y, x+w, y+h)

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._window._convert_coordinates(coordinates)
		self._list.append('fbox', self._window._convert_color(color),
				(x, y, w, h))
		self._optimize(1)
		self._update_bbox(x, y, x+w, y+h)

	def drawmarker(self, color, coordinates):
		pass # XXXX To be implemented

	def usefont(self, fontobj):
		self._font = fontobj
		self._font._initparams(self._window._wid)
		self._list.append('font', fontobj)
		return self.baseline(), self.fontheight(), self.pointsize()

	def setfont(self, font, size):
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, margin = 0):
		return self.usefont(findfont(fontname, 10))

	def baseline(self):
		return self._font.baseline() * self._window._vfactor

	def fontheight(self):
		return self._font.fontheight() * self._window._vfactor

	def pointsize(self):
		return self._font.pointsize()

	def strsize(self, str):
		width, height = self._font.strsize(self._window._wid, str)
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
		old_fontinfo = None
		if self._font._checkfont(w._wid):
			old_fontinfo = savefontinfo(w._wid)
		self._font._setfont(w._wid)
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
			twidth = Qd.TextWidth(str, 0, len(str))
			self._curpos = x + float(twidth) / w._rect[_WIDTH], y
			self._update_bbox(x0, y0, x0+twidth, y0+int(height/self._window._vfactor))
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		if old_fontinfo:
			restorefontinfo(w._wid, old_fontinfo)
		return oldx, oldy, maxx - oldx, newy - oldy + height - base
		
	def _update_bbox(self, minx, miny, maxx, maxy):
		assert type(minx) == type(maxx) == type(miny) == type(maxy) == type(1)
		if minx > maxx:
			minx, maxx = maxx, minx
		if miny > maxy:
			miny, maxy = maxy, miny
		self._clonebboxes.append(minx, miny, maxx, maxy)
		
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
	def __init__(self, dispobj, coordinates, z=0):
		self._coordinates = coordinates
		self._dispobj = dispobj
		self._z = z
		buttons = dispobj._buttons
		for i in range(len(buttons)):
			if buttons[i]._z <= z:
				buttons.insert(i, self)
				break
		else:
			buttons.append(self)
		self._hicolor = self._color = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		if self._color == dispobj._bgcolor:
##			print 'not drawing button'
			return
##		print 'drawing button', self._color, dispobj._bgcolor
		self._dispobj.drawbox(coordinates)

	def close(self):
		if self._dispobj is None:
			return
		self._dispobj._buttons.remove(self)
		self._dispobj = None

	def is_closed(self):
		return self._dispobj is None

	def hiwidth(self, width):
		pass

	def hicolor(self, color):
		self._hicolor = color

	def highlight(self):
		pass

	def unhighlight(self):
		pass
		
	def _inside(self, x, y):
		bx, by, bw, bh = self._coordinates
		return (bx <= x <= bx+bw and by <= y <= by+bh)

_pt2mm = 25.4 / 72			# 1 inch == 72 points == 25.4 mm

_fontmap = {
	  'Times-Roman': ('Times', 0),
	  'Times-Italic': ('Times', _qd_italic),
	  'Times-Bold': ('Times', _qd_bold),

	  'Utopia': ('New York', 0),
	  'Utopia-Italic': ('New York', _qd_italic),
	  'Utopia-Bold': ('New York', _qd_bold),

	  'Palatino': ('Palatino', 0),
	  'Palatino-Italic': ('Palatino', _qd_italic),
	  'Palatino-Bold': ('Palatino', _qd_bold),

	  'Helvetica': ('Helvetica', 0),
	  'Helvetica-Bold': ('Helvetica', _qd_bold),
	  'Helvetica-Oblique': ('Helvetica', _qd_italic),

	  'Courier': ('Courier', 0),
	  'Courier-Bold': ('Courier', _qd_bold),
	  'Courier-Oblique': ('Courier', _qd_italic),
	  'Courier-Bold-Oblique': ('Courier', _qd_italic+_qd_bold),
	  
	  'Greek': ('GrHelvetica', 0),
	  'Greek-Bold': ('GrHelvetica', _qd_bold),
	  'Greek-Italic': ('GrHelvetica', _qd_italic),
	  }
	  
fonts = _fontmap.keys()

class findfont:
	def __init__(self, fontname, pointsize):
		if not _fontmap.has_key(fontname):
			raise error, 'Font not found: '+fontname
		self._fontnum = Fm.GetFNum(_fontmap[fontname][0])
		self._fontface = _fontmap[fontname][1]
		self._pointsize = pointsize
##DBG:		self._fontnum = 1; self._fontface = 0; self._pointsize = 0
		self._inited = 0
		
	def _getinfo(self):
		"""Get details of font (mac-only)"""
		return self._fontnum, self._fontface, self._pointsize
		
	def _setfont(self, wid):
		"""Set our font, saving the old one for later"""
		Qd.SetPort(wid)
		Qd.TextFont(self._fontnum)
		Qd.TextFace(self._fontface)
		Qd.TextSize(self._pointsize)
		
	def _checkfont(self, wid):
		"""Check whether our font needs to be installed in this wid"""
		return checkfontinfo(wid, (self._fontnum, self._fontface, self._pointsize))
		
	def _initparams(self, wid):
		"""Obtain font params like ascent/descent, if needed"""
		if self._inited:
			return
		self._inited = 1
		old_fontinfo = savefontinfo(wid)
		self._setfont(wid)
		self.ascent, self.descent, widMax, self.leading = Qd.GetFontInfo()
		restorefontinfo(wid, old_fontinfo)

	def close(self):
		pass

	def is_closed(self):
		return 0

	def strsize(self, wid, str):
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * (self.ascent + self.descent + self.leading)
		old_fontinfo = None
		if self._checkfont(wid):
			old_fontinfo = savefontinfo(wid)
		self._setfont(wid)
		for str in strlist:
			width = Qd.TextWidth(str, 0, len(str))
			if width > maxwidth:
				maxwidth = width
		if old_fontinfo:
			restorefontinfo(wid, old_fontinfo)
		return float(maxwidth) / _x_pixel_per_mm, \
		       float(maxheight) / _y_pixel_per_mm

	def baseline(self):
		return float(self.ascent+self.leading) / _y_pixel_per_mm

	def fontheight(self):
		return float(self.ascent + self.descent + self.leading) \
			/ _y_pixel_per_mm

	def pointsize(self):
		return self._pointsize

##class showmessage:
##	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
##		     cancelCallback = None, name = 'message',
##		     title = 'message'):
##		pass
##
##	def close(self):
##		pass

def showmessage(text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message'):
	import EasyDialogs
	EasyDialogs.Message(text)
	if callback:
		callback()
		
class Dialog:
	def __init__(self, *args):
		raise 'Dialogs not implemented for mac'

#
# Note: this class knows very well how it will be used.
# Especially, the way it handles the create_menu stuff is tied
# to the way the player creates it's menu.
#		
class MainDialog:
	def __init__(self, list, title = None, prompt = None, grab = 1,
		     vertical = 1):
		self.items = []
		self._channelmenu = None
		self._windowmenu = None
		self.menu = toplevel._addmenu('Control')
		self._createmenu(self.menu, list)
		
	def _createmenu(self, menu, list, ischannel=0):
		for item in list:
			if not item:
				menu.addseparator()
				self.items.append(None)
			else:
				title, callback = item[:2]
				shortcut = ''
##				if type(callback) == type(()):
##					m = MenuItem(menu, title, shortcut, callback)
##				else:
##					m = SubMenu(menu, title, title)
##					self._createmenu(m, callback)
				off = title[-6:] == ' (off)'
				if off:
					title = title[:-6]
				m = MenuItem(menu, title, shortcut, callback)
				if ischannel:
					m.check(not off)
				self.items.append(m)

	def close(self):
		pass

	def destroy_menu(self):
		if self._windowmenu:
			self._windowmenu.delete()
			self._windowmenu = None
		if self._channelmenu:
			self._channelmenu.delete()
			self._channelmenu = None

	def _flatten_menu(self, list):
		"""Flatten the menu (it is created with popups which we don't want)"""
		nlist = []
		for item in list:
			if type(item[1]) == type(()):
				nlist.append(item)
			else:
				nlist = nlist + self._flatten_menu(item[1])
		return nlist
		
	def create_menu(self, list, title = None):
		self.destroy_menu()
			
		channellist = self._flatten_menu(list)
		windowlist = []
		titles = toplevel._wid_to_title.values()
		for item in channellist:
			name = item[0]
			if name[-6:] == ' (off)':
				name = name[:-6]
			if name in titles:
				windowlist.append(item)
				

		self._windowmenu = toplevel._addmenu('Windows')
		self._createmenu(self._windowmenu, windowlist, 1)

		self._channelmenu = toplevel._addmenu('Channels')
		self._createmenu(self._channelmenu, channellist, 1)

	def getbutton(self, button):
		raise 'getbutton called'

	def setbutton(self, button, onoff = 1):
		self.items[button].check(onoff)

def multchoice(prompt, list, defindex):
	print 'MULTCHOICE', list, defindex
	return defindex

def beep():
	MacOS.SysBeep()
	#import pdb ; pdb.set_trace()
