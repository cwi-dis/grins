__version__ = "$Id$"

import windowinteface, WMEVENTS
import MMNode
from TemporalViewDialog import TemporalViewDialog
from usercmd import *
from TemporalWidgets import *

class TemporalView(TemporalViewDialog):
	def __init__(self, toplevel):
		self.toplevel = None
		self.root = self.toplevel.root
		self.scene_graph = None	# : TemporalWidget

		# Oooh yes, let's do some really cool selection code.
		# Of course, I'll write it _later_.
		self.selected_channels = [] # Alain: catch me if you caaaan!! :-)
		self.selected_nodes = [] # This is a must!

		self.time = 0		# Currently selected "time" - in seconds.
		self.zoomfactorx = 0	# Scale everything to this! Done in the Widgets for this
					# node rather than the geometric primitives!
		self.__add_commands()



	def __add_commands(self):
		# Messy function. Keep last.
