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
			(ALL, 'Close', [
				(ALL, 'Close', CLOSE_WINDOW),
				]),
			(ALL, 'Edit', [
				(ALL, 'Cut', CUT),
				(ALL, 'Copy', COPY),
				(ALL, 'Paste', [
					(ALL, 'Before', PASTE_BEFORE),
					(ALL, 'After', PASTE_AFTER),
					(ALL, 'Within', PASTE_UNDER),
					]),
				(ALL, 'Delete', DELETE),
				(ALL, None),
				(ALL, 'New Node', [
					(ALL, 'Before', NEW_BEFORE),
					(ALL, 'After', NEW_AFTER),
					(ALL, 'Within', NEW_UNDER),
					(ALL, None),
					(ALL, 'Seq Parent', NEW_SEQ),
					(ALL, 'Par Parent', NEW_PAR),
					(ALL, 'Switch Parent', NEW_ALT),
					(CMIF, 'Choice Parent', NEW_CHOICE),
					]),
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
				]),
			(ALL, 'View', [
				(ALL, 'Expand/Collapse', EXPAND),
				(ALL, 'Expand All', EXPANDALL),
				(ALL, 'Collapse All', COLLAPSEALL),
				(ALL, None),
				(ALL, 'Synchronize Selection', PUSHFOCUS),
				(ALL, None),
				(ALL, 'Image Thumbnails', THUMBNAIL, 't'),
				]),
			(ALL, 'Help', [
				(ALL, 'Help...', HELP),
				]),
			],
		'toolbar': None, # no images yet...
		'close': [ CLOSE_WINDOW, ],
		}

	interior_popupmenu = (
		(ALL, 'New Node Before', NEW_BEFORE),
		(ALL, 'New Node After', NEW_AFTER),
		(ALL, 'New Node Within', NEW_UNDER),
		(ALL, None),
		(ALL, 'Cut', CUT),
		(ALL, 'Copy', COPY),
		(ALL, 'Delete', DELETE),
		(ALL, None),
		(ALL, 'Paste Before', PASTE_BEFORE),
		(ALL, 'Paste After', PASTE_AFTER),
		(ALL, 'Paste Within', PASTE_UNDER),
		(ALL, None),
		(ALL, 'Play Node', PLAYNODE),
		(ALL, 'Play from Node', PLAYFROM),
		(ALL, None),
		(ALL, 'Expand/Collapse', EXPAND),
		(ALL, 'Expand All', EXPANDALL),
		(ALL, 'Collapse All', COLLAPSEALL),
		(ALL, None),
		(ALL, 'Create Simple Anchor', CREATEANCHOR),
		(ALL, 'Finish Hyperlink', FINISH_LINK),
		(ALL, None),
		(ALL, 'Info...', INFO),
		(ALL, 'Properties...', ATTRIBUTES),
		(ALL, 'Anchors...', ANCHORS),
		)

	leaf_popupmenu = (
		(ALL, 'New Node Before', NEW_BEFORE),
		(ALL, 'New Node After', NEW_AFTER),
		(ALL, None),
		(ALL, 'Cut', CUT),
		(ALL, 'Copy', COPY),
		(ALL, 'Delete', DELETE),
		(ALL, None),
		(ALL, 'Paste Before', PASTE_BEFORE),
		(ALL, 'Paste After', PASTE_AFTER),
		(ALL, None),
		(ALL, 'Play Node', PLAYNODE),
		(ALL, 'Play from Node', PLAYFROM),
		(ALL, None),
		(ALL, 'Create Simple Anchor', CREATEANCHOR),
		(ALL, 'Finish Hyperlink', FINISH_LINK),
		(ALL, None),
		(ALL, 'Info...', INFO),
		(ALL, 'Properties...', ATTRIBUTES),
		(ALL, 'Anchors...', ANCHORS),
		(ALL, 'Edit Content...', CONTENT),
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
		self.window.setpopupmenu(template, SMIL)
