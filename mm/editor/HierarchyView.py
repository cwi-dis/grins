# New hierarchy view implementation.

# Like the channel view, this uses raw GL windows -- much simpler than
# trying to abuse FORMS.

# Beware: this module uses X11-like world coordinates:
# positive Y coordinates point down from the top of the window.
# Also the convention for box coordinates is (left, top, right, bottom)

import gl
import GL
import DEVICE
import fl
import MMAttrdefs
import MMNode
import FontStuff
from Dialog import GLDialog
from ViewDialog import ViewDialog


def fix(r, g, b): return r, g, b	# Hook for color conversions


# Color assignments (RGB)

BGCOLOR = fix(200, 200, 200)		# Light gray
BORDERCOLOR = fix(75, 75, 75)		# Dark gray
BORDERLIGHT = fix(255, 255, 255)	# White
CHANNELCOLOR = fix(240, 240, 240)	# Very light gray
CHANNELOFFCOLOR = fix(160, 160, 160)	# Darker gray
LEAFCOLOR = fix(208, 182, 160)		# Pale pinkish, match block view nodes
ALTNODECOLOR = fix(255, 224, 200)	# Same but brighter
BAGCOLOR = fix(152, 174, 200)		# Light blue
PARCOLOR = fix(150, 150, 150)		# Gray
SEQCOLOR = fix(150, 150, 150)		# Gray
TEXTCOLOR = fix(0, 0, 0)		# Black


# Focus color assignments (from light to dark gray)

FOCUSLEFT   = fix(244, 244, 244)
FOCUSTOP    = fix(204, 204, 204)
FOCUSRIGHT  = fix(40, 40, 40)
FOCUSBOTTOM = fix(91, 91, 91)
FOCUSBORDER = fix(0, 0, 0)		# Thin line around it


# Geometry parameters

TITLEHEIGHT = 25			# Height of box' title bar
MINWIDTH = 30				# Minimal box width
MARGIN = 5				# Margin around nested boxes
AMARGIN = 15				# Margin left/right of ANCESTORBOXes


# Box types

ANCESTORBOX = 0
INNERBOX = 1
LEAFBOX = 2


