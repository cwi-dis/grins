from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
import MMAttrdefs
from usercmd import *

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
			('Close', [
				('Close', CLOSE_WINDOW),
				]),
			('Edit', [
				('Delete', DELETE),
				None,
				('New Channel...', NEW_CHANNEL),
				None,
				('Move Channel', MOVE_CHANNEL),
				('Copy Channel', COPY_CHANNEL),
				('Toggle Channel State', TOGGLE_ONOFF),
				None,
				('Info...', INFO),
				('Properties...', ATTRIBUTES),
				('Edit Content...', CONTENT),
				]),
			('Play', [
				('Play Node', PLAYNODE),
				('Play from Node', PLAYFROM),
				]),
			('Linking', [
				('Create Simple Anchor', CREATEANCHOR),
				('Finish Hyperlink to Selection', FINISH_LINK),
				('Anchors...', ANCHORS),
				None,
				('Create Sync Arc from Selection...', FINISH_ARC),
				('Select Sync Arc', SYNCARCS),
				]),
			('View', [
				('Zoom In', CANVAS_WIDTH),
				('Fit in Window', CANVAS_RESET),
				None,
				('Synchronize Selection', PUSHFOCUS),
				None,
				('Unused Channels', TOGGLE_UNUSED, 't'),
				('Sync Arcs', TOGGLE_ARCS, 't'),
				('Image Thumbnails', THUMBNAIL, 't'),
				('Bandwidth Usage', TOGGLE_BWSTRIP, 't'),
				None,
				('Highlight in Player', HIGHLIGHT),
				('Unhighlight in Player', UNHIGHLIGHT),
				('Minidocument Navigation', [
					('Next', NEXT_MINIDOC),
					('Previous', PREV_MINIDOC),
					('Ancestors', ANCESTORS),
					('Siblings', SIBLINGS),
					('Descendants', DESCENDANTS),
					]),
##				('Layout navigation', LAYOUTS),
				]),
			('Help', [
				('Help...', HELP),
				]),
			],
		'toolbar': None, # no images yet...
		'close': [ CLOSE_WINDOW, ],
		}

	def __init__(self):
		ViewDialog.__init__(self, 'cview_')

	def show(self, title):
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1, adornments = self.adornments, canvassize = (w, h))
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
		self.window.setpopupmenu(menutemplate)

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)

class GOCommand:
	POPUP_NONE = (
		('New Channel...', NEW_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_NONE

	def helpcall(self):
		pass

class BandwidthStripBoxCommand:
	POPUP_BWSTRIP = (
		("14k4", BANDWIDTH_14K4),
		("28k8", BANDWIDTH_28K8),
		("ISDN", BANDWIDTH_ISDN),
		("T1 (1 Mbps)", BANDWIDTH_T1),
		("LAN (10 Mbps)", BANDWIDTH_LAN),
		None,
		("Other...", BANDWIDTH_OTHER),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_BWSTRIP

class ChannelBoxCommand:
	POPUP_CHANNEL = (
##		('Toggle Channel State', TOGGLE_ONOFF),
		('Properties...', ATTRIBUTES),
		None,
		('Delete', DELETE),
		None,
		('Move Channel', MOVE_CHANNEL),
		('Copy Channel', COPY_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_CHANNEL

class NodeBoxCommand:
	POPUP_NODE = (
		('Play Node', PLAYNODE),
		('Play from Node', PLAYFROM),
		None,
		('Create Simple Anchor', CREATEANCHOR),
		('Finish Hyperlink to Selection', FINISH_LINK),
		('Create Sync Arc from Selection...', FINISH_ARC),
		None,
		('Info...', INFO),
		('Properties...', ATTRIBUTES),
		('Anchors...', ANCHORS),
		('Edit Content...', CONTENT),
		)

	def __init__(self, mother, node):
		self.popupmenu = self.POPUP_NODE

class ArcBoxCommand:
	POPUP_SYNCARC = (
		('Info...', INFO),
		None,
		('Delete', DELETE),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_SYNCARC
