__version__ = "$Id$"

# Link editor.

from MMExc import *
import MMAttrdefs
import AttrEdit
from ViewDialog import ViewDialog
import windowinterface
from AnchorDefs import *

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
M_KEEP = 9

from LinkEditDialog import LinkBrowserDialog, LinkEditorDialog

class LinkEdit(ViewDialog, LinkBrowserDialog):
	def __init__(self, toplevel):
		ViewDialog.__init__(self, 'links_')
		self.last_geometry = None
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.context = self.root.GetContext()
		self.editmgr = self.context.geteditmgr()
		title = self.__maketitle()
		self.left = Struct()
		self.right = Struct()
		self.left.fillfunc = self.fill_all
		self.right.fillfunc = self.fill_relation
		self.left.node = None
		self.right.node = None
		self.left.focus = None
		self.right.focus = None
		self.left.hidden = 0
		self.right.hidden = 0
		self.linkfocus = None
		self.interesting = []

		LinkBrowserDialog.__init__(self, self.__maketitle(), 
			[('All', (self.menu_callback, (self.left, M_ALL))),
			 ('Dangling',
			  (self.menu_callback, (self.left, M_DANGLING))),
			 ('From Timeline view selection',
			  (self.menu_callback, (self.left, M_TCFOCUS))),
			 ('From Structure view selection',
			  (self.menu_callback, (self.left, M_BVFOCUS))),
			 ], self.left,
			[('All', (self.menu_callback, (self.right, M_ALL))),
			  ('Dangling',
			   (self.menu_callback, (self.right, M_DANGLING))),
			  ('From Timeline view selection',
			   (self.menu_callback, (self.right, M_TCFOCUS))),
			  ('From Structure view selection',
			   (self.menu_callback, (self.right, M_BVFOCUS))),
			  ('All related anchors',
			   (self.menu_callback, (self.right, M_RELATION))),
			  ('No anchors, links only',
			   (self.menu_callback, (self.right, M_NONE))),
			  ('External',
			   (self.menu_callback, (self.right, M_EXTERNAL))),
			  ('Keep list',
			   (self.menu_callback, (self.right, M_KEEP))),
			 ], self.right)

		# make some methods available through self.left and self.right
		self.left.browser_setlabel = self.leftsetlabel
		self.left.browser_show = self.leftshow
		self.left.browser_hide = self.lefthide
		self.left.browser_dellistitems = self.leftdellistitems
		self.left.browser_delalllistitems = self.leftdelalllistitems
		self.left.browser_addlistitems = self.leftaddlistitems
		self.left.browser_replacelistitem = self.leftreplacelistitem
		self.left.browser_selectitem = self.leftselectitem
		self.left.browser_makevisible = self.leftmakevisible
		self.left.buttons_setsensitive = self.leftbuttonssetsensitive
		self.left.browser_getselected = self.leftgetselected
		self.left.browser_getlist = self.leftgetlist

		self.right.browser_setlabel = self.rightsetlabel
		self.right.browser_show = self.rightshow
		self.right.browser_hide = self.righthide
		self.right.browser_dellistitems = self.rightdellistitems
		self.right.browser_delalllistitems = self.rightdelalllistitems
		self.right.browser_addlistitems = self.rightaddlistitems
		self.right.browser_replacelistitem = self.rightreplacelistitem
		self.right.browser_selectitem = self.rightselectitem
		self.right.browser_makevisible = self.rightmakevisible
		self.right.buttons_setsensitive = self.rightbuttonssetsensitive
		self.right.browser_getselected = self.rightgetselected
		self.right.browser_getlist = self.rightgetlist

	def __maketitle(self):
		return 'Hyperlinks (' + self.toplevel.basename + ')'

	def fixtitle(self):
		self.settitle(self.__maketitle())

	def __repr__(self):
		return '<LinkEdit instance, root=' + `self.root` + '>'

	def show(self):
		if not self.is_showing():
			self.toplevel.showstate(self, 1)
			self.updateform()
			LinkBrowserDialog.show(self)
			self.toplevel.checkviews()
			self.editmgr.register(self)

	def hide(self):
		if self.is_showing():
			self.toplevel.showstate(self, 0)
			self.editmgr.unregister(self)
			LinkBrowserDialog.hide(self)
			self.toplevel.checkviews()

	def delete_callback(self):
		self.hide()

	def destroy(self):
		LinkBrowserDialog.close(self)
		del self.left.browser_setlabel
		del self.left.browser_show
		del self.left.browser_hide
		del self.left.browser_dellistitems
		del self.left.browser_delalllistitems
		del self.left.browser_addlistitems
		del self.left.browser_replacelistitem
		del self.left.browser_selectitem
		del self.left.browser_makevisible
		del self.left.buttons_setsensitive
		del self.left.browser_getselected
		del self.right.browser_setlabel
		del self.right.browser_show
		del self.right.browser_hide
		del self.right.browser_dellistitems
		del self.right.browser_delalllistitems
		del self.right.browser_addlistitems
		del self.right.browser_replacelistitem
		del self.right.browser_selectitem
		del self.right.browser_makevisible
		del self.right.buttons_setsensitive
		del self.right.browser_getselected
		del self.left
		del self.right

	def get_geometry(self):
		pass

	# Method to return a whole-node anchor for a node, or optionally
	# create one.
	def wholenodeanchor(self, node, type=ATYPE_WHOLE):
		alist = MMAttrdefs.getattr(node, 'anchorlist')[:]
		for a in alist:
			if type == a[A_TYPE]:
				if type == ATYPE_DEST:
					return (node.GetUID(), a[A_ID])
				else:
					windowinterface.showmessage("Such an anchor already exists on this node")
					return None
		em = self.editmgr
		if not em.transaction(): return None
		a = ('0', type, [])
		alist.append(a)
		em.setnodeattr(node, 'anchorlist', alist[:])
		em.commit()
		rv = (node.GetUID(), '0')
		self.interesting.append(rv)
		return rv

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
		str.browser_setlabel('None')
		str.anchors = []

	def fill_node(self, str):
		str.browser_setlabel('Node:')
		str.anchors = getanchors(str.node, 0)

	def fill_all(self, str):
		str.browser_setlabel('All')
		str.anchors = getanchors(self.root, 1)

	def fill_relation(self, str):
		if str <> self.right:
			print 'LinkEdit: left anchorlist cannot be related!'
		str.browser_setlabel('Related')
		str.anchors = []
		if self.left.focus is None:
			return
		lfocus = self.left.anchors[self.left.focus]
		links = self.context.hyperlinks.findalllinks(lfocus, None)
		for l in links:
			if not l[ANCHOR2] in str.anchors:
				str.anchors.append(l[ANCHOR2])

	def fill_dangling(self, str):
		str.browser_setlabel('Dangling')
		all = getanchors(self.root, 1)
		nondangling = \
			  self.context.hyperlinks.findnondanglinganchordict()
		str.anchors = []
		for a in all:
			if not nondangling.has_key(a):
				str.anchors.append(a)

	def fill_interesting(self, str):
		str.browser_setlabel('Interesting')
		self.fixinteresting()
		str.anchors = self.interesting[:]

	def fill_external(self, str):
		str.browser_setlabel('External')
		str.anchors = self.toplevel.getallexternalanchors()

	def fill_keep(self, str):
		str.browser_setlabel('Kept')
		# check that all anchors still exist
		allanchors = getanchors(self.root, 1)
		oldanchors = str.anchors
		str.anchors = []
		for a in oldanchors:
			if a in allanchors:
				str.anchors.append(a)

	def finish_link(self, node):
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
		if not em.transaction(): return
		self.interesting.remove(srcanchor)
		if dstanchor in self.interesting:
			self.interesting.remove(dstanchor)
		link = srcanchor, dstanchor, DIR_1TO2, TYPE_JUMP
		em.addlink(link)
		em.commit()

	def set_interesting(self, anchor):
		self.interesting.append(anchor)

	def makename(self, anchor):
		if type(anchor) is not type(()):
			return anchor
		uid, aid = anchor
		if '/' in uid:
			return aid + ' in ' + uid
		node = self.context.mapuid(uid)
		nodename = node.GetRawAttrDef('name', '#' + uid)
		if type(aid) is not type(''): aid = `aid`
		return nodename + '.' + aid

	# This functions re-loads one of the anchor browsers.

	def reloadanchors(self, str, scroll):
		if str.hidden:
			str.browser_hide()
		else:
			str.browser_show()
		# Try to keep focus correct
		if str.focus is not None:
			focusvalue = str.anchors[str.focus]
		else:
			focusvalue = None
		str.focus = None
		# If the browser is node-bound, check that the node still
		# exists.
		if str.node:
			if str.node.GetRoot() is not self.root:
				str.node = None
				str.fillfunc = self.fill_none
		if hasattr(str, 'anchors'):
			oldanchors = str.anchors
		else:
			oldanchors = []
		str.fillfunc(str)
		if str.anchors != oldanchors:
			# Most of the code here is to make the
			# behavior of the scrolled lists acceptable.
			# We don't want the list to be scrolled if it
			# isn't necessary, and we want to keep the
			# focus visible.
			delete = []
			n = -1
			ordered = 1
			for i in range(len(oldanchors)):
				a = oldanchors[i]
				try:
					j = str.anchors.index(a)
				except ValueError:
					delete.append(i)
				else:
					if j < n:
						ordered = 0
						break
					n = j
			add = []
			n = -1
			for i in range(len(str.anchors)):
				a = str.anchors[i]
				try:
					j = oldanchors.index(a)
				except ValueError:
					add.append(i, a)
				else:
					if j < n:
						ordered = 0
						break
					n = j
			if ordered:
				if delete:
					str.browser_dellistitems(delete)
				names = []
				for i, a in add:
					name = self.makename(a)
					if not names:
						pos = i
					if i == pos + len(names):
						names.append(name)
					else:
						str.browser_addlistitems(names, pos)
						names = [name]
						pos = i
				if names:
					str.browser_addlistitems(names, pos)
			else:
				names = []
				for a in str.anchors:
					name = self.makename(a)
					names.append(name)
				str.browser_delalllistitems()
				str.browser_addlistitems(names, -1)
		# deal with possible node name changes
		list = str.browser_getlist()
		
		if len(list)==0:
			# deal with LinkEditDialog not hidden but destroyed (e.g win32)
			for i in range(len(str.anchors)):
				a = str.anchors[i]
				name = self.makename(a)
				list.append(name)
			if	len(list):
				str.browser_addlistitems(list, -1)
	
		for i in range(len(str.anchors)):
			a = str.anchors[i]
			name = self.makename(a)
			if name != list[i]:
				str.browser_replacelistitem(i, name)

		if focusvalue:
			try:
				str.focus = str.anchors.index(focusvalue)
			except ValueError:
				pass
