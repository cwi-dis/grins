__version__ = "$Id$"

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
import windowinterface, WMEVENTS
from ChannelViewDialog import ChannelViewDialog, GOCommand, \
	ChannelBoxCommand, NodeBoxCommand, ArcBoxCommand
from usercmd import *

from MMNode import alltypes, leaftypes, interiortypes
import MMAttrdefs
import Timing
from MMExc import *
from AnchorDefs import *
from ArmStates import *
from MMTypes import *


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

begend = ('begin', 'end')


# Channel view class

class ChannelView(ChannelViewDialog):

	# Initialization.
	# (Actually, most things are initialized by show().)

	def __init__(self, toplevel):
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
		self.showall = 1
		self.placing_channel = 0
		self.thumbnails = 0
		title = 'Channel View (' + self.toplevel.basename + ')'
		ChannelViewDialog.__init__(self)
		self.delayed_drawarcs_id = None

	def __repr__(self):
		return '<ChannelView instance, root=' + `self.root` + '>'

	# Dialog interface

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Channel View (' + self.toplevel.basename + ')'
		ChannelViewDialog.show(self, title)
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
		self.setcommands(obj.commandlist, title = obj.menutitle)

	def hide(self, *rest):
		if not self.is_showing():
			return
		self.toplevel.showstate(self, 0)
		ChannelViewDialog.hide(self)
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
		if self.future_focus is not None:
			focus = self.future_focus
			self.future_focus = None
		elif self.focus is None:
			focus = '', None
		elif type(self.focus) is type(()):
			focus = self.focus
		elif self.focus.__class__ is ChannelBox:
			focus = 'c', self.focus.channel
		elif self.focus.__class__ is NodeBox:
			focus = 'n', self.focus.node
		elif self.focus.__class__ is ArcBox:
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

	# Event interface

	def resize(self, *rest):
		if self.focus is None:
			focus = '', None
		elif type(self.focus) is type(()):
			focus = self.focus
		elif self.focus.__class__ is ChannelBox:
			focus = 'c', self.focus.channel
		elif self.focus.__class__ is NodeBox:
			focus = 'n', self.focus.node
		elif self.focus.__class__ is ArcBox:
			focus = 'a', None
		else:
			focus = '', None
		self.recalc(focus)
		self.reshape()
		self.draw()

	def thumbnailcall(self):
		self.thumbnails = not self.thumbnails
		self.settoggle(THUMBNAIL, self.thumbnails)
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		bl, fh, ps = self.new_displist.usefont(f_title)
		self.draw()

	def canvascall(self, code):
		self.window.setcanvassize(code)

	def redraw(self):
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
			self.toplevel.setwaiting()
			self.select(x, y)
			self.toplevel.setready()

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
		height = 1.0 - top - self.new_displist.strsize('m')[0]
		vt0, vt1 = self.timerange()
		dt = vt1 - vt0

		# Compute the 'ideal' top/bottom
		return top + (height * (t0 - vt0) / dt), \
		       top + (height * (t1 - vt0) / dt)

	def mapchannel(self, channel):
		# Map channel to left and right coordinates
		if channel.chview_map is not None:
			return channel.chview_map
		list = self.visiblechannels()
		nchannels = len(list)
		try:
			i = list.index(channel)
		except ValueError:
			return 0, 0
		height = float(self.timescaleborder) / nchannels
		x, y = (i + 0.1) * height, (i + 0.9) * height
		channel.chview_map = x, y
		return x, y

	def channelgapindex(self, y):
		list = self.visiblechannels()
		nchannels = len(list)
		if nchannels == 0:
		    return 0
		height = float(self.timescaleborder) / nchannels
		rv = int((y+height/2)/height)
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
		self.showall = (not self.showall)
		for c in self.context.channels:
			c.chview_map = None
		self.redraw()

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
		self.channelright = displist.strsize('999999')[0]
		self.nodetop = self.channelright * 1.5
		self.timescaleborder = 1.0 - 4 * fh

		self.objects = []
		self.focus = self.lockednode = None
		self.baseobject = BaseBox(self, '(base)')
		self.objects.append(self.baseobject)
		self.timescaleobject = TimeScaleBox(self)
		self.objects.append(self.timescaleobject)
		self.initchannels(focus)
		self.initnodes(focus)
		self.initarcs(focus)
		focus = self.focus
		self.baseobject.select()
		if focus is not None:
			focus.select()

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

	def delayed_drawarcs(self):
		self.delayed_drawarcs_id = None
		if not self.arcs:
			return
		self.init_display()
		self.drawarcs()
		self.render()

	def delay_drawarcs(self):
		if self.delayed_drawarcs_id is not None:
			windowinterface.canceltimer(self.delayed_drawarcs_id)
		if self.arcs:
			self.delayed_drawarcs_id = windowinterface.settimer(
				0.01, (self.delayed_drawarcs, ()))

	# Channel stuff

	def initchannels(self, focus):
		for c in self.context.channels:
			obj = ChannelBox(self, c)
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
		if node is not None and node.GetRoot() is not self.root:
			node = None
		if node is not None and not node.IsMiniDocument():
			node = None
		if node is None:
			node = self.root.FirstMiniDocument()
		if node is None:
			node = self.root
		self.viewroot = node
		self.fixtitle()

	# Change the view root
	def setviewroot(self, node):
		if node is None or node is self.viewroot:
			return
		self.cleanup()
		self.viewroot = node
		self.recalc(('b', None))
		self.reshape()
		self.fixtitle()
		self.draw()

	def focuscall(self):
		top = self.toplevel
		top.setwaiting()
		top.hierarchyview.globalsetfocus(self.viewroot)
		top.setready()

	def setviewrootcb(self, node):
		self.toplevel.setwaiting()
		self.setviewroot(node)
		self.toplevel.setready()

	def fixtitle(self):
		title = 'Channel View (' + self.toplevel.basename + ')'
		if None is not self.viewroot is not self.root:
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
			c.chview_map = None
			if c.used:
				self.usedchannels.append(c)
			elif not self.showall:
				c.chview_map = 0, 0
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
		elif t in bagtypes:
			self.scandescendants(node)
		else:
			obj = INodeBox(self, node)
			self.objects.append(obj)
			for c in node.GetChildren():
				self.scantree(c, focus)

	def scandescendants(self, node):
		for c in node.GetChildren():
			t = c.GetType()
			if t in bagtypes:
				self.scandescendants(c)
			elif c.IsMiniDocument():
				name = c.GetRawAttrDef('name', '(NoName)')
				self.baseobject.descendants.append((name, (c,)))
			elif t in interiortypes:
				self.scandescendants(c)

	def addancestors(self):
		self.baseobject.ancestors[:] = []
		path = self.viewroot.GetPath()
		for node in path[:-1]:
			if node.IsMiniDocument():
				name = node.GetRawAttrDef('name', '(NoName)')
				self.baseobject.ancestors.append((name, (node,)))

	def addsiblings(self):
		self.baseobject.siblings[:] = []
		parent = self.viewroot.GetParent()
		if parent:
			while parent.parent and \
				  parent.parent.GetType() in bagtypes:
				parent = parent.parent
			self.scansiblings(parent)

	def scansiblings(self, node):
		for c in node.GetChildren():
			if c.GetType() in bagtypes:
				self.scansiblings(c)
			elif c.IsMiniDocument():
				name = c.GetRawAttrDef('name', '(NoName)')
				if c is self.viewroot:
					name = name + ' (current)'
				self.baseobject.siblings.append((name, (c,)))

	# Arc stuff

	def initarcs(self, focus):
		arcs = []
		self.scanarcs(self.viewroot, focus, arcs)
		self.objects[len(self.objects):] = self.arcs = arcs

	def scanarcs(self, node, focus, arcs):
		type = node.GetType()
		if type in leaftypes and node.GetChannel():
			self.addarcs(node, arcs)
		elif type not in bagtypes:
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
			if xnode.FindMiniDocument() is self.viewroot:
				obj = ArcBox(self,
					     xnode, xside, delay, ynode, yside)
				arcs.append(obj)

	# Focus stuff (see also recalc)

	def deselect(self):
		if self.focus and type(self.focus) is not type(()):
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
		self.setcommands(obj.commandlist, title = obj.menutitle)

	# Global focus stuff

	def getfocus(self):
		if self.focus and type(self.focus) is not type(()):
			return self.focus.getnode()
		else:
			return None

	def globalsetfocus(self, node):
		# May have to switch view root
		mini = node.FindMiniDocument()
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
				  "(use shortcut 'T')",
				  mtype = 'warning', parent = self.window)
			return
	        if self.placing_channel:
		        windowinterface.showmessage(
				'Please place the other channel first!',
				mtype = 'error', parent = self.window)
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
		list = []
		for name in commonchanneltypes + otherchanneltypes:
			list.append(name, (self.select_cb, (name,)))
		list.append(None)
		list.append('Cancel')
		windowinterface.Dialog(list, title = 'Select', prompt = prompt, grab = 1, vertical = 1, parent = self.window)

	def select_cb(self, name):
		self.placing_channel = PLACING_NEW
		self.placing_type = name
		windowinterface.setcursor('stop')
		self.window.setcursor('channel')

	def copychannel(self, name):
		if self.visiblechannels() <> self.context.channels:
			windowinterface.showmessage(
				  "You can't create a new channel\n" +
				  "unless you are showing unused channels\n" +
				  "(use shortcut 'T')",
				  mtype = 'warning')
			return
	        if self.placing_channel:
		        windowinterface.showmessage(
				'Please place the other channel first!',
				mtype = 'error')
			return
		#
		# Slightly hacky code: we try to check here whether
		# the transaction is possible, but we don't do it till later.
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		editmgr.rollback()
		windowinterface.setcursor('stop')
		self.window.setcursor('channel')
		self.placing_channel = PLACING_COPY
		self.placing_orig = name

	def movechannel(self, name):
		if self.visiblechannels() <> self.context.channels:
			windowinterface.showmessage(
				  "You can't move a channel\n" +
				  "unless you are showing unused channels\n" +
				  "(use shortcut 'T')",
				  mtype = 'warning')
			return
	        if self.placing_channel:
		        windowinterface.showmessage(
				'Please place the other channel first!',
				mtype = 'error')
			return
		#
		# Slightly hacky code: we try to check here whether
		# the transaction is possible, but we don't do it till later.
		editmgr = self.editmgr
		if not editmgr.transaction():
			return		# Not possible at this time
		editmgr.rollback()
		windowinterface.setcursor('stop')
		self.window.setcursor('channel')
		self.placing_channel = PLACING_MOVE
		self.placing_orig = name

	def finish_channel(self, x, y):
	        placement_type = self.placing_channel
	        self.placing_channel = 0
		index = self.channelgapindex(y)
	        windowinterface.setcursor('')
		editmgr = self.editmgr
		if not editmgr.transaction():
			return
		self.toplevel.setwaiting()
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

		root_layout = None
		if placement_type == PLACING_NEW:
		    # find a root window
		    # if there is one, root_layout will be its name,
		    # if there are multiple, root_layout will be '',
		    # if there are none, root_layout will be None.
		    for key, val in context.channeldict.items():
			if val.get('base_window') is None:
			    # we're looking at a top-level channel
			    if root_layout is None:
				# first one
				root_layout = key
			    else:
				# multiple root windows
				root_layout = ''
		    editmgr.addchannel(name, index, self.placing_type)
		elif placement_type == PLACING_COPY:
		    editmgr.copychannel(name, index, self.placing_orig)
		else:
		    c = context.channeldict[name]
		    editmgr.movechannel(name, index)
		    index = context.channels.index(c)
		channel = context.channels[index]
		if placement_type == PLACING_NEW and root_layout:
			channel['base_window'] = root_layout
		self.future_focus = 'c', channel
		self.showall = 1	# Force showing the new channel
		for c in self.context.channels:
			c.chview_map = None
		self.cleanup()
		editmgr.commit()
		if placement_type in (PLACING_NEW, PLACING_COPY):
			import AttrEdit
			AttrEdit.showchannelattreditor(self.toplevel,
						       channel, new = 1)
		self.toplevel.setready()

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

