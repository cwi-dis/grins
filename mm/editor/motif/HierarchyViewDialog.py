# HierarchyView dialog - Version for standard windowinterface
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
from usercmd import *
from flags import *

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
			(LIGHT, 'Close', [
				(LIGHT, 'Close', CLOSE_WINDOW),
				]),
			(LIGHT, 'Edit', [
				(LIGHT, 'Cut', CUT),
				(LIGHT, 'Copy', COPY),
				(LIGHT, 'Paste', [
					(LIGHT, 'Before', PASTE_BEFORE),
					(LIGHT, 'After', PASTE_AFTER),
					(LIGHT, 'Within', PASTE_UNDER),
					]),
				(LIGHT, 'Delete', DELETE),
				(LIGHT, None),
				(LIGHT, 'New Node', [
					(LIGHT, 'Before', NEW_BEFORE),
					(LIGHT, 'After', NEW_AFTER),
					(LIGHT, 'Within', NEW_UNDER),
					(LIGHT, None),
					(LIGHT, 'Seq Parent', NEW_SEQ),
					(LIGHT, 'Par Parent', NEW_PAR),
					(LIGHT, 'Switch Parent', NEW_ALT),
					(CMIF, 'Choice Parent', NEW_CHOICE),
					]),
				(LIGHT, None),
				(LIGHT, 'Info...', INFO),
				(LIGHT, 'Properties...', ATTRIBUTES),
				(LIGHT, 'Edit Content...', CONTENT),
				]),
			(LIGHT, 'Play', [
				(LIGHT, 'Play Node', PLAYNODE),
				(LIGHT, 'Play from Node', PLAYFROM),
				]),
			(LIGHT, 'Linking', [
				(LIGHT, 'Create Simple Anchor', CREATEANCHOR),
				(LIGHT, 'Finish Hyperlink to Selection', FINISH_LINK),
				(LIGHT, 'Anchors...', ANCHORS),
				]),
			(LIGHT, 'View', [
				(LIGHT, 'Expand/Collapse', EXPAND),
				(LIGHT, 'Expand All', EXPANDALL),
				(LIGHT, 'Collapse All', COLLAPSEALL),
				(SMIL, None),
				(SMIL, 'Synchronize Selection', PUSHFOCUS),
				(LIGHT, None),
				(LIGHT, 'Image Thumbnails', THUMBNAIL, 't'),
				(LIGHT, 'Show Playable', PLAYABLE, 't'),
				(LIGHT, 'Show Durations', TIMESCALE, 't'),
				]),
			(LIGHT, 'Help', [
				(LIGHT, 'Help...', HELP),
				]),
			],
		'toolbar': None, # no images yet...
		'close': [ CLOSE_WINDOW, ],
		}

	interior_popupmenu = (
		(LIGHT, 'New Node Before', NEW_BEFORE),
		(LIGHT, 'New Node After', NEW_AFTER),
		(LIGHT, 'New Node Within', NEW_UNDER),
		(LIGHT, None),
		(LIGHT, 'Cut', CUT),
		(LIGHT, 'Copy', COPY),
		(LIGHT, 'Delete', DELETE),
		(LIGHT, None),
		(LIGHT, 'Paste Before', PASTE_BEFORE),
		(LIGHT, 'Paste After', PASTE_AFTER),
		(LIGHT, 'Paste Within', PASTE_UNDER),
		(LIGHT, None),
		(LIGHT, 'Play Node', PLAYNODE),
		(LIGHT, 'Play from Node', PLAYFROM),
		(LIGHT, None),
		(LIGHT, 'Expand/Collapse', EXPAND),
		(LIGHT, 'Expand All', EXPANDALL),
		(LIGHT, 'Collapse All', COLLAPSEALL),
		(LIGHT, None),
		(LIGHT, 'Create Simple Anchor', CREATEANCHOR),
		(LIGHT, 'Finish Hyperlink', FINISH_LINK),
		(LIGHT, None),
		(LIGHT, 'Info...', INFO),
		(LIGHT, 'Properties...', ATTRIBUTES),
		(LIGHT, 'Anchors...', ANCHORS),
		)

	leaf_popupmenu = (
		(LIGHT, 'New Node Before', NEW_BEFORE),
		(LIGHT, 'New Node After', NEW_AFTER),
		(LIGHT, None),
		(LIGHT, 'Cut', CUT),
		(LIGHT, 'Copy', COPY),
		(LIGHT, 'Delete', DELETE),
		(LIGHT, None),
		(LIGHT, 'Paste Before', PASTE_BEFORE),
		(LIGHT, 'Paste After', PASTE_AFTER),
		(LIGHT, None),
		(LIGHT, 'Play Node', PLAYNODE),
		(LIGHT, 'Play from Node', PLAYFROM),
		(LIGHT, None),
		(LIGHT, 'Create Simple Anchor', CREATEANCHOR),
		(LIGHT, 'Finish Hyperlink', FINISH_LINK),
		(LIGHT, None),
		(LIGHT, 'Info...', INFO),
		(LIGHT, 'Properties...', ATTRIBUTES),
		(LIGHT, 'Anchors...', ANCHORS),
		(LIGHT, 'Edit Content...', CONTENT),
		)

	def __init__(self):
		ViewDialog.__init__(self, 'hview_')

	# transf from HierarchyView
	def helpcall(self):
		import Help
		Help.givehelp(self.window._hWnd,'Hierarchy_view')

	def show(self):
		if self.is_showing():
			self.window.pop(poptop = 1)
			return
		title = 'Structure View (%s)' % self.toplevel.basename
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.adornments['flags'] = curflags()
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
		self.window.setpopupmenu(template, curflags())
