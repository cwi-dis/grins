
import Transitions

# timer support
import windowinterface
import time

class TransitionEngine:
	def __init__(self, window, outtrans, runit, dict):
		self.windows = [window,]
		self.outtrans = outtrans
		self.dict = dict
		
		self.duration = dict.get('dur', 1)
		self._multiElement = dict.get('multiElement')
		self._childrenClip = dict.get('childrenClip')

		trtype = dict['trtype']
		subtype = dict.get('subtype')
		klass = Transitions.TransitionFactory(trtype, subtype)
		self.transitiontype = klass(self, dict)

		self.__fiber_id = 0

		self.startprogress = dict['startProgress']
		self.endprogress = dict['endProgress']
		if self.endprogress<=self.startprogress:
			self.startprogress = 0.0
			self.endprogress = 1.0
			#raise AssertionError

		self.__transperiod = self.duration / (self.endprogress-self.startprogress)
		self.__begin = self.__transperiod * self.startprogress
		self.__end = self.__transperiod * self.endprogress

	def __del__(self):
		if self.transitiontype:
			self.endtransition()

	def join(self, window, ismaster):
		"""Join this (sub or super) window to an existing transition"""
		if ismaster:
			self.windows.insert(0, window)
		else:
			self.windows.append(window)
		x, y, w, h = self.windows[0]._rect
		self.transitiontype.move_resize((0, 0, w, h))

	def ismaster(self, wnd):
		return self.windows[0]==wnd

	def begintransition(self):
		# transition window
		# or parent window in multiElement transitions
		wnd = self.windows[0]
		
		# resize to this window
		x, y, w, h = wnd._rect
		self.transitiontype.move_resize((0, 0, w, h))

		# create surfaces
		self._passive = wnd._passive
		wnd._drawsurf = wnd.createDDS()
		self._active = wnd.createDDS()
		self._tmp = wnd.createDDS()

		self.__start = time.time() - self.__begin
		self.settransitionvalue(self.startprogress)
		if self.duration<=0.0:
			self.settransitionvalue(self.endprogress)
		else:	
			self.__register_for_timeslices()

	def endtransition(self):
		self.__unregister_for_timeslices()
		self.windows[0]._drawsurf = None
		self.transitiontype = None
	
	def settransitionvalue(self, value):
		if value<0.0 or value>1.0:
			raise AssertionError

		parameters = self.transitiontype.computeparameters(value)
		wnd = self.windows[0]
		
		if self._multiElement:
			wnd.paintOnDDS(self._active, wnd)
		else:
			wnd._paintOnDDS(self._active, wnd._rect)

		if self.outtrans:
			vfrom = self._active
			vto = wnd._passive
		else:
			vfrom = wnd._passive
			vto = self._active

		tmp  = self._tmp
		dst  = wnd._drawsurf
		dstrgn = None
		self.transitiontype.updatebitmap(parameters, vto, vfrom, tmp, dst, dstrgn)
		wnd.update()

	def onIdle(self):
		t_sec = time.time() - self.__start
		if t_sec>=self.__end:
			self.settransitionvalue(self.endprogress)
			self.__unregister_for_timeslices()
		else:
			self.settransitionvalue(t_sec/self.__transperiod)
	
	def __register_for_timeslices(self):
		if not self.__fiber_id:
			windowinterface.setidleproc(self.onIdle)
			self.__fiber_id = 1

	def __unregister_for_timeslices(self):
		if self.__fiber_id:
			windowinterface.cancelidleproc(self.onIdle)
			self.__fiber_id = 0