class GO(GOCommand):

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
		self.arcmenu = []

		# Menu and shortcut definitions are stored as data in
		# the class

		self.menutitle = 'Base ops'
		self.commandlist = [
			CLOSE_WINDOW(callback = (self.mother.hide, ())),
			CANVAS_HEIGHT(callback = (self.canvascall,
					(windowinterface.DOUBLE_HEIGHT,))),
			CANVAS_WIDTH(callback = (self.canvascall,
					(windowinterface.DOUBLE_WIDTH,))),
			CANVAS_RESET(callback = (self.canvascall,
					(windowinterface.RESET_CANVAS,))),
			NEW_CHANNEL(callback = (self.newchannelcall, ())),
			NEXT_MINIDOC(callback = (self.nextminicall, ())),
			PREV_MINIDOC(callback = (self.prevminicall, ())),
			ANCESTORS(callback = self.mother.setviewrootcb),
			SIBLINGS(callback = self.mother.setviewrootcb),
			DESCENDANTS(callback = self.mother.setviewrootcb),
			TOGGLE_UNUSED(callback = (self.toggleshowcall, ())),
			THUMBNAIL(callback = (self.mother.thumbnailcall, ())),
			]
		import Help
		if Help.hashelp():
			self.commandlist.append(HELP(callback=(self.helpcall,())))
		GOCommand.__init__(self)

	def __repr__(self):
		if hasattr(self, 'name'):
			name = ', name=' + `self.name`
		else:
			name = ''
		return '<%s instance%s>' % (self.__class__.__name__, name)

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
		d.centerstring(0, self.mother.timescaleborder,
			       self.mother.channelright, 1.0, str)

	def select(self):
		# Make this object the focus
		if self.selected:
			return
		self.mother.deselect()
		self.selected = 1
		self.mother.focus = self
		self.mother.setcommands(self.commandlist,
					       title = self.menutitle)
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
			mother.setcommands(baseobject.commandlist,
						  title = baseobject.menutitle)
			self.drawfocus()

	def ishit(self, x, y):
		# Check whether the given mouse coordinates are in this object
		return 0

	# Methods corresponding to the menu entries

