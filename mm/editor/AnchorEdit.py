# Anchor editor modeless dialog


import fl
import gl
from FL import *
import flp
from Dialog import Dialog

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

form_template = None	# result of flp.parse_form is stored here


# Top-level interface to show/hide a node's anchor editor

def showanchoreditor(toplevel, node):
	try:
		anchoreditor = node.anchoreditor
	except AttributeError:
		anchoreditor = AnchorEditor().init(toplevel, node)
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

class AnchorEditor(Dialog):

	def init(self, toplevel, node):
		self.node = node
		self.toplevel = toplevel
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		self.anchorlist = []
		self.focus = None # None or 0...len(self.anchorlist)-1
		self.changed = 0
		#
		global form_template
		if form_template == None:
		    form_template = flp.parse_form('AnchorEditForm', 'form')
		#
		width = form_template[0].Width
		height = form_template[0].Height
		title = self.maketitle()
		hint = ''
		self = Dialog.init(self, width, height, title, hint)
		#
		flp.merge_full_form(self, self.form, form_template)
		#
		return self

	def __repr__(self):
		return '<AnchorEditor instance, node=' + `self.node` + '>'

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
			self.pop()
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
		anchorlist = MMAttrdefs.getattr(self.node, 'anchorlist')
		if anchorlist <> self.anchorlist:
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
		em.setnodeattr(n, 'anchorlist', self.anchorlist[:])
		em.commit()
		return 1

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Anchors for node: ' + name

	# Fill form from local data.  Clear the form beforehand.
	#
	def updateform(self):
		self.form.freeze_form()
		self.anchor_browser.clear_browser()
		for i in self.anchorlist:
			id = i[A_ID]
			if type(id) <> type(''): id = `id`
			name = '#' + self.name + '.' + id
			self.anchor_browser.add_browser_line(name)
		self.show_focus()
		self.form.unfreeze_form()

	def show_focus(self):
		self.anchor_browser.deselect_browser()
		if self.focus == None:
			self.group.hide_object()
			self.edit_button.hide_object()
		else:
			self.anchor_browser.select_browser_line(self.focus+1)
			self.show_type()
			self.group.show_object()

	def show_type(self):
		if self.focus == None:
			print 'AnchorEdit: show_type without focus!'
			return
		a = self.anchorlist[self.focus]
		loc = a[A_ARGS]
		type = a[A_TYPE]
		self.whole_button.set_button(type == ATYPE_WHOLE)
		self.auto_button.set_button(type == ATYPE_AUTO)
		self.normal_button.set_button(type == ATYPE_NORMAL)
		self.pause_button.set_button(type == ATYPE_PAUSE)
		if type in (ATYPE_NORMAL, ATYPE_PAUSE):
			self.edit_button.show_object()
		else:
			self.edit_button.hide_object()

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
			new = self.toplevel.player.defanchor(self.node, new)
			if new == None:
				new = old
		if new <> old:
			self.anchorlist[self.focus] = new
			self.changed = 1
		self.show_type()

	def close(self):
		if self.showing:
			self.unregister(self)
			self.hide()
	#
	# Standard callbacks (from Dialog())
	#
	def cancel_callback(self, dummy):
		self.close()

	def restore_callback(self, (obj, arg)):
		self.getvalues(TRUE)
		self.updateform()

	def apply_callback(self, (obj, arg)):
		obj.set_button(1)
		if self.changed:
			dummy = self.setvalues()
		obj.set_button(0)

	def ok_callback(self, (obj, arg)):
		obj.set_button(1)
		if not self.changed or self.setvalues():
			self.close()
		obj.set_button(0)
	#
	# Private callbacks
	#
	def anchor_callback(self, dummy):
		self.focus = self.anchor_browser.get_browser() - 1
		if not 0 <= self.focus < len(self.anchorlist):
			self.focus = None
		self.show_focus()

	def add_callback(self, dummy):
		self.changed = 1
		maxid = 0
		for id, atype, args in self.anchorlist:
			if type(id) == type(0) and id > maxid:
				maxid = id
		id = maxid + 1
		name = '#' + self.name + '.' + `id`
		self.anchorlist.append((id, ATYPE_WHOLE, []))
		self.anchor_browser.add_browser_line(name)
		self.focus = len(self.anchorlist)-1
		self.show_focus()

	def delete_callback(self, dummy):
		if self.focus != self.anchor_browser.get_browser() - 1:
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
		self.anchor_browser.delete_browser_line(self.focus+1)
		if self.focus >= len(self.anchorlist):
			self.focus = self.focus - 1
			if self.focus < 0:
				self.focus = None
		self.show_focus()

	def setloc_callback(self, (obj, value)):
		# value can be '0', '1', '2' or '3' (a string!)
		if self.focus == None:
			print 'AnchorEdit: no focus in setloc!'
			return
		self.set_type(eval(value))

	def edit_callback(self, dummy):
		if self.focus == None:
			print 'AnchorEdit: no focus in edit_callback'
		self.set_type(None)


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
	#
	print 'parsing', filename, '...'
	root = MMTree.ReadFile(filename)
	#
	print 'quit button ...'
	quitform = fl.make_form(FLAT_BOX, 50, 50)
	quitbutton = quitform.add_button(NORMAL_BUTTON, 0, 0, 50, 50, 'Quit')
	quitform.set_form_position(600, 10)
	quitform.show_form(PLACE_POSITION, FALSE, 'QUIT')
	#
	print 'showanchoreditor ...'
	showanchoreditor(root)
	#
	print 'go ...'
	while 1:
		obj = fl.do_forms()
		if obj == quitbutton:
			hideanchoreditor(root)
			break
		print 'This object should have a callback!', `obj.label`
