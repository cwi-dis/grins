# Channel view window.
# Beware: this module uses X11-like world coordinates:
# positive Y coordinates point down from the top of the window.
# Also the convention for box coordinates is (left, top, right, bottom)

# XXX To do:
# - remember 'locked' over commit
# - remember sync arc focus over commit
# - what about group nodes?  (I'd say draw a box to display them?)
# - store focus and locked node as attributes
# - improve arm colors
# - accept middle button as shortcut for lock/unlock?


from math import sin, cos, atan2, pi, ceil, floor
import windowinterface, EVENTS, StringStuff
from ViewDialog import ViewDialog

from MMNode import alltypes, leaftypes, interiortypes
import MMAttrdefs
import Timing
from MMExc import *
from AnchorDefs import *
from ArmStates import *


def fix(r, g, b): return r, g, b	# Hook for color conversions


# Color assignments (RGB)

BGCOLOR = fix(200, 200, 200)		# Light gray
BORDERCOLOR = fix(75, 75, 75)		# Dark gray
BORDERLIGHT = fix(255, 255, 255)	# White
CHANNELCOLOR = fix(240, 240, 240)	# Very light gray
CHANNELOFFCOLOR = fix(160, 160, 160)	# Darker gray
NODECOLOR = fix(208, 182, 160)		# Pale pinkish, match hierarchy view
ALTNODECOLOR = fix(255, 224, 200)	# Same but brighter
ARROWCOLOR = fix(0, 0, 255)		# Blue
TEXTCOLOR = fix(0, 0, 0)		# Black
FOCUSCOLOR = fix(255, 0, 0)		# Red (for sync arcs only now)
LOCKEDCOLOR = fix(200, 255, 0)		# Yellowish green
ANCHORCOLOR = fix(255, 127, 0)		# Orange/pinkish

# Focus color assignments (from light to dark gray)

FOCUSBORDER = fix(0, 0, 0)
FOCUSLEFT   = fix(244, 244, 244)
FOCUSTOP    = fix(204, 204, 204)
FOCUSRIGHT  = fix(40, 40, 40)
FOCUSBOTTOM = fix(91, 91, 91)

# Arm colors
armcolors = { \
	     ARM_SCHEDULED: (200, 200, 0), \
	     ARM_ARMING: (255, 255, 0), \
	     ARM_ARMED: (255, 200, 0), \
	     ARM_PLAYING: (0, 255, 0), \
	     ARM_WAITSTOP: (0, 127, 0), \
	     }


# Arrowhead dimensions

ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

# Font we use
f_title = windowinterface.findfont('Helvetica', 10)

# Types of things we can do in the (modal) channel-pointing mode
PLACING_NEW = 1
PLACING_COPY = 2
PLACING_MOVE = 3


# Channel view class

