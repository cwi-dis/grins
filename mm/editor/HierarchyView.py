__version__ = "$Id$"

# New hierarchy view implementation.

# Beware: this module uses X11-like world coordinates:
# positive Y coordinates point down from the top of the window.
# Also the convention for box coordinates is (left, top, right, bottom)

import windowinterface, WMEVENTS
import MMAttrdefs
import MMNode
from HierarchyViewDialog import HierarchyViewDialog
from usercmd import *
import os
import urlparse, MMurl


import settings
DISPLAY_VERTICAL = settings.get('vertical_structure')
hierarchy_minimum_sizes = settings.get('hierarchy_minimum_sizes')
root_expanded = settings.get('root_expanded')
structure_name_size = settings.get('structure_name_size')


# Color assignments (RGB)

BGCOLOR = settings.get('structure_bgcolor')
LEAFCOLOR = settings.get('structure_leafcolor')
RPCOLOR = settings.get('structure_rpcolor')
SLIDECOLOR = settings.get('structure_slidecolor')
BAGCOLOR = settings.get('structure_bagcolor')
ALTCOLOR = settings.get('structure_altcolor')
PARCOLOR = settings.get('structure_parcolor')
SEQCOLOR = settings.get('structure_seqcolor')
TEXTCOLOR = settings.get('structure_textcolor')
CTEXTCOLOR = settings.get('structure_ctextcolor')
EXPCOLOR = settings.get('structure_expcolor')
COLCOLOR = settings.get('structure_colcolor')
ECBORDERCOLOR = settings.get('structure_ecbordercolor')

LEAFCOLOR_NOPLAY = settings.get('structure_darkleaf')
RPCOLOR_NOPLAY = settings.get('structure_darkrp')
SLIDECOLOR_NOPLAY = settings.get('structure_darkslide')
BAGCOLOR_NOPLAY = settings.get('structure_darkbag')
ALTCOLOR_NOPLAY = settings.get('structure_darkalt')
PARCOLOR_NOPLAY = settings.get('structure_darkpar')
SEQCOLOR_NOPLAY = settings.get('structure_darkseq')

# Focus color assignments (from light to dark gray)

FOCUSLEFT = settings.get('structure_focusleft')
FOCUSTOP = settings.get('structure_focustop')
FOCUSRIGHT = settings.get('structure_focusright')
FOCUSBOTTOM = settings.get('structure_focusbottom')


# Box types

ANCESTORBOX = 0
INNERBOX = 1
LEAFBOX = 2


# Fonts used below
f_title = windowinterface.findfont('Helvetica', 10)
f_channel = windowinterface.findfont('Helvetica', 8)

##class oldsizes:
##	SIZEUNIT = windowinterface.UNIT_MM # units for the following
##	MINSIZE = settings.get('thumbnail_size') # minimum size for a node
##	MAXSIZE = 2 * MINSIZE
##	TITLESIZE = f_title.fontheight()*1.2
##	CHNAMESIZE = f_channel.fontheight()*1.2
##	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
##	HOREXTRASIZE = f_title.strsize('XX')[0]
##	ARRSIZE = f_title.strsize('xx')[0]	# width of collapse/expand arrow
##	GAPSIZE = 1.0						# size of gap between nodes
##	HEDGSIZE = 1.0						# size of edges
##	VEDGSIZE = 1.0						# size of edges
##	FLATBOX = 0

class sizes_time:
	SIZEUNIT = windowinterface.UNIT_PXL # units for the following
	MINSIZE = 48 
	MAXSIZE = 128
	TITLESIZE = f_title.fontheightPXL()*1.2
	CHNAMESIZE = 0
	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
	HOREXTRASIZE = f_title.strsizePXL('XX')[0]
	ARRSIZE = f_title.strsizePXL('xx')[0]	# width of collapse/expand arrow
	GAPSIZE = 0 #2						# size of gap between nodes
	HEDGSIZE = 0 #3						# size of edges
	VEDGSIZE = 3 #3						# size of edges
	FLATBOX = 1

class sizes_notime:
	SIZEUNIT = windowinterface.UNIT_PXL # units for the following
	MINSIZE = 48 
	MAXSIZE = 128
	TITLESIZE = f_title.fontheightPXL()*1.2
	CHNAMESIZE = 0
	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
	HOREXTRASIZE = f_title.strsizePXL('XX')[0]
	ARRSIZE = f_title.strsizePXL('xx')[0]	# width of collapse/expand arrow
	GAPSIZE = 2 #2						# size of gap between nodes
	HEDGSIZE = 3 #3						# size of edges
	VEDGSIZE = 3 #3						# size of edges
	FLATBOX = 0

##class othersizes:
##	SIZEUNIT = windowinterface.UNIT_MM # units for the following
##	MINSIZE = settings.get('thumbnail_size') # minimum size for a node
##	MAXSIZE = 2 * MINSIZE
##	TITLESIZE = f_title.fontheight()*1.2
##	CHNAMESIZE = 0
##	LABSIZE = TITLESIZE+CHNAMESIZE		# height of labels
##	HOREXTRASIZE = f_title.strsize('XX')[0]
##	ARRSIZE = f_title.strsize('xx')[0]	# width of collapse/expand arrow
##	GAPSIZE = 1.0						# size of gap between nodes
##	HEDGSIZE = 1.0						# size of edges
##	VEDGSIZE = 1.0						# size of edges
##	FLATBOX = 0


#
# We expand a number of hierarchy levels on first open. The number
# given here is the number of _nodes_ we minimally want to open.
# We (of course) continue to open all nodes on the same level.
#
NODES_WANTED_OPEN = 7

