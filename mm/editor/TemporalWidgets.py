# Work in progress.

import Widgets
import Bandwidth
import MMurl, MMAttrdefs, MMmimetypes, MMNode
import features
import os, windowinterface
import settings
from AppDefaults import *

# Import some useful, already-written widgets.
from StructureWidgets import MMNodeWidget, StructureObjWidget, Icon

class GeoDisplayWidget:
	def set_display(self, g):
		self.graph = g
		self.setup()

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
		self.timeWidgets = []	# All node widgets, sorted by time.
		self.channelWidgets = [] # All channel widgets, which node widgets belong to.
		self.breaks = {}	# The exceptions to the time bar. All breaks are the same size.
		self.__init_create_channels(self.root.context.channels)
		self.__init_create_widgets(self.node)

	def __init_create_channels(channels):
		# Create a channel widget for each MMChannel
		for c in channels:
			self.channelWidgets.append(self._factory.createchannel(c))

	def __init_create_widgets(self, node):
		# Recurse throught the MMNode structure, creating a Widget tree from it.
		pass

	def setup(self):
		pass


class TemporalWidgetFactory:
	# A singleton factory which creates widgets based on node types.
	def createnode(self, m):
		assert isinstance(m, MMNode.MMNode)
		# Create a new view of that MMNode

	def createchannel(self, c):
		assert isinstance(c, MMNode.MMChannel)

	def setup(self):
		return


class ChannelWidget(Widgets.Widget, GeoDisplayWidget):
	# A widget representing a certain channel.
	def setup(self):
		# Once this widget has recieved something to display on, it can create some
		# widgets.
		pass

class TimeWidget(MMNodeWidget, GeoDisplayWidget):
	# Abstract base class for any widget that has a start and end time.
	# Instances of superclasses must be drawn on a time canvas (coords are 
	def setup(self):
		pass