class ChannelView(ViewDialog):

	# Initialization.
	# (Actually, most things are initialized by show().)

	def init(self, toplevel):
		self.window = None
		self.displist = self.new_displist = None
		self.waiting = 0
		self.last_geometry = None
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.viewroot = None
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		self.focus = None
		self.future_focus = None
		self.showall = 0
		self.placing_channel = 0
		title = 'Channel View (' + self.toplevel.basename + ')'
		self = ViewDialog.init(self, 'cview_')
		return self

	def __repr__(self):
		return '<ChannelView instance, root=' + `self.root` + '>'

	# Dialog interface

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Channel View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1)
		if self.waiting:
			self.window.setcursor('watch')
		self.window.register(EVENTS.Mouse0Press, self.mouse, None)
		self.window.register(EVENTS.ResizeWindow, self.redraw, None)
		self.window.register(EVENTS.WindowExit, self.hide, None)
		self.window.bgcolor(BGCOLOR)
		# Other administratrivia
		self.editmgr.register(self)
		self.toplevel.checkviews()
		# Compute objects to draw and where to draw them, then draw
		self.fixviewroot()
		focus = self.focus
		if not focus: focus = ('b', None)
		self.recalc(focus)
		self.reshape()
		self.draw()
		if self.focus:
			obj = self.focus
		else:
			obj = self.baseobject
		self.window.create_menu(obj.menutitle, obj.commandlist)

	def hide(self, *rest):
		if not self.is_showing():
			return
		self.toplevel.showstate(self, 0)
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = self.new_displist = None
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

	# Edit manager interface (as dependent client)

	def transaction(self):
		return 1 # It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		if self.future_focus <> None:
			focus = self.future_focus
			self.future_focus = None
		elif self.focus is None:
			focus = '', None
		elif type(self.focus) == type(()):
			focus = self.focus
		elif self.focus.__class__ == ChannelBox:
			focus = 'c', self.focus.channel
		elif self.focus.__class__ == NodeBox:
			focus = 'n', self.focus.node
		elif self.focus.__class__ == ArcBox:
			focus = 'a', None
		else:
			focus = '', None
		self.cleanup()
		if self.is_showing():
			self.fixviewroot()
			self.recalc(focus)
			self.reshape()
			self.draw()

	def kill(self):
		self.destroy()

	# Event interface (override glwindow methods)

	def redraw(self, *rest):
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		bl, fh, ps = self.new_displist.usefont(f_title)
		# RESIZE event.
		self.reshape()
		self.draw()

	def channels_changed(self):
		# Called when a channel is switched on or off from the
		# player (this bypasses the edit manager so it can be
		# done even when the document is playing).
		if self.is_showing():
			self.redraw()

	def mouse(self, dummy, window, event, params):
		x, y = params[0:2]
		if self.placing_channel:
			self.finish_channel(x, y)
		else:
			self.select(x, y)

	# Time-related subroutines

	def timerange(self):
		# Return the range of times used in the window
		v = self.viewroot
		t0, t1 = v.t0, v.t1
		return t0, max(t1, t0 + 10)

	def maptimes(self, t0, t1):
		# Map begin and end times to top and bottom in window

		# Calculate our position in relative time
		top = self.nodetop
		height = 1.0 - top - self.new_displist.fontheight()
		vt0, vt1 = self.timerange()
		dt = vt1 - vt0

		# Compute the 'ideal' top/bottom
		return top + (height * (t0 - vt0) / dt), \
		       top + (height * (t1 - vt0) / dt)

	def mapchannel(self, channel):
		# Map channel to left and right coordinates
		list = self.visiblechannels()
		nchannels = len(list)
		try:
			i = list.index(channel)
		except ValueError:
			return 0, 0
		width = float(self.timescaleborder) / nchannels
		return (i + 0.1) * width, (i + 0.9) * width

	def channelgapindex(self, x):
		list = self.visiblechannels()
		nchannels = len(list)
		if nchannels == 0:
		    return 0
		width = float(self.timescaleborder) / nchannels
		rv = int((x+width/2)/width)
		if rv < 0:
		    rv = 0
		elif rv > nchannels:
		    rv = nchannels
		return rv

	# Clear the list of objects we know

	def cleanup(self):
		self.focus = self.lockednode = None
		for obj in self.objects:
			obj.cleanup()
		self.objects = []
		self.arcs = []
		self.baseobject = None
		self.timescaleobject = None

	# Toggle 'showall' setting

	def toggleshow(self):
		windowinterface.setcursor('watch')
		self.showall = (not self.showall)
		self.redraw()
		windowinterface.setcursor('')

	# Return list of currently visible channels

	def visiblechannels(self):
		if self.showall:
			return self.context.channels
		else:
			return self.usedchannels

	# Recalculate the set of objects we should be drawing

	def recalc(self, focus):
		displist = self.window.newdisplaylist(BGCOLOR)
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = displist
		bl, fh, ps = displist.usefont(f_title)
		self.channelbottom = 4 * fh
		self.nodetop = 6 * fh
		self.timescaleborder = 1.0 - displist.strsize('999999')[0]

		self.objects = []
		self.focus = self.lockednode = None
		self.baseobject = GO(self, '(base)')
		self.baseobject.select()
		self.objects.append(self.baseobject)
		self.timescaleobject = TimeScaleBox(self)
		self.objects.append(self.timescaleobject)
		self.initchannels(focus)
		self.initnodes(focus)
		self.initarcs(focus)

	# Recompute the locations where the objects should be drawn

	def reshape(self):
	        self.discontinuities = []
		Timing.needtimes(self.viewroot)
		for c in self.context.channels:
			c.lowest = 0
		for obj in self.objects:
			obj.reshape()

	# Draw the window

	def draw(self):
		for obj in self.objects:
			obj.draw()
		self.render()

	def drawarcs(self):
		if self.is_showing():
			for obj in self.arcs:
				obj.draw()
	
	# Channel stuff

	def initchannels(self, focus):
		for c in self.context.channels:
			obj = ChannelBox(self, c)
			self.objects.append(obj)
			if focus[0] == 'c' and focus[1] is c:
				obj.select()

	# View root stuff

	def nextviewroot(self):
		windowinterface.setcursor('watch')
		for c in self.viewroot.GetChildren():
			node = c.FirstMiniDocument()
			if node: break
		else:
			node = self.viewroot.NextMiniDocument()
			if node is None:
				node = self.root.FirstMiniDocument()
		self.setviewroot(node)
		windowinterface.setcursor('')

	def prevviewroot(self):
		windowinterface.setcursor('watch')
		children = self.viewroot.GetChildren()[:]
		children.reverse()
		for c in children:
			node = c.LastMiniDocument()
			if node: break
		else:
			node = self.viewroot.PrevMiniDocument()
			if node is None:
				node = self.root.LastMiniDocument()
		self.setviewroot(node)
		windowinterface.setcursor('')

	# Make sure the view root is set to *something*, and fix the title
	def fixviewroot(self):
		node = self.viewroot
		if node <> None and node.GetRoot() <> self.root:
			node = None
		if node <> None and not node.IsMiniDocument():
			node = None
		if node == None:
			node = self.root.FirstMiniDocument()
		if node == None:
			node = self.root
		self.viewroot = node
		self.fixtitle()

	# Change the view root
	def setviewroot(self, node):
		if node == None or node == self.viewroot:
			return
		self.cleanup()
		self.viewroot = node
		self.recalc(('b', None))
		self.reshape()
		self.fixtitle()
		self.draw()

	def fixtitle(self):
		title = 'Channel View (' + self.toplevel.basename + ')'
		if None <> self.viewroot <> self.root:
			name = MMAttrdefs.getattr(self.viewroot, 'name')
			title = title + ': ' + name
		if self.is_showing():
			self.window.settitle(title)

	# Node stuff

	def initnodes(self, focus):
		Timing.needtimes(self.viewroot)
		for c in self.context.channels: c.used = 0
		self.baseobject.descendants[:] = []
		self.scantree(self.viewroot, focus)
		self.usedchannels = []
		for c in self.context.channels:
			if c.used: self.usedchannels.append(c)
		self.addancestors()
		self.addsiblings()

	def scantree(self, node, focus):
		t = node.GetType()
		if t in leaftypes:
			channel = node.GetChannel()
			if channel:
				channel.used = 1
				obj = NodeBox(self, node)
				self.objects.append(obj)
				if focus[0] == 'n' and focus[1] is node:
					obj.select()
		elif t == 'bag':
			self.scandescendants(node)
		else:
			for c in node.GetChildren():
				self.scantree(c, focus)

	def scandescendants(self, node):
		for c in node.GetChildren():
			if c.IsMiniDocument():
				name = c.GetRawAttrDef('name', '(NoName)')
				tuple = ('', name, (self.setviewroot, (c,)))
				self.baseobject.descendants.append(tuple)
			elif c.GetType() == 'bag':
				self.scandescendants(c)
			elif c.GetType() in interiortypes:
				self.scandescendants(c)

	def addancestors(self):
		self.baseobject.ancestors[:] = []
		path = self.viewroot.GetPath()
		for node in path[:-1]:
			if node.IsMiniDocument():
				name = node.GetRawAttrDef('name', '(NoName)')
				tuple = ('', name, (self.setviewroot, (node,)))
				self.baseobject.ancestors.append(tuple)

	def addsiblings(self):
		self.baseobject.siblings[:] = []
		parent = self.viewroot.GetParent()
		if parent:
			while parent.parent and \
				  parent.parent.GetType() == 'bag':
				parent = parent.parent
			self.scansiblings(parent)

	def scansiblings(self, node):
		for c in node.GetChildren():
			if c.IsMiniDocument():
				name = c.GetRawAttrDef('name', '(NoName)')
				if c is self.viewroot:
					name = name + ' (current)'
				tuple = ('', name, (self.setviewroot, (c,)))
				self.baseobject.siblings.append(tuple)
			elif c.GetType() == 'bag':
				self.scansiblings(c)

	# Arc stuff

	def initarcs(self, focus):
		arcs = []
		self.scanarcs(self.viewroot, focus, arcs)
		self.objects[len(self.objects):] = self.arcs = arcs
	
	def scanarcs(self, node, focus, arcs):
		if node.GetType() in leaftypes and node.GetChannel():
			self.addarcs(node, arcs)
		else:
			for c in node.GetChildren():
				self.scanarcs(c, focus, arcs)

	def addarcs(self, ynode, arcs):
		for arc in MMAttrdefs.getattr(ynode, 'synctolist'):
			xuid, xside, delay, yside = arc
			try:
				xnode = ynode.MapUID(xuid)
			except NoSuchUIDError:
				# Skip sync arc from non-existing node
				continue
			if self.viewroot.IsAncestorOf(xnode) and \
			   xnode.GetType() in leaftypes and \
			   xnode.GetChannel():
				obj = ArcBox(self,
					     xnode, xside, delay, ynode, yside)
				arcs.append(obj)

	# Focus stuff (see also recalc)

	def deselect(self):
		if self.focus and type(self.focus) != type(()):
			self.focus.deselect()
		else:
			self.focus = None

	def select(self, x, y):
		self.init_display()
		self.deselect()
		hits = []
		for obj in self.objects:
			if obj.ishit(x, y):
				hits.append(obj)
		if hits:
			obj = hits[-1]	# Last object (the one drawn on top)
			if self.lockednode:
			    if obj.is_node_object:
				obj.finishlink()
				return
			    else:
				windowinterface.beep()
				self.lockednode.unlock()
			obj.select()
			self.drawarcs()
		self.render()
		if self.focus:
			obj = self.focus
		else:
			obj = self.baseobject
		self.window.create_menu(obj.menutitle, obj.commandlist)

	# Global focus stuff

	def getfocus(self):
		if self.focus and type(self.focus) != type(()):
			return self.focus.getnode()
		else:
			return None

	def globalsetfocus(self, node):
		# May have to switch view root
		mini = node
		while not mini.IsMiniDocument():
			mini = mini.GetParent()
			if mini == None:
				return
		if not self.is_showing():
			self.viewroot = mini
			self.focus = ('n', node)
			return
		self.setviewroot(mini) # No-op if already there
		self.init_display()
		if hasattr(node, 'cv_obj'):
			obj = node.cv_obj
			self.deselect()
			obj.select()
			self.drawarcs()
		self.render()

	# Create a new channel
	# XXXX Index is obsolete!
	def newchannel(self, index):
		if self.visiblechannels() <> self.context.channels:
			windowinterface.showmessage(
				  "You can't create a new channel\n" +
				  "unless you are showing unused channels\n" +
				  "(use shortcut 'T')")
			return
	        if self.placing_channel:
		        windowinterface.showmessage(
				'Please place the other channel first!',)
			return
		#
		# Slightly hacky code: we try to check here whether
		# the transaction is possible, but we don't do it till later.
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		editmgr.rollback()
		from ChannelMap import commonchanneltypes, otherchanneltypes
		prompt = 'Select channel type, then place channel:'
		list = commonchanneltypes[:]
		list.append('Other...')
		list.append('Cancel')
		olist = otherchanneltypes[:]
		olist.append('Other...')
		olist.append('Cancel')
		while 1:
			default = len(list)-1
			i = windowinterface.multchoice(prompt, list, default)
			if i+1 >= len(list):
				return		# User doesn't want to choose
			elif list[i] == 'Other...':
				list, olist = olist, list
				continue
			type = list[i]
			break
		windowinterface.setcursor('channel')
		self.placing_channel = PLACING_NEW
		self.placing_type = type

	def copychannel(self, name):
		if self.visiblechannels() <> self.context.channels:
			windowinterface.showmessage(
				  'You can\'t create a new channel\n' +
				  'unless you are showing unused channels\n' +
				  '(use shortcut \'T\')')
			return
	        if self.placing_channel:
		        windowinterface.showmessage(
				'Please place the other channel first!')
			return
		#
		# Slightly hacky code: we try to check here whether
		# the transaction is possible, but we don't do it till later.
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		editmgr.rollback()
		windowinterface.setcursor('channel')
		self.placing_channel = PLACING_COPY
		self.placing_orig = name

	def movechannel(self, name):
		if self.visiblechannels() <> self.context.channels:
			windowinterface.showmessage(
				  'You can\'t move a channel\n' +
				  'unless you are showing unused channels\n' +
				  '(use shortcut \'T\')')
			return
	        if self.placing_channel:
		        windowinterface.showmessage(
				'Please place the other channel first!')
			return
		#
		# Slightly hacky code: we try to check here whether
		# the transaction is possible, but we don't do it till later.
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		editmgr.rollback()
		windowinterface.setcursor('channel')
		self.placing_channel = PLACING_MOVE
		self.placing_orig = name

	def finish_channel(self, x, y):
	        placement_type = self.placing_channel
	        self.placing_channel = 0
		index = self.channelgapindex(x)
	        windowinterface.setcursor('')
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		    
		i = 1
		context = self.context
		if placement_type in (PLACING_NEW, PLACING_COPY):
		    base = 'NEW'
		    name = base + `i`
		    while context.channeldict.has_key(name):
			i = i+1
			name = base + `i`
		else:
		    name = self.placing_orig

		if placement_type == PLACING_NEW:
		    editmgr.addchannel(name, index, self.placing_type)
		elif placement_type == PLACING_COPY:
		    editmgr.copychannel(name, index, self.placing_orig)
		else:
		    c = context.channeldict[name]
		    editmgr.movechannel(name, index)
		    index = context.channels.index(c)
		channel = context.channels[index]
		self.future_focus = 'c', channel
		self.showall = 1	# Force showing the new channel
		self.cleanup()
		editmgr.commit()
		if placement_type in (PLACING_NEW, PLACING_COPY):
			import AttrEdit
			AttrEdit.showchannelattreditor(channel)

	# Window stuff

	def init_display(self):
		if self.new_displist:
			print 'init_display: new_displist already exists'
		self.new_displist = self.displist.clone()

	def render(self):
		self.new_displist.render()
		if self.displist:
			self.displist.close()
		self.displist = self.new_displist
		self.new_displist = None


