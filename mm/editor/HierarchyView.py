__version__ = "$Id$"

# New hierarchy view implementation.

# Beware: this module uses X11-like world coordinates:
# positive Y coordinates point down from the top of the window.
# Also the convention for box coordinates is (left, top, right, bottom)

# XXX delete this:
TODO = """
Move focus back to parent node before deleting anything.
properties doesn't work on a multi-selection..
test drag+drop with multiple nodes.
"""



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
		self.playicons = []

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
		self.need_redraw_selection = 0 # Whether we only need to redraw the selection.

		self.focus_lock = 0	# prevents recursive focus requests.

		self.base_display_list = None # A display list that may be cloned and appended to.
		self.extra_displist = None

		# Selections
		#self.selected_widget = None # Is a MMWidget, which could resemble a node or a widget.
		#self.old_selected_widget = None	# This is the node that used to have the focus but needs redrawing.
		self.selected_icon = None
		self.old_selected_icon = None

		self.multi_selected_widgets = [] # When there are multiple selected widgets.
					# For the meanwhile, you can only multi-select MMWidgets which have nodes.
					# These extra selected widgets are added on top of the currently selected widget.
		self.old_multi_selected_widgets = [] # The old list of widgets that need to all be unselected.
		self.need_redraw_select = 0
		
		self.event_sources = [] # This is the specially selected "I am the node from which a new begin event will be made to"
		self.old_event_sources = []
		self.droppable_widget = None # ahh.. something that sjoerd added. Assume that it's used for the fancy drop-notification.
		self.old_droppable_widget = None

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
			CREATE_EVENT_SOURCE(callback = (self.set_event_source, ())),
			FIND_EVENT_SOURCE(callback = (self.find_event_source, ())),
			DRAG_PAR(),
			DRAG_SEQ(),
			DRAG_SWITCH(),
			DRAG_EXCL(),
			DRAG_PRIO(),
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
		self.convertrpcommands = [
			CONVERTRP(callback = (self.convertrpcall, ())),
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
		self.finisheventcommands = [
			CREATE_BEGIN_EVENT(callback = (self.create_begin_event_dest, ())),
			CREATE_END_EVENT(callback = (self.create_end_event_dest, ())),
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
		if heavy:
			rv.append(NEW_UNDER_MEDIA(callback = (self.createundercall, ('null',))))
		if heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_UNDER_IMAGE(callback = (self.createundercall, ('image',))))
		if  heavy or ctx.compatchannels(chtype='sound'):
			rv.append(NEW_UNDER_SOUND(callback = (self.createundercall, ('sound',))))
		if heavy or ctx.compatchannels(chtype='video'):
			rv.append(NEW_UNDER_VIDEO(callback = (self.createundercall, ('video',))))
		if heavy or ctx.compatchannels(chtype='brush'):
			rv.append(NEW_UNDER_BRUSH(callback = (self.createundercall, ('brush',))))
		if heavy or ctx.compatchannels(chtype='text'):
			rv.append(NEW_UNDER_TEXT(callback = (self.createundercall, ('text',))))
		if heavy or ctx.compatchannels(chtype='html'):
			rv.append(NEW_UNDER_HTML(callback = (self.createundercall, ('html',))))
		if heavy or ctx.compatchannels(chtype='svg'):
			rv.append(NEW_UNDER_SVG(callback = (self.createundercall, ('svg',))))
		rv.append(NEW_UNDER_ANIMATE(callback = (self.createundercall, ('animate',))))
		return rv


	def _getmediacommands(self, ctx):
		# Enable commands to edit the media

		heavy = not features.lightweight

		rv = []
		if heavy:
			rv.append(NEW_BEFORE_MEDIA(callback = (self.createbeforecall, ('null',))))
		if heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_BEFORE_IMAGE(callback = (self.createbeforecall, ('image',))))
		if heavy or ctx.compatchannels(chtype='sound'):
			rv.append(NEW_BEFORE_SOUND(callback = (self.createbeforecall, ('sound',))))
		if heavy or ctx.compatchannels(chtype='video'):
			rv.append(NEW_BEFORE_VIDEO(callback = (self.createbeforecall, ('video',))))
		if heavy or ctx.compatchannels(chtype='brush'):
			rv.append(NEW_BEFORE_BRUSH(callback = (self.createbeforecall, ('brush',))))
		if heavy or ctx.compatchannels(chtype='text'):
			rv.append(NEW_BEFORE_TEXT(callback = (self.createbeforecall, ('text',))))
		if heavy or ctx.compatchannels(chtype='html'):
			rv.append(NEW_BEFORE_HTML(callback = (self.createbeforecall, ('html',))))
		if heavy or ctx.compatchannels(chtype='svg'):
			rv.append(NEW_BEFORE_SVG(callback = (self.createbeforecall, ('svg',))))
		if heavy:
			rv.append(NEW_AFTER_MEDIA(callback = (self.createaftercall, ('null',))))
		if heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_AFTER_IMAGE(callback = (self.createaftercall, ('image',))))
		if heavy or ctx.compatchannels(chtype='sound'):
			rv.append(NEW_AFTER_SOUND(callback = (self.createaftercall, ('sound',))))
		if heavy or ctx.compatchannels(chtype='video'):
			rv.append(NEW_AFTER_VIDEO(callback = (self.createaftercall, ('video',))))
		if heavy or ctx.compatchannels(chtype='brush'):
			rv.append(NEW_AFTER_BRUSH(callback = (self.createaftercall, ('brush',))))
		if heavy or ctx.compatchannels(chtype='text'):
			rv.append(NEW_AFTER_TEXT(callback = (self.createaftercall, ('text',))))
		if heavy or ctx.compatchannels(chtype='html'):
			rv.append(NEW_AFTER_HTML(callback = (self.createaftercall, ('html',))))
		if heavy or ctx.compatchannels(chtype='svg'):
			rv.append(NEW_AFTER_SVG(callback = (self.createaftercall, ('svg',))))
		rv.append(NEW_BEFORE_ANIMATE(callback = (self.createbeforecall, ('animate',))))
		rv.append(NEW_AFTER_ANIMATE(callback = (self.createaftercall, ('animate',))))
		rv.append(MERGE_PARENT(callback=(self.merge_parent, ())))
		return rv

	def _getanimatecommands(self, ctx):
		rv = []
		rv.append(NEW_BEFORE_ANIMATE(callback = (self.createbeforecall, ('animate',))))
		rv.append(NEW_AFTER_ANIMATE(callback = (self.createaftercall, ('animate',))))
		rv.append(NEW_UNDER_ANIMATE(callback = (self.createundercall, ('animate',))))
		return rv

	def __compute_commands(self, commands):
		# Compute the commands for the current selected object.
		# TODO: Make context menu setting within the StructureWidgets menu instead.
		if len(self.multi_selected_widgets) > 1:
			return self.__compute_multi_commands(commands)
		elif len(self.multi_selected_widgets) < 1:
			# No node selected.
			return self.commands # XXX or should I return an empty list??
		
		fnode = self.get_selected_node()
		fntype = fnode.GetType()	

		if fnode.WillPlay():
			commands = commands + self.noslidecommands
		else:
			commands = commands + self.noslidecommands[2:]
		if self.toplevel.links and self.toplevel.links.has_interesting(): # ??!! -mjvdg
			commands = commands + self.finishlinkcommands
		if len(self.event_sources) > 0:
			commands = commands + self.finisheventcommands
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
			if fnode.GetComputedMimeType() == 'image/vnd.rn-realpix':
				commands = commands + self.rpconvertcommands
		if fntype == 'seq':
			for c in fnode.GetChildren():
				ctype = c.GetType()
				if (ctype != 'ext' or c.GetChannelType() != 'image') and \
				   ctype != 'brush':
					break
			else:
				commands = commands + self.convertrpcommands

		# Enable "paste" commands depending on what is in the clipboard.
		t, n = self.editmgr.getclip()
		if t in ('node', 'multinode') and n is not None:
			if fntype in MMNode.interiortypes:
				# can only paste inside interior nodes
				commands = commands + self.pasteinteriorcommands
			if fnode is not self.root:
				# can't paste before/after root node
				commands = commands + self.pastenotatrootcommands
		# commands is not mutable here.
		return commands

	def __compute_multi_commands(self, commands, widgets = None):
		if not widgets:		# saves a few cycles.
			widgets = self.get_selected_widgets()
		if len(self.event_sources) > 0:
			commands = commands + self.finisheventcommands
		if not self.scene_graph in widgets:
			commands = commands + self.notatrootcommands
		return commands
		
	def aftersetfocus(self):
		# Called after the focus has been set to a specific node.
		# This:
		# 1) Determines the commands for the node (requires: node, view?)
		# 2) Determines a pop-up menu for the node (requires: node, view if there is view spec info.)

		widgets = self.get_selected_widgets()

		if len(widgets) < 1:
			return

		commands = self.commands # Use a copy.. the original is a template.

		if len(widgets) == 1:# If there is one selected element:
			widget = widgets[0]
			if isinstance(widget, StructureWidgets.TransitionWidget):
				# O.k, I'm not quite sure what this is meant to do: -mjvdg
				which, transitionnames = self.get_selected_widget().posttransitionmenu()
				self.translist = []
				for trans in transitionnames:
					self.translist.append((trans, (which, trans)))
			popupmenu = widget.get_popupmenu()
			#commands = commands + widget.get_commands() # I would like to do it like this -mjvdg
		else: # There is more than one selected element
			popupmenu = self.multi_popupmenu
			#commands = commands + ??.. how to you treat a multiple selection like a single object?

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
		# XXX print "TODO: make sure the focus is visible."
		# Although I'm not really sure if this is needed, because
		# I can't think of a circumstance where the focus is hidden.
		# Selecting a node from elsewhere??
		#for w in widgets:
		#	if not w.iscollapsed():
		#		w.uncollapse()
