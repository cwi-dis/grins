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


from math import sin, cos, atan2, pi
import gl, GL, DEVICE
import fl
import FontStuff
import MenuMaker
from Dialog import GLDialog
from ViewDialog import ViewDialog

from MMNode import alltypes, leaftypes, interiortypes
import MMAttrdefs
import Timing
from ArmStates import *
from MMExc import *
from AnchorDefs import *


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
		title = 'Channel View (' + self.toplevel.basename + ')'
		self = ViewDialog.init(self, 'cview_')
		return GLDialog.init(self, title)

	def __repr__(self):
		return '<ChannelView instance, root=' + `self.root` + '>'

	# Special interface for the Player to show armed state of nodes

##	def setarmedmode(self, node, mode):
##		try:
##			obj = node.cv_obj
##		except AttributeError:
##			return # Invisible node
##		obj.setarmedmode(mode)
##		self.drawarcs()
##
##	def unarm_all(self):
##		if self.is_showing():
##			for obj in self.objects:
##				obj.resetarmedmode()
##			self.setwin()
##			self.draw()

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
		self.recalc(('b', None))
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
			focus = 'c', self.focus.name
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

	# Clear the list of objects we know

	def cleanup(self):
		self.focus = self.lockednode = None
		for obj in self.objects:
			obj.cleanup()
		self.objects = []
		self.arcs = []
		self.baseobject = None

	# Recalculate the set of objects we should be drawing

	def recalc(self, focus):
		self.objects = []
		self.focus = self.lockednode = None
		self.baseobject = GO().init(self, '(base)')
		self.baseobject.select()
		self.objects.append(self.baseobject)
		self.initchannels(focus)
		self.initnodes(focus)

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

	# Recompute the locations where the objects should be drawn

	def reshape(self):
		Timing.needtimes(self.viewroot)
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
		for name in self.context.channelnames:
			obj = ChannelBox().init(self, name)
			self.objects.append(obj)
			if focus[0] == 'c' and focus[1] == name:
				obj.select()

	# View root stuff

	def nextviewroot(self):
		node = self.viewroot.NextMiniDocument()
		if node == None:
			node = self.root.FirstMiniDocument()
		self.setviewroot(node)

	def prevviewroot(self):
		node = self.viewroot.PrevMiniDocument()
		if node == None:
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
		self.fixtitle()
		self.recalc(('b', None))
		self.setwin()
		self.reshape()
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
		arcs = []
		self.scantree(self.viewroot, focus, arcs)
		self.objects[len(self.objects):] = self.arcs = arcs

	def scantree(self, node, focus, arcs):
		if node.GetType() in leaftypes:
			channel = node.GetChannel()
			if channel:
				obj = NodeBox().init(self, node, channel.name)
				self.objects.append(obj)
				if focus[0] == 'n' and focus[1] is node:
					obj.select()
				self.addarcs(node, arcs)
		else:
			for c in node.GetChildren():
				self.scantree(c, focus, arcs)

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
		if not self.is_showing():
			return
		# May have to switch view root
		mini = node
		while not mini.IsMiniDocument():
			mini = mini.GetParent()
			if mini == None:
				return
		self.setviewroot(mini) # No-op if already there
		try:
			obj = node.cv_obj
		except:
			return
		self.setwin()
		self.deselect()
		obj.select()
		self.drawarcs()


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
		return None

	def cleanup(self):
		# Called just before forgetting the object
		self.mother = None

	def reshape(self):
		# Recompute the size and location
		self.ok = 1

	def draw(self):
		# Draw everything
		self.drawfocus()

	def drawfocus(self):
		# Draw the part that changes when the focus changes
		pass

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

	# Subroutine used by ArcBox and NodeBox to calculate a node's position

	def nodebox(self, node):
		# Compute the left/right sides from the channel position
		channel = node.GetChannel()
		nchannels = len(self.mother.context.channels)
		i = self.mother.context.channels.index(channel)
		width = self.mother.width / nchannels
		left = (i + 0.1) * width
		right = (i + 0.9) * width

		# Calculate our position in relative time
		totaltop = self.mother.nodetop
		totalbottom = self.mother.height
		totalheight = totalbottom - totaltop - f_fontheight
		totaltime = self.mother.viewroot.t1 - self.mother.viewroot.t0
		if totaltime <= 0: totaltime = 1
		starttime = node.t0 - self.mother.viewroot.t0
		stoptime  = node.t1 - self.mother.viewroot.t0

		# Compute the 'ideal' top/bottom
		top = totaltop + (totalheight * starttime / totaltime)
		bottom = totaltop + (totalheight * stoptime / totaltime)

		# Compute top/bottom so that normally we keep a
		# 1 pixel margin above/below, but at the same time
		# set a minimal size (to fit the label in and so we can
		# be selected with the mouse)
		bottom = max(bottom-1, top+f_fontheight)
		top = top + 1

		#print top, ':', bottom, '(', margin, ')', top, ':', bottom,
		#print MMAttrdefs.getattr(node, 'name')

		return int(left), int(top), int(right), int(bottom)

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
		editmgr = self.mother.editmgr
		context = self.mother.context
		if not editmgr.transaction():
			return # Not possible at this time
		import multchoice
		from ChannelMap import channeltypes
		prompt = 'Channel type:'
		list = channeltypes[:]
		list.append('Cancel')
		default = list.index('text')
		i = multchoice.multchoice(prompt, list, default)
		if i+1 >= len(list):
			editmgr.rollback()
			return # User doesn't want to choose a type
		type = list[i]
		i = 1
		base = 'NEW'
		name = base + `i`
		while name in self.mother.context.channelnames:
			i = i+1
			name = base + `i`
		editmgr.addchannel(name, self.newchannelindex(), type)
		self.mother.future_focus = 'c', name
		self.mother.cleanup()
		editmgr.commit()
		# NB: when we get here, this object is nearly dead already!
		import AttrEdit
		AttrEdit.showchannelattreditor(context, name)

	def nextminicall(self):
		self.mother.nextviewroot()

	def prevminicall(self):
		self.mother.prevviewroot()

	def newchannelindex(self):
		return len(self.mother.context.channelnames)

	# Menu and shortcut definitions are stored as data in the class,
	# since they are the same for all objects of a class...

	commandlist = c = []
	c.append('h', 'Help...',         helpcall)
	c.append('c', 'New channel...',  newchannelcall)
	c.append('N', 'Next mini-document', nextminicall)
	c.append('P', 'Previous mini-document', prevminicall)
	menu = MenuMaker.MenuObject().init('Base ops', commandlist)