##		if str.focus is None and str.anchors:
##			str.focus = 0
		if str.focus is None and len(str.anchors) == 1:
			str.focus = 0
		if str.focus is not None:
			str.browser_selectitem(str.focus)
			if scroll:
				str.browser_makevisible(str.focus)
			str.browser_show()
			str.buttons_setsensitive(1)
		else:
			str.buttons_setsensitive(0)
		if str.node:
			str.browser_setlabel('Node: ' +
					MMAttrdefs.getattr(str.node, 'name'))

	# This function reloads the link browser or makes it invisible
	def reloadlinks(self):
		slf = self.left.focus
		srf = self.right.focus
		if slf is None or (srf is None and not self.right.hidden):
			# At least one unfocussed anchorlist. No browser
			self.middlehide()
			self.linkfocus = None
			return
		lfocus = self.left.anchors[slf]
		if self.right.hidden:
			rfocus = None
		else:
			rfocus = self.right.anchors[srf]
		if self.linkfocus is None:
			fvalue = None
		else:
			fvalue = self.links[self.linkfocus]
		self.linkfocus = None
		self.links = self.context.hyperlinks.findalllinks(lfocus,
								  rfocus)
		lines = []
		for i in self.links:
			line = typestr[i[TYPE]] + ' ' + dirstr[i[DIR]]
			lines.append(line)
		self.middledelalllistitems()
		self.middleaddlistitems(lines, -1)
		if fvalue:
			try:
				self.linkfocus = self.links.index(fvalue)
			except ValueError:
				pass
		if self.links and self.linkfocus is None:
			self.linkfocus = 0
		if self.linkfocus is None:
			self.editsetsensitive(0)
			self.deletesetsensitive(0)
		else:
			self.middleselectitem(self.linkfocus)
			self.middlemakevisible(self.linkfocus)
			self.editsetsensitive(1)
			self.deletesetsensitive(1)
		self.middleshow()
		if self.right.hidden:
			self.addsetsensitive(0)
		else:
			self.addsetsensitive(1)
		if self.linkfocus:
			link = self.links[self.linkfocus]
			lfocus = link[ANCHOR1]
			rfocus = link[ANCHOR2]
		lnode = rnode = None
		lanchor = self.__findanchor(lfocus)
		ranchor = self.__findanchor(rfocus)
		if lanchor is None or ranchor is None or \
		   ((lanchor[A_TYPE] not in SourceAnchors or
		     ranchor[A_TYPE] not in DestinationAnchors) and \
		    (lanchor[A_TYPE] not in DestinationAnchors or
		     ranchor[A_TYPE] not in SourceAnchors)):
			# can only add links between a source and a
			# destionation anchor
			self.addsetsensitive(0)

	# Reload/redisplay all data
	def updateform(self, str = None):
		self.reloadanchors(self.left, str is None or str is self.left)
		self.reloadanchors(self.right, str is None or str is self.right)
		self.reloadlinks()

	# Start editing a link
	def startlinkedit(self, fromfocus):
		if fromfocus and  self.linkfocus is None:
			print 'LinkEdit: Start editing without focus!'
			return
		if fromfocus:
			editlink = self.links[self.linkfocus]
		else:
			slf = self.left.focus
			srf = self.right.focus
			if slf is None or (srf is None and not self.right.hidden):
				print 'LinkEdit: edit without anchor focus!'
				return
			n1 = self.left.anchors[slf]
			n2 = self.right.anchors[srf]
			if n1 == n2:
				windowinterface.beep()
				return
			a1 = self.__findanchor(n1)
			a2 = self.__findanchor(n2)
			if a1 is None or a2 is None:
				print 'LinkEdit: cannot find anchors!'
				return
			if a1[A_TYPE] not in SourceAnchors:
				# left node can only be destination
				if a2[A_TYPE] not in SourceAnchors:
					print 'LinkEdit: 2 destination achors!'
					return
				dir = DIR_2TO1
			else:
				dir = DIR_1TO2
			editlink = (n1, n2, dir, TYPE_JUMP)
		self.editorshow(editlink, not fromfocus)

	def __findanchor(self, anchor):
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


	# Callback functions
	def anchor_browser_callback(self, str):
		focus = str.browser_getselected()
		if focus != str.focus:
			str.focus = focus
			self.updateform(str)

	def show_callback(self, str):
		if str.focus is None:
			print 'LinkEdit: show without a focus!'
			return
		anchor = str.anchors[str.focus]
		if type(anchor) is not type(()):
			# external anchor
			print 'LinkEdit: anchor with unknown node UID!'
			return
		uid = anchor[0]
		try:
			node = self.context.mapuid(uid)
		except NoSuchUIDError:
			print 'LinkEdit: anchor with unknown node UID!'
			return
		top = self.toplevel
		top.setwaiting()
		top.hierarchyview.globalsetfocus(node)
		top.channelview.globalsetfocus(node)

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
			if str.node is None:
				str.fillfunc = self.fill_none
			else:
				str.fillfunc = self.fill_node
		elif ind == M_BVFOCUS:
			str.node = self.GetHierarchyViewFocus()
			if str.node is None:
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
		elif ind == M_KEEP:
			str.node = None
			str.fillfunc = self.fill_keep
		else:
			print 'Unknown menu selection'
			return
		self.updateform(str)

	def link_browser_callback(self):
		focus = self.middlegetselected()
		if focus != self.linkfocus:
			self.linkfocus = focus
			self.updateform()

	def link_new_callback(self, *dummy):
		self.linkfocus = None
		self.startlinkedit(0)
