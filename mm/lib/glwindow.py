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


# List of windows, indexed by window id converted to string.

windowmap = {}


# Registration procedure.
# Events will be handled automatically whenever you call
# fl.do_forms() or fl.check_forms().

def register(object, wid):
	fl.set_event_call_back(dispatch)
	windowmap[`wid`] = object
	object.glwindow_wid = wid


# Unregistration procedure.

def unregister(object):
	del windowmap[`object.glwindow_wid`]


# The base class for GL windows

class glwindow():
	#
	# Event dispatchers, named after the events.
	# Note: the window is *not* made current; you must call winset()!
	#
	def redraw(self):
		# REDRAW event.  This may also mean a resize!
		pass
	#
	def keybd(self, val):
		# KEYBD event.
		# 'val' is the ASCII value of the character.
		pass
	#
	def mouse(self, (dev, val)):
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
		#  WINSHUT event: close window, other windows remain.
		# This may be refused.
		pass
	#
	def winquit(self):
		#  WINQUIT event: close last window.
		# This may be refused.
		# By default, call the method for closing any old window.
		self.winshut()


# Install backward compatibility (un)registration methods.

glwindow.register = register
glwindow.unregister = unregister


# Global state

class Struct(): pass
state = Struct()
state.focuswindow = None
state.focuswid = None


# Old functions that used to be more complicated:

mainloop = fl.do_forms
check = fl.check_forms


# Event dispatcher, installed as FORMS' event callback

from DEVICE import REDRAW, KEYBD, MOUSE3, MOUSE2, MOUSE1, INPUTCHANGE
from DEVICE import WINSHUT, WINQUIT

def dispatch(dev, val):
	if dev = REDRAW:
		# Ignore events for unregistered windows
		key = `val`
		if windowmap.has_key(key):
			window = windowmap[key]
			gl.winset(val)
			window.redraw()
		else:
			report('REDRAW event for unregistered window')
	elif dev = KEYBD:
		if state.focuswindow:
			gl.winset(state.focuswid)
			state.focuswindow.keybd(val)
		else:
			report('KEYBD event with no focus window')
	elif dev in (MOUSE3, MOUSE2, MOUSE1): # In left-to-right order
		if state.focuswindow:
			gl.winset(state.focuswid)
			state.focuswindow.mouse(dev, val)
		else:
			report('MOUSE event with no focus window')
	elif dev = INPUTCHANGE:
		if state.focuswindow:
			gl.winset(state.focuswid)
			state.focuswindow.leavewindow()
			state.focuswindow = None
			state.focuswid = None
		if val <> 0:
			key = `val`
			if windowmap.has_key(key):
				state.focuswindow = windowmap[key]
				state.focuswid = val
				gl.winset(val)
				state.focuswindow.enterwindow()
			else:
				report('INPUTCHANGE for unregistered window')
	elif dev = WINSHUT:
		key = `val`
		if windowmap.has_key(key):
			gl.winset(val)
			window = windowmap[key]
			window.winshut()
		else:
			report('WINSHUT for unregistered window')
	elif dev = WINQUIT:
		report('WINQUIT')
		key = `val`
		if windowmap.has_key(key):
			gl.winset(val)
			window = windowmap[key]
			window.winquit()
		else:
			report('WINQUIT for unregistered window')
	else:
		report('unrecognized event: ' + `dev, val`)


# Debug/warning output function for dispatch()

def report(s):
	print 'glwindow.dispatch:', s


# Useful subroutine to call prefposition/prefsize.
# The input arguments (h, v) are in X screen coordinates (origin top left);
# prefposition uses GL screen coordinates (origin bottom left).
# Negative (h, v) values or zero (width, height) values are assumed
# to be defaults.
# XXX Should use 0 for (h, v) defaults and negative values for offsets
# XXX from right/top end!

def setgeometry(arg):
	if arg = None:
		return # Everything default
	h, v, width, height = arg
	if h < 0 and v < 0 and width = 0 and height = 0:
		return # Everything default
	if width = 0 and height = 0:
		height = 300
		width = 400
	else:
		# Default aspect ratio (height/width) is 3/4
		if width = 0: width = int(height / 0.75)
		elif height = 0: height = int(width * 0.75)
	if h < 0 and v < 0:
		gl.prefsize(width, height)
	else:
		scrwidth = gl.getgdesc(GL.GD_XPMAX)
		scrheight = gl.getgdesc(GL.GD_YPMAX)
		x, y = h, scrheight-v-height
		# Correction for window manager frame size
		x = x - WMCORR_X
		y = y + WMCORR_Y
		gl.prefposition(x, x+width-1, y, y+height-1)


# Return the geometry parameters of current GL window, in a format
# that can be passed to setgeometry to reconstruct the window's geometry.

def getgeometry():
	x, y = gl.getorigin()
	width, height = gl.getsize()
	scrwidth = gl.getgdesc(GL.GD_XPMAX)
	scrheight = gl.getgdesc(GL.GD_YPMAX)
	return x, scrheight - y - height, width, height


# Change the geometry of a window

def relocate(arg):
	if arg = None: return
	h, v, width, height = arg
	scrwidth = gl.getgdesc(GL.GD_XPMAX)
	scrheight = gl.getgdesc(GL.GD_YPMAX)
	x1, x2 = h, h + width
	y1, y2 = scrheight-v-height, scrheight-v
	gl.winposition(x1, x2, y1, y2)


# Hack, hack: some X window managers interpret the prefered position
# and size as including the window frame.  Different window managers
# have different deviations of the window position.  This wouldn't
# be a big problem, except that if you repeatedly close a window and
# reopen it at its last position, it tends to drift away.
# To compensate for this, the user can set the environment variable
# WMCORR to the (x,y) correction constants.  For TWM, for instance,
# WMCORR=1,21 appears to be valid.  For 4Dwm, use WMCORR=0,0 (default).
# The correction is applied by setgeometry().

import posix
if posix.environ.has_key('WMCORR'):
	WMCORR_X, WMCORR_Y = eval(posix.environ['WMCORR'])
	# Make sure they are integers:
	WMCORR_X = int(WMCORR_X)
	WMCORR_Y = int(WMCORR_Y)
else:
	WMCORR_X, WMCORR_Y = 0, 0
