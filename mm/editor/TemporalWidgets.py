__version__ = "$Id:"

# Known bugs:
# * the tree next to the channels isn't drawn correctly sometimes.
# * Structure nodes overlap each other.

# TODO:
# * Collapsing nodes
# * Collapsing regions
# * Show the time scale.
# * Drag and drop

import types

import Widgets
import Bandwidth
import MMurl, MMAttrdefs, MMmimetypes, MMNode
import features
import os, windowinterface
import settings
from AppDefaults import *
from GeometricPrimitives import *

# Import some useful, already-written widgets.
from StructureWidgets import MMNodeWidget, StructureObjWidget, Icon

class GeoDisplayWidget:
	def set_display(self, g):
		self.graph = g


######################################################################
# The main container.
######################################################################

# Global pointer statuses.
# Maybe not needed.
NORMAL = 0
DRAGGING_NODE = 1
MOVE_NODE_START = 2
MOVE_NODE_END = 3
MOVE_CHANNEL = 4

# Some sizes and colors.
BARWIDTH = settings.get('temporal_barwidth')
CHANNELWIDTH = settings.get('temporal_channelwidth')
NODESTART = settings.get('temporal_nodestart')
#NODEEND = settings.get('temporal_nodeend')
CHANNELHEIGHT = settings.get('temporal_channelheight')
CHANNELTREEINDENT = 8
CCHAN = settings.get('temporal_channelcolor')
CNODE = settings.get('temporal_nodecolor')
CPAR = settings.get('temporal_parcolor')
CSEQ = settings.get('temporal_seqcolor')
CEXCL = settings.get('temporal_exclcolor')
CPRIO = settings.get('temporal_priocolor')
CSWITCH = settings.get('temporal_switchcolor')
TIMESCALE = settings.get('temporal_timescale')
CFILLTIME = settings.get('temporal_fillcolor')

