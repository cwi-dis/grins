__version__ = "$Id$"

# Scheduler - The scheduler for playing cmif documents.

import time
from sched import scheduler
from MMExc import *
import MMAttrdefs
import Timing
from MMTypes import *
from ArmStates import *
from HDTL import HD, TL
# Not needed? from AnchorDefs import *
import SR

debugtimer = 0

# Priorities for the various events:
N_PRIO = 5
[PRIO_PREARM_NOW, PRIO_INTERN, PRIO_STOP, PRIO_START, PRIO_LO] = range(N_PRIO)

class SchedulerContext:
	def __init__(self, parent, node, seeknode):
		self.active = 1
		self.parent = parent
		self.sractions = []
		self.srevents = {}
		self.playroot = node
		#self.parent.ui.duration_ind.label = '??:??'

		self.prepare_minidoc(seeknode)

	
	#
	# stop - cleanup SchedulerContext.
	#
	def stop(self):
		if not self.active:
			return
		self.active = 0
		unarmallnodes(self.playroot)
		self.stopcontextchannels()
		self.srevents = {}
		self.parent._remove_sctx(self)
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
		for i in self.channels:
			print i, '\t', len(self.prearmlists[i])
		print '----------------------------------'

	#
	# genprearms generates the list of channels and a list of
	# nodes to be prearmed, in the right order.
	def gen_prearms(self, s_node):
		if not s_node:
			s_node = self.playroot
		if hasattr(s_node, 'prearmlists'):
			self.prearmlists = {}
			for cn, val in s_node.prearmlists.items():
				ch = self.parent.ui.getchannelbyname(cn)
				self.prearmlists[ch] = val[:]
			self.channels = self.prearmlists.keys()
			self.channelnames = s_node.prearmlists.keys()
			self.parent.channels_in_use = \
					self.parent.channels_in_use + \
					self.channels
			return 1
		#
		# Create channel lists
		#
		self.channelnames, err = self.playroot.GetAllChannels()
		self.channels = []
		if err:
			import windowinterface
			enode, echan = err
			ename = MMAttrdefs.getattr(enode, 'name')
			windowinterface.showmessage('Error: overlap in channels'+ \
				  '\nchannels:'+(`echan`[1:-1])+ \
				  '\nparent node:'+ename)
			return 0
		# First make a pass to check channels are free
		todo = []
		for cn in self.channelnames:
			ch = self.parent.ui.getchannelbyname(cn)
			if not ch:
			        import windowinterface
				windowinterface.showmessage(
				    'Channel does not exist: ' + cn)
				return 0
			if ch in self.parent.channels_in_use:
				import windowinterface
				windowinterface.showmessage(
				    'Channel already in use: ' + cn)
				return 0
			todo.append(ch)
		# Next, actually set them to be in use.
		for ch in todo:
			self.parent.channels_in_use.append(ch)
			self.channels.append(ch)
		#
		# Create per-channel list of prearms
		#
		self.prearmlists = {}
		for ch in self.channels:
			self.prearmlists[ch] = []
		GenAllPrearms(self.parent.ui, self.playroot, self.prearmlists)
		self.playroot.EndPruneTree()
		mini = self.playroot.FindMiniDocument()
		Timing.needtimes(mini)
		s_node.prearmlists = {}
		for ch, val in self.prearmlists.items():
			s_node.prearmlists[ch._name] = val[:]
		return 1
	#
	def startcontextchannels(self):
		for ch in self.channels:
			ch.startcontext(self)
	#
	def stopcontextchannels(self):
		for ch in self.channels:
			ch.stopcontext(self)
			self.parent.channels_in_use.remove(ch)
	#
	def setpaused(self, paused):
		for ch in self.channels:
			ch.setpaused(paused)

	#
	# getnextprearm returns next prearm event due for given channel
	#
	def getnextprearm(self, ch):
		chlist = self.prearmlists[ch]
		if not chlist:
			return None
		ev = chlist[0]
		del chlist[0]
		return ev
	#
	# run_initial_prearms schedules the first prearms.
	# Prearms that are immedeately needed are scheduled in a hi-pri queue,
	# the ones that are not needed until later in a lo-pri queue. Also, the
	# lo-pri queue is run one-event-at-a-time, so we put them in there 
	# sorted by time
	#
	def run_initial_prearms(self):
		# XXXX Code gone to gen_prearms
		prearmnowlist = []
		prearmlaterlist = []
		now = self.playroot.t0
		parent = self.parent
		for ch in self.channels:
			ev = self.getnextprearm(ch)
			if not ev:
				continue
			if ev[1].t0 <= now:
				prearmnowlist.append(ev)
			else:
				prearmlaterlist.append(ev[1].t0, ev)
		for ev in prearmnowlist:
			parent.add_runqueue(self, PRIO_PREARM_NOW, ev)
		prearmlaterlist.sort()
		for time, ev in prearmlaterlist:
			parent.add_lopriqueue(self, time, ev)
	#
	# FutureWork returns true if we may have something to do at some
	# time in the future (i.e. if we're not done yet)
	#
	def FutureWork(self):
		if self.srevents:
			return 1
		self.parent.ui.sctx_empty(self) # XXXX
		return 0
	#
	# XXXX
	#
	def prepare_minidoc(self, seeknode):
		self.sractions, self.srevents = self.playroot.GenAllSR(seeknode)

	#
	# Start minidoc starts playing what we've prepared
	#
	def start(self, s_node, s_aid, s_args):
		if not self.gen_prearms(s_node):
			return 0
		self.run_initial_prearms()
		self.startcontextchannels()
		if s_node and s_aid:
			self.seekanchor(s_node, s_aid, s_args)
		self.parent.event(self, (SR.SCHED, self.playroot))
		self.parent.updatetimer()
		return 1
	#
	# Seekanchor indicates that we are playing here because of the
	# anchor specified.
	#
	def seekanchor(self, node, aid, aargs):
		chan = self.parent.ui.getchannelbynode(node)
		if chan:
			chan.seekanchor(node, aid, aargs)
	#
	# Incoming events from channels, or the start event.
	#
	def event(self, ev):
		srlist, firstevents = self.getsrlist(ev)
		for sr in srlist:
			if sr[0] == SR.PLAY:
				prio = PRIO_START
			elif sr[0] == SR.PLAY_STOP:
				prio = PRIO_STOP
			else:
				prio = PRIO_INTERN
			self.parent.add_runqueue(self, prio, sr)
		for sr in firstevents:
			self.parent.add_runqueue(self, PRIO_LO, sr)
	#
	def arm_ready(self, chan):
		if not self.prearmlists.has_key(chan):
			raise 'Arm_ready event for unknown channel', chan
		pev = self.getnextprearm(chan)
		if pev:
			self.parent.add_lopriqueue(self, pev[1].t0, pev)
	#
	def play_done(self, node):
		self.parent.event(self, (SR.PLAY_DONE, node))
	#
	def arm_done(self, node):
		self.parent.event(self, (SR.ARM_DONE, node))
	#
	def anchorfired(self, node, anchorlist, arg):
		return self.parent.anchorfired(self, node, anchorlist, arg)
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
		if srlist is None:
			raise 'Scheduler: actions already sched for ev:', ev
		if len(srlist) == 2:
			num, srlist = srlist
			firstactions = []
		else:
			#
			# Firstactions are executed when the first
			# event comes in and then immedeately forgotten
			#
			num, srlist, firstactions = srlist
		num = num - 1
		if num < 0:
			raise 'Scheduler: waitcount<0:', (num, srlist)
		elif num == 0:
			self.sractions[actionpos] = None
		else:
			self.sractions[actionpos] = (num, srlist)
			srlist = []
		return srlist, firstactions
		
