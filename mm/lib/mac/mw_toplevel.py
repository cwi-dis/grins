import Win
import Qd
import Dlg
import Evt
import Events
import Windows
import Menu
MenuMODULE=Menu  # Silly name clash with FrameWork.Menu
from FrameWork import MenuBar, AppleMenu
import MacOS
import sys
import MenuTemplate
import Qt

#
# Stuff we need from other mw_ modules
#
import mw_globals
from mw_globals import error
from mw_globals import UNIT_MM, UNIT_PXL, UNIT_SCREEN
from mw_globals import ReadMask, WriteMask
from mw_globals import FALSE, TRUE
import mw_resources
import mw_menucmd
import mw_windows

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

CMDSET_WINDOW, CMDSET_GROUP, CMDSET_GLOBAL = 0, 1, 2

def _beep():
	MacOS.SysBeep()

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
# Event loop parameters
#

EVENTMASK=0xffff
MINIMAL_TIMEOUT=0	# How long we yield at the very least
TICKS_PER_SECOND=60.0	# Standard mac thing


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
		"""A dialog wants to be application-modal"""
		if dialog:
			if self._grabbed:
				print 'Another window is already grabbed!'
				_beep()
				self._grabbed = None
				return
			self._grabbed = dialog._wid
		else:
			self._grabbed = None
					
	def mainloop(self):
		"""The event mainloop"""
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
		"""Do the eventloop once with timeout. If this returns
		an event continue looping without a timeout. This effectively
		waits and then reads all outstanding events"""
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
		#
		# First check for dialog events and handle those.
		#
		if Dlg.IsDialogEvent(event):
			if self._handle_dialogevent(event):
				return
		#
		# Otherwise decode and pass to the correct routine.
		#
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
			
	def _handle_dialogevent(self, event):
		what = event[0]
		if what == Events.keyDown:
			what, message, when, where, modifiers = event
			if modifiers & Events.cmdKey:
				return 0	# Let menu code handle it
			c = chr(message & Events.charCodeMask)
			#
			# Do default key processing
			#
			if c == '\r':
				wid = Win.FrontWindow()
				try:
					window = self._wid_to_window[wid]
				except KeyError:
					pass
				else:
					try:
						defaultcb = window._do_defaulthit
					except AttributeError:
						pass
					else:
						defaultcb()
						return 1
		gotone, wid, item = Dlg.DialogSelect(event)
		if gotone:
			if self._wid_to_window.has_key(wid):
				self._wid_to_window[wid].do_itemhit(item, event)
			else:
				print 'Dialog event for unknown dialog'
			return 1
		return 0		

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
					_beep()
					self._grabbed.SelectWindow()
					return
				# Frontmost. Handle click.
				self._handle_contentclick(wid, 1, where, event, (modifiers & Events.shiftKey))
			else:
				if self._grabbed and self._grabbed != wid:
					_beep()
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
				_beep()
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

	def _do_user_item(self, wid, item):
		"""Handle redraw for user items in dialogs"""
		try:
			win = self._wid_to_window[wid]
		except KeyError:
			print "Unknown dialog for user item redraw", wid, item
		else:
			try:
				redrawfunc = win.do_itemdraw
			except AttributeError:
				print "Dialog for user item redraw has no do_itemdraw()", win, item
			else:
				redrawfunc(item)
	#
	# timer interface
	#
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
		"""Called when the scheduler starts with low-priority
		activities, may be used to do some redraws, etc"""
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
	def __init__(self):
		_Event.__init__(self)
		_init_cursors()
		self._clearall()
		self._initmenu()
		
		MacOS.EnableAppswitch(0)
		
		Dlg.SetUserItemHandler(None)
		self._dialog_user_item_handler = \
		    Dlg.SetUserItemHandler(self._do_user_item)

	def _clearall(self):
		"""Code common to init and close"""
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
		self._menubar = None
		
	def _initcommands(self):
		for cmd in MenuTemplate.UNUSED_COMMANDS:
			mw_globals._all_commands[cmd] = 1
		self._command_handler = \
			  mw_menucmd.CommandHandler(MenuTemplate.MENUBAR)
		
	def close(self):
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		self._command_handler.uninstall_cmd(CMDSET_GLOBAL,
						    self._globalgroup)
		self._globalgroup.close()
		del self._globalgroup
		for group in self._windowgroups[:]:
			group.close()
		if self._command_handler:
			del self._command_handler
		self._clearall()
		MacOS.EnableAppswitch(1)

	def addclosecallback(self, func, args):
		"""Specify a routine to be called on termination"""
		self._closecallbacks.append(func, args)

	#
	# Menu and popup menu handling.
	#
	
	def _initmenu(self):
		self._menubar = MenuBar(self)
		AppleMenu(self._menubar, "About GRiNS...", self._mselect_about)
		self._menus = []
		
	def _addmenu(self, title):
		"""Add a menu to the menubar. Used by mw_menucmd"""
		m = mw_menucmd.MyMenu(self._menubar, title)
		self._menus.append(m)
		return m
		
	def _addpopup(self):
		m = mw_menucmd.MyPopupMenu(self._menubar)
		return m

	def _mselect_about(self, *args):
		d = Dlg.GetNewDialog(mw_resources.ABOUT_ID, -1)
		if not d:
			return
		w = d.GetDialogWindow()
		tp, h, rect = d.GetDialogItem(mw_resources.ABOUT_VERSION_ITEM)
		import version
		Dlg.SetDialogItemText(h, 'GRiNS ' + version.version)
		w.ShowWindow()
		d.DrawDialog()
		while 1:
			n = Dlg.ModalDialog(None)
			if n > 0:
				return
			print 'Huh? Selected', n

	#
	# Windowgroup handling
	#
	
	def windowgroup(self, title=None, cmdlist=[], globalgroup=0):
		rv = mw_windows._WindowGroup(title, cmdlist)
		self._windowgroups.append(rv)
		if globalgroup:
			level = CMDSET_GLOBAL
			self._globalgroup = rv
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
				if __debug__:
					raise 'Oops... Group is empty without invisible window...'
			
	#	
	# Menu/command handling
	#
	
	def _install_window_commands(self, window):
		"""Install window commands and document commands for
		corresponding document"""
		if self._command_handler.install_cmd(CMDSET_WINDOW, window):
			# We don't remove the group when the window
			# decativates, is this correct?
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

	#
	# Window handling.
	#
	
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = None, pixmap = 0, units=UNIT_MM,
		      adornments=None, canvassize=None, commandlist=[]):
		wid, w, h = self._openwindow(x, y, w, h, title, units)
		rv = mw_windows._Window(self, wid, 0, 0, w, h, 0, pixmap,
					title, adornments, canvassize,
					commandlist)
		self._register_wid(wid, rv)
		return rv

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE,
			type_channel = None, pixmap = 0, units=UNIT_MM,
			adornments=None, canvassize=None, commandlist=[]):
		wid, w, h = self._openwindow(x, y, w, h, title, units)
		rv = mw_windows._Window(self, wid, 0, 0, w, h, 1, pixmap,
					title, adornments, canvassize,
					commandlist)
		self._register_wid(wid, rv)
		return rv
		
	def _openwindow(self, x, y, w, h, title, units):
		"""Internal - Open window given xywh, title.
		Returns window-id"""
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
			# Keep room for the menubar
			y = y + _screen_top_offset
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
				
	#
	# Window ID (MacOS window handle) handling.
	#
	
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

	#
	# Handling of events that are forwarded to windows
	#
	
	def _handle_contentclick(self, wid, down, where, event, shifted):
		"""A mouse-click inside a window, dispatch to the
		correct window"""
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

	#
	# Cursor handling.
	#
	
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
			# Change the cursor when we're over the resize area,
			# unless option is pressed
			partcode, mwid = Win.FindWindow(where)
			if not option_pressed and wid == mwid and \
			   partcode == Windows.inGrow:
				wtd_cursor = _resize
			elif win._mouse_over_button(lwhere):
				wtd_cursor = _hand
		if wtd_cursor != self._cur_cursor: 
			Qd.SetCursor(wtd_cursor)
			self._cur_cursor = wtd_cursor


	#
	# Miscellaneous methods.
	#
	
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

	def getsize(self):
		return toplevel._mscreenwidth, toplevel._mscreenheight

	def _getmbarheight(self):
		return _screen_top_offset

	def _getmmfactors(self):
		return _x_pixel_per_mm, _y_pixel_per_mm
	
