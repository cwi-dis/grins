import time

class TransitionEngine:
	def __init__(self, window, inout, runit, dict):
		print 'transition', self, window, time.time(), dict
		
	def endtransition(self):
		print 'endtransition', self, time.time()
		
	def changed(self):
		print 'changed', self, time.time()
		
	def settransitionvalue(self, value):
		pass
		
