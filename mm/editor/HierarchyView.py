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
		self.drawing = 0	# A lock to prevent recursion in the draw() method of self.
		self.redrawing = 0	# A lock to prevent recursion in redraw()
		self.need_resize = 1	# Whether the tree needs to be resized.
		self.dirty = 1		# Whether the scene graph needs redrawing.
		self.selected_widget = None
		self.focusobj = None	# Old Object() code - remove this when no longer used. TODO
		self.focusnode = self.prevfocusnode = self.root	# : MMNode - remove when no longer used.
		self.editmgr = self.root.context.editmgr

		self.destroynode = None	# node to be destroyed later
		self.thumbnails = settings.get('structure_thumbnails')
		self.showplayability = 1
		self.timescale = None
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
		self.show_links = 1	# Show HTML links??? I think.. -mjvdg.
		self.sizes = sizes_notime
		from cmif import findfile
		self.datadir = findfile('GRiNS-Icons')
		
		self.__add_commands()
		HierarchyViewDialog.__init__(self)		

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
				EDIT_TVIEW(callback = (self.edit_in_tview, ())),
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
		rv.append(NEW_UNDER_ALT(callback = (self.createunderintcall, ('alt',))))
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

		fnode = self.focusnode

		if isinstance(self.selected_widget, TransitionWidget):
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
		elif isinstance(self.selected_widget, TransitionWidget):
			popupmenu = self.transition_popupmenu
			commands = commands + self.transitioncommands
		else:
			popupmenu = self.leaf_popupmenu	# for all leaf nodes.

		commands = self.__compute_commands(commands) # Adds to the commands for the current focus node.		
		self.setcommands(commands)
		
		self.setpopup(popupmenu)
		self.setstate()

		# make sure focus is visible
		if self.focusnode.GetParent():
			self.focusnode.GetParent().ExpandParents()

##		t0, t1, t2, download, begindelay = self.focusnode.GetTimes('bandwidth')
		# XXX Very expensive...
		if self.timescale in ('focus', 'cfocus'):
			self.need_resize = 1
			self.dirty = 1
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
		self.selected_widget = None
		self.focusobj = None
		self.scene_graph = create_MMNode_widget(self.root, self)
		self.dirty = 1
		self.need_resize = 1
		if self.window and self.focusnode:
			self.select_node(self.focusnode)
			widget = self.focusnode.views['struct_view']
			self.window.scrollvisible(widget.get_box(), windowinterface.UNIT_PXL)


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
		self.draw()

	def refresh_scene_graph(self):
		# Recalculates the node structure from the MMNode structure.
		if self.scene_graph is not None:
			self.scene_graph.destroy()
		self.create_scene_graph()

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
			x,y = self.scene_graph.get_minsize()
			self.mcanvassize = x,y

			if x < 1.0 or y < 1.0:
				print "Error: unconverted relative coordinates found. HierarchyView:497"
			if self.timescale:
				self.timemapper = TimeMapper.TimeMapper(self.timescale=='cfocus')
				if self.timescale == 'global':
					timeroot = self.scene_graph
				else:
					timeroot = self.focusnode.views['struct_view']
				# Remove old timing info
				self.scene_graph.removedependencies()
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
		else:
			self.draw_scene()
		
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
		self.setfocusnode(node)

	def globalfocuschanged(self, focustype, focusobject):
		# for now, catch only MMNode focus
		if focustype == 'MMNode':
			if isinstance(focusobject, MMNode.MMNode) and focusobject is not self.focusnode:
				self.select_node(focusobject, 1)
				self.aftersetfocus()
				self.need_resize = 1
				self.dirty = 1
				self.draw()
##		else:
##			print "DEBUG: globalfocuschanged called but not used: ", focustype, focusobject

	#################################################
	# Event handlers                                #
	#################################################
	def redraw(self, *rest):
		# Handles redraw events, for example when the canvas is resized.
		self.draw_scene()

	def mouse(self, dummy, window, event, params):
		self.toplevel.setwaiting()
		x, y = params[0:2]
		if x >= 1 or y >= 1:
			windowinterface.beep()
			return
		x = x * self.mcanvassize[0]
		y = y * self.mcanvassize[1]
		self.mousehitx = x
		self.mousehity = y
		self.select(x, y)

		if self.need_resize:
			self.draw()
		else:
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
			horizontal = (t not in ('par', 'alt', 'excl', 'prio'))
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
		self.focusobj = None
		self.focusnode = None

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
			prearmtime = node.compute_download_time()
			if prearmtime:
				arc = MMNode.MMSyncArc(node, 'begin', srcnode='syncbase', delay=prearmtime)
				self.editmgr.setnodeattr(node, 'beginlist', [arc])
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

		if isinstance(dstobj, StructureObjWidget): # If it's an internal node.
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
		self.focusobj = None
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
		self.setfocusnode(siblings[i])
		self.draw()

	def toparent(self):
		if not self.focusnode:
			windowinterface.beep()
			return
		parent = self.focusnode.GetParent()
		if not parent:
			windowinterface.beep()
			return
		self.setfocusnode(parent)
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
		self.setfocusnode(children[i])
		self.draw()

	def select_widget(self, widget, external = 0):
		# Set the focus to a specific widget on the user interface.
		# Make the widget the current selection.
		if self.selected_widget == widget:
			# don't do anything if the focus is already set to the requested widget.
			# this is important because of the setglobalfocus call below.
			return
		if isinstance(self.selected_widget, Widgets.Widget):
			self.selected_widget.unselect()
		self.selected_widget = widget
		self.focusobj = widget	# Used for callbacks.
		self.prevfocusnode = self.focusnode
		if widget is None:
			self.focusnode = None
		else: 
			self.focusnode = widget.node
			widget.select()
			self.window.scrollvisible(widget.get_box(), windowinterface.UNIT_PXL)
		self.aftersetfocus()
		self.dirty = 1
		if not external:
			# avoid recursive setglobalfocus
			self.editmgr.setglobalfocus("MMNode", self.focusnode)

	def select_node(self, node, external = 0):
		# Set the focus to a specfic MMNode (obviously the focus did not come from the UI)
		self.setfocusnode(node, external)
		
	def setfocusnode(self, node, external = 0):
		# Try not to call this function
		if not node:
			self.select_widget(None, external)
		else:
			widget = node.views['struct_view']
			self.select_widget(widget, external)

	# Handle a selection click at (x, y)
	def select(self, x, y):
		widget = self.scene_graph.get_obj_at((x,y))
		if widget == None:
			#print "DEBUG: No widget under the mouse."
			pass
		if widget==None or widget==self.selected_widget:
			return
		else:
			self.select_widget(widget)
##			self.aftersetfocus()
			self.dirty = 1
		assert isinstance(widget.node, MMNode.MMNode)
#		print "DEBUG: Hierarchyview recieved select(x,y)"


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
		if self.focusobj: self.focusobj.helpcall()

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
		self.dirty = 1
		self.draw()

	def playablecall(self):
		self.toplevel.setwaiting()
		self.showplayability = not self.showplayability
		self.settoggle(PLAYABLE, self.showplayability)
		self.dirty = 1
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
		self.dirty = 1
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

	def rpconvertcall(self):
		if self.focusobj: self.focusobj.rpconvertcall()

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

	def edit_in_tview(self):
		if self.focusobj:
			self.toplevel.open_node_in_tview(self.focusobj.node)

def expandnode(node):
	# Bad hack. I shouldn't refer to private attrs of a node.
	node.collapsed = 0
