_version__ = "$Id$"

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
import os
import urlparse, MMurl
from math import ceil
import string
import MMmimetypes
import features
import compatibility
import Widgets
from StructureWidgets import *
import TimeMapper

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
#		self.displist = None
#		self.new_displist = None
		self.last_geometry = None

		self.root = self.toplevel.root # : MMNode - the root of the MMNode heirachy
#		self.objects = []	# A list of objects that are displayed on the screen.
		self.scene_graph = None # The next generation list of objects that are displayed on the screen
					# of type EditWindow.
		self.drawing = 0	# A lock to prevent recursion in the draw() method of self.
		self.redrawing = 0	# A lock to prevent recursion in redraw()
		self.need_resize = 1	# Whether the tree needs to be resized.
		self.dirty = 1		# Whether the scene graph needs redrawing.
		self.selected_widget = None
		self.focusobj = None	# Old Object() code - remove this when no longer used. TODO
		self.focusnode = self.prevfocusnode = self.root	# : MMNode - remove when no longer used.
		self.editmgr = self.root.context.editmgr

		self.destroynode = None	# node to be destroyed later
		self.expand_on_show = 1
		self.thumbnails = 1
		self.showplayability = 1
		self.timescale = 0
		self.usetimestripview = 0
		if features.H_TIMESTRIP in features.feature_set:
			if self._timestripconform():
				self.usetimestripview = 1
			else:
				windowinterface.showmessage("Warning: document structure cannot be displayed as timestrip.  Using structured view.")
		self.pushbackbars = features.H_VBANDWIDTH in features.feature_set 	# display download times as pushback bars on MediaWidgets.
		self.dropbox = features.H_DROPBOX in features.feature_set	# display a drop area at the end of every node.
		self.transboxes = features.H_TRANSITIONS in features.feature_set # display transitions
		self.translist = []	# dynamic transition menu
		self.show_links = 1;	# Show HTML links??? I think.. -mjvdg.
		self.sizes = sizes_notime
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')
		
		self.__add_commands()
		HierarchyViewDialog.__init__(self)		

		self.create_scene_graph() # A hierarchy of displayable objects for the screen.
		if not self.usetimestripview:
			self.scene_graph.collapse_levels(3) # Collapse all nodes less than 3 levels down.

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
			]
		if not lightweight:
			self.commands.append(PUSHFOCUS(callback = (self.focuscall, ())))
			self.commands.append(TIMESCALE(callback = (self.timescalecall, ())))
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
				NEW_CHOICE(callback = (self.createbagcall, ())),
				NEW_ALT(callback = (self.createaltcall, ())),
				DELETE(callback = (self.deletecall, ())),
				CUT(callback = (self.cutcall, ())),
				]			
		self.structure_commands = [
				NEW_BEFORE(callback = (self.createbeforecall, ())),
				NEW_BEFORE_SEQ(callback = (self.createbeforeintcall, ('seq',))),
				NEW_BEFORE_PAR(callback = (self.createbeforeintcall, ('par',))),
				NEW_BEFORE_CHOICE(callback = (self.createbeforeintcall, ('bag',))),
				NEW_BEFORE_ALT(callback = (self.createbeforeintcall, ('alt',))),
				NEW_AFTER(callback = (self.createaftercall, ())),
				NEW_AFTER_SEQ(callback = (self.createafterintcall, ('seq',))),
				NEW_AFTER_PAR(callback = (self.createafterintcall, ('par',))),
				NEW_AFTER_CHOICE(callback = (self.createafterintcall, ('bag',))),
				NEW_AFTER_ALT(callback = (self.createafterintcall, ('alt',))),
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
##				INFO(callback = (self.infocall, ())),
				ANCHORS(callback = (self.anchorcall, ())),
				]

		self.slidecommands = self._getmediacommands(self.toplevel.root.context, slide = 1) + self.notatrootcommands[4:6]

		self.rpcommands = self._getmediaundercommands(self.toplevel.root.context, slide = 1)

		self.finishlinkcommands = [
			FINISH_LINK(callback = (self.hyperlinkcall, ())),
			]
		self.navigatecommands = [
			TOPARENT(callback = (self.toparent, ())),
			TOCHILD(callback = (self.tochild, (0,))),
			NEXTSIBLING(callback = (self.tosibling, (1,))),
			PREVSIBLING(callback = (self.tosibling, (-1,))),
			]
		import Help
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
		
	def _getmediaundercommands(self, ctx, slide = 0):
		#import settings
		heavy = not features.lightweight
		rv = [
			NEW_UNDER(callback = (self.createundercall, ())),
			]
		if not slide:
			rv.append(NEW_UNDER_SEQ(callback = (self.createunderintcall, ('seq',))))
			rv.append(NEW_UNDER_PAR(callback = (self.createunderintcall, ('par',))))
			#rv.append(NEW_UNDER_CHOICE(callback = (self.createunderintcall, ('bag',))))
			rv.append(NEW_UNDER_ALT(callback = (self.createunderintcall, ('alt',))))
			if ctx.attributes.get('project_boston', 0):
				rv.append(NEW_UNDER_EXCL(callback = (self.createunderintcall, ('excl',))))
		if heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_UNDER_IMAGE(callback = (self.createundercall, ('image',))))
		if not slide and (heavy or ctx.compatchannels(chtype='sound')):
			rv.append(NEW_UNDER_SOUND(callback = (self.createundercall, ('sound',))))
		if not slide and (heavy or ctx.compatchannels(chtype='video')):
			rv.append(NEW_UNDER_VIDEO(callback = (self.createundercall, ('video',))))
		if not slide and (heavy or ctx.compatchannels(chtype='text')):
			rv.append(NEW_UNDER_TEXT(callback = (self.createundercall, ('text',))))
		if not slide and (heavy or ctx.compatchannels(chtype='html')):
			rv.append(NEW_UNDER_HTML(callback = (self.createundercall, ('html',))))
		if not slide:
			rv.append(NEW_UNDER_ANIMATION(callback = (self.createundercall, ('animate',))))
		if compatibility.G2 == features.compatibility:
			if not slide and (heavy or ctx.compatchannels(chtype='RealPix')):
				rv.append(NEW_UNDER_SLIDESHOW(callback = (self.createundercall, ('RealPix',))))
		return rv


	def _getmediacommands(self, ctx, slide = 0):
		# Enable commands to edit the media
		# If slide is 0, include commands. Else, not.

		import settings
		heavy = not features.lightweight

		rv = []
# mjvdg 12-oct-2000: moved this to the constructor.
# TODO: delete this code, if it is correct.
# 		if slide:
# 			rv = []
# 		else:
# 			rv = [
# 				NEW_BEFORE(callback = (self.createbeforecall, ())),
# 				NEW_BEFORE_SEQ(callback = (self.createbeforeintcall, ('seq',))),
# 				NEW_BEFORE_PAR(callback = (self.createbeforeintcall, ('par',))),
# 				NEW_BEFORE_CHOICE(callback = (self.createbeforeintcall, ('bag',))),
# 				NEW_BEFORE_ALT(callback = (self.createbeforeintcall, ('alt',))),
# 				NEW_AFTER(callback = (self.createaftercall, ())),
# 				NEW_AFTER_SEQ(callback = (self.createafterintcall, ('seq',))),
# 				NEW_AFTER_PAR(callback = (self.createafterintcall, ('par',))),
# 				NEW_AFTER_CHOICE(callback = (self.createafterintcall, ('bag',))),
# 				NEW_AFTER_ALT(callback = (self.createafterintcall, ('alt',))),
# 				]
# 			if ctx.attributes.get('project_boston', 0):
# 				rv.append(NEW_AFTER_EXCL(callback = (self.createafterintcall, ('excl',))))
# 				rv.append(NEW_BEFORE_EXCL(callback = (self.createbeforeintcall, ('excl',))))
		if slide or heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_BEFORE_IMAGE(callback = (self.createbeforecall, ('image',))))
		if not slide and (heavy or ctx.compatchannels(chtype='sound')):
			rv.append(NEW_BEFORE_SOUND(callback = (self.createbeforecall, ('sound',))))
		if not slide and (heavy or ctx.compatchannels(chtype='video')):
			rv.append(NEW_BEFORE_VIDEO(callback = (self.createbeforecall, ('video',))))
		if not slide and (heavy or ctx.compatchannels(chtype='text')):
			rv.append(NEW_BEFORE_TEXT(callback = (self.createbeforecall, ('text',))))
		if not slide and (heavy or ctx.compatchannels(chtype='html')):
			rv.append(NEW_BEFORE_HTML(callback = (self.createbeforecall, ('html',))))
		if compatibility.G2 == features.compatibility:
			if not slide and (heavy or ctx.compatchannels(chtype='RealPix')):
				rv.append(NEW_BEFORE_SLIDESHOW(callback = (self.createbeforecall, ('RealPix',))))
		if slide or heavy or ctx.compatchannels(chtype='image'):
			rv.append(NEW_AFTER_IMAGE(callback = (self.createaftercall, ('image',))))
		if not slide and (heavy or ctx.compatchannels(chtype='sound')):
			rv.append(NEW_AFTER_SOUND(callback = (self.createaftercall, ('sound',))))
		if not slide and (heavy or ctx.compatchannels(chtype='video')):
			rv.append(NEW_AFTER_VIDEO(callback = (self.createaftercall, ('video',))))
		if not slide and (heavy or ctx.compatchannels(chtype='text')):
			rv.append(NEW_AFTER_TEXT(callback = (self.createaftercall, ('text',))))
		if not slide and (heavy or ctx.compatchannels(chtype='html')):
			rv.append(NEW_AFTER_HTML(callback = (self.createaftercall, ('html',))))
		if compatibility.G2 == features.compatibility:
			if not slide and (heavy or ctx.compatchannels(chtype='RealPix')):
				rv.append(NEW_AFTER_SLIDESHOW(callback = (self.createaftercall, ('RealPix',))))
		if not slide:
			rv.append(NEW_BEFORE_ANIMATION(callback = (self.createbeforecall, ('animate',))))
			rv.append(NEW_AFTER_ANIMATION(callback = (self.createaftercall, ('animate',))))
		return rv

	def _getanimatecommands(self, ctx, slide = 0):
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
		is_realpix = fntype == 'ext' and fnode.GetChannelType() == 'RealPix'

		# Add realpix commands
		if is_realpix:
			commands = commands + self.rpcommands

		# Add Slideshow nodes
		#if fnode.__class__ is SlideMMNode:
		#	commands = commands + self.slidecommands
		#else:			# else add really important commands...
		if 1: # I don't want to break the indentation here -mjvdg.
			commands = commands + self.noslidecommands
			if self.toplevel.links and self.toplevel.links.has_interesting(): # ??!! -mjvdg
				commands = commands + self.finishlinkcommands
			if fntype in MMNode.interiortypes or \
			   (is_realpix and MMAttrdefs.getattr(fnode, 'file')):
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

		# Enable "paste" commands depending on what is in the clipboard.
		import Clipboard
		t, n = Clipboard.getclip()
		if t == 'node' and n is not None:
			# can only paste if there's something to paste
			#if n.__class__ is SlideMMNode:
			#	# Slide can only go in RealPix node
			#	if is_realpix and MMAttrdefs.getattr(fnode, 'file'):
			#		commands = commands + self.pasteinteriorcommands
			#	elif fntype == 'slide':
			#		commands = commands + self.pastenotatrootcommands
			if 0:
				pass;
			else:
				if fntype in MMNode.interiortypes:
					# can only paste inside interior nodes
					commands = commands + self.pasteinteriorcommands
				if fnode is not self.root and fntype != 'slide':
					# can't paste before/after root node
					commands = commands + self.pastenotatrootcommands
		# commands is not mutable here.
		return commands;

	
	def aftersetfocus(self):
		# Called after the focus has been set to a specific node.

		fnode = self.focusnode;

		if isinstance(self.selected_widget, TransitionWidget):
			which, transitionnames = self.selected_widget.posttransitionmenu()
			self.translist = []
			for trans in transitionnames:
				self.translist.append((trans, (which, trans)))

		commands = self.commands # Use a copy.. the original is a template.
		fntype = self.focusnode.GetType();
		is_realpix = fntype == 'ext' and fnode.GetChannelType() == 'RealPix'
		
		# Choose the pop-up menu.
