__version__ = "$Id$"

# Scheduler - The scheduler for playing cmif documents.

import time
from sched import scheduler
from MMExc import *
import MMAttrdefs
import MMNode
from MMTypes import *
from ArmStates import *
import SR
import settings
import features
import MMStates

if __debug__:
	debugtimer = 0
	debugevents = 0
	debugdump = 0

# A complicated error message for a technical simple case.
NODE_NOT_RUN="""Not rendered.

The duration, freeze and other constraints
caused this item to be skipped completely."""

SCHEDULE_DEPTH = 3			# how deep we should go scheduling sync arcs
					# a value < 3 gave various continuation problems

# Priorities for the various events:
N_PRIO = 5
[PRIO_PREARM_NOW, PRIO_INTERN, PRIO_STOP, PRIO_START, PRIO_LO] = range(N_PRIO)

error = 'Scheduler.error'

class SchedulerContext:
	# There is n Scheduler Context instances for each Scheduler instance.
	# The current implementation only has one Scheduler instance and, when playing, one SchedulerContext
	# instance

	def __init__(self, parent, node, seeknode):
		self.queue = []
		self.active = 1
		self.parent = parent
		self.srdict = {}
		self.scheduled_children = 0
		self.channels = []	# channels that have received a startcontext call
		self.erase_chan = {}
		self.playroot = MMNode.FakeRootNode(node)
		#self.parent.ui.duration_ind.label = '??:??'

		self.prepare_minidoc(seeknode, 0)
		if __debug__:
			if debugdump:self.dump()


	#
	# stop - cleanup SchedulerContext.
	#
	def stop(self, curtime):
		if not self.active:
			return
		self.active = 0
		self.stopcontextchannels(curtime)
		self.srdict = {}
		self.erase_chan = {}
		self.parent._remove_sctx(self)
		self.playroot.reinit()
		self.playroot.resetall(None)
		del self.parent
		del self.playroot

	#
	# Dump - Dump a scheduler context
	#
	if __debug__:
		def dump(self, events=None, actions=None):
			actions = {}
			for ev, srdict in self.srdict.items():
				ac = srdict[ev]
				if ac is None:
					continue
				if not actions.has_key(id(ac)):
					actions[id(ac)] = [ac]
				actions[id(ac)].append(ev)
			print '------------------------------'
			for l in actions.values():
				num, ac = l[0]
				events = l[1:]
				if num != len(events):
					print 'discrepancy:',
				print SR.evlist2string(events),
				print '-->',
				print SR.evlist2string(ac)
			print '----------------------------------'

	#
	def startcontextchannels(self):
		for ch in self.channels:
			ch.startcontext(self)
	#
	def stopcontextchannels(self, curtime):
		for ch in self.channels:
			ch.stopcontext(self, curtime)
##			self.parent.channels_in_use.remove(ch)
		self.channels = []
	#
	def setpaused(self, paused):
		for ch in self.channels:
			ch.uipaused(paused)

	#
	# FutureWork returns true if we may have something to do at some
	# time in the future (i.e. if we're not done yet)
	#
	def FutureWork(self, curtime):
		if self.srdict or self.scheduled_children:
			return 1
		self.parent.ui.sctx_empty(self, curtime) # XXXX
		return 0
	#
	# Initialize SR actions and events before playing
	#
	def prepare_minidoc(self, seeknode, curtime):
		self.srdict = self.playroot.GenAllSR(curtime, seeknode, sctx = self)
	#
	# Re-initialize SR actions and events for a looping node, preparing
	# for the next time through the loop
	#
	def restartloop(self, node, curtime):
		if __debug__:
			if debugdump: self.dump()
		srdict = node.GenLoopSR(curtime, self)
		for key, value in srdict.items():
			if self.srdict.has_key(key):
				raise error, 'Duplicate event '+SR.ev2string(key)
			self.srdict[key] = value
	#
	# Start minidoc starts playing what we've prepared
	#
	def start(self, s_node, s_args, timestamp = None):
		if __debug__:
			if debugevents: print 'SchedulerContext.start',`self`, `s_node`, `s_args`, timestamp, self.parent.timefunc()
		self.startcontextchannels()
		if s_node:
			self.seekanchor(s_node, s_args)
		playroot = self.playroot
		if timestamp is None:
			timestamp = self.parent.timefunc()
		playroot.set_start_time(timestamp)

		self.parent.event(self, (SR.SCHED, self.playroot), timestamp)
		self.parent.updatetimer(timestamp)
		return 1
	#
	# Seekanchor indicates that we are playing here because of the
	# anchor specified.
	#
	def seekanchor(self, node, aargs):
		if isinstance(node, MMNode.MMNode_body):
			node = node.parent
		chan = self.parent.ui.getchannelbynode(node)
		if chan:
			chan.seekanchor(node, aargs)
	#
	# Incoming events from channels, or the start event.
	#
	def event(self, ev, timestamp):
		if __debug__:
			if debugevents: print 'event', SR.ev2string(ev), timestamp, self.parent.timefunc()
		srlist = self.getsrlist(ev)
		self.queuesrlist(srlist, timestamp)

	def sched_arc(self, node, arc, curtime, event = None, marker = None, timestamp = None, depth = 0, external = 0, propagate = 1, force = 0):
		# Schedules a single SyncArc for a node.
		
		# node is the node for the start of the arc.
		# arc is the SyncArc
		# event is the event 
		# marker is ?
		# timestamp is the time.. now.

		if __debug__:
			if debugevents: print 'sched_arc',`node`,`arc`,curtime,event,marker,propagate,timestamp,self.parent.timefunc()
		if arc.wallclock is not None:
			timestamp = arc.resolvedtime(self)-arc.delay
		elif arc.marker is not None and '#' in arc.marker:
			timestamp = arc.refnode().markerhappened(arc.marker, self)
		elif timestamp is None:	# Retrieve the timestamp if it was not supplied.
			timestamp = self.parent.timefunc()
		if arc.ismin:
			list = []
		elif arc.isstart:
			dev = 'begin'
##			list = arc.dstnode.GetBeginList()
			list = []
			if not force and arc.dstnode.isresolved(self) is None:
##			if not node.checkendlist(self, timestamp):
				# we didn't find a time interval
				if __debug__:
					if debugevents: print 'sched_arc: not allowed to start',arc,self.parent.timefunc()
				if external:
					self.parent.updatetimer(curtime)
				return
		else:
			if event is not None and event not in ('begin', 'end'):
				# a real event, only does something when node is active
				if arc.dstnode.playing in (MMStates.IDLE, MMStates.PLAYED):
					if external:
						self.parent.updatetimer(curtime)
					return
				# delay sync arc to min time if not dur
				if not arc.isdur and arc.dstnode.has_min:
					timestamp = max(arc.dstnode.start_time + arc.dstnode.has_min, timestamp)
			dev = 'end'
			list = arc.dstnode.GetEndList()
			list = list + arc.dstnode.durarcs
		if arc.timestamp is not None and arc.timestamp != timestamp+arc.delay:
			if arc.qid is not None:
				if __debug__:
					if debugevents: print 'sched_arc: cancel',`arc`,self.parent.timefunc()
				self.cancelarc(arc, timestamp)
		for a in list:
			if a.qid is None:
				continue
			if a.ismin:
				continue
			if a.timestamp > timestamp + arc.delay:
				if __debug__:
					if debugevents: print 'sched_arc: cancel',`a`,self.parent.timefunc()
				self.cancelarc(a, timestamp)
				if a.isstart:
					if a.dstnode.GetSchedParent():
						srdict = a.dstnode.GetSchedParent().gensr_child(curtime, a.dstnode, runchild = 0, sctx = self)
						self.srdict.update(srdict)
						if __debug__:
							if debugevents: print 'scheduled_children-1 a',`a.dstnode`,`a`,event,a.dstnode.scheduled_children,self.parent.timefunc()
						a.dstnode.scheduled_children = a.dstnode.scheduled_children - 1
					else:
						# root node
						self.scheduled_children = self.scheduled_children - 1
				else:
					if __debug__:
						if debugevents: print 'scheduled_children-1 b',`a.dstnode`,`a`,event,a.dstnode.scheduled_children,self.parent.timefunc()
					a.dstnode.scheduled_children = a.dstnode.scheduled_children - 1
		if arc.qid is None and (not arc.isstart or arc.dstnode.playing != MMStates.PLAYING or timestamp + arc.delay != arc.dstnode.start_time):
			if arc.isstart:
				pnode = arc.dstnode.GetSchedParent()
				if pnode is not None:
					srdict = pnode.gensr_child(curtime, arc.dstnode, runchild = 0, sctx = self)
					pnode.starting_children = pnode.starting_children + 1
					self.srdict.update(srdict)
					if __debug__:
						if debugevents: print 'scheduled_children+1 c',`arc.dstnode`,`arc`,event,arc.dstnode.scheduled_children,self.parent.timefunc()
					arc.dstnode.scheduled_children = arc.dstnode.scheduled_children + 1
				else:
					# root node
					self.scheduled_children = self.scheduled_children + 1
			else:
				if __debug__:
					if debugevents: print 'scheduled_children+1 d',`arc.dstnode`,`arc`,event,arc.dstnode.scheduled_children,self.parent.timefunc()
				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children + 1
