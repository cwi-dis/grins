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
			(FLAG_PRO, 'Close', [
				(FLAG_PRO, 'Close', CLOSE_WINDOW),
				]),
			(FLAG_PRO, 'Edit', [
				(FLAG_PRO, 'Delete', DELETE),
				(FLAG_PRO, None),
				(FLAG_PRO, 'New Channel...', NEW_CHANNEL),
				(FLAG_PRO, None),
				(FLAG_PRO, 'Move Channel', MOVE_CHANNEL),
				(FLAG_PRO, 'Copy Channel', COPY_CHANNEL),
				(FLAG_CMIF, 'Toggle Channel State', TOGGLE_ONOFF),
				(FLAG_PRO, None),
##				(FLAG_PRO, 'Info...', INFO),
				(FLAG_PRO, 'Properties...', ATTRIBUTES),
				(FLAG_PRO, 'Edit Content...', CONTENT),
				]),
			(FLAG_PRO, 'Play', [
				(FLAG_PRO, 'Play Node', PLAYNODE),
				(FLAG_PRO, 'Play from Node', PLAYFROM),
				]),
			(FLAG_PRO, 'Linking', [
				(FLAG_PRO, 'Create Simple Anchor', CREATEANCHOR),
				(FLAG_PRO, 'Finish Hyperlink to Selection', FINISH_LINK),
				(FLAG_PRO, 'Anchors...', ANCHORS),
				(FLAG_PRO, None),
				(FLAG_PRO, 'Create Sync Arc from Selection...', FINISH_ARC),
				(FLAG_PRO, 'Select Sync Arc', SYNCARCS),
				]),
			(FLAG_PRO, 'View', [
				(FLAG_PRO, 'Zoom In', CANVAS_WIDTH),
				(FLAG_PRO, 'Fit in Window', CANVAS_RESET),
				(FLAG_PRO, None),
				(FLAG_PRO, 'Synchronize Selection', PUSHFOCUS),
				(FLAG_PRO, None),
				(FLAG_PRO, 'Unused Channels', TOGGLE_UNUSED, 't'),
				(FLAG_PRO, 'Sync Arcs', TOGGLE_ARCS, 't'),
				(FLAG_PRO, 'Image Thumbnails', THUMBNAIL, 't'),
				(FLAG_PRO, 'Bandwidth Usage', TOGGLE_BWSTRIP, 't'),
				(FLAG_CMIF, None),
##				(FLAG_PRO, 'Layout navigation', LAYOUTS),
				]),
			(FLAG_PRO, 'Help', [
				(FLAG_PRO, 'Help...', HELP),
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
		self.window.set_dynamiclist(SYNCARCS, (self.focus and self.focus.arcmenu) or [])
##		self.window.set_dynamiclist(LAYOUTS, self.layouts)

	def setpopup(self, menutemplate):
		self.window.setpopupmenu(menutemplate, curflags())

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)

class GOCommand:
	POPUP_NONE = (
		(FLAG_PRO, 'New Channel...', NEW_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_NONE

	def helpcall(self):
		pass

class BandwidthStripBoxCommand:
	POPUP_BWSTRIP = (
		(FLAG_PRO, "14k4", BANDWIDTH_14K4),
		(FLAG_PRO, "28k8", BANDWIDTH_28K8),
		(FLAG_PRO, "ISDN", BANDWIDTH_ISDN),
		(FLAG_PRO, "T1 (1 Mbps)", BANDWIDTH_T1),
		(FLAG_PRO, "LAN (10 Mbps)", BANDWIDTH_LAN),
		(FLAG_PRO, None),
		(FLAG_PRO, "Other...", BANDWIDTH_OTHER),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_BWSTRIP

class ChannelBoxCommand:
	POPUP_CHANNEL = (
##		(FLAG_PRO, 'Toggle Channel State', TOGGLE_ONOFF),
		(FLAG_PRO, 'Properties...', ATTRIBUTES),
		(FLAG_PRO, None),
		(FLAG_PRO, 'Delete', DELETE),
		(FLAG_PRO, None),
		(FLAG_PRO, 'Move Channel', MOVE_CHANNEL),
		(FLAG_PRO, 'Copy Channel', COPY_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_CHANNEL

class NodeBoxCommand:
	POPUP_NODE = (
		(FLAG_PRO, 'Play Node', PLAYNODE),
		(FLAG_PRO, 'Play from Node', PLAYFROM),
		(FLAG_PRO, None),
		(FLAG_PRO, 'Create Simple Anchor', CREATEANCHOR),
		(FLAG_PRO, 'Finish Hyperlink to Selection', FINISH_LINK),
		(FLAG_PRO, 'Create Sync Arc from Selection...', FINISH_ARC),
		(FLAG_PRO, None),
##		(FLAG_PRO, 'Info...', INFO),
		(FLAG_PRO, 'Properties...', ATTRIBUTES),
		(FLAG_PRO, 'Anchors...', ANCHORS),
		(FLAG_PRO, 'Edit Content...', CONTENT),
		)

	def __init__(self, mother, node):
		self.popupmenu = self.POPUP_NODE

class ArcBoxCommand:
	POPUP_SYNCARC = (
		(FLAG_PRO, 'Properties...', ATTRIBUTES),
		(FLAG_PRO, None),
		(FLAG_PRO, 'Delete', DELETE),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_SYNCARC
