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
import MenuTemplate
import Qt

UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2

ENABLE_TRANSPARENT_IMAGES=1

CMDSET_WINDOW, CMDSET_GROUP, CMDSET_GLOBAL = 0, 1, 2

RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH = 0, 1, 2

# XXXX Or is it better to copy these?
from FrameWork import Menu, PopupMenu, MenuBar, AppleMenu, MenuItem, SubMenu
class MyMenuMixin:
	# We call our callbacks in a simpler way...
	def dispatch(self, id, item, window, event):
		title, shortcut, callback, type = self.items[item-1]
		if callback:
			apply(callback[0], callback[1])

	def addsubmenu(self, label, title=''):
		sub = MyMenu(self.bar, title, -1)
		item = self.additem(label, '\x1B', None, 'submenu')
		self.menu.SetItemMark(item, sub.id)
		return sub

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
		self.toggle_values = []
		self.toggle_entries = []
		for item in list:
			if item is None:
				menu.addseparator()
			else:
				is_toggle_item = 0
				if len(item) > 3:
					char, itemstring, callback, tp = item[:4]
					if tp == 't':
						is_toggle_item = 1
						callback = (self.toggle_callback, (len(self.toggle_values), callback))
						if len(item) > 4:
							self.toggle_values.append(item[4])
						else:
							self.toggle_values.append(0)
				elif len(item) == 3:
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
					if is_toggle_item:
						self.toggle_entries.append(m)
						m.check(self.toggle_values[-1])
						
	def toggle_callback(self, index, (cbfunc, cbargs)):
		self.toggle_values[index] = not self.toggle_values[index]
		self.toggle_entries[index].check(self.toggle_values[index])
		apply(cbfunc, cbargs)
						
	def popup(self, x, y, event, window=None):
		self._themenu.popup(x, y, event, window=window)

class SelectPopupMenu(PopupMenu):
	def __init__(self, list):
		PopupMenu.__init__(self, toplevel._menubar)
		self.additemlist(list)

	def additemlist(self, list):
		for item in list:
			self.additem(item)
			
	def getpopupinfo(self):
		return self.menu, self.id
#
# The cursors we need
#
_arrow = Qd.qd.arrow
_watch = Qd.GetCursor(4).data
_hand = None
_channel = None
_link = None
_resize = None
CURSORS={}

def _init_cursors():
	global _hand, _channel, _link, _resize, CURSORS
	_hand = Qd.GetCursor(512).data
	_channel = Qd.GetCursor(513).data
	_link = Qd.GetCursor(514).data
	_resize = Qd.GetCursor(515).data
	
	# These funny names are the X names for the cursors, used by the
	# rest of the code
	CURSORS={
		'watch': _watch,
		'stop': _channel,
		'channel': _channel,
		'link': _link
	}

