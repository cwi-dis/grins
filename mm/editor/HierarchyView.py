__version__ = "$Id$"

# New hierarchy view implementation.

# Beware: this module uses X11-like world coordinates:
# positive Y coordinates point down from the top of the window.
# Also the convention for box coordinates is (left, top, right, bottom)

# mjvdg: TODO:
# drawing with no children doesn't work well yet.
# There seems to be a bug which prevents an image being displayed if starting from
# an empty 'document' - investigate.

import windowinterface, WMEVENTS
import MMAttrdefs
import MMNode
import EditableObjects
from HierarchyViewDialog import HierarchyViewDialog
import BandwidthCompute
from usercmd import *
import os, sys
import urlparse, MMurl
from math import ceil
import string
import MMmimetypes
import features
import compatibility
import Widgets
import StructureWidgets
import Help
import AttrEdit
import Hlinks				# for merging nodes only.
import Sizes

import settings

# Color settings
from AppDefaults import *

######################################################################
class HierarchyView(HierarchyViewDialog):
	def __init__(self, toplevel):
		self.toplevel = toplevel

		self.window = None
		self.last_geometry = None

		self.root = self.toplevel.root
		self.scene_graph = None

		self.editmgr = self.root.context.editmgr

		self.thumbnails = settings.get('structure_thumbnails')
		self.showplayability = 1
		self.usetimestripview = 0
		if features.H_TIMESTRIP in features.feature_set:
			if self._timestripconform():
				self.usetimestripview = 1
			else:
				windowinterface.showmessage("Warning: document structure cannot be displayed as timestrip.  Using structured view.", parent=self.window)
		self.pushbackbars = features.H_VBANDWIDTH in features.feature_set 	# display download times as pushback bars on MediaWidgets.
		self.dropbox = features.H_DROPBOX in features.feature_set	# display a drop area at the end of every node.
		self.transboxes = features.H_TRANSITIONS in features.feature_set # display transitions
		self.translist = []	# dynamic transition menu
		self.show_links = 1	# Show HTML links??? I think.. -mjvdg.
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')
		
		self.__add_commands()
		self.__dragside = None
		HierarchyViewDialog.__init__(self)

	def __init_state(self):
		# Sets the state of this view - i.e. selected nodes etc.
		# This gets called before the scene is initialised.
		# Drawing optimisations
		self.drawing = 0	# A lock to prevent recursion in the draw() method of self.
		self.redrawing = 0	# A lock to prevent recursion in redraw()
		self.need_refresh = 1	# Whether to refresh the whole scene graph, for example when a node is added / deleted / moved.
		self.need_resize = 1	# Whether the tree needs to be resized. Implies need_redraw
		self.need_redraw = 1	# Whether the scene graph needs redrawing.

		self.base_display_list = None # A display list that may be cloned and appended to.
		self.extra_displist = None

		# Selections
		self.selected_widget = None # Is a MMWidget, which could resemble a node or a widget.
		self.old_selected_widget = None	# This is the node that used to have the focus but needs redrawing.
		self.selected_icon = None
		self.old_selected_icon = None

		self.multi_selected_widgets = [] # When there are multiple selected widgets.
					# For the meanwhile, you can only multi-select MMWidgets which have nodes.
		self.old_multi_selected_widgets = [] # The old list of widgets that need to all be unselected.
		self.need_redraw_select = 0
		
		self.begin_event_source = None # This is the specially selected "I am the node from which a new begin event will be made to"
		self.droppable_widget = None # ahh.. something that sjoerd added. Assume that it's used for the fancy drop-notification.
		self.old_droppable_widget = None

		# Remove sometime.
		self.focusnode = self.prevfocusnode = self.root	# : MMNode - remove when no longer used.

		self.arrow_list = []	# A list of arrows to be drawn after everything else.
		self.__select_arrow_list = [] # Used for working out the selected arrows.

	def __add_commands(self):
		# Add the user-interface commands that are used for this window.
		lightweight = features.lightweight
		self.commands = [
			CLOSE_WINDOW(callback = (self.hide, ())),

			COPY(callback = (self.copycall, ())),
			COPYPROPERTIES(callback = (self.copypropertiescall, ())),
			PASTEPROPERTIES(callback = (self.pastepropertiescall, ())),

			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),

			THUMBNAIL(callback = (self.thumbnailcall, ())),

			EXPANDALL(callback = (self.expandallcall, (1,))),
			COLLAPSEALL(callback = (self.expandallcall, (0,))),
			
			COMPUTE_BANDWIDTH(callback = (self.bandwidthcall, ())),
			CREATE_BEGIN_EVENT_SOURCE(callback = (self.create_begin_event_source, ())),
			CREATE_BEGIN_EVENT_DESTINATION(callback = (self.create_begin_event_dest, ())),
			FIND_EVENT_SOURCE(callback = (self.find_event_source, ())),
			]

		self.interiorcommands = self._getmediaundercommands(self.toplevel.root.context) + [
			EXPAND(callback = (self.expandcall, ())),
			#MERGE_CHILD(callback = (self.merge_child, ())),
		]

		if not lightweight:
			self.interiorcommands.append(TIMESCALE(callback = (self.timescalecall, ('global',))))
			self.interiorcommands.append(LOCALTIMESCALE(callback = (self.timescalecall, ('focus',))))
			self.interiorcommands.append(CORRECTLOCALTIMESCALE(callback = (self.timescalecall, ('cfocus',))))
			self.commands.append(PLAYABLE(callback = (self.playablecall, ())))

		self.mediacommands = self._getmediacommands(self.toplevel.root.context)

		self.pasteinteriorcommands = [
				PASTE_UNDER(callback = (self.pasteundercall, ())),
				]

		self.pastenotatrootcommands = [
				PASTE_BEFORE(callback = (self.pastebeforecall, ())),
				PASTE_AFTER(callback = (self.pasteaftercall, ())),
				]
		self.notatrootcommands = [
				NEW_SEQ(callback = (self.createseqcall, ())),
				NEW_PAR(callback = (self.createparcall, ())),
				NEW_SWITCH(callback = (self.createaltcall, ())),
				DELETE(callback = (self.deletecall, ())),
				CUT(callback = (self.cutcall, ())),
				]			
		self.structure_commands = [
				NEW_BEFORE(callback = (self.createbeforecall, ())),
				NEW_BEFORE_SEQ(callback = (self.createbeforeintcall, ('seq',))),
				NEW_BEFORE_PAR(callback = (self.createbeforeintcall, ('par',))),
				NEW_BEFORE_SWITCH(callback = (self.createbeforeintcall, ('switch',))),
				NEW_AFTER(callback = (self.createaftercall, ())),
				NEW_AFTER_SEQ(callback = (self.createafterintcall, ('seq',))),
				NEW_AFTER_PAR(callback = (self.createafterintcall, ('par',))),
				NEW_AFTER_SWITCH(callback = (self.createafterintcall, ('switch',))),
				#EDIT_TVIEW(callback = (self.edit_in_tview, ())),
				]
		self.rpconvertcommands = [
			RPCONVERT(callback = (self.rpconvertcall, ())),
			]
		self.mediacommands = self.mediacommands + self.structure_commands
		if self.toplevel.root.context.attributes.get('project_boston', 0):
			self.structure_commands.append(NEW_AFTER_EXCL(callback = (self.createafterintcall, ('excl',))))
			self.structure_commands.append(NEW_BEFORE_EXCL(callback = (self.createbeforeintcall, ('excl',))))

			