# Base class for Graphical Objects.
# These live in close symbiosis with their "mother", the ChannelView!
# Note: reshape() must be called before draw() or ishit() can be called.

class GO:

	def __init__(self, mother, name):
		self.mother = mother
		self.name = name
		self.selected = 0
		self.ok = 0
		self.is_node_object = 0

		# Submenus listing related mini-documents

		self.ancestors = []
		self.descendants = []
		self.siblings = []

		# Menu and shortcut definitions are stored as data in
		# the class

		self.commandlist = c = []
##		c.append('h', 'Help...', (self.helpcall, ()))
		c.append('n', 'New channel...',  (self.newchannelcall, ()))
		c.append('N', 'Next mini-document', (self.nextminicall, ()))
		c.append('P', 'Previous mini-document', (self.prevminicall, ()))
		c.append('',  'Ancestors', self.ancestors)
		c.append('', 'Siblings', self.siblings)
		c.append('', 'Descendants', self.descendants)
		c.append('T', 'Toggle unused channels', (self.toggleshowcall, ()))
		self.menutitle = 'Base ops'

	def __repr__(self):
		return '<GO instance, name=' + `self.name` + '>'

	def getnode(self):
		# Called by mother's getfocusnode()
		# Overridden by NodeBox
		return None

	def cleanup(self):
		# Called just before forgetting the object
		self.commandlist = []
		self.mother = None

	def reshape(self):
		# Recompute the size and location
		self.ok = 1

	def draw(self):
		# Draw everything, if ok
		if not self.ok: return
		self.drawfocus()

	def drawfocus(self):
		# Draw the part that changes when the focus changes
		visible = len(self.mother.visiblechannels())
		total = len(self.mother.context.channels)
		if visible == total: return
		str = '%d more' % (total-visible)
		d = self.mother.new_displist
		d.fgcolor(TEXTCOLOR)
		StringStuff.centerstring(d, self.mother.timescaleborder, 0,
					 1.0, self.mother.channelbottom, str)

	def select(self):
		# Make this object the focus
		if self.selected:
			return
		self.mother.deselect()
		self.selected = 1
		self.mother.focus = self
		self.mother.window.create_menu(self.menutitle, self.commandlist)
		if self.ok:
			self.drawfocus()

	def deselect(self):
		# Remove this object from the focus
		if not self.selected:
			return
		self.selected = 0
		mother = self.mother
		mother.focus = None
		if self.ok:
			baseobject = mother.baseobject
			mother.window.create_menu(baseobject.menutitle,
						  baseobject.commandlist)
			self.drawfocus()

	def ishit(self, x, y):
		# Check whether the given mouse coordinates are in this object
		return 0

	# Methods corresponding to the menu entries

	def helpcall(self):
		import Help
		Help.givehelp('Channel_view')

	def newchannelcall(self):
		self.mother.newchannel(self.newchannelindex())

	def nextminicall(self):
		self.mother.nextviewroot()

	def prevminicall(self):
		self.mother.prevviewroot()

	def toggleshowcall(self):
		self.mother.toggleshow()

	def newchannelindex(self):
		# NB Overridden by ChannelBox to insert before current!
		return len(self.mother.context.channelnames)


