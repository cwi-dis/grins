# Names that start with `_' are for internal use only.

import gl, GL, DEVICE
##_dev_map = {}
##for key in DEVICE.__dict__.keys():
##	val = DEVICE.__dict__[key]
##	if not _dev_map.has_key(val):
##		_dev_map[val] = key
##	else:
##		_dev_map[val] = _dev_map[val] + ' ' + key
import fm
import string
from EVENTS import *
_Accelerator = 1024
import os
debug = os.environ.has_key('WINDOWDEBUG')
import time, select

error = 'windowinterface.error'
Version = 'GL'

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

import sys

_has_fl = sys.modules.has_key('fl')
_last_forms = None

def startmonitormode():
	global _has_fl
	if _has_fl or sys.modules.has_key('fl'):
		import fl, glwindow
		_has_fl = 1
		fl.deactivate_all_forms()
		glwindow.stop_callback_mode()

def endmonitormode():
	global _has_fl
	if _has_fl or sys.modules.has_key('fl'):
		import fl, glwindow
		_has_fl = 1
		fl.activate_all_forms()
		glwindow.start_callback_mode()

def qread():
	global _last_forms, _has_fl
	if _has_fl or sys.modules.has_key('fl'):
		import fl, glwindow
		_has_fl = 1
		toplevel._win_lock.acquire()
		while not _last_forms:
			_last_forms = fl.do_forms()
		dev, val = fl.qread()
##		glwindow.dispatch(dev, val)
		toplevel._win_lock.release()
##		dev, val = 0, 0
	else:
		import gl
		dev, val = gl.qread()
	_last_forms = None
	return dev, val

def qtest():
	global _last_forms, _has_fl
	retval = None
	if _has_fl or sys.modules.has_key('fl'):
		import fl
		_has_fl = 1
		toplevel._win_lock.acquire()
		if not _last_forms:
			_last_forms = fl.check_forms()
		retval = fl.qtest()
		if retval:
			_last_forms = -1
		toplevel._win_lock.release()
	else:
		import gl
		retval = gl.qtest()
	return retval

def qdevice(dev):
	global _has_fl
	if _has_fl or sys.modules.has_key('fl'):
		import fl
		_has_fl = 1
		fl.qdevice(dev)
	else:
		import gl
		gl.qdevice(dev)

have_cl = have_jpeg = 0
try:
	import cl, CL
	have_cl = 1
except ImportError:
	try:
		import jpeg
		have_jpeg = 1
	except ImportError:
		pass

# Cursors
_ARROW = 0				# predefined
_WATCH = 1
_CHANNEL = 2
_LINK = 3
_STOP = 4

# Colors
_DEF_BGCOLOR = 255,255,255		# white
_DEF_FGCOLOR =   0,  0,  0		# black

_window_list = {}			# mapping from window ID to object
_image_cache = {}			# cache of prepared images
_cache_full = 0				# 1 if we shouldn't cache more images
_size_cache = {}
_drawbox = 0				# 1 to draw boxes around windows

gl.foreground()
_screenwidth = gl.getgdesc(GL.GD_XPMAX)
_screenheight = gl.getgdesc(GL.GD_YPMAX)
_mscreenwidth = gl.getgdesc(GL.GD_XMMAX)
_mscreenheight = gl.getgdesc(GL.GD_YMMAX)
if _screenwidth == 1024 and \
	  _screenheight == 768 and \
	  gl.getgdesc(GL.GD_BITS_NORM_SNG_RED) == 3 and \
	  gl.getgdesc(GL.GD_BITS_NORM_SNG_GREEN) == 3 and \
	  gl.getgdesc(GL.GD_BITS_NORM_SNG_BLUE) == 2:
	_is_entry_indigo = 1
else:
	_is_entry_indigo = 0

_watch = [0x0ff0, 0x1ff8, 0x381c, 0x718e,
	  0xe187, 0xc183, 0xc183, 0xc1f3,
	  0xc1f3, 0xc003, 0xc003, 0xe007,
	  0x700e, 0x381c, 0x1ff8, 0x0ff0,
	 ]

_channel = [0x0000, 0x0000, 0x0000, 0x0180,
	    0x0660, 0x1818, 0x6006, 0x8181,
	    0x8181, 0x6006, 0x1818, 0x0660,
	    0x0180, 0x0000, 0x0000, 0x0000
	 ]
_link = [0x0000, 0x7f80, 0x8040, 0x7e20,
	 0x1010, 0x0e10, 0x1010, 0x0e28,
	 0x1044, 0x0c82, 0x0304, 0x0248,
	 0x0110, 0x00a0, 0x0040, 0x0000
	]
_stop = [0x0000, 0x07c0, 0x1ff0, 0x3ff8,
	 0x7ffc, 0x7ffc, 0xfffe, 0xc006,
	 0xc006, 0xc006, 0xfffe, 0x7ffc,
	 0x7ffc, 0x3ff8, 0x1ff0, 0x07c0
	]
_watch.reverse()			# Turn it upside-down
gl.defcursor(_WATCH, _watch*8)
gl.curorigin(_WATCH, 8, 8)
_channel.reverse()			# Turn it upside-down
gl.defcursor(_CHANNEL, _channel*8)
gl.curorigin(_CHANNEL, 8, 8)
_link.reverse()
gl.defcursor(_LINK, _link*8)
gl.curorigin(_LINK, 0, 14)
_stop.reverse()
gl.defcursor(_STOP, _stop*8)
gl.curorigin(_STOP, 8, 8)

class _DummyLock:
	def acquire(self):
		pass
	def release(self):
		pass

class _Toplevel:
	def __init__(self):
		self._parent_window = None
		self._subwindows = []
		self._fgcolor = _DEF_FGCOLOR
		self._bgcolor = _DEF_BGCOLOR
		self._cursor = ''
		self._win_lock = _DummyLock()
		if debug: print 'TopLevel.__init__('+`self`+')'

	def close(self):
		if debug: print 'Toplevel.close()'
		import posix
		global _image_cache
		for win in self._subwindows[:]:
			win.close()
		for key in _image_cache.keys():
			try:
				posix.unlink(_image_cache[key][-1])
			except posix.error:
				pass
		_image_cache = {}

	def setcursor(self, cursor):
		if debug: print 'Toplevel.setcursor('+`cursor`+')'
		for win in self._subwindows:
			win.setcursor(cursor)
		self._cursor = cursor

	def newwindow(self, x, y, w, h, title):
		if debug: print 'Toplevel.newwindow'+`x, y, w, h, title`
		window = _Window(1, self, x, y, w, h, title)
		event._qdevice()
		dummy = event.testevent()
		return window

	newcmwindow = newwindow

	def pop(self):
		pass

	def push(self):
		pass

	def getsize(self):
		return _mscreenwidth, _mscreenheight

	def usewindowlock(self, lock):
		if debug: print `self`+'.usewindowlock()'
		if lock:
			self._win_lock = lock
		else:
			self._win_lock = _DummyLock()

	def getmouse(self):
		mx = gl.getvaluator(DEVICE.MOUSEX)
		my = _screenheight - gl.getvaluator(DEVICE.MOUSEY) - 1
		return float(mx) * _mscreenwidth / _screenwidth, \
			  float(my) * _mscreenheight / _screenheight


_box_message = """\
Use left mouse button to draw a box.
Click `Done' when ready or `Cancel' to cancel."""

# symbol used for returning
_box_finished = '_finished'

class _Boxes:
	def __init__(self, window, msg, callback, box):
		if len(box) == 1 and type(box) == type(()):
			box = box[0]
		if len(box) not in (0, 4):
			raise TypeError, 'bad arguments'
		if len(box) == 0:
			self.box = None
		else:
			self.box = box
		self.window = window
		self.callback = callback
		self.old_display = window._active_display_list
		window.pop()
		window._close_subwins()
		win = window
		fa1 = []
		fa2 = []
		while win:
			try:
				fa = win.getregister(Mouse0Press)
			except error:
				fa = None
			else:
				win.unregister(Mouse0Press)
			fa1.append(fa)
			try:
				fa = win.getregister(Mouse0Release)
			except error:
				fa = None
			else:
				win.unregister(Mouse0Release)
			fa2.append(fa)
			win = win._parent_window
		self.fa1 = fa1
		self.fa2 = fa2
		if not self.box:
			window.register(Mouse0Press, self.first_press, None)
		else:
			window.register(Mouse0Press, self.press, None)
		if self.old_display and not self.old_display.is_closed():
			d = self.old_display.clone()
		else:
			d = window.newdisplaylist()
		for win in window._subwindows:
			b = win._sizes
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self.display = d.clone()
		d.fgcolor(255, 0, 0)
		if box:
			d.drawbox(box)
		d.render()
		self.cur_display = d
		if msg:
			msg = msg + '\n\n' + _box_message
		else:
			msg = _box_message
		self._looping = 0
		self.dialog = Dialog(None, msg, 0, 0,
				[('', 'Done', (self.done_callback, ())),
				 ('', 'Cancel', (self.cancel_callback, ()))])

	def __del__(self):
		self.close()

	def close(self):
		self.window._open_subwins()
		if self.old_display and not self.old_display.is_closed():
			self.old_display.render()
		self.display.close()
		self.cur_display.close()
		self.dialog.close()

	def _size_cb(self, x, y, w, h):
		self.box = x, y, w, h

	def first_press(self, dummy, win, ev, val):
		win._sizebox((val[0], val[1], 0, 0), 0, 0, self._size_cb)
		win.register(Mouse0Press, self.press, None)
		self.after_press()

	def press(self, dummy, win, ev, val):
		x, y = val[0:2]
		b = self.box
		if b[0] + b[2]/4 < x < b[0] + b[2]*3/4:
			constrainx = 1
		else:
			constrainx = 0
		if b[1] + b[3]/4 < y < b[1] + b[3]*3/4:
			constrainy = 1
		else:
			constrainy = 0
		self.display.render()
		
		if constrainx and constrainy:
			self.box = win._movebox(b, 0, 0)
		else:
			if x < b[0] + b[2]/2:
				x0 = b[0] + b[2]
				w = -b[2]
			else:
				x0 = b[0]
				w = b[2]
			if y < b[1] + b[3]/2:
				y0 = b[1] + b[3]
				h = -b[3]
			else:
				y0 = b[1]
				h = b[3]
			win._sizebox((x0, y0, w, h),
				    constrainx, constrainy, self._size_cb)
		self.after_press()

	def after_press(self):
		d = self.display.clone()
		d.fgcolor(255, 0, 0)
		d.drawbox(self.box)
		d.render()
		self.cur_display.close()
		self.cur_display = d

	def loop(self):
		startmonitormode()
		self.window.setcursor('')
		try:
			try:
				self._looping = 1
				while 1:
					dummy = event.readevent()
			except _box_finished:
				return
		finally:
			endmonitormode()

	def done_callback(self):
		self.close()
		apply(self.callback, self.box)
		if self._looping:
			raise _box_finished

	def cancel_callback(self):
		self.close()
		apply(self.callback, ())
		if self._looping:
			raise _box_finished