##		if node.GetParent():
##			node.GetParent().ExpandParents()


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
		focusobject = self.editmgr.getglobalfocus()
		self.focus_lock = 0
		if not focusobject:
			self.editmgr.setglobalfocus([self.root])
		else:
			self.globalfocuschanged(focusobject)
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

		w = self.get_selected_widget()

		# 1. Do we need a new display list?
		if self.need_redraw or self.base_display_list is None:
			# Make a new display list.
			d = self.window.newdisplaylist(BGCOLOR, windowinterface.UNIT_PXL)
			if len(self.event_sources) > 0:
				# Set the dangling icon
				for b in self.event_sources:
					widget = b.views['struct_view']
					widget.set_dangling_event()
			self.scene_graph.draw(d) # Keep it for later!
			self.need_redraw = 0
			self.droppable_widget = None
			self.old_droppable_widget = None
			self.old_selected_widget = None
			self.old_selected_icon = None
			self.old_multi_selected_widgets = []
			self.old_event_sources = []
			self.playicons = []
		elif w is self.old_selected_widget and \
		     self.selected_icon is self.old_selected_icon and \
		     self.droppable_widget is self.old_droppable_widget and \
		     len(self.old_multi_selected_widgets)==0 and \
		     self.event_sources is self.old_event_sources and \
		     not self.need_redraw_selection:
			# nothing to do
			self.redrawing = 0
			return
		else:
			d = self.base_display_list.clone()
			
		# 2. Undraw stuff.
		if len(self.old_event_sources) > 0:
			for b in self.old_event_sources:
				b.views['struct_view'].draw_unselected(d)
		if len(self.event_sources) > 0:
			for b in self.event_sources:
				b.views['struct_view'].draw_unselected(d)
		for i in self.old_multi_selected_widgets:
			i.draw_unselected(d)
		self.old_multi_selected_widgets = []

		if self.old_droppable_widget is not None:
			if self.old_droppable_widget is w:
				pass
			elif self.old_droppable_widget is self.old_selected_widget:
				pass
			else:
				self.old_droppable_widget.draw_unselected(d)
			self.old_droppable_widget = None
