__version__ = "$Id$"

print "DEBUG: using the temporal view."

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
		self.window = None	# I still don't know where the window comes from.
		
		# Oooh yes, let's do some really cool selection code.
		# Of course, I'll write it _later_.
		self.selected_channels = []
		self.selected_nodes = []
		self.just_selected = None	# prevents the callback from the editmanager from doing too much work.
		
		self.time = 0		# Currently selected "time" - in seconds.
		self.zoomfactorx = 0	# Scale everything to this! Done in the Widgets for this
					# node rather than the geometric primitives!
		self.__add_commands()
		self.showing = 0
		
		self.geodl = GeoWidget(self) # This is the basic graph of geometric primitives.
		self.scene = None	# This is the collection of widgets which define the behaviour of the geo privs.
		self.editmgr = self.root.context.editmgr
		self.recurse_lock = 0	# a lock to prevent recursion.

	def destroy(self):
		pass;

	def __add_commands(self):
		self.commands = [
			CLOSE_WINDOW(callback = (self.hide, ())),
			]
		self.navigatecommands = [
			TOPARENT(callback = (self.toparent, ())),
			TOCHILD(callback = (self.tochild, (0,))),
			NEXTSIBLING(callback = (self.tosibling, (1,))),
			PREVSIBLING(callback = (self.tosibling, (-1,))),
			]


	def show(self):
		if self.is_showing():
			TemporalViewDialog.show(self)
			return
		self.showing = 1
		self.init_scene()
		self.editmgr.register(self, 1)
		title = 'Channel View (' + self.toplevel.basename + ')'
		TemporalViewDialog.show(self)
		self.recalc()
		self.draw()

	def hide(self):
		print "DEBUG: self.hide() called."
		if not self.is_showing():
			print "Error: window is not actually showing."
			return
		TemporalViewDialog.hide(self)
		self.cleanup()
		self.editmgr.unregister(self)
		self.toplevel.checkviews()
		self.showing = 0

	def toparent(self):
		print "Not implemented: TemporalView.toparent()"

	def tochild(self):
		print "Not implemented: TemporalView.tochild()"

	def tosibling(self):
		print "Not implemented: TemporalView.tosibling()"

	def cleanup(self):
		pass

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

	def redraw(self):
		# No optimisation - do a complete scene graph redraw.
		self.init_scene()
		self.recalc()
		self.draw()

	def recalc(self):
		self.scene.recalc()

	def get_geometry(self):
		# (?!) called when this window is saved.
		if self.window:
			self.last_geometry = self.geodl.getgeometry()
			print "DEBUG: last geo is:" , self.last_geometry
		else:
			self.last_geometry = (0,0,0,0) # guessing the data type
			

	def update_popupmenu(self):
		commands = self.commands
		popupmenu = [self.no_popupmenu]	# there needs to be a default.
		print "DEBUG: selected nodes: ", self.selected_nodes, len(self.selected_nodes)
		if len(self.selected_nodes) != 1:
			print "Warning: Multiple selection pop-ups not thought about yet."
		else:
			n = self.selected_nodes[0].node
			if n.GetType() in MMNode.interiortypes:
				popupmenu = self.interior_popupmenu
				if n.children:
					commands = commands + self.navigatecommands[1:2]
			else:
				popupmenu = self.leaf_popupmenu
		self.setcommands(commands)
		self.setpopup(popupmenu)


######################################################################
		# Selection management.

	def select_channel(self, channel):
		self.selected_channels.append(channel)
		self.just_selected = channel

	def unselect_channels(self):
		for i in self.selected_channels:
			i.unselect()

	def select_node(self, node):
		# Called back from the scene
		self.just_selected = node
		self.selected_nodes.append(node)
		self.update_popupmenu()

	def unselect_nodes(self):
		# Called back from the scene
		for i in self.selected_nodes:
			i.unselect()

######################################################################
		# Edit manager interface

	def transaction(self, type):
		return 1

	def rollback(self):
		print "TODO: rollback."

	def commit(self, type):
		self.redraw()

	def kill(self):
		self.destroy()

	def globalfocuschanged(self, focustype, focusobject):
		if self.just_selected:
			self.just_selected = 0
			return
		if self.recurse_lock:
			return
		self.recurse_lock = 1
		if self.scene:
			if focustype == 'MMNode':
				try:
					self.scene.select_node(focusobject.views['tempview'])
				except KeyError:
					pass # Don't worry about it. This means it is probably a structure node.
					# What we /could/ do is select all of the syncbars associated to it..
			#elif focustype == 'MMChannel':
			#	self.scene.select_channel(focusobject)
		self.draw()
		self.recurse_lock = 0

######################################################################
		# window event handlers:

	def rel2abs(self, (x, y)):
		if x < 1.0 and y < 1.0 and self.geodl:
			x = x * self.geodl.canvassize[0]
			y = y * self.geodl.canvassize[1]
		return x,y

	def ev_mouse0press(self, dummy, window, event, params):
#		import time
		coords = self.rel2abs(params[0:2])

#		before = time.time()
		self.scene.click(coords)
#		print "DEBUG: Clicking..", time.time() - before

#		before = time.time()
		self.draw()
#		print "DEBUG: Drawing..", time.time() - before

#		before = time.time()
		if isinstance(self.just_selected, MMWidget):
			self.editmgr.setglobalfocus('MMNode', self.just_selected.node)
		elif isinstance(self.just_selected, ChannelWidget):
			self.editmgr.setglobalfocus('MMChannel', self.just_selected.get_channel())
#		print "DEBUG: Calling edit manager..", time.time()-before

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
		x,y,mode, xf, yf= params[0:5]
		x,y = self.rel2abs((x,y))
		xf, yf = self.rel2abs((xf, yf))
		return self.scene.dragging_node((x,y), (xf, yf), mode)
		

	def ev_dropnode(self, dummy, window, event, params):
		print "Dropped a node!"
		return 0