class HierarchyView(HierarchyViewDialog):

	#################################################
	# Outside interface                             #
	#################################################

	def __init__(self, toplevel):
		self.sizes = sizes_notime
		self.commands = [
			CLOSE_WINDOW(callback = (self.hide, ())),

			COPY(callback = (self.copycall, ())),

			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),

			PUSHFOCUS(callback = (self.focuscall, ())),

			THUMBNAIL(callback = (self.thumbnailcall, ())),
			PLAYABLE(callback = (self.playablecall, ())),
			TIMESCALE(callback = (self.timescalecall, ())),

			EXPANDALL(callback = (self.expandallcall, (1,))),
			COLLAPSEALL(callback = (self.expandallcall, (0,))),
			]
		self.interiorcommands = [
			NEW_UNDER(callback = (self.createundercall, ())),
			]
		self.pasteinteriorcommands = [
			PASTE_UNDER(callback = (self.pasteundercall, ())),
			]
		self.pastenotatrootcommands = [
			PASTE_BEFORE(callback = (self.pastebeforecall, ())),
			PASTE_AFTER(callback = (self.pasteaftercall, ())),
			]
		self.notatrootcommands = [
			NEW_BEFORE(callback = (self.createbeforecall, ())),
			NEW_AFTER(callback = (self.createaftercall, ())),
			NEW_SEQ(callback = (self.createseqcall, ())),
			NEW_PAR(callback = (self.createparcall, ())),
			NEW_CHOICE(callback = (self.createbagcall, ())),
			NEW_ALT(callback = (self.createaltcall, ())),
			DELETE(callback = (self.deletecall, ())),
			CUT(callback = (self.cutcall, ())),
			EXPAND(callback = (self.expandcall, ())),
			]
		self.noslidecommands = [
			INFO(callback = (self.infocall, ())),
			FINISH_LINK(callback = (self.hyperlinkcall, ())),
			ANCHORS(callback = (self.anchorcall, ())),
			CREATEANCHOR(callback = (self.createanchorcall, ())),
			PLAYNODE(callback = (self.playcall, ())),
			PLAYFROM(callback = (self.playfromcall, ())),
			]
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commands.append(HELP(callback=(self.helpcall,())))

		self.window = None
		self.displist = None
		self.new_displist = None
		self.last_geometry = None
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.focusnode = self.prevfocusnode = self.root
		self.editmgr = self.root.context.editmgr
		self.destroynode = None	# node to be destroyed later
		self.expand_on_show = 1
		self.thumbnails = 1
		self.showplayability = 0
		self.timescale = 0
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')
		HierarchyViewDialog.__init__(self)

	def __repr__(self):
		return '<HierarchyView instance, root=' + `self.root` + '>'

	def aftersetfocus(self):
		import Clipboard
		commands = self.commands
		fnode = self.focusnode
		fntype = fnode.GetType()
		is_realpix = fntype == 'ext' and fnode.GetChannelType() == 'RealPix'
		if fntype in MMNode.interiortypes or is_realpix:
			popupmenu = self.interior_popupmenu
		else:
			popupmenu = self.leaf_popupmenu
		if fnode.__class__ is not SlideMMNode:
			commands = commands + self.noslidecommands
			if fntype in MMNode.interiortypes or \
			   (is_realpix and MMAttrdefs.getattr(fnode, 'file')):
				commands = commands + self.interiorcommands
		if fnode is not self.root:
			# can't do certain things to the root
			commands = commands + self.notatrootcommands
		t, n = Clipboard.getclip()
		if t == 'node' and n is not None:
			# can only paste if there's something to paste
			if n.__class__ is SlideMMNode:
				# Slide can only go in RealPix node
				if is_realpix and MMAttrdefs.getattr(fnode, 'file'):
					commands = commands + self.pasteinteriorcommands
				elif fntype == 'slide':
					commands = commands + self.pastenotatrootcommands
			else:
				if fntype in MMNode.interiortypes:
					# can only paste inside interior nodes
					commands = commands + self.pasteinteriorcommands
				if fnode is not self.root and fntype != 'slide':
					# can't paste before/after root node
					commands = commands + self.pastenotatrootcommands
		self.setcommands(commands)
		self.setpopup(popupmenu)

		# make sure focus is visible
		node = fnode.GetParent()
		while node is not None:
			if not hasattr(node, 'expanded'):
				expandnode(node)
			node = node.GetParent()

	def show(self):
		if self.is_showing():
			HierarchyViewDialog.show(self)
			return
		HierarchyViewDialog.show(self)
		self.aftersetfocus()
		self.window.bgcolor(BGCOLOR)
		self.objects = []
		# Other administratrivia
		self.editmgr.register(self)
		self.toplevel.checkviews()
		if self.expand_on_show:
			# Only do this the first time: open a few nodes
			self.expand_on_show = 0
			levels = countlevels(self.root, NODES_WANTED_OPEN)
			do_expand(self.root, 1, levels)
		expandnode(self.root)
		self.recalc()

	def hide(self, *rest):
		if not self.is_showing():
			return
		HierarchyViewDialog.hide(self)
		self.cleanup()
		self.editmgr.unregister(self)
		self.toplevel.checkviews()

	def is_showing(self):
		return self.window is not None

	def destroy(self):
		self.hide()

	def get_geometry(self):
		if self.window:
			self.last_geometry = self.window.getgeometry()

	def init_display(self):
		if self.new_displist:
			print 'init_display: new_displist already exists'
			self.new_displist.close()
		self.new_displist = self.displist.clone()

	def render(self):
		self.new_displist.render()
		self.displist.close()
		self.displist = self.new_displist
		self.new_displist = None

	#################################################
	# Outside interface (inherited from ViewDialog) #
	#################################################

	def getfocus(self):
		return self.focusnode

	def globalsetfocus(self, node):
		if not self.is_showing():
			return
		if not self.root.IsAncestorOf(node):
			raise RuntimeError, 'bad node passed to globalsetfocus'
		self.init_display()
		self.setfocusnode(node)
		if self.new_displist:
			# setfocusnode may have drawn already
			self.render()

	#################################################
	# Event handlers                                #
	#################################################

	def redraw(self, *rest):
		# RESIZE event. (the routine is misnamed)
		self.toplevel.setwaiting()
		self.cleanup()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		self.displist = None
		self.recalcboxes()
		self.draw()

	def mouse(self, dummy, window, event, params):
		self.toplevel.setwaiting()
		x, y = params[0:2]
		self.select(x, y)

	def cvdrop(self, obj, window, event, params):
		em = self.editmgr
		if not em.transaction():
			return
		node = obj.node
		em.setnodevalues(node, [])
		em.setnodetype(node, 'ext')
		em.commit()
		# try again, now with an ext node as destination
		self.dropfile(obj, window, event, params)

	def dropfile(self, maybeobj, window, event, params):
		x, y, filename = params
		if maybeobj is not None:
			obj = maybeobj
		else:
			obj = self.whichhit(x, y)
			if not obj:
				windowinterface.beep()
				return
		self.init_display()
		self.setfocusobj(obj)
		if event == WMEVENTS.DropFile:
			url = MMurl.pathname2url(filename)
		else:
			url = filename
		t = obj.node.GetType()
		if t == 'imm':
			self.render()
			windowinterface.showmessage('destination node is an immediate node, change to external?', mtype = 'question', callback = (self.cvdrop, (obj, window, event, params)))
			return
		if t == 'ext' and \
		   obj.node.GetChannelType() == 'RealPix':
			from mimetypes import guess_type
			mtype = guess_type(url)[0]
			interior = (mtype != 'image/vnd.rn-realpix')
			if interior and \
			   not MMAttrdefs.getattr(obj.node, 'file'):
				windowinterface.showmessage('can only edit a RealPix node if the URL has been filled in', mtype = 'error')
				self.render()
				return
		else:
			interior = (obj.node.GetType() in MMNode.interiortypes)
		if (interior and t == 'ext') or t == 'slide':
			# new or changed node is a slide, check URL
			if interior:
				purl = MMAttrdefs.getattr(obj.node, 'file')
			else:
				purl = MMAttrdefs.getattr(obj.node.GetParent(),
							  'file')
			purl = obj.node.GetContext().findurl(purl)
			url = cvslideurl(url, purl)
			if not url:
				# the error message has already been shown
				self.render()
				return
		else:
			# make URL relative to document
			url = self.toplevel.relative_url(url)
		if interior:
			horizontal = (t in ('par', 'alt')) == DISPLAY_VERTICAL
			i = -1
			# if node is expanded, determine where in the node
			# the file is dropped, else create at end
			if hasattr(obj.node, 'expanded'):
				# find the index of the first child where the
				# appropriate drop coordinate is after the
				# center of the child
				# if no such child, return -1 (which means
				# at the end)
				children = obj.node.children
				for i in range(len(children)):
					box = children[i].box
					if (x,y)[not horizontal] <= (box[not horizontal] + box[(not horizontal) + 2]) / 2:
						break
				else:
					i = -1
			self.create(0, url, i)
		else:
			em = self.editmgr
			if not em.transaction():
				self.render()
				return
			obj.node.SetAttr('file', url)
			if t == 'slide' and \
			   (MMAttrdefs.getattr(obj.node, 'displayfull') or
			    MMAttrdefs.getattr(obj.node, 'fullimage')):
				import Sizes
				purl = MMAttrdefs.getattr(obj.node.GetParent(), 'file')
				url = MMurl.basejoin(purl, url)
				url = obj.node.GetContext().findurl(url)
				w, h = Sizes.GetSize(url)
				if w != 0 and h != 0:
					if MMAttrdefs.getattr(obj.node, 'displayfull'):
						obj.node.SetAttr('subregionwh',(w,h))
					if MMAttrdefs.getattr(obj.node, 'fullimage'):
						obj.node.SetAttr('imgcropwh', (w,h))
			em.commit()

	def dragfile(self, dummy, window, event, params):
		x, y = params
		obj = self.whichhit(x, y)
		if not obj:
			windowinterface.setdragcursor('dragnot')
		elif obj.node.GetType() in MMNode.interiortypes:
			windowinterface.setdragcursor('dragadd')
		else:
			windowinterface.setdragcursor('dragset')

	#################################################
	# Edit manager interface (as dependent client)  #
	#################################################

	def transaction(self):
		return 1 # It's always OK to start a transaction

	def rollback(self):
		self.destroynode = None

	def commit(self):
		if self.destroynode:
			self.destroynode.Destroy()
		self.destroynode = None
		self.cleanup()
		if self.is_showing():
			self.recalc()

	def kill(self):
		self.destroy()

	#################################################
	# Upcalls from objects                          #
	#################################################

	def deletefocus(self, cut):
		node = self.focusnode
		if not node or node is self.root:
			windowinterface.beep()
			return
		em = self.editmgr
		if not em.transaction():
			return
		self.toplevel.setwaiting()
		parent = node.GetParent()
		siblings = parent.GetChildren()
		nf = siblings.index(node)
		if nf < len(siblings)-1:
			self.focusnode = siblings[nf+1]
		elif nf > 0:
			self.focusnode = siblings[nf-1]
		else:
			self.focusnode = parent
		self.aftersetfocus()
		em.delnode(node)
		if cut:
			import Clipboard
			t, n = Clipboard.getclip()
			if t == 'node' and node is not None:
				self.destroynode = n
			Clipboard.setclip('node', node)
		else:
			self.destroynode = node
		em.commit()

	def copyfocus(self):
		node = self.focusnode
		if not node:
			windowinterface.beep()
			return
		import Clipboard
		t, n = Clipboard.getclip()
		if t == 'node' and n is not None:
			n.Destroy()
		Clipboard.setclip('node', node.DeepCopy())
		self.aftersetfocus()

	def create(self, where, url = None, index = -1):
		node = self.focusnode
		if node is None:
			windowinterface.showmessage(
				'There is no selection to insert into',
				mtype = 'error')
			return
		parent = node.GetParent()
		if parent is None and where <> 0:
			windowinterface.showmessage(
				"Can't insert before/after the root",
				mtype = 'error')
			return
		self.toplevel.setwaiting()
		type = node.GetType()
		if (where == 0 and type == 'ext' and
		    node.GetChannelType() == 'RealPix') or \
		   (where != 0 and type == 'slide'):
			type = 'slide'
		elif url is None:
			type = node.GetType()
			if where == 0:
				children = node.GetChildren()
				if children:
					type = children[0].GetType()
		else:
			type = 'ext'
		if where <> 0:
			layout = MMAttrdefs.getattr(parent, 'layout')
		else:
			layout = MMAttrdefs.getattr(node, 'layout')
		if type == 'slide':
			ctx = node.GetContext()
			node = SlideMMNode('slide', ctx, ctx.newuid())
			ctx.knownode(node.GetUID(), node)
			# provide a default for tag attribute
			if url is not None:
				import Sizes
				node.SetAttr('tag', 'fadein')
				if where:
					pnode = self.focusnode.GetParent()
				else:
					pnode = self.focusnode
				purl = ctx.findurl(MMAttrdefs.getattr(pnode, 'file'))
				furl = MMurl.basejoin(purl,url)
				w,h = Sizes.GetSize(furl)
				if w != 0 and h != 0:
					node.SetAttr('subregionwh', (w,h))
					node.SetAttr('imgcropwh', (w,h))
				start, minstart = slidestart(pnode, furl, index)
				if minstart > start:
					node.SetAttr('start', minstart - start)
			else:
				node.SetAttr('tag', 'fill')
		else:
			node = self.root.context.newnode(type)
		if url is not None:
			node.SetAttr('file', url)
		if type != 'slide' and layout == 'undefined' and \
		   self.toplevel.layoutview is not None and \
		   self.toplevel.layoutview.curlayout is not None:
			node.SetAttr('layout', self.toplevel.layoutview.curlayout)
		if self.insertnode(node, where, index):
			if type == 'slide':
				import AttrEdit
				AttrEdit.showattreditor(self.toplevel, node)
			else:
				import NodeInfo
				NodeInfo.shownodeinfo(self.toplevel, node, new = 1)

	def insertparent(self, type):
		node = self.focusnode
		if node is None:
			windowinterface.showmessage(
				'There is no selection to insert at',
				mtype = 'error')
			return
		parent = node.GetParent()
		if parent is None:
			windowinterface.showmessage(
				"Can't insert above the root",
				mtype = 'error')
			return
		em = self.editmgr
		if not em.transaction():
			return
		self.toplevel.setwaiting()
		siblings = parent.GetChildren()
		i = siblings.index(node)
		em.delnode(node)
		newnode = node.GetContext().newnode(type)
		em.addnode(parent, i, newnode)
		em.addnode(newnode, 0, node)
		self.prevfocusnode = self.focusnode
		self.focusnode = newnode
		expandnode(newnode)
		self.aftersetfocus()
		em.commit()
		import NodeInfo
		NodeInfo.shownodeinfo(self.toplevel, newnode)

	def paste(self, where):
		import Clipboard
		type, node = Clipboard.getclip()
		if type <> 'node' or node is None:
			windowinterface.showmessage(
			    'The clipboard does not contain a node to paste',
			    mtype = 'error')
			return
		if self.focusnode is None:
			windowinterface.showmessage(
				'There is no selection to paste into',
				mtype = 'error')
			return
		self.toplevel.setwaiting()
		if node.context is not self.root.context:
			node = node.CopyIntoContext(self.root.context)
		else:
			Clipboard.setclip(type, node.DeepCopy())
		dummy = self.insertnode(node, where)

	def insertnode(self, node, where, index = -1):
		# 'where' is coded as follows: -1: before; 0: under; 1: after
		if where <> 0:
			parent = self.focusnode.GetParent()
			if parent is None:
				windowinterface.showmessage(
					"Can't insert before/after the root",
					mtype = 'error')
				node.Destroy()
				return 0
		elif where == 0:
			ntype = self.focusnode.GetType()
			if ntype not in MMNode.interiortypes and \
			   (ntype != 'ext' or
			    self.focusnode.GetChannelType() != 'RealPix' or
			    node.__class__ is not SlideMMNode):
				windowinterface.showmessage('Selection is a leaf node!',
							    mtype = 'error')
				node.Destroy()
				return 0
		em = self.editmgr
		if not em.transaction():
			node.Destroy()
			return 0
		if where == 0:
			em.addnode(self.focusnode, index, node)
			expandnode(self.focusnode)
		else:
			children = parent.GetChildren()
			i = children.index(self.focusnode)
			if where > 0:
				i = i+1
			em.addnode(parent, i, node)
		self.prevfocusnode = self.focusnode
		self.focusnode = node
		self.aftersetfocus()
		em.commit()
		return 1

	#################################################
	# Internal subroutines                          #
	#################################################

	# Clear the list of objects
	def cleanup(self):
		for obj in self.objects:
			obj.cleanup()
		self.objects = []
		self.focusobj = None

	# Navigation functions

	def tosibling(self, direction):
		if not self.focusnode:
			windowinterface.beep()
			return
		parent = self.focusnode.GetParent()
		if not parent:
			windowinterface.beep()
			return
		siblings = parent.GetChildren()
		i = siblings.index(self.focusnode) + direction
		if not 0 <= i < len(siblings):
			# XXX Could go to parent instead?
			windowinterface.beep()
			return
		self.setfocusnode(siblings[i])

	def toparent(self):
		if not self.focusnode:
			windowinterface.beep()
			return
		parent = self.focusnode.GetParent()
		if not parent:
			windowinterface.beep()
			return
		self.setfocusnode(parent)

	def tochild(self, i):
		if not self.focusnode:
			windowinterface.beep()
			return
		if self.focusnode.GetType() not in MMNode.interiortypes:
			windowinterface.beep()
			return
		children = self.focusnode.GetChildren()
		if i < 0: i = i + len(children)
		if not 0 <= i < len(children):
			windowinterface.beep()
			return
		self.setfocusnode(children[i])

	# Handle a selection click at (x, y)
	def select(self, x, y):
		obj = self.whichhit(x, y)
		if not obj:
			windowinterface.beep()
			return
		if (not root_expanded or obj.node is not self.root) and \
		   hasattr(obj.node, 'abox'):
			l, t, r, b = obj.node.abox
			if l <= x <= r and t <= y <= b:
				self.prevfocusnode = self.focusnode
				self.focusnode = obj.node
				obj.expandcall()
				return
		if obj.node is self.focusnode:
			return
		self.init_display()
		self.setfocusobj(obj)
		self.render()

	# Find the smallest object containing (x, y)
	def whichhit(self, x, y):
		hitobj = None
		for obj in self.objects:
			if obj.ishit(x, y):
				hitobj = obj
		return hitobj

	# Find the object corresponding to the node
	def whichobj(self, node):
		for obj in self.objects:
			if obj.node is node:
				return obj
		return None

	# Select the given object, deselecting the previous focus
	def setfocusobj(self, obj):
		if self.focusobj:
			self.focusobj.deselect()
		self.prevfocusnode = self.focusnode
		if obj:
			self.focusnode = obj.node
			self.focusobj = obj
			self.focusobj.select()
		else:
			self.focusnode = None
			self.focusobj = None
		self.aftersetfocus()

	# Select the given node as focus
	def setfocusnode(self, node):
		if not node:
			self.setfocusobj(None)
			return
		obj = self.whichobj(node)
		if obj:
			self.setfocusobj(obj)
			x1,y1,x2,y2 = obj.box
			self.window.scrollvisible((x1,y1,x2-x1,y2-y1))
			return
		self.prevfocusnode = self.focusnode
		self.focusnode = node
		# Need to expand some nodes
		node = node.GetParent()
		while node is not None:
			expandnode(node)
			node = node.GetParent()
		self.recalc()

	# Recursively position the boxes. Minimum sizes are already set, we may only have
	# to extend them.
	def makeboxes(self, list, node, box):
		t = node.GetType()
		left, top, right, bottom = box
		if not hasattr(node, 'expanded') or \
		   not node.GetChildren():
			if self.timescale:
				cw, ch = self.canvassize
				w, h, b = node.boxsize
				print "makebox", node, self.canvassize, node.boxsize #DBG
				if DISPLAY_VERTICAL:
					top = top + b / ch
					bottom = top + h / ch
				else:
					left = left + b / cw
					right = left + w / cw
			elif hierarchy_minimum_sizes:
				right = left + self.horsize