##		if w is not self.old_selected_widget:
##			if self.old_selected_widget is not None:
##				self.old_selected_widget.draw_unselected(d)
##			w.draw_selected(d)
##			self.old_selected_widget = w
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
		for node in self.playicons:
			node.playicon.draw(d)
		self.playicons = []
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

	#################################################
	# Outside interface (inherited from ViewDialog) #
	#################################################

	def globalfocuschanged(self, focusobject, redraw = 1):
		# for now, catch only multinode focus ( a list of selected nodes)
		if self.focus_lock:
			return

		if not focusobject:
			return # shouldn't really happen. Fail here??
		select_us = []
		for nnode in focusobject:
			if nnode.getClassName() == 'MMNode':
				select_us.append(nnode)
		self.select_nodes(select_us, external=1)
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
		self.toplevel.setwaiting()
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
	# Selection management
	#
	# The selection is stored in a list of selected widgets.
	# If the list is empty, there is no selection.
	# When there is one entry, there is one node selected.
	# When there are multiple entries, well, then there is are multiple
	# nodes selected.
	# Also be aware that more selection code exists to show which icon
	# is selected.

	def get_selected_node(self):
		# This returns None if the selection is multiple or non-existant.
		# Call this method to:
		# 1. determine if there is a single selected node (for positional operations e.g. paste)
		# 2. get that node.
		if len(self.multi_selected_widgets) != 1:
			return None
		else:
			widget = self.multi_selected_widgets[0]
			assert isinstance(widget, StructureWidgets.MMNodeWidget)
			node = widget.get_node()
			assert isinstance(node, MMNode.MMNode)
			return node;

	def get_selected_nodes(self):
		allnodes=[]
		rv = []
		for i in self.multi_selected_widgets:
			n = i.get_node()
			assert isinstance(n, MMNode.MMNode)
			allnodes.append(n)
		# If there is a child-parent relationship, return only the parent:
		for i in allnodes:
			for j in allnodes:
				if j is not i and j.IsAncestorOf(i):
					break
			else:
				rv.append(i)
		return rv;

	def get_selected_widgets(self):
		return self.multi_selected_widgets
	
	def get_selected_widget(self):
		if len(self.multi_selected_widgets) == 1:
			return self.multi_selected_widgets[0]	# we don't want to return the first widget.
		else:
			return None

	######################################################################
	# Operations on nodes
	#


	######################################################################
	# Adding a node.
	# This code is near the end of this class under various createbefore.. createafter.. callbacks.
	# At some stage they need to be moved here; there is no need to yet.
	
	######################################################################
	# Delete the selected node.
	def migrate_focus(self, nodes):
		# Fix the structure view selection.  Nodes is a list
		# of nodes that are going to be deleted.  We select
		# the common ancestor of these nodes, and if that is
		# also to be deleted, we select a node near by.
		# Returns true if successful and deletion can proceed.

		# In english: move the focus to a safe place before deleting
		# or copying a selection.
		anc = nodes[0]
		for n in nodes:
			if n is self.root:
				# can't delete root node
				windowinterface.beep()
				return 0 # failed
			anc = n.CommonAncestor(anc)
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

	def deletecall(self):
		# The "delete" event handler
		self.toplevel.setwaiting()
		nodes = self.get_selected_nodes()

		# Preconditions:
		if len(nodes) < 1:
			return 0
		if self.root in nodes:
			# In theory, if the root node is in the selection then it would be the only node.
			assert len(nodes) == 0
			return 0

		if not self.migrate_focus(nodes):	# migrate the focus to a safe place.
			return 0

		if not self.editmgr.transaction():
			return 0

		for node in nodes:
			self.editmgr.delnode(node)
			self.fixsyncarcs(self.root, nodes)

		self.editmgr.commit()


	######################################################################
	# Edit a node
	def attrcall(self):
		if self.selected_icon:
			self.selected_icon.attrcall()
		elif self.get_selected_widget():
			self.get_selected_widget().attrcall()

	def infocall(self):
		if self.get_selected_widget(): self.get_selected_widget().infocall()

	def editcall(self):
		if self.get_selected_widget(): self.get_selected_widget().editcall()

	# win32++
	def _editcall(self):
		if self.get_selected_widget(): self.get_selected_widget()._editcall()
	def _opencall(self):
		if self.get_selected_widget(): self.get_selected_widget()._opencall()

	######################################################################
	# Copy a node.
	def copycall(self):
		# The event handler for copying nodes.
		windowinterface.setwaiting()
		nodes = self.get_selected_nodes()

		if len(nodes) < 1:
			windowinterface.beep()
			return 0
		# it is permissable to copy to the root node, so that does not need to be checked.

		copyme = []
		for i in self.get_selected_nodes():
			copyme.append(i.DeepCopy())
		# XXX so where is this method?
		# self.__clean_clipboard()
		self.editmgr.setclip('multinode', copyme, owned=1)

		self.aftersetfocus()

	######################################################################
	# Copy and paste properties of a node (or multiple nodes)
	def copypropertiescall(self):
		if not hasattr(windowinterface, 'mmultchoice'):
			windowinterface.beep()
			return
		node = self.get_selected_node()
		context = node.context
		attrlist = node.getattrnames()
		defattrlist = attrlist[:]
		# Remove ones we don't normally copy
		if 'name' in defattrlist:
			defattrlist.remove('name')
		if 'file' in defattrlist:
			defattrlist.remove('file')
		copylist = windowinterface.mmultchoice('Select properties to copy', attrlist, defattrlist, parent=self.getparentwindow())
		if not copylist: return
		newnode = context.newattrcontainer()
		dict = self._copyattrdict(node, newnode, copylist)
		# XXXX Clear clip
		context.editmgr.setclip('properties', newnode, owned=1)

	def pastepropertiescall(self):
		nodes = self.get_selected_nodes()
		assert(nodes)
		em = self.root.context.editmgr
		tp, clipnode = em.getclip()
		if tp != 'properties':
			windowinterface.beep()
			return
		assert isinstance(clipnode, MMNode.MMAttrContainer)
		if not em.transaction():
			return
		for node in nodes:
			allowedlist = node.getallattrnames()
			wanted = []
			for attrname in allowedlist:
				if clipnode.attrdict.has_key(attrname):
					wanted.append(attrname)
			prop = self._copyattrdict(clipnode, node, wanted, editmgr=em)
		em.commit()
		
	######################################################################
	# Cut a node.
	def cutcall(self):
		#  UNTESTED XXX
		# The "cut" event handler.
		self.toplevel.setwaiting()
		nodes = self.get_selected_nodes()

		if len(nodes) < 1:
			windowinterface.beep()
			return 0
		if self.root in nodes:
			assert len(nodes)==1
			windowinterface.beep()
			return 0

		if not self.migrate_focus(nodes):	# move the focus before we delete it.
			return 0

		if not self.editmgr.transaction():
			return 0

		for n in nodes:
			self.editmgr.delnode(n)
		self.fixsyncarcs(self.root, nodes)
		if len(nodes) == 0:
			self.editmgr.setclip('', None)
		elif len(nodes) == 1:
			self.editmgr.setclip('node', nodes[0])
		else:
			self.editmgr.setclip('multinode', nodes)
		self.editmgr.commit()
	
		
	######################################################################
	# Paste a node. (TODO: multiple selected nodes).
	# see self.paste()
	def pastebeforecall(self):
		if self.get_selected_node(): self.paste(-1)

	def pasteaftercall(self):
		if self.get_selected_node(): self.paste(1)

	def pasteundercall(self):
		if self.get_selected_node(): self.paste(0)


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
			self.draw()
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
				self.draw()
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
			self.draw()
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
				self.draw()
				windowinterface.showmessage("file not compatible with channel type `%s'" % obj.node.GetChannelType(), mtype = 'error', parent = self.window)
				return
			em = self.editmgr
			if not em.transaction():
				self.draw()
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

	#################################################
	# Edit manager interface (as dependent client)  #
	#################################################

	def transaction(self, type):
		return 1 # It's always OK to start a transaction

	def rollback(self):
		pass

	def commit(self, type):
		self.refresh_scene_graph()
		
		focusobject = self.editmgr.getglobalfocus()
		if not focusobject:
			# Shouldn't the editmgr do this?
			self.editmgr.setglobalfocus([self.root])
		else:
			self.globalfocuschanged(focusobject, redraw = 0)
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

	def create(self, where, url = None, index = -1, chtype = None, ntype = None):
		# Create a new node in the Structure view.
		# (assuming..) 'where' is -1:before, 0:here, 1:after. -mjvdg

		start_transaction = 1
		lightweight = features.lightweight
		node = self.get_selected_node()
		if node is None:
			self.draw()
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
			self.draw()
			windowinterface.showmessage(
				"Can't insert before/after the root",
				mtype = 'error', parent = self.window)
			return

		if chtype=='animate':
			newnode = self.root.context.newanimatenode('animate')
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
		elif chtype == 'brush':
			type = 'brush'
		elif chtype == 'text':
			type = 'imm'
		else:
			type = 'ext'
					
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

		dftchannel = None
		# try to find out the default channel following two rules (evaluated in the right order):
		# 1) according to the GRiNS project_default_region_xxx attributes
		# 2) if at this stage, no default channel found, take the first media found which has a region from the parent nodes
		computedType = node.GetChannelType()

		# stage 1:
		# find the project_default_region_xxx attribute to look at according to the channel type
		attributeName = None
		if computedType in ('video', 'RealPix'):
			attributeName = 'project_default_region_video'
		elif computedType in ('text', 'RealText'):
			attributeName = 'project_default_region_text'
		elif computedType == 'sound':
			attributeName = 'project_default_region_sound'
		elif computedType in ('image','svg','html','brush'):
			attributeName = 'project_default_region_image'
			
		# the default channel is stored in the container nodes
		if attributeName and pnode:
			dftchannel = pnode.GetInherAttrDef(attributeName, None)

		# stage 2:
		# look at the region defined for the sibling nodes
		if not dftchannel:
			dftchannel = self.__searchRegion1(pnode, node)
				
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
				if not dftchannel:
					AttrEdit.showattreditor(self.toplevel, node, 'channel')

	# search a default region in looking at the children of the parent,
	# and recursivly until the root element
	def __searchRegion1(self, pnode, childToExclude):
		if pnode == None:
			# no parent
			return None
		# look at in children
		dftchannel = self.__searchRegion2(pnode, childToExclude)
		if dftchannel != None:
			# region found. return this one
			return dftchannel

		# no region in any child found, look at into the parent
		return self.__searchRegion1(pnode.GetParent(), pnode)

	# search a default region in looking the children,
	# and recursively until the leaf elements
	def __searchRegion2(self, pnode, childToExclude=None):
		children = pnode.GetChildren()
		if children != None:
			for child in children:
				if child is not childToExclude:
					type = child.GetType()
					import MMTypes
					if type in MMTypes.mediatypes:
						# media node
						dftchannel = child.GetChannelName()
						if dftchannel != 'undefined' and child.GetChannel() != None:
							# the region exist, return this one
							return dftchannel
					else:
						# container node, recursive search
						dftchannel = self.__searchRegion2(child)
						if dftchannel != None:
							return dftchannel
		# no valid region found
		return None
	
	def insertparent(self, type):
		# Inserts a parent node before this one.
		# XXX TODO: rewrite me.
		if not self.get_selected_widget():
			windowinterface.showmessage(
				'There is no selection to insert at',
				mtype = 'error', parent = self.window)
			return None
		node = self.get_selected_widget().get_node()
		parent = node.GetParent()
		if parent is None:
			windowinterface.showmessage(
				"Can't insert above the root",
				mtype = 'error', parent = self.window)
			return

		attrlist = node.getattrnames()
		defattrlist = attrlist[:]
		for a in ['name', 'file']:
			if a in defattrlist: defattrlist.remove(a)

		copylist = windowinterface.mmultchoice('Select properties for new parent node', attrlist, defattrlist, parent=self.getparentwindow())
		if not copylist: return

		em = self.editmgr
		if not em.transaction():
			return
		self.toplevel.setwaiting()

		# This is one way of doing this.
