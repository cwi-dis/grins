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
import string
import windowinterface, WMEVENTS
from ChannelViewDialog import ChannelViewDialog, GOCommand, \
     BandwidthStripBoxCommand, ChannelBoxCommand, NodeBoxCommand, \
     ArcBoxCommand
from usercmd import *
from BandwidthCompute import BandwidthAccumulator

import MMAttrdefs
import Timing
from MMExc import *
from AnchorDefs import *
from ArmStates import *
from MMTypes import *
import os
import Bandwidth
import settings

OPTION_TIMESCALEBOX_BOXES = 0		# Turn on for measure-tape timeline


# Color assignments (RGB)

BGCOLOR = settings.get('timeline_bgcolor')
GUTTERTOPCOLOR = settings.get('timeline_guttertop')
GUTTERBOTTOMCOLOR = settings.get('timeline_gutterbottom')
BORDERCOLOR = settings.get('timeline_bordercolor')
CHANNELCOLOR = settings.get('timeline_channelcolor')
CHANNELOFFCOLOR = settings.get('timeline_channeloffcolor')
NODECOLOR = settings.get('timeline_nodecolor')
ALTNODECOLOR = settings.get('timeline_altnodecolor')
NODEOFFCOLOR = settings.get('timeline_nodeoffcolor')
ALTNODEOFFCOLOR = settings.get('timeline_altnodeoffcolor')
ARROWCOLOR = settings.get('timeline_arrowcolor')
TEXTCOLOR = settings.get('timeline_textcolor')
FOCUSCOLOR = settings.get('timeline_focuscolor')
LOCKEDCOLOR = settings.get('timeline_lockedcolor')
ANCHORCOLOR = settings.get('timeline_anchorcolor')

# Focus color assignments (from light to dark gray)

FOCUSLEFT = settings.get('timeline_focusleft')
FOCUSTOP = settings.get('timeline_focustop')
FOCUSRIGHT = settings.get('timeline_focusright')
FOCUSBOTTOM = settings.get('timeline_focusbottom')

# Arm colors
ARMACTIVECOLOR = settings.get('timeline_armactivecolor')
ARMINACTIVECOLOR = settings.get('timeline_arminactivecolor')
ARMERRORCOLOR = settings.get('timeline_armerrorcolor')
PLAYACTIVECOLOR = settings.get('timeline_playactivecolor')
PLAYINACTIVECOLOR = settings.get('timeline_playinactivecolor')
PLAYERRORCOLOR = settings.get('timeline_playerrorcolor')

armcolors = {
	ARM_SCHEDULED: (200, 200, 0),
	ARM_ARMING: ARMACTIVECOLOR,
	ARM_ARMED: ARMINACTIVECOLOR,
	ARM_PLAYING: PLAYACTIVECOLOR,
	ARM_WAITSTOP: PLAYINACTIVECOLOR,
	}


# Arrowhead dimensions

ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

# Font we use
f_title = windowinterface.findfont('Helvetica', 10)
f_timeline = windowinterface.findfont('Helvetica', 9)

# Types of things we can do in the (modal) channel-pointing mode
PLACING_NEW = 1
PLACING_COPY = 2
PLACING_MOVE = 3

begend = ('begin', 'end')

CHANGAP = 0.5
NOTHUMB_CHANHEIGHT = 5.0
THUMB_CHANHEIGHT = 2.0 + settings.get('thumbnail_size')
TSHEIGHT = f_title.fontheight() * 4
STRIPHEIGHT = f_title.fontheight() * 5

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
		self.arcs = []
		self.placing_channel = 0
		self.thumbnails = 0
		self.chanheight = NOTHUMB_CHANHEIGHT
		self.showbandwidthstrip = 0
		self._ignore_resize = 0
		self._common_commandlist = None
##		self.layouts = [('All channels', ())]
##		for name in self.context.layouts.keys():
##			self.layouts.append((name, (name,)))
##		self.curlayout = None
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
			ChannelViewDialog.show(self, None)
			return
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

	def hide(self, *rest):
		if not self.is_showing():
			return
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

	def transaction(self, type):
		return 1 # It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self, type):
		self.redrawafterchange()

	def redrawafterchange(self):
##		self.layouts = [('All channels', ())]
##		for name in self.context.layouts.keys():
##			self.layouts.append((name, (name,)))
##		if self.curlayout is not None and \
##		   not self.context.layouts.has_key(self.curlayout):
##			self.curlayout = None
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

	def kill(self):
		self.destroy()

	# Event interface

	def resize(self, *rest):
		if self._ignore_resize:
			return
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
		self.recalcxxx()
		for obj in self.objects:
			obj.reshape()
		self.draw()

	def thumbnailcall(self):
		self.thumbnails = not self.thumbnails
		if self.thumbnails:
			self.chanheight = THUMB_CHANHEIGHT
		else:
			self.chanheight = NOTHUMB_CHANHEIGHT
		self.settoggle(THUMBNAIL, self.thumbnails)
		self.redrawafterchange()

	def canvascall(self, code):
		from windowinterface import UNIT_MM
		width, height = self.window.getcanvassize(UNIT_MM)
		if code == windowinterface.RESET_CANVAS:
			self._ignore_resize = 1
			self.window.setcanvassize(windowinterface.RESET_CANVAS)
			self._ignore_resize = 0
			self.reshape()
		elif code == windowinterface.DOUBLE_WIDTH:
			width = 2 * width
			self.window.setcanvassize((UNIT_MM, width, height))
			obj = self.focus
			if obj and obj.__class__ in (ArcBox, NodeBox):
				self.window.scrollvisible((obj.left, obj.top,
						   obj.right-obj.left,
						   obj.bottom-obj.top))