#
# ID's of resources
ABOUT_ID=512
ABOUT_VERSION_ITEM=2

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
MINIMAL_TIMEOUT=0	# How long we yield at the very least
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
		self.needmenubarrecalc = 0
		self._timers = []
		self._timer_id = 0
		self._timerfunc = None
		self._time = Evt.TickCount()/TICKS_PER_SECOND
		self._idles = []
		self._grabbed = None
		self._active_movies = 0
		l, t, r, b = Qd.qd.screenBits.bounds
		self._draglimit = l+4, t+4+_screen_top_offset, r-4, b-4
		self.removed_splash = 0

	def grab(self, dialog):
		if dialog:
			if self._grabbed:
				print 'Another window is already grabbed!'
				beep()
				self._grabbed = None
				return
			self._grabbed = dialog._wid
		else:
			self._grabbed = None
					
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
					
			if self._idles or self._active_movies:
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
				import splash
				splash.splash()
				self.removed_splash = 1
			gotone, event = Evt.WaitNextEvent(EVENTMASK, timeout)
		
			if gotone:
				while gotone:
					self._handle_event(event)
					if self._active_movies:
						Qt.MoviesTask(0)
					gotone, event = Evt.WaitNextEvent(EVENTMASK, 0)
				if self._active_movies:
					Qt.MoviesTask(0)
				return 1
			else:
				if self._active_movies:
					Qt.MoviesTask(0)
				if self.needmenubarrecalc and self._command_handler:
					self._command_handler.update_menus()
					self.needmenubarrecalc = 0
				self._fixcursor(event) # Should return a region
			return 0		
				
	def _handle_event(self, event):
		"""Handle a single MacOS event"""
		what = event[0]
		if what == Events.mouseDown:
			self._handle_mousedown(event)
		elif what == Events.mouseUp:
			self._handle_mouseup(event)
		elif what == Events.keyDown:
			self._handle_keydown(event)
		elif what == Events.updateEvt:
			self._handle_update_event(event)
		elif what == Events.activateEvt:
			self._handle_activate_event(event)
		else:
			MacOS.HandleEvent(event)
			
	def _handle_update_event(self, event, beginupdate=1):
		what, message, when, where, modifiers = event
		wid = Win.WhichWindow(message)
		if not wid:
			MacOS.HandleEvent(event)
		else:
			ourwin = self._find_wid(wid)
			if not ourwin:
				MacOS.HandleEvent(event)
			else:
				Qd.SetPort(wid)
				if beginupdate:
					wid.BeginUpdate()
				ourwin._redraw(wid.GetWindowPort().visRgn)
				if beginupdate:
					wid.EndUpdate()
	
	def _handle_activate_event(self, event):
		what, message, when, where, modifiers = event
		# XXXX Shouldn't be here, only on process switches
		self._cur_cursor = None	# We don't know the active cursor
		
		wid = Win.WhichWindow(message)
		if not wid:
			self._install_window_commands(None)
			MacOS.HandleEvent(event)
		else:
			ourwin = self._find_wid(wid)
			if not ourwin:
				self._install_window_commands(None)
				MacOS.HandleEvent(event)
			else:
				self._activate_ours(ourwin, modifiers&1)
		# We appear to miss activates, at least with the Sioux window
		# open (maybe Sioux gets them?). We simulate them when needed.
		if not (modifiers &1):
			wid = Win.FrontWindow()
			ourwin = self._find_wid(wid)
			if ourwin:
				self._activate_ours(ourwin, 1)
				
	def _activate_ours(self, ourwin, activate):
		if activate:
			self._install_window_commands(ourwin)
		ourwin._activate(activate)

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
			# Since we don't draw the grow region usually there may
			# be content there. The user can click the content by using
			# the <option> key.
			if not (modifiers & Events.optionKey):
				window = self._find_wid(wid)
				if not window:
					MacOS.HandleEvent(event)
					return
				rv = wid.GrowWindow(where, (32, 32, 0x3fff, 0x3fff))
				newh, neww = (rv>>16) & 0xffff, rv & 0xffff
				window._resize_callback(neww, newh)
			else:
				partcode = Windows.inContent
		if partcode == Windows.inContent:
			frontwin = Win.FrontWindow()
			if wid == frontwin:
				# Check that we don't have a grabbed window that has been pushed behind
				if self._grabbed and self._grabbed != wid:
					beep()
					self._grabbed.SelectWindow()
					return
				# Frontmost. Handle click.
				self._handle_contentclick(wid, 1, where, event, (modifiers & Events.shiftKey))
			else:
				if self._grabbed and self._grabbed != wid:
					beep()
					wid = self._grabbed
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
				self._handle_menu_key(c, event)
				MenuMODULE.HiliteMenu(0)
				return
		else:
			w = Win.FrontWindow()
			handled = self._handle_keyboardinput(w, c, where, event)
			if not handled:
				beep()
			return
		MacOS.HandleEvent(event)
		
	def _handle_menu_key(self, c, event):
		result = MenuMODULE.MenuKey(ord(c))
		id = (result>>16) & 0xffff	# Hi word
		item = result & 0xffff		# Lo word
		if id:
			self._menubar.dispatch(id, item, None, event)
			return 1
		return 0

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
		
	# Routine to maintain the number of currently active movies
	def _set_movie_active(self, is_active):
		if is_active:
			self._active_movies = self._active_movies + 1
		else:
			self._active_movies = self._active_movies - 1
		if self._active_movies < 0:
			raise 'Too many movies deactivated'
		
# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel(_Event):
	def __init__(self, closing=0):
		_Event.__init__(self)
		_init_cursors()
		self._closecallbacks = []
		self._subwindows = []
		self._windowgroups = []
		self._active_windowgroup = None
		self._wid_to_window = {}
		self._bgcolor = 0xffff, 0xffff, 0xffff # white
		self._fgcolor =      0,      0,      0 # black
		self._hfactor = self._vfactor = 1.0
		self.defaultwinpos = 10	# 1 cm from topleft we open the first window
		self._command_handler = None
		self._cursor_is_default = 1
		self._cur_cursor = None

		self._initmenu()		
		MacOS.EnableAppswitch(0)
		
	def _initmenu(self):
		self._menubar = MenuBar(self)
		AppleMenu(self._menubar, "About GRiNS...", self._mselect_about)
		self._menus = []
		
	def initcommands(self):
		self._command_handler = CommandHandler(MenuTemplate.MENUBAR)
		
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
##		port = w.GetWindowPort()
##		l, t, r, b = port.portRect
##		sl, st, sr, sb = Qd.qd.screenBits.bounds
##		x = ((sr-sl) - (r-l)) / 2
##		y = ((sb-st-16) - (b-t)) / 5
##		w.MoveWindow(x, y, 0)
		tp, h, rect = d.GetDialogItem(ABOUT_VERSION_ITEM)
		import version
		Dlg.SetDialogItemText(h, 'GRiNS ' + version.version)
		w.ShowWindow()
		d.DrawDialog()
		while 1:
			n = Dlg.ModalDialog(None)
			if n > 0:
				return
			print 'Huh? Selected', n
		
	def close(self):
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		for group in self._windowgroups[:]:
			group.close()
		if self._command_handler:
			del self._command_handler
		self.__init__(1)		# clears all lists
		MacOS.EnableAppswitch(1)

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	def windowgroup(self, title=None, cmdlist=[], globalgroup=0):
		rv = _WindowGroup(title, cmdlist)
		self._windowgroups.append(rv)
		if globalgroup:
			level = CMDSET_GLOBAL
		else:
			level = CMDSET_GROUP
		self._install_group_commands(rv, level)
		return rv
		
	def _close_windowgroup(self, group):
		self._windowgroups.remove(group)
		self._command_handler.uninstall_cmd(CMDSET_GROUP, group)
		self.needmenubarrecalc = 1
		
	def _get_group_names(self):
		names = []
		current = None
		for group in self._windowgroups[1:]: # Skip global commands
			if group == self._active_windowgroup:
				current = len(names)
			names.append(group._title)
		return names, current
		
	def _get_window_names(self):
		names = []
		current = None
		front_wid = Win.FrontWindow()
		for win in self._wid_to_window.values():
			if win._title == None:
				# These are dialogs which aren't open yet
				continue
			if win._wid == front_wid:
				current = len(names)
			names.append(win._title)
		return names, current
		
	def _pop_window(self, title):
		for win in self._subwindows:
			if win._title == title:
				win.pop()
				
	def _pop_group(self, title):
		for group in self._windowgroups:
			if group._title == title:
				break
		else:
			print 'Pop unknown group?', title
			return
		self._install_group_commands(group)
		# Pop all windows in the group. If the group has no
		# window we pop an invisible window (we know there is one)
		any_popped = 0
		invisible = None
		for win in self._subwindows:
			if win.window_group == group:
				if win._title:
					win.pop()
					any_popped = 1
				else:
					invisible = win
		if not any_popped:
			if invisible:
				invisible.pop()
			else:
				print 'Oops... Group is empty without invisible window...'
			
		
	# Menu/command handling
	def _install_window_commands(self, window):
		"""Install window commands and document commands for corresponding document"""
		if self._command_handler.install_cmd(CMDSET_WINDOW, window):
			# We don't remove the group when the window decativates, is this correct?
			if window:
				group = window.window_group
				if __debug__:
					if not group:
						raise 'Window without a group?'
				self._install_group_commands(group)
			self.needmenubarrecalc = 1
		
	def _install_group_commands(self, group, level=CMDSET_GROUP):
		if group == self._active_windowgroup:
			return
		self._command_handler.install_cmd(level, group)
		self._active_windowgroup = group
		self.needmenubarrecalc = 1
		
	def _changed_group_commands(self):
		self.needmenubarrecalc = 1
		
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE,
				pixmap = 0, units=UNIT_MM, adornments=None, canvassize=None,
				commandlist=None):
		wid, w, h = self._openwindow(x, y, w, h, title, units)
		rv = _Window(self, wid, 0, 0, w, h, 0, pixmap, title, adornments, canvassize, commandlist)
		self._register_wid(wid, rv)
		return rv

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE,
				pixmap = 0, units=UNIT_MM, adornments=None, canvassize=None,
				commandlist=None):
		wid, w, h = self._openwindow(x, y, w, h, title, units, menubar=[])
		rv = _Window(self, wid, 0, 0, w, h, 1, pixmap, title, adornments, canvassize, commandlist)
		self._register_wid(wid, rv)
		return rv
		
	def _openwindow(self, x, y, w, h, title, units):
		"""Internal - Open window given xywh, title. Returns window-id"""
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
		
	def _register_wid(self, wid, window):
		self._wid_to_window[wid] = window
		window.window_group = self._active_windowgroup
		
	def _close_wid(self, wid):
		"""Close a MacOS window and remove references to it"""
		window = self._wid_to_window[wid]
		window.window_group = None
		self.needmenubarrecalc = 1
		self._command_handler.must_update_window_menu = 1
		del self._wid_to_window[wid]
		
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
			return 0
		window._goaway()
		return 1

	def setcursor(self, cursor):
		if CURSORS.has_key(cursor):
			data = CURSORS[cursor]
			Qd.SetCursor(data)
			self._cursor_is_default = 0
		else:
			self._cursor_is_default = 1
			self._cur_cursor = None