# Class for Channel Objects

class ChannelBox(GO):

	def init(self, mother, name):
		self = GO.init(self, mother, name)
		self.ctype = '???'
		cdict = self.mother.context.channeldict
		if cdict.has_key(name):
			cattrs = cdict[name]
			if cattrs.has_key('type'):
				self.ctype = cattrs['type']
		return self

	def __repr__(self):
		return '<ChannelBox instance, name=' + `self.name` + '>'

	def reshape(self):
		nchannels = len(self.mother.context.channelnames)
		i = self.mother.context.channelnames.index(self.name)
		height = self.mother.channelbottom
		width = self.mother.width / nchannels
		space = gl.strwidth(' ')
		self.left = int(i * width + space*0.5)
		self.right = int((i+1) * width - space)
		self.top = 0
		self.bottom = height
		self.xcenter = (self.left + self.right) / 2
		self.ycenter = (self.top + self.bottom) / 2
		self.farbottom = self.mother.height
		self.ok = 1

	def ishit(self, x, y):
		return self.left <= x <= self.right and \
		       self.top <= y <= self.bottom

	def draw(self):
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
		gl.v2i(l, y)
		gl.v2i(x, t)
		gl.v2i(r, y)
		gl.v2i(x, b)
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
			gl.v2i(l, y)
			gl.v2i(x, t)
			gl.v2i(x, tt)
			gl.v2i(ll, y)
			gl.endpolygon()

			gl.RGBcolor(FOCUSTOP)
			gl.bgnpolygon()
			gl.v2i(x, t)
			gl.v2i(r, y)
			gl.v2i(rr, y)
			gl.v2i(x, tt)
			gl.endpolygon()

			gl.RGBcolor(FOCUSRIGHT)
			gl.bgnpolygon()
			gl.v2i(r, y)
			gl.v2i(x, b)
			gl.v2i(x, bb)
			gl.v2i(rr, y)
			gl.endpolygon()

			gl.RGBcolor(FOCUSBOTTOM)
			gl.bgnpolygon()
			gl.v2i(l, y)
			gl.v2i(ll, y)
			gl.v2i(x, bb)
			gl.v2i(x, b)
			gl.endpolygon()

			gl.RGBcolor(FOCUSBORDER)
			gl.linewidth(1)
			gl.bgnclosedline()
			gl.v2i(l, y)
			gl.v2i(x, t)
			gl.v2i(r, y)
			gl.v2i(x, b)
			gl.endclosedline()
		else:
			gl.linewidth(1)
			gl.RGBcolor(BORDERCOLOR)
			gl.bgnclosedline()
			gl.v2i(l, y)
			gl.v2i(x, t)
			gl.v2i(r, y)
			gl.v2i(x, b)
			gl.endclosedline()

			gl.RGBcolor(BORDERLIGHT)
			gl.bgnclosedline()
			gl.v2i(l+1, y+1)
			gl.v2i(x+1, t+1)
			gl.v2i(r+1, y+1)
			gl.v2i(x+1, b+1)
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
		gl.v2i(self.xcenter, self.bottom)
		gl.v2i(self.xcenter, self.farbottom)
		gl.endline()
		gl.RGBcolor(BORDERLIGHT)
		gl.bgnline()
		gl.v2i(self.xcenter+1, self.bottom)
		gl.v2i(self.xcenter+1 , self.farbottom)
		gl.endline()

	# Menu stuff beyond what GO offers

	def attrcall(self):
		import AttrEdit
		AttrEdit.showchannelattreditor(self.mother.context, self.name)

	def delcall(self):
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
	menu = MenuMaker.MenuObject().init('Channel ops', commandlist)