#		if fnode.__class__ is SlideMMNode: # for a realmedia slideshow node.
#			popupmenu = self.slide_popupmenu
#		el
		if fntype in MMNode.interiortypes or is_realpix: # for all internal nodes.
			popupmenu = self.interior_popupmenu
			# if node has children, or if we don't know that the
			# node has children (collapsed RealPix node), enable
			# the TOCHILD command
			if fnode.children or (is_realpix and not hasattr(fnode, 'expanded')):
				commands = commands + self.navigatecommands[1:2]
		elif isinstance(self.selected_widget, TransitionWidget):
			popupmenu = self.transition_popupmenu
			commands = commands + self.transitioncommands
		else:
			popupmenu = self.leaf_popupmenu	# for all leaf nodes.

		commands = self.__compute_commands(commands); # Adds to the commands for the current focus node.		
		self.setcommands(commands)
		
		self.setpopup(popupmenu)
		self.setstate()

		# make sure focus is visible
		if self.focusnode.GetParent():
			self.focusnode.GetParent().ExpandParents()
##		node = fnode.GetParent()
##		while node is not None:
##			if not hasattr(node, 'expanded'):
##				expandnode(node)
##			node = node.GetParent()

	##############################################################################
	#
	# Drawing code
	#
	##############################################################################

	def create_scene_graph(self):
		# Iterate through the MMNode structure (starting from self.root)
		# and create a scene graph from it.
		# As such, any old references into the old scene graph need to be reinitialised.
		self.selected_widget = None
		self.focusobj = None
		self.scene_graph = create_MMNode_widget(self.root, self)
		self.dirty = 1
		self.need_resize = 1
		if self.window and self.focusnode:
			self.select_node(self.focusnode)

	# Callbacks for the Widget classes.
	def get_window_size_abs(self):
		return self.mcanvassize;

	def show(self):
		if self.is_showing():
			HierarchyViewDialog.show(self)
			return
		HierarchyViewDialog.show(self)
		self.aftersetfocus()
		self.window.bgcolor(BGCOLOR)
##		self.objects = []
		# Other administratrivia
		self.editmgr.register(self,1) # 1 means we want to participate in global focus management.
		self.toplevel.checkviews()
		# This is already done in create_scene_graph