##	def layoutcall(self, name = None):
##		curlayout = self.curlayout
##		self.curlayout = name
##		if curlayout != name:
##			self.resize()

	def redraw(self):
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = self.window.newdisplaylist(BGCOLOR)
		bl, fh, ps = self.new_displist.usefont(f_title)
		# RESIZE event.
		self.reshape()

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

	def dropfile(self, dummy, window, event, params):
		import MMurl
		x, y, filename = params
		obj = self.whichhit(x, y)
		if not obj or not obj.is_node_object:
			windowinterface.beep()
			return
		self.init_display()
		self.deselect()
		obj.select()
		em = self.editmgr
		if not em.transaction():
			self.render()
			return
		if event == WMEVENTS.DropFile:
			url = MMurl.pathname2url(filename)
			url = self.context.relativeurl(url)
		else:
			url = filename
		obj.node.SetAttr('file', url)
		em.commit()

	def dragfile(self, dummy, window, event, params):
		x, y = params
		obj = self.whichhit(x, y)
		if not obj or not obj.is_node_object:
			windowinterface.setdragcursor('dragnot')
		else:
			windowinterface.setdragcursor('dragset')

	# Time-related subroutines

	def timerange(self):
		# Return the range of times used in the window
		v = self.viewroot
		t0, t1, t2, dummy, dummy = self.viewroot.GetTimes()
		t0 = t0 - self.prerolltime
		return t0, max(t2, t0 + 10)

	def maptimes(self, t0, t1):
		# Map begin and end times to top and bottom in window

		# Calculate our position in relative time
		top = self.nodetop
		height = self.nodebottom - top
		vt0, vt1 = self.timerange()
		dt = vt1 - vt0

		# Compute the 'ideal' top/bottom
		return top + (height * (t0 - vt0) / dt), \
		       top + (height * (t1 - vt0) / dt)

	def mapchannel(self, channel, line = 0):
		# Map channel to left and right coordinates
		if channel.chview_map is not None:
			x, y, height = channel.chview_map[:3]
			return x + line*height, y + line*height
		list = self.visiblechannels()
		channellines = self.channellines
		nchannels = len(list)
		nlines = 0
		found = 0
		for ch in list:
			n = channellines.get(ch.name, 0) or 1
			if channel is ch:
				found = 1
			nlines = nlines + n
		if not found:
			# channel not visible
			return 0, 0
		# store the hard-won information
		totheight = nlines * self.chanheight + nchannels * CHANGAP
		factor = float(self.bandwidthstripborder) / totheight
		chh = self.chanheight*factor
		x = 0
		for ch in list:
			n = channellines.get(ch.name, 0) or 1
			chy = (x + self.chanheight) * factor
			chx = x * factor
			x = x + n * self.chanheight + CHANGAP
			ch.chview_map = chx, chy, chh, n
		x, y, height = channel.chview_map[:3]
		return x + line*height, y + line*height

	def channelgapindex(self, y):
		list = self.visiblechannels()
		for i in range(len(list)):
			y0, y1, h, n = list[i].chview_map
			if y0 <= y <= y1 + (n-1) * h:
				return i
		return len(list)

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
		self.redrawafterchange()

	# Return list of currently visible channels

	def allchannels(self):
		channels = []
		for c in self.context.channels:
			if c['type'] == 'layout':
				channels.append(c)
		return channels

	def visiblechannels(self):
##		layout = {}
##		for ch in self.context.layouts.get(self.curlayout, self.context.channels):
##			layout[ch.name] = 0
		if self.showall:
			channels = self.allchannels()
		else:
			channels = self.usedchannels
##		ret = []
##		for ch in channels:
##			if layout.has_key(ch.name):
##				ret.append(ch)
##		return ret
		return channels

	# Recalculate the set of objects we should be drawing

	def recalc(self, focus):
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
		self.initarcs(focus)
		self.initnodes(focus)
		self.objects[len(self.objects):] = self.arcs
		self.initbwstrip()

		# enable Next and Prev Minidoc commands if there are minidocs