##			self._fixcursor()
			
	def _fixcursor(self, event):
		"""Select watch or hand cursor"""
		if event:
			what, message, when, where, modifiers = event
			option_pressed = modifiers&Events.optionKey
		else:
			# XXXX Needed?
			raise 'kaboo kaboo'
		if not self._cursor_is_default:
			return
		wtd_cursor = _arrow
		wid = Win.FrontWindow()
		if self._wid_to_window.has_key(wid):
			win = self._wid_to_window[wid]
			Qd.SetPort(wid)
			lwhere = Qd.GlobalToLocal(where)
			# Change the cursor when we're over the resize area, unless
			# option is pressed
			partcode, mwid = Win.FindWindow(where)
			if not option_pressed and wid == mwid and partcode == Windows.inGrow:
				wtd_cursor = _resize
			elif win._mouse_over_button(lwhere):
				wtd_cursor = _hand
		if wtd_cursor != self._cur_cursor: 
			Qd.SetCursor(wtd_cursor)
			self._cur_cursor = wtd_cursor

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
		
class _WindowGroup:
	"""Menu-command mapping support"""
	def __init__(self, title, cmdlist):
		self._title = title
		self._cmds_toggled = {}
		self._dict = {}
		self.set_commandlist(cmdlist)
		
	def __repr__(self):
		return '<WindowGroup %s>'%self._title
	
	def settitle(self, title):
		self._title = title
		toplevel._changed_group_commands() # XXXX Is this good enough?
		
	def close(self):
		toplevel._close_windowgroup(self)
		del self._dict
		
	def create_menu(self, menu, title):
		pass
		
	def set_toggle(self, cmd, onoff):
		self._cmds_toggled[cmd] = onoff
		toplevel._changed_group_commands()
		
	def get_toggle(self, cmd):
		if self._cmds_toggled.has_key(cmd):
			return self._cmds_toggled[cmd]
		return 0
		
	def toggle_toggle(self, cmd):
		old = self.get_toggle(cmd)
		self.set_toggle(cmd, not old)
		
	def _set_cmd_dict(self, dict):
		self._dict = dict
		toplevel._changed_group_commands()
		
	def set_commandlist(self, list):
		dict = {}
		for item in list:
			cmd = item.__class__
			dict[cmd] = item
		self._set_cmd_dict(dict)
		
	def has_command(self, cmd):
		return self._dict.has_key(cmd)
		
	def get_command_callback(self, cmd):
		if self._dict.has_key(cmd):
			return self._dict[cmd].callback
		return None
		