#		if self.expand_on_show:
#			# Only do this the first time: open a few nodes
#			self.expand_on_show = 0
#			levels = countlevels(self.root, NODES_WANTED_OPEN)
#			do_expand(self.root, 1, levels)
		#expandnode(self.root)
		
		self.refresh_scene_graph()
		self.draw()

	def refresh_scene_graph(self):
		# Recalculates the node structure from the MMNode structure.
		if self.scene_graph is not None:
			self.scene_graph.destroy();
		self.create_scene_graph();

	def draw(self):
		# Recalculate the size of all boxes and draw on screen.
		if self.drawing == 1:
			return
		self.drawing = 1

		self.resize_scene()	# will cause a redraw() event anyway.
		
		self.drawing = 0

	def resize_scene(self):
		# Set the size of the first widget.
		if self.need_resize:
			self.need_resize = 0
			# Easiest to create the timemapper always
			x,y = self.scene_graph.get_minsize_abs()
			self.mcanvassize = x,y

			if x < 1.0 or y < 1.0:
				print "Error: unconverted relative coordinates found. HierarchyView:497"
			if self.timescale:
				self.timemapper = TimeMapper.TimeMapper()
				self.scene_graph.adddependencies()
				self.scene_graph.addcollisions(None, None)
				self.timemapper.calculate()
				t0, t1, t2, dummy, dummy = self.root.GetTimes('bandwidth')
				maxx = self.timemapper.time2pixel(t1, align='right')
				if maxx > x:
					x = maxx
			else:
				self.timemapper = None

			self.scene_graph.moveto((0,0,x,y))
			self.scene_graph.recalc()
			self.mcanvassize = x,y
			self.window.setcanvassize((self.sizes.SIZEUNIT, x, y)) # Causes a redraw() event.

			self.timemapper = None
		
	def draw_scene(self):
		# Only draw the scene, nothing else.
		if self.redrawing:
			print "Error: recursive redraws."
			return
		self.redrawing = 1
		if self.dirty:
			d = self.window.newdisplaylist(BGCOLOR, windowinterface.UNIT_PXL)
			self.scene_graph.draw(d)
			d.render()
			self.dirty = 0
		self.redrawing = 0

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
			self.scene_graph.destroy();
		self.scene_graph = None;
		self.hide()

	def get_geometry(self):
		if self.window:
			self.last_geometry = self.window.getgeometry()

	def init_display(self):
		#if self.new_displist:
		#	print 'init_display: new_displist already exists'
		#	self.new_displist.close()
		#self.new_displist = self.displist.clone()
		self.draw()
		
	def opt_init_display(self):
		# Only open a new displaylist if none exists at the moment
		# eh? -mjvdg
		#self.draw()
		#if self.new_displist:
		#	return None
		#self.init_display()
		#return self.new_displist
		self.draw()

	def render(self):
		self.draw()
		#self.new_displist.render()
		#self.displist.close()
		#self.displist = self.new_displist
		#self.new_displist = None

	def opt_render(self):
		if self.new_displist:
			self.render()

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
		self.setfocusnode(node)

	def globalfocuschanged(self, focustype, focusobject):
		# for now, catch only MMNode focus
		if focustype == 'MMNode':
			print "DEBUG: globalfocuschanged: ", focustype, focusobject
			# Callback from the editmanager to set the focus to a specific node.
			#print "DEBUG: HierarchyView received globalsetfocus with ", focustype, focusobject
			if isinstance(focusobject, MMNode.MMNode) and focusobject is not self.focusnode:
				self.select_node(focusobject);
				self.aftersetfocus();
				self.need_resize = 1
				self.dirty = 1
				self.draw();
		else:
			print "DEBUG: globalfocuschanged called but not used: ", focustype, focusobject

	#################################################
	# Event handlers                                #
	#################################################
	def redraw(self, *rest):
		# Handles redraw events, for example when the canvas is resized.
		self.draw_scene()

	def mouse(self, dummy, window, event, params):
		self.toplevel.setwaiting()
		x, y = params[0:2]
		if x < 1.0 and y < 1.0:
			x = x * self.mcanvassize[0]
			y = y * self.mcanvassize[1]
		self.mousehitx = x
		self.mousehity = y
		self.select(x, y)

		# The mouse is only ever used for selecting, so this will not change the
		# size of the scene.
		self.draw_scene()

	def mouse0release(self, dummy, window, event, params):
		self.toplevel.setwaiting()
		x,y = params[0:2]
		if x < 1.0 and y < 1.0:
			x = x * self.mcanvassize[0]
			y = y * self.mcanvassize[1]
		obj = self.scene_graph.get_obj_at((x,y))
		if obj:
			obj.mouse0release()
			self.draw()

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
			obj = maybenode.views['struct_view'];
			self.select_widget(obj);
			#self.setfocusnode(maybenode)
			#obj = self.whichobj(maybenode)
		else:
			obj = self.scene_graph.get_obj_at((x,y));
			#obj = self.whichhit(x, y)
			if not obj:
				windowinterface.beep()
				return
			self.select_widget(obj);
			#self.setfocusobj(obj) # give the focus to the object which was dropped on.
			
		if event == WMEVENTS.DropFile:
			url = MMurl.pathname2url(filename)
		else:
			url = filename

		ctx = obj.node.GetContext() # ctx is the node context (MMNodeContext)
		t = obj.node.GetType()	# t is the type of node (String)
		if t == 'imm':
			self.render()
			windowinterface.showmessage('destination node is an immediate node, change to external?', mtype = 'question', callback = (self.cvdrop, (obj.node, window, event, params)), parent = self.window)
			return
		if t == 'ext' and \
		   obj.node.GetChannelType() == 'RealPix':
			mtype = MMmimetypes.guess_type(url)[0]
			interior = (mtype != 'image/vnd.rn-realpix')
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
			horizontal = (t not in ('par', 'alt', 'excl', 'prio'))
			i = -1
			# if node is expanded, determine where in the node
			# the file is dropped, else create at end
			i = obj.get_nearest_node_index((x,y))
			self.create(0, url, i)
		else:
			# check that URL compatible with node's channel
			if t != 'slide' and features.lightweight and \
			   obj.node.GetChannelName() not in ctx.compatchannels(url):
					self.render()
					windowinterface.showmessage("file not compatible with channel type `%s'" % obj.node.GetChannelType(), mtype = 'error', parent = self.window)
					return
			if t == 'slide':
				ftype = MMmimetypes.guess_type(url)[0] or ''
				if ftype[:5] != 'image' or \
				   string.find(ftype, 'real') >= 0:
					self.render()
					windowinterface.showmessage("only images allowed in RealPix node", mtype = 'error', parent = self.window)
					return
			em = self.editmgr
			if not em.transaction():
				self.render()
				return
			obj.node.SetAttr('file', url) # TODO: Don't like this. This should be done in MMNode.
			#if t == 'slide' and \
			#   (MMAttrdefs.getattr(obj.node, 'displayfull') or
			#    MMAttrdefs.getattr(obj.node, 'fullimage')):
			#	import Sizes
			#	url = obj.node.GetContext().findurl(url)
			#	w, h = Sizes.GetSize(url)
			#	if w != 0 and h != 0:
			#		if MMAttrdefs.getattr(obj.node, 'displayfull'):
			#			obj.node.SetAttr('subregionwh',(w,h))
			#		if MMAttrdefs.getattr(obj.node, 'fullimage'):
			#			obj.node.SetAttr('imgcropwh', (w,h))

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
		self.focusobj = None

		self.refresh_scene_graph()
		self.need_resize = 1
		self.dirty = 1
		self.draw()

	def kill(self):
		self.destroy()

	#################################################
	# Upcalls from widgets                          #
	#################################################

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
		
		if cut:
			import Clipboard
			t, n = Clipboard.getclip()
			if t == 'node' and node is not None:
				self.destroynode = n
			Clipboard.setclip('node', node)
		else:
			self.destroynode = node
		em.commit()

	def copyfocus(self):
		# Copies the node with focus to the clipboard.
		node = self.focusnode
		if not node:
			windowinterface.beep()
			return
		import Clipboard
		t, n = Clipboard.getclip()
		if t == 'node' and n is not None:
			n.Destroy()
		Clipboard.setclip('node', node.DeepCopy())
		self.aftersetfocus()

		
	def create(self, where, url = None, index = -1, chtype = None, ntype = None):
		# Create a new node in the Structure view.
		# (assuming..) 'where' is -1:before, 0:here, 1:after. -mjvdg

		start_transaction = 1
		# experimental SMIL Boston layout code
		internalchtype = chtype
		# end experimental
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
					import AttrEdit
					AttrEdit.showattreditor(self.toplevel, newnode, chtype = chtype)
			return 

		ctx = node.GetContext()
		type = node.GetType()
		if ntype is not None:
			type = ntype
		elif (where == 0 and type == 'ext' and
		      node.GetChannelType() == 'RealPix') or \
		      (where != 0 and type == 'slide'):
			type = 'slide'
		elif url is None and chtype is None:
			type = node.GetType()
			if where == 0:
				children = node.GetChildren()
				if children:
					type = children[0].GetType()
		else:
			type = 'ext'

		chname = None
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
			if dftchannel is not None and dftchtype != 'undefined':
				i = 0
				while ctx.channeldict.has_key('%s %d' % (dftchannel, i)):
					i = i + 1
				chname = '%s %d' % (dftchannel, i)
				em = self.editmgr
				if not em.transaction():
					return
				start_transaction = 0
				em.addchannel(chname, len(ctx.channelnames), dftchtype)
				chlist = [chname]
				bch = ctx.getchannel(dftchannel)
				if bch.has_key('base_window'):
					w, h = bch['base_winoff'][2:]
				else:
					w, h = bch['winsize']
				em.setchannelattr(chname, 'units', windowinterface.UNIT_PXL)
				em.setchannelattr(chname, 'base_window', dftchannel)
				em.setchannelattr(chname, 'base_winoff', (0,0,w,h))
			else:
				chlist = ctx.compatchannels(url, chtype)
				if dftchannel:
					nchlist = []
					for chname in chlist:
						if ctx.getchannel(chname).GetLayoutChannel().name == dftchannel:
							nchlist.append(chname)
					chlist = nchlist
			if chlist:
				if len(chlist) > 1:
					i = windowinterface.multchoice('Choose a channel for this file', chlist, 0, parent = self.window)
					if i < 0:
						self.opt_render()
						# Cancel
						return
					chname = chlist[i]
				else:
					chname = chlist[0]
				chtype = None
			elif lightweight and \
			     (url is not None or chtype is not None):
				self.opt_render()
				windowinterface.showmessage(
					'There are no channels for this mediatype in the presentation',
					mtype = 'error', parent = self.window)
				return
		else:
			chtype = None
		self.toplevel.setwaiting()
		if where <> 0:
			layout = MMAttrdefs.getattr(parent, 'layout')
		else:
			layout = MMAttrdefs.getattr(node, 'layout')
		if type == 'slide':
			node = SlideMMNode('slide', ctx, ctx.newuid())
			ctx.knownode(node.GetUID(), node)
			# provide a default for tag attribute
			if url is not None:
				import Sizes
				node.SetAttr('tag', 'fadein')
				if where:
					pnode = self.focusnode.GetParent()
				else:
					pnode = self.focusnode
				furl = ctx.findurl(url)
				w,h = Sizes.GetSize(furl)
				if w != 0 and h != 0:
					node.SetAttr('subregionwh', (w,h))
					node.SetAttr('imgcropwh', (w,h))
				start, minstart = slidestart(pnode, furl, index)
				if minstart > start:
					node.SetAttr('start', minstart - start)
			else:
				node.SetAttr('tag', 'fill')
			# and provide a default caption
			node.SetAttr('caption', '<clear/>')
		else:
			node = ctx.newnode(type) # Create a new node
		# experimental SMIL Boston layout code
		node._internalchtype = internalchtype
		# end experimental			
		if url is not None:
			node.SetAttr('file', url)
		if chname:
			node.SetAttr('channel', chname)
		if type != 'slide' and layout == 'undefined' and \
		   self.toplevel.layoutview is not None and \
		   self.toplevel.layoutview.curlayout is not None:
			node.SetAttr('layout', self.toplevel.layoutview.curlayout)
		if self.insertnode(node, where, index, start_transaction = start_transaction, end_transaction = 0):
			prearmtime = node.compute_download_time()
			if prearmtime:
				arc = MMNode.MMSyncArc(node, 'begin', srcnode='syncbase', delay=prearmtime)
				self.editmgr.setnodeattr(node, 'beginlist', [arc])
			self.editmgr.commit()
			if not lightweight:
				import AttrEdit
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
##		if not features.lightweight:
##			import NodeInfo
##			NodeInfo.shownodeinfo(self.toplevel, newnode)

	def paste(self, where):
		import Clipboard
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
			    self.focusnode.GetChannelType() != 'RealPix' or
			    node.GetChannelType() != 'animate'): # or
			    #node.__class__ is not SlideMMNode):
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
			#expandnode(self.focusnode)
		else:
			children = parent.GetChildren()
			i = children.index(self.focusnode)
			if where > 0:	# Insert after
				i = i+1
				em.addnode(parent, i, node)
				# This code is actually unreachable - I suspect this function is
				# only ever called when the node being added has no URL. -mjvdg
# 				print "DEBUG: coming very close to untested code."
# 				if grins_snap and node.attrdict.has_key("file"): # mjvdg 28-sept-2000
# 					# If this is the final node, insert a blank node after
# 					# (copying this node to preserve all attr's)
# 					print "DEBUG: Maybe add a node after the current?"
# 					if obj.GetNext() == None:
# 						print "DEBUG: entered untested code"
# 						nextnode = node.DeepCopy()
# 						em.setnodeattr(nextnode.node, "file", None)
# 						em.addnode(parent, i+1, nextnode)
				
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
		xd, yd = dst
		xs, ys = src
		# Problem: dstobj will be an internal node.
		dstobj = self.whichhit(xd, yd)
		srcobj = self.whichhit(xs, ys)

		srcnode = srcobj.node.DeepCopy()
		self.toplevel.setwaiting()
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
			return;

		# We need to keep the nodes, because the objects get purged during each commit.
		srcnode = srcobj.node
		destnode = dstobj.node

		# If srcnode is a parent of destnode, then we have a major case of incest.
		# the node will be removed from it's position and appended to one of it's children.
		# and then, garbage collected.
		if srcnode.IsAncestorOf(destnode):
			windowinterface.showmessage("You can't move a node into one of it's children.", mtype='error', parent = self.window);
			return
					  
		if not srcnode or srcnode is self.root:
			windowinterface.beep()
			return

		if isinstance(dstobj, StructureObjWidget): # If it's an internal node.
			nodeindex = dstobj.get_nearest_node_index(dst) # works for seqs and verticals!! :-)
			self.focusnode = destnode
			if nodeindex != -1:
				assert nodeindex < len(destnode.children)
				self.focusnode = destnode.children[nodeindex] # I hope that works!
				if self.focusnode is srcnode: # The same node.
					return;
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
		self.focusobj = None
		self.selected_widget = None
		return
	
