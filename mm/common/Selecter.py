__version__ = "$Id$"

#
# Selecter module - Handles hyperjumps and assigning contexts.
#

import MMAttrdefs
from Scheduler import Scheduler
from AnchorDefs import *
from MMTypes import *
from MMExc import *			# exceptions
import MMStates
from Hlinks import TYPE_JUMP, TYPE_CALL, TYPE_FORK, ANCHOR2, TYPE, STYPE, DTYPE
import windowinterface
import SR

[RS_NODE, RS_SCTX, RS_BAG, RS_PARENT] = range(4)

class Selecter:
	def __init__(self):
		self.scheduler = Scheduler(self)

	#
	# State transitions.
	#
	def play(self):
		if self.playing:
			raise 'Already playing'
		self.reset()
		self.sctx = self.scheduler.play(self.userplayroot, None, None, None, timestamp = 0)
		if not self.sctx:
			return
		self.playing = 1
		self.showstate()
	#
	def stop(self):
		if self.playing:
			self.scheduler.stop_all()
		else:
			self.fullreset()

	def stopped(self):
		self.playing = 0
		self.showstate()
	#
	def reset(self):
		self.scheduler.resettimer()
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
		for dest in destlist:
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
		list = self.followcompanchors(seek_node, dest_aid)
		if list is not None:
			rv = 0
			for node_id, aid in list:
				try:
					node = self.context.mapuid(node_id)
				except NoSuchUIDError:
					windowinterface.showmessage('Dangling: \n'+\
						  `(node_id, aid)`)
					continue
				if self.gotonode(node, aid, arg):
					rv = 1
			return rv
		# It is not a composite anchor. Continue
		self.scheduler.setpaused(1)
		timestamp = self.scheduler.timefunc()
		sctx = self.scheduler.sctx_list[0]
		if seek_node.playing != MMStates.IDLE:
			# case 1, the target element is or has been active
			if seek_node.playing == MMStates.PLAYED: # XXX or FROZEN?
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
				if x.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN):
					gototime = x.start_time
				elif x.playing == MMStates.PLAYED:
					gototime = x.time_list[0][0]
				elif resolved is not None:
					gototime = resolved
				else:
					x.start_time = gototime
		self.scheduler.settime(gototime)
		x = seek_node
		path = []
		while x is not None:
			path.append(x)
			x = x.GetSchedParent()
		path.reverse()
		sctx.gototime(path[0], gototime, timestamp, path)
		self.scheduler.setpaused(0)
		return 0

	def followcompanchors(self, node, aid):
		if not aid:
			return None
		for a in MMAttrdefs.getattr(node, 'anchorlist'):
			if a.aid == aid and a.atype == ATYPE_COMP:
				return arg
		return None
	#
	# sctx_empty is called from the scheduler when a context has become
	# empty.
	def sctx_empty(self, sctx):
		sctx.stop()
		self.sctx = None

def nodename(node):
	if node is None:
		return '<none>'
	str = MMAttrdefs.getattr(node, 'name')
	str = str + '#' + node.GetUID()
	return str
