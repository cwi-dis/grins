# Work in progress.

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
BARWIDTH = 8
CHANNELWIDTH = 100
NODESTART = 102
NODEEND = 600

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

	def __init__(self, node, mother):
		MMNodeWidget.__init__(self, node, mother)
		self._factory = TemporalWidgetFactory()
		self._factory.set_root(mother)
		self.channelWidgets = {} # All channel widgets, which node widgets belong to.

		self.channelHeight = 16

		self.maxtime = self.node.GetTimes()[1]
		self.__init_create_channels(self.node.context.channels)

#		self.lbar = self._factory.createbar(self.node)
#		self.lbar.time = -1
#		self.lbar.special =1
#		self.rbar = self._factory.createbar(self.node) # also.
#		self.rbar.time = self.maxtime - 0.00001
#		self.syncbars = [self.lbar, self.rbar] # otherwise two bars with the same times will clobber each other.

		self.start_breaks = {} # A dictionary of the breaks from the start of a struct node
		self.end_breaks = {} # same, maps times to lists of nodes.
		self.breaks_cache = [] # A cache for improving times to fetch from the cache.

		self.structnodes = []	# A sorted list, by time of the structure nodes.

		self.mainnode = self.__init_create_widgets(self.node)
		self.editmgr = node.context.editmgr

		self.pointer_object_of_interest = None # Which object looks appealing to the selection.

	def setup(self):
#		self.nodes_l = CHANNELWIDTH + 6
#		x,y,w,h = self.get_box()
#		self.nodes_r = x+w
		pass

	def destroy(self):
		# A destructor.
		for i in self.syncbars:
			i.destroy()
		for i in self.channelWidgets.values():
			i.destroy()

	def set_maxtime(self, time):
		# Sets the maximum time for this presentation.
		self.maxtime = time

	def __init_create_channels(self, channels):
		# Create a channel widget for each MMChannel
		for c in channels:
			if c['type'] == 'layout':
				bob = self._factory.createchannel(c)
				if bob:
					self.channelWidgets[bob.name] = (bob)
					bob.set_canvas(self)
		bob = self._factory.createchannel(None)
		self.channelWidgets['undefined'] = bob
		bob.set_canvas(self)

# delete me:
##	def __init_create_widgets(self, node, leftbar, rightbar):
##		# Create all the widgets and the bars between them.
##		if node.type == 'seq':
##			# delete me:
##			##kids = node.GetSchedChildren()
####			lb = leftbar
####			leftbar.start_of_sequence = 1
####			for i in range(0, len(kids)):
####				if i == len(kids)-1:
####					# Then this is the final bar.
####					self.__init_create_widgets(kids[i], lb, rightbar)
####				else:
####					# Create a new bar after this child
####					# Note that this is the only place new bars should be created.
####					rb = self._factory.createbar(node)
####					self.syncbars.append(rb) # add it to the list of bars
####					#self.breaks[rb.get_time()] = rb	# and to the list of breaks in time.
####					self.__init_create_widgets(kids[i], lb, rb)
####					lb = rb
##		elif node.type == 'par':
####			if leftbar.par is None:
####				leftbar.par = node
####			for i in node.GetSchedChildren():
####				# Create a node for each child and add it here.. conceptually only.
####				self.__init_create_widgets(i, leftbar, rightbar)
##		elif node.type not in ['excl', 'switch'] and node.GetChannel(): # if this is a leaf node.
##			bob = self._factory.createnode(node)
##			# This is pretty obscure code here!
##			self.channelWidgets[bob.get_channel()].append(bob)
##			leftbar.attach_widget_right(bob)
##			rightbar.attach_widget_left(bob)
##			return bob

	def __init_create_widgets(self, node):
		# this is a recursive function. The current widget is the widget which the node(s)
		# get inserted into.
		t = node.type
		# All leaf nodes should be checked already.
		if t == 'seq':
			print "sequence."
			container = self._factory.createseq(node)
		elif t == 'par':
			print "par."
			container = self._factory.createpar(node)
		elif t == 'excl':
			print "exclusief."
			container = self._factory.createexcl(node)
		elif t == 'alt':
			print "switch."
			container = self._factory.createswitch(node)
		else:
			print "Unknown node type: ", t
			return None
		self.structnodes.append(container)

		# populate the node.
		for i in node.children:
			if i.type in MMNode.leaftypes:
				# i is a leafnode
				bob = self._factory.createnode(i)
				n = bob.get_channel()
				print "Debug: bob is: <"+n+">"
				self.channelWidgets[n].append(bob)
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

	def time2pixel(self, time):
		# Also need to take time breaks into consideration (TODO)
		assert 0
