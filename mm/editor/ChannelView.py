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
import gl, GL, DEVICE
import fl
import FontStuff
import MenuMaker
from Dialog import GLDialog
from ViewDialog import ViewDialog

from MMNode import alltypes, leaftypes, interiortypes
import MMAttrdefs
import Timing
from MMExc import *
from AnchorDefs import *
from ArmStates import *


# Round an 8-bit RGB color triple to 4-bit (as used by doublebuffer)
# Currently disabled -- doesn't seem to work as expected

def fix(r, g, b):
	return r, g, b
##	return r/16*17, g/16*17, b/16*17

# Color assignments (RGB)

BGCOLOR = fix(200, 200, 200)		# Light gray
BORDERCOLOR = fix(75, 75, 75)		# Dark gray
BORDERLIGHT = fix(255, 255, 255)	# White
CHANNELCOLOR = fix(240, 240, 240)	# Very light gray
CHANNELOFFCOLOR = fix(160, 160, 160)	# Darker gray
NODECOLOR = fix(208, 182, 160)		# Pale pinkish, match block view nodes
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

# Anchor indicator box size
ABOXSIZE = 6

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
f_title = FontStuff.FontObject().init('Helvetica', 10)
f_fontheight = f_title.fontheight


# Channel view class

class ChannelView(ViewDialog, GLDialog):

	# Initialization.
	# (Actually, most things are initialized by show().)

	def init(self, toplevel):
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.viewroot = None
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		self.focus = None
		self.future_focus = None
		self.showall = 0
		title = 'Channel View (' + self.toplevel.basename + ')'
		self = ViewDialog.init(self, 'cview_')
		return GLDialog.init(self, title)

	def __repr__(self):
		return '<ChannelView instance, root=' + `self.root` + '>'

	# Dialog interface (extends GLDiallog.{setwin,show,hide})

	def setwin(self):
		GLDialog.setwin(self)
		f_title.setfont()

	def show(self):
		if self.is_showing():
			self.setwin()
			return
		GLDialog.show(self)
		self.initwindow()
		# Other administratrivia
		self.editmgr.register(self)
		self.toplevel.checkviews()
		# Compute objects to draw and where to draw them, then draw
		self.fixviewroot()
		focus = self.focus
		if not focus: focus = ('b', None)
		self.recalc(focus)
		self.getshape()
		self.reshape()
		self.draw()

	def initwindow(self):
		# Use RGB mode
		gl.RGBmode()
		gl.gconfig()
		# Clear the window right now (looks better)
		gl.RGBcolor(BGCOLOR)
		gl.clear()
		# Ask for events
		self.initevents()

	def hide(self):
		if not self.is_showing():
			return
		GLDialog.hide(self)
		self.cleanup()
		self.editmgr.unregister(self)
		self.toplevel.checkviews()

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
			self.setwin()
			self.fixviewroot()
			self.recalc(focus)
			self.reshape()
			self.draw()

	def kill(self):
		self.destroy()

	# Event interface (override glwindow methods)

	def initevents(self):
		# Called by initwindow() above to ask for these events
		fl.qdevice(DEVICE.LEFTMOUSE)
		fl.qdevice(DEVICE.MIDDLEMOUSE)
		fl.qdevice(DEVICE.RIGHTMOUSE)
		fl.qdevice(DEVICE.KEYBD)

	def winshut(self):
		# WINSHUT event: close window, other windows remain.
		# (Also called by default WINQUIT handler.)
		self.hide()

	def redraw(self):
		# REDRAW event.  This may also mean a resize!
		if (self.width, self.height) != gl.getsize():
			self.getshape()
			self.reshape()
		self.draw()

	def channels_changed(self):
		# Called when a channel is switched on or off from the
		# player (this bypasses the edit manager so it can be
		# done even when the document is playing).
		if self.is_showing():
			self.setwin()
			self.redraw()

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
				if self.focus:
					self.focus.popupmenu(x, y)
				else:
					self.baseobject.popupmenu(x, y)

	def keybd(self, val):
		# KEYBD event.
		# 'val' is the ASCII value of the character.
		c = chr(val)
		if self.focus:
			self.focus.shortcut(c)
		else:
			self.baseobject.shortcut(c)

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
		bottom = self.height
		height = bottom - top - f_fontheight
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
		self.showall = (not self.showall)
		self.reshape()
		self.draw()

	# Return list of currently visible channels

	def visiblechannels(self):
		if self.showall:
			return self.context.channels
		else:
			return self.usedchannels

	# Recalculate the set of objects we should be drawing

	def recalc(self, focus):
		self.objects = []
		self.focus = self.lockednode = None
		self.baseobject = GO().init(self, '(base)')
		self.baseobject.select()
		self.objects.append(self.baseobject)
		self.timescaleobject = TimeScaleBox().init(self)
		self.objects.append(self.timescaleobject)
		self.initchannels(focus)
		self.initnodes(focus)
		self.initarcs(focus)

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
		self.channelbottom = 4 * f_fontheight
		self.nodetop = 6 * f_fontheight
		self.timescaleborder = width - f_title.getstrwidth('999999')

	# Recompute the locations where the objects should be drawn

	def reshape(self):
		Timing.needtimes(self.viewroot)
		for c in self.context.channels:
			c.lowest = 0
		for obj in self.objects:
			obj.reshape()

	# Draw the window

	def draw(self):
		gl.RGBcolor(BGCOLOR)
		gl.clear()
		for obj in self.objects:
			obj.draw()

	def drawarcs(self):
		if self.is_showing():
			for obj in self.arcs:
				obj.draw()
	
	# Channel stuff

	def initchannels(self, focus):
		for c in self.context.channels:
			obj = ChannelBox().init(self, c)
			self.objects.append(obj)
			if focus[0] == 'c' and focus[1] is c:
				obj.select()

	# View root stuff

	def nextviewroot(self):
		for c in self.viewroot.GetChildren():
			node = c.FirstMiniDocument()
			if node: break
		else:
			node = self.viewroot.NextMiniDocument()
			if node is None:
				node = self.root.FirstMiniDocument()
		self.setviewroot(node)

	def prevviewroot(self):
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
		self.setwin()
		self.reshape()
		self.fixtitle()
		self.draw()

	def fixtitle(self):
		title = 'Channel View (' + self.toplevel.basename + ')'
		if None <> self.viewroot <> self.root:
			name = MMAttrdefs.getattr(self.viewroot, 'name')
			title = title + ': ' + name
		self.settitle(title)

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
		rebuild_menus()

	def scantree(self, node, focus):
		t = node.GetType()
		if t in leaftypes:
			channel = node.GetChannel()
			if channel:
				channel.used = 1
				obj = NodeBox().init(self, node)
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
				func = make_closure(GO.setviewrootcall, c)
				tuple = ('', name, func)
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
				func = make_closure(GO.setviewrootcall, node)
				tuple = ('', name, func)
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
				func = make_closure(GO.setviewrootcall, c)
				tuple = ('', name, func)
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
				obj = ArcBox().init(self, \
					xnode, xside, delay, ynode, yside)
				arcs.append(obj)

	# Focus stuff (see also recalc)

	def deselect(self):
		if self.focus:
			self.focus.deselect()

	def select(self, x, y):
		self.deselect()
		hits = []
		for obj in self.objects:
			if obj.ishit(x, y):
				hits.append(obj)
		if not hits:
			return
		obj = hits[-1] # Last object (the one drawn on top)
		obj.select()
		self.drawarcs()

	# Global focus stuff

	def getfocus(self):
		if self.focus:
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
		if not hasattr(node, 'cv_obj'):
			return
		obj = node.cv_obj
		self.setwin()
		self.deselect()
		obj.select()
		self.drawarcs()

	# Create a new channel

	def newchannel(self, index):
		if self.visiblechannels() <> self.context.channels:
			fl.show_message( \
				  'You can\'t create a new channel', \
				  'unless you are showing unused channels', \
				  '(use shortcut \'T\')')
			return
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		import windowinterface
		from ChannelMap import commonchanneltypes, otherchanneltypes
		prompt = 'Channel type:'
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
				editmgr.rollback()
				return		# User doesn't want to choose
			elif list[i] == 'Other...':
				list, olist = olist, list
				continue
			type = list[i]
			break
		i = 1
		base = 'NEW'
		name = base + `i`
		context = self.context
		while context.channeldict.has_key(name):
			i = i+1
			name = base + `i`
		editmgr.addchannel(name, index, type)
		channel = context.channels[index]
		self.future_focus = 'c', channel
		self.showall = 1	# Force showing the new channel
		self.cleanup()
		editmgr.commit()
		import AttrEdit
		AttrEdit.showchannelattreditor(channel)


