# Anchor editor modeless dialog


import windowinterface
import MMExc
import MMAttrdefs
from MMNode import alltypes, leaftypes, interiortypes


# The 'anchors' attribute of a node is a list of triples.
# Each triple has the form (id, type, args):
# - id:   a number identifying the anchor uniquely (within this node)
# - type: one of the ATYPE_* constants defined in AnchorDefs
# - args: used by the channel to define what the anchor looks like
# The form of args depends on what the channel puts there.
# It is normally a list of values, e.g. [x0, y0, x1, y1] giving the
# boundaries of a box, or an empty list if there is no extra information.

from AnchorDefs import *

TypeValues = [ ATYPE_WHOLE, ATYPE_NORMAL, ATYPE_PAUSE, ATYPE_AUTO, ATYPE_COMP,
	  ATYPE_ARGS]
TypeLabels = [ 'dest only', 'normal', 'pausing (obsolete)', 'auto-firing', 'composite',
	  'with arguments']

FALSE, TRUE = 0, 1

# Top-level interface to show/hide a node's anchor editor

def showanchoreditor(toplevel, node):
	try:
		anchoreditor = node.anchoreditor
	except AttributeError:
		anchoreditor = AnchorEditor(toplevel, node)
		node.anchoreditor = anchoreditor
	anchoreditor.open()

def hideanchoreditor(node):
	try:
		anchoreditor = node.anchoreditor
	except AttributeError:
		return # No anchor editor for this node
	anchoreditor.close()


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