##				if node.__class__ is SlideMMNode:
##					right = right + self.horsize
				bottom = top + self.versize
			list.append((node, LEAFBOX, (left, top, right, bottom)))
			return left, top, right, bottom
		listindex = len(list)
		list.append((node, INNERBOX, box))
		top = top + self.titleheight
		left = left + self.horedge
		bottom = bottom - self.veredge
		right = right - self.horedge
		children = node.GetChildren()
		size = 0
		horizontal = (t in ('par', 'alt')) == DISPLAY_VERTICAL
		for child in children:
			size = size + child.boxsize[not horizontal]
			if DISPLAY_VERTICAL != horizontal:
				size = size + child.boxsize[2]
		# size is minimum size required for children in mm
		if horizontal:
			gapsize = self.horgap
			totsize = right - left
		else:
			gapsize = self.vergap
			totsize = bottom - top
		# totsize is total available size for all children with inter-child gap
		factor = (totsize - (len(children) - 1) * gapsize) / size
		maxr = 0
		maxb = 0
		for child in children:
			size = child.boxsize[not horizontal]
			if DISPLAY_VERTICAL != horizontal:
				size = size + child.boxsize[2]
			if horizontal:
				right = left + size * factor
			else:
				bottom = top + size * factor
			l,t,r,b = self.makeboxes(list, child, (left, top, right, bottom))
			if horizontal:
				left = r + gapsize
				if b > maxb: maxb = b
			else:
				top = b + gapsize
				if r > maxr: maxr = r
		if horizontal:
			maxr = left - gapsize + self.horedge
			maxb = maxb + self.veredge
		else:
			maxb = top - gapsize + self.veredge
			maxr = maxr + self.horedge
		box = box[0], box[1], maxr, maxb
		list[listindex] = node, INNERBOX, box
		return box

	# Intermedeate step in the recomputation of boxes. At this point the minimum
	# sizes are already set. We only have to compute gapsizes (based on current w/h),
	# call makeboxes to position the boxes and create the objects.
	def recalcboxes(self):
		self.focusobj = None
		prevfocusobj = None
		rootobj = None
		rw, rh = self.window.getcanvassize(self.sizes.SIZEUNIT)
		rw = float(rw)
		rh = float(rh)
		self.canvassize = rw, rh
		self.titleheight = float(self.sizes.TITLESIZE) / rh
		self.chnameheight = float(self.sizes.CHNAMESIZE) / rh
		self.horedge = float(self.sizes.HEDGSIZE) / rw
		self.veredge = float(self.sizes.VEDGSIZE) / rh
		self.horgap = float(self.sizes.GAPSIZE) / rw
		self.vergap = float(self.sizes.GAPSIZE) / rh
		self.horsize = float(self.sizes.MINSIZE + self.sizes.HOREXTRASIZE) / rw
		self.versize = float(self.sizes.MINSIZE + self.sizes.LABSIZE) / rh
		self.arrsize = float(self.sizes.ARRSIZE) / rw
		list = []
		self.makeboxes(list, self.root, (0, 0, 1, 1))
		for item in list:
			print 'BOX', item #DBG
			obj = Object(self, item)
			self.objects.append(obj)
			if item[0] is self.focusnode:
				self.focusobj = obj
			if item[0] is self.prevfocusnode:
				prevfocusobj = obj
			if item[0] is self.root:
				rootobj = obj
		if self.focusobj is not None:
			self.focusobj.selected = 1
		elif prevfocusobj is not None:
			self.focusnode = self.prevfocusnode
			self.focusobj = prevfocusobj
			prevfocusobj.selected = 1
		else:
			self.focusnode = self.root
			self.focusobj = rootobj
			rootobj.selected = 1
		self.aftersetfocus()
		x1,y1,x2,y2 = self.focusobj.box
		self.window.scrollvisible((x1,y1,x2-x1,y2-y1))

	# First step in box recomputation after an edit (or changing expand/collapse, etc):
	# computes minimum sizes of all nodes, and does either a redraw (if everything still
	# fits in the window) or a setcanvassize (which results in a resize, and hence
	# a redraw)
	def recalc(self):
		window = self.window
		self.cleanup()
		if root_expanded:
			expandnode(self.root) # root always expanded
		width, height, begin = self.sizeboxes(self.root, self.timescale)
		if DISPLAY_VERTICAL:
			height = height + begin
		else:
			width = width + begin
		cwidth, cheight = window.getcanvassize(self.sizes.SIZEUNIT)
		mwidth = mheight = 0 # until we have a way to get the min. size
		if not hierarchy_minimum_sizes and \
		   (width <= cwidth <= width * 1.1 or width < cwidth <= mwidth) and \
		   (height <= cheight <= height * 1.1 or height < cheight <= mheight):
			# size change not big enough, just redraw
			self.redraw()
		else:
			# this call causes a ResizeWindow event
			window.setcanvassize((self.sizes.SIZEUNIT, width, height))

	# Draw the window, assuming the object shapes are all right. This is the final
	# step in the redraw code (and the only step needed if we only enable
	# thumbnails, or do a similar action that does not affect box coordinates).
	def draw(self):
		displist = self.new_displist
		dummy = displist.usefont(f_title)
		for obj in self.objects:
			obj.draw()
		displist.render()
		if self.displist:
			self.displist.close()
		self.displist = displist
		self.new_displist = None

	# Menu handling functions