class Scheduler(scheduler):
	def __init__(self, ui):
		self.queue = []
		self.ui = ui
		self.toplevel = self.ui.toplevel
		self.context = self.ui.context
		self.sctx_list = []
		self.runqueues = []
		for i in range(N_PRIO):
			self.runqueues.append([])
		self.starting_to_play = 0
		self.playing = 0
		self.paused = 0
		self.resettimer()
		self.paused = 0
		# 'inherit' method from parent:
		self.anchorfired = self.ui.anchorfired
		self.channels_in_use = []

	#
	# Playing algorithm.
	#
	def play(self, node, seek_node, anchor_id, anchor_arg):
		# XXXX Is the following true for alt nodes too?
		if node.GetType() == 'bag':
			raise 'Cannot play choice node'
		# XXXX This statement should move to an intermedeate level.
		if self.ui.sync_cv:
			self.toplevel.channelview.globalsetfocus(node)
		sctx = SchedulerContext(self, node, seek_node)
		self.sctx_list.append(sctx)
		self.playing = self.playing + 1
		if not sctx.start(seek_node, anchor_id, anchor_arg):
##			print 'Scheduler: play abort'
			sctx.stop()
			return None
		self.starting_to_play = 1
		self.ui.showstate() # Give the anxious user a clue...
		return sctx
	#
	def _remove_sctx(self, sctx):
