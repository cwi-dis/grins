# Work in progress.

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

class TimeCanvas(MMNodeWidget, GeoDisplayWidget):
	# This implements a container that contains time-based classes.
	# It is a facade to deal with the rest of the widgets here.
	# Issues to deal with:
	# * Channels may or may not be the y axis.
	# * Time will be the x axis.
	# * There will be breaks in time to accommodate structure nodes.
	# * This may or may not have a playback bar attached to it (how I
	#   wish I could use a decent widget set..)

	def __init__(self, node, root):
		MMNodeWidget.__init__(self, node, root)
		import Timing
		Timing.needtimes(node)
		self._factory = TemporalWidgetFactory()
		self._factory.set_root(root)
		self.channelWidgets = {} # All channel widgets, which node widgets belong to.
		self.breaks = {}	# A dict of times->syncbars.
		self.channelNameWidth = 100 # Length of the name of the channel
		self.channelPlayWidth = 600 # Length of the playable part of the channel
		self.channelHeight = 16
		self.maxtime = node.t1
		self.__init_create_channels(self.node.context.channels)
		self.lbar = self._factory.createbar(self.node)
		self.rbar = self._factory.createbar(self.node) # also.
		self.__init_create_widgets(self.node, self.lbar, self.rbar)
		self.editmgr = node.context.editmgr

	def setup(self):
		self.nodes_l = self.channelNameWidth + 6
		x,y,w,h = self.get_box()
		self.nodes_r = x+w

	def set_maxtime(self, time):
		# Sets the maximum time for this presentation.
		self.maxtime = time

	def __init_create_channels(self, channels):
		# Create a channel widget for each MMChannel
		for c in channels:
			bob = self._factory.createchannel(c)
			if bob:
				self.channelWidgets[bob.name] = (bob)
				bob.set_canvas(self)

	def __init_create_widgets(self, node, leftbar, rightbar):
		# Create all the widgets and the bars between them.
		if node.type == 'seq':
			kids = node.GetSchedChildren()
			lb = leftbar
			for i in range(0, len(kids)):
				# Create a new bar after this child
				rb = self._factory.createbar(node)
				# Fill in the new bar.
				self.__init_create_widgets(kids[i], lb, rb)
				self.breaks[rb.get_time()] = rb
				lb = rb
				if i == len(kids)-1:
					# Then this is the final bar.
					rightbar.attach_widget_left(rb)
					rb.attach_widget_right(rightbar)
		elif node.type == 'par':
			for i in node.GetSchedChildren():
				# Create a node for each child and add it here.. conceptually only.
				self.__init_create_widgets(i, leftbar, rightbar)
		elif node.type not in ['excl', 'switch']: # if this is a leaf node.
			bob = self._factory.createnode(node)
			self.channelWidgets[bob.get_channel()].append(bob)
			leftbar.attach_widget_right(bob)
			rightbar.attach_widget_left(bob)
			return bob

	def time2pixel(self, time):
		# Also need to take time breaks into consideration (TODO)
		return ((self.channelPlayWidth/self.maxtime) * time) + self.channelNameWidth + 4

	def moveto(self, (l,t,r,b)):
		# Oooh. I'm being moved. All of my children will also have to be moved.
		# This affects my timescale.

		# Blatantly ignore l and t
		l = 0
		t = 0
		MMNodeWidget.moveto(self, (l,t,r,b))

	def recalc(self):
		t = 2
		l = 2
		r = 2 + self.channelNameWidth
		# Move all of my children (channels)
		for i in self.channelWidgets.values():
			i.moveto((l,t,r,t+self.channelHeight))
			t = t + self.channelHeight + 2
		# Move all of my breaks (each syncbar only needs to know it's x position)
		for i in self.breaks.values():
			x = self.time2pixel(i.get_time())
			i.moveto((x,42,69,13)) # I just think that those numbers are cool. Life. Love. Death.
		self.lbar.moveto((self.time2pixel(0), 1,2,3))
		self.rbar.moveto((self.time2pixel(self.node.t1), 1, 2, 3))

	def click(self, coords):
		# The z-ordering goes as follows:
		# 1) check the sync bars
		# 2) check the nodes.
		# You may need to add more to this as time goes by.
		if self.lbar.is_hit(coords):
			self.select_syncbar(self.lbar)
		elif self.rbar.is_hit(coords):
			self.select_syncbar(self.rbar)
		else:
			for i in self.breaks.values():
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

	def select_syncbar(self, bar):
		print "Selected: ", bar, " (TODO)"
		if isinstance(bar, SyncBarWidget):
			bar.select()

	def select_channel(self, channel):
		print "Selected: ", channel, " (TODO)"
		self.root.unselect_channels()
		if isinstance(channel, ChannelWidget):
			self.root.select_channel(channel)
			channel.select()
			self.editmgr.setglobalfocus('MMChannel', channel.channel)

	def select_node(self, mmwidget):
		print "Selected: ", mmwidget, " (TODO)"
		self.root.unselect_nodes()
		if isinstance(mmwidget, MMWidget):
			self.root.select_node(mmwidget)
			mmwidget.select()
			self.editmgr.setglobalfocus('MMNode', mmwidget.node)
			# Also, set the node's channel.

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
		assert isinstance(c, MMNode.MMChannel)
		bob = ChannelWidget(self.root)
		graph = self.root.get_geodl()
		bob.set_channel(c)
		bob.set_display(graph)
		bob.setup()
		return bob

	def createbar(self, n):
		assert isinstance(n, MMNode.MMNode)
		bob = SyncBarWidget(n, self.root)
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
		self.name = self.channel.name
		self.nodes = []		# A list of all nodes in this channel.

		self.w_outerbox = self.graph.AddWidget(Box(self.root))
		self.w_name = self.graph.AddWidget(Text(self.root))
		self.w_name.set_text(self.name)


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

		# Move all of my nodes too.
		mx,my,mw,mh = self.get_box()
		for i in self.nodes:
			l = self.canvas.time2pixel(i.get_starttime())
			r = self.canvas.time2pixel(i.get_endtime())
			i.moveto((l,my,r,my+mh))

	def append(self, value):
		assert isinstance(value, MMWidget)
		# Append a node to this channel.
		self.nodes.append(value)

	def is_hit_y(self, coords):
		hx,hy = coords
		x,y,w,h = self.get_box()
		if y < hy < y+h:
			return 1
		else:
			return 0

	def get_node_at(self, coords):
		# My parent node has asked me to handle this click. Very well then.
		for n in self.nodes:
			if n.is_hit(coords):
				return n


