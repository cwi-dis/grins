__version__ = "$Id$"

# Scheduler - The scheduler for playing cmif documents.

import time
from sched import scheduler
from MMExc import *
import MMAttrdefs
import MMNode
from MMTypes import *
from ArmStates import *
from HDTL import HD, TL
from AnchorDefs import *
import SR
import settings
import MMStates

debugtimer = 0
debugevents = 0
debugdump = 0

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
		self.playroot = MMNode.FakeRootNode(node)
		#self.parent.ui.duration_ind.label = '??:??'

		self.prepare_minidoc(seeknode)
		if debugdump:self.dump()


	#
	# stop - cleanup SchedulerContext.
	#
	def stop(self):
		if not self.active:
			return
		self.active = 0
		self.stopcontextchannels()
		self.srdict = {}
		self.parent._remove_sctx(self)
		self.playroot.resetall(self.parent)
		del self.parent
		del self.playroot

	#
	# Dump - Dump a scheduler context
	#
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
	def stopcontextchannels(self):
		for ch in self.channels:
			ch.stopcontext(self)
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
	def FutureWork(self):
		if self.srdict or self.scheduled_children:
			return 1
		self.parent.ui.sctx_empty(self) # XXXX
		return 0
	#
	# Initialize SR actions and events before playing
	#
	def prepare_minidoc(self, seeknode):
		self.srdict = self.playroot.GenAllSR(seeknode, sctx = self, curtime = self.parent.timefunc())
	#
	# Re-initialize SR actions and events for a looping node, preparing
	# for the next time through the loop
	#
	def restartloop(self, node):
		if debugdump: self.dump()
		srdict = node.GenLoopSR(self, self.parent.timefunc())
		for key, value in srdict.items():
			if self.srdict.has_key(key):
				raise error, 'Duplicate event '+SR.ev2string(key)
			self.srdict[key] = value
	#
	# Start minidoc starts playing what we've prepared
	#
	def start(self, s_node, s_aid, s_args, timestamp = None):
		if debugevents: print 'SchedulerContext.start',`self`, `s_node`, `s_aid`, `s_args`, timestamp, self.parent.timefunc()
		self.startcontextchannels()
		if s_node and s_aid:
			self.seekanchor(s_node, s_aid, s_args)
		playroot = self.playroot
		if timestamp is None:
			timestamp = self.parent.timefunc()
		playroot.set_start_time(timestamp)

		self.parent.event(self, (SR.SCHED, self.playroot), timestamp)