##		for obj in self.objects:
##			obj.cleanup()
##		self.objects = []
##		self.focusobj = None

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
		self.setfocusnode(siblings[i])

	def toparent(self):
		if not self.focusnode:
			windowinterface.beep()
			return
		parent = self.focusnode.GetParent()
		if not parent:
			windowinterface.beep()
			return
		self.setfocusnode(parent)

	def tochild(self, i):
		node = self.focusnode
		if not node:
			windowinterface.beep()
			return
		ntype = node.GetType()
		if ntype not in MMNode.interiortypes and \
		   (ntype != 'ext' or node.GetChannelType() != 'RealPix'):
			windowinterface.beep()
			return
		expandnode(node)
		children = node.GetChildren()
		if i < 0: i = i + len(children)
		if not 0 <= i < len(children):
			windowinterface.beep()
			return
		self.setfocusnode(children[i])

	def select_widget(self, widget):
		# Set the focus to a specific widget on the user interface.
		# Make the widget the current selection.
		if isinstance(self.selected_widget, Widgets.Widget):
			self.selected_widget.unselect()
		self.selected_widget = widget
		self.focusobj = widget	# Used for callbacks.
		self.prevfocusnode = self.focusnode
		if widget == None:
			self.focusnode = None
		else: 
			self.focusnode = widget.node
			widget.select()
			self.window.scrollvisible(widget.get_box(), windowinterface.UNIT_PXL)
		self.aftersetfocus()
		self.editmgr.setglobalfocus("MMNode", widget.node); 

	def select_node(self, node):
		# Set the focus to a specfic MMNode (obviously the focus did not come from the UI)
		self.setfocusnode(node);
		
	def setfocusnode(self, node):
		# Try not to call this function
		if not node:
			self.select_widget(None);
		else:
			widget = node.views['struct_view'];
			self.select_widget(widget);
		self.editmgr.setglobalfocus("MMNode", node);

	# Handle a selection click at (x, y)
	def select(self, x, y):
		widget = self.scene_graph.get_obj_at((x,y))
		if widget == None:
			print "No widget under the mouse."
		if widget==None or widget==self.selected_widget:
			return
		else:
			self.select_widget(widget)
			self.aftersetfocus()
			self.dirty = 1

##		obj = self.whichhit(x, y)
##		if not obj:
##			windowinterface.beep()
##			return
##		if (not root_expanded or obj.node is not self.root) and \
##		   hasattr(obj.node, 'abox'):
##			l, t, r, b = obj.node.abox
##			if l <= x <= r and t <= y <= b:
##				self.prevfocusnode = self.focusnode
##				self.focusnode = obj.node
##				obj.expandcall()
##				return
##		if obj.node is not self.focusnode:
##			self.setfocusobj(obj)
##			self.render()
##		if obj.iconbox:
##			l, t, w, h = obj.iconbox
##			if l <= x <= l+w and t <= y <= t+h:
##				if obj.node.infoicon:
##					# If we hit the iconbox and there is something in it
##					# print the message
##					msg = obj.node.errormessage
##					if msg:
##						windowinterface.showmessage('%s'%msg, parent = self.window)
##						return
##				if show_links and obj.getlinkicon():
##					self.toplevel.links.show(node=obj.node)

	# Find the smallest object containing (x, y)
	def whichhit(self, x, y):
		# Now a bad hack.
		# Return the scene object which is at position x,y.
		# Used for dragging and dropping objects.
#		if x < 1.0 or y < 1.0:
#			print "DEBUG: Warning! Either this was a click at the top-right corner or we have unconverted relative coords."
#			import traceback; traceback.print_stack()
		return self.scene_graph.get_obj_at((x,y))

	# Find the object corresponding to the node
	def whichobj(self, node):
		print "DEBUG: you shouldn't call this function."
		return node.views['struct_view']
##		for obj in self.objects:
##			if obj.node is node:
##				return obj
##		return None

	# Select the given object, deselecting the previous focus
	def setfocusobj(self, obj):
		print "DEBUG: you shouldn't call this function."
		select_widget(obj)
		return;

##		assert isinstance(obj, Widgets.Widget)

##		self.init_display()
##		if self.focusobj:
##			self.focusobj.deselect()
##		self.prevfocusnode = self.focusnode
##		if obj:
##			self.focusnode = obj.node
##			self.focusobj = obj
##			self.focusobj.select()
##		else:
##			self.focusnode = None
##			self.focusobj = None
##		self.aftersetfocus()

	# Select the given node as focus
##	def setfocusnode(self, node):
##		if not node:
##			self.select_widget(None);
##		else:
##			widget = node.views['struct_view'];
##			self.select_widget(widget);

##		if not node:
##			self.setfocusobj(None)
##			self.render()
##			return
##		obj = self.whichobj(node)
##		if obj:
##			self.setfocusobj(obj)
##			x1,y1,x2,y2 = obj.box
##			self.window.scrollvisible((x1,y1,x2-x1,y2-y1))
##			self.render()
##			return
##		self.prevfocusnode = self.focusnode
##		self.focusnode = node
##		# Need to expand some nodes
##		node = node.GetParent()
##		while node is not None:
##			expandnode(node)
##			node = node.GetParent()
##		self.recalc()

	# Recursively position the boxes. Minimum sizes are already set, we may only have
	# to extend them.
#	def makeboxes(self, list, node, box):
#		assert 0

##		ntype = node.GetType()
##		left, top, right, bottom = box
##		if self.timescale:
##			cw, ch = self.canvassize # pixels (from self.sizes.SIZEUNITS)
##			w, h, t0 = node.boxsize
##			left = t0 / cw
##			right = left + w / cw
##		if not hasattr(node, 'expanded') or \
##		   not node.GetChildren():
##			if hierarchy_minimum_sizes:
##				if not self.timescale:
##					right = left + self.horsize
##				bottom = top + self.versize
##			list.append((node, LEAFBOX, (left, top, right, bottom)))
##			return left, top, right, bottom
##		listindex = len(list)
##		list.append((node, INNERBOX, box))
##		top = top + self.titleheight # coords are fractions of total window size.
##		left = left + self.horedge
##		bottom = bottom - self.veredge
##		right = (right - self.horedge) 
##		children = node.GetChildren()
##		size = 0
##		horizontal = (ntype not in ('par', 'alt', 'excl', 'prio'))
##		# animate++
##		if ntype in MMNode.leaftypes and node.GetChildren() and \
##		   (ntype != 'ext' or node.GetChannelType() != 'RealPix'):
##			horizontal = 0
##		for child in children:
##			size = size + child.boxsize[not horizontal]
##			if horizontal:
##				size = size + child.boxsize[2]
##		# size is minimum size required for children in mm
### use this to make drop area also proportional to available size
####		if ntype == 'seq' and grins_snap:
####			size = size + self.sizes.DROPAREA
##		if horizontal:
##			gapsize = self.horgap
##			totsize = right - left
##		else:
##			gapsize = self.vergap
##			totsize = bottom - top
### use this to have a fixed size drop area
##		if ntype == 'seq' and grins_snap:
##			totsize = totsize - self.droparea
##		# totsize is total available size for all children with inter-child gap
##		factor = (totsize - (len(children) - 1) * gapsize) / size
##		maxr = 0
##		maxb = 0
##		for child in children:
##			size = child.boxsize[not horizontal]
##			if horizontal:
##				size = size + child.boxsize[2]
##			if horizontal:
##				right = left + size * factor
##			else:
##				bottom = top + size * factor
##			l,t,r,b = self.makeboxes(list, child, (left, top, right, bottom))
##			if horizontal:
##				left = r + gapsize
##				if b > maxb: maxb = b
##			else:
##				top = b + gapsize
##				if r > maxr: maxr = r
##		if ntype == 'seq' and grins_snap:
##			if horizontal:
####				left = left + self.sizes.DROPAREA * factor
##				left = left + self.droparea + gapsize
####			else:		# not used? mjvdg.
####				right = right + self.sizes.DROPAREA * factor
####				right = right + self.droparea + gapsize
##		if horizontal:
##			maxr = left - gapsize + self.horedge
##			#if ntype == 'seq': maxr = maxr + sizes_notime.DROPAREASIZE * factor
##			maxb = maxb + self.veredge
##		else:
##			maxb = top - gapsize + self.veredge
##			maxr = maxr + self.horedge
##		box = box[0], box[1], maxr, maxb
##		list[listindex] = node, INNERBOX, box
##		return box

	# Intermedeate step in the recomputation of boxes. At this point the minimum
	# sizes are already set. We only have to compute gapsizes (based on current w/h),
	# call makeboxes to position the boxes and create the objects.
#	def recalcboxes(self):
#		x,y = self.scene_graph.get_minsize_abs()
#		print "DEBUG: Recalcboxes: recalculating the scene graph."
#		self.scene_graph.recalc()
#		return
		
	# TODO: Remove this code -mjvdg
