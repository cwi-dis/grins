# Time chart window (for historic reasons called "Channel View")
# Beware: this module uses X11-like world coordinates:
# positive Y coordinates point down from the top of the window.
# Also the convention for box coordinates is (left, top, right, bottom)

# XXX To do:
# - remember 'locked' over commit
# - remember sync arc focus over commit
# - redraw all sync arcs whenever a node is redrawn
# - show arm colors
# - what about group nodes?  (I'd say draw a box to display them?)
# - store focus and locked node as attributes
# - improve color scheme
# - draw 3D-look boxes


from math import sin, cos, atan2, pi
import gl, GL, DEVICE
import fl
from Dialog import GLDialog
from ViewDialog import ViewDialog

from MMNode import alltypes, leaftypes, interiortypes
import MMAttrdefs
import Timing
from ArmStates import *


# Color assignments (RGB)

BGCOLOR = 200, 200, 200			# Light gray
BORDER1COLOR = 75, 75, 75		# Dark gray
BORDER2COLOR = 50, 50, 150		# Dark blueish gray
CHANNELCOLOR = 240, 240, 240		# Very light gray
NODECOLOR = 220, 220, 220		# Rather light gray
ARROWCOLOR = 0, 0, 255			# Blue
TEXTCOLOR = 0, 0, 0			# Black
FOCUSCOLOR = 255, 0, 0			# Red
LOCKEDCOLOR = 0, 255, 0			# Green
LINECOLOR = 255, 255, 255		# White

# Arm colors
armcolors = { \
	     ARM_SCHEDULED: (200, 200, 0), \
	     ARM_ARMING: (255, 255, 0), \
	     ARM_ARMED: (255, 200, 0), \
	     ARM_PLAYING: (0, 255, 0), \
	     }


# Arrowhead dimensions

ARR_LENGTH = 18.0
ARR_HALFWIDTH = 5.0
ARR_SLANT = ARR_HALFWIDTH / ARR_LENGTH


# Channel view class