# Base class for Graphical Objects.
# These live in close symbiosis with their "mother", the ChannelView!
# Note: reshape() must be called before draw() or ishit() can be called.

class GO:

	def init(self, mother, name):
		self.mother = mother
		self.name = name
		self.selected = 0
		self.ok = 0
		return self

	def __repr__(self):
		return '<GO instance, name=' + `self.name` + '>'

	def getnode(self):
		# Called by mother's getfocusnode()
		# Overridden by NodeBox
		return None

	def cleanup(self):
		# Called just before forgetting the object
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
		gl.RGBcolor(TEXTCOLOR)
		f_title.centerstring(self.mother.timescaleborder, 0, \
			  self.mother.width, self.mother.channelbottom, \
			  str)

	def select(self):
		# Make this object the focus
		if self.selected:
			return
		self.mother.deselect()
		self.selected = 1
		self.mother.focus = self
		if self.ok:
			self.drawfocus()

	def deselect(self):
		# Remove this object from the focus
		if not self.selected:
			return
		self.selected = 0
		self.mother.focus = None
		if self.ok:
			self.drawfocus()

	def ishit(self, x, y):
		# Check whether the given mouse coordinates are in this object
		return 0

	# Methods to handle interaction events

	# Handle a right button mouse click in the object
	def popupmenu(self, x, y):
		func = self.__class__.menu.popup(x, y)
		if func: func(self)

	# Handle a shortcut in the object
	def shortcut(self, c):
		func = self.__class__.menu.shortcut(c)
		if func: func(self)
		else: gl.ringbell()

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

	def setviewrootcall(self, node):
		self.mother.setviewroot(node)

	def newchannelindex(self):
		# NB Overridden by ChannelBox to insert before current!
		return len(self.mother.context.channelnames)

	# Submenus listing related mini-documents

	ancestors = []
	descendants = []
	siblings = []

	# Menu and shortcut definitions are stored as data in the class,
	# since they are the same for all objects of a class...

	commandlist = c = []
	c.append('h', 'Help...',         helpcall)
	c.append('c', 'New channel...',  newchannelcall)
	c.append('N', 'Next mini-document', nextminicall)
	c.append('P', 'Previous mini-document', prevminicall)
	c.append('',  'Ancestors', ancestors)
	c.append('', 'Siblings', siblings)
	c.append('', 'Descendants', descendants)
	c.append('T', 'Toggle unused channels', toggleshowcall)
	menutitle = 'Base ops'
	menu = MenuMaker.MenuObject().init(menutitle, commandlist)


