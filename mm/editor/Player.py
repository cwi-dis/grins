# Player module -- mostly defines the Player class.


import time
import gl
import fl
from FL import *
from sched import scheduler
import glwindow
from MMExc import *
import MMAttrdefs
import Timing


# The player algorithm treats the head and tail (begin and end) sides
# of a node as separate events in time; there are separate counters
# and lists of dependencies, indexed by the symbolic constants
# HD and TL: e.g., node.counter[HD], node.deps[HD].

HD, TL = 0, 1


# Control Panel dimensions

CPWIDTH = 300
CPHEIGHT = 100


# The channel map is in a separate module for easy editing.

from ChannelMap import channelmap


# The Player class has only a single instance.
# Its run() method, once started, never returns normally; this replaces
# the mainloop() function in glwindow.py.
#
# It is important that as much time as possible is spent in run()
# rather than in subordinate routines; this improves response time.
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
# To add multiple players, the loop in run(), calling glwindow.mainloop(),
# must be moved to a central place, which implements a real-time queue.
# Player objects must calculate the expected real-time delay to their
# next event and post an event in the RT queue for that time.
# When the expected time changes (e.g., pause is pressed), they should
# cancel the original event and post a new one.  Etc.
# XXX BECAUSE OF THIS, CREATING A SECOND PLAYER CURRENTLY DOESN'T WORK;
# XXX THIS BREAKS THE "RESTORE" COMMAND!

