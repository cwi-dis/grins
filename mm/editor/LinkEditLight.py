__version__ = "$Id$"

import MMAttrdefs
import windowinterface
from Hlinks import ANCHOR1, ANCHOR2, DIR, TYPE, DIR_1TO2, DIR_2TO1, \
		   DIR_2WAY, TYPE_JUMP, A_SRC_STOP, A_DEST_PLAY
from AnchorDefs import *

class LinkEditLight:
	def __init__(self, toplevel):
		self.toplevel = toplevel
		self.context = toplevel.root.GetContext()
		self.editmgr = toplevel.editmgr
		self.make_interesting()

	def hide(self):
		pass

	def show(self, node = None, aid = None):
		pass

	def is_showing(self):
		return 0

	def fixtitle(self):
		pass

	def get_geometry(self):
		pass

	def save_geometry(self):
		pass

	def destroy(self):
		self.interesting = []
		self.toplevel = None
		self.context = None
		self.editmgr = None

	def make_interesting(self):
		self.interesting = []
		self.__make_interesting(self.toplevel.root)

	def __make_interesting(self, node):
		uid = node.GetUID()
		hlinks = self.context.hyperlinks
		for a in node.GetAttrDef('anchorlist', []):
			if a[A_TYPE] not in SourceAnchors:
				continue
			anchor = uid, a[A_ID]
			if not hlinks.findsrclinks(anchor):
				self.interesting.append(anchor)
		for c in node.GetChildren():
			self.__make_interesting(c)

	def set_interesting(self, anchor):
		self.interesting.append(anchor)

	def has_interesting(self):
		return not not self.interesting

	# Make sure all anchors in 'interesting' actually exist
	def fixinteresting(self):
		dlist = []
		hlinks = self.context.hyperlinks
		for nid, aid in self.interesting:
			node = self.context.mapuid(nid)
			for a in MMAttrdefs.getattr(node, 'anchorlist'):
				if a[A_ID] == aid:
					if a[A_TYPE] not in SourceAnchors or \
					   hlinks.findsrclinks((nid, aid)):
						# exists, but wrong type or has link
						dlist.append((nid, aid))
					break
			else:
				dlist.append((nid,aid))
		for a in dlist:
##			print 'lost anchor:', a
			self.interesting.remove(a)

	def islinksrc(self, node):
		alist = MMAttrdefs.getattr(node, 'anchorlist')
		uid = node.GetUID()
		hlinks = self.context.hyperlinks
		for a in alist:
			anchor = uid, a[A_ID]
			if a[A_TYPE] in SourceAnchors and \
			   hlinks.findsrclinks(anchor):
				return 1
		return 0

	# Method to return a whole-node anchor for a node, or optionally
	# create one.
	# If an anchor of type ATYPE_DEST is requested, we may return one
	# of type ATYPE_WHOLE, since that can serve as a destination anchor.
	# If an anchor of type ATYPE_WHOLE is requested, we may upgrade an
	# anchor of ATYPE_DEST to ATYPE_WHOLE.
	def wholenodeanchor(self, node, type=ATYPE_WHOLE, notransaction = 0, create = 1, interesting = 1):
		alist = MMAttrdefs.getattr(node, 'anchorlist')[:]
		dest = whole = None
		for i in range(len(alist)):
			a = alist[i]
			if a[A_TYPE] == ATYPE_DEST:
				dest = i
			elif a[A_TYPE] == ATYPE_WHOLE:
				whole = i
			if type == a[A_TYPE]:
				if type == ATYPE_DEST or not create:
					return (node.GetUID(), a[A_ID])
				else:
					windowinterface.showmessage("Such an anchor already exists on this node")
					return None
		if not create:
			return None
		if type == ATYPE_DEST and whole is not None:
			# return whole-node anchor for destination anchor
			return (node.GetUID(), alist[whole][A_ID])
		em = self.editmgr
		if not notransaction and not em.transaction():
			return None
		if type == ATYPE_WHOLE and dest is not None:
			# we can upgrade the destination-only anchor
			alist[i] = a = (alist[i][0], ATYPE_WHOLE,) + alist[i][2:]
		else:
			a = ('0', type, [], (0,0), None)
			alist.append(a)
		em.setnodeattr(node, 'anchorlist', alist[:])
		if not notransaction:
			em.commit()
		rv = (node.GetUID(), a[A_ID])
		if interesting:
			self.interesting.append(rv)
		return rv

	def finish_link(self, node, notransaction = 0):
		self.fixinteresting()
		if not self.interesting:
			windowinterface.showmessage('No reasonable sources for link')
			return
		if len(self.interesting) == 1:
			srcanchor = self.interesting[0]
		else:
			anchors = ['Cancel']
			for a in self.interesting:
				anchors.append(self.makename(a))
			i = windowinterface.multchoice('Choose source anchor',
				  anchors, 0)
			if i == 0:
				return
			srcanchor = self.interesting[i-1]
		dstanchor = self.wholenodeanchor(node, type=ATYPE_DEST)
		if not dstanchor:
			return
		em = self.editmgr
		if not notransaction and not em.transaction():
			return
		self.interesting.remove(srcanchor)
		if dstanchor in self.interesting:
			self.interesting.remove(dstanchor)
		link = srcanchor, dstanchor, DIR_1TO2, TYPE_JUMP, A_SRC_STOP, A_DEST_PLAY
		em.addlink(link)
		if not notransaction:
			em.commit()

	def makename(self, anchor):
		if type(anchor) is not type(()):
			return anchor
		uid, aid = anchor
		if '/' in uid:
			return aid + ' in ' + uid
		node = self.context.mapuid(uid)
		nodename = node.GetRawAttrDef('name', '#' + uid)
		if self.findanchor(anchor)[A_TYPE] == ATYPE_DEST:
			return nodename
		if type(aid) is not type(''): aid = `aid`
		return nodename + '.' + aid

	def findanchor(self, anchor):
		if anchor is not None:
			if type(anchor) is not type(()):
				return (anchor, ATYPE_DEST, [], (0,0))
			uid, aid = anchor
			if '/' in uid:
				# external anchor
				return (aid, ATYPE_DEST, [], (0,0))
			node = self.context.mapuid(uid)
			for a in MMAttrdefs.getattr(node, 'anchorlist'):
				if a[A_ID] == aid:
					return a
		return None