##			print 'set timestamp a',arc,timestamp + arc.delay
			arc.timestamp = timestamp + arc.delay
##			if not arc.isstart and not arc.ismin and arc.srcnode is arc.dstnode and arc.event == 'begin':
##				# end arcs have lower priority than begin arcs
##				# this is important to get proper freeze
##				# behavior in constructs such as
##				# <par>
##				#   <par>
##				#     <img .../>
##				#   </par>
##				#   <video .../>
##				# </par>
##				prio = 1
##			else:
##				prio = 0
			prio = arc.srcnode != 'syncbase'
			if arc.isstart and arc.dstnode.playing in (MMStates.PLAYING, MMStates.FROZEN) and arc.dstnode.start_time == arc.timestamp:
				pass
			else:
				arc.qid = self.parent.enterabs(arc.timestamp, prio, self.trigger, (max(arc.timestamp,curtime),arc,None,None,arc.timestamp))
			if arc.isstart:
				if arc.dstnode.start_time is None or arc.dstnode.start_time > arc.timestamp:
					arc.dstnode.set_start_time(arc.timestamp, 0)
				arc.dstnode.depends['begin'].append(arc)
			else:
				arc.dstnode.depends['end'].append(arc)
				if arc.ismin:
					arc.dstnode.has_min = arc.delay
			if node.deparcs.has_key(event) and arc not in node.deparcs[event]:
				node.deparcs[event].append(arc)
				arc.depends.append((node, event))
		if propagate and not arc.ismin and (force or arc.dstnode is not node or dev != event) and depth < SCHEDULE_DEPTH:
			ts = timestamp+arc.delay
			if arc.dstnode.has_min and dev == 'end':
				# maybe delay dependent sync arcs
				mintime = arc.dstnode.has_min
				ts = max(ts, arc.dstnode.start_time + mintime)
			self.sched_arcs(arc.dstnode, curtime, dev, timestamp=ts, depth = depth+1)
		if external:
			self.parent.updatetimer(curtime)

	def sched_arcs(self, node, curtime, event = None, marker = None, timestamp = None, depth = 0, external = 0):
		# Schedule all sync and event arcs that depend on
		# event or marker happening on node.  Only one of
		# event and marker is supplied (i.e. not None).
		if __debug__:
			if debugevents: print 'sched_arcs',`node`,event,marker,timestamp,self.parent.timefunc(),depth
		if node.isresolved(self) is None:
			return
		if timestamp is None:	# Retrieve the timestamp if it was not supplied.
			timestamp = self.parent.timefunc()
		channel = accesskey = None
		if event is not None:
			node.event(timestamp, event) # record that event happened
			if type(event) is type(()):
				# if tuple, it's either accesskey or
				# event from channel (i.e. region or
				# topLayout).
				if event[1] == 'accesskey':
					accesskey = event[2]
					event = None
				else:
					channel, event = event[:2]
		if marker is not None:
			node.marker(timestamp, marker) # record that marker happened

		# Iterate through the dependant syncarcs of this node
		for arc in node.sched_children:
			# this tests wheter the dependant arc can be
			# scheduled at this time (i.e. it should be of
			# the right type with a definite delay etc.).
			if __debug__:
				if debugevents: print 'sched_arcs',`node`,'trying',`arc`,
			if (arc.channel != channel or
			    arc.getevent() != event or
			    arc.marker != marker or
			    arc.accesskey != accesskey or
			    arc.delay is None) and \
			   (arc.getevent() is not None or
			    arc.marker is not None or
			    marker is not None or
			    arc.accesskey is not None or
			    arc.delay is None or
			    ((event != 'begin' or arc.dstnode not in node.GetSchedChildren()) and
			     (event != 'end' or arc.dstnode in node.GetSchedChildren()))) and \
			   (marker is not None or
			    arc.marker is None or
			    '#' not in arc.marker or
			    event != 'begin'):
				if __debug__:
					if debugevents: print 'continue'
				continue
			if depth > 0 and arc.srcnode == 'syncbase' and arc.dstnode in node.GetSchedChildren():
				if __debug__:
					if debugevents: print 'continue too'
				continue
			propagate = 1
			if arc.isstart:
				blist = arc.dstnode.FilterArcList(arc.dstnode.GetBeginList())
				for a in blist:
					if a.isresolved(self):
						t = a.resolvedtime(self)
						if t < arc.timestamp and t >= self.parent.timefunc():
							propagate = 0
							break
			if __debug__:
				if debugevents: print 'do it'
			do_continue = 0	# on old Python we can't continue from inside try/except
			try:
				if arc.__in_sched_arcs:
					# loop in syncarcs
					if __debug__:
						if debugevents: print 'break syncarc loop',arc
					do_continue = 1
			except AttributeError:
				pass
			else:
				if do_continue:
					continue
			arc.__in_sched_arcs = 1	# to break recursion
			self.sched_arc(node, arc, curtime, event, marker, timestamp, depth, propagate = propagate)
			arc.__in_sched_arcs = 0
		if depth == 0 and event == 'begin':
			# also do children that are runnable
			for child in node.wtd_children:
				for arc in child.FilterArcList(child.GetBeginList()):
					if arc.qid is None and arc.isresolved(self):
						t = child.isresolved(self)
						if t is not None:
							if __debug__:
								if debugevents: print 'sched_arcs: also do',arc,timestamp,t
							arc.__in_sched_arcs = 1	# to break recursion
							self.sched_arc(node, arc, curtime, event, None, t-arc.delay, depth)
							arc.__in_sched_arcs = 0
		if __debug__:
			if debugevents: print 'sched_arcs return',`node`,event,marker,timestamp,self.parent.timefunc()
		if external:
			self.parent.updatetimer(curtime)

	def trigger(self, curtime, arc, node = None, path = None, timestamp = None):
		# Triggers a single syncarc.

		# if arc == None, arc is not used, but node and timestamp are
		# this happens when trigger is called because of a hyperjump

		# if arc != None, arc is used, and node and timestamp are not
		# this is the normal case

		parent = self.parent
		parent.setpaused(1, curtime, 0)
		if __debug__:
			if debugevents: print 'trigger',curtime,`arc`,`node`,`path`,timestamp,parent.timefunc()
		paused = parent.paused
		parent.paused = 0
		self.flushqueue(curtime)
		if not parent.playing:
			return
		parent.paused = paused

		if arc is not None:
			node = arc.dstnode
			if arc.qid is None:
				if __debug__:
					if debugevents: print 'trigger: ignore arc',`arc`
				parent.updatetimer(curtime)
				return
			if arc.qid and parent.queue and parent.queue[0][:2] < arc.qid[:2]:
				# a higher priority element has cropped up in
				# the queue: reinsert this one so that the
				# other one can be handled first
				# must insert it before all other equal priority events
				i = 0
				while i < len(parent.queue) and parent.queue[i][:2] < arc.qid[:2]:
					i = i+1
				parent.queue.insert(i, (arc.qid[0], arc.qid[1], self.trigger, (curtime,arc,None,None,timestamp)))
				parent.updatetimer(curtime)
				return
			if not arc.isstart and node.playing in (MMStates.IDLE, MMStates.PLAYED):
				# node is not playing so we should
				# ignore terminating arcs
				if __debug__:
					if debugevents: print 'trigger: idle',`arc`
				self.cancelarc(arc, timestamp, propagate = 1, syncbase = 0)
				parent.updatetimer(curtime)
				return
			if node.has_min and not arc.isstart and not arc.ismin:
				# must delay this arc
				node.delayed_end = 1
