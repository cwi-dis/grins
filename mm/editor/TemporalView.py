__version__ = "$Id$"

import windowinterface, WMEVENTS
import MMNode
from TemporalViewDialog import TemporalViewDialog
from usercmd import *
from TemporalWidgets import *
from GeometricPrimitives import *
import Clipboard
import EditableObjects

class TemporalView(TemporalViewDialog):
	def __init__(self, toplevel):
		TemporalViewDialog.__init__(self)
		self.toplevel = toplevel
		self.root = toplevel.root
		self.window = None	# I still don't know where the window comes from.
					# It just kind of magically appears here at some stage.
		# Oooh yes, let's do some really cool selection code.
		# Of course, I'll write it _later_.
		self.selected_regions = []
		self.selected_nodes = []
		self.just_selected = None	# prevents the callback from the editmanager from doing too much work.
		
		self.time = 0		# Currently selected "time" - in seconds.
		self.__add_commands()
		self.showing = 0
		
		self.geodl = GeoWidget(self) # This is the basic graph of geometric primitives.
		self.scene = None	# This is the collection of widgets which define the behaviour of the geo privs.
		self.editmgr = self.root.context.editmgr
		self.recurse_lock = 0	# a lock to prevent recursion.

		self.zoomfactorx = 1.0	# Scale everything to this! Done in the Widgets for this
					# node rather than the geometric primitives!
		self.destroynode = None	# This is the node to destroy (has been cut or deleleted.)
		self.minimal_channels = 0 # Whether to show all or just a few channels.


	def destroy(self):
		if self.scene is not None:
			self.scene.destroy()
			self.scene = None
		self.geodl.destroy()

	def __add_commands(self):
		self.commands = [
			CLOSE_WINDOW(callback = (self.hide, ())),
			CANVAS_ZOOM_IN(callback = (self.zoomincall, ())),
			CANVAS_ZOOM_OUT(callback = (self.zoomoutcall, ())),
			]

		self.commands = self.commands + [
			TOPARENT(callback = (self.toparent, ())),
			TOCHILD(callback = (self.tochild, (0,))),
			NEXTSIBLING(callback = (self.tosibling, (1,))),
			PREVSIBLING(callback = (self.tosibling, (-1,))),
			EXPAND(callback = (self.expandcall, ())),
			PASTE_UNDER(callback = (self.pasteundercall, ())),
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
		self.select_node(self.scene.mainnode)
		self.recalc()
		self.draw()

	def hide(self):
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

	def tochild(self, i):
		print "Not implemented: TemporalView.tochild()"

	def tosibling(self, direction):
		print "Not implemented: TemporalView.tosibling()"

	def helpcall(self):
		if self.focusobj: self.focusobj.helpcall()

	def expandcall(self):
		if self.focusobj: self.focusobj.expandcall()
		self.draw()

	def expandallcall(self, expand):
		if self.focusobj: self.focusobj.expandallcall(expand)
		self.draw()

	def cleanup(self):
		pass

	def is_showing(self):
		return self.showing

	def init_scene(self):
		if self.scene is not None:
			self.scene.destroy()
		self.scene = TimeCanvas(self.root, self, minimal_channels = self.minimal_channels)
		self.scene.setup()
		self.scene.set_display(self.geodl)

	def get_geodl(self):
		return self.geodl

	def goto_node(self, node):
		if not isinstance(node, MMNode.MMNode):
			print "DEBUG: temporal view could not jump to a non-MMNode."
			return -1
		self.root = node
		self.minimal_channels = 1
		self.init_scene()
		self.redraw()

	def draw(self):
		self.geodl.redraw()

	def redraw(self):
		# No optimisation - do a complete scene graph redraw.
		self.init_scene()
		self.recalc()
		self.draw()

	def recalc(self):
		self.scene.recalc(zoom=self.zoomfactorx)

	def get_geometry(self):
		# (?!) called when this window is saved.
		if self.window:
			self.last_geometry = self.geodl.getgeometry()
		else:
			self.last_geometry = (0,0,0,0) # guessing the data type
			

	def update_popupmenu_node(self):
		# Sets the popup menu to channel mode.
		# TODO: what about the root node and so forth?
		commands = self.commands
		popupmenu = [self.menu_no_nodes]	# there needs to be a default.
		if len(self.selected_nodes) != 1:
			print "Warning: Selection is: ", self.selected_nodes
			print "Warning: Multiple selection pop-ups not thought about yet."
		else:
			node = self.selected_nodes[0].node
			commands = commands + node.GetCommands()
			# - /not/ system independent: popupmenu = node.GetContextMenu()
			##n = self.selected_nodes[0].node
			if node.GetType() in MMNode.interiortypes:
				popupmenu = self.menu_interior_nodes
				#commands = commands + self.interiorcommands \
				#	   + self.pasteinteriorcommands \
				#	   + self.structure_commands 
				#if node.children:
				#	commands = commands + self.navigatecommands
				#if node is not self.root:
				#	commands = commands + self.notatrootcommands
			else:
				popupmenu = self.menu_leaf_nodes
		self.setcommands(commands)
		self.setpopup(popupmenu)

	def update_popupmenu_channel(self):
		# Sets the popup menu to node mode.
		commands = self.commands
		popupmenu = self.menu_no_channel
		if len(self.selected_regions) != 1:
			print "Warning: Selected region is: ", self.selected_regions
			print "Warning: Multiple channel selection not thought about yet."
		else:
			popupmenu = self.menu_channel
		self.setcommands(commands)
		self.setpopup(popupmenu)


######################################################################
		# Selection management.

	def select_channel(self, channel):
		self.selected_regions.append(channel)
		self.just_selected = channel
		self.focusobj = channel.channel
		self.update_popupmenu_channel()

	def unselect_channels(self):
		for i in self.selected_regions:
			i.unselect()
		self.selected_regions = []
		self.focusobj = None

	def select_node(self, node):
		# Called back from the scene
		assert isinstance(node, MMNodeWidget)
		self.just_selected = node
		self.selected_nodes.append(node)
		self.focusobj = node
		self.update_popupmenu_node()

	def unselect_nodes(self):
		# Called back from the scene
		for i in self.selected_nodes:
			i.unselect()
		self.selected_nodes = []
		self.focusobj = None

######################################################################
		# Edit manager interface

	def transaction(self, type):
		return 1

	def rollback(self):
		print "TODO: rollback."

	def commit(self, type):
		if self.destroynode is not None:
			self.destroynode.destroy()
			self.destroynode = None
		self.unselect_nodes()
		self.unselect_channels()
		self.redraw()

	def kill(self):
		self.destroy()

	def globalfocuschanged(self, focustype, focusobject):
		if self.just_selected:
			self.just_selected = None
			return
		if self.recurse_lock:
			return
		self.recurse_lock = 1
		if self.scene:
			if focustype == 'MMNode':
				try:
					self.scene.select_node(focusobject.views['tempview'])
					self.just_selected = None
				except KeyError:
					pass # Don't worry about it. This means it is probably a structure node.
					# What we /could/ do is select all of the syncbars associated to it..
			elif focustype == 'MMChannel':
				self.scene.select_mmchannel(focusobject)
				self.just_selected = None
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
		if isinstance(self.just_selected, MMWidget) or isinstance(self.just_selected, MultiMMWidget):
			self.editmgr.setglobalfocus('MMNode', self.just_selected.node)
		elif isinstance(self.just_selected, ChannelWidget):
			self.editmgr.setglobalfocus('MMChannel', self.just_selected.get_channel())
#		print "DEBUG: Calling edit manager..", time.time()-before

	def ev_mouse0release(self, dummy, window, event, params):
		#print "mouse released! :-( "
		pass

	def ev_mouse2press(self, dummy, window, event, params):
		self.ev_mouse0press(self, dummy, window, event, params)

	def ev_mouse2release(self, dummy, window, event, params):
		#print "rigth mouse released! :-)"
		pass

	def ev_exit(self, dummy, window, event, params):
		return

	def ev_pastefile(self, dummy, window, event, params):
		print "TODO: Pasting a file!"

	def ev_dragfile(self, dummy, window, event, params):
		return windowinterface.DROPEFFECT_MOVE

	def ev_dropfile(self, dummy, window, event, params):
		x,y,filename = params[0:5]
		x,y = self.rel2abs((x,y))
		if event == WMEVENTS.DropFile:
			url = MMurl.pathname2url(filename)
		else:
			url = filename
		self.ev_mouse0press(dummy,window,event,params)
		self.scene.dropfile((x,y),url)

	def ev_dragnode(self, dummy, window, event, params):
		return windowinterface.DROPEFFECT_MOVE
		#x,y,mode, xf, yf= params[0:5]
		#x,y = self.rel2abs((x,y))
		#xf, yf = self.rel2abs((xf, yf))
		#return self.scene.dragging_node((xf,yf), (x, y), mode)
		

	def ev_dropnode(self, dummy, window, event, params):
		x,y,mode,xf,yf = params[0:5]
		x,y = self.rel2abs((x,y))
		xf,yf = self.rel2abs((xf,yf))
		self.ev_mouse0press(dummy,window,event,params)
		self.scene.dropnode((xf,yf), (x, y))

	def zoomincall(self):
		self.zoomfactorx = self.zoomfactorx * 2
		self.recalc()
		self.draw()

	def zoomoutcall(self):
		self.zoomfactorx = self.zoomfactorx / 2
		self.recalc()
		self.draw()

	def pasteundercall(self):
		# This needs an index to say which element is going to be pasted here.
		# For the meanwhile, paste at the end.
		if len(self.selected_nodes) is not 1:
			windowinterface.beep()
			return
		elif isinstance(self.selected_nodes[0], TimeWidget) \
		     and isinstance(self.selected_nodes[0].node, EditableObjects.EditableMMNode):
			self.selected_nodes[0].node.pasteundercall(-1) # paste at the end ("-1")
