__version__ = "$Id$"

# A GL window object class

# This is an abstract class; you use it as a base class if you want
# to use an actual window object class.

# The main reason for existance is that we need to dispatch GL events
# to the correct code.  The abstract class has callbacks for each type
# of event that GL can send; your concrete class must enable the events
# that it is interested in.  The code for the main loop that dispatches
# events is also here; it uses the FORMS event interface so you can
# also use forms.  *** This means that your window must use the FORMS
# equivalents of the GL device routines, like fl.(un)qdevice(),
# fl.qtest() and fl.qread().  If you don't you're in big trouble! ***

import gl, GL, DEVICE
import fl, FL
import GLLock



# List of windows, indexed by window id converted to string.

windowmap = {}


# Registration procedure.
# Events will be handled automatically whenever you call
# fl.do_forms() or fl.check_forms().

def register(object, wid):
	start_callback_mode()
	windowmap[`wid`] = object
	object.glwindow_wid = wid


# Unregistration procedure.

def unregister(object):
	del windowmap[`object.glwindow_wid`]


callback_mode = 0

def start_callback_mode():
	global callback_mode
	callback_mode = 1
	fl.activate_all_forms()
	fl.set_event_call_back(dispatch)

def stop_callback_mode():
	global callback_mode
	callback_mode = 0
	fl.deactivate_all_forms()
	fl.set_event_call_back(None)

# The base class for GL windows

class glwindow:
	#
	# Basic administrative functions.
	#
	def __init__(self, wid):
		# Initialize the instance.  Derived classes may extend
		# or override this to their liking (e.g. use a
		# different way to store the window id).
		self.wid = wid
	#
	def __repr__(self):
		return '<glwindow instance, wid=' + `self.wid` + '>'
	#
	def setwin(self):
		# Make the window current.  Derived classes may extend
		# or override this to set more state, e.g. fonts.
		gl.winset(self.wid)
	#
	# Event dispatchers, named after the events.
	# The window is current by the time this function is called.
	#
	def redraw(self):
		# REDRAW event.  This may also mean a resize!
		pass
	#
	def rawkey(self, val):
		# raw key event (0-255)
		# 'val' is the key code as defined in DEVICE.py or <device.h>
		pass
	#
	def keybd(self, val):
		# KEYBD event.
		# 'val' is the ASCII value of the character.
		pass
	#
	def mouse(self, dev, val):
		# MOUSE[123] event.
		# 'dev' is MOUSE[123].  'val' is 1 for down, 0 for up.
		pass
	#
	def mousex(self, val):
		# MOUSEX event.
		# 'val' is the new mouse x value.
		pass
	#
	def mousey(self, val):
		# MOUSEY event.
		# 'val' is the new mouse y value.
		pass
	#
	def enterwindow(self):
		# INPUTCHANGE event with val <> 0: mouse enters the window.
		pass
	#
	def leavewindow(self):
		# INPUTCHANGE event with val = 0: mouse leaves the window.
		pass
	#
	def winshut(self):
		# WINSHUT event: close window, other windows remain.
		# This may be refused.
		pass
	#
	def winquit(self):
		# WINQUIT event: close last window.
		# This may be refused.
		# By default, call the method for closing any old window.
		self.winshut()
	#


# Global state

focuswindow = None
focuswid = None


# Old functions that used to be more complicated:

mainloop = fl.do_forms
check = fl.check_forms


# Event dispatcher, installed as FORMS' event callback

dispmap = {}
def devregister(devval, callback, arg):
	dispmap[devval] = (callback, arg)
def undevregister(devval):
	if dispmap.has_key(devval):
		dismap.remove(devval)

from DEVICE import REDRAW, KEYBD, MOUSE3, MOUSE2, MOUSE1, INPUTCHANGE
from DEVICE import WINSHUT, WINQUIT, MOUSEX, MOUSEY

# Locked on entry, locked on return.
def dispatch(dev, val):
	import windowinterface
##	print 'dispatch:', `dev,val` #DBG
	if GLLock.gl_lock:
##		print 'release'
		GLLock.gl_lock.release()
	# Use some undocumented internals of the windowinterface module.
	windowinterface.event._doevent(dev, val)
	while callback_mode and windowinterface.testevent():
		window, event, value = windowinterface.readevent()
##		print 'dispatch now:', event #DBG
##	print 're-acquire'
	GLLock.gl_lock.acquire()
##	handle_event(dev, val)

def handle_event(dev, val):
	global focuswindow, focuswid
	if dev == REDRAW:
		# Ignore events for unregistered windows
		key = `val`
		if windowmap.has_key(key):
			window = windowmap[key]
			window.setwin()
			window.redraw()
##		else:
##			report('REDRAW event for unregistered window')
	elif dispmap.has_key(`dev`+':'+`val`):
		callback, arg = dispmap[`dev`+':'+`val`]
		callback(arg)
	elif not callback_mode:
		pass			# ignore event if not in callback mode
	elif dev == KEYBD:
		if focuswindow:
			focuswindow.setwin()
			focuswindow.keybd(val)