##	def helpcall(self):
##		if self.focusobj: self.focusobj.helpcall()

	def expandcall(self):
		if self.focusobj: self.focusobj.expandcall()

	def expandallcall(self, expand):
		if self.focusobj: self.focusobj.expandallcall(expand)

	def thumbnailcall(self):
		self.thumbnails = not self.thumbnails
		self.settoggle(THUMBNAIL, self.thumbnails)
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		self.draw()

	def playablecall(self):
		self.showplayability = not self.showplayability
		self.settoggle(PLAYABLE, self.showplayability)
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		self.draw()

	def timescalecall(self):
		self.timescale = not self.timescale
		if self.timescale:
			self.sizes = sizes_time
		else:
			self.sizes = sizes_notime
		self.settoggle(TIMESCALE, self.timescale)
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		self.recalc()

	def playcall(self):
		if self.focusobj: self.focusobj.playcall()

	def playfromcall(self):
		if self.focusobj: self.focusobj.playfromcall()

	def attrcall(self):
		if self.focusobj: self.focusobj.attrcall()

	def infocall(self):
		if self.focusobj: self.focusobj.infocall()

	def editcall(self):
		if self.focusobj: self.focusobj.editcall()

	# win32++
	def _editcall(self):
		if self.focusobj: self.focusobj._editcall()
	def _opencall(self):
		if self.focusobj: self.focusobj._opencall()

	def anchorcall(self):
		if self.focusobj: self.focusobj.anchorcall()

	def createanchorcall(self):
		if self.focusobj: self.focusobj.createanchorcall()

	def hyperlinkcall(self):
		if self.focusobj: self.focusobj.hyperlinkcall()

	def focuscall(self):
		if self.focusobj: self.focusobj.focuscall()

	def deletecall(self):
		if self.focusobj: self.focusobj.deletecall()

	def cutcall(self):
		if self.focusobj: self.focusobj.cutcall()

	def copycall(self):
		if self.focusobj: self.focusobj.copycall()

	def createbeforecall(self):
		if self.focusobj: self.focusobj.createbeforecall()

	def createaftercall(self):
		if self.focusobj: self.focusobj.createaftercall()

	def createundercall(self):
		if self.focusobj: self.focusobj.createundercall()

	def createseqcall(self):
		if self.focusobj: self.focusobj.createseqcall()

	def createparcall(self):
		if self.focusobj: self.focusobj.createparcall()

	def createbagcall(self):
		if self.focusobj: self.focusobj.createbagcall()

	def createaltcall(self):
		if self.focusobj: self.focusobj.createaltcall()

	def pastebeforecall(self):
		if self.focusobj: self.focusobj.pastebeforecall()

	def pasteaftercall(self):
		if self.focusobj: self.focusobj.pasteaftercall()

	def pasteundercall(self):
		if self.focusobj: self.focusobj.pasteundercall()


	# Recursive procedure to calculate geometry of boxes.
	def sizeboxes(self, node, structure_duration):
		# Helper for first step in size recomputation: compute minimum sizes of
		# all node boxes.
		ntype = node.GetType()
		minsize = self.sizes.MINSIZE
		if structure_duration:
			begin = MMAttrdefs.getattr(node, 'begin') * settings.get('time_scale_factor')
		else:
			begin = 0
		if structure_duration and ntype in MMNode.leaftypes:
			import Duration, math
			dur = Duration.get(node) * settings.get('time_scale_factor')
			if dur < 0:
				dur = 0
			elif dur > 1000:
				dur = 1000
			minsize = dur
		if DISPLAY_VERTICAL:
			minwidth = self.sizes.MINSIZE
			minheight = minsize
		else:
			minwidth = minsize
			minheight = self.sizes.MINSIZE
		if structure_name_size:
			name = MMAttrdefs.getattr(node, 'name')
			if self.sizes.SIZEUNIT == windowinterface.UNIT_MM:
				namewidth = (name and f_title.strsize(name)[0]) or 0
			else:
				namewidth = (name and f_title.strsizePXL(name)[0]) or 0
			if ntype in MMNode.interiortypes or \
			   (ntype == 'ext' and node.GetChannelType() == 'RealPix'):
				namewidth = namewidth + self.sizes.ARRSIZE
			minwidth = max(min(self.sizes.MAXSIZE, namewidth), minwidth) + self.sizes.HOREXTRASIZE
		else:
			minwidth = minwidth + self.sizes.HOREXTRASIZE
		children = node.GetChildren()
		if not hasattr(node, 'expanded') or not children:
			node.boxsize = minwidth, minheight + self.sizes.LABSIZE, begin
			return node.boxsize
		nchildren = len(children)
		width = height = 0
		horizontal = (ntype in ('par', 'alt')) == DISPLAY_VERTICAL
		for child in children:
			w, h, b = self.sizeboxes(child, structure_duration)
			if horizontal:
				# children laid out horizontally
				if h > height:
					height = h
				width = width + w + self.sizes.GAPSIZE
			else:
				# children laid out vertically
				if w > width:
					width = w
				height = height + h + self.sizes.GAPSIZE
			if DISPLAY_VERTICAL:
				height = height + b
			else:
				width = width + b
		if horizontal:
			width = width - self.sizes.GAPSIZE
		else:
			height = height - self.sizes.GAPSIZE
		width = max(width + 2 * self.sizes.HEDGSIZE, minwidth)
		height = height + self.sizes.VEDGSIZE + self.sizes.LABSIZE
		node.boxsize = width, height, begin
		return node.boxsize

