__version__ = "$Id$"

from Carbon import Win
from Carbon import Qd
from Carbon import Dlg
from Carbon import Evt
from Carbon import Events
from Carbon import Windows
from Carbon import Menu
MenuMODULE=Menu  # Silly name clash with FrameWork.Menu
from FrameWork import MenuBar, AppleMenu
from MiniAEFrame import AEServer
import MacOS
import sys
import MenuTemplate
import gestalt
from Carbon import Qt
from Carbon import QuickTime
from Carbon import Scrap
from Carbon import TE
from Carbon import AE

def _qtavailable():
	try:
		avail = gestalt.gestalt('qtim')
	except MacOS.Error:
		return 0
	return (avail != 0)
	
if not _qtavailable():
	Qt = None
	
def GetVideoSize(url):
	if not Qt:
		return 0,0
	import MMurl
	try:
		filename = MMurl.urlretrieve(url)[0]
	except IOError:
		return 0,0
	Qt.EnterMovies()
	try:
		movieResRef = Qt.OpenMovieFile(filename, 1)
	except (ValueError, Qt.Error), arg:
		print 'Cannot open QT movie:',filename, arg
		return 0, 0
	try:
		movie, d1, d2 = Qt.NewMovieFromFile(movieResRef, 0,
			QuickTime.newMovieDontResolveDataRefs)
	except (ValueError, Qt.Error), arg:
		print 'Cannot read QT movie:',filename, arg
		return 0, 0
	l, t, r, b = movie.GetMovieBox()
	return r-l, b-t
	
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
##_x_pixel_per_inch, _y_pixel_per_inch = Qd.ScreenRes()
_x_pixel_per_inch, _y_pixel_per_inch = 100.0, 100.0
_x_pixel_per_mm = _x_pixel_per_inch / 25.4
_y_pixel_per_mm = _y_pixel_per_inch / 25.4

#
# Height of menu bar and height of window title
#
_screen_top_offset = 26	# XXXX Should be gotten from GetMBarHeight()
_window_top_offset=21	# XXXX Is this always correct?
_l, _t, _r, _b = Qd.GetQDGlobalsScreenBits().bounds
DEFAULT_WIDTH, DEFAULT_HEIGHT = (_r-_l)/2, (_b-_t)/2
del _l, _t, _r, _b
#
# Event loop parameters
#

NO_AE_EVENTMASK=Events.everyEvent & ~Events.highLevelEventMask
AE_EVENTMASK=Events.everyEvent
#
TICKS_PER_SECOND=60.0	# Standard mac thing
MINIMAL_TIMEOUT=0	# How long we yield at the very least
MAXIMAL_TIMEOUT=int(0.5*TICKS_PER_SECOND)	# Check at least every half second
DOUBLECLICK_TIME=Evt.GetDblTime()

MEMORY_CHECK_INTERVAL=5		# Check memory every 5 seconds
MEMORY_WARN=1000000			# Warn if largest block < 1Mb
MEMORY_ALERT_ID=514