## 	def helpcall(self):
## 		import Help
## 		Help.givehelp('Channel_view')

	def canvascall(self, code):
		self.mother.canvascall(code)

	def newchannelcall(self):
		self.mother.newchannel(self.newchannelindex())

	def nextminicall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.nextviewroot()
		mother.toplevel.setready()

	def prevminicall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.prevviewroot()
		mother.toplevel.setready()

	def toggleshowcall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.toggleshow()
		mother.toplevel.setready()

	def newchannelindex(self):
		# NB Overridden by ChannelBox to insert before current!
		return len(self.mother.context.channelnames)


class BaseBox(GO):
	def __init__(self, mother, name):
		GO.__init__(self, mother, name)
		self.commandlist = self.commandlist + [
			PUSHFOCUS(callback = (mother.focuscall, ())),
			]

# Class for the time scale object

class TimeScaleBox(GO):

	def __init__(self, mother):
		GO.__init__(self, mother, 'timescale')

	def reshape(self):
		self.top = self.mother.timescaleborder + \
			   self.mother.new_displist.fontheight()
		self.bottom = 1.0
		t0, t1 = self.mother.timerange()
		self.left, self.right = self.mother.maptimes(t0, t1)
		self.ok = 1

	def drawfocus(self):
		l, t, r, b = self.left, self.top, self.right, self.bottom
		width = r-l
		if width <= 0:
			return
		d = self.mother.new_displist
		f_width = d.strsize('x')[0]
		d.fgcolor(BORDERCOLOR)
		# Draw rectangle around boxes
		hmargin = d.strsize('x')[0] / 9
		vmargin = d.fontheight() / 4
		l = l + hmargin
		t = t + vmargin
		r = r - hmargin
		b = (4*t+b)/5
		d.drawbox((l, t, r - l, b - t))
		# Compute number of division boxes
		t0, t1 = self.mother.timerange()
		dt = t1 - t0
		n = int(ceil(dt/10.0))
		# Compute distance between numeric indicators
		div = 1
		i = 0
		while (n/div) * 1.5 * f_width >= width:
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
			l, r = self.mother.maptimes(it0, it1)
			l = max(l, self.left)
			r = min(r, self.right)
			if r <= l:
				continue
			d.drawfbox(BORDERCOLOR, (l, t, r - l, b - t))
			if i%div <> 0:
				continue
			d.centerstring(l-f_width*2, b,
				       l+f_width*2, self.bottom,
				       `i*10`)
		for i in self.mother.discontinuities:
		        l, r = self.mother.maptimes(i, i)
			d.drawline(ANCHORCOLOR, [(l, t), (l, b)])