def do_expand(node, expand, nlevels=None):
	if nlevels == 0:
		return 0
	if nlevels != None:
		nlevels = nlevels - 1
	ntype = node.GetType()
	if ntype not in MMNode.interiortypes and \
	   (ntype != 'ext' or node.GetChannelType() != 'RealPix'):
		return 0
	changed = 0
	if expand:
		if not hasattr(node, 'expanded'):
			expandnode(node)
			changed = 1
	elif hasattr(node, 'expanded'):
		collapsenode(node)
		changed = 1
	for child in node.GetChildren():
		if do_expand(child, expand, nlevels):
			changed = 1
	return changed			# any changes in this subtree

def countlevels(node, numwanted):
	on_this_level = [node]
	level = 1
	while 1:
		numwanted = numwanted - len(on_this_level)
		if numwanted <= 0 or not on_this_level:
			return level
		on_next_level = []
		for n in on_this_level:
			on_next_level = on_next_level + n.GetChildren()
		on_this_level = on_next_level
		level = level + 1

# XXX The following should be merged with ChannelView's GO class :-(

# (Graphical) object class
class Object:

	# Initialize an instance
	def __init__(self, mother, item):
		self.mother = mother
		node, self.boxtype, self.box = item
		node.box = self.box
		self.node = node
		if self.node.__class__ is SlideMMNode:
			self.name = MMAttrdefs.getattr(node, 'tag')
		else:
			self.name = MMAttrdefs.getattr(node, 'name')
		self.selected = 0
		self.ok = 1
		if node.GetType() == 'ext' and \
		   node.GetChannelType() == 'RealPix':
			if not hasattr(node, 'slideshow'):
				node.slideshow = SlideShow(node)

	# Make this object the focus
	def select(self):
		if self.selected:
			return
		self.selected = 1
		if self.ok:
			self.drawfocus()

	# Remove this object from the focus
	def deselect(self):
		if not self.selected:
			return
		self.selected = 0
		if self.ok:
			self.drawfocus()

	# Check for mouse hit inside this object
	def ishit(self, x, y):
		l, t, r, b = self.box
		return l <= x <= r and t <= y <= b

	def cleanup(self):
		self.mother = None
		node = self.node
		del node.box

	def draw(self):
		d = self.mother.new_displist
		dummy = d.usefont(f_title)
		rw, rh = self.mother.canvassize
		titleheight = self.mother.titleheight
		awidth = self.mother.arrsize
		chnameheight = self.mother.chnameheight
		##hmargin = d.strsize('x')[0] / 1.5
		##vmargin = titleheight / 5
		hmargin, vmargin = d.get3dbordersize()
		hmargin = hmargin*1.5
		vmargin = vmargin*1.5
		l, t, r, b = self.box
		node = self.node
		nt = node.GetType()
		willplay = not self.mother.showplayability or node.WillPlay()
		if nt in MMNode.leaftypes:
			if node.GetChannelType() == 'RealPix':
				if willplay:
					color = RPCOLOR
				else:
					color = RPCOLOR_NOPLAY
			else:
				if willplay:
					color = LEAFCOLOR
				else:
					color = LEAFCOLOR_NOPLAY
		elif nt == 'seq':
			if willplay:
				color = SEQCOLOR
			else:
				color = SEQCOLOR_NOPLAY
		elif nt == 'par':
			if willplay:
				color = PARCOLOR
			else:
				color = PARCOLOR_NOPLAY
		elif nt == 'bag':
			if willplay:
				color = BAGCOLOR
			else:
				color = BAGCOLOR_NOPLAY
		elif nt == 'alt':
			if willplay:
				color = ALTCOLOR
			else:
				color = ALTCOLOR_NOPLAY
		elif nt == 'slide':
			if willplay:
				color = SLIDECOLOR
			else:
				color = SLIDECOLOR_NOPLAY
		else:
			color = 255, 0, 0 # Red -- error indicator
		d.drawfbox(color, (l, t, r - l, b - t))
		self.drawfocus()
		t1 = min(b, t + titleheight + vmargin)
		if node.GetType() not in MMNode.interiortypes and \
		   not hasattr(node, 'expanded') and \
		   b-t-vmargin >= titleheight+chnameheight:
			if chnameheight:
				b1 = b - chnameheight
				# draw channel name along bottom of box
				if node.__class__ is not SlideMMNode:
					self.drawchannelname(l+hmargin/2, b1,
							     r-hmargin/2, b-vmargin/2)
			else:
				b1 = b - 1.5*vmargin
			# draw thumbnail/icon if enough space
