
# base class for transition taxonomy
class Transition:
	def __init__(self, memdc):
		self._memdc = memdc

	def setValue(self, d):
		if d<0.0 or d>1.0:
			raise AssertionError
		self._curvalue = d
		curMemDC = self._memdc.createCurMemDC()
		dc = self._memdc.beginUpdate()
		params = self.coputeparams()
		self.updatebitmap(dc, self._memdc, curMemDC, params)
		self._memdc.endUpdate()

	def getSize(self):
		return self._memdc.getSize()

	def getRect(self):
		w, h = self._memdc.getSize()
		return 0, 0, w, h

	def bitblt(self, dc1, rc, dc2, pos):
		if rc[2]!=0 and rc[3]!=0:
			self._memdc.drawMemDCOn(dc1,rc,dc2,pos)
	
	def updatebitmap(self, dc, dc1, dc2, params):
		rc1, pos1, rc2, pos2 = params
		self.bitblt(dc, rc1, dc1, pos1)
		self.bitblt(dc, rc2, dc2, pos2)

	# default to a subtype of EdgeWipeTransition
	def coputeparams(self):
		w, h = self.getSize()
		d = self._curvalue
		dw = int(d*w+0.5)

		# copy frozen bmp
		rc1 = dw, 0, w-dw, h # copy to this rect
		pos1 = dw, 0 # starting from bmp pos

		# copy current bmp
		rc2 = 0, 0, dw, h # copy to this rect
		pos2 = 0, 0 # starting from bmp pos

		return rc1, pos1, rc2, pos2

class EdgeWipeTransition(Transition):
	def coputeparams(self):
		w, h = self.getSize()
		d = self._curvalue
		dw = int(d*w+0.5)

		# copy frozen bmp
		rc1 = dw, 0, w-dw, h # copy to this rect
		pos1 = dw, 0 # starting from bmp pos

		# copy current bmp
		rc2 = 0, 0, dw, h # copy to this rect
		pos2 = 0, 0 # starting from bmp pos

		return rc1, pos1, rc2, pos2

class IrisWipeTransition(Transition):
	pass

class RadialWipeTransition(Transition):
	pass

class MatrixWipeTransition(Transition):
	pass

class PushWipeTransition(Transition):
	def coputeparams(self):
		w, h = self.getSize()
		d = self._curvalue
		dw = int(d*w+0.5)

		# copy frozen bmp
		rc1 = dw, 0, w-dw, h # copy to this rect
		pos1 = 0, 0 # starting from bmp pos

		# copy current bmp
		rc2 = 0, 0, dw, h # copy to this rect
		pos2 = 0, 0 # starting from bmp pos

		return rc1, pos1, rc2, pos2

class SlideWipeTransition(Transition):
	def coputeparams(self):
		w, h = self.getSize()
		d = self._curvalue
		dw = int(d*w+0.5)

		# copy frozen bmp
		rc1 = dw, 0, w-dw, h # copy to this rect
		pos1 = dw, 0 # starting from bmp pos

		# copy current bmp
		rc2 = 0, 0, dw, h # copy to this rect
		pos2 = w-dw, 0 # starting from bmp pos

		return rc1, pos1, rc2, pos2

class FadeTransition(Transition):
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
	def __init__(self, dict, memdc):
		self._dict = dict
		self._memdc = memdc

	# return the appropriate transition class
	def getTransition(self):
		trtype = self._dict.get('trtype')
		if TRANSITIONDICT.has_key(trtype):
			return TRANSITIONDICT[trtype](self._memdc)
		return Transition(self._memdc)

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
