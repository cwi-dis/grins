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
				('New channel...', NEW_CHANNEL),
				('Move channel', MOVE_CHANNEL),
				('Copy channel', COPY_CHANNEL),
				None,
				('Toggle channel state', TOGGLE_ONOFF),
				]),
			('Play', [
				('Play node', PLAYNODE),
				('Play from node', PLAYFROM),
				]),
			('Tools', [
				('Info...', INFO),
				('Properties...', ATTRIBUTES),
				('Anchors...', ANCHORS),
				('Edit content...', CONTENT),
				None,
				('Create simple anchor', CREATEANCHOR),
				('Finish hyperlink to focus', FINISH_LINK),
				('Create sync arc from focus...', FINISH_ARC),
				]),
			('Navigate', [
				('Level of detail', [
					('More horizontal detail', CANVAS_WIDTH),
					('More vertical detail', CANVAS_HEIGHT),
					('Fit in window', CANVAS_RESET),
					]),
				None,
				('Send focus to other views', PUSHFOCUS),
				('Select sync arc', SYNCARCS),
				None,
				(('Show unused channels',
				  'Hide unused channels'),
				 TOGGLE_UNUSED, 't'),
				(('Show sync arcs', 'Hide sync arcs'),
				 TOGGLE_ARCS, 't'),
				(('Show thumbnails', 'Hide thumbnails'),
				 THUMBNAIL, 't'),
				(('Show bandwidth strip', 'Hide bandwidth strip'),
				 TOGGLE_BWSTRIP, 't'),
				None,
				('Highlight in player', HIGHLIGHT),
				('Unhighlight in player', UNHIGHLIGHT),
				('Minidocument navigation', [
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
		('Create new channel', NEW_CHANNEL),
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
		('Toggle channel state', TOGGLE_ONOFF),
		('Properties...', ATTRIBUTES),
		None,
		('Delete', DELETE),
		None,
		('Move channel', MOVE_CHANNEL),
		('Copy channel', COPY_CHANNEL),
		)

	def __init__(self):
		self.popupmenu = self.POPUP_CHANNEL

class NodeBoxCommand:
	POPUP_NODE = (
		('Play node', PLAYNODE),
		('Play from node', PLAYFROM),
		None,
		('Create simple anchor', CREATEANCHOR),
		('Finish hyperlink to focus', FINISH_LINK),
		('Create sync arc from focus...', FINISH_ARC),
		None,
		('Info...', INFO),
		('Properties...', ATTRIBUTES),
		('Anchors...', ANCHORS),
		('Edit content...', CONTENT),
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