# Class for the time scale object

class TimeScaleBox(GO):

	def init(self, mother):
		return GO.init(self, mother, 'timescale')

	def __repr__(self):
		return '<TimeScaleBox instance>'

	def reshape(self):
		self.left = self.mother.timescaleborder + \
			  f_title.getstrwidth(' ')
		self.right = self.mother.width
		t0, t1 = self.mother.timerange()
		self.top, self.bottom = self.mother.maptimes(t0, t1)
		self.ok = 1

	def drawfocus(self):
		l, t, r, b = self.left, self.top, self.right, self.bottom
		height = b-t
		if height <= 0:
			return
		gl.RGBcolor(BORDERCOLOR)
		# Draw rectangle around boxes
		l = l+2
		t = t+2
		r = (4*l+r)/5
		b = b-2
		gl.bgnclosedline()
		gl.v2f(l, t)
		gl.v2f(r, t)
		gl.v2f(r, b)
		gl.v2f(l, b)
		gl.endclosedline()
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
		while i < n:
			i = i + 1
			#
			it0 = t0 + i*10
			it1 = it0 + 5
			t, b = self.mother.maptimes(it0, it1)
			t = max(t, self.top + 2)
			b = min(b, self.bottom - 2)
			if b <= t:
				continue
			gl.RGBcolor(BORDERCOLOR)
			gl.bgnpolygon()
			gl.v2f(l, t)
			gl.v2f(r, t)
			gl.v2f(r, b)
			gl.v2f(l, b)
			gl.endpolygon()
			if i%div <> 0:
				continue
			gl.RGBcolor(TEXTCOLOR)
			f_title.centerstring( \
				  r, t-f_fontheight/2, \
				  self.right, t+f_fontheight/2, \
				  `i*10`)


# Class for Channel Objects

