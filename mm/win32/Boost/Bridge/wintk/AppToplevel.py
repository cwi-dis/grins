__version__ = "$Id$"

import winkernel

import MainWnd

from appcon import *

class _Toplevel:
	def __init__(self):
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._idles = {}
		self.__idleid = 0
		self._time = float(winkernel.GetTickCount())/TICKS_PER_SECOND

		self._frame = None

	def newdocument(self, cmifdoc, adornments=None, commandlist=None):
		if self._frame is None:
			self._frame = MainWnd.MainWnd()
			self._frame.create()
		return self._frame

	def createmainwnd(self, title = None, adornments = None, commandlist = None):
		if self._frame is None:
			self._frame = MainWnd.MainWnd()
			self._frame.create()
			self._frame.set_commandlist(commandlist, 'app')
		return self._frame

	def getactivedocframe(self):
		return self._frame
	
	def getmainwnd(self):
		if self._frame is None:
			self._frame = MainWnd.MainWnd()
			self._frame.create()
		return self._frame

	def serve_events(self,params=None):	
		while self._timers:
			t = float(winkernel.GetTickCount())/TICKS_PER_SECOND
			sec, cb, tid = self._timers[0]
			sec = sec - (t - self._time)
			self._time = t
			if sec <= 0.002:
				del self._timers[0]
				apply(apply, cb)
			else:
				self._timers[0] = sec, cb, tid
				break
		self._time = float(winkernel.GetTickCount())/TICKS_PER_SECOND
		self.serve_timeslices()

	# Register a timer even
	def settimer(self, sec, cb):
		self._timer_id = self._timer_id + 1
		t0 = float(winkernel.GetTickCount())/TICKS_PER_SECOND
		if self._timers:
			t, a, i = self._timers[0]
			t = t - (t0 - self._time) # can become negative
			self._timers[0] = t, a, i
		self._time = t0
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

	# Unregister a timer even
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

	# Register for receiving timeslices
	def setidleproc(self, cb):
		self.__idleid = self.__idleid + 1
		self._idles[self.__idleid] = cb
		return self.__idleid

	# Register for receiving timeslices
	def cancelidleproc(self, id):
		del self._idles[id]

	# Dispatch timeslices
	def serve_timeslices(self):
		for onIdle in self._idles.values():
			onIdle()

	def _image_size(self, filename, grinsdoc):
		from win32ig import win32ig
		img = win32ig.load(filename) 
		return win32ig.size(img)[:2]

	def _image_handle(self, filename, grinsdoc):
		from win32ig import win32ig
		return win32ig.load(filename) 

	#
	def register_embedded(self, event, func, arg):
		if event == 'OnOpen':
			self.__onOpenEvent = func, arg

	def unregister_embedded(event):
		self.__onOpenEvent = None

	def getOpenEvent(self):
		return self.__onOpenEvent