##		self.focusobj = None
##		prevfocusobj = None
##		rootobj = None
##		rw, rh = self.window.getcanvassize(self.sizes.SIZEUNIT)
##		rw = float(rw)
##		rh = float(rh)
##		self.canvassize = rw, rh
##		self.titleheight = float(self.sizes.TITLESIZE) / rh
##		self.chnameheight = float(self.sizes.CHNAMESIZE) / rh
##		self.horedge = float(self.sizes.HEDGSIZE) / rw
##		self.veredge = float(self.sizes.VEDGSIZE) / rh
##		self.horgap = float(self.sizes.GAPSIZE) / rw
##		self.vergap = float(self.sizes.GAPSIZE) / rh
##		self.horsize = float(self.sizes.MINSIZE + self.sizes.HOREXTRASIZE) / rw
##		self.versize = float(self.sizes.MINSIZE + self.sizes.LABSIZE) / rh
##		self.arrwidth = float(self.sizes.ARRSIZE) / rw
##		self.arrheight = float(self.sizes.ARRSIZE) / rh
##		self.errwidth = float(self.sizes.ERRSIZE) / rw
##		self.errheight = float(self.sizes.ERRSIZE) / rh
##		self.droparea = float(self.sizes.DROPAREA) / rw
##		list = []
##		if self.timescale:
##			timebarheight = float(self.sizes.TIMEBARHEIGHT)/rh
##			self.timescalebox = (0, 0, 1, 0.666*timebarheight)
##			databox = (0, timebarheight, 1, 1)
##		else:
##			self.timescalebox = None
##			databox = (0, 0, 1, 1)
##		self.makeboxes(list, self.root, databox)
##		for item in list:	
##			obj = Object(self, item)
##			self.objects.append(obj)						

##			# Attach nipples to media nodes only
##			if grins_snap and obj.node.GetType() in MMNode.leaftypes:
##				left_nipple = Nipple(self, item)
##				left_nipple.append_to_left()
##				self.objects.append(left_nipple)
##				right_nipple = Nipple(self, item)
##				right_nipple.append_to_right()
##				self.objects.append(right_nipple)

##			if item[0] is self.focusnode:
##				self.focusobj = obj
##			if item[0] is self.prevfocusnode:
##				prevfocusobj = obj
##			if item[0] is self.root:
##				rootobj = obj
##		if self.focusobj is not None:
##			self.focusobj.selected = 1
##		elif prevfocusobj is not None:
##			self.focusnode = self.prevfocusnode
##			self.focusobj = prevfocusobj
##			prevfocusobj.selected = 1
##		else:
##			self.focusnode = self.root
##			self.focusobj = rootobj
##			rootobj.selected = 1
##		self.aftersetfocus()
##		x1,y1,x2,y2 = self.focusobj.box
##		self.window.scrollvisible((x1,y1,x2-x1,y2-y1))

	# First step in box recomputation after an edit (or changing expand/collapse, etc):
	# computes minimum sizes of all nodes, and does either a redraw (if everything still
	# fits in the window) or a setcanvassize (which results in a resize, and hence
	# a redraw)
#	def recalc(self):
#		window = self.window
##		self.cleanup()
##		if root_expanded:
##			expandnode(self.root) # root always expanded
##		if self.timescale:
##			Timing.needtimes(self.root)
##			self.timescalefactor = settings.get('time_scale_factor')
#		width, height, begin = self.sizeboxes(self.root)
#		width = width + begin
##		cwidth, cheight = window.getcanvassize(self.sizes.SIZEUNIT)
##		mwidth = mheight = 0 # until we have a way to get the min. size
##		if not hierarchy_minimum_sizes and \
##		   (width <= cwidth <= width * 1.1 or width < cwidth <= mwidth) and \
##		   (height <= cheight <= height * 1.1 or height < cheight <= mheight):
##			# size change not big enough, just redraw
##			self.redraw()
##		else:
##			# this call causes a ResizeWindow event
#		self.window.setcanvassize((self.sizes.SIZEUNIT, width, height))

	# Draw the window, assuming the object shapes are all right. This is the final
	# step in the redraw code (and the only step needed if we only enable
	# thumbnails, or do a similar action that does not affect box coordinates).
##	def draw(self):
##		print "DEBUG: drawing."
##		displist = self.new_displist
##		dummy = displist.usefont(f_title)

##		#for obj in self.objects:
##		#	obj.draw()
##		#if self.timescale:
##		#	self.drawtimescale()

##		self.scene_graph.draw(displist)

##		self.new_displist = None
##		displist.render()
##		if self.displist:
##			self.displist.close()
##		self.displist = displist

##		self.new_displist = None

##	def drawtimescale(self):
##		displist = self.new_displist
##		t0 = self.root.t0
##		t1 = self.root.t1
##		l, t, r, b = self.timescalebox
##		m = (t+b)/2
##		displist.usefont(f_timescale)
##		linecolor = TEXTCOLOR
##		f_width = displist.strsize('x')[0]
##		# Draw rectangle around boxes
####		hmargin = f_width / 9
####		vmargin = displist.fontheight() / 4
##		displist.drawline(linecolor, [(l, m), (r, m)])
##		# Compute the number of ticks. Don't put them too close
##		# together.
##		dt = t1 - t0
##		tickstep = 1
##		while 1:
##			n = int(ceil(dt/tickstep))
##			if n*f_width < (r-l):
##				break
##			tickstep = tickstep * 10
##		# Compute distance between numeric indicators
##		div = 1
##		i = 0
##		maxlabelsize = len(str(ceil(dt)))
##		while (n/div) * (maxlabelsize+0.5) * f_width >= (r-l):
##			if i%3 == 0:
##				div = div*2
##			elif i%3 == 1:
##				div = div/2*5
##			else:
##				div = div/5*10
##			i = i+1
##		# Draw division boxes and numeric indicators
##		# This gives MemoryError: for i in range(n):
##		# This code should be looked into.
##		i = -1
##		displist.fgcolor(TEXTCOLOR)
##		while i < n:
##			i = i + 1
##			#
##			it0 = t0 + i*tickstep
##			pos = l + (r-l)*float(i)/n
##			if i%div == 0:
##				displist.drawline(linecolor, [(pos, m), (pos, b)])
##			else:
##				displist.drawline(linecolor, [(pos, m), (pos, (m+b)/2)])
##			if i%div <> 0:
##				continue
##			if tickstep < 1:
##				ticklabel = `i*tickstep`
##			else:
##				ts_value = int(i*tickstep)
##				ticklabel = '%3d:%02.2d'%(ts_value/60, ts_value%60)
##			if 0 < i < n-1:
##				width = displist.strsize(ticklabel)[0]
##				displist.centerstring(pos-width/2, t, pos+width/2, m, ticklabel)
##		# And show total duration
##		ticklabel = '%ds '%int(t1)
##		width = displist.strsize(ticklabel)[0]
##		displist.centerstring(r-width, t, r, m, ticklabel)

	##############################################################################
	# Menu handling functions - Callbacks.
	##############################################################################

##	def helpcall(self):
##		if self.focusobj: self.focusobj.helpcall()

	def expandcall(self):
		if self.focusobj: self.focusobj.expandcall()
		self.draw()

	def expandallcall(self, expand):
		if self.focusobj: self.focusobj.expandallcall(expand)
		self.draw()

	def thumbnailcall(self):
		self.toplevel.setwaiting()
		self.thumbnails = not self.thumbnails
		self.settoggle(THUMBNAIL, self.thumbnails)
		#f self.new_displist:
		#	self.new_displist.close()
		#self.new_displist = self.window.newdisplaylist(BGCOLOR)
		print "TODO: enable/disable thumbnails."
		self.draw()

	def playablecall(self):
		self.toplevel.setwaiting()
		self.showplayability = not self.showplayability
		self.settoggle(PLAYABLE, self.showplayability)
		#if self.new_displist:
		#	self.new_displist.close()
		#self.new_displist = self.window.newdisplaylist(BGCOLOR)
		self.draw()

	def timescalecall(self):
		self.toplevel.setwaiting()
		self.timescale = not self.timescale
		self.settoggle(TIMESCALE, self.timescale)
		self.refresh_scene_graph()
		self.need_resize = 1
		self.dirty = 1
		self.draw()
		
	def bandwidthcall(self):
		self.toplevel.setwaiting()
#		import settings # settings has already been imported -mjvdg.
		import BandwidthCompute
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
		if self.focusobj: self.focusobj.transition_callback(which, transition)

	def playcall(self):
		if self.focusobj: self.focusobj.playcall()

	def playfromcall(self):
		if self.focusobj: self.focusobj.playfromcall()

	def attrcall(self):
		if self.focusobj: self.focusobj.attrcall()

	def infocall(self):
		if self.focusobj: self.focusobj.infocall()

	def editcall(self):
		if self.focusobj: self.focusobj.editcall()

	# win32++
	def _editcall(self):
		if self.focusobj: self.focusobj._editcall()
	def _opencall(self):
		if self.focusobj: self.focusobj._opencall()

	def anchorcall(self):
		if self.focusobj: self.focusobj.anchorcall()

	def createanchorcall(self):
		if self.focusobj: self.focusobj.createanchorcall()

	def hyperlinkcall(self):
		if self.focusobj: self.focusobj.hyperlinkcall()

	def focuscall(self):
		if self.focusobj: self.focusobj.focuscall()

	def deletecall(self):
		if self.focusobj: self.focusobj.deletecall()

	def cutcall(self):
		if self.focusobj: self.focusobj.cutcall()

	def copycall(self):
		if self.focusobj: self.focusobj.copycall()

	def createbeforecall(self, chtype=None):
		if self.focusobj: self.focusobj.createbeforecall(chtype)

	def createbeforeintcall(self, ntype):
		if self.focusobj: self.focusobj.createbeforeintcall(ntype)

	def createaftercall(self, chtype=None):
		if self.focusobj: self.focusobj.createaftercall(chtype)

	def createafterintcall(self, ntype):
		if self.focusobj: self.focusobj.createafterintcall(ntype)

	def createundercall(self, chtype=None):
		if self.focusobj: self.focusobj.createundercall(chtype)

	def createunderintcall(self, ntype=None):
		if self.focusobj: self.focusobj.createunderintcall(ntype)

	def createseqcall(self):
		if self.focusobj: self.focusobj.createseqcall()

	def createparcall(self):
		if self.focusobj: self.focusobj.createparcall()

	def createexclcall(self):
		if self.focusobj: self.focusobj.createexclcall()

	def createbagcall(self):
		if self.focusobj: self.focusobj.createbagcall()

	def createaltcall(self):
		if self.focusobj: self.focusobj.createaltcall()

	def pastebeforecall(self):
		if self.focusobj: self.focusobj.pastebeforecall()

	def pasteaftercall(self):
		if self.focusobj: self.focusobj.pasteaftercall()

	def pasteundercall(self):
		if self.focusobj: self.focusobj.pasteundercall()


	# Recursive procedure to calculate geometry of boxes.