##		else:			# TODO: clean this up. This should be later.
##			self.interiorcommands = []
##			self.pasteinteriorcommands = []
##			self.pastenotatrootcommands = []
##			self.notatrootcommands = [
##				DELETE(callback = (self.deletecall, ())),
##				CUT(callback = (self.cutcall, ())),
##				]

		if self.toplevel.root.context.attributes.get('project_boston', 0):
			self.notatrootcommands.append(NEW_EXCL(callback = (self.createexclcall, ())))
		self.animatecommands = self._getanimatecommands(self.toplevel.root.context)
		self.createanchorcommands = [
			CREATEANCHOR(callback = (self.createanchorcall, ())),
			]
		self.noslidecommands = [
			PLAYNODE(callback = (self.playcall, ())),
			PLAYFROM(callback = (self.playfromcall, ())),
			]
		if not lightweight:
			self.noslidecommands = self.noslidecommands + [
				ANCHORS(callback = (self.anchorcall, ())),
				]

		self.finishlinkcommands = [
			FINISH_LINK(callback = (self.hyperlinkcall, ())),
			]
		self.navigatecommands = [
			TOPARENT(callback = (self.toparent, ())),
			TOCHILD(callback = (self.tochild, (0,))),
			NEXTSIBLING(callback = (self.tosibling, (1,))),
			PREVSIBLING(callback = (self.tosibling, (-1,))),
			]
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commands.append(HELP(callback=(self.helpcall,())))
		self.transitioncommands = [
			TRANSITION(callback = self.transition_callback),
			]

	def __repr__(self):
		return '<HierarchyView instance, root=' + `self.root` + '>'

	def _timestripconform(self):
		# Return true if document conforms to the format needed for timestrip display
		if self.root.GetType() != 'seq' or len(self.root.children) != 1:
			return 0
		child = self.root.children[0]
		if child.GetType() != 'par':
			return 0
		for grandchild in child.children:
			if grandchild.GetType() != 'seq':
				return 0
		return 1
		
	def _getmediaundercommands(self, ctx):
		heavy = not features.lightweight
		rv = [
			NEW_UNDER(callback = (self.createundercall, ())),
			]
		rv.append(NEW_UNDER_SEQ(callback = (self.createunderintcall, ('seq',))))
		rv.append(NEW_UNDER_PAR(callback = (self.createunderintcall, ('par',))))
		rv.append(NEW_UNDER_SWITCH(callback = (self.createunderintcall, ('switch',))))
		if ctx.attributes.get('project_boston', 0):
			rv.append(NEW_UNDER_EXCL(callback = (self.createunderintcall, ('excl',))))
		if heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_UNDER_IMAGE(callback = (self.createundercall, ('image',))))
		if  heavy or ctx.compatchannels(chtype='sound'):
			rv.append(NEW_UNDER_SOUND(callback = (self.createundercall, ('sound',))))
		if heavy or ctx.compatchannels(chtype='video'):
			rv.append(NEW_UNDER_VIDEO(callback = (self.createundercall, ('video',))))
		if heavy or ctx.compatchannels(chtype='text'):
			rv.append(NEW_UNDER_TEXT(callback = (self.createundercall, ('text',))))
		if heavy or ctx.compatchannels(chtype='html'):
			rv.append(NEW_UNDER_HTML(callback = (self.createundercall, ('html',))))
		if heavy or ctx.compatchannels(chtype='svg'):
			rv.append(NEW_UNDER_SVG(callback = (self.createundercall, ('svg',))))
		rv.append(NEW_UNDER_ANIMATION(callback = (self.createundercall, ('animate',))))
		return rv


	def _getmediacommands(self, ctx):
		# Enable commands to edit the media

		heavy = not features.lightweight

		rv = []
		if heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_BEFORE_IMAGE(callback = (self.createbeforecall, ('image',))))
		if heavy or ctx.compatchannels(chtype='sound'):
			rv.append(NEW_BEFORE_SOUND(callback = (self.createbeforecall, ('sound',))))
		if heavy or ctx.compatchannels(chtype='video'):
			rv.append(NEW_BEFORE_VIDEO(callback = (self.createbeforecall, ('video',))))
		if heavy or ctx.compatchannels(chtype='text'):
			rv.append(NEW_BEFORE_TEXT(callback = (self.createbeforecall, ('text',))))
		if heavy or ctx.compatchannels(chtype='html'):
			rv.append(NEW_BEFORE_HTML(callback = (self.createbeforecall, ('html',))))
		if heavy or ctx.compatchannels(chtype='svg'):
			rv.append(NEW_BEFORE_SVG(callback = (self.createbeforecall, ('svg',))))
		if heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_AFTER_IMAGE(callback = (self.createaftercall, ('image',))))
		if heavy or ctx.compatchannels(chtype='sound'):
			rv.append(NEW_AFTER_SOUND(callback = (self.createaftercall, ('sound',))))
		if heavy or ctx.compatchannels(chtype='video'):
			rv.append(NEW_AFTER_VIDEO(callback = (self.createaftercall, ('video',))))
		if heavy or ctx.compatchannels(chtype='text'):
			rv.append(NEW_AFTER_TEXT(callback = (self.createaftercall, ('text',))))
		if heavy or ctx.compatchannels(chtype='html'):
			rv.append(NEW_AFTER_HTML(callback = (self.createaftercall, ('html',))))
		if heavy or ctx.compatchannels(chtype='svg'):
			rv.append(NEW_AFTER_SVG(callback = (self.createaftercall, ('svg',))))
		rv.append(NEW_BEFORE_ANIMATION(callback = (self.createbeforecall, ('animate',))))
		rv.append(NEW_AFTER_ANIMATION(callback = (self.createaftercall, ('animate',))))
		rv.append(MERGE_PARENT(callback=(self.merge_parent, ())))
		return rv

	def _getanimatecommands(self, ctx):
		rv = []
		rv.append(NEW_BEFORE_ANIMATION(callback = (self.createbeforecall, ('animate',))))
		rv.append(NEW_AFTER_ANIMATION(callback = (self.createaftercall, ('animate',))))
		rv.append(NEW_UNDER_ANIMATION(callback = (self.createundercall, ('animate',))))
		return rv

	def __compute_commands(self, commands):
		# Compute the commands for the current selected object.
		# TODO: Make context menu setting within the StructureWidgets menu instead.
		fnode = self.focusnode
		fntype = fnode.GetType()	

		commands = commands + self.noslidecommands
		if self.toplevel.links and self.toplevel.links.has_interesting(): # ??!! -mjvdg
			commands = commands + self.finishlinkcommands
		if fntype in MMNode.interiortypes:
			commands = commands + self.interiorcommands # Add interior structure modifying commands.
		if fntype not in MMNode.interiortypes and \
		   fnode.GetChannelType() != 'sound' and \
		   not (self.toplevel.links and self.toplevel.links.islinksrc(fnode)):
			commands = commands + self.createanchorcommands

		if fnode is not self.root:
			# can't do certain things to the root
			#if fnode.__class__ is not SlideMMNode:
			commands = commands + self.notatrootcommands + self.mediacommands
			#
			commands = commands + self.navigatecommands[0:1]
			pchildren = fnode.GetParent().GetChildren()

			findex = pchildren.index(fnode)
			if findex > 0:
				commands = commands + self.navigatecommands[3:4]
			if findex < len(pchildren) - 1:
				commands = commands + self.navigatecommands[2:3]

		if fntype in MMNode.leaftypes and fnode.GetChannelType() != 'animate':
			commands = commands + self.animatecommands[2:3]
		if fntype == 'ext':
			commands = commands + self.rpconvertcommands

		# Enable "paste" commands depending on what is in the clipboard.
		t, n = self.editmgr.getclip()
		if t == 'node' or t == 'multinode' and n is not None:
			if fntype in MMNode.interiortypes:
				# can only paste inside interior nodes
				commands = commands + self.pasteinteriorcommands
			if fnode is not self.root:
				# can't paste before/after root node
				commands = commands + self.pastenotatrootcommands
		# commands is not mutable here.
		return commands

	
	def aftersetfocus(self):
		# Called after the focus has been set to a specific node.
		# This:
		# 1) Determines the commands for the node (requires: node, view?)
		# 2) Determines a pop-up menu for the node (requires: node, view if there is view spec info.)
		fnode = self.selected_widget.get_node()
		#commands = []

		if isinstance(self.selected_widget, StructureWidgets.TransitionWidget):
			which, transitionnames = self.selected_widget.posttransitionmenu()
			self.translist = []
			for trans in transitionnames:
				self.translist.append((trans, (which, trans)))

		commands = self.commands # Use a copy.. the original is a template.
		fntype = self.focusnode.GetType()
		
		# Choose the pop-up menu.
		if len(self.multi_selected_widgets) > 0:
			popupmenu = self.multi_popupmenu
		elif fntype in MMNode.interiortypes: # for all internal nodes.
			popupmenu = self.interior_popupmenu
			# if node has children enable
			# the TOCHILD command
			if fnode.children:
				commands = commands + self.navigatecommands[1:2]
		elif isinstance(self.selected_widget, StructureWidgets.TransitionWidget):
			popupmenu = self.transition_popupmenu
			commands = commands + self.transitioncommands
		else:
			popupmenu = self.leaf_popupmenu	# for all leaf nodes.

		commands = self.__compute_commands(commands) # Adds to the commands for the current focus node.		
		#commands = fnode.GetCommands() # The preferred way of doing things.
		self.setcommands(commands)

		# Forcidably change the pop-up menu if we have selected an Icon.
		if self.selected_icon is not None:
			a = self.selected_icon.get_contextmenu()
			if a is not None:
				self.setpopup(a)
			else:
				self.setpopup(popupmenu)
		else:
			self.setpopup(popupmenu)

		self.setstate()

		# make sure focus is visible
		if self.focusnode.GetParent():
			self.focusnode.GetParent().ExpandParents()


	##############################################################################
	#
	# Drawing code
	#
	##############################################################################

	def create_scene_graph(self):
		# Iterate through the MMNode structure (starting from self.root)
		# and create a scene graph from it.
		# As such, any old references into the old scene graph need to be reinitialised.
		self.__init_state()
		self.scene_graph = StructureWidgets.create_MMNode_widget(self.root, self)
		#if self.window and self.focusnode:
		#	self.select_node(self.focusnode)
		#	widget = self.focusnode.views['struct_view']
		#	self.window.scrollvisible(widget.get_box(), windowinterface.UNIT_PXL)


	# Callbacks for the Widget classes.
	def get_window_size_abs(self):
		return self.mcanvassize

	def show(self):
		if self.is_showing():
			HierarchyViewDialog.show(self)
			return
		HierarchyViewDialog.show(self)
