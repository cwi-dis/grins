# Scheduler - The scheduler for playing cmif documents.


import time
from sched import scheduler
from MMExc import *
import MMAttrdefs
import Timing
import rtpool
from MMNode import alltypes, leaftypes, interiortypes
from ArmStates import *
from HDTL import HD, TL
from AnchorDefs import *
import SR

import fl	# For fl.showmessage only

# Priorities for the various events:
N_PRIO = 3
[PRIO_PREARM_NOW, PRIO_RUN, PRIO_LO] = range(N_PRIO)

class SchedulerContext():
	def init(self, parent, node, stop_on_end):
		self.active = 1
		self.parent = parent
		self.sractions = []
		self.srevents = {}
		self.playroot = node

		self.prepare_minidoc(stop_on_end)
		return self

	
	#
	# done - cleanup SchedulerContext.
	#
	def done(self):
		self.active = 0
		self.srevents = {}
		del self.sractions
		del self.parent
		del self.playroot

	#
	# genprearms generates the list of channels and a list of
	# nodes to be prearmed, in the right order.
	def gen_prearms(self):
		#
		# Create channel lists
		#
		self.channelnames, err = GetAllChannels(self.playroot)
		if err:
			enode, echan = err
			ename = MMAttrdefs.getattr(enode, 'name')
			fl.show_message('Warning: overlap in channels', \
				  'channels:'+(`echan`[1:-1]), \
				  'parent node:'+ename)
			#XXXX
			return 0
		#
		# Create per-channel list of prearms
		#
		self.prearmlists = {}
		for ch in self.channelnames:
			self.prearmlists[ch] = []
		GenAllPrearms(self.playroot, self.prearmlists)
		return 1
	#
	def stopchannels(self):
		for ch in self.channelnames:
			self.parent.channels[ch].stop()
	def softresetchannels(self):
		for ch in self.channelnames:
			self.parent.channels[ch].softreset()
	#
	# getnextprearm returns next prearm event due for given channel
	#
	def getnextprearm(self, ch):
		chlist = self.prearmlists[ch]
		if not chlist:
			return None
		ev = chlist[0]
		del chlist[0]
		# Not too useful: ev[1].set_armedmode(ARM_SCHEDULED)
		return ev
	#
	# run_initial_prearms schedules the first prearms.
	# Prearms that are immedeately needed are scheduled in a hi-pri queue,
	# the ones that are not needed until later in a lo-pri queue. Also, the
	# lo-pri queue is run one-event-at-a-time, so we put them in there 
	# sorted by time
	#
	def run_initial_prearms(self):
		mini = findminidocument(self.playroot)
		Timing.needtimes(mini)
		prearmnowlist = []
		prearmlaterlist = []
		now = self.playroot.t0
		for ch in self.channelnames:
			ev = self.getnextprearm(ch)
			if ev[1].t0 <= now:
				prearmnowlist.append(ev)
			else:
				prearmlaterlist.append(ev[1].t0, ev)
		self.parent.add_runqueue(self, PRIO_PREARM_NOW, prearmnowlist)
		prearmlaterlist.sort()
		pll = []
		for time, ev in prearmlaterlist:
			self.parent.add_lopriqueue(self, time, ev)
	#
	# Zap first prearm event on each channel and return list of
	# arm-done events.
	#
	def zap_initial_prearms(self):
		list = []
		for chname in self.channelnames:
			aev = self.getnextprearm(chname)
			if aev:
				list.append(SR.ARM_DONE, aev[1])
		return list

	#
	# FutureWork returns true if we may have something to do at some
	# time in the future (i.e. if we're not done yet)
	#
	def FutureWork(self):
		return (self.srevents <> {})
	#
	# XXXX
	#
	def prepare_minidoc(self, stop_on_end):
		#if self.play_all_bags:
		#	mini = self.playroot
		#else:
		#	mini = findminidocument(self.playroot)
		srlist = GenAllSR(self.playroot)
		#
		# If this is not the root document and if the 'pause minidoc'
		# flag is on we should not schedule the done for the root.
		#
		if stop_on_end:
			srlist.append(([(SR.SCHED_DONE, self.playroot)], \
				  [(SR.SCHED_STOP, self.playroot)]))
		else:
			srlist.append(([(SR.SCHED_DONE, self.playroot)], []))
			srlist.append(([(SR.NO_EVENT, self.playroot)], []))
		self.sractions = []
		self.srevents = {}
		for events, actions in srlist:
			nevents = len(events)
			actionpos = len(self.sractions)
			self.sractions.append((nevents, actions))
			for ev in events:
				if self.srevents.has_key(`ev`):
					raise 'Scheduler: Duplicate event:', \
						  SR.ev2string(ev)
				self.srevents[`ev`] = actionpos
		#if mini == self.playroot:
		#	arm_events = Timing.getinitial(mini)
		#else:
		#	arm_events = []
		#Timing.prepare(self.playroot)
		#return arm_events
	#
	# Start minidoc starts playing what we've prepared
	#
	def start_minidoc(self):
		if not self.gen_prearms():
			return 0
		self.run_initial_prearms()
		self.parent.event((self, (SR.SCHED, self.playroot)))
		return 1
	#
	# Seek minidoc to given node and start playing from there
	#
	def seek_minidoc(self, node):
		if self.playroot == node:
			return self.start_minidoc()
		if not self.gen_prearms():
			return None
		events = self.zap_initial_prearms()
		events.append(SR.SCHED, self.playroot)
		event_wanted = (SR.SCHED, node)
		found = None
		while events:
			ev = events[0]
			del events[0]
			srlist = self.getsrlist(ev)
			if event_wanted in srlist:
				# This is what we're looking for.
				# Give to parent and continue searching.
				found = srlist
			else:
				for nev, narg in srlist:
					if nev == SR.PLAY:
						events.append(\
							  SR.PLAY_DONE, narg)
						#
						# When a node is finished
						# pretend the next arm
						#
						ch = MMAttrdefs.getattr(narg,\
							  'channel')
						aev = self.getnextprearm(ch)
						if aev:
							aev = (SR.ARM_DONE,\
								  aev[1])
							events.append(aev)
					elif nev == SR.PLAY_STOP:
						pass
					elif nev == SR.SYNC:
						events.append(SR.SYNC_DONE, \
							  narg[1])
					else:
						events.append(nev, narg)
		if not found:
			raise 'scheduler: seek: node not found', node
		self.parent.add_runqueue(self, PRIO_RUN, found)
		return 1

	#
	# Incoming events from channels, or the start event.
	#
	def event(self, ev):
		srlist = self.getsrlist(ev)
		#if ev[0] == SR.ARM_DONE:
		#	cname = MMAttrdefs.getattr(ev[1], 'channel')
		#	pev = self.getnextprearm(cname)
		#	if pev:
		#		srlist.append(pev)
		if srlist:
			self.parent.add_runqueue(self, PRIO_RUN, srlist)

	def arm_ready(self, cname):
		pev = self.getnextprearm(cname)
		if pev:
			self.parent.add_lopriqueue(self, pev[1].t0, pev)
	#
	# Partially handle an event, updating the internal queues and
	# returning executable SRs, if any.
	#
	def getsrlist(self, ev):
		#print 'event:', SR.ev2string(ev)
		try:
			actionpos = self.srevents[`ev`]
			del self.srevents[`ev`]
		except KeyError:
			raise 'Scheduler: Unknown event:', SR.ev2string(ev)
		srlist = self.sractions[actionpos]
		if srlist == None:
			raise 'Scheduler: actions already sched for ev:', ev
		num, srlist = srlist
		num = num - 1
		if num < 0:
			raise 'Scheduler: waitcount<0:', (num, srlist)
		elif num == 0:
			self.sractions[actionpos] = None
			return srlist
		else:
			self.sractions[actionpos] = (num, srlist)
		return []
		
