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
import Scrap
import TE

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

CMDSET_WINDOW, CMDSET_GROUP, CMDSET_GLOBAL = 0, 1, 2

def beep():
	MacOS.SysBeep()

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
		self._grabbed_wids = []
		self._active_movies = 0
		self._mouse_tracker = None
		l, t, r, b = Qd.qd.screenBits.bounds
		self._draglimit = l+4, t+4+_screen_top_offset, r-4, b-4
		self.removed_splash = 0
		self._scrap_to_TE()

	def grab(self, dialog):
		"""A dialog wants to be application-modal"""
		if dialog:
			self.grabwids([dialog._wid])
		else:
			self.grabwids([])
			
	def grabwids(self, widlist):
		"""Grab a list of window-id's"""
		if not widlist:
			self._grabbed_wids = []
			return
		if self._grabbed_wids:
			print 'Another window is already grabbed!'
			beep()
			self._grabbed_wids = []
			return
		self._grabbed_wids = widlist[:]
		if not Win.FrontWindow() in self._grabbed_wids:
			self._grabbed_wids[0].SelectWindow()
			
	def setmousetracker(self, tracker):
		if tracker and self._mouse_tracker:
			raise 'Mouse tracker already active'
		self._mouse_tracker = tracker
					
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
					
			if self._idles or self._active_movies or self._mouse_tracker:
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
		self.setready()
		region = self._fixcursor()
		gotone, event = Evt.WaitNextEvent(EVENTMASK, timeout, region)
		
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
			if self._mouse_tracker:
				self._mouse_tracker(event)
			if self._active_movies:
				Qt.MoviesTask(0)
			if Dlg.IsDialogEvent(event):
				self._handle_dialogevent(event)
			if self.needmenubarrecalc and self._command_handler:
				self._command_handler.update_menus()
				self.needmenubarrecalc = 0
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
			# If there is a mouse tracker pass the event there in stead of
			# to the normal handler.
			if self._mouse_tracker:
				self._mouse_tracker(event)
			else:
				self._handle_mouseup(event)
		elif what == Events.keyDown:
			self._handle_keydown(event)
		elif what == Events.updateEvt:
			self._handle_update_event(event)
		elif what == Events.activateEvt:
			self._handle_activate_event(event)
		elif what == Events.osEvt:
			self._handle_os_event(event)
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
		self._mouseregionschanged()
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
				
	def _handle_os_event(self, event):
		what, message, when, where, modifiers = event
		which = (message >> 24) & 0xff
		if which == 1:
			# Suspend or resume event
			# XXXX We also get an activate event, don't we?
			is_resume = (message & 1)
			convert_clip = (message & 2)
			# Convert the TextEdit clipboard
			if convert_clip:
				if is_resume:
					self._scrap_to_TE()
				else:
					self._TE_to_scrap()
			if is_resume:
				self._cur_cursor = None
				self._mouseregionschanged()
			# Nothing else to do for suspend/resume
		# Nothing to do for mouse moved events
	
	def _scrap_to_TE(self):
		try:
			TE.TEFromScrap()
		except TE.Error:	# There may not be anything there...
			pass
		
	def _TE_to_scrap(self):
		Scrap.ZeroScrap()
		TE.TEToScrap()
	
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
			self._mouseregionschanged()
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
				if rv:
					newh, neww = (rv>>16) & 0xffff, rv & 0xffff
					window._zapregions()
					window._resize_callback(neww, newh)
					self._mouseregionschanged()
			else:
				partcode = Windows.inContent
		if partcode == Windows.inContent:
			frontwin = Win.FrontWindow()
			if wid == frontwin:
				# Check that we don't have a grabbed window that has been pushed behind
				if self._grabbed_wids and not frontwin in self._grabbed_wids:
					beep()
					self._grabbed_wids[0].SelectWindow()
					self._mouseregionschanged()
					return
				# Frontmost. Handle click.
				self._handle_contentclick(wid, 1, where, event, (modifiers & Events.shiftKey))
			else:
				if self._grabbed_wids and not wid in self._grabbed_wids:
					beep()
					wid = self._grabbed_wids[0]
				# Not frontmost. Activate.
				wid.SelectWindow()
				self._mouseregionschanged()
		elif partcode == Windows.inDrag:
			wid.DragWindow(where, self._draglimit)
			window = self._find_wid(wid)
			if window:
				window._zapregions()
			self._mouseregionschanged()
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
			self._mouseregionschanged()
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
		self._cached_regions = {}
		_Event.__init__(self)
		self._init_cursors()
		self._clearall()
		self._initmenu()
		
		MacOS.EnableAppswitch(0)
		
		Dlg.SetUserItemHandler(None)
		self._dialog_user_item_handler = \
		    Dlg.SetUserItemHandler(self._do_user_item)

	def _clearall(self):
		"""Code common to init and close"""
		self._TE_to_scrap()
		self._mouseregionschanged()
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
		self._cur_cursor = None		# The currently active cursor
		self._wtd_cursor = ''		# The wanted cursor
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
		extraw, extrah = mw_windows.calc_extra_size(adornments, canvassize)
		wid, w, h = self._openwindow(x, y, w, h, title, units, extraw, extrah)
		rv = mw_windows._Window(self, wid, 0, 0, w, h, 0, pixmap,
					title, adornments, canvassize,
					commandlist)
		self._register_wid(wid, rv)
		return rv

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE,
			type_channel = None, pixmap = 0, units=UNIT_MM,
			adornments=None, canvassize=None, commandlist=[]):
		extraw, extrah = mw_windows.calc_extra_size(adornments, canvassize)
		wid, w, h = self._openwindow(x, y, w, h, title, units, extraw, extrah)
		rv = mw_windows._Window(self, wid, 0, 0, w, h, 1, pixmap,
					title, adornments, canvassize,
					commandlist)
		self._register_wid(wid, rv)
		return rv
		
	def _openwindow(self, x, y, w, h, title, units, extraw=0, extrah=0):
		"""Internal - Open window given xywh, title.
		Returns window-id"""
		if w <= 0 or h <= 0:
			raise 'Illegal window size'
		#
		# First determine x, y position
		#
		if x is None or y is None:
			x = y = self.defaultwinpos
			self.defaultwinpos = self.defaultwinpos + 5
		elif units == UNIT_MM:
			x = int(x*_x_pixel_per_mm)
			y = int(y*_y_pixel_per_mm)
		elif units == UNIT_PXL:
			pass
		elif units == UNIT_SCREEN:
			l, t, r, b = Qd.qd.screenBits.bounds
			t = t + _screen_top_offset
			scrw = r-l
			scrh = b-t
			x = int(x*scrw+0.5)
			y = int(y*scrh+0.5)
		else:
			raise error, 'bad units specified'
		y = y + _screen_top_offset
		#
		# Next determine width, height
		#
		if units == UNIT_MM:
			w = int(w*_x_pixel_per_mm)
			h = int(h*_y_pixel_per_mm)
		elif units == UNIT_PXL:
			pass
		elif units == UNIT_SCREEN:
			l, t, r, b = Qd.qd.screenBits.bounds
			t = t + _screen_top_offset
			scrw = r-l
			scrh = b-t
			w = int(w*scrw)
			h = int(h*scrh)
		else:
			raise error, 'bad units specified'
		w = w + extraw
		h = h + extrah
			
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
			if not win._title:
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
		self._mouseregionschanged()
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
	def _init_cursors(self):
		#
		# The default cursor is either arrow or hand, and the resize cursor
		# is used when hovering over the resize area.
		#
		arrow_cursor = Qd.qd.arrow
		hand_cursor = Qd.GetCursor(512).data
		resize_cursor = Qd.GetCursor(515).data
		watch_cursor = Qd.GetCursor(4).data

		channel = Qd.GetCursor(513).data
		link = Qd.GetCursor(514).data
		
		#
		# These funny names are the X names for the cursors, used by the
		# rest of the code
		#
		self._cursor_dict={
			'stop': channel,
			'channel': channel,
			'link': link,
		# These are internal names, not user settable
			'_arrow': arrow_cursor,
			'_hand': hand_cursor,
			'_resize': resize_cursor,
			'_watch': watch_cursor
		}
		
		self._waiting = 0
		
	def setwaiting(self):
		"""About to embark on a long computation. Set the watch cursor"""
		if self._waiting:
			return
		self._waiting = 1
		self._installcursor('_watch')
		
	def setready(self):
		"""Ready for user input again. Make sure we use the correct cursor"""
		if not self._waiting:
			return
		self._waiting = 0
		# No need to update cursor, happens in next event loop passage

	def setcursor(self, cursor):
		"""Globally set the cursor for all windows"""
		if cursor == 'watch':
			cursor = ''
		if not self._cursor_dict.has_key(cursor):
			print 'Unknown cursor', cursor
			cursor = ''
		for win in self._subwindows:
			win.setcursor(cursor)
		# No need to update cursor, happens in next event loop passage

	def _installcursor(self, cursor):
		"""Low-level cursor change: set the cursor if different from what it is"""
		if cursor == self._cur_cursor:
##			print 'already installed', cursor
			return
##		print 'install', cursor
		self._cur_cursor = cursor
		Qd.SetCursor(self._cursor_dict[cursor])
			
	def _fixcursor(self):
		"""Select the correct cursor and display it"""
		if self._waiting:
			self._installcursor('_watch')
			return None

		keys = Evt.GetKeys()
		option_pressed = (ord(keys[7]) & 4)
		lwhere = Evt.GetMouse()
		where = Qd.LocalToGlobal(lwhere)
		frontwid = Win.FrontWindow()
		try:
			frontwindow = self._wid_to_window[frontwid]
		except KeyError:
			# The front window isn't ours. Use the arrow
			self._installcursor('_arrow')
			return None
		partcode, cursorwid = Win.FindWindow(where)
		#
		# First check whether we need the resize cursor
		#
		if cursorwid == frontwid and not option_pressed:
			rgn = self._mkmouseregion('grow', frontwindow)
			if Qd.PtInRgn(where, rgn):
				self._installcursor('_resize')
				return rgn
		#
		# Then check for point outside content area of front window
		#
		if not frontwid or frontwid != cursorwid or \
				(frontwid == cursorwid and partcode != Windows.inContent):
			self._installcursor('_arrow')
			return self._mkmouseregion('outside', frontwindow)
		wtd_cursor = frontwindow._wtd_cursor
		if wtd_cursor:
			self._installcursor(wtd_cursor)
			return self._mkmouseregion('inside', frontwindow)
		#
		# Next check whether we're inside a button or not
		#
		rgn = self._mkmouseregion('buttons', frontwindow)
		if Qd.PtInRgn(where, rgn):
			self._installcursor('_hand')
			return rgn
		self._installcursor('_arrow')
		return self._mkmouseregion('nobuttons', frontwindow)

	def _buttonschanged(self):
		"""Buttons have changed. Remove our cached regions and recompute next time"""
		self._mouseregionschanged('buttons', 'nobuttons')
		
	def _mouseregionschanged(self, *which):
		"""Clear mouse region cache, because windows have moved or buttons changed"""
