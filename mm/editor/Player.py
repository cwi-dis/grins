# Player module -- mostly defines the Player class.


import time
import gl
import fl
from FL import *
from sched import scheduler
import glwindow
from MMExc import *
import MMAttrdefs


# The player algorithm treats the head and tail (begin and end) sides
# of a node as separate events in time; there are separate counters
# and lists of dependencies, indexed by the symbolic constants
# HD and TL: e.g., node.counter[HD], node.deps[HD].

HD, TL = 0, 1


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
# To add multiple players, the loop in run(), calling glwindow.check(),
# must be moved to a central place, which implements a real-time queue.
# Player objects must calculate the expected real-time delay to their
# next event and post an event in the RT queue for that time.
# When the expected time changes (e.g., pause is pressed), they should
# cancel the original event and post a new one.  Etc.

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
		self.state = 'stopped'
		# Make the channel objects -- this pops up windows...
		self.channels = {}
		self.channelnames = []
		self.makechannels()
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
	#
	# Queue interface, based upon sched.scheduler.
	# This queue has variable time, to implement pause and slow/fast,
	# but the interface to its callers is the same, except init().
	#
	# Inherit enterabs(), enter(), cancel(), empty() from scheduler.
	# The timefunc is implemented differently (it's a real method),
	# but the call to it from enter() doesn't mind.
	# There is no delayfunc -- our run() doesn't use that.
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
			raise RuntimeError, 'Queue.setrate with negative rate'
		msec = time.millitimer()
		t = (msec - self.msec_origin) / 1000.0
		now = self.origin + t * self.rate
		self.origin = now
		self.msec_origin = msec
		self.rate = rate
		for cname in self.channelnames:
			self.channels[cname].setrate(self.rate)
	#
	# This version of run() busy-waits when there is nothing to do.
	# XXX Eventually we should use FORMS timer objects instead.
	#
	def run(self):
		while 1:
			obj = glwindow.check()
			if obj <> None:
				raise RuntimeError, 'object without callback!'
			idle = 1
			if self.queue:
				when, prio, action, argument = self.queue[0]
				now = self.timefunc()
				if now >= when:
					del self.queue[0]
					void = action(argument)
					idle = 0
			if idle:
				self.showtime()
				time.millisleep(50)
	#
	# User interface.
	#
	def makecpanel(self):
		#
		cpanel = fl.make_form(FLAT_BOX, 300, 100)
		#
		# The play, pause and stop buttons are inactive buttons
		# (used for display) covered by invisible buttons
		# (used for reactivity).  This seems to be the only way
		# to avoid the default interaction between mouse clicks
		# the button's appearance...
		#
		x, y, w, h = 0, 50, 100, 50
		self.playbutton = \
			cpanel.add_button(INOUT_BUTTON, x,y,w,h, 'Play')
		self.playbutton.set_call_back(self.play_callback, None)
		# self.playbutton.active = 0
		#
		x, y, w, h = 100, 50, 50, 50
		self.pausebutton = \
			cpanel.add_button(INOUT_BUTTON,x,y,w,h, 'Pause')
		self.pausebutton.set_call_back(self.pause_callback, None)
		# self.pausebutton.active = 0
		#
		x, y, w, h = 150, 50, 50, 50
		self.stopbutton = \
			cpanel.add_button(INOUT_BUTTON,x,y,w,h, 'Stop')
		self.stopbutton.set_call_back(self.stop_callback, None)
		#
		x, y, w, h = 50, 0, 150, 50
		self.statebutton = \
			cpanel.add_button(NORMAL_BUTTON,x,y,w,h, '')
		self.statebutton.boxtype = FLAT_BOX
		self.statebutton.set_call_back(self.state_callback, None)
		#
		x, y, w, h = 200, 50, 50, 50
		self.fastbutton = \
			cpanel.add_button(INOUT_BUTTON,x,y,w,h, 'Faster')
		self.fastbutton.set_call_back(self.fast_callback, None)
		#
		x, y, w, h = 250, 50, 50, 50
		self.speedbutton = \
			cpanel.add_button(NORMAL_BUTTON,x,y,w,h, '')
		self.speedbutton.boxtype = FLAT_BOX
		self.speedbutton.set_call_back(self.speed_callback, None)
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
		self.play()
	#
	def pause_callback(self, (obj, arg)):
		if not obj.pushed:
			self.showstate()
		else:
			if self.state = 'frozen':
				self.play()
			else:
				self.freeze()
	#
	def stop_callback(self, (obj, arg)):
		if self.state = 'stopped' and obj.pushed:
			# Perform some extra resetting
			self.resettimer()
			self.resetchannels()
		else:
			self.stop()
	#
	def state_callback(self, (obj, arg)):
		self.showtime()
	#
	def fast_callback(self, (obj, arg)):
		if obj.pushed:
			self.faster()
	#
	def speed_callback(self, (obj, arg)):
		self.showtime()
	#
	# State transitions.
	# There are three states: 'stopped', 'frozen' and 'playing'.
	# (The word 'frozen' is used instead of 'paused' since the pause
	# button toggles between 'frozen' and 'playing').
	# The difference between 'frozen' and 'playing' state is really
	# only the rate (0.0 vs. 1.0).  'stopped' is very different
	# because the playing process is not active, and the tree may
	# be edited.  A variant on playing state, fast forward, is not
	# represented as a separate state -- the rate is simply larger.
	# (XXX maybe pause should also not be represented as a state.)
	#
	def play(self):
		if self.state = 'playing':
			pass
		elif self.state = 'frozen':
			pass
		elif self.state = 'stopped':
			if not self.maystart():
				self.showstate()
				return
			self.start_playing()
		else:
			raise CheckError, 'play in state ' + `self.state`
		self.setrate(1.0)
		self.setstate('playing')
	#
	def freeze(self):
		if self.state = 'playing':
			pass
		elif self.state = 'frozen':
			pass
		elif self.state = 'stopped':
			if not self.maystart():
				self.showstate()
				return
			self.start_playing()
		else:
			raise CheckError, 'freeze in state ' + `self.state`
		self.setrate(0.0)
		self.setstate('frozen')
	#
	def stop(self):
		if self.state = 'playing':
			self.stop_playing()
		elif self.state = 'frozen':
			self.stop_playing()
		elif self.state = 'stopped':
			pass
		else:
			raise CheckError, 'stop in state ' + `self.state`
		self.setrate(0.0)
		self.setstate('stopped')
	#
	def faster(self):
		if self.state = 'playing':
			pass
		elif self.state = 'frozen':
			self.setrate(1.0)
		elif self.state = 'stopped':
			if not self.maystart():
				self.showstate()
				return
			self.start_playing()
			self.setrate(1.0)
		else:
			raise CheckError, 'fast in state ' + `self.state`
		self.setrate(self.rate * 2.0)
		self.setstate('playing')
	#
	def maystart(self):
		return 1
	#
	def setstate(self, state):
		self.state = state
		self.showstate()
	#
	def showstate(self):
		self.playbutton.set_button(self.state = 'playing')
		self.pausebutton.set_button(self.state = 'frozen')
		self.fastbutton.set_button( \
			self.state = 'playing' and self.rate > 1.0)
		self.showtime()
	#
	def showtime(self):
		now = int(self.timefunc() * 10) * 0.1
		label = 'T = ' + `now`
		if self.statebutton.label <> label:
			self.statebutton.label = label
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
	# Playing algorithm.
	#
	def start_playing(self):
		self.resettimer()
		self.resetchannels()
		self.prep1(self.root)
		self.prep2(self.root)
		if self.root.counter[HD] <> 0:
			raise RuntimeError, 'head of root has dependencies!?!'
		self.root.counter[HD] = 1
		self.decrement(0, self.root, HD)
	#
	def stop_playing(self):
		self.queue[:] = [] # Erase all events with brute force!
		self.cleanup(self.root)
	#
	def cleanup(self, node):
		# XXX (doesn't need to be a method)
		del node.counter
		del node.deps
		type = node.GetType()
		if type in ('seq', 'par'):
			for c in node.GetChildren():
				self.cleanup(c)
	#
	def prep1(self, node):
		node.counter = [0, 0]
		node.deps = [], []
		type = node.GetType()
		if type = 'seq':
			xnode, xside = node, HD
			for c in node.GetChildren():
				self.prep1(c)
				self.adddep(xnode, xside, 0, c, HD)
				xnode, xside = c, TL
			self.adddep(xnode, xside, 0, node, TL)
		elif type = 'par':
			for c in node.GetChildren():
				self.prep1(c)
				self.adddep(node, HD, 0, c, HD)
				self.adddep(c, TL, 0, node, TL)
		else:
			# Special case -- delay -1 means execute leaf node
			# of leaf node when playing
			self.adddep(node, HD, -1, node, TL)
	#
	def prep2(self, node):
		arcs = MMAttrdefs.getattr(node, 'synctolist')
		for arc in arcs:
			print 'sync arc:', arc, 'to:', node.GetUID()
			xuid, xside, delay, yside = arc
			xnode = node.MapUID(xuid)
			self.adddep(xnode, xside, delay, node, yside)
		#
		if node.GetType() in ('seq', 'par'):
			for c in node.GetChildren(): self.prep2(c)
	#
	def adddep(self, (xnode, xside, delay, ynode, yside)):
		# XXX (doesn't need to be a method)
		ynode.counter[yside] = ynode.counter[yside] + 1
		if delay >= 0:
			xnode.deps[xside].append(delay, ynode, yside)
	#
	def decrement(self, (delay, node, side)):
		if delay > 0:
			id = self.enter(delay, 0, self.decrement, \
						(0, node, side))
			return
		x = node.counter[side] - 1
		node.counter[side] = x
		if x > 0:
			return
		if x < 0:
			raise RuntimeError, 'counter below zero!?!?'
		if node.GetType() not in ('seq', 'par'):
			if side = HD:
				chan = self.getchannel(node)
				chan.play(node, self.decrement, (0, node, TL))
		for arg in node.deps[side]:
			self.decrement(arg)
		if node.GetParent() = None and side = TL:
			# The whole tree is finished -- stop playing.
			self.stop()
	#
	# Channel access utilities.
	#
	def getduration(self, node):
		chan = self.getchannel(node)
		return chan.getduration(node)
	#
	def getchannel(self, node):
		cname = MMAttrdefs.getattr(node, 'channel')
		return self.channels[cname] # What? no channel on this node?
	#
