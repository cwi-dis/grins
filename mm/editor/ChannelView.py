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

import MMAttrdefs
import Timing
from MMExc import *
from AnchorDefs import *
from ArmStates import *
from MMTypes import *
import os
import Bandwidth


def fix(r, g, b): return r, g, b	# Hook for color conversions


# Color assignments (RGB)

BGCOLOR = fix(200, 200, 200)		# Light gray
BORDERCOLOR = fix(75, 75, 75)		# Dark gray
BORDERLIGHT = fix(255, 255, 255)	# White
CHANNELCOLOR = fix(240, 240, 240)	# Very light gray
CHANNELOFFCOLOR = fix(160, 160, 160)	# Darker gray
NODECOLOR = fix(208, 182, 160)		# Pale pinkish, match hierarchy view
ALTNODECOLOR = fix(255, 224, 200)	# Same but brighter
NODEOFFCOLOR = CHANNELOFFCOLOR
ALTNODEOFFCOLOR = BGCOLOR
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
ARMACTIVECOLOR = (255, 255, 0)
ARMINACTIVECOLOR = (255, 200, 0)
ARMERRORCOLOR = (255, 0, 0)
PLAYACTIVECOLOR = (0, 255, 0)
PLAYINACTIVECOLOR = (0, 127, 0)
PLAYERRORCOLOR = (255, 0, 0)

