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
		self.selected_regions = []
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
			COPY(callback = (self.copycall, ())),
			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),
			#THUMBNAIL(callback = (self.thumbnailcall, ())),
			EXPANDALL(callback = (self.expandallcall, (1,))),
			COLLAPSEALL(callback = (self.expandallcall, (0,))),
			PLAYNODE(callback = (self.playcall, ())),
			PLAYFROM(callback = (self.playfromcall, ())),
			]
		self.navigatecommands = [
			TOPARENT(callback = (self.toparent, ())),
			TOCHILD(callback = (self.tochild, (0,))),
			NEXTSIBLING(callback = (self.tosibling, (1,))),
			PREVSIBLING(callback = (self.tosibling, (-1,))),
			]

		self.interiorcommands = [
			EXPAND(callback = (self.expandcall, ())),
			NEW_UNDER(callback = (self.createundercall, ())),
			NEW_UNDER_SEQ(callback = (self.createunderintcall, ('seq',))),
			NEW_UNDER_PAR(callback = (self.createunderintcall, ('par',))),
			NEW_UNDER_ALT(callback = (self.createunderintcall, ('alt',))),
			NEW_UNDER_EXCL(callback = (self.createunderintcall, ('excl',))),
			NEW_UNDER_IMAGE(callback = (self.createundercall, ('image',))),
			NEW_UNDER_SOUND(callback = (self.createundercall, ('sound',))),
			NEW_UNDER_VIDEO(callback = (self.createundercall, ('video',))),
			NEW_UNDER_TEXT(callback = (self.createundercall, ('text',))),
			NEW_UNDER_HTML(callback = (self.createundercall, ('html',))),
			]

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
			

	def update_popupmenu_node(self):
		# Sets the popup menu to channel mode.
		commands = self.commands
		popupmenu = [self.menu_no_nodes]	# there needs to be a default.
		if len(self.selected_nodes) != 1:
			print "Warning: Selection is: ", self.selected_nodes
			print "Warning: Multiple selection pop-ups not thought about yet."
		else:
			n = self.selected_nodes[0].node
			if n.GetType() in MMNode.interiortypes:
				popupmenu = self.menu_interior_nodes
				commands = commands + self.interiorcommands \
					   + self.pasteinteriorcommands \
					   + self.structure_commands
				if n.children:
					commands = commands + self.navigatecommands
				if n is not self.root:
					commands = commands + self.notatrootcommands
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
		self.redraw()

	def kill(self):
		self.destroy()

	def globalfocuschanged(self, focustype, focusobject):
		print "DEBUG: TemporalView recieved global focus change: ", focustype, focusobject
		if self.just_selected:
			print "DEBUG: Just selected that channel."
			self.just_selected = None
			return
		if self.recurse_lock:
			print "DEBUG: Got a recurse lock."
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
		print "DEBUG: redrawing.."
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
		print "I should kill myself (the window, that is :-) )"

	def ev_pastefile(self, dummy, window, event, params):
		print "Pasting a file!"

	def ev_dragfile(self, dummy, window, event, params):
		print "Drag file!"

	def ev_dropfile(self, dummy, window, event, params):
		print "Dropping a file!"

	def ev_dragnode(self, dummy, window, event, params):
		print "DEBUG: ev_dragnode called."
		x,y,mode, xf, yf= params[0:5]
		x,y = self.rel2abs((x,y))
		xf, yf = self.rel2abs((xf, yf))
		return self.scene.dragging_node((x,y), (xf, yf), mode)
		

	def ev_dropnode(self, dummy, window, event, params):
		print "Dropped a node!"
		return 0

######################################################################
	# Commands from the menus.

	def helpcall(self):
		if self.focusobj: self.focusobj.helpcall()

	def expandcall(self):
		if self.focusobj: self.focusobj.expandcall()
		self.draw()

	def expandallcall(self, expand):
		if self.focusobj: self.focusobj.expandallcall(expand)
		self.draw()

	def playablecall(self):
		self.toplevel.setwaiting()
		self.showplayability = not self.showplayability
		self.settoggle(PLAYABLE, self.showplayability)
		self.draw()

	def bandwidthcall(self):
		print "TODO: bandwidth compute."
##		self.toplevel.setwaiting()
##		bandwidth = settings.get('system_bitrate')
##		if bandwidth > 1000000:
##			bwname = "%dMbps"%(bandwidth/1000000)
##		elif bandwidth % 1000 == 0:
##			bwname = "%dkbps"%(bandwidth/1000)
##		else:
##			bwname = "%dbps"%bandwidth
##		msg = 'Computing bandwidth usage at %s...'%bwname
##		dialog = windowinterface.BandwidthComputeDialog(msg, parent=self.getparentwindow())
##		bandwidth, prerolltime, delaycount, errorseconds, errorcount = \
##			BandwidthCompute.compute_bandwidth(self.root)
##		dialog.setinfo(prerolltime, errorseconds, delaycount, errorcount)
##		dialog.done()

	def playcall(self):
		if self.focusobj: self.focusobj.playcall()

	def playfromcall(self):
		if self.focusobj: self.focusobj.playfromcall()

	def attrcall(self):
		if isinstance(self.focusobj, MMNode.MMChannel):
			import AttrEdit
			AttrEdit.showchannelattreditor(self.toplevel, self.focusobj)
		else:
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

	def rpconvertcall(self):
		if self.focusobj: self.focusobj.rpconvertcall()

	def deletecall(self):
		if self.focusobj: self.focusobj.deletecall()

	def cutcall(self):
		if self.focusobj: self.focusobj.cutcall()

	def copycall(self):
		if self.focusobj: self.focusobj.copycall()

	def copyfocus(self):
		import Clipboard
		# Copies the node with focus to the clipboard.
		if len(self.selected_nodes) == 1 and isinstance(self.selected_nodes[0], MMWidget):
			node = self.selected_nodes[0].node
			print "DEBUG: Node: ", node
			if not node:
				windowinterface.beep()
				return
			t, n = Clipboard.getclip()
			if t == 'node' and n is not None:
				n.Destroy()
			Clipboard.setclip('node', node.DeepCopy())
			print "DEBUG: Copied node to clipboard."
		else:
			print "Warning: Multiple selection copy not done yet."

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