# Class for the time scale object

class TimeScaleBox(GO):

	def __init__(self, mother):
		GO.__init__(self, mother, 'timescale')

	def __repr__(self):
		return '<TimeScaleBox instance>'

	def reshape(self):
		self.left = self.mother.timescaleborder + \
			  self.mother.new_displist.strsize(' ')[0]
		self.right = 1.0
		t0, t1 = self.mother.timerange()
		self.top, self.bottom = self.mother.maptimes(t0, t1)
		self.ok = 1

	def drawfocus(self):
		l, t, r, b = self.left, self.top, self.right, self.bottom
		height = b-t
		if height <= 0:
			return
		d = self.mother.new_displist
		f_fontheight = d.fontheight()
		d.fgcolor(BORDERCOLOR)
		# Draw rectangle around boxes
		hmargin = d.strsize('x')[0] / 4
		vmargin = d.fontheight() / 9
		l = l + hmargin
		t = t + vmargin
		r = (4*l+r)/5
		b = b - vmargin
		d.drawbox(l, t, r - l, b - t)
		# Compute number of division boxes
		t0, t1 = self.mother.timerange()
		dt = t1 - t0
		n = int(ceil(dt/10.0))
		# Compute distance between numeric indicators
		div = 1
		i = 0
		while (n/div) * 1.5 * f_fontheight >= height:
			if i%3 == 0:
				div = div*2
			elif i%3 == 1:
				div = div/2*5
			else:
				div = div/5*10
			i = i+1
		# Draw division boxes and numeric indicators
		# This gives MemoryError: for i in range(n):
		# This code should be looked into.
		i = -1
		d.fgcolor(TEXTCOLOR)
		while i < n:
			i = i + 1
			#
			it0 = t0 + i*10
			it1 = it0 + 5
			t, b = self.mother.maptimes(it0, it1)
			t = max(t, self.top)
			b = min(b, self.bottom)
			if b <= t:
				continue
			d.drawfbox(BORDERCOLOR, l, t, r - l, b - t)
			if i%div <> 0:
				continue
			StringStuff.centerstring(d,
				  r, t-f_fontheight/2,
				  self.right, t+f_fontheight/2,
				  `i*10`)
		for i in self.mother.discontinuities:
		        t, b = self.mother.maptimes(i, i)
			d.drawline(ANCHORCOLOR, [(l, t), (r, t)])
			