# Class for Channel Objects

class ChannelBox(GO, ChannelBoxCommand):

	def __init__(self, mother, channel):
		GO.__init__(self, mother, channel.name)
		self.channel = channel
		try:
			self.ctype = channel['type']
		except KeyError:
			self.ctype = '???'

		self.commandlist = self.commandlist + [
			ATTRIBUTES(callback = (self.attrcall, ())),
			DELETE(callback = (self.delcall, ())),
			MOVE_CHANNEL(callback = (self.movecall, ())),
			COPY_CHANNEL(callback = (self.copycall, ())),
			TOGGLE_ONOFF(callback = (self.channel_onoff, ())),
			HIGHLIGHT(callback = (self.highlight, ())),
			UNHIGHLIGHT(callback = (self.unhighlight, ())),
			]
		self.menutitle = 'Channel %s ops' % self.name
		ChannelBoxCommand.__init__(self)

	def channel_onoff(self):
		self.mother.toplevel.setwaiting()
		player = self.mother.toplevel.player
		ch = self.channel
		if player.is_showing():
			player.channel_callback(ch.name)
			self.mother.toplevel.setready()
			return
		try:
			isvis = ch.attrdict['visible']
		except KeyError:
			isvis = 1
		ch.attrdict['visible'] = not isvis
		self.mother.channels_changed()
		self.mother.toplevel.setready()

	def reshape(self):
		top, bottom = self.mother.mapchannel(self.channel)
		if top == bottom:
			self.ok = 0
			return
		self.left = 0
		self.right = self.mother.channelright
		self.top = top
		self.bottom = bottom
		self.xcenter = (self.left + self.right) / 2
		self.ycenter = (self.top + self.bottom) / 2
		self.farright = 1.0
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
		try:
			visible = cd['visible']
		except KeyError:
			visible = 1
		if visible:
			color = CHANNELCOLOR
		else:
			color = CHANNELOFFCOLOR
		d.drawfdiamond(color, (l, t, r - l, b - t))

		# Outline the diamond; 'engraved' normally,
		# 'sticking out' if selected
		if self.selected:
			d.draw3ddiamond(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT,
					FOCUSBOTTOM, (l, t, r - l, b - t))
		d.fgcolor(BORDERCOLOR)
		d.drawdiamond((l, t, r - l, b - t))

		# Draw the name
		d.fgcolor(TEXTCOLOR)
		d.centerstring(l, t, r, b, self.name)