##				self.cancelarc(arc, timestamp, propagate = 1)
				if arc.isdur:
					# fill between end of simple duration and end of active duration
					self.do_terminate(node, curtime, timestamp, fill = node.GetFill(), skip_cancel = 1)
##				node.delayed_arcs.append(arc)
##				if arc in node.durarcs:
##					self.do_terminate(node, curtime, timestamp, fill = node.GetFill())
				parent.updatetimer(curtime)
				return
##			if arc.getevent() == 'end' and arc.refnode().playing == MMStates.IDLE:
##				if __debug__:
##					if debugevents: print 'ignoring',arc
##				self.cancelarc(arc, timestamp, propagate = 1)
##				parent.updatetimer(curtime)
##				return
			for nd, ev in arc.depends:
				try:
					nd.deparcs[ev].remove(arc)
				except ValueError:
					pass
			arc.depends = []
			timestamp = arc.resolvedtime(self)
			save_qid = arc.qid
			arc.qid = None
			try:
				if arc.isstart:
					node.depends['begin'].remove(arc)
				else:
					node.depends['end'].remove(arc)
			except ValueError:
				pass
##			if arc in node.durarcs:
##				node.sched_children.remove(arc)
##				node.durarcs.remove(arc)
##			else:
##				pbody = node.GetSchedParent()
##				if pbody.looping_body_self:
##					pbody = pbody.looping_body_self
##				if (arc.srcnode, arc) in pbody.arcs:
##					pbody.arcs.remove((arc.srcnode, arc))
##					arc.srcnode.sched_children.remove(arc)
		pnode = node.GetSchedParent()
		if arc is not None:
			if arc.ismin:
				node.has_min = 0
				if __debug__:
					if debugevents: print 'scheduled_children-1 e',`node`,`arc`,node.scheduled_children,parent.timefunc()
				node.scheduled_children = node.scheduled_children - 1
				if node.delayed_end:
					self.sched_arcs(node, curtime, 'end', timestamp = timestamp)
				if node.delayed_play_done:
					self.play_done(node, curtime, timestamp = timestamp)
				node.delayed_play_done = node.delayed_end = 0
##				while node.delayed_arcs:
##					arc = node.delayed_arcs[0]
##					del node.delayed_arcs[0]
##					arc.qid = 0
##					self.trigger(curtime, arc)
				parent.updatetimer(curtime)
				return
##				# if there is a SCHED_STOPPING event on the
##				# right-hand side in the srdict, don't stop
##				for ev, srdict in self.srdict.items():
##					numac = srdict[ev]
##					if numac is None:
##						continue
##					for ac in numac[1]:
##						op, nd = ac
##						if op == SR.SCHED_STOPPING and nd == node:
##							if __debug__:
##								if debugevents: print 'trigger: not stopping (ismin)'
##							return
			if arc.isstart:
				if pnode is not None:
					pnode.starting_children = pnode.starting_children - 1
					if __debug__:
						if debugevents: print 'scheduled_children-1 f',`node`,`arc`,node.scheduled_children,parent.timefunc()
					if node.scheduled_children > 0:
						node.scheduled_children = node.scheduled_children - 1
				if arc.path:
					path = arc.path
					arc.path = None
					# zap all other paths
					for a in arc.dstnode.GetBeginList():
						a.path = None
			else:
				if __debug__:
					if debugevents: print 'scheduled_children-1 g',`node`,`arc`,node.scheduled_children,parent.timefunc()
				if node.scheduled_children > 0:
					node.scheduled_children = node.scheduled_children - 1
				if node.playing not in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
					# ignore end event if not playing
					if __debug__:
						if debugevents: print 'node not playing',parent.timefunc()
					node.endtime = (timestamp, arc.getevent())
					parent.updatetimer(curtime)
					return
				if arc.isdur:
					dur = node.GetAttrDef('duration', None)
					if dur is not None and dur != -1 and arc.srcnode is arc.dstnode:
						# arc is for explicit duration, so node should terminate
						pass
					elif node.GetTerminator() == 'LAST':
						if node.starting_children > 0:
							if __debug__:
								if debugevents: print 'not stopping (scheduled children)'
							parent.updatetimer(curtime)
							return
						for c in node.GetSchedChildren():
							if c.playing == MMStates.PLAYING:
								if __debug__:
									if debugevents: print 'not stopping (playing children)'
								parent.updatetimer(curtime)
								return
					elif node.starting_children > 0:
						i = 0
						while i < len(parent.queue) and parent.queue[i][:2] <= save_qid[:2]:
							i = i+1
						if i > 0:
							if __debug__:
								if debugevents: print 'delay stop (scheduled children)'
							node.scheduled_children = node.scheduled_children + 1
							arc.qid = save_qid
							parent.queue.insert(i, (arc.qid[0], arc.qid[1], self.trigger, (curtime,arc,None,None,timestamp)))
							parent.updatetimer(curtime)
							return
				if __debug__:
					if debugevents: print 'terminating node',parent.timefunc()
				if pnode is not None and \
				   pnode.type == 'excl' and \
				   pnode.pausestack and \
				   node not in pnode.pausestack:
					nnode = pnode.pausestack[0]
					del pnode.pausestack[0]
					self.do_terminate(node, curtime, timestamp)
					if not parent.playing:
						return
					self.do_resume(nnode, curtime, timestamp)
				else:
					self.do_terminate(node, curtime, timestamp, fill = node.GetFill())
					self.flushqueue(curtime)
##				for a in node.FilterArcList(node.GetBeginList()):
##					if a.isresolved(self) and a.resolvedtime(self) >= timestamp:
##						self.sched_arc(node, arc, curtime, event='begin', timestamp=timestamp)
				parent.updatetimer(curtime)
				return
		# the node should start, but we need to do some more checks
		if not pnode:
			self.scheduled_children = self.scheduled_children - 1
		if not pnode or pnode.playing != MMStates.PLAYING:
			# ignore event when node can't play
			if __debug__:
				if debugevents: print 'parent not playing',parent.timefunc()
			parent.updatetimer(curtime)
			return
		# ignore restart attribute on hyperjump (i.e. when arc is None)
		if arc is not None and \
		   ((node.playing in (MMStates.PLAYING, MMStates.PAUSED) and
		     node.GetRestart() != 'always') or
		    (node.playing in (MMStates.FROZEN, MMStates.PLAYED) and
		     node.GetRestart() == 'never')):
			# ignore event when node doesn't want to play
			if __debug__:
				if debugevents: print "node won't restart",parent.timefunc()
			self.cancelarc(arc, timestamp)
			parent.updatetimer(curtime)
			return
		endlist = node.GetEndList()
		endlist = node.FilterArcList(endlist)
		# This "if" statement is to not get flashes in the
		# editor if you have a RealPix file that was converted
		# to SMIL 2.0 and the images all overlap and you start
		# somewhere in the middle of the sequence.
		# Whether we do this also in the player is debatable.
		# We should really be better at not flashing.
		fill = None
		if features.editor and timestamp < curtime:
			fill = node.GetFill()
			if fill == 'hold':
				fill = 'freeze'
		endtime = node.calcendfreezetime(self, fill = fill)
		if endtime is not None and endtime >= 0 and endtime <= curtime:
			found = 0
		elif endlist:
			found = 0
			for a in endlist:
				if a.event is not None and a.event not in ('begin', 'end'):
					# events can happen again and again
					found = 1
				elif not a.isresolved(self):
					# any unresolved time is after any resolved time
					found = 1
				else:
					ats = a.resolvedtime(self)
					if ats > curtime:
						found = 1
					elif ats == curtime:
						found = 1
						break
		else:
			found = 1
		if not found:
			# we didn't find a time interval
			if __debug__:
				if debugevents: print 'not allowed to start',node,parent.timefunc()
			node.set_infoicon('error', NODE_NOT_RUN)
			srdict = pnode.gensr_child(curtime, node, runchild = 0, sctx = self)
			self.srdict.update(srdict)
			ev = (SR.SCHED_DONE, node)
			if __debug__:
				if debugevents: print 'trigger: queueing',SR.ev2string(ev), timestamp, parent.timefunc()
			parent.event(self, ev, timestamp)
			parent.updatetimer(curtime)
			return
		# now we know for sure the node should start
		# if node is playing (or not stopped), must terminate it first
		if node.playing not in (MMStates.IDLE, MMStates.PLAYED):
			if __debug__:
				if debugevents: print 'terminating node',parent.timefunc()
			pnode.scheduled_children = pnode.scheduled_children + 1
			self.do_terminate(node, curtime, timestamp)
			if not parent.playing:
				return
			self.flushqueue(curtime)
			if arc is not None and arc.event is not None and arc.event not in ('begin','end'):
				# node starting because of event: clear old time stamp
				if __debug__:
					if debugevents: print 'clear timestamp',node
				node.set_start_time(None)
			self.sched_arcs(node, curtime, 'begin', timestamp=timestamp, depth=1)
			pnode.scheduled_children = pnode.scheduled_children - 1
