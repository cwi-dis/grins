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

	def destroy(self):
		pass;

	def __add_commands(self):
		self.commands = [
			CLOSE_WINDOW(callback = (self.hide, ())),
			]

	def show(self):
		if self.is_showing():
			TemporalViewDialog.show(self)
			return
		self.showing = 1
		self.init_scene()
		title = 'Channel View (' + self.toplevel.basename + ')'
		TemporalViewDialog.show(self)
		self.recalc()
		self.draw()

	def is_showing(self):
		return self.showing

	def init_scene(self):
		if self.scene is not None:
			self.scene.destroy()
		self.scene = TimeCanvas(self.root, self)
		self.scene.setup()
		self.scene.set_display(self.geodl)

	def get_geodl(self):
		return self.geodl

	def draw(self):
		self.geodl.redraw()

	def recalc(self):
		self.scene.recalc()

######################################################################
		# Selection management.

	def select_channel(self, channel):
		self.selected_channels.append(channel)

	def unselect_channels(self):
		for i in self.selected_channels:
			i.unselect()

	def select_node(self, node):
		self.selected_nodes.append(node)

	def unselect_nodes(self):
		for i in self.selected_nodes:
			i.unselect()

######################################################################
		# window event handlers:

	def ev_mouse0press(self, dummy, window, event, params):
		x,y = params[0:2]
		if x < 1.0 and y < 1.0:
			x = x * self.geodl.canvassize[0]
			y = y * self.geodl.canvassize[1]
		self.scene.click((x,y))
		self.draw()

	def ev_mouse0release(self, dummy, window, event, params):
		print "mouse released! :-( "

	def ev_mouse2press(self, dummy, window, event, params):
		print "right mouse pressed! :-)"

	def ev_mouse2release(self, dummy, window, event, params):
		print "rigth mouse released! :-)"

	def ev_exit(self, dummy, window, event, params):
		print "I should kill myself (the window, that is :-) )"

	def ev_pastefile(self, dummy, window, event, params):
		print "Pasting a file!"

	def ev_dragfile(self, dummy, window, event, params):
		print "Drag file!"

	def ev_dropfile(self, dummy, window, event, params):
		print "Dropping a file!"

	def ev_dragnode(self, dummy, window, event, params):
		print "Dragging a node!"

	def ev_dropnode(self, dummy, window, event, params):
		print "Dropped a node!"
