# A GL window object class

# This is an abstract class; you use it as a base class if you want
# to use an actual window object class.

# The main reason for existance is that we need to dispatch GL events
# to the correct code.  The abstract has callbacks for each type of
# event that GL can send; your concrete class must enable the events
# that it is interested in.  The code for the main loop that dispatches
# events is also here; it uses the FORMS event interface so you can
# also use forms.  *** This means that your window must use the FORMS
# equivalents of the GL device routines, like fl.(un)qdevice(),
# fl.qtest() and fl.qread().  If you don't you're in big trouble! ***

import gl
from GL import *
from DEVICE import *
import fl, FL

# List of windows, indexed by window id converted to string.
windowmap = {}

# The base class for GL windows
class glwindow():
	#
	# Registration method.  Call this from your init method,
	# with the window ID of the window you've created.
	#
	def register(self, wid):
		self.glwindow_wid = wid
		windowmap[`wid`] = self
	#
	# Unregistration method.  Call this when you close the window.
	#
	def unregister(self):
		del windowmap[`self.glwindow_wid`]
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
	def enter(self):
		# INPUTCHANGE event with val <> 0: mouse enters the window.
		pass
	#
	def leave(self):
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
		pass

# Debug/warning output function
def report(s):
	print 'glwindow:', s

# Global state
class Struct(): pass
state = Struct()
state.focuswindow = None


# Some utility functions

def mainloop():
	while 1:
		if fl.do_forms() = FL.EVENT:
			dispatch(fl.qread())

def check():
	while 1:
		obj = fl.check_forms()
		if obj <> FL.EVENT: break
		dispatch(fl.qread())

def dispatch(dev, val):
	if dev = REDRAW:
		window = windowmap[`val`]
		window.redraw()
	elif dev = KEYBD:
		if state.focuswindow:
			state.focuswindow.keybd(val)
		else:
			report('KEYBD event with no focus window!')
	elif dev in (MOUSE3, MOUSE2, MOUSE1): # In left-to-right order
		if state.focuswindow:
			state.focuswindow.mouse(dev, val)
		else:
			report('MOUSE event with no focus window!')
	elif dev = INPUTCHANGE:
		if state.focuswindow:
			state.focuswindow.leave()
			state.focuswindow = None
		if val = 0:
			pass
		else:
			state.focuswindow = windowmap[`val`]
			state.focuswindow.enter()
	elif dev = WINSHUT:
		window = windowmap[`val`]
		window.winshut()
	elif dev = WINQUIT:
		window = windowmap[`val`]
		window.winquit()
	else:
		report('dispatch unrecognized event')


# Useful subroutine to call prefposition/prefsize.
# The input arguments (h, v) are in X screen coordinates (origin top left);
# prefposition uses GL screen coordinates (origin bottom left).
# Negative (h, v) values or zero (width, height) values are assumed
# to be defaults.
# XXX Should use 0 for (h, v) defaults and negative values for offsets
# XXX from right/top end!

def setgeometry(h, v, width, height):
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
		scrwidth = gl.getgdesc(GD_XPMAX)
		scrheight = gl.getgdesc(GD_YPMAX)
		x, y = h, scrheight-v-height
		gl.prefposition(x, x+width-1, y, y+height-1)
