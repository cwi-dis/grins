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


def fix(r, g, b): return r, g, b	# Hook for color conversions


import settings
DISPLAY_VERTICAL = settings.get('vertical_structure')


# Color assignments (RGB)

BGCOLOR = fix(200, 200, 200)		# Light gray
BORDERCOLOR = fix(75, 75, 75)		# Dark gray
BORDERLIGHT = fix(255, 255, 255)	# White
CHANNELCOLOR = fix(240, 240, 240)	# Very light gray
CHANNELOFFCOLOR = fix(160, 160, 160)	# Darker gray
LEAFCOLOR = fix(208, 182, 160)		# Pale pinkish, match channel view
ALTNODECOLOR = fix(255, 224, 200)	# Same but brighter
BAGCOLOR = fix(152, 174, 200)		# Light blue
ALTCOLOR = fix(152, 200, 174)		# Light green
PARCOLOR = fix(150, 150, 150)		# Gray
SEQCOLOR = fix(150, 150, 150)		# Gray
TEXTCOLOR = fix(0, 0, 0)		# Black
CTEXTCOLOR = fix(50, 50, 50)		# Very dark gray
EXPCOLOR = fix(255, 0, 0)		# Red
COLCOLOR = fix(0, 255, 0)		# Green


# Focus color assignments (from light to dark gray)

FOCUSLEFT   = fix(244, 244, 244)
FOCUSTOP    = fix(204, 204, 204)
FOCUSRIGHT  = fix(40, 40, 40)
FOCUSBOTTOM = fix(91, 91, 91)
FOCUSBORDER = fix(0, 0, 0)		# Thin line around it


# Box types

ANCESTORBOX = 0
INNERBOX = 1
LEAFBOX = 2


# Fonts used below
f_title = windowinterface.findfont('Helvetica', 10)
f_channel = windowinterface.findfont('Helvetica', 8)

MINSIZE = 10.0				# minimum size for a node
LABSIZE = f_title.fontheight() * 1.5	# height of label
GAPSIZE = 1.0				# size of gap between nodes
EDGSIZE = 0.5				# size of edges


