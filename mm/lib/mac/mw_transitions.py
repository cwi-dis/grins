import time
import Qd
import mw_globals

class TransitionClass:
	def __init__(self, engine, dict):
		self.dict = dict
		
	def _computeparameters(self, value, oldparameters):
		pass
		
	def _updatebitmap(self, parameters, src1, src2, dst):
		pass
		
class NullTransition(TransitionClass):
	pass
	
class WipeTransition(TransitionClass):
	def _computeparameters(self, value, oldparameters):
		return int(value*100)
		
	def _updatebitmap(self, parameters, src1, src2, dst):
		print '-Update to', parameters

class TransitionEngine:
	def __init__(self, window, inout, runit, dict):
		print 'transition', self, window, time.time(), dict
		dur = dict.get('dur', 1)
		self.window = window
		self.starttime = time.time()	# Correct?
		self.duration = dur
		self.running = runit
		self.value = 0
		self.transitiontype = WipeTransition(self, dict)
		self.currentparameters = None
		# xxx startpercent/endpercent
		# xxx transition type, etc
##		self.endtimerid = mw_globals.toplevel.settimer(dur, (self._cleanup, ()))
		mw_globals.toplevel.setidleproc(self.changed)
		
	def endtransition(self):
		"""Called by upper layer (window) to tear down the transition"""
		print 'endtransition', self, time.time()
		mw_globals.toplevel.cancelidleproc(self.changed)
		self.window = None
		self.transitiontype = None
		
	def changed(self):
		"""Called by upper layer when it wants the destination bitmap recalculated"""
		print 'changed', self, time.time()
		if self.running:
			self.value = float(time.time() - self.starttime) / self.duration
			if self.value >= 1.0:
				self._cleanup()
				return
		self._updatebitmap()
		
	def settransitionvalue(self, value):
		"""Called by uppoer layer when it has a new percentage value"""
		self.value = value / 100.0
		self._updatebitmap()
		
	def _cleanup(self):
		"""Internal function called when our time is up. Ask the upper layer (window)
		to tear us down"""
		if self.window:
			self.window.endtransition()
		
	def _updatebitmap(self):
		"""Internal: do the actual computation, iff anything has changed since last time"""
		oldparameters = self.currentparameters
		self.currentparameters = self.transitiontype._computeparameters(self.value, oldparameters)
		if self.currentparameters == oldparameters:
			return
		self.transitiontype._updatebitmap(self.currentparameters, None, None, None)