##		self.parent.updatetimer()
		return 1
	#
	# Seekanchor indicates that we are playing here because of the
	# anchor specified.
	#
	def seekanchor(self, node, aid, aargs):
		if isinstance(node, MMNode.MMNode_body):
			node = node.parent
		chan = self.parent.ui.getchannelbynode(node)
		if chan:
			chan.seekanchor(node, aid, aargs)
	#
	# Incoming events from channels, or the start event.
	#
	def event(self, ev, timestamp):
		if debugevents: print 'event', SR.ev2string(ev), timestamp, self.parent.timefunc()
		srlist = self.getsrlist(ev)
		self.queuesrlist(srlist, timestamp)

	def sched_arc(self, node, arc, event = None, marker = None, timestamp = None):
		# Schedules a single SyncArc for a node.
		
		# node is the node for the start of the arc.
		# arc is the SyncArc
		# event is the event 
		# marker is ?
		# timestamp is the time.. now.

		if debugevents: print 'sched_arc',`node`,`arc`,event,marker,timestamp,self.parent.timefunc()
		if arc.wallclock is not None:
			timestamp = arc.resolvedtime(self)-arc.delay
		if arc.ismin:
			list = []
		elif arc.isstart:
			dev = 'begin'
			list = arc.dstnode.GetBeginList()
			list = []
		else:
			if event is not None and event not in ('begin', 'end'):
				# a real event, only does something when node is active
				if arc.dstnode.playing in (MMStates.IDLE, MMStates.PLAYED):
					return
			dev = 'end'
			list = arc.dstnode.GetEndList()
			list = list + arc.dstnode.durarcs
		if arc.timestamp is not None and arc.timestamp != timestamp+arc.delay:
			if arc.qid is not None:
				if debugevents: print 'sched_arc: cancel',`arc`,self.parent.timefunc()
				self.cancelarc(arc, timestamp)
		for a in list:
			if a.qid is None:
				continue
			if a.ismin:
				continue
			if a.timestamp > timestamp + arc.delay:
				if debugevents: print 'sched_arc: cancel',`a`,self.parent.timefunc()
				self.cancelarc(a, timestamp)
				if a.isstart:
					if a.dstnode.GetSchedParent():
						srdict = a.dstnode.GetSchedParent().gensr_child(a.dstnode, runchild = 0, sctx = self, curtime = self.parent.timefunc())
						self.srdict.update(srdict)
						if debugevents: print 'scheduled_children-1 a',`a.dstnode`,`a`,event,a.dstnode.scheduled_children,self.parent.timefunc()
						a.dstnode.scheduled_children = a.dstnode.scheduled_children - 1
					else:
						# root node
						self.scheduled_children = self.scheduled_children - 1
				else:
					if debugevents: print 'scheduled_children-1 b',`a.dstnode`,`a`,event,a.dstnode.scheduled_children,self.parent.timefunc()
					a.dstnode.scheduled_children = a.dstnode.scheduled_children - 1
		if arc.qid is None:
			if arc.isstart:
				if arc.dstnode.GetSchedParent():
					srdict = arc.dstnode.GetSchedParent().gensr_child(arc.dstnode, runchild = 0, sctx = self, curtime = self.parent.timefunc())
					self.srdict.update(srdict)
					if debugevents: print 'scheduled_children+1 c',`arc.dstnode`,`arc`,event,arc.dstnode.scheduled_children,self.parent.timefunc()
					arc.dstnode.scheduled_children = arc.dstnode.scheduled_children + 1
				else:
					# root node
					self.scheduled_children = self.scheduled_children + 1
			else:
				if debugevents: print 'scheduled_children+1 d',`arc.dstnode`,`arc`,event,arc.dstnode.scheduled_children,self.parent.timefunc()
				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children + 1
			arc.timestamp = timestamp + arc.delay
			if not arc.isstart and not arc.ismin and arc.srcnode is arc.dstnode and arc.event == 'begin':
				# end arcs have lower priority than begin arcs
				# this is important to get proper freeze
				# behavior in constructs such as
				# <par>
				#   <par>
				#     <img .../>
				#   </par>
				#   <video .../>
				# </par>
				prio = 1
			else:
				prio = 0
			arc.qid = self.parent.enterabs(arc.timestamp, prio, self.trigger, (arc,))
			if arc.isstart:
				arc.dstnode.set_start_time(arc.timestamp, 0)
				arc.dstnode.depends['begin'].append(arc)
			else:
				arc.dstnode.depends['end'].append(arc)
			if node.deparcs.has_key(event) and arc not in node.deparcs[event]:
				node.deparcs[event].append(arc)
				arc.depends.append((node, event))
		if not arc.ismin and (arc.dstnode is not node or dev != event):
			ts = timestamp+arc.delay
			if arc.dstnode.has_min and dev == 'end':
				# maybe delay dependent sync arcs
				mintime = arc.dstnode.GetMin()
				ts = max(ts, arc.dstnode.start_time + mintime)
			self.sched_arcs(arc.dstnode, dev, timestamp=ts)

	def sched_arcs(self, node, event = None, marker = None, timestamp = None):
		# Schedules all event-based syncarcs for a single node.
		# Note that syncarcs that can be derived from the node structure (i.e. start and end of nodes)
		# are made already in SMILTreeRead and are accessable in MMNode via the 'beginlist' and 'endlist'
		# attrs.

		# node is the node.
		# event is a tuple of (event, ?, ((channel, event)|accesskey))
		# marker is (?)
		# timestamp is the time "now".

		if debugevents: print 'sched_arcs',`node`,event,marker,timestamp,self.parent.timefunc()
		if timestamp is None:	# Retrieve the timestamp if it was not supplied.
			timestamp = self.parent.timefunc()
		channel = accesskey = None
		if event is not None:	# Retrieve the event if it was not supplied.
			node.event(timestamp, event)
			if type(event) is type(()): # If the event is an empty tuple.
				if event[1] == 'accesskey': # If the event was from a keypress
					accesskey = event[2]
					event = None
				else:
					channel, event = event[:2]
		if marker is not None:
			node.marker(timestamp, marker)

		# Iterate through the scheduled syncarcs for this node
		for arc in node.sched_children:	# for all the scheduled children of that node.
					# for a node, the scheduled children is a list of MMSyncArcs
			if (arc.channel != channel or # If none of these conditions match, try the next node.
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
			       (event != 'end' or arc.dstnode in node.GetSchedChildren()))):
				continue
			do_continue = 0
			try:
				if arc.__in_sched_arcs:
					# loop in syncarcs
					if debugevents: print 'break syncarc loop',arc
					do_continue = 1
			except AttributeError:
				pass
			else:
				if do_continue:
					continue
			arc.__in_sched_arcs = 1	# to break recursion
			atime = 0
			if arc.srcanchor is not None:
				for a in node.attrdict.get('anchorlist', []):
					if a.aid == arc.srcanchor:
						if event == 'end':
							atime = a.atimes[1]
						else:
							atime = a.atimes[0]
						break
			self.sched_arc(node, arc, event, marker, timestamp+atime)
			arc.__in_sched_arcs = 0
		if debugevents: print 'sched_arcs return',`node`,event,marker,timestamp,self.parent.timefunc()

	def trigger(self, arc, node = None, path = None, timestamp = None):
		# Triggers a single syncarc.

		# if arc == None, arc is not used, but node and timestamp are
		# if arc != None, arc is used, and node and timestamp are not
		parent = self.parent
		if debugevents: print 'trigger',`arc`,`node`,`path`,timestamp,parent.timefunc()
		paused = parent.paused
		parent.paused = 0
		self.flushqueue()
		if not parent.playing:
			return
		parent.paused = paused

		if arc is not None:
			if arc.qid is None:
				if debugevents: print 'trigger: ignore arc',`arc`
				parent.updatetimer()
				return
			if arc.qid and parent.queue and parent.queue[0][:2] < arc.qid[:2]:
				# a higher priority element has cropped up in
				# the queue: reinsert this one so that the
				# other one can be handled first
				arc.qid = parent.enterabs(arc.qid[0], arc.qid[1], self.trigger, (arc,))
				parent.updatetimer()
				return
			if arc.getevent() == 'end' and arc.refnode().playing == MMStates.IDLE:
				if debugevents: print 'ignoring',arc
				self.cancelarc(arc, timestamp, propagate = 1)
				parent.updatetimer()
				return
			for nd, ev in arc.depends:
				try:
					nd.deparcs[ev].remove(arc)
				except ValueError:
					pass
			arc.depends = []
			timestamp = arc.resolvedtime(self)
			node = arc.dstnode
			arc.qid = None
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
				if debugevents: print 'scheduled_children-1 e',`node`,`arc`,node.scheduled_children,parent.timefunc()
				node.scheduled_children = node.scheduled_children - 1
				while node.delayed_arcs:
					arc = node.delayed_arcs[0]
					del node.delayed_arcs[0]
					arc.qid = 0
					self.trigger(arc)
				if node.scheduled_children > 0:
					parent.updatetimer()
					return
				# if there is a SCHED_STOPPING event on the
				# right-hand side in the srdict, don't stop
				for ev, srdict in self.srdict.items():
					numac = srdict[ev]
					if numac is None:
						continue
					for ac in numac[1]:
						op, nd = ac
						if op == SR.SCHED_STOPPING and nd == node:
							if debugevents: print 'trigger: not stopping (ismin)'
							return
			if arc.isstart:
				if pnode:
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
				if node.has_min:
					# must delay this arc
					node.delayed_arcs.append(arc)
					if arc in node.durarcs:
						self.do_terminate(node, timestamp, fill = node.GetFill())
					parent.updatetimer()
					return
				if debugevents: print 'scheduled_children-1 g',`node`,`arc`,node.scheduled_children,parent.timefunc()
				if node.scheduled_children > 0:
					node.scheduled_children = node.scheduled_children - 1
				if node.playing not in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
					# ignore end event if not playing
					if debugevents: print 'node not playing',parent.timefunc()
					node.endtime = (timestamp, arc.getevent())
					parent.updatetimer()
					return
				if debugevents: print 'terminating node',parent.timefunc()
				if pnode is not None and \
				   pnode.type == 'excl' and \
				   pnode.pausestack and \
				   node not in pnode.pausestack:
					nnode = pnode.pausestack[0]
					del pnode.pausestack[0]
					self.do_terminate(node, timestamp)
					if not parent.playing:
						return
					self.do_resume(nnode, timestamp)
				else:
					self.do_terminate(node, timestamp, fill = node.GetFill())
					self.flushqueue()
				parent.updatetimer()
				return
		if not pnode:
			self.scheduled_children = self.scheduled_children - 1
		if not pnode or pnode.playing != MMStates.PLAYING:
			# ignore event when node can't play
			if debugevents: print 'parent not playing',parent.timefunc()
			parent.updatetimer()
			return
		# ignore restart attribute on hyperjump (i.e. when arc is None)
		if arc is not None and \
		   ((node.playing in (MMStates.PLAYING, MMStates.PAUSED) and
		     node.GetRestart() != 'always') or
		    (node.playing in (MMStates.FROZEN, MMStates.PLAYED) and
		     node.GetRestart() == 'never')):
			# ignore event when node doesn't want to play
			if debugevents: print "node won't restart",parent.timefunc()
			self.cancelarc(arc, timestamp)
			parent.updatetimer()
			return
		endlist = node.GetEndList()
		equal = 0
		if endlist:
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
					if ats > timestamp:
						found = 1
					elif ats == timestamp:
						equal = 1
						found = 1
						break
			if not found:
				if debugevents: print 'not allowed to start',parent.timefunc()
				srdict = pnode.gensr_child(node, runchild = 0, sctx = self, curtime = parent.timefunc())
				self.srdict.update(srdict)
				ev = (SR.SCHED_DONE, node)
				if debugevents: print 'trigger: queueing',SR.ev2string(ev), timestamp, parent.timefunc()
				parent.event(self, ev, timestamp)
				parent.updatetimer()
				return
		# if node is playing (or not stopped), must terminate it first
		if node.playing not in (MMStates.IDLE, MMStates.PLAYED):
			if debugevents: print 'terminating node',parent.timefunc()
			pnode.scheduled_children = pnode.scheduled_children + 1
			self.do_terminate(node, timestamp)
			if not parent.playing:
				return
			self.flushqueue()
			self.sched_arcs(node, 'begin', timestamp=timestamp)
			pnode.scheduled_children = pnode.scheduled_children - 1
		if pnode.type == 'excl':
			action = 'nothing'
			for sib in pnode.GetSchedChildren():
				if sib is node:
					continue
				if sib.playing == MMStates.PLAYING:
					# found a playing sibling,
					# check priorityClass stuff
					pcmp, p1, p2 = sib.PrioCompare(node)
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
					if debugevents: print 'action',action,parent.timefunc()
					if action == 'stop':
						fill = sib.GetFill()
						if fill != 'hold' and fill != 'transition':
							fill = 'remove'
						self.do_terminate(sib, timestamp, fill = fill)
						if not parent.playing:
							return
					elif action == 'never':
						if arc is not None:
							self.cancelarc(arc, timestamp)
						self.cancel_gensr(node)
						parent.updatetimer()
						return
					elif action == 'defer':
						if node not in pnode.pausestack:
							srdict = pnode.gensr_child(node, sctx = self, curtime = parent.timefunc())
							self.srdict.update(srdict)
						node.set_start_time(timestamp)
						self.do_pause(pnode, node, 'hide', timestamp)
						parent.updatetimer()
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
					self.do_terminate(sib, timestamp, fill = fill)
					if not parent.playing:
						return
					break
		elif pnode.type == 'seq':
			# parent is seq, must terminate running child first
			if debugevents: print 'terminating siblings',parent.timefunc()
			srdict = pnode.gensr_child(node, runchild = 0, sctx = self, curtime = self.parent.timefunc())
			self.srdict.update(srdict)
			for c in pnode.GetSchedChildren():
				# don't have to terminate it again
				if c is not node and c.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
					# if fill="hold", freeze child, otherwise kill
					fill = c.GetFill()
					if fill != 'hold' and fill != 'transition':
						fill = 'remove'
					self.do_terminate(c, timestamp, fill = fill, cancelarcs = arc is None)
					if not parent.playing:
						return
					# there can be only one active child
					break
		paused = parent.paused
		parent.paused = 0
		self.flushqueue()
		if not parent.playing:
			return
		parent.paused = paused
		# we must start the node, but how?
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
		ndur = node.calcfullduration(self)
		mintime, maxtime = node.GetMinMax()
		if ndur is None:
			# unknown duration, assume indefinite
			ndur = -1
		if ndur >= 0:
			ndur = max(mintime, ndur) # play at least this long
		if maxtime >= 0 and ndur >= 0:
			ndur = max(maxtime, ndur) # don't play longer than this
		if ndur >= 0 and timestamp + ndur <= parent.timefunc() and node.GetFill() == 'remove':
			runchild = 0
		srdict = pnode.gensr_child(node, runchild, path = path, sctx = self, curtime = parent.timefunc())
		self.srdict.update(srdict)
		if debugdump: self.dump()
		node.set_start_time(timestamp)
		if runchild:
			parent.event(self, (SR.SCHED, node), timestamp)
		else:
			if debugevents: print 'trigger, no run',parent.timefunc()
			node.startplay(timestamp)
			timestamp = timestamp + ndur # we know ndur >= 0
			node.stopplay(timestamp)
