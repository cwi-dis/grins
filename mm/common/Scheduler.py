__version__ = "$Id$"

# Scheduler - The scheduler for playing cmif documents.

import time
from sched import scheduler
from MMExc import *
import MMAttrdefs
from MMTypes import *
from ArmStates import *
from HDTL import HD, TL
# Not needed? from AnchorDefs import *
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
	def __init__(self, parent, node, seeknode):
		self.queue = []
		self.active = 1
		self.parent = parent
		self.srdict = {}
		self.scheduled_children = 0
		if not settings.noprearm:
			self.unexpected_armdone = {}
			self.prearmlists = {}
		self.playroot = node
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
		if not settings.noprearm:
			unarmallnodes(self.playroot)
		self.stopcontextchannels()
		self.srdict = {}
		self.parent._remove_sctx(self)
		self.playroot.resetall(self.parent)
		del self.parent
		del self.playroot
		if not settings.noprearm:
			for v in self.prearmlists.values():
				if v:
					v.root().destroy()
			del self.prearmlists

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
	# genprearms generates the list of channels and a list of
	# nodes to be prearmed, in the right order.
	def gen_prearms(self, s_node):
		if not s_node:
			s_node = self.playroot
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
		if not settings.noprearm:
			self.prearmlists = GenAllPrearms(self.parent.ui,
							 self.playroot,
							 self.channels)
		self.playroot.EndPruneTree()
		mini = self.playroot.FindMiniDocument()
		return 1

	def cancelprearms(self, node):
		"""Cancel prearms for node and its descendents, it has
		just been terminated"""
		if settings.noprearm:
			raise error, 'cancelprearms called when noprearm set'
		for list in self.prearmlists.values():
			list.cancel(node)

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
			ch.uipaused(paused)

	#
	# getnextprearm returns next prearm event due for given channel
	#
	def getnextprearm(self, ch):
		if settings.noprearm:
			raise error, 'getnextprearm called when noprearm set'
		if not self.prearmlists.has_key(ch):
			return None
		if not self.prearmlists[ch]:
			return None
		self.prearmlists[ch], node = self.prearmlists[ch].next()
		if not node:
			return None
		return (SR.PLAY_ARM, node)
	#
	# run_initial_prearms schedules the first prearms.
	# Prearms that are immedeately needed are scheduled in a hi-pri queue,
	# the ones that are not needed until later in a lo-pri queue. Also, the
	# lo-pri queue is run one-event-at-a-time, so we put them in there
	# sorted by time
	#
	def run_initial_prearms(self):
		if settings.noprearm:
			raise error, 'run_initial_prearms called when noprearm set'
		# XXXX Code gone to gen_prearms
		prearmnowlist = []
		prearmlaterlist = []
		now = self.playroot.GetTimes()[0]
		parent = self.parent
		for ch in self.channels:
			ev = self.getnextprearm(ch)
			if not ev:
				continue
			t0 = ev[1].GetTimes()[0]
			if t0 <= now:
				prearmnowlist.append(ev)
			else:
				prearmlaterlist.append((t0, ev))
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
		if self.srdict or self.scheduled_children:
			return 1
		self.parent.ui.sctx_empty(self) # XXXX
		return 0
	#
	# Initialize SR actions and events before playing
	#
	def prepare_minidoc(self, seeknode):
		self.srdict = self.playroot.GenAllSR(seeknode, curtime = self.parent.timefunc())
	#
	# Re-initialize SR actions and events for a looping node, preparing
	# for the next time through the loop
	#
	def restartloop(self, node):
		if debugdump: self.dump()
		srdict = node.GenLoopSR(self.parent.timefunc())
		for key, value in srdict.items():
			if self.srdict.has_key(key):
				raise error, 'Duplicate event '+SR.ev2string(key)
			self.srdict[key] = value
			#
			# ARMDONE events may have arrived too early.
			# Re-schedule them.
			#
			if not settings.noprearm and \
			   self.unexpected_armdone.has_key(key):
				ev, node = key
				del self.unexpected_armdone[key]
				self.parent.add_runqueue(self, PRIO_PREARM_NOW,
					       (SR.PLAY_OPTIONAL_ARM, node) )

	#
	# Tell arm datastructures that we will go through the loop at
	# least once more after the current loop is finished.
	#
	def arm_moreloops(self, node):
		if settings.noprearm:
			raise error, 'arm_moreloops called when noprearm set'
		for tree in self.prearmlists.values():
			tree.root().looponcemore(node)

	#
	# Start minidoc starts playing what we've prepared
	#
	def start(self, s_node, s_aid, s_args, timestamp = None):
		if debugevents: print 'SchedulerContext.start',`self`, `s_node`, `s_aid`, `s_args`, timestamp, self.parent.timefunc()
		if not self.gen_prearms(s_node):
			return 0
		if not settings.noprearm:
			self.run_initial_prearms()
		self.startcontextchannels()
		if s_node and s_aid:
			self.seekanchor(s_node, s_aid, s_args)
		playroot = self.playroot
		if timestamp is None:
			timestamp = self.parent.timefunc()
		playroot.start_time = timestamp
		if playroot.looping_body_self:
			playroot.looping_body_self.start_time = timestamp
		if playroot.realpix_body:
			playroot.realpix_body.start_time = timestamp
		if playroot.caption_body:
			playroot.caption_body.start_time = timestamp

		self.parent.event(self, (SR.SCHED, self.playroot), timestamp)
