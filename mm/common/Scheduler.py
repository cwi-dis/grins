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

# Actions on end-of-play:
[END_STOP, END_PAUSE, END_KEEP] = range(3)

class SchedulerContext():
	def init(self, parent, node, seeknode, end_action):
		self.active = 1
		self.parent = parent
		self.sractions = []
		self.srevents = {}
		self.playroot = node
		self.parent.ui.duration_ind.label = '??:??'

		self.prepare_minidoc(seeknode, end_action)
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
	# Dump - Dump a scheduler context
	#
	def dump(self):
		print '------------------------------'
		print '--------- events:'
		for ev in self.srevents.keys():
			print SR.ev2string(ev),'\t', self.srevents[ev]
		print '--------- actions:'
		for i in range(len(self.sractions)):
			if self.sractions[i]:
				ac, list = self.sractions[i]
				print i,'\t',ac, '\t', SR.evlist2string(list)
		print '------------ #prearms outstanding:'
		for i in self.channelnames:
			print i, '\t', len(self.prearmlists[i])
		print '----------------------------------'

	#
	# genprearms generates the list of channels and a list of
	# nodes to be prearmed, in the right order.
	def gen_prearms(self):
		#
		# Create channel lists
		#
		self.channelnames, err = GetAllChannels(self.playroot)
		self.channels = []
		for cn in self.channelnames:
			self.channels.append(\
				  self.parent.ui.getchannelbyname(cn))
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
		self.playroot.EndPruneTree()
		return 1
	#
	def stopchannels(self):
		for ch in self.channels:
			ch.stop()
	def softresetchannels(self):
		for ch in self.channels:
			ch.softreset()
	def setrate(self, rate):
		for ch in self.channels:
			ch.setrate(rate)
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
			if not ev:
				continue
			if ev[1].t0 <= now:
				prearmnowlist.append(ev)
			else:
				prearmlaterlist.append(ev[1].t0, ev)
		self.parent.add_runqueue(self, PRIO_PREARM_NOW, prearmnowlist)
		prearmlaterlist.sort()
		pll = []
		for time, ev in prearmlaterlist:
			self.parent.add_lopriqueue(self, time, ev)
		d = int(self.playroot.t1 - self.playroot.t0)
		self.parent.ui.duration_ind.label = `d/60`+':'+`d/10%6`+`d%10`
	#
	# FutureWork returns true if we may have something to do at some
	# time in the future (i.e. if we're not done yet)
	#
	def FutureWork(self):
		return (self.srevents <> {})
	#
	# XXXX
	#
	def prepare_minidoc(self, seeknode, end_action):
		srlist = GenAllSR(self.playroot, seeknode)
		#
		# If this is not the root document and if the 'pause minidoc'
		# flag is on we should not schedule the done for the root.
		#
		if end_action == END_STOP:
			srlist.append(([(SR.SCHED_DONE, self.playroot)], \
				  [(SR.SCHED_STOP, self.playroot)]))
		elif end_action == END_PAUSE:
			srlist.append(([(SR.SCHED_DONE, self.playroot)], []))
			srlist.append(([(SR.NO_EVENT, self.playroot)], []))
		else: # end_action == END_KEEP
			srlist.append(([(SR.SCHED_DONE, self.playroot)], \
				  [(SR.SCHED_FINISH, self.playroot)]))
		self.sractions = []
		self.srevents = {}
		for events, actions in srlist:
			nevents = len(events)
			actionpos = len(self.sractions)
			self.sractions.append((nevents, actions))
			for ev in events:
				if self.srevents.has_key(ev):
					raise 'Scheduler: Duplicate event:', \
						  SR.ev2string(ev)
				self.srevents[ev] = actionpos
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
	# Incoming events from channels, or the start event.
	#
	def event(self, ev):
		srlist = self.getsrlist(ev)
		if srlist:
			self.parent.add_runqueue(self, PRIO_RUN, srlist)

	def arm_ready(self, cname):
		if cname == 'Scottish': print 'Scottish ready' #DBG
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
			actionpos = self.srevents[ev]
			del self.srevents[ev]
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
	def init(self, ui):
		self.queue = []
		self.ui = ui
		self.toplevel = self.ui.toplevel
		self.context = self.ui.context
		self.sctx_list = []
		self.starting_to_play = 0
		return self

	#
	# Playing algorithm.
	#
	def start_playing(self, rate):
		if not self.ui.maystart():
			return 0
		#if self.ui.play_all_bags:
		#	self.ui.playroot = self.ui.playroot.FirstMiniDocument()
		#else:
		if 1:
			while self.ui.playroot.GetType() == 'bag':
				self.ui.showstate()
				node = choosebagitem(self.ui.playroot)
				if not node:
					return 0
				self.ui.playroot = node
		self.ui.playing = 1
		#self.reset()
		self.runqueues = []
		for i in range(N_PRIO):
			self.runqueues.append([])
		self.toplevel.setwaiting()
		if self.ui.sync_cv:
			self.toplevel.channelview.globalsetfocus(self.ui.playroot)
		if self.ui.userplayroot != self.ui.root:
			end_action = END_KEEP
		elif not self.ui.pause_minidoc or \
			  self.ui.playroot == self.ui.root:
			end_action = END_STOP
		else:
			end_action = END_PAUSE
		sctx = SchedulerContext().init(self, self.ui.playroot, \
			  None, end_action)
		self.sctx_list.append(sctx)
		if not sctx.start_minidoc():
			self.suspend_sctx(sctx)
			return 0
		self.setrate(rate)
		self.ui.showstate() # Give the anxious user a clue...
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
	def dump(self):
		print '=============== scheduler dump'
		print '# timed events:', len(self.queue)
		print '# contexts:', len(self.sctx_list)
		for i in range(len(self.runqueues)):
			print '---- runqueue',i
			print SR.evlist2string(self.runqueues[i])
		for i in range(len(self.sctx_list)):
			print '---- context',i
			self.sctx_list[i].dump()
		print '==============================='
		
	def stop_playing(self):
		if not self.ui.playing:
			return
		self.ui.playing = 0
		self.measure_armtimes = 0
		for sctx in self.sctx_list:
			self.suspend_sctx(sctx)
		self.setrate(0.0) # Stop the clock
		self.ui.showstate()
		if self.starting_to_play:
			self.toplevel.setready()
			self.starting_to_play = 0
	#
	# Callback for anchor activations, called by channels.
	# Return 1 if the anchor fired, 0 if nothing happened.
	#
	def anchorfired(self, node, anchorlist):
		if not self.ui.playing:
			fl.show_message('The document is not playing!','','')
			return 0
		self.toplevel.setwaiting()
		destlist = []
		pause_anchor = 0
		# Firing an anchor continues the player if it was paused.
		if self.rate == 0.0:
			self.setrate(1.0)
			self.ui.showstate()
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
		#if self.ui.play_all_bags:
		#	seek_node = seek_node.FirstMiniDocument()
		#else:
		if 1:
			while seek_node.GetType() == 'bag':
				seek_node = choosebagitem(seek_node)
				if seek_node == None:
					self.toplevel.setready()
					return 0
		if len(self.sctx_list) <> 1:
			raise 'Uh-oh, not yet implemented (multi-sctx)'
		old_sctx = self.sctx_list[0]
		playroot = findminidocument(seek_node)
		if playroot == self.ui.root or not self.ui.pause_minidoc:
			end_action = END_STOP
		else:
			end_action = END_PAUSE
		newsctx = SchedulerContext().init(self, playroot, \
			  seek_node, end_action)
		self.sctx_list.append(newsctx)
		if not newsctx.start_minidoc():
			self.suspend_sctx(newsctx)
			self.toplevel.setready()
			return 0
		self.purge_sctx_queues(old_sctx)
		if self.ui.sync_cv:
			self.toplevel.channelview.globalsetfocus(playroot)
		old_sctx.softresetchannels()
		self.suspend_sctx(old_sctx)
		self.ui.playroot = playroot
		self.updatetimer()
		self.starting_to_play = 1
		return 1

	#
	# The timer callback routine, called via a forms timer object.
	# This is what makes SR's being executed.
	#
	def timer_callback(self):
		#
		# We have two queues to execute: the timed queue and the
		# normal SR queue. Currently, we execute the timed queue first.
		# Also, e have to choose here between an eager and a non-eager
		# algorithm. For now, we're eager, on both queues.
		#
		now = self.timefunc()
		while self.queue and self.queue[0][0] <= now:
			when, prio, action, argument = self.queue[0]
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
		#self.ui.showtime()
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
		if not self.ui.playing:
			delay = 0
			#print 'updatetimer: not playing' #DBG
		elif self.rate and ( self.runqueues[PRIO_PREARM_NOW] or \
			  self.runqueues[PRIO_RUN]):
			#
			# We have SR actions to execute. Make the callback
			# happen as soon as possible.
			#
			delay = 0.001
			#print 'updatetimer: runnable events' #DBG
		elif self.runqueues[PRIO_LO]:
			delay = 0.001
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
			else:
				self.ui.showtime()
			#print 'updatetimer: timed events' #DBG
		elif not self.FutureWork():
			#
			# No more events (and nothing runnable either).
			# We're thru.
			#
			#print 'updatetimer: no more work' #DBG
			self.ui.showtime()
			self.stop_playing()
			return
		else:
			#
			# Nothing to do for the moment.
			# Tick every second, so we see the timer run.
			#
			delay = 1
			self.ui.showtime()
			#print 'updatetimer: idle' #DBG
		#print 'updatetimer: delay=', delay
		self.ui.set_timer(delay)
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
		if self.rate:
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
		elif action == SR.SCHED_FINISH:
			self.stop_playing()
		else:
			sctx.event((action, arg))
	#
	# Execute a PLAY SR.
	#
	def do_play(self, sctx, node):
		if self.starting_to_play:
			self.toplevel.setready()
			self.starting_to_play = 0
		chan = self.ui.getchannelbynode(node)
		#chan.arm_only(node)
		ready_ev = (sctx, (SR.PLAY_DONE, node))
		node.set_armedmode(ARM_PLAYING)
		chan.play(node, self.event, ready_ev)
	#
	# Execute a PLAY_STOP SR.
	#
	def do_play_stop(self, sctx, node):
		chan = self.ui.getchannelbynode(node)
		node.set_armedmode(ARM_DONE)
		chan.clearnode(node)
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
		chan = self.ui.getchannelbynode(node)
		node.set_armedmode(ARM_ARMING)
		chan.arm_only(node)
		node.set_armedmode(ARM_ARMED)
		self.event(sctx, (SR.ARM_DONE, node))
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
	        #if self.frozen: return self.frozen_value
		if not self.rate:
			return self.time_pause - self.time_origin
		return time.time() - self.time_origin
	#
	def resettimer(self):
		self.rate = 0.0		# Initially the clock is frozen
		#self.frozen = 0
		#self.frozen_value = 0
		self.time_origin = time.time()
		self.time_pause = self.time_origin
	#
	def skiptimer(self, amount):
		self.time_origin = self.time_origin - amount
	#
	def setrate(self, rate):
		if rate < 0.0:
			raise CheckError, 'setrate with negative rate'
		if self.rate == rate:
			return

		# Subtract time paused
		if rate:
			self.time_origin = self.time_origin - \
				  (time.time()-self.time_pause)
		else:
			self.time_pause = time.time()
		self.rate = rate
		for sctx in self.sctx_list:
			sctx.setrate(self.rate)
		self.updatetimer()
	#
	def getrate(self):
		return self.rate
	#
#
# GenAllSR - Return all (evlist, actionlist) pairs.
#
def GenAllSR(node, seeknode):
	#
	# First generate arcs
	#
	node.PruneTree(seeknode)
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
	for child in node.GetWtdChildren():
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
#
# Unarm all nodes
#
def unarmallnodes(node):
	node.set_armedmode(ARM_NONE)
	children = node.GetChildren()
	for child in children:
		unarmallnodes(child)
