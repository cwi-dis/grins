
import Transitions

# timer support
import windowinterface
import time

class TransitionEngine:
	def __init__(self, window, inout, runit, dict):
		self.window = window
		self.duration = dict.get('dur', 1)
		self.inout = inout

		trtype = dict['trtype']
		subtype = dict.get('subtype')
		klass = Transitions.TransitionFactory(trtype, subtype)
		self.transitiontype = klass(self, dict)

		self.__fiber_id = 0

		x, y, w, h = self.window._rect
		self.transitiontype.move_resize((0, 0, w, h))

	def __del__(self):
		self.endtransition()

	def begintransition(self):
		# create surfaces
		self._passive = self.window._passive
		self.window._drawsurf = self.window.createDDS()
		self._active = self.window.createDDS()
		self._tmp = self.window.createDDS()

		self.__start = time.time()
		self.settransitionvalue(0.0)
		if self.duration<=0.0:
			self.settransitionvalue(1.0)
		else:	
			self.__register_for_timeslices()

	def endtransition(self):
		self.window._drawsurf = None
		self.__unregister_for_timeslices()
		self.__transition = None
	
	def settransitionvalue(self, value):
		if value<0.0 or value>1.0:
			raise AssertionError

		parameters = self.transitiontype.computeparameters(value)
		self.window.paintOnDDS(self._active)
		src_active = self._active
		src_passive = self.window._passive
		tmp  = self._tmp
		dst  = self.window._drawsurf
		dstrgn = None
		if not self.inout:
			self.transitiontype.updatebitmap(parameters, src_active, src_passive, tmp, dst, dstrgn)
		else:
			self.transitiontype.updatebitmap(parameters, src_passive, src_active, tmp, dst, dstrgn)
		
		self.window.update()

	def __onDur(self):
		self.endtransition()

	def on_idle_callback(self):
		self.__fiber_id=0
		t_sec=time.time() - self.__start
		if t_sec>=self.duration:
			self.settransitionvalue(1.0)
			self.__onDur()
		else:
			self.settransitionvalue(t_sec/self.duration)
			self.__register_for_timeslices()
			
	def __register_for_timeslices(self):
		if self.__fiber_id==0:
			self.__fiber_id = windowinterface.settimer(0.05, (self.on_idle_callback,()))

	def __unregister_for_timeslices(self):
		if self.__fiber_id!=0:
			windowinterface.canceltimer(self.__fiber_id)
			self.__fiber_id = 0