##		self.parent.updatetimer()
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
	def event(self, ev, timestamp):
		if debugevents: print 'event', SR.ev2string(ev), timestamp, self.parent.timefunc()
		srlist = self.getsrlist(ev)
		self.queuesrlist(srlist, timestamp)

	def sched_arc(self, node, arc, event = None, marker = None, deparc = None, timestamp = None):
		if debugevents: print 'sched_arc',`node`,`arc`,event,marker,`deparc`,timestamp,self.parent.timefunc()
		if arc.wallclock is not None:
			timestamp = arc.resolvedtime(self.parent.timefunc)-arc.delay
		if arc.ismin:
			list = []
		elif arc.isstart:
			dev = 'begin'
			list = MMAttrdefs.getattr(arc.dstnode, 'beginlist')
			list = []
		else:
			dev = 'end'
			list = MMAttrdefs.getattr(arc.dstnode, 'endlist')
			list = list + arc.dstnode.durarcs
		if arc.timestamp is not None and arc.timestamp != timestamp+arc.delay:
			if arc.qid is not None:
				if debugevents: print 'sched_arcs: cancel',`arc`,self.parent.timefunc()
				self.cancelarc(arc, timestamp)
		for a in list:
			if a.qid is None:
				continue
			if a.ismin:
				continue
			if a.timestamp > timestamp + arc.delay:
				if debugevents: print 'sched_arcs: cancel',`a`,self.parent.timefunc()
				self.cancelarc(a, timestamp)
				if a.isstart:
					if a.dstnode.GetSchedParent():
						srdict = a.dstnode.GetSchedParent().gensr_child(a.dstnode, runchild = 0, curtime = self.parent.timefunc())
						self.srdict.update(srdict)
					else:
						# root node
						self.scheduled_children = self.scheduled_children - 1
				else:
					if debugevents: print 'scheduled_children-1',`a.dstnode`,`node`,event,self.parent.timefunc()
					a.dstnode.scheduled_children = a.dstnode.scheduled_children - 1
		if arc.qid is None:
			if arc.isstart:
				if arc.dstnode.GetSchedParent():
					srdict = arc.dstnode.GetSchedParent().gensr_child(arc.dstnode, runchild = 0, curtime = self.parent.timefunc())
					self.srdict.update(srdict)
				else:
					# root node
					self.scheduled_children = self.scheduled_children + 1
			else:
				if debugevents: print 'scheduled_children+1',`arc`,`node`,event,self.parent.timefunc()
				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children + 1
			if arc.refnode() is node:
				arc.timestamp = timestamp + arc.delay
			if not arc.isstart and not arc.ismin and arc.srcnode is arc.dstnode:
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
			if arc.depends is not None:
				try:
					arc.deparcs.remove(arc)
				except ValueError:
					pass
			arc.depends = deparc # can be None
			if deparc is not None:
				deparc.deparcs.append(arc)
		if not arc.ismin and (arc.dstnode is not node or dev != event):
			self.sched_arcs(arc.dstnode, dev, deparc = arc, timestamp=timestamp+arc.delay)

	def sched_arcs(self, node, event = None, marker = None, deparc = None, timestamp = None):
		if debugevents: print 'sched_arcs',`node`,event,marker,timestamp,self.parent.timefunc()
		if timestamp is None:
			timestamp = self.parent.timefunc()
		channel = accesskey = None
		if event is not None:
			node.event(timestamp, event)
			if type(event) is type(()):
				if event[1] == 'accessKey':
					accesskey = event[2]
					event = None
				else:
					channel, event = event[:2]
		if marker is not None:
			node.marker(timestamp, marker)
		for arc in node.sched_children:
			if (arc.channel != channel or
			    arc.event != event or
			    arc.marker != marker or
			    arc.accesskey != accesskey or
			    arc.delay is None) and \
			   (arc.event is not None or
			    arc.marker is not None or
			    marker is not None or
			    arc.delay is None or
			    ((event != 'begin' or arc.dstnode not in node.GetSchedChildren()) and
			     (event != 'end' or arc.dstnode in node.GetSchedChildren()))):
				continue
			atime = 0
			if arc.srcanchor is not None:
				for id, atype, args, times in node.attrdict.get('anchorlist', []):
					if id == arc.srcanchor:
						if event == 'end':
							atime = times[1]
						else:
							atime = times[0]
						break
			self.sched_arc(node, arc, event, marker, deparc, timestamp+atime)
		if debugevents: print 'sched_arcs return',`node`,event,marker,timestamp,self.parent.timefunc()

	def trigger(self, arc, node = None, path = None, timestamp = None):
		# if arc == None, arc is not used, but node and timestamp are
		# if arc != None, arc is used, and node and timestamp are not
		parent = self.parent
		paused = parent.paused
		parent.paused = 0
		self.flushqueue()
		if not parent.playing:
			return
		parent.paused = paused

		deparcs = []
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
			if arc.depends is not None:
				try:
					arc.depends.deparcs.remove(arc)
				except ValueError:
					pass
				arc.depends = None
			deparcs = arc.deparcs
			for a in arc.deparcs:
				a.depends = None
			arc.deparcs = []
			timestamp = arc.resolvedtime(parent.timefunc)
			node = arc.dstnode
			arc.qid = None
			if debugevents: print 'trigger', `arc`, timestamp,parent.timefunc()
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
		elif debugevents: print 'trigger', `node`, timestamp,parent.timefunc()
		if arc is not None:
			if arc.ismin:
				node.has_min = 0
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
							return
			if arc.isstart:
				if arc.path:
					path = arc.path
					arc.path = None
					# zap all other paths
					for a in MMAttrdefs.getattr(arc.dstnode, 'beginlist'):
						a.path = None
			else:
				if node.has_min:
					# must delay this arc
					node.delayed_arcs.append(arc)
					fill = node.GetFill()
					for c in node.GetSchedChildren():
						self.do_terminate(c, timestamp, fill = fill)
						if not parent.playing:
							return
					parent.updatetimer()
					return
				if debugevents: print 'scheduled_children-1',`node`,parent.timefunc()
				if node.scheduled_children > 0:
					node.scheduled_children = node.scheduled_children - 1
				if node.playing not in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
					# ignore end event if not playing
					if debugevents: print 'node not playing',parent.timefunc()
					parent.updatetimer()
					return
				if debugevents: print 'terminating node',parent.timefunc()
				pnode = node.GetSchedParent()
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
				parent.updatetimer()
				return
		pnode = node.GetSchedParent()
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
			for a in deparcs:
				self.cancelarc(a, timestamp)
			parent.updatetimer()
			return
		endlist = MMAttrdefs.getattr(node, 'endlist')
		equal = 0
		if endlist:
			found = 0
			for a in endlist:
				if not a.isresolved(parent.timefunc):
					# any unresolved time is after any resolved time
					found = 1
				else:
					ats = a.resolvedtime(parent.timefunc)
					if ats > timestamp:
						found = 1
					elif ats == timestamp:
						equal = 1
						found = 1
						break
			if not found:
				if debugevents: print 'not allowed to start',parent.timefunc()
				srdict = pnode.gensr_child(node, runchild = 0, curtime = parent.timefunc())
				self.srdict.update(srdict)
				ev = (SR.SCHED_DONE, node)
				if debugevents: print 'trigger: queueing',SR.ev2string(ev), timestamp, parent.timefunc()
				parent.event(self, ev, timestamp)
				parent.updatetimer()
				return
		# if node is playing (or not stopped), must terminate it first
		if node.playing not in (MMStates.IDLE, MMStates.PLAYED):
			if debugevents: print 'terminating node',parent.timefunc()
			self.do_terminate(node, timestamp)
			if not parent.playing:
				return
			self.sched_arcs(node, 'begin', timestamp=timestamp)
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
						self.do_terminate(sib, timestamp)
						if not parent.playing:
							return
					elif action == 'never':
						if arc is not None:
							self.cancelarc(arc, timestamp)
							for a in deparcs:
								self.cancelarc(a, timestamp)
						parent.updatetimer()
						return
					elif action == 'defer':
						if node not in pnode.pausestack:
							srdict = pnode.gensr_child(node, curtime = parent.timefunc())
							self.srdict.update(srdict)
						node.start_time = timestamp
						p = node.parent
						while p and p.type == 'alt':
							p.start_time = timestamp
							p = p.parent
						if node.looping_body_self:
							node.looping_body_self.start_time = node.start_time
						if node.realpix_body:
							node.realpix_body.start_time = node.start_time
						if node.caption_body:
							node.caption_body.start_time = node.start_time
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
					self.do_terminate(sib, timestamp)
					if not parent.playing:
						return
					break
		elif pnode.type == 'seq':
			# parent is seq, must terminate running child first
			if debugevents: print 'terminating siblings',parent.timefunc()
			for c in pnode.GetSchedChildren():
				# don't have to terminate it again
				if c is not node and c.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
					# if fill="hold", freeze child, otherwise kill
					fill = c.GetFill()
					if fill != 'hold':
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
		ndur = node.calcfullduration()
		if MMAttrdefs.getattr(node, 'min') == 0 and \
		   (equal or (ndur == 0 and node.GetFill() == 'remove')):
			runchild = 0
		else:
			runchild = 1
		srdict = pnode.gensr_child(node, runchild, path = path, curtime = parent.timefunc())
		self.srdict.update(srdict)
		if debugdump: self.dump()
		node.start_time = timestamp
		p = node.parent
		while p and p.type == 'alt':
			p.start_time = timestamp
			p = p.parent
		if node.looping_body_self:
			node.looping_body_self.start_time = node.start_time
		if node.realpix_body:
			node.realpix_body.start_time = node.start_time
		if node.caption_body:
			node.caption_body.start_time = node.start_time
		if runchild:
			parent.event(self, (SR.SCHED, node), timestamp)
		else:
			if debugevents: print 'trigger, no run',parent.timefunc()
			node.startplay(self, timestamp)
			node.stopplay(timestamp)