## 		# Draw the channel type
		import ChannelMap
		map = ChannelMap.shortcuts
		if map.has_key(self.ctype):
			C = map[self.ctype]
		else:
			C = '?'
		d.centerstring(r, t, self.mother.nodetop, b, C)

	def drawline(self):
		# Draw a gray and a white vertical line
		d = self.mother.new_displist
		d.fgcolor(BORDERCOLOR)
		d.drawline(BORDERCOLOR, [(self.right, self.ycenter),
					 (self.farright, self.ycenter)])

	# Menu stuff beyond what GO offers

	def attrcall(self):
		self.mother.toplevel.setwaiting()
		import AttrEdit
		AttrEdit.showchannelattreditor(self.mother.toplevel,
					       self.channel)
		self.mother.toplevel.setready()

	def delcall(self):
		if self.channel in self.mother.usedchannels:
			windowinterface.showmessage(
				  "You can't delete a channel\n" +
				  'that is still in use',
				  mtype = 'error')
			return
		mother = self.mother
		editmgr = mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		mother.toplevel.setwaiting()
		editmgr.delchannel(self.name)
		mother.cleanup()
		editmgr.commit()
		mother.toplevel.setready()

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



class NodeBox(GO, NodeBoxCommand):

	def __init__(self, mother, node):
		import Duration
		self.node = node
		duration = Duration.get(node)
		self.pausenode = duration < 0
		self.hasanchors = self.haspause = 0
		try:
			alist = self.node.GetRawAttr('anchorlist')
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
		if not hasattr(node, 'armedmode') or node.armedmode is None:
			node.armedmode = ARM_NONE
		name = MMAttrdefs.getattr(node, 'name')
		self.locked = 0
		GO.__init__(self, mother, name)
		self.is_node_object = 1
		self.commandlist = self.commandlist + [
			PLAYNODE(callback = (self.playcall, ())),
			PLAYFROM(callback = (self.playfromcall, ())),
			PUSHFOCUS(callback = (self.focuscall, ())),
			FINISH_ARC(callback = (self.newsyncarccall, ())),
			FINISH_LINK(callback = (self.hyperlinkcall, ())),
			INFO(callback = (self.infocall, ())),
			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),
			ANCHORS(callback = (self.anchorcall, ())),
			SYNCARCS(callback = self.selsyncarc),
			]
		self.arcmenu = arcmenu = []
		for arc in MMAttrdefs.getattr(node, 'synctolist'):
			xuid, xside, delay, yside = arc
			try:
				xnode = node.MapUID(xuid)
			except NoSuchUIDError:
				# Skip sync arc from non-existing node
				continue
			if xnode.FindMiniDocument() is mother.viewroot:
				xname = MMAttrdefs.getattr(xnode, 'name')
				if not xname:
					xname = '#' + xuid
				arcmenu.append('From %s of node "%s" to %s of self' % (begend[xside], xname, begend[yside]), (xnode, xside, delay, yside))
		self.menutitle = 'Node %s ops' % self.name
		NodeBoxCommand.__init__(self, mother, node)


	def selsyncarc(self, xnode, xside, delay, yside):
		ynode = self.node
		mother = self.mother
		for arc in mother.arcs:
			if (xnode, xside, yside, ynode) == (arc.snode, arc.sside, arc.dside, arc.dnode):
				mother.toplevel.setwaiting()
				mother.init_display()
				arc.select()
				mother.drawarcs()
				mother.render()
				mother.toplevel.setready()
				return

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
## 			self.mother.drawarcs((self.left, self.top, self.right, self.bottom))
			self.mother.render()
			self.mother.delay_drawarcs()

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
		snode, sside, delay, dnode, dside, new = \
			self.mother.lockednode.node, 1, 0.0, self.node, 0, 1