class _Event(AEServer):
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
		self._idles = {}
		self.__idleid = 0
		self._grabbed_wids = []
		self._active_movies = 0
		self._active_movie_windows = []
		self._mouse_tracker = None
		self._mouse_timer = None
		self._last_mouse_where = (-100, -100)
		self._last_mouse_when = -100
		self._eventmask = NO_AE_EVENTMASK
		l, t, r, b = Qd.GetQDGlobalsScreenBits().bounds
		self._draglimit = l+4, t+4+_screen_top_offset, r-4, b-4
		self.removed_splash = 0
		self._scrap_to_TE()
		AEServer.__init__(self)

	def grab(self, dialog):
		"""A dialog wants to be application-modal"""
		if dialog:
			self.grabwids([dialog._onscreen_wid])
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
		
	def setmousetimer(self, timerfunc, args):
		self.cancelmousetimer()
		self._mouse_timer = self.settimer(0.4, (timerfunc, args))
		
	def cancelmousetimer(self):
		if self._mouse_timer:
			self.canceltimer(self._mouse_timer)
			self._mouse_timer = None
			
	def clearmousetimer(self):
		self._mouse_timer = None
		
	def _enable_ae(self):
		"""Enable AppleEvent processing."""
		self._eventmask = AE_EVENTMASK
	
	def installaehandler(self, klass, type, callback):
		self._enable_ae()
		AEServer.installaehandler(self, klass, type, callback)
		
	def mainloop(self):
		"""The event mainloop"""
		last_memory_check = Evt.TickCount()
		self._initcommands()
		while 1:
			try:
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
					timeout = MAXIMAL_TIMEOUT
					
				if self.needmenubarredraw:
					MenuMODULE.DrawMenuBar()
					self.needmenubarredraw = 0
					
				# Clean up any stacktraces
				sys.exc_traceback = None
				sys.last_traceback = None
				
				if not self._eventloop(timeout):
					for rtn in self._idles.values():
						rtn()
			except SystemExit:
				raise
			except:
				if hasattr(sys, 'exc_info'):
					exc_type, exc_value, exc_traceback = sys.exc_info()
				else:
					exc_type, exc_value, exc_traceback = sys.exc_type, sys.exc_value, sys.exc_traceback
				import traceback, pdb, settings, version
				print
				print '\t-------------------------------------------------'
				print '\t| Fatal error - Please mail this output to      |'
				print '\t| grins-support@oratrix.com with a description  |'
				print '\t| of the circumstances.                         |'
				print '\t-------------------------------------------------'
				print '\tVersion:', version.version
				print
				traceback.print_exception(exc_type, exc_value, None)
				traceback.print_tb(exc_traceback)
				print
				msg = "A serious error has ocurred, see the log window for details.\nPlease save your work and exit GRiNS."
				if settings.get('debug'):
					msg = msg + '\nDo you want to enter the debugger?'
					showmessage(msg, mtype='question', callback=(pdb.post_mortem, (exc_traceback,)))
				else:
					showmessage(msg)
								
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
		gotone, event = Evt.WaitNextEvent(self._eventmask, timeout, region)
		
		if gotone:
			while gotone:
				if self._mouse_timer:
					self.cancelmousetimer()
				self._handle_event(event)
				if self._active_movies and Qt:
					Qt.MoviesTask(0)
					for w in self._active_movie_windows:
						w.changed()
				gotone, event = Evt.WaitNextEvent(self._eventmask, 0)
			if self._active_movies and Qt:
				Qt.MoviesTask(0)
				for w in self._active_movie_windows:
					w.changed()
			return 1
		else:
			if self._mouse_tracker:
				self._mouse_tracker(event)
			if self._active_movies and Qt:
				Qt.MoviesTask(0)
				for w in self._active_movie_windows:
					w.changed()
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
		elif what == Events.kHighLevelEvent:
			try:
				AE.AEProcessAppleEvent(event)
			except AE.Error, err:
				print 'Error in AppleEvent processing: ', err
		elif hasattr(MacOS, 'HandleEvent'):
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
		gotone, dlg, item = Dlg.DialogSelect(event)
		if gotone:
			wid = dlg.GetDialogWindow()
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
			if hasattr(MacOS, 'HandleEvent'):
				MacOS.HandleEvent(event)
			else:
				print 'DBG: unhandled event', event
		else:
			ourwin = self._find_wid(wid)
			if not ourwin:
				if hasattr(MacOS, 'HandleEvent'):
					MacOS.HandleEvent(event)
				else:
					print 'DBG: unhandled event', event
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
			if hasattr(MacOS, 'HandleEvent'):
				MacOS.HandleEvent(event)
			else:
				print 'DBG: unhandled event', event
		else:
			ourwin = self._find_wid(wid)
			if not ourwin:
				self._install_window_commands(None)
				if hasattr(MacOS, 'HandleEvent'):
					MacOS.HandleEvent(event)
				else:
					print 'DBG: unhandled event', event
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
		Scrap.ClearCurrentScrap()
		TE.TEToScrap()
	
	def _activate_ours(self, ourwin, activate):
		if activate:
			self._install_window_commands(ourwin)
