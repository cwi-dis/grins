__version__ = "$Id$"

#
# Selecter module - Handles hyperjumps and assigning contexts to
# bagnode-runslots.
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
		self.runslots = []
		self.bags_needing_done_ev = []

	#
	# State transitions.
	#
	def play(self):
		if self.playing:
			raise 'Already playing'
		self.reset()
		list = self.mkbaglist(self.userplayroot)
		if not list:
			return
		list = self.killconflictingbags(list)
		if not self.startbaglist(list, None, timestamp = 0):
			return
		self.playing = 1
		self.updateuibaglist()
		self.showstate()
	#
	def stop(self):
		if self.playing:
			self.scheduler.stop_all()
		else:
			self.fullreset()

	def stopped(self):
		self.runslots = []
		self.bags_needing_done_ev = []
		self.playing = 0
		self.updateuibaglist()
		self.showstate()
	#
	def reset(self):
		self.scheduler.resettimer()
	#
	# Routines to manipulate run slots
	#
	# mkbaglist - Called when a bag is played to select the node in it.
	# Returns a list of bags and nodes to play.
	#
	def mkbaglist(self, node):
		list = [(node, None, None, None)]
		# XXXX has to be changed for alt nodes
		while node.GetType() in bagtypes:
			newnode = choosebagitem(node, 1)
			if newnode is None:
				return None
			list.append((newnode, None, node, node))
			node = newnode
		list.reverse()
		return list
	#
	# findbaglist - Find the list of bags leading up to a node.
	#
	def findbaglist(self, node):
		parent = None
		if node:
			mini = node.FindMiniDocument()
			bag = mini.FindMiniBag()
			if bag:
				parent = bag.FindMiniDocument()
		else:
			mini = None
			bag = None
		list = [(mini, None, bag, parent)]
		while parent:
			mini = parent
			bag = mini.FindMiniBag()
			if bag:
				parent = bag.FindMiniDocument()
			else:
				parent = None
			list.append((mini, None, bag, parent))
		return list
	#
	# killconflictingbags - Take a bag list, kill conflicting minidocs
	# and return the new bag list.
	#
	def killconflictingbags(self, baglist):
##		print 'killconflictingbags:', baglist
		newlist = []
		for slot in baglist:
			newlist.append(slot)
			mini, sctx, bag, parent = slot
			i = self.findslotindexbybag(bag)
			if i is not None:
##				print 'kcb: found', bag, 'in', i
				# Ok, this bag is currently active.
				# Kill whatever is in it (and below)
				# and return the list upto here as what to
				# execute.
				oldslot = self.runslots[i]
				self.killslot(oldslot)
##				print 'kcb:newlist:', newlist
				return newlist
		return newlist
	#
	# findslotindexbybag - Return runslot index of given bag, or 'None'.
	#
	def findslotindexbybag(self, bag):
		for i in range(len(self.runslots)):
			if self.runslots[i][RS_BAG] is bag:
				return i
		return None
	#
	# findslotbybag - Return runslot of given bag, or None.
	#
	def findslotbybag(self, bag):
		i = self.findslotindexbybag(bag)
		if i is None:
			return None
		return self.runslots[i]
	#
	# findslotbynode - Return runslot of given node, or 'None'.
	#
	def findslotbynode(self, node):
		for i in range(len(self.runslots)):
			if self.runslots[i][RS_NODE] is node:
				return self.runslots[i]
		return None
	#
	# findslotbysctx - Return runslot of given sctx, or 'None'.
	#
	def findslotbysctx(self, sctx):
		for i in range(len(self.runslots)):
			if self.runslots[i][RS_SCTX] is sctx:
				return self.runslots[i]
		return None
	#
	# startbaglist - Start everything in a bag.
	#
	def startbaglist(self, baglist, prevslot, timestamp = None):
		for slot in baglist:
			if slot[RS_NODE].GetType() not in bagtypes:
				mini, sctx, bag, parent = slot
				if prevslot:
					seeknode = prevslot[RS_BAG]
				else:
					seeknode = None
				sctx = self.scheduler.play(mini, seeknode, \
					  None, None, timestamp)
				if not sctx:
					dummy = self.killconflictingbags( \
						  baglist)
					return 0
				slot = mini, sctx, bag, parent
			self.runslots.append(slot)
			prevslot = slot
		return 1

	#
	# killslot - Remove a run slot
	#
	def killslot(self, slot):