class NodeBox(GO):

	def __repr__(self):
		return '<NodeBox instance, name=' + `self.name` + '>'

	def init(self, mother, node, cname):
		self.node = node
		self.hasanchors = self.haspause = 0
		try:
			alist = self.node.GetRawAttr('anchorlist')
		except NoSuchAttrError:
			alist = None
		if alist: # Not None and not []
			self.hasanchors = 1
			for a in alist:
				if a[A_TYPE] == ATYPE_PAUSE:
					self.haspause = 1
					break
		node.cv_obj = self
		node.setarmedmode = self.setarmedmode
		if node.armedmode == None:
			node.armedmode = ARM_NONE
		self.cname = cname # Channel name
		name = MMAttrdefs.getattr(node, 'name')
		self.locked = 0
		return GO.init(self, mother, name)

	def getnode(self):
		return self.node

	def cleanup(self):
		del self.node.cv_obj
		self.node.setarmedmode = self.node.setarmedmode_dummy
		GO.cleanup(self)

	def setarmedmode(self, mode):
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
		self.left, self.top, self.right, self.bottom = \
			self.nodebox(self.node)
		self.ok = 1

	def ishit(self, x, y):
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
		gl.v2i(l, t)
		gl.v2i(r, t)
		gl.v2i(r, b)
		gl.v2i(l, b)
		gl.endpolygon()

		# If the end time was inherited, make the bottom-right
		# triangle of the box a lighter color
		if self.node.t0t1_inherited:
			gl.RGBcolor(ALTNODECOLOR)
			gl.bgnpolygon()
			gl.v2i(r, t)
			gl.v2i(r, b)
			gl.v2i(l, b)
			gl.endpolygon()

		# If there are anchors on this node,
		# draw a small orange box in the bottom left corner
		if self.hasanchors:
			gl.RGBcolor(ANCHORCOLOR)
			gl.bgnpolygon()
			gl.v2i(l, b)
			gl.v2i(l+ABOXSIZE, b)
			gl.v2i(l+ABOXSIZE, b-ABOXSIZE)
			gl.v2i(l, b-ABOXSIZE)
			gl.endpolygon()

		# If there is a pausing anchor,
		# draw an orange line at the bottom
		if self.haspause:
			gl.RGBcolor(ANCHORCOLOR)
			gl.bgnpolygon()
			gl.v2i(l, b)
			gl.v2i(r, b)
			gl.v2i(r, b-ABOXSIZE)
			gl.v2i(l, b-ABOXSIZE)
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

		# Draw the name, centered in the box
		gl.RGBcolor(TEXTCOLOR)
		f_title.centerstring(l, t, r, b, self.name)

	# Menu stuff beyond what GO offers

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

	commandlist = c = GO.commandlist[:]
	char, text, proc = c[-1]
	c[-1] = char, text + '%l', proc
	c.append('p', 'Play node...', playcall)
	c.append('i', 'Node info...', infocall)
	c.append('a', 'Node attr...', attrcall)
	c.append('e', 'Edit contents...', editcall)
	c.append('t', 'Edit anchors...%l', anchorcall)
	c.append('f', 'Push focus', focuscall)
	c.append('l', 'Lock node', lockcall)
	c.append('u', 'Unlock node', unlockcall)
	c.append('s', 'New sync arc...', newsyncarccall)
	menu = MenuMaker.MenuObject().init('Node ops', commandlist)