##		else:
##			self._install_window_commands(None)
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
			if hasattr(MacOS, 'HandleEvent'):
				MacOS.HandleEvent(event)
			else:
				print 'DBG: unhandled event', event
			return
		if partcode == Windows.inGrow:
			# Since we don't draw the grow region usually there may
			# be content there. The user can click the content by using
			# the <option> key.
			if not (modifiers & Events.optionKey):
				window = self._find_wid(wid)
				if not window:
					if hasattr(MacOS, 'HandleEvent'):
						MacOS.HandleEvent(event)
					else:
						print 'DBG: unhandled event', event
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
				if modifiers & Events.controlKey:
					modifiername = 'contextual'
				elif modifiers & Events.shiftKey:
					modifiername = 'add'
				else:
					modifiername = None
				double = 0
				if when - self._last_mouse_when < DOUBLECLICK_TIME and not modifiername:
					x1, y1 = self._last_mouse_where
					x2, y2 = where
					if abs(x2-x1) < 5 and abs(y2-y1) < 5:
						double = 1
				if modifiername or double:
					# Reset the double-click timer
					self._last_mouse_where = -100, -100
					self._last_mouse_when = -100
				else:
					self._last_mouse_where = where
					self._last_mouse_when = when
				self._handle_contentclick(wid, 1, where, event, modifiername, double)
			else:
				if self._grabbed_wids and not wid in self._grabbed_wids:
					beep()
					wid = self._grabbed_wids[0]
				# Not frontmost. Activate.
				wid.SelectWindow()
				self._mouseregionschanged()
		elif partcode == Windows.inDrag:
			wid.DragWindow(where, self._draglimit)
			# Fixup for dragging non-grabbed windows:
			if self._grabbed_wids and not wid in self._grabbed_wids:
				wid = self._grabbed_wids[0]
				wid.SelectWindow()
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
			if hasattr(MacOS, 'HandleEvent'):
				MacOS.HandleEvent(event)
			else:
				print 'DBG: unhandled event', event

	def _handle_mouseup(self, event):
		"""Handle a MacOS mouseUp event"""
		what, message, when, where, modifiers = event
		partcode, wid = Win.FindWindow(where)
		if not wid:
			return
		if partcode == Windows.inContent:
			if wid == Win.FrontWindow():
				# Frontmost. Handle click.
				self._handle_contentclick(wid, 0, where, event, (modifiers & Events.controlKey), 0)

	def _handle_keydown(self, event):
		"""Handle a MacOS keyDown event"""
		if self._handle_menu_event(event):
				MenuMODULE.HiliteMenu(0)
				return
		(what, message, when, where, modifiers) = event
		c = chr(message & Events.charCodeMask)
		if not modifiers & Events.cmdKey:
			w = Win.FrontWindow()
			handled = self._handle_keyboardinput(w, c, where, event)
			if not handled:
				beep()
			return
		if hasattr(MacOS, 'HandleEvent'):
			MacOS.HandleEvent(event)
		else:
			print 'DBG: unhandled event', event
		
	def _handle_menu_event(self, event):
		result = MenuMODULE.MenuEvent(event)
		id = (result>>16) & 0xffff	# Hi word
		item = result & 0xffff		# Lo word
		if id:
			self._menubar.dispatch(id, item, None, event)
			return 1
		return 0

	def _do_user_item(self, dlg, item):
		"""Handle redraw for user items in dialogs"""
		wid = dlg.GetDialogWindow()
		try:
			win = self._wid_to_window[wid]
		except KeyError:
			print "Unknown dialog for user item redraw", wid, dlg, item
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
		self._timers.append((sec - t, cb, self._timer_id))
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
		
	def getcurtime(self):
		return Evt.TickCount()/TICKS_PER_SECOND
		
	def settimevirtual(self, virtual):
		pass
				
	def setidleproc(self, cb):
		"""Adds an idle-loop callback"""
		id = self.__idleid
		self.__idleid = self.__idleid + 1
		self._idles[id] = cb
		return id
		
	def cancelidleproc(self, id):
		"""Remove an idle-loop callback"""
		del self._idles[id]

	def lopristarting(self):
		"""Called when the scheduler starts with low-priority
		activities, may be used to do some redraws, etc"""
		self._eventloop(0)
		
	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		raise error, 'No select_setcallback for the mac'
		
	# Routine to maintain the number of currently active movies
	def _set_movie_active(self, is_active, which_window):
		if is_active:
			self._active_movies = self._active_movies + 1
			self._active_movie_windows.append(which_window)
		else:
			self._active_movies = self._active_movies - 1
			self._active_movie_windows.remove(which_window)
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
		self._next_xpos = 16
		self._next_ypos = 54
		self._command_handler = None
		self._cursor_is_default = 1
		self._cur_cursor = None		# The currently active cursor
		self._wtd_cursor = ''		# The wanted cursor
		self._menubar = None
		self._globalgroup = None
		self._commands_initialized = 0
		
	def _initcommands(self):
		if self._commands_initialized:
			return
		self._commands_initialized = 1
		for cmd in MenuTemplate.UNUSED_COMMANDS:
			mw_globals._all_commands[cmd] = 1
		self._command_handler = \
			  mw_menucmd.CommandHandler(MenuTemplate.MENUBAR)
		
	def close(self):
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		if self._globalgroup:
			self._command_handler.uninstall_cmd(CMDSET_GLOBAL,
							    self._globalgroup)
			self._globalgroup.close()
			self._globalgroup = None
		for group in self._windowgroups[:]:
			group.close()
		if self._command_handler:
			del self._command_handler
		self._clearall()

	def addclosecallback(self, func, args):
		"""Specify a routine to be called on termination"""
		self._closecallbacks.append((func, args))

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
		htext = d.GetDialogItemAsControl(mw_resources.ABOUT_VERSION_ITEM)
		import version
		Dlg.SetDialogItemText(htext, 'GRiNS ' + version.version)
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
		self._initcommands()
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
##				if __debug__:
##					if not group:
##						raise 'Window without a group?'
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
	
	def newwindow(self, x, y, w, h, title,
		      pixmap = 0, units=UNIT_MM,
		      adornments=None, canvassize=None, commandlist=[],
		      resizable=1, bgcolor=None):
		self._initcommands()
		extras = mw_windows.calc_extra_size(adornments, canvassize)
		wid, w, h = self._openwindow(x, y, w, h, title, units, resizable, extras)
		rv = mw_windows._Window(self, wid, 0, 0, w, h, 0, pixmap,
					title, adornments, canvassize,
					commandlist, resizable, bgcolor)
		self._register_wid(wid, rv)
		return rv
	
	newcmwindow = newwindow