class HierarchyView(HierarchyViewDialog):

	#################################################
	# Outside interface                             #
	#################################################

	def __init__(self, toplevel):
		self.commands = [
			CLOSE_WINDOW(callback = (self.hide, ())),

			NEW_UNDER(callback = (self.createundercall, ())),

			COPY(callback = (self.copycall, ())),

			PLAYNODE(callback = (self.playcall, ())),
			PLAYFROM(callback = (self.playfromcall, ())),
			INFO(callback = (self.infocall, ())),
			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),
			ANCHORS(callback = (self.anchorcall, ())),
			CREATEANCHOR(callback = (self.createanchorcall, ())),
			FINISH_LINK(callback = (self.hyperlinkcall, ())),

			PUSHFOCUS(callback = (self.focuscall, ())),

			THUMBNAIL(callback = (self.thumbnailcall, ())),

			EXPANDALL(callback = (self.expandallcall, (1,))),
			COLLAPSEALL(callback = (self.expandallcall, (0,))),
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
		self.thumbnails = 1
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')
		HierarchyViewDialog.__init__(self)

	def __repr__(self):
		return '<HierarchyView instance, root=' + `self.root` + '>'

	def aftersetfocus(self):
		import Clipboard
		commands = self.commands
		if self.focusnode.GetType() in MMNode.interiortypes:
			popupmenu = self.interior_popupmenu
		else:
			popupmenu = self.leaf_popupmenu
		if self.focusnode is not self.root:
			# can't do certain things to the root
			commands = commands + self.notatrootcommands
		t, n = Clipboard.getclip()
		if t == 'node' and n is not None:
			# can only paste if there's something to paste
			if self.focusnode.GetType() in MMNode.interiortypes:
				# can only paste inside interior nodes
				commands = commands + self.pasteinteriorcommands
			if self.focusnode is not self.root:
				# can't paste before/after root node
				commands = commands + self.pastenotatrootcommands
		self.setcommands(commands)
		self.setpopup(popupmenu)

		# make sure focus is visible
		node = self.focusnode.GetParent()
		while node is not None:
			if not hasattr(node, 'expanded'):
				node.expanded = 1
			node = node.GetParent()

	def show(self):
		HierarchyViewDialog.show(self)
		self.aftersetfocus()
		self.window.bgcolor(BGCOLOR)
		self.objects = []
		# Other administratrivia
		self.editmgr.register(self)
		self.toplevel.checkviews()
		self.recalc()

	def hide(self, *rest):
		if not self.is_showing():
			return
		self.toplevel.showstate(self, 0)
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
		# RESIZE event.
		self.toplevel.setwaiting()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		self.displist = None
		self.recalcboxes()
		self.draw()

	def mouse(self, dummy, window, event, params):
		self.toplevel.setwaiting()
		x, y = params[0:2]
		self.select(x, y)

	def dropfile(self, dummy, window, event, params):
		import MMurl
		x, y, filename = params
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
		if obj.node.GetType() in MMNode.leaftypes:
			em = self.editmgr
			if not em.transaction():
				self.render()
				return
			obj.node.SetAttr('file', url)
			em.commit()
		else:
			self.create(0, url)


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

	def create(self, where, url = None):
		node = self.focusnode
		if node is None:
			windowinterface.showmessage(
				'There is no focus to insert to',
				mtype = 'error')
			return
		parent = node.GetParent()
		if parent is None and where <> 0:
			windowinterface.showmessage(
				"Can't insert before/after the root",
				mtype = 'error')
			return
		self.toplevel.setwaiting()
		if url is None:
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
		node = self.root.context.newnode(type)
		if url is not None:
			node.SetAttr('file', url)
		if layout == 'undefined' and \
		   self.toplevel.layoutview.curlayout is not None:
			node.SetAttr('layout', self.toplevel.layoutview.curlayout)
		if self.insertnode(node, where):
			import NodeInfo
			NodeInfo.shownodeinfo(self.toplevel, node, new = 1)

	def insertparent(self, type):
		node = self.focusnode
		if node is None:
			windowinterface.showmessage(
				'There is no focus to insert at',
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
				'There is no focus to paste to',
				mtype = 'error')
			return
		self.toplevel.setwaiting()
		if node.context is not self.root.context:
			node = node.CopyIntoContext(self.root.context)
		else:
			Clipboard.setclip(type, node.DeepCopy())
		dummy = self.insertnode(node, where)

	def insertnode(self, node, where):
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
		    if self.focusnode.GetType() not in MMNode.interiortypes:
			windowinterface.showmessage('Focus is a leaf node!',
						    mtype = 'error')
			node.Destroy()
			return 0
		em = self.editmgr
		if not em.transaction():
			node.Destroy()
			return 0
		if where == 0:
			em.addnode(self.focusnode, len(self.focusnode.GetChildren()), node)
			self.focusnode.expanded = 1
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
		if obj.node is not self.root and hasattr(obj.node, 'abox'):
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
			node.expanded = 1
			node = node.GetParent()
		self.recalc()

	# Recalculate the set of objects
	def makeboxes(self, list, node, box):
		t = node.GetType()
		if t in MMNode.leaftypes or \
		   not hasattr(node, 'expanded') or \
		   not node.GetChildren():
			list.append((node, LEAFBOX, box))
			return
		list.append((node, INNERBOX, box))
		left, top, right, bottom = box
		top = top + self.titleheight
		left = left + self.horedge
		bottom = bottom - self.veredge
		right = right - self.horedge
		children = node.GetChildren()
		size = 0
		horizontal = (t in ('par', 'alt')) == DISPLAY_VERTICAL
		for child in children:
			cht = child.GetType()
			if cht in MMNode.leaftypes or not hasattr(child, 'expanded'):
				size = size + MINSIZE
				if not horizontal:
					size = size + LABSIZE
			else:
				size = size + child.expanded[not horizontal]
		# size is minimum size required for children in mm
		if horizontal:
			gapsize = self.horgap
			totsize = right - left
		else:
			gapsize = self.vergap
			totsize = bottom - top
		# totsize is total available size for all children with inter-child gap
		factor = (totsize - (len(children) - 1) * gapsize) / size
		for child in children:
			cht = child.GetType()
			if cht in MMNode.leaftypes or not hasattr(child, 'expanded'):
				size = MINSIZE
				if not horizontal:
					size = size + LABSIZE
			else:
				size = child.expanded[not horizontal]
			if horizontal:
				right = left + size * factor
			else:
				bottom = top + size * factor
			self.makeboxes(list, child, (left, top, right, bottom))
			if horizontal:
				left = right + gapsize
			else:
				top = bottom + gapsize

	def recalcboxes(self):
		self.focusobj = None
		prevfocusobj = None
		rootobj = None
		rw, rh = self.window.getcanvassize(windowinterface.UNIT_MM)
		self.canvassize = rw, rh
		self.titleheight = float(LABSIZE) / rh
		self.horedge = float(EDGSIZE) / rw
		self.veredge = float(EDGSIZE) / rh
		self.horgap = float(GAPSIZE) / rw
		self.vergap = float(GAPSIZE) / rh
		list = []
		self.makeboxes(list, self.root, (0, 0, 1, 1))
		for item in list:
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

	def recalc(self):
		from windowinterface import UNIT_MM
		window = self.window
		self.cleanup()
		self.root.expanded = 1	# root always expanded
		width, height = sizeboxes(self.root)
		cwidth, cheight = window.getcanvassize(UNIT_MM)
		mwidth = mheight = 0 # until we have a way to get the min. size
		if (width <= cwidth <= width * 1.1 or width < cwidth <= mwidth) and \
		   (height <= cheight <= height * 1.1 or height < cheight <= mheight):
			# size change not big enough, just redraw
			self.redraw()
		else:
			# this call causes a ResizeWindow event
			window.setcanvassize((UNIT_MM, width, height))

	# Draw the window, assuming the object shapes are all right
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