class _ScrollMixin:
	"""Mixin class for scrollable/resizable windows"""
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
		toplevel._set_movie_active(isactive)
			
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
		return self._rect[0], self._rect[1], self._rect[0]+self._rect[2], \
			self._rect[1]+self._rect[3]
			
	def _goaway(self):
		"""User asked us to go away. Tell upper layers (but don't go yet)"""
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
					(child._transparent == -1 and child._active_displist):
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
		
# 		rv = _Window(self, wid, 0, 0, w, h, 1, pixmap, title, adornments, canvassize, commandlist)

class _Window(_CommonWindow, _WindowGroup, _ScrollMixin):
	"""Toplevel window"""
	
	def __init__(self, parent, wid, x, y, w, h, defcmap = 0, pixmap = 0, 
			title="", adornments=None, canvassize = None, commandlist=None):
		
		self._istoplevel = 1
		_CommonWindow.__init__(self, parent, wid)
		_WindowGroup.__init__(self, title, commandlist)
		
		self._transparent = 0
		
		# Note: the toplevel init routine is called with pixel coordinates,
		# not fractional coordinates
		w, h = _ScrollMixin.__init__(self, w, h, canvassize)
		self._rect = 0, 0, w, h
		
		self._hfactor = parent._hfactor / (float(w) / _x_pixel_per_mm)
		self._vfactor = parent._vfactor / (float(h) / _y_pixel_per_mm)
	
	def close(self):
		_ScrollMixin.close(self)
		_CommonWindow.close(self)
		# XXXX Not WindowGroup?
		
	def settitle(self, title):
		"""Set window title"""
		if not self._wid:
			return  # Or raise error?
		_WindowGroup.settitle(self, title)
		if title == None:
			title = ''
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
		
	def _activate(self, onoff):
		_CommonWindow._activate(self, onoff)
##		_WindowGroup._activate(self, onoff)
		_ScrollMixin._activate(self, onoff)

	def _resize_callback(self, width, height):
		x, y = self._rect[:2]
		width, height = self._resizescrollbars(width, height)
		self._rect = x, y, width, height
		# convert pixels to mm
		parent = self._parent
		self._hfactor = parent._hfactor / (float(width) / _x_pixel_per_mm)
		self._vfactor = parent._vfactor / (float(height) / _y_pixel_per_mm)
		for d in self._displists[:]:
			d.close()
		self._wid.SizeWindow(width, height, 1)
		self._clipchanged()
		for w in self._subwindows:
			w._do_resize1()
		# call resize callbacks
		self._do_resize2()


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
		##x, y, w, h = parent._convert_coordinates(self._sizes, crop = 1)
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
		if window._transparent == -1:
			window._parent._clipchanged()
		window._active_displist = self
		#
		# We make one optimization here: if we are a clone
		# and our parent is the current display list and
		# our parent has already been really rendered (i.e.
		# the update event has been received) we don't have
		# to send an InvalRect for the whole window area but
		# only for the bit that differs between clone and parent.
		#
		# XXXX This stopped working due to a mod by Sjoerd...
		if 0 and self._cloneof and self._cloneof is window._active_displist \
				and self._cloneof._really_rendered and self._clonebboxes:
			for bbox in self._clonebboxes:
				Win.InvalRect(bbox)
			self._clonebboxes = []
		elif self._can_render_now():
			if not window._clip:
				window._mkclip()
			saveclip = Qd.NewRgn()
			Qd.GetClip(saveclip)
			Qd.SetClip(window._clip)
			self._render()
			Qd.SetClip(saveclip)
			Qd.DisposeRgn(saveclip)
		else:
			Win.InvalRect(window.qdrect())
	
	def _can_render_now(self):
		"""Return true if we can do the render now, in stead of
		scheduling the update event"""
		##return 0
		# First check that no update events are pending.
		window = self._window
		rgn = Qd.NewRgn()
		window._wid.GetWindowUpdateRgn(rgn)
		ok = Qd.EmptyRgn(rgn)
		if ok:
			ok = window._is_on_top()
