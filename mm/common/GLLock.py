# This module defines a global lock on GL operations

gl_lock = None

def init():
	global gl_lock
	if gl_lock is None:
		import thread
		gl_lock = thread.allocate_lock()