class _Event:
	def __init__(self):
		self._queue = []
		self._curwin = None
		self._savemouse = None
		self._savex = None
		self._fdlist = []
		self._winfd = gl.qgetfd()
		self._nestingdepth = 0
		self._timers = []
		self._callbacks = {}
		self._windows = {}
		self._select_fdlist = []
		self._select_dict = {}
		self._timenow = time.time()
		self._timerid = 0
		self._modal = []
		if debug: print 'Event.__init__('+`self`+')'

	def _qdevice(self):
		if debug: print 'Event.qdevice()'
##		toplevel._win_lock.acquire()
		qdevice(DEVICE.REDRAW)
		qdevice(DEVICE.INPUTCHANGE)
		qdevice(DEVICE.WINQUIT)
		qdevice(DEVICE.WINSHUT)
		qdevice(DEVICE.KEYBD)
		qdevice(DEVICE.LEFTMOUSE)
		qdevice(DEVICE.MIDDLEMOUSE)
		qdevice(DEVICE.RIGHTMOUSE)
		gl.tie(DEVICE.LEFTMOUSE, DEVICE.MOUSEX, DEVICE.MOUSEY)
		gl.tie(DEVICE.MIDDLEMOUSE, DEVICE.MOUSEX, DEVICE.MOUSEY)
		gl.tie(DEVICE.RIGHTMOUSE, DEVICE.MOUSEX, DEVICE.MOUSEY)
##		toplevel._win_lock.release()

	def _checktime(self):
		timenow = time.time()
		timediff = timenow - self._timenow
		while self._timers:
			(t, arg, tid) = self._timers[0]
			t = t - timediff
			if t > 0:
				self._timers[0] = (t, arg, tid)
				self._timenow = timenow
				return
			# Timer expired, enter it in event queue.
			# Also, check next timer in timer queue (by looping).
			del self._timers[0]
			self._queue.append((None, TimerEvent, arg))
			timediff = -t	# -t is how much too late we were
		self._timenow = timenow # Fix by Jack

	def settimer(self, sec, arg):
		self._checktime()
		t = 0
		self._timerid = self._timerid + 1
		for i in range(len(self._timers)):
			time, dummy, tid = self._timers[i]
			if t + time > sec:
				self._timers[i] = (time - sec + t, dummy, tid)
				self._timers.insert(i, (sec - t, arg, self._timerid))
				return self._timerid
			t = t + time
		self._timers.append(sec - t, arg, self._timerid)
		return self._timerid

	def canceltimer(self, id):
		for i in range(len(self._timers)):
			t, arg, tid = self._timers[i]
			if tid == id:
				del self._timers[i]
				if i < len(self._timers):
					tt, arg, tid = self._timers[i]
					self._timers[i] = (tt + t, arg, tid)
				return
##		raise error, 'unknown timer id'

	def entereventunique(self, win, event, arg):
		if debug: print 'Event.entereventunique'+`win,event,arg`
		if (win, event, arg) not in self._queue:
			self._queue.append((win, event, arg))

	def enterevent(self, win, event, arg):
		if debug: print 'Event.enterevent'+`win,event,arg`
		self._checktime()
		self._queue.append((win, event, arg))

	def _readeventtimeout(self, timeout):
		if timeout == 0 or self._queue:
			if self._nestingdepth > 0:
				return
		self._nestingdepth = self._nestingdepth + 1
		try:
			if debug:
				print 'Event._readeventtimeout('+`timeout`+')'
			while qtest():
				dev, val = qread()
				self._dispatch(dev, val)
			if self._queue:
				timeout = 0
			fdlist = [self._winfd] + self._fdlist
			try:
				if timeout is None:
					ifdlist, ofdlist, efdlist = select.select(
						  fdlist, [], [])
				else:
					ifdlist, ofdlist, efdlist = select.select(
						  fdlist, [], [], timeout)
			except select.error, msg:
				if type(msg) == type(()) and msg[0] == 4:
					# ignode EINTR
					ifdlist = []
				else:
					# re-raise exception
					raise select.error, msg
			for fd in ifdlist:
				if fd in self._fdlist:
					self.entereventunique(None, FileEvent,
						  fd)
			while qtest():
				dev, val = qread()
				self._dispatch(dev, val)
		finally:
			self._nestingdepth = self._nestingdepth - 1

	def _readevent(self):
		if debug: print 'Event._readevent()'
		self._readeventtimeout(None)

	def _getevent(self, timeout):
		import time
		if debug > 1: print 'Event._getevent('+`timeout`+')'
		t0 = time.time()
		if self._queue:
			timeout = 0	# force collecting events w/out waiting
		while 1:
			if timeout is not None:
				t1 = time.time()
				timeout = timeout - (t1 - t0)
				if timeout < 0:
					timeout = 0
				t0 = t1
			self._readeventtimeout(timeout)
			for winkey in _window_list.keys():
				win = _window_list[winkey]
				if win._must_redraw:
					win._redraw()
			if self._queue:
				return 1
			if timeout is not None and timeout <= 0:
				return 0

	def _dispatch(self, dev, val):
		if (dev, val) == (0, 0):
			return
##		print 'dispatch',
##		if _dev_map.has_key(dev):
##			print _dev_map[dev],
##		else:
##			print `dev`,
##		print `val`
		if debug: print 'Event._dispatch'+`dev,val`
		if dev == DEVICE.INPUTCHANGE:
			self._savemouse = None
			if val == 0:
				self._curwin = None
			elif not _window_list.has_key(val):
				self._curwin = None
			else:
				self._curwin = _window_list[val]
				return
		elif dev == DEVICE.REDRAW:
			self._savemouse = None
			if _window_list.has_key(val):
				win = _window_list[val]
				win._must_redraw = 1
				if win._parent_window == toplevel:
					toplevel._win_lock.acquire()
					gl.winset(win._window_id)
					w, h = gl.getsize()
					toplevel._win_lock.release()
					if (w, h) != (win._width, win._height):
						win._resize()
				return
		elif dev == DEVICE.KEYBD:
			self._savemouse = None
			if self._curwin:
				if gl.getvaluator(DEVICE.LEFTALTKEY) or \
				   gl.getvaluator(DEVICE.RIGHTALTKEY):
					val = val + 128
				self._queue.append((self._curwin, KeyboardInput, chr(val)))
				return
		elif dev in (DEVICE.LEFTMOUSE, DEVICE.MIDDLEMOUSE, DEVICE.RIGHTMOUSE):
			if self._curwin:
				self._savemouse = dev, val
				return
		elif dev == DEVICE.MOUSEX:
			if self._curwin:
				self._savex = val
				return
		elif dev == DEVICE.MOUSEY:
			if self._curwin:
				if not self._savemouse:
					return
				if self._curwin.is_closed():
					return
				y = val
				dev, val = self._savemouse
				x = self._savex
				toplevel._win_lock.acquire()
				gl.winset(self._curwin._window_id)
				x0, y0 = gl.getorigin()
				toplevel._win_lock.release()
				x = float(x - x0) / self._curwin._width
				y = 1.0 - float(y - y0) / self._curwin._height
				if x < 0 or x > 1 or y < 0 or y > 1:
					print 'mouse click outside of window'
				buttons = []
				adl = self._curwin._active_display_list
				if adl:
					for but in adl._buttonlist:
						if but._inside(x, y):
							buttons.append(but)
				if dev == DEVICE.LEFTMOUSE:
					if val:
						dev = Mouse0Press
					else:
						dev = Mouse0Release
				elif dev == DEVICE.MIDDLEMOUSE:
					if val:
						dev = Mouse1Press
					else:
						dev = Mouse1Release
				else:
					if val:
						dev = Mouse2Press
					else:
						dev = Mouse2Release
				self._queue.append(self._curwin, dev,
						   (x, y, buttons))
				return
		elif dev in (DEVICE.WINSHUT, DEVICE.WINQUIT):
			self._queue.append((self._curwin, WindowExit, None))
			return
##		self._queue.append((self._curwin, dev, val))
		import sys
		if sys.modules.has_key('glwindow'):
			import glwindow
			glwindow.handle_event(dev, val)

	def _doevent(self, dev, val):
		if debug: print 'Event._doevent'+`dev,val`
		self._dispatch(dev, val)
		for winkey in _window_list.keys():
			win = _window_list[winkey]
			if win._must_redraw:
				win._redraw()
		
	def _trycallback(self):
		if not self._queue:
			raise error, 'internal error: event expected'
		window, event, value = self._queue[0]
		if self._modal and event != ResizeWindow:
			if type(self._modal[-1]) in (type(()), type([])):
				if window not in self._modal[-1]:
					return 0
			else:
				if window is not self._modal[-1]:
					return 0
		if event == FileEvent:
			if self._select_dict.has_key(value):
				del self._queue[0]
				func, arg = self._select_dict[value]
				apply(func, arg)
				return 1
		if window and window.is_closed():
			return 0
		if event == KeyboardInput:
			key = (window, _Accelerator)
			if self._windows.has_key(key):
				accdict, dummy = self._windows[key]
				if accdict.has_key(value):
					del self._queue[0]
					func, arg = accdict[value]
					apply(func, arg)
					return 1
		for w in [window, None]:
			while 1:
				for key in [(w, event), (w, None)]:
					if self._windows.has_key(key):
						del self._queue[0]
						func, arg = self._windows[key]
						apply(func, (arg, window,
							  event, value))
						return 1
				if not w:
					break
				w = w._parent_window
				if w == toplevel:
					break
		return 0

	def testevent(self):
		if debug > 1: print 'Event.testevent()'
		while 1:
			self._checktime()
			if self._getevent(0):
				if not self._trycallback():
					# get here if the first event
					# in the queue does not cause
					# a callback
					return 1
				continue
			# get here only when there are no pending events
			return 0

	def readevent_timeout(self, timeout):
		if debug: print 'Event.readevent_timeout()'
		if self._getevent(timeout):
			event = self._queue[0]
			del self._queue[0]
			return event
		else:
			return None
		
	def waitevent(self, timeout = None):
		if debug: print 'Event.waitevent()'
		dummy = self._getevent(timeout)

	def readevent(self):
		while 1:
			if self.testevent():
				return self.readevent_timeout(None)
			if self._timers:
				(t, arg, tid) = self._timers[0]
				t0 = time.time()
			else:
				t = None
			self.waitevent(timeout = t)
			if self._timers:
				t1 = time.time()
				dt = t1 - t0
				self._timers[0] = (t - dt, arg, tid)

	def setfd(self, fd):
		if type(fd) <> type(1):
			fd = fd.fileno()
		if fd not in self._fdlist:
			self._fdlist.append(fd)

	def rmfd(self, fd):
		if fd in self._fdlist:
			self._fdlist.remove(fd)

	def register(self, win, event, func, arg):
		key = (win, event)
		if func:
			self._windows[key] = (func, arg)
			if win:
				win._call_on_close(self.remove_window_callbacks)
		elif self._windows.has_key(key):
			del self._windows[key]
		else:
			raise error, 'not registered'

	def unregister(self, win, event):
		try:
			self.register(win, event, None, None)
		except error:
			pass

	def getregister(self, win, event):
		try:
			return self._windows[(win, event)]
		except KeyError:
			raise error, 'not registered'

	def remove_window_callbacks(self, window):
		# called when window closes
		for (w, e) in self._windows.keys():
			if w == window:
				self.unregister(w, e)

	def setcallback(self, event, func, arg):
		self.register(None, event, func, arg)

	def select_setcallback(self, fd, cb, arg):
		if type(fd) <> type(1):
			fd = fd.fileno()
		if cb is None:
			self._select_fdlist.remove(fd)
			del self._select_dict[fd]
			self.rmfd(fd)
			return
		if not self._select_dict.has_key(fd):
			self._select_fdlist.append(fd)
		self._select_dict[fd] = (cb, arg)
		self.setfd(fd)

	def startmodal(self, window):
		self._modal.append(window)

	def endmodal(self):
		del self._modal[-1]

	def mainloop(self):
		while 1:
			dummy = self.readevent()