##		node.cleanup_sched(parent)
		for c in node.GetSchedChildren():
			c.resetall(parent)
		if pnode.type == 'excl':
			action = 'nothing'
			for sib in pnode.GetSchedChildren():
				if sib is node:
					continue
				if sib.playing == MMStates.PLAYING:
					# found a playing sibling,
					# check priorityClass stuff
					pcmp, p1, p2 = sib.PrioCompare(node)
					if __debug__:
						if debugevents: print `sib`,`node`,pcmp,p1,p2,parent.timefunc()
					if pcmp == 0:
						if p1[0].type == 'excl':
							# no priorityClass
							action = 'stop'
						else:
							action = MMAttrdefs.getattr(p1[0], 'peers')
					elif pcmp < 0:
						action = MMAttrdefs.getattr(p1[1], 'lower')
					else:
						action = MMAttrdefs.getattr(p1[1], 'higher')
					if __debug__:
						if debugevents: print 'action',action,parent.timefunc()
					if action == 'stop':
						fill = sib.GetFill()
						if fill != 'hold' and fill != 'transition':
							fill = 'remove'
						self.do_terminate(sib, curtime, timestamp, fill = fill)
						if not parent.playing:
							return
					elif action == 'never':
						if arc is not None:
							self.cancelarc(arc, timestamp)
						self.cancel_gensr(node)
						parent.updatetimer(curtime)
						return
					elif action == 'defer':
						if node not in pnode.pausestack:
							srdict = pnode.gensr_child(curtime, node, sctx = self)
							self.srdict.update(srdict)
						node.set_start_time(timestamp)
						self.do_pause(pnode, node, 'hide', timestamp)
						parent.updatetimer(curtime)
						return
					elif action == 'pause':
						if pcmp == 0:
							x = p1[0]
						else:
							x = p1[1]
						pd = None
						while (pd is None or pd == 'inherit') and x.type == 'prio':
							pd = x.attrdict.get('pauseDisplay')
							x = x.parent
						if pd is None:
							pd = 'show'
						self.do_pause(pnode, sib, pd, timestamp)
					break
				elif sib.playing == MMStates.FROZEN:
					fill = sib.GetFill()
					if fill != 'hold' and fill != 'transition':
						fill = 'remove'
					self.do_terminate(sib, curtime, timestamp, fill = fill)
					if not parent.playing:
						return
					break
		elif pnode.type == 'seq':
			# parent is seq, must terminate running child first
			if __debug__:
				if debugevents: print 'terminating siblings',parent.timefunc()
			srdict = pnode.gensr_child(curtime, node, runchild = 0, sctx = self)
			self.srdict.update(srdict)
			for c in pnode.GetSchedChildren():
				# don't have to terminate it again
				if c is not node and c.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
					# if fill="hold", freeze child, otherwise kill
					fill = c.GetFill()
					if fill != 'hold' and fill != 'transition':
						fill = 'remove'
					self.do_terminate(c, curtime, timestamp, fill = fill, cancelarcs = arc is None)
					if not parent.playing:
						return
					# there can be only one active child
					break
		paused = parent.paused
		parent.paused = 0
		self.flushqueue(curtime)
		if not parent.playing:
			return
		parent.paused = paused
		# we must start the node, but how?
		if __debug__:
			if debugevents: print 'starting node',`node`,parent.timefunc()
			if debugdump: self.dump()
		# complicated rules to determine whether we need to play:
		# if start time + duration is before current time and
		# fill is remove, we don't play.  Duration is
		# determined from the real duration and the min and
		# max times.
		runchild = 1
		if hasattr(node, 'endtime'):
			tm, ev = node.endtime
			if tm == timestamp or ev in ('begin', 'end'):
				runchild = 0
			del node.endtime
		ndur = node.calcfullduration(self, ignoremin = 1)
		mintime, maxtime = node.GetMinMax()
		if ndur is None:
			# unknown duration, assume indefinite
			ndur = -1
		if ndur >= 0:
			ndur = max(mintime, ndur) # play at least this long
		if maxtime >= 0:
			if ndur >= 0:
				ndur = max(maxtime, ndur) # don't play longer than this
			else:
				ndur = maxtime
		if ndur >= 0 and timestamp + ndur <= parent.timefunc() and MMAttrdefs.getattr(node, 'erase') != 'never' and node.GetFill() == 'remove':
			runchild = 0
		srdict = pnode.gensr_child(curtime, node, runchild, path = path, sctx = self)
		self.srdict.update(srdict)
		if __debug__:
			if debugdump: self.dump()
		node.set_start_time(timestamp)
		if runchild:
			parent.event(self, (SR.SCHED, node), timestamp)
		else:
			if __debug__:
				if debugevents: print 'trigger, no run',parent.timefunc()
			node.set_infoicon('error', NODE_NOT_RUN)
			node.startplay(timestamp)
			timestamp = timestamp + ndur # we know ndur >= 0
			node.stopplay(timestamp)
##			self.sched_arcs(node, curtime, 'begin', timestamp=timestamp)
##			self.sched_arcs(node, curtime, 'end', timestamp=timestamp)
			ev = (SR.SCHED_DONE, node)
			if __debug__:
				if debugevents: print 'trigger: queueing(2)',SR.ev2string(ev), timestamp, parent.timefunc()
			parent.event(self, ev, timestamp)
		parent.updatetimer(curtime)

	def cancelarc(self, arc, timestamp, cancel_gensr = 1, propagate = 0, syncbase = 1):
		if __debug__:
			if debugevents: print 'cancelarc',`arc`,timestamp
# the commented-out lines fix a problem with
# Default_Fill_on_time_container1.smil but cause worse problems with
# hyperlinking.
##		if arc.timestamp == timestamp:
##			if __debug__:
##				if debugevents: print 'cancelarc returning early'
##			return
		try:
			self.parent.cancel(arc.qid)
		except ValueError:
			pass
		else:
			if __debug__:
				if debugevents: print 'scheduled_children-1 j',`arc.dstnode`,`arc`,arc.dstnode.scheduled_children,self.parent.timefunc()
			arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
			pnode = arc.dstnode.GetSchedParent()
			if pnode is not None:
				pnode.starting_children = pnode.starting_children - 1
		arc.qid = None
		for nd, ev in arc.depends:
			try:
				nd.deparcs[ev].remove(arc)
			except ValueError:
				pass
		arc.depends = []
		if arc.isstart:
			ev = 'begin'
		else:
			ev = 'end'
		depends = arc.dstnode.depends[ev]
		try:
			depends.remove(arc)
		except ValueError:
			pass
		if not depends:
			# no more arcs can cause the event to happen:
			# cancel any dependant arcs
			deparcs = arc.dstnode.deparcs[ev]
			arc.dstnode.deparcs[ev] = []
			if not propagate and arc.timestamp == timestamp:
				return
			if arc.isstart and cancel_gensr:
				self.cancel_gensr(arc.dstnode)
			for a in deparcs:
				if syncbase or (a.srcnode != 'syncbase' and not a.implicit):
					self.cancelarc(a, timestamp, cancel_gensr, propagate)

	def gototime(self, node, gototime, timestamp, path = None):
		# XXX trigger syncarcs that should go off after gototime?
		parent = self.parent
		if __debug__:
			if debugevents: print 'gototime',`node`,gototime,timestamp,node.time_list,parent.timefunc()
		# timestamp is "current" time
		# gototime is time where we want to start
		if not path:
			path = None
		elif node is path[0]:
			del path[0]
		if path:
			path0 = path[0]
			if path0.type == 'switch':
				path0 = path0.ChosenSwitchChild()
		for start, end1, end2 in node.time_list:
			if start > gototime:
				# no more valid intervals
				break
			if end2 is None or end2 > gototime:
				# found a valid interval, start node
				if node.playing in (MMStates.PLAYING, MMStates.PAUSED):
					if node.GetSyncBehavior() == 'independent':
						# leave this guy alone
						return
					if node.type in ('par', 'excl'):
						# interior node that should be playing
						# is already playing.  Recurse
						for c in node.GetSchedChildren():
							if path and c is path0:
								self.gototime(c, gototime, timestamp, path)
							else:
								self.gototime(c, gototime, timestamp)
						if node.type == 'par' or not path:
							return
					if node.type in ('seq', 'excl'):
						if path:
							if path0 in node.GetSchedChildren():
								self.gototime(path0, gototime, timestamp, path)
								return