##		# find a sync arc between the two nodes and use that
##		list = dnode.GetRawAttrDef('synctolist', None)
##		if list is None:
##			list = []
##		suid = snode.GetUID()
##		for (xn, xs, de, ys) in list:
##			if xn is suid:
##				sside, delay, dside, new = xs, de, ys, 0
##				break
		editmgr.addsyncarc(snode, sside, delay, dnode, dside)
		self.mother.cleanup()
		editmgr.commit()
		# NB: when we get here, this object is nearly dead already!
		import ArcInfo
		ArcInfo.showarcinfo(self.mother, root, snode, sside, delay,
				    dnode, dside, new = new)

	def select(self):
		self.unlock()
		GO.select(self)

	def reshape(self):
		# Compute ideal box coordinates
		channel = self.node.GetChannel()
		if self.pausenode:
			parent = self.node.GetParent()
			if parent is None:
				t1 = self.node.t1
			elif parent.GetType() == 'seq':
				siblings = parent.GetChildren()
				index = siblings.index(self.node)
				if len(siblings) > index+1:
					t1 = siblings[index+1].t0
				else:
					t1 = parent.t1
			else:
				t1 = parent.t1
			if t1 == self.node.t0:
				t1 = self.node.t1
		else:
			t1 = self.node.t1
		left, right = self.mother.maptimes(self.node.t0, t1)
		top, bottom = self.mother.mapchannel(channel)
		if self.node.timing_discont:
		    self.mother.discontinuities.append(
			self.node.t0+self.node.timing_discont)

		hmargin = self.mother.new_displist.strsize('x')[0] / 15
		left = left + hmargin
		right = right - hmargin

		# Move top down below the previous node if necessary
		if left < channel.lowest:
			left = channel.lowest

		# Keep space for at least one line of text
		# bottom = max(bottom, top+f_fontheight-2)
