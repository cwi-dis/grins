__version__ = "$Id$"

import Transitions

# timer support
import windowinterface
import time

# for Sleep
import winkernel

import wingdi

class TransitionEngine:
	def __init__(self, window, outtrans, runit, dict, cb):
		self.windows = [window,]
		self.outtrans = outtrans
		
		self.__duration = dict.get('dur', 1)
		self.__multiElement = dict.get('coordinated')
		self.__childrenClip = dict.get('clipBoundary', 'children') == 'children'

		self.__callback = cb

		trtype = dict.get('trtype', 'fade')
		subtype = dict.get('subtype')
		klass = Transitions.TransitionFactory(trtype, subtype)
		self.__transitiontype = klass(self, dict)

		self.__fiber_id = None
		self.__running = 0		

		self.__startprogress = dict.get('startProgress', 0)
		self.__endprogress = dict.get('endProgress', 1)
		if self.__endprogress <= self.__startprogress:
			self.__transperiod = 0
		elif self.__duration <= 0:
			self.__transperiod = 0
			self.__startprogress = self.__endprogress
		else:
			self.__transperiod = float(self.__endprogress - self.__startprogress) / self.__duration

	def __del__(self):
		if self.__transitiontype:
			self.endtransition()
		del self._tosurf
		del self._tmp

	def begintransition(self):
		self.__createSurfaces()
		self.__running = 1	
		self.__start = time.time()
		self.settransitionvalue(self.__startprogress)
		if self.__duration<=0.0:
			self.settransitionvalue(self.__endprogress)
		else:	
			self.__register_for_timeslices()

	def endtransition(self):
		if not self.__transitiontype: return
		self.__unregister_for_timeslices()
		if self.__callback:
			apply(apply, self.__callback)
			self.__callback = None
		self.__transitiontype = None
		self.__running = 0		
		wnd = self.windows[0]
		if wnd.is_closed():
			return
		else:
			# XXX: patch
			if self.outtrans and wnd._active_displist:
				wnd._active_displist.close()
		for win in self.windows:
			win._transition = None
			win._drawsurf = None
		wnd.update(wnd.getwindowpos())

	def settransitionvalue(self, value):
		if value<0.0 or value>1.0:
			raise AssertionError
		parameters = self.__transitiontype.computeparameters(value)
		
		# transition window
		# or parent window in multiElement transitions
		wnd = self.windows[0]
		if wnd.is_closed():
			return
		
		# cases:
		# 1. multiElement==true, childrenClip==true
		# 2. multiElement==true, childrenClip==false
		# 3. multiElement==false
		if self.__multiElement:
			if self.__childrenClip:
				# since children clipping will be done in wnd's paint method
				# do a normal painting on active surface
				wnd.paintOnSurf(self._tosurf, wnd)
			else:
				# do a normal painting on active surface
				wnd.paintOnSurf(self._tosurf, wnd)
		else:
			if self.outtrans:
				wnd._paintOnSurf(wnd._fromsurf)
				wnd.updateBackSurf(self._tosurf, exclwnd = wnd) 
			else:
				wnd.updateBackSurf(wnd._fromsurf, exclwnd = wnd)
				wnd._paintOnSurf(self._tosurf)
	
		fromsurf = 	wnd._fromsurf
		tosurf = self._tosurf	
		tmpsurf  = self._tmp
		dstsurf  = wnd._drawsurf
		dstrgn = None
		
		self.__transitiontype.updatebitmap(parameters, tosurf, fromsurf, tmpsurf, dstsurf, dstrgn)
		wnd.update(wnd.getwindowpos())

	def join(self, window, ismaster, cb):
		# Join this (sub or super) window to an existing transition
		if ismaster:
			self.__callback = cb
			if self.isrunning():
				self.windows.insert(0, window)
				self.__createSurfaces()
			else:
				self.windows.insert(0, window)
		else:
			self.windows.append(window)

		x, y, w, h = self.windows[0]._rect
		self.__transitiontype.move_resize((0, 0, w, h))

	def _ismaster(self, wnd):
		return self.windows[0]==wnd

	def _isrunning(self):
		return self.__running

	def __createSurfaces(self):
		# transition window
		# or parent window in multiElement transitions
		wnd = self.windows[0]
		try:
			wnd._fromsurf = wnd.cloneBackSurf(exclwnd = wnd, dopaint = 1)
			wnd._drawsurf = wnd.cloneBackSurf(exclwnd = wnd, dopaint = 0)
			self._tosurf = wnd.cloneBackSurf(exclwnd = wnd, dopaint = 0)
			self._tmp = wnd.cloneBackSurf(exclwnd = wnd, dopaint = 0)
		except wingdi.error, arg:
			print arg

		# resize to this window
		x, y, w, h = wnd._rect
		self.__transitiontype.move_resize((0, 0, w, h))

	def __onIdle(self):
		if self.windows[0].is_closed():
			self.endtransition()
			return
		t_sec = time.time() - self.__start
		if t_sec>=self.__duration:
			try:
				self.settransitionvalue(self.__endprogress)
				self.endtransition()
			except ddraw.error, arg:
				print arg			
		else:
			try:
				self.settransitionvalue(self.__startprogress + self.__transperiod * t_sec)
			except wingdi.error, arg:
				print arg			
				
	
	def __register_for_timeslices(self):
		if not self.__fiber_id:
			self.__fiber_id = windowinterface.setidleproc(self.__onIdle)

	def __unregister_for_timeslices(self):
		if self.__fiber_id is not None:
			windowinterface.cancelidleproc(self.__fiber_id)
			self.__fiber_id = None


