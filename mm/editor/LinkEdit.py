__version__ = "$Id$"

# Link editor.

from MMExc import *
import MMAttrdefs
import AttrEdit
from ViewDialog import ViewDialog
import windowinterface
import MMTypes
import features

from Hlinks import ANCHOR1, ANCHOR2, DIR, DIR_1TO2, DIR_2TO1, DIR_2WAY
dirstr = ['->', '<-', '<->']

class Struct: pass

M_ALL = 1
M_DANGLING = 2
M_INTERESTING = 3
M_BVFOCUS = 5
M_RELATION = 6
M_NONE = 7
M_EXTERNAL = 8
M_KEEP = 9

from LinkEditLight import LinkEditLight
from LinkEditDialog import LinkBrowserDialog, LinkEditorDialog

class LinkEdit(LinkEditLight, LinkBrowserDialog, ViewDialog):
	def __init__(self, toplevel):
		LinkEditLight.__init__(self, toplevel)
		ViewDialog.__init__(self, 'links_')
		self.last_geometry = None
		self.root = toplevel.root
		self.left = Struct()
		self.right = Struct()
		self.left.fillfunc = self.fill_all
		self.right.fillfunc = self.fill_relation
		self.left.nodelist = []
		self.right.nodelist = []
		self.left.focus = None
		self.right.focus = None
		self.left.hidden = 0
		self.right.hidden = 0
		self.linkfocus = None

		LinkBrowserDialog.__init__(self, self.__maketitle(),
			[('All internal', (self.menu_callback, (self.left, M_ALL))),
			 ('Dangling',
			  (self.menu_callback, (self.left, M_DANGLING))),
			 ('Follow selection',
			  (self.menu_callback, (self.left, M_BVFOCUS))),
			 ], self.left,
			[('All internal', (self.menu_callback, (self.right, M_ALL))),
			  ('Dangling',
			   (self.menu_callback, (self.right, M_DANGLING))),
			  ('Follow selection',
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
		import MMurl
		basename = MMurl.unquote(self.toplevel.basename)
		return 'Hyperlinks (' + basename + ')'

	def fixtitle(self):
		self.settitle(self.__maketitle())

	def __repr__(self):
		return '<LinkEdit instance, root=' + `self.root` + '>'

	def show(self, node = None, anchor = None):
		if self.is_showing():
			LinkBrowserDialog.show(self)
		else:
			self.updateform()
			LinkBrowserDialog.show(self)
			self.toplevel.checkviews()
			self.followfocus = []
			self.editmgr.register(self, want_focus = 1)
		if node is not None:
			self.left.nodelist = [node]
			self.left.fillfunc = self.fill_node
			self.left.focus = None
			self.reloadanchors(self.left, 0)
			if anchor is None:
				# if no anchor given, select first
				# anchor
				if self.left.anchors:
					anchor = self.left.anchors[0]
			if anchor is not None:
				for i in range(len(self.left.anchors)):
					if self.left.anchors[i] is anchor:
						self.left.focus = i
						break
				self.right.nodelist = []
				self.right.fillfunc = self.fill_relation
			self.updateform(self.left)

	def hide(self):
		if self.is_showing():
			self.editmgr.unregister(self)
			LinkBrowserDialog.hide(self)
			self.toplevel.checkviews()

	def is_showing(self):
		return LinkBrowserDialog.is_showing(self)

	def delete_callback(self):
		self.hide()

	def destroy(self):
		LinkBrowserDialog.close(self)
		LinkEditLight.destroy(self)
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

	# The fill functions. These are set in the left and right structures
	# and used to fill the browsers.

	def fill_none(self, str):
		str.browser_setlabel('None')
		str.anchors = []

	def fill_node(self, str):
		str.browser_setlabel('From selection')
		str.anchors = []
		for n in str.nodelist:
			str.anchors = str.anchors + n.getanchors(0)

	def fill_all(self, str):
		str.browser_setlabel('All internal')
		str.anchors = self.root.getanchors(1)

	def fill_relation(self, str):
		if str != self.right:
			print 'LinkEdit: left anchorlist cannot be related!'
		str.browser_setlabel('Related')
		str.anchors = []
		if self.left.focus is None:
			return
		lfocus = self.left.anchors[self.left.focus]
		links = self.context.hyperlinks.findalllinks(lfocus, None)
		for l in links:
			if l[ANCHOR2] not in str.anchors:
				str.anchors.append(l[ANCHOR2])

	def fill_dangling(self, str):
		str.browser_setlabel('Dangling')
		all = self.root.getanchors(1)
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
		str.anchors = self.context.getexternalanchors()

	def fill_keep(self, str):
		str.browser_setlabel('Kept')
		# check that all anchors still exist
		allanchors = self.root.getanchors(1)
		oldanchors = str.anchors
		str.anchors = []
		for a in oldanchors:
			if a in allanchors:
				str.anchors.append(a)

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
		if str.nodelist:
			for i in range(len(str.nodelist)-1,-1,-1):
				if str.nodelist[i].GetRoot() is not self.root:
					del str.nodelist[i]
			if not str.nodelist:
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
					add.append((i, a))
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

		newlist = []
		for i in range(len(str.anchors)):
			a = str.anchors[i]
			name = self.makename(a)
			if i >= len(list):
				newlist.append(name)
			elif name != list[i]:
				str.browser_replacelistitem(i, name)
		if newlist:
			str.browser_addlistitems(newlist, -1)

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
			anchor = str.anchors[str.focus]
			if type(anchor) is type(''):
				str.buttons_setsensitive(0)
			else:
				str.buttons_setsensitive(1)
		else:
			str.buttons_setsensitive(0)
##		if str.nodelist and len(str.nodelist) == 1:
##			str.browser_setlabel('Node: ' +
##					MMAttrdefs.getattr(str.nodelist[0], 'name'))

	# This function reloads the link browser or makes it invisible
	def reloadlinks(self):
		slf = self.left.focus
		srf = self.right.focus
		if slf is None or (srf is None and not self.right.hidden):
			# At least one unfocussed anchorlist. No browser
			self.middlehide()
			self.linkfocus = None
			return
		hlinks = self.context.hyperlinks
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
		self.links = hlinks.findalllinks(lfocus, rfocus)
		lines = []
		for i in self.links:
			line = dirstr[i[DIR]]
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
		if lfocus is None or rfocus is None or \
		   lfocus is rfocus or \
		   ((type(lfocus) is type('') or
		     lfocus.GetType() != 'anchor' or
		     hlinks.findsrclinks(lfocus)) and \
		    (type(rfocus) is type('') or
		     rfocus.GetType() != 'anchor' or
		     hlinks.findsrclinks(rfocus))):
			# can only add links between a source and a
			# destination anchor, and only if the source
			# anchor is not already used as a link source
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
			hlinks = self.context.hyperlinks
			if type(n1) is type('') or n1.GetType() != 'anchor' or hlinks.findsrclinks(n1):
				# left node can only be destination
				if type(n2) is type('') or n2.GetType() != 'anchor' or hlinks.findsrclinks(n2):
					print 'LinkEdit: 2 destination achors!'
					return
				dir = DIR_2TO1
			else:
				dir = DIR_1TO2
			editlink = n1, n2, dir
		self.editorshow(editlink, not fromfocus)

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
		if type(anchor) is type(''):
			# external anchor
			print 'LinkEdit: external anchor!'
			return
		if anchor.GetType() == 'anchor':
			node = anchor.GetParent()
		else:
			node = anchor
		top = self.toplevel
		top.setwaiting()
		self.editmgr.setglobalfocus([node])

	def menu_callback(self, str, ind):
		if str in self.followfocus:
			self.followfocus.remove(str)
		self.addexternalsetsensitive(0)
		str.hidden = 0
		if ind == M_ALL:
			str.nodelist = []
			str.fillfunc = self.fill_all
		elif ind == M_DANGLING:
			str.nodelist = []
			str.fillfunc = self.fill_dangling
		elif ind == M_INTERESTING:
			str.nodelist = []
			str.fillfunc = self.fill_interesting
		elif ind == M_BVFOCUS:
			self.followfocus.append(str)
			self.globalfocuschanged(self.editmgr.getglobalfocus())
		elif ind == M_RELATION:
			str.nodelist = []
			str.fillfunc = self.fill_relation
		elif ind == M_NONE:
			str.nodelist = []
			str.fillfunc = self.fill_none
			str.hidden = 1
		elif ind == M_EXTERNAL:
			str.nodelist = []
			str.fillfunc = self.fill_external
			self.addexternalsetsensitive(1)
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
			str.nodelist = []
			str.fillfunc = self.fill_keep
		else:
			print 'Unknown menu selection'
			return
		self.updateform(str)

	def globalfocuschanged(self, focuslist, update = 1):
		for str in self.followfocus:
			str.nodelist = []
			for n in focuslist:
				if n.getClassName() == 'MMNode':
					str.nodelist.append(n)
			if not str.nodelist:
				str.fillfunc = self.fill_none
			else:
				str.fillfunc = self.fill_node
			if update:
				self.updateform(str)

	def add_external_callback(self):
		windowinterface.InputDialog('URL',
					    '',
					    self.new_external_callback,
					    cancelCallback = (self.new_external_callback, ()))

	def new_external_callback(self, url = None):
		if not url:
			return
		import string
		url = string.join(string.split(url, ' '), '%20')
		if url not in self.context.externalanchors:
			em = self.editmgr
			if not em.transaction(): return
			em.addexternalanchor(url)
			em.commit()
			self.updateform()

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
		# maybe add anchors of old link to interesting
		a = l[ANCHOR1]
		if type(a) is not type('') and \
		   a.GetType() == 'anchor' and \
		   not self.context.hyperlinks.findsrclinks(a):
			self.set_interesting(a)
		a = l[ANCHOR2]
		if type(a) is not type('') and \
		   a.GetType() == 'anchor' and \
		   not self.context.hyperlinks.findsrclinks(a):
			self.set_interesting(a)
		em.commit()
		self.updateform()

	def link_edit_callback(self):
		if self.linkfocus is None:
			print 'LinkEdit: edit w/o focus!'
			return
		self.startlinkedit(1)

	def anchoredit_callback(self, str):
		if str.focus is None:
			print 'LinkEdit: anchoredit without a focus!'
			return
		anchor = str.anchors[str.focus]
		if type(anchor) is type(''):
			# external anchor
			print 'LinkEdit: external anchor!'
			return
##		if anchor.GetType() == 'anchor':
##			node = anchor.GetParent()
##		else:
##			node = anchor
		AttrEdit.showattreditor(self.toplevel, anchor)

	# EditMgr interface
	def transaction(self, type):
		return 1

	def rollback(self):
		pass

	def commit(self, type):
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
			# maybe add anchors of old link to interesting
			a = l[ANCHOR1]
			if type(a) is not type('') and \
			   a.GetType() == 'anchor' and \
			   not self.context.hyperlinks.findsrclinks(a):
				self.set_interesting(a)
			a = l[ANCHOR2]
			if type(a) is not type('') and \
			   a.GetType() == 'anchor' and \
			   not self.context.hyperlinks.findsrclinks(a):
				self.set_interesting(a)
		em.addlink(editlink)
		# remove anchors involved in this link from interesting
		if editlink[ANCHOR1] in self.interesting:
			self.interesting.remove(editlink[ANCHOR1])
		if editlink[ANCHOR2] in self.interesting:
			self.interesting.remove(editlink[ANCHOR2])
		em.commit()

class LinkEditEditor(LinkEditorDialog):
	def __init__(self, parent, title, editlink, isnew):
		self.parent = parent
		a1, a2, dir = self.editlink = editlink
		self.changed = isnew
		hlinks = parent.context.hyperlinks
		llinks = rlinks = []
		if type(a1) is not type('') and a1.GetType() == 'anchor':
			llinks = hlinks.findsrclinks(a1)
			if not isnew and dir in (DIR_1TO2, DIR_2WAY) and llinks:
				del llinks[0]
		if type(a2) is not type('') and a2.GetType() == 'anchor':
			rlinks = hlinks.findsrclinks(a2)
			if not isnew and dir in (DIR_2TO1, DIR_2WAY) and rlinks:
				del rlinks[0]
		# XXX To do extend this interface with the new types
		# for now, keep the compatibility
		leftsrc = type(a1) is not type('') and a1.GetType() == 'anchor' and not llinks
		rightsrc = type(a2) is not type('') and a2.GetType() == 'anchor' and not rlinks
		LinkEditorDialog.__init__(self, title, dirstr,
					  dir,
					  [leftsrc,
					   rightsrc,
					   leftsrc and rightsrc])
		self.oksetsensitive(self.changed)

	def run(self):
		self.show()
		return self.editlink

	def linkdir_callback(self):
		linkdir = self.linkdirgetchoice()
		l = self.editlink
		if l[DIR] != linkdir:
			self.changed = 1
			# XXX for now, ignore sourcePlaystate and destinationPlaystate
			self.editlink = l[ANCHOR1], l[ANCHOR2], linkdir
			self.linkdirsetchoice(linkdir)
			self.oksetsensitive(self.changed)

	def ok_callback(self):
		self.parent.editsave(self.editlink)
		self.close()

	def cancel_callback(self):
		self.close()
