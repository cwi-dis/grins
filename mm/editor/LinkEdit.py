# Link editor.

from MMExc import *
import MMAttrdefs
import AttrEdit
from ViewDialog import ViewDialog
import windowinterface, EVENTS
from AnchorDefs import A_TYPE, A_ID, ATYPE_WHOLE

from MMNode import interiortypes

from Hlinks import ANCHOR1, ANCHOR2, DIR, TYPE, DIR_1TO2, DIR_2TO1, \
	           DIR_2WAY, TYPE_JUMP
typestr = ['JUMP', 'CALL', 'FORK']
dirstr = ['->', '<-', '<->']

class Struct: pass

M_ALL = 1
M_DANGLING = 2
M_INTERESTING = 3
M_TCFOCUS = 4
M_BVFOCUS = 5
M_RELATION = 6
M_NONE = 7
M_EXTERNAL = 8

class LinkEdit(ViewDialog):
	def init(self, toplevel):
		self = ViewDialog.init(self, 'links_')
		self.last_geometry = None
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		title = 'Hyperlinks (' + toplevel.basename + ')'
		self.window = windowinterface.Window(title)
		self.showing = self.window.is_showing()
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

		win1 = self.window.SubWindow({'top': None, 'left': None})
		menu = win1.PulldownMenu([
			('Set anchorlist',
			 [('All', (self.menu_callback, (self.left, M_ALL))),
			  ('Dangling', (self.menu_callback,
					(self.left, M_DANGLING))),
			  ('From Channel view focus', (self.menu_callback,
						(self.left, M_TCFOCUS))),
			  ('From Hierarchy view focus', (self.menu_callback,
						(self.left, M_BVFOCUS)))]
			 )],
			{'top': None, 'left': None, 'right': None})
		list = win1.List('None', [],
				 (self.anchor_browser_callback, (self.left,)),
				 {'top': menu, 'left': None, 'right': None})
		self.left.browser = list
		self.left.node_show = win1.ButtonRow(1, [
			('', 'Push focus', (self.show_callback, (self.left,)))
			],
			{'top': list, 'left': None, 'right': None})
		self.left.anchoredit_show = win1.ButtonRow(1,
				[('', 'Anchor editor...', (self.anchoredit_callback, (self.left,)))],
				{'top': self.left.node_show,
				 'left': None, 'right': None})

		win2 = self.window.SubWindow({'top': None, 'left': win1})
		dummymenu = win2.PulldownMenu([('placeholder', [])],
				{'top': None, 'left': None, 'right': None})
		self.link_browser = win2.List('links:', [],
				(self.link_browser_callback, ()),
				{'top': dummymenu,
				 'left': None, 'right': None})
		self.link_new = win2.ButtonRow(1,
				[('', 'Add...', (self.link_new_callback, ()))],
				{'top': self.link_browser,
				 'left': None, 'right': None})
		self.link_edit = win2.ButtonRow(0,
				[('', 'Edit...', (self.link_edit_callback, ())),
				 ('', 'Delete', (self.link_delete_callback, ()))],
				{'top': self.link_new,
				 'left': None, 'right': None})

		win3 = self.window.SubWindow({'top': None, 'left': win2, 'right': None})
		menu = win3.PulldownMenu([
			('Set anchorlist',
			 [('All', (self.menu_callback, (self.right, M_ALL))),
			  ('Dangling', (self.menu_callback,
					(self.right, M_DANGLING))),
			  ('From Channel view focus', (self.menu_callback,
						     (self.right, M_TCFOCUS))),
			  ('From Hierarchy view focus', (self.menu_callback,
						     (self.right, M_BVFOCUS))),
			  ('All related anchors', (self.menu_callback,
						   (self.right, M_RELATION))),
			  ('No anchors, links only', (self.menu_callback,
						      (self.right, M_NONE))),
			  ('External', (self.menu_callback,
					(self.right, M_EXTERNAL)))]
			 )],
				{'top': None, 'left': None, 'right': None})
		list = win3.List('None', [],
				 (self.anchor_browser_callback, (self.right,)),
				 {'top': menu, 'left': None, 'right': None})
		self.right.browser = list
		self.right.node_show = win3.ButtonRow(1, [
			('', 'Push focus', (self.show_callback, (self.right,)))
			],
			{'top': list, 'left': None, 'right': None})
		self.right.anchoredit_show = win3.ButtonRow(1,
				[('', 'Anchor editor...', (self.anchoredit_callback, (self.right,)))],
				{'top': self.right.node_show,
				 'left': None, 'right': None})

		self.link_dir = self.window.OptionMenu('Link direction:',
				dirstr, 0, (self.linkdir_callback, ()),
				{'top': win1, 'left': None})

		self.ok_group = self.window.ButtonRow(0,
				[('', 'OK', (self.ok_callback, ())),
				 ('', 'Cancel', (self.cancel_callback, ()))],
				{'top': win1, 'left': self.link_dir, 'right': None})

		self.window.fix()

		dummymenu.hide()

		self.linkedit = 0
		self.linkfocus = None
		self.interesting = []
		return self

	def fixtitle(self):
		if self.is_showing():
			self.window.settitle('Hyperlinks (' + self.toplevel.basename + ')')

	def __repr__(self):
		return '<LinkEdit instance, root=' + `self.root` + '>'

	def transaction(self):
		return 1

	def rollback(self):
		pass

	def commit(self):
		self.updateform()

	def kill(self):
		self.destroy()

	def show(self):
		if not self.window.is_showing():
			self.updateform()
			self.window.show()
			self.showing = self.window.is_showing()
			self.toplevel.checkviews()
			self.editmgr.register(self)

	def hide(self):
		if self.window.is_showing():
			self.editmgr.unregister(self)
			self.window.hide()
			self.toplevel.checkviews()

	def destroy(self):
		self.left = self.right = None
		self.window.close()
		self.window = None

	def setwaiting(self):
		pass

	def setready(self):
		pass

	def is_showing(self):
		return self.window.is_showing()

	def get_geometry(self):
		pass

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

	# Make sure all anchors in 'interesting' actually exist
	def fixinteresting(self):
		dlist = []
		for nid, aid in self.interesting:
			node = self.context.mapuid(nid)
			alist = MMAttrdefs.getattr(node, 'anchorlist')
			for a in alist:
				if a[A_ID] == aid:
					break
			else:
				dlist.append(nid,aid)
		for a in dlist:
			print 'lost anchor:', a
			self.interesting.remove(a)

	# The fill functions. These are set in the left and right structures
	# and used to fill the browsers.

	def fill_none(self, str):
		str.browser.setlabel('None')
		str.anchors = []

	def fill_node(self, str):
		str.browser.setlabel('Node:')
		str.anchors = getanchors(str.node, 0)

	def fill_all(self, str):
		str.browser.setlabel('All')
		str.anchors = getanchors(self.root, 1)

	def fill_relation(self, str):
		if str <> self.right:
			print 'LinkEdit: left anchorlist cannot be related!'
		str.browser.setlabel('Related')
		str.anchors = []
		if self.left.focus == None:
			return
		lfocus = self.left.anchors[self.left.focus]
		links = self.context.hyperlinks.findalllinks(lfocus, None)
		for l in links:
			if not l[ANCHOR2] in str.anchors:
				str.anchors.append(l[ANCHOR2])

	def fill_dangling(self, str):
		str.browser.setlabel('Dangling')
		all = getanchors(self.root, 1)
		nondangling = \
			  self.context.hyperlinks.findnondanglinganchordict()
		str.anchors = []
		for a in all:
			if not nondangling.has_key(a):
				str.anchors.append(a)

	def fill_interesting(self, str):
		str.browser.setlabel('Interesting')
		self.fixinteresting()
		str.anchors = self.interesting[:]

	def fill_external(self, str):
		str.browser.setlabel('External')
		str.anchors = self.toplevel.getallexternalanchors()

	def finish_link(self, node):
		self.fixinteresting()
		if not self.interesting:
			windowinterface.showmessage('No reasonable sources for link')
			return
		anchors = ['Cancel']
		for a in self.interesting:
			anchors.append(self.makename(a))
		i = windowinterface.multchoice('Choose source anchor',
			  anchors, 0)
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
		if '/' in uid:
			return aid + ' in ' + uid
		node = self.context.mapuid(uid)
		nodename = node.GetRawAttrDef('name', uid)
		if type(aid) <> type(''): aid = `aid`
		return '#' + nodename + '.' + aid

	# This functions re-loads one of the anchor browsers.
	def reloadanchors(self, str):
		if str.hidden:
			str.browser.hide()
			str.node_show.hide()
		else:
			str.browser.show()
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
		if hasattr(str, 'anchors'):
			oldanchors = str.anchors
		else:
			oldanchors = []
		str.fillfunc(str)
		if str.anchors != oldanchors:
			str.browser.delalllistitems()
			for a in str.anchors:
				name = self.makename(a)
				str.browser.addlistitem(name, -1)
		if focusvalue:
			try:
				str.focus = str.anchors.index(focusvalue)
			except ValueError:
				pass
		if str.focus == None and str.anchors:
			str.focus = 0
			self.linkedit = 0
		if str.focus <> None:
			str.browser.selectitem(str.focus)
			str.browser.show()
			str.node_show.show()
			str.anchoredit_show.show()
		else:
			str.node_show.hide()
			str.anchoredit_show.hide()
		if str.node:
			str.browser.setlabel('Node: ' +
					MMAttrdefs.getattr(str.node, 'name'))

	# This function reloads the link browser or invisibilizes it
	def reloadlinks(self):
		slf = self.left.focus
		srf = self.right.focus
		if slf == None or (srf == None and not self.right.hidden):
			# At least one unfocussed anchorlist. No browser
			self.link_browser.hide()
			self.link_new.hide()
			self.link_edit.hide()
			self.link_dir.hide()
			self.ok_group.hide()
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
		self.link_browser.delalllistitems()
		for i in self.links:
			line = typestr[i[TYPE]] + ' ' + dirstr[i[DIR]]
			self.link_browser.addlistitem(line, -1)
		if fvalue:
			try:
				self.linkfocus = self.links.index(fvalue)
			except ValueError:
				pass
		if self.links and self.linkfocus == None and not self.linkedit:
			self.linkfocus = 0
		if self.linkfocus == None:
			self.link_edit.hide()
			pass
		else:
			self.link_browser.selectitem(self.linkfocus)
			self.link_edit.show()
		if self.linkedit:
			self.set_radio_buttons()
			self.link_dir.show()
		else:
			self.link_dir.hide()
			self.ok_group.hide()
		self.link_browser.show()
		if self.right.hidden:
			self.link_new.hide()
		else:
			self.link_new.show()

	# Reload/redisplay all data
	def updateform(self):
		self.reloadanchors(self.left)
		self.reloadanchors(self.right)
		self.reloadlinks()

	# Start editing a link
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
				windowinterface.beep()
				self.linkedit = 0
				return
			self.editlink = (n1, n2, DIR_1TO2, TYPE_JUMP)

	# Update the link edit radio buttons to reflect the state of
	# the edited link
	def set_radio_buttons(self):
		linkdir = self.editlink[DIR]
		linktype = self.editlink[TYPE]
		self.link_dir.setpos(linkdir)
		if self.linkfocus == None:
			# We seem to be adding
			self.ok_group.show()
			return
		link = self.links[self.linkfocus]
		if linkdir == link[DIR] and linktype == link[TYPE]:
			self.ok_group.hide()
		else:
			self.ok_group.show()

	# Callback functions
	def anchor_browser_callback(self, str):
		focus = str.browser.getselected()
		if focus != str.focus:
			str.focus = focus
			self.linkedit = 0
			self.updateform()

	def show_callback(self, str):
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
		windowinterface.setcursor('watch')
		self.toplevel.hierarchyview.globalsetfocus(node)
		self.toplevel.channelview.globalsetfocus(node)
		windowinterface.setcursor('')

	def menu_callback(self, str, ind):
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
			str.node = self.GetChannelViewtFocus()
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
		elif ind == M_EXTERNAL:
			str.node = None
			str.fillfunc = self.fill_external
