# HierarchyView dialog - Version for standard windowinterface
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
from usercmd import *

class HierarchyViewDialog(ViewDialog):
	adornments = {
		'shortcuts': {'d': DELETE,
			      'x': CUT,
			      'c': COPY,
			      'p': PLAYNODE,
			      'G': PLAYFROM,
			      'i': INFO,
			      'a': ATTRIBUTES,
			      'e': CONTENT,
			      't': ANCHORS,
			      'T': CREATEANCHOR,
			      'L': FINISH_LINK,
			      'f': PUSHFOCUS,
			      },
		'menubar': [
			('Close', [
				('Close', CLOSE_WINDOW),
				]),
			('Edit', [
				('Cut', CUT),
				('Copy', COPY),
				('Paste', [
					('Before', PASTE_BEFORE),
					('After', PASTE_AFTER),
					('Within', PASTE_UNDER),
					]),
				('Delete', DELETE),
				None,
				('New Node', [
					('Before', NEW_BEFORE),
					('After', NEW_AFTER),
					('Within', NEW_UNDER),
					None,
					('Seq Parent', NEW_SEQ),
					('Par Parent', NEW_PAR),
					('Switch Parent', NEW_ALT),
					('Choice Parent', NEW_CHOICE),
					]),
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
				]),
			('View', [
				('Expand/Collapse', EXPAND),
				('Expand All', EXPANDALL),
				('Collapse All', COLLAPSEALL),
				None,
				('Synchronize Selection', PUSHFOCUS),
				None,
				('Image Thumbnails', THUMBNAIL, 't'),
				]),
			('Help', [
				('Help...', HELP),
				]),
			],
		'toolbar': None, # no images yet...
		'close': [ CLOSE_WINDOW, ],
		}

	interior_popupmenu = (
		('New Node Before', NEW_BEFORE),
		('New Node After', NEW_AFTER),
		('New Node Within', NEW_UNDER),
		None,
		('Cut', CUT),
		('Copy', COPY),
		('Delete', DELETE),
		None,
		('Paste Before', PASTE_BEFORE),
		('Paste After', PASTE_AFTER),
		('Paste Within', PASTE_UNDER),
		None,
		('Play Node', PLAYNODE),
		('Play from Node', PLAYFROM),
		None,
		('Expand/Collapse', EXPAND),
		('Expand All', EXPANDALL),
		('Collapse All', COLLAPSEALL),
		None,
		('Create Simple Anchor', CREATEANCHOR),
		('Finish Hyperlink', FINISH_LINK),
		None,
		('Info...', INFO),
		('Properties...', ATTRIBUTES),
		('Anchors...', ANCHORS),
		)

	leaf_popupmenu = (
		('New Node Before', NEW_BEFORE),
		('New Node After', NEW_AFTER),
		None,
		('Cut', CUT),
		('Copy', COPY),
		('Delete', DELETE),
		None,
		('Paste Before', PASTE_BEFORE),
		('Paste After', PASTE_AFTER),
		None,
		('Play Node', PLAYNODE),
		('Play from Node', PLAYFROM),
		None,
		('Create Simple Anchor', CREATEANCHOR),
		('Finish Hyperlink', FINISH_LINK),
		None,
		('Info...', INFO),
		('Properties...', ATTRIBUTES),
		('Anchors...', ANCHORS),
		('Edit Content...', CONTENT),
		)

	def __init__(self):
		ViewDialog.__init__(self, 'hview_')

	# transf from HierarchyView
	def helpcall(self):
		import Help
		Help.givehelp(self.window._hWnd,'Hierarchy_view')

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Structure View (%s)' % self.toplevel.basename
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title,
				pixmap = 1, adornments = self.adornments,
				canvassize = (w, h),
				commandlist = self.commands)
		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
		self.window.register(WMEVENTS.DropFile, self.dropfile, None)
		self.window.register(WMEVENTS.DropURL, self.dropfile, None)

	def hide(self, *rest):
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = None
		self.new_displist = None

	def fixtitle(self):
		if self.is_showing():
			title = 'Structure View (' + self.toplevel.basename + ')'
			self.window.settitle(title)

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)

	def setcommands(self, commandlist):
		self.window.set_commandlist(commandlist)

	def setpopup(self, template):
		self.window.setpopupmenu(template)