class Player() = scheduler():
	#
	# Initialization.
	#
	def init(self, root):
		# Initialize the scheduler and parameters for timefunc
		self.queue = []
		self.resettimer()
		# Initialize the player
		self.root = root
		self.playing = 0
		self.abcontrol = ()
		# Make the channel objects -- this pops up windows...
		self.channels = {}
		self.channelnames = []
		self.makechannels()
		# Initialize the setcurrenttime callback
		self.setcurrenttime_callback = None
		# Make the control panel last, to show we're ready, finally...
		self.makecpanel()
		# Return self, as any class initializer
		return self
	#
	def show(self):
		self.showchannels()
		self.showcpanel()
	#
	def hide(self):
		self.hidecpanel()
		self.hidechannels()
	#
	def destroy(self):
		self.destroycpanel()
		self.destroychannels()
	#
	def set_setcurrenttime_callback(self, setcurrenttime):
		self.setcurrenttime_callback = setcurrenttime
	#
	#
	# Queue interface, based upon sched.scheduler.
	# This queue has variable time, to implement pause and slow/fast,
	# but the interface to its callers is the same, except init().
	#
	# Inherit enter(), cancel(), empty() from scheduler.
	# Override enterabs() since it must update the timer object.
	# The timefunc is implemented differently (it's a real method),
	# but the call to it from enter() doesn't mind.
	# There is no delayfunc -- our run() doesn't use that.
	#
	def enterabs(self, args):
		id = scheduler.enterabs(self, args)
		self.updatetimer()
		return id
	#
	def timefunc(self):
		t = (time.millitimer() - self.msec_origin) / 1000.0
		now = self.origin + t * self.rate
		return now
	#
	def resettimer(self):
		self.origin = 0.0	# Current time
		self.rate = 0.0		# Initially the clock is frozen
		self.msec_origin = 0	# Arbitrary since rate is 0.0
	#
	def setrate(self, rate):
		if rate < 0.0:
			raise RuntimeError, 'setrate with negative rate'
		if self.rate = rate:
			return
		msec = time.millitimer()
		t = (msec - self.msec_origin) / 1000.0
		now = self.origin + t * self.rate
		self.origin = now
		self.msec_origin = msec
		self.rate = rate
		for cname in self.channelnames:
			self.channels[cname].setrate(self.rate)
		self.updatetimer()
	#
	def updatetimer(self):
		now = self.timefunc()
		if self.queue:
			when = self.queue[0][0]
		else:
			when = now + 1.0
		delay = min(when - now, 1.0 - now%1.0)
		if delay <= 0:
			delay = 0.001 # Immediate, but nonzero
		if self.rate = 0.0:
			delay = 0.0 # Infinite
		else:
			delay = delay / self.rate
		self.timerobject.set_timer(delay)
	#
	# This version of run() blocks when there is nothing to do.
	# It never returns!
	# XXX Hence destroying and then re-creating this view doesn't work.
	#
	def run(self):
		self.updatetimer()
		glwindow.mainloop()
	#
	# User interface.
	#
	def makecpanel(self):
		#
		cpanel = fl.make_form(FLAT_BOX, CPWIDTH, CPHEIGHT)
		#
		# The play, pause and stop buttons are inactive buttons
		# (used for display) covered by invisible buttons
		# (used for reactivity).  This seems to be the only way
		# to avoid the default interaction between mouse clicks
		# the button's appearance...
		#
		x, y, w, h = 0, 50, 98, 48
		self.playbutton = \
			cpanel.add_button(INOUT_BUTTON, x,y,w,h, 'Play')
		self.playbutton.set_call_back(self.play_callback, None)
		# self.playbutton.active = 0
		#
		x, y, w, h = 100, 50, 48, 48
		self.pausebutton = \
			cpanel.add_button(INOUT_BUTTON,x,y,w,h, 'Pause')
		self.pausebutton.set_call_back(self.pause_callback, None)
		# self.pausebutton.active = 0
		#
		x, y, w, h = 150, 50, 48, 48
		self.stopbutton = \
			cpanel.add_button(INOUT_BUTTON,x,y,w,h, 'Stop')
		self.stopbutton.set_call_back(self.stop_callback, None)
		#
		x, y, w, h = 200, 50, 48, 48
		self.fastbutton = \
			cpanel.add_button(INOUT_BUTTON,x,y,w,h, 'Faster')
		self.fastbutton.set_call_back(self.fast_callback, None)
		#
		x, y, w, h = 200, 0, 98, 48
		self.abbutton = \
			cpanel.add_button(NORMAL_BUTTON,x,y,w,h, 'A-B')
		self.abbutton.set_call_back(self.ab_callback, None)
		#
		x, y, w, h = 0, 0, 198, 48
		self.statebutton = \
			cpanel.add_button(NORMAL_BUTTON,x,y,w,h, '')
		self.statebutton.boxtype = FLAT_BOX
		self.statebutton.set_call_back(self.state_callback, None)
		#
		x, y, w, h = 250, 50, 48, 48
		self.speedbutton = \
			cpanel.add_button(NORMAL_BUTTON,x,y,w,h, '')
		self.speedbutton.boxtype = FLAT_BOX
		self.speedbutton.set_call_back(self.speed_callback, None)
		#
		self.timerobject = cpanel.add_timer(HIDDEN_TIMER,0,0,0,0, '')
		self.timerobject.set_call_back(self.timer_callback, None)
		#
		self.cpanel = cpanel
	#
	def showcpanel(self):
		#
		# Use the winpos attribute of the root to place the panel
		#
		h, v = MMAttrdefs.getattr(self.root, 'player_winpos')
		width, height = 300, 100
		glwindow.setgeometry(h, v, width, height)
		#
		self.cpanel.show_form(PLACE_SIZE, TRUE, 'Control Panel')
	#
	def hidecpanel(self):
		self.cpanel.hide_form()
	#
	def destroycpanel(self):
		self.hide()
		# XXX Ougt to garbage-collect everything now...
	#
	# FORMS callbacks.
	#
	def play_callback(self, (obj, arg)):
		if obj.pushed:
			self.play()
		self.showstate()
	#
	def pause_callback(self, (obj, arg)):
		if obj.pushed:
			if self.playing and self.rate = 0.0:
				self.play()
			else:
				self.freeze()
		self.showstate()
	#
	def stop_callback(self, (obj, arg)):
		if obj.pushed:
			if not self.playing:
				# Extra heavy duty reset
				self.resettimer()
				self.resetchannels()
				if self.setcurrenttime_callback:
					self.setcurrenttime_callback(0.0)
			else:
				self.stop()
		self.showstate()
	#
	def fast_callback(self, (obj, arg)):
		if obj.pushed:
			self.faster()
		self.showstate()
	#
	def ab_callback(self, (obj, arg)):
		if self.abcontrol:
			text = `self.abcontrol`
			if text[:1] = '(' and text[-1:] = ')':
				text = text[1:-1]
		else:
			text = ''
		text = fl.show_input('New (A,B) times:', text)
		if not text:
			self.abcontrol = ()
		else:
			try:
				ab = eval(text)
				if ab = ():
					self.abcontrol = ()
				else:
					# Do a little type checking...
					a, b = ab
					a = a + 0.0
					b = b + 0.0
					self.abcontrol = a, b
			except:
				import gl
				gl.ringbell()
	#
	def state_callback(self, (obj, arg)):
		self.showstate()
	#
	def speed_callback(self, (obj, arg)):
		self.showstate()
	#
	def timer_callback(self, (obj, arg)):
		while self.queue:
			when, prio, action, argument = self.queue[0]
			now = self.timefunc()
			delay = when - now
			if delay > 0.0:
				break
			del self.queue[0]
			void = action(argument)
		self.updatetimer()
		self.showtime()
	#
	# State transitions.
	#
	def play(self):
		if not self.playing:
			if not self.maystart():
				self.showstate()
				return
			self.start_playing()
		self.setrate(1.0)
	#
	def freeze(self):
		if not self.playing:
			if not self.maystart():
				self.showstate()
				return
			self.start_playing()
		self.setrate(0.0)
	#
	def stop(self):
		if self.playing:
			self.stop_playing()
			self.showstate()
	#
	def faster(self):
		if not self.playing:
			if not self.maystart():
				self.showstate()
				return
			self.start_playing()
		if self.rate = 0.0:
			self.setrate(2.0)
		else:
			self.setrate(self.rate * 2.0)
	#
	def maystart(self):
		return 1
	#
	def showstate(self):
		if not self.playing:
			self.playbutton.set_button(0)
			self.pausebutton.set_button(0)
			self.fastbutton.set_button(0)
		else:
			self.playbutton.set_button(0.0 < self.rate <= 1.0)
			self.pausebutton.set_button(0.0 = self.rate)
			self.fastbutton.set_button(1.0 < self.rate)
		self.showtime()
	#
	def showtime(self):
		now = int(self.timefunc())
		label = 'T = ' + `now`
		if self.statebutton.label <> label:
			self.statebutton.label = label
		#
		rate = self.rate
		if int(rate) = rate: rate = int(rate)
		label = `rate`
		if self.speedbutton.label <> label:
			self.speedbutton.label = label
	#
	# Channels.
	#
	def makechannels(self):
		#
		for name in self.root.context.channelnames:
			attrdict = self.root.context.channeldict[name]
			self.channelnames.append(name)
			self.channels[name] = self.newchannel(name, attrdict)
	#
	def showchannels(self):
		for name in self.channelnames:
			self.channels[name].show()
	#
	def hidechannels(self):
		for name in self.channelnames:
			self.channels[name].hide()
	#
	def destroychannels(self):
		for name in self.channelnames:
			self.channels[name].destroy()
	#
	def newchannel(self, (name, attrdict)):
		if not attrdict.has_key('type'):
			raise TypeError, \
				'channel ' +`name`+ ' has no type attribute'
		type = attrdict['type']
		if not channelmap.has_key(type):
			raise TypeError, \
				'channel ' +`name`+ ' has bad type ' +`type`
		chclass = channelmap[type]
		ch = chclass().init(name, attrdict, self)
		return ch
	#
	def resetchannels(self):
		for cname in self.channelnames:
			self.channels[cname].reset()
	#
	def stopchannels(self):
		for cname in self.channelnames:
			self.channels[cname].stop()
	#
	# Playing algorithm.
	#
	def start_playing(self):
		self.resettimer()
		self.resetchannels()
		Timing.calctimes(self.root)
		Timing.prepare(self.root)
		self.root.counter[HD] = 1
		self.decrement(0, self.root, HD)
		self.playing = 1
	#
	def stop_playing(self):
		self.setrate(0.0) # Stop the clock
		self.stopchannels() # Tell the channels to quit it
		self.queue[:] = [] # Erase all events with brute force!
		self.updatetimer()
		Timing.cleanup(self.root) # Collect some garbage
		self.playing = 0
	#
	def decrement(self, (delay, node, side)):
		if self.abcontrol:
			a, b = self.abcontrol
			doit = (a <= node.t0 <= b)
		else:
			doit = 1
		if delay > 0 and doit: # Sync arc contains delay
			id = self.enter(delay, 0, self.decrement, \
						(0, node, side))
			return
		x = node.counter[side] - 1
		node.counter[side] = x
		if x > 0:
			return # Wait for other sync arcs
		if x < 0:
			raise RuntimeError, 'counter below zero!?!?'
		if node.GetType() not in ('seq', 'par'):
			if side = HD:
				if doit:
					chan = self.getchannel(node)
					chan.play(node, self.decrement, \
						  (0, node, TL))
					if self.setcurrenttime_callback:
						self.setcurrenttime_callback \
								(node.t0)
				else:
					dummy = self.enter(0.0, 0, \
						self.decrement, (0, node, TL))
		for arg in node.deps[side]:
			self.decrement(arg)
		if node.GetParent() = None and side = TL:
			# The whole tree is finished -- stop playing.
			if self.setcurrenttime_callback:
				self.setcurrenttime_callback(node.t1)
			self.stop()
	#
	# Channel access utilities.
	#
	def getchannel(self, node):
		cname = MMAttrdefs.getattr(node, 'channel')
		return self.channels[cname] # What? no channel on this node?
	#