class _Font:
	def __init__(self, fontname, size):
		self._font = _findfont(fontname, size)
		self._baseline, self._fontheight, = self._fontparams()
		self._fontname = fontname
		self._pointsize = size
		self._closed = 0
##		self._pointsize = float(self.fontheight()) * 72.0 / 25.4
##		print '_Font() pointsize:',size,self._pointsize

	def __repr__(self):
		s = '<_Font instance, font=' + `self._fontname` + \
		    ', ps=' + `self._pointsize`
		if self.is_closed():
			s = s + ' (closed)'
		return s + '>'

	def close(self):
		self._closed = 1
		del self._font

	def is_closed(self):
		return self._closed

	def strsize(self, str):
		if self.is_closed():
			raise error, 'font object already closed'
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * self._fontheight
		for str in strlist:
			width = self._font.getstrwidth(str)
			if width > maxwidth:
				maxwidth = width
		return float(maxwidth) * _mscreenwidth / _screenwidth, \
			  float(maxheight) * _mscreenheight / _screenheight

	def baseline(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return float(self._baseline) * _mscreenheight / _screenheight

	def fontheight(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return float(self._fontheight) * _mscreenheight / _screenheight

	def pointsize(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return self._pointsize

	def _fontparams(self):
		printermatched, fixed_width, xorig, yorig, xsize, ysize, \
			  fontheight, nglyphs = self._font.getfontinfo()
		baseline = fontheight - yorig
		return baseline, fontheight

class _Button:
	def __init__(self, dispobj, x, y, w, h):
##		print 'create',`self`
		if debug: print 'Button.__init__()'
		self._dispobj = dispobj
		window = dispobj._window
		self._corners = x, y, x + w, y + h
		self._coordinates = window._convert_coordinates(x, y, w, h)
		self._color = dispobj._fgcolor
		self._hicolor = dispobj._fgcolor
		self._linewidth = dispobj._linewidth
		self._hiwidth = self._linewidth
		self._highlighted = 0
		dispobj._buttonlist.append(self)
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		d = dispobj._displaylist
		if dispobj._curcolor != self._color:
			d.append(gl.RGBcolor, self._color)
			dispobj._curcolor = self._color
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.recti, self._coordinates)

##	def __del__(self):
##		print 'delete',`self`

	def close(self):
		dispobj = self._dispobj
		if dispobj:
			dispobj._buttonlist.remove(self)
		self._dispobj = None

	def is_closed(self):
		return self._dispobj is None

	def getwindow(self):
		return self._dispobj._window

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, *color):
		if self.is_closed():
			raise error, 'button already closed'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._hicolor = color

	def highlight(self):
		if self.is_closed():
			raise error, 'button already closed'
		dispobj = self._dispobj
		if dispobj._window._active_display_list != dispobj:
			raise error, 'can only highlight rendered button'
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		toplevel._win_lock.acquire()
		gl.winset(self._dispobj._window._window_id)
		gl.RGBcolor(self._hicolor)
		gl.linewidth(self._hiwidth)
		gl.recti(self._coordinates)
		toplevel._win_lock.release()
		self._highlighted = 1

	def unhighlight(self):
		if self.is_closed():
			raise error, 'button already closed'
		if not self._highlighted:
			return
		self._highlighted = 0
		dispobj = self._dispobj
		if dispobj._window._active_display_list != dispobj:
			raise error, 'can only unhighlight rendered button'
		if self._hiwidth > self._linewidth:
			dispobj.render()
		else:
			toplevel._win_lock.acquire()
			gl.winset(self._dispobj._window._window_id)
			gl.RGBcolor(self._color)
			gl.linewidth(self._linewidth)
			gl.recti(self._coordinates)
			toplevel._win_lock.release()

	def _inside(self, x, y):
		# return 1 iff the given coordinates fall within the button
		if (self._corners[0] <= x <= self._corners[2]) and \
			  (self._corners[1] <= y <= self._corners[3]):
			return 1
		else:
			return 0

# Display List.  A window may have several display lists.  When the
# list is rendered, it becomes the active display list.
class _DisplayList:
	def __init__(self, window):
		self._window = window	# window to which this belongs
##		print 'create',`self`
		self._rendered = 0	# 1 iff rendered at some point
		self._bgcolor = window._bgcolor
		self._fgcolor = window._fgcolor
		self._font = None
		self._fontheight = 0
		self._baseline = 0
		self._curfont = None
		self._curcolor = self._bgcolor
		self._displaylist = []
		self._buttonlist = []
		self._linewidth = 1
		self._curpos = 0, 0
		self._xpos = 0
		self._cloneof = None
		window._displaylists.append(self)
		if debug: print 'DisplayList.init'+`self,window`

##	def __del__(self):
##		print 'delete',`self`

	def __repr__(self):
		s = '<_DisplayList instance, window=' + `self._window`
		if self.is_closed():
			s = s + ' (closed)'
		elif self._rendered:
			if self._window._active_display_list is self:
				s = s + ' (active)'
			else:
				s = s + ' (rendered)'
		return s + '>'

	def close(self):
		if debug: print `self`+'.close()'
		if self.is_closed():
			return
		for button in self._buttonlist[:]:
			button.close()
		window = self._window
		window._displaylists.remove(self)
		for d in window._displaylists:
			if d._cloneof is self:
				d._cloneof = None
		if window._active_display_list is self:
			window._active_display_list = None
			window._redraw()
		self._window = None
		self._rendered = 0
		del self._displaylist
		del self._font
		del self._curfont
		del self._buttonlist
		del self._cloneof

	def is_closed(self):
		return self._window is None

	def render(self):
		if debug: print `self`+'.render()'
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if window._active_display_list:
			for but in window._active_display_list._buttonlist:
				but._highlighted = 0
		toplevel._win_lock.acquire()
		gl.winset(window._window_id)
		if not self._cloneof or \
		   self._cloneof is not window._active_display_list or \
		   window._active_display_list._buttonlist:
			gl.RGBcolor(self._bgcolor)
			gl.clear()
			self._clonestart = 0
		for funcargs in self._displaylist[self._clonestart:]:
			if type(funcargs) == type(()):
				func, args = funcargs
				func(args)
			else:
				funcargs()
		window._active_display_list = self
		if _drawbox or window._drawbox:
			gl.linewidth(1)
			gl.RGBcolor(self._fgcolor)
			gl.recti(0, 0, window._width - 1, window._height - 1)
		gl.gflush()
		toplevel._win_lock.release()
		self._rendered = 1

	def clone(self):
		if debug: print `self`+'.clone()'
		if self.is_closed():
			raise error, 'displaylist already closed'
		new = _DisplayList(self._window)
		new._displaylist = self._displaylist[:]
		new._fgcolor = self._fgcolor
		new._bgcolor = self._bgcolor
		new._curcolor = None
		new._font = self._font
		new._fontheight = self._fontheight
		new._baseline = self._baseline
		new._curfont = None
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._displaylist)
		return new


	#
	# Color handling
	#
	def fgcolor(self, *color):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color

	#
	# Buttons
	#
	def newbutton(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		return _Button(self, x, y, w, h)

	#
	# Images
	#
	def display_image_from_file(self, file, *crop):
		if self.is_closed():
			raise error, 'displaylist already closed'
		window = self._window
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(crop) == 4:
			top, bottom, left, right = crop
			if top + bottom >= 1 or left + right >= 1:
				raise TypeError, 'arg count mismatch'
		elif len(crop) == 0:
			top, bottom, left, right = 0, 0, 0, 0
		else:
			raise TypeError, 'arg count mismatch'
		win_x, win_y, win_w, win_h, im_x, im_y, im_w, im_h, \
			  depth, scale, image = \
				  window._prepare_image_from_file(file,
					  top, bottom, left, right)
		d = self._displaylist
		d.append(gl.rectzoom, (scale, scale))
		if depth == 1:
			d.append(gl.pixmode, (GL.PM_SIZE, 8))
		else:
			d.append(gl.pixmode, (GL.PM_SIZE, 32))
			depth = 4
		if (im_x, im_y) == (0, 0):
			d.append(gl.lrectwrite, (win_x, win_y,
				  win_x+win_w-1, win_y+win_h-1, image))
		else:
			d.append(gl.pixmode, (GL.PM_STRIDE, im_w))
			d.append(gl.lrectwrite, (win_x, win_y,
				  win_x+win_w-1, win_y+win_h-1,
				  image[(im_w*im_y+im_x)*depth:]))
			d.append(gl.pixmode, (GL.PM_STRIDE, 0))
		return float(win_x) / window._width, \
			  float(win_y) / window._height, \
			  float(win_w) / window._width, \
			  float(win_h) / window._height

	#
	# Drawing methods
	#
	def linewidth(self, width):	# XXX--should use a better unit
		self._linewidth = int(width)

	def drawline(self, color, points):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawline'+`points`
		d = self._displaylist
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.bgnline)
		x0, y0 = points[0]
		for x, y in points:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			d.append(gl.v2f, (x, y))
		d.append(gl.endline)

	def drawfpolygon(self, color, points):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if debug: print `self`+'.drawfpolygon'+`points`
		d = self._displaylist
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		d.append(gl.bgnpolygon)
		for x, y in points:
			x, y = window._convert_coordinates(x, y, 0, 0)[:2]
			d.append(gl.v2f, (x, y))
		d.append(gl.endpolygon)

	def drawbox(self, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawbox'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		x0, y0, x1, y1 = window._convert_coordinates(x, y, w, h)
		if self._curcolor != self._fgcolor:
			d.append(gl.RGBcolor, self._fgcolor)
			self._curcolor = self._fgcolor
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.recti, (x0, y0, x1, y1))

	def drawfbox(self, color, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawfbox'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		x0, y0, x1, y1 = window._convert_coordinates(x, y, w, h)
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.bgnpolygon)
		d.append(gl.v2f, (x0, y0))
		d.append(gl.v2f, (x0, y1))
		d.append(gl.v2f, (x1, y1))
		d.append(gl.v2f, (x1, y0))
		d.append(gl.endpolygon)

	def draw3dbox(self, cl, ct, cr, cb, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		l, b, r, t = window._convert_coordinates(x, y, w, h)
		l = l+1
		t = t-1
		r = r-1
		b = b+1
		l1 = l - 1
		t1 = t + 1
		r1 = r
		b1 = b
		ll = l + 2
		tt = t - 2
		rr = r - 2
		bb = b + 3
		if self._curcolor != cl:
			d.append(gl.RGBcolor, (cl))
			self._curcolor = cl
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (l1, t1))
		d.append(gl.v2i, (ll, tt))
		d.append(gl.v2i, (ll, bb))
		d.append(gl.v2i, (l1, b1))
		d.append(gl.endpolygon, ())
		if self._curcolor != ct:
			d.append(gl.RGBcolor, (ct))
			self._curcolor = ct
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (l1, t1))
		d.append(gl.v2i, (r1, t1))
		d.append(gl.v2i, (rr, tt))
		d.append(gl.v2i, (ll, tt))
		d.append(gl.endpolygon, ())
		if self._curcolor != cr:
			d.append(gl.RGBcolor, (cr))
			self._curcolor = cr
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (r1, t1))
		d.append(gl.v2i, (r1, b1))
		d.append(gl.v2i, (rr, bb))
		d.append(gl.v2i, (rr, tt))
		d.append(gl.endpolygon, ())
		if self._curcolor != cb:
			d.append(gl.RGBcolor, (cb))
			self._curcolor = cb
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2i, (l1, b1))
		d.append(gl.v2i, (ll, bb))
		d.append(gl.v2i, (rr, bb))
		d.append(gl.v2i, (r1, b1))
		d.append(gl.endpolygon, ())

	def drawdiamond(self, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawfdiamond'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		x0, y0, x1, y1 = window._convert_coordinates(x, y, w, h)
		if self._curcolor != self._fgcolor:
			d.append(gl.RGBcolor, self._fgcolor)
			self._curcolor = self._fgcolor
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.bgnclosedline, ())
		d.append(gl.v2i, (x0, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y1))
		d.append(gl.v2i, (x1, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y0))
		d.append(gl.endclosedline, ())

	def drawfdiamond(self, color, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.drawfdiamond'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		x0, y0, x1, y1 = window._convert_coordinates(x, y, w, h)
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.bgnpolygon)
		d.append(gl.v2i, (x0, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y1))
		d.append(gl.v2i, (x1, (y0 + y1)/2))
		d.append(gl.v2i, ((x0 + x1)/2, y0))
		d.append(gl.endpolygon)

	def draw3ddiamond(self, cl, ct, cr, cb, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		if debug: print `self`+'.draw3dbox'+`coordinates`
		x, y, w, h = coordinates
		d = self._displaylist
		l, b, r, t = window._convert_coordinates(x, y, w, h)
		x = (l + r) / 2
		y = (t + b) / 2
		n = int(3.0 * (r-l) / (t-b) + 0.5)
		ll = l + n
		tt = t - 3
		rr = r - n
		bb = b + 3

		d.append(gl.RGBcolor, cl)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (l, y))
		d.append(gl.v2f, (x, t))
		d.append(gl.v2f, (x, tt))
		d.append(gl.v2f, (ll, y))
		d.append(gl.endpolygon, ())

		d.append(gl.RGBcolor, ct)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (x, t))
		d.append(gl.v2f, (r, y))
		d.append(gl.v2f, (rr, y))
		d.append(gl.v2f, (x, tt))
		d.append(gl.endpolygon, ())

		d.append(gl.RGBcolor, cr)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (r, y))
		d.append(gl.v2f, (x, b))
		d.append(gl.v2f, (x, bb))
		d.append(gl.v2f, (rr, y))
		d.append(gl.endpolygon, ())

		d.append(gl.RGBcolor, cb)
		d.append(gl.bgnpolygon, ())
		d.append(gl.v2f, (l, y))
		d.append(gl.v2f, (ll, y))
		d.append(gl.v2f, (x, bb))
		d.append(gl.v2f, (x, b))
		d.append(gl.endpolygon, ())

