__version__ = "$Id$"

# Anchor editor modeless dialog


import windowinterface
import MMExc
import MMAttrdefs
from MMNode import alltypes, leaftypes, interiortypes
import settings


# The 'anchors' attribute of a node is a list of triples.
# Each triple has the form (id, type, args):
# - id:   a number identifying the anchor uniquely (within this node)
# - type: one of the ATYPE_* constants defined in AnchorDefs
# - args: used by the channel to define what the anchor looks like
# The form of args depends on what the channel puts there.
# It is normally a list of values, e.g. [x0, y0, x1, y1] giving the
# boundaries of a box, or an empty list if there is no extra information.

from AnchorDefs import *

CMIF_TypeValues = [ ATYPE_WHOLE, ATYPE_DEST, ATYPE_NORMAL, ATYPE_PAUSE,
	       ATYPE_AUTO, ATYPE_COMP, ATYPE_ARGS ]
CMIF_TypeLabels = [  'whole node', 'dest only', 'partial node', 'pausing',
		'auto-firing', 'composite', 'with arguments']
SMIL_TypeValues = [ ATYPE_WHOLE, ATYPE_DEST, ATYPE_NORMAL ]
SMIL_TypeLabels = [  'whole node', 'dest only', 'partial node']

FALSE, TRUE = 0, 1

# Top-level interface to show/hide a node's anchor editor

def showanchoreditor(toplevel, node):
	try:
		anchoreditor = node.anchoreditor
	except AttributeError:
		anchoreditor = AnchorEditor(toplevel, node)
		node.anchoreditor = anchoreditor
	else:
		anchoreditor.pop()


# Class used to implement an achor editing dialog.
# Each instance is associated with a different node.
# Note that the data is in three places:
# (1) in the node (or its attribute list)
# (2) in the anchor editor object
# (3) in the FORMS object
# Transfers are as follows:
# (1) -> (2): when opened, or by [Restore]
# (1) <- (2): on [OK] / [Accept]
# (2) -> (3): when (1) -> (2) is done or when data is changed (e.g. Add / Del)
# (2) <- (3): by callback functions or just before [OK] / [Accept]

from AnchorEditDialog import AnchorEditorDialog

