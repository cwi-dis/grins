# New hierarchy view implementation.

# Beware: this module uses X11-like world coordinates:
# positive Y coordinates point down from the top of the window.
# Also the convention for box coordinates is (left, top, right, bottom)

import windowinterface, EVENTS, StringStuff
import MMAttrdefs
import MMNode
from ViewDialog import ViewDialog


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


class HierarchyView(ViewDialog):

	#################################################
	# Outside interface                             #
	#################################################

	def init(self, toplevel):
		self.window = None
		self.displist = None
		self.new_displist = None
		self.waiting = 0
		self.last_geometry = None
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.viewroot = self.root
		self.focusnode = self.root
		self.editmgr = self.root.context.editmgr
		self = ViewDialog.init(self, 'hview_')
		return self

	def __repr__(self):
		return '<HierarchyView instance, root=' + `self.root` + '>'

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Hierarchy View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1)
		if self.waiting:
			self.window.setcursor('watch')
		self.window.register(EVENTS.Mouse0Press, self.mouse, None)
		self.window.register(EVENTS.ResizeWindow, self.redraw, None)
		self.window.register(EVENTS.WindowExit, self.hide, None)
		self.window.bgcolor(BGCOLOR)
		self.objects = []
		# Other administratrivia
		self.editmgr.register(self)
		self.toplevel.checkviews()
		self.fixviewroot()
		self.recalc()
		self.draw()
		self.window.create_menu(self.focusobj.name, self.focusobj.menu)

	def hide(self, *rest):
		if not self.is_showing():
			return
		self.toplevel.showstate(self, 0)
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = None
		self.new_displist = None
		self.cleanup()
		self.editmgr.unregister(self)
		self.toplevel.checkviews()

	def setwaiting(self):
		self.waiting = 1
		if self.window:
			self.window.setcursor('watch')

	def setready(self):
		self.waiting = 0
		if self.window:
			self.window.setcursor('')

	def is_showing(self):
		return self.window is not None

	def destroy(self):
		self.hide()

	def get_geometry(self):
		if self.window:
			self.last_geometry = self.window.getgeometry()

	def init_display(self):
		if self.new_displist:
			print 'init_display: new_displist alread exists'
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

	def fixtitle(self):
		if self.is_showing():
			title = 'Hierarchy View (' + self.toplevel.basename + ')'
			self.window.settitle(title)

	#################################################
	# Event handlers                                #
	#################################################

	def redraw(self, *rest):
		# RESIZE event.
		self.recalc()
		self.draw()

	def mouse(self, dummy, window, event, params):
		x, y = params[0:2]
		self.select(x, y)

	# this doesn't work yet...
	def rawkey(self, dev, val):
		# raw key event (0-255)
		# 'val' is the key code as defined in DEVICE or <device.h>
		if val == 0: return # up
		if dev in (DEVICE.LEFTARROWKEY, DEVICE.PAD4):
			self.tosibling(-1)
		if dev in (DEVICE.RIGHTARROWKEY, DEVICE.PAD6):
			self.tosibling(1)
		if dev in (DEVICE.UPARROWKEY, DEVICE.PAD8):
			self.toparent()
		if dev in (DEVICE.DOWNARROWKEY, DEVICE.PAD2):
			self.tochild(0)
		if dev in (DEVICE.PAD5, DEVICE.PADPERIOD):
			self.zoomhere()

	#################################################
	# Edit manager interface (as dependent client)  #
	#################################################

	def transaction(self):
		return 1 # It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
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
		parent = node.GetParent()
		siblings = parent.GetChildren()
		nf = siblings.index(node)
		if nf < len(siblings)-1: self.focusnode = siblings[nf+1]
		elif nf > 0: self.focusnode = siblings[nf-1]
		else: self.focusnode = parent
		em.delnode(node)
		if cut:
			import Clipboard
			Clipboard.setclip('node', node)
		em.commit()

	def copyfocus(self):
		node = self.focusnode
		if not node:
			windowinterface.beep()
			return
		import Clipboard
		Clipboard.setclip('node', node.DeepCopy())

	def create(self, where):
		node = self.focusnode
		if node is None:
			windowinterface.showmessage(
				'There is no focus to insert to',
				type = 'error')
			return
		parent = node.GetParent()
		if parent is None and where <> 0:
			windowinterface.showmessage(
				"Can't insert before/after the root",
				type = 'error')
			return
		type = node.GetType()
		if where == 0:
			children = node.GetChildren()
			if children:
				type = children[0].GetType()
		node = self.root.context.newnode(type)
		if self.insertnode(node, where):
			import NodeInfo
			NodeInfo.shownodeinfo(self.toplevel, node)

	def insertparent(self, type):
		node = self.focusnode
		if node is None:
			windowinterface.showmessage(
				'There is no focus to insert at',
				type = 'error')
			return
		parent = node.GetParent()
		if parent is None:
			windowinterface.showmessage(
				"Can't insert above the root",
				type = 'error')
			return
		em = self.editmgr
		if not em.transaction():
			return
		siblings = parent.GetChildren()
		i = siblings.index(node)
		em.delnode(node)
		newnode = node.GetContext().newnode(type)
		em.addnode(parent, i, newnode)
		em.addnode(newnode, 0, node)
		self.focusnode = newnode
		em.commit()
		import NodeInfo
		NodeInfo.shownodeinfo(self.toplevel, newnode)

	def paste(self, where):
		import Clipboard
		type, node = Clipboard.getclip()
		if type <> 'node' or node is None:
			windowinterface.showmessage(
			    'The clipboard does not contain a node to paste',
			    type = 'error')
			return
		if self.focusnode is None:
			windowinterface.showmessage(
				'There is no focus to paste to',
				type = 'error')
			return
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
					type = 'error')
				node.Destroy()
				return 0
		elif where == 0:
		    if self.focusnode.GetType() not in MMNode.interiortypes:
			windowinterface.showmessage('Focus is a leaf node!',
						    type = 'error')
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
		em.commit()
		return 1

	def zoomout(self):
		if self.viewroot is self.root:
			windowinterface.beep()
			return
		windowinterface.setcursor('watch')
		self.viewroot = self.viewroot.GetParent()
		self.recalc()
		self.draw()
		windowinterface.setcursor('')

	def zoomin(self):
		if self.viewroot is self.focusnode or not self.focusnode:
			windowinterface.beep()
			return
		windowinterface.setcursor('watch')
		path = self.focusnode.GetPath()
		i = path.index(self.viewroot)
		self.viewroot = path[i+1]
		self.recalc()
		self.draw()
		windowinterface.setcursor('')

	def zoomhere(self):
		if self.viewroot is self.focusnode or not self.focusnode:
			return
		windowinterface.setcursor('watch')
		self.viewroot = self.focusnode
		self.recalc()
		self.draw()
		windowinterface.setcursor('')

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
				windowinterface.setcursor('watch')
				self.viewroot = self.focusnode
				self.recalc()
				self.draw()
				windowinterface.setcursor('')
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
			obj = makeobject(self, item)
			self.objects.append(obj)
			if item[0] in focuspath:
				# This relies on the fact that nodes
				# are listed in pre-order!
				self.focusobj = obj
		if self.focusobj:
			self.focusnode = self.focusobj.node
			self.focusobj.selected = 1
			self.window.create_menu(self.focusobj.name,
						self.focusobj.menu)
		else:
			self.focusnode = None

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
		makeboxes(list, self.viewroot, left, top, right, bottom, displist)
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

	# Get the current window shape and set the transformation.
	# Note that the Y axis is made to point down, like X coordinates!
	# Assume we are the current window.
	def getshape(self):
		gl.reshapeviewport()
		self.width, self.height = gl.getsize()
		x0, x1, y0, y1 = gl.getviewport()
		width, height = x1-x0, y1-y0
		MASK = 20
		gl.viewport(x0-MASK, x1+MASK, y0-MASK, y1+MASK)
		gl.scrmask(x0, x1, y0, y1)
		gl.ortho2(-MASK, width+MASK, height+MASK, -MASK)


