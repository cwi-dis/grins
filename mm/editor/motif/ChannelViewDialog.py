from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
import MMAttrdefs
from usercmd import *
from flags import *

class ChannelViewDialog(ViewDialog):
	adornments = {
		'shortcuts': {
			'n': NEW_CHANNEL,
			'N': NEXT_MINIDOC,
			'P': PREV_MINIDOC,
			'T': TOGGLE_UNUSED,
##			'i': INFO,
			'a': ATTRIBUTES,
			'd': DELETE,
			'm': MOVE_CHANNEL,
			'c': COPY_CHANNEL,
			'p': PLAYNODE,
			'G': PLAYFROM,
			'f': PUSHFOCUS,
			's': FINISH_ARC,
			'T': CREATEANCHOR,
			'L': FINISH_LINK,
			'e': CONTENT,
			't': ANCHORS,
			'b': TOGGLE_BWSTRIP,
			},
		'menubar': [
			(SMIL, 'Close', [
				(SMIL, 'Close', CLOSE_WINDOW),
				]),
			(SMIL, 'Edit', [
				(SMIL, 'Delete', DELETE),
				(SMIL, None),
				(SMIL, 'New Channel...', NEW_CHANNEL),
				(SMIL, None),
				(SMIL, 'Move Channel', MOVE_CHANNEL),
				(SMIL, 'Copy Channel', COPY_CHANNEL),
				(CMIF, 'Toggle Channel State', TOGGLE_ONOFF),
				(SMIL, None),
##				(SMIL, 'Info...', INFO),
				(SMIL, 'Properties...', ATTRIBUTES),
				(SMIL, 'Edit Content...', CONTENT),
				]),
			(SMIL, 'Play', [
				(SMIL, 'Play Node', PLAYNODE),
				(SMIL, 'Play from Node', PLAYFROM),
				]),
			(SMIL, 'Linking', [
				(SMIL, 'Create Simple Anchor', CREATEANCHOR),
				(SMIL, 'Finish Hyperlink to Selection', FINISH_LINK),
				(SMIL, 'Anchors...', ANCHORS),
				(SMIL, None),
				(SMIL, 'Create Sync Arc from Selection...', FINISH_ARC),
				(SMIL, 'Select Sync Arc', SYNCARCS),
				]),
			(SMIL, 'View', [
				(SMIL, 'Zoom In', CANVAS_WIDTH),
				(SMIL, 'Fit in Window', CANVAS_RESET),
				(SMIL, None),
				(SMIL, 'Synchronize Selection', PUSHFOCUS),
				(SMIL, None),
				(SMIL, 'Unused Channels', TOGGLE_UNUSED, 't'),
				(SMIL, 'Sync Arcs', TOGGLE_ARCS, 't'),
				(SMIL, 'Image Thumbnails', THUMBNAIL, 't'),
				(SMIL, 'Bandwidth Usage', TOGGLE_BWSTRIP, 't'),
				(CMIF, None),
				(CMIF, 'Minidocument Navigation', [
					(CMIF, 'Next', NEXT_MINIDOC),
					(CMIF, 'Previous', PREV_MINIDOC),
					(CMIF, 'Ancestors', ANCESTORS),
					(CMIF, 'Siblings', SIBLINGS),
					(CMIF, 'Descendants', DESCENDANTS),
					]),
##				(SMIL, 'Layout navigation', LAYOUTS),
				]),
			(SMIL, 'Help', [
				(SMIL, 'Help...', HELP),
				]),
			],
		'toolbar': None, # no images yet...
		'close': [ CLOSE_WINDOW, ],
		}

	def __init__(self):
		ViewDialog.__init__(self, 'cview_')

	def show(self, title):
		if self.is_showing():
			self.window.pop(poptop = 1)
			return
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.adornments['flags'] = curflags()
		self.window = windowinterface.newcmwindow(x, y, w, h, title,
				pixmap = 1, adornments = self.adornments,
				canvassize = (w, h))
		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.set_toggle(TOGGLE_UNUSED, self.showall)
		self.window.set_toggle(TOGGLE_ARCS, self.showarcs)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
		self.window.register(WMEVENTS.DropFile, self.dropfile, None)
		self.window.register(WMEVENTS.DropURL, self.dropfile, None)

	def hide(self, *rest):
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = self.new_displist = None

	def setcommands(self, commandlist, title):
		self.window.set_commandlist(commandlist)
		self.window.set_dynamiclist(ANCESTORS, self.baseobject.ancestors)
		self.window.set_dynamiclist(SIBLINGS, self.baseobject.siblings)
		self.window.set_dynamiclist(DESCENDANTS, self.baseobject.descendants)
		self.window.set_dynamiclist(SYNCARCS, (self.focus and self.focus.arcmenu) or [])
##		self.window.set_dynamiclist(LAYOUTS, self.layouts)

	def setpopup(self, menutemplate):
		self.window.setpopupmenu(menutemplate, SMIL)

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)

class GOCommand:
	POPUP_NONE = (
		(SMIL, 'New Channel...', NEW_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_NONE

	def helpcall(self):
		pass

class BandwidthStripBoxCommand:
	POPUP_BWSTRIP = (
		(SMIL, "14k4", BANDWIDTH_14K4),
		(SMIL, "28k8", BANDWIDTH_28K8),
		(SMIL, "ISDN", BANDWIDTH_ISDN),
		(SMIL, "T1 (1 Mbps)", BANDWIDTH_T1),
		(SMIL, "LAN (10 Mbps)", BANDWIDTH_LAN),
		(SMIL, None),
		(SMIL, "Other...", BANDWIDTH_OTHER),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_BWSTRIP

class ChannelBoxCommand:
	POPUP_CHANNEL = (
##		(SMIL, 'Toggle Channel State', TOGGLE_ONOFF),
		(SMIL, 'Properties...', ATTRIBUTES),
		(SMIL, None),
		(SMIL, 'Delete', DELETE),
		(SMIL, None),
		(SMIL, 'Move Channel', MOVE_CHANNEL),
		(SMIL, 'Copy Channel', COPY_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_CHANNEL

class NodeBoxCommand:
	POPUP_NODE = (
		(SMIL, 'Play Node', PLAYNODE),
		(SMIL, 'Play from Node', PLAYFROM),
		(SMIL, None),
		(SMIL, 'Create Simple Anchor', CREATEANCHOR),
		(SMIL, 'Finish Hyperlink to Selection', FINISH_LINK),
		(SMIL, 'Create Sync Arc from Selection...', FINISH_ARC),
		(SMIL, None),
##		(SMIL, 'Info...', INFO),
		(SMIL, 'Properties...', ATTRIBUTES),
		(SMIL, 'Anchors...', ANCHORS),
		(SMIL, 'Edit Content...', CONTENT),
		)

	def __init__(self, mother, node):
		self.popupmenu = self.POPUP_NODE

class ArcBoxCommand:
	POPUP_SYNCARC = (
##		(SMIL, 'Info...', INFO),
##		(SMIL, None),
		(SMIL, 'Delete', DELETE),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_SYNCARC