##  	def helpcall(self):
## 		if self.focusobj: self.focusobj.helpcall()

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
def sizeboxes(node):
	t = node.GetType()
	if t in MMNode.leaftypes or not hasattr(node, 'expanded'):
		return MINSIZE, MINSIZE + LABSIZE
	children = node.GetChildren()
	nchildren = len(children)
	width = height = 0
	horizontal = (t in ('par', 'alt')) == DISPLAY_VERTICAL
	if children:
		for child in children:
			w, h = sizeboxes(child)
			if horizontal:
				# children laid out horizontally
				if h > height:
					height = h
				width = width + w + GAPSIZE
			else:
				# children laid out vertically
				if w > width:
					width = w
				height = height + h + GAPSIZE
		if horizontal:
			width = width - GAPSIZE
		else:
			height = height - GAPSIZE
		width = width + 2 * EDGSIZE
		height = height + 2 * EDGSIZE
	else:
		# minimum size if no children
		width = height = MINSIZE
	height = height + LABSIZE
	node.expanded = (width, height)
	return width, height

def do_expand(node, expand):
	t = node.GetType()
	if t in MMNode.leaftypes:
		return 0
	changed = 0
	if expand:
		if not hasattr(node, 'expanded'):
			node.expanded = 1
			changed = 1
	elif hasattr(node, 'expanded'):
		del node.expanded
		changed = 1
	for child in node.GetChildren():
		if do_expand(child, expand):
			changed = 1
	return changed			# any changes in this subtree

# XXX The following should be merged with ChannelView's GO class :-(