##			self.sched_arcs(node, 'begin', timestamp=timestamp)
##			self.sched_arcs(node, 'end', timestamp=timestamp)
			ev = (SR.SCHED_DONE, node)
			if debugevents: print 'trigger: queueing(2)',SR.ev2string(ev), timestamp, parent.timefunc()
			parent.event(self, ev, timestamp)
		parent.updatetimer()

	def cancelarc(self, arc, timestamp, cancel_gensr = 1, propagate = 0):
		if debugevents: print 'cancelarc',`arc`,timestamp
# the commented-out lines fix a problem with
# Default_Fill_on_time_container1.smil but cause worse problems with
# hyperlinking.
##		if arc.timestamp == timestamp:
##			if debugevents: print 'cancelarc returning early'
##			return
		try:
			self.parent.cancel(arc.qid)
		except ValueError:
			pass
		else:
			if debugevents: print 'scheduled_children-1 j',`arc.dstnode`,`arc`,arc.dstnode.scheduled_children,self.parent.timefunc()
			arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
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
				self.cancelarc(a, timestamp, cancel_gensr)

	def gototime(self, node, gototime, timestamp, path = None):
		# XXX trigger syncarcs that should go off after gototime?
		parent = self.parent
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
		for start, end in node.time_list:
			if start > gototime:
				# no more valid intervals
				break
			if end is None or end > gototime:
				# found a valid interval, start node
				if node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
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
							for s, e in c.time_list:
								if s > gototime:
									break
								if e is None or e > gototime:
									self.gototime(c, gototime, timestamp)
									return
						# XXX no children that want to start?
						return
				# start interior node not yet playing or
				# start any leaf node
				self.trigger(None, node, path, start)
				self.sched_arcs(node, 'begin', timestamp = start)
				return
		if node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
			# no valid intervals, so node should not play
			self.do_terminate(node, timestamp)
			if not parent.playing:
				return
		if path is not None or node.playing == MMStates.IDLE:
			# no intervals yet, check whether we should play
			resolved = node.isresolved(self)
			if path is not None and resolved is None:
				resolved = gototime
			if resolved is not None:
				self.trigger(None, node, path, resolved)
				self.sched_arcs(node, 'begin', timestamp = resolved)

	def cancel_gensr(self, node):
		# cancel the SCHED_DONE that was added by gensr_child()
		# but only if the node never played
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

	def do_terminate(self, node, timestamp, fill = 'remove', cancelarcs = 0, chkevent = 1):
		parent = self.parent
		if debugevents: print 'do_terminate',node,timestamp,fill,parent.timefunc()
		if debugdump: parent.dump()
		if fill != 'remove' and node.GetSchedParent() is None:
			fill = 'remove'
		self.cancel_gensr(node)
		for arc in node.durarcs + node.GetEndList():
			if arc.qid is not None:
				if debugevents: print 'cancel',`arc`,parent.timefunc()
				self.cancelarc(arc, timestamp, not cancelarcs)
