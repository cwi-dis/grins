# Player module -- mostly defines the Player class.


import time
import gl
import fl
from FL import *
from sched import scheduler
import glwindow
from MMExc import *
import MMAttrdefs
from Dialog import BasicDialog
from ViewDialog import ViewDialog
import Timing
from MMNode import alltypes, leaftypes, interiortypes


# The player algorithm treats the head and tail (begin and end) sides
# of a node as separate events in time; there are separate counters
# and lists of dependencies, indexed by the symbolic constants
# HD and TL: e.g., node.counter[HD], node.deps[HD].
# This is also used in module Timing!

HD, TL = 0, 1


# Nominal Control Panel dimensions

CPWIDTH = 300
CPHEIGHT = 100


# The channel map is in a separate module for easy editing.

from ChannelMap import channelmap


# The Player class normally has only a single instance.
#
# It implements a queue using "virtual time" using an invisible timer
# object in its form.

class Player(ViewDialog, scheduler, BasicDialog):
	#
	# Initialization.
	#
	def init(self, toplevel):
		self = ViewDialog.init(self, 'player_')
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.playroot = self.root
		self.queue = []
		self.resettimer()
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.editmgr.register(self)
		self.setcurrenttime_callback = None
		self.playing = self.locked = 0
		self.channelnames = []
		self.channels = {}
		self.channeltypes = {}
		return BasicDialog.init(self, (0, 0, 'Player'))
	#
	# EditMgr interface (as dependent client).
	#
	def transaction(self):
		# Disallow changes while we are playing.
		if self.playing:
			m1 = 'You can\'t do that right now'
			m3 = 'The document is still playing!'
			fl.show_message(m1, '--', m3)
			return 0
		self.locked = 1
		return 1
	#
	def commit(self):
		if self.showing:
			self.checkchannels()
			if self.playroot.GetRoot() <> self.root:
				self.playroot = self.root
		self.locked = 0
		self.showstate()
	#
	def rollback(self):
		# Nothing has changed after all.
		self.locked = 0
	#
	# Extend BasicDialog show/hide/destroy methods.
	#
	def show(self):
		if self.showing: return
		self.abcontrol = ()
		self.makechannels()
		self.fullreset()
		BasicDialog.show(self)
		self.toplevel.checkviews()
		self.showchannels()
		self.showstate()
	#
	def hide(self):
		if not self.showing: return
		self.stop()
		self.fullreset()
		BasicDialog.hide(self)
		self.toplevel.checkviews()
		self.destroychannels()
	#
	def save_geometry(self):
		ViewDialog.save_geometry(self)
		for name in self.channelnames:
			self.channels[name].save_geometry()
	#
	def set_setcurrenttime_callback(self, setcurrenttime):
		self.setcurrenttime_callback = setcurrenttime
	#
	# Internal reset.
	#
	def fullreset(self):
		self.reset()
		self.playroot = self.root
	#
	def reset(self):
		self.resettimer()
		self.resetchannels()
		if self.setcurrenttime_callback:
			self.setcurrenttime_callback(0.0)
	#
	# Queue interface, based upon sched.scheduler.
	# This queue has variable time, to implement pause and slow/fast,
	# but the interface to its callers is the same, except init()
	# and run() -- the queue runs automatically as long as our
	# form is being checked.
	#
	# Inherit enter(), cancel(), empty() from scheduler.
	# Override enterabs() since it must update the timer object.
	# The timefunc is implemented differently (it's a real method),
	# but the call to it from enter() doesn't mind.
	# There is no delayfunc() since we don't have a run() function.
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
			raise CheckError, 'setrate with negative rate'
		if self.rate == rate:
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
		if self.rate == 0.0:
			delay = 0.0 # Infinite
		else:
			delay = delay / self.rate
		self.timerobject.set_timer(delay)
	#
	# User interface.
	#
	def make_form(self):
		#
		self.form = form = fl.make_form(FLAT_BOX, CPWIDTH, CPHEIGHT)
		#
		# The play, pause and stop buttons are inactive buttons
		# (used for display) covered by invisible buttons
		# (used for reactivity).  This seems to be the only way
		# to avoid the default interaction between mouse clicks
		# the button's appearance...
		#
		x, y, w, h = 0, 50, 98, 48
		self.playbutton = \
			form.add_button(INOUT_BUTTON, x,y,w,h, 'Play')
		self.playbutton.set_call_back(self.play_callback, None)
		#
		x, y, w, h = 100, 50, 48, 48
		self.pausebutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Pause')
		self.pausebutton.set_call_back(self.pause_callback, None)
		#
		x, y, w, h = 150, 50, 48, 48
		self.stopbutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Stop')
		self.stopbutton.set_call_back(self.stop_callback, None)
		#
		x, y, w, h = 200, 50, 48, 48
		self.fastbutton = \
			form.add_button(INOUT_BUTTON,x,y,w,h, 'Faster')
		self.fastbutton.set_call_back(self.fast_callback, None)
		#
		x, y, w, h = 200, 0, 48, 48
		self.abbutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'A-B\nplay')
		self.abbutton.set_call_back(self.ab_callback, None)
		#
		x, y, w, h = 250, 0, 48, 48
		self.menubutton = \
			form.add_menu(PUSH_MENU,x,y,w,h, 'Menu')
		self.menubutton.set_call_back(self.menu_callback, None)
		#
		x, y, w, h = 100, 0, 98, 48
		self.statebutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, 'T = 0')
		self.statebutton.boxtype = FLAT_BOX
		self.statebutton.set_call_back(self.state_callback, None)
		#
		x, y, w, h = 0, 0, 98, 48
		self.partbutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, '')
		self.partbutton.boxtype = FLAT_BOX
		self.partbutton.set_call_back(self.part_callback, None)
		#
		x, y, w, h = 250, 50, 48, 48
		self.speedbutton = \
			form.add_button(NORMAL_BUTTON,x,y,w,h, '0')
		self.speedbutton.boxtype = FLAT_BOX
		self.speedbutton.set_call_back(self.speed_callback, None)
		#
		self.timerobject = form.add_timer(HIDDEN_TIMER,0,0,0,0, '')
		self.timerobject.set_call_back(self.timer_callback, None)
	#
	# FORMS callbacks.
	#
	def play_callback(self, (obj, arg)):
		if obj.pushed:
			self.play()
		else:
			self.showstate() # Undo unwanted change by FORMS
	#
	def pause_callback(self, (obj, arg)):
		if obj.pushed:
			if self.playing and self.rate == 0.0:
				self.play()
			else:
				self.pause()
		else:
			self.showstate() # Undo unwanted change by FORMS
	#
	def stop_callback(self, (obj, arg)):
		if obj.pushed:
			if not self.playing:
				self.fullreset()
				self.showstate()
			else:
				self.stop()
		else:
			self.showstate() # Undo unwanted change by FORMS
	#
	def fast_callback(self, (obj, arg)):
		if obj.pushed:
			self.faster()
		else:
			self.showstate() # Undo unwanted change by FORMS
	#
	def ab_callback(self, (obj, arg)):
		if self.abcontrol:
			text = `self.abcontrol`
			if text[:1] == '(' and text[-1:] == ')':
				text = text[1:-1]
		else:
			text = ''
		text = fl.show_input('New (A,B) times:', text)
		if not text:
			self.abcontrol = ()
		else:
			try:
				ab = eval(text)
				if ab == ():
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
	def menu_callback(self, (obj, arg)):
		i = self.menubutton.get_menu() - 1
		if 0 <= i < len(self.channelnames):
			name = self.channelnames[i]
			if self.channels[name].is_showing():
				self.channels[name].hide()
			else:
				self.channels[name].show()
			self.makemenu()
	#
	def state_callback(self, (obj, arg)):
		# This is a button disguised as a button.
		# The callback needn't do anything, but since it
		# has to exist anyway, why not let it update the state...
		self.showstate()
	#
	def part_callback(self, (obj, arg)):
		# This is a button disguised as a button.
		# The callback needn't do anything, but since it
		# has to exist anyway, why not let it update the state...
		self.showstate()
	#
	def speed_callback(self, (obj, arg)):
		# Same comments as for state_callback() above
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
			if not self.start_playing(1.0):
				return
		else:
			self.setrate(1.0)
			self.showstate()
	#
	def playsubtree(self, node):
		if not self.showing:
			self.show()
		if self.playing:
			self.stop()
		if node.GetRoot() <> self.root:
			raise CheckError, 'playsubtree with bad arg'
		self.playroot = node
		self.play()
	#
	def pause(self):
		if not self.playing:
			if not self.start_playing(0.0):
				return
		else:
			self.setrate(0.0)
			self.showstate()
	#
	def stop(self):
		if self.playing:
			self.stop_playing()
			self.showstate()
	#
	def faster(self):
		if not self.playing:
			if not self.start_playing(2.0):
				return
		else:
			if self.rate == 0.0:
				self.setrate(2.0)
			else:
				self.setrate(self.rate * 2.0)
			self.showstate()
	#
	def maystart(self):
		return not self.locked
	#
	def showstate(self):
		if not self.playing:
			self.playbutton.set_button(0)
			self.pausebutton.set_button(0)
			self.fastbutton.set_button(0)
		else:
			self.playbutton.set_button(0.0 < self.rate <= 1.0)
			self.pausebutton.set_button(0.0 == self.rate)
			self.fastbutton.set_button(1.0 < self.rate)
		if self.playroot is self.root:
			self.partbutton.label = ''
		else:
			name = MMAttrdefs.getattr(self.playroot, 'name')
			if name == 'none':
				label = 'part play'
			else:
				label = 'part play:\n' + name
			self.partbutton.label = label
		self.showtime()
	#
	def showtime(self):
		now = int(self.timefunc())
		label = 'T = ' + `now`
		if self.statebutton.label <> label:
			self.statebutton.label = label
		#
		rate = self.rate
		if int(rate) == rate: rate = int(rate)
		label = `rate`
		if self.speedbutton.label <> label:
			self.speedbutton.label = label
	#
	# Channels.
	#
	def makechannels(self):
		for name in self.context.channelnames:
			attrdict = self.context.channeldict[name]
			self.newchannel(name, attrdict)
			self.channelnames.append(name)
		self.makemenu()
	#
	def checkchannels(self):
		# XXX Ought to detect renamed channels...
		# (1) Delete channels that have disappeared
		# or whose type has changed
		for name in self.channelnames[:]:
			if name not in self.context.channelnames:
				self.killchannel(name)
			else:
				oldtype = self.channeltypes[name]
				newtype = \
				    self.context.channeldict[name]['type']
				if oldtype <> newtype:
					self.killchannel(name)
		# (2) Add new channels that have appeared
		for name in self.context.channelnames:
			if name not in self.channelnames:
				attrdict = self.context.channeldict[name]
				self.newchannel(name, attrdict)
				i = self.context.channelnames.index(name)
				self.channelnames.insert(i, name)
				self.channels[name].show()
		self.makemenu()
	#
	def makemenu(self):
		self.menubutton.set_menu('')
		for name in self.channelnames:
			if self.channels[name].is_showing():
				onoff = ''
			else:
				onoff = '(off)'
			self.menubutton.addto_menu(name + ' ' + onoff + '|')
	#
	def showchannels(self):
		for name in self.channelnames:
			self.channels[name].show()
		self.makemenu()
	#
	def hidechannels(self):
		for name in self.channelnames:
			self.channels[name].hide()
		self.makemenu()
	#
	def destroychannels(self):
		for name in self.channelnames[:]:
			self.killchannel(name)
		self.makemenu()
	#
	def killchannel(self, name):
		self.channels[name].destroy()
		self.channelnames.remove(name)
		del self.channels[name]
		del self.channeltypes[name]
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
		self.channels[name] = ch
		self.channeltypes[name] = type
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
	def start_playing(self, rate):
		if not self.maystart():
			return 0
		self.playing = 1
		self.reset()
		self.setrate(rate)
		if self.playroot.GetRoot() <> self.root:
			self.playroot = self.root # In case it's been deleted
		self.showstate() # Give the anxious user a clue...
		Timing.prepare(self.playroot)
		self.playroot.counter[HD] = 1
		self.decrement(0, self.playroot, HD)
		return 1
	#
	def stop_playing(self):
		self.playing = 0
		self.stopchannels() # Tell the channels to quit it
		self.queue[:] = [] # Erase all events with brute force!
		self.setrate(0.0) # Stop the clock
		self.showstate()
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
			raise CheckError, 'counter below zero!?!?'
		if node.GetType() not in interiortypes:
			if side == HD:
				if doit:
					chan = self.getchannel(node)
					if chan == None:
						print 'Play node w/o channel'
						doit = 0
				if doit:
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
		if node == self.playroot and side == TL:
			# The whole tree is finished -- stop playing.
			if self.setcurrenttime_callback:
				self.setcurrenttime_callback(node.t1)
			self.stop()
	#
	# Channel access utilities.
	#
	def getchannel(self, node):
		cname = MMAttrdefs.getattr(node, 'channel')
		if self.channels.has_key(cname):
			return self.channels[cname]
		else:
			return None
	#