##			if b1-t1 >= titleheight and \
##			   r-l >= hmargin * 2.5:
			ctype = node.GetChannelType()
			if node.__class__ is SlideMMNode and \
			   MMAttrdefs.getattr(node, 'tag') in ('fadein', 'crossfade', 'wipe'):
				ctype = 'image'
			f = os.path.join(self.mother.datadir, '%s.tiff' % ctype)
			url = node.GetAttrDef('file', None)
			if url and self.mother.thumbnails and ctype == 'image':
				if node.__class__ is SlideMMNode:
					url = MMurl.basejoin(MMAttrdefs.getattr(node.parent, 'file'), url)
				url = node.context.findurl(url)
				try:
					f = MMurl.urlretrieve(url)[0]
				except IOError:
					# f not reassigned!
					pass
			##ih = min(b1-t1, titleheight+chnameheight)
			ih = b1-t1
			if node.__class__ is SlideMMNode and \
			   MMAttrdefs.getattr(node, 'tag') in ('fill','fadeout'):
				d.drawfbox(MMAttrdefs.getattr(node, 'color'), (l+hmargin, (t1+b1-ih)/2, r-l-2*hmargin, ih))
				d.fgcolor(TEXTCOLOR)
				d.drawbox((l+hmargin, (t1+b1-ih)/2, r-l-2*hmargin, ih))
			elif f is not None:
				try:
					box = d.display_image_from_file(f, center = 1, coordinates = (l+hmargin, (t1+b1-ih)/2, r-l-2*hmargin, ih), scale=-2)
				except windowinterface.error:
					pass
				else:
					d.fgcolor(TEXTCOLOR)
					d.drawbox(box)
		# draw a little triangle to indicate expanded/collapsed state
		title_left = l+hmargin
		if (node.GetType() in MMNode.interiortypes and not \
		    (root_expanded and node is self.mother.root)) \
		    or \
		   (node.GetType() == 'ext' and
		    node.GetChannelType() == 'RealPix'):
			title_left = title_left + awidth
			aheight = titleheight - 2*vmargin
			node.abox = l+hmargin, t+vmargin, l+hmargin+awidth, t+vmargin+aheight
			if hasattr(node, 'expanded'):
				# expanded node, point down
				expcolor = EXPCOLOR
##				if :
##					expcolor = BGCOLOR
				d.drawfpolygon(expcolor,
					[(l+hmargin, t+vmargin),
					 (l+hmargin+awidth,t+vmargin),
					 (l+hmargin+awidth/2,t+vmargin+aheight)])
				d.drawline(ECBORDERCOLOR, [
					(l+hmargin, t+vmargin),
					(l+hmargin+awidth/2,t+vmargin+aheight),
					(l+hmargin+awidth,t+vmargin),
					])
			else:
				# collapsed node, point right
				d.drawfpolygon(COLCOLOR,
					[(l+hmargin,t+vmargin),
					 (l+hmargin,t+vmargin+aheight),
					 (l+hmargin+awidth,t+vmargin+aheight/2)])
				d.drawline(ECBORDERCOLOR, [
					(l+hmargin,t+vmargin),
					(l+hmargin+awidth,t+vmargin+aheight/2),
					(l+hmargin,t+vmargin+aheight),
					])

		# draw the name
		d.fgcolor(TEXTCOLOR)
		d.centerstring(title_left, t+vmargin/2, r-hmargin/2, t1, self.name)
		# If this is a node with suppressed detail,
		# draw some lines
		if self.boxtype == LEAFBOX and \
		   node.GetType() in MMNode.interiortypes and \
		   len(node.GetChildren()) > 0:
			l1 = l + hmargin*2
			t1 = t + titleheight + vmargin
			r1 = r - hmargin*2
			b1 = b - vmargin*2
			if l1 < r1 and t1 < b1:
				if (node.GetType() in ('par', 'alt')) == DISPLAY_VERTICAL:
					stepsize = (r1-l1)/2
					while stepsize > hmargin*4:
						stepsize = stepsize / 2
					x = l1
					while x <= r1:
						d.drawline(TEXTCOLOR,
							   [(x, t1), (x, b1)])
						x = x + stepsize
				else:
					stepsize = (b1-t1)/2
					while stepsize > vmargin*4:
						stepsize = stepsize / 2
					x = l1
					y = t1
					while y <= b1:
						d.drawline(TEXTCOLOR,
							   [(l1, y), (r1, y)])
						y = y + stepsize

	def drawchannelname(self, l, t, r, b):
		d = self.mother.new_displist
		d.fgcolor(CTEXTCOLOR)
		dummy = d.usefont(f_channel)
		d.centerstring(l, t, r, b, self.node.GetChannelName())
		dummy = d.usefont(f_title)

	def drawfocus(self):
		cl = FOCUSLEFT
		ct = FOCUSTOP
		cr = FOCUSRIGHT
		cb = FOCUSBOTTOM
		if self.selected:
			cl, cr = cr, cl
			ct, cb = cb, ct
		d = self.mother.new_displist
		l, t, r, b = self.box
		if self.mother.sizes.FLATBOX:
			d.fgcolor(ct)
			d.drawbox((l, t, r-l, b-t))
		else:
			d.draw3dbox(cl, ct, cr, cb, (l, t, r - l, b - t))

	# Menu handling functions

##	def helpcall(self):
##		import Help
##		Help.givehelp('Hierarchy_view')

	def expandcall(self):
		self.mother.toplevel.setwaiting()
		if hasattr(self.node, 'expanded'):
			collapsenode(self.node)
		else:
			expandnode(self.node)
		self.mother.recalc()

	def expandallcall(self, expand):
		self.mother.toplevel.setwaiting()
		if do_expand(self.node, expand):
			# there were changes
			# make sure root isn't collapsed
			self.mother.recalc()

	def playcall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.player.playsubtree(self.node)

	def playfromcall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.player.playfrom(self.node)

	def attrcall(self):
		self.mother.toplevel.setwaiting()
		import AttrEdit
		AttrEdit.showattreditor(self.mother.toplevel, self.node)

	def infocall(self):
		self.mother.toplevel.setwaiting()
		import NodeInfo
		NodeInfo.shownodeinfo(self.mother.toplevel, self.node)

	def changefile(self,file):
		self.mother.toplevel.setwaiting()
		try:
			import NodeInfoHelper
			h=NodeInfoHelper.NodeInfoHelper(self.mother.toplevel, self.node,0)
			h.browserfile_callback(file)
			h.ok_callback()
		except:
			pass

	def editcall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit.showeditor(self.node)
	def _editcall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit._showeditor(self.node)
	def _opencall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit._showviewer(self.node)

	def anchorcall(self):
		self.mother.toplevel.setwaiting()
		import AnchorEdit
		AnchorEdit.showanchoreditor(self.mother.toplevel, self.node)

	def createanchorcall(self):
		self.mother.toplevel.links.wholenodeanchor(self.node)

	def hyperlinkcall(self):
		self.mother.toplevel.links.finish_link(self.node)

	def focuscall(self):
		top = self.mother.toplevel
		top.setwaiting()
		if top.channelview is not None:
			top.channelview.globalsetfocus(self.node)

	def deletecall(self):
		self.mother.deletefocus(0)

	def cutcall(self):
		self.mother.deletefocus(1)

	def copycall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.copyfocus()

	def createbeforecall(self):
		self.mother.create(-1)

	def createaftercall(self):
		self.mother.create(1)

	def createundercall(self):
		self.mother.create(0)

	def createseqcall(self):
		self.mother.insertparent('seq')

	def createparcall(self):
		self.mother.insertparent('par')

	def createbagcall(self):
		self.mother.insertparent('bag')

	def createaltcall(self):
		self.mother.insertparent('alt')

	def pastebeforecall(self):
		self.mother.paste(-1)

	def pasteaftercall(self):
		self.mother.paste(1)

	def pasteundercall(self):
		self.mother.paste(0)

