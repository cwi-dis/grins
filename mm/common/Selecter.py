__version__ = "$Id$"

#
# Selecter module - Handles hyperjumps and assigning contexts.
#

import MMAttrdefs
import Scheduler
from AnchorDefs import *
from MMTypes import *
from MMExc import *			# exceptions
import MMStates
from Hlinks import TYPE_JUMP, TYPE_CALL, TYPE_FORK, ANCHOR2, TYPE, STYPE, DTYPE
import windowinterface
import SR

class Selecter:
	def __init__(self):
		self.scheduler = Scheduler.Scheduler(self)

	#
	# State transitions.
	#
	def play(self, starttime = 0):
		if self.playing:
			raise 'Already playing'
		self.reset(starttime)
		self.sctx = self.scheduler.play(self.userplayroot, None, None, None, timestamp = 0)
		if not self.sctx:
			return
		self.playing = 1
		paused = self.scheduler.paused
		self.scheduler.paused = 0
		self.sctx.flushqueue(starttime)
		self.scheduler.paused = paused
		self.showstate()
	#
	def stop(self):
		if self.playing:
			self.scheduler.stop_all(self.scheduler.timefunc())
		else:
			self.fullreset()

	def stopped(self):
		self.playing = 0
		self.showstate()
	#
	def reset(self, starttime = 0):
		self.scheduler.resettimer(starttime)
	#
	# Callback for anchor activations, called by channels.
	# Return 1 if the anchor fired, 0 if nothing happened.
	# XXXX This routine should also get a source-context arg.
	#
	def anchorfired(self, old_sctx, node, anchorlist, arg):
		#self.showpauseanchor(0) # also see Scheduler.py
		destlist = []
		pause_anchor = 0
		# Firing an anchor continues the player if it was paused.
		if self.scheduler.getpaused():
			self.pause(0)
		for i in anchorlist:
			if i[1] == ATYPE_PAUSE:
				pause_anchor = 1
			aid = (node.GetUID(), i[0])
			rv = self.context.hyperlinks.findsrclinks(aid)
			destlist = destlist + rv
		if not destlist:
			if not pause_anchor:
				windowinterface.showmessage( \
				'No hyperlink source at this anchor')
			return 0
		root = node.GetRoot()
		for dest in destlist:
			if not self.context.isgoodlink(dest, root):
				continue
			if not self.gotoanchor(dest, arg):
				return 0
## 		if arg:
## 			windowinterface.showmessage('Args:'+`arg`)
		return 1

	def gotoanchor(self, link, arg):
		anchor2 = link[ANCHOR2]
		ltype = link[TYPE]
		if ltype != TYPE_JUMP or type(anchor2) is not type(()) or \
		   '/' in anchor2[0]:	# cmif compatibility
			return self.toplevel.jumptoexternal(anchor2, ltype, link[STYPE], link[DTYPE])
		dest_uid, dest_aid = anchor2
		try:
			seek_node = self.context.mapuid(dest_uid)
		except NoSuchUIDError:
			windowinterface.showmessage('Dangling hyperlink selected')
			return 0
		return self.gotonode(seek_node, dest_aid, arg)

	def gotonode(self, seek_node, dest_aid, arg):
		# First check whether this is an indirect anchor
		if Scheduler.debugevents: print 'gotonode',seek_node,dest_aid,arg
		self.scheduler.setpaused(1)
		timestamp = self.scheduler.timefunc()
		sctx = self.scheduler.sctx_list[0]
		if seek_node.playing != MMStates.IDLE:
			# case 1, the target element is or has been active
			if seek_node.playing in (MMStates.PLAYED, MMStates.FROZEN):
				gototime = seek_node.time_list[0][0]
			else:
				gototime = seek_node.start_time
		else:
			# XXX
			x = seek_node
			path = []
			while x is not None:
				resolved = x.isresolved(sctx)
				path.append((x, resolved))
				if resolved is not None:
					break
				x = x.GetSchedParent()
			path.reverse()
			for x, resolved in path:
				if x.playing in (MMStates.PLAYING, MMStates.PAUSED):
					gototime = x.start_time
				elif x.playing in (MMStates.PLAYED, MMStates.FROZEN):
					gototime = x.time_list[0][0]
				elif resolved is not None:
					gototime = resolved
				else:
					x.start_time = gototime
		self.scheduler.settime(gototime)
		if seek_node.GetType() == 'switch':
			x = seek_node.ChosenSwitchChild()
			if not x:
				x = seek_node.GetSchedParent()
		else:
			x = seek_node
		path = []
		while x is not None:
			path.append(x)
			x = x.GetSchedParent()
		path.reverse()
		sctx.gototime(path[0], gototime, timestamp, path)
		self.scheduler.setpaused(0, gototime)
		return 0

	#
	# sctx_empty is called from the scheduler when a context has become
	# empty.
	def sctx_empty(self, sctx, curtime):
		sctx.stop(curtime)
		self.sctx = None

def nodename(node):
	if node is None:
		return '<none>'
	str = MMAttrdefs.getattr(node, 'name')
	str = str + '#' + node.GetUID()
	return str