class Scheduler(scheduler):
	def init(self):
		self.sctx_list = []
		self.playing_nodes = []
		self.pause_minidoc = 1
		self.starting_to_play = 0
		return self

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
		self.playing = 1
		self.reset()
		self.runqueues = []
		for i in range(N_PRIO):
			self.runqueues.append([])
		self.toplevel.setwaiting()
		if self.sync_cv:
			self.toplevel.channelview.globalsetfocus(self.playroot)
		stop_on_end = ((self.playroot == self.root) or \
			  not self.pause_minidoc)
		sctx = SchedulerContext().init(self, self.playroot, \
			  stop_on_end)
		self.sctx_list.append(sctx)
		if not sctx.start_minidoc():
			self.suspend_sctx(sctx)
			return 0
		self.setrate(rate)
		self.showstate() # Give the anxious user a clue...
		self.starting_to_play = 1
		return 1
	#
	def suspend_sctx(self, sctx):
		unarmallnodes(sctx.playroot)
		sctx.stopchannels()
		sctx.done()
		self.purge_sctx_queues(sctx)
		self.sctx_list.remove(sctx)

	def purge_sctx_queues(self, sctx):
		for queue in self.runqueues:
			tokill = []
			for ev in queue:
				if ev[0] == sctx:
					tokill.append(ev)
			for ev in tokill:
				queue.remove(ev)
	#
	def stop_playing(self):
		if not self.playing:
			return
		self.playing = 0
		self.measure_armtimes = 0
		for sctx in self.sctx_list:
			self.suspend_sctx(sctx)
		self.setrate(0.0) # Stop the clock
		self.showstate()
		if self.starting_to_play:
			self.toplevel.setready()
			self.starting_to_play = 0
	#
	# Callback for anchor activations, called by channels.
	# Return 1 if the anchor fired, 0 if nothing happened.
	#
	def anchorfired(self, node, anchorlist):
		self.toplevel.setwaiting()
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
		if not destlist:
			if not pause_anchor:
				fl.show_message( \
				'No hyperlink source at this anchor', '', '')
			self.toplevel.setready()
			return 0
		if len(destlist) > 1:
			fl.show_message( \
				'Sorry, multiple links not supported', '', '')
			self.toplevel.setready()
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
			self.toplevel.setready()
			return 0
		if self.play_all_bags:
			seek_node = seek_node.FirstMiniDocument()
		else:
			while seek_node.GetType() == 'bag':
				seek_node = choosebagitem(seek_node)
				if seek_node == None:
					self.toplevel.setready()
					return 0
