
import Transitions

# timer support
import windowinterface
import time

class TransitionEngine:
	def __init__(self, window, inout, runit, dict):
		self.duration = dict.get('dur', 1)

		trtype = dict['trtype']
		subtype = dict.get('subtype')
		klass = Transitions.TransitionFactory(trtype, subtype)
		self.transitiontype = klass(self, dict)
		#print klass, inout, runit, dict

		# implementation artifact vars
		self._memdc = window._passiveMemDC
		self.__fiber_id = 0

		w, h = self._memdc.getSize()
		self.transitiontype.move_resize((0, 0, w, h))

	def __del__(self):
		self.endtransition()

	def begintransition(self):
		self.__start = time.time()
		self.settransitionvalue(0.0)
		if self.duration<=0.0:
			self.settransitionvalue(1.0)
		else:	
			self.__register_for_timeslices()

	def endtransition(self):
		self.__unregister_for_timeslices()
		self.__transition = None
	
	def settransitionvalue(self, value):
		print 'settransitionvalue',value
		if value<0.0 or value>1.0:
			raise AssertionError
		curMemDC = self._memdc.createCurMemDC()
		dc = self._memdc.beginUpdate()
		parameters = self.transitiontype.computeparameters(value)
		self.transitiontype.updatebitmap(parameters, self._memdc, curMemDC, None, dc, None)
		self._memdc.endUpdate()

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

