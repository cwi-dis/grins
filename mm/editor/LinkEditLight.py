__version__ = "$Id$"

import MMAttrdefs
import windowinterface
from Hlinks import ANCHOR1, ANCHOR2, DIR, TYPE, DIR_1TO2, DIR_2TO1, \
		   DIR_2WAY, TYPE_JUMP
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
		for aid, atype, aargs in node.GetAttrDef('anchorlist', []):
			if atype not in SourceAnchors:
				continue
			anchor = uid, aid
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
			alist = MMAttrdefs.getattr(node, 'anchorlist')
			for a in alist:
				if a[A_ID] == aid:
					if a[A_TYPE] not in SourceAnchors or \
					   hlinks.findsrclinks((nid, aid)):
						# exists, but wrong type or has link
						dlist.append((nide, aid))
					break
			else:
				dlist.append((nid,aid))
		for a in dlist:
##			print 'lost anchor:', a
			self.interesting.remove(a)

	# Method to return a whole-node anchor for a node, or optionally
	# create one.
	def wholenodeanchor(self, node, type=ATYPE_WHOLE, notransaction = 0, create = 1):
		alist = MMAttrdefs.getattr(node, 'anchorlist')[:]
		for a in alist:
			if type == a[A_TYPE]:
				if type == ATYPE_DEST or not create:
					return (node.GetUID(), a[A_ID])
				else:
					windowinterface.showmessage("Such an anchor already exists on this node")
					return None
		if not create:
			return None
		em = self.editmgr
		if not notransaction and not em.transaction():
			return None
		a = ('0', type, [])
		alist.append(a)
		em.setnodeattr(node, 'anchorlist', alist[:])
		if not notransaction:
			em.commit()
		rv = (node.GetUID(), '0')
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
		link = srcanchor, dstanchor, DIR_1TO2, TYPE_JUMP
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
				return (anchor, ATYPE_DEST, ())
			uid, aid = anchor
			if '/' in uid:
				# external anchor
				return (aid, ATYPE_DEST, ())
			node = self.context.mapuid(uid)
			for a in MMAttrdefs.getattr(node, 'anchorlist'):
				if a[A_ID] == aid:
					return a
		return None