##		playroot = findminidocument(seek_node)
##		self.suspend_playing()
##		self.playroot = playroot
##		if self.sync_cv:
##			self.toplevel.channelview.globalsetfocus(self.playroot)
##		self.reset()
##		self.sctx = SchedulerContext().init(self, self.playroot, 0)
##		if not self.sctx.seek_minidoc(seek_node):
##			self.stop_playing()
##			return 1    # Cannot continue old document at this pt.
##		self.setrate(1.0)
		if len(self.sctx_list) <> 1:
			raise 'Uh-oh, not yet implemented (multi-sctx)'
		old_sctx = self.sctx_list[0]
		playroot = findminidocument(seek_node)
		stop_on_end = ((playroot == self.root) or \
			  not self.pause_minidoc)
		newsctx = SchedulerContext().init(self, playroot, stop_on_end)
		self.sctx_list.append(newsctx)
		if not newsctx.seek_minidoc(seek_node):
			self.suspend_sctx(newsctx)
			self.toplevel.set_ready()
			return 0
		self.purge_sctx_queues(old_sctx)
		if self.sync_cv:
			self.toplevel.channelview.globalsetfocus(playroot)
		old_sctx.softresetchannels()
		self.suspend_sctx(old_sctx)
		self.playroot = playroot
		self.updatetimer()
		self.starting_to_play = 1
		return 1

	#
	# The timer callback routine, called via a forms timer object.
	# This is what makes SR's being executed.
	#
	def timer_callback(self, obj, arg):
		#
		# We have two queues to execute: the timed queue and the
		# normal SR queue. Currently, we execute the timed queue first.
		# Also, e have to choose here between an eager and a non-eager
		# algorithm. For now, we're eager, on both queues.
		#
		now = self.timefunc()
		while self.queue and self.queue[0][0] <= now:
			when, prio, action, argument = self.queue[0]
			#delay = when - now
			#if delay < -0.1:
			#	self.statebutton.lcol = GL.MAGENTA
			#else:
			#	self.statebutton.lcol = self.statebutton.col2
			#if delay > 0.0:
			#	break
			del self.queue[0]
			void = apply(action, argument)
			now = self.timefunc()
		#
		# Now the normal runqueue
		#
		queue = self.selectqueue()
		for action in queue:
			self.runone(action)
		self.updatetimer()
		#self.showtime()
	#
	# FutureWork returns true if any of the scheduler contexts
	# has possible future work.
	def FutureWork(self):
		for sctx in self.sctx_list:
			if sctx.FutureWork():
				return 1
		return 0
	#
	# Updatetimer restarts the forms timer object. If we have work to do
	# we set the timeout very short, otherwise we simply stop the clock.
	def updatetimer(self):
		if not self.playing:
			delay = 0
			#print 'updatetimer: not playing' #DBG
		elif self.runqueues[PRIO_PREARM_NOW] or \
			  self.runqueues[PRIO_RUN] or \
			  self.runqueues[PRIO_LO]:
			#
			# We have SR actions to execute. Make the callback
			# happen as soon as possible.
			#
			delay = 0.001
			#print 'updatetimer: runnable events' #DBG
		elif self.queue:
			#
			# We have activity in the timed queue. Make sure we
			# get scheduled when the first activity is due.
			#
			now = self.timefunc()
			when = self.queue[0][0]
			delay = when - now
			if delay <= 0:
				#
				# It is overdue. Make the callback happen
				# fast.
				delay = 0.001
			#print 'updatetimer: timed events' #DBG
		elif not self.FutureWork():
			#
			# No more events (and nothing runnable either).
			# We're thru.
			#
			#print 'updatetimer: no more work' #DBG
			self.stop_playing()
			return
		else:
			#
			# Nothing to do for the moment. Stop the clock.
			#
			delay = 0
			#print 'updatetimer: idle' #DBG
		#print 'updatetimer: delay=', delay
		self.timerobject.set_timer(delay)
	#
	# Incoming events from channels, or the start event.
	#
	def event(self, *ev):
		# Hack: we can be called with either sctx, (action,node) or
		# ((sctx, (action,node),) arg, due to the way apply works.
		# sigh...
		if len(ev) == 1:
			ev = ev[0]
		sctx, ev = ev
		
		if ev[0] == SR.PLAY_DONE:
			ev[1].set_armedmode(ARM_WAITSTOP)

		if sctx.active:
			sctx.event(ev)
		self.updatetimer()
	#
	# opt_prearm should be turned into a normal event at some point.
	# It signals that the channel is ready for the next arm
	def arm_ready(self, cname):
		#XXXX Wrong for multi-context (have to find correct sctx)
		if len(self.sctx_list) > 1:
			raise 'Uh-oh, arm_ready multi-sctx'
		elif len(self.sctx_list) == 1:
			sctx = self.sctx_list[0]
			sctx.arm_ready(cname)
	#
	# Concatenate the given list of SR's to the runqueue.
	#
	def add_runqueue(self, sctx, prio, srlist):
		for sr in srlist:
			self.runqueues[prio].append(sctx, sr, 0)
	def add_lopriqueue(self, sctx, time, sr):
		runq = self.runqueues[PRIO_LO]
		for i in range(len(runq)):
			if runq[i][2] > time:
				runq.insert(i, (sctx, sr, time))
				return
		runq.append(sctx, sr, time)
			
	#
	# Try to run one SR. Return 0 if nothing to be done.
	#
	def selectqueue(self):
		#
		# First look in the high priority queues. We always run all
		# the events here.
		#
		for i in range(N_PRIO-1):
			if self.runqueues[i]:
				queue = self.runqueues[i]
				self.runqueues[i] = []
				return queue
		#
		# Otherwise we run one event from the lo-pri queue.
		#
		if self.runqueues[N_PRIO-1]:
			queue = [self.runqueues[N_PRIO-1][0]]
			del self.runqueues[N_PRIO-1][0]
			return queue
		#
		# Otherwise we run nothing.
		#
		return []

	def runone(self, (sctx, todo, dummy)):
		if not sctx.active:
			raise 'Scheduler: running from finished context'
		#DBG print 'exec: ', SR.ev2string(todo)
		action, arg = todo
		if action == SR.PLAY:
			self.do_play(sctx, arg)
		elif action == SR.PLAY_STOP:
			self.do_play_stop(sctx, arg)
		elif action == SR.SYNC:
			self.do_sync(sctx, arg)
		elif action == SR.PLAY_ARM:
			self.do_play_arm(sctx, arg)
		else:
			sctx.event((action, arg))
	#
	# Execute a PLAY SR.
	#
	def do_play(self, sctx, node):
		if self.starting_to_play:
			self.toplevel.setready()
			self.starting_to_play = 0
		chan = self.getchannel(node)
		#chan.arm_only(node)
		ready_ev = (sctx, (SR.PLAY_DONE, node))
		node.set_armedmode(ARM_PLAYING)
		chan.play(node, self.event, ready_ev)
		#self.playing_nodes.append(node)
	#
	# Execute a PLAY_STOP SR.
	#
	def do_play_stop(self, sctx, node):
		chan = self.getchannel(node)
		node.set_armedmode(ARM_DONE)
		chan.clearnode(node)
		#self.playing_nodes.remove(node)
	#
	# Execute a SYNC SR
	#
	def do_sync(self, sctx, (delay, aid)):
		ev = (sctx, (SR.SYNC_DONE, aid))
		id = self.enterabs(self.timefunc()+delay, 0, self.event, ev)
	#
	# Execute an ARM SR
	#
	def do_play_arm(self, sctx, node):
		chan = self.getchannel(node)
		node.set_armedmode(ARM_ARMING)
		chan.arm_only(node)
		node.set_armedmode(ARM_ARMED)
		self.event(sctx, (SR.ARM_DONE, node))
	#
	# Stop all playing nodes.
	# XXXX This needs to be done on selected channels only.
	#
	#def do_play_stop_all(self):
	#	for node in self.playing_nodes:
	#		chan = self.getchannel(node)
	#		chan.clearnode(node)
	#	self.playing_nodes = []
	#
	# Queue interface, based upon sched.scheduler.
	# This queue has variable time, to implement pause,
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
	def enterabs(self, time, priority, action, argument):
		id = scheduler.enterabs(self, time, priority, action, argument)
		self.updatetimer()
		return id
	#
	def timefunc(self):
	        if self.frozen: return self.frozen_value
		if not self.rate:
			return self.time_pause - self.time_origin
		return time.time() - self.time_origin
	#
	def resettimer(self):
		self.rate = 0.0		# Initially the clock is frozen
		self.frozen = 0
		self.frozen_value = 0
		self.time_origin = time.time()
		self.time_pause = self.time_origin
	#
	def skiptimer(self, amount):
		self.time_origin = self.time_origin - amount
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

		# Subtract time paused
		self.time_origin = self.time_origin - \
			  (time.time()-self.time_pause)
		self.rate = rate
		for cname in self.channelnames:
			self.channels[cname].setrate(self.rate)
		self.updatetimer()
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
# GenAllSR - Return all (evlist, actionlist) pairs.
#
def GenAllSR(node):
	#
	# First generate arcs
	#
	arcs = node.GetArcList()
	arcs = node.FilterArcList(arcs)
	for i in range(len(arcs)):
		n1, s1, n2, s2, delay = arcs[i]
		n1.SetArcSrc(s1, delay, i)
		n2.SetArcDst(s2, i)
	#
	# Now run through the tree
	#
	nodelist = [node]
	srlist = []
	while nodelist:
		cur_nodelist = nodelist[:]
		nodelist = []
		for cur_node in cur_nodelist:
			cur_srlist, children = cur_node.gensr()
			nodelist = nodelist + children
			srlist = srlist + cur_srlist
	return srlist
