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


def fix(r, g, b): return r, g, b	# Hook for color conversions


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
			FINISH_LINK(callback = (self.hyperlinkcall, ())),

			PUSHFOCUS(callback = (self.focuscall, ())),

			CANVAS_HEIGHT(callback = (self.canvascall,
					(windowinterface.DOUBLE_HEIGHT,))),
			CANVAS_WIDTH(callback = (self.canvascall,
					(windowinterface.DOUBLE_WIDTH,))),
			CANVAS_RESET(callback = (self.canvascall,
					(windowinterface.RESET_CANVAS,))),
			THUMBNAIL(callback = (self.thumbnailcall, ())),
			]
		self.zoomincommands = [
			ZOOMIN(callback = (self.zoomincall, ())),
			ZOOMHERE(callback = (self.zoomherecall, ())),
			]
		self.zoomoutcommand = [
			ZOOMOUT(callback = (self.zoomoutcall, ())),
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
		self.viewroot = self.root
		self.focusnode = self.root
		self.editmgr = self.root.context.editmgr
		self.destroynode = None	# node to be destroyed later
		self.thumbnails = 1
		HierarchyViewDialog.__init__(self)

	def __repr__(self):
		return '<HierarchyView instance, root=' + `self.root` + '>'

	def aftersetfocus(self):
		import Clipboard
		commands = self.commands
		if self.focusnode is not self.root:
			# can't do certain things to the root
			commands = commands + self.notatrootcommands
		if self.viewroot is not self.focusnode:
			# can only zoom in if focus is different from viewroot
			commands = commands + self.zoomincommands
		if self.viewroot is not self.root:
			# can only zoom out if we're not already viewing root
			commands = commands + self.zoomoutcommand
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

	def show(self):
		HierarchyViewDialog.show(self)
		self.aftersetfocus()
		self.window.bgcolor(BGCOLOR)
		self.objects = []
		# Other administratrivia
		self.editmgr.register(self)
		self.toplevel.checkviews()
		self.fixviewroot()
		self.recalc()
		self.draw()

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
		self.recalc()
		self.draw()

	def mouse(self, dummy, window, event, params):
		self.toplevel.setwaiting()
		x, y = params[0:2]
		self.select(x, y)

## 	# this doesn't work yet...
## 	def rawkey(self, dev, val):
## 		# raw key event (0-255)
## 		# 'val' is the key code as defined in DEVICE or <device.h>
## 		if val == 0: return # up
## 		if dev in (DEVICE.LEFTARROWKEY, DEVICE.PAD4):
## 			self.tosibling(-1)
## 		if dev in (DEVICE.RIGHTARROWKEY, DEVICE.PAD6):
## 			self.tosibling(1)
## 		if dev in (DEVICE.UPARROWKEY, DEVICE.PAD8):
## 			self.toparent()
## 		if dev in (DEVICE.DOWNARROWKEY, DEVICE.PAD2):
## 			self.tochild(0)
## 		if dev in (DEVICE.PAD5, DEVICE.PADPERIOD):
## 			self.zoomhere()

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
			self.fixviewroot()
			self.recalc()
			self.draw()

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

	def create(self, where):
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
		type = node.GetType()
		if where == 0:
			children = node.GetChildren()
			if children:
				type = children[0].GetType()
		if where <> 0:
			layout = MMAttrdefs.getattr(parent, 'layout')
		else:
			layout = MMAttrdefs.getattr(node, 'layout')
		node = self.root.context.newnode(type)
		if not layout and self.toplevel.layoutview.curlayout is not None:
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
			em.addnode(self.focusnode, 0, node)
		else:
			children = parent.GetChildren()
			i = children.index(self.focusnode)
			if where > 0:
				i = i+1
			em.addnode(parent, i, node)
		self.focusnode = node
		self.aftersetfocus()
		em.commit()
		return 1

	def zoomout(self):
		if self.viewroot is self.root:
			windowinterface.beep()
			return
		self.viewroot = self.viewroot.GetParent()
		self.recalc()
		self.draw()

	def zoomin(self):
		if self.viewroot is self.focusnode or not self.focusnode:
			windowinterface.beep()
			return
		path = self.focusnode.GetPath()
		try:
			i = path.index(self.viewroot)
		except ValueError:
			# the focus is on one of the stacked (folded) nodes
			self.viewroot = self.focusnode
		else:
			self.viewroot = path[i+1]
		self.recalc()
		self.draw()

	def zoomhere(self):
		if self.viewroot is self.focusnode or not self.focusnode:
			return
		self.viewroot = self.focusnode
		self.recalc()
		self.draw()

	#################################################
	# Internal subroutines                          #
	#################################################

	# Make sure the view root and focus make sense (after a tree update)
	def fixviewroot(self):
		if self.viewroot.GetRoot() is not self.root:
			self.viewroot = self.root
		if self.focusnode and \
		   not self.root.IsAncestorOf(self.focusnode):
			self.focusnode = None
		if self.focusnode is None:
			self.focusnode = self.viewroot
		self.aftersetfocus()

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
		if obj.node is self.focusnode:
			# Double click -- zoom in or out
			if self.viewroot is not self.focusnode:
				self.viewroot = self.focusnode
				self.recalc()
				self.draw()
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
		if obj:
			self.focusnode = obj.node
			self.focusobj = obj
			self.focusobj.select()
		else:
			self.focusnode = None
			self.focusobj = None
		self.aftersetfocus()

	# Select the given node as focus, possibly zooming around
	def setfocusnode(self, node):
		if not node:
			self.setfocusobj(None)
			return
		obj = self.whichobj(node)
		if obj:
			self.setfocusobj(obj)
			return
		# Need to zoom around
		# XXX should zoom out less in some cases
		path = node.GetPath()
		for vr in path:
			self.viewroot = vr
			self.focusnode = node
			self.aftersetfocus()
			self.recalc()
			if self.focusnode is node:
				break
		self.draw()

	# Recalculate the set of objects
	def recalc(self):
		self.cleanup()
		if self.focusnode:
			focuspath = self.focusnode.GetPath()
		else:
			focuspath = []
		self.focusobj = None
		list = self.makegeometries()
		for item in list:
			obj = Object(self, item)
			self.objects.append(obj)
			if item[0] in focuspath:
				# This relies on the fact that nodes
				# are listed in pre-order!
				self.focusobj = obj
		if self.focusobj:
			self.focusnode = self.focusobj.node
			self.focusobj.selected = 1
		else:
			self.focusnode = None
		self.aftersetfocus()

	# Make a list of geometries for boxes
	def makegeometries(self):
		if self.new_displist:
			self.new_displist.close()
		displist = self.window.newdisplaylist(BGCOLOR)
		self.new_displist = displist
		bl, titleheight, ps = displist.usefont(f_title)
		amargin = displist.strsize('x')[0] * 2
		titleheight = titleheight * 1.5
		list = []
		left, top = 0, 0
		right, bottom = 1, 1
		path = self.viewroot.GetPath() # Ancestors of viewroot
		if bottom-top < len(path) * titleheight:
			# Truncate path, move viewroot up
			n = max(0, int((bottom-top)/titleheight) - 1)
			self.viewroot = path[n]
			path = path[:n+1]
		for node in path[:-1]:
			newtop = top + titleheight
			box = left + amargin, top, right - amargin, newtop
			list.append(node, ANCESTORBOX, box)
			top = newtop
		minwidth = displist.strsize('x')[0] * 4
		titleheight = displist.fontheight() * 1.5
		hmargin = minwidth / 6
		vmargin = titleheight / 5
		makeboxes(list, self.viewroot, left, top, right, bottom,
			  minwidth, titleheight, hmargin, vmargin)
		return list

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

	def canvascall(self, code):
		self.window.setcanvassize(code)

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

	def anchorcall(self):
		if self.focusobj: self.focusobj.anchorcall()

	def hyperlinkcall(self):
		if self.focusobj: self.focusobj.hyperlinkcall()

	def focuscall(self):
		if self.focusobj: self.focusobj.focuscall()

	def zoomoutcall(self):
		if self.focusobj: self.focusobj.zoomoutcall()

	def zoomincall(self):
		if self.focusobj: self.focusobj.zoomincall()

	def zoomherecall(self):
		if self.focusobj: self.focusobj.zoomherecall()

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
# This makes a box for the give node with the given dimensions,
# and if possible makes boxes for the children.
# The algorithm is as follows:
# Each of the children of node are allocated a minimum space (minwidth
# x titleheight).  How much of the extra space each child gets depends
# on how many children it has.  The "unit" extra space is the total
# extra space divided by the total number of children and
# grandchildren.  Each child is allocated n extra units where n is
# equal to the number of grandchildren plus one.
def makeboxes(list, node, left, top, right, bottom,
	      minwidth, titleheight, hmargin, vmargin):
	box = left, top, right, bottom
	t = node.GetType()
	children = node.GetChildren()
	nchildren = len(children)
	if t in MMNode.leaftypes or \
	   nchildren == 0 or \
	   right-left < minwidth + 2*hmargin or \
	   bottom-top < 2*titleheight + 2*vmargin:
		# no children, or expanded children won't fit
		list.append(node, LEAFBOX, box)
		return

	# Calculate space available for children
	top = top + titleheight + vmargin
	left = left + hmargin
	right = right - hmargin
	bottom = bottom - vmargin

	# calculate number of grandchildren
	ngrands = 0
	for c in children:
		ngrands = ngrands + len(c.GetChildren())

	# the two branches here are basically identical--the
	# horizontal and vertical directions have been exchanged
	if t == 'par':
		# children laid out horizontally
		# needed is the minimum space needed to draw all children
		needed = nchildren * (minwidth + hmargin) - hmargin
		# rest is the space left over to divide over the children
		rest = right - left - needed
		if rest < 0:
			# expanded children don't fit
			list.append(node, LEAFBOX, box)
			return
		# "draw" our box
		list.append(node, INNERBOX, box)
		# extra is the "unit" extra space
		extra = rest / (ngrands + nchildren)
		for c in children:
			# cright is the right edge of the child
			cright = left+minwidth+(1+len(c.GetChildren()))*extra
			makeboxes(list, c, left, top, cright, bottom,
				  minwidth, titleheight, hmargin, vmargin)
			# left is the left edge of the next child
			left = cright + hmargin
	else:
		# children laid out vertically
		# for other comments, see the other branch
		needed = nchildren * (titleheight + vmargin) - vmargin
		rest = bottom - top - needed
		if rest < 0:
			list.append(node, LEAFBOX, box)
			return
		extra = rest / (ngrands + nchildren)
		list.append(node, INNERBOX, box)
		for c in children:
			cbottom = top+titleheight+(1+len(c.GetChildren()))*extra
			makeboxes(list, c, left, top, right, cbottom,
				  minwidth, titleheight, hmargin, vmargin)
			top = cbottom + vmargin


# XXX The following should be merged with ChannelView's GO class :-(

# Fonts used below
f_title = windowinterface.findfont('Helvetica', 10)
f_channel = windowinterface.findfont('Helvetica', 8)

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
		titleheight = d.fontheight() * 1.5
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
		# Draw the name, centered in the box
		if node.GetType() in MMNode.leaftypes:
			b1 = b
			# Leave space for the channel if at all possible
			if b1-t-vmargin >= 2*titleheight:
				b1 = b1 - titleheight
				# And draw it now
				self.drawchannelname(l+hmargin/2, b1,
						     r-hmargin/2, b-vmargin/2)
				# draw thumbnail if enough space
				if self.mother.thumbnails and \
				   b1-t-vmargin >= 2*titleheight and \
				   r-l >= hmargin * 4.5 and \
				   node.GetChannelType() == 'image':
					import MMurl
					try:
						f = MMurl.urlretrieve(node.context.findurl(MMAttrdefs.getattr(node, 'file')))[0]
					except IOError:
						pass
					else:
						box = d.display_image_from_file(f, center = 0, coordinates = (l+hmargin, t+vmargin, r-l-2*hmargin, 2*titleheight))
						d.fgcolor(TEXTCOLOR)
						d.drawbox(box)
						t = box[1] + box[3]
		else:
			b1 = min(b, t + titleheight + vmargin)
		d.fgcolor(TEXTCOLOR)
		d.centerstring(l, t, r, b1, self.name)
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
				if node.GetType() == 'par':
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
		import ChannelMap
		cname = self.node.GetChannelName()
		ctype = self.node.GetChannelType()
		map = ChannelMap.shortcuts
		if map.has_key(ctype):
			C = map[ctype]
		else:
			C = '?'
		d = self.mother.new_displist
		d.fgcolor(CTEXTCOLOR)
		dummy = d.usefont(f_channel)
		d.centerstring(l, t, r, b, C + ': ' + cname)
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

	def editcall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit.showeditor(self.node)

	def anchorcall(self):
		self.mother.toplevel.setwaiting()
		import AnchorEdit
		AnchorEdit.showanchoreditor(self.mother.toplevel, self.node)

	def hyperlinkcall(self):
		self.mother.toplevel.links.finish_link(self.node)

	def focuscall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.channelview.globalsetfocus(self.node)

	def zoomoutcall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.zoomout()

	def zoomincall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.zoomin()

	def zoomherecall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.zoomhere()

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
