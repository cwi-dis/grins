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
		self._factory = TemporalWidgetFactory()
		self._factory.set_root(root)
		self.timeWidgets = []	# All node widgets, sorted by time.
		self.channelWidgets = {} # All channel widgets, which node widgets belong to.
		self.breaks = {}	# The exceptions to the time bar. All breaks are the same size.
		self.__init_create_channels(self.node.context.channels)
		self.__init_create_widgets(self.node)

	def __init_create_channels(self, channels):
		# Create a channel widget for each MMChannel
		x = 1
		y = 1
		w = 100
		h = 16
		for c in channels:
			bob = self._factory.createchannel(c)
			if bob:
				self.channelWidgets[bob.name] = (bob)
				bob.moveto((x,y,x+w,y+h))
				y = y + h + 2
		self.moveto((0,0,x+w,y+h))

	def __init_create_widgets(self, node):
		# Recurse throught the MMNode structure, creating a Widget tree from it.
		# For the meanwhile, only create the leaf nodes.
		if node.type in ['seq', 'par', 'excl', 'switch']:
			for i in node.GetChildren():
				self.__init_create_widgets(i)
		else:
			bob = self._factory.createnode(node)
			bob.set_channel(self.channelWidgets[node.GetChannelName()])
			bob.setup()
			self.timeWidgets.append(bob)

	def set_maxtime(self, time):
		# Sets the maximum time for this presentation.
		self.maxtime = time

	def time_to_pxl(self, time):
		# converts the time to a pixel value.
		pass

	def setup(self):
		pass

	def moveto(self, (l,t,r,b)):
		# Oooh. I'm being moved. All of my children will also have to be moved.
		# This affects my timescale.

		# Blatantly ignore l and t
		l = 0
		t = 0
		MMNodeWidget.moveto(self, (l,t,r,b))

		# Move all of my children.
		

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
		self.w_outerbox = self.graph.AddWidget(Box(self.root))
		self.w_name = self.graph.AddWidget(Text(self.root))
		self.w_name.set_text(self.name)

	def set_channel(self, c):
		self.channel = c

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


class TimeWidget(MMNodeWidget, GeoDisplayWidget):
	# Abstract base class for any widget that has a start and end time.
	# Instances of superclasses must be drawn on a time canvas (coords are 
	def setup(self):
		pass

	def set_channel(self, c):
		pass


class MMWidget(TimeWidget, GeoDisplayWidget):
	# This is the box which represents one leaf node.
	def setup(self):
		TimeWidget.setup(self)
		self.w_outerbox = self.graph.AddWidget(Box(self.root))
		self.name = self.node.GetAttr('name')
		self.w_text = self.graph.AddWidget(Text(self.root))
		self.w_text.set_text(self.name)

	def moveto(self, coords):
		TimeWidget.moveto(coords)
		self.w_outerbox.moveto(coords)
		self.w_text.moveto(coords)


class SyncBarWidget(TimeWidget, GeoDisplayWidget):
	# This is a syncronisation bar.
	# Think about this more, worry about it later.
	# This also puts breaks in the timeline.
	def setup(self):
		pass


class MediaBarWidget(Widget, GeoDisplayWidget):
	# This is the media bar at the bottom of the view.
	def get_prefered_size(self):
		return 24,800

	def setup(self):
		self.w_play = None # Working here.


class ButtonWidget(Widget, GeoDisplayWidget):
	# This is a button.
	pass


class SliderWidget(Widget, GeoDisplayWidget):
	# This is a slider.
	pass