##			self.sched_arcs(node, 'begin', timestamp=timestamp)
##			self.sched_arcs(node, 'end', timestamp=timestamp)
			ev = (SR.SCHED_DONE, node)
			if debugevents: print 'trigger: queueing(2)',SR.ev2string(ev), timestamp, parent.timefunc()
			parent.event(self, ev, timestamp)
		parent.updatetimer()

	def cancelarc(self, arc, timestamp):
		if debugevents: print 'cancelarc',`arc`,timestamp
		try:
			self.parent.cancel(arc.qid)
		except ValueError:
			pass
		arc.qid = None
		deparcs = arc.deparcs
		arc.deparcs = []
##		if arc.isstart:
##			ev = (SR.SCHED_DONE, arc.dstnode)
##			if self.srdict.has_key(ev):
##				self.parent.event(self, ev, timestamp)
		for a in deparcs:
			self.cancelarc(arc, timestamp)
			a.depends = None

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
			if path0.type == 'alt':
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
			resolved = node.isresolved()
			if path is not None and resolved is None:
				resolved = gototime
			if resolved is not None:
				self.trigger(None, node, path, resolved)
				self.sched_arcs(node, 'begin', timestamp = resolved)
		return

	def do_terminate(self, node, timestamp, fill = 'remove', cancelarcs = 0, chkevent = 1):
		parent = self.parent
		if debugevents: print 'do_terminate',node,timestamp,fill,parent.timefunc()
		if debugdump: parent.dump()
		for arc in node.durarcs + MMAttrdefs.getattr(node, 'endlist'):
			if arc.qid is not None:
				if debugevents: print 'cancel',`arc`,parent.timefunc()
				self.cancelarc(arc, timestamp)
				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
		if fill == 'remove' and node.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
			for arc in node.delayed_arcs:
				arc.dstnode.scheduled_children = arc.dstnode.scheduled_children - 1
			node.delayed_arcs = []
			getchannelfunc = node.context.getchannelbynode
			if node.type in leaftypes and getchannelfunc:
				chan = getchannelfunc(node)
				if chan:
					if debugevents: print 'stopplay',`node`,parent.timefunc()
					chan.stopplay(node)
					node.set_armedmode(ARM_DONE)
			for c in node.GetSchedChildren():
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
		self.flushqueue()
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
				adur = node.calcfullduration()
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
			return
		for qid in parent.queue[:]:
			time, priority, action, argument = qid
			if action != self.trigger:
				continue
			arc = argument[0]
			if arc.srcnode is node and arc.event == 'end':
				if debugevents: print 'do_terminate: cancel',`arc`,parent.timefunc()
				self.cancelarc(arc, timestamp)

	def flushqueue(self):
		parent = self.parent
		if debugevents: print 'flushqueue',parent.timefunc()
		while 1:
			self.queue = parent.selectqueue()
			if not self.queue:
				break
			for action in self.queue:
				if not parent.playing:
					break
				ts = None
				if len(action) > 3:
					ts = action[3]
					action = action[:3]
				parent.runone(action, ts)
		self.queue = []

	def freeze_play(self, node, timestamp = None):
		parent = self.parent
		if debugevents: print 'freeze_play',`node`,parent.timefunc()
		if node.playing in (MMStates.PLAYING, MMStates.PAUSED):
			getchannelfunc = node.context.getchannelbynode
			if node.type in leaftypes and getchannelfunc:
				chan = getchannelfunc(node)
				if chan:
					if debugevents: print 'freeze',`node`,parent.timefunc()
					chan.freeze(node)
			for c in node.GetSchedChildren():
				self.do_terminate(c, timestamp, fill = 'freeze')
				if not parent.playing:
					return
			node.playing = MMStates.FROZEN

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
			chan = getchannelfunc(node)
			if chan:
				if debugevents: print 'freeze',`node`,self.parent.timefunc()
				chan.pause(node, action)
		for c in node.GetSchedChildren():
			self.pause_play(c, action, timestamp)
		node.playing = MMStates.PAUSED

	def do_resume(self, node, timestamp):
		if debugevents: print 'resume',node,timestamp,self.parent.timefunc()
		if node.playing != MMStates.FROZEN:
			for arc in node.durarcs:
				if arc.qid is None:
					arc.qid = self.parent.enterabs(timestamp + arc.paused, 0, self.trigger, (arc,))
					arc.timestamp = timestamp + arc.paused
					del arc.paused
		ev = (SR.SCHED, node)
		if self.srdict.has_key(ev):
			node.start_time = timestamp
			p = node.parent
			while p and p.type == 'alt':
				p.start_time = timestamp
				p = p.parent
			self.parent.event(self, ev, timestamp)
		else:
			self.resume_play(node, timestamp)

	def resume_play(self, node, timestamp):
		if node.playing != MMStates.PAUSED:
			return
		getchannelfunc = node.context.getchannelbynode
		if node.type in leaftypes and getchannelfunc:
			chan = getchannelfunc(node)
			if chan:
				if debugevents: print 'freeze',`node`,self.parent.timefunc()
				chan.resume(node)
		if node.type == 'excl':
			for c in node.GetSchedChildren():
				if c.playing == MMStates.PAUSED and \
				   c not in node.pausestack:
					self.resume_play(c, timestamp)
		else:
			for c in node.GetSchedChildren():
				self.resume_play(c, timestamp)
		node.playing = MMStates.PLAYING

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
	def arm_ready(self, chan):
		if settings.noprearm:
			raise error, 'arm_ready called when noprearm set'
		if not self.prearmlists.has_key(chan):
			raise error, 'Arm_ready event for unknown channel %s' % chan
		pev = self.getnextprearm(chan)
		if pev:
			self.parent.add_lopriqueue(self, pev[1].GetTimes()[0], pev)
	#
	def play_done(self, node, timestamp = None):
		self.parent.event(self, (SR.PLAY_DONE, node), timestamp)

	#
	def arm_done(self, node, timestamp = None):
		if settings.noprearm:
			raise error, 'arm_done called when noprearm set'
		self.parent.event(self, (SR.ARM_DONE, node), timestamp)
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
			if not settings.noprearm and ev[0] == SR.ARM_DONE:
				self.unexpected_armdone[ev] = 1
				return []
			elif ev[0] == SR.SCHED_STOPPING:
				# XXXX Hack to forestall crash on interior
				# nodes with duration that are terminated:
				# their terminating syncarc is still there...
				print 'Warning: unexpected', SR.ev2string(ev),self.parent.timefunc()
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

	# search_unexpected_prearm checks whether any expected ARM_DONE's were
	# received for this node and clears them.
	def search_unexpected_prearm(self, node):
		if settings.noprearm:
			raise error, 'search_unexpected_prearm called when noprearm set'
		for ev, arg in self.unexpected_armdone.keys():
			if arg == node:
				del self.unexpected_armdone[ev, arg]
				return 1
		return 0


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
		self.channels_in_use = []

	#
	# Playing algorithm.
	#
	def play(self, node, seek_node, anchor_id, anchor_arg, timestamp=None):
		# XXXX Is the following true for alt nodes too?
		if node.GetType() == 'bag':
			raise error, 'Cannot play choice node'
		# XXXX This statement should move to an intermedeate level.
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
		elif not settings.noprearm and self.runqueues[PRIO_PREARM_NOW] or \
			  self.runqueues[PRIO_LO]:
			#
			# We are not running (paused=1), but we can do some
			# prearms
			#
			delay = 0.001
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
			if ev[0] == SR.PLAY_DONE:
				ev[1].set_armedmode(ARM_WAITSTOP)
			elif ev[0] == SR.ARM_DONE:
				ev[1].set_armedmode(ARM_ARMED)
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
		if not settings.noprearm and self.runqueues[PRIO_PREARM_NOW]:
			queue = self.runqueues[PRIO_PREARM_NOW]
			self.runqueues[PRIO_PREARM_NOW] = []
			return queue
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
		if action == SR.PLAY:
			self.do_play(sctx, arg, timestamp)
		elif action == SR.PLAY_STOP:
			self.do_play_stop(sctx, arg, timestamp)
		elif action == SR.PLAY_ARM:
			self.do_play_arm(sctx, arg, timestamp)
		elif action == SR.PLAY_OPTIONAL_ARM:
			self.do_play_arm(sctx, arg, timestamp, optional=1)
		elif action in (SR.BAG_START, SR.BAG_STOP):
			raise RuntimeError('BAG')