# eh. Wrong.
##		assert 0 # write me.
##		if time < 0:
##			print "Time below zero: ", time
##			return self.channelNameWidth + 4
##		elif time == 0:
##			return self.channelNameWidth + 4 + barwidth
##		num_breaks = 0
##		for i in self.syncbars:
##			if float(i.get_time()) <= float(time) :
##				num_breaks = num_breaks + 1
##		return_me = ((self.channelPlayWidth/self.maxtime) * time) + self.channelNameWidth + 4 + num_breaks*barwidth
##		return return_me

#	def node_start_x(self, widget):
#		# returns the start position of the node.
#		# refer to the break dictionaries and cached list to determine the x position.##
#
#	def node_end_x(self, widget):
#		# returns the end position of the node.

	def moveto(self, (l,t,r,b)):
		# See also self.recalc()
		# This affects my timescale.

		# Blatantly ignore l and t
		l = 0
		t = 0
		MMNodeWidget.moveto(self, (l,t,r,b))

	def recalc(self):
		t = 2
		l = 2
		r = 2 + CHANNELWIDTH

		# Move all of the channels into position.
		for i in self.channelWidgets.values():
			i.moveto((l,t,r,t+self.channelHeight))
			t = t + self.channelHeight + 2
			
		# delete me: 
		# Move all of my breaks (each syncbar only needs to know it's x position)
		#for i in self.syncbars:
		#	time = i.get_time() - 0.0001
		#	x = self.time2pixel(time)
		#	print "DEBUG: Moving bar to: ", x, " time is: ", time, "channelNameWidth: ", self.channelNameWidth
		#	i.moveto((x,42,69,13)) # I just think that those numbers are cool. Life. Love. Death.
		
		self.mainnode.moveto((NODESTART, 2, NODEEND, t+self.channelHeight+2))
		self.mainnode.recalc()

	def click(self, coords):
		# The z-ordering goes as follows:
		# 1) check the sync bars
		# 2) check the nodes.
		# You may need to add more to this as time goes by.
		for i in self.syncbars:
			if i.is_hit(coords):
				self.select_syncbar(i)
		for c in self.channelWidgets.values():
			if c.is_hit_y(coords):
				if c.is_hit(coords):
					self.select_channel(c)
				else:
					n = c.get_node_at(coords)
					self.select_node(n)
		
	# TODO: what about CTRL-clicks for multiple selection?

#	def select_syncbar(self, bar):
#		self.root.unselect_nodes()
#		if isinstance(bar, SyncBarWidget):
#			self.root.select_node(bar)
#			bar.select()
#			self.editmgr.setglobalfocus('MMNode', bar.node)
#			# Also, set the node's channel.

	def select_channel(self, channel):
		print "DEBUG: these are the syncbars:"
		for i in self.syncbars:
			print " * ",i.tostring()
		self.mother.unselect_channels()
		if isinstance(channel, ChannelWidget):
			self.mother.select_channel(channel)
			channel.select()
			self.editmgr.setglobalfocus('MMChannel', channel.channel)

	def select_node(self, mmwidget):
		# TODO: also structure nodes.
		self.mother.unselect_nodes()
		if isinstance(mmwidget, MMWidget):
			self.mother.select_node(mmwidget)
			mmwidget.select()
			self.editmgr.setglobalfocus('MMNode', mmwidget.node)
			# Also, set the node's channel.

# delete me
#	def dragging_node(self, tgtcoords, srccoords, mode):
#		print "DEBUG: dragging node; ", tgtcoords, srccoords, mode
#		return windowinterface.DROPEFFECT_NONE


######################################################################
# A factory to create new widgets in this file.
######################################################################

