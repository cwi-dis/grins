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
			'L': FINISH_LINK,
			'e': CONTENT,
			't': ANCHORS,
			},
		'menubar': [
			('Close', [
				('Close', CLOSE_WINDOW),
				]),
			('Edit', [
				('Undo', UNDO),
				('Delete', DELETE),
				('New channel...', NEW_CHANNEL),
				('Move channel', MOVE_CHANNEL),
				('Copy channel', COPY_CHANNEL),
				None,
				('Toggle on/off', TOGGLE_ONOFF),
				]),
			('Focus', [
				('Synchronize', PUSHFOCUS),
				None,
				('Play node', PLAYNODE),
				('Play from node', PLAYFROM),
				None,
				('Show info...', INFO),
				('Show attributes...', ATTRIBUTES),
				('Show anchors...', ANCHORS),
				('Edit content...', CONTENT),
				None,
				('Finish hyperlink to focus...', FINISH_LINK),
				('Finish syncarc from focus...', FINISH_ARC),
				None,
				('Select sync arc', SYNCARCS),
				]),
			('View', [
				('Toggle unused channels', TOGGLE_UNUSED),
				None,
				('Minidocument', [
					('Next', NEXT_MINIDOC),
					('Previous', PREV_MINIDOC),
					('Ancestors', ANCESTORS),
					('Siblings', SIBLINGS),
					('Descendants', DESCENDANTS),
					]),
				None,
				('Highlight', HIGHLIGHT),
				('Unhighlight', UNHIGHLIGHT),
				None,
				('Double height of canvas', CANVAS_HEIGHT),
				('Double width of canvas', CANVAS_WIDTH),
				('Reset canvas size', CANVAS_RESET),
				None,
				('Show thumbnails', THUMBNAIL, 't'),
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
		if self.waiting:
			self.window.setcursor('watch')
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)

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

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)

class GOCommand:
	def __init__(self):
		pass

	def helpcall(self):
		pass


class ChannelBoxCommand:
	def __init__(self):
		pass

class NodeBoxCommand:
	def __init__(self, mother, node):
		pass

class ArcBoxCommand:
	def __init__(self):
		pass