##			self.ui.bag_event(sctx, todo)
		elif action == SR.LOOPSTART:
			self.do_loopstart(sctx, arg, timestamp)
			arg.startplay(sctx, timestamp)
			sctx.sched_arcs(arg.looping_body_self,
					'begin', timestamp=timestamp)
		elif action == SR.LOOPEND:
			self.do_loopend(sctx, arg, timestamp)
		elif action == SR.LOOPRESTART:
			self.do_looprestart(sctx, arg, timestamp)
			arg.startplay(sctx, timestamp)
			sctx.sched_arcs(arg.looping_body_self,
					'begin', timestamp=timestamp)
		else:
			if action == SR.SCHED_STOPPING:
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
				adur = arg.calcfullduration()
				if arg.fullduration is None or adur is None or adur < 0:
					sctx.sched_arcs(arg, 'end', timestamp=timestamp)
			elif action == SR.SCHED_START:
				arg.startplay(sctx, timestamp)
				sctx.sched_arcs(arg, 'begin', timestamp=timestamp)
##				adur = arg.calcfullduration()
##				if arg.fullduration is not None and adur is not None and adur >= 0:
##					sctx.sched_arcs(arg, 'end', timestamp=timestamp+adur)
			elif action == SR.SCHED_STOP:
				if debugevents: print 'cleanup',`arg`,self.timefunc()
				arg.cleanup_sched(self)
			sctx.event((action, arg), timestamp)

	#
	# Execute a PLAY SR.
	#
	def do_play(self, sctx, node, timestamp):
		if debugevents: print 'do_play',`node`,node.start_time, timestamp,self.timefunc()
		if self.starting_to_play:
			self.starting_to_play = 0
		chan = self.ui.getchannelbynode(node)
		node.set_armedmode(ARM_PLAYING)
		node.startplay(sctx, timestamp)