##		print 'Remove:', sctx
		self.playing = self.playing - 1
		self.purge_sctx_queues(sctx)
		self.sctx_list.remove(sctx)

	def purge_sctx_queues(self, sctx):
		for queue in self.runqueues:
			tokill = []
			for ev in queue:
				if ev[0] is sctx:
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
			for j in self.runqueues[i]:
				print SR.ev2string(j[1]),
			print
		for i in range(len(self.sctx_list)):
			print '---- context',i
			self.sctx_list[i].dump()
		print '==============================='
		
	def stop_all(self):
##		print 'STOP_ALL', self.sctx_list
		to_stop = self.sctx_list[:]
		for sctx in to_stop:
			sctx.stop()
		to_stop = None
##		print 'Now', self.sctx_list
		self.ui.showstate()
		if self.starting_to_play:
			self.starting_to_play = 0
		self.playing = 0
		self.ui.play_done()

##	#
##	# XXXX This routine is temporary. Eventually the channels should
##	# also indicate the sctx when an anchor fires.
##	def find_sctx(self, node):
##		channel = self.ui.getchannelbynode(node)
##		for sctx in self.sctx_list:
##			if sctx.contains_channel(channel):
##				return sctx
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
		if debugtimer: print 'timer_callback'
		self.toplevel.setwaiting()
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
		# if we're going to be called very soon, don't bother
		# calling setready
		if self.delay == 0 or self.delay > 0.01:
			self.toplevel.setready()
	#
	# FutureWork returns true if any of the scheduler contexts
	# has possible future work. Each context's FutureWork has to be
	# called (since this is also where contexts tell that they are empty).
	#
	def FutureWork(self):
		has_work = 0
		for sctx in self.sctx_list:
			if sctx.FutureWork():
				has_work = 1
		return has_work
	#
	# Updatetimer restarts the forms timer object. If we have work to do
	# we set the timeout very short, otherwise we simply stop the clock.
	def updatetimer(self):
		# Helper variable:
		self.delay = 0
		work = 0
		for q in self.runqueues:
			if q:
				work = 1
				break
		if not self.playing:
			delay = 0
			if debugtimer: print 'updatetimer: not playing' #DBG
		elif not self.paused and work:
			#
			# We have SR actions to execute. Make the callback
			# happen as soon as possible.
			#
			delay = 0.001
			if debugtimer: print 'updatetimer: runnable events' #DBG
		elif self.runqueues[PRIO_PREARM_NOW] or \
			  self.runqueues[PRIO_LO]:
			#
			# We are not running (paused=1), but we can do some
			# prearms
			#
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
##			else:
##				self.ui.showtime()
			if debugtimer: print 'updatetimer: timed events' #DBG
		elif not self.FutureWork():
			#
			# No more events (and nothing runnable either).
			# We're thru.
			#
			if debugtimer: print 'updatetimer: no more work' #DBG
##			self.ui.showtime()
			self.stop_all()
			return
		else:
			#
			# Nothing to do for the moment.
			# Tick every second, so we see the timer run.
			#