# Class for Channel Objects

class ChannelBox(GO):

	def __init__(self, mother, channel):
		GO.__init__(self, mother, channel.name)
		self.channel = channel
		if channel.has_key('type'):
			self.ctype = channel['type']
		else:
			self.ctype = '???'
		c = self.commandlist
		c.append(None)
		c.append('i', '', (self.attrcall, ()))
		c.append('a', 'Channel attr...', (self.attrcall, ()))
		c.append('d', 'Delete channel',  (self.delcall, ()))
		c.append('m', 'Move channel', (self.movecall, ()))
		c.append('c', 'Copy channel', (self.copycall, ()))
		c.append(None)
		c.append('', 'Toggle on/off', (self.channel_onoff, ()))
		c.append(None)
		c.append('', 'Highlight window', (self.highlight, ()))
		c.append('', 'Unhighlight window', (self.unhighlight, ()))
		self.menutitle = 'Channel ' + self.name + ' ops'

	def __repr__(self):
		return '<ChannelBox instance, name=' + `self.name` + '>'

	def channel_onoff(self):
		player = self.mother.toplevel.player
		ch = self.channel
		if player.is_showing():
			player.cmenu_callback(ch.name)
			return
		if ch.attrdict.has_key('visible'):
			isvis = ch.attrdict['visible']
		else:
			isvis = 1
		ch.attrdict['visible'] = not isvis
		self.mother.channels_changed()

	def reshape(self):
		left, right = self.mother.mapchannel(self.channel)
		if left == right:
			self.ok = 0
			return
		self.left = left
		self.right = right
		self.top = 0
		self.bottom = self.mother.channelbottom
		self.xcenter = (self.left + self.right) / 2
		self.ycenter = (self.top + self.bottom) / 2
		self.farbottom = 1.0
		self.ok = 1

	def ishit(self, x, y):
		if not self.ok: return 0
		return self.left <= x <= self.right and \
		       self.top <= y <= self.bottom

	def draw(self):
		if not self.ok: return
		self.drawline()
		self.drawfocus()

	def drawfocus(self):

		l = self.left
		t = self.top
		r = self.right
		b = self.bottom
		x = self.xcenter
		y = self.ycenter

		d = self.mother.new_displist

		# Draw a diamond
		cd = self.mother.context.channeldict[self.name]
		if cd.has_key('visible'):
			visible = cd['visible']
		else:
			visible = 1
		if visible:
			color = CHANNELCOLOR
		else:
			color = CHANNELOFFCOLOR
		d.drawfdiamond(color, l, t, r - l, b - t)

		# Outline the diamond; 'engraved' normally,
		# 'sticking out' if selected
		if self.selected:
			d.draw3ddiamond(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT,
					FOCUSBOTTOM, l, t, r - l, b - t)
		d.fgcolor(BORDERCOLOR)
		d.drawdiamond(l, t, r - l, b - t)

		# Draw the name
		d.fgcolor(TEXTCOLOR)
		StringStuff.centerstring(d, l, t, r, b, self.name)

		# Draw the channel type
		ctype = '(' + self.ctype + ')'
		StringStuff.centerstring(d, l, b, r, b + d.fontheight(), ctype)

	def drawline(self):
		# Draw a gray and a white vertical line
		d = self.mother.new_displist
		d.fgcolor(BORDERCOLOR)
		d.drawline(BORDERCOLOR, [(self.xcenter, self.bottom),
					 (self.xcenter, self.farbottom)])

	# Menu stuff beyond what GO offers

	def attrcall(self):
		import AttrEdit
		AttrEdit.showchannelattreditor(self.channel)

	def delcall(self):
		if self.channel in self.mother.usedchannels:
			windowinterface.showmessage(
				  "You can't delete a channel\n" +
				  'that is still in use')
			return
		editmgr = self.mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.delchannel(self.name)
		self.mother.cleanup()
		editmgr.commit()

	def movecall(self):
	        self.mother.movechannel(self.name)

	def copycall(self):
	        self.mother.copychannel(self.name)

	def newchannelindex(self):
		# Hook for newchannelcall to determine placement
		return self.mother.context.channelnames.index(self.name)

	def highlight(self):
		channels = self.mother.toplevel.player.channels
		if channels.has_key(self.name):
			channels[self.name].highlight()

	def unhighlight(self):
		channels = self.mother.toplevel.player.channels
		if channels.has_key(self.name):
			channels[self.name].unhighlight()