#	def sizeboxes(self, node):
		# Helper for first step in size recomputation: compute minimum sizes of
		# all node boxes.
#		assert 0
##		ntype = node.GetType()
##		minsize = self.sizes.MINSIZE
##		if self.timescale:
##			if node.__class__ is SlideMMNode:
##				pnode = node.GetParent()
##				pchildren = pnode.GetChildren()
##				i = pchildren.index(node)
##				dur = (pnode.t1 - pnode.t0) / len(pchildren)
##				t0 = pnode.t0 + i * dur
##				t1 = t0 + dur
##			else:
##				t0 = node.t0
##				t1 = node.t1
##			begin = t0 * self.timescalefactor
##			dur = (t1 - t0) * self.timescalefactor
##			if dur < 0:
##				dur = 0
##			minsize = dur
##		else:
##			begin = 0
##		minwidth = minsize
##		minheight = self.sizes.MINSIZE
##		if self.timescale:
##			pass # Don't mess with the size, it is important
##		elif structure_name_size:
##			name = MMAttrdefs.getattr(node, 'name')
##			if self.sizes.SIZEUNIT == windowinterface.UNIT_MM:
##				namewidth = (name and f_title.strsize(name)[0]) or 0
##			else:
##				namewidth = (name and f_title.strsizePXL(name)[0]) or 0
####			if ntype in MMNode.interiortypes or \
####			   (ntype == 'ext' and node.GetChannelType() == 'RealPix'):
####				namewidth = namewidth + self.sizes.ARRSIZE
##			namewidth = namewidth + self.sizes.ARRSIZE + self.sizes.ERRSIZE # Always
##			minwidth = max(min(self.sizes.MAXSIZE, namewidth), minwidth) + self.sizes.HOREXTRASIZE
##		else:
##			minwidth = minwidth + self.sizes.HOREXTRASIZE
##		children = node.GetChildren()
##		# if this is an empty root...
##		if node == self.root and not children and ntype in ('seq', 'par', 'alt', 'excl', 'prio'):
##			print "DEBUG: this is the root node without any children."
##			width = minwidth + 2*self.sizes.HOREXTRASIZE
##			height = minheight + 2*self.sizes.GAPSIZE + self.sizes.LABSIZE	# Bah. It's sort of the same size. Who'll notice?
##			node.boxsize = width, height, begin
##			return node.boxsize
##		if not hasattr(node, 'expanded') or not children:
##			node.boxsize = minwidth, minheight + self.sizes.LABSIZE, begin
##			return node.boxsize
			
##		nchildren = len(children)
##		width = height = 0
##		horizontal = (ntype not in ('par', 'alt', 'excl', 'prio'))
##		for child in children:
##			w, h, b = self.sizeboxes(child)
##			if horizontal:
##				# children laid out horizontally
##				if h > height:
##					height = h
##				width = width + w + self.sizes.GAPSIZE
##			else:
##				# children laid out vertically
##				if w > width:
##					width = w
##				height = height + h + self.sizes.GAPSIZE
##			width = width + b
##		if ntype == 'seq' and grins_snap:
##			if horizontal:
##				width = width + self.sizes.DROPAREA
##			else:
##				height = height + self.sizes.DROPAREA
##		if horizontal:
##			width = width - self.sizes.GAPSIZE
##		else:
##			height = height - self.sizes.GAPSIZE
##		if self.timescale:
##			# Again, for timescale mode we happily ignore all these computations
##			width = minwidth
##		else:
##			width = max(width + 2 * self.sizes.HEDGSIZE, minwidth)
##		height = height + self.sizes.VEDGSIZE + self.sizes.LABSIZE
##		node.boxsize = width, height, begin
##		return node.boxsize

##def do_expand(node, expand, nlevels=None, expleaftypes=0):
##	if nlevels == 0:
##		return 0
##	if nlevels != None:
##		nlevels = nlevels - 1
##	ntype = node.GetType()

##	# animate++
##	if expleaftypes and ntype in MMNode.leaftypes and node.GetChildren() and \
##		   (ntype != 'ext' or node.GetChannelType() != 'RealPix'):
##		pass
##	elif ntype not in MMNode.interiortypes and\
##	   (ntype != 'ext' or node.GetChannelType() != 'RealPix'):
##		return 0

##	changed = 0
##	if expand:
##		if not hasattr(node, 'expanded'):
##			expandnode(node)
##			changed = 1
##	elif hasattr(node, 'expanded'):
##		collapsenode(node)
##		changed = 1
##	for child in node.GetChildren():
##		if do_expand(child, expand, nlevels, expleaftypes):
##			changed = 1
##	return changed			# any changes in this subtree

##def countlevels(node, numwanted):
##	on_this_level = [node]
##	level = 1
##	while 1:
##		numwanted = numwanted - len(on_this_level)
##		if numwanted <= 0 or not on_this_level:
##			return level
##		on_next_level = []
##		for n in on_this_level:
##			on_next_level = on_next_level + n.GetChildren()
##		on_this_level = on_next_level
##		level = level + 1

# XXX The following should be merged with ChannelView's GO class :-(
# Actually, this will be using a completely different approach now :-). -mjvdg.

# class Object:
# 	# Will soon be deprecated.
	
# 	def __init__(self, mother, item):
# 		# mother is a HierachyView
# 		# item is a tuple of (MMNode, int, box) where box is (float, float, float, float)		
# 		print "TODO: Objects will soon no longer be used. -mjvdg."
# 		self.mother = mother	# : HierarchyView
# 		node, self.boxtype, self.box = item
# 		node.box = self.box	# Assigning the coords to the MMNode
# 		node.set_infoicon = self.set_infoicon # Temp override of class method
# 		self.node = node	# : MMNode
# 		self.iconbox = None
# 		if self.node.__class__ is SlideMMNode:
# 			self.name = MMAttrdefs.getattr(node, 'tag')
# 		else:
# 			self.name = MMAttrdefs.getattr(node, 'name')
# 		self.selected = 0
# 		self.ok = 1
# 		if node.GetType() == 'ext' and \
# 		   node.GetChannelType() == 'RealPix':
# 			if not hasattr(node, 'slideshow'):
# 				import realnode
# 				node.slideshow = realnode.SlideShow(node)

# 	# Make this object the focus
# 	def select(self):
# 		if self.selected:
# 			return
# 		self.selected = 1
# 		if self.ok:
# 			self.drawfocus()

# 	# Remove this object from the focus
# 	def deselect(self):
# 		if not self.selected:
# 			return
# 		self.selected = 0
# 		if self.ok:
# 			self.drawfocus()

# 	# Check for mouse hit inside this object
# 	def ishit(self, x, y):
# 		l, t, r, b = self.box
# 		return l <= x <= r and t <= y <= b

# 	def cleanup(self):
# 		self.mother = None
# 		node = self.node
# 		del node.box
# 		del node.set_infoicon  # Makes class method visible again