## XXXX Needs to be fixed for dynamically generated commandlists!x
##		if self.baseobject.descendants or \
##		   self.baseobject.ancestors or \
##		   self.baseobject.siblings:
##			for obj in self.objects:
##				obj.commandlist = obj.commandlist + [
##					NEXT_MINIDOC(callback = (obj.nextminicall, ())),
##					PREV_MINIDOC(callback = (obj.prevminicall, ())),
##					]

		focus = self.focus
		self.baseobject.select()
		if focus is not None:
			focus.select()

	def recalcxxx(self):
		width, height = self.window.getcanvassize(windowinterface.UNIT_MM)
		displist = self.window.newdisplaylist(BGCOLOR)
		if self.new_displist:
			self.new_displist.close()
		self.new_displist = displist
		bl, fh, ps = displist.usefont(f_title)
##		self.channelright = displist.strsize('999999')[0]
##		self.nodetop = min(self.channelright * 2, self.channelright + .05)
		self.thumbwidth = displist.strsize('999')[0]
		self.channelright = displist.strsize('999999999999')[0]
		self.nodetop = self.channelright + displist.get3dbordersize()[1]
		self.nodebottom = 1.0 - displist.strsize('m')[0]
		self.nodemargin = displist.strsize('x')[0] / 15
		w, h = displist.strsize('m')
		self.aboxsize = w / 2, h / 3

		self.timescaleborder = 1.0 - float(TSHEIGHT) / height
		if self.showbandwidthstrip:
			stripheight = float(STRIPHEIGHT) / height
			self.bandwidthstripborder = self.timescaleborder - stripheight
		else:
			self.bandwidthstripborder = self.timescaleborder

	# Recompute the locations where the objects should be drawn

	def calculatechannellines(self):
		channels = {}
		for o in self.objects:
			if o.__class__ is not NodeBox:
				continue
			ch = o.node.GetChannel()
			if ch is None: continue
			ch = ch.GetLayoutChannel().name
			if not channels.has_key(ch): channels[ch] = []
			channels[ch].append(o)
		for list in channels.values():
			list.sort(nodesort)
		for ch, list in channels.items():
			x = []
			for o in list:
				t0, t1, t2, dummy, dummy = o.node.GetTimes()
				for i in range(len(x)):
					if t0 >= x[i]:
						x[i] = t2
						o.channelline = i
						break
				else:
					o.channelline = len(x)
					x.append(t2)
			channels[ch] = len(x)
		self.channellines = channels

	def reshape(self):
		from windowinterface import UNIT_MM
		self.discontinuities = []
		Timing.needtimes(self.viewroot)
		self.calculatechannellines()
		channellines = self.channellines
		visiblechannels = self.visiblechannels()
		nlines = 0
		for ch in visiblechannels:
			nlines = nlines + (channellines.get(ch.name, 0) or 1)
##		if hasattr(windowinterface, 'RESET_HEIGHT'):
##			self.window.setcanvassize(windowinterface.RESET_HEIGHT)
		width, height = self.window.getcanvassize(UNIT_MM)
		height = len(visiblechannels) * CHANGAP + nlines * self.chanheight + TSHEIGHT
		if self.showbandwidthstrip:
			height = height + STRIPHEIGHT
		# this causes a ResizeWindow event
		self.window.setcanvassize((UNIT_MM, width, height))

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
			if c['type'] != 'layout':
				continue
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

	def focuscall(self):
		top = self.toplevel
		top.setwaiting()
		if top.hierarchyview is not None:
			top.hierarchyview.globalsetfocus(self.viewroot)

	def setviewrootcb(self, node):
		self.toplevel.setwaiting()
		self.setviewroot(node)

	def fixtitle(self):
		import MMurl
		basename = MMurl.unquote(self.toplevel.basename)
		title = 'Timeline View (' + basename + ')'
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
				c.chview_map = 0, 0, 0, 0
		self.addancestors()
		self.addsiblings()

	def scantree(self, node, focus):
		t = node.GetType()
		if t in leaftypes:
			channel = node.GetChannel()
			if channel:
				channel = channel.GetLayoutChannel()
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
		self.arcs = arcs

	def scanarcs(self, node, focus, arcs):
		type = node.GetType()
		if type in leaftypes and node.GetChannel():
			self.addarcs(node, arcs, focus)
		elif type not in bagtypes:
			for c in node.GetChildren():
				self.scanarcs(c, focus, arcs)

	def addarcs(self, ynode, arcs, focus):
		synctolist = MMAttrdefs.getattr(ynode, 'synctolist')
		delay = MMAttrdefs.getattr(ynode, 'begin')
		if delay > 0:
			from HDTL import HD, TL
			parent = ynode.GetParent()
			if parent.GetType() == 'seq':
				xnode = None
				xside = TL
				for n in parent.GetChildren():
					if n is ynode:
						break
					xnode = n
				if xnode is None:
					# first child in seq
					xnode = parent
					xside = HD
			else:
				xnode = parent
				xside = HD
			# don't append, make copy!
			synctolist = synctolist + [(xnode.GetUID(), xside, delay, HD)]
		for arc in synctolist:
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
		# Adjust timebar
		self.prerolltime = prerolltime
		# And the rest of the prearms
		prearmlist = []
		for nodelist in nodematrix:
			t_arm = -self.prerolltime
			for info in nodelist:
				t0, t1, node, prearm, bandwidth = info
				prearmlist.append((t_arm, t0, prearm, node))
				t_arm = t0
		prearmlist.sort()
		for t_arm, t0, prearm, node in prearmlist:
			pabox = self.bwstripobject.pabox(t_arm, t0, prearm, node)
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
		obj = self.whichhit(x, y)
		if obj:
			if self.lockednode:
				if obj.is_node_object and obj != self.lockednode:
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
		self.setcommands(obj.getcommandlist(), title = obj.menutitle)
		self.setpopup(obj.popupmenu)

	def whichhit(self, x, y):
		# find last object (the one drawn on top)
		objects = self.objects[:]
		objects.reverse()	# now find first object...
		for obj in objects:
			if obj.ishit(x, y):
				return obj
		return None

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
			self.window.scrollvisible((obj.left, obj.top,
						   obj.right-obj.left,
						   obj.bottom-obj.top))
		self.render()

	# Create a new channel
	# XXXX Index is obsolete!
	def newchannel(self, index = None, chtype = None):
		if index == None:
			if self.focus and type(self.focus) <> type(()):
				index = self.focus.newchannelindex()
