__version__ = "$Id$"

from Channel import *
#
# This rather boring channel is used for laying-out other channels
#
class LayoutChannel(ChannelWindow):

	def __init__(self, name, attrdict, scheduler, ui):
		ChannelWindow.__init__(self, name, attrdict, scheduler, ui)
		self.is_layout_channel = 1

	def __repr__(self):
		return '<LayoutChannel instance, name=' + `self._name` + '>'

	def do_arm(self, node):
	        print 'LayoutChannel: cannot play nodes on a layout channel'
		return 1