# 	def draw(self):
# 		d = self.mother.new_displist
# 		dummy = d.usefont(f_title)
# 		rw, rh = self.mother.canvassize
# 		titleheight = self.mother.titleheight
# 		awidth = self.mother.arrwidth
# 		aheight = self.mother.arrheight
# 		chnameheight = self.mother.chnameheight
# 		##hmargin = d.strsize('x')[0] / 1.5
# 		##vmargin = titleheight / 5
# 		hmargin, vmargin = d.get3dbordersize()
# 		hmargin = hmargin*1.5
# 		vmargin = vmargin*1.5
# 		l, t, r, b = self.box
# 		node = self.node
# 		ntype = node.GetType()
# 		willplay = not self.mother.showplayability or node.WillPlay()
# 		if ntype in MMNode.leaftypes:
# 			if node.GetChannelType() == 'RealPix':
# 				if willplay:
# 					color = RPCOLOR
# 				else:
# 					color = RPCOLOR_NOPLAY
# 			elif node.GetChannelType()=='animate':
# 				if willplay:
# 					color = SLIDECOLOR
# 				else:
# 					color = SLIDECOLOR_NOPLAY
# 			else:
# 				if willplay:
# 					color = LEAFCOLOR
# 				else:
# 					color = LEAFCOLOR_NOPLAY
# 		elif ntype == 'seq':
# 			if willplay:
# 				color = SEQCOLOR
# 			else:
# 				color = SEQCOLOR_NOPLAY
# 		elif ntype == 'par':
# 			if willplay:
# 				color = PARCOLOR
# 			else:
# 				color = PARCOLOR_NOPLAY
# 		elif ntype == 'excl':
# 			if willplay:
# 				color = EXCLCOLOR
# 			else:
# 				color = EXCLCOLOR_NOPLAY
# 		elif ntype == 'prio':
# 			if willplay:
# 				color = PRIOCOLOR
# 			else:
# 				color = PRIOCOLOR_NOPLAY
# 		elif ntype == 'bag':
# 			if willplay:
# 				color = BAGCOLOR
# 			else:
# 				color = BAGCOLOR_NOPLAY
# 		elif ntype == 'alt':
# 			if willplay:
# 				color = ALTCOLOR
# 			else:
# 				color = ALTCOLOR_NOPLAY
# 		elif ntype == 'slide':
# 			if willplay:
# 				color = SLIDECOLOR
# 			else:
# 				color = SLIDECOLOR_NOPLAY
# 		else:
# 			color = 255, 0, 0 # Red -- error indicator
# 		d.drawfbox(color, (l, t, r - l, b - t))
# 		self.drawfocus()
# 		t1 = min(b, t + titleheight + vmargin)
# 		if node.GetType() not in MMNode.interiortypes and \
# 		   not hasattr(node, 'expanded') and \
# 		   b-t-vmargin >= titleheight+chnameheight:
# 			if chnameheight:
# 				b1 = b - chnameheight
# 				# draw channel name along bottom of box
# 				if node.__class__ is not SlideMMNode:
# 					self.drawchannelname(l+hmargin/2, b1,
# 							     r-hmargin/2, b-vmargin/2)
# 			else:
# 				b1 = b - 1.5*vmargin
# 			# draw thumbnail/icon if enough space
# ##			if b1-t1 >= titleheight and \
# ##			   r-l >= hmargin * 2.5:
# 			url = node.GetAttrDef('file', None)
# 			if url:
# 				mtype = MMmimetypes.guess_type(url)[0]
# 			else:
# 				mtype = None
# 			ctype = node.GetChannelType()
# 			if node.__class__ is SlideMMNode and \
# 			   MMAttrdefs.getattr(node, 'tag') in ('fadein', 'crossfade', 'wipe'):
# 				ctype = 'image'
# 			elif ctype == 'sound' and mtype and string.find(mtype, 'real') >= 0:
# 				ctype = 'RealAudio'
# 			elif ctype == 'video' and mtype and string.find(mtype, 'real') >= 0:
# 				ctype = 'RealVideo'
# 			f = os.path.join(self.mother.datadir, '%s.tiff' % ctype)
# 			if url and self.mother.thumbnails and ctype == 'image':
# 				url = node.context.findurl(url)
# 				try:
# 					f = MMurl.urlretrieve(url)[0]
# 				except IOError, arg:
# 					self.set_infoicon('error', 'Cannot load image: %s'%`arg`)
# 			ih = b1-t1
# 			iw = r-l-2*hmargin
# 			# XXXX The "0" values below need to be thought about
# 			if iw <= 0 or ih <= 0:
# 				# The box is too small, ignore the preview
# 				pass
# 			elif node.__class__ is SlideMMNode and \
# 			   MMAttrdefs.getattr(node, 'tag') in ('fill','fadeout'):
# 				d.drawfbox(MMAttrdefs.getattr(node, 'color'), (l+hmargin, (t1+b1-ih)/2, r-l-2*hmargin, ih))
# 				d.fgcolor(TEXTCOLOR)
# 				d.drawbox((l+hmargin, (t1+b1-ih)/2, iw, ih))
# 			elif node.GetChannelType() == 'brush':
# 				d.drawfbox(MMAttrdefs.getattr(node, 'fgcolor'), (l+hmargin, (t1+b1-ih)/2, r-l-2*hmargin, ih))
# 				d.fgcolor(TEXTCOLOR)
# 				d.drawbox((l+hmargin, (t1+b1-ih)/2, iw, ih))
# 			elif f is not None:
# 				try:
# 					box = d.display_image_from_file(f, center = 1,
# 									coordinates = (l+hmargin, (t1+b1-ih)/2, iw, ih), scale=-2)
# 				except windowinterface.error:
# 					pass
# 				else:
# 					d.fgcolor(TEXTCOLOR)
# 					d.drawbox(box)
# 			# Draw the transition handles. WORKING HERE mjvdg
# 			# Actually, I was just mucking around. Delete this.
# 			#gap = sizes_notime.GAPSIZE/pix_winwidth
# 			#wsize = gap/2
# 			#hsize = (b-t)/3
# 			#th_top = t +  ( (b-t)/2 - hsize/2 ) # top of box.
# 			#th1_left = l - gap/2		    			
# 			#th2_left = r
# 			#d.drawbox((th1_left, th_top, wsize, hsize))
# 			#d.drawbox((th2_left, th_top, wsize, hsize))
			
# 		# draw a little triangle to indicate expanded/collapsed state
# 		title_left = l+hmargin
# 		if (node.GetType() in MMNode.interiortypes and not \
# 		    (root_expanded and node is self.mother.root)) \
# 		    or \
# 		   (node.GetType() == 'ext' and
# 		    node.GetChannelType() == 'RealPix'):
# 			left_pos = title_left
# 			title_left = title_left + awidth
# 			# Check whether it fits
# 			if l+awidth+2*hmargin <= r and t+aheight+2*vmargin <= b:
# 				node.abox = left_pos, t+vmargin, title_left, t+vmargin+aheight
# 				# We assume here that the icon has room around the edges
# 				# Also, don't set self.iconbox (yet: erroricons on structnodes TBD)
# 				iconbox = left_pos, t+vmargin, awidth, aheight
# 				if hasattr(node, 'expanded'):
# 					d.drawicon(iconbox, 'open')
# 				else:
# 					d.drawicon(iconbox, 'closed')
# 			else:
# 				node.abox = (0, 0, -1, -1)
				
# 		# Draw a decoration at the end of the node.
# 		if ntype == 'seq' and grins_snap and (not self.boxtype==LEAFBOX or self.node==self.mother.root): 
# 			border = float(sizes_notime.HEDGSIZE)/rw
# 			base = float(sizes_notime.VEDGSIZE)/rh
			
# 			dec_right = r-border
# 			minsize = float(sizes_notime.DROPAREASIZE)/rw
# 			dec_left = dec_right - self.mother.droparea
# 			dec_bottom = b-base
# 			dec_top = t+titleheight
			
# 			d.draw3dbox(FOCUSLEFT, FOCUSTOP, FOCUSRIGHT, FOCUSBOTTOM,
# 				    (dec_left, dec_top, dec_right-dec_left, dec_bottom-dec_top))
# 			d.drawfbox( LEAFCOLOR,
# 				    (dec_left+hmargin, dec_top+vmargin, dec_right-dec_left-2*hmargin, dec_bottom-dec_top-2*vmargin) )

# 		# animate++
# 		if node.GetType() in MMNode.leaftypes and node.GetChildren() and \
# 		   (ntype != 'ext' or node.GetChannelType() != 'RealPix'):
# 			left_pos = title_left
# 			title_left = title_left + awidth
# 			# Check whether it fits
# 			if l+awidth+2*hmargin <= r and t+aheight+2*vmargin <= b:
# 				node.abox = left_pos, t+vmargin, title_left, t+vmargin+aheight
# 				iconbox = left_pos, t+vmargin, awidth, aheight
# 				if hasattr(node, 'expanded'):
# 					d.drawicon(iconbox, 'open')
# 				else:
# 					d.drawicon(iconbox, 'closed')
# 			else:
# 				node.abox = (0, 0, -1, -1)

# 		# And leave room for the bandwidth and/or error icon
# 		left_pos = title_left
# 		title_left = title_left + awidth
# 		self.iconbox = left_pos, t+vmargin, awidth, aheight
# 		if node.infoicon:
# 			d.drawicon(self.iconbox, node.infoicon)
# 		elif show_links:
# 			d.drawicon(self.iconbox, self.getlinkicon())
# 		else:
# 			d.drawicon(self.iconbox, '')
# 		# draw the name
# 		d.fgcolor(TEXTCOLOR)
# 		d.centerstring(title_left, t+vmargin/2, r-hmargin/2, t1, self.name)
# 		# If this is a node with suppressed detail,
# 		# draw some lines
# 		if self.boxtype == LEAFBOX and \
# 		   node.GetType() in MMNode.interiortypes and \
# 		   len(node.GetChildren()) > 0:
# 			l1 = l + hmargin*2
# 			t1 = t + titleheight + vmargin
# 			r1 = r - hmargin*2
# 			b1 = b - vmargin*2
# 			if l1 < r1 and t1 < b1:
# 				if node.GetType() in ('par', 'alt', 'excl', 'prio'):
# 					# Draw horizontal lines
# 					stepsize = (b1-t1)/2
# 					while stepsize > vmargin*4:
# 						stepsize = stepsize / 2
# 					x = l1
# 					y = t1
# 					while y <= b1:
# 						d.drawline(TEXTCOLOR,
# 							   [(l1, y), (r1, y)])
# 						y = y + stepsize
# 				else:
# 					# Draw verticle lines.
# 					stepsize = (r1-l1)/2
# 					while stepsize > hmargin*4:
# 						stepsize = stepsize / 2
# 					x = l1
# 					while x <= r1:
# 						d.drawline(TEXTCOLOR,
# 							   [(x, t1), (x, b1)])
# 						x = x + stepsize

# 	def drawchannelname(self, l, t, r, b):
# 		d = self.mother.new_displist
# 		d.fgcolor(CTEXTCOLOR)
# 		dummy = d.usefont(f_channel)
# 		d.centerstring(l, t, r, b, self.node.GetChannelName())
# 		dummy = d.usefont(f_title)

# 	def drawfocus(self):
# 		cl = FOCUSLEFT
# 		ct = FOCUSTOP
# 		cr = FOCUSRIGHT
# 		cb = FOCUSBOTTOM
# 		if self.selected:
# 			cl, cr = cr, cl
# 			ct, cb = cb, ct
# 		d = self.mother.new_displist
# 		l, t, r, b = self.box
# 		if self.mother.sizes.FLATBOX:
# 			d.fgcolor(ct)
# 			d.drawbox((l, t, r-l, b-t))
# 		else:
# 			d.draw3dbox(cl, ct, cr, cb, (l, t, r - l, b - t))
			
# 	def set_infoicon(self, icon, msg=None):
# 		"""Redraw the informational icon for this node"""
# 		self.node.infoicon = icon
# 		self.node.errormessage = msg
# 		if not self.iconbox:
# 			return
# 		d = self.mother.opt_init_display()
# 		if not d:
# 			return
# 		if not icon:
# 			icon = self.getlinkicon()
# 		d.drawicon(self.iconbox, icon)
# 		self.mother.render()