##		print 'DBG: newchannel', self.focus, index
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
			self.select_cb(index, chtype)
			return
		prompt = 'Select channel type:'
		list = []
		import ChannelMap
		for name in ChannelMap.getvalidchanneltypes(self.context):
			list.append((name, (self.select_cb, (index, name,))))
		list.append(None)
		list.append('Cancel')
		windowinterface.Dialog(list, title = 'Select', prompt = prompt, grab = 1, vertical = 1, parent = self.window)

	def select_cb(self, index, name):
		self.placing_channel = PLACING_NEW
		self.placing_type = name
		self.finish_channel(1.0, 1.0, index)  # X, Y ignored if index specified
##		windowinterface.setcursor('stop')
##		self.window.setcursor('channel')

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

	def finish_channel(self, x, y, index=None):
		placement_type = self.placing_channel
		self.placing_channel = 0
		if not index:
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
##			if self.curlayout and self.context.layouts.has_key(self.curlayout):
##				layoutchannels = self.context.layouts[self.curlayout]
##				layoutchannels.append(self.context.channeldict[name])
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
		self.commandlist = None

		# Menu and shortcut definitions are stored as data in
		# the class

		self.menutitle = 'Base ops'
		GOCommand.__init__(self)
		
	def mkcommandlist(self):
		if self.commandlist:
			return
		# First create common-common-commandlist
		mother = self.mother
		if not mother._common_commandlist:
			mother._common_commandlist = [
				CLOSE_WINDOW(callback = (mother.hide, ())),
##				CANVAS_HEIGHT(callback = (mother.canvascall,
##						(windowinterface.DOUBLE_HEIGHT,))),
				CANVAS_WIDTH(callback = (mother.canvascall,
						(windowinterface.DOUBLE_WIDTH,))),
				CANVAS_RESET(callback = (mother.canvascall,
						(windowinterface.RESET_CANVAS,))),
				NEW_CHANNEL(callback = (mother.newchannel, ())),
				ANCESTORS(callback = mother.setviewrootcb),
				SIBLINGS(callback = mother.setviewrootcb),
				DESCENDANTS(callback = mother.setviewrootcb),
				TOGGLE_UNUSED(callback = (mother.toggleshow, ())),
				THUMBNAIL(callback = (mother.thumbnailcall, ())),
				TOGGLE_ARCS(callback = (mother.togglearcs, ())),
##				LAYOUTS(callback = mother.layoutcall),
				TOGGLE_BWSTRIP(callback = (mother.togglebwstrip, ())),
				]
		self.commandlist = mother._common_commandlist[:]
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(HELP(callback=(self.helpcall,())))
			
	def getcommandlist(self):
		self.mkcommandlist()
		return self.commandlist

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
		total = len(self.mother.allchannels())
		if visible == total: return
		str = '%d more' % (total-visible)
		d = self.mother.new_displist
		d.usefont(f_title)
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
		self.mother.setcommands(self.getcommandlist(),
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
			mother.setcommands(baseobject.getcommandlist(),
						  title = baseobject.menutitle)
			mother.setpopup(baseobject.popupmenu)
			self.drawfocus()
		if self.mother.bwstripobject:
			self.mother.bwstripobject.setstripfocus([])

	def ishit(self, x, y):
		# Check whether the given mouse coordinates are in this object
		return 0

	# Methods corresponding to the menu entries

##	def helpcall(self):
##		import Help
##		Help.givehelp('Channel_view')

##	def newchannelcall(self, chtype = None):
##		self.mother.newchannel(self.newchannelindex(), chtype)

##	def nextminicall(self):
##		mother = self.mother
##		mother.toplevel.setwaiting()
##		mother.nextviewroot()

##	def prevminicall(self):
##		mother = self.mother
##		mother.toplevel.setwaiting()
##		mother.prevviewroot()

	def newchannelindex(self):
		# NB Overridden by ChannelBox to insert before current!
		return len(self.mother.context.channelnames)


class BaseBox(GO):
	def __init__(self, mother, name):
		GO.__init__(self, mother, name)
		
	def mkcommandlist(self):
		if self.commandlist:
			return
		GO.mkcommandlist(self)
		self.commandlist = self.commandlist + [
			PUSHFOCUS(callback = (self.mother.focuscall, ())),
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
		d.usefont(f_timeline)
		f_width = d.strsize('x')[0]
		d.fgcolor(BORDERCOLOR)
		# Draw rectangle around boxes
		hmargin = f_width / 9
		vmargin = d.fontheight() / 4
		l = l + hmargin
		t = t + vmargin
		r = r - hmargin
		b = (4*t+b)/5
		if OPTION_TIMESCALEBOX_BOXES:
			d.drawbox((l, t, r - l, b - t))
		else:
			d.drawline(BORDERCOLOR, [(l, b), (r, b)])
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
			if OPTION_TIMESCALEBOX_BOXES:
				d.drawfbox(BORDERCOLOR, (l, t, r - l, b - t))
			elif i%div == 0:
				d.drawline(BORDERCOLOR, [(l, t), (l, b)])
			else:
				d.drawline(BORDERCOLOR, [(l, (t+b)/2), (l, b)])
			if i%div <> 0:
				continue
			if tickstep < 1:
				ticklabel = `i*tickstep`
			else:
				ts_value = int(i*tickstep)
				ticklabel = '%3d:%02.2d'%(ts_value/60, ts_value%60)
			d.centerstring(l-f_width*3, b,
				       l+f_width*3, self.bottom,
				       ticklabel)
		# For things left of t0 (preload time) draw ticks only,
		# and the total value
		fart0, dummy = self.mother.timerange()
		farleft, dummy = self.mother.maptimes(fart0, t1)
		it0 = t0 - tickstep
		i = 0
		while it0 > fart0:
			i = i + 1
			l, dummy = self.mother.maptimes(it0, t0)
			if i%div == 0:
				d.drawline(BORDERCOLOR, [(l, t), (l, b)])
			else:
				d.drawline(BORDERCOLOR, [(l, (t+b)/2), (l, b)])
			it0 = it0 - tickstep
		if fart0 != t0:
			l, r = self.mother.maptimes(it0, t0)
			d.drawline(BORDERCOLOR, [(l, t), (l, b)])
			d.centerstring(l-f_width*5, b,
				       r, self.bottom,
				       "%ds preroll"%(t0-fart0))

		# And draw markers in places where time breaks
		for i in self.mother.discontinuities:
			l, r = self.mother.maptimes(i, i)
			d.drawline(ANCHORCOLOR, [(l, t), (l, b)])
			
class BandwidthStripBox(GO, BandwidthStripBoxCommand):
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
		1000000: "T1",
		10000000: "LAN",
		}

	def __init__(self, mother):
		GO.__init__(self, mother, 'bandwidthstrip')
		self.is_bandwidth_strip = 1
		self.boxes = []
		self.focusboxes = []
		self.bandwidth = settings.get('system_bitrate')
		self.bwname = self._bwstr(self.bandwidth)

		self.maxbw = 2*self.bandwidth
		self.usedbandwidth = BandwidthAccumulator(self.bandwidth)
		self.time_to_bwnodes = []
		self.time_to_panodes = []
		self.focussed_bwnodes = []
		self.focussed_panodes = []
		BandwidthStripBoxCommand.__init__(self)
		
	def mkcommandlist(self):
		if self.commandlist:
			return
		GO.mkcommandlist(self)
		self.commandlist = self.commandlist + [
			BANDWIDTH_14K4(callback = (self.bwcall, (14400,))),
			BANDWIDTH_28K8(callback = (self.bwcall, (28800,))),
			BANDWIDTH_ISDN(callback = (self.bwcall, (64000,))),
			BANDWIDTH_T1(callback = (self.bwcall, (1000000,))),
			BANDWIDTH_LAN(callback = (self.bwcall, (10000000,))),
			BANDWIDTH_OTHER(callback = (self.otherbwcall, ())),
			]

	def _bwstr(self, bandwidth):
		# Convert bandwidth number to string
		if self.BWNAMES.has_key(bandwidth):
			return self.BWNAMES[bandwidth]
		elif bandwidth > 1000000:
			return"%d Mbps" % (bandwidth / 1000000)
		elif bandwidth > 1000:
			return "%d Kbps" % (bandwidth / 1000)
		return "%d bps" % bandwidth

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
		f_width, f_height = d.strsize('x')
##		d.fgcolor(BORDERCOLOR)
		hmargin = f_width / 9
		l = l + hmargin
		r = r - hmargin
		# Draw the axes
		d.drawline(BORDERCOLOR, [(l, t), (l, b), (r, b)])
		bwpos = (t+b)/2 # XXXX
		d.drawline(BORDERCOLOR, [(l, bwpos), (r, bwpos)])
		d.fgcolor(TEXTCOLOR)
		d.centerstring(0, bwpos-f_height/2, self.mother.channelright,
			       bwpos+f_height/2, self.bwname)
		if self.usedbandwidth.maxused > self.usedbandwidth.max:
			d.fgcolor(PLAYERRORCOLOR)
			d.centerstring(0, t, self.mother.channelright,
				       t+f_height, self._bwstr(
					       self.usedbandwidth.maxused))

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
					self.focussed_bwnodes.append(node)
			for t0, t1, node in self.time_to_panodes:
				if t0 <= t <= t1:
					self.focussed_panodes.append(node)
		self.nodehighlight(self.focussed_bwnodes, PLAYACTIVECOLOR)
		self.nodehighlight(self.focussed_panodes, ARMACTIVECOLOR)
		return GO.select(self)

	def nodehighlight(self, list, color):
		for node in list:
			node.set_bandwidthhighlight(color)

	def deselect(self):
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
		if bandwidth == 0:
			return []
##		box = (t0, t1, 0, bandwidth, 1)
		overflow, boxes = self.usedbandwidth.reserve(t0, t1, bandwidth)
		self.boxes = self.boxes + boxes
		self.time_to_bwnodes.append((t0, t1, node))
		return boxes

	def pabox(self, t_arm, t0, prearmsize, node):
		"""Reserve bandwidth for prearming prearmsize, starting after
		t_arm and ending before t0. Return a list of boxes"""
		overflow, xt0, xt1, boxes = self.usedbandwidth.prearmreserve(t_arm, t0, prearmsize)
		if prearmsize == 0:
			return []
		self.boxes = self.boxes + boxes
		if not (xt0 is None or xt1 is None):
			self.time_to_panodes.append((xt0, xt1, node))
		return boxes

	def bwcall(self, bandwidth):
		if type(bandwidth) == type(""):
			try:
				bandwidth = string.atoi(bandwidth)
			except ValueError:
				bandwidth = -1
		if bandwidth <= 0:
			windowinterface.showmessage("Incorrect bandwidth")
			return
		import settings
		settings.set('system_bitrate', bandwidth)
		self.mother.toplevel.prefschanged()

	def otherbwcall(self):
		windowinterface.InputDialog("Bandwidth (bps)",
					    `self.bandwidth`, self.bwcall)

# Class for Channel Objects

class ChannelBox(GO, ChannelBoxCommand):

	def __init__(self, mother, channel):
		GO.__init__(self, mother, channel.name)
		self.channel = channel
		self.ctype = channel.get('type', '???')
		
		self.menutitle = 'Channel %s ops' % self.name
		ChannelBoxCommand.__init__(self)

	def mkcommandlist(self):
		if self.commandlist:
			return
		GO.mkcommandlist(self)
		self.commandlist = self.commandlist + [
			ATTRIBUTES(callback = (self.attrcall, ())),
			MOVE_CHANNEL(callback = (self.movecall, ())),
			COPY_CHANNEL(callback = (self.copycall, ())),
			TOGGLE_ONOFF(callback = (self.channel_onoff, ())),
			HIGHLIGHT(callback = (self.highlight, ())),
			UNHIGHLIGHT(callback = (self.unhighlight, ())),
			]
		# if not root layout
		if self.ctype != 'layout':
			self.commandlist = self.commandlist + [	
			DELETE(callback = (self.delcall, ()))
			]

	def channel_onoff(self):
		self.mother.toplevel.setwaiting()
		player = self.mother.toplevel.player
		ch = self.channel
		if player.is_showing():
			player.channel_callback(ch.name)
			return
		isvis = ch.attrdict.get('visible', 1)
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
		xindent, yindent = d.get3dbordersize()

		# Draw a diamond
		cd = self.mother.context.channeldict[self.name]
		visible = cd.get('visible', 1)
		if visible:
			color = CHANNELCOLOR
		else:
			color = CHANNELOFFCOLOR
##		d.drawfdiamond(color, (l, t, r - l, b - t))
		d.drawfbox(color, (l, t, r - l, b - t))

		# Outline the diamond; 'engraved' normally,
		# 'sticking out' if selected
		if self.selected:
##			d.draw3ddiamond(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT,
##					FOCUSBOTTOM, (l, t, r - l, b - t))
			d.draw3dbox(FOCUSBOTTOM, FOCUSBOTTOM, FOCUSBOTTOM,
					FOCUSBOTTOM, (l, t, r - l, b - t))
		d.fgcolor(BORDERCOLOR)
##		d.drawdiamond((l, t, r - l, b - t))
		d.drawbox((l, t, r - l, b - t))

		# Draw the name
		xindent, yindent = d.get3dbordersize()
		thumb_r = r - xindent
		thumb_l = thumb_r - self.mother.thumbwidth
		name_t = t + yindent
		name_b = b - yindent
		name_l = l + xindent
		name_r = thumb_l
		d.fgcolor(TEXTCOLOR)
		d.centerstring(name_l, name_t, name_r, name_b, self.name)

##		# Draw the channel type
		f = os.path.join(self.mother.datadir, '%s.tiff' % self.ctype)
		try:
			d.display_image_from_file(f, center = 1,
					coordinates = (thumb_l, name_t, thumb_r-thumb_l, name_b-name_t))
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
##		d.drawline(BORDERCOLOR, [(self.right, self.ycenter),
##					 (self.farright, self.ycenter)])
		x, y, h, n = self.channel.chview_map
		top = self.mother.mapchannel(self.channel)[0]
		bottom = self.mother.mapchannel(self.channel, (self.mother.channellines.get(self.channel.name, 0) or 1) - 1)[1]
##		d.drawline(BORDERCOLOR, [(0.0, top),
##					 (1.0, top)])
##		d.drawline(BORDERCOLOR, [(0.0, bottom),
##					 (1.0, bottom)])
		d.draw3dhline(GUTTERTOPCOLOR, GUTTERBOTTOMCOLOR, 0.0, 1.0, bottom)
##		r = self.right
##		xindent, yindent = d.get3dbordersize()
##		x = r+xindent/2
##		d.drawline(BORDERCOLOR, [(x, top), (x, bottom)])

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
		return self.mother.context.channelnames.index(self.name)+1

	def highlight(self):
		channels = self.mother.toplevel.player.channels
		if channels.has_key(self.name):
			channels[self.name].highlight()

	def unhighlight(self):
		channels = self.mother.toplevel.player.channels
		if channels.has_key(self.name):
			channels[self.name].unhighlight()



def nodesort(o1, o2):
	o1_t0, dummy, o1_t2, dummy, dummy = o1.node.GetTimes()
	o2_t0, dummy, o2_t2, dummy, dummy = o1.node.GetTimes()
	d = cmp(o1_t0, o2_t0)
	if d == 0:
		d = cmp(o1_t2, o2_t2)
	return d

class NodeBox(GO, NodeBoxCommand):

	def __init__(self, mother, node):
		import Duration
		self.node = node
		duration = Duration.get(node)
		self.pausenode = duration < 0
		self.hasanchors = self.haspause = 0
		alist = self.node.GetRawAttrDef('anchorlist', None)
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

		self.arcmenu = arcmenu = []
		for arc in mother.arcs:
			xnode, xside, delay, ynode, yside = arc.arcid
			if ynode is not node:
				continue
			xname = MMAttrdefs.getattr(xnode, 'name')
			if not xname:
				xname = '#' + xnode.GetUID()
			if xside in (0, 1):
				xside = begend[xside]
			arcmenu.append(('From %s of node "%s" to %s of self' % (xside, xname, begend[yside]), (xnode, xside, delay, yside)))
		self.menutitle = 'Node %s ops' % self.name
		NodeBoxCommand.__init__(self, mother, node)

	def mkcommandlist(self):
		if self.commandlist:
			return
		GO.mkcommandlist(self)
		self.commandlist = self.commandlist + [
			PLAYNODE(callback = (self.playcall, ())),
			PLAYFROM(callback = (self.playfromcall, ())),
			PUSHFOCUS(callback = (self.focuscall, ())),
			FINISH_ARC(callback = (self.newsyncarccall, ())),
			CREATEANCHOR(callback = (self.createanchorcall, ())),
			FINISH_LINK(callback = (self.hyperlinkcall, ())),
##			INFO(callback = (self.infocall, ())),
			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),
			ANCHORS(callback = (self.anchorcall, ())),
			SYNCARCS(callback = self.selsyncarc),
			]

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
		if mode <> self.node.armedmode:
			self.mother.init_display()
			self.node.armedmode = mode
			self.drawfocus()