##							raise error, 'internal error'
						for c in node.GetSchedChildren():
							for s, e1, e2 in c.time_list:
								if s > gototime:
									break
								if e2 is None or e2 > gototime:
									self.gototime(c, gototime, timestamp)
									return
						# XXX no children that want to start?
						return
				# start interior node not yet playing or
				# start any leaf node
				self.trigger(gototime, None, node, path, start)
				self.sched_arcs(node, gototime, 'begin', timestamp = start)
				return
		if node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
			# no valid intervals, so node should not play
			self.do_terminate(node, gototime, timestamp)
			if not parent.playing:
				return
		if path is not None or node.playing in (MMStates.IDLE, MMStates.PLAYED):
			# no intervals yet, check whether we should play
			resolved = node.isresolved(self)
			if path is not None and resolved is None:
				resolved = gototime
			if resolved is not None:
				if resolved <= gototime:
					self.trigger(gototime, None, node, path, resolved)
				else:
					self.parent.enterabs(resolved, 0, self.trigger, (resolved, None, node, path, resolved))
				self.sched_arcs(node, gototime, 'begin', timestamp = resolved)

	def cancel_gensr(self, node):
		# cancel the SCHED_DONE that was added by gensr_child()
		# but only if the node never played
		if __debug__:
			if debugevents: print 'cancel_gensr',`node`
		ev = (SR.SCHED_DONE, node)
		if node.playing == MMStates.IDLE and \
		   self.srdict.has_key(ev):
			for e, s in self.srdict.items():
				numac = s[e]
				if numac is None:
					continue
				if ev in numac[1]:
					return
			if __debug__:
				if debugevents: print 'canceling SCHED_DONE',`node`
			srdict = self.srdict[ev]
			val = srdict[ev]
			del self.srdict[ev]
			srdict[ev] = None
			if val is not None:
				num, srlist = val
				num = num - 1
				if num > 0:
					val[0] = num
			del node.GetSchedParent().srdict[ev]

	def do_terminate(self, node, curtime, timestamp, fill = 'remove', cancelarcs = 0, chkevent = 1, skip_cancel = 0, ignore_erase = 0):
		parent = self.parent
		if __debug__:
			if debugevents: print 'do_terminate',node,curtime,timestamp,fill,parent.timefunc()
			if debugdump: parent.dump()
		try:
			if node.__terminating:
				if __debug__:
					if debugevents: print 'recursive terminate',node
				return
		except AttributeError:
			pass
		node.__terminating = 1
		if fill != 'remove' and node.GetSchedParent() is None:
			fill = 'remove'
		if not ignore_erase and MMAttrdefs.getattr(node, 'erase') == 'never':
			fill = 'freeze'
			self.erase_chan[node.GetChannelName()] = node
		self.cancel_gensr(node)
		if not skip_cancel:
			for arc in node.durarcs + node.GetEndList():
				if arc.qid is not None:
					if __debug__:
						if debugevents: print 'cancel',`arc`,parent.timefunc()
					self.cancelarc(arc, timestamp, not cancelarcs)
##					if __debug__:
##						if debugevents: print 'scheduled_children-1 h',`arc.dstnode`,arc.dstnode.scheduled_children,parent.timefunc()
##					arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
		if fill == 'remove' and node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN, MMStates.PLAYED):
##			for arc in node.delayed_arcs:
##				if __debug__:
##					if debugevents: print 'scheduled_children-1 i',`arc.dstnode`,arc.dstnode.scheduled_children,parent.timefunc()
##				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
##			node.delayed_arcs = []
			getchannelfunc = node.context.getchannelbynode
			if node.type in playtypes and getchannelfunc:
				xnode = node
				if isinstance(xnode, MMNode.MMNode_body):
					xnode = xnode.parent
				chan = getchannelfunc(xnode)
				if chan:
					if __debug__:
						if debugevents: print 'stopplay',`node`,parent.timefunc()
					chan.stopplay(xnode, curtime)
					self.sched_arcs(xnode, curtime, 'endEvent', timestamp = curtime)
			if node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
				if node.playing == MMStates.FROZEN:
					node.time_list[-1] = node.time_list[-1][0], node.time_list[-1][1], timestamp
				else:
					node.time_list[-1] = node.time_list[-1][0], timestamp, timestamp
				for c in [node.looping_body_self,
					  node.realpix_body,
					  node.caption_body] + \
					 node.GetSchedChildren():
					if c is None:
						continue
					c.has_min = 0 # just to be sure
					self.do_terminate(c, curtime, timestamp, fill=fill, cancelarcs=cancelarcs)
					if not parent.playing:
						node.__terminating = 0
						return
				node.stopplay(timestamp)
				node.cleanup_sched(parent)