# (Graphical) object class
class Object:

	# Initialize an instance
	def __init__(self, mother, item):
		self.mother = mother
		self.node, self.boxtype, self.box = item
		self.name = MMAttrdefs.getattr(self.node, 'name')
		self.selected = 0
		self.ok = 1

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

	def draw(self):
		d = self.mother.new_displist
		dummy = d.usefont(f_title)
		rw, rh = self.mother.canvassize
		titleheight = self.mother.titleheight
		hmargin = d.strsize('x')[0] / 1.5
		vmargin = titleheight / 5
		l, t, r, b = self.box
		node = self.node
		nt = node.GetType()
		if nt in MMNode.leaftypes:
			color = LEAFCOLOR
		elif nt == 'seq':
			color = SEQCOLOR
		elif nt == 'par':
			color = PARCOLOR
		elif nt == 'bag':
			color = BAGCOLOR
		elif nt == 'alt':
			color = ALTCOLOR
		else:
			color = 255, 0, 0 # Red -- error indicator
		d.drawfbox(color, (l, t, r - l, b - t))
		self.drawfocus()
		t1 = min(b, t + titleheight + vmargin)
		if node.GetType() in MMNode.leaftypes and \
		   b-t-vmargin >= 2*titleheight:
			b1 = b - titleheight
			# draw channel name along bottom of box
			self.drawchannelname(l+hmargin/2, b1,
					     r-hmargin/2, b-vmargin/2)
			# draw thumbnail/icon if enough space
##			if b1-t1 >= titleheight and \
##			   r-l >= hmargin * 2.5:
			ctype = node.GetChannelType()
			f = os.path.join(self.mother.datadir, '%s.tiff' % ctype)
			if ctype == 'image' and self.mother.thumbnails:
				import MMurl
				try:
					f = MMurl.urlretrieve(node.context.findurl(MMAttrdefs.getattr(node, 'file')))[0]
				except IOError:
					# f not reassigned!
					pass
			if f is not None:
				ih = min(b1-t1, 2*titleheight)
				try:
					box = d.display_image_from_file(f, center = 1, coordinates = (l+hmargin, (t1+b1-ih)/2, r-l-2*hmargin, ih))
				except windowinterface.error:
					pass
				else:
					d.fgcolor(TEXTCOLOR)
					d.drawbox(box)
		# draw a little triangle to indicate expanded/collapsed state
		if node.GetType() in MMNode.interiortypes:
			awidth = LABSIZE/rw - 2*hmargin
			aheight = titleheight - 2*vmargin
			node.abox = l+hmargin, t+vmargin, l+hmargin+awidth, t+vmargin+aheight
			if hasattr(node, 'expanded'):
				# expanded node, point down
				d.drawfpolygon(EXPCOLOR,
					[(l+hmargin, t+vmargin),
					 (l+hmargin+awidth,t+vmargin),
					 (l+hmargin+awidth/2,t+vmargin+aheight)])
			else:
				# collapsed node, point right
				d.drawfpolygon(COLCOLOR,
					[(l+hmargin,t+vmargin),
					 (l+hmargin,t+vmargin+aheight),
					 (l+hmargin+awidth,t+vmargin+aheight/2)])

		# draw the name
		d.fgcolor(TEXTCOLOR)
		d.centerstring(l+hmargin/2, t+vmargin/2, r-hmargin/2, t1, self.name)
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
					x = l1
					while x < r1:
						d.drawline(TEXTCOLOR,
							   [(x, t1), (x, b1)])
						x = x + hmargin
				else:
					y = t1
					while y < b1:
						d.drawline(TEXTCOLOR,
							   [(l1, y), (r1, y)])
						y = y + vmargin

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
		d.draw3dbox(cl, ct, cr, cb, (l, t, r - l, b - t))

	# Menu handling functions

## 	def helpcall(self):
## 		import Help
## 		Help.givehelp('Hierarchy_view')

	def expandcall(self):
		self.mother.toplevel.setwaiting()
		if hasattr(self.node, 'expanded'):
			del self.node.expanded
		else:
			self.node.expanded = 1
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