class ChannelBox(GO):

	def init(self, mother, channel):
		self = GO.init(self, mother, channel.name)
		self.channel = channel
		if channel.has_key('type'):
			self.ctype = channel['type']
		else:
			self.ctype = '???'
		return self

	def __repr__(self):
		return '<ChannelBox instance, name=' + `self.name` + '>'

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
		self.farbottom = self.mother.height
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

		# Draw a diamond
		cd = self.mother.context.channeldict[self.name]
		if cd.has_key('visible'):
			visible = cd['visible']
		else:
			visible = 1
		if visible:
			gl.RGBcolor(CHANNELCOLOR)
		else:
			gl.RGBcolor(CHANNELOFFCOLOR)
		gl.bgnpolygon()
		gl.v2f(l, y)
		gl.v2f(x, t)
		gl.v2f(r, y)
		gl.v2f(x, b)
		gl.endpolygon()

		# Outline the diamond; 'engraved' normally,
		# 'sticking out' if selected
		if self.selected:
			n = int(3.0 * (r-l) / (b-t) + 0.5)
			ll = l + n
			tt = t + 3
			rr = r - n
			bb = b - 3

			gl.RGBcolor(FOCUSLEFT)
			gl.bgnpolygon()
			gl.v2f(l, y)
			gl.v2f(x, t)
			gl.v2f(x, tt)
			gl.v2f(ll, y)
			gl.endpolygon()

			gl.RGBcolor(FOCUSTOP)
			gl.bgnpolygon()
			gl.v2f(x, t)
			gl.v2f(r, y)
			gl.v2f(rr, y)
			gl.v2f(x, tt)
			gl.endpolygon()

			gl.RGBcolor(FOCUSRIGHT)
			gl.bgnpolygon()
			gl.v2f(r, y)
			gl.v2f(x, b)
			gl.v2f(x, bb)
			gl.v2f(rr, y)
			gl.endpolygon()

			gl.RGBcolor(FOCUSBOTTOM)
			gl.bgnpolygon()
			gl.v2f(l, y)
			gl.v2f(ll, y)
			gl.v2f(x, bb)
			gl.v2f(x, b)
			gl.endpolygon()

			gl.RGBcolor(FOCUSBORDER)
			gl.linewidth(1)
			gl.bgnclosedline()
			gl.v2f(l, y)
			gl.v2f(x, t)
			gl.v2f(r, y)
			gl.v2f(x, b)
			gl.endclosedline()
		else:
			gl.linewidth(1)
			gl.RGBcolor(BORDERCOLOR)
			gl.bgnclosedline()
			gl.v2f(l, y)
			gl.v2f(x, t)
			gl.v2f(r, y)
			gl.v2f(x, b)
			gl.endclosedline()

			gl.RGBcolor(BORDERLIGHT)
			gl.bgnclosedline()
			gl.v2f(l+1, y+1)
			gl.v2f(x+1, t+1)
			gl.v2f(r+1, y+1)
			gl.v2f(x+1, b+1)
			gl.endclosedline()

		# Draw the name
		gl.RGBcolor(TEXTCOLOR)
		f_title.centerstring(self.left, self.top, \
			  self.right, self.bottom, self.name)

		# Draw the channel type
		ctype = '(' + self.ctype + ')'
		f_title.centerstring(self.left, self.bottom, \
			  self.right, self.bottom + f_fontheight, ctype)

	def drawline(self):
		# Draw a gray and a white vertical line
		gl.RGBcolor(BORDERCOLOR)
		gl.linewidth(1)
		gl.bgnline()
		gl.v2f(self.xcenter, self.bottom)
		gl.v2f(self.xcenter, self.farbottom)
		gl.endline()
		gl.RGBcolor(BORDERLIGHT)
		gl.bgnline()
		gl.v2f(self.xcenter+1, self.bottom)
		gl.v2f(self.xcenter+1 , self.farbottom)
		gl.endline()

	# Menu stuff beyond what GO offers

	def attrcall(self):
		import AttrEdit
		AttrEdit.showchannelattreditor(self.channel)

	def delcall(self):
		if self.channel in self.mother.usedchannels:
			fl.show_message( \
				  'You can\'t delete a channel', \
				  'that is still in use', '')
			return
		editmgr = self.mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.delchannel(self.name)
		self.mother.cleanup()
		editmgr.commit()

	def newchannelindex(self):
		# Hook for newchannelcall to determine placement
		return self.mother.context.channelnames.index(self.name)

	commandlist = c = GO.commandlist[:]
	char, text, proc = c[-1]
	c[-1] = char, text + '%l', proc
	c.append('i', '', attrcall)
	c.append('a', 'Channel attr...', attrcall)
	c.append('d', 'Delete channel',  delcall)
	menutitle = 'Channel ops'
	menu = MenuMaker.MenuObject().init(menutitle, commandlist)