## 		if left + self.mother.new_displist.strsize('x')[0] * 1.2 > right:
## 		    right = left + self.mother.new_displist.strsize('x')[0] * 1.2
## 		    self.mother.discontinuities.append(
## 			(self.node.t0+self.node.t1)/2)

		# Update channel's lowest node
		channel.lowest = right

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
		else:
			try:
				color = armcolors[self.node.armedmode]
			except KeyError:
				color = NODECOLOR
		d.drawfbox(color, (l, t, r - l, b - t))

		# If the end time was inherited, make the bottom-right
		# triangle of the box a lighter color
		if self.node.t0t1_inherited:
			d.drawfpolygon(ALTNODECOLOR, [(r, t), (r, b), (l, b)])

		# If there are anchors on this node,
		# draw a small orange box in the top right corner
		if self.hasanchors:
			d.drawfbox(ANCHORCOLOR, (r-haboxsize, t,
						 haboxsize, vaboxsize))

		# If there is a pausing anchor,
		# draw an orange line at the right
		if self.haspause:
			d.drawfbox(ANCHORCOLOR, (r-haboxsize, t,
						 haboxsize, b-t))

		# If this is a pausing node
		# draw a small orange box in the bottom right corner
		if self.pausenode:
			d.drawfbox(ANCHORCOLOR, (r-haboxsize, b-vaboxsize,
						 haboxsize, vaboxsize))

		# Draw a "3D" border if selected, else an "engraved" outline
		if self.selected:
			d.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT,
				    FOCUSBOTTOM, (l, t, r - l, b - t))
		else:
			d.fgcolor(BORDERCOLOR)
			d.drawbox((l, t, r - l, b - t))

		# Maybe draw a thumbnail image
		if self.mother.thumbnails and \
		   r - l >= haboxsize * 6 and \
		   b - t >= vaboxsize * 9 and \
		   self.node.GetChannelType() == 'image':
			import MMurl
			try:
				f = MMurl.urlretrieve(self.node.context.findurl(MMAttrdefs.getattr(self.node, 'file')))[0]
			except IOError:
				pass
			else:
				box = d.display_image_from_file(f, center = 0, coordinates = (l, t, haboxsize * 6, vaboxsize * 9))
				l = box[0] + box[2]
				d.fgcolor((0,0,0))
				d.drawbox(box)

		# Draw the name, centered in the box
		d.fgcolor(TEXTCOLOR)
		d.centerstring(l, t, r, b, self.name)

	# Menu stuff beyond what GO offers

	def playcall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.player.playsubtree(self.node)
		top.setready()

	def playfromcall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.player.playfrom(self.node)
		top.setready()

	def attrcall(self):
		self.mother.toplevel.setwaiting()
		import AttrEdit
		AttrEdit.showattreditor(self.mother.toplevel, self.node)
		self.mother.toplevel.setready()

	def infocall(self):
		self.mother.toplevel.setwaiting()
		import NodeInfo
		NodeInfo.shownodeinfo(self.mother.toplevel, self.node)
		self.mother.toplevel.setready()

	def editcall(self):
		self.mother.toplevel.setwaiting()
		import NodeEdit
		NodeEdit.showeditor(self.node)
		self.mother.toplevel.setready()

	def anchorcall(self):
		self.mother.toplevel.setwaiting()
		import AnchorEdit
		AnchorEdit.showanchoreditor(self.mother.toplevel, self.node)
		self.mother.toplevel.setready()

	def newsyncarccall(self):
		self.mother.init_display()
		self.lock()
		self.mother.render()

	def focuscall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.hierarchyview.globalsetfocus(self.node)
		top.setready()

	def hyperlinkcall(self):
		self.mother.toplevel.links.finish_link(self.node)