class ChannelView(ViewDialog, GLDialog):

	# Initialization.
	# (Actually, most things are initialized by show().)

	def init(self, toplevel):
		self.toplevel = toplevel
		self.root = self.toplevel.root
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		self.focus = None
		self = ViewDialog.init(self, 'cview_')
		return GLDialog.init(self, 'Time chart')

	# Special interface for the Player to show armed state of nodes

	def setarmedmode(self, node, mode):
		try:
			obj = node.cv_obj
		except AttributeError:
			return # Invisible node
		obj.setarmedmode(mode)

	def unarm_all(self):
		if self.is_showing():
			self.unarm_node(self.root)

	def unarm_node(self, node):
		self.setarmedmode(node, ARM_NONE)
		for child in node.GetChildren():
			self.unarm_node(child)

	# Dialog interface (extends GLDiallog.{show,hide})

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
		pass # Nothing changed

	def commit(self):
		if self.focus is None:
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

	def mouse(self, (dev, val)):
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
		self.baseobject = None

	# Recalculate the set of objects we should be drawing

	def recalc(self, focus):
		self.objects = []
		self.focus = self.lockednode = None
		self.baseobject = GO().init(self, 'Time chart')
		self.baseobject.select()
		self.objects.append(self.baseobject)
		self.initchannels(focus)
		self.initnodes(focus)

	# Get the current window shape and set the transformation.
	# Note that the Y axis is made to point down, like X coordinates!
	# Assume we are the current window.

	def getshape(self):
		gl.reshapeviewport()
		x0, x1, y0, y1 = gl.getviewport()
		width, height = x1-x0, y1-y0
		MASK = 20
		gl.viewport(x0-MASK, x1+MASK, y0-MASK, y1+MASK)
		gl.scrmask(x0, x1, y0, y1)
		gl.ortho2(-MASK-0.5, width+MASK-0.5, \
			  height+MASK-0.5, -MASK-0.5)
		self.width, self.height = width, height
		self.channelbottom = 4 * gl.getheight()
		self.nodetop = 5 * gl.getheight()

	# Recompute the locations where the objects should be drawn

	def reshape(self):
		Timing.optcalctimes(self.root)
		for obj in self.objects:
			obj.reshape()

	# Draw the window

	def draw(self):
		gl.RGBcolor(BGCOLOR)
		gl.clear()
		for obj in self.objects:
			obj.draw()
	
	# Channel stuff

	def initchannels(self, focus):
		for name in self.context.channelnames:
			obj = ChannelBox().init(self, name)
			self.objects.append(obj)
			if focus[0] == 'c' and focus[1] == name:
				obj.select()

	# Node stuff

	def initnodes(self, focus):
		Timing.optcalctimes(self.root)
		arcs = []
		self.scantree(self.root, focus, arcs)
		self.objects[len(self.objects):] = self.arcs = arcs

	def scantree(self, node, focus, arcs):
		if node.GetType() in leaftypes:
			cname = MMAttrdefs.getattr(node, 'channel')
			if cname in self.context.channelnames:
				obj = NodeBox().init(self, node, cname)
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
			xnode = ynode.MapUID(xuid)
			if self.root.IsAncestorOf(xnode) and \
				xnode.GetType() in leaftypes and \
				MMAttrdefs.getattr(xnode, 'channel') in \
					self.context.channelnames:
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
		obj = hits[-1] # Last object (usually drawn on top)
		obj.select()

	# Global focus stuff
	def getfocus(self):
		if self.focus:
			return self.focus.getnode()
		else:
			return None

	def globalsetfocus(self, node):
		if self.is_showing():
			try:
				obj = node.cv_obj
			except:
				return
			self.setwin()
			self.deselect()
			obj.select()


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
		cname = MMAttrdefs.getattr(node, 'channel')
		nchannels = len(self.mother.context.channelnames)
		i = self.mother.context.channelnames.index(cname)
		width = self.mother.width / nchannels
		left = (i + 0.1) * width
		right = (i + 0.9) * width

		# Calculate our position in relative time
		totaltop = self.mother.nodetop
		totalbottom = self.mother.height
		totalheight = totalbottom - totaltop - gl.getheight()
		totaltime = self.mother.root.t1 - self.mother.root.t0
		if totaltime <= 0: totaltime = 1
		starttime = node.t0 - self.mother.root.t0
		stoptime  = node.t1 - self.mother.root.t0

		# Compute the 'ideal' top/bottom
		top = totaltop + (totalheight * starttime / totaltime)
		bottom = totaltop + (totalheight * stoptime / totaltime)

		# Compute top/bottom so that normally we keep a
		# 1 pixel margin above/below, but at the same time
		# set a minimal size (to fit the label in and so we can
		# be selected with the mouse)
		bottom = max(bottom-1, top+gl.getheight())
		top = top + 1

		#print top, ':', bottom, '(', margin, ')', top, ':', bottom,
		#print MMAttrdefs.getattr(node, 'name')

		return left, top, right, bottom

	# Subroutine to make the menu, the list of menuprocs, and the keymap.
	# Don't use it as a method!

	def makemenu(title, commandlist):
		menutext = title + '%t'
		menuprocs = []
		keymap = {}
		for char, text, proc in commandlist:
			keymap[char] = proc
			if text:
				menutext = menutext + '|' + char + ' ' + text
			menuprocs.append(proc)
		menu = gl.newpup()
		gl.addtopup(menu, menutext, 0)
		return menu, menuprocs, keymap

	# Methods to handle interaction events

	def popupmenu(self, x, y):
		i = gl.dopup(self.__class__.menu)
		if 0 < i <= len(self.__class__.menuprocs):
			self.__class__.menuprocs[i-1](self)

	def shortcut(self, c):
		if self.__class__.keymap.has_key(c):
			self.__class__.keymap[c](self)
		else:
			gl.ringbell()

	# Methods corresponding to the menu entries

	def helpcall(self):
		self.mother.toplevel.help.givehelp('Time_chart')

	def newchannelcall(self):
		editmgr = self.mother.editmgr
		context = self.mother.context
		if not editmgr.transaction():
			return # Not possible at this time
		i = 1
		base = 'NEW'
		name = base + `i`
		while name in self.mother.context.channelnames:
			i = i+1
			name = base + `i`
		editmgr.addchannel(name, self.newchannelindex(), 'null')
		editmgr.commit()
		# NB: when we get here, this object is nearly dead already!
		import AttrEdit
		AttrEdit.showchannelattreditor(context, name)

	def newchannelindex(self):
		return len(self.mother.context.channelnames)

	# Menu and shortcut definitions are stored as data in the class,
	# since they are the same for all objects of a class...

	commandlist = c = []
	c.append('h', 'Help...',         helpcall)
	c.append('c', 'New channel...',  newchannelcall)
	menu, menuprocs, keymap = makemenu('Base ops', commandlist)


# Class for Channel Objects