class SlideMMNode(MMNode.MMNode):
	def GetChannel(self):
		return None

	def GetChannelName(self):
		return 'undefined'

	def setgensr(self):
		self.gensr = self.gensr_leaf

	def GetAttrDef(self, attr, default):
		if self.attrdict.has_key(attr):
			return self.attrdict[attr]
		if attr == 'color':
			return MMAttrdefs.getattr(self.GetParent(), 'bgcolor')
		return default

class DummyRP:
	# used when parsing the RealPix file failed for some reason
	aspect = 'true'
	author = None
	width = height = 0
	duration = 0
	copyright = None
	maxfps = None
	preroll = None
	title = None
	url = None
	tags = []

	def __init__(self):
		bitrate = settings.get('system_bitrate')
		if bitrate >= 112000:
			bitrate = 80000
		elif bitrate >= 64000:
			bitrate = 45000
		elif bitrate >= 56000:
			bitrate = 34000
		elif bitrate >= 28800:
			bitrate = 20000
		elif bitrate >= 14400:
			bitrate = 10000
		else:
			bitrate = bitrate * 0.7
		self.bitrate = bitrate

class SlideShow:
	__callback_added = 0
	tmpfiles = []

	def __init__(self, node):
		if node.GetType() != 'ext' or \
		   node.GetChannelType() != 'RealPix':
			raise RuntimeError("shouldn't happen")
		update = 0
		self.node = node
		import realsupport
		ctx = node.GetContext()
		url = MMAttrdefs.getattr(node, 'file')
		if not url:
			name = MMAttrdefs.getattr(node, 'name') or '<unnamed>'
			cname = node.GetChannelName()
			windowinterface.showmessage('No URL specified for slideshow node %s on channel %s' % (name, cname), mtype = 'warning')
			rp = DummyRP()
		else:
			ourl = url
			url = ctx.findurl(url)
			utype, host, path, params, query, tag = urlparse.urlparse(url)
			url = urlparse.urlunparse((utype, host, path, params, query, ''))
			self.url = url
			fp = None
			try:
				fn, hdr = MMurl.urlretrieve(url)
				fp = open(fn)
				rp = realsupport.RPParser(fn, self.printfunc)
				rp.feed(fp.read())
				rp.close()
			except:
				rp = None
				if hasattr(ctx, 'template'):
					url = MMurl.basejoin(ctx.template, ourl)
					try:
						fn, hdr = MMurl.urlretrieve(url)
						fp = open(fn)
						rp = realsupport.RPParser(fn, self.printfunc)
						rp.feed(fp.read())
						rp.close()
						update = 1
					except:
						pass
					url = self.url
				if rp is None:
					windowinterface.showmessage('Cannot read slideshow file with URL %s in node %s on channel %s' % (url, MMAttrdefs.getattr(node, 'name') or '<unnamed>', node.GetChannelName()), mtype = 'warning')
					rp = DummyRP()
			if fp is not None:
				fp.close()
		self.url = url
		self.rp = rp
		attrdict = node.GetAttrDict()
		attrdict['bitrate'] = rp.bitrate
		if rp.width == 0 and rp.height == 0:
			# no size specified, initialize with channel size
			rp.width, rp.height = node.GetChannel().get('base_winoff',(0,0,256,256))[2:4]
		attrdict['size'] = rp.width, rp.height
		attrdict['duration'] = rp.duration
		if rp.aspect != 'true':
			attrdict['aspect'] = 0
		if rp.author is not None:
			attrdict['author'] = rp.author
		if rp.copyright is not None:
			attrdict['copyright'] = rp.copyright
		if rp.maxfps is not None:
			attrdict['maxfps'] = rp.maxfps
		if rp.preroll is not None:
			attrdict['preroll'] = rp.preroll
		if rp.title is not None:
			attrdict['title'] = rp.title
		if rp.url is not None:
			attrdict['href'] = rp.url
		self.editmgr = ctx.editmgr
		ctx.editmgr.registerfirst(self) # *must* come first
		if update:
			self.update(changed = 1)

	def destroy(self):
		del self.node
		del self.rp
		del self.editmgr

	def printfunc(self, msg):
		windowinterface.showmessage('While reading %s:\n\n' % self.url + msg)

	def transaction(self):
		return 1

	def rollback(self):
		pass

	def commit(self):
		self.update()

	def update(self, changed = 0):
		node = self.node
		oldrp = self.rp
		if node.GetType() != 'ext' or \
		   node.GetChannelType() != 'RealPix':
			# not a RealPix node anymore
			self.editmgr.unregister(self)
			collapsenode(node)
			del node.slideshow
			self.destroy()
			# XXX what to do with node.tmpfile?
			if hasattr(node, 'tmpfile'):
				try:
					os.unlink(node.tmpfile)
				except:
					pass
				del node.tmpfile
			return
		if oldrp is None:
			return
		ctx = node.GetContext()
		url = MMAttrdefs.getattr(node, 'file')
		if not url:
			# no URL specified, give warning and keep content
			name = MMAttrdefs.getattr(node, 'name') or '<unnamed>'
			cname = node.GetChannelName()
			windowinterface.showmessage('No URL specified for slideshow node %s on channel %s' % (name, cname), mtype = 'warning')
		else:
			url = ctx.findurl(url)
			utype, host, path, params, query, tag = urlparse.urlparse(url)
			url = urlparse.urlunparse((utype, host, path, params, query, ''))
			if url != self.url:
				# different URL specified
				try:
					fn, hdr = MMurl.urlretrieve(url)
				except IOError:
					# new file does not exist
					if self.url:
						outype, ohost, opath, oparams, oquery, tag = urlparse.urlparse(self.url)
						import posixpath
						if (outype, ohost, oparams, oquery) != (utype, host, params, query) or posixpath.dirname(opath) != posixpath.dirname(path):
							# different directory, new content
							rp = DummyRP()
						else:
							# same directory, keep content
							rp = self.rp
					else:
						# no original URL, keep content
						rp = self.rp
				else:
					# new file exists, use it
					import realsupport
					fp = open(fn)
					rp = realsupport.RPParser(fn)
					try:
						rp.feed(fp.read())
						rp.close()
					except:
						windowinterface.showmessage('error while reading RealPix file with URL %s in node %s on channel %s' % (url, MMAttrdefs.getattr(node, 'name') or '<unnamed>', node.GetChannelName()), mtype = 'warning')
						rp = DummyRP()
					fp.close()
				if rp is not self.rp and hasattr(node, 'tmpfile'):
					# new content, delete temp file