class HierarchyView(ViewDialog, GLDialog):

	#################################################
	# Outside interface (inherited from GLDialog)   #
	#################################################

	def init(self, toplevel):
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.viewroot = self.root
		self.focusnode = None
		self.editmgr = self.root.context.editmgr
		title = 'Hierarchy View (' + toplevel.basename + ')'
		self = ViewDialog.init(self, 'hview_')
		return GLDialog.init(self, title)

	def __repr__(self):
		return '<HierarchyView instance, root=' + `self.root` + '>'

	def setwin(self):
		GLDialog.setwin(self)
		FontStuff.setfont()

	def show(self):
		if self.is_showing():
			self.setwin()
			return
		GLDialog.show(self)
		self.initwindow()
		self.objects = []
		# Other administratrivia
		self.editmgr.register(self)
		self.toplevel.checkviews()
		self.fixviewroot()
		self.getshape()
		self.recalc()
		self.draw()

	def hide(self):
		if not self.is_showing():
			return
		GLDialog.hide(self)
		self.cleanup()
		self.editmgr.unregister(self)
		self.toplevel.checkviews()

	#################################################
	# Outside interface (inherited from ViewDialog) #
	#################################################

	def getfocus(self):
		return self.focusnode

	def globalsetfocus(self, node):
		if not self.root.IsAncestorOf(node):
			raise RuntimeError, 'bad node passed to globalsetfocus'
		self.focusnode = node
		if self.focusnode.IsAncestorOf(self.viewroot):
			self.viewroot = self.focusnode
		self.recalc()
		if self.focusnode <> node and self.viewroot <> self.focusnode:
			# Need to zoom around
			path = node.GetPath()
			for vr in path:
				self.viewroot = vr
				self.focusnode = node
				self.recalc()
				if self.focusnode is node:
					break
		self.setwin()
		self.draw()

	#################################################
	# Event handlers (called by GLDialog)           #
	#################################################

	def redraw(self):
		# REDRAW event.  This may also mean a resize!
		if (self.width, self.height) <> gl.getsize():
			self.getshape()
			self.recalc()
		self.draw()

	def mouse(self, dev, val):
		# MOUSE[123] event.
		# 'dev' is MOUSE[123].  'val' is 1 for down, 0 for up.
		# First translate (x, y) to world coordinates
		# (This assumes world coord's are X-like)
		x = gl.getvaluator(DEVICE.MOUSEX)
		y = gl.getvaluator(DEVICE.MOUSEY)
		x0, y0 = gl.getorigin()
		width, height = gl.getsize()
		x = x - x0
		y = height - (y - y0)
		#
		if dev == DEVICE.LEFTMOUSE:
			if val == 0: # up
				self.select(x, y)
		elif dev == DEVICE.RIGHTMOUSE:
			if val == 1: # down
				if self.focusobj:
					self.focusobj.popupmenu(x, y)

	def keybd(self, val):
		# KEYBD event.
		# 'val' is the ASCII value of the character.
		c = chr(val)
		if self.focusobj:
			self.focusobj.shortcut(c)

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
			self.setwin()
			self.fixviewroot()
			self.recalc()
			self.draw()

	def kill(self):
		self.destroy()

	#################################################
	# Upcalls from objects                          #
	#################################################

	def deletefocus(self, cut):
		if not self.focusnode or self.focusnode is self.root:
			gl.ringbell()
			return
		em = self.editmgr
		if not em.transaction():
			return
		parent = self.focusnode.GetParent()
		siblings = parent.GetChildren()
		nf = siblings.index(self.focusnode)
		if nf < len(siblings)-1: newfocus = siblings[nf+1]
		elif nf > 0: newfocus = siblings[nf-1]
		else: newfocus = parent
		if cut:
			import Clipboard
			Clipboard.setclip('node', self.focusnode)
		em.delnode(self.focusnode)
		self.focusnode = newfocus
		em.commit()

	def copyfocus(self):
		if not self.focusnode:
			gl.ringbell()
			return
		import Clipboard
		Clipboard.setclip('node', self.focusnode.DeepCopy())

	def create(self, where):
		if self.focusnode is None:
			fl.show_message('There is no focus to insert to','','')
			return
		parent = self.focusnode.GetParent()
		if parent is None and where <> 0:
			fl.show_message( \
			  'Can\'t insert before/after the root','','')
			return
		type = self.focusnode.GetType()
		if where == 0:
			children = self.focusnode.GetChildren()
			if children:
				type = children[0].GetType()
		node = self.root.context.newnode(type)
		self.insertnode(node, where)

	def paste(self, where):
		import Clipboard
		type, node = Clipboard.getclip()
		if type <> 'node' or node is None:
			fl.show_message( \
			  'The clipboard does not contain a node to paste', \
			  '', '')
			return
		if self.focusnode is None:
			fl.show_message('There is no focus to paste to','','')
			return
		if node.context is not self.root.context:
			node = node.CopyIntoContext(self.root.context)
		else:
			Clipboard.setclip(type, node.DeepCopy())
		self.insertnode(node, where)

	def insertnode(self, node, where):
		# 'where' is coded as follows: -1: before; 0: under; 1: after
		if where <> 0:
			parent = self.focusnode.GetParent()
			if parent is None:
				fl.show_message( \
				  'Can\'t insert before/after the root','','')
				node.Destroy()
				return
		em = self.editmgr
		if not em.transaction():
			node.Destroy()
			return
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

	def zoomout(self):
		if self.viewroot is self.root:
			gl.ringbell()
			return
		self.viewroot = self.viewroot.GetParent()
		self.recalc()
		self.draw()

	def zoomin(self):
		if self.viewroot is self.focusnode or not self.focusnode:
			gl.ringbell()
			return
		path = self.focusnode.GetPath()
		i = path.index(self.viewroot)
		self.viewroot = path[i+1]
		self.recalc()
		self.draw()

	#################################################
	# Internal subroutines                          #
	#################################################

	# Initialize the GL settings for the window
	def initwindow(self):
		# Use RGB mode
		gl.RGBmode()
		# Use double buffering if enough bitplanes available
		rbits = gl.getgdesc(GL.GD_BITS_NORM_DBL_RED)
		gbits = gl.getgdesc(GL.GD_BITS_NORM_DBL_GREEN)
		bbits = gl.getgdesc(GL.GD_BITS_NORM_DBL_BLUE)