class TemporalWidgetFactory:
	# A singleton factory which creates widgets based on node types.
	def createnode(self, m):
		assert isinstance(m, MMNode.MMNode)
		bob = MMWidget(m, self.root)
		bob.set_display(self.root.get_geodl())
		bob.setup()
		return bob

	def createchannel(self, c):
		assert isinstance(c, MMNode.MMChannel) or c is None
		bob = ChannelWidget(self.root)
		graph = self.root.get_geodl()
		bob.set_channel(c)
		bob.set_display(graph)
		bob.setup()
		return bob

# delete me.
#	def createbar(self, n):
#		assert isinstance(n, MMNode.MMNode)
#		bob = SyncBarWidget(n, self.root)
#		bob.set_display(self.root.get_geodl())
#		bob.setup()
#		return bob

	def createseq(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = SeqMMWidget(node, self.root)
		bob.set_display(self.root.get_geodl())
		bob.setup()
		return bob

	def createpar(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = ParMMWidget(node, self.root)
		bob.set_display(self.root.get_geodl())
		bob.setup()
		return bob

	def createexcl(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = ExclMMWidget(node, self.root)
		bob.set_display(self.root.get_geodl())
		bob.setup()
		return bob

	def createswitch(self, node):
		assert isinstance(node, MMNode.MMNode)
		bob = SwitchMMWidget(node, self.root)
		bob.set_display(self.root.get_geodl())
		bob.setup()
		return bob

	def set_root(self, root):
		self.root = root

	def setup(self):
		return


######################################################################
# The widgets.
######################################################################

class ChannelWidget(Widgets.Widget, GeoDisplayWidget):
	# A widget representing a certain channel.
	def setup(self):
		# Once this widget has recieved something to display on, it can create some
		# widgets.
		if self.channel:
			self.name = self.channel.name
		else:
			self.name = 'undefined'
		self.nodewidgets = []		# A list of all node widgets in this channel.
		self.w_fbox = self.graph.AddWidget(FBox(self.mother))
		self.w_fbox.set_color((232,193,152))
		self.w_outerbox = self.graph.AddWidget(Box(self.mother))
		self.w_name = self.graph.AddWidget(Text(self.mother))
		self.w_name.set_text(self.name)

	def destroy(self):
		for i in self.nodewidgets:
			i.destroy()	# nodes is a list of mmwidgets, not MMNodes.
		self.nodewidgets = None
		self.graph.DelWidget(self.w_outerbox)
		self.graph.DelWidget(self.w_name)
		self.graph.DelWidget(self.w_fbox)

	def set_channel(self, c):
		self.channel = c

	def set_canvas(self, c):
		# The canvas is used to find the time position of elements.
		self.canvas = c

	def select(self):
		Widgets.Widget.select(self)
		self.w_outerbox.set_color((255,255,255))

	def unselect(self):
		Widgets.Widget.unselect(self)
		self.w_outerbox.set_color((0,0,0))

	def moveto(self, coords):
		# Take my widgets with me.
		Widgets.Widget.moveto(self, coords)
		self.w_outerbox.moveto(coords)
		self.w_name.moveto(coords)
		self.w_fbox.moveto(coords)

		mx, my, mw, mh = self.get_box()
		for i in self.nodewidgets:
			i.set_y(my, my+mh)

		# Move all of my nodes too.
		# DELETE ME. The x coordinate is handled by the strcture widgets.
		#mx,my,mw,mh = self.get_box()
		#for i in self.nodewidgets:
		#	l = self.canvas.time2pixel(i.get_starttime())
		#	r = self.canvas.time2pixel(i.get_endtime())
		#	i.moveto((l,my,r,my+mh))

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

	def get_node_at(self, coords):
		# My parent node has asked me to handle this click. Very well then.
		for n in self.nodewidgets:
			if n.is_hit(coords):
				return n
		bob.root = self.root

	def get_draggable(self, coords):
		print "TODO: dragging channels around."
		return []


class TimeWidget(MMNodeWidget, GeoDisplayWidget):
	# Abstract base class for any widget that has a start and end time.
	# Instances of superclasses must be drawn on a time canvas (coords are 
	def setup(self):
		self.editmgr = self.node.context.editmgr

	def set_x(self, l,r):
		print "TimeWidget.set_x(", l, r, ")", self
		x,y,w,h = self.get_box()
		self.moveto((l,y,r,y+h))
		
	def set_y(self, t,b):
		print "TimeWidget.set_y(", t, b, ")", self
		x,y,w,h = self.get_box()
		self.moveto((x,t,x+w,b))

	def GetTimes(self):
		return self.node.GetTimes()


class MMWidget(TimeWidget, GeoDisplayWidget):
	# This is the box which represents one leaf node.
	# I am a slave to my channel. My channel will resize me and move me around.
	def setup(self):
		TimeWidget.setup(self)
		self.w_fbox = self.graph.AddWidget(FBox(self.mother))
		self.w_fbox.set_color((205,207,194))
		self.w_outerbox = self.graph.AddWidget(Box(self.mother))
		self.name = self.node.GetAttrDef('name', '')
		self.w_text = self.graph.AddWidget(Text(self.mother))
		self.w_text.set_text(self.name)
		self.node.views['tempview'] = self

	def destroy(self):
		# TODO: remove me from the list of MMNode Views.
		del self.node.views['tempview']
		self.graph.DelWidget(self.w_outerbox)
		self.graph.DelWidget(self.w_text)
		self.graph.DelWidget(self.w_fbox)

	def moveto(self, coords):
		l,t,r,b = coords
		if r-l < BARWIDTH:
			coords = l,t,l+BARWIDTH, b
		TimeWidget.moveto(self, coords)
		self.w_fbox.moveto(coords)
		self.w_outerbox.moveto(coords)
		self.w_text.moveto(coords)
#		print "DEBUG: MMWidget moved to ", self.get_box()

	def set_channel(self, c):
		print "TODO"

	def get_channel(self):
		# Returns a string which is this node's channel.
		if not self.node.GetChannel():
			print "ERROR: no channel", self.node, self.node.GetChannel()
			return 'undefined'
		print "DEBUG: get_channel returning: ", self.node.GetChannel().GetLayoutChannel().name
		return self.node.GetChannel().GetLayoutChannel().name

	def get_starttime(self):
		return self.node.GetTimes()[0]

	def get_endtime(self):
		return self.node.GetTimes()[1]

	def select(self):
		Widgets.Widget.select(self)
		self.w_outerbox.set_color((255,255,255))

	def unselect(self):
		Widgets.Widget.unselect(self)
		self.w_outerbox.set_color((0,0,0))

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
		print "TODO: deprecated api used."
		return self.get_channel()

	def recalc(self):
		pass

# delete me.
##class SyncBarWidget(TimeWidget, GeoDisplayWidget):
##	# This is a syncronisation bar.
##	# EVERY SYNCRONISATION BAR CREATES A BREAK IN THE TIMELINE.
##	# And the positions of those breaks is dead useful for dragging and dropping.

##	# Every syncbar has a partner - this is always the end of one bar and the start of another
##	# except when this is the first or the last node.
##	# If I represent a par, I am either the start or the end.
##	# If I represent a seq, I am either the start, end or an element.
##	# My node that I represent is stored in self.node in a superclass.

##	def tostring(self):
##		return "SyncBar "+str(id(self))+" left:"+repr(self.attached_left) \
##			+" right:"+repr(self.attached_right)

##	def __repr__(self):
##		return "SyncBar instance " + str(id(self))

##	def setup(self):
##		self.attached_left = []
##		self.w_blobs_left = []	# These two arrays are mapped together.

##		self.attached_right = []
##		self.w_blobs_right = []	# These two arrays are mapped together.

##		# I am a bar with little blobs attaching me to the right and left nodes there.
##		self.w_fbox = self.graph.AddWidget(FBox(self.root))
##		self.w_fbox.set_color((110,110,110))
##		self.w_bar = self.graph.AddWidget(Box(self.root))
##		self.start_of_sequence = 0
##		self.par = None
##		self.time = None	# for hard-coding the time.

##	def destroy(self):
##		for i in self.w_blobs_left + self.w_blobs_right:
##			self.graph.DelWidget(i)
##		self.graph.DelWidget(self.w_bar)
##		self.graph.DelWidget(self.w_fbox)
##		self.w_blobs_left = None
##		self.w_blobs_right = None
##		self.attached_left = None # Prevents circular references.
##		self.attached_right = None

##	def attach_widget_left(self, widget):
##		self.attached_left.append(widget)
##		blob = self.graph.AddWidget(FBox(self.root))
##		blob.set_color((40,40,40))
##		self.w_blobs_left.append(blob)

##	def attach_widget_right(self, widget):
##		self.attached_right.append(widget)
##		blob = self.graph.AddWidget(FBox(self.root))
##		blob.set_color((40,40,40))
##		self.w_blobs_right.append(blob)

##	def moveto(self, coords):
##		print "DEBUG: syncbar moving to: ", coords
##		l,t,r,b = coords
##		# Blatently ignore t, b, r.
##		t = None
##		b = None

##		# Remember that sometimes, w_blobs_left may contain another blob.
##		for i in range(0,len(self.w_blobs_left)):
##			nx, ny, nw, nh = self.attached_left[i].get_box()

##			# Find the highest and lowest point.
##			if t == None or t > ny:
##				t = ny
##			if b == None or b < ny+nh:
##				b = ny+nh
##			# Make it stretch to the node.
##			self.w_blobs_left[i].moveto((nx+nw-3,ny+6,l+5,ny+12))
##		for i in range(0,len(self.w_blobs_right)):
##			nx, ny, nw, nh = self.attached_right[i].get_box()

##			# Find the highest and lowest point.
##			if t == None or t > ny:
##				t = ny
##			if b == None or b < ny+nh:
##				b = ny+nh
##			self.w_blobs_right[i].moveto((l+BARWIDTH-2,ny+6,nx+5,ny+12))
##		if t == None: t=0
##		if b == None: b = 10
##		l = l + 1
##		ncoords = (l, t-2, l+BARWIDTH, b+2)
##		self.w_fbox.moveto(ncoords)
##		self.w_bar.moveto(ncoords)
##		# I need to move myself to handle clicks.
##		TimeWidget.moveto(self, ncoords)

##	def get_time(self):
##		# Based on the position in the sequence.
##		if self.time is not None:
##			#print "DEBUG: returning hard-coded time: ", self.time
##			return self.time
##		elif self.start_of_sequence:
##			#print "DEBUG: returning start of sequence: ", self.node.GetTimes()[0]
##			return self.node.GetTimes()[0]
##		elif self.par is not None:
##			#print "DEBUG: returning start of par: ", self.node.GetTimes()[0]
##			times = self.par.GetTimes()
##			return times[0]
##		else:	
##			print "Error: syncbar has no associated widget.", self
##			return 0.0
##			#if len(self.attached_right) > 0:
##			#	return self.attached_right[0].node.t0
##			#elif self.attached_left:
##			#	return self.attached_left[0].node.t1
##			#else:
##			#	print "ERROR: I have no attached nodes, thus no time."

##	def select(self):
##		self.w_bar.set_color((255,255,255))
##		for i in self.w_blobs_left+self.w_blobs_right:
##			i.set_color((255,255,255))
##		TimeWidget.select(self)

##	def unselect(self):
##		self.w_bar.set_color((0,0,0))
##		for i in self.w_blobs_left + self.w_blobs_right:
##			i.set_color((40,40,40))
##		TimeWidget.unselect(self)

##	def get_draggable(self, coords):
##		# return a box.
##		return [self.graph.AddWidget(DraggableBox(self.root))]


class MultiMMWidget(TimeWidget):
	# represents any node which has children.
	def setup(self):
		self.subwidgets = []
	def add(self, bob):
		print "DEBUG: adding a child: ", bob, self
		self.subwidgets.append(bob)
		print "Subwidgets now: ", self.subwidgets

class SeqMMWidget(MultiMMWidget):
	# Represents a seq widget on the screen

	def setup(self):
		MultiMMWidget.setup(self)
		self.y_start_cached = None
		self.y_end_cached = None

	def __repr__(self):
		return "I'm a SeqMMWidget"

	def recalc(self):
		# iterate through my subwidgets, resizing each.
		print "DEBUG: seqwidget.recalc()", self.subwidgets
		mytimes = self.node.GetTimes()
		x,y,w,h = self.get_box()
		print "DEBUG: SeqWidget.getbox:  ", x, y, w, h
		if mytimes[1]-mytimes[0] > 0:
			ppt = w/(mytimes[1]-mytimes[0])	# pixels per time
		else:
			ppt = 0
		
		for i in self.subwidgets:
			ctime = i.GetTimes()
			cl = (ctime[0]-mytimes[0])*ppt + x + BARWIDTH
			cr = (ctime[1]-mytimes[0])*ppt + x + BARWIDTH
			i.set_x(cl, cr)
			i.recalc()

	def get_y_start(self):
		if self.y_start_cached is not None:
			return self.y_start_cached
		else:
			if len(self.subwidgets) > 0:
				bob = self.subwidgets[0].get_y_start()
				self.y_start_cached = bob
				return bob
			else:
				assert 0

	def get_y_end(self):
		if self.y_end_cached is not None:
			return self.y_end_cached
		else:
			if len(self.subwidgets) > 0:
				bob = self.subwidgets[len(self.subwidgets)-1].get_y_end()
				self.y_end_cached = bob
				return bob
			else:
				return 0


class BarMMWidget(MultiMMWidget):
	# The base class for pars, switches, Excls.
	def setup(self):
		MultiMMWidget.setup(self)
		self.w_startbar = self.graph.AddWidget(Box(self.mother))
		self.w_endbar = self.graph.AddWidget(Box(self.mother))
		self.w_endbar.set_color((255,255,255))
		self.y_start_cached = None
		self.y_end_cached = None

	def __repr__(self):
		return "I'm a BarMMWidget"

	def moveto(self, coords):
		size = BARWIDTH
		l,t,r,b = coords

		# bars are moved in the recalc() function
		#self.w_startbar.moveto((l,t,l+size,b))
		#self.w_endbar.moveto((r-size, t, r, b))
		TimeWidget.moveto(self,coords)
		
	def destroy(self):
		self.graph.DelWidget(self.w_startbar)
		self.graph.DelWidget(self.w_endbar)

	def recalc(self):
		# recurse through my subwidgets, resizing each.
		# also, set the bar sizes.
		print "DEBUG: barwidget.recalc()"
		mytimes = self.node.GetTimes()
		x,y,w,h = self.get_box()
		print "DEBUG: barwidget.get_box:", x,y,w,h

		# Set the bars position
		# The start bar..
		t,b = self.get_y_start()
		# The +2's are to make this show from behind other bars
		self.w_startbar.moveto((x+2, t+2, x+BARWIDTH+2, b+2))
		# The end bar..
		t,b = self.get_y_end()
		self.w_endbar.moveto((x+w-BARWIDTH-2, t-2, x+w-2, b-2))

		w = w - 2*BARWIDTH	# remember the size of the bars!
		x = x + BARWIDTH
		if mytimes[1]-mytimes[0] > 0:
			ppt = w/(mytimes[1]-mytimes[0])	# pixels per time
			for i in self.subwidgets:
				ctime = i.GetTimes()
				cl = (ctime[0]-mytimes[0])*ppt
				cr = (ctime[1]-mytimes[0])*ppt
				print "DEBUG: BarWidget: cl:", cl, " cr:", cr
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
				print "Bleep!", t, b
				if highest == None:
					highest = t
				elif t < highest:
					highest = t
				if lowest == None:
					lowest = b
				elif b > lowest:
					lowest = b
			self.y_start_cached = (highest, lowest)
			print "DEBUG: get_y_start returning ", self.y_start_cached
			return (highest, lowest)
		else:
			# TODO: node with no subwidgets.
			assert 0

	def get_y_end(self):
		# returns a tuple of the top and bottom of the end of this node
		if self.y_end_cached is not None:
			print "DEBUG: get_y_end returning: ", self.y_end_cached
			return self.y_end_cached
		elif len(self.subwidgets) > 0:
			highest = None
			lowest = None
			for i in self.subwidgets:
				print "DEBUG: i is: ", i
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
			print "DEBUG: get_y_end returning: ", highest, lowest
			return (highest, lowest)
		else:
			assert 0	# node with no children. I'm not happy.


class ParMMWidget(BarMMWidget):
	# Represents a par node on the screen
	pass
	#def setup(self):
	#	# This node needs:
	#	# * A start bar.
	#	# * An end bar
	#	# * Blobs on the bars to glue them to this node's container.
	#	# * Perhaps other widgets, such as a name.
	#	self.startbar = None # and so forth.
	

class SwitchMMWidget(BarMMWidget):
	# Represents a switch widget on the screen
	pass


class ExclMMWidget(BarMMWidget):
	# Represents an excl on the screen
	pass


