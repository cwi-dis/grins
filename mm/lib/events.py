import windowinterface, time, select
from EVENTS import *

error = 'events.error'

class _Events:
	def init(self):
		self._timers = []
		self._callbacks = {}
		self._windows = {}
		self._winfd = windowinterface.getfd()
		self._select_fdlist = []
		self._select_dict = {}
		self._timenow = float(time.millitimer()) / 1000
		self._timerid = 0
		self._modal = 0
		return self

	def _checktime(self):
		timenow = float(time.millitimer()) / 1000
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
			windowinterface.enterevent(None, TimerEvent, arg)
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

	def enterevent(self, win, event, arg):
		self._checktime()
		windowinterface.enterevent(win, event, arg)

	def pollevent(self):
		if self.testevent():
			return self.readevent()
		else:
			return None

	def _trycallback(self):
		event = windowinterface.peekevent()
		if not event:
			raise error, 'internal error: event expected'
		window, event, value = event
		if self._modal:
			if event != ResizeWindow:
				return 0
		if window and window.is_closed():
			return 0
		for w in [window, None]:
			while 1:
				for key in [(w, event), (w, None)]:
					if self._windows.has_key(key):
						e = windowinterface.readevent()
						func, arg = self._windows[key]
						apply(func, (arg, window, \
							  event, value))
						return 1
				if not w:
					break
				w = w._parent_window
				if w == windowinterface._toplevel:
					break
		return 0

	def testevent(self):
		while 1:
			self._checktime()
			if windowinterface.testevent():
				if not self._trycallback():
					# get here if the first event
					# in the queue does not cause
					# a callback
					return 1
				continue
			# get here only when there are no pending events
			return 0

	def readevent(self):
		while 1:
			if self.testevent():
				return windowinterface.readevent()
			if self._timers or self._select_fdlist:
				if self._timers:
					(t, arg, tid) = self._timers[0]
					t0 = time.millitimer()
				else:
					t = 0
				wtd = [self._winfd] + self._select_fdlist
				ifdlist, ofdlist, efdlist = select.select(\
					  wtd, [], [], t)
				for fd in ifdlist:
					if fd in self._select_fdlist:
						(cb, a) = self._select_dict[fd]
						apply(cb, a)
				if self._timers:
					t1 = time.millitimer()
					dt = float(t1 - t0) / 1000
					self._timers[0] = (t - dt, arg, tid)
			else:
				windowinterface.waitevent()

	def remove_window_callbacks(self, window):
		# called when window closes
		for (w, e) in self._windows.keys():
			if w == window:
				self.unregister(w, e)

	def setcallback(self, event, func, arg):
		self.register(None, event, func, arg)

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

	def clean_callbacks(self):
		for (win, event) in self._windows.keys():
			if win and win.is_closed():
				self.register(win, event, None, None)

	def select_setcallback(self, fd, cb, arg):
		if cb == None:
			self._select_fdlist.remove(fd)
			del self._select_dict[fd]
			return
		if not self._select_dict.has_key(fd):
			self._select_fdlist.append(fd)
		self._select_dict[fd] = (cb, arg)

	def startmodal(self):
		self._modal = 1

	def endmodal(self):
		self._modal = 0

	def mainloop(self):
		while 1:
			dummy = self.readevent()

# There is one instnce of the _Events class.  It is created here.
_event_instance = _Events().init()

# In case you want an class instance you can use this.
def Events():
	return _event_instance

# The interface functions.
def settimer(sec, arg):
	_event_instance.settimer(sec, arg)

def enterevent(win, event, arg):
	_event_instance.enterevent(win, event, arg)

def pollevent():
	return _event_instance.pollevent()

def testevent():
	return _event_instance.testevent()

def readevent():
	return _event_instance.readevent()

def setcallback(event, func, arg):
	_event_instance.setcallback(event, func, arg)

def register(win, event, func, arg):
	_event_instance.register(win, event, func, arg)

def unregister(win, event):
	_event_instance.unregister(win, event)

def clean_callbacks():
	_event_instance.clean_callbacks()

def select_setcallback(fd, cb, arg):
	_event_instance.select_setcallback(fd, cb, arg)

def startmodal():
	_event_instance.startmodal()

def endmodal():
	_event_instance.endmodal()

def mainloop():
	_event_instance.mainloop()
