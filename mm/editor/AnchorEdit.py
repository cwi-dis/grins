# Anchor editor using the FORMS library (fl, FL), based upon Dialog.


import path
import posix
import string
import fl
import gl
from FL import *
import flp

import MMExc
import MMAttrdefs
import MMParser
import MMWrite

import NodeEdit

# from MMNode import alltypes, leaftypes, interiortypes

# from ChannelMap import channelmap

from Dialog import Dialog

FORMWIDTH=350
FORMHEIGHT=230

class Struct: pass
_global = Struct()

_global.cwd = posix.getcwd()+'/'
_global.dir = ''
_global.form = None


# There are two basic calls into this module (but see below for more):
# showanchoreditor(node) creates an node info form for a node
# and hideanchoreditor(node) hides it again.  Since the editor may also
# hide itself, spurious hide calls are ignored; also, only one node
# info form is allowed per node, and extra show calls are also ignored
# (actually, these close and re-open the window to draw attention...).
# Hiding the form when the user has changed part of it may ask the
# user what should be done about this -- this part of the interface
# hasn't been completely thought out yet.

def _showanchoreditor(node,new):
	try:
		anchoreditor = node.anchoreditor
	except NameError:	# BCOMPAT
		anchoreditor = AnchorEditor().init(node)
		node.anchoreditor = anchoreditor
	except AttributeError:
		anchoreditor = AnchorEditor().init(node)
		node.anchoreditor = anchoreditor
	anchoreditor.open(new)

def showanchoreditor(node): _showanchoreditor(node,0)

def shownewanchoreditor(node): _showanchoreditor(node,1)

def hideanchoreditor(node):
	try:
		anchoreditor = node.anchoreditor
	except NameError:	# BCOMPAT
		return
	except AttributeError:
		return # No node info form active
	anchoreditor.close()


# An additional call to check whether the node info form is currently
# active for a node (so the caller can put up a warning "you are already
# editing this node's attributes" instead of just silence).

def hasanchoreditor(node):
	try:
		anchoreditor = node.anchoreditor
	except NameError:	# BCOMPAT
		return 0
	except AttributeError:
		return 0 # No node info form active
	return anchoreditor.showing
#
#

class AnchorEditor(Dialog):
	def init(self, node):
		self.node = node
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		self.anchorlist = None
		self.focus = None
		self.changed = 0
		self.getvalues(TRUE)
		#
		title = self.maketitle()
		self = Dialog.init(self, (FORMWIDTH, FORMHEIGHT, title,''))
		if _global.form == None:
		    _global.form = flp.parse_form('AnchorEditForm', 'form')
		#
		flp.merge_full_form(self, self.form, _global.form)
		#
		return self
	#
	def transaction(self):
		return 1
	#
	def getcontext(self):
		return self.context
	def register(self, object):
		if self.editmgr <> None:   # DEBUG
		    self.editmgr.register(object)
	def unregister(self, object):
		if self.editmgr <> None:   # DEBUG
		    self.editmgr.unregister(object)
	#
	def stillvalid(self):
		return self.node.GetRoot() is self.root
	#
	def commit(self):
		if not self.stillvalid():
			self.close()
		else:
			self.getvalues(FALSE)
			self.updateform()
			gl.winset(self.form.window)
			gl.wintitle(self.maketitle())
	#
	def rollback(self):
		pass
	#
	def open(self,new):
		self.close()
		self.title = self.maketitle()
		self.getvalues(TRUE)
		self.updateform()
		self.register(self)
		self.show()
	#
	def getvalues(self, always):
		#
		# First get all values (except those changed, if
		# always is true)
		#
		self.nodename = MMAttrdefs.getattr(self.node,'name')
		self.uid = self.node.GetUID()
		if self.changed and not always:
			return
		self.anchorid = MMAttrdefs.getattr(self.node,'anchorid')
		anchorlist = MMAttrdefs.getattr(self.node,'anchorlist')[:]
		if anchorlist <> self.anchorlist:
			self.focus = None
			self.anchorlist = anchorlist
	#
	def setvalues(self):
		em = self.editmgr
		n = self.node
		if not em.transaction(): return 0
		em.setnodeattr(n, 'anchorid', self.anchorid)
		em.setnodeattr(n, 'anchorlist', self.anchorlist)
		self.changed = 0
		em.commit()
		return 1
	def maketitle(self):
		return 'Anchor editor for ' + self.nodename
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
	#
	def show_focus(self):
		self.anchor_browser.deselect_browser()
		if self.focus == None:
			self.group.hide_object()
		else:
			self.group.show_object()
			self.anchor_browser.select_browser_line(self.focus+1)
			self.show_location()

	#
	def show_location(self):
		# XXX Should change sometime
		self.begin_button.set_button(0)
		self.end_button.set_button(0)
		self.whole_button.set_button(1)
		self.internal_button.set_button(0)
	#
	#
	def close(self):
		if self.showing:
			self.unregister(self)
			self.hide()
	#
	# Standard callbacks (from Dialog())
	#
	def cancel_callback(self, dummy):
		self.close()
	#
	def restore_callback(self, (obj, arg)):
		self.getvalues(TRUE)
		self.updateform()
	#
	def apply_callback(self, (obj, arg)):
		obj.set_button(1)
		if self.changed:
			dummy = self.setvalues()
		obj.set_button(0)
	#
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
		self.show_focus()
	def add_callback(self, dummy):
		self.changed = 1
		id = self.anchorid
		self.anchorid = self.anchorid + 1
		name = '#' + self.uid + '.' + `id`
		self.anchorlist.append((id, [0]))
		self.anchor_browser.add_browser_line(name)
		self.focus = len(self.anchorlist)-1
		self.show_focus()
	def delete_callback(self, dummy):
		if self.focus == None:
			print 'This is not possible...'
			return
		del self.anchorlist[self.focus]
		self.anchor_browser.delete_browser_line(self.focus+1)
		self.focus = None
		self.show_focus()
	def setloc_callback(self, (obj, value)):
		# Ignore, for now
		if self.focus == None:
			print 'This is not possible...'
		self.show_location()
		
# Routine to close all attribute editors in a node and its context.

def hideall(root):
	hidenode(root)

# Recursively close the attribute editor for this node and its subtree.

def hidenode(node):
	hideanchoreditor(node)
	if node.GetType() in interiortypes:
		for child in node.GetChildren():
			hidenode(child)


# Test program -- edit the attributes of the root node.

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