class ArcBox(GO):

	def __repr__(self):
		return '<ArcBox instance, name=' + `self.name` + '>'

	def init(self, mother, snode, sside, delay, dnode, dside):
		self.snode, self.sside, self.delay, self.dnode, self.dside = \
			snode, sside, delay, dnode, dside
		return GO.init(self, mother, 'arc')

	def reshape(self):
		sbox = self.nodebox(self.snode)
		dbox = self.nodebox(self.dnode)
		if self.sside: self.sy = sbox[3]
		else: self.sy = sbox[1]
		if self.dside: self.dy = dbox[3]
		else: self.dy = dbox[1]
		self.sx = (sbox[0] + sbox[2]) / 2
		self.dx = (dbox[0] + dbox[2]) / 2
		#
		lx = self.dx - self.sx
		ly = self.dy - self.sy
		angle = atan2(lx, ly)
		# print 'lx =', lx, 'ly =', ly, 'angle =', angle
		self.cos = cos(angle)
		self.sin = sin(angle)
		self.rotation = 270 - angle * 180.0 / pi
		self.ok = 1

	def ishit(self, x, y):
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
		gl.v2i(self.sx, self.sy)
		gl.v2i(self.dx, self.dy)
		gl.endline()
		# Draw the arrowhead
		# Translate so that the point of the arrowhead is (0, 0)
		# Rotate so that it comes in horizontally from the right
		gl.pushmatrix()
		gl.translate(self.dx, self.dy, 0)
		gl.rot(self.rotation, 'z')
		gl.bgnpolygon()
		gl.v2i(0, 0)
		gl.v2i(ARR_LENGTH, ARR_HALFWIDTH)
		gl.v2i(ARR_LENGTH, -ARR_HALFWIDTH)
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
	menu = MenuMaker.MenuObject().init('Sync arc ops', commandlist)