##			delay = 1
##			self.ui.showtime()
			#self.ui.showpauseanchor(1) # Does not work look nice
			if debugtimer:  'updatetimer: idle' #DBG
			return
		if debugtimer: print 'updatetimer: delay=', delay
		self.delay = delay
		self.ui.set_timer(delay)
	#
	# Incoming events from channels, or the start event.
	#
	def event(self, sctx, ev):
		if sctx.active:
			if ev[0] == SR.PLAY_DONE:
				ev[1].set_armedmode(ARM_WAITSTOP)
			elif ev[0] == SR.ARM_DONE:
				ev[1].set_armedmode(ARM_ARMED)
			sctx.event(ev)
		self.updatetimer()
##	#
##	# opt_prearm should be turned into a normal event at some point.
##	# It signals that the channel is ready for the next arm
##	def arm_ready(self, chan):
##		#XXXX Wrong for multi-context (have to find correct sctx)
##		for sctx in self.sctx_list:
##			if sctx.arm_ready(chan):
##				print 'prearm:', cname, sctx
##				return
##		raise 'arm_ready: unused channel', chan
	#
	# Add the given SR to one of the runqueues.
	#
	def add_runqueue(self, sctx, prio, sr):
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
		if not self.paused:
			for i in range(N_PRIO-1):
				if self.runqueues[i]:
					queue = self.runqueues[i]
					self.runqueues[i] = []
					return queue
		#
		# Otherwise we run one event from one of the arm queues.
		#
		if self.runqueues[PRIO_PREARM_NOW]:
			queue = self.runqueues[PRIO_PREARM_NOW]
			self.runqueues[PRIO_PREARM_NOW] = []
			return queue
		if self.runqueues[PRIO_LO]:
			import windowinterface
			windowinterface.lopristarting()
			queue = [self.runqueues[PRIO_LO][0]]
			del self.runqueues[PRIO_LO][0]
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
		elif action in (SR.BAG_START, SR.BAG_STOP):
			self.ui.bag_event(sctx, todo)
		else:
			sctx.event((action, arg))
	#
	# Execute a PLAY SR.
	#
	def do_play(self, sctx, node):
		if self.starting_to_play:
			self.starting_to_play = 0
		chan = self.ui.getchannelbynode(node)
		node.set_armedmode(ARM_PLAYING)
		chan.play(node)
	#
	# Execute a PLAY_STOP SR.
	#
	def do_play_stop(self, sctx, node):
		chan = self.ui.getchannelbynode(node)
		node.set_armedmode(ARM_DONE)
		chan.stopplay(node)
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
		chan.arm(node)
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
		if self.paused:
			return self.time_pause - self.time_origin
		return time.time() - self.time_origin
	#
	def resettimer(self):
		#self.rate = 0.0		# Initially the clock is frozen
		#self.frozen = 0
		#self.frozen_value = 0
		self.time_origin = time.time()
		self.time_pause = self.time_origin
	#
	def skiptimer(self, amount):
		self.time_origin = self.time_origin - amount
	#
	def getpaused(self):
		return self.paused
		
	def setpaused(self, paused):
		if self.paused == paused:
			return

		# Subtract time paused
		if not self.paused:
			self.time_origin = self.time_origin - \
				  (time.time()-self.time_pause)
		else:
			self.time_pause = time.time()
		self.paused = paused
		for sctx in self.sctx_list:
			sctx.setpaused(paused)
		self.updatetimer()

#
# GenAllPrearms fills the prearmlists dictionary with all arms needed.
#
def GenAllPrearms(ui, node, prearmlists):
	nodetype = node.GetType()
	if nodetype in bagtypes:
		return
	if nodetype in leaftypes:
		chan = ui.getchannelbynode(node)
		prearmlists[chan].append((SR.PLAY_ARM, node))
		return
	for child in node.GetWtdChildren():
		GenAllPrearms(ui, child, prearmlists)

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
	#print 'UNARM', MMAttrdefs.getattr(node, 'name')
## 	if not hasattr(node, 'armedmode'):
## 		# if node does not have an 'armedmode' attribute, it
## 		# also does not have a GetChildren method
## 		return
	node.set_armedmode(ARM_NONE)
	try:
		children = node.GetChildren()
	except AttributeError:
		return
	for child in children:
		if child.GetType() not in bagtypes:
			unarmallnodes(child)

