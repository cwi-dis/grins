
# base class for transition taxonomy
class Transition:
	def __init__(self, sfrom, sto):
		self._sfrom, self._sto = sfrom, sto

	def setValue(self, d):
		if d<0.0 or d>1.0:
			raise AssertionError
		print 'transition.setValue',d
		if d==0.0:
			return self._sfrom
		elif d==1.0:
			return self._sto
		else:
			return None

class EdgeWipeTransition(Transition):
	pass

class IrisWipeTransition(Transition):
	pass

class RadialWipeTransition(Transition):
	pass

class MatrixWipeTransition(Transition):
	pass

class PushWipeTransition(Transition):
	pass

class SlideWipeTransition(Transition):
	pass

class FadeTransition(Transition):
	pass

class SlideWipeTransition(Transition):
	pass

###################################
# TransitionFactory
# a helper class responsible to select 
# the appropriate transition class

TRANSITIONDICT = {
	"edgeWipe" : EdgeWipeTransition,
	"irisWipe" : IrisWipeTransition,
	"radialWipe" : RadialWipeTransition,
	"matrixWipe" : MatrixWipeTransition,
	"pushWipe" : PushWipeTransition,
	"slideWipe" : SlideWipeTransition,
	"fade" : FadeTransition,
}

class TransitionFactory:
	def __init__(self, dict, sfrom, sto):
		self._dict = dict
		self._sfrom, self._sto = sfrom, sto

	# return the appropriate transition class
	def getTransition(self):
		trtype = self._dict.get('trtype')
		if TRANSITIONDICT.has_key(trtype):
			return TRANSITIONDICT[trtype](self._sfrom, self._sto)
		return Transition(self._sfrom, self._sto)

###################################
# TransitionEngine
# responsible to play a transition
# (a GRiNS channel like entity)

# timer support
import windowinterface
import time

class TransitionEngine:
	def __init__(self, transition, dict):
		self.__transition = transition
		self.__duration = dict.get('dur', 1.0)
		self.__fiber_id = 0

	def __del__(self):
		self.endtransition()

	def begintransition(self):
		self.__start = time.time()
		self.settransitionvalue(0.0)
		if self.__duration<=0.0:
			self.settransitionvalue(1.0)
		else:	
			self.__register_for_timeslices()

	def endtransition(self):
		self.__unregister_for_timeslices()
		self.__transition = None
	
	def settransitionvalue(self, value):
		self.__transition.setValue(value)

	def __onDur(self):
		if not self.__transition:
			return
		self.endtransition()

	def on_idle_callback(self):
		self.__fiber_id=0
		if self.__transition:
			t_sec=time.time() - self.__start
			if t_sec>=self.__duration:
				self.settransitionvalue(1.0)
				self.__onDur()
			else:
				self.settransitionvalue(t_sec/self.__duration)
				self.__register_for_timeslices()
			
	def __register_for_timeslices(self):
		if self.__fiber_id==0:
			self.__fiber_id = windowinterface.settimer(0.05, (self.on_idle_callback,()))

	def __unregister_for_timeslices(self):
		if self.__fiber_id!=0:
			windowinterface.canceltimer(self.__fiber_id)
			self.__fiber_id = 0