class NodeBox(GO):

	def __repr__(self):
		return '<NodeBox instance, name=' + `self.name` + '>'

	def __init__(self, mother, node):
		self.node = node
		self.pausenode = (MMAttrdefs.getattr(node, 'duration') < 0)
		self.hasanchors = self.haspause = 0
		try:
			alist = self.node.GetRawAttr('anchorlist')
			modanchorlist(alist)
		except NoSuchAttrError:
			alist = None
		if alist: # Not None and not []
			self.hasanchors = 1
			for a in alist:
				if a[A_TYPE] in (ATYPE_PAUSE, ATYPE_ARGS):
					self.haspause = 1
					break
		node.cv_obj = self
		node.set_armedmode = self.set_armedmode
		if node.armedmode == None:
			node.armedmode = ARM_NONE
		name = MMAttrdefs.getattr(node, 'name')
		self.locked = 0
		GO.__init__(self, mother, name)
		self.is_node_object = 1
		c = self.commandlist
		c.append(None)
		c.append('p', 'Play node...', (self.playcall, ()))
		c.append('G', 'Play from here...', (self.playfromcall, ()))
		c.append('f', 'Push focus', (self.focuscall, ()))
		c.append(None)
		c.append('s', 'Finish sync arc...', (self.newsyncarccall, ()))
		c.append('L', 'Finish hyperlink...', (self.hyperlinkcall, ()))
		c.append(None)
		c.append('i', 'Node info...', (self.infocall, ()))
		c.append('a', 'Node attr...', (self.attrcall, ()))
		c.append('e', 'Edit contents...', (self.editcall, ()))
		c.append('t', 'Edit anchors...', (self.anchorcall, ()))
		self.menutitle = 'Node ' + self.name + ' ops'


	def getnode(self):
		return self.node

	def cleanup(self):
		del self.node.cv_obj
		# This makes the inherited set_armedmode from the class
		# visible again:
		del self.node.set_armedmode
		GO.cleanup(self)

	def set_armedmode(self, mode):
		# print 'node', self.name, 'setarmedmode', mode
		if mode <> self.node.armedmode:
			self.mother.init_display()
			self.node.armedmode = mode
			self.drawfocus()
			self.mother.drawarcs()
			self.mother.render()

	def lock(self):
		if not self.locked:
			self.deselect()
			if self.mother.lockednode:
				self.mother.lockednode.unlock()
			self.locked = 1
			self.mother.lockednode = self
			self.mother.window.setcursor('link')
			self.drawfocus()

	def unlock(self):
		if self.locked:
		        self.mother.window.setcursor('')
			self.locked = 0
			self.mother.lockednode = None
			self.drawfocus()

	def finishlink(self):
		if not self.mother.lockednode:
			windowinterface.beep()
			return
		self.mother.window.setcursor('')
		editmgr = self.mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		root = self.mother.root
		snode, sside, delay, dnode, dsize = \
			self.mother.lockednode.node, 1, 0.0, self.node, 0
		editmgr.addsyncarc(snode, sside, delay, dnode, dsize)
		self.mother.cleanup()
		editmgr.commit()
		# NB: when we get here, this object is nearly dead already!
		import ArcInfo
		ArcInfo.showarcinfo(root, snode, sside, delay, dnode, dsize)

	def select(self):
		self.unlock()
		GO.select(self)

	def reshape(self):
		# Compute ideal box coordinates
		channel = self.node.GetChannel()
		left, right = self.mother.mapchannel(channel)
		top, bottom = self.mother.maptimes(self.node.t0, self.node.t1)
		if self.node.timing_discont:
		    self.mother.discontinuities.append(
			self.node.t0+self.node.timing_discont)

		vmargin = self.mother.new_displist.fontheight() / 15
		top = top + vmargin
		bottom = bottom - vmargin

		# Move top down below the previous node if necessary
		if top < channel.lowest:
			top = channel.lowest

		# Keep space for at least one line of text
		# bottom = max(bottom, top+f_fontheight-2)
		if top + self.mother.new_displist.fontheight() * 1.2 > bottom:
		    bottom = top + self.mother.new_displist.fontheight() * 1.2
		    self.mother.discontinuities.append(
			(self.node.t0+self.node.t1)/2)

		# Update channel's lowest node
		channel.lowest = bottom

		self.left, self.top, self.right, self.bottom = \
			left, top, right, bottom
		self.ok = 1

	def ishit(self, x, y):
		if not self.ok: return 0
		return self.left <= x <= self.right and \
		       self.top <= y <= self.bottom

	def drawfocus(self):
		l, t, r, b = self.left, self.top, self.right, self.bottom

		d = self.mother.new_displist
		w, h = d.strsize('m')
		haboxsize = w / 2
		vaboxsize = h / 3

		# Draw a box
		if self.locked:
			color = LOCKEDCOLOR
		elif armcolors.has_key(self.node.armedmode):
			color = armcolors[self.node.armedmode]
		else:
			color = NODECOLOR
		d.drawfbox(color, l, t, r - l, b - t)

		# If the end time was inherited, make the bottom-right
		# triangle of the box a lighter color
		if self.node.t0t1_inherited:
			d.drawfpolygon(ALTNODECOLOR, [(r, t), (r, b), (l, b)])

		# If there are anchors on this node,
		# draw a small orange box in the bottom left corner
		if self.hasanchors:
			d.drawfbox(ANCHORCOLOR, l, b-vaboxsize,
				   haboxsize, vaboxsize)

		# If there is a pausing anchor,
		# draw an orange line at the bottom
		if self.haspause:
			d.drawfbox(ANCHORCOLOR, l, b-vaboxsize,
				   r - l, vaboxsize)

		# If this is a pausing node
		# draw a small orange box in the bottom right corner
		if self.pausenode:
			d.drawfbox(ANCHORCOLOR, r-haboxsize, b-vaboxsize,
				   haboxsize, vaboxsize)

		# Draw a "3D" border if selected, else an "engraved" outline
		if self.selected:
			d.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT,
				    FOCUSBOTTOM, l, t, r - l, b - t)
		else:
			d.fgcolor(BORDERCOLOR)
			d.drawbox(l, t, r - l, b - t)

		# Draw the name, centered in the box
		d.fgcolor(TEXTCOLOR)
		StringStuff.centerstring(d, l, t, r, b, self.name)

	# Menu stuff beyond what GO offers

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

	def newsyncarccall(self):
		self.mother.init_display()
		self.lock()
		self.mother.render()

	def focuscall(self):
		self.mother.toplevel.hierarchyview.globalsetfocus(self.node)

	def hyperlinkcall(self):
		self.mother.toplevel.links.finish_link(self.node)