## Debug: show the region to update
##		if not ok:
##			Qd.RGBForeColor((0xffff, 0, 0))
##			Qd.PaintRgn(rgn)
##			Qd.RGBForeColor((0x0, 0, 0))
##			Qd.PaintRgn(rgn)
##			Qd.RGBForeColor((0xffff, 0, 0))
##			Qd.PaintRgn(rgn)
##			import time
##			MacOS.SysBeep()
##			time.sleep(2)
		Qd.DisposeRgn(rgn)
		return ok
		
	def _render(self):
		self._really_rendered = 1
		self._window._active_displist = self
		Qd.RGBBackColor(self._bgcolor)
		Qd.RGBForeColor(self._fgcolor)
		if self._window._transparent <= 0:
			Qd.EraseRect(self._window.qdrect())
		for i in self._list:
			self._render_one(i)
			
	def _render_one(self, entry):
		cmd = entry[0]
		window = self._window
		wid = window._wid
		
		if cmd == 'clear':
			Qd.EraseRect(window.qdrect())
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
				    center = 1, coordinates = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       w._prepare_image(file, crop, scale, center, coordinates)
		self._list.append('image', mask, image, src_x, src_y,
				  dest_x, dest_y, width, height)
		self._optimize(2)
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
			return
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
		     title = 'message', parent = None):
	import EasyDialogs
	if '\n' in text:
		text = string.join(string.split(text, '\n'), '\r')
	EasyDialogs.Message(text)
	if callback:
		callback()
		
class Dialog:
	def __init__(self, *args):
		raise 'Dialogs not implemented for mac'

def MainDialog(cmdlist, title=None, prompt=None, grab=1, vertical=1, globalgroup=0):
	return toplevel.windowgroup(title, cmdlist, globalgroup=globalgroup)

class _SpecialMenu:
	"""_SpecialMenu - Helper class for CommandHandler Window and Document menus"""
	
	def __init__(self, title, callbackfunc):
		self.items = []
		self.menus = []
		self.cur = None
		self.title = title
		self.callback = callbackfunc
		self.menu = toplevel._addmenu(self.title)
		
	def set(self, list, cur):
		if list != self.items:
			# If the list isn't the same we have to modify it
			if list[:len(self.items)] != self.items:
				# And if the old list isn't a prefix we start from scratch
				self.menus.reverse()
				for m in self.menus:
					m.delete()
				self.menus = []
				self.items = []
				self.cur = None
			list = list[len(self.items):]
			for item in list:
				self.menus.append(MenuItem(self.menu, item, None, (self.callback, (item,))))
				self.items.append(item)
		if cur != self.cur:
			if self.cur != None:
				self.menus[self.cur].check(0)
			if cur != None:
				self.menus[cur].check(1)
			self.cur = cur
		self.menu.enable(not not self.items)
				
