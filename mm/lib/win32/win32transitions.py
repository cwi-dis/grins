
import Transitions

# timer support
import windowinterface
import time

class TransitionEngine:
	def __init__(self, window, inout, runit, dict):
		self.window = window
		self.duration = dict.get('dur', 1)
		self.outtransition = inout

		trtype = dict['trtype']
		subtype = dict.get('subtype')
		klass = Transitions.TransitionFactory(trtype, subtype)
		self.transitiontype = klass(self, dict)

		self.__fiber_id = 0

		x, y, w, h = self.window._rect
		self.transitiontype.move_resize((0, 0, w, h))

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

	def begintransition(self):
		# create surfaces
		self._passive = self.window._passive
		self.window._drawsurf = self.window.createDDS()
		self._active = self.window.createDDS()
		self._tmp = self.window.createDDS()

		self.__start = time.time() - self.__begin
		self.settransitionvalue(self.startprogress)
		if self.duration<=0.0:
			self.settransitionvalue(self.endprogress)
		else:	
			self.__register_for_timeslices()

	def endtransition(self):
		self.__unregister_for_timeslices()
		self.window._drawsurf = None
		self.transitiontype = None
	
	def settransitionvalue(self, value):
		if value<0.0 or value>1.0:
			raise AssertionError

		parameters = self.transitiontype.computeparameters(value)
		self.window.paintOnDDS(self._active, self.window)
		if self.outtransition:
			vfrom = self._active
			vto = self.window._passive
		else:
			vfrom = self.window._passive
			vto = self._active
		tmp  = self._tmp
		dst  = self.window._drawsurf
		dstrgn = None
		self.transitiontype.updatebitmap(parameters, vto, vfrom, tmp, dst, dstrgn)
		self.window.update()

	def onIdle(self):
		t_sec = time.time() - self.__start
		if t_sec>=self.__end:
			self.settransitionvalue(self.endprogress)
			self.endtransition()
		else:
			self.settransitionvalue(t_sec/self.__transperiod)
	
	def isCallable(self):
		return self.transitiontype != None

	def __register_for_timeslices(self):
		if not self.__fiber_id:
			self.__fiber_id=windowinterface.register((self.isCallable,()),(self.onIdle,()))

	def __unregister_for_timeslices(self):
		if self.__fiber_id:
			windowinterface.unregister(self.__fiber_id)
			self.__fiber_id=0