##				for c in node.GetSchedChildren():
##					c.resetall(parent)
		elif fill != 'remove' and node.playing in (MMStates.PLAYING, MMStates.PAUSED):
			self.freeze_play(node, curtime, timestamp)
			if not parent.playing:
				node.__terminating = 0
				return
		pnode = node.GetSchedParent()
		if pnode is not None and \
		   pnode.type == 'excl' and \
		   node in pnode.pausestack:
			pnode.pausestack.remove(node)
		paused = parent.paused
		parent.paused = 0
		self.flushqueue(curtime, 1)
		if not parent.playing:
			node.__terminating = 0
			return
		parent.paused = paused
		ev = (SR.SCHED_STOPPING, node)
		if chkevent and self.srdict.has_key(ev):
			for q in self.queue + parent.runqueues[PRIO_INTERN]:
				if q[:3] == (self, ev, 0):
					# already queued
					break
			else:
				# not yet queued
				if __debug__:
					if debugevents: print 'queueing',SR.ev2string(ev), timestamp, parent.timefunc()
				adur = node.calcfullduration(self)
				if node.fullduration is None or adur is None or adur < 0:
					if node.has_min:
						ts = max(timestamp, node.start_time + node.has_min)
					else:
						ts = timestamp
					self.sched_arcs(node, curtime, 'end', timestamp=ts)
				if not node.has_min:
					parent.event(self, ev, timestamp)
		if fill == 'remove':
			ev = (SR.SCHED_STOP, node)
			if self.srdict.has_key(ev):
				parent.event(self, ev, timestamp)
				for e, srdict in self.srdict.items():
					srlist = srdict[e][1]
					if ev in srlist:
						srlist.remove(ev)
		if cancelarcs:
			for qid in parent.queue[:]:
				time, priority, action, argument = qid
				if action != self.trigger:
					continue
				arc = argument[1]
				if arc.srcnode is node and arc.getevent() == 'end':
					if __debug__:
						if debugevents: print 'do_terminate: cancel',`arc`,parent.timefunc()
					self.cancelarc(arc, timestamp)
		# now that this node is done, schedule its next interval (if any)
		mint = None
		for arc in node.FilterArcList(node.GetBeginList()):
			if arc.isresolved(self):
				t = arc.resolvedtime(self)
				if t > timestamp:
					if mint is None or mint[0] < t:
						mint = t, arc
		if mint is not None:
			t, arc = mint
			self.sched_arc(node, arc, curtime, 'begin', timestamp = t - arc.delay, force = 1)
		node.__terminating = 0
		if __debug__:
			if debugevents: print 'do_terminate: return',node

	# callback from channel to indicate that a transition finished
	# on a region overlapping with this node's region, so we must
	# terminate this node if it was frozen with fill="transition"
	def transitiondone(self, node, curtime):
		if node.playing == MMStates.FROZEN and node.GetFill() == 'transition':
			self.do_terminate(node, curtime, self.parent.timefunc())

	def flushqueue(self, curtime, xxx = 0):
		parent = self.parent
		if __debug__:
			if debugevents: print 'flushqueue',curtime,parent.timefunc()
		while 1:
			while self.queue:
				action = self.queue[0]
				if not parent.playing:
					break
				if xxx and action[1][0] == SR.LOOPRESTART:
					return
				del self.queue[0]
				ts = None
				if len(action) > 3:
					ts = action[3]
					action = action[:3]
				parent.runone(action, curtime, ts)
			self.queue = parent.selectqueue()
			if not self.queue:
				break
		if __debug__:
			if debugevents: print 'flushqueue return'

	def freeze_play(self, node, curtime, timestamp = None):
		parent = self.parent
		if __debug__:
			if debugevents: print 'freeze_play',`node`,curtime,parent.timefunc()
		if node.playing in (MMStates.PLAYING, MMStates.PAUSED):
			getchannelfunc = node.context.getchannelbynode
			if node.type in playtypes and getchannelfunc:
				xnode = node
				if isinstance(xnode, MMNode.MMNode_body):
					xnode = xnode.parent
				chan = getchannelfunc(xnode)
				if chan:
					if __debug__:
						if debugevents: print 'freeze',`node`,parent.timefunc()
					chan.freeze(xnode, curtime)
					self.sched_arcs(xnode, curtime, 'endEvent', timestamp = curtime)
			for c in node.GetSchedChildren():
				self.do_terminate(c, curtime, timestamp, fill = 'freeze')
				if not parent.playing:
					return
			node.time_list[-1] = node.time_list[-1][0], timestamp, node.time_list[-1][2]
			node.playing = MMStates.FROZEN
			node.set_armedmode(ARM_WAITSTOP)

	def do_pause(self, pnode, node, action, timestamp):
		if __debug__:
			if debugevents: print 'pause',node,timestamp,self.parent.timefunc()
		if node in pnode.pausestack:
			pnode.pausestack.remove(node)
		if node.playing in (MMStates.IDLE, MMStates.PLAYED):
			for i in range(len(pnode.pausestack)):
				pcmp, p1, p2 = pnode.pausestack[i].PrioCompare(node)
				if pcmp > 0:
					pnode.pausestack.insert(i, node)
					break
			else:
				pnode.pausestack.append(node)
		else:
			self.pause_play(node, action, timestamp)
			for i in range(len(pnode.pausestack)):
				pcmp, p1, p2 = pnode.pausestack[i].PrioCompare(node)
				if pcmp >= 0:
					pnode.pausestack.insert(i, node)
					break
			else:
				pnode.pausestack.append(node)

	def pause_play(self, node, action, timestamp):
		if node.playing not in (MMStates.PLAYING, MMStates.FROZEN):
			return
		for arc in node.durarcs:
			if arc.qid is not None:
				arc.paused = arc.qid[0] - timestamp
				self.cancelarc(arc, timestamp)
				if __debug__:
					if debugevents: print 'pause_play',`arc`,arc.paused,self.parent.timefunc()
		getchannelfunc = node.context.getchannelbynode
		if node.type in playtypes and getchannelfunc:
			xnode = node
			if isinstance(xnode, MMNode.MMNode_body):
				xnode = xnode.parent
			chan = getchannelfunc(xnode)
			if chan:
				if __debug__:
					if debugevents: print 'freeze',`node`,self.parent.timefunc()
				chan.pause(xnode, action, timestamp)
		for c in node.GetSchedChildren():
			self.pause_play(c, action, timestamp)
		node.playing = MMStates.PAUSED
		node.set_armedmode(ARM_PAUSING)

	def do_resume(self, node, curtime, timestamp):
		if __debug__:
			if debugevents: print 'resume',node,timestamp,self.parent.timefunc()
		ev = (SR.SCHED, node)
		if self.srdict.has_key(ev):
			node.set_start_time(timestamp, 0)
			self.sched_arcs(node, curtime, 'begin', timestamp=timestamp)
			self.parent.event(self, ev, timestamp)
		else:
			self.resume_play(node, curtime, timestamp)

	def resume_play(self, node, curtime, timestamp):
		if node.playing != MMStates.PAUSED:
			return
		parent = self.parent
		if node.playing != MMStates.FROZEN:
			for arc in node.durarcs:
				if arc.qid is None and hasattr(arc, 'paused'):
					arc.qid = parent.enterabs(timestamp + arc.paused, 0, self.trigger, (curtime,arc,None,None,timestamp + arc.paused))
##					print 'set timestamp b',arc,timestamp + arc.paused
					arc.timestamp = timestamp + arc.paused
					del arc.paused
		getchannelfunc = node.context.getchannelbynode
		if node.type in playtypes and getchannelfunc:
			xnode = node
			if isinstance(xnode, MMNode.MMNode_body):
				xnode = xnode.parent
			chan = getchannelfunc(xnode)
			if chan:
				if __debug__:
					if debugevents: print 'resume play',`node`,parent.timefunc()
				chan.resume(xnode, timestamp)
		if node.type == 'excl':
			for c in node.GetSchedChildren():
				if c.playing == MMStates.PAUSED and \
				   c not in node.pausestack:
					self.resume_play(c, curtime, timestamp)
		else:
			for c in node.GetSchedChildren():
				self.resume_play(c, curtime, timestamp)
		node.playing = MMStates.PLAYING
		node.set_armedmode(ARM_PLAYING)

	def queuesrlist(self, srlist, timestamp = None):
		for sr in srlist:
			if __debug__:
				if debugevents: print '  queue', SR.ev2string(sr), timestamp,self.parent.timefunc()
			if sr[0] == SR.PLAY:
				prio = PRIO_START
			elif sr[0] == SR.PLAY_STOP:
				prio = PRIO_STOP
			else:
				prio = PRIO_INTERN
			self.parent.add_runqueue(self, prio, sr, timestamp)
	#
	def play_done(self, node, curtime, timestamp = None):
		return
		if node.GetTerminator() == 'MEDIA' and \
		   not node.attrdict.has_key('duration') and \
		   not node.FilterArcList(node.GetEndList()):
			if node.has_min:
				if __debug__:
					if debugevents: print 'play_done: delaying',node,timestamp
				node.delayed_play_done = 1
			else:
				self.parent.event(self, (SR.SCHED_STOPPING, node.looping_body_self or node), timestamp)
				self.parent.updatetimer(curtime) # ???

	#
	def anchorfired(self, node, arg):
		return self.parent.anchorfired(self, node, arg)
	#
	# Partially handle an event, updating the internal queues and
	# returning executable SRs, if any.
	#
	def getsrlist(self, ev):
		if __debug__:
			if debugevents: print 'event:', SR.ev2string(ev),self.parent.timefunc()
		try:
			srdict = self.srdict[ev]
			del self.srdict[ev]
		except KeyError:
			if ev[0] == SR.SCHED_STOPPING:
				# XXXX Hack to forestall crash on interior
				# nodes with duration that are terminated:
				# their terminating syncarc is still there...
				if __debug__: print 'Warning: unexpected', SR.ev2string(ev),self.parent.timefunc()
				return []
			raise error, 'Scheduler: Unknown event: %s' % SR.ev2string(ev)
		numsrlist = srdict.get(ev)
		if not numsrlist:
			raise error, 'Scheduler: actions already sched for ev: %s' % ev
		del srdict[ev]
		num, srlist = numsrlist
		num = num - 1
		if num < 0:
			raise error, 'Scheduler: waitcount<0: %s' % (num, srlist)
		elif num == 0:
			numsrlist[:] = []
			return srlist
		else:
			numsrlist[0] = num
		return []


class Scheduler(scheduler):
	def __init__(self, ui):
		# not calling scheduler.__init__ on purpose
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
		self.resettimer()
		self.paused = 0
		# 'inherit' method from parent:
		self.anchorfired = self.ui.anchorfired