# also done in refresh_scene_graph
##		self.aftersetfocus()
		self.window.bgcolor(BGCOLOR)
		# Other administratrivia
		self.editmgr.register(self,1) # 1 means we want to participate in global focus management.
		self.toplevel.checkviews()
		
		self.refresh_scene_graph()
		self.need_resize = 1
		focustype, focusobject = self.editmgr.getglobalfocus()
		if focustype is None and focusobject is None:
			self.editmgr.setglobalfocus('MMNode', self.root)
		else:
			self.globalfocuschanged(focustype, focusobject)
		if self.need_redraw:
			self.draw()

	def refresh_scene_graph(self):
		# Recalculates the node structure from the MMNode structure.
		if self.scene_graph is not None:
			self.scene_graph.destroy()
		self.create_scene_graph()

	######################################################################
		# Redrawing the Structure View.
	# A small note about redrawing:
	# * Only call at the end of (every) top-level event handlers just before you return to the
	#   event loop.
	# * Optimisations are done using flags - if you want certain optimisations done, set and read
	#   these flags. This is much more flexible and easier than state management.
	# -mjvdg.

		
	def draw(self):
		# Recalculate the size of all boxes and draw on screen.
		if self.drawing:
			return
		self.drawing = 1

		if self.need_resize:
			#print "DEBUG: resizing scene..", time.time()
			self.resize_scene()	# will cause a redraw() event anyway.
			#print "DEBUG: done resizing scene..", time.time()
			# When you resize the canvas, a callback will make it redraw itself.
		else:
			# This doesn't make a callback.
			#print "DEBUG: only drawing the scene", time.time()
			self.draw_scene()
			#print "DEBUG: finished drawing the scene", time.time()
		self.drawing = 0
		self.setstate()

	def resize_scene(self):
		# Set the size of the first widget.
		self.need_resize = 0
		self.need_redraw = 1
		x,y = self.scene_graph.recalc_minsize()
		self.mcanvassize = x,y

		if x < 1.0 or y < 1.0:
			print "Error: unconverted relative coordinates found. HierarchyView:497"
		self.scene_graph.moveto((0,0,x,y))
		self.scene_graph.recalc()
		self.window.setcanvassize((SIZEUNIT, x, y)) # Causes a redraw() event.

	def draw_scene(self):
		# Only draw the scene, nothing else.
		# This method uses several flags for optimisations.
		# By setting these flags, you can control which parts of the scene
		# need to be recalculated or redrawn.
		if self.redrawing:
			print "Error: recursive redraws."
			return
		self.redrawing = 1

