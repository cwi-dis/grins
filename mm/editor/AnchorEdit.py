# Anchor editor

import MMExc
import MMAttrdefs
import fl
import gl
from FL import *
import flp
from Dialog import Dialog


FORMWIDTH = 350
FORMHEIGHT = 230

formtemplate = None


def showanchoreditor(node):
	try:
		anchoreditor = node.anchoreditor
	except AttributeError:
		anchoreditor = AnchorEditor().init(node)
		node.anchoreditor = anchoreditor
	anchoreditor.open()


def hideanchoreditor(node):
	try:
		anchoreditor = node.anchoreditor
	except AttributeError:
		return # No node info form active
	anchoreditor.close()


class AnchorEditor(Dialog):

	def init(self, node):
		self.node = node
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		self.anchorlist = []
		self.focus = None # None or 0...len(self.anchorlist)-1
		self.changed = 0
		#
		title = self.maketitle()
		self = Dialog.init(self, (FORMWIDTH, FORMHEIGHT, title, ''))
		#
		global formtemplate
		if formtemplate == None:
		    formtemplate = flp.parse_form('AnchorEditForm', 'form')
		#
		flp.merge_full_form(self, self.form, formtemplate)
		#
		return self

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
			self.getvalues(FALSE)
			self.updateform()
			self.title = self.maketitle()
			gl.winset(self.form.window)
			gl.wintitle(self.title)

	def rollback(self):
		pass

	def open(self):
		self.close()
		self.title = self.maketitle()
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
			name = '#' + self.uid + '.' + `i[0]`
			self.anchor_browser.add_browser_line(name)
		self.show_focus()
		self.form.unfreeze_form()

	def show_focus(self):
		self.anchor_browser.deselect_browser()
		if self.focus == None:
			self.group.hide_object()
		else:
			self.group.show_object()
			self.anchor_browser.select_browser_line(self.focus+1)
			self.show_location()


	def show_location(self):
		# XXX Should change sometime
		self.begin_button.set_button(0)
		self.end_button.set_button(0)
		self.whole_button.set_button(1)
		self.internal_button.set_button(0)

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
			id, dummy = max(self.anchorlist)
			id = id+1
		else:
			id = 1
		name = '#' + self.uid + '.' + `id`
		self.anchorlist.append((id, [0]))
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
		# Ignore, for now
		if self.focus == None:
			print 'AnchorEdit: no focus in setloc!'
		self.show_location()


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
