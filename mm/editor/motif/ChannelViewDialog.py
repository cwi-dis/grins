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
			'i': INFO,
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
			(ALL, 'Close', [
				(ALL, 'Close', CLOSE_WINDOW),
				]),
			(ALL, 'Edit', [
				(ALL, 'Delete', DELETE),
				(ALL, None),
				(ALL, 'New Channel...', NEW_CHANNEL),
				(ALL, None),
				(ALL, 'Move Channel', MOVE_CHANNEL),
				(ALL, 'Copy Channel', COPY_CHANNEL),
				(CMIF, 'Toggle Channel State', TOGGLE_ONOFF),
				(ALL, None),
				(ALL, 'Info...', INFO),
				(ALL, 'Properties...', ATTRIBUTES),
				(ALL, 'Edit Content...', CONTENT),
				]),
			(ALL, 'Play', [
				(ALL, 'Play Node', PLAYNODE),
				(ALL, 'Play from Node', PLAYFROM),
				]),
			(ALL, 'Linking', [
				(ALL, 'Create Simple Anchor', CREATEANCHOR),
				(ALL, 'Finish Hyperlink to Selection', FINISH_LINK),
				(ALL, 'Anchors...', ANCHORS),
				(ALL, None),
				(ALL, 'Create Sync Arc from Selection...', FINISH_ARC),
				(ALL, 'Select Sync Arc', SYNCARCS),
				]),
			(ALL, 'View', [
				(ALL, 'Zoom In', CANVAS_WIDTH),
				(ALL, 'Fit in Window', CANVAS_RESET),
				(ALL, None),
				(ALL, 'Synchronize Selection', PUSHFOCUS),
				(ALL, None),
				(ALL, 'Unused Channels', TOGGLE_UNUSED, 't'),
				(ALL, 'Sync Arcs', TOGGLE_ARCS, 't'),
				(ALL, 'Image Thumbnails', THUMBNAIL, 't'),
				(ALL, 'Bandwidth Usage', TOGGLE_BWSTRIP, 't'),
				(CMIF, None),
				(CMIF, 'Minidocument Navigation', [
					(CMIF, 'Next', NEXT_MINIDOC),
					(CMIF, 'Previous', PREV_MINIDOC),
					(CMIF, 'Ancestors', ANCESTORS),
					(CMIF, 'Siblings', SIBLINGS),
					(CMIF, 'Descendants', DESCENDANTS),
					]),
##				(ALL, 'Layout navigation', LAYOUTS),
				]),
			(ALL, 'Help', [
				(ALL, 'Help...', HELP),
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
		(ALL, 'New Channel...', NEW_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_NONE

	def helpcall(self):
		pass

class BandwidthStripBoxCommand:
	POPUP_BWSTRIP = (
		(ALL, "14k4", BANDWIDTH_14K4),
		(ALL, "28k8", BANDWIDTH_28K8),
		(ALL, "ISDN", BANDWIDTH_ISDN),
		(ALL, "T1 (1 Mbps)", BANDWIDTH_T1),
		(ALL, "LAN (10 Mbps)", BANDWIDTH_LAN),
		(ALL, None),
		(ALL, "Other...", BANDWIDTH_OTHER),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_BWSTRIP

class ChannelBoxCommand:
	POPUP_CHANNEL = (
##		(ALL, 'Toggle Channel State', TOGGLE_ONOFF),
		(ALL, 'Properties...', ATTRIBUTES),
		(ALL, None),
		(ALL, 'Delete', DELETE),
		(ALL, None),
		(ALL, 'Move Channel', MOVE_CHANNEL),
		(ALL, 'Copy Channel', COPY_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_CHANNEL

class NodeBoxCommand:
	POPUP_NODE = (
		(ALL, 'Play Node', PLAYNODE),
		(ALL, 'Play from Node', PLAYFROM),
		(ALL, None),
		(ALL, 'Create Simple Anchor', CREATEANCHOR),
		(ALL, 'Finish Hyperlink to Selection', FINISH_LINK),
		(ALL, 'Create Sync Arc from Selection...', FINISH_ARC),
		(ALL, None),
		(ALL, 'Info...', INFO),
		(ALL, 'Properties...', ATTRIBUTES),
		(ALL, 'Anchors...', ANCHORS),
		(ALL, 'Edit Content...', CONTENT),
		)

	def __init__(self, mother, node):
		self.popupmenu = self.POPUP_NODE

class ArcBoxCommand:
	POPUP_SYNCARC = (
		(ALL, 'Info...', INFO),
		(ALL, None),
		(ALL, 'Delete', DELETE),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_SYNCARC