##		import time

		# 1. Do we need a new display list?
		if self.need_redraw or self.base_display_list is None:
			# Make a new display list.
			d = self.window.newdisplaylist(BGCOLOR, windowinterface.UNIT_PXL)
			self.scene_graph.draw(d) # Keep it for later!
			self.need_redraw = 0
			self.droppable_widget = None
			self.old_droppable_widget = None
			self.old_selected_widget = None
			self.old_selected_icon = None
			self.old_multi_selected_widgets = []
		elif self.selected_widget is self.old_selected_widget and \
		     self.selected_icon is self.old_selected_icon and \
		     self.droppable_widget is self.old_droppable_widget and \
		     len(self.old_multi_selected_widgets)==0 and \
		     not self.need_redraw_selection:
			# nothing to do
			self.redrawing = 0
			return
		else:
			d = self.base_display_list.clone()

		# 2. Undraw stuff.
		for i in self.old_multi_selected_widgets:
			i.draw_unselected(d)
		self.old_multi_selected_widgets = []

		if self.old_droppable_widget is not None:
			if self.old_droppable_widget is self.selected_widget:
				pass
			elif self.old_droppable_widget is self.old_selected_widget:
				pass
			else:
				self.old_droppable_widget.draw_unselected(d)
			self.old_droppable_widget = None
		if self.selected_widget is not self.old_selected_widget:
			if self.old_selected_widget is not None:
				self.old_selected_widget.draw_unselected(d)
			self.selected_widget.draw_selected(d)
			self.old_selected_widget = self.selected_widget
		if self.selected_icon is not self.old_selected_icon:
			if self.old_selected_icon is not None:
				self.old_selected_icon.draw_unselected(d)
			self.selected_icon.draw_selected(d)
		if self.droppable_widget is not None:
			self.droppable_widget.draw_box(d)
			self.old_droppable_widget = self.droppable_widget

		# Multiple selection.
		for i in self.multi_selected_widgets:
			i.draw_selected(d)

		# Draw the arrows on top.
		newdl = d
		if self.arrow_list:
			newdl = d.clone()
			self.draw_arrows(d)
		d.render()
		if self.extra_displist is not None:
			self.extra_displist.close()
			self.extra_displist = None
		if self.base_display_list is not None:
			self.base_display_list.close()
		self.base_display_list = newdl
		if d is not newdl:
			self.extra_displist = d	# remember so that we can close later
		self.need_redraw_selection = 0
		self.redrawing = 0

	def add_arrow(self, caller, color, source, dest):
		# Draw arrows on top of everything else.
		self.arrow_list.append((caller, color,source, dest))

	def draw_arrows(self, displist):
		for i in self.arrow_list:
			caller, color,source,dest = i
			displist.drawarrow(color, source, dest)
		self.__select_arrow_list = self.arrow_list
		self.arrow_list = []	# You need to remake it every time.

	def hide(self, *rest):
		if not self.is_showing():
			return
		HierarchyViewDialog.hide(self)
		self.cleanup()
		self.editmgr.unregister(self)
		self.toplevel.checkviews()

	def is_showing(self):
		return self.window is not None

	def destroy(self):
		if self.scene_graph is not None:
			self.scene_graph.destroy()
		self.scene_graph = None
		self.hide()

	def get_geometry(self):
		if self.window:
			self.last_geometry = self.window.getgeometry()

	def init_display(self):
		self.draw()
		
	def opt_init_display(self):
		self.draw()

	def render(self):
		self.draw()

	def opt_render(self):
		self.draw() # Is this needed?

	#################################################
	# Outside interface (inherited from ViewDialog) #
	#################################################

	def getfocus(self):
		return self.focusnode

	def globalsetfocus(self, node):
		#print "DEBUG: HierarchyView received globalsetfocus with ", node
		if not self.is_showing():
			return
		if not self.root.IsAncestorOf(node):
			raise RuntimeError, 'bad node passed to globalsetfocus'
		self.select_node(node, 1)

	def globalfocuschanged(self, focustype, focusobject, redraw = 1):
		# for now, catch only MMNode focus
		#print "DEBUG: HierarchyView received globalfocuschanged with ", focustype
		# XXX Temporary: pick first item of multiselect. Michael will
		# fix this later.
		if not focusobject:
			return # XXXX Or should we de-select?
		if type(focusobject) == type([]):
			focusobject = focusobject[0][1]
			print "XXX Selecting first item of multiselect"
		if not hasattr(focusobject, 'getClassName'):
			print 'Error: focus objects need getClassName() method!', focusobject
			return
		if focusobject.getClassName() != 'MMNode':
			return
		if self.selected_widget is not None and self.selected_widget.get_node() is focusobject:
			return
		self.select_node(focusobject, external = 1, scroll = redraw)
		if redraw:
			self.draw()

	#################################################
	# Event handlers                                #
	#################################################
	# Note that any interactive event should probably call self.draw().
	# Self.draw() uses a flag mechanism, and is smart enough not to waste
	# time redrawing things that it doesn't need.
	
	def redraw(self, *rest):
		# Handles redraw events, for example when the canvas is resized.
		self.draw_scene()

	def mousemove(self, dummy, window, event, point):
		if self.__dragside is not None:
			self.window._dragging = None # XXX win32 specific, should define proper interface
			obj, side, timemapper, timeline = self.__dragside
			if timeline is not None:
				x,y,w,h = timeline.get_box()
				px, py = point
				apply(self.window.drawxorline, self.__line)
				self.__line = (px,py),(px, y+h/2)
				apply(self.window.drawxorline, self.__line)
		elif self.scene_graph is not None:
			rv = self.scene_graph.get_obj_near(point)
			if rv is None or rv[2] is None:
				self.window.setcursor('')
				return
			self.window.setcursor('darrow')

	def mouse(self, dummy, window, event, params):
		x, y, dummy, modifier = params
		px = int(x * self.mcanvassize[0] + .5) # This is kind of dumb - it has already been converted from pixels
		py = int(y * self.mcanvassize[1] + .5) #  to floats in the windowinterface.
		rv = self.scene_graph.get_obj_near((px, py))
		self.__dragside = rv
		if rv is None or rv[2] is None:
			self.__dragside = None
			if x >= 1 or y >= 1:
				# out of bounds, beep and ignore
				windowinterface.beep()
				return
			if modifier == 'add':
				self.addclick(px, py)
			else:
				self.click(px, py)
		else:
			# start dragging
			self.mousedrag(1)
			obj, side, timemapper, timeline = rv
			if timeline is not None:
				x,y,w,h = timeline.get_box()
				self.__line = (px,py),(px, y+h/2)
				self.window.drawxorline((px,py),(px, y+h/2))

	def mouse0release(self, dummy, window, event, params):
		x,y = params[0:2]
		px = int(x * self.mcanvassize[0] + .5)
		py = int(y * self.mcanvassize[1] + .5)
		if self.__dragside is not None:
			obj, side, timemapper, timeline = self.__dragside
			self.__dragside = None
			self.mousedrag(0)
			if timeline is not None:
				apply(self.window.drawxorline, self.__line)
				self.__line = None
			if obj.timeline is not None:
				if side == 'left':
					# can't drag left side of timeline
					return
				l,t,r,b = obj.timeline.get_pos_abs()
				obj.timeline.setminwidth(max(px-l, 1))
				self.need_resize = 1
				self.draw()
				return
			t = obj.pixel2time(px, side, timemapper)
			em = self.editmgr
			if not em.transaction():
				return
			if side == 'left':
				# delete first simple delay syncarc
				for arc in obj.node.GetAttrDef('beginlist', []):
					if arc.srcnode == 'syncbase' and arc.event is None and arc.marker is None and arc.channel is None:
						em.delsyncarc(obj.node, 'beginlist', arc)
						break
				newarc = MMNode.MMSyncArc(obj.node, 'begin', srcnode = 'syncbase', delay = t)
				em.addsyncarc(obj.node, 'beginlist', newarc, 0)
			else:
				em.setnodeattr(obj.node, 'duration', t)
			em.commit()
			return
		if x >= 1 or y >= 1:
			# out of bounds, ignore
			return
		self.toplevel.setwaiting()
		obj = self.scene_graph.get_clicked_obj_at((px,py))
		if obj:
##			import time
##			print "DEBUG: releasing mouse.." , time.time()
			obj.mouse0release((px, py))
##			print "DEBUG: drawing...", time.time()
			self.draw()