class TimeCanvas(MMNodeWidget, GeoDisplayWidget):
	# This implements a container that contains time-based classes.
	# It is a facade to deal with the rest of the widgets here.
	# Issues to deal with:
	# * Channels may or may not be the y axis.
	# * Time will be the x axis.
	# * There will be breaks in time to accommodate structure nodes.
	# * This may or may not have a playback bar attached to it (how I
	#   wish I could use a decent widget set..)

	# Note that this class is tightly coupled to the TemporalView.

	def __init__(self, node, mother, minimal_channels = 0):
		MMNodeWidget.__init__(self, node, mother)
		self.root_mm_node = node
		self._factory = global_factory
		self._factory.set_mother(mother)
		self.channelHeight = CHANNELHEIGHT # getting hacky. Oh well.

		self.maxtime = self.node.GetTimes()[1]
		self.start_breaks = {} # A dictionary of the breaks from the start of a struct node
		self.end_breaks = {} # same, maps times to lists of nodes.
		self.breaks_cache = [] # A cache for improving times to fetch from the cache.

		self.structnodes = []	# A sorted list, by time of the structure nodes.

		global_factory.timecanvas = self
		self.node_channel_mapping = {} # A dictionary of channel names -> lists of nodes in that channel.
		self.mainnode = self.__init_create_widgets(self.node)
		if minimal_channels:
			self.channeltree = global_factory.createminimalchanneltree(node)
		else:
			self.channeltree = global_factory.createchanneltree(node)
		self.editmgr = node.context.editmgr
		self.timescale = TIMESCALE

		self.pointer_object_of_interest = None # Which object looks appealing to the selection.

	def setup(self):
		pass

	def destroy(self):
		self.mainnode.destroy()
		self.channeltree.destroy()
		self.structnodes = None
		self.start_breaks = None
		self._factory = None
		self.root_mm_node = None

	def set_maxtime(self, time):
		# Sets the maximum time for this presentation.
		self.maxtime = time

	def __init_create_widgets(self, node):
		# this is a recursive function. The current widget is the widget which the node(s)
		# get inserted into.
		t = node.type
		# All leaf nodes should be checked already.
		if t == 'seq':
			container = self._factory.createseq(node)
		elif t == 'par':
			container = self._factory.createpar(node)
		elif t == 'excl':
			container = self._factory.createexcl(node)
		elif t == 'alt':
			container = self._factory.createswitch(node)
		elif t == 'prio':
			container = self._factory.createprio(node)
		else:
			assert 0
		self.structnodes.append(container)

		# populate the node.
		for i in node.children:
			if i.type in MMNode.leaftypes:
				# i is a leafnode
				bob = self._factory.createnode(i)
				n = bob.get_channel()
				if self.node_channel_mapping.has_key(n):
					self.node_channel_mapping[n].append(bob)
				else:
					self.node_channel_mapping[n] = [bob]
			else:
				# i is a struct node.
				bob = self.__init_create_widgets(i)
				self._add_breaks(bob)
				# TODO: what do I do with the struct nodes?
			container.add(bob)
		return container

	def _add_breaks(self, widget):
		# Add this to the breaks in the timeline.
		nodetimes = widget.node.GetTimes()
		if self.start_breaks.has_key(nodetimes[0]):
			self.start_breaks[nodetimes[0]].append(widget)
		else:
			self.start_breaks[nodetimes[0]] = [widget]
		
		if self.end_breaks.has_key(nodetimes[1]):
			self.end_breaks[nodetimes[1]].append(widget)
		else:
			self.end_breaks[nodetimes[1]] = [widget]
		self.breaks_cache.append(nodetimes[0])
		self.breaks_cache.append(nodetimes[1])
		self.breaks_cache.sort() # TODO: slow.

	def moveto(self, (l,t,r,b)):
		# See also self.recalc()
		# This affects my timescale.

		# Blatantly ignore l and t
		l = 0
		t = 0
		MMNodeWidget.moveto(self, (l,t,r,b))

	def recalc(self, zoom=1):
		t = 2
		l = 2
		r = 2 + CHANNELWIDTH
		self.channeltree.moveto((2,2,CHANNELWIDTH+2, CHANNELHEIGHT+2))
		iter = self.channeltree.get_LRiter()
		while iter.next():
			w_channel = iter.get()
			w_channel_name = w_channel.get_name()
			x,y,w,h = w_channel.get_box()
			if self.node_channel_mapping.has_key(w_channel_name):
				for i in self.node_channel_mapping[w_channel_name]:
					yr = y + CHANNELHEIGHT*i.get_channel_index()
					i.set_y(yr,yr+CHANNELHEIGHT)
		self.channeltree.recalc()

		# nwidth is the needed width for this.
		nwidth = self.mainnode.get_width(self.timescale) * zoom
		# Make it a reasonable value.
		#while nwidth > 2000:
		#	nwidth = nwidth / 2
		#while nwidth < 100:
		#	nwidth = nwidth * 2

		# Predict the number of bars needed:
		numbars = self.mainnode.guess_num_bars()
		times = self.mainnode.GetTimes()
		# Check that they are reasonable numbers:
		if times[0] == 0 and times[2] > 0 and times[2] < 9999999:
			# Used later, esp. in sequences for working out timing information.
			self.pixels_per_time = nwidth / (times[2] - times[0]) # doesn't include the bars!
		else:
			print "Warning: Weird timing information."
			self.pixels_per_time = 1
		self.mainnode.moveto((NODESTART, 2, NODESTART+nwidth+numbars*BARWIDTH, t+self.channelHeight+2))
		self.mainnode.recalc()

	def click(self, coords):
		# What was clicked: a channel or a node?
		x,y = coords
		if x < CHANNELWIDTH:	# A channel was selected.
			self.select_channel(self.channeltree.get_obj_at(coords))
		else:
			node = self.get_node_at(coords)
			self.select_node(node)

	def get_node_at(self, coords):
		# Check the structure nodes.
		for i in self.structnodes:
			if i.is_hit(coords):
				return i

		# Check the leaf nodes.
		channel = self.channeltree.get_obj_at(coords)
		if channel:
			channelname = channel.get_name()
			try:
				for n in self.node_channel_mapping[channelname]:
					if n.is_hit(coords):
						return n
			except KeyError:
				pass
		return None

	def select_channel(self, w_channel):
		# Note that the channel given in the parameters is a widget, not a MMChannel.
		# You get the MMChannel by calling the "get_channel" method.
		self.mother.unselect_channels()
		if isinstance(w_channel, ChannelWidget):
			w_channel.select()
			self.mother.select_channel(w_channel)
			self.channeltree.recalc()

	def select_mmchannel(self, mmchannel):
		if isinstance(mmchannel, MMNode.MMChannel):
			channelw = mmchannel.views['TemporalView']
			self.select_channel(channelw)

	def select_node(self, mmwidget):
		# TODO: also structure nodes.
		self.mother.unselect_nodes()
		if isinstance(mmwidget, MMWidget) or isinstance(mmwidget, MultiMMWidget):
			self.mother.select_node(mmwidget)
			mmwidget.select()

	def dragging_node(self, tgtcoords, srccoords, mode):
		return windowinterface.DROPEFFECT_NONE

	def dropnode(self, srccoords, tgtcoords):
		sx,sy = srccoords
		tx, ty = tgtcoords

		# Find the source.
		if sx < CHANNELWIDTH:	# The source is a channel.
			source = self.channeltree.get_obj_at(srccoords)
		else:
			source = self.get_node_at(srccoords)

		if source is None:
			return 0

		# Find the target.
		if tx < CHANNELWIDTH:
			target = self.channeltree.get_obj_at(tgtcoords)
		else:
			target = self.get_node_at(tgtcoords)

		if target:
			target.happily_receive_dropped_object(source)
		else:
			self.happily_receive_dropped_object(source)

	def dropfile(self, coords, url):
		# I received a file. Yay.
		x,y = coords
		if x < CHANNELWIDTH:
			windowinterface.beep()
			return
		else:
			tgt = self.get_node_at(coords)

		if tgt is None:
			return

		channel = self.channeltree.get_obj_at(coords)
		tgt.happily_receive_dropped_file(url, channel)

	def happily_receive_dropped_object(self, obj):
		pass