##		self.updateform()

	def link_delete_callback(self):
		if self.linkfocus is None:
			print 'LinkEdit: delete link w/o focus!'
			return
		l = self.links[self.linkfocus]
		em = self.editmgr
		if not em.transaction(): return
		em.dellink(l)
		em.commit()
		self.updateform()

	def link_edit_callback(self):
		if self.linkfocus is None:
			print 'LinkEdit: edit w/o focus!'
			return
		self.startlinkedit(1)
##		self.updateform()

	def anchoredit_callback(self, str):
		if str.focus is None:
			print 'LinkEdit: anchoredit without a focus!'
			return
		if type(anchor) is not type(()):
			# external anchor
			print 'LinkEdit: anchor with unknown node UID!'
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

	# EditMgr interface
	def transaction(self):
		return 1

	def rollback(self):
		pass

	def commit(self):
		self.updateform()

	def kill(self):
		self.hide()
		
	def editorshow(self, editlink, isnew):
		editor = LinkEditEditor(self, "Hyperlink properties", editlink, isnew)
		editor.run()

	def editsave(self, editlink):
		em = self.editmgr
		if not em.transaction(): return
		if self.linkfocus is not None:
			l = self.links[self.linkfocus]
			em.dellink(l)
		em.addlink(editlink)
		em.commit()

