# Anchor editor modeless dialog


import fl
import gl
from FL import *
import flp
from Dialog import Dialog

import MMExc
import MMAttrdefs
from MMNode import alltypes, leaftypes, interiortypes

A_ID   = 0
A_TYPE = 1
A_ARGS = 2

ATYPE_WHOLE  = 0
ATYPE_AUTO   = 1
ATYPE_NORMAL = 2
ATYPE_PAUSE  = 3

form_template = None


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
		anchorlist = MMAttrdefs.getattr(self.node, 'anchorlist')[:]
		if anchorlist <> self.anchorlist:
			self.anchorlist = anchorlist
			self.focus = 0
			if self.focus >= len(self.anchorlist):
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
	#
	# updateform - Fill form from local data. Will clear the
	# form beforehand.
	#
	def updateform(self):
		self.form.freeze_form()
		self.anchor_browser.clear_browser()
		for i in self.anchorlist:
			name = '#' + self.uid + '.' + `i[A_ID]`
			self.anchor_browser.add_browser_line(name)
		self.show_focus()
		self.form.unfreeze_form()

	def show_focus(self):
		self.anchor_browser.deselect_browser()
		if self.focus == None:
			self.group.hide_object()
			self.edit_button.hide_object()
		else:
			self.group.show_object()
			self.anchor_browser.select_browser_line(self.focus+1)
			self.show_location()


	def show_location(self):
		# XXX Should change sometime
		if self.focus == None:
			print 'AnchorEdit: show_location without focus!'
		a = self.anchorlist[self.focus]
		loc = a[A_ARGS]
		type = a[A_TYPE]
		self.begin_button.set_button(type == 0)
		self.end_button.set_button(type == 1)
		self.whole_button.set_button(type == 2)
		self.internal_button.set_button(type == 3)
		if type in (ATYPE_NORMAL, ATYPE_PAUSE):
			self.edit_button.show_object()
		else:
			self.edit_button.hide_object()

	def set_location(self, loc):
		if self.focus == None:
			print 'AnchorEdit: show_location without focus!'
		a = self.anchorlist[self.focus]
		self.changed = 1
		if loc == None:
			loc = a[A_TYPE]
		if loc in (ATYPE_AUTO, ATYPE_WHOLE):
			a = (a[0], loc, [])
		else:
			a = (a[0], loc, a[2])
			na = self.toplevel.player.defanchor(self.node, a)
			if na == None:
				a = (a[0], ATYPE_WHOLE, [])
			else:
				a = na
		self.anchorlist[self.focus] = a
		self.show_location()

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
		if self.anchorlist:
			id, dummy, dummy2 = max(self.anchorlist)
			id = id+1
		else:
			id = 1
		name = '#' + self.uid + '.' + `id`
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
		# Ignore, for now
		if self.focus == None:
			print 'AnchorEdit: no focus in setloc!'
		self.set_location(eval(value))

	def edit_callback(self, dummy):
		if self.focus == None:
			print 'AnchorEdit: no focus in edit_callback'
		self.set_location(None)

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