######################################################################
# A factory to create new widgets in this file.
######################################################################

class TemporalWidgetFactory:
	# A singleton factory which creates widgets based on node types.
	def createnode(self, m):
		assert isinstance(m, MMNode.MMNode)
		bob = MMWidget(m, self.mother)
		bob.timecanvas = self.timecanvas
		bob.set_display(self.mother.get_geodl())
		bob.setup()
		return bob

	def createchannel(self, c):
		assert isinstance(c, MMNode.MMChannel) or c is None
		bob = ChannelWidget(self.mother)
		graph = self.mother.get_geodl()
		bob.set_channel(c)
		bob.set_display(graph)
		bob.editmgr = self.editmgr
		try:
			bob.nodewidgets = self.timecanvas.node_channel_mapping[c.name]
		except Exception:
			bob.nodewidgets = []
			print "Warning: channel has no widgets mapped to it:", c.name
		bob.setup()
		return bob

	def createchanneltree(self, node):
		bob = ChannelTree(self.mother)
		bob.cpos = (0,2,CHANNELWIDTH,CHANNELHEIGHT)
		bob.set_rootmmnode(node)
		graph = self.mother.get_geodl()
		bob.set_display(graph)
		bob.setup()
		return bob

	def createminimalchanneltree(self, node):
		bob = MinimalChannelTree(self.mother)
		bob.cpos = (0,2,CHANNELWIDTH,CHANNELHEIGHT)
		bob.set_rootmmnode(node)
		bob.timecanvas = self.timecanvas
		graph = self.mother.get_geodl()
		bob.set_display(graph)
		bob.setup()
		return bob

	def createseq(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = SeqMMWidget(node, self.mother)
		bob.set_display(self.mother.get_geodl())
		bob.timecanvas = self.timecanvas
		bob.setup()
		return bob

	def createpar(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = ParMMWidget(node, self.mother)
		bob.timecanvas = self.timecanvas
		bob.set_display(self.mother.get_geodl())
		bob.setup()
		return bob

	def createexcl(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = ExclMMWidget(node, self.mother)
		bob.timecanvas = self.timecanvas
		bob.set_display(self.mother.get_geodl())
		bob.setup()
		return bob

	def createswitch(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = SwitchMMWidget(node, self.mother)
		bob.timecanvas = self.timecanvas
		bob.set_display(self.mother.get_geodl())
		bob.setup()
		return bob

	def createprio(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = PrioMMWidget(node, self.mother)
		bob.timecanvas = self.timecanvas
		bob.set_display(self.mother.get_geodl())
		bob.setup()
		return bob

	def set_mother(self, mother):
		self.mother = mother
		self.editmgr = mother.editmgr

	def setup(self):
		return

global_factory = TemporalWidgetFactory()


######################################################################
# The widgets.
######################################################################

class ChannelTree(Widgets.Widget, GeoDisplayWidget):
	# This is an interactive tree of channels, regions and viewports. Dang.
	# The y coordinates of the channels need to be available to the TimeWidgets.
	# Does this widget have geometric primitives?

	def setup(self):
		self.channeltree = []	# A list of channel widgets.
		self.widgets = []	# The lines that the tree is made of.
		self.channelhelper = self.node.GetContext().getchanneltree()
		self.viewports = self.channelhelper.getviewports()
		for i in self.viewports: # Adds all the channels to this tree.
			self.add_channel_to_bottom(i, 0) # recursively add the viewport and it's children.

	def __repr__(self):
		return "ChannelTree " + repr(self.channeltree)

	def set_rootmmnode(self, node):
		self.node = node

	def destroy(self):
		for i in self.widgets:
			self.graph.DelWidget(i)
		self.viewports = None
		for i in self.channeltree:
			i.destroy()
		self.channelhelper = None

	def get_viewports(self):
		return self.viewports

	def get_LRiter(self):
		return LRChannelTreeIter(self.channeltree)

	def minimise(self):
		self.minimal_channels = 1

	def recalc(self):
		# Add lines to show where the tree is.
		currentindent = 0
		currentvline = None	# I wish you could define variables in Python.
		x,y,w,h = self.get_box()
		top = y
		levels = []		# A stack for iterative recursion

		for i in self.widgets:
			self.graph.DelWidget(i)
		self.widgets = []
		for chan in self.channeltree:
			tx, ty, tw, th = chan.get_box()
			indent = chan.get_depth()
			leftpos = tx + (indent-1)*CHANNELTREEINDENT + CHANNELTREEINDENT/2
			
			bob = self.graph.AddWidget(Line(self.mother))
			bob.moveto((
				leftpos,
				ty+CHANNELHEIGHT/2,
				leftpos + CHANNELTREEINDENT/2,
				ty+CHANNELHEIGHT/2))
			self.widgets.append(bob)

			if indent == currentindent:
				if currentvline:
					currentvline.moveto((
						leftpos,
						top,
					leftpos,
						ty+th-CHANNELHEIGHT/2))
			elif indent > currentindent:
				# The current line gets promoted to a parent.
				# Every parent has a vertical line on it.
				# WORKING HERE
				currentvline = self.graph.AddWidget(Line(self.mother))
				self.widgets.append(currentvline)
				currentvline.moveto((
					leftpos,
					ty + CHANNELHEIGHT/2,
					leftpos,
					ty+CHANNELHEIGHT))
				levels.append((top, currentvline))
				top = ty
				currentindent = indent;
			else: # indent < currentindent
				tail = levels[len(levels)-1]
				levels = levels[:len(levels)-1]
				top, currentvline = tail
				currentindent = indent

	def add_channel_to_bottom(self, channel, treedepth):
		# This is a recursive function that adds not only this channel ,but
		# also all of it's children.
		# treedepth is the depth into the channel tree, thus it is proportional to the x coordinate.
		bob = global_factory.createchannel(channel)
		self.channeltree.append(bob)
		bob.set_depth(treedepth)
		x,y,w,h = self.cpos
		cheight = bob.get_height()
		bob.moveto((x,y,x+w,y+CHANNELHEIGHT*cheight))
		self.cpos = (x,y+CHANNELHEIGHT*cheight+2,w,CHANNELHEIGHT)
		# add all subchannels to the tree also.
		for i in self.channelhelper.getsubregions(channel):
			self.add_channel_to_bottom(i, treedepth+1)

	def get_obj_at(self, coords):
		x,y = coords
		for chan in self.channeltree:
			cx,cy,cw,ch = chan.get_box()
			if cy < y <= cy+ch:
				return chan


class MinimalChannelTree(ChannelTree):
	def setup(self):
		self.mapping = self.timecanvas.node_channel_mapping
		ChannelTree.setup(self)

	def recalc(self):
		# No, I /don't/ want a tree.
		for i in self.widgets:
			self.graph.DelWidget(i)
		self.widgets = []

	def __repr__(self):
		return "Minimal channel tree " + repr(self.channeltree)

	def add_channel_to_bottom(self, channel, treedepth):
		# ignore the treedepth
		try:
			if len(self.mapping[channel.name]) > 0:
				# Then add this channel to the bottom.
				bob = global_factory.createchannel(channel)
				self.channeltree.append(bob)
				bob.set_depth(0)
				x,y,w,h = self.cpos
				cheight = bob.get_height()
				bob.moveto((x,y,x+w,y+CHANNELHEIGHT*cheight))
				self.cpos = (x,y+CHANNELHEIGHT*cheight+2,w,CHANNELHEIGHT)
		except KeyError:
			pass
		for i in self.channelhelper.getsubregions(channel):
			self.add_channel_to_bottom(i, 0)



class LRChannelTreeIter:
	# Left -> Right Iterater for the ChannelTree class.
	# This breaks encapsulation a bit, but that doesn't matter.
	def __init__(self, channeltree):
		self.channeltree = channeltree
		self.reset()
	def reset(self):
		self.pos = -1		# You must call iter.next() at least once before using.
	def next(self):
		self.pos = self.pos + 1
		if self.pos < len(self.channeltree):
			return 1
		else:
			return 0
	def prev(self):
		if self.pos > 0:
			self.pos = self.pos - 1
			return 1
		else:
			return 0
	def get(self):
		try:
			return self.channeltree[self.pos]
		except IndexError:
			print "Index Error,  position is: ", self.pos
			assert 0
			# If the channel doesn't exist, that means that no nodes have that channel.


class ChannelWidget(Widgets.Widget, GeoDisplayWidget):
	# A widget representing a certain channel.
	def setup(self):
		# Once this widget has recieved something to display on, it can create some
		# widgets.
		if self.channel:
			self.name = self.channel.name
			self.channel.views['TemporalView'] = self
		else:
			print "ERROR: I have no channel"
			self.name = 'undefined'
#		self.nodewidgets = []		# A list of all node widgets in this channel.
		self.w_fbox = self.graph.AddWidget(FBox(self.mother))
		self.w_fbox.set_color((232,193,152))
#		self.w_outerbox = self.graph.AddWidget(Box(self.mother))
		self.w_name = self.graph.AddWidget(Text(self.mother))
		self.w_name.align('l')
		self.w_name.set_text(self.name)

	def destroy(self):
#		for i in self.nodewidgets:
#			i.destroy()	# nodes is a list of mmwidgets, not MMNodes.
		self.nodewidgets = None
#		self.graph.DelWidget(self.w_outerbox)
		self.graph.DelWidget(self.w_name)
		self.graph.DelWidget(self.w_fbox)

	def set_depth(self, d):
		self.depth = d
	def get_depth(self):
		return self.depth

	def set_channel(self, c):
		self.channel = c
	def get_channel(self):
		return self.channel

	def set_canvas(self, c):
		# The canvas is used to find the time position of elements.
		self.canvas = c

	def select(self):
		Widgets.Widget.select(self)
		self.w_fbox.set_color((250,230,230))
		self.w_name.need_redraw()

	def unselect(self):
		Widgets.Widget.unselect(self)
		self.w_fbox.set_color((232,193,152))
		self.w_name.need_redraw()

	def moveto(self, coords):
		# Take my widgets with me.
		l,t,r,b = coords
		Widgets.Widget.moveto(self, coords)
#		self.w_outerbox.moveto(coords)
		self.w_name.moveto((l+2+CHANNELTREEINDENT*self.depth, t, r, t+2+self.w_name.get_height()))
		self.w_fbox.moveto(coords)

		mx, my, mw, mh = self.get_box()

	def append(self, value):
		assert isinstance(value, MMWidget)
		# Append a node to this channel.
		self.nodewidgets.append(value)

	def is_hit_y(self, coords):
		hx,hy = coords
		x,y,w,h = self.get_box()
		if y < hy < y+h:
			return 1
		else:
			return 0

	def get_draggable(self, coords):
		return []

	def get_name(self):
		return self.name

	def get_height(self):
		# Return the number of MMWidgets high I need to be to fit them in.
		stack = []
		max = 0
		for node in self.nodewidgets:
			# Resolve the stack - time is now the start time of the node.
			time = node.get_starttime()
			iindex = -1
			for i in stack:
				if i.get_endtime() <= time:
					iindex = stack.index(i)
			# This is a hack because Python won't let you assign out of a list.
			if iindex == -1:
				iindex = len(stack)
				stack.append(node)
			else:
				stack[iindex] = node
			node.set_channel_index(iindex)
			if max < len(stack):
				max = len(stack)
		if max < 1:
			return 1
		else:
			return max

	def happily_receive_dropped_object(self, obj):
		if isinstance(obj, TimeWidget):
			# It's a node.
			obj.change_channel(self.name)
		elif isinstance(obj, ChannelWidget):
			# Don't really know what to do.
			windowinterface.beep()



######################################################################
	# The node representations
######################################################################

class TimeWidget(MMNodeWidget, GeoDisplayWidget):
	# Abstract base class for any widget that has a start and end time.
	# Instances of superclasses must be drawn on a time canvas (coords are 
	def setup(self):
		self.editmgr = self.node.context.editmgr
		self.node.views['tempview'] = self

	def destroy(self):
		if self.node.views:
			del self.node.views['tempview']

	def set_x(self, l,r):
		x,y,w,h = self.get_box()
		self.moveto((l,y,r,y+h))
		
	def set_y(self, t,b):
		x,y,w,h = self.get_box()
		self.moveto((x,t,x+w,b))

	def GetTimes(self):
		return self.node.GetTimes()

	def get_starttime(self):
		return self.node.GetTimes()[0]

	def get_endtime(self):
		return self.node.GetTimes()[1]

	def get_width(self, timescale):
		times = self.node.GetTimes()
		return (times[1] - times[0])*timescale

	def guess_num_bars(self):
		self.needed_bars = 0
		return 0;

	def select_parents(self):
		if self.node.parent and self.node.parent.views.has_key('tempview'):
			self.node.parent.views['tempview'].select_parents()
		if not self.selected:
			self.select()

	def unselect_parents(self):
		if self.node.parent and self.node.parent.views.has_key('tempview'):
			self.node.parent.views['tempview'].unselect_parents()
		if self.selected:
			self.unselect()

	def happily_receive_dropped_object(self, obj):
		if isinstance(obj, ChannelWidget):
			windowinterface.beep()
		elif isinstance(obj, TimeWidget):
			if obj is self:
				windowinterface.beep()
			else:
				# Append that object to the end of this one.
				pass
		else:
			windowinterface.beep()

	def happily_receive_dropped_file(self, url, channel):
		return			# Virtual function.


class MMWidget(TimeWidget, GeoDisplayWidget):
	# This is the box which represents one leaf node.
	# I am a slave to my channel. My channel will resize me and move me around.
	def setup(self):
		TimeWidget.setup(self)
		self.w_fbox = self.graph.AddWidget(FBox(self.mother))
		self.w_fbox.set_color(CNODE)
		self.w_outerbox = self.graph.AddWidget(Box(self.mother))
		self.w_filltimeouterbox = self.graph.AddWidget(Box(self.mother))
		self.w_filltimebox = self.graph.AddWidget(FBox(self.mother))
		self.w_filltimebox.set_color(CFILLTIME);
		self.name = self.node.GetAttrDef('name', '')
		self.w_text = self.graph.AddWidget(Text(self.mother))
		self.w_text.set_text(self.name)
		self.w_icon = self.graph.AddWidget(Image(self.mother))
		self.w_icon.set_file(self.node.GetTypeIconFile())

	def destroy(self):
		# TODO: remove me from the list of MMNode Views.
		TimeWidget.destroy(self)
		self.graph.DelWidget(self.w_outerbox)
		self.graph.DelWidget(self.w_text)
		self.graph.DelWidget(self.w_fbox)
		self.graph.DelWidget(self.w_filltimebox)
		self.graph.DelWidget(self.w_filltimeouterbox)
		self.graph.DelWidget(self.w_icon)

	def moveto(self, coords):
		l,t,r,b = coords
		if r-l < BARWIDTH:
			self.hide()
			return
		TimeWidget.moveto(self, coords)
		self.w_text.moveto(coords)

		start_time, end_time, endfill_time, download_delay, begin_delay = self.node.GetTimes()
		# l is proportional to start_time, r is proportional to endfill_time
		# middle is proportional to end_time, which is where the boxes change color.
		# so if 'f' is the fraction of the bar that is not fill time,
		try:
			f = (end_time-start_time) / (endfill_time - start_time)
		except ZeroDivisionError:
			f = 0
		middle = f * (r-l) + l
		if middle-l < CHANNELHEIGHT:
			middle = CHANNELHEIGHT+l
			if r < middle:
				r = middle
		self.w_outerbox.moveto((l,t,middle, b))
		self.w_fbox.moveto((l,t,middle,b))
		# This overlaps the borders a bit to make the fill part and the play part merge a bit.
		self.w_filltimebox.moveto((middle-1, t+(1.0/5*float(b-t))+1,r,(b-(1.0/5*float(b-t)))-1))
		self.w_filltimeouterbox.moveto((middle, t+(1.0/5*float(b-t)),r,(b-(1.0/5*float(b-t)))))
		self.w_icon.moveto((l-2,t+1,l+CHANNELHEIGHT+2,t+CHANNELHEIGHT-2)) # counters off-by-one errors.


	def hide(self):
		return
		# for all of my widgets, call w.hide()
		self.hidden = 1

	def set_channel(self, c):
		print "TODO: change this node's channel."

	def get_channel(self):
		# Returns a string which is this node's channel.
		if not self.node.GetChannel():
			print "ERROR: no channel", self.node, self.node.GetChannel()
			return 'undefined'
		return self.node.GetChannel().GetLayoutChannel().name

	def select(self):
		Widgets.Widget.select(self)
		self.w_fbox.need_redraw()
		self.w_outerbox.set_color((255,255,255))
		self.w_filltimeouterbox.set_color((255,255,255))
		self.w_filltimebox.need_redraw()
		self.w_text.need_redraw()
		self.w_icon.need_redraw()
		# Also select my superiors.
		self.select_parents()
	def unselect(self):
		Widgets.Widget.unselect(self)
		self.w_fbox.need_redraw()
		self.w_outerbox.set_color((0,0,0))
		self.w_filltimeouterbox.set_color((0,0,0))
		self.w_filltimebox.need_redraw()
		self.w_text.need_redraw()
		self.w_icon.need_redraw()
		self.unselect_parents()

#	def select(self):
#		self.w_fbox.set_color((230,230,230))
#	def unselect(self):
#		self.w_fbox.set_color(CNODE)

	def get_draggable(self, coords):
		# return a box.
		b = self.graph.AddWidget(DraggableBox(self.mother))
		x,y,w,h = self.get_box()
		b.moveto((x,y,x+w,y+h))
		return [b]

	def get_y_start(self):
		# Assuming that this node has been assigned a channel already.
		x,y,w,h = self.get_box()
		return y,y+h
	get_y_end = get_y_start

	def GetChannelName(self):
		return self.get_channel()

	def recalc(self):
		pass

	def is_hit(self, coords):
		return self.w_fbox.is_hit(coords) or self.w_filltimebox.is_hit(coords)

	def get_node_at(self, foobar):
		return 0

	def set_channel_index(self, i):
		self.channel_index = i;
	def get_channel_index(self):
		return self.channel_index

	def change_channel(self, channelstr):
		# Er.. see also set_channel.
		print "TODO: change a node's channel."

	def accepts_droppable_object(self, obj):
		return 0		# never.

	def happily_receive_dropped_object(self, obj):
		# What is a leaf node going to do with an object?
		windowinterface.beep()

	def happily_receive_dropped_file(self, url, channel):
		self.node.SetURL(url)	# the node handles the edit manager.


class MultiMMWidget(TimeWidget):
	# represents any node which has children.
	def setup(self):
		TimeWidget.setup(self)
		self.subwidgets = []
		self.leafnode = 0;	# will hide all children if I am.
	def add(self, bob):
		self.subwidgets.append(bob)
	def destroy(self):
		TimeWidget.destroy(self)
		for i in self.subwidgets:
			i.destroy()
	def is_hit(self, coords):
		if self.w_startbar.is_hit(coords) or self.w_endbar.is_hit(coords):
			return 1
		else:
			return 0
	def get_node_at(self, coords):
		if self.is_hit(coords):
			return self
		else:
			for i in self.subwidgets:
				if i.is_hit(coords):
					return i
				else:
					return i.get_node_at(coords)

	def select(self):
		TimeWidget.select(self)
		r,g,b = self.color
		highlight = (r*1.5, g*1.5, b*1.5)
		self.w_startbar.set_color(highlight)
		self.w_endbar.set_color(highlight)
		self.w_startbar_b.need_redraw()
		self.w_endbar_b.need_redraw()	       

	def unselect(self):
		TimeWidget.unselect(self)
		self.w_startbar.set_color(self.color)
		self.w_endbar.set_color(self.color)
		self.w_startbar_b.need_redraw()
		self.w_endbar_b.need_redraw()		

	def collapse(self):
		self.leafnode = 1
	def uncollapse(self):
		self.leafnode = 0

	def change_channel(self, new_channel):
		return			# Structure nodes don't have channels.

	def accepts_droppable_object(self, obj):
		if isinstance(obj, TimeWidget):
			return 1
		else:
			return 0

	def happily_receive_dropped_object(self, obj):
		if isinstance(obj, TimeWidget):
			self.node.take(obj.node, -1) # Add at end.
		else:
			# It is no type of object that I know of.
			windowinterface.beep()

	def happily_receive_dropped_file(self, url, channel):
		# Add the file as a new leaf node.
		self.node.NewLeafNode(url=url)

class SeqMMWidget(MultiMMWidget):
	# Represents a seq widget on the screen

	def setup(self):
		self.color = CSEQ
		MultiMMWidget.setup(self)
		self.y_start_cached = None
		self.y_end_cached = None
		self.w_startbar = self.graph.AddWidget(FBox(self.mother))
		self.w_startbar_b = self.graph.AddWidget(Box(self.mother))
		self.w_endbar = self.graph.AddWidget(FBox(self.mother))
		self.w_endbar_b = self.graph.AddWidget(Box(self.mother))
		self.w_startbar.set_color(self.color)
		self.w_endbar.set_color(self.color)
		self.w_lines = []
		self.w_endline = self.graph.AddWidget(Line(self.mother))

	def destroy(self):
		MultiMMWidget.destroy(self)
		self.graph.DelWidget(self.w_startbar)
		self.graph.DelWidget(self.w_startbar_b)
		self.graph.DelWidget(self.w_endbar)
		self.graph.DelWidget(self.w_endbar_b)
		for i in self.w_lines:
			self.graph.DelWidget(i)
		self.graph.DelWidget(self.w_endline)

	def add(self, bob):
		MultiMMWidget.add(self, bob)
		self.w_lines.append(self.graph.AddWidget(Line(self.mother)))

	def __repr__(self):
		return "I'm a SeqMMWidget"

	def recalc(self):
		# iterate through my subwidgets, resizing each.
		mytimes = self.node.GetTimes()
		x,y,w,h = self.get_box()
		endx = x + w # - BARWIDTH + BARWIDTH
		bars_so_far = 0

		# Add the start and end bars.
		# TODO: Make this better.
		t, b = self.get_y_start()
		self.w_startbar.moveto((x,t,x+BARWIDTH,b))
		self.w_startbar_b.moveto((x,t,x+BARWIDTH,b))
		t,b = self.get_y_end()
		self.w_endbar.moveto((x+w-BARWIDTH, t, x+w, b))
		self.w_endbar_b.moveto((x+w-BARWIDTH, t, x+w, b))

		x = x + BARWIDTH
		w = w - 2*BARWIDTH
		prevx = x
		prevy = (t+b)/2
		if mytimes[2]>mytimes[0]:
			endtime = mytimes[2]
			ppt = self.timecanvas.pixels_per_time
			for i in range(0, len(self.subwidgets)):
				ctime = self.subwidgets[i].GetTimes()
				cl = (ctime[0]-mytimes[0])*ppt + x + bars_so_far
				cendtime = ctime[2]
				this_bars = self.subwidgets[i].needed_bars * BARWIDTH
				nodewidth = (cendtime-mytimes[0])*ppt + this_bars
				cr = nodewidth + x + bars_so_far
				self.subwidgets[i].set_x(cl, cr)
				self.subwidgets[i].recalc()
				y1, y2 = self.subwidgets[i].get_y_end()
				self.w_lines[i].moveto((prevx, prevy, cl, (y1+y2)/2))
				# WORKING HERE - Things don't look quite right yet.
				prevx = cr
				prevy = (y1+y2)/2
				bars_so_far = bars_so_far + this_bars
		else:
			print "Error: undrawable node: ", self.node

		self.w_endline.moveto((prevx, prevy, endx-BARWIDTH , (t+b)/2))

	def get_y_start(self):
		if self.y_start_cached is not None:
			return self.y_start_cached
		else:
			if len(self.subwidgets) > 0:
				bob = self.subwidgets[0].get_y_start()
				self.y_start_cached = bob
				return bob
			else:
				return (2,CHANNELHEIGHT)

	def get_y_end(self):
		if self.y_end_cached is not None:
			return self.y_end_cached
		else:
			if len(self.subwidgets) > 0:
				bob = self.subwidgets[len(self.subwidgets)-1].get_y_end()
				self.y_end_cached = bob
				return bob
			else:
				return (2,CHANNELHEIGHT)

	def guess_num_bars(self):
		return_me = 0
		for i in self.subwidgets:
			return_me = return_me + i.guess_num_bars()
		self.needed_bars = 2 + return_me
		return 2 + return_me


class BarMMWidget(MultiMMWidget):
	# The base class for pars, switches, Excls.
	def setup(self):
		MultiMMWidget.setup(self)
		self.w_startbar = self.graph.AddWidget(FBox(self.mother))
		self.w_startbar.set_color(self.color)
		self.w_startbar_b = self.graph.AddWidget(Box(self.mother))
		self.w_endbar = self.graph.AddWidget(FBox(self.mother))
		self.w_endbar.set_color(self.color)
		self.w_endbar_b = self.graph.AddWidget(Box(self.mother))
		self.y_start_cached = None
		self.y_end_cached = None

	def __repr__(self):
		return "I'm a BarMMWidget"

	def moveto(self, coords):
		size = BARWIDTH
		l,t,r,b = coords
		TimeWidget.moveto(self,coords)
		
	def destroy(self):
		MultiMMWidget.destroy(self)
		self.graph.DelWidget(self.w_startbar)
		self.graph.DelWidget(self.w_startbar_b)
		self.graph.DelWidget(self.w_endbar)
		self.graph.DelWidget(self.w_endbar_b)

	def recalc(self):
		# recurse through my subwidgets, resizing each.
		# also, set the bar sizes.
		mytimes = self.node.GetTimes()
		x,y,w,h = self.get_box()

		# Set the bars position
		# The start bar..
		t,b = self.get_y_start()
		self.w_startbar.moveto((x, t, x+BARWIDTH, b))
		self.w_startbar_b.moveto((x,t,x+BARWIDTH,b))
		# The end bar..
		t,b = self.get_y_end()
		if w < 2*BARWIDTH:
			w = 2*BARWIDTH
		self.w_endbar.moveto((x+w-BARWIDTH, t, x+w, b))
		self.w_endbar_b.moveto((x+w-BARWIDTH, t, x+w, b))
		w = w - 2*BARWIDTH	# remember the size of the bars!
		x = x + BARWIDTH
		
		if mytimes[2] > mytimes[0]:
			endtime = mytimes[2]
			ppt = w/(endtime-mytimes[0])	# pixels per time
			for i in self.subwidgets:
				ctime = i.GetTimes()
				cl = (ctime[0]-mytimes[0])*ppt
				cr = (endtime-mytimes[0])*ppt
				i.set_x(cl+x, cr+x)
				i.recalc()
		else:
			print "Error: times are equal: ", mytimes[0], mytimes[1]

	def get_y_start(self):
		# returns a tuple of the top and bottom of the front of this node.
		if self.y_start_cached is not None:
			return self.y_start_cached
		elif len(self.subwidgets) > 0:
			# calculate the highest and lowest widgets.
			highest = None
			lowest = None
			for i in self.subwidgets:
				t,b = i.get_y_start()
				if highest == None:
					highest = t
				elif t < highest:
					highest = t
				if lowest == None:
					lowest = b
				elif b > lowest:
					lowest = b
			self.y_start_cached = (highest, lowest)
			return (highest, lowest)
		else:
			# TODO: node with no subwidgets.
			return (2,CHANNELHEIGHT)

	def get_y_end(self):
		# returns a tuple of the top and bottom of the end of this node
		if self.y_end_cached is not None:
			return self.y_end_cached
		elif len(self.subwidgets) > 0:
			highest = None
			lowest = None
			for i in self.subwidgets:
				(t,b) = i.get_y_end()
				if highest == None:
					highest = t
				elif t < highest:
					highest = t
				if lowest == None:
					lowest = b
				elif b > lowest:
					lowest = b
			self.y_end_cached = (highest, lowest)
			return (highest, lowest)
		else:
			return (2,CHANNELHEIGHT)	# node with no children. I'm not happy.

	def guess_num_bars(self):
		return_me = 0
		for i in self.subwidgets:
			n = i.guess_num_bars()
			if n > return_me: # just return the number of bars for the subw with the most.
				return_me = n
		self.needed_bars = 2 + return_me
		return 2 + return_me


class ParMMWidget(BarMMWidget):
	# Represents a par node on the screen
	def setup(self):
		self.color = CPAR
		BarMMWidget.setup(self)

class SwitchMMWidget(BarMMWidget):
	# Represents a switch widget on the screen
	def setup(self):
		self.color = CSWITCH
		BarMMWidget.setup(self)

class PrioMMWidget(BarMMWidget):
	# represents a priority class.
	def setup(self):
		self.color = CPRIO
		BarMMWidget.setup(self)

class ExclMMWidget(BarMMWidget):
	# Represents an excl on the screen
	def setup(self):
		self.color = CEXCL
		BarMMWidget.setup(self)

