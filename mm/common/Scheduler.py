# Scheduler - The scheduler for playing cmif documents.


import time
from sched import scheduler
from MMExc import *
import MMAttrdefs
import Timing
import rtpool
from MMNode import alltypes, leaftypes, interiortypes
from ArmStates import *
from AnchorEdit import A_ID, A_TYPE, ATYPE_PAUSE
from HDTL import HD, TL

import fl	# For fl.showmessage only


class Scheduler(scheduler):
	#
	# Initialization.
	#
	def init(self):
		self.rtpool = rtpool.rtpool().init()
		return self
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
		now = self.origin + t*self.rate
		return now
	#
	def addtotimer(self, delay):
		if self.rate:
			self.origin = self.origin + delay
	#
	def resettimer(self):
		self.origin = 0.0	# Current time
		self.rate = 0.0		# Initially the clock is frozen
		self.msec_origin = 0	# Arbitrary since rate is 0.0
		self.frozen = 0
		self.frozen_value = 0
	#
	def skiptimer(self, amount):
		self.origin = self.origin + amount
	#
	def freeze(self):
	        if not self.frozen:
			self.frozen_value = self.timefunc()
		self.frozen = self.frozen + 1
	#
	def unfreeze(self):
	        self.frozen = self.frozen - 1
		if self.frozen < 0:
			print 'Player: self.frozen < 0!'
			raise 'Kaboo!'
	#
	# XXXX Can be a lot simpler, because rate can only be 1 or 0
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
		if self.seeking and delay > 0:
			self.skiptimer(delay)
			self.timerobject.set_timer(0.001)
##			print 'Player: updatetimer: skipped ', delay
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
		#print 'Player: Next timer: ', delay
		if self.ignore_delays:
			self.addtotimer(delay)
			delay = 0.001
		self.timerobject.set_timer(delay)
	#
	# Playing algorithm.
	#
	def start_playing(self, rate):
		if not self.maystart():
			return 0
		if self.play_all_bags:
			self.playroot = self.playroot.FirstMiniDocument()
		else:
			while self.playroot.GetType() == 'bag':
				self.showstate()
				node = choosebagitem(self.playroot)
				if not node:
					return 0
				self.playroot = node
		return self.start_2_playing(rate)
	#
	def start_2_playing(self, rate):
		arm_events = self.resume_1_playing(rate)
		for pn in arm_events:
			d = pn.GetRawAttr('arm_duration')
			c = self.getchannel(pn)
			pn.setarmedmode(ARM_SCHEDULED)
			# XXX Attempted fix by Jack: get rid of
			# multiple-arms of first few events
			if pn.t0 > 0:
				pn.prearm_event = self.rtpool.enter(pn.t0, d, \
				  c.arm_only, pn)
			else:
				c.arm_only(pn)
		self.resume_2_playing()
		return 1
	#
	def continue_next_bag(self):
		if not self.play_all_bags:
			return 0
		if self.playroot == self.root.LastMiniDocument():
			return 0
		self.suspend_playing()
		self.playroot = self.playroot.NextMiniDocument()
		if self.sync_cv:
			self.toplevel.channelview.globalsetfocus(self.playroot)
		return self.start_2_playing(1)
	#
	def resume_1_playing(self,rate):
		self.setwaiting()
		if self.sync_cv:
			self.toplevel.channelview.globalsetfocus(self.playroot)
		self.playing = 1
		self.reset()
		self.setrate(rate)
		self.showstate() # Give the anxious user a clue...
		if self.play_all_bags:
			mini = self.playroot
		else:
			mini = findminidocument(self.playroot)
		Timing.needtimes(mini)
		if mini == self.playroot:
			arm_events = Timing.getinitial(mini)
		else:
			arm_events = []
		Timing.prepare(self.playroot)
		return arm_events
	#
	def resume_2_playing(self):
		d = int(self.playroot.t1 - self.playroot.t0)
		label = `d/60` + ':' + `d/10%6` + `d % 10`
		self.duration_ind.label = label
		self.playroot.counter[HD] = 1
		self.decrement(0, self.playroot, HD)
		dummy = self.enter(0.1, 0, self.setready, ())
	#
	def suspend_playing(self):
		self.stopchannels() # Tell the channels to quit it
		self.queue[:] = [] # Erase all events with brute force!
		#print 'Player: Flush rtpool'
		self.rtpool.flush()
		self.setrate(0.0) # Stop the clock
		self.showstate()
		unarmallnodes(self.playroot)
		self.setready()
	#
	def stop_playing(self):
		self.playing = 0
		self.measure_armtimes = 0
		self.suspend_playing()
	#
	def seek_done(self):
		for node in self.seek_nodelist:
		    ch = self.getchannel(node)
		    if self.measure_armtimes:
			    ch.arm_and_measure(node)
		    else:
			    ch.arm_only(node)
	            node.setarmedmode(ARM_PLAYING)
		    dummy = self.enter(0.0, 0, ch.play, \
			      (node, self.decrement, (0, node, TL)))
		    if self.setcurrenttime_callback:
			    self.setcurrenttime_callback(node.t0)
		self.seeking = 0
		self.seek_node = None
		self.seek_nodelist = []
	#
	def dummy(arg):
		pass
	#
	def decrement(self, (delay, node, side)):
		#print 'DEC', delay, node, side, ' of ', node.counter[side]
	        self.freeze()
		if delay > 0: # Sync arc contains delay
			id = self.enter(delay, 0, self.decrement, \
						(0, node, side))
			self.unfreeze()
			return
		if side == TL and node.counter[side] == 0:
			# XXX To be fixed soon...
			print 'Player:Skip spurious decrement of tail on ', \
				  MMAttrdefs.getattr(node, 'name')
			self.unfreeze()
			return
		x = node.counter[side] - 1
		node.counter[side] = x
		if x > 0:
		        self.unfreeze()
			return # Wait for other sync arcs
		if x < 0:
			print 'Player: Node counter below zero on ', \
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
		type = node.GetType()
		if type not in interiortypes:
		    if side == HD:
			if doit:
			    chan = self.getchannel(node)
			    if chan == None:
				print 'Player: Play node w/o channel'
				doit = 0
			if doit and self.seeking:
			    if node.t0 <= self.seek_node.t0 < node.t1:
				    self.seek_nodelist.append(node)
			    else:
				    d = chan.getduration(node)
