#
# Selecter module - Handles hyperjumps and assigning contexts to
# bagnode-runslots.
#

import MMAttrdefs
from Scheduler import Scheduler, END_PAUSE, END_STOP, END_KEEP
from AnchorDefs import *
from MMNode import leaftypes
import dialogs
import SR

[RS_NODE, RS_SCTX, RS_BAG, RS_PARENT] = range(4)

class Selecter:
	def init(self):
		self.scheduler = Scheduler().init(self)
		self.runslots = []
		self.bags_needing_done_ev = []
		return self

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
		if not self.startbaglist(list):
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
		self.stopped()

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
		while node.GetType() == 'bag':
			newnode = choosebagitem(node, 1)
			if newnode == None:
				return None
			list.append(newnode, None, node, node)
			node = newnode
		list.reverse()
		return list
	#
	# findbaglist - Find the list of bags leading up to a node.
	#
	def findbaglist(self, node):
		mini = findminidocument(node)
		bag = findminibag(mini)
		parent = findminidocument(bag)
		list = [(mini, None, bag, parent)]
		while parent:
			mini = parent
			bag = findminibag(mini)
			parent = findminidocument(bag)
			list.append(mini, None, bag, parent)
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
			if i <> None:
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
			if self.runslots[i][RS_BAG] == bag:
				return i
		return None
	#
	# findslotbybag - Return runslot of given bag, or None.
	#
	def findslotbybag(self, bag):
		i = self.findslotindexbybag(bag)
		if i == None:
			return None
		return self.runslots[i]
	#
	# findslotbynode - Return runslot of given node, or 'None'.
	#
	def findslotbynode(self, node):
		for i in range(len(self.runslots)):
			if self.runslots[i][RS_NODE] == node:
				return self.runslots[i]
		return None
	#
	# findslotbysctx - Return runslot of given sctx, or 'None'.
	#
	def findslotbysctx(self, sctx):
		for i in range(len(self.runslots)):
			if self.runslots[i][RS_SCTX] == sctx:
				return self.runslots[i]
		return None
	#
	# startbaglist - Start everything in a bag.
	#
	def startbaglist(self, baglist):
		prevslot = None
		for slot in baglist:
			if slot[RS_NODE].GetType() <> 'bag':
				mini, sctx, bag, parent = slot
				if prevslot:
					seeknode = prevslot[RS_BAG]
				else:
					seeknode = None
				sctx = self.scheduler.play(mini, seeknode, \
					  None, END_STOP)
				if not sctx:
					dummy = self.killconflictingbags( \
						  baglist)
					return 0
				slot = mini, sctx, bag, parent
			self.runslots.append(slot)
		return 1
		
	#
	# killslot - Remove a run slot
	#
	def killslot(self, slot):
##		print 'killslot:', slot
		node, sctx, bag, parent = slot
		if sctx:
			sctx.stop()
		self.runslots.remove(slot)