class TimeWidget(MMNodeWidget, GeoDisplayWidget):
	# Abstract base class for any widget that has a start and end time.
	# Instances of superclasses must be drawn on a time canvas (coords are 
	def setup(self):
		self.editmgr = self.node.context.editmgr


class MMWidget(TimeWidget, GeoDisplayWidget):
	# This is the box which represents one leaf node.
	# I am a slave to my channel. My channel will resize me and move me around.
	def setup(self):
		TimeWidget.setup(self)
		self.w_outerbox = self.graph.AddWidget(Box(self.root))
		self.name = self.node.GetAttr('name')
		self.w_text = self.graph.AddWidget(Text(self.root))
		self.w_text.set_text(self.name)

	def moveto(self, coords):
		TimeWidget.moveto(self, coords)
		self.w_outerbox.moveto(coords)
		self.w_text.moveto(coords)

	def set_channel(self, c):
		print "TODO"

	def get_channel(self):
		return self.node.GetChannelName()

	def get_starttime(self):
		return self.node.t0

	def get_endtime(self):
		return self.node.t1

	def select(self):
		Widgets.Widget.select(self)
		self.w_outerbox.set_color((255,255,255))

	def unselect(self):
		Widgets.Widget.unselect(self)
		self.w_outerbox.set_color((0,0,0))

class SyncBarWidget(TimeWidget, GeoDisplayWidget):
	# This is a syncronisation bar.
	# EVERY SYNCRONISATION BAR CREATES A BREAK IN THE TIMELINE.
	# And the positions of those breaks is dead useful for dragging and dropping.

	# Every syncbar has a partner - this is always the end of one bar and the start of another
	# except when this is the first or the last node.
	# If I represent a par, I am either the start or the end.
	# If I represent a seq, I am either the start, end or an element.
	# My node that I represent is stored in self.node in a superclass.

	def __repr__(self):
		return "SyncBar "+self.node.uid+" left:"+str(len(self.attached_left))+" right:"+str(len(self.attached_right))
	
	def setup(self):
		print "DEBUG: new syncbar instance: ", self.node.uid
		self.attached_left = []
		self.w_blobs_left = []	# These two arrays are mapped together.

		self.attached_right = []
		self.w_blobs_right = []	# These two arrays are mapped together.

		# I am a bar with little blobs attaching me to the right and left nodes there.
		self.w_bar = self.graph.AddWidget(Box(self.root))

	def attach_widget_left(self, widget):
		self.attached_left.append(widget)
		self.w_blobs_left.append(self.graph.AddWidget(Box(self.root)))

	def attach_widget_right(self, widget):
		self.attached_right.append(widget)
		self.w_blobs_right.append(self.graph.AddWidget(Box(self.root)))

	def moveto(self, coords):
		l,t,r,b = coords
		barwidth = 8
		# Blatently ignore t, b, r.
		t = None
		b = None

		# Remember that sometimes, w_blobs_left may contain another blob.
		for i in range(0,len(self.w_blobs_left)):
			nx, ny, nh, nw = self.attached_left[i].get_box()

			# Find the highest and lowest point.
			if t == None or t > ny:
				t = ny
			if b == None or b < ny+nh:
				b = ny+nh
			print "DEBUG: b now: ", b, "ny: ", ny, ", nh: ", nh
			self.w_blobs_left[i].moveto((l-barwidth/2-4,ny+6,l-barwidth/2+2,ny+12))
			#print self, " left blob rendered at ", self.w_blobs_left[i].get_box()
		for i in range(0,len(self.w_blobs_right)):
			nx, ny, nw, nh = self.attached_right[i].get_box()

			# Find the highest and lowest point.
			if t == None or t > ny:
				t = ny
			if b == None or b < ny+nh:
				b = ny+nh
			print "DEBUG: b now: ", b, "ny: ", ny, ", nh: ", nh
			self.w_blobs_right[i].moveto((l+barwidth/2-2,ny+6,l+barwidth/2+4,ny+12))
		if t == None: t=0
		if b == None: b = 10
		self.w_bar.moveto((l-(barwidth/2), t-3, l+(barwidth/2), b+3))
		# I need to move myself to handle clicks.
		TimeWidget.moveto(self, (l-(barwidth/2), t-3, r+(barwidth/2), b+3))

	def get_time(self):
		if len(self.attached_right) > 0:
			return self.attached_right[0].node.t0
		elif self.attached_left:
			return self.attached_left[0].node.t1
		else:
			print "I have no attached nodes."

##class MediaBarWidget(Widget, GeoDisplayWidget):
##	# This is the media bar at the bottom of the view.
##	def get_prefered_size(self):
##		return 24,800

##	def setup(self):
##		self.w_play = None # Working here.


##class ButtonWidget(Widget, GeoDisplayWidget):
##	# This is a button.
##	pass


##class SliderWidget(Widget, GeoDisplayWidget):
##	# This is a slider.
##	pass