# 	def getlinkicon(self):
# 		"""Return icon to draw for showing incoming/outgoing hyperlinks"""
# 		links = self.node.context.hyperlinks
# 		is_src, is_dst = links.findnodelinks(self.node)
# 		if is_src:
# 			if is_dst:
# 				return 'linksrcdst'
# 			else:
# 				return 'linksrc'
# 		else:
# 			if is_dst:
# 				return 'linkdst'
# 			else:
# 				return ''

# 	def GetPrevious(self):		# mjvdg 27-sept-2000
# 		# returns the object prior to this one.
# 		if isinstance(self.node, MMNode.MMNode):
# 			#import pdb
# 			#pdb.set_trace()
# 			return self.mother.whichobj(self.node.GetPrevious())
# 		else:
# 			# This shouldn't happen.. in theory.
# 			print "DEBUG: Object does not have an MMNode!"
# 			return None

# 	def HasNoURL(self):		# mjvdg 27-sept-2000
# 		# returns True if this object's URL is empty.
# 		if isinstance(self.node, MMNode.MMNode):
# 			return not self.node.attrdict.has_key('file')
# 		else:
# 			return 0
	

# 	#
# 	# Menu handling functions, aka callbacks.
# 	#

# ##	def helpcall(self):
# ##		import Help
# ##		Help.givehelp('Hierarchy_view')

# 	def expandcall(self):
# 		# 'Expand' the view of this node.
# 		self.mother.toplevel.setwaiting()
# 		if hasattr(self.node, 'expanded'):
# 			collapsenode(self.node)
# 		else:
# 			expandnode(self.node)
# 		self.mother.recalc()

# 	def expandallcall(self, expand):
# 		# Expand the view of this node and all kids.
# 		self.mother.toplevel.setwaiting()
# 		if do_expand(self.node, expand, None, 1):
# 			# there were changes
# 			# make sure root isn't collapsed
# 			self.mother.recalc()

# 	def playcall(self):
# 		top = self.mother.toplevel
# 		top.setwaiting()
# 		top.player.playsubtree(self.node)

# 	def playfromcall(self):
# 		top = self.mother.toplevel
# 		top.setwaiting()
# 		top.player.playfrom(self.node)

# 	def attrcall(self):
# 		self.mother.toplevel.setwaiting()
# 		import AttrEdit
# 		AttrEdit.showattreditor(self.mother.toplevel, self.node)

# 	def infocall(self):
# 		self.mother.toplevel.setwaiting()
# 		import NodeInfo
# 		NodeInfo.shownodeinfo(self.mother.toplevel, self.node)

# 	def editcall(self):
# 		self.mother.toplevel.setwaiting()
# 		import NodeEdit
# 		NodeEdit.showeditor(self.node)
# 	def _editcall(self):
# 		self.mother.toplevel.setwaiting()
# 		import NodeEdit
# 		NodeEdit._showeditor(self.node)
# 	def _opencall(self):
# 		self.mother.toplevel.setwaiting()
# 		import NodeEdit
# 		NodeEdit._showviewer(self.node)

# 	def anchorcall(self):
# 		self.mother.toplevel.setwaiting()
# 		import AnchorEdit
# 		AnchorEdit.showanchoreditor(self.mother.toplevel, self.node)

# 	def createanchorcall(self):
# 		self.mother.toplevel.links.wholenodeanchor(self.node)

# 	def hyperlinkcall(self):
# 		self.mother.toplevel.links.finish_link(self.node)

# 	def focuscall(self):
# 		top = self.mother.toplevel
# 		top.setwaiting()
# 		if top.channelview is not None:
# 			top.channelview.globalsetfocus(self.node)

# 	def deletecall(self):
# 		self.mother.deletefocus(0)

# 	def cutcall(self):
# 		self.mother.deletefocus(1)

# 	def copycall(self):
# 		mother = self.mother
# 		mother.toplevel.setwaiting()
# 		mother.copyfocus()

# 	def createbeforecall(self, chtype=None):
# 		self.mother.create(-1, chtype=chtype)

# 	def createbeforeintcall(self, ntype):
# 		self.mother.create(-1, ntype=ntype)

# 	def createaftercall(self, chtype=None):
# 		self.mother.create(1, chtype=chtype)

# 	def createafterintcall(self, ntype):
# 		self.mother.create(1, ntype=ntype)

# 	def createundercall(self, chtype=None):
# 		self.mother.create(0, chtype=chtype)

# 	def createunderintcall(self, ntype):
# 		self.mother.create(0, ntype=ntype)

# 	def createseqcall(self):
# 		self.mother.insertparent('seq')

# 	def createparcall(self):
# 		self.mother.insertparent('par')

# 	def createbagcall(self):
# 		self.mother.insertparent('bag')

# 	def createaltcall(self):
# 		self.mother.insertparent('alt')

# 	def pastebeforecall(self):
# 		self.mother.paste(-1)

# 	def pasteaftercall(self):
# 		self.mother.paste(1)

# 	def pasteundercall(self):
# 		self.mother.paste(0)


# class Nipple(Widgets.Widget):
# 	# The Nipples of an object are a graphical representation of the transitions
# 	# between the MMNodes that the object refers to.

# 	# TODO: rewrite this code.

# 	def __init__(self, mother, item):
# 		self.mother = mother
# 		self.node, self.boxtype, self.box = item # self.node is shared with another Object.
# 		self.breast = self.mother.whichobj(self.node) # The object that I'm attached to.
# 		self.iconbox = None	# This is the relevant icon for this nipple.
# 		self.top = None
# 		self.left = None
# 		self.width = None
# 		self.height = None

# 	def select(self):
# 		Object.select(self.breast)

# 	def deselect(self):
# 		Object.deselect(self.breast)

# 	def draw(self):
# 		d = self.mother.new_displist
# 		d.drawbox((self.left, self.top, self.width, self.height))

# 	def append_to_left(self):
# 		# Calulates size and position for appending to left of an Object.
# 		l, t, r, b = self.box

# 		canvas_width, canvas_height = self.mother.canvassize
# 		wgapsize = (sizes_notime.GAPSIZE)/canvas_width
		
# 		self.left = l - wgapsize/2
# 		self.top = t + (b-t)/3
# 		self.width = wgapsize/2
# 		self.height = (b-t)/3

# 	def append_to_right(self):
# 		# Calulates size and position for appending to right of an Object.
# 		l, t, r, b = self.box

# 		canvas_width, canvas_height = self.mother.canvassize
# 		wgapsize = (sizes_notime.GAPSIZE)/canvas_width

# 		self.left = r
# 		self.top = t + (b-t)/3
# 		self.width = wgapsize/2
# 		self.height = (b-t)/3
		
# 	def ishit(self, x, y):
# 		if self.top < y <= self.top+self.height and self.left < x < self.left+self.width:
# 			print "Hit!!"
# 			return 1
# 		else:
# 			return 0

# 	def cleanup(self):
# 		return			# no cleanup needs to be done on a Nipple.
# 					# This is handled by the assoc-ed Object.
				       		
# specialized node for RealPix slides (transitions)
##class SlideMMNode(MMNode.MMNode):
##	def GetChannel(self):
##		return None

##	def GetChannelName(self):
##		return 'undefined'

##	def setgensr(self):
##		self.gensr = self.gensr_leaf

##	def GetAttrDef(self, attr, default):
##		if self.attrdict.has_key(attr):
##			return self.attrdict[attr]
##		if attr == 'color':
##			return MMAttrdefs.getattr(self.GetParent(), 'bgcolor')
##		return default

def expandnode(node):
	# Bad hack. I shouldn't refer to private attrs of a node.
	node.collapsed = 0

##def expandnode(node):
##	if hasattr(node, 'expanded'):
##		# already expanded
##		return
##	node.expanded = 1
##	if node.GetType() != 'ext' or node.GetChannelType() != 'RealPix':
##		return
##	if not hasattr(node, 'slideshow'):
##		import realnode
##		node.slideshow = realnode.SlideShow(node)
##	ctx = node.GetContext()
##	for attrs in node.slideshow.rp.tags:
##		child = SlideMMNode('slide', ctx, ctx.newuid())
##		ctx.knownode(child.GetUID(), child)
##		child.parent = node
##		node.children.append(child)
##		child.attrdict.update(attrs)

##def collapsenode(node):
##	if hasattr(node, 'expanded'):
##		del node.expanded
##	# only remove children if they are of type SlideMMNode
##	children = node.GetChildren()
##	if not children or children[0].__class__ is not SlideMMNode:
##		return
##	ctx = node.GetContext()
##	for child in children:
##		child.parent = None
##		ctx.forgetnode(child.GetUID())
##	node.children = []

##def slidestart(pnode, url, index):
##	import Bandwidth
##	ctx = pnode.GetContext()
##	i = index
##	if i == -1:
##		i = len(pnode.children)
##	urls = {}
##	start = MMAttrdefs.getattr(pnode, 'preroll')
##	filesize = 0
##	children = pnode.children
##	for i in range(0, i):
##		child = children[i]
##		start = start + MMAttrdefs.getattr(child, 'start')
##		if MMAttrdefs.getattr(child,'tag') in ('fadein', 'crossfade', 'wipe'):
##			curl = MMAttrdefs.getattr(child, 'file')
##			if not curl:
##				continue
##			if not urls.has_key(curl):
##				try:
##					thissize = Bandwidth.GetSize(ctx.findurl(curl), convert = MMAttrdefs.getattr(child, 'project_convert'))
##					if thissize:
##						filesize = filesize + thissize
##				except Bandwidth.Error, arg:
##					child.set_infoicon('error', arg)
##			urls[curl] = 0
##	try:
##		thissize = Bandwidth.GetSize(url)
##		filesize = filesize + thissize
##	except Bandwidth.Error, arg:
##		pnode.set_infoicon('error', arg)
##	minstart = float(filesize) * 8 / MMAttrdefs.getattr(pnode, 'bitrate')
##	return start, minstart