##			self.mother.drawarcs((self.left, self.top, self.right, self.bottom))
			self.mother.render()
			self.mother.delay_drawarcs()

	def set_bandwidthhighlight(self, mode):
		if mode <> self.bandwidthhighlight:
##			self.mother.init_display()
			self.bandwidthhighlight = mode
			self.drawfocus()
##			self.mother.drawarcs((self.left, self.top, self.right, self.bottom))
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
		mother = self.mother
		if not mother.lockednode:
			windowinterface.beep()
			return
		mother.window.setcursor('')
		editmgr = mother.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		root = mother.root
		snode, sside, delay, dnode, dside, new = \
			mother.lockednode.node, 1, 0.0, self.node, 0, 1
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
		mother.cleanup()
		editmgr.commit()
		# NB: when we get here, this object is nearly dead already!
		import ArcInfo
		ArcInfo.showarcinfo(mother, root, snode, sside, delay,
				    dnode, dside, new = new)

	def select(self):
		self.unlock()
		GO.select(self)

	def reshape(self):
		# Compute ideal box coordinates
		channel = self.node.GetChannel()
		node_t0, node_t1, node_t2, dummy, dummy = self.node.GetTimes()
		if channel:
			channel = channel.GetLayoutChannel()
		if self.pausenode:
			parent = self.node.GetParent()
			dummy, dummy, parent_t2, dummy, dummy = parent.GetTimes()
			if parent is None:
				t1 = node_t2
			elif parent.GetType() == 'seq':
				siblings = parent.GetChildren()
				index = siblings.index(self.node)
				if len(siblings) > index+1:
					t1 = siblings[index+1].GetTimes()[0]
				else:
					t1 = parent_t2
			else:
				t1 = parent_t2
			if t1 == node_t0:
				t1 = node_t2
		else:
			t1 = node_t2
		left, right = self.mother.maptimes(node_t0, t1)
		top, bottom = self.mother.mapchannel(channel, self.channelline)