##				if debugevents: print 'scheduled_children-1 h',`arc.dstnode`,arc.dstnode.scheduled_children,parent.timefunc()
##				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
		if fill == 'remove' and node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN, MMStates.PLAYED):
			for arc in node.delayed_arcs:
				if debugevents: print 'scheduled_children-1 i',`arc.dstnode`,arc.dstnode.scheduled_children,parent.timefunc()
				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
			node.delayed_arcs = []
			getchannelfunc = node.context.getchannelbynode
			if node.type in leaftypes and getchannelfunc:
				xnode = node
				if isinstance(xnode, MMNode.MMNode_body):
					xnode = xnode.parent
				chan = getchannelfunc(xnode)
				if chan:
					if debugevents: print 'stopplay',`node`,parent.timefunc()
					chan.stopplay(xnode)
			if node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
				for c in [node.looping_body_self,
					  node.realpix_body,
					  node.caption_body] + \
					 node.GetSchedChildren():
					if c is None:
						continue
					self.do_terminate(c, timestamp, fill=fill, cancelarcs=cancelarcs)
					if not parent.playing:
						return
				node.stopplay(timestamp)
				node.cleanup_sched(parent)
				for c in node.GetSchedChildren():
					c.resetall(parent)
		elif fill != 'remove' and node.playing in (MMStates.PLAYING, MMStates.PAUSED):
			self.freeze_play(node, timestamp)
			if not parent.playing:
				return
		pnode = node.GetSchedParent()
		if pnode is not None and \
		   pnode.type == 'excl' and \
		   node in pnode.pausestack:
			pnode.pausestack.remove(node)
		paused = parent.paused
		parent.paused = 0
		self.flushqueue(1)
		if not parent.playing:
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
				if debugevents: print 'queueing',SR.ev2string(ev), timestamp, parent.timefunc()
				adur = node.calcfullduration(self)
				if node.fullduration is None or adur is None or adur < 0:
					self.sched_arcs(node, 'end', timestamp=timestamp)
				parent.event(self, ev, timestamp)
		if fill == 'remove':
			ev = (SR.SCHED_STOP, node)
			if self.srdict.has_key(ev):
				parent.event(self, ev, timestamp)
				for e, srdict in self.srdict.items():
					srlist = srdict[e][1]
					if ev in srlist:
						srlist.remove(ev)
		if not cancelarcs:
			if debugevents: print 'do_terminate: return: not cancelarcs',node
			return
		for qid in parent.queue[:]:
			time, priority, action, argument = qid
			if action != self.trigger:
				continue
			arc = argument[0]
			if arc.srcnode is node and arc.getevent() == 'end':
				if debugevents: print 'do_terminate: cancel',`arc`,parent.timefunc()
				self.cancelarc(arc, timestamp)
		if debugevents: print 'do_terminate: return',node

	# callback from channel to indicate that a transition finished
	# on a region overlapping with this node's region, so we must
	# terminate this node if it was frozen with fill="transition"
	def transitiondone(self, node):
		if node.playing == MMStates.FROZEN and node.GetFill() == 'transition':
			self.do_terminate(node, self.parent.timefunc())

	def flushqueue(self, xxx = 0):
		parent = self.parent
		if debugevents: print 'flushqueue',parent.timefunc()
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
				parent.runone(action, ts)
			self.queue = parent.selectqueue()
			if not self.queue:
				break

	def freeze_play(self, node, timestamp = None):
		parent = self.parent
		if debugevents: print 'freeze_play',`node`,parent.timefunc()
		if node.playing in (MMStates.PLAYING, MMStates.PAUSED):
			getchannelfunc = node.context.getchannelbynode
			if node.type in leaftypes and getchannelfunc:
				xnode = node
				if isinstance(xnode, MMNode.MMNode_body):
					xnode = xnode.parent
				chan = getchannelfunc(xnode)
				if chan:
					if debugevents: print 'freeze',`node`,parent.timefunc()
					chan.freeze(xnode)
			for c in node.GetSchedChildren():
				self.do_terminate(c, timestamp, fill = 'freeze')
				if not parent.playing:
					return
			node.playing = MMStates.FROZEN
			node.set_armedmode(ARM_WAITSTOP)

	def do_pause(self, pnode, node, action, timestamp):
		if debugevents: print 'pause',node,timestamp,self.parent.timefunc()
		if node in pnode.pausestack:
			pnode.pausestack.remove(node)
		for arc in node.durarcs:
			if arc.qid is not None:
				arc.paused = arc.qid[0] - timestamp
				self.cancelarc(arc, timestamp)
				if debugevents: print 'pause_play',`arc`,arc.paused,self.parent.timefunc()
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
		getchannelfunc = node.context.getchannelbynode
		if node.type in leaftypes and getchannelfunc:
			xnode = node
			if isinstance(xnode, MMNode.MMNode_body):
				xnode = xnode.parent
			chan = getchannelfunc(xnode)
			if chan:
				if debugevents: print 'freeze',`node`,self.parent.timefunc()
				chan.pause(xnode, action)
		for c in node.GetSchedChildren():
			self.pause_play(c, action, timestamp)
		node.playing = MMStates.PAUSED
		node.set_armedmode(ARM_WAITSTOP) # XXX ?

	def do_resume(self, node, timestamp):
		if debugevents: print 'resume',node,timestamp,self.parent.timefunc()
		ev = (SR.SCHED, node)
		if self.srdict.has_key(ev):
			node.set_start_time(timestamp, 0)
			self.sched_arcs(node, 'begin', timestamp=timestamp)
			self.parent.event(self, ev, timestamp)
		else:
			if node.playing != MMStates.FROZEN:
				for arc in node.durarcs:
					if arc.qid is None:
						arc.qid = self.parent.enterabs(timestamp + arc.paused, 0, self.trigger, (arc,))
						arc.timestamp = timestamp + arc.paused
						del arc.paused
			self.resume_play(node, timestamp)

	def resume_play(self, node, timestamp):
		if node.playing != MMStates.PAUSED:
			return
		getchannelfunc = node.context.getchannelbynode
		if node.type in leaftypes and getchannelfunc:
			xnode = node
			if isinstance(xnode, MMNode.MMNode_body):
				xnode = xnode.parent
			chan = getchannelfunc(xnode)
			if chan:
				if debugevents: print 'freeze',`node`,self.parent.timefunc()
				chan.resume(xnode)
		if node.type == 'excl':
			for c in node.GetSchedChildren():
				if c.playing == MMStates.PAUSED and \
				   c not in node.pausestack:
					self.resume_play(c, timestamp)
		else:
			for c in node.GetSchedChildren():
				self.resume_play(c, timestamp)
		node.playing = MMStates.PLAYING
		node.set_armedmode(ARM_PLAYING)

	def queuesrlist(self, srlist, timestamp = None):
		for sr in srlist:
			if debugevents: print '  queue', SR.ev2string(sr), timestamp,self.parent.timefunc()
			if sr[0] == SR.PLAY:
				prio = PRIO_START
			elif sr[0] == SR.PLAY_STOP:
				prio = PRIO_STOP
			else:
				prio = PRIO_INTERN
			self.parent.add_runqueue(self, prio, sr, timestamp)
	#
	def play_done(self, node, timestamp = None):
		if node.GetTerminator() == 'MEDIA' and \
		   not node.attrdict.has_key('duration') and \
		   not node.FilterArcList(node.GetEndList()):
			self.parent.event(self, (SR.SCHED_STOPPING, node.looping_body_self or node), timestamp)

	#
	def anchorfired(self, node, anchorlist, arg):
		return self.parent.anchorfired(self, node, anchorlist, arg)
	#
	# Partially handle an event, updating the internal queues and
	# returning executable SRs, if any.
	#
	def getsrlist(self, ev):
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
		if self.ui.sync_cv and self.toplevel.channelview is not None:
			self.toplevel.channelview.globalsetfocus(node)
		sctx = SchedulerContext(self, node, seek_node)
		self.sctx_list.append(sctx)
		self.playing = self.playing + 1
		if not sctx.start(seek_node, anchor_id, anchor_arg, timestamp):
			if debugevents: print 'Scheduler: play abort',self.timefunc()
			sctx.stop()
			return None
		self.starting_to_play = 1
		return sctx
	#
	def _remove_sctx(self, sctx):
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

	def stop_all(self):
		if debugevents: print 'STOP_ALL', self.sctx_list,self.timefunc()
		to_stop = self.sctx_list[:]
		for sctx in to_stop:
			sctx.stop()
		to_stop = None
		if debugevents: print 'Now', self.sctx_list,self.timefunc()
		if debugevents: self.dump()
		self.queue = []		# XXX shouldn't be necessary, but it is
		if self.starting_to_play:
			self.starting_to_play = 0
		self.playing = 0
		self.ui.play_done()
		self.toplevel.set_timer(0)

	#
	# The timer callback routine, called via a forms timer object.
	# This is what makes SR's being executed.
	#
	def timer_callback(self):
		#
		# We have two queues to execute: the timed queue and the
		# normal SR queue. Currently, we execute the timed queue first.
		# Also, we have to choose here between an eager and a non-eager
		# algorithm. For now, we're eager, on both queues.
		#
		if debugtimer: print 'timer_callback',self.timefunc()
		now = self.timefunc()
		while self.queue and self.queue[0][0] <= now:
			self.toplevel.setwaiting()
			when, prio, action, argument = self.queue[0]
			del self.queue[0]
			void = apply(action, argument)
			now = self.timefunc()
		#
		# Now the normal runqueue
		#
		queue = self.selectqueue()
		if queue:
			self.toplevel.setwaiting()
			for action in queue:
				if not self.playing:
					break
				timestamp = None
				if len(action) > 3:
					timestamp = action[3]
					action = action[:3]
				self.runone(action, timestamp)
		self.updatetimer()
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
				delay = 0.001
			if debugtimer: print 'updatetimer: timed events' #DBG
		elif not self.FutureWork():
			#
			# No more events (and nothing runnable either).
			# We're thru.
			#
			if debugtimer: print 'updatetimer: no more work' #DBG
			self.stop_all()
			self.ui.set_timer(0.001)
			return
		else:
			#
			# Nothing to do for the moment.
			# Tick every second, so we see the timer run.
			#
			if debugtimer:  'updatetimer: idle' #DBG
			return
		if debugtimer: print 'updatetimer: delay=', delay
		self.delay = delay
		self.ui.set_timer(delay)
	#
	# Incoming events from channels, or the start event.
	#
	def event(self, sctx, ev, timestamp):
		if sctx.active:
##			if ev[0] == SR.ARM_DONE:
##				ev[1].set_armedmode(ARM_ARMED)
			sctx.event(ev, timestamp)
		self.updatetimer()
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

	def runone(self, (sctx, todo, dummy), timestamp = None):
		if not sctx.active:
			raise error, 'Scheduler: running from finished context'
		if debugevents: print 'exec: ', SR.ev2string(todo), timestamp, self.timefunc()
		if timestamp is None:
			timestamp = self.timefunc()
		action, arg = todo
		if action == SR.LOOPSTART:
			self.do_loopstart(sctx, arg, timestamp)
			arg.looping_body_self.set_start_time(timestamp)
			if arg.type in leaftypes:
				self.do_play(sctx, arg.looping_body_self, timestamp)
			else:
				arg.looping_body_self.startplay(timestamp)
			sctx.sched_arcs(arg.looping_body_self,
					'begin', timestamp=timestamp)
			arg.looping_body_self.loopcount = 0
		elif action == SR.LOOPEND:
			self.do_loopend(sctx, arg, timestamp)
		elif action == SR.LOOPRESTART:
			if self.do_looprestart(sctx, arg, timestamp):
				arg.looping_body_self.set_start_time(timestamp)
				if arg.type in leaftypes:
					self.do_play(sctx, arg.looping_body_self, timestamp)
				else:
					arg.looping_body_self.startplay(timestamp)
				sctx.sched_arcs(arg.looping_body_self,
						'begin', timestamp=timestamp)
				arg.looping_body_self.loopcount = arg.looping_body_self.loopcount + 1
				sctx.sched_arcs(arg, 'repeat(%d)' % arg.looping_body_self.loopcount)
		elif action == SR.SCHED_STOPPING:
			if arg.scheduled_children:
				if debugevents: print 'not stopping',`arg`,arg.scheduled_children,self.timefunc()
				return
			if arg.type in interiortypes and \
			   arg.playing != MMStates.PLAYED and \
			   (arg.attrdict.get('duration') is not None or
			    arg.attrdict.get('end') is not None):
				if debugevents: print 'not stopping (dur/end)',`arg`,self.timefunc()
				return
			if arg.GetFill() == 'remove':
				for ch in arg.GetSchedChildren():
					sctx.do_terminate(ch, timestamp, chkevent = 0)
					if not self.playing:
						return
			else:
				sctx.do_terminate(arg, timestamp, fill = arg.GetFill(), chkevent = 0)
				if not self.playing:
					return
			adur = arg.calcfullduration(self)
			if arg.fullduration is None or adur is None or adur < 0:
				if not arg.has_min:
					sctx.sched_arcs(arg, 'end', timestamp=timestamp)
			sctx.event((action, arg), timestamp)
		elif action == SR.SCHED_START:
			if arg.type in leaftypes and arg.looping_body_self is None:
				self.do_play(sctx, arg, timestamp)
			else:
				arg.startplay(timestamp)
			sctx.sched_arcs(arg, 'begin', timestamp=timestamp)