##		self.channels_in_use = []

	#
	# Playing algorithm.
	#
	def play(self, node, seek_node, anchor_id, anchor_arg, timestamp=None):
		sctx = SchedulerContext(self, node, seek_node)
		self.sctx_list.append(sctx)
		self.playing = self.playing + 1
		if not sctx.start(seek_node, anchor_arg, timestamp):
			if __debug__:
				if debugevents: print 'Scheduler: play abort',self.timefunc()
			sctx.stop(timestamp)
			return None
		self.starting_to_play = 1
		return sctx
	#
	def _remove_sctx(self, sctx):
		if __debug__:
			if debugevents: print 'Remove:', sctx,self.timefunc()
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
	if __debug__:
		def dump(self):
			print '=============== scheduler dump'
			print '# timed events:', len(self.queue)
			if self.queue:
				print 'current time:',self.timefunc()
				for time, priority, action, argument in self.queue:
					print time, priority, action, argument
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

	def stop_all(self, curtime):
		if __debug__:
			if debugevents: print 'STOP_ALL', self.sctx_list,self.timefunc()
		to_stop = self.sctx_list[:]
		for sctx in to_stop:
			sctx.stop(curtime)
		to_stop = None
		if __debug__:
			if debugevents: print 'Now', self.sctx_list,self.timefunc()
		if __debug__:
			if debugevents: self.dump()
		self.queue = []		# XXX shouldn't be necessary, but it is
		if self.starting_to_play:
			self.starting_to_play = 0
		self.playing = 0
		self.ui.play_done()
		self.toplevel.set_timer(-1, None)

	#
	# The timer callback routine, called via a forms timer object.
	# This is what makes SR's being executed.
	#
	def timer_callback(self, curtime):
		#
		# We have two queues to execute: the timed queue and the
		# normal SR queue. Currently, we execute the timed queue first.
		# Also, we have to choose here between an eager and a non-eager
		# algorithm. For now, we're eager, on both queues.
		#
		if __debug__:
			if debugtimer: print 'timer_callback',self.timefunc()
		if not self.playing:
			return
		now = self.timefunc()
		while self.queue and self.queue[0][0] <= now:
##			self.toplevel.setwaiting()
			when, prio, action, argument = self.queue[0]
			del self.queue[0]
			apply(action, argument)
			if not self.playing:
				return
			now = self.timefunc()
		#
		# Now the normal runqueue
		#
		queue = self.selectqueue()
		if queue:
##			self.toplevel.setwaiting()
			for action in queue:
				timestamp = None
				if len(action) > 3:
					timestamp = action[3]
					action = action[:3]
				self.runone(action, curtime, timestamp)
				if not self.playing:
					return
		self.updatetimer(curtime)
	#
	# FutureWork returns true if any of the scheduler contexts
	# has possible future work. Each context's FutureWork has to be
	# called (since this is also where contexts tell that they are empty).
	#
	def FutureWork(self, curtime):
		has_work = 0
		for sctx in self.sctx_list:
			if sctx.FutureWork(curtime):
				has_work = 1
		return has_work
	#
	# Updatetimer restarts the forms timer object. If we have work to do
	# we set the timeout very short, otherwise we simply stop the clock.
	def updatetimer(self, curtime):
		# Helper variable:
		work = 0
		for q in self.runqueues:
			if q:
				work = 1
				break
		if not self.playing:
			delay = -1
			if __debug__:
				if debugtimer: print 'updatetimer: not playing' #DBG
		elif not self.paused and work:
			#
			# We have SR actions to execute. Make the callback
			# happen as soon as possible.
			#
			delay = 0
			if __debug__:
				if debugtimer: print 'updatetimer: runnable events' #DBG
		elif self.queue and not self.paused:
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
				delay = 0
			if __debug__:
				if debugtimer: print 'updatetimer: timed events' #DBG
		elif not self.FutureWork(curtime):
			#
			# No more events (and nothing runnable either).
			# We're thru.
			#
			if __debug__:
				if debugtimer: print 'updatetimer: no more work' #DBG
			self.stop_all(curtime)
			self.ui.set_timer(0, curtime)
			return
		else:
			#
			# Nothing to do for the moment.
			# Tick every second, so we see the timer run.
			#
			if __debug__:
				if debugtimer:  'updatetimer: idle' #DBG
			self.setpaused(0, curtime, 0)
			return
		if __debug__:
			if debugtimer: print 'updatetimer: delay=', delay
		if delay == 0:
			self.setpaused(1, curtime, 0)
		else:
			self.setpaused(0, curtime, 0)
		self.ui.set_timer(delay, curtime + max(delay, 0))
	#
	# Incoming events from channels, or the start event.
	#
	def event(self, sctx, ev, timestamp):
		if sctx.active:
##			if ev[0] == SR.ARM_DONE:
##				ev[1].set_armedmode(ARM_ARMED)
			sctx.event(ev, timestamp)

	#
	# Add the given SR to one of the runqueues.
	#
	def add_runqueue(self, sctx, prio, sr, timestamp = None):
		self.runqueues[prio].append((sctx, sr, 0, timestamp))

	def add_lopriqueue(self, sctx, time, sr):
		runq = self.runqueues[PRIO_LO]
		for i in range(len(runq)):
			if runq[i][2] > time:
				runq.insert(i, (sctx, sr, time))
				return
		runq.append((sctx, sr, time))

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
		if self.runqueues[PRIO_LO]:
			import windowinterface
			windowinterface.lopristarting()
			# That call may have called callbacks, so we have to check
			# again
		if self.runqueues[PRIO_LO]:
			queue = [self.runqueues[PRIO_LO][0]]
			del self.runqueues[PRIO_LO][0]
			return queue
		#
		# Otherwise we run nothing.
		#
		return []

	def runone(self, (sctx, todo, dummy), curtime, timestamp = None):
		if not sctx.active:
			raise error, 'Scheduler: running from finished context'
		if __debug__:
			if debugevents: print 'exec: ', SR.ev2string(todo), timestamp, self.timefunc()
		if timestamp is None:
			timestamp = self.timefunc()
		action, arg = todo
		if action == SR.LOOPSTART:
			self.do_loopstart(sctx, arg, timestamp)
			arg.looping_body_self.set_start_time(timestamp)
			if arg.type in playtypes:
				self.do_play(sctx, arg.looping_body_self, curtime, timestamp)
			else:
				arg.looping_body_self.startplay(timestamp)
			sctx.sched_arcs(arg.looping_body_self, curtime, 'begin', timestamp=timestamp)
			arg.looping_body_self.loopcount = 0
		elif action == SR.LOOPEND:
			self.do_loopend(sctx, arg, timestamp)
		elif action == SR.LOOPRESTART:
			if self.do_looprestart(sctx, arg, curtime, timestamp):
				arg.looping_body_self.set_start_time(timestamp)
				if arg.type in playtypes:
					self.do_play(sctx, arg.looping_body_self, curtime, timestamp)
				else:
					arg.looping_body_self.startplay(timestamp)
				sctx.sched_arcs(arg.looping_body_self, curtime, 'begin', timestamp=timestamp)
				arg.looping_body_self.loopcount = arg.looping_body_self.loopcount + 1
				sctx.sched_arcs(arg, curtime, 'repeat(%d)' % arg.looping_body_self.loopcount, timestamp = curtime)
				sctx.sched_arcs(arg, curtime, 'repeatEvent', timestamp = curtime)
		elif action == SR.SCHED_STOPPING:
			if arg.scheduled_children or arg.has_min:
				if __debug__:
					if debugevents: print 'not stopping',`arg`,arg.scheduled_children,self.timefunc()
				return
			if arg.starting_children > 0 and arg.GetTerminator() == 'LAST':
				if __debug__:
					if debugevents: print 'not stopping (scheduled children)',`arg`,arg.starting_children,self.timefunc()
				return
			if arg.type in interiortypes and \
			   arg.playing != MMStates.PLAYED and \
			   (arg.attrdict.get('duration') is not None or
			    arg.attrdict.get('end') is not None):
				if __debug__:
					if debugevents: print 'not stopping (dur/end)',`arg`,self.timefunc()
				return
			pnode = arg.GetSchedParent()
			if pnode is not None and pnode.GetType() == 'excl' and pnode.pausestack and arg not in pnode.pausestack:
				nnode = pnode.pausestack[0]
				del pnode.pausestack[0]
				sctx.do_terminate(arg, curtime, timestamp)
				if not self.playing:
					return
				sctx.do_resume(nnode, curtime, timestamp)
			elif arg.GetFill() == 'remove':
				for ch in arg.GetSchedChildren():
					sctx.do_terminate(ch, curtime, timestamp, chkevent = 0)
					if not self.playing:
						return
			else:
				sctx.do_terminate(arg, curtime, timestamp, fill = arg.GetFill(), chkevent = 0)
				if not self.playing:
					return
			adur = arg.calcfullduration(self)
			if arg.fullduration is None or adur is None or adur < 0:
				if arg.has_min:
					timestamp = max(timestamp, arg.start_time + arg.has_min)
				sctx.sched_arcs(arg, curtime, 'end', timestamp=timestamp)
			sctx.event((action, arg), timestamp)
		elif action == SR.SCHED_START:
			if arg.isresolved(sctx) is not None:
				arg.set_start_time(timestamp)
				if arg.type in playtypes and arg.looping_body_self is None:
					self.do_play(sctx, arg, curtime, timestamp)
				else:
					arg.startplay(timestamp)
				if not self.playing:
					return
				sctx.sched_arcs(arg, curtime, 'begin', timestamp=timestamp)