##		sctx.sched_arcs(node, 'begin', timestamp = timestamp)
##		ndur = node.calcfullduration()
##		if ndur is not None and ndur >= 0:
##			sctx.sched_arcs(node, 'end', timestamp = timestamp+ndur)
		chan.play(node)

	#
	# Execute a PLAY_STOP SR.
	#
	def do_play_stop(self, sctx, node, timestamp):
		if node.playing not in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
			if debugevents: print 'do_play_stop: already stopped',`node`,self.timefunc()
			return
		chan = self.ui.getchannelbynode(node)
		node.set_armedmode(ARM_DONE)
		chan.stopplay(node)
		node.stopplay(timestamp)

	#
	# LOOPSTART SR - Enter a loop at the top.
	# (resets loopcounter to initial value and generates LOOPSTART_DONE)
	#
	def do_loopstart(self, sctx, node, timestamp):
##		print 'LOOPSTART', node
		if not node.moreloops(decrement=1):
			raise error, 'Loopstart without more loops!'
		if not settings.noprearm:
			sctx.arm_moreloops(node)
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
			return
		if not settings.noprearm and node.moreloops():
			# If this is still not the last loop we also
			# set the arm-structures to loop once more.
			sctx.arm_moreloops(node)
		sctx.restartloop(node)
		self.event(sctx, (SR.LOOPSTART_DONE, node), timestamp)
	#
	# Execute an ARM SR
	#
	def do_play_arm(self, sctx, node, timestamp, optional=0):
		if settings.noprearm:
			raise error, 'do_play_arm called when noprearm set'
		chan = self.ui.getchannelbynode(node)
		node.set_armedmode(ARM_ARMING)
		if optional:
			chan.optional_arm(node)
		else:
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
		if debugevents: print 'enterabs',time,priority,action,argument,self.timefunc()
		id = scheduler.enterabs(self, time, priority, action, argument)
		self.updatetimer()
		return id

	def timefunc(self):
		if self.paused:
			return self.time_pause - self.time_origin
		return time.time() - self.time_origin

	def resettimer(self):
		self.time_origin = time.time()
		self.time_pause = self.time_origin

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