##					windowinterface.showmessage('You have edited the content of the slideshow file in node %s on channel %s' % (MMAttrdefs.getattr(node, 'name') or '<unnamed>', node.GetChannelName()), mtype = 'warning')
					choice = windowinterface.multchoice('Save changes to %s?' % self.url, ['Yes', 'No', 'Cancel'], 2)
					if choice == 2:
						# cancel
						node.SetAttr('file', self.url)
						self.update()
						return
					if choice == 0:
						# yes, save file
						node.SetAttr('file', self.url)
						writenodes(node)
						node.SetAttr('file', url)
					else:
						# no, discard changes
						try:
							os.unlink(node.tmpfile)
						except:
							pass
						del node.tmpfile
				self.url = url
				self.rp = rp
		rp = self.rp
		attrdict = node.GetAttrDict()
		if attrdict['bitrate'] != rp.bitrate:
			if rp is oldrp:
				rp.bitrate = attrdict['bitrate']
				changed = 1
			else:
				attrdict['bitrate'] = rp.bitrate
		size = attrdict.get('size', (256, 256))
		if size != (rp.width, rp.height):
			if rp is oldrp:
				rp.width, rp.height = size
				changed = 1
			else:
				if rp.width == 0 and rp.height == 0:
					rp.width, rp.height = node.GetChannel().get('base_winoff',(0,0,256,256))[2:4]
				attrdict['size'] = rp.width, rp.height
		if attrdict['duration'] != rp.duration:
			if rp is oldrp:
				rp.duration = attrdict['duration']
				changed = 1
			else:
				attrdict['duration'] = rp.duration
		aspect = attrdict.get('aspect', 1)
		if (rp.aspect == 'true') != aspect:
			if rp is oldrp:
				rp.aspect = ['false','true'][aspect]
				changed = 1
			else:
				attrdict['aspect'] = rp.aspect == 'true'
		if attrdict.get('author') != rp.author:
			if rp is oldrp:
				rp.author = attrdict.get('author')
				changed = 1
			elif rp.author is not None:
				attrdict['author'] = rp.author
			else:
				del attrdict['author']
		if attrdict.get('copyright') != rp.copyright:
			if rp is oldrp:
				rp.copyright = attrdict.get('copyright')
				changed = 1
			elif rp.copyright is not None:
				attrdict['copyright'] = rp.copyright
			else:
				del attrdict['copyright']
		if attrdict.get('title') != rp.title:
			if rp is oldrp:
				rp.title = attrdict.get('title')
				changed = 1
			elif rp.title is not None:
				attrdict['title'] = rp.title
			else:
				del attrdict['title']
		if attrdict.get('href') != rp.url:
			if rp is oldrp:
				rp.url = attrdict.get('href')
				changed = 1
			elif rp.url is not None:
				attrdict['href'] = rp.url
			else:
				del attrdict['href']
		if attrdict.get('maxfps') != rp.maxfps:
			if rp is oldrp:
				rp.maxfps = attrdict.get('maxfps')
				changed = 1
			elif rp.maxfps is not None:
				attrdict['maxfps'] = rp.maxfps
			else:
				del attrdict['maxfps']
		if attrdict.get('preroll') != rp.preroll:
			if rp is oldrp:
				rp.preroll = attrdict.get('preroll')
				changed = 1
			elif rp.preroll is not None:
				attrdict['preroll'] = rp.preroll
			else:
				del attrdict['preroll']
		if hasattr(node, 'expanded'):
			if oldrp is rp:
				i = 0
				children = node.children
				nchildren = len(children)
				taglist = rp.tags
				ntags = len(taglist)
				rp.tags = []
				nnodes = max(ntags, nchildren)
				while i < nnodes:
					if i < nchildren:
						childattrs = children[i].attrdict
						rp.tags.append(childattrs.copy())
					else:
						changed = 1
						childattrs = None
					if i < ntags:
						attrs = taglist[i]
					else:
						changed = 1
						attrs = None
					if childattrs != attrs:
						changed = 1
					i = i + 1
			else:
				# re-create children
				collapsenode(node)
				expandnode(node)
		if changed:
			if not hasattr(node, 'tmpfile'):
				url = MMAttrdefs.getattr(node, 'file')
				if not url:
					url = node.context.baseurl
				else:
					url = MMurl.basejoin(node.context.baseurl, url)
				if not url:
					windowinterface.showmessage('specify a location for this node')
					return
				utype, host, path, params, query, fragment = urlparse.urlparse(url)
				if (utype and utype != 'file') or \
				   (host and host != 'localhost'):
					windowinterface.showmessage('cannot do this for now')
					return
				import tempfile
				pre = tempfile.gettempprefix()
				dir = os.path.dirname(MMurl.url2pathname(path))
				while 1:
					tempfile.counter = tempfile.counter + 1
					file = os.path.join(dir, pre+`tempfile.counter`+'.rp')
					if not os.path.exists(file):
						break
				node.tmpfile = file
				if not SlideShow.__callback_added:
					windowinterface.addclosecallback(
						deltmpfiles, ())
					SlideShow.__callback_added = 1
				SlideShow.tmpfiles.append(file)
##			import realsupport
##			realsupport.writeRP(node.tmpfile, rp, node)
			MMAttrdefs.flushcache(node)

	def kill(self):
		pass

def deltmpfiles():
	for file in SlideShow.tmpfiles:
		try:
			os.unlink(file)
		except:
			pass
	SlideShow.tmpfiles = []

def expandnode(node):
	if hasattr(node, 'expanded'):
		# already expanded
		return
	node.expanded = 1
	if node.GetType() != 'ext' or node.GetChannelType() != 'RealPix':
		return
	if not hasattr(node, 'slideshow'):
		node.slideshow = SlideShow(node)
	ctx = node.GetContext()
	for attrs in node.slideshow.rp.tags:
		child = SlideMMNode('slide', ctx, ctx.newuid())
		ctx.knownode(child.GetUID(), child)
		child.parent = node
		node.children.append(child)
		child.attrdict.update(attrs)

def collapsenode(node):
	if hasattr(node, 'expanded'):
		del node.expanded
	# only remove children if they are of type SlideMMNode
	children = node.GetChildren()
	if not children or children[0].__class__ is not SlideMMNode:
		return
	ctx = node.GetContext()
	for child in children:
		child.parent = None
		ctx.forgetnode(child.GetUID())
	node.children = []

def writenodes(node, evallicense=0):
	if node.GetType() in MMNode.interiortypes:
		for child in node.children:
			writenodes(child, evallicense)
	elif hasattr(node, 'tmpfile'):
		import realsupport
		realsupport.writeRP(node.tmpfile, node.slideshow.rp, node)
		url = MMAttrdefs.getattr(node, 'file')
		if not url:
			# XXX--no URL specified for RealPix node
			return
		url = node.GetContext().findurl(url)
		utype, host, path, params, query, tag = urlparse.urlparse(url)
		if (not utype or utype == 'file') and \
		   (not host or host == 'localhost'):
			try:
				f = open(MMurl.url2pathname(path), 'w')
				f.write(open(node.tmpfile).read())
				f.close()
			except:
				print 'cannot write file for node',node
			else:
				del node.tmpfile
		else:
			# XXX complain
			print 'cannot write file for node',node

def cvslideurl(url, purl):
	# Convert url to be relative to purl.
	# If this is not posible, return a canonicalized version.
	utype, host, path, params, query, tag = urlparse.urlparse(purl)
	if (utype and utype != 'file') or (host and host != 'localhost'):
		windowinterface.showmessage('Can only edit local RealPix files', mtype = 'warning')
		return
	sutype, shost, spath, sparams, squery, stag = urlparse.urlparse(url)
	if (sutype and sutype != 'file') or (shost and shost != 'localhost'):
		return MMurl.canonURL(url)
	# both the RealPix URL and the slide URL are local files
	import posixpath
	if posixpath.isabs(spath):
		if not posixpath.isabs(path):
			# find absolute path of RealPix URL
			path = urlparse.urlparse(MMurl.pathname2url(os.path.join(os.getcwd(), MMurl.url2pathname(path))))[2]
		dir = posixpath.dirname(path)
		if spath[:len(dir)] == dir:
			# make relative
			url = spath[len(dir)+1:]
		else:
			return MMurl.canonURL(url)
	# nothing wrong with this URL that we can see
	return url

def slidestart(pnode, url, index):
	import Bandwidth
	i = index
	if i == -1:
		i = len(pnode.children)
	urls = {}
	start = MMAttrdefs.getattr(pnode, 'preroll')
	purl = MMAttrdefs.getattr(pnode, 'file')
	filesize = 0
	children = pnode.children
	for i in range(0, i):
		child = children[i]
		start = start + MMAttrdefs.getattr(child, 'start')
		if MMAttrdefs.getattr(child,'tag') in ('fadein', 'crossfade', 'wipe'):
			curl = MMAttrdefs.getattr(child, 'file')
			if not curl:
				continue
			curl = MMurl.basejoin(purl,curl)
			if not urls.has_key(curl):
				filesize = filesize + Bandwidth.GetSize(curl)
			urls[curl] = 0
	filesize = filesize + Bandwidth.GetSize(url)
	minstart = float(filesize) * 8 / MMAttrdefs.getattr(pnode, 'bitrate')
	return start, minstart
