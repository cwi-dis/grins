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

		# Oooh yes, let's do some really cool selection code.
		# Of course, I'll write it _later_.
		self.selected_channels = [] # Alain: catch me if you caaaan!! :-)
		self.selected_nodes = [] # This is a must!

		self.time = 0		# Currently selected "time" - in seconds.
		self.zoomfactorx = 0	# Scale everything to this! Done in the Widgets for this
					# node rather than the geometric primitives!
		self.__add_commands()
		self.showing = 0

		self.geodl = GeoWidget(self) # This is the basic graph of geometric primitives.
		self.scene = None	# This is the collection of widgets which define the behaviour of the geo privs.
		self.init_scene()

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
		self.recalc()
		self.draw()

	def is_showing(self):
		return self.showing

	def init_scene(self):
		self.scene = TimeCanvas(self.root, self)
		self.scene.setup()
		self.scene.set_display(self.geodl)

	def get_geodl(self):
		return self.geodl

	def draw(self):
		self.geodl.redraw()

	def recalc(self):
		self.scene.recalc()