#
# GenAllPrearms fills the prearmlists dictionary with all arms needed.
#
def GenAllPrearms(ui, node, channels):
	if settings.noprearm:
		raise error, 'GenAllPrearms called when noprearm set'
	nodetype = node.GetType()
	if nodetype in bagtypes:
		return {}
	if nodetype in leaftypes:
		if node.realpix_body or node.caption_body:
			# Special case for parallel captions to realpix slideshows
			rv = {}
			if node.realpix_body:
				ch = ui.getchannelbynode(node.realpix_body)
				rv[ch] = ArmStorageLeaf(node.realpix_body)
			if node.caption_body:
				ch = ui.getchannelbynode(node.caption_body)
				rv[ch] = ArmStorageLeaf(node.caption_body)
			return rv
		chan = ui.getchannelbynode(node)
		return {chan : ArmStorageLeaf(node)}
	#
	# For now, create internal data structure for each interior node
	#
	prearmlists = {}
	for ch in channels:
		prearmlists[ch] = ArmStorageTree(node)
	for child in node.GetWtdChildren():
		newprearmlists = GenAllPrearms(ui, child, channels)
		for key, value in newprearmlists.items():
			prearmlists[key].append(value)
		# XXXX hack to only play first child in alt nodes
		if nodetype == 'alt':
			break
	for k, v in prearmlists.items():
		if v.isempty():
			del prearmlists[k]
		else:
			v.setparents()
	return prearmlists

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
##		if child.GetType() not in bagtypes:
			unarmallnodes(child)