class NodeBox(GO):

	def __repr__(self):
		return '<NodeBox instance, name=' + `self.name` + '>'

	def init(self, mother, node):
		self.node = node
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
		return GO.init(self, mother, name)

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
			self.node.armedmode = mode
			self.mother.setwin()
			self.drawfocus()
			self.mother.drawarcs()

	def lock(self):
		if not self.locked:
			self.deselect()
			if self.mother.lockednode:
				self.mother.lockednode.unlock()
			self.locked = 1
			self.mother.lockednode = self
			self.drawfocus()

	def unlock(self):
		if self.locked:
			self.locked = 0
			self.mother.lockednode = None
			self.drawfocus()

	def select(self):
		self.unlock()
		GO.select(self)

	def reshape(self):
		# Compute ideal box coordinates
		channel = self.node.GetChannel()
		left, right = self.mother.mapchannel(channel)
		top, bottom = self.mother.maptimes(self.node.t0, self.node.t1)

		# Move top/bottom inwards by one pixel
		top = top+1
		bottom = bottom-1

		# Move top down below the previous node if necessary
		if top < channel.lowest:
			top = channel.lowest

		# Keep space for at least one line of text
		bottom = max(bottom, top+f_fontheight-2)

		# Update channel's lowest node
		channel.lowest = int(bottom)

		self.left, self.top, self.right, self.bottom = \
			left, top, right, bottom
		self.ok = 1

	def ishit(self, x, y):
		if not self.ok: return 0
		return self.left <= x <= self.right and \
		       self.top <= y <= self.bottom

	def drawfocus(self):
		l, t, r, b = self.left, self.top, self.right, self.bottom

		# Draw a box
		if self.locked:
			gl.RGBcolor(LOCKEDCOLOR)
		elif armcolors.has_key(self.node.armedmode):
			gl.RGBcolor(armcolors[self.node.armedmode])
		else:
			gl.RGBcolor(NODECOLOR)
		gl.bgnpolygon()
		gl.v2f(l, t)
		gl.v2f(r, t)
		gl.v2f(r, b)
		gl.v2f(l, b)
		gl.endpolygon()

		# If the end time was inherited, make the bottom-right
		# triangle of the box a lighter color
		if self.node.t0t1_inherited:
			gl.RGBcolor(ALTNODECOLOR)
			gl.bgnpolygon()
			gl.v2f(r, t)
			gl.v2f(r, b)
			gl.v2f(l, b)
			gl.endpolygon()

		# If there are anchors on this node,
		# draw a small orange box in the bottom left corner
		if self.hasanchors:
			gl.RGBcolor(ANCHORCOLOR)
			gl.bgnpolygon()
			gl.v2f(l, b)
			gl.v2f(l+ABOXSIZE, b)
			gl.v2f(l+ABOXSIZE, b-ABOXSIZE)
			gl.v2f(l, b-ABOXSIZE)
			gl.endpolygon()

		# If there is a pausing anchor,
		# draw an orange line at the bottom
		if self.haspause:
			gl.RGBcolor(ANCHORCOLOR)
			gl.bgnpolygon()
			gl.v2f(l, b)
			gl.v2f(r, b)
			gl.v2f(r, b-ABOXSIZE)
			gl.v2f(l, b-ABOXSIZE)
			gl.endpolygon()

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
			gl.v2f(l1, t1)
			gl.v2f(ll, tt)
			gl.v2f(ll, bb)
			gl.v2f(l1, b1)
			gl.endpolygon()
			gl.RGBcolor(FOCUSTOP)
			gl.bgnpolygon()
			gl.v2f(l1, t1)
			gl.v2f(r1, t1)
			gl.v2f(rr, tt)
			gl.v2f(ll, tt)
			gl.endpolygon()
			gl.RGBcolor(FOCUSRIGHT)
			gl.bgnpolygon()
			gl.v2f(r1, t1)
			gl.v2f(r1, b1)
			gl.v2f(rr, bb)
			gl.v2f(rr, tt)
			gl.endpolygon()
			gl.RGBcolor(FOCUSBOTTOM)
			gl.bgnpolygon()
			gl.v2f(l1, b1)
			gl.v2f(ll, bb)
			gl.v2f(rr, bb)
			gl.v2f(r1, b1)
			gl.endpolygon()
			gl.RGBcolor(FOCUSBORDER)
			gl.linewidth(1)
			gl.bgnclosedline()
			gl.v2f(l1, t)
			gl.v2f(r, t)
			gl.v2f(r, b)
			gl.v2f(l1, b)
			gl.endclosedline()
		else:
			# Outline the box in 'engraved' look
			gl.RGBcolor(BORDERCOLOR)
			gl.linewidth(1)
			gl.bgnclosedline()
			gl.v2f(l-1, t)
			gl.v2f(r, t)
			gl.v2f(r, b-1)
			gl.v2f(l-1, b-1)
			gl.endclosedline()
			gl.RGBcolor(BORDERLIGHT)
			gl.bgnclosedline()
			gl.v2f(l, t+1)
			gl.v2f(r+1, t+1)
			gl.v2f(r+1, b)
			gl.v2f(l, b)
			gl.endclosedline()

		# Draw the name, centered in the box
		gl.RGBcolor(TEXTCOLOR)
		f_title.centerstring(l, t, r, b, self.name)

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

	def lockcall(self):
		self.lock()

	def unlockcall(self):
		if self.mother.lockednode:
			self.mother.lockednode.unlock()
		else:
			gl.ringbell()

	def newsyncarccall(self):
		if not self.mother.lockednode:
			gl.ringbell()
			return
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

	def focuscall(self):
		self.mother.toplevel.hierarchyview.globalsetfocus(self.node)

	def hyperlinkcall(self):
		self.mother.toplevel.links.finish_link(self.node)

	commandlist = c = GO.commandlist[:]
	char, text, proc = c[-1]
	c[-1] = char, text + '%l', proc
	c.append('p', 'Play node...', playcall)
	c.append('G', 'Play from here...%l', playfromcall)
	c.append('i', 'Node info...', infocall)
	c.append('a', 'Node attr...', attrcall)
	c.append('e', 'Edit contents...', editcall)
	c.append('t', 'Edit anchors...', anchorcall)
	c.append('L', 'Finish hyperlink...%l', hyperlinkcall)
	c.append('f', 'Push focus', focuscall)
	c.append('l', 'Lock node', lockcall)
	c.append('u', 'Unlock node', unlockcall)
	c.append('s', 'New sync arc...', newsyncarccall)
	menutitle = 'Node ops'
	menu = MenuMaker.MenuObject().init(menutitle, commandlist)