class INodeBox(GO):

	def __init__(self, mother, node):
		self.node = node
		node.cv_obj = self
		name = MMAttrdefs.getattr(node, 'name')
		GO.__init__(self, mother, name)

	def getnode(self):
		return self.node

	def cleanup(self):
		del self.node.cv_obj
		GO.cleanup(self)

	def reshape(self):
		left, right = self.mother.maptimes(self.node.t0, self.node.t1)
		self.left = left
		self.right = right
		self.top = 0
		self.bottom = 0
		self.ok = 1

	def drawfocus(self):
		return


class ArcBox(GO, ArcBoxCommand):

	def __init__(self, mother, snode, sside, delay, dnode, dside):
		self.snode, self.sside, self.delay, self.dnode, self.dside = \
			snode, sside, delay, dnode, dside
		GO.__init__(self, mother, 'arc')
		self.commandlist = self.commandlist + [
			INFO(callback = (self.infocall, ())),
			DELETE(callback = (self.delcall, ())),
			]
		self.meutitle = 'Sync arc ops'
		ArcBoxCommand.__init__(self)


	def reshape(self):
		try:
			sobj = self.snode.cv_obj
			dobj = self.dnode.cv_obj
		except AttributeError:
			self.ok = 0
			return
		if self.sside: self.sx = sobj.right
		else: self.sx = sobj.left
		if self.dside: self.dx = dobj.right
		else: self.dx = dobj.left
		self.sy = (sobj.top + sobj.bottom) / 2
		self.dy = (dobj.top + dobj.bottom) / 2
		if self.sy == 0: self.sy = self.dy
		if self.dy == 0: self.dy = self.sy
		if self.sx == self.dx and self.sy == self.dy:
			# start and end of arrow are the same
			# force a difference by moving up the start
			dx = 0.0000000000001
			while self.sx == self.dx:
				dx = dx * 10
				self.sx = self.sx - dx
		self.ok = 1

	def ishit(self, x, y):
		if not self.ok: return 0
		return self.mother.window.hitarrow((x, y), (self.sx, self.sy),
						   (self.dx, self.dy))

	def drawfocus(self):
		# The entire sync arc has the focus color if selected
		if self.selected:
			color = FOCUSCOLOR
		else:
			color = ARROWCOLOR
		self.mother.new_displist.drawarrow(color, (self.sx, self.sy),
						   (self.dx, self.dy))

	# Menu stuff beyond what GO offers

	def infocall(self):
		self.mother.toplevel.setwaiting()
		import ArcInfo
		ArcInfo.showarcinfo(self.mother, self.mother.root,
				    self.snode, self.sside, self.delay,
				    self.dnode, self.dside)
		self.mother.toplevel.setready()

	def delcall(self):
		mother = self.mother
		editmgr = mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		mother.toplevel.setwaiting()
		editmgr.delsyncarc(self.snode, self.sside, \
			self.delay, self.dnode, self.dside)
		mother.cleanup()
		editmgr.commit()
		mother.toplevel.setready()

	def selnode(self, node):
		top = self.mother.toplevel
		top.setwaiting()
		self.mother.globalsetfocus(node)
		top.setready()
