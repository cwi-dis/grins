__version__ = "$Id$"

import windowinterface, WMEVENTS
import MMNode
from TemporalViewDialog import TemporalViewDialog
from usercmd import *
from TemporalWidgets import *
from GeometricPrimitives import *

class TemporalView(TemporalViewDialog):
	def __init__(self, toplevel):
		TemporalViewDialog.__init__(self)
		self.toplevel = toplevel
		self.root = toplevel.root
		self.scene_graph = None	# : TemporalWidget; This graph remains here the whole time.

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

		# DEBUG: Draw something on the window.	
		dl = self.window.newdisplaylist((50,50,50), windowinterface.UNIT_PXL)
		dl.drawbox((50,50,100,100))
		dl.render()

	def is_showing(self):
		return self.showing

	def init_scene(self):
		f = TemporalWidgetFactory()
		self.scene_graph = f.createNewTree(self.root)
		geodl = GeoWidget(self)
		self.scene_graph.set_display(geodl)
