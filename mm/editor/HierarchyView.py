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
import TimeMapper
import Help
import Clipboard
import AttrEdit
import Sizes

import settings

# Color settings
from AppDefaults import *

class HierarchyView(HierarchyViewDialog):

	#################################################
	# Outside interface                             #
	#################################################

	def __init__(self, toplevel):
		self.toplevel = toplevel

		self.window = None
		self.last_geometry = None

		self.root = self.toplevel.root
		self.scene_graph = None

		self.editmgr = self.root.context.editmgr

		self.thumbnails = settings.get('structure_thumbnails')
		self.showplayability = 1
		self.timescale = None
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
		self.sizes = sizes_notime
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')
		
		self.__add_commands()
		HierarchyViewDialog.__init__(self)		

	def __init_state(self):
		# Sets the state of this view - i.e. selected nodes etc.
		# This gets called before the scene is initialised.
		# Drawing optimisations
		self.drawing = 0	# A lock to prevent recursion in the draw() method of self.
		self.redrawing = 0	# A lock to prevent recursion in redraw()
		self.need_resize = 1	# Whether the tree needs to be resized.
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
		self.destroynode = None	# node to be destroyed later

		self.arrow_list = []	# A list of arrows to be drawn after everything else.

	def __add_commands(self):
		# Add the user-interface commands that are used for this window.
		lightweight = features.lightweight
		self.commands = [
			CLOSE_WINDOW(callback = (self.hide, ())),

			COPY(callback = (self.copycall, ())),

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
		if not lightweight:
			self.commands.append(TIMESCALE(callback = (self.timescalecall, ('global',))))
			self.commands.append(LOCALTIMESCALE(callback = (self.timescalecall, ('focus',))))
			self.commands.append(CORRECTLOCALTIMESCALE(callback = (self.timescalecall, ('cfocus',))))
			self.commands.append(PLAYABLE(callback = (self.playablecall, ())))

		self.interiorcommands = self._getmediaundercommands(self.toplevel.root.context) + [
			EXPAND(callback = (self.expandcall, ())),
		]

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
		rv.append(NEW_BEFORE_ANIMATION(callback = (self.createbeforecall, ('animate',))))
		rv.append(NEW_AFTER_ANIMATION(callback = (self.createaftercall, ('animate',))))
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
		t, n = Clipboard.getclip()
		if t == 'node' and n is not None:
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
		fnode = self.selected_widget.get_node()

		if isinstance(self.selected_widget, StructureWidgets.TransitionWidget):
			which, transitionnames = self.selected_widget.posttransitionmenu()
			self.translist = []
			for trans in transitionnames:
				self.translist.append((trans, (which, trans)))

		commands = self.commands # Use a copy.. the original is a template.
		fntype = self.focusnode.GetType()
		
		# Choose the pop-up menu.
		if fntype in MMNode.interiortypes: # for all internal nodes.
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

##		t0, t1, t2, download, begindelay = self.focusnode.GetTimes('bandwidth')
		# XXX Very expensive...
		if self.timescale in ('focus', 'cfocus'):
			self.need_resize = 1
			self.need_redraw = 1
##			self.draw()
		

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
		self.scene_graph.dont_draw_children = 0
		self.draw()

	def refresh_scene_graph(self):
		# Recalculates the node structure from the MMNode structure.
		if self.scene_graph is not None:
			self.scene_graph.destroy()
		self.create_scene_graph()

	######################################################################
		# Redrawing the Structure View.
	######################################################################
	# A small note about redrawing:
	# * Only call at the end of (every) top-level event handlers just before you return to the
	#   event loop.
	# * Optimisations are done using flags - if you want certain optimisations done, set and read
	#   these flags. This is much more flexible and easier than state management.
	# -mjvdg.

		
	def draw(self):
		# Recalculate the size of all boxes and draw on screen.
		if self.drawing == 1:
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

	def resize_scene(self):
		# Set the size of the first widget.
		self.need_resize = 0
		# Easiest to create the timemapper always
		x,y = self.scene_graph.get_minsize()
		self.mcanvassize = x,y

		if x < 1.0 or y < 1.0:
			print "Error: unconverted relative coordinates found. HierarchyView:497"
		if self.timescale:
			if self.timescale == 'global':
				timeroot = self.scene_graph
			elif self.focusnode is not None:
				timeroot = self.focusnode.views['struct_view']
			else:
				timeroot = None
				self.timemapper = None
			# Remove old timing info
			self.scene_graph.removedependencies()
			if timeroot is not None:
				self.timemapper = TimeMapper.TimeMapper(self.timescale=='cfocus')
				# Collect the minimal pixel distance for pairs of time values,
				# and the minimum number of pixels needed to represent single time
				# values
				timeroot.adddependencies()
				timeroot.addcollisions(None, None)
				# Now put in an extra dependency so the node for which we are going to
				# display time has enough room to the left of it to cater for the non-timed
				# nodes to be displayed there
				timeroot_minpos = timeroot.get_minpos()
				t0, t1, t2, dummy, dummy = timeroot.node.GetTimes('bandwidth')
				if t0 == 0:
					self.timemapper.addcollision(0, timeroot_minpos)
				else:
					self.timemapper.adddependency(0, t0, timeroot_minpos)
				print 'Minpos', t0, timeroot_minpos
				# Work out the equations
				self.timemapper.calculate()
				# Calculate how many extra pixels this has cost us
				tr_width = self.timemapper.time2pixel(t2, align='right') - \
						self.timemapper.time2pixel(t0)
				tr_extrawidth = tr_width - timeroot.get_minsize()[0]
				print 'Normal', timeroot.get_minsize()[0], 'Timed', tr_width, "Extra", tr_extrawidth
				if tr_extrawidth > 0:
					x = x + tr_extrawidth
				#x = tr_width #DBG
		else:
			self.timemapper = None

		self.scene_graph.moveto((0,0,x,y))
		self.scene_graph.recalc()
		self.mcanvassize = x,y
		self.window.setcanvassize((self.sizes.SIZEUNIT, x, y)) # Causes a redraw() event.

		self.timemapper = None

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

	def add_arrow(self, color, source, dest):
		# Draw arrows on top of everything else.
		self.arrow_list.append((color,source, dest))

	def draw_arrows(self, displist):
		for i in self.arrow_list:
			color,source,dest = i
			displist.drawarrow(color, source, dest)
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

	def globalfocuschanged(self, focustype, focusobject):
		# for now, catch only MMNode focus
		#print "DEBUG: HierarchyView received globalfocuschanged with ", focustype
		if focustype == 'MMNode':
			if isinstance(focusobject, MMNode.MMNode) and focusobject is not self.focusnode:
				self.select_node(focusobject, 1)
				self.aftersetfocus()
				self.need_resize = 0
				self.need_redraw = 0
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

	def mouse(self, dummy, window, event, params):
		# Hack added by mjvdg: params[3] is the params as given by win32, including shift, ctrl status.
		self.toplevel.setwaiting()
		x, y, dummy, modifier = params

		if x >= 1 or y >= 1:
			windowinterface.beep()
			return
		x = x * self.mcanvassize[0] # This is kind of dumb - it has already been converted from pixels
		y = y * self.mcanvassize[1] #  to floats in the windowinterface.
##		self.mousehitx = x
##		self.mousehity = y
		if modifier == 'add':
			self.addclick(x, y)
		else:
			self.click(x,y)

		self.draw()

	def mouse0release(self, dummy, window, event, params):
		self.toplevel.setwaiting()
		x,y = params[0:2]
		if x >= 1 or y >= 1:
			return
		x = x * self.mcanvassize[0]
		y = y * self.mcanvassize[1]
		obj = self.scene_graph.get_clicked_obj_at((x,y))
		if obj:
##			import time
##			print "DEBUG: releasing mouse.." , time.time()
			obj.mouse0release((x,y))
##			print "DEBUG: drawing...", time.time()
			self.draw()
##			print "Done drawing. ", time.time()

	def cvdrop(self, node, window, event, params):
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
		if x < 1.0 and y < 1.0:
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
			# If the node is in ('par'...) then it is vertical
			horizontal = (t not in ('par', 'switch', 'excl', 'prio'))
			i = -1
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
		if x < 1.0 and y < 1.0:
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
		self.destroynode = None

	def commit(self, type):
		if self.destroynode:
			self.destroynode.Destroy()
		self.destroynode = None
		self.selected_widget = None
		self.selected_widget = None
		self.focusnode = None

		self.refresh_scene_graph()
		self.need_resize = 1
		self.need_redraw = 1
		self.draw()

	def kill(self):
		self.destroy()

	#################################################
	# Upcalls from widgets                          #
	#################################################

	# delete all syncarcs in the tree rooted at root that refer to node
	# this works best if node is not part of the tree (so that it is not
	# returned for "prev" and "syncbase" syncarcs).
	def fixsyncarcs(self, root, node):
		em = self.editmgr
		beginlist = []
		changed = 0
		for arc in MMAttrdefs.getattr(root, 'beginlist'):
			if arc.refnode() is node:
				em.delsyncarc(root, 'beginlist', arc)
		endlist = []
		changed = 0
		for arc in MMAttrdefs.getattr(root, 'endlist'):
			if arc.refnode() is node:
				em.delsyncarc(root, 'endlist', arc)
		for c in root.GetChildren():
			self.fixsyncarcs(c, node)

	def deletefocus(self, cut):
		# Deletes the node with focus.
		node = self.focusnode
		if not node or node is self.root:
			windowinterface.beep()
			return
		em = self.editmgr
		if not em.transaction():
			return
		self.toplevel.setwaiting()
		parent = node.GetParent()
		siblings = parent.GetChildren()
		nf = siblings.index(node)
		if nf < len(siblings)-1:
			self.select_node(siblings[nf+1])
		elif nf > 0:
			self.select_node(siblings[nf-1])
		else:
			self.select_node(parent)
		
		em.delnode(node)
		self.fixsyncarcs(parent.GetRoot(), node)
		
		if cut:
			t, n = Clipboard.getclip()
##			if t == 'node' and node is not None:
##				self.destroynode = n
			Clipboard.setclip('node', node)
##		else:
##			self.destroynode = node
		em.commit()

	def copyfocus(self):
		# Copies the node with focus to the clipboard.
		node = self.focusnode
		if not node:
			windowinterface.beep()
			return
		t, n = Clipboard.getclip()
		if t == 'node' and n is not None:
			n.Destroy()
		Clipboard.setclip('node', node.DeepCopy())
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
					AttrEdit.showattreditor(self.toplevel, newnode, chtype = chtype)
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

		ctx = node.GetContext()
		mimetype = ctx.computeMimeType(type, url)
		if chtype == None:
			chtype = pnode.guessChannelType(type, mimetype)

		dftchannel = None
		if type == 'ext' or type == 'imm':
			# See whether the current node specifies a default channel.
			# XXXX Because this is actually a regionname we have a bit of work
			# to do to find the two possible channel names. This code also needs
			# a bit of cleanup, as the channelname<->regionname mapping may be
			# different.
			dftchannel = MMAttrdefs.getattr(pnode, 'project_default_region')
			if dftchannel == 'undefined':
				dftchannel = None
			dftchtype = MMAttrdefs.getattr(pnode, 'project_default_type')
			if dftchtype != 'undefined':
				if chtype is None:
					chtype = dftchtype
				elif chtype != dftchtype:
					self.opt_render()
					windowinterface.showmessage('Incompatible file', mtype = 'error', parent = self.window)
					return
#			if dftchannel is not None and dftchtype != 'undefined':
#				em = self.editmgr
#				if not em.transaction():
#					return
#				start_transaction = 0
#				chlist = [chname]
#			else:
#				chlist = ctx.compatchannels(url, chtype)
#				if dftchannel:
#					nchlist = []
#					for chname in chlist:
#						if ctx.getchannel(chname).GetLayoutChannel().name == dftchannel:
#							nchlist.append(chname)
#					chlist = nchlist
#			if chlist:
#				if len(chlist) > 1:
#					i = windowinterface.multchoice('Choose a channel for this file', chlist, 0, parent = self.window)
#					if i < 0:
#						self.opt_render()
#						# Cancel
#						return
#					chname = chlist[i]
#				else:
#					chname = chlist[0]
#				chtype = None
#			elif lightweight and \
#			     (url is not None or chtype is not None):
#				self.opt_render()
#				windowinterface.showmessage(
#					'There are no channels for this mediatype in the presentation',
#					mtype = 'error', parent = self.window)
#				return
#		else:
#			chtype = None
		self.toplevel.setwaiting()
		if where <> 0:
			layout = MMAttrdefs.getattr(parent, 'layout')
		else:
			layout = MMAttrdefs.getattr(node, 'layout')
		node = ctx.newnode(type) # Create a new node

		if url is not None:
			node.SetAttr('file', url)
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
				AttrEdit.showattreditor(self.toplevel, node, chtype = chtype)

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
		type, node = Clipboard.getclip()
		if type <> 'node' or node is None:
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
		if node.context is not self.root.context:
			node = node.CopyIntoContext(self.root.context)
		else:
			Clipboard.setclip(type, node.DeepCopy())
		dummy = self.insertnode(node, where)

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
		self.selected_widget = None
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

		if self.selected_widget == widget:
			# don't do anything if the focus is already set to the requested widget.
			# this is important because of the setglobalfocus call below.

			# If we select an icon, then we also select it's widget when we have really selected it's icon.
			if not (self.selected_icon and isinstance(self.selected_widget, StructureWidgets.MMNodeWidget)):
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
			self.editmgr.setglobalfocus("MMNode", self.focusnode)

	def also_select_widget(self, widget):
		# Select another widget without losing the selection (ctrl-click).
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
		self.need_redraw_selection = 1

	def select_node(self, node, external = 0):
		# Set the focus to a specfic MMNode (obviously the focus did not come from the UI)
		if not node:
			self.select_widget(None, external)
		elif node.views.has_key('struct_view'):
			widget = node.views['struct_view']
			self.select_widget(widget, external)

	# TODO: Jack: I know that this is going to mess the mac stuff up.
	# I'm not quite sure how to do right-clicks on a mac. Sorry. -mjvdg.
	def click(self, x, y):
		# Called only from self.mouse, which is the event handler.
		clicked_widget = self.scene_graph.get_clicked_obj_at((x,y))
		clicked_widget.mouse0press((x,y))
		self.select_widget(clicked_widget, scroll=0)
		# The calling method will re-draw the screen.

	def addclick(self, x, y):
		clicked_widget = self.scene_graph.get_clicked_obj_at((x,y))
		clicked_widget.mouse0press((x,y))
		self.also_select_widget(clicked_widget)

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
		if self.selected_widget: self.selected_widget.expandcall()
		self.draw()

	def expandallcall(self, expand):
		if self.selected_widget: self.selected_widget.expandallcall(expand)
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
		if self.timescale == which:
			self.timescale = None
			self.settoggle(TIMESCALE, 0)
			self.settoggle(LOCALTIMESCALE, 0)
			self.settoggle(CORRECTLOCALTIMESCALE, 0)
		elif which == 'global':
			self.timescale = 'global'
			self.settoggle(TIMESCALE, 1)
			self.settoggle(LOCALTIMESCALE, 0)
			self.settoggle(CORRECTLOCALTIMESCALE, 0)
		elif which == 'focus':
			self.timescale = 'focus'
			self.settoggle(TIMESCALE, 0)
			self.settoggle(LOCALTIMESCALE, 1)
			self.settoggle(CORRECTLOCALTIMESCALE, 0)
		else:
			self.timescale = 'cfocus'
			self.settoggle(TIMESCALE, 0)
			self.settoggle(LOCALTIMESCALE, 0)
			self.settoggle(CORRECTLOCALTIMESCALE, 1)
		self.refresh_scene_graph()
		self.need_resize = 1
		self.need_redraw = 1
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

	def transition_callback(self, which, transition):
		if self.selected_widget: self.selected_widget.transition_callback(which, transition)

	def playcall(self):
		if self.selected_widget: self.selected_widget.playcall()

	def playfromcall(self):
		if self.selected_widget: self.selected_widget.playfromcall()

	def attrcall(self):
		if self.selected_widget: self.selected_widget.attrcall()

	def infocall(self):
		if self.selected_widget: self.selected_widget.infocall()

	def editcall(self):
		if self.selected_widget: self.selected_widget.editcall()

	# win32++
	def _editcall(self):
		if self.selected_widget: self.selected_widget._editcall()
	def _opencall(self):
		if self.selected_widget: self.selected_widget._opencall()

	def anchorcall(self):
		if self.selected_widget: self.selected_widget.anchorcall()

	def createanchorcall(self):
		if self.selected_widget: self.selected_widget.createanchorcall()

	def hyperlinkcall(self):
		if self.selected_widget: self.selected_widget.hyperlinkcall()

	def rpconvertcall(self):
		if self.selected_widget: self.selected_widget.rpconvertcall()

	def deletecall(self):
		if self.selected_widget: self.selected_widget.deletecall()

	def cutcall(self):
		if self.selected_widget: self.selected_widget.cutcall()

	def copycall(self):
		if self.selected_widget: self.selected_widget.copycall()

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

	def pastebeforecall(self):
		if self.selected_widget: self.selected_widget.pastebeforecall()

	def pasteaftercall(self):
		if self.selected_widget: self.selected_widget.pasteaftercall()

	def pasteundercall(self):
		if self.selected_widget: self.selected_widget.pasteundercall()

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
def expandnode(node):
	# Bad hack. I shouldn't refer to private attrs of a node.
	node.collapsed = 0
