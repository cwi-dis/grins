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

class glwindow():
	#
	# Registration method.  Call this from your init method,
	# with the window ID of the window you've created.
	#
	def register(self, wid):
		self.wid = wid
		windowmap[`wid`] = self
	#
	# Unregistration method.  Call this when you close the window.
	#
	def unregister(self):
		del windowmap[`self.wid`]
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

class Struct(): pass
state = Struct()
state.focuswindow = None

def mainloop():
	while 1:
		obj = fl.do_forms()
		if obj = FL.EVENT:
			dev, val = fl.qread()
			dispatch(dev, val)
		else:
			if obj = None:
				print 'do_forms returned NULL object!'
			else:
				print 'do_forms returned alien object!'

def check():
	while 1:
		obj = fl.check_forms()
		if obj = None:
			return None
		if obj = FL.EVENT:
			dev, val = fl.qread()
			dispatch(dev, val)
		else:
			return obj

def dispatch(dev, val):
	if dev = REDRAW:
		window = windowmap[`val`]
		window.redraw()
	elif dev = KEYBD:
		if state.focuswindow:
			state.focuswindow.keybd(val)
		else:
			print 'KEYBD event with no focus window!'
	elif dev in (MOUSE3, MOUSE2, MOUSE1): # In left-to-right order
		if state.focuswindow:
			state.focuswindow.mouse(dev, val)
		else:
			print 'MOUSE event with no focus window!'
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
