# This is the outermost loop in the entire editor/viewer application.
#
# No other code should ever sleep or wait for external events
# (checking events is OK) or do I/O that may block indefinitely
# (file I/O is OK, but not tty I/O).
#
# An exception may be made for modal dialogs ("goodies" of the FORMS library)
# but these should be used *very* sparingly.  In principle every user
# interface component should be reactive at all times.  For example,
# asking for a file name should not be done with a modal dialog -- a
# modeless file selector (which may remain open between uses) is better.
#
# Tasks of this module:
# - call fl.check_forms() or fl.do_forms() to handle forms callbacks
# - dispatch events to non-forms GL windows
# - manage the virtual timer queue

import time
import glwindow
from sched import scheduler

# This queue inherits its interface from the standard module 'sched',
# except for init() and run().  There will be only a single instance.
# All times are expressed in seconds using floating point.
#
class Queue() = scheduler():
	#
	# Inherit enterabs(), enter(), cancel(), empty() from scheduler.
	# The timefunc is implemented differently (it's a real method),
	# and there is no delayfunc!!!
	#
	def init(self):
		self.queue = []
		self.origin = 0.0
		self.msec_origin = time.millitimer()
		self.rate = 0.0		# Initially the clock is frozen
		self.prevrate = 1.0	# Unfreezing starts it at normal speed
		return self
	#
	def timefunc(self):
		t = (time.millitimer() - self.msec_origin) / 1000.0
		now = self.origin + t * self.rate
		return now
	#
	def setrate(self, rate):
		if rate < 0.0:
			raise RuntimeError, 'Queue.setrate with negative rate'
		msec = time.millitimer()
		t = (msec - self.msec_origin) / 1000.0
		now = self.origin + t * self.rate
		self.origin = now
		self.msec_origin = msec
		self.rate = rate
	#
	def freeze(self):
		if self.rate <> 0.0:
			self.prevrate = self.rate
			self.setrate(0)
	#
	def unfreeze(self):
		if self.rate = 0.0:
			self.setrate(self.prevrate)
	#
	# This version of run() busy-waits when there is nothing to do.
	# Eventually we should use FORMS timer objects instead.
	#
	def run(self):
		q = self.queue
		while 1:
			obj = glwindow.check()
			if obj <> None:
				raise RuntimeError, 'object without callback!'
			if q:
				time, priority, action, argument = q[0]
				now = self.timefunc()
				if now >= time:
					del q[0]
					void = action(argument)
	#