armcolors = { \
	     ARM_SCHEDULED: (200, 200, 0), \
	     ARM_ARMING: ARMACTIVECOLOR, \
	     ARM_ARMED: ARMINACTIVECOLOR, \
	     ARM_PLAYING: PLAYACTIVECOLOR, \
	     ARM_WAITSTOP: PLAYINACTIVECOLOR, \
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
		self.last_geometry = None
		self.toplevel = toplevel
		self.root = toplevel.root
		self.viewroot = None
		self.context = self.root.context
		self.editmgr = self.context.editmgr
		self.focus = None
		self.future_focus = None
		self.showall = 1
		self.showarcs = 1
		self.placing_channel = 0
		self.thumbnails = 0
		self.showbandwidthstrip = 0
		self.layouts = [('All channels', ())]
		for name in self.context.layouts.keys():
			self.layouts.append((name, (name,)))
		self.curlayout = None
		title = 'Timeline View (' + self.toplevel.basename + ')'
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')
		ChannelViewDialog.__init__(self)
		self.delayed_drawarcs_id = None

	def __repr__(self):
		return '<ChannelView instance, root=' + `self.root` + '>'

	# Dialog interface

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Timeline View (' + self.toplevel.basename + ')'
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
		self.setpopup(obj.popupmenu)

	def hide(self, *rest):
		if not self.is_showing():
			return
		self.toplevel.showstate(self, 0)
		ChannelViewDialog.hide(self)
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

	# Edit manager interface (as dependent client)

	def transaction(self):
		return 1 # It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self):
		self.layouts = [('All channels', ())]
		for name in self.context.layouts.keys():
			self.layouts.append((name, (name,)))
		if self.curlayout is not None and \
		   not self.context.layouts.has_key(self.curlayout):
			self.curlayout = None
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
			focus = 'a', self.focus.arcid
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
			focus = 'a', self.focus.arcid
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

	def layoutcall(self, name = None):
		curlayout = self.curlayout
		self.curlayout = name
		if curlayout != name:
			self.resize()

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

	# Time-related subroutines

	def timerange(self):
		# Return the range of times used in the window
		v = self.viewroot
		t0, t1 = v.t0 - self.prerolltime, v.t1
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

	def mapchannel(self, channel, line = 0):
		# Map channel to left and right coordinates
		if channel.chview_map is not None:
			x, y, height = channel.chview_map
			return x + line*height, y + line*height
		list = self.visiblechannels()
		channellines = self.channellines
		nlines = 0
		i = None
		for ch in list:
			if channel is ch:
				i = nlines
			nlines = nlines + (channellines.get(ch.name, 0) or 1)
		if i is None:
			# channel not visible
			return 0, 0
# original code: all channels and extra lines at same distance from each other
##		height = float(self.bandwidthstripborder) / nlines
##		x, y = (i + 0.1) * height, (i + 0.9) * height
##		channel.chview_map = x, y, height
##		return x + line*height, y + line*height
# new code: extra lines closer together
		nchannels = len(list)
		nextras = nlines - nchannels
		dist = float(self.bandwidthstripborder) / (nchannels + 0.9 * nextras)
		height = 0.8 * dist
		ldist = 0.9 * dist
		x = 0.1 * dist
		for ch in list:
			if channel is ch:
				y = x + height
				channel.chview_map = x, y, ldist
				return x + line * ldist, y + line * ldist
			n = channellines.get(ch.name, 0) or 1
			x = x + (n - 1) * ldist + dist

	def channelgapindex(self, y):
		list = self.visiblechannels()
		nchannels = len(list)
		if nchannels == 0:
		    return 0
		height = float(self.bandwidthstripborder) / nchannels
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
		self.toplevel.setwaiting()
		self.showall = (not self.showall)
		for c in self.context.channels:
			c.chview_map = None
		self.settoggle(TOGGLE_UNUSED, self.showall)
		self.redraw()

	def togglearcs(self):
		self.toplevel.setwaiting()
		self.showarcs = not self.showarcs
		self.settoggle(TOGGLE_ARCS, self.showarcs)
		self.arcs = []
		self.resize()
		
	def togglebwstrip(self):
		self.toplevel.setwaiting()
		self.showbandwidthstrip = not self.showbandwidthstrip
		self.settoggle(TOGGLE_BWSTRIP, self.showbandwidthstrip)
		self.resize()

	# Return list of currently visible channels

	def visiblechannels(self):
		layout = {}
		for ch in self.context.layouts.get(self.curlayout, self.context.channels):
			layout[ch.name] = 0
		if self.showall:
			channels = self.context.channels
		else:
			channels = self.usedchannels
		ret = []
		for ch in channels:
			if layout.has_key(ch.name):
				ret.append(ch)
		return ret

	# Recalculate the set of objects we should be drawing

	def recalc(self, focus):
		displist = self.window.newdisplaylist(BGCOLOR)
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = displist
		bl, fh, ps = displist.usefont(f_title)
		self.channelright = displist.strsize('999999')[0]
		self.nodetop = min(self.channelright * 2, self.channelright + .05)
		self.timescaleborder = 1.0 - 4 * fh
		if self.showbandwidthstrip:
			# Wild guess: make bandwidth strip 5 textlines high, but at most
			# 15% of the window
			stripheight = 5 * fh
##			print 'DBG', stripheight
			if stripheight > 0.15:
				stripheight = 0.15
			self.bandwidthstripborder = self.timescaleborder - stripheight
		else:
			self.bandwidthstripborder = self.timescaleborder

		self.objects = []
		self.channelnodes = {}
		self.focus = self.lockednode = None
		self.baseobject = BaseBox(self, '(base)')
		self.objects.append(self.baseobject)
		self.timescaleobject = TimeScaleBox(self)
		self.objects.append(self.timescaleobject)
		if self.showbandwidthstrip:
			self.bwstripobject = BandwidthStripBox(self)
			self.objects.append(self.bwstripobject)
		else:
			self.bwstripobject = None
		self.initchannels(focus)
		self.initnodes(focus)
		self.initarcs(focus)
		self.initbwstrip()

		# enable Next and Prev Minidoc commands if there are minidocs
		if self.baseobject.descendants or \
		   self.baseobject.ancestors or \
		   self.baseobject.siblings:
			for obj in self.objects:
				obj.commandlist = obj.commandlist + [
					NEXT_MINIDOC(callback = (obj.nextminicall, ())),
					PREV_MINIDOC(callback = (obj.prevminicall, ())),
					]

		focus = self.focus
		self.baseobject.select()
		if focus is not None:
			focus.select()

	# Recompute the locations where the objects should be drawn

	def calculatechannellines(self):
		channels = {}
		for o in self.objects:
			if o.__class__ is not NodeBox:
				continue
			ch = o.node.attrdict.get('channel')
			if ch is None: continue
			if not channels.has_key(ch): channels[ch] = []
			channels[ch].append(o)
		for list in channels.values():
			list.sort(nodesort)
		for ch, list in channels.items():
			x = []
			for o in list:
				for i in range(len(x)):
					if o.node.t0 >= x[i]:
						x[i] = o.node.t1
						o.channelline = i
						break
				else:
					o.channelline = len(x)
					x.append(o.node.t1)
			channels[ch] = len(x)
		self.channellines = channels

	def reshape(self):
	        self.discontinuities = []
		Timing.needtimes(self.viewroot)
		self.calculatechannellines()
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

	def setviewrootcb(self, node):
		self.toplevel.setwaiting()
		self.setviewroot(node)

	def fixtitle(self):
		title = 'Timeline View (' + self.toplevel.basename + ')'
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
				c.chview_map = 0, 0, 0
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
				if (focus[0] == 'n' and focus[1] is node) or \
				   (focus[0] == 'a' and focus[1][3] is node):
					obj.select()
				if self.showbandwidthstrip:
					# Remember channel->node mapping
					# for prearm order
					if self.channelnodes.has_key(channel):
						self.channelnodes[channel].append(obj)
					else:
						self.channelnodes[channel] = [obj]
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
		if not self.showarcs:
			return
		arcs = []
		self.scanarcs(self.viewroot, focus, arcs)
		self.objects[len(self.objects):] = self.arcs = arcs

	def scanarcs(self, node, focus, arcs):
		type = node.GetType()
		if type in leaftypes and node.GetChannel():
			self.addarcs(node, arcs, focus)
		elif type not in bagtypes:
			for c in node.GetChildren():
				self.scanarcs(c, focus, arcs)

	def addarcs(self, ynode, arcs, focus):
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
				if focus[0] == 'a' and \
				   focus[1] == (xnode, xside, delay, ynode, yside):
					obj.select()

	# Bandwidth strip stuff

	def initbwstrip(self):
		# clear all bandwidth box pointers
		for obj in self.objects:
			obj.bandwidthboxes = []
		self.prerolltime = 0

		if not self.bwstripobject:
			return
		# For each channel replace the nodelist by a list
		# with nodes and timing info. We don't need the channel
		# identity anymore, so store the result in a list of lists
		nodematrix = []
		for nodelist in self.channelnodes.values():
			newnodelist = []
			for node in nodelist:
				bwdata = node.getbandwidthdata()
				if not bwdata:
					continue
				newnodelist.append(bwdata)
			nodematrix.append(newnodelist)
		# loop over nodes and create continuous media bandwidth boxes
		for nodelist in nodematrix:
			for info in nodelist:
				t0, t1, node, prearm, bandwidth = info
				bwbox = self.bwstripobject.bwbox(
					t0, t1, bandwidth, node)
				node.bandwidthboxes = node.bandwidthboxes + \
						      bwbox
		# Compute initial prearm time (prearms that have t0==0)
		prerolltime = 0
		maxbandwidth = self.bwstripobject.getbandwidth()
		for nodelist in nodematrix:
			for node in nodelist:
				t0, t1, node, prearm, bandwidth = node
				if t0 != 0:
					break
				prerolltime = prerolltime + \
					      (float(prearm)/maxbandwidth)
##				if prearm: print 'PREROLL', t0, t1, node, prearm, bandwidth, prerolltime #DBG
		# Adjust timebar
		self.prerolltime = prerolltime
		# And the rest of the prearms
		prearmlist = []
		for nodelist in nodematrix:
			t_arm = -self.prerolltime
			for info in nodelist:
				t0, t1, node, prearm, bandwidth = info
				prearmlist.append(t_arm, t0, prearm, node)
				t_arm = t0
		prearmlist.sort()
		for t_arm, t0, prearm, node in prearmlist:
			pabox = self.bwstripobject.pabox(t_arm, t0, prearm, node)
##			print 'PREARM', t_arm, t0, prearm, '->', pabox
			node.bandwidthboxes = node.bandwidthboxes + pabox
		
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
			if obj.is_bandwidth_strip:
			    # The bandwidth strip wants x,y
			    obj.select(x, y)
			else:
			    obj.select()
			self.drawarcs()
		self.render()
		if self.focus:
			obj = self.focus
		else:
			obj = self.baseobject
		self.setcommands(obj.commandlist, title = obj.menutitle)
		self.setpopup(obj.popupmenu)

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
	def newchannel(self, index, chtype = None):
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
		if chtype is not None:
			if chtype not in commonchanneltypes + otherchanneltypes:
				windowinterface.showmessage(
					'Unknown channel type in newchannel',
					mtype = 'error')
				return
			self.select_cb(chtype)
			return
		prompt = 'Select channel type, then place channel:'
		list = []
		import ChannelMap
		for name in ChannelMap.getvalidchanneltypes():
			list.append(name, (self.select_cb, (name,)))
		list.append(None)
		list.append('Cancel')
		windowinterface.Dialog(list, title = 'Select', prompt = prompt, grab = 1, vertical = 1, parent = self.window)

	def select_cb(self, name):
		self.placing_channel = PLACING_NEW
		self.placing_type = name
		self.finish_channel(1.0, 1.0)
## 		windowinterface.setcursor('stop')
## 		self.window.setcursor('channel')

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
		self.window.setcursor('')
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
		    if self.curlayout and self.context.layouts.has_key(self.curlayout):
			layoutchannels = self.context.layouts[self.curlayout]
			layoutchannels.append(self.context.channeldict[name])
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
		self.is_bandwidth_strip = 0
		self.bandwidthboxes = []

		# Submenus listing related mini-documents

		self.ancestors = []
		self.descendants = []
		self.siblings = []
		self.arcmenu = []

		# Menu and shortcut definitions are stored as data in
		# the class

		self.menutitle = 'Base ops'
		self.commandlist = [
			CLOSE_WINDOW(callback = (mother.hide, ())),
			CANVAS_HEIGHT(callback = (self.canvascall,
					(windowinterface.DOUBLE_HEIGHT,))),
			CANVAS_WIDTH(callback = (self.canvascall,
					(windowinterface.DOUBLE_WIDTH,))),
			CANVAS_RESET(callback = (self.canvascall,
					(windowinterface.RESET_CANVAS,))),
			NEW_CHANNEL(callback = (self.newchannelcall, ())),
			ANCESTORS(callback = mother.setviewrootcb),
			SIBLINGS(callback = mother.setviewrootcb),
			DESCENDANTS(callback = mother.setviewrootcb),
			TOGGLE_UNUSED(callback = (mother.toggleshow, ())),
			THUMBNAIL(callback = (mother.thumbnailcall, ())),
			TOGGLE_ARCS(callback = (mother.togglearcs, ())),
			LAYOUTS(callback = mother.layoutcall),
			TOGGLE_BWSTRIP(callback = (mother.togglebwstrip, ())),
			]
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
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
		self.mother.setpopup(self.popupmenu)
		if self.ok:
			self.drawfocus()
		if self.mother.bwstripobject:
			self.mother.bwstripobject.setstripfocus(self.bandwidthboxes)

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
			mother.setpopup(baseobject.popupmenu)
			self.drawfocus()
		if self.mother.bwstripobject:
			self.mother.bwstripobject.setstripfocus([])

	def ishit(self, x, y):
		# Check whether the given mouse coordinates are in this object
		return 0

	# Methods corresponding to the menu entries

## 	def helpcall(self):
## 		import Help
## 		Help.givehelp('Channel_view')

	def canvascall(self, code):
		self.mother.canvascall(code)

	def newchannelcall(self, chtype = None):
		self.mother.newchannel(self.newchannelindex(), chtype)

	def nextminicall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.nextviewroot()

	def prevminicall(self):
		mother = self.mother
		mother.toplevel.setwaiting()
		mother.prevviewroot()

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
		if t0 < 0:	# Don't draw over preroll time
			t0 = 0
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
		if t0 < 0:
			t0 = 0
		dt = t1 - t0
		# Compute the number of ticks. Don't put them too close
		# together.
		tickstep = 1
		while 1:
			n = int(ceil(dt/tickstep))
			if n*f_width < width:
				break
			tickstep = tickstep * 10
		# Compute distance between numeric indicators
		div = 1
		i = 0
		maxlabelsize = len(str(ceil(dt)))
		while (n/div) * (maxlabelsize+0.5) * f_width >= width:
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
			it0 = t0 + i*tickstep
			it1 = it0 + (tickstep*0.5)
			l, r = self.mother.maptimes(it0, it1)
			l = max(l, self.left)
			r = min(r, self.right)
			if r <= l:
				continue
			d.drawfbox(BORDERCOLOR, (l, t, r - l, b - t))
			if i%div <> 0:
				continue
			d.centerstring(l-f_width*3, b,
				       l+f_width*3, self.bottom,
				       `i*tickstep`)
		for i in self.mother.discontinuities:
		        l, r = self.mother.maptimes(i, i)
			d.drawline(ANCHORCOLOR, [(l, t), (l, b)])

class BandwidthAccumulator:
	# Accumulated used bandwidth. The datastructure used is a
	# list of (starttime, bandwidth) tuples, sorted by _reverse_
	# starttime.
	#
	
	def __init__(self, max):
		self.max = max
		self.used = [(0, 0)]

	def _findslot(self, t0):
		"""Find the slot in which t0 falls"""
##		if t0 < 0:
##			raise 'Illegal t0', t0
		#
		# Search through the slots (ordered backward) until we
		# find the one in which t0 lies.
		#
		for i in range(len(self.used)):
			if self.used[i][0] <= t0:
				break
		else:
			self.used.append((t0, 0))
			return len(self.used)-1
		return i

	def _find(self, t0, t1):
		"""Create a slot from t0 to t1, or possibly shorter,
		return the slot index and the new t1"""
		i = self._findslot(t0)
		t_i, bandwidth = self.used[i]
		# If the slot doesn't start exactly at t0 we split it
		# in two.
		if t_i < t0:
			self.used[i:i] = [(t0, bandwidth)]
		# Next, if the end time doesn't fit lower it. The higher
		# layers will handle the trailing end by iterating.
		if i > 0 and t1 > self.used[i-1][0]:
			t1 = self.used[i-1][0]
		# Finally, if the slot continues after t1 we create a new
		# slot.
		if i == 0 or t1 < self.used[i-1][0]:
			self.used[i:i] = [(t1, bandwidth)]
			i = i + 1
		# Now slot i points to the (new) t0,t1 range.
		return i, t1
		
	def _findavailbw(self, t0):
		"""Return the available bandwidth at t0 and the time
		t1 at which that value may change"""
		i = self._findslot(t0)
		bw = self.max - self.used[i][1]
		if bw < 0:
			bw = 0
		if i == 0:
			t1 = None
		else:
			t1 = self.used[i-1][0]
		return bw, t1

	def reserve(self, t0, t1, bandwidth, bwtype=1):
		boxes = []
		while 1:
			i, cur_t1 = self._find(t0, t1)
			t0_0, oldbw = self.used[i]
			if bwtype <= 1 and bandwidth > self.max:
				curbwtype = bwtype + 2
			else:
				curbwtype = bwtype
			boxes.append((t0, cur_t1, oldbw, oldbw+bandwidth,
				      curbwtype))
			self.used[i] = (t0, oldbw+bandwidth)
			t0 = cur_t1
			if t0 >= t1:
				break
		return boxes

	def prearmreserve(self, t0, t1, size):
		# First pass: see whether we can do it. For each "slot"
		# we check the available bandwidth and see whether there
		# is enough before t1 passes
		size = float(size)
		sizetmp = size
		tcur = tnext = t0
		overall_t0 = overall_t1 = None
		while sizetmp > 0 and tnext < t1:
			availbw, tnext = self._findavailbw(tcur)
			if tnext > t1:
				tnext = t1
			size_in_slot = availbw*(tnext-tcur)
			if size_in_slot > 0:
				sizetmp = sizetmp - size_in_slot
			tcur = tnext
		if sizetmp > 0:
			# It didn't fit. We reserve continuous bandwidth
			# so the picture makes sense.
			if t1 == t0:
				t1 = t0 + 0.1
			return t0, t1, self.reserve(t0, t1, size/(t1-t0), bwtype=2)
		# It did fit. Do the reservations.
		boxes = []
		while size > 0:
			if t0 >= t1:
				raise 'Bandwidth algorithm error'
			i, tnext = self._find(t0, t1)
			t0_0, bw = self.used[i]
			bwfree = self.max - bw
			size_in_slot = bwfree*(tnext-t0)
			if size_in_slot <= 0:
				t0 = tnext
				continue
			if size_in_slot > size:
				# Yes, everything fits. Compute end time
				# and possibly create new slot
				tnext = t0 + size/bwfree
				i, tnext = self._find(t0, tnext)
				size_in_slot = size
			boxes.append((t0, tnext, bw, self.max, 0))
			if overall_t0 is None:
				overall_t0 = t0
			overall_t1 = tnext
			self.used[i] = t0, self.max
			size = int(size - size_in_slot)
			t0 = tnext
		return overall_t0, overall_t1, boxes
		
class BandwidthStripBox(GO):
	BWSCOLORS = [	# Without focus
			ARMINACTIVECOLOR,     # Preload
			PLAYINACTIVECOLOR,      # Playing
			ARMERRORCOLOR,        # Preload, too much bw used
			PLAYERRORCOLOR,       # Playing, too much bw used
		] , [   # with focus
			ARMACTIVECOLOR,
			PLAYACTIVECOLOR,
			ARMACTIVECOLOR,
			PLAYACTIVECOLOR,
		]

	BWNAMES = {
		14400: "14k4",
		28800: "28k8",
		64000: "ISDN",
		128000: "2xISDN"
       }

	def __init__(self, mother):
		GO.__init__(self, mother, 'bandwidthstrip')
		self.is_bandwidth_strip = 1
		self.boxes = []
		self.focusboxes = []
		import settings
		self.bandwidth = settings.get('system_bitrate')
		if self.BWNAMES.has_key(self.bandwidth):
			self.bwname = self.BWNAMES[self.bandwidth]
		elif self.bandwidth > 1000000:
			self.bwname = "%d Mbps" % (self.bandwidth / 1000000)
		elif self.bandwidth > 1000:
			self.bwname = "%d Kbps" % (self.bandwidth / 1000)
		else:
			self.bwname = "%d bps" % self.bandwidth

		self.maxbw = 2*self.bandwidth
		self.usedbandwidth = BandwidthAccumulator(self.bandwidth)
		self.time_to_bwnodes = []
		self.time_to_panodes = []
		self.focussed_bwnodes = []
		self.focussed_panodes = []

	def getbandwidth(self):
		return self.bandwidth

	def reshape(self):
		self.top = self.mother.bandwidthstripborder + \
			   self.mother.new_displist.fontheight()
		self.bottom = self.mother.timescaleborder
		t0, t1 = self.mother.timerange()
		self.left, self.right = self.mother.maptimes(t0, t1)
		self.ok = 1

	def drawfocus(self):
		l, t, r, b = self.left, self.top, self.right, self.bottom
		width = r-l
		if width <= 0:
			return
		d = self.mother.new_displist
##		f_width = d.strsize('x')[0]
##		d.fgcolor(BORDERCOLOR)
		hmargin = d.strsize('x')[0] / 9
		l = l + hmargin
		r = r - hmargin
		# Draw the axes
		d.drawline(BORDERCOLOR, [(l, t), (l, b), (r, b)])
		bwpos = (t+b)/2 # XXXX
		f_height = d.strsize('x')[1]
		d.drawline(BORDERCOLOR, [(l, bwpos), (r, bwpos)])
		d.fgcolor(TEXTCOLOR)
		d.centerstring(0, bwpos-f_height/2, self.mother.channelright,
			       bwpos+f_height, self.bwname)
		for box in self.boxes:
			self._drawbox(box, 0)
		for box in self.focusboxes:
			self._drawbox(box, 1)

	def ishit(self, x, y):
		if not self.ok: return 0
		return self.left <= x <= self.right and \
		       self.top <= y <= self.bottom

	def select(self, x=None, y=None):
		self.nodehighlight(self.focussed_bwnodes, None)
		self.nodehighlight(self.focussed_panodes, None)
		self.focussed_bwnodes = []
		self.focussed_panodes = []
		t0, t1 = self.mother.timerange()
		if not x is None and self.left <= x <= self.right:
			factor = float(x-self.left)/(self.right-self.left)
			t = t0+factor*(t1-t0)
			for t0, t1, node in self.time_to_bwnodes:
				if t0 <= t <= t1:
##					print "TEST", t0, t1, t, node
					self.focussed_bwnodes.append(node)
			for t0, t1, node in self.time_to_panodes:
				if t0 <= t <= t1:
##					print "TEST2", t0, t1, t, node
					self.focussed_panodes.append(node)
		self.nodehighlight(self.focussed_bwnodes, PLAYACTIVECOLOR)
		self.nodehighlight(self.focussed_panodes, ARMACTIVECOLOR)
		return GO.select(self)

	def nodehighlight(self, list, color):
		for node in list:
			node.set_bandwidthhighlight(color)

	def deselect(self):
##		print "DESELECT"
		self.nodehighlight(self.focussed_bwnodes, None)
		self.nodehighlight(self.focussed_panodes, None)
		self.focussed_bwnodes = []
		self.focussed_panodes = []
		return GO.deselect(self)
			       
	def setstripfocus(self, focusboxes):
		if self.ok:
			for box in self.focusboxes:
				self._drawbox(box, 0)
		self.focusboxes = focusboxes
		if self.ok:
			for box in self.focusboxes:
				self._drawbox(box, 1)

	def _drawbox(self, (t0, t1, min, max, which), focus):
		color = self.BWSCOLORS[focus][which]
		d = self.mother.new_displist
		l, r = self.mother.maptimes(t0, t1)
		factor = (self.bottom-self.top)/float(self.maxbw)
		# If it sticks out over the top we clip it
		toohigh = max - self.maxbw
		if toohigh > 0:
			max = max - toohigh
			min = min - toohigh
		if min < 0:
			min = 0
		t = self.bottom - (max*factor)
		b = self.bottom - (min*factor)

		d.drawfbox(color, (l, t, r-l, b-t))

	def bwbox(self, t0, t1, bandwidth, node):
		"""Reserve bandwidth from t0 until t1. Return list of boxes
		depicting the bandwidth"""
##		box = (t0, t1, 0, bandwidth, 1)
		boxes = self.usedbandwidth.reserve(t0, t1, bandwidth)
		self.boxes = self.boxes + boxes
		self.time_to_bwnodes.append(t0, t1, node)
		return boxes

	def pabox(self, t_arm, t0, prearmsize, node):
		"""Reserve bandwidth for prearming prearmsize, starting after
		t_arm and ending before t0. Return a list of boxes"""
		xt0, xt1, boxes = self.usedbandwidth.prearmreserve(t_arm, t0, prearmsize)
		self.boxes = self.boxes + boxes
		if not (xt0 is None or xt1 is None):
			self.time_to_panodes.append(xt0, xt1, node)
		return boxes

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
			return
		try:
			isvis = ch.attrdict['visible']
		except KeyError:
			isvis = 1
		ch.attrdict['visible'] = not isvis
		self.mother.channels_changed()

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
		f = os.path.join(self.mother.datadir, '%s.tiff' % self.ctype)
		try:
			d.display_image_from_file(f, center = 1, coordinates = (r, t, self.mother.nodetop-r, b-t))
		except windowinterface.error:
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



def nodesort(o1, o2):
	d = cmp(o1.node.t0, o2.node.t0)
	if d == 0:
		d = cmp(o1.node.t1, o2.node.t1)
	return d

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
		self.bandwidthhighlight = None
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
			CREATEANCHOR(callback = (self.createanchorcall, ())),
			FINISH_LINK(callback = (self.hyperlinkcall, ())),
			INFO(callback = (self.infocall, ())),
			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),
			ANCHORS(callback = (self.anchorcall, ())),
			SYNCARCS(callback = self.selsyncarc),
			]

		# win32++
		import sys
		if sys.platform == 'win32':
			self.commandlist = self.commandlist + [
				CONTENT_EDIT_REG(callback = (self._editcall, ())),
				CONTENT_OPEN_REG(callback = (self._opencall, ())),
				]

		self.arcmenu = arcmenu = []
		if mother.showarcs:
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

	def set_bandwidthhighlight(self, mode):
		# print 'node', self.name, 'setarmedmode', mode
		if mode <> self.bandwidthhighlight:
##			self.mother.init_display()
			self.bandwidthhighlight = mode
			self.drawfocus()
## 			self.mother.drawarcs((self.left, self.top, self.right, self.bottom))
##			self.mother.render()
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
		top, bottom = self.mother.mapchannel(channel, self.channelline)
		if hasattr(self.node,'timing_discont') and self.node.timing_discont:
		    self.mother.discontinuities.append(
			self.node.t0+self.node.timing_discont)

		hmargin = self.mother.new_displist.strsize('x')[0] / 15
		left = left + hmargin
		right = right - hmargin

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

		# give box a minimal size
		if l + haboxsize > r:
			r = l + haboxsize

		if self.node.WillPlay():
			nodecolor = NODECOLOR
			altnodecolor = ALTNODECOLOR
		else:
			nodecolor = NODEOFFCOLOR
			altnodecolor = ALTNODEOFFCOLOR

		# Draw a box
		if self.locked:
			color = LOCKEDCOLOR
		else:
			try:
				color = armcolors[self.node.armedmode]
			except KeyError:
				color = nodecolor
		d.drawfbox(color, (l, t, r - l, b - t))

		# If the end time was inherited, make the bottom-right
		# triangle of the box a lighter color
		if self.node.t0t1_inherited:
			d.drawfpolygon(altnodecolor, [(r, t), (r, b), (l, b)])

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
		# And overdraw if we have a bandwidth highlight
		if self.bandwidthhighlight:
			d.fgcolor(self.bandwidthhighlight)
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

	def getbandwidthdata(self):
		if not self.node.WillPlay():
			return None
		t0 = self.node.t0
		t1 = self.node.t1
		prearm, bandwidth = Bandwidth.get(self.node)
		return t0, t1, self, prearm, bandwidth

	# Menu stuff beyond what GO offers

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

	def newsyncarccall(self):
		self.mother.init_display()
		self.lock()
		self.mother.render()

	def focuscall(self):
		top = self.mother.toplevel
		top.setwaiting()
		top.hierarchyview.globalsetfocus(self.node)

	def createanchorcall(self):
		self.mother.toplevel.links.wholenodeanchor(self.node)

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
		self.arcid = snode, sside, delay, dnode, dside
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
		ArcBox.arc_info=ArcInfo.showarcinfo(self.mother, self.mother.root,
				    self.snode, self.sside, self.delay,
				    self.dnode, self.dside)

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

	def selnode(self, node):
		top = self.mother.toplevel
		top.setwaiting()
		self.mother.globalsetfocus(node)