##		print 'killslot:', slot
		node, sctx, bag, parent = slot
		self.runslots.remove(slot)
		if sctx:
			sctx.stop()
##		print 'RUNSLOTS after kill:', self.runslots
		tokill = []
		for slot in self.runslots:
			if node and slot[RS_PARENT] is node:
				tokill.append(slot)
##		print 'dependent kills:'
		for slot in tokill:
			self.killslot(slot)
##		print 'killslot done'
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
				resolved = x.isresolved()
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
		self.scheduler.sctx_list[0].gototime(path[0], gototime, timestamp, path)
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
	# bagevent is called by the scheduler to start/stop a bag.
	#
	def bag_event(self, sctx, (event, bag)):
## 		print 'bagevent in', sctx, SR.ev2string((event, bag))
		if event == SR.BAG_START:
			if self.findslotbybag(bag) is not None:
##				print 'bag_event: Bag already active:', bag
##				self.dumpbaglist()
				return
			# Find corresponding minidoc
			slot = self.findslotbysctx(sctx)
			if not slot:
				self.dumpbaglist()
				raise 'bag_event: called from unknown sctx:', \
					  sctx
			parent = slot[RS_NODE]
			node = choosebagitem(bag, 0)
			if node:
				new_sctx = self.scheduler.play(node, \
					  None, None, None)
			else:
##				print 'bag_event: no node to play'
				new_sctx = None
			if not new_sctx:
				node = None
##				print 'bag_event: early termination of choice node'
				self.scheduler.event(sctx, (SR.BAG_DONE, bag))
			else:
				self.bags_needing_done_ev.append(bag)
			self.runslots.append((node, new_sctx, bag, parent))
		elif event == SR.BAG_STOP:
			slot = self.findslotbybag(bag)
			if slot is None:
				print 'bag_event: Choice node not active:', bag
				self.dumpbaglist()
				return
			self.killslot(slot)
		self.updateuibaglist()
	#
	# sctx_empty is called from the scheduler when a context has become
	# empty.
	def sctx_empty(self, sctx):
##		print 'sctx_empty:', sctx
		slot = self.findslotbysctx(sctx)
		self.runslots.remove(slot)
		d1, d2, bag, parent = slot
		self.runslots.append((None, None, bag, parent))
		sctx.stop()
		parent_slot = self.findslotbynode(parent)
		if not parent_slot:
			raise 'sctx_empty: parent not running:', parent
		d1, parent_sctx, d2, d3 = parent_slot
		if bag in self.bags_needing_done_ev:
##			print SR.ev2string((SR.BAG_DONE, bag)), 'in', \
##				  parent_sctx
			self.scheduler.event(parent_sctx, (SR.BAG_DONE, bag))
			self.bags_needing_done_ev.remove(bag)
		self.updateuibaglist()

	#
	# Create baglist for user interface
	#
	def updateuibaglist(self):
		list = []
		for mini, sctx, bag, parent in self.runslots:
			if sctx:
				str = 'node '
			else:
				str = 'choice '
			str = str + nodename(mini)
			str = str + ' in '
			str = str + nodename(bag)
			str = str + ' @ ' + nodename(parent)
			list.append(str)
		self.makeslotmenu(list)

	def dumpbaglist(self):
		list = []
		for mini, sctx, bag, parent in self.runslots:
			if sctx:
				str = 'node '
			else:
				str = 'choice '
			str = str + nodename(mini)
			str = str + ' in '
			str = str + nodename(bag)
			str = str + ' @ ' + nodename(parent)
			print str

def nodename(node):
	if node is None:
		return '<none>'
	str = MMAttrdefs.getattr(node, 'name')
	str = str + '#' + node.GetUID()
	return str

# Choose an item from a bag, or None if the bag is empty
# This is a modal dialog!
# (Also note the similarity with NodeEdit._showmenu...)

def choosebagitem(node, interactive):
	indexname = MMAttrdefs.getattr(node, 'bag_index')
	children = node.GetChildren()
	if not children:
		return None
	list = []
	for child in children:
		name = MMAttrdefs.getattr(child, 'name')
		if name == '':
			name = '???'
		elif name == indexname:
			return child
		list.append(name)
	if not interactive:
		return None
	list.append('Cancel')
	prompt = 'Please select an item\nfrom the choice node:'
	choice = windowinterface.multchoice(prompt, list, len(list) - 1)
	if 0 <= choice < len(children):
		return children[choice]
	else:
		return None