##			print "Done drawing. ", time.time()


	######################################################################
	#
	#	 Operations on nodes.
	#	 (i.e. interface to the edit manager.
	#
	######################################################################
	#
	# There is a general pattern to all of these functions.
	# 1. Get the necessary information. If something is generic, stick it in Editablenode.py
	# 2. em.transaction()
	# 3. Do the editmanager operations.
	# 4. em.commit.
	#
	# # # # # # # # # # # # # # # # # # 
	# Operations on nodes.
	#
	# Always: Add, delete(/remove), Edit.
	#
	# Nodes
	# -----
	# * Add a node
	# * Delete a node
	# * Edit a node (pop up properties)
	# * Copy a node
	# * Cut a node
	# * Paste a node
	# * Drag and drop
	#   - Move
	#   - Copy
	#   - Move to another view (not implemented?)
	#   - Drop a file
	#
	# Multiple selection (only nodes selected)
	# ------------------
	# * Multiple selections cannot be added.
	# * Delete
	# * Edit (multiple properties??)
	# * Copy
	# * Cut
	# * Paste
	# * Drag and drop a multiple selection
	#   - Move a selection (Makes all nodes children of the target).
	#   - Copy a selection (ditto)
	#   - Drop multiple files?
	#   - Move multiple nodes to another view?

	######################################################################
	# Adding a node.
	# This code is near the end of this class under various createbefore.. createafter.. callbacks.
	# At some stage they need to be moved here; there is no need to yet.
	
	######################################################################
	# Delete the selected node.
	def fixselection(self, nodes):
		# fix the structure view selection nodes is a list of
		# nodes that are going to be deleted we select the
		# common ancestor of these nodes, and if that is also
		# to be deleted, we select a node near by.
		# this also starts a transaction
		# returns true if successful and deletion can proceed
		if not nodes:
			return 0	# failed
		anc = nodes[0]
		for n in nodes:
			if n is self.root:
				# can't delete root node
				windowinterface.beep()
				return 0 # failed
			anc = n.CommonAncestor(anc)
		if not self.editmgr.transaction():
			return 0	# failed
		if anc in nodes:
			parent = anc.GetParent()
			siblings = parent.GetChildren()
			nf = siblings.index(anc)
			if nf < len(siblings)-1:
				self.select_node(siblings[nf+1])
			elif nf > 0:
				self.select_node(siblings[nf-1])
			else:
				self.select_node(parent)
		else:
			self.select_node(anc)
		return 1		# succeeded

	def deletecall(self, cut = 0):
		if len(self.multi_selected_widgets) > 0:
			# Delete multiple nodes.
			self.toplevel.setwaiting()
			nodes = self.get_multi_nodes()
			if self.fixselection(nodes):
				for n in nodes:
					self.editmgr.delnode(n)
				self.fixsyncarcs(self.root, nodes)
				self.editmgr.commit()
				if cut:
					self.__clean_clipboard()
					self.editmgr.setclip('multinode', nodes)
		else:
			node = self.selected_widget.get_node()
			self.toplevel.setwaiting()
			if self.fixselection([node]):
				self.editmgr.delnode(node)
				self.fixsyncarcs(self.root, [node]) #  TODO: shouldn't this be done in the editmanager? -mjvdg
				self.editmgr.commit()
				if cut:
					self.__clean_clipboard()
					self.editmgr.setclip('node', node)

	######################################################################
	# Edit a node
	def attrcall(self):
		if self.selected_icon:
			self.selected_icon.attrcall()
		elif self.selected_widget:
			self.selected_widget.attrcall()

	def infocall(self):
		if self.selected_widget: self.selected_widget.infocall()

	def editcall(self):
		if self.selected_widget: self.selected_widget.editcall()

	# win32++
	def _editcall(self):
		if self.selected_widget: self.selected_widget._editcall()
	def _opencall(self):
		if self.selected_widget: self.selected_widget._opencall()

	######################################################################
	# Copy a node.
	def copycall(self):
		windowinterface.setwaiting()
		if len(self.multi_selected_widgets) > 0:
			copyme = []
			for i in self.get_multi_nodes():
				copyme.append(i.DeepCopy())
			self.__clean_clipboard()
			self.editmgr.setclip('multinode', copyme)
		else:
			copyme = self.focusnode.DeepCopy()
			self.__clean_clipboard()
			self.editmgr.setclip('node', copyme)

	def __clean_clipboard(self):
		# Note: after this call you *MUST* set the clipboard to
		# a new value
		t,n = self.editmgr.getclip()
		if t == 'node' and n is not None:
			n.Destroy()
		elif t == 'multinode' and n is not None:
			for i in n:
				i.Destroy()

	######################################################################
	# Copy and paste properties of a node (or multiple nodes)
	def copypropertiescall(self):
		self.focusnode.copypropertiescall()
		
	def pastepropertiescall(self):
		for node in self.get_multi_nodes():
			node.pastepropertiescall()
	
	######################################################################
	# Cut a node.
	def cutcall(self):
		self.deletecall(cut = 1)
		
		
	######################################################################
	# Paste a node. (TODO: multiple selected nodes).
	# see self.paste()
	def pastebeforecall(self):
		if self.selected_widget: self.selected_widget.pastebeforecall()

	def pasteaftercall(self):
		if self.selected_widget: self.selected_widget.pasteaftercall()

	def pasteundercall(self):
		if self.selected_widget: self.selected_widget.pasteundercall()

	######################################################################
	# Drag and drop
	# TODO: find this code.
	

	def cvdrop(self, node, window, event, params):
		# Change to an external node and re-drop it.
		em = self.editmgr
		if not em.transaction():
			return
		em.setnodevalues(node, [])
		em.setnodetype(node, 'ext')
		em.commit()
		# try again, now with an ext node as destination
		self.dropfile(node, window, event, params)

	def dropfile(self, maybenode, window, event, params):
		# Called when a file is dragged-and-dropped onto this HeirachyView
		x, y, filename = params
		# Convert to pixels.
		if not (0 <= x < 1 and 0 <= y < 1):
			windowinterface.beep()
			return
		
		x = x * self.mcanvassize[0]
		y = y * self.mcanvassize[1]

		if maybenode is not None:
			# but how did dropfile() get a node?? Nevertheless..
			obj = maybenode.views['struct_view']
			self.select_widget(obj)
		else:
			obj = self.scene_graph.get_obj_at((x,y))
			#obj = self.whichhit(x, y)
			if not obj:
				windowinterface.beep()
				return
			self.select_widget(obj)
			#self.setfocusobj(obj) # give the focus to the object which was dropped on.
			
		if event == WMEVENTS.DropFile:
			url = MMurl.pathname2url(filename)
		else:
			url = filename

		ctx = obj.node.GetContext() # ctx is the node context (MMNodeContext)
		t = obj.node.GetType()	# t is the type of node (String)
		# Test for invalid targets.
		if t == ('imm','brush','animate','prefetch'):
			self.render()
			windowinterface.showmessage('destination node is an immediate node, change to external?', mtype = 'question', callback = (self.cvdrop, (obj.node, window, event, params)), parent = self.window)
			return
		else:
			interior = (obj.node.GetType() in MMNode.interiortypes)
		# make URL relative to document
		url = ctx.relativeurl(url)

		# TODO: this code really could be less obfuscated.. the widgets should be able to handle their
		# own drag and drop. The MMNode's should be able to create nodes after them if they are sequences
		# and so forth.

		# 'interior' is true if the type of node is in ['seq', 'par', 'excl'...]
		# in other words, interior is false if this is a leaf node (TODO: confirm -mjvdg)
		if interior:
			# if node is expanded, determine where in the node
			# the file is dropped, else create at end
			i = obj.get_nearest_node_index((x,y))
			self.create(0, url, i)
		else:
			# check that URL compatible with node's channel
			if features.lightweight and \
			   obj.node.GetChannelName() not in ctx.compatchannels(url):
					self.render()
					windowinterface.showmessage("file not compatible with channel type `%s'" % obj.node.GetChannelType(), mtype = 'error', parent = self.window)
					return
			em = self.editmgr
			if not em.transaction():
				self.render()
				return
			obj.node.SetAttr('file', url)
			em.commit()

	def dragfile(self, dummy, window, event, params):
		x, y = params
		# Convert to absolute coordinates
		if not (0 <= x < 1 and 0 <= y < 1):
			obj = None
		else:
			x = x * self.mcanvassize[0]
			y = y * self.mcanvassize[1]
			obj = self.whichhit(x, y)

		if not obj:
			windowinterface.setdragcursor('dragnot')
		elif obj.node.GetType() in MMNode.interiortypes:
			windowinterface.setdragcursor('dragadd')
		else:
			windowinterface.setdragcursor('dragset')

	def get_multi_nodes(self):
		# Returns a list of currently selected nodes.
		# Actually, returns a list of the common parents of the nodes.
		if self.selected_widget is None:
			return []
		r = [self.selected_widget.get_node()]
		for i in self.multi_selected_widgets:
			r.append(i.get_node())
		r2 = []
		for i in r:
			for j in r:
				if j is not i and j.IsAncestorOf(i):
					break
			else:
				r2.append(i)
		return r2

	#################################################
	# Edit manager interface (as dependent client)  #
	#################################################

	def transaction(self, type):
		return 1 # It's always OK to start a transaction

	def rollback(self):
		pass
##		self.destroynode = None

	def commit(self, type):