##		else:
##			report('KEYBD event with no focus window')
	elif dev in (MOUSE3, MOUSE2, MOUSE1): # In left-to-right order
		if focuswindow:
			focuswindow.setwin()
			focuswindow.mouse(dev, val)
##		else:
##			report('MOUSE event with no focus window')
	elif dev == MOUSEX:
		if focuswindow:
			focuswindow.setwin()
			focuswindow.mousex(val)
##		else:
##			report('MOUSEX event with no focus window')
	elif dev == MOUSEY:
		if focuswindow:
			focuswindow.setwin()
			focuswindow.mousey(val)
##		else:
##			report('MOUSEY event with no focus window')
	elif dev == INPUTCHANGE:
		if focuswindow:
			focuswindow.setwin()
			focuswindow.leavewindow()
			focuswindow = None
			focuswid = None
		if val <> 0:
			key = `val`
			if windowmap.has_key(key):
				focuswindow = windowmap[key]
				focuswid = val
				focuswindow.setwin()
				focuswindow.enterwindow()
##			else:
##				report('INPUTCHANGE for unregistered window')
	elif dev == WINSHUT:
		key = `val`
		if windowmap.has_key(key):
			window = windowmap[key]
			window.setwin()
			window.winshut()
##		else:
##			report('WINSHUT for unregistered window')
	elif dev == WINQUIT:
		report('WINQUIT')
		key = `val`
		if windowmap.has_key(key):
			window = windowmap[key]
			window.setwin()
			window.winquit()
##		else:
##			report('WINQUIT for unregistered window')
	elif 0 <= dev <= 255:
		if focuswindow:
			focuswindow.setwin()
			focuswindow.rawkey(dev, val)
##		else:
##			report('raw key event with no focus window')
	else:
		report('unrecognized event: ' + `dev, val`)


# Debug/warning output function for dispatch()

def report(s):
	print 'glwindow.dispatch:', s


def mm2pixels(h, v):
	h = int(float(h)/gl.getgdesc(GL.GD_XMMAX)*gl.getgdesc(GL.GD_XPMAX)+0.5)
	v = int(float(v)/gl.getgdesc(GL.GD_YMMAX)*gl.getgdesc(GL.GD_YPMAX)+0.5)
	return h, v

def pixels2mm(h, v):
	h = float(h) / gl.getgdesc(GL.GD_XPMAX) * gl.getgdesc(GL.GD_XMMAX)
	v = float(v) / gl.getgdesc(GL.GD_YPMAX) * gl.getgdesc(GL.GD_YMMAX)
	return h, v

# Useful subroutine to call prefposition/prefsize.
# The input arguments (h, v) are in X screen coordinates (origin top left);
# prefposition uses GL screen coordinates (origin bottom left).
# Negative (h, v) values or zero (width, height) values are assumed
# to be defaults.
# XXX Should use 0 for (h, v) defaults and negative values for offsets
# XXX from right/top end!

def setgeometry(arg):
	if arg is None:
		return # Everything default
	h, v, width, height = arg
	if h < 0 and v < 0 and width == 0 and height == 0:
		return # Everything default
	if width == 0 and height == 0:
		height = 86.4
		width = 115.2
	else:
		# Default aspect ratio (height/width) is 3/4
		if width == 0: width = int(height / 0.75)
		elif height == 0: height = int(width * 0.75)
	width, height = mm2pixels(width, height)
	h, v = mm2pixels(h, v)
	if h < 0 and v < 0:
		gl.prefsize(width, height)
	else:
		scrwidth = gl.getgdesc(GL.GD_XPMAX)
		scrheight = gl.getgdesc(GL.GD_YPMAX)
		x, y = h, scrheight-v-height
		# Correction for window manager frame size
		import calcwmcorr
		wmcorr_x, wmcorr_y = calcwmcorr.calcwmcorr()
		x = x - wmcorr_x
		y = y + wmcorr_y
		gl.prefposition(x, x+width-1, y, y+height-1)


# Return the geometry parameters of current GL window, in a format
# that can be passed to setgeometry to reconstruct the window's geometry.

def getgeometry():
	x, y = gl.getorigin()
	width, height = gl.getsize()
	scrwidth = gl.getgdesc(GL.GD_XMMAX)
	scrheight = gl.getgdesc(GL.GD_YMMAX)
	x, y = pixels2mm(x, y)
	width, height = pixels2mm(width, height)
	return x, scrheight - y - height, width, height


# Change the geometry of a window

def relocate(arg):
	if arg is None: return
	h, v, width, height = arg
	h, v = mm2pixels(h, v)
	width, height = mm2pixels(width, height)
	scrwidth = gl.getgdesc(GL.GD_XPMAX)
	scrheight = gl.getgdesc(GL.GD_YPMAX)
	x1, x2 = h, h + width
	y1, y2 = scrheight-v-height, scrheight-v
	gl.winposition(x1, x2, y1, y2)