#			if self.external:
#				doc, aname = self.external[0]
#			else:
#				doc, aname = '', ''
#			doc = fl.show_input('Give document name', doc)
#			aname = fl.show_input('Give anchor name', aname)
#			if not doc or not aname:
#				self.external = []
#			else:
#				if not '/' in doc:
#					doc = './' + doc
#				self.external = [(doc, aname)]
		else:
			print 'Unknown menu selection'
			return
		self.updateform()

	def link_browser_callback(self):
		focus = self.link_browser.getselected()
		if focus != self.linkfocus:
			self.linkedit = 0
			self.linkfocus = focus
			self.updateform()

	def link_new_callback(self, *dummy):
		self.linkfocus = None
		self.startlinkedit(0)
		self.updateform()

	def link_delete_callback(self):
		if self.linkfocus == None:
			print 'LinkEdit: delete link w/o focus!'
			return
		l = self.links[self.linkfocus]
		self.context.hyperlinks.dellink(l)
		self.updateform()

	def link_edit_callback(self):
		if self.linkfocus == None:
			print 'LinkEdit: edit w/o focus!'
			return
		self.startlinkedit(1)
		self.updateform()

	def linkdir_callback(self):
		linkdir = self.link_dir.getpos()
		l = self.editlink
		if l[DIR] != linkdir:
			self.editlink = l[ANCHOR1], l[ANCHOR2], linkdir, \
					l[TYPE]
			self.set_radio_buttons()

	def ok_callback(self):
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

	def cancel_callback(self):
		self.linkedit = 0
		self.updateform()

	def anchoredit_callback(self, str):
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

	def GetChannelViewtFocus(self):
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

# Return a dest-only anchor for a node