##				adur = arg.calcfullduration(self)
##				if arg.fullduration is not None and adur is not None and adur >= 0:
##					sctx.sched_arcs(arg, 'end', timestamp=timestamp+adur)
			sctx.event((action, arg), timestamp)
		elif action == SR.SCHED_STOP:
			if debugevents: print 'cleanup',`arg`,self.timefunc()
			arg.cleanup_sched(self)
			sctx.event((action, arg), timestamp)
		else:
			sctx.event((action, arg), timestamp)

	#
	# Execute a PLAY SR.
	#
	def do_play(self, sctx, node, timestamp):
		if debugevents: print 'do_play',`node`,node.start_time, timestamp,self.timefunc()
		if self.starting_to_play:
			self.starting_to_play = 0
		xnode = node
		if isinstance(xnode, MMNode.MMNode_body):
			xnode = xnode.parent
		chan = self.ui.getchannelbynode(xnode)
		if chan not in sctx.channels:
			sctx.channels.append(chan)
			chan.startcontext(sctx)
		node.startplay(timestamp)
##		sctx.sched_arcs(node, 'begin', timestamp = timestamp)
##		ndur = node.calcfullduration(self)
##		if ndur is not None and ndur >= 0:
##			sctx.sched_arcs(node, 'end', timestamp = timestamp+ndur)
		chan.play(xnode)

	#
	# Execute a PLAY_STOP SR.
	#
	def do_play_stop(self, sctx, node, timestamp):
		if node.playing not in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
			if debugevents: print 'do_play_stop: already stopped',`node`,self.timefunc()
			return
		xnode = node
		if isinstance(xnode, MMNode.MMNode_body):
			xnode = xnode.parent
		chan = self.ui.getchannelbynode(xnode)
		chan.freeze(xnode)
		node.stopplay(timestamp)

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
	def do_looprestart(self, sctx, node, timestamp):