##		if hasattr(self.node,'timing_discont') and self.node.timing_discont:
##			self.mother.discontinuities.append(
##				node_t0+self.node.timing_discont)

		hmargin = self.mother.nodemargin
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
		haboxsize, vaboxsize = self.mother.aboxsize

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
			color = armcolors.get(self.node.armedmode, nodecolor)
		d.drawfbox(color, (l, t, r - l, b - t))

		# If the end time was inherited, make the bottom-right
		# triangle of the box a lighter color
		if self.node.GetFill() != 'remove':
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
##		print 'rect', l, t, r, b
		xindent, yindent = d.get3dbordersize()
##		print 'indent', xindent, yindent
		thumb_l = l + xindent
		thumb_t = t + yindent
		thumb_w = (r-l)/2 - 2*xindent
		thumb_h = (b-t) - 2*yindent
##		print 'thumb', thumb_l, thumb_t, thumb_w, thumb_h
		if self.mother.thumbnails and \
		   thumb_w > 0 and thumb_h > 0 and \
		   self.node.GetChannelType() == 'image':
			import MMurl
			try:
				f = MMurl.urlretrieve(self.node.context.findurl(MMAttrdefs.getattr(self.node, 'file')))[0]
			except IOError:
				pass
			else:
				try:
					box = d.display_image_from_file(f, center = 0,
							coordinates = (thumb_l, thumb_t, thumb_w, thumb_h))
				except windowinterface.error:
					pass
				else:
					l = box[0] + box[2]
					d.fgcolor((0,0,0))
					d.drawbox(box)