##		siblings = parent.GetChildren()
##		i = siblings.index(node)
##		em.delnode(node)
##		newnode = node.GetContext().newnode(type)
##		em.addnode(parent, i, newnode)
##		em.addnode(newnode, 0, node)
##		self._copyattrdict(node, newnode, copylist, editmgr=em)

		# This is another.
		url = MMAttrdefs.getattr(node, 'file')
		name = MMAttrdefs.getattr(node, 'name')
		newtype = node.type
		em.setnodeattr(node, 'file', None)
		em.setnodeattr(node, 'name', None)
		em.setnodetype(node, type)
		newnode = node.GetContext().newnode(newtype)
		children = node.children[:]
		for i in range(0, len(children)):
			em.delnode(children[i])
			em.addnode(newnode, -1, children[i])
		em.addnode(node, 0, newnode)
		em.setnodeattr(newnode, 'file', url)
		em.setnodeattr(newnode, 'name', name)
		
		em.setglobalfocus([newnode])
		expandnode(newnode)

		self.aftersetfocus()
		em.commit()
		if not features.lightweight:
			AttrEdit.showattreditor(self.toplevel, newnode, 'name')

	def paste(self, where):
		# where is -1 (before), 0 (under) or 1 (after)
		
		type, node = self.editmgr.getclip()
		if node is None:
			windowinterface.showmessage(
			    'The clipboard does not contain a node to paste',
			    mtype = 'error', parent = self.window)
			return
		if self.get_selected_node() is None:
			windowinterface.showmessage(
				'There is no selection to paste into',
			 	mtype = 'error', parent = self.window)
			return
		self.toplevel.setwaiting()

		type, node = self.editmgr.getclipcopy()
		if type == 'node':
			# If there is a single node on the clipboard.
			# The hierarchyview always copies and cuts multnodes..
			if node.context is not self.root.context:
				node = node.CopyIntoContext(self.root.context)
			self.insertnode(node, where)
		elif type == 'multinode':
			if not self.editmgr.transaction():
				return
			for n in node:	# I can't use insertnode because I need to access the editmanager.
				if n.context is not self.root.context:
					n = n.CopyIntoContext(self.root.context)
				self.editmgr.addnode(self.get_selected_node(), -1, n)
			self.editmgr.commit()

	def insertnode(self, node, where, index = -1, start_transaction = 1, end_transaction = 1):
		# 'where' is coded as follows: -1: before 0: under 1: after
		assert where in [-1,0,1] # asserts by MJVDG.. delete them if they
		assert node is not None # catch too many bugs :-).
		assert isinstance(node, MMNode.MMNode)

		if where <> 0:
			# Get the parent
			parent = self.get_selected_node().parent
			if parent is None:
				windowinterface.showmessage(
					"Can't insert before/after the root",
					mtype = 'error', parent = self.window)
				node.Destroy()
				return 0
		elif where == 0 and node.GetChannelType()!='animate':
			# Special condition for animate
			ntype = self.get_selected_widget().get_node().GetType()
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
			em.addnode(self.get_selected_node(), index, node)
		else:
			children = parent.GetChildren()
			i = children.index(self.get_selected_node())
			if where > 0:	# Insert after
				i = i+1
				em.addnode(parent, i, node)
				# This code is actually unreachable - I suspect this function is
				# only ever called when the node being added has no URL. -mjvdg
				
			else:		# Insert before
				em.addnode(parent, i, node)

		em.setglobalfocus([node])
		self.aftersetfocus()
		if end_transaction:
			em.commit()
		return 1

	# Copy node at position src to position dst
	def dropnewstructnode(self, type, pos):
		self.toplevel.setwaiting()
		xd, yd = pos
		# Problem: dstobj will be an internal node.
		dstobj = self.whichhit(xd, yd)
		self.select_widget(dstobj)
		if type == DRAG_PAR:
			ntype = 'par'
		elif type == DRAG_SEQ:
			ntype = 'seq'
		elif type == DRAG_SWITCH:
			ntype = 'switch'
		elif type == DRAG_EXCL:
			ntype = 'excl'
		elif type == DRAG_PRIO:
			ntype = 'prio'
		else:
			print 'Unknown dragtool:', type
			return
		dummy = self.create(0, ntype=ntype)

	def dropexistingnode(self, cmd, dstpos, srcnode=None, srcpos=None):
		# cmd can be 'copy' or 'move'. The return value is the
		# same or it can be 'copydone' which means the caller
		# does not have to worry: we've copied its object if needed)
		# (Actually pretty similar to None: nothing happened).
		#
		self.toplevel.setwaiting()
		#
		# Find source, optionally copy it (into context or straight)
		#
		mustdestroy = None
		mustunlinksrc = 0
		if not srcnode:
			# Compat code for x/y based drag-drop.
			sx, sy = srcpos
			srcwidget = self.whichhit(sx, sy)
			srcnode = srcwidget.node
			if not srcnode:
				# shouldn't happen
				print "Drag-drop from nowhere..."
				self.draw()
				return None
			if cmd == 'copy':
				cmd = 'link'
				srcnode = srcnode.DeepCopy()
				mustdestroy = srcnode
			else:
				mustunlinksrc = 1
		if srcnode.context is not self.root.context:
			# Node comes from another document.
			srcnode = srcnode.CopyIntoContext(self.root.context)
			mustdestroy = srcnode
			cmd = 'link'
		#
		# Find destination node and check ancestry makes sense
		#
		dx, dy = dstpos
		dstwidget = self.whichhit(dx, dy)
		if not dstwidget:
			print 'Drag-drop to nowhere...'
			self.draw()
			if mustdestroy:
				mustdestroy.Destroy()
			return None
		dstnode = dstwidget.node
		if cmd == 'move' and srcnode.IsAncestorOf(dstnode):
			windowinterface.showmessage("You cannot move a node to its children")
			if mustdestroy: 
				mustdestroy.Destroy()
			self.draw()
			return None
		#
		# Find destination position
		#
		if isinstance(dstwidget, StructureWidgets.StructureObjWidget): # If it's an internal node.
			nodeindex = dstwidget.get_nearest_node_index((dx, dy)) # works for seqs and verticals!! :-)
		else:
			# can't move to leaf node
			if mustdestroy:
				mustdestroy.Destroy()
			self.draw()
			windowinterface.beep()
			return None
		#
		# Move or copy the node
		#
		em = self.editmgr
		if not em.transaction():
			if mustdestroy:
				mustdestroy.Destroy()
			self.draw()
			return
		self.toplevel.setwaiting()
		if mustunlinksrc:
			em.delnode(srcnode)
		em.addnode(dstnode, nodeindex, srcnode)
		em.commit()
		#
		# Return an indication of what we did
		#
		return cmd

	#################################################
	# Internal subroutines                          #
	#################################################

	# Clear the list of objects
	def cleanup(self):
		if self.scene_graph is not None:
			self.scene_graph.destroy()
			self.scene_graph = None
		self.multi_selected_widgets = []

	# Navigation functions

	# XXX TODO: rewrite these. Audit the code. Oh yes, give the code soul.
	# Now that I think about it, we could add occasional poetry to the code.
	# or even better, write obfuscated ascii-art code.
	# def an_ode_to_code(self, x, y):

	def tosibling(self, direction):
		if not self.get_selected_node():
			windowinterface.beep()
			return
		parent = self.get_selected_node().GetParent()
		if not parent:
			windowinterface.beep()
			return
		siblings = parent.GetChildren()
		i = siblings.index(self.get_selected_node()) + direction
		if not 0 <= i < len(siblings):
			# XXX Could go to parent instead?
			windowinterface.beep()
			return
		self.select_node(siblings[i])
		self.draw()

	def toparent(self):
		if not self.get_selected_node():
			windowinterface.beep()
			return
		parent = self.get_selected_node().GetParent()
		if not parent:
			windowinterface.beep()
			return
		self.select_node(parent)
		self.draw()

	def tochild(self, i):
		node = self.get_selected_node()
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
		# Deselect the old selected widgets.

		if self.focus_lock:
			print "WARNING: recursive focus detected in the HierarchyView. Continuing."
			return 0

		# If the widget is None, well just clear everything.
		if widget is None:
			self.unselect_all()
			return

		# If this is the old selected widget, do nothing.
		if len(self.multi_selected_widgets) == 1 and self.multi_selected_widgets[0] is widget \
		   and (self.selected_icon is None or not isinstance(self.multi_selected_widgets[0], StructureWidgets.MMNodeWidget)):
			# don't do anything if the focus is already set to the requested widget.
			# this is important because of the setglobalfocus call below.

			# If we select an icon, then we also select it's widget when we have really selected it's icon.
			return

		self.unselect_all()

		# Now select the widget.

		# If it's an icon, select it and then continue with it's parent.
		if isinstance(widget, StructureWidgets.MMWidgetDecoration):
			if isinstance(widget, StructureWidgets.Icon) and widget.is_selectable():
				if self.selected_icon is not widget:
					self.selected_icon = widget # keep it so we can unselect it later.
					self.selected_icon.select()
			# Select the underlying mmwidget of the decoration..
			widget = widget.get_mmwidget()

		widget.select()
		if scroll:
			self.window.scrollvisible(widget.get_box(), windowinterface.UNIT_PXL)

		self.multi_selected_widgets = [widget]
		self.aftersetfocus()	# XXX change this.

		if not external:
			# If this method is called, there is only _one_ widget selected.
			self.focus_lock = 1
			self.editmgr.setglobalfocus([self.get_selected_node()])
			self.focus_lock = 0

	def also_select_widget(self, widget, external=0, scroll=1):
		# XXX UNTESTED
		# Select another widget without losing the selection (ctrl-click).

		if self.focus_lock:
			print "WARNING: recursive focus detected in the HierarchyView. Continuing."
			return 0

		if len(self.multi_selected_widgets) == 0:
			self.select_widget(widget)
			return
		
		if isinstance(widget, StructureWidgets.MMWidgetDecoration):
			widget = widget.get_mmwidget()

		if widget in self.get_selected_widgets():
			# Toggle multi-selective widgets.
			self.multi_selected_widgets.remove(widget)
			self.old_multi_selected_widgets.append(widget)
			if not external:
				self.focus_lock = 1
				self.editmgr.delglobalfocus([widget.get_node()])
				self.focus_lock = 0
		elif isinstance(widget, StructureWidgets.MMNodeWidget):
			self.multi_selected_widgets.append(widget)
			widget.select()
			if not external:
				self.focus_lock = 1
				self.editmgr.addglobalfocus([widget.get_node()])
				self.focus_lock = 0

		if scroll:
			self.window.scrollvisible(widget.get_box(), windowinterface.UNIT_PXL)

		self.aftersetfocus()	# XXX
		self.need_redraw_selection = 1

	def unselect_all(self):
		# XXX UNTESTED
		# Clears the current selection completely, widget, icon and all.
		# First, unselect the old widget.
		widgets = self.get_selected_widgets()
		self.old_multi_selected_widgets = widgets

		for w in widgets:
			if isinstance(w, Widgets.Widget):
				w.unselect()
		self.multi_selected_widgets = []
		# and if there is a selected icon..
		if isinstance(self.selected_icon, StructureWidgets.Icon):
			self.selected_icon.unselect()
			self.selected_icon = None
		# This isn't needed: self.need_redraw_selection = 1

	def select_node(self, node, external = 0, scroll = 1):
		# Set the focus to a specfic MMNode (obviously the focus did not come from the UI)
		self.select_nodes([node], external = external, scroll = scroll)

	def select_nodes(self, nodelist, external = 0, scroll = 1):
		# Select a list of nodes.
		# XXX with a bit of thought, this could be optimised by checking what I already have
		# selected. However, that could be a bit difficult.
		if len(nodelist) == 0:
			self.select_widget(None, external, scroll)
		elif nodelist[0].views.has_key('struct_view'):
			currently_selected_nodes = self.get_selected_nodes()
			self.select_widget(nodelist[0].views['struct_view'], external, scroll)
			for node in nodelist[1:]:
				if node.views.has_key('struct_view'):
					self.also_select_widget(node.views['struct_view'], external=external)

	def select_arrow(self, arrow):
		caller, colour, src, dest = arrow
		# caller is an MMNodewidget, src and dest are coordinates.
		caller.attrcall(initattr='beginlist')

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

	##############################################################################
	# Menu handling functions - Callbacks.
	##############################################################################

	def helpcall(self):
		# I'm uncertain whether this gets ever called - mjvdg
		# There is no helpcall in selected_widget
		if self.get_selected_widget(): self.get_selected_widget().helpcall()

	def expandcall(self):
		if self.get_selected_widget():
			self.toplevel.setwaiting()
			self.get_selected_widget().expandcall()
			self.draw()

	def expandallcall(self, expand):
		if self.get_selected_widget():
			self.toplevel.setwaiting()
			self.get_selected_widget().expandallcall(expand)
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
			node = self.get_selected_node()
		else:
			node = self.get_selected_node()
		if node.showtime == which:
			self.clear_showtime(node)
		else:
			node.showtime = which
		self.need_resize = 1
		self.draw()

	def clear_showtime(self, node):
		node.showtime = 0
		for c in node.children:
			self.clear_showtime(c)

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
		if self.get_selected_widget(): self.get_selected_widget().transition_callback(which, transition)

	def playcall(self):
		if self.get_selected_widget(): self.get_selected_widget().playcall()

	def playfromcall(self):
		if self.get_selected_widget(): self.get_selected_widget().playfromcall()

	def anchorcall(self):
		if self.get_selected_widget(): self.get_selected_widget().anchorcall()

	def createanchorcall(self):
		if self.get_selected_widget(): self.get_selected_widget().createanchorcall()

	def hyperlinkcall(self):
		if self.get_selected_widget(): self.get_selected_widget().hyperlinkcall()

	def rpconvertcall(self):
		if self.get_selected_widget():
			self.toplevel.setwaiting()
			self.get_selected_widget().rpconvertcall()

	def convertrpcall(self):
		if self.get_selected_widget():
			self.toplevel.setwaiting()
			self.get_selected_widget().convertrpcall()

	def createbeforecall(self, chtype=None):
		if self.get_selected_widget(): self.get_selected_widget().createbeforecall(chtype)

	def createbeforeintcall(self, ntype):
		if self.get_selected_widget(): self.get_selected_widget().createbeforeintcall(ntype)

	def createaftercall(self, chtype=None):
		if self.get_selected_widget(): self.get_selected_widget().createaftercall(chtype)

	def createafterintcall(self, ntype):
		if self.get_selected_widget(): self.get_selected_widget().createafterintcall(ntype)

	def createundercall(self, chtype=None):
		if self.get_selected_widget(): self.get_selected_widget().createundercall(chtype)

	def createunderintcall(self, ntype=None):
		if self.get_selected_widget(): self.get_selected_widget().createunderintcall(ntype)

	def createseqcall(self):
		if self.get_selected_widget(): #self.get_selected_widget().createseqcall()
			self.insertparent('seq')
			
	def createparcall(self):
		if self.get_selected_widget(): #self.get_selected_widget().createparcall()
			self.insertparent('par')

	def createexclcall(self):
		if self.get_selected_widget(): self.get_selected_widget().createexclcall()

	def createaltcall(self):
		if self.get_selected_widget(): self.get_selected_widget().createaltcall()

	def set_event_source(self):
		if len(self.multi_selected_widgets) > 0:
			self.__clear_event_source()
			for w in self.multi_selected_widgets: # This must be the _actual_ list of widgets.
				self.event_sources.append(w.get_node())
				w.set_dangling_event()
		else:
			windowinterface.beep() # Should not happen
		self.draw()
			
	def __clear_event_source(self):
		# Resets the event source list.
		# called only from set_event_source
		self.old_event_sources = self.event_sources
		for b in self.event_sources:
			widget = b.views['struct_view']
			widget.clear_dangling_event()
		self.event_sources = []
			
	def create_begin_event_dest(self):
		widgets = self.get_selected_widgets()

		if len(widgets)==1 and len(self.event_sources) > 0:
			if not self.editmgr.transaction():
				return 0
			node = widgets[0].get_node()
			for src in self.event_sources:
				# XXX BUG! each NewBeginEvent is another transaction. Idiot.
				node.NewBeginEvent(src, 'activateEvent', editmgr=self.editmgr)
				# I assume a draw is not needed (due to NewBeginEvent)...
			self.editmgr.commit()
			self.event_sources = []
			self.old_event_sources = []
		else:
			windowinterface.beep() # Should not happen

	def create_end_event_dest(self):
		widgets = self.get_selected_widgets()

		if len(widgets)==1 and len(self.event_sources) > 0:
			if not self.editmgr.transaction():
				return 0
			node = widgets[0].get_node()
			for src in self.event_sources:
				# XXX BUG! each NewBeginEvent is another transaction. Idiot.
				node.NewEndEvent(src, 'activateEvent', editmgr=self.editmgr)
				# I assume a draw is not needed (due to NewBeginEvent)...
			self.editmgr.commit()
			self.event_sources = []
			self.old_event_sources = []
		else:
			windowinterface.beep() # Should not happen

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
		if not self.get_selected_widget():
			self.popup_error("No selected node!")
			return
		if not isinstance(self.get_selected_widget(), StructureWidgets.MMNodeWidget):
			self.popup_error("You can only merge nodes!")
			return
		child = self.get_selected_widget().node
		if not child.parent:
			self.popup_error("The root node has no parent to merge with!")
			return
		parent = child.parent
		# Now, check that this node is an only child.
		if len(parent.children) <> 1:
			self.popup_error("You can only merge a node with it's parents if it has no siblings.")
			return
		# also check that the child is not an immediate node
		# After a brief discussion with Sjoerd, this shouldn't be a problem.

		em = self.editmgr
		if not em.transaction():
			return -1


		# Events..
		#-------------
		# 1. Search through the whole tree looking for events. Don't forget that I'm also in the tree.
		# 2. Any events pointing to the child should now point to it's parent.
		# This doesn't affect the child or the parent.
		nodes = self.find_events_to_node(child, self.root) # This is a list of nodes containing events caused by this node.
		parent_uid = parent.GetUID()
		child_uid = child.GetUID()
		uidremap = {child_uid: parent_uid}
		for n in nodes:		# Find all events and change their destination.
			assert isinstance(n, MMNode.MMNode)
			newbeginlist = []
			for s in MMAttrdefs.getattr(n, 'beginlist'):
				# I should be checking for events between the child and the parent here.
				# I think I'll just let the user sort it out -mjvdg.
				assert isinstance(s, MMNode.MMSyncArc)
				newsyncarc = s.copy(uidremap)
				newbeginlist.append(newsyncarc)
			newendlist = []
			for s in MMAttrdefs.getattr(n, 'endlist'):
				assert isinstance(s, MMNode.MMSyncArc)
				newsyncarc = s.copy(uidremap)
				newendlist.append(newsyncarc)
			em.setnodeattr(n, 'beginlist', newbeginlist)
			em.setnodeattr(n, 'endlist', newendlist)

		childattrs = child.attrdict
		myattrs = parent.attrdict
		#conflicts = []		# A list of conflicting keys.

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
		
	def _copyattrdict(self, oldnode, newnode, attrnamelist=None, editmgr=None):
		# Copy (part of) a nodes attrdict to another node
		attrdict = oldnode.attrdict
		uidremap = {oldnode.GetUID() : newnode.GetUID()}
		# None means copy all attributes
		if attrnamelist is None:
			attrnamelist = attrdict.keys()
		for attrname in attrnamelist:
			attrvalue = attrdict[attrname]
			# note to self(mjvdg) - If it fails here, do you have oldnode and newnode the right way around?
			# beginlist and endlist need special handling because the arcs contain
			# backreferences to the node
			if attrname in ('beginlist', 'endlist'):
				new = []
				for arc in attrvalue:
					new.append(arc.copy(uidremap))
				attrvalue = new
			else:
				attrvalue = MMNode._valuedeepcopy(attrvalue)
			# Now either set the value through the edit mgr or manually
			if editmgr:
				editmgr.setnodeattr(newnode, attrname, attrvalue)
			else:
				newnode.attrdict[attrname] = attrvalue

	def popup_error(self, message):
		# I should have done this a long time ago.
		windowinterface.showmessage(message, mtype="error", parent=self.window)

def expandnode(node):
	node.collapsed = 0
