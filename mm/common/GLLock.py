# This module defines a global lock on GL operations.
# The gl_rawlock is the real lock, and the gl_lock is a wrapper that
# allows you to do multiple acquires() within a single thread.
# NOTE that the gl_lock should NEVER be shared by multiple threads.

gl_rawlock = None
gl_lock = None

def init():
	global gl_lock, gl_rawlock
	if gl_rawlock is None:
		import thread
		gl_rawlock = thread.allocate_lock()
		gl_lock = LockWrapper(gl_rawlock)

class LockWrapper:
	def __init__(self, lock):
		self.lock = lock
		self.count = 0

	def acquire(self, *args):
		if self.count < 0:
			raise 'LockWrapper.acquire: lock.count < 0!'
		if self.count:
			self.count = self.count + 1
##			print 'acquire skipped:', self.count #DBG
			if args == ():
				return
			else:
				return 1
##		print 'do acquire' #DBG
		if args == ():		# Hard acquire
			self.lock.acquire()
			self.count = 1
			return
		else:			# Soft acquire
			rv = self.lock.acquire(args[0])
			if rv:
				self.count = 1
			return rv

	def release(self):
		if self.count <= 0:
			raise 'LockWrapper.release: lock.count <= 0!'
		self.count = self.count - 1
		if self.count:
##			print 'release skipped:', self.count #DBG
			return
##		print 'do release' #DBG
		self.lock.release()