##					print 'box', box
		elif self.mother.thumbnails and \
		     settings.get('RPthumbnails') and \
		     thumb_w > 0 and thumb_h > 0 and \
		     self.node.GetChannelType() == 'RealPix' and \
		     hasattr(self.node, 'slideshow'):
			import MMurl
			start = 0
			node_t0 = self.node.GetTimes()[0]
			for attrs in self.node.slideshow.rp.tags:
				start = start + attrs.get('start', 0)
				if attrs.get('tag', 'fill') in ('fadein', 'crossfade', 'wipe') and attrs.get('file'):
					x = self.mother.maptimes(node_t0+start, 0)[0]
					try:
						f = MMurl.urlretrieve(self.node.context.findurl(attrs.get('file')))[0]
					except IOError:
						pass
					else:
						clip = (l+xindent, t+yindent, r-l-2*xindent, b-t-2*yindent)
						try:
							box = d.display_image_from_file(f, center = 0, coordinates = (x+xindent, thumb_t, thumb_w, thumb_h), clip = clip)
						except windowinterface.error:
							pass
						else:
							d.fgcolor((0,0,0))
							d.drawbox(box, clip = clip)

		# Draw the name, centered in the box
		d.fgcolor(TEXTCOLOR)
		d.centerstring(l, t, r, b, self.name)

	def getbandwidthdata(self):
		if not self.node.WillPlay():
			return None
		t0, t1, t2, dummy, dummy = self.node.GetTimes()
		try:
			prearm, bandwidth = Bandwidth.get(self.node)
		except Bandwidth.Error, msg:
			self.node.set_infoicon('error', msg)
			prearm = bandwidth = 0
		return t0, t2, self, prearm, bandwidth

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
		if top.hierarchyview is not None:
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
		t0, t1, t2, dummy, dummy = self.node.GetTimes()
		left, right = self.mother.maptimes(t0, t2)
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
		self.menutitle = 'Sync arc ops'
		ArcBoxCommand.__init__(self)

	def mkcommandlist(self):
		if self.commandlist:
			return
		GO.mkcommandlist(self)
		self.commandlist = self.commandlist + [
			ATTRIBUTES(callback = (self.attrcall, ())),
			DELETE(callback = (self.delcall, ())),
			]

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

	def attrcall(self):
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