class ArcBox(GO):

	def __repr__(self):
		return '<ArcBox instance, name=' + `self.name` + '>'

	def __init__(self, mother, snode, sside, delay, dnode, dside):
		self.snode, self.sside, self.delay, self.dnode, self.dside = \
			snode, sside, delay, dnode, dside
		GO.__init__(self, mother, 'arc')
		c = self.commandlist
		c.append(None)
		c.append('i', 'Sync arc info...', (self.infocall, ()))
		c.append('d', 'Delete sync arc',  (self.delcall, ()))
		self.menutitle = 'Sync arc ' + self.name + ' ops'


	def reshape(self):
		try:
			sobj = self.snode.cv_obj
			dobj = self.dnode.cv_obj
		except AttributeError:
			self.ok = 0
			return
		if self.sside: self.sy = sobj.bottom
		else: self.sy = sobj.top
		if self.dside: self.dy = dobj.bottom
		else: self.dy = dobj.top
		self.sx = (sobj.left + sobj.right) / 2
		self.dx = (dobj.left + dobj.right) / 2
		#
		lx = self.dx - self.sx
		ly = self.dy - self.sy
		if lx == 0.0 == ly: angle = 0.0
		else: angle = atan2(lx, ly)
		# print 'lx =', lx, 'ly =', ly, 'angle =', angle
		self.cos = cos(angle)
		self.sin = sin(angle)
		self.rotation = 270 - angle * 180.0 / pi
		self.ok = 1

	def ishit(self, x, y):
		if not self.ok: return 0
		return self.mother.window.hitarrow(x, y, self.sx, self.sy,
						   self.dx, self.dy)

	def drawfocus(self):
		# The entire sync arc has the focus color if selected
		if self.selected:
			color = FOCUSCOLOR
		else:
			color = ARROWCOLOR
		self.mother.new_displist.drawarrow(color, self.sx, self.sy,
						   self.dx, self.dy)

	# Menu stuff beyond what GO offers

	def infocall(self):
		import ArcInfo
		ArcInfo.showarcinfo(self.mother.root, \
			self.snode, self.sside, self.delay, \
			self.dnode, self.dside)

	def delcall(self):
		editmgr = self.mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.delsyncarc(self.snode, self.sside, \
			self.delay, self.dnode, self.dside)
		self.mother.cleanup()
		editmgr.commit()

# Wrap up a function and some arguments for later calling with fewer
# arguments.  The arguments given here are passed *after* the
# arguments given on the call.
def make_closure(func, *args):
	return Closure(func, args).call_it

# helper class for make_closure
class Closure:
	def __init__(self, func, argstuple):
		self.func = func
		self.argstuple = argstuple
	def call_it(self, *args):
		return apply(self.func, args + self.argstuple)