##				adur = arg.calcfullduration(self)
##				if arg.fullduration is not None and adur is not None and adur >= 0:
##					sctx.sched_arcs(arg, curtime, 'end', timestamp=timestamp+adur)
			sctx.event((action, arg), timestamp)
		elif action == SR.SCHED_STOP:
			if __debug__:
				if debugevents: print 'cleanup',`arg`,self.timefunc()
			arg.cleanup_sched(self)
			sctx.event((action, arg), timestamp)
		else:
			sctx.event((action, arg), timestamp)

	#
	# Execute a PLAY SR.
	#
	def do_play(self, sctx, node, curtime, timestamp):
		if __debug__:
			if debugevents: print 'do_play',`node`,node.start_time, curtime, timestamp,self.timefunc()
		if self.starting_to_play:
			self.starting_to_play = 0
		xnode = node
		if isinstance(xnode, MMNode.MMNode_body):
			xnode = xnode.parent
		n = sctx.erase_chan.get(node.GetChannelName())
		if n is not None:
			sctx.do_terminate(n, curtime, timestamp, ignore_erase = 1)
			del sctx.erase_chan[node.GetChannelName()]
		chan = self.ui.getchannelbynode(xnode)
		if chan not in sctx.channels:
			sctx.channels.append(chan)
			chan.startcontext(sctx)
		node.startplay(timestamp)
##		sctx.sched_arcs(node, curtime, 'begin', timestamp = timestamp)
##		ndur = node.calcfullduration(self)
##		if ndur is not None and ndur >= 0:
##			sctx.sched_arcs(node, curtime, 'end', timestamp = timestamp+ndur)
		sctx.sched_arcs(node, curtime, 'beginEvent', timestamp = curtime)
		chan.play(xnode, curtime)

	#
	# LOOPSTART SR - Enter a loop at the top.
	# (resets loopcounter to initial value and generates LOOPSTART_DONE)
	#
	def do_loopstart(self, sctx, node, timestamp):
##		print 'LOOPSTART', node
		if not node.moreloops(decrement=1):
			raise error, 'Loopstart without more loops!'
		self.event(sctx, (SR.LOOPSTART_DONE, node), timestamp)

	#
	# LOOPEND SR - End of loop. Either loop once more or continue
	#
	def do_loopend(self, sctx, node, timestamp):
##		print 'LOOPEND', node
		if node.moreloops():
			#
			# This is tricky. We first have to do the SCHED_STOP
			# actions (stopping all descendents, probably), and
			# only after that we can re-install the new srlist
			# and go back into the loop. We do this by scheduling
			# scheduling the (pseudo-) sr LOOPRESTART in a low
			# priority queue. do_looprestart will then be
			# called after all the cleaun actions.
			#
##			print 'MORE TO PLAY'
##			self.add_runqueue(sctx, PRIO_INTERN,
##					  (SR.SCHED_STOP, node))
			self.add_runqueue(sctx, PRIO_START,
					  (SR.LOOPRESTART, node), timestamp)
		else:
##			print 'NO MORE TO PLAY'
			self.event(sctx, (SR.LOOPEND_DONE, node), timestamp)
	#
	# LOOPRESTART - Regenerate loop events and restart
	#
	def do_looprestart(self, sctx, node, curtime, timestamp):
##		print 'LOOPRESTART', node
		if not node.moreloops(decrement=1):
			# Node has been terminated in the mean time
			self.event(sctx, (SR.LOOPEND_DONE, node), timestamp)
			return 0
		sctx.restartloop(node, curtime)
		self.event(sctx, (SR.LOOPSTART_DONE, node), timestamp)
		return 1
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
		if __debug__:
			if debugevents: print 'enterabs',time,priority,action,argument,self.timefunc()
		id = scheduler.enterabs(self, time, priority, action, argument)
		return id

	def timefunc(self):
		if self.__paused:
			return self.time_pause - self.time_origin
		return time.time() - self.time_origin

	def resettimer(self, starttime = 0):
		self.time_origin = time.time() - starttime
		self.time_pause = self.time_origin + starttime
		self.__paused = 1

	def getpaused(self):
		return self.paused

	def settime(self, timestamp):
		if __debug__:
			if debugevents: print 'settime',timestamp
		if self.__paused:
			self.time_origin = self.time_pause - timestamp
		else:
			self.time_origin = time.time() - timestamp

	def setpaused(self, paused, curtime = None, propagate = 1):
		if curtime is None:
			curtime = self.timefunc()
		if self.__paused != paused and (paused or propagate or not self.paused):
			if not paused:
				# continue playing
				if __debug__:
					if debugevents: print 'continuing', propagate, self.time_pause - self.time_origin
				# subtract time paused
				self.time_origin = self.time_origin + \
						   (time.time()-self.time_pause)
			else:
				# remember time paused
				self.time_pause = time.time()
				if __debug__:
					if debugevents: print 'pausing', propagate, self.time_pause - self.time_origin
			self.__paused = paused
		if not propagate:
			return
		if self.paused != paused:
			self.paused = paused
			for sctx in self.sctx_list:
				sctx.setpaused(paused)
			self.updatetimer(curtime)

class ArmStorageTree:
	def __init__(self, node):
		self.children = []
		self.index = 0
		self.parent = None
		self.node = node
		self.onemoretime = 0

	def setparents(self):
		# Last stage of tree buildup: link children back to parent
		for c in self.children:
			c.parent = self

	def destroy(self):
		# Destroy the whole tree starting at any node
		if self.parent:
			raise error, 'Destroy with parent!'
		for c in self.children:
			c.parent = None
			c.destroy()
		del self.parent
		del self.children

	def cancel(self, node):
		# Cancel arms for node and descendents, knowing that
		# node is currently active (so somewhere between current and
		# root)
		if node == self.node:
			self.do_cancel()
		elif self.parent:
			self.parent.cancel(node)

	def do_cancel(self):
		# Cancel arm for this node and its descendents
		self.index = len(self.children)+1
		self.onemoretime = 0
		for ch in self.children[self.index:]:
			ch.do_cancel()

	def next(self):
		# Return next ArmStorage to query and next node to arm
		if self.index >= len(self.children) and self.onemoretime:
##			print 'ONEMOREARM', self.node
			for ch in self.children:
				ch.do_looponcemore()
			self.onemoretime = 0
			self.index = 0
		if self.index < len(self.children):
			self.index = self.index + 1
			return self.children[self.index-1].next()
		if not self.parent:
			return self, None
		# Remove ourselves if we're empty anyway
		parent = self.parent
##		if len(self.children) == 0:
##			self.parent.children.remove(self)
##			self.parent = None
		return parent.next()

	def append(self, x):
		self.children.append(x)

	def isempty(self):
		return len(self.children) == 0

	def looponcemore(self, node):
		if self.node == node:
			self.do_looponcemore()
		else:
			for ch in self.children:
				ch.looponcemore(node)

	def do_looponcemore(self):
##		print 'LOOPONCEMORE', self.node
		self.onemoretime = 1
##		for ch in self.children:
##			ch.do_looponcemore()

	def root(self):
		if self.parent:
			return self.parent.root()
		return self

class ArmStorageLeaf:
	def __init__(self, node):
		self.node = node
		self.parent = None

	def destroy(self):
		del self.parent
		del self.node

	def root(self):
		return self

	def do_cancel(self):
		print 'CANCELARM', self.node
		pass

	def do_revive(self):
		pass

	def next(self):
		node = self.node
		return self.parent, node

	def isempty(self):
		return 0

	def looponcemore(self, node):
		pass

	def do_looponcemore(self):
		pass

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
		unarmallnodes(child)