# Recursive procedure to calculate geometry of boxes.
# This makes a box for the give node with the given dimensions,
# and if possible makes boxes for the children.
def makeboxes(list, node, left, top, right, bottom, displist):
	minwidth = displist.strsize('x')[0] * 4
	titleheight = displist.fontheight() * 1.5
	hmargin = minwidth / 6
	vmargin = titleheight / 5
	box = left, top, right, bottom
	height = bottom-top
	t = node.GetType()
	n = len(node.GetChildren())
	if t in MMNode.leaftypes or n == 0 \
		  or right-left < minwidth + 2*hmargin \
		  or bottom-top < 2*titleheight + 2*vmargin:
		list.append(node, LEAFBOX, box)
		return
	# Calculate space available for children
	top = top + titleheight + vmargin
	left = left + hmargin
	right = right - hmargin
	bottom = bottom - vmargin
	if t == 'par':
		avail = (right-left+hmargin) / n - hmargin
		if avail < minwidth:
			list.append(node, LEAFBOX, box)
			return
		list.append(node, INNERBOX, box)
		for i in range(n):
			c = node.GetChild(i)
			makeboxes(list, c, left, top, left+avail, bottom,
				  displist)
			left = left+avail+hmargin
			n = n-1
			if n > 0:
				avail = (right-left+hmargin) / n - hmargin
	else:
		avail = (bottom-top+vmargin) / n - vmargin
		if avail < titleheight:
			list.append(node, LEAFBOX, box)
			return
		list.append(node, INNERBOX, box)
		for i in range(n):
			c = node.GetChild(i)
			makeboxes(list, c, left, top, right, top+avail,
				  displist)
			top = top+avail+vmargin
			n = n-1
			if n > 0:
				avail = (bottom-top+vmargin) / n - vmargin