##				    print 'Player: Skip node duration=', d
				    dummy = self.enter(d, 0, self.decrement, \
					      (0, node, TL))
			elif doit:
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
			    #print 'Node ', MMAttrdefs.getattr(node, 'name')
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
				print 'Player: Node not pre-armed on', \
				    MMAttrdefs.getattr(node, 'channel'), node.uid
				if self.measure_armtimes:
					dummy = self.enter(0.0, -1, \
						  chan.arm_and_measure, node)
				else:
					dummy = self.enter(0.0, -1, \
						  chan.arm_only, node)
			    dummy = self.enter(0.0, 0, chan.play, \
				(node, self.decrement, (0, node, TL)))
			    if self.setcurrenttime_callback:
				self.setcurrenttime_callback(node.t0)
			else:
			    dummy = self.enter(0.0, 0, \
				self.decrement, (0, node, TL))
		    else:
			# Side is Tail, so...
##			node.setarmedmode(ARM_DONE)
			if not self.seeking:
				self.opt_prearm(node)
		elif type == 'par' and side == TL:
##			print 'Player: Parnode finished'
			# A parallel node has finished. Tell the channels
			# to clear their windows of the children nodes.
			children = node.GetChildren()
			for child in children:
				chan = self.getchannel(child)
				if chan <> None:
					dummy = self.enter(0.0, 1, chan.clearnode, child)
		for arg in node.deps[side]:
			self.decrement(arg)
		if node == self.playroot and side == TL:
			# The whole mini-document is finished -- stop playing.
			if self.setcurrenttime_callback:
				self.setcurrenttime_callback(node.t1)
			if self.play_all_bags:
				# Hack: we don't now how recursive we are, so
				# we remember self.frozen and fix it up later.
				kf = self.frozen
				if not self.continue_next_bag():
					print 'No next bag!'
					self.stop()
				print 'Ok, there we go!', self.frozen
				self.frozen = kf
			else:
				self.stop()
		self.unfreeze()
	#
	# opt_prearm allows channels to schedule a pre-arm of the next node on
	# the channel *before* the current one is finished playing. It is
	# currently used by the sound channel only (but could conceivably
	# be used by the Image channel as well).
	#
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
			pn.setarmedmode(ARM_SCHEDULED)
			pn.prearm_event = self.rtpool.enter(pn.t0, d, \
				c.arm_only, pn)
	#
	# Channel access utilities.
	#
	# The 'node.channel' cache might not be as helpful as it seems. It
	# does cut down on the number of calls to getattr() (1 per node played
	# in stead of 3), but the getattr cache also helped before. The saving
	# is about .1 second per node played.
	#
	def getchannel(self, node):
		try:
			return node.channel
		except AttributeError:
			pass
		cname = MMAttrdefs.getattr(node, 'channel')
		if self.channels.has_key(cname):
			node.channel = self.channels[cname]
		else:
			node.channel = None
		return node.channel
	#
	# Callback for anchor activations, called by channels.
	# Return 1 if the anchor fired, 0 if nothing happened.
	#
	def anchorfired(self, node, anchorlist):
		destlist = []
		pause_anchor = 0
		# Firing an anchor continues the player if it was paused.
		if self.rate == 0.0:
			self.setrate(1.0)
			self.showstate()
		for i in anchorlist:
			if i[A_TYPE] == ATYPE_PAUSE:
				pause_anchor = 1
			aid = (node.GetUID(), i[A_ID])
			rv = self.context.hyperlinks.findsrclinks(aid)
			destlist = destlist + rv