##		print 'RUNSLOTS after kill:', self.runslots
		tokill = []
		for slot in self.runslots:
			if node and slot[RS_PARENT] == node:
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
	def anchorfired(self, old_sctx, node, anchorlist):
		self.showpauseanchor(0)
		self.toplevel.setwaiting()
		destlist = []
		pause_anchor = 0
		# Firing an anchor continues the player if it was paused.
		if self.scheduler.getpaused():
			self.pause(0)
		for i in anchorlist:
			if i[A_TYPE] == ATYPE_PAUSE:
				pause_anchor = 1
			aid = (node.GetUID(), i[A_ID])
			rv = self.context.hyperlinks.findsrclinks(aid)
			destlist = destlist + rv
		if not destlist:
			self.toplevel.setready()
			if not pause_anchor:
				dialogs.showmessage( \
				'No hyperlink source at this anchor')
			return 0
		for dest in destlist:
			if not self.gotoanchor(dest):
				return 0
		return 1

	def gotoanchor(self, (anchor1, anchor2, dir, type)):
		if type <> 0:
			dialogs.showmessage('Sorry, will JUMP anyway')
		dest_uid, dest_aid = anchor2
		if '/' in dest_uid:
			if dest_uid[-2:] == '/1':
				dest_uid = dest_uid[:-2]
			return self.toplevel.jumptoexternal(dest_uid, dest_aid)
		try:
			seek_node = self.context.mapuid(dest_uid)
		except NoSuchUIDError:
			self.toplevel.setready()
			dialogs.showmessage('Dangling hyperlink selected')
			return 0
		return self.gotonode(seek_node, dest_aid)

	def gotonode(self, seek_node, dest_aid):
		# First check whether this is an indirect anchor
		list = self.followcompanchors(seek_node, dest_aid)
		if list <> None:
			rv = 0
			for node_id, aid in list:
				try:
					node = self.context.mapuid(node_id)
				except NoSuchUIDError:
					self.toplevel.setready()
					dialogs.showmessage('Dangling: \n'+\
						  `(node_id, aid)`)
					continue
				if self.gotonode(node, aid):
					rv = 1
			return rv
		# It is not a composite anchor. Continue
		while seek_node.GetType() == 'bag':
			dest_aid = None
			seek_node = choosebagitem(seek_node, 1)
			if seek_node == None:
				self.toplevel.setready()
				return 0
		baglist = self.findbaglist(seek_node)
		baglist = self.killconflictingbags(baglist)
		if not self.startbaglist(baglist[1:]):
			return 0
		mini, sctx, bag, parent = baglist[0]
		new_sctx = self.scheduler.play(mini, seek_node, dest_aid, \
			  END_STOP)
		if not new_sctx:
			dummy = self.killconflictingbags(baglist)
			self.toplevel.setready()
			return 0
		self.runslots.append(mini, new_sctx, bag, parent)
		self.updateuibaglist()
		return 1
	#
	def followcompanchors(self, node, aid):
		if not aid:
			return None
		alist = MMAttrdefs.getattr(node, 'anchorlist')
		for id, tp, arg in alist:
			if id == aid and tp == ATYPE_COMP:
				return arg
		return None
	#
	# bagevent is called by the scheduler to start/stop a bag.
	#
	def bag_event(self, sctx, (event, bag)):
##		print 'bagevent in', sctx, SR.ev2string((event, bag))
		if event == SR.BAG_START:
			if self.findslotbybag(bag) <> None:
				print 'bag_event: Bag already active:', bag
				self.dumpbaglist()
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
					  None, None, END_STOP)
			else:
##				print 'bag_event: no node to play'
				new_sctx = None
			if not new_sctx:
				node = None
##				print 'bag_event: early termination of bag'
				self.scheduler.event(sctx, (SR.BAG_DONE, bag))
			else:
				self.bags_needing_done_ev.append(bag)
			self.runslots.append(node, new_sctx, bag, parent)
		elif event == SR.BAG_STOP:
			slot = self.findslotbybag(bag)
			if slot == None:
				print 'bag_event: Bag not active:', bag
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
		self.runslots.append(None, None, bag, parent)
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
				str = 'bag '
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
				str = 'bag '
			str = str + nodename(mini)
			str = str + ' in '
			str = str + nodename(bag)
			str = str + ' @ ' + nodename(parent)
			print str

def nodename(node):
	if node == None:
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
		type = child.GetType()
		if type == 'bag':
			colorindex = 60 # XXX BlockView.BAGCOLOR
		elif type in leaftypes:
			colorindex = 61 # XXX BlockView.LEAFCOLOR
		else:
			colorindex = None
		list.append((name, colorindex))
	if not interactive:
		return None
	list.append('Cancel')
	prompt = 'Please select an item\nfrom the bag:'
	choice = dialogs.multchoice(prompt, list, len(list) - 1)
	if 0 <= choice < len(children):
		return children[choice]
	else:
		return None

# Find the root of a node's mini-document

def findminidocument(node):
	if not node:
		return None
	path = node.GetPath()
	if len(path) <= 1:
		# The root node
		return node
	i = len(path)-2  # Index to parent of current node
	while i >= 0 and path[i].GetType() <> 'bag':
		i = i-1
	return path[i+1]

# Find the nearest bag given a minidocument.
def findminibag(mini):
	bag = mini.GetParent()
	if bag and bag.GetType() <> 'bag':
		raise 'findminibag: minidoc not rooted in a bag!'
	return bag
