# Player module -- mostly defines the Player class.


import time
import gl
import fl
from FL import *
import flp
from sched import scheduler
import glwindow
from MMExc import *
import MMAttrdefs
from Dialog import BasicDialog
from ViewDialog import ViewDialog
import Timing
import rtpool
from MMNode import alltypes, leaftypes, interiortypes
from ArmStates import *


# The player algorithm treats the head and tail (begin and end) sides
# of a node as separate events in time; there are separate counters
# and lists of dependencies, indexed by the symbolic constants
# HD and TL: e.g., node.counter[HD], node.deps[HD].
# This is also used in module Timing!

HD, TL = 0, 1


# Nominal Control Panel dimensions

CPWIDTH = 300
CPHEIGHT = 100


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
		self.rtpool = rtpool.rtpool().init()
		self.resettimer()
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.editmgr.register(self)
		self.setcurrenttime_callback = None
		self.playing = self.locked = 0
		self.channelnames = []
		self.channels = {}
		self.channeltypes = {}
		self.timing_changed = 0
		self.ff = 0
		self.seeking = 0
		self.seek_node = None
		return BasicDialog.init(self, 0, 0, 'Player')
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

	def kill(self):
		self.destroy()
	#
	# Extend BasicDialog show/hide/destroy methods.
	#
	def show(self):
		if self.showing: return
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
		self.oldrate = 1.0
		self.timing_changed = 0
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
	        if self.frozen: return self.frozen_value
		t = (time.millitimer() - self.msec_origin) / 1000.0
		now = self.origin + t * self.rate
		return now
	#
	def resettimer(self):
		self.origin = 0.0	# Current time
		self.rate = 0.0		# Initially the clock is frozen
		self.oldrate = 0.0
		self.msec_origin = 0	# Arbitrary since rate is 0.0
		self.frozen = 0
		self.frozen_value = 0
		self.latecount = 0.0
	#
	def skiptimer(self, amount):
		self.origin = self.origin + amount
	#
	def freeze(self):
	        if not self.frozen:
		    self.frozen_value = self.timefunc()
		self.frozen = self.frozen + 1
	def unfreeze(self):
	        self.frozen = self.frozen - 1
		if self.frozen <= 0:
		    if self.frozen < 0:
			print 'Player: self.frozen < 0!'
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
		delay = when - now
		if (self.ff or self.seeking) and delay > 0:
			self.skiptimer(delay)
			self.timerobject.set_timer(0.001)
			print 'Updatetimer: skipped ', delay
			return
		delay = min(delay, 1.0 - now%1.0)
		if delay <= 0:
			delay = 0.001 # Immediate, but nonzero
		if self.rate == 0.0:
			delay = 0.0 # Infinite
		else:
			delay = delay / self.rate
		if not self.rtpool.empty():
			# See if we should react immedeately because of
			# realtime event
			rtime = self.rtpool.shortest()
			if delay == 0.0 or rtime < delay:
				delay = 0.001
		print 'Next timer: ', delay
		self.timerobject.set_timer(delay)
	#
	# User interface.
	#
	def make_form(self):
		ftemplate = flp.parse_form('PlayerForm', 'form')
		flp.create_full_form(self, ftemplate)
		self.speedbutton.set_counter_value(1)
		self.speedbutton.set_counter_bounds(1,128)
		self.speedbutton.set_counter_step(1,1)
		
	#
	# FORMS callbacks.
	#
	def play_callback(self, (obj, arg)):
		self.play()

	#
	def pause_callback(self, (obj, arg)):
		self.pause()

	#
	def stop_callback(self, (obj, arg)):
		self.stop()

	#
	def speed_callback(self, (obj, arg)):
		self.oldrate = obj.get_counter_value()
		if self.playing:
			self.setrate(self.oldrate)
		self.showstate()
	#
	def menu_callback(self, (obj, arg)):
		i = self.menubutton.get_menu() - 1
		if 0 <= i < len(self.channelnames):
			name = self.channelnames[i]
			#if self.channels[name].is_showing():
			#	self.channels[name].hide()
			#else:
			#	self.channels[name].show()
			self.channels[name].flip_visible()
			self.makemenu()
	#
	def deltiming_callback(self, (obj, arg)):
		del_timing(self.playroot)
		Timing.calctimes(self.playroot)
		obj.set_button(0)
	#
	def ff_callback(self, (obj, arg)):
		#print self.queue # DBG
		if not self.playing:
			obj.set_button(not obj.get_button())
			return
		self.ff = obj.get_button()
		self.updatetimer()
	#
	def dummy_callback(self, dummy):
		pass
	#
	def timer_callback(self, (obj, arg)):
	        gap = None
		while self.queue:
			when, prio, action, argument = self.queue[0]
			now = self.timefunc()
			delay = when - now
			if delay < -0.1:
			    self.late_ind.lcol, self.late_ind.col2 = \
				      self.late_ind.col2, self.late_ind.lcol
			    self.latecount = self.latecount - delay
			    self.late_ind.label = `int(self.latecount)`
			else:
			    self.late_ind.lcol, self.late_ind.col2 = \
				      self.late_ind.col2, self.late_ind.lcol
			if delay > 0.0:
				break
			del self.queue[0]
			void = action(argument)
		if not self.queue and self.rate > 0.0:
			print 'Huh? Nothing in the queue?'
		if not self.queue or self.rate == 0.0:
			delay = 10000.0		# Infinite
			now = self.timefunc()
		rtevent = self.rtpool.bestfit(now, delay)
		if rtevent:
			dummy, dummy2, action, argument = rtevent
			dummy = action(argument)
		self.updatetimer()
		self.showtime()
	#
	# State transitions.
	#
	def play(self):
		self.ff = 0
		self.seeking = 0
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
		self.ff = 0
		self.seeking = 0
		if self.playing:
			if self.rate == 0.0:	# Paused, continue
				self.setrate(self.oldrate)
			else:
				self.oldrate = self.rate
				self.setrate(0.0)
		else:
			self.start_playing(0.0)
		self.showstate()
	#
	def stop(self):
		self.ff = 0
		self.seeking = 0
		if self.playing:
			self.stop_playing()
		else:
			self.fullreset()
		self.showstate()
	#
	#
	def maystart(self):
		return not self.locked
	#
	def showstate(self):
		self.ffbutton.set_button(self.ff)
		if not self.playing:
			self.playbutton.set_button(0)
			self.pausebutton.set_button(0)
			self.stopbutton.set_button(1)
			self.speedbutton.set_counter_value(self.oldrate)
		else:
			self.stopbutton.set_button(0)
			self.playbutton.set_button(self.rate >= 1.0)
			self.pausebutton.set_button(0.0 == self.rate)
			self.speedbutton.set_counter_value(self.oldrate)
		if self.playroot is self.root:
			self.partbutton.label = ''
		else:
			name = MMAttrdefs.getattr(self.playroot, 'name')
			if name == 'none':
				label = 'part play'
			else:
				label = 'part play: ' + name
			self.partbutton.label = label
		if self.timing_changed:
			self.savelabel.lcol = self.savelabel.col2
		else:
			self.savelabel.lcol = self.savelabel.col1
		self.showtime()
	#
	def showtime(self):
		if self.msec_origin == 0:
			self.statebutton.label = '--:--'
			return
		now = int(self.timefunc())
		label = `now/60` + ':' + `now/10%6` + `now % 10`
		if self.statebutton.label <> label:
			self.statebutton.label = label
		#
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
		# (3) Update visibility of all channels
		for name in self.channelnames:
			self.channels[name].check_visible()
		# (4) Update menu
		self.makemenu()
	#
	def makemenu(self):
		self.menubutton.set_menu('')
		for name in self.channelnames:
			if self.channels[name].is_showing():
				onoff = ''
			else:
				onoff = ' (off)'
			self.menubutton.addto_menu(name + onoff)
			# XXX This is for FORMS version 2.0b;
			# XXX for version 2.0 (beta), append a '|'.
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
		from ChannelMap import channelmap
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
		arm_events = self.resume_1_playing(rate)
		for pn in arm_events:
			d = pn.GetRawAttr('arm_duration')
			c = self.getchannel(pn)
			self.setarmedmode(pn, ARM_SCHEDULED)
			pn.prearm_event = self.rtpool.enter(pn.t0, d, \
				  c.arm_only, pn)
		self.resume_2_playing()
		return 1
	#
	def resume_1_playing(self,rate):
		for cname in self.channelnames:
			self.channels[cname].playerseek_lastnode = None
		MMAttrdefs.startstats()
		self.playing = 1
		self.reset()
		self.setrate(rate)
		if self.playroot.GetRoot() <> self.root:
			self.playroot = self.root # In case it's been deleted
		self.showstate() # Give the anxious user a clue...
		Timing.optcalctimes(self.playroot)
		arm_events = Timing.getinitial(self.playroot)
		return arm_events
	def resume_2_playing(self):
		Timing.prepare(self.playroot)
		d = int(self.playroot.t1 - self.playroot.t0)
		label = `d/60` + ':' + `d/10%6` + `d % 10`
		self.duration_ind.label = label
		self.playroot.counter[HD] = 1
		self.decrement(0, self.playroot, HD)
	#
	def suspend_playing(self):
		self.stopchannels() # Tell the channels to quit it
		self.queue[:] = [] # Erase all events with brute force!
		# print 'Flush rtpool'
		self.rtpool.flush()
		self.setrate(0.0) # Stop the clock
		self.showstate()
		# print 'unarm chview'
		chv = self.toplevel.channelview
		chv.unarm_all()
	def stop_playing(self):
		self.playing = 0
		self.suspend_playing()
		if self.timing_changed:
			Timing.calctimes(self.playroot)
			Timing.optcalctimes(self.playroot)
		a = MMAttrdefs.stopstats()
		MMAttrdefs.showstats(a)
	#
	def seek_done(self):
		skipchannel = self.getchannel(self.seek_node)
		for cname in self.channelnames:
		    ch = self.channels[cname]
		    if ch == skipchannel: continue
		    node = ch.playerseek_lastnode
		    if node:
			dummy = self.enter(0.0, -1, \
				  ch.arm_and_measure, node)
			self.setarmedmode(node, ARM_PLAYING)
			dummy = self.enter(0.0, 0, ch.play, \
				  (node, self.decrement, (0, node, TL)))
			if self.setcurrenttime_callback:
				self.setcurrenttime_callback(node.t0)
		self.seeking = 0
		self.seek_node = None
	def dummy(arg):
		pass
	def decrement(self, (delay, node, side)):
		# print 'DEC', delay, node, side, ' of ', node.counter[side]
	        self.freeze()
		if delay > 0: # Sync arc contains delay
			id = self.enter(delay, 0, self.decrement, \
						(0, node, side))
			self.unfreeze()
			return
		if side == TL and node.counter[side] == 0:
			# To be fixed soon...
			print 'Skip spurious decrement of tail on ', \
				  MMAttrdefs.getattr(node, 'name')
			self.unfreeze()
			return
		x = node.counter[side] - 1
		node.counter[side] = x
		if x > 0:
		        self.unfreeze()
			return # Wait for other sync arcs
		if x < 0:
			print 'Node counter below zero on ', \
				  MMAttrdefs.getattr(node, 'name'), \
				  MMAttrdefs.getattr(node, 'channel')
			print self.queue
			raise CheckError, 'counter below zero!?!?'
		if self.seeking and side == HD:
			# We're searching for a node after a hyperjump
			# See if this is the correct node.
			if node == self.seek_node:
			        self.seek_done()
		doit = 1
		if node.GetType() not in interiortypes:
		    if side == HD:
			if doit:
			    chan = self.getchannel(node)
			    if chan == None:
				print 'Play node w/o channel'
				doit = 0
			if doit and self.seeking:
			    chan.playerseek_lastnode = node
			    d = chan.getduration(node)
			    print 'Skip node duration=', d
			    dummy = self.enter(d, 0, self.decrement, \
				(0, node, TL))
			elif doit:
			    if self.ff:
				self.ff = 0
				self.ffbutton.set_button(0)
			    #
			    # Begin tricky code section. First we have to find
			    # out wether the event has already been armed or
			    # not. if prearm_event doesn't exist we do it
			    # ourselves, if it exists and is None it
			    # is all done, otherwise it hasn't fired
			    # yet, so (again) we do it ourselves. 
			    # If we do the arm ourselves we use prio -1, so
			    # we do the arm before the play.
			    #
			    must_arm = 1
			    # print 'Node ', MMAttrdefs.getattr(node, 'name')
			    try:
				if node.prearm_event == None:
				    must_arm = 0
				else:
				    # The pre-arm event didn't happen
				    self.rtpool.cancel(node.prearm_event)
				del node.prearm_event
			    except AttributeError:
				pass
			    if must_arm:
				print 'Node not pre-armed on', \
				    MMAttrdefs.getattr(node, 'channel')
				dummy = self.enter(0.0, -1, \
				    chan.arm_and_measure, node)
			    self.setarmedmode(node, ARM_PLAYING)
			    dummy = self.enter(0.0, 0, chan.play, \
				(node, self.decrement, (0, node, TL)))
			    if self.setcurrenttime_callback:
				self.setcurrenttime_callback(node.t0)
			else:
			    dummy = self.enter(0.0, 0, \
				self.decrement, (0, node, TL))
		    else:
			# Side is Tail, so...
			self.setarmedmode(node, ARM_DONE)
			self.opt_prearm(node)
		for arg in node.deps[side]:
			self.decrement(arg)
		if node == self.playroot and side == TL:
			# The whole tree is finished -- stop playing.
			if self.setcurrenttime_callback:
				self.setcurrenttime_callback(node.t1)
			self.stop()
		self.unfreeze()
	#
	# opt_prearm allows channels to schedule a pre-arm of the next node on
	# the channel *before* the current one is finished playing. It is
	# currently used by the sound channel only (but could conceivably
	# be used by the Image channel as well).
	def opt_prearm(self, node):
		if node.node_to_arm:
			pn = node.node_to_arm
			try:
				# If prearm_event exists it has already
				# been taken care of.
				dummy = pn.prearm_event
				return
			except:
				pass
			d = pn.GetRawAttr('arm_duration')
			c = self.getchannel(pn)
			self.setarmedmode(pn, ARM_SCHEDULED)
			pn.prearm_event = self.rtpool.enter(pn.t0, d, \
				c.arm_only, pn)
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
	# Routine to do prearm feedback
	#
	def setarmedmode(self, node, mode):
		self.toplevel.channelview.setarmedmode(node, mode)
	#
	# Callback for anchor activations
	#
	def anchorfired(self, node, anchorlist):
		for i in anchorlist:
			print 'Anchor fired: ', i
		destlist = []
		for i in anchorlist:
			aid = (node.GetUID(), i[0])
			print 'Anchorid: ', aid
			rv = self.context.hyperlinks.findsrclink(aid)
			destlist = destlist + rv
		print 'Destinations:', destlist
		if not destlist:
			fl.show_message('No hyperlink sourced at this anchor')
			return
		if len(destlist) <> 1:
			print 'Sorry, not supported yet'
			return
		dest = destlist[0][1]
		if destlist[0][0] <> 0:
			print 'Sorry, will do JUMP anyway'
		try:
			self.seek_node = self.context.mapuid(dest[0])
			self.suspend_playing()
			self.seeking = 1
			self.playroot = self.root
			dummy = self.resume_1_playing(1.0)
			self.resume_2_playing()
		except NoSuchUIDError:
			fl.show_message('Dangling hyperlink selected')
			return

#
# del_timing removes all arm_duration attributes (so they will be recalculated)
#
def del_timing(node):
	if node.GetAttrDict().has_key('arm_duration'):
		node.DelAttr('arm_duration')
	if node.GetType() in ('par', 'seq'):
		children = node.GetChildren()
		for child in children:
			del_timing(child)
