# This file is used by ../lib/windowinterface to decide whether to use
# fl.qdevice or gl.qdevice. In the editor fl is used.
import fl
fl_or_gl = fl

_real_qread = fl.qread
_real_qtest = fl.qtest

_last_forms = None

_no_qread = 1				# not allowed to block initially

def mayblock():
	return _no_qread == 0

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
	global _last_forms
	while not _last_forms:
		_last_forms = fl.do_forms()
	retval = _real_qread()
	_last_forms = None
	return retval

def _qtest():
	global _last_forms
	if not _last_forms:
		_last_forms = fl.check_forms()
	if _last_forms:
		retval = _real_qtest()
		return retval
	return None

fl_or_gl.qread = _qread
fl_or_gl.qtest = _qtest