##		print 'Player: Destinations:', destlist
		if not destlist:
			if pause_anchor:
				return 0
			fl.show_message( \
				'No hyperlink source at this anchor', '', '')
			return 0
		if len(destlist) > 1:
			fl.show_message( \
				'Sorry, multiple links not supported', '', '')
			return 0
		# XXX This assumes all links have this lay-out!
		anchor1, anchor2, dir, type = destlist[0]
		if type <> 0:
			fl.show_message('Sorry, will JUMP anyway', '', '')
		dest_uid, dest_aid = anchor2
		try:
			seek_node = self.context.mapuid(dest_uid)
		except NoSuchUIDError:
			fl.show_message('Dangling hyperlink selected', '', '')
			return 0
		if self.play_all_bags:
			seek_node = seek_node.FirstMiniDocument()
		else:
			while seek_node.GetType() == 'bag':
				seek_node = choosebagitem(seek_node)
				if seek_node == None:
					return 0
		playroot = findminidocument(seek_node)
		self.suspend_playing()
		self.seek_node = seek_node
		self.playroot = playroot
		self.seeking = (playroot <> seek_node)
		if self.seeking:
			dummy = self.resume_1_playing(1.0)
			self.resume_2_playing()
		else:
			dummy = self.start_2_playing(1.0)
			# Which *does* do prearms
		return 1


# Choose an item from a bag, or None if the bag is empty
# This is a modal dialog!
# (Also note the similarity with NodeEdit._showmenu...)

def choosebagitem(node):
	indexname = MMAttrdefs.getattr(node, 'bag_index')
	children = node.GetChildren()
	list = []
	for child in children:
		name = MMAttrdefs.getattr(child, 'name')
		if name == '':
			name = '???'
		elif name == indexname:
			return child
		type = child.GetType()
		if type == 'bag':
			colorindex = 60 # XXX BlockView.BAGCOLOR
		elif type in leaftypes:
			colorindex = 61 # XXX BlockView.LEAFCOLOR
		else:
			colorindex = None
		list.append((name, colorindex))
	list.append('Cancel')
	prompt = 'Please select an item\nfrom the bag:'
	import multchoice
	choice = multchoice.multchoice(prompt, list, len(list) - 1)
	if 0 <= choice < len(children):
		return children[choice]
	else:
		return None


# Find the root of a node's mini-document

def findminidocument(node):
	path = node.GetPath()
	i = len(path)
	while i > 0 and path[i-1].GetType() <> 'bag':
		i = i-1
	if 0 <= i < len(path):
		return path[i]
	else:
		print 'Weird: findminidocument of bag node'
		return node


#  Remove all arm_duration attributes (so they will be recalculated)

def del_timing(node):
	if node.GetAttrDict().has_key('arm_duration'):
		node.DelAttr('arm_duration')
	children = node.GetChildren()
	for child in children:
		del_timing(child)


# Flush per-node channel cache
#
# See comments for getchannel on the usefulness of the routine.
#
def flushchannelcache(node):
	try:
		del node.channel
	except (AttributeError, KeyError):
		pass
	children = node.GetChildren()
	for child in children:
		flushchannelcache(child)
#
# Unarm all nodes
#
def unarmallnodes(node):
	node.setarmedmode(ARM_NONE)
	children = node.GetChildren()
	for child in children:
		unarmallnodes(child)