class AnchorEditor:

	def __init__(self, toplevel, node):
		self.node = node
		self.toplevel = toplevel
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		self.anchorlist = []
		self.focus = None # None or 0...len(self.anchorlist)-1
		self.changed = 0
		self.editable = 1

		title = self.maketitle()

		self.window = w = windowinterface.Window(title, resizable = 1,
				deleteCallback = (self.cancel_callback, ()))

		buttons = w.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ()))],
			bottom = None, left = None, right = None, vertical = 0)
		self.composite = w.Label('Composite:', useGadget = 0,
					 bottom = buttons, left = None,
					 right = None)
		self.type_choice = w.OptionMenu('Type:', TypeLabels, 0,
						(self.type_callback, ()),
						bottom = self.composite,
						left = None, right = None)
		self.buttons = w.ButtonRow(
			[('New', (self.add_callback, ())),
			 ('Edit...', (self.edit_callback, ())),
			 ('Delete', (self.delete_callback, ())),
			 ('Export...', (self.export_callback, ()))],
			top = None, right = None)
		self.anchor_browser = w.Selection(None, 'Id:', [],
						  (self.anchor_callback, ()),
						  top = None, left = None,
						  right = self.buttons,
						  bottom = self.type_choice)
		w.fix()

	def __repr__(self):
		return '<AnchorEditor instance, node=' + `self.node` + '>'

	def show(self):
		self.window.show()

	def hide(self):
		self.window.hide()

	def is_showing(self):
		return self.window.is_showing()

	def settitle(self, title):
		self.window.settitle(title)

	def transaction(self):
		return 1

	def getcontext(self):
		return self.context

	def register(self, object):
		if self.editmgr <> None:   # DEBUG
			self.editmgr.register(object)

	def unregister(self, object):
		if self.editmgr <> None:   # DEBUG
			self.editmgr.unregister(object)

	def stillvalid(self):
		return self.node.GetRoot() is self.root

	def commit(self):
		if not self.stillvalid():
			self.close()
		else:
			self.settitle(self.maketitle())
			self.getvalues(FALSE)
			self.updateform()

	def rollback(self):
		pass

	def kill(self):
		self.close()
		self.destroy()

	def open(self):
		if self.is_showing():
			self.window.show()
			return
		self.close()
		self.settitle(self.maketitle())
		self.getvalues(TRUE)
		self.updateform()
		self.register(self)
		self.show()

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
		modanchorlist(anchorlist)
		if anchorlist <> self.anchorlist:
			# Communicate new anchors to Link editor:
			for a in anchorlist:
				if not a in self.anchorlist:
					aid = (self.uid, a[A_ID])
					self.toplevel.links.set_interesting(\
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
		if not em.transaction(): return 0
		self.changed = 0
		n = self.node
		old_alist = MMAttrdefs.getattr(self.node, 'anchorlist')
		em.setnodeattr(n, 'anchorlist', self.anchorlist[:])
		for a in self.anchorlist:
			if not a in old_alist:
				aid = (self.uid, a[A_ID])
				self.toplevel.links.set_interesting(aid)
		em.commit()
		return 1

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Anchors for node: ' + name

	# Fill form from local data.  Clear the form beforehand.
	#
	def updateform(self):
		names = []
		for i in self.anchorlist:
			id = i[A_ID]
			if type(id) <> type(''): id = `id`
			#name = '#' + self.name + '.' + id
			names.append(id)
		self.anchor_browser.delalllistitems()
		self.anchor_browser.addlistitems(names, -1)
		self.show_focus()

	def show_focus(self):
##		self.anchor_browser.deselect_browser()
		if self.focus and self.editable:
			self.buttons.show(1)
		else:
			self.buttons.hide(1)
		if self.focus == None:
			self.buttons.hide(2)
			self.type_choice.hide()
##			self.group.hide_object()
			self.composite.hide()
##			self.id_input.hide_object()
		else:
			self.anchor_browser.selectitem(self.focus)
			self.buttons.show(2)
			self.type_choice.show()
##			self.group.show_object()
			self.show_type()

	def show_type(self):
		if self.focus == None:
			print 'AnchorEdit: show_type without focus!'
			return
		a = self.anchorlist[self.focus]
		loc = a[A_ARGS]
		type = a[A_TYPE]
		if type == ATYPE_COMP:
			self.composite.show()
			self.type_choice.hide()
			self.buttons.hide(1)
			self.composite.setlabel('Composite: ' + `loc`)
			return
		self.type_choice.show()
		self.composite.hide()
		for i in range(len(TypeValues)):
			if type == TypeValues[i]:
				self.type_choice.setpos(i)
		if type in (ATYPE_NORMAL, ATYPE_PAUSE, ATYPE_ARGS) \
			  and self.editable:
			self.buttons.show(1)
		else:
			self.buttons.hide(1)

	def set_type(self, type):
		if self.focus == None:
			print 'AnchorEdit: set_type without focus!'
			return
		old = new = self.anchorlist[self.focus]
		if type == None:
			type = new[A_TYPE]
		if type in (ATYPE_AUTO, ATYPE_WHOLE):
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
		if self.is_showing():
			self.unregister(self)
			self.hide()
	#
	# Standard callbacks
	#
	def cancel_callback(self):
		self.close()

	def restore_callback(self):
		self.getvalues(TRUE)
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
		focus = self.anchor_browser.getselected()
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
			if type(id) == type(0) and id > maxid:
				maxid = id
		id = `maxid + 1`
		#name = '#' + self.name + '.' + id
		name = id
		self.anchorlist.append((id, ATYPE_WHOLE, []))
		self.anchor_browser.addlistitem(name, -1)
		self.focus = len(self.anchorlist)-1
		self.show_focus()

	def id_callback(self, *dummy):
		# XXXX Does not work for non-whole-node anchors if
		# self.editable is false
		self.changed = 1
		if self.focus == None:
			raise 'id callback without focus!'
		anchor = self.anchorlist[self.focus]
		id = self.id_input.get_input()
		anchor = (id, anchor[1], anchor[2])
		self.anchorlist[self.focus] = anchor
		self.show_focus()

	def delete_callback(self):
		# XXXX Does not work for non-whole-node anchors if
		# self.editable is false
		if self.focus != self.anchor_browser.getselected():
			print 'AnchorEdit: wrong focus in delete!'
			self.focus = None
			self.show_focus()
			return
		if self.focus == None:
			print 'AnchorEdit: no focus in delete!'
			return
		id, atype, arg = self.anchorlist[self.focus]
		self.changed = 1
		del self.anchorlist[self.focus]
		self.anchor_browser.dellistitem(self.focus)
		if self.focus >= len(self.anchorlist):
			self.focus = self.focus - 1
			if self.focus < 0:
				self.focus = None
		self.show_focus()

	def type_callback(self):
		if self.focus == None:
			print 'AnchorEdit: no focus in setloc!'
			return
		i = self.type_choice.getpos()
		self.set_type(TypeValues[i])


	def edit_callback(self):
		if self.focus == None:
			print 'AnchorEdit: no focus in edit_callback'
		self.set_type(None)

	def export_callback(self):
		if self.focus == None:
			print 'AnchorEdit: no focus in export_callback'
			return
		dummy = windowinterface.InputDialog(
			'External name for anchor:', '', self.do_export)

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


# Routine to close all attribute editors in a node and its context.

def hideall(root):
	hidenode(root)


# Recursively close the attribute editor for this node and its subtree.

def hidenode(node):
	hideanchoreditor(node)
	if node.GetType() in interiortypes:
		for child in node.GetChildren():
			hidenode(child)


# Test program -- edit anchors of the root node

def test():
	import sys, MMTree
	if sys.argv[1:]:
		filename = sys.argv[1]
	else:
		filename = 'demo.cmif'

	print 'parsing', filename, '...'
	root = MMTree.ReadFile(filename)

	print 'quit button ...'
	quitform = windowinterface.Window('Quit')
	b = quitform.ButtonRow([('QUIT', (sys.exit, (0,)))], vertical = 0)

	print 'showanchoreditor ...'
	showanchoreditor(root)

	print 'go ...'
	windowinterface.mainloop()