class AnchorEditor(AnchorEditorDialog):

	def __init__(self, toplevel, node):
		if settings.get('cmif'):
			self.TypeValues = CMIF_TypeValues
			self.TypeLabels = CMIF_TypeLabels
		else:
			self.TypeValues = SMIL_TypeValues
			self.TypeLabels = SMIL_TypeLabels
		self.node = node
		self.toplevel = toplevel
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		self.anchorlist = []
		self.focus = None # None or 0...len(self.anchorlist)-1
		self.changed = 0
		self.editable = 1
		self.getvalues(TRUE)
		names = self.makelist()

		AnchorEditorDialog.__init__(self, self.maketitle(), self.TypeLabels,
					    names, self.focus)

		self.show_focus()
		self.editmgr.register(self)

	def __repr__(self):
		return '<AnchorEditor instance, node=' + `self.node` + '>'

	def getcontext(self):
		return self.context

	def stillvalid(self):
		return self.node.GetRoot() is self.root

	def transaction(self):
		return 1

	def commit(self):
		if not self.stillvalid():
			self.close()
		else:
			self.settitle(self.maketitle())
			self.getvalues(FALSE)
			self.selection_seteditable(self.editable)
			self.updateform()

	def rollback(self):
		pass

	def kill(self):
		self.close()

	def getvalues(self, force):
		# If 'force' is false, don't get the values if the
		# user has already edited them in any way; this is
		# needed whe we get a commit() from elsewhere.
		if self.changed and not force:
			return
		self.uid = self.node.GetUID()
		self.name = self.node.GetRawAttrDef('name', self.uid)
		hasfixed = self.toplevel.player.updatefixedanchors(self.node)
		self.editable = (not hasfixed)
		anchorlist = MMAttrdefs.getattr(self.node, 'anchorlist')
		if anchorlist <> self.anchorlist:
			# Communicate new anchors to Link editor:
			for a in anchorlist:
				if not a in self.anchorlist:
					aid = (self.uid, a[A_ID])
					self.toplevel.links.set_interesting(
						  aid)
			self.anchorlist = anchorlist[:]
			if self.anchorlist:
				self.focus = 0
			else:
				self.focus = None
		self.changed = 0

	def setvalues(self):
		em = self.editmgr
		if not em: # DEBUG
			self.changed = 0
			return 1
		# check uniqueness of anchor names
		names = {}
		for anchor in self.anchorlist:
			if names.has_key(anchor[0]):
				windowinterface.showmessage('Anchor names not unique')
				return 0
			names[anchor[0]] = 0
		if not em.transaction(): return 0
		n = self.node
		old_alist = MMAttrdefs.getattr(self.node, 'anchorlist')
		new_alist = self.anchorlist[:]
		self.changed = 0
		em.setnodeattr(n, 'anchorlist', new_alist or None)
		if old_alist is None:
			old_alist = []
		else:
			old_alist = map(lambda a: a[A_ID], old_alist)
		new_alist = map(lambda a: a[A_ID], new_alist)
		for aid in new_alist or []:
			if aid not in old_alist:
				# new anchor
				aid = (self.uid, aid)
				self.toplevel.links.set_interesting(aid)
		for aid in old_alist:
			if aid not in new_alist:
				# deleted anchor
				aid = (self.uid, aid)
				hlinks = self.context.hyperlinks
				for link in hlinks.findalllinks(aid, None):
					hlinks.dellink(link)
		em.commit()
		return 1

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Anchors for node ' + name

	# Fill form from local data.  Clear the form beforehand.
	#
	def makelist(self):
		names = []
		for i in self.anchorlist:
			id = i[A_ID]
			names.append(id)
		return names

	def updateform(self):
		names = self.makelist()
		self.selection_setlist(names, self.focus)
		self.show_focus()

	def show_focus(self):
		if self.focus is None:
			self.edit_setsensitive(0)
			self.delete_setsensitive(0)
			self.selection_seteditable(0)
			self.export_setsensitive(0)
			self.type_choice_hide()
			self.composite_hide()
		else:
			self.show_type()

	def show_type(self):
		if self.focus is None:
			print 'AnchorEdit: show_type without focus!'
			return
		a = self.anchorlist[self.focus]
		loc = a[A_ARGS]
		type = a[A_TYPE]
		editable = self.editable or type in WholeAnchors
		self.edit_setsensitive(editable)
		self.delete_setsensitive(editable)
		self.selection_setselection(self.focus)
		self.selection_seteditable(editable)
		self.export_setsensitive(1)
		self.type_choice_show()
		for i in range(len(self.TypeValues)):
			if type == self.TypeValues[i]:
				self.type_choice_setchoice(i)
		if type == ATYPE_COMP:
			self.composite_show()
			self.edit_setsensitive(0)
			self.composite_setlabel('Composite: ' + `loc`)
			for i in range(len(self.TypeValues)):
				self.type_choice_setsensitive(
					i, self.TypeValues[i] == ATYPE_COMP)
			return
		for i in range(len(self.TypeValues)):
			if self.TypeValues[i] == ATYPE_COMP:
				self.type_choice_setsensitive(i, 0)
			elif self.TypeValues[i] in WholeAnchors:
				self.type_choice_setsensitive(i, self.editable or type in WholeAnchors)
			else:
				# can choose this type if node is
				# editable, or if the current value is
				# a non-editable type (i.e., the
				# anchor must already exist in the
				# data).
				self.type_choice_setsensitive(i, self.editable or type not in WholeAnchors)
		self.composite_hide()
		if self.focus is not None:
			self.edit_setsensitive(self.editable)
			self.selection_seteditable(self.editable or self.anchorlist[self.focus][A_TYPE] in WholeAnchors)
		else:
			self.edit_setsensitive(0)
			self.selection_seteditable(0)

	def set_type(self, type):
		if self.focus is None:
			print 'AnchorEdit: set_type without focus!'
			return
		self.toplevel.setwaiting()
		old = new = self.anchorlist[self.focus]
		if type is None:
			type = new[A_TYPE]
		if type in WholeAnchors:
			new = (new[0], type, [])
		else:
			new = (new[0], type, new[2])
			if self.editable:
				self.toplevel.player.defanchor(
					self.node, new, self._anchor_cb)
				return
		if new <> old:
			self.anchorlist[self.focus] = new
			self.changed = 1
		self.show_type()

	def _anchor_cb(self, new):
		if self.anchorlist[self.focus] != new:
			self.anchorlist[self.focus] = new
			self.changed = 1
		self.show_type()

	def close(self):
		self.editmgr.unregister(self)
		AnchorEditorDialog.close(self)
		del self.node.anchoreditor
		del self.node
		del self.toplevel
		del self.context
		del self.editmgr
		del self.root
		del self.anchorlist

	#
	# Standard callbacks
	#
	def cancel_callback(self):
		self.close()

	def restore_callback(self):
		self.getvalues(TRUE)
		self.selection_seteditable(self.editable)
		self.updateform()

	def apply_callback(self):
		if self.changed:
			dummy = self.setvalues()

	def ok_callback(self):
		if not self.changed or self.setvalues():
			self.close()

	#
	# Private callbacks
	#
	def anchor_callback(self):
		focus = self.selection_getselection()
		if focus != self.focus:
			self.focus = focus
			self.show_focus()

	def add_callback(self):
		self.changed = 1
		maxid = 0
		for id, atype, args in self.anchorlist:
			try:
				id = eval('0+'+id)
			except:
				pass
			if type(id) is type(0) and id > maxid:
				maxid = id
		id = `maxid + 1`
		#name = '#' + self.name + '.' + id
		name = id
		self.anchorlist.append((id, ATYPE_WHOLE, []))
		self.selection_append(name)
		self.focus = len(self.anchorlist)-1
		self.show_focus()

	def id_callback(self):
		if self.focus is None or \
		   self.focus != self.selection_getselection():
			return
		anchor = self.anchorlist[self.focus]
		id = self.selection_gettext()
		anchor = (id, anchor[1], anchor[2])
		if self.anchorlist[self.focus] == anchor:
			return
		self.changed = 1
		self.anchorlist[self.focus] = anchor
		self.selection_replaceitem(self.focus, id)
		self.show_focus()

	def delete_callback(self):
		if self.focus != self.selection_getselection():
			print 'AnchorEdit: wrong focus in delete!'
			self.focus = None
			self.show_focus()
			return
		if self.focus is None:
			print 'AnchorEdit: no focus in delete!'
			return
		id, atype, arg = self.anchorlist[self.focus]
		self.changed = 1
		del self.anchorlist[self.focus]
		self.selection_deleteitem(self.focus)
		if self.focus >= len(self.anchorlist):
			self.focus = self.focus - 1
			if self.focus < 0:
				self.focus = None
		self.show_focus()

	def type_callback(self):
		if self.focus is None:
			print 'AnchorEdit: no focus in setloc!'
			return
		i = self.type_choice_getchoice()
		self.set_type(self.TypeValues[i])


	def edit_callback(self):
		if self.focus is None:
			print 'AnchorEdit: no focus in edit_callback'
		self.set_type(None)

	def export_callback(self):
		if self.focus is None:
			print 'AnchorEdit: no focus in export_callback'
			return
		dummy = windowinterface.InputDialog(
			'External name for anchor', '', self.do_export)

	def do_export(self, name):
		if not name:
			return
		rootanchors = MMAttrdefs.getattr(self.root, 'anchorlist')
		for a in rootanchors:
			if a[A_ID] == name:
				windowinterface.showmessage('Already exists')
				return
		aid = self.anchorlist[self.focus][A_ID]
		a = (name, ATYPE_COMP, [(self.uid, aid)])
		rootanchors.append(a)
		em = self.editmgr
		if not em.transaction(): return 0
		em.setnodeattr(self.root, 'anchorlist', rootanchors[:])
		em.commit()