##		if self.destroynode:
##			self.destroynode.Destroy()
##		self.destroynode = None
		self.selected_widget = None
		self.focusnode = None

		#print "TODO: Optimisation in the HierarchyView here: refreshing scene graph on each commit."
		self.refresh_scene_graph()
		
		focustype, focusobject = self.editmgr.getglobalfocus()
		if focustype is None and focusobject is None:
			self.editmgr.setglobalfocus('MMNode', self.root)
		else:
			self.globalfocuschanged(focustype, focusobject, redraw = 0)
		#if type == 'STRUCTURE_CHANGED':	# for example, something was deleted or added
		#	self.need_resize = 1
		#elif type == 'ATTRS_CHANGED': # for example, a new event was added.
		#	self.need_redraw = 1 
		self.draw()

	def kill(self):
		self.destroy()

	#################################################
	# Upcalls from widgets                          #
	#################################################

	# delete all syncarcs in the tree rooted at root that refer to node
	# this works best if node is not part of the tree (so that it is not
	# returned for "prev" and "syncbase" syncarcs).
	def fixsyncarcs(self, root, nodelist):
		em = self.editmgr
		beginlist = []
		changed = 0
		for arc in MMAttrdefs.getattr(root, 'beginlist'):
			if isinstance(arc.srcnode, MMNode.MMNode) and arc.srcnode.GetRoot() in nodelist:
				em.delsyncarc(root, 'beginlist', arc)
		endlist = []
		changed = 0
		for arc in MMAttrdefs.getattr(root, 'endlist'):
			if isinstance(arc.srcnode, MMNode.MMNode) and arc.srcnode.GetRoot() in nodelist:
				em.delsyncarc(root, 'endlist', arc)
		for c in root.GetChildren():
			self.fixsyncarcs(c, nodelist)

	def copyfocus(self):
		# Copies the node with focus to the clipboard.
		node = self.focusnode
		if not node:
			windowinterface.beep()
			return
		t, n = self.editmgr.getclip()
		if t == 'node' and n is not None:
			n.Destroy()
		self.editmgr.setclip('node', node.DeepCopy())
		self.aftersetfocus()

		
	def create(self, where, url = None, index = -1, chtype = None, ntype = None):
		# Create a new node in the Structure view.
		# (assuming..) 'where' is -1:before, 0:here, 1:after. -mjvdg

		start_transaction = 1
		lightweight = features.lightweight
		node = self.focusnode
		if node is None:
			self.opt_render()
			windowinterface.showmessage(
				'There is no selection to insert into',
				mtype = 'error', parent = self.window)
			return
			
		parent = node.GetParent()
		# pnode -- prospective parent of new node
		if where:
			pnode = parent
		else:
			pnode = node
		if parent is None and where <> 0:
			self.opt_render()
			windowinterface.showmessage(
				"Can't insert before/after the root",
				mtype = 'error', parent = self.window)
			return

		if chtype=='animate':
			animlist = ['animate','set','animateMotion', 'animateColor',]
			i = windowinterface.multchoice('Choose animation element', animlist, 0, parent = self.window)
			if i < 0: return # cancel creation
			newnode = self.root.context.newanimatenode(animlist[i])
			newnode.targetnode = node
			if self.insertnode(newnode, where, index):
				if not lightweight:
					AttrEdit.showattreditor(self.toplevel, newnode)
			return 

		type = node.GetType()
		if ntype is not None:
			type = ntype
		elif url is None and chtype is None:
			type = node.GetType()
			if where == 0:
				children = node.GetChildren()
				if children:
					type = children[0].GetType()
		else:
			type = 'ext'

		dftchannel = None
		self.toplevel.setwaiting()
		if where <> 0:
			layout = MMAttrdefs.getattr(parent, 'layout')
		else:
			layout = MMAttrdefs.getattr(node, 'layout')
		node = node.GetContext().newnode(type) # Create a new node

		if url is not None:
			node.SetAttr('file', url)
			# figure out a reasonable default name for the new node
			# the name is the basename of the URL
			# figure out file name part
			path = urlparse.urlparse(url)[2]
			if path:
				import posixpath
				# get last bit (after last slash)
				base = posixpath.split(path)[1]
				if base:
					# remove extensions
					base = posixpath.splitext(base)[0]
					if base:
						# convert %-escapes
						base = MMurl.unquote(base)
						# and assign
						node.SetAttr('name', base)
		if dftchannel:
			node.SetAttr('channel', dftchannel)
		if layout == 'undefined' and \
		   self.toplevel.layoutview is not None and \
		   self.toplevel.layoutview.curlayout is not None:
			node.SetAttr('layout', self.toplevel.layoutview.curlayout)
		if self.insertnode(node, where, index, start_transaction = start_transaction, end_transaction = 0):