class ChannelBox(GO):

	def reshape(self):
		nchannels = len(self.mother.context.channelnames)
		i = self.mother.context.channelnames.index(self.name)
		height = self.mother.channelbottom
		width = self.mother.width / nchannels
		space = gl.strwidth(' ')
		self.left = i * width + space*0.5
		self.right = (i+1) * width - space
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
		# Draw a diamond
		gl.RGBcolor(CHANNELCOLOR)
		gl.bgnpolygon()
		gl.v2f(self.left, self.ycenter)
		gl.v2f(self.xcenter, self.top)
		gl.v2f(self.right, self.ycenter)
		gl.v2f(self.xcenter, self.bottom)
		gl.endpolygon()

		# Outline the diamond; in a different color if we are selected
		if self.selected:
			gl.RGBcolor(FOCUSCOLOR)
		else:
			gl.RGBcolor(BORDER1COLOR)
		gl.linewidth(2)
		gl.bgnclosedline()
		gl.v2f(self.left, self.ycenter)
		gl.v2f(self.xcenter, self.top)
		gl.v2f(self.right, self.ycenter)
		gl.v2f(self.xcenter, self.bottom)
		gl.endclosedline()

		# Draw the name
		gl.RGBcolor(TEXTCOLOR)
		centerstring(self.left, self.top, self.right, self.bottom, \
			     self.name)

	def drawline(self):
		# Draw a vertical line
		gl.RGBcolor(LINECOLOR)
		gl.linewidth(2)
		gl.bgnline()
		gl.v2f(self.xcenter, self.bottom)
		gl.v2f(self.xcenter, self.farbottom)
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
	menu, menuprocs, keymap = GO.makemenu('Channel ops', commandlist)


class NodeBox(GO):

	def init(self, mother, node, cname):
		self.node = node
		node.cv_obj = self
		self.cname = cname # Channel name
		name = MMAttrdefs.getattr(node, 'name')
		self.locked = 0
		self.armedmode = ARM_NONE
		return GO.init(self, mother, name)

	def getnode(self):
		return self.node

	def cleanup(self):
		del self.node.cv_obj
		GO.cleanup(self)

	def setarmedmode(self, mode):
		# print 'node', self.name, 'setarmedmode', mode
		self.armedmode = mode
		GLDialog.show(self.mother) # For winset() effect
		self.drawfocus()

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
		# Draw a box
		if armcolors.has_key(self.armedmode):
			gl.RGBcolor(armcolors[self.armedmode])
		else:
			gl.RGBcolor(NODECOLOR)
		gl.bgnpolygon()
		gl.v2f(self.left, self.top)
		gl.v2f(self.right, self.top)
		gl.v2f(self.right, self.bottom)
		gl.v2f(self.left, self.bottom)
		gl.endpolygon()

		# Outline the box; in a different color if we are selected
		if self.locked:
			gl.RGBcolor(LOCKEDCOLOR)
		elif self.selected:
			gl.RGBcolor(FOCUSCOLOR)
		elif self.node.t0t1_inherited:
			gl.RGBcolor(BORDER2COLOR)
		else:
			gl.RGBcolor(BORDER1COLOR)
		gl.linewidth(2)
		gl.bgnclosedline()
		gl.v2f(self.left, self.top)
		gl.v2f(self.right, self.top)
		gl.v2f(self.right, self.bottom)
		gl.v2f(self.left, self.bottom)
		gl.endclosedline()

		# Draw the name
		gl.RGBcolor(TEXTCOLOR)
		centerstring(self.left, self.top, self.right, self.bottom, \
			     self.name)

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
		editmgr.commit()
		# NB: when we get here, this object is nearly dead already!
		import ArcInfo
		ArcInfo.showarcinfo(root, snode, sside, delay, dnode, dsize)

	commandlist = c = GO.commandlist[:]
	char, text, proc = c[-1]
	c[-1] = char, text + '%l', proc
	c.append('p', 'Play node...', playcall)
	c.append('i', 'Node info...', infocall)
	c.append('a', 'Node attr...', attrcall)
	c.append('t', 'Anchor edit...', anchorcall)
	c.append('e', 'Edit contents...%l', editcall)
	c.append('l', 'Lock node', lockcall)
	c.append('u', 'Unlock node', unlockcall)
	c.append('s', 'New sync arc...', newsyncarccall)
	menu, menuprocs, keymap = GO.makemenu('Node ops', commandlist)


class ArcBox(GO):

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
		editmgr.commit()

	commandlist = c = GO.commandlist[:]
	char, text, proc = c[-1]
	c[-1] = char, text + '%l', proc
	c.append('i', 'Sync arc info...', infocall)
	c.append('d', 'Delete sync arc',  delcall)
	menu, menuprocs, keymap = \
		GO.makemenu('Sync arc ops', commandlist)

	


# Subroutine to draw a string centered at a given point

def centerstring(left, top, right, bottom, str):
	x = (left + right) * 0.5
	y = (top + bottom) * 0.5
	width = right - left
	# Get font parameters:
	d = gl.getdescender() # Max descender size
	h = gl.getheight()    # Line height
	w = gl.strwidth(str)  # Width of string
	while str and w > width:
		str = str[:-1]
		w = gl.strwidth(str)
	gl.cmov2(x-w*0.5, y+h*0.5-d)
	gl.charstr(str)