##		d.append(gl.RGBcolor, (FOCUSBORDER))
##		d.append(gl.linewidth, (1))
##		d.append(gl.bgnclosedline, ())
##		d.append(gl.v2f, (l, y))
##		d.append(gl.v2f, (x, t))
##		d.append(gl.v2f, (r, y))
##		d.append(gl.v2f, (x, b))
##		d.append(gl.endclosedline, ())

	def drawarrow(self, color, sx, sy, dx, dy):
		import math
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		d = self._displaylist
		sx, sy = window._convert_coordinates(sx, sy, 0, 0)[:2]
		dx, dy = window._convert_coordinates(dx, dy, 0, 0)[:2]
		lx = dx - sx
		ly = dy - sy
		if lx == ly == 0:
			angle = 0.0
		else:
			angle = math.atan2(ly, lx)
		rotation = 180 + angle * 180.0 / math.pi
		if self._curcolor != color:
			d.append(gl.RGBcolor, color)
			self._curcolor = color
		# Draw the line from src to dst
		d.append(gl.linewidth, 2)
		d.append(gl.bgnline)
		d.append(gl.v2i, (sx, sy))
		d.append(gl.v2i, (dx, dy))
		d.append(gl.endline)
		# Draw the arrowhead
		# Translate so that the point of the arrowhead is (0, 0)
		# Rotate so that it comes in horizontally from the right
		d.append(gl.pushmatrix)
		d.append(gl.translate, (dx, dy, 0))
		d.append(gl.rot, (rotation, 'z'))
		d.append(gl.bgnpolygon)
		d.append(gl.v2f, (0, 0))
		d.append(gl.v2f, (ARR_LENGTH, ARR_HALFWIDTH))
		d.append(gl.v2f, (ARR_LENGTH, -ARR_HALFWIDTH))
		d.append(gl.endpolygon)
		d.append(gl.popmatrix)

	#
	# Font and text handling
	#
	def usefont(self, fontobj):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		self._font = fontobj
		f = float(_screenheight) / _mscreenheight / window._height
		self._baseline = fontobj.baseline() * f
		self._fontheight = fontobj.fontheight() * f
		return self._baseline, self._fontheight, fontobj.pointsize()

	def setfont(self, font, size):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, *opt_margin):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(opt_margin) == 0:
			margin = 0
		elif len(opt_margin) == 1:
			margin = opt_margin[0]
		else:
			raise error, 'too many arguments'
		if margin < 0 or margin >= 1:
			raise error, 'rediculous margin: ' + `margin`
		mfac = 1 - margin
		window = self._window
		strlist = string.splitfields(str, '\n')
		nlines = len(strlist)
		fontobj = findfont(fontname, 100)
		firsttime = 1
		height = fontobj.fontheight() * _screenheight / _mscreenheight
		while firsttime or nlines * height > window._height * mfac:
			firsttime = 0
			ps = float(window._height*mfac*_mscreenheight*fontobj.pointsize())/\
				  float(nlines*fontobj.fontheight()*_screenheight)
			fontobj.close()
			if ps <= 0:
				raise error, 'string does not fit in window'
			fontobj = findfont(fontname, ps)
			height = fontobj.fontheight() * _screenheight / _mscreenheight
		for str in strlist:
			width, height = fontobj.strsize(str)
			width = width * _screenwidth / _mscreenwidth
			while width > window._width * mfac:
				ps = float(window._width) * mfac * fontobj.pointsize() / width
				if ps <= 0:
					raise error, 'string does not fit in window'
				fontobj.close()
				fontobj = findfont(fontname, ps)
				width, height = fontobj.strsize(str)
				width = width * _screenwidth / _mscreenwidth
		return self.usefont(fontobj)

	def baseline(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if not self._font:
			raise error, 'font not set'
		return self._baseline

	def fontheight(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if not self._font:
			raise error, 'font not set'
		return self._fontheight

	def pointsize(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if not self._font:
			raise error, 'font not set'
		return self._font.pointsize()

	def strsize(self, str):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = 0
		for str in strlist:
			width, height = self._font.strsize(str)
			width = width * _screenwidth / _mscreenwidth
			if width > maxwidth:
				maxwidth = width
			maxheight = maxheight + self._fontheight
		return float(maxwidth) / self._window._width, maxheight

	def strfit(self, text, width, height):
		# this could be made more efficient
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		for i in range(1, len(text)):
			w, h = self.strsize(text[:i])
			if w > width or h > height:
				return i - 1
		return len(text)

	def setpos(self, x, y):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._curpos = x, y
		self._xpos = x

	def getpos(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self._curpos

	def writestr(self, str):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		w = self._window	# some abbreviations
		f = self._font._font
		d = self._displaylist
		strlist = string.splitfields(str, '\n')
		if self._curcolor != self._fgcolor:
			d.append(gl.RGBcolor, self._fgcolor)
			self._curcolor = self._fgcolor
		if self._curfont != f:
			d.append(f.setfont)
			self._curfont = f
		x, y = oldx, oldy = self._curpos
		oldy = oldy - self._baseline
		maxx = oldx
		for str in strlist:
			x0, y0 = w._convert_coordinates(x, y, 0, 0)[:2]
			d.append(gl.cmov2, (x0, y0))
			d.append(fm.prstr, str)
			self._curpos = x + float(f.getstrwidth(
				  str)) / w._width, y
			x = self._xpos
			y = y + self._fontheight
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, \
			  newy - oldy + self._fontheight - self._baseline


class _Window:
	def __init__(self, is_toplevel, parent, x, y, w, h, title):
		self._parent_window = parent
		if not is_toplevel:
			return
		toplevel._win_lock.acquire()
		try:
			import calcwmcorr
			wmcorr_x, wmcorr_y = calcwmcorr.calcwmcorr()
		except ImportError:
			wmcorr_x, wmcorr_y = 0, 0
		x0, y0 = x, y
		x1, y1 = x0 + w, y0 + h
		x0 = int(float(x0)/_mscreenwidth*_screenwidth+0.5)
		y0 = int(float(y0)/_mscreenheight*_screenheight+0.5)
		x1 = int(float(x1)/_mscreenwidth*_screenwidth+0.5) - 1
		y1 = int(float(y1)/_mscreenheight*_screenheight+0.5) - 1
		gl.prefposition(x0 - wmcorr_x, x1 - wmcorr_x,
			  _screenheight - y1 - 1 + wmcorr_y,
			  _screenheight - y0 - 1 + wmcorr_y)
		if title is None:
			gl.noborder()
			title = ''
			noborder = 1
		else:
			noborder = 0
		self._window_id = gl.winopen(title)
		self._title = title
		if debug: print 'Window.init'+`self, parent, x, y, w, h, title`
		if noborder:
			gl.noborder()
		gl.winconstraints()
		self._init2()

	def __repr__(self):
		s = '<_Window instance'
		if hasattr(self, '_window_id'):
			s = s + ', window_id=' + `self._window_id`
		if hasattr(self, '_parent_window'):
			if self._parent_window is toplevel:
				if hasattr(self, '_title'):
					s = s + ', title=' + `self._title`
				else:
					s = s + ', toplevel'
			else:
				s = s + ', parent=' + `self._parent_window`
		if self.is_closed():
			s = s + ' (closed)'
		s = s + '>'
		return s

	def __del__(self):
		if not _window_list.has_key(self._window_id):
			self.close()

	def _init2(self):
		if debug: print `self`+'.init2()'
##		print 'create',`self`
		# we are already locked on entry, we are unlocked on return
		gl.RGBmode()
		gl.gconfig()
		gl.reshapeviewport()
		self._width, self._height = gl.getsize()
		gl.ortho2(-0.5, self._width-0.5, -0.5, self._height-0.5)
		toplevel._win_lock.release()
		self._bgcolor = self._parent_window._bgcolor
		self._fgcolor = self._parent_window._fgcolor
		self._drawbox = _drawbox
		self._subwindows = []
		self._subwindows_closed = 0
		self._displaylists = []
		self._active_display_list = None
		self._menu = None
		self._menuids = []
		self._accelerators = None
		self._menuprocs = None
		self._closecallbacks = []
		_window_list[self._window_id] = self
		self._redraw_func = None
		self._redraw()
		self.setcursor(self._parent_window._cursor)
		self._parent_window._subwindows.append(self)
		if hasattr(self._parent_window, '_toplevel'):
			self._toplevel = self._parent_window._toplevel
		else:
			self._toplevel = self

	def newwindow(self, *coordinates, **options):
		if debug: print `self`+'.newwindow'+`coordinates`
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		x0, y0, x1, y1 = self._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._toplevel._window_id)
		tx, ty = gl.getorigin()
		gl.winset(self._window_id)
		wx, wy = gl.getorigin()
		wx, wy = wx - tx, wy - ty
		x0, y0 = x0 + wx, y0 + wy
		x1, y1 = x1 + wx, y1 + wy
		new_window = _Window(0, self, 0, 0, 0, 0, 0)
		new_window._window_id = gl.swinopen(self._window_id)
		gl.winposition(x0, x1, y0, y1)
		new_window._parent_window = self
		new_window._sizes = x, y, w, h
		new_window._toplevel = self._toplevel
		new_window._init2()
		dummy = event.testevent()
		return new_window

	newcmwindow = newwindow

	def close(self):
		if debug: print `self`+'.close()'
		if not _window_list.has_key(self._window_id):
			# apparently already closed
			return
		for func in self._closecallbacks[:]:
			func(self)
		del self._closecallbacks
		for win in self._subwindows[:]:
			win.close()
		for displist in self._displaylists[:]:
			displist.close()
		del self._displaylists
		self.destroy_menu()
		del self._menuids
		del self._menu
		del self._menuprocs
		del self._accelerators
		gl.winclose(self._window_id)
		del _window_list[self._window_id]
		parent = self._parent_window
		parent._subwindows.remove(self)
		self._parent_window = None
		self._toplevel = None
		# let our parent window inherit events meant for us
		dummy = event.testevent()	# read all pending events
		q = []
		for (win, ev, val) in event._queue:
			if win == self:
				if parent in (None, toplevel):
					# delete event if we have no parent:
					continue
				win = parent
			q.append((win, ev, val))
		event._queue = q

	def _close_subwins(self):
		for win in self._subwindows:
			win._close_win()
		self._subwindows_closed = 1

	def _open_subwins(self):
		if self.is_closed():
			raise error, 'window already closed'
		for win in self._subwindows:
			if not win.is_closed():
				win._open_win()
		self._subwindows_closed = 0

	def _close_win(self):
		# close the GL window connected to this instance
		if debug: print `self`+'._close_win()'
		if self._parent_window == toplevel:
			raise error, 'can\'t close top-level window'
		self._close_subwins()
		gl.winclose(self._window_id)
		del _window_list[self._window_id]
		self._window_id = -1

	def _open_win(self):
		# re-open a GL window for this instance
		if self.is_closed():
			raise error, 'window already closed'
		if self._window_id != -1:
			raise error, 'window not closed'
		x, y, w, h = self._sizes
		x0, y0, x1, y1 = self._parent_window._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._toplevel._window_id)
		tx, ty = gl.getorigin()
		gl.winset(self._parent_window._window_id)
		wx, wy = gl.getorigin()
		wx, wy = wx - tx, wy - ty
		x0, y0 = x0 + wx, y0 + wy
		x1, y1 = x1 + wx, y1 + wy
		self._window_id = gl.swinopen(self._parent_window._window_id)
		gl.winposition(x0, x1, y0, y1)
		gl.RGBmode()
		gl.gconfig()
		gl.reshapeviewport()
		self._width, self._height = gl.getsize()
		gl.ortho2(-0.5, self._width-0.5, -0.5, self._height-0.5)
		toplevel._win_lock.release()
		_window_list[self._window_id] = self
		self.setcursor(self._cursor)
		self._open_subwins()

	def _call_on_close(self, func):
		if not func in self._closecallbacks:
			self._closecallbacks.append(func)

	def is_closed(self):
		return not hasattr(self, '_displaylists')

	def showwindow(self):
		self._drawbox = 1
		self._redraw()

	def dontshowwindow(self):
		if self._drawbox:
			self._drawbox = 0
			self._redraw()

	def fgcolor(self, *color):
		if debug: print `self`+'.fgcolor()'
		if self.is_closed():
			raise error, 'window already closed'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color

	def bgcolor(self, *color):
		if debug: print `self`+'.bgcolor()'
		if self.is_closed():
			raise error, 'window already closed'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._bgcolor = color
		if not self._active_display_list:
			toplevel._win_lock.acquire()
			gl.winset(self._window_id)
			gl.RGBcolor(self._bgcolor)
			gl.clear()
			toplevel._win_lock.release()

	def settitle(self, title):
		if self.is_closed():
			raise error, 'window already closed'
		if self._parent_window != toplevel:
			raise error, 'can only settitle at top-level'
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.wintitle(title)
		toplevel._win_lock.release()
		self._title = title

	def newdisplaylist(self, *bgcolor):
		if self.is_closed():
			raise error, 'window already closed'
		list = _DisplayList(self)
		if len(bgcolor) == 1 and type(bgcolor[0]) == type(()):
			bgcolor = bgcolor[0]
		if len(bgcolor) == 3:
			list._bgcolor = list._curcolor = bgcolor
		elif len(bgcolor) != 0:
			raise TypeError, 'arg count mismatch'
		return list

	def create_box(self, msg, callback, *box):
		_Boxes(self, msg, callback, box).loop()

	def _sizebox(self, (x, y, w, h), constrainx, constrainy, callback):
		if debug: print `self`+'.sizebox()'
		if self.is_closed():
			raise error, 'window already closed'
		if constrainx and constrainy:
			raise error, 'can\'t constrain both X and Y directions'
		# we must invert y0 and y1 here because convert_coordinates
		# inverts them also and here it is important which coordinate
		# comes first but not which coordinate is the higher
		x0, y1, x1, y0 = self._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		if gl.getplanes() < 12:
			gl.drawmode(GL.PUPDRAW)
			gl.mapcolor(GL.RED, 255, 0, 0)
		else:
			gl.drawmode(GL.OVERDRAW)
		gl.qreset()
		gl.color(0)
		gl.clear()
		gl.color(GL.RED)
		gl.recti(x0, y0, x1, y1)
		screenx0, screeny0 = gl.getorigin()
		mx, my = x1, y1
		width, height = gl.getsize()
		toplevel._win_lock.release()
		while 1:
			while event.testevent() == 0:
				if not constrainx:
					mx = gl.getvaluator(DEVICE.MOUSEX) - \
						  screenx0
					if mx < 0:
						mx = 0
					if mx >= width:
						mx = width - 1
				if not constrainy:
					my = gl.getvaluator(DEVICE.MOUSEY) - \
						  screeny0
					if my < 0:
						my = 0
					if my >= height:
						my = height - 1
				if mx != x1 or my != y1:
					toplevel._win_lock.acquire()
					gl.winset(self._window_id)
					gl.color(0)
					gl.clear()
					x1, y1 = mx, my
					gl.color(GL.RED)
					gl.recti(x0, y0, x1, y1)
					toplevel._win_lock.release()
			w, e, v = event.readevent()
			if e == Mouse0Release:
				break
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.color(0)
		gl.clear()
		gl.drawmode(GL.NORMALDRAW)
		toplevel._win_lock.release()
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, w, h = float(x0) / (width - 1), \
			  float(height - y1 - 1) / (height - 1), \
			  float(x1 - x0) / (width - 1), \
			  float(y1 - y0) / (height - 1)
		# constrain coordinates to window
		if x < 0:
			x = 0
		if y < 0:
			y = 0
		if x + w > 1:
			w = 1 - x
		if y + h > 1:
			h = 1 - y
		apply(callback, (x, y, w, h))

	def _movebox(self, (x, y, w, h), constrainx, constrainy):
		if debug: print `self`+'.movebox()'
		if self.is_closed():
			raise error, 'window already closed'
		if constrainx and constrainy:
			raise error, 'can\'t constrain both X and Y directions'
		x0, y0, x1, y1 = self._convert_coordinates(x, y, w, h)
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		if gl.getplanes() < 12:
			gl.drawmode(GL.PUPDRAW)
			gl.mapcolor(GL.RED, 255, 0, 0)
		else:
			gl.drawmode(GL.OVERDRAW)
		gl.color(0)
		gl.clear()
		gl.color(GL.RED)
		gl.recti(x0, y0, x1, y1)
		screenx0, screeny0 = gl.getorigin()
		omx = gl.getvaluator(DEVICE.MOUSEX) - screenx0
		omy = gl.getvaluator(DEVICE.MOUSEY) - screeny0
		width, height = gl.getsize()
		toplevel._win_lock.release()
		while 1:
			while event.testevent() == 0:
				if not constrainx:
					mx = gl.getvaluator(DEVICE.MOUSEX) - screenx0
				if not constrainy:
					my = gl.getvaluator(DEVICE.MOUSEY) - screeny0
				if mx != omx or my != omy:
					dx = mx - omx
					dy = my - omy
					toplevel._win_lock.acquire()
					gl.winset(self._window_id)
					gl.color(0)
					gl.clear()
					x0 = x0 + dx
					x1 = x1 + dx
					if x0 < 0:
						x1 = x1 - x0
						x0 = 0
					if x1 >= width:
						x0 = x0 - (x1 - width) - 1
						x1 = width - 1
					y0 = y0 + dy
					y1 = y1 + dy
					if y0 < 0:
						y1 = y1 - y0
						y0 = 0
					if y1 >= height:
						y0 = y0 - (y1 - height) - 1
						y1 = height - 1
					gl.color(GL.RED)
					gl.recti(x0, y0, x1, y1)
					omx, omy = mx, my
					toplevel._win_lock.release()
			w, e, v = event.readevent()
			if e == Mouse0Release:
				break
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.color(0)
		gl.clear()
		gl.drawmode(GL.NORMALDRAW)
		toplevel._win_lock.release()
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, w, h = float(x0) / (width - 1), \
			  float(height - y1 - 1) / (height - 1), \
			  float(x1 - x0) / (width - 1), \
			  float(y1 - y0) / (height - 1)
		# constrain coordinates to window
		if x < 0:
			x = 0
		if y < 0:
			y = 0
		if x + w > 1:
			w = 1 - x
		if y + h > 1:
			h = 1 - y
		return x, y, w, h

	def pop(self):
		if debug: print `self`+'.pop()'
		if self.is_closed():
			raise error, 'window already closed'
# The following statement was commented out because it had the
# undesirable effect that when the second of two subwindows was
# popped, the first disappeared under its parent window.  It may be
# that the current situation also has undesirable side effects, but I
# haven't seen them yet.  --sjoerd
##		self._parent_window.pop()
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.winpop()
		toplevel._win_lock.release()

	def push(self):
		if debug: print `self`+'.push()'
		if self.is_closed():
			raise error, 'window already closed'
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.winpush()
		toplevel._win_lock.release()

	def getgeometry(self):
		if self.is_closed():
			raise error, 'window already closed'
		toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		x, y = gl.getorigin()
		toplevel._win_lock.release()
		h = float(_mscreenheight) / _screenheight
		w = float(_mscreenwidth) / _screenwidth
		return float(x) * w, (_screenheight - y - self._height) * h, \
			  self._width * w, self._height * h

	def setredrawfunc(self, func):
		if func:
			self._redraw_func = func
		else:
			self._redraw_func = None

	def _resize(self):
		toplevel._win_lock.acquire()
		if self._parent_window != toplevel:
			x, y, w, h = self._sizes
			x0, y0, x1, y1 = \
				  self._parent_window._convert_coordinates(
					  x, y, w, h)
			gl.winset(self._window_id)
			gl.winposition(x0, x1, y0, y1)
		gl.winset(self._window_id)	# just to be sure
		gl.reshapeviewport()
		self._width, self._height = gl.getsize()
		gl.ortho2(-0.5, self._width-0.5, -0.5, self._height-0.5)
		toplevel._win_lock.release()
		# close all display objects after a resize
		for displist in self._displaylists[:]:
			displist.close()
		for win in self._subwindows:
			win._resize()
		event.enterevent(self, ResizeWindow, None)

	def _redraw(self):
		if not hasattr(self, '_closecallbacks'):
			return		# closing: don't redraw
		if debug: print `self`+'._redraw()',
		if self._subwindows_closed:
			if debug: print 'draw subwindows'
			toplevel._win_lock.acquire()
			gl.winset(self._window_id)
			gl.RGBcolor(self._bgcolor)
			gl.clear()
			gl.RGBcolor(self._fgcolor)
			for win in self._subwindows:
				x, y, w, h = win._sizes
				x0, y0, x1, y1 = self._convert_coordinates(x, y, w, h)
				gl.recti(x0, y0, x1, y1)
			toplevel._win_lock.release()
		if self._redraw_func:
			if debug: print 'use redraw func'
			self._redraw_func()
		elif self._active_display_list:
			if debug: print 'use display list'
			buttons = []
			for but in self._active_display_list._buttonlist:
				if but._highlighted:
					buttons.append(but)
			self._active_display_list.render()
			for but in buttons:
				but.highlight()
		else:
			if debug: print 'clear'
			toplevel._win_lock.acquire()
			gl.winset(self._window_id)
			gl.RGBcolor(self._bgcolor)
			gl.clear()
			toplevel._win_lock.release()
		if _drawbox or self._drawbox:
			toplevel._win_lock.acquire()
			gl.linewidth(1)
			if self._active_display_list:
				color = self._active_display_list._fgcolor
			else:
				color = self._fgcolor
			gl.RGBcolor(color)
			gl.recti(0, 0, self._width - 1, self._height - 1)
			toplevel._win_lock.release()
		self._must_redraw = 0

	def setcursor(self, cursor):
		if self._window_id >= 0:
			for win in self._subwindows:
				win.setcursor(cursor)
			try:
				toplevel._win_lock.acquire()
				gl.winset(self._window_id)
				if cursor == 'watch':
					gl.setcursor(_WATCH, 0, 0)
				elif cursor == 'channel':
				        gl.setcursor(_CHANNEL, 0, 0)
				elif cursor == 'link':
					gl.setcursor(_LINK, 0, 0)
				elif cursor == 'stop':
					gl.setcursor(_STOP, 0, 0)
				elif cursor == '':# default is arrow cursor
					gl.setcursor(_ARROW, 0, 0)
				else:
					raise error, 'unknown cursor glyph'
			finally:
				toplevel._win_lock.release()
		self._cursor = cursor

	def _prepare_image_from_file(self, file, top, bottom, left, right):
		global _cache_full
		cachekey = `file`+':'+`self._width`+'x'+`self._height`
		if _image_cache.has_key(cachekey):
			retval = _image_cache[cachekey]
			filename = retval[-1]
			try:
				image = open(filename).read()
			except:		# any error...
				del _image_cache[cachekey]
				import os
				try:
					os.unlink(filename)
				except posix.error:
					pass
			else:
				return retval[:-1] + (image,)
		import img, imgformat
		try:
			reader = img.reader(imgformat.rgb_b2t, file)
		except img.error, arg:
			raise error, arg
		xsize = reader.width
		ysize = reader.height
		try:
			image = reader.read()
		except:
			raise error, 'Unspecified error reading image'
		_size_cache[file] = xsize, ysize
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		width, height = self._width, self._height
		scale = min(float(width)/(xsize - left - right), \
			    float(height)/(ysize - top - bottom))
		width, height = xsize, ysize
		if scale != int(scale):
			import imageop
			width = int(xsize * scale)
			height = int(ysize * scale)
			image = imageop.scale(image, 4, xsize, ysize,
					      width, height)
			top = int(top * scale)
			bottom = int(bottom * scale)
			left = int(left * scale)
			right = int(right * scale)
			scale = 1.0
		x, y = (self._width-(width-left-right))/2, \
			  (self._height-(height-top-bottom))/2
		retval = x, y, width - left - right, height - top - bottom, \
			  left, bottom, width, height, 4, scale, \
			  image
		if not _cache_full:
			import tempfile
			filename = tempfile.mktemp()
			try:
				f = open(filename, 'wb')
				f.write(image)
			except:		# any error...
				print 'Warning: caching image failed'
				import os
				try:
					os.unlink(filename)
				except:
					pass
				_cache_full = 1
			else:
				_image_cache[cachekey] = retval[:-1] + (filename,)
		return retval

	def _image_size(self, file):
		if _size_cache.has_key(file):
			return _size_cache[file]
		import img
		try:
			reader = img.reader(None, file)
		except img.error, arg:
			raise error, arg
		width = reader.width
		height = reader.height
		_size_cache[file] = width, height
		return width, height

	def _convert_coordinates(self, x, y, w, h):
		x0, y0 = x, y
		x1, y1 = x + w, y + h
		# convert relative sizes to pixel sizes relative to
		# lower-left corner of the window
		x0 = int((self._width - 1) * x0 + 0.5)
		y0 = int((self._height - 1) * y0 + 0.5)
		x1 = int((self._width - 1) * x1 + 0.5)
		y1 = int((self._height - 1) * y1 + 0.5)
		y0, y1 = self._height - y1 - 1, self._height - y0 - 1
		return x0, y0, x1, y1

	def register(self, ev, func, arg):
		event.register(self, ev, func, arg)

	def unregister(self, ev):
		event.unregister(self, ev)

	def getregister(self, ev):
		return event.getregister(self, ev)

	def destroy_menu(self):
		for menu in self._menuids:
			gl.freepup(menu)
		self._menuids = []
		self._menuprocs = [None]
		if self._active_display_list:
			self.unregister(KeyboardInput)
		self._accelerators = {}
		self.unregister(Mouse2Press)
		self.unregister(_Accelerator)

	def _popup_menu(self, *args):
		i = gl.dopup(self._menu)
		if 0 < i < len(self._menuprocs):
			func, arg = self._menuprocs[i]
			apply(func, arg)

	def _keyb_inp(self, arg, win, ev, val):
		if self._accelerators.has_key(val):
			func, arg = self._accelerators[val]
			apply(func, arg)

	def create_menu(self, title, list):
		self.destroy_menu()
		self._menu = self._create_menu(title, list)
		self.register(Mouse2Press, self._popup_menu, None)
		if self._accelerators:
			self.register(_Accelerator, self._accelerators, None)

	def _create_menu(self, title, list):
		menu = self._menu = gl.newpup()
		self._menuids.append(menu)
		if title:
			gl.addtopup(menu, title + '%t', 0)
		for i in range(len(list)):
			entry = list[i]
			if entry is None:
				# add separator line
				continue
			accelerator, label, callback = entry
			text = label
			if i < len(list) - 1 and list[i + 1] is None:
				text = text + '%l'
			if type(callback) is type([]):
				text = '   ' + text
				submenu = self._create_menu(None, callback)
				gl.addtopup(menu, text + '%m', submenu)
			else:
				if type(callback) is not type(()):
					callback = (callback, (label,))
				if accelerator:
					if type(accelerator) is not type('') or \
					   len(accelerator) != 1:
						raise error, 'menu accelerator must be single character'
					self._accelerators[accelerator] = callback
					text = accelerator + ' ' + text
				else:
					text = '   ' + text
				text = text + '%x' + `len(self._menuprocs)`
				gl.addtopup(menu, text, 0)
				self._menuprocs.append(callback)
		return menu

	def hitarrow(self, x, y, sx, sy, dx, dy):
		# return 1 iff (x,y) is within the arrow head
		import math
		if self.is_closed():
			raise error, 'window already closed'
		sx, sy = self._convert_coordinates(sx, sy, 0, 0)[:2]
		dx, dy = self._convert_coordinates(dx, dy, 0, 0)[:2]
		x, y = self._convert_coordinates(x, y, 0, 0)[:2]
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
			return 0
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return 0
		return 1

# Font stuff
def _findfont(fontname, size):
	if not _fontmap.has_key(fontname):
		print 'Warning: ' + `fontname` + ' not in fontmap'
	else:
		if int(size) == size:
			size = int(size)
		fontname = _fontmap[fontname]
	key = fontname + `size`
	if _fontcache.has_key(key):
		return _fontcache[key]
	key1 = fontname + `1`
	if _fontcache.has_key(key1):
		f1 = _fontcache[key1]
	else:
		f1 = _fontcache[key1] = fm.findfont(fontname)
	f = _fontcache[key] = f1.scalefont(size)
	return f

_fontcache = {}
_fontmap = {
	  'Times-Roman':	'Times-Roman',
	  'Times-Italic':	'Times-Italic',
	  'Times-Bold':		'Times-Bold',
	  'Utopia-Bold':	'Utopia-Bold',
	  'Palatino-Bold':	'Palatino-Bold',
	  'Helvetica':		'Helvetica',
	  'Helvetica-Bold':	'Helvetica-Bold',
	  'Helvetica-Oblique':	'Helvetica-Oblique',
	  'Courier':		'Courier',
	  'Courier-Bold':	'Courier-Bold',
	  'Courier-Oblique':	'Courier-Oblique',
	  'Courier-Bold-Oblique':'Courier-Bold-Oblique',
	  }
fonts = _fontmap.keys()

toplevel = _Toplevel()
event = _Event()

# Interface routines for the top level.
##def newwindow(x, y, w, h, title, **options):
##	return apply(toplevel.newwindow, (x, y, w, h, title), options)
newwindow = toplevel.newwindow

newcmwindow = newwindow

def close():
	toplevel.close()

def setcursor(cursor):
	toplevel.setcursor(cursor)

def getsize():
	return toplevel.getsize()

def findfont(fontname, pointsize):
	return _Font(fontname, pointsize)

def beep():
	gl.ringbell()

def usewindowlock(lock):
	toplevel.usewindowlock(lock)

def getmouse():
	return toplevel.getmouse()

def settimer(sec, arg):
	return event.settimer(sec, arg)

def settimerfunc(func, arg):
	event.setcallback(TimerEvent, func, arg)

def select_setcallback(fd, cb, arg):
	event.select_setcallback(fd, cb, arg)

def mainloop():
	event.mainloop()

def canceltimer(id):
	event.canceltimer(id)

#	showdialog(message, buttons...) -> button_text
#		Show a dialog window with the specified message (may
#		contain newlines) and buttons with the specified
#		texts.  The window stays up until one of the buttons
#		is clicked.  The value of the button is then returned.
#		One button may start with '!'.  This button is the
#		default answer and is returned when the user types a
#		RETURN.
#
#	showmessage(message)
#		Show a dialog box with the given message and a Done
#		button.  The function does not return a value.
#
#	showquestion(question)
#		Show a dialog box with the given question and Yes and
#		No buttons.  The value returned is 1 if the Yes
#		buttons was pressed and 0 if the No button was
#		pressed.
#
#	multchoice(message, buttonlist, defindex)
#		Show a dialog box with the given message and list of
#		buttons.  Defindex is the index in the list of the
#		default button.  The value returned is the index of
#		the button which was pressed.
#
# The presentation can be changed by setting any of the variables in
# the configuration section.  See the comments near the variables.

# some configuration variables
BGCOLOR = 255, 255, 0			# background color of window: yellow
FGCOLOR = 0, 0, 0			# foreground color of window: black
HICOLOR = 255, 0, 0			# highlight color of window: red
INTERBUTTONGAP = '   '			# space between buttons
BUTTONFILLER = ' '			# extra space added before and
					# after button text
FONT = 'Times-Roman'			# font used for texts
POINTSIZE = 14				# point size used for texts
WINDOWTITLE = None			# title of pop-up window
DEFLINEWIDTH = 3			# linewidth round default button
WINDOWMARGIN = 1			# margin around text and buttons
CENTERLINES = 0				# whether to center all lines
DONEMSG = ' Done '			# text in button of showmessage
YESMSG = ' Yes '			# text of "Yes" answer of showquestion
NOMSG = ' No '				# text of "No" answer of showquestion
# changing any of the following changes the interface to the user/programmer
DEFBUTTON = '!'				# indicates this is default button
DEFANSWER = '\r', '\n'			# keys that trigger default answer

_break_loop = '_break_loop'

class Dialog:
	def __init__(self, title, prompt, grab, vertical, list, *coordinates):
		if len(list) == 0:
			raise TypeError, 'arg count mismatch'
		# self.events is used to remember events that we are
		# not interested in but that may be important for
		# whoever calls us.
		self.vertical = vertical
		self.events = []
		self.title = title
		self.message = prompt
		self.buttons = []
		self.buttonlist = list
		self._callbacks = {}
		self._accelerators = {}
		self._grab = grab
		self._looping = 0
		self._finish = None
		mx, my, winwidth, winheight = self._calcsize()
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) == 0:
			coordinates = mx, my, winwidth, winheight
		elif len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		mx, my, winwidth, winheight = coordinates
		self.window = newwindow(mx, my, winwidth, winheight, title)
		self.window.bgcolor(BGCOLOR)
		# remember these settings since we may need them later
		self.INTERBUTTONGAP = INTERBUTTONGAP
		self.CENTERLINES = CENTERLINES
		self.DEFBUTTON = DEFBUTTON
		self.DEFLINEWIDTH = DEFLINEWIDTH
		self.DEFANSWER = DEFANSWER
		self.HICOLOR = HICOLOR
		self.FGCOLOR = FGCOLOR
		self.FONT = FONT
		self.draw_window()
		self.window.register(Mouse0Press, self._mpress, None)
		self.window.register(Mouse0Release, self._mrelease, None)
		self.window.register(ResizeWindow, self.draw_window, None)
		if grab:
			self.window.register(None, self._ignore, None)

	def _calcsize(self):
		title = self.title
		prompt = self.message
		list = self.buttonlist
		vertical = self.vertical
		font = findfont(FONT, POINTSIZE)
		mw = 0			# max width of a button
		mh = 0			# max height in lines of a button
		nsep = 0		# number of separators
		if type(prompt) == type(''):
			mw = 0
			for txt in string.splitfields(prompt, '\n'):
				width, height = font.strsize(txt)
				if vertical and width > mw:
					mw = width
					self.widest_button = txt
			width, height = font.strsize(prompt)
			height = height + font.fontheight()
		elif prompt is None:
			width, height = 0, 0
		else:
			raise TypeError, 'message must be text or `None\''
		self.defstr = None
		for entry in list:	# loops at least once
			if entry is None:
				nsep = nsep + 1
				continue
			if type(entry) == type(()):
				label, callback = entry
			else:
				label, callback = '', entry, None
			if callback and type(callback) is not type(()):
				callback = (callback, (label,))
			self._callbacks[label] = callback
			self.buttons.append(label)
			butstrs = string.splitfields(label, '\n')
			for bt in butstrs:	# loops at least once
				txt = BUTTONFILLER + bt + BUTTONFILLER
				bw, bh = font.strsize(txt)
				if bw > mw:
					mw = bw
					self.widest_button = txt
			if len(butstrs) > mh:
				mh = len(butstrs)
		sw, sh = font.strsize(INTERBUTTONGAP)
		font.close()
		self.buttonlines = mh
		self.nseparators = nsep
		if vertical:
			buttonwidth = mw
			buttonheight = mh * bh * len(self.buttons)
			sw, sh = 0, sh * 0.5
##			buttonheight = buttonheight + (len(self.buttons) - 1) * sh
			buttonheight = buttonheight + nsep * sh
		else:
			buttonwidth = len(self.buttons) * mw
			buttonheight = mh * bh
			buttonwidth = buttonwidth + (len(self.buttons) - 1) * sw
		if buttonwidth > width:
			width = buttonwidth
		height = height + buttonheight
		winwidth = width + WINDOWMARGIN * 2
		winheight = height + WINDOWMARGIN * 2
		scrwidth, scrheight = getsize()
		buttonwidth = float(buttonwidth) / width
		buttonheight = float(buttonheight) / height
		mw = float(mw) / width
		sw = float(sw) / width
		mx, my = getmouse()
		mx = mx - winwidth * 0.5
		if mx < 0:
			mx = 0
		if mx + winwidth > scrwidth:
			mx = scrwidth - winwidth
		my = my - winheight * 0.5
		if my < 0:
			my = 0
		if my + winheight > scrheight:
			my = scrwidth - winheight
		return mx, my, winwidth, winheight

	def __del__(self):
		self.close()

	def draw_window(self, *rest):
		vertical = self.vertical
		d = self.window.newdisplaylist()
		d.fgcolor(self.FGCOLOR)
		if not self.title:
			d.drawbox(0,0,1,1)
		if vertical:
##			bm = self.widest_button + '\n' * (len(self.buttons) * self.buttonlines - 1 + (len(self.buttons) + self.nseparators + 1) * 0.5)
			bm = self.widest_button + '\n' * (len(self.buttons) * self.buttonlines - 1 + (self.nseparators + 1) / 2)
		else:
			bm = (self.widest_button + self.INTERBUTTONGAP) * \
				(len(self.buttons) - 1) + \
			     self.widest_button + '\n' * (self.buttonlines - 1)
		if type(self.message) == type(''):
			m = self.message + '\n' + '\n' + bm
		else:
			m = bm
		bl, fh, ps = d.fitfont(self.FONT, m, 0.10)
		yorig = 0.05 + bl
		if type(self.message) == type(''):
			w, h = d.strsize(self.message)
			if self.CENTERLINES:
				for str in string.splitfields(self.message, '\n'):
					dx, dy = d.strsize(str)
					d.setpos((1.0 - dx) * 0.5, yorig)
					x, y, dx, dy = d.writestr(str)
					yorig = yorig + dy
			else:
				d.setpos((1.0 - w) * 0.5, yorig)
				x, y, dx, dy = d.writestr(self.message)
				yorig = yorig + dy
		mw, h = d.strsize(self.widest_button)
		mh = h * self.buttonlines	# height of the buttons
		w, h = d.strsize(bm)
		sw, sh = d.strsize(self.INTERBUTTONGAP)
		# calculate (xbase, ybase), the top-left corner of the button
		xbase = (1.0 - w) * 0.5
		if vertical:
			sw, sh = 0, sh * 0.5
			buttonheight = mh * len(self.buttons)
##			buttonheight = buttonheight + (len(self.buttons) - 1) * sh
			buttonheight = buttonheight + self.nseparators * sh
			if type(self.message) == type(''):
				ybase = 1.0 - 0.05 - buttonheight
			else:
				ybase = (1.0 - buttonheight) * 0.5
		else:
			sh = 0
			if type(self.message) == type(''):
				ybase = 1.0 - 0.05 - mh
			else:
				ybase = (1.0 - mh) * 0.5
		self.buttonboxes = []
		for entry in self.buttonlist:
			if entry is None:
				d.drawline(self.FGCOLOR,
					   [(0, ybase + sh * 0.5),
					    (1, ybase + sh * 0.5)])
				ybase = ybase + sh
				continue
			if type(entry) == type(()):
				butstr, callback = entry
			else:
				butstr = entry
			d.linewidth(1)
			w, h = d.strsize(butstr)
			ypos = ybase + (mh - h) * 0.5 + bl
			if self.CENTERLINES:
				for bt in string.splitfields(butstr, '\n'):
					w, h = d.strsize(bt)
					d.setpos(xbase + (mw - w) * 0.5, ypos)
					box = d.writestr(bt)
					ypos = ypos + fh
			else:
				d.setpos(xbase + (mw - w) * 0.5, ypos)
				box = d.writestr(butstr)
			buttonbox = d.newbutton(xbase, ybase, mw, mh)
			buttonbox.hicolor(self.HICOLOR)
			self.buttonboxes.append(buttonbox)
			if vertical:
##				ybase = ybase + mh + sh
				ybase = ybase + mh
			else:
				xbase = xbase + mw + sw
		d.render()
		self.highlighted = []

	# On mouse press, highlight the button, but don't do anything.
	# On mouse release, execute the callback (but only if we're
	# still in the button, of course) and de-highlight the button.
	def _mpress(self, dummy, win, ev, val):
		for but in val[2]:
			try:
				i = self.buttonboxes.index(but)
			except:
				beep()
			else:
				but.highlight()
				self.highlighted.append(but)

	def _mrelease(self, dummy, win, ev, val):
		for but in val[2]:
			if but in self.highlighted:
				try:
					i = self.buttonboxes.index(but)
				except:
					pass
				else:
					callback = self._callbacks[self.buttons[i]]
					if callback:
						apply(callback[0], callback[1])
				if self._finish is None:
					self._finish = 1
		for but in self.highlighted:
			if not but.is_closed():
				but.unhighlight()
		self.highlighted = []
		if self._looping and self._finish is not None:
			raise _break_loop

	def _resize(self, *rest):
		self.draw_window()

	def _ignore(self, *rest):
		pass

	def _loop(self):
		startmonitormode()
		event.startmodal(self.window)
		self._finish = None
		self._looping = 1
		try:
			try:
				while self._finish is None:
					win, ev, val = readevent()
			except _break_loop:
				pass
		finally:
			self.window.close()
			self._looping = 0
			endmonitormode()
			event.endmodal()

	#
	# Some functions we provide for our window.
	#
	def settitle(self, title):
		self.window.settitle(title)

	def getgeometry(self):
		return self.window.getgeometry()

	def _convert_menu_list(self, list):
		newlist = []
		for entry in list:
			if entry is None:
				newlist.append(entry)
			else:
				label, callback = entry
				if type(callback) == type([]):
					callback = self._convert_menu_list(callback)
				newlist.append('', label, callback)
		return newlist

	def create_menu(self, title, list):
		self.window.create_menu(title, self._convert_menu_list(list))

	def close(self):
		self.window.close()

def showmessage(text, type = 'message', grab = 1, callback = None,
		cancelCallback = None, **options):
	list = [('\r', 'Done', callback)]
	if cancelCallback or type == 'question':
		list.append('', 'Cancel', cancelCallback)
	d = Dialog(None, text, grab, 0, list)
	d._loop()
	return d

class _Question(Dialog):
	def __init__(self, text):
		self._finish = None
		Dialog.__init__(self, None, text, 1, 0,
				[('y', 'Yes', (self._ok_callback, ())),
				 ('n', 'No', (self._cancel_callback, ()))])

	def run(self):
		self._loop()
		return self._finish

	def _ok_callback(self):
		self._finish = 1

	def _cancel_callback(self):
		self._finish = 0

def showquestion(text):
	d = _Question(text)
	return d.run()

class _MultChoice(Dialog):
	def __init__(self, prompt, msg_list, defindex):
		self._finish = None
		self.msg_list = msg_list
		list = []
		for i in range(len(msg_list)):
			msg = msg_list[i]
			if i == defindex:
				acc = '\r'
			else:
				acc = ''
			list.append(acc, msg, (self._callback, (msg,)))
		Dialog.__init__(self, None, prompt, 1, 0, list)

	def run(self):
		self._loop()
		return self._finish

	def _callback(self, msg):
		for i in range(len(self.msg_list)):
			if msg is self.msg_list[i]:
				self._finish = i
				return

def multchoice(prompt, list, defindex):
	d = _MultChoice(prompt, list, defindex)
	return d.run()
		
def FileDialog(prompt, directory, filter, file, cb_ok, cb_cancel):
	import fl
	filename = fl.show_file_selector(prompt, directory, filter, file)
	if filename:
		if cb_ok:
			cb_ok(filename)
	else:
		if cb_cancel:
			cb_cancel()

def InputDialog(prompt, default, cb):
	import fl
	value = fl.show_input(prompt, default)
	if value and cb is not None:
		cb(value)

class SelectionDialog:
	def __init__(self, listprompt, itemprompt, itemlist, default,
		     title = 'SelectionDialog'):
		import fl, FL
		self._title = title
		self._callbacks = {}

		self._form = fl.make_form(FL.FLAT_BOX, 300, 320)
		form = self._form

		x, y, w, h = 0, 0, 300, 250
		self._browser = form.add_browser(FL.HOLD_BROWSER, x, y, w, h,
						 listprompt)
		self._browser.set_call_back(self._browser_callback, None)

		buttonwidth = 300 / len(buttonlist)
		x, y, w, h = 0, 250, buttonwidth, 39
		buttonlist = ['Ok', 'Cancel']
		for entry in buttonlist:
			if type(entry) == type(()):
				accelerator, label, callback = entry
			else:
				accelerator, label, callback = '', entry, None
			if callback and type(callback) is not type(()):
				callback = (callback, (label,))
			button = form.add_button(FL.NORMAL_BUTTON, x, y, w, h,
						 label)
			button.set_call_back(self._callback, label)
			self._callbacks[label] = callback
			x = x + buttonwidth

		x, y, w, h = 50, 290, 250, 30
		if itemprompt is None:
			itemprompt = 'Selection'
		self.nameinput = form.add_input(FL.NORMAL_INPUT, x, y, w, h,
						itemprompt)
		self.nameinput.set_call_back(self.name_callback, None)

		for item in itemlist:
			self._browser.add_browser_line(item)

		form.show_form(FL.PLACE_SIZE, 1, self._title)
		self.showing = 1

	def close(self):
		self._browser = None
		self._form = None

	def getselection(self):
		return self.nameinput.get_input()

	def getselected(self):
		i = self._browser.get_browser()
		if i:
			return i - 1
		else:
			return None

	def getlistitem(self, pos):
		if pos < 0:
			pos = self._browser.get_browser_maxline()
		else:
			pos = pos + 1
		return self._browser.get_browser_line(pos)

	def addlistitem(self, item, pos):
		if pos < 0:
			self._browser.add_browser_line(item)
		else:
			self._browser.insert_browser_line(pos + 1, item)

	def dellistitem(self, pos):
		self._browser.delete_browser_line(pos + 1)

	def replacelistitem(self, pos, newitem):
		self._browser.replace_browser_line(pos + 1, newitem)

	def delalllistitems(self):
		self._browser.clear_browser()

	def selectitem(self, pos):
		if pos < 0:
			pos = self._browser.get_browser_maxline()
		else:
			pos = pos + 1
		self._browser.select_browser_line(pos)
		line = self._browser.get_browser_line(pos)
		self.nameinput.set_input(line)

	#
	# Various callbacks
	#
	def _browser_callback(self, obj, arg):
		# When an item is selected in the browser,
		# copy its name to the input box.
		i = self._browser.get_browser()
		if i == 0:
			return
		name = self._browser.get_browser_line(i)
		self.nameinput.set_input(name)

	def _callback(self, obj, arg):
		if arg == 'Ok':
			try:
				func = self.OkCallback
			except AttributeError:
				pass
			else:
				ret = func(self.nameinput.get_input())
				if ret:
					if type(ret) == type(''):
						showmessage(ret, type = 'error')
					return
		if arg == 'Cancel':
			try:
				func = self.CancelCallback
			except AttributeError:
				pass
			else:
				ret = func()
				if ret:
					if type(ret) == type(''):
						showmessage(ret, type = 'error')
					return
		self.close()

	def name_callback(self, obj, arg):
		# When the user presses TAB or RETURN,
		# search the browser for a matching name and select it.
		name = self.nameinput.get_input()
		for i in range(self._browser.get_browser_maxline()):
			if self._browser.get_browser_line(i+1) == name:
				self._browser.select_browser_line(i+1)
				break
