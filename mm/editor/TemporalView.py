__version__ = "$Id$"

import windowinterface, WMEVENTS
import MMNode
from TemporalViewDialog import TemporalViewDialog
from usercmd import *
from TemporalWidgets import *

class TemporalView(TemporalViewDialog):
	def __init__(self, toplevel):
		TemporalViewDialog.__init__(self)
		self.toplevel = toplevel
		self.root = toplevel.root
		self.scene_graph = None	# : TemporalWidget

		# Oooh yes, let's do some really cool selection code.
		# Of course, I'll write it _later_.
		self.selected_channels = [] # Alain: catch me if you caaaan!! :-)
		self.selected_nodes = [] # This is a must!

		self.time = 0		# Currently selected "time" - in seconds.
		self.zoomfactorx = 0	# Scale everything to this! Done in the Widgets for this
					# node rather than the geometric primitives!
		self.__add_commands()
		self.showing = 0

	def destroy(self):
		pass;

	def __add_commands(self):
		# Messy function. Keep last.
		pass

	def show(self):
		if self.is_showing():
			TemporalViewDialog.show(self)
			return
		self.showing = 1
		title = 'Channel View (' + self.toplevel.basename + ')'
		TemporalViewDialog.show(self)
		print "Do I have a window? ", self.window

	def is_showing(self):
		return self.showing