##		print 'regions changed', which
		if not which:
			which = self._cached_regions.keys()
		for key in which:
			if not self._cached_regions.has_key(key):
				continue
			rgn = self._cached_regions[key]
			Qd.DisposeRgn(rgn)
			del self._cached_regions[key]
			
	def _mkmouseregion(self, which, frontwin):
		"""Make a mousetrap region and cache it"""
		try:
			return self._cached_regions[which]
		except KeyError:
			pass
##		print 'region not cached', which
		if which == 'inside':
			x0, y0, x1, y1 = frontwin.qdrect()
			Qd.SetPort(frontwin._wid)
			x0, y0 = Qd.LocalToGlobal((x0, y0))
			x1, y1 = Qd.LocalToGlobal((x1, y1))
			rgn = Qd.NewRgn()
			Qd.RectRgn(rgn, (x0, y0, x1, y1))
		elif which == 'outside':
			otherrgn = self._mkmouseregion('inside', frontwin)
			rgn = Qd.NewRgn()
			Qd.RectRgn(rgn, (-32767, -32767, 32767, 32767))
			Qd.DiffRgn(rgn, otherrgn, rgn)
		elif which == 'grow':
			rgn = Qd.NewRgn()
			if frontwin._needs_grow_cursor():
				x0, y0, x1, y1 = frontwin.qdrect()
				Qd.SetPort(frontwin._wid)
				x1, y1 = Qd.LocalToGlobal((x1, y1))
				Qd.RectRgn(rgn, (x1-15, y1-15, x1, y1))
		elif which == 'buttons':
			otherrgn = frontwin._get_button_region()
			rgn = Qd.NewRgn()
			Qd.CopyRgn(otherrgn, rgn)
		elif which == 'nobuttons':
			otherrgn1 = self._mkmouseregion('inside', frontwin)
			otherrgn2 = self._mkmouseregion('buttons', frontwin)
			rgn = Qd.NewRgn()
			Qd.DiffRgn(otherrgn1, otherrgn2, rgn)
		else:
			print 'Unknown region', which
			return None
		self._cached_regions[which] = rgn
		return rgn
		
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
		return self._mscreenwidth, self._mscreenheight

	def _getmbarheight(self):
		return _screen_top_offset

	def _getmmfactors(self):
		return _x_pixel_per_mm, _y_pixel_per_mm
	