##			prearmtime = node.compute_download_time()
##			if prearmtime:
##				arc = MMNode.MMSyncArc(node, 'begin', srcnode='syncbase', delay=prearmtime)
##				self.editmgr.addsyncarc(node, 'beginlist', arc)
			self.editmgr.commit()
			if not lightweight:
				AttrEdit.showattreditor(self.toplevel, node, 'channel')

	def insertparent(self, type):
		node = self.focusnode
		if node is None:
			windowinterface.showmessage(
				'There is no selection to insert at',
				mtype = 'error', parent = self.window)
			return
		parent = node.GetParent()
		if parent is None:
			windowinterface.showmessage(
				"Can't insert above the root",
				mtype = 'error', parent = self.window)
			return
		em = self.editmgr
		if not em.transaction():
			return
		self.toplevel.setwaiting()
		siblings = parent.GetChildren()
		i = siblings.index(node)
		em.delnode(node)
		newnode = node.GetContext().newnode(type)
		em.addnode(parent, i, newnode)
		em.addnode(newnode, 0, node)
		self.prevfocusnode = self.focusnode
		self.focusnode = newnode
		expandnode(newnode)
		self.aftersetfocus()
		em.commit()

	def paste(self, where):
		type, node = self.editmgr.getclip()
		if node is None:
			windowinterface.showmessage(
			    'The clipboard does not contain a node to paste',
			    mtype = 'error', parent = self.window)
			return
		if self.focusnode is None:
			windowinterface.showmessage(
				'There is no selection to paste into',
			 	mtype = 'error', parent = self.window)
			return
		self.toplevel.setwaiting()

		if type == 'node':
			if node.context is not self.root.context:
				node = node.CopyIntoContext(self.root.context)
			else:
				self.editmgr.setclip(type, node.DeepCopy())
			self.insertnode(node, where)
		elif type == 'multinode':
			if not self.editmgr.transaction():
				return
			for i in node:	# I can't use insertnode because I need to access the editmanager.
				n = i.DeepCopy()
				if n.context is not self.root.context:
					n = n.CopyIntoContext(self.root.context)
				self.editmgr.addnode(self.focusnode, -1, n)
			self.editmgr.commit()

	def insertnode(self, node, where, index = -1, start_transaction = 1, end_transaction = 1):
		# 'where' is coded as follows: -1: before 0: under 1: after
		assert where in [-1,0,1] # asserts by MJVDG.. delete them if they
		assert node is not None # catch too many bugs :-).
		assert isinstance(node, MMNode.MMNode)

		if where <> 0:
			# Get the parent
			parent = self.focusnode.GetParent()
			if parent is None:
				windowinterface.showmessage(
					"Can't insert before/after the root",
					mtype = 'error', parent = self.window)
				node.Destroy()
				return 0
		elif where == 0 and node.GetChannelType()!='animate':
			# Special condition for animation
			ntype = self.focusnode.GetType()
			if ntype not in MMNode.interiortypes and \
			   (ntype != 'ext' or
			    node.GetChannelType() != 'animate'): 
				windowinterface.showmessage('Selection is a leaf node!',
							    mtype = 'error', parent = self.window)
				node.Destroy()
				return 0
		em = self.editmgr
		if start_transaction and not em.transaction():
			node.Destroy()
			return 0

		if where == 0:		# insert under (within? -mjvdg)
			# Add (using editmgr) a child to the node with focus
			# Index is the index in the list of children
			# Node is the new node
			em.addnode(self.focusnode, index, node)
		else:
			children = parent.GetChildren()
			i = children.index(self.focusnode)
			if where > 0:	# Insert after
				i = i+1
				em.addnode(parent, i, node)
				# This code is actually unreachable - I suspect this function is
				# only ever called when the node being added has no URL. -mjvdg
				
			else:		# Insert before
				em.addnode(parent, i, node)


		self.prevfocusnode = self.focusnode
		self.focusnode = node
		self.aftersetfocus()
		if end_transaction:
			em.commit()
		return 1

	# Copy node at position src to position dst
	def copynode(self, dst, src):
		self.toplevel.setwaiting()
		xd, yd = dst
		xs, ys = src
		# Problem: dstobj will be an internal node.
		dstobj = self.whichhit(xd, yd)
		srcobj = self.whichhit(xs, ys)

		srcnode = srcobj.node.DeepCopy()
		if srcnode.context is not self.root.context:
			srcnode = srcnode.CopyIntoContext(self.root.context)
		self.focusnode = dstobj.node
		dummy = self.insertnode(srcnode, 0)

	# Move node at position src to position dst
	def movenode(self, dst, src):
		xd, yd = dst
		xs, ys = src
		srcobj = self.whichhit(xs, ys)
		dstobj = self.whichhit(xd, yd)

		if srcobj is dstobj:
			return

		# We need to keep the nodes, because the objects get purged during each commit.
		srcnode = srcobj.node
		destnode = dstobj.node

		# If srcnode is a parent of destnode, then we have a major case of incest.
		# the node will be removed from it's position and appended to one of it's children.
		# and then, garbage collected.
		if srcnode.IsAncestorOf(destnode):
			windowinterface.showmessage("You can't move a node into one of it's children.", mtype='error', parent = self.window)
			return

		if not srcnode or srcnode is self.root:
			windowinterface.beep()
			return

		if isinstance(dstobj, StructureWidgets.StructureObjWidget): # If it's an internal node.
			nodeindex = dstobj.get_nearest_node_index(dst) # works for seqs and verticals!! :-)
			self.focusnode = destnode
			if nodeindex != -1:
				assert nodeindex < len(destnode.children)
				self.focusnode = destnode.children[nodeindex] # I hope that works!
				if self.focusnode is srcnode: # The same node.
					return
			else:
				if len(destnode.children)>0 and destnode.children[-1] is srcnode:
					# The same node.
					return
		else:
			# can't move to leaf node
			windowinterface.beep()
			return

		em = self.editmgr
		if not em.transaction():
			return
		self.toplevel.setwaiting()
		em.delnode(srcnode)
		em.addnode(destnode, nodeindex, srcnode)
		em.commit()

	#################################################
	# Internal subroutines                          #
	#################################################

	# Clear the list of objects
	def cleanup(self):
		if self.scene_graph is not None:
			self.scene_graph.destroy()
			self.scene_graph = None
		self.selected_widget = None

	# Navigation functions

	def tosibling(self, direction):
		if not self.focusnode:
			windowinterface.beep()
			return
		parent = self.focusnode.GetParent()
		if not parent:
			windowinterface.beep()
			return
		siblings = parent.GetChildren()
		i = siblings.index(self.focusnode) + direction
		if not 0 <= i < len(siblings):
			# XXX Could go to parent instead?
			windowinterface.beep()
			return
		self.select_node(siblings[i])
		self.draw()

	def toparent(self):
		if not self.focusnode:
			windowinterface.beep()
			return
		parent = self.focusnode.GetParent()
		if not parent:
			windowinterface.beep()
			return
		self.select_node(parent)
		self.draw()

	def tochild(self, i):
		node = self.focusnode
		if not node:
			windowinterface.beep()
			return
		ntype = node.GetType()
		if ntype not in MMNode.interiortypes:
			windowinterface.beep()
			return
		expandnode(node)
		children = node.GetChildren()
		if i < 0: i = i + len(children)
		if not 0 <= i < len(children):
			windowinterface.beep()
			return
		self.select_node(children[i])
		self.draw()

	def select_widget(self, widget, external = 0, scroll = 1):
		# Set the focus to a specific widget on the user interface, whether
		# it is a node, icon or anything else which is selected.
		# Make the widget the current selection.
		# If external is enabled, don't call the editmanager.

		if self.selected_widget is widget:
			# don't do anything if the focus is already set to the requested widget.
			# this is important because of the setglobalfocus call below.

			# If we select an icon, then we also select it's widget when we have really selected it's icon.
			if self.selected_icon is None or not isinstance(self.selected_widget, StructureWidgets.MMNodeWidget):
				return

		# First, unselect the old widget.
		if isinstance(self.selected_widget, Widgets.Widget):
			self.selected_widget.unselect()
		if isinstance(self.selected_icon, StructureWidgets.Icon):
			self.selected_icon.unselect()
			self.selected_icon = None

		# Remove these two lines of code at some stage.
		self.prevfocusnode = self.focusnode

		# Now select the widget.
		if widget is None:
			self.focusnode = None
		else:			# All cases where the widget is not None follow here:
			if isinstance(widget, StructureWidgets.MMWidgetDecoration):
				if isinstance(widget, StructureWidgets.Icon) and widget.is_selectable():
					if self.selected_icon is not widget:
						self.selected_icon = widget # keep it so we can unselect it later.
						self.selected_icon.select()
				# Select the underlying mmwidget of the decoration..
				widget = widget.get_mmwidget()
			widget.select()
			self.focusnode = widget.get_node() # works on all widgets.
			if scroll:
				self.window.scrollvisible(widget.get_box(), windowinterface.UNIT_PXL)

		self.old_selected_widget = self.selected_widget
		self.selected_widget = widget
		self.old_multi_selected_widgets = self.multi_selected_widgets
		self.multi_selected_widgets = []

		self.aftersetfocus()
		if not external:
			# avoid recursive setglobalfocus
			if len(self.multi_selected_widgets) > 0:
				a = []
				for i in self.multi_selected_widgets:
					a.append(i.get_node())
				self.editmgr.setglobalfocus("MMNode", a)
			else:
				self.editmgr.setglobalfocus("MMNode", self.selected_widget.get_node())

	def also_select_widget(self, widget):
		# Select another widget without losing the selection (ctrl-click).

		if self.selected_widget is None:
			self.select_widget(widget)
			return
		
		if isinstance(widget, StructureWidgets.MMWidgetDecoration):
			widget = widget.get_mmwidget()
			self.multi_selected_widgets.append(widget)

		if widget is self.selected_widget:
			return
		elif widget in self.multi_selected_widgets:
			# Toggle multi-selective widgets.
			self.multi_selected_widgets.remove(widget)
			self.old_multi_selected_widgets.append(widget)
		elif isinstance(widget, StructureWidgets.MMNodeWidget):
			self.multi_selected_widgets.append(widget)
			widget.select()

		self.aftersetfocus()
		self.need_redraw_selection = 1

	def select_node(self, node, external = 0, scroll = 1):
		# Set the focus to a specfic MMNode (obviously the focus did not come from the UI)
		if not node:
			self.select_widget(None, external, scroll)
		elif node.views.has_key('struct_view'):
			widget = node.views['struct_view']
			self.select_widget(widget, external, scroll)

	def select_arrow(self, arrow):
		caller, colour, src, dest = arrow
		# caller is an MMNodewidget, src and dest are coordinates.
		caller.attrcall(initattr='beginlist')

	# TODO: Jack: I know that this is going to mess the mac stuff up.
	# I'm not quite sure how to do right-clicks on a mac. Sorry. -mjvdg.
	def click(self, x, y):
		# Called only from self.mouse, which is the event handler.
		# mjvdg: This causes a bug. By not returning from this function, the ui thinks that
		# the click has not finished when the dialog box is popped up (attrcall above does this).
		#for i in self.__select_arrow_list:
		#	caller, colour, src, dest = i
		#	if self.window.hitarrow((x,y), src, dest):
		#		self.select_arrow(i)
		clicked_widget = self.scene_graph.get_clicked_obj_at((x,y))
		if clicked_widget:
			clicked_widget.mouse0press((x,y))
			self.select_widget(clicked_widget, scroll=0)
		self.draw()

	def addclick(self, x, y):
		clicked_widget = self.scene_graph.get_clicked_obj_at((x,y))
		clicked_widget.mouse0press((x,y))
		self.also_select_widget(clicked_widget)
		self.draw()

	# Find the smallest object containing (x, y)
	def whichhit(self, x, y):
		# Now a bad hack.
		# Return the scene object which is at position x,y.
		# Used for dragging and dropping objects.
		return self.scene_graph.get_obj_at((x,y))

	# Find the object corresponding to the node
	def whichobj(self, node):
		#print "DEBUG: you shouldn't call this function."
		return node.views['struct_view']

	# Select the given object, deselecting the previous focus
	def setfocusobj(self, obj):
		#print "DEBUG: you shouldn't call this function."
		select_widget(obj)
		return

	##############################################################################
	# Menu handling functions - Callbacks.
	##############################################################################

	def helpcall(self):
		if self.selected_widget: self.selected_widget.helpcall()

	def expandcall(self):
		if self.selected_widget:
			self.toplevel.setwaiting()
			self.selected_widget.expandcall()
			self.draw()

	def expandallcall(self, expand):
		if self.selected_widget:
			self.toplevel.setwaiting()
			self.selected_widget.expandallcall(expand)
			self.draw()

	def thumbnailcall(self):
		self.toplevel.setwaiting()
		self.thumbnails = not self.thumbnails
		self.settoggle(THUMBNAIL, self.thumbnails)
		self.need_redraw = 1
		self.draw()

	def playablecall(self):
		self.toplevel.setwaiting()
		self.showplayability = not self.showplayability
		self.settoggle(PLAYABLE, self.showplayability)
		self.need_redraw = 1
		self.draw()

	def timescalecall(self, which):
		self.toplevel.setwaiting()
		if which == 'global':
			which = 'focus'
			node = self.root
		elif which == 'focus':
			node = self.selected_widget.node
		else:
			node = self.selected_widget.node
		if node.showtime == which:
			node.showtime = 0
		else:
			node.showtime = which
		self.need_resize = 1
		self.draw()

	def bandwidthcall(self):
		self.toplevel.setwaiting()
		bandwidth = settings.get('system_bitrate')
		if bandwidth > 1000000:
			bwname = "%dMbps"%(bandwidth/1000000)
		elif bandwidth % 1000 == 0:
			bwname = "%dkbps"%(bandwidth/1000)
		else:
			bwname = "%dbps"%bandwidth
		msg = 'Computing bandwidth usage at %s...'%bwname
		dialog = windowinterface.BandwidthComputeDialog(msg, parent=self.getparentwindow())
		bandwidth, prerolltime, delaycount, errorseconds, errorcount = \
			BandwidthCompute.compute_bandwidth(self.root)
		dialog.setinfo(prerolltime, errorseconds, delaycount, errorcount)
		dialog.done()
		self.need_redraw = 1
		self.draw()

	def transition_callback(self, which, transition):
		if self.selected_widget: self.selected_widget.transition_callback(which, transition)

	def playcall(self):
		if self.selected_widget: self.selected_widget.playcall()

	def playfromcall(self):
		if self.selected_widget: self.selected_widget.playfromcall()

	def anchorcall(self):
		if self.selected_widget: self.selected_widget.anchorcall()

	def createanchorcall(self):
		if self.selected_widget: self.selected_widget.createanchorcall()

	def hyperlinkcall(self):
		if self.selected_widget: self.selected_widget.hyperlinkcall()

	def rpconvertcall(self):
		if self.selected_widget: self.selected_widget.rpconvertcall()

	def createbeforecall(self, chtype=None):
		if self.selected_widget: self.selected_widget.createbeforecall(chtype)

	def createbeforeintcall(self, ntype):
		if self.selected_widget: self.selected_widget.createbeforeintcall(ntype)

	def createaftercall(self, chtype=None):
		if self.selected_widget: self.selected_widget.createaftercall(chtype)

	def createafterintcall(self, ntype):
		if self.selected_widget: self.selected_widget.createafterintcall(ntype)

	def createundercall(self, chtype=None):
		if self.selected_widget: self.selected_widget.createundercall(chtype)

	def createunderintcall(self, ntype=None):
		if self.selected_widget: self.selected_widget.createunderintcall(ntype)

	def createseqcall(self):
		if self.selected_widget: self.selected_widget.createseqcall()

	def createparcall(self):
		if self.selected_widget: self.selected_widget.createparcall()

	def createexclcall(self):
		if self.selected_widget: self.selected_widget.createexclcall()

	def createaltcall(self):
		if self.selected_widget: self.selected_widget.createaltcall()

	def create_begin_event_source(self):
		if self.selected_widget:
			self.begin_event_source = self.selected_widget.get_node() # which works even if it's an icon.
	def create_begin_event_dest(self):
		if self.selected_widget and self.begin_event_source:
			self.selected_widget.get_node().NewBeginEvent(self.begin_event_source, 'activateEvent')

	def find_event_source(self):
		# This feels like the wrong place for a function like this.
		# Never the less..
		if self.selected_icon and len(self.selected_icon.arrowto) > 0:
			if len(self.selected_icon.arrowto) > 1:
				windowinterface.showmessage("This node has more than one associated event!", mtype='error', parent=self.window)
				return
			else:
				other_icon = self.selected_icon.arrowto[0]
				self.select_widget(other_icon)
				self.draw()

	def merge_parent(self):
		# This merges a child node with it's parent.
		# Possible special cases:
		# - child node event depends on parent
		# - parent node event depends on child
		# - hyperlink from parent to child
		# - hyperlink from child to parent
		# - hyperlink from child or parent to itself.
		# - repeats??
		# - the root node (done)
		# - special types of nodes (comment nodes, priority classes)
		
		# first check if this can happen.
		if not self.selected_widget:
			self.popup_error("No selected node!")
			return
		if not isinstance(self.selected_widget, StructureWidgets.MMNodeWidget):
			self.popup_error("You can only merge nodes!")
			return
		child = self.selected_widget.node
		if not child.parent:
			self.popup_error("The root node has no parent to merge with!")
			return
		parent = child.parent
		# Now, check that this node is an only child.
		if len(parent.children) <> 1:
			self.popup_error("You can only merge a node with it's parents if it has no siblings.")
			return

		em = self.editmgr
		if not em.transaction():
			return -1

		# Events..
		#-------------
		# 1. Search through the whole tree looking for events. Don't forget that I'm also in the tree.
		# 2. Any events pointing to the child should now point to it's parent.
		# This doesn't affect the child or the parent.

		print "TODO: check for events between the child and the parent."
		
		nodes = self.find_events_to_node(child, self.root) # This is a list of nodes containing events caused by this node.
		print "DEBUG: nodes are: ", nodes
		parent_uid = parent.GetUID()
		child_uid = child.GetUID()
		uidremap = {child_uid: parent_uid}
		for n in nodes:		# Find all events and change their destination.
			assert isinstance(n, MMNode.MMNode)
			newbeginlist = []
			print "DEBUG: oldbeginlist for ", n, " is: ", MMAttrdefs.getattr(n, 'beginlist')
			for s in MMAttrdefs.getattr(n, 'beginlist'):
				assert isinstance(s, MMNode.MMSyncArc)
				newsyncarc = s.copy(uidremap)					
				newbeginlist.append(newsyncarc)
			newendlist = []
			for s in MMAttrdefs.getattr(n, 'endlist'):
				assert isinstance(s, MMNode.MMSyncArc)
				newsyncarc = s.copy(uidremap)
				newendlist.append(newsyncarc)
			print "DEBUG: new begin list is: ", newbeginlist
			em.setnodeattr(n, 'beginlist', newbeginlist)
			em.setnodeattr(n, 'endlist', newendlist)

		childattrs = child.attrdict
		myattrs = parent.attrdict
		conflicts = []		# A list of conflicting keys.

		# Work through all the attributes; add them all to the parent.
		# Note that this includes the events ('beginlist', 'endlist') and the anchors.
		# The anchors have no problem; they reference the node in no way.
		for ck, cv in childattrs.items():
			#if myattrs.has_key(ck) and ck not in ['name']:
				#conflicts.append(ck)
			#else:
			em.setnodeattr(parent, ck, cv)
		#print "DEBUG: conflicts are: ", conflicts

		# Hyperlinks..
		#--------------
		links = []
		# Copy the list..
		for l in self.root.context.hyperlinks.links:
			links.append(l)
		
		# Re-align them to the parent node
		for l in links:
			# l is a tuple that points to my anchors.
			((suid, said), (duid, daid), d, t, s, p) = l
			changed = 0
			if suid == child_uid:
				suid = parent_uid
				changed = 1
			if duid == child_uid:
				duid = parent_uid
				changed = 1
			if changed:
				# We need to use a copy of the list; otherwise this won't work here:
				em.dellink(l)
				em.addlink(((suid, said), (duid, daid), d, t, s, p))

		child_type=child.type
		child_children = child.children

		# Lastly, delete the child node.
		em.delnode(child)

		em.setnodetype(parent, child_type) # This cannot be done until the child has been deleted.
		for c in child_children:
			c.Extract()
			em.addnode(parent, -1, c)

		self.need_refresh = 1
		em.commit()		# This does a redraw.
		print "Done.. links are now:", self.root.context.hyperlinks.links


	def find_events_to_node(self, node, current):
		# /Recursively/ find all event pointing to node, starting from current.
		# This returns a list of nodes that contain the events.
		# Jack told me that iteration is a bad thing.
		# This method (appears to) works.
		assert isinstance(node, MMNode.MMNode)
		assert isinstance(current, MMNode.MMNode)
		return_me = []
		beginlist = MMAttrdefs.getattr(current, 'beginlist')
		for s in beginlist:
			assert isinstance(s, MMNode.MMSyncArc)
			if s.srcnode is node:
				return_me.append(current)
				break
		else:
			endlist = MMAttrdefs.getattr(current, 'endlist')
			for s in endlist:
				assert isinstance(s, MMNode.MMSyncArc)
				if s.dstnode is node:
					return_me.append(current)
					break
				
		for c in current.children:
			return_me = return_me + self.find_events_to_node(node, c)
		return return_me
		

	def popup_error(self, message):
		# I should have done this a long time ago.
		windowinterface.showmessage(message, mtype="error", parent=self.window)

def expandnode(node):
	node.collapsed = 0
