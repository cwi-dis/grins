# Link editor.

import gl
import fl
import flp
from FL import *
import glwindow
from MMExc import *
import MMAttrdefs
import AttrEdit
from Dialog import BasicDialog
from ViewDialog import ViewDialog
import dialogs
from AnchorDefs import A_TYPE, A_ID, ATYPE_WHOLE

from MMNode import interiortypes

from Hlinks import ANCHOR1, ANCHOR2, DIR, TYPE, DIR_1TO2, DIR_2TO1, \
	           DIR_2WAY, TYPE_JUMP
typestr = ['JUMP', 'CALL', 'FORK']
dirstr = ['->', '<-', '<->']

class Struct: pass

# The menus:
LEFT_MENU = 'All|Dangling|Interesting|From Time Chart focus' + \
	  '|From Block View focus'
RIGHT_MENU = LEFT_MENU + '|All related anchors|No anchors, links only'
M_ALL = 1
M_DANGLING = 2
M_INTERESTING = 3
M_TCFOCUS = 4
M_BVFOCUS = 5
M_RELATION = 6
M_NONE = 7

class LinkEdit(ViewDialog, BasicDialog):
	#
	def init(self, toplevel):
		self = ViewDialog.init(self, 'links_')
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		form = flp.parse_form('LinkEditForm', 'form')
		width, height = glwindow.pixels2mm(form[0].Width, \
			  form[0].Height)
		title = 'Hyperlinks (' + toplevel.basename + ')'
		self = BasicDialog.init(self, width, height, title)
		self.left = Struct()
		self.right = Struct()
		self.left.fillfunc = self.fill_none
		self.right.fillfunc = self.fill_none
		self.left.node = None
		self.right.node = None
		self.left.focus = None
		self.right.focus = None
		self.left.hidden = 0
		self.right.hidden = 0
		self.linkedit = 0
		self.linkfocus = None
		flp.merge_full_form(self, self.form, form)
		self.left.node_menu.set_menu(LEFT_MENU)
		self.right.node_menu.set_menu(RIGHT_MENU)
		self.interesting = []
		return self
	#
	def fixtitle(self):
		self.settitle('Hyperlinks (' + self.toplevel.basename + ')')
	#
	def __repr__(self):
		return '<LinkEdit instance, root=' + `self.root` + '>'
	#
	def transaction(self):
		return 1
	#
	def rollback(self):
		pass
	#
	def commit(self):
		if self.form.window >= 0:
			gl.winset(self.form.window)
		self.updateform()
	#
	def kill(self):
		self.destroy()
	#
	def show(self):
		if not self.showing:
			self.updateform()
			BasicDialog.show(self)
			self.toplevel.checkviews()
			self.editmgr.register(self)
	#
	def hide(self):
		if self.showing:
			self.editmgr.unregister(self)
			BasicDialog.hide(self)
			self.toplevel.checkviews()
	#
	def destroy(self):
		self.left = self.right = None
		BasicDialog.destroy(self)
	#
	# Method to return a whole-node anchor for a node, or optionally
	# create one.
	def wholenodeanchor(self, node):
		alist = MMAttrdefs.getattr(node, 'anchorlist')
		for a in alist:
			if a[A_TYPE] == ATYPE_WHOLE:
				return (node.GetUID(), a[A_ID])
		em = self.editmgr
		if not em.transaction(): return None
		a = ('0', ATYPE_WHOLE, [])
		alist.append(a)
		em.setnodeattr(node, 'anchorlist', alist[:])
		em.commit()
		return (node.GetUID(), '0')
	#
	# The fill functions. These are set in the left and right structures
	# and used to fill the browsers.
	#
	def fill_none(self, str):
		str.sel_label.label = ''
		str.anchors = []

	def fill_node(self, str):
		str.sel_label.label = 'Node:'
		str.anchors = getanchors(str.node, 0)

	def fill_all(self, str):
		str.sel_label.label = 'All'
		str.anchors = getanchors(self.root, 1)

	def fill_relation(self, str):
		if str <> self.right:
			print 'LinkEdit: left anchorlist cannot be related!'
		str.sel_label.label = 'Related'
		str.anchors = []
		if self.left.focus == None:
			return
		lfocus = self.left.anchors[self.left.focus]
		links = self.context.hyperlinks.findalllinks(lfocus, None)
		for l in links:
			if not l[ANCHOR2] in str.anchors:
				str.anchors.append(l[ANCHOR2])

	def fill_dangling(self, str):
		str.sel_label.label = 'Dangling'
		all = getanchors(self.root, 1)
		nondangling = \
			  self.context.hyperlinks.findnondanglinganchordict()
		str.anchors = []
		for a in all:
			if not nondangling.has_key(a):
				str.anchors.append(a)

	def fill_interesting(self, str):
		str.sel_label.label = 'Interesting'
		str.anchors = self.interesting[:]
	#
	def finish_link(self, node):
		if not self.interesting:
			dialogs.showmessage('No reasonable sources for link')
			return
		anchors = ['Cancel']
		for a in self.interesting:
			anchors.append(self.makename(a))
		i = dialogs.multchoice('Choose source anchor', anchors, 0)
		if i == 0:
			return
		srcanchor = self.interesting[i-1]
		dstanchor = self.wholenodeanchor(node)
		if not dstanchor:
			return
		self.interesting.remove(srcanchor)
		link = srcanchor, dstanchor, DIR_1TO2, TYPE_JUMP
		self.context.hyperlinks.addlink(link)
		
	def set_interesting(self, anchor):
		self.interesting.append(anchor)

	def makename(self, (uid, aid)):
		node = self.context.mapuid(uid)
		nodename = node.GetRawAttrDef('name', uid)
		if type(aid) <> type(''): aid = `aid`
		return '#' + nodename + '.' + aid
	#
	# This functions re-loads one of the anchor browsers.
	#
	def reloadanchors(self, str):
		if str.hidden:
			str.anchor_browser.hide_object()
			str.node_show.hide_object()
			str.node_name.hide_object()
		else:
			str.anchor_browser.show_object()
		# Try to keep focus correct
		if str.focus <> None:
			focusvalue = str.anchors[str.focus]
		else:
			focusvalue = None
		str.focus = None
		# If the browser is node-bound, check that the node still
		# exists.
		if str.node:
			if str.node.GetRoot() <> self.root:
				str.node = None
				str.fillfunc = self.fill_none
		str.anchor_browser.clear_browser()
		str.fillfunc(str)
		for a in str.anchors:
			name = self.makename(a)
			str.anchor_browser.add_browser_line(name)
		if focusvalue:
			try:
				str.focus = str.anchors.index(focusvalue)
			except ValueError:
				pass
		if str.focus == None and str.anchors:
			str.focus = 0
			self.linkedit = 0
		if str.focus <> None:
			str.anchor_browser.select_browser_line(str.focus+1)
			str.anchor_browser.set_browser_topline(str.focus+1)
			str.node_show.show_object()
			str.anchoredit_show.show_object()
		else:
			str.node_show.hide_object()
			str.anchoredit_show.hide_object()
		if str.node:
			str.node_name.label = \
				  MMAttrdefs.getattr(str.node, 'name')
			str.node_name.show_object()
		else:
			str.node_name.hide_object()
	#
	# This function reloads the link browser or invisibilizes it
	#
	def reloadlinks(self):
		slf = self.left.focus
		srf = self.right.focus
		if slf == None or (srf == None and not self.right.hidden):
			# At least one unfocussed anchorlist. No browser
			self.link_group.hide_object()
			self.link_dir_group.hide_object()
			self.link_mod_group.hide_object()
			self.ok_group.hide_object()
			self.linkfocus = None
			self.linkedit = 0
			return
		lfocus = self.left.anchors[slf]
		if self.right.hidden:
			rfocus = None
		else:
			rfocus = self.right.anchors[srf]
		if self.linkfocus == None:
			fvalue = None
		else:
			fvalue = self.links[self.linkfocus]
		self.linkfocus = None
		self.links = self.context.hyperlinks.findalllinks \
			  (lfocus,rfocus)
		self.link_browser.clear_browser()
		for i in self.links:
			line = typestr[i[TYPE]] + ' ' + dirstr[i[DIR]]
			self.link_browser.add_browser_line(line)
		if fvalue:
			try:
				self.linkfocus = self.links.index(fvalue)
			except ValueError:
				pass
		if self.links and self.linkfocus == None and not self.linkedit:
			self.linkfocus = 0
		if self.linkfocus == None:
			self.link_mod_group.hide_object()
		else:
			self.link_browser.select_browser_line(self.linkfocus+1)
			self.link_mod_group.show_object()
		if self.linkedit:
			self.set_radio_buttons()
			self.link_dir_group.show_object()
		else:
			self.link_dir_group.hide_object()
			self.ok_group.hide_object()
		self.link_group.show_object()
		if self.right.hidden:
			self.link_add.hide_object()
	#
	# Reload/redisplay all data
	#
	def updateform(self):
		self.form.freeze_form()
		self.reloadanchors(self.left)
		self.reloadanchors(self.right)
		self.reloadlinks()
		self.form.unfreeze_form()
	#
	# Start editing a link
	#
	def startlinkedit(self, fromfocus):
		if fromfocus and  self.linkfocus == None:
			print 'LinkEdit: Start editing without focus!'
			return
		self.linkedit = 1
		if fromfocus:
			l = self.links[self.linkfocus]
			self.editlink = l
		else:
			slf = self.left.focus
			srf = self.right.focus
			if slf==None or (srf==None and not self.right.hidden):
				print 'LinkEdit: edit without anchor focus!'
				self.linkedit = 0
				return
			n1 = self.left.anchors[slf]
			n2 = self.right.anchors[srf]
			if n1 == n2:
				gl.ringbell()
				self.linkedit = 0
				return
			self.editlink = (n1, n2, DIR_1TO2, TYPE_JUMP)
	#
	# Update the link edit radio buttons to reflect the state of
	# the edited link
	#
	def set_radio_buttons(self):
		linkdir = self.editlink[DIR]
		linktype = self.editlink[TYPE]
		self.linkdir_but0.set_button(linkdir == 0)
		self.linkdir_but1.set_button(linkdir == 1)
		self.linkdir_but2.set_button(linkdir == 2)
		if self.linkfocus == None:
			# We seem to be adding
			self.ok_group.show_object()
			return
		link = self.links[self.linkfocus]
		if linkdir == link[DIR] and linktype == link[TYPE]:
			self.ok_group.hide_object()
		else:
			self.ok_group.show_object()
	#
	# Callback functions
	#
	def anchor_browser_callback(self, br, str):
		str = getattr(self, str)
		ind = br.get_browser()
		if ind:
			str.focus = ind - 1
		else:
			str.focus = None
		self.linkedit = 0
		self.updateform()
	#
	def show_callback(self, but, str):
		str = getattr(self, str)
		if str.focus == None:
			print 'LinkEdit: show without a focus!'
			return
		anchor = str.anchors[str.focus]
		uid = anchor[0]
		try:
			node = self.context.mapuid(uid)
		except NoSuchUIDError:
			print 'LinkEdit: anchor with unknown node UID!'
			return
		self.toplevel.hierarchyview.globalsetfocus(node)
		self.toplevel.channelview.globalsetfocus(node)
	#
	def menu_callback(self, menu, str):
		str = getattr(self, str)
		ind = menu.get_menu()
		str.hidden = 0
		if ind == M_ALL:
			str.node = None
			str.fillfunc = self.fill_all
		elif ind == M_DANGLING:
			str.node = None
			str.fillfunc = self.fill_dangling
		elif ind == M_INTERESTING:
			str.node = None
			str.fillfunc = self.fill_interesting
		elif ind == M_TCFOCUS:
			str.node = self.GetTimeChartFocus()
			if str.node == None:
				str.fillfunc = self.fill_none
			else:
				str.fillfunc = self.fill_node
		elif ind == M_BVFOCUS:
			str.node = self.GetHierarchyViewFocus()
			if str.node == None:
				str.fillfunc = self.fill_none
			else:
				str.fillfunc = self.fill_node
		elif ind == M_RELATION:
			str.node = None
			str.fillfunc = self.fill_relation
		elif ind == M_NONE:
			str.node = None
			str.fillfunc = self.fill_none
			str.hidden = 1
		else:
			print 'Unknown menu selection'
			return
		self.updateform()
	def link_browser_callback(self, *dummy):
		self.linkedit = 0
		f = self.link_browser.get_browser()
		if f <= 0:
			self.linkfocus = None
		else:
			self.linkfocus = f-1
		self.updateform()
	def link_add_callback(self, *dummy):
		self.linkfocus = None
		self.startlinkedit(0)
		self.updateform()
	def link_delete_callback(self, *dummy):
		if self.linkfocus == None:
			print 'LinkEdit: delete link w/o focus!'
			return
		l = self.links[self.linkfocus]
		self.context.hyperlinks.dellink(l)
		self.updateform()
	def link_edit_callback(self, *dummy):
		if self.linkfocus == None:
			print 'LinkEdit: edit w/o focus!'
			return
		self.startlinkedit(1)
		self.updateform()
	def linkdir_callback(self, obj, value):
		l = self.editlink
		self.editlink = l[ANCHOR1], l[ANCHOR2], eval(value), l[TYPE]
		self.set_radio_buttons()
	def ok_callback(self, *dummy):
		# XXX Focus isn't correct after an add.
		if not self.linkedit:
			print 'LinkEdit: OK while not editing!'
			return
		if self.linkfocus <> None:
			l = self.links[self.linkfocus]
			self.context.hyperlinks.dellink(l)
		self.context.hyperlinks.addlink(self.editlink)
		self.linkedit = 0
		self.updateform()
	def cancel_callback(self, *dummy):
		self.linkedit = 0
		self.updateform()
	def anchoredit_callback(self, but, str):
		str = getattr(self, str)
		if str.focus == None:
			print 'LinkEdit: anchoredit without a focus!'
			return
		anchor = str.anchors[str.focus]
		uid = anchor[0]
		try:
			node = self.context.mapuid(uid)
		except NoSuchUIDError:
			print 'LinkEdit: anchor with unknown node UID!'
			return
		import AnchorEdit
		AnchorEdit.showanchoreditor(self.toplevel, node)
	#
	def GetTimeChartFocus(self):
		return self.toplevel.channelview.getfocus()

	def GetHierarchyViewFocus(self):
		return self.toplevel.hierarchyview.getfocus()


	

#
# General functions
#
def getanchors(node, recursive):
	from AnchorDefs import modanchorlist
	rawanchors = MMAttrdefs.getattr(node, 'anchorlist')
	modanchorlist(rawanchors)
	uid = node.GetUID()
	anchors = []
	for i in rawanchors:
		anchors.append((uid, i[0]))
	if recursive and node.GetType() in interiortypes:
		children = node.GetChildren()
		for i in children:
			anchors = anchors + getanchors(i, 1)
	return anchors
#
# Return a dest-only anchor for a node