##	def newcmwindow(self, x, y, w, h, title,
##			pixmap = 0, units=UNIT_MM,
##			adornments=None, canvassize=None, commandlist=[],
##			resizable=1):
##		self._initcommands()
##		extras = mw_windows.calc_extra_size(adornments, canvassize)
##		wid, w, h = self._openwindow(x, y, w, h, title, units, resizable, extras)
##		rv = mw_windows._Window(self, wid, 0, 0, w, h, 1, pixmap,
##					title, adornments, canvassize,
##					commandlist, resizable)
##		self._register_wid(wid, rv)
##		return rv
		
	def _openwindow(self, x, y, w, h, title, units, resizable=1, extras=(0,0,0,0)):
		"""Internal - Open window given xywh, title.
		Returns window-id"""
		extraw, extrah, minw, minh = extras
		if w <= 0 or h <= 0:
			units = UNIT_PXL
			w = DEFAULT_WIDTH
			h = DEFAULT_HEIGHT
			if w < minw:
				w = minw
			if h < minh:
				h = minh
		#
		# First determine x, y position
		#
		if x<0 or y<0 or x is None or y is None:
			x, y = self._next_window_pos()
		elif units == UNIT_MM:
			x = int(x*_x_pixel_per_mm)
			y = int(y*_y_pixel_per_mm)
		elif units == UNIT_PXL:
			pass
		elif units == UNIT_SCREEN:
			l, t, r, b = Qd.GetQDGlobalsScreenBits().bounds
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
			l, t, r, b = Qd.GetQDGlobalsScreenBits().bounds
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
		l, t, r, b = Qd.GetQDGlobalsScreenBits().bounds
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
			
		if resizable:
			defprocid = 0
		else:
			defprocid = 4
		wid = Win.NewCWindow((x, y, x1, y1), title, 1, defprocid, -1, 1, 0 )
		
		return wid, w, h
		
	def _next_window_pos(self):
		x = self._next_xpos
		y = self._next_ypos
		if x < 200:
			self._next_xpos = self._next_xpos + 20
		else:
			self._next_xpos = 16
		if y < 100:
			self._next_ypos = self._next_ypos + 28
		else:
			self._next_ypos = 44
		return x, y

	def _get_window_names(self):
		names = []
		current = None
		front_wid = Win.FrontWindow()
		for win in self._wid_to_window.values():
			if not win._title:
				# These are dialogs which aren't open yet
				continue
			if win._onscreen_wid == front_wid:
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
		if wid == Win.FrontWindow():
			self._install_window_commands(None)
		window = self._wid_to_window[wid]
		window.window_group = None
		self.needmenubarrecalc = 1
		self._command_handler.must_update_window_menu = 1
		self._mouseregionschanged()
		del self._wid_to_window[wid]
		
	def _is_last_in_group(self, wid):
		"""See if this window is the last one in the group"""
		window = self._wid_to_window[wid]
		group = window.window_group
		if not group:
##			print 'DBG: no group', window
			return 0	# Can't be last if no group
		for w in self._wid_to_window.values():
			if w == window:
				continue	# Skip the parameter window
			if w.window_group == group and w.is_showing():
##				print 'DBG: same group', window, w
				return 0	# Someone else
##		print 'DBG: last', window
		return 1
		
	def _call_optional_command(self, cmd):
		if self._command_handler.find_command(cmd):
			self._command_handler.normal_callback(cmd)
			return 1
		return 0
		
	def _find_wid(self, wid):
		"""Map a MacOS window to our window object, or None"""
		if self._wid_to_window.has_key(wid):
			return self._wid_to_window[wid]
		return None

	#
	# Handling of events that are forwarded to windows
	#
	
	def _handle_contentclick(self, wid, down, where, event, modifiers, double):
		"""A mouse-click inside a window, dispatch to the
		correct window"""
		window = self._find_wid(wid)
		if not window:
			return
		window._contentclick(down, where, event, modifiers, double)
		
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
		arrow_cursor = Qd.GetQDGlobalsArrow()
		hand_cursor = Qd.GetCursor(512).data
		resize_cursor = Qd.GetCursor(515).data
		watch_cursor = Qd.GetCursor(4).data

		channel = Qd.GetCursor(513).data
		link = Qd.GetCursor(514).data
		
		dragset = Qd.GetCursor(516).data
		dragadd = Qd.GetCursor(517).data
		dragnot = Qd.GetCursor(518).data
		
		#
		# These funny names are the X names for the cursors, used by the
		# rest of the code
		#
		self._cursor_dict={
			'stop': channel,
			'channel': channel,
			'link': link,
			'': arrow_cursor,
		# These are internal names, not user settable
			'_arrow': arrow_cursor,
			'_hand': hand_cursor,
			'_resize': resize_cursor,
			'_watch': watch_cursor,
		# These are for drag and drop only
			'dragadd': dragadd,
			'dragset': dragset,
			'dragnot': dragnot,
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
		
	def setdragcursor(self, cursor):
		"""Set cursor for the duration of a drag"""
		self._installcursor(cursor)

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

		frontwid = Win.FrontWindow()
		if frontwid and self._wid_to_window.has_key(frontwid):
			frontwindow = self._wid_to_window[frontwid]
		else:
			# The front window isn't ours. Use the arrow
			self._installcursor('_arrow')
			return None
		Qd.SetPort(frontwid)
		keys = Evt.GetKeys()
		option_pressed = (ord(keys[7]) & 4)
		lwhere = Evt.GetMouse()
		where = Qd.LocalToGlobal(lwhere)
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
##		print 'regions changed', which #DBG
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
##		print 'region not cached', which #DBG
		if which == 'inside':
			x0, y0, x1, y1 = frontwin.qdrect()
			Qd.SetPort(frontwin._onscreen_wid)
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
				Qd.SetPort(frontwin._onscreen_wid)
				x1, y1 = Qd.LocalToGlobal((x1, y1))
				Qd.RectRgn(rgn, (x1-15, y1-15, x1, y1))
		elif which == 'buttons':
			otherrgn = frontwin._get_button_region()
			rgn = Qd.NewRgn()
			Qd.CopyRgn(otherrgn, rgn)
			Qd.SetPort(frontwin._onscreen_wid)
			xglob, yglob = Qd.LocalToGlobal((0, 0))
			Qd.OffsetRgn(rgn, xglob, yglob)
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

	def getscreensize(self):
		l, t, r, b = Qd.GetQDGlobalsScreenBits().bounds
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
	
	def dumpwindows(self):
		for w in self._wid_to_window.values():
			w.dumpwindow()