class CommandHandler:
	def __init__(self, menubartemplate):
		self.cmd_to_menu = {}
		self.cmd_enabled = {}
		self.must_update_window_menu = 1
		self.must_update_document_menu = 1
		self.all_cmd_groups = [None, None, None]
		self.menubartraversal = []
		for menutemplate in menubartemplate:
			title, content = menutemplate
			menu = toplevel._addmenu(title)
			itemlist = self.makemenu(menu, content)
			self.menubartraversal.append(MenuTemplate.CASCADE, menu, itemlist)
		# Create special menus
		self.document_menu = _SpecialMenu('Documents', toplevel._pop_group)
		self.window_menu = _SpecialMenu('Windows', toplevel._pop_window)
			
	def install_cmd(self, number, group):
		if self.all_cmd_groups[number] == group:
			return 0
		self.all_cmd_groups[number] = group
		if number == 0:
			self.must_update_window_menu = 1
		else:
			self.must_update_document_menu = 1
		# Don't update, we do that in the event loop by calling
		# update_menus_enabled
		return 1
		
	def uninstall_cmd(self, number, group):
		if self.all_cmd_groups[number] == group:
			self.install_cmd(number, None)
			return 1
		if __debug__:
			if group in self.all_cmd_groups:
				raise 'Oops, group in wrong position!'
		return 0
			
	def makemenu(self, menu, content):
		itemlist = []
		for entry in content:
			entry_type = entry[0]
			if entry_type in (MenuTemplate.ENTRY, MenuTemplate.TOGGLE):
				dummy, name, shortcut, cmd = entry
				if self.cmd_to_menu.has_key(cmd):
					raise 'Duplicate menu command', (name, cmd)
				if entry_type == MenuTemplate.ENTRY:
					cbfunc = self.normal_callback
				else:
					cbfunc = self.toggle_callback
				mentry = MenuItem(menu, name, shortcut, (cbfunc, (cmd,)))
				self.cmd_to_menu[cmd] = mentry
				self.cmd_enabled[cmd] = 1
				itemlist.append(entry_type, cmd)
			elif entry_type == MenuTemplate.SEP:
				menu.addseparator()
			elif entry_type == MenuTemplate.CASCADE:
				dummy, name, subcontent = entry
				submenu = SubMenu(menu, name, name)
				subitemlist = self.makemenu(submenu, subcontent)
				itemlist.append(entry_type, submenu, subitemlist)
			else:
				raise 'Unknown menu entry type', entry_type
		return itemlist
				
	def toggle_callback(self, cmd):
		mentry = self.cmd_to_menu[cmd]
		group = self.find_toggle_group(cmd)
		if group:
			group.toggle_toggle(cmd) # Will force a menubar redraw later
		else:
			print 'HUH? No group for toggle cmd', cmd
		self.normal_callback(cmd)
		
	def normal_callback(self, cmd):
		cmd = self.find_command(cmd, mustfind=1)
		if cmd:
			func, arglist = cmd
			apply(func, arglist)
		else: # debug
			print 'CommandHandler: unknown command', cmd #debug
		
	def find_command(self, cmd, mustfind=0):
		for group in self.all_cmd_groups:
			if group:
				callback = group.get_command_callback(cmd)
				if callback:
					if mustfind and not self.cmd_enabled[cmd]: # debug
						print 'CommandHandler: disabled command selected:', cmd # debug
					return callback
		return None
		
	def find_toggle_group(self, cmd):
		for group in self.all_cmd_groups:
			if group and group.has_command(cmd):
					return group
		return None
		
	def _update_one(self, items):
		any_active = 0
		for item in items:
			itemtype = item[0]
			if itemtype == MenuTemplate.CASCADE:
				itemtype, submenu, subitems = item
				must_be_enabled = self._update_one(subitems)
				submenu.enable(must_be_enabled)
			else:
				itemtype, cmd = item
				must_be_enabled = (not not self.find_command(cmd))
				if must_be_enabled != self.cmd_enabled[cmd]:
					mentry = self.cmd_to_menu[cmd]
					mentry.enable(must_be_enabled)
					self.cmd_enabled[cmd] = must_be_enabled
				if must_be_enabled and itemtype == MenuTemplate.TOGGLE:
					mentry = self.cmd_to_menu[cmd]
					group = self.find_toggle_group(cmd)
					if group:
						mentry.check(group.get_toggle(cmd))
			if must_be_enabled:
				any_active = 1
		return any_active

	def update_menus(self):
		self._update_one(self.menubartraversal)
		if self.must_update_window_menu:
			self.update_window_menu()
			self.must_update_window_menu = 0
		if self.must_update_document_menu:
			self.update_document_menu()
			self.must_update_document_menu = 0
				
	def update_window_menu(self):
		list, cur = toplevel._get_window_names()
		self.window_menu.set(list, cur)
		
	def update_document_menu(self):
		list, cur = toplevel._get_group_names()
		self.document_menu.set(list, cur)
		
def multchoice(prompt, list, defindex):
	print 'MULTCHOICE', list, defindex
	return defindex

def beep():
	MacOS.SysBeep()