##		if rbits + gbits + bbits >= 12:
##			gl.doublebuffer()
		gl.gconfig()
		# Clear the window right now (looks better)
		gl.RGBcolor(BGCOLOR)
		gl.clear()
		gl.swapbuffers()
		# Ask for events
		self.initevents()

	# Initialize the event settings for the window
	def initevents(self):
		# Called by initwindow() above to ask for these events
		fl.qdevice(DEVICE.LEFTMOUSE)
		fl.qdevice(DEVICE.MIDDLEMOUSE)
		fl.qdevice(DEVICE.RIGHTMOUSE)
		fl.qdevice(DEVICE.KEYBD)

	# Make sure the view root makes sense (after a tree update)
	def fixviewroot(self):
		if self.viewroot.GetRoot() <> self.root:
			self.viewroot = self.root
		self.fixfocus()

	# Make sure the focus is under the viewroot (called by fixviewroot)
	def fixfocus(self):
		if self.focusnode:
			if not self.viewroot.IsAncestorOf(self.focusnode):
				self.focusnode = None
		if not self.focusnode:
			self.focusnode = self.viewroot

	# Clear the list of objects
	def cleanup(self):
		for obj in self.objects:
			obj.cleanup()
		self.objects = []

	# Select the object at (x, y)
	def select(self, x, y):
		if self.focusobj:
			self.focusobj.deselect()
			self.focusobj = None
		self.focus = None
		for obj in self.objects:
			if obj.ishit(x, y):
				self.focusnode = obj.node
				self.focusobj = obj
		if not self.focusnode:
			self.focusnode = self.viewroot
			for obj in self.objects:
				if obj.node is self.focusnode:
					self.focusobj = obj
					break
		if self.focusobj:
			self.focusobj.select()
		if self.focusnode.IsAncestorOf(self.viewroot) \
			  and self.focusnode is not self.viewroot:
			self.viewroot = self.focusnode
			self.recalc()
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
		else:
			self.focusnode = None

	# Make a list of geometries for boxes
	def makegeometries(self):
		list = []
		left, top = 0, 0
		right, bottom = self.width, self.height
		path = self.viewroot.GetPath() # Ancestors of viewroot
		if bottom-top < len(path) * TITLEHEIGHT:
			# Truncate path, move viewroot up
			n = max(0, (bottom-top)/TITLEHEIGHT - 1)
			self.viewroot = path[n]
			path = path[:n+1]
		for node in path[:-1]:
			newtop = top + TITLEHEIGHT
			box = left + AMARGIN, top, right - AMARGIN, newtop
			list.append(node, ANCESTORBOX, box)
			top = newtop
		makeboxes(list, self.viewroot, left, top, right, bottom)
		return list

	# Draw the window, assuming the object shapes are all right
	def draw(self):
		gl.RGBcolor(BGCOLOR)
		gl.clear()
		for obj in self.objects:
			obj.draw()
		gl.swapbuffers()

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
		gl.ortho2(-MASK-0.5, width+MASK-0.5, \
			  height+MASK-0.5, -MASK-0.5)


# Recursive procedure to calculate geometry of boxes.
# This makes a box for the give node with the given dimensions,
# and if possible makes boxes for the children.
def makeboxes(list, node, left, top, right, bottom):
	box = left, top, right, bottom
	height = bottom-top
	t = node.GetType()
	n = len(node.GetChildren())
	if t in MMNode.leaftypes or n == 0 \
		  or right-left < MINWIDTH + 2*MARGIN \
		  or bottom-top < 2*TITLEHEIGHT + 2*MARGIN:
		list.append(node, LEAFBOX, box)
		return
	# Calculate space available for children
	top = top + TITLEHEIGHT + MARGIN
	left = left + MARGIN
	right = right - MARGIN
	bottom = bottom - MARGIN
	if t == 'par':
		avail = (right-left+MARGIN) / n - MARGIN
		if avail < MINWIDTH:
			list.append(node, LEAFBOX, box)
			return
		list.append(node, INNERBOX, box)
		for i in range(n):
			c = node.GetChild(i)
			makeboxes(list, c, left, top, left+avail, bottom)
			left = left+avail+MARGIN
			n = n-1
			if n > 0:
				avail = (right-left+MARGIN) / n - MARGIN
	else:
		avail = (bottom-top+MARGIN) / n - MARGIN
		if avail < TITLEHEIGHT:
			list.append(node, LEAFBOX, box)
			return
		list.append(node, INNERBOX, box)
		for i in range(n):
			c = node.GetChild(i)
			makeboxes(list, c, left, top, right, top+avail)
			top = top+avail+MARGIN
			n = n-1
			if n > 0:
				avail = (bottom-top+MARGIN) / n - MARGIN


# XXX The following should be merged with ChannelView's GO class :-(