##		print 'LOOPRESTART', node
		if not node.moreloops(decrement=1):
			# Node has been terminated in the mean time
			self.event(sctx, (SR.LOOPEND_DONE, node), timestamp)
			return 0
		sctx.restartloop(node)
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
		if debugevents: print 'enterabs',time,priority,action,argument,self.timefunc()
		id = scheduler.enterabs(self, time, priority, action, argument)
		self.updatetimer()
		return id

	def timefunc(self):
		if self.paused:
			return self.time_pause - self.time_origin
		return time.time() - self.time_origin

	def resettimer(self, starttime = 0):
		self.time_origin = time.time() - starttime
		self.time_pause = self.time_origin + starttime

	def getpaused(self):
		return self.paused

	def settime(self, timestamp):
		if debugevents: print 'settime',timestamp
		self.time_origin = self.time_pause - timestamp

	def setpaused(self, paused):
		if self.paused == paused:
			return

		if not paused:
			# subtract time paused
			self.time_origin = self.time_origin + \
					   (time.time()-self.time_pause)
		else:
			# remember time paused
			self.time_pause = time.time()
		self.paused = paused
		for sctx in self.sctx_list:
			sctx.setpaused(paused)
		self.updatetimer()

class ArmStorageTree:
	def __init__(self, node):
		self.children = []
		self.index = 0
		self.parent = None
		self.node = node
		self.onemoretime = 0

	def setparents(self):
		"""Last stage of tree buildup: link children back to parent"""
		for c in self.children:
			c.parent = self

	def destroy(self):
		"""Destroy the whole tree starting at any node"""
		if self.parent:
			raise error, 'Destroy with parent!'
		for c in self.children:
			c.parent = None
			c.destroy()
		del self.parent
		del self.children

	def cancel(self, node):
		"""Cancel arms for node and descendents, knowing that
		node is currently active (so somewhere between current and
		root)"""
		if node == self.node:
			self.do_cancel()
		elif self.parent:
			self.parent.cancel(node)

	def do_cancel(self):
		"""Cancel arm for this node and its descendents"""
		self.index = len(self.children)+1
		self.onemoretime = 0
		for ch in self.children[self.index:]:
			ch.do_cancel()

	def next(self):
		"""Return next ArmStorage to query and next node to arm"""
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

##	def dump(self, level):
##		print ' '*level, 'LEAF', self.node

	def isempty(self):
		return 0

	def looponcemore(self, node):
		pass

	def do_looponcemore(self):
		pass

#  Remove all arm_duration attributes (so they will be recalculated)

def del_timing(node):
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
		unarmallnodes(child)