#
# MergeList merges two lists. It also returns a status value to indicate
# whether there was an overlap between the lists.
#
def MergeLists(l1, l2):
	overlap = []
	for i in l2:
		if i in l1:
			overlap.append(i)
		else:
			l1.append(i)
	return l1, overlap
#
# GetAllChannels - Get a list of all channels used in a tree.
# If there is overlap between parnode children the node in error is returned.
def GetAllChannels(node):
	if node.GetType() in leaftypes:
		return [MMAttrdefs.getattr(node, 'channel')], None
	errnode = None
	overlap = []
	list = []
	for ch in node.GetChildren():
		chlist, cherrnode = GetAllChannels(ch)
		if cherrnode:
			errnode = cherrnode
		list, choverlap = MergeLists(list, chlist)
		if choverlap:
			overlap = overlap + choverlap
	if overlap and node.GetType() == 'par':
		errnode = (node, overlap)
	return list, errnode
#
# GenAllPrearms fills the prearmlists dictionary with all arms needed.
#
def GenAllPrearms(node, prearmlists):
	if node.GetType() in leaftypes:
		chan = MMAttrdefs.getattr(node, 'channel')
		prearmlists[chan].append((SR.PLAY_ARM, node))
		return
	for child in node.GetChildren():
		GenAllPrearms(child, prearmlists)
		
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
	node.set_armedmode(ARM_NONE)
	children = node.GetChildren()
	for child in children:
		unarmallnodes(child)
