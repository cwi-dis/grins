# This file is used by ../lib/windowinterface to decide whether to use
# fl.qdevice or gl.qdevice. In the editor fl is used.
import fl
fl_or_gl = fl

_real_qread = fl.qread
_real_qtest = fl.qtest

_last_forms = None

_no_qread = 1				# not allowed to block initially

_lock = None

def mayblock():
	return _no_qread == 0

def uselock(lock):
	global _lock
	_lock = lock

def startmonitormode():
	global _no_qread
	import glwindow
	fl.deactivate_all_forms()
	glwindow.stop_callback_mode()
	_no_qread = 0

def endmonitormode():
	global _no_qread
	import glwindow
	fl.activate_all_forms()
	glwindow.start_callback_mode()
	_no_qread = 1

def _qread():
	if _lock:
		_lock.acquire()
	global _last_forms
	while not _last_forms:
		_last_forms = fl.do_forms()
	dev, val = _real_qread()
	import glwindow
	glwindow.dispatch(dev, val)
	if _lock:
		_lock.release()
	_last_forms = None
	return 0, 0

def _qtest():
	if not mayblock():
		return None
	if _lock:
		_lock.acquire()
	retval = None
	global _last_forms
	if not _last_forms:
		_last_forms = fl.check_forms()
	if _last_forms:
		retval = _real_qtest()
	if _lock:
		_lock.release()
	return retval

fl_or_gl.qread = _qread
fl_or_gl.qtest = _qtest