class LinkEditEditor(LinkEditorDialog):
	def __init__(self, parent, title, editlink, isnew):
		LinkEditorDialog.__init__(self, title, dirstr, typestr,
					  editlink[DIR], editlink[TYPE])
		self.parent = parent
		self.editlink = editlink
		self.changed = isnew
		self.oksetsensitive(self.changed)

	def run(self):
		self.show()
		return self.editlink
		
	def linkdir_callback(self):
		linkdir = self.linkdirgetchoice()
		l = self.editlink
		if l[DIR] != linkdir:
			self.changed = 1
			self.editlink = l[ANCHOR1], l[ANCHOR2], linkdir, \
					l[TYPE]
			self.linkdirsetchoice(linkdir)
			self.oksetsensitive(self.changed)

	def linktype_callback(self):
		linktype = self.linktypegetchoice()
		l = self.editlink
		if l[TYPE] != linktype:
			self.changed = 1
			self.editlink = l[ANCHOR1], l[ANCHOR2], l[DIR], \
					linktype
			self.linktypesetchoice(linktype)
			self.oksetsensitive(self.changed)

	def ok_callback(self):
		self.parent.editsave(self.editlink)
		self.close()

	def cancel_callback(self):
		self.close()
#
# General functions
#
def getanchors(node, recursive):
	rawanchors = MMAttrdefs.getattr(node, 'anchorlist')
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