# XXX The following should be merged with ChannelView's GO class :-(

# Create a new object
def makeobject(mother, item):
	return Object(mother, item)

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
		self.menu = [
			(None, 'New node', [
				(None, 'Before focus', (self.createbeforecall, ())),
				(None, 'After focus', (self.createaftercall, ())),
				(None, 'Under focus', (self.createundercall, ())),
				(None, 'Above focus', [
					(None, 'Sequential', (self.createseqcall, ())),
					(None, 'Parallel', (self.createparcall, ())),
					(None, 'Bag', (self.createbagcall, ())),
					]),
				]),
			('d', 'Delete focus', (self.deletecall, ())),
			None,
			('x', 'Cut focus', (self.cutcall, ())),
			('c', 'Copy focus', (self.copycall, ())),
			(None, 'Paste', [
				(None, 'Before focus', (self.pastebeforecall, ())),
				(None, 'After focus', (self.pasteaftercall, ())),
				(None, 'Under focus', (self.pasteundercall, ())),
				]),
			None,
			('p', 'Play node...', (self.playcall, ())),
			('G', 'Play from here...', (self.playfromcall, ())),
			None,
			('i', 'Node info...', (self.infocall, ())),
			('a', 'Node attr...', (self.attrcall, ())),
			('e', 'Edit contents...', (self.editcall, ())),
			('t', 'Edit anchors...', (self.anchorcall, ())),
			('L', 'Finish hyperlink...', (self.hyperlinkcall, ())),
			None,
			('f', 'Push focus', (self.focuscall, ())),
			('z', 'Zoom out', (self.zoomoutcall, ())),
			('.', 'Zoom here', (self.zoomherecall, ())),
			('Z', 'Zoom in', (self.zoomincall, ())),
##			None,
##			('h', 'Help...', (self.helpcall, ())),
			]

	# Handle a right button mouse click in the object
	def popupmenu(self, x, y):
		func = self.__class__.menu.popup(x, y)
		if func: func(self)

	# Handle a shortcut in the object
	def shortcut(self, c):
		func = self.__class__.menu.shortcut(c)
		if func: func(self)
		else: gl.ringbell()

	# Make this object the focus
	def select(self):
		if self.selected:
			return
		self.selected = 1
		if self.ok:
			self.mother.window.create_menu(self.name, self.menu)
			self.drawfocus()

	# Remove this object from the focus
	def deselect(self):
		if not self.selected:
			return
		self.selected = 0
		if self.ok:
			self.mother.window.destroy_menu()
			self.drawfocus()

	# Check for mouse hit inside this object
	def ishit(self, x, y):
		l, t, r, b = self.box
		return l <= x <= r and t <= y <= b

	def cleanup(self):
		self.menu = []
		self.mother = None

	def draw(self):
		d = self.mother.new_displist
		dummy = d.usefont(f_title)
		titleheight = d.fontheight() * 1.5
		hmargin = d.strsize('x')[0] / 1.5
		vmargin = titleheight / 5
		l, t, r, b = self.box
		nt = self.node.GetType()
		if nt in MMNode.leaftypes:
			color = LEAFCOLOR
		elif nt == 'seq':
			color = SEQCOLOR
		elif nt == 'par':
			color = PARCOLOR
		elif nt == 'bag':
			color = BAGCOLOR
		else:
			color = 255, 0, 0 # Red -- error indicator
		d.drawfbox(color, (l, t, r - l, b - t))
		self.drawfocus()
		# Draw the name, centered in the box
		if self.node.GetType() in MMNode.leaftypes:
			b1 = b
			# Leave space for the channel if at all possible
			if b1-t-vmargin >= 2*titleheight:
				b1 = b1 - titleheight
				# And draw it now
				self.drawchannelname(l+hmargin/2, b1,
						     r-hmargin/2, b-vmargin/2)
		else:
			b1 = min(b, t + titleheight + vmargin)
		d.fgcolor(TEXTCOLOR)
		StringStuff.centerstring(d, l, t, r, b1, self.name)
		# If this is a node with suppressed detail,
		# draw some lines
		if self.boxtype == LEAFBOX and \
			  self.node.GetType() in MMNode.interiortypes and \
			  len(self.node.GetChildren()) > 0:
			l1 = l + hmargin*2
			t1 = t + titleheight + vmargin
			r1 = r - hmargin*2
			b1 = b - vmargin*2
			if l1 < r1 and t1 < b1:
				if self.node.GetType() == 'par':
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
		StringStuff.centerstring(d, l, t, r, b, C + ': ' + cname)
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

	def helpcall(self):
		import Help
		Help.givehelp('Hierarchy_view')

	def playcall(self):
		self.mother.toplevel.player.playsubtree(self.node)

	def playfromcall(self):
		self.mother.toplevel.player.playfrom(self.node)

	def attrcall(self):
		import AttrEdit
		AttrEdit.showattreditor(self.node)

	def infocall(self):
		import NodeInfo
		NodeInfo.shownodeinfo(self.mother.toplevel, self.node)

	def editcall(self):
		import NodeEdit
		NodeEdit.showeditor(self.node)
	
	def anchorcall(self):
		import AnchorEdit
		AnchorEdit.showanchoreditor(self.mother.toplevel, self.node)

	def hyperlinkcall(self):
		self.mother.toplevel.links.finish_link(self.node)

	def focuscall(self):
		self.mother.toplevel.channelview.globalsetfocus(self.node)

	def zoomoutcall(self):
		self.mother.zoomout()

	def zoomincall(self):
		self.mother.zoomin()

	def zoomherecall(self):
		self.mother.zoomhere()

	def deletecall(self):
		self.mother.deletefocus(0)

	def cutcall(self):
		self.mother.deletefocus(1)

	def copycall(self):
		self.mother.copyfocus()

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

	def pastebeforecall(self):
		self.mother.paste(-1)

	def pasteaftercall(self):
		self.mother.paste(1)

	def pasteundercall(self):
		self.mother.paste(0)