class ArcBox(GO):

	def __repr__(self):
		return '<ArcBox instance, name=' + `self.name` + '>'

	def init(self, mother, snode, sside, delay, dnode, dside):
		self.snode, self.sside, self.delay, self.dnode, self.dside = \
			snode, sside, delay, dnode, dside
		return GO.init(self, mother, 'arc')

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
		# XXX Shouldn't we be using gl.pick() here?
		# Translate
		x, y = x - self.dx, y - self.dy
		# Rotate
		nx = x * self.cos - y * self.sin
		ny = x * self.sin + y * self.cos
		# Test
		if ny > 0 or ny < -ARR_LENGTH:
			return 0
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return 0
		return 1

	def drawfocus(self):
		# The entire sync arc has the focus color if selected
		if self.selected:
			gl.RGBcolor(FOCUSCOLOR)
		else:
			gl.RGBcolor(ARROWCOLOR)
		# Draw the line from src to dst
		gl.linewidth(2)
		gl.bgnline()
		gl.v2f(self.sx, self.sy)
		gl.v2f(self.dx, self.dy)
		gl.endline()
		# Draw the arrowhead
		# Translate so that the point of the arrowhead is (0, 0)
		# Rotate so that it comes in horizontally from the right
		gl.pushmatrix()
		gl.translate(self.dx, self.dy, 0)
		gl.rot(self.rotation, 'z')
		gl.bgnpolygon()
		gl.v2f(0, 0)
		gl.v2f(ARR_LENGTH, ARR_HALFWIDTH)
		gl.v2f(ARR_LENGTH, -ARR_HALFWIDTH)
		gl.endpolygon()
		gl.popmatrix()

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

	commandlist = c = GO.commandlist[:]
	char, text, proc = c[-1]
	c[-1] = char, text + '%l', proc
	c.append('i', 'Sync arc info...', infocall)
	c.append('d', 'Delete sync arc',  delcall)
	menutitle = 'Sync arc ops'
	menu = MenuMaker.MenuObject().init(menutitle, commandlist)

# Rebuild all menus (to accomodate changes in entries)
def rebuild_menus():
	for cls in GO, ChannelBox, NodeBox, ArcBox:
		cls.menu.close()
		cls.menu = MenuMaker.MenuObject().init(cls.menutitle,
						       cls.commandlist)

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