# Make a menu, a list of menuprocs, and a keymap.
def makemenu(commandlist):
	menuprocs = []
	keymap = {}
	menu = makesubmenu(commandlist, menuprocs, keymap)
	return menu, menuprocs, keymap

# Make a (sub)menu (subroutine for makemenu)
def makesubmenu(commandlist, menuprocs, keymap):
	menu = gl.newpup()
	for char, text, proc in commandlist:
		if char: keymap[char] = proc
		else: char = '  '
		text = char + ' ' + text
		if proc is None:
			gl.addtopup(menu, text, 0)
		elif type(proc) == type([]):
			submenu = makesubmenu(proc, menuprocs, keymap)
			gl.addtopup(menu, text + '%m', submenu)
		else:
			gl.addtopup(menu, text + '%x' + `1+len(menuprocs)`, 0)
			menuprocs.append(proc)
	return menu

# Create a new object
def makeobject(mother, item):
	return Object().init(mother, item)

# (Graphical) object class
class Object:

	# Initialize an instance
	def init(self, mother, item):
		self.mother = mother
		self.node, self.boxtype, self.box = item
		self.name = MMAttrdefs.getattr(self.node, 'name')
		self.selected = 0
		self.ok = 1
		return self

	# Handle a right button mouse click in the object
	def popupmenu(self, x, y):
		i = gl.dopup(self.__class__.menu)
		if 0 < i <= len(self.__class__.menuprocs):
			self.__class__.menuprocs[i-1](self)

	# Handle a shortcut in the object
	def shortcut(self, c):
		if self.__class__.keymap.has_key(c):
			self.__class__.keymap[c](self)
		else:
			gl.ringbell()

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
		l, t, r, b = self.box
		nt = self.node.GetType()
		if nt in MMNode.leaftypes:
			gl.RGBcolor(LEAFCOLOR)
		elif nt == 'seq':
			gl.RGBcolor(SEQCOLOR)
		elif nt == 'par':
			gl.RGBcolor(PARCOLOR)
		elif nt == 'bag':
			gl.RGBcolor(BAGCOLOR)
		else:
			gl.RGBcolor(255, 0, 0) # Red -- error indicator
		gl.bgnpolygon()
		gl.v2i(l, t)
		gl.v2i(r, t)
		gl.v2i(r, b)
		gl.v2i(l, b)
		gl.endpolygon()
		self.drawfocus()
		# Draw the name, centered in the box
		if self.boxtype == INNERBOX or \
			  self.boxtype == LEAFBOX and \
			    self.node.GetType() in MMNode.interiortypes:
			b = min(b, t + TITLEHEIGHT + MARGIN)
		gl.RGBcolor(TEXTCOLOR)
		FontStuff.centerstring(l+3, t+3, r-3, b-3, self.name)

	def drawfocus(self):
		l, t, r, b = self.box
		l = l+1
		t = t+1
		r = r-1
		b = b-1
		# Draw a Motif style border
		# (True Motif would also require making the focus darker)
		# XXX Alas, it looks silly when you have a lot of nesting
		# XXX (-: like a Mexican Pyramid :-)
		cl = FOCUSLEFT
		ct = FOCUSTOP
		cr = FOCUSRIGHT
		cb = FOCUSBOTTOM
		if self.selected:
			cl, cr = cr, cl
			ct, cb = cb, ct
		l1 = l - 1
		t1 = t - 1
		r1 = r
		b1 = b
		ll = l + 2
		tt = t + 2
		rr = r - 2
		bb = b - 3
		gl.RGBcolor(cl)
		gl.bgnpolygon()
		gl.v2i(l1, t1)
		gl.v2i(ll, tt)
		gl.v2i(ll, bb)
		gl.v2i(l1, b1)
		gl.endpolygon()
		gl.RGBcolor(ct)
		gl.bgnpolygon()
		gl.v2i(l1, t1)
		gl.v2i(r1, t1)
		gl.v2i(rr, tt)
		gl.v2i(ll, tt)
		gl.endpolygon()
		gl.RGBcolor(cr)
		gl.bgnpolygon()
		gl.v2i(r1, t1)
		gl.v2i(r1, b1)
		gl.v2i(rr, bb)
		gl.v2i(rr, tt)
		gl.endpolygon()
		gl.RGBcolor(cb)
		gl.bgnpolygon()
		gl.v2i(l1, b1)
		gl.v2i(ll, bb)
		gl.v2i(rr, bb)
		gl.v2i(r1, b1)
		gl.endpolygon()
		return
		gl.RGBcolor(FOCUSBORDER)
		gl.linewidth(1)
		gl.bgnclosedline()
		gl.v2i(l1, t)
		gl.v2i(r, t)
		gl.v2i(r, b)
		gl.v2i(l1, b)
		gl.endclosedline()

	def olddrawfocus(self):
		l, t, r, b = self.box
		l = l+1
		t = t+1
		r = r-1
		b = b-1
		# Draw a "3D" border if selected, else an "engraved" outline
		if self.selected:
			l1 = l - 1
			t1 = t - 1
			r1 = r
			b1 = b
			ll = l + 3
			tt = t + 3
			rr = r - 3
			bb = b - 3
			gl.RGBcolor(FOCUSLEFT)
			gl.bgnpolygon()
			gl.v2i(l1, t1)
			gl.v2i(ll, tt)
			gl.v2i(ll, bb)
			gl.v2i(l1, b1)
			gl.endpolygon()
			gl.RGBcolor(FOCUSTOP)
			gl.bgnpolygon()
			gl.v2i(l1, t1)
			gl.v2i(r1, t1)
			gl.v2i(rr, tt)
			gl.v2i(ll, tt)
			gl.endpolygon()
			gl.RGBcolor(FOCUSRIGHT)
			gl.bgnpolygon()
			gl.v2i(r1, t1)
			gl.v2i(r1, b1)
			gl.v2i(rr, bb)
			gl.v2i(rr, tt)
			gl.endpolygon()
			gl.RGBcolor(FOCUSBOTTOM)
			gl.bgnpolygon()
			gl.v2i(l1, b1)
			gl.v2i(ll, bb)
			gl.v2i(rr, bb)
			gl.v2i(r1, b1)
			gl.endpolygon()
			gl.RGBcolor(FOCUSBORDER)
			gl.linewidth(1)
			gl.bgnclosedline()
			gl.v2i(l1, t)
			gl.v2i(r, t)
			gl.v2i(r, b)
			gl.v2i(l1, b)
			gl.endclosedline()
		else:
			# Outline the box in 'engraved' look
			gl.RGBcolor(BORDERCOLOR)
			gl.linewidth(1)
			gl.bgnclosedline()
			gl.v2i(l-1, t)
			gl.v2i(r, t)
			gl.v2i(r, b-1)
			gl.v2i(l-1, b-1)
			gl.endclosedline()
			gl.RGBcolor(BORDERLIGHT)
			gl.bgnclosedline()
			gl.v2i(l, t+1)
			gl.v2i(r+1, t+1)
			gl.v2i(r+1, b)
			gl.v2i(l, b)
			gl.endclosedline()

	# Menu handling functions

	def helpcall(self):
		import Help
		Help.givehelp('Hierarchy_view')

	def playcall(self):
		self.mother.toplevel.player.playsubtree(self.node)

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

	def focuscall(self):
		self.mother.toplevel.channelview.globalsetfocus(self.node)

	def zoomoutcall(self):
		self.mother.zoomout()

	def zoomincall(self):
		self.mother.zoomin()

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

	def pastebeforecall(self):
		self.mother.paste(-1)

	def pasteaftercall(self):
		self.mother.paste(1)

	def pasteundercall(self):
		self.mother.paste(0)

	# Menu and shortcut definitions are stored as data in the class,
	# since they are the same for all objects of a class...

	commandlist = [ \
		(None, 'Create', [ \
			(None, 'Before focus', createbeforecall), \
			(None, 'After focus', createaftercall), \
			(None, 'Under focus', createundercall), \
			]), \
		('d', 'Delete focus%l', deletecall), \
		('x', 'Cut focus', cutcall), \
		('c', 'Copy focus', copycall), \
		(None, 'Paste%l', [ \
			(None, 'Before focus', pastebeforecall), \
			(None, 'After focus', pasteaftercall), \
			(None, 'Under focus', pasteundercall), \
			]), \
		('f', 'Push focus', focuscall), \
		('p', 'Play node...', playcall), \
		('i', 'Node info...', infocall), \
		('a', 'Node attr...', attrcall), \
		('e', 'Edit contents...', editcall), \
		('t', 'Edit anchors...%l', anchorcall), \
		('Z', 'Zoom out', zoomoutcall), \
		('z', 'Zoom in%l', zoomincall), \
		('h', 'Help...', helpcall), \
		]
	# XXX navigation commands: up/down/prev/next
	menu, menuprocs, keymap = makemenu(commandlist)


