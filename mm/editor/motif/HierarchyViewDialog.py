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
			      'L': FINISH_LINK,
			      'f': PUSHFOCUS,
			      'z': ZOOMOUT,
			      '.': ZOOMHERE,
			      'Z': ZOOMIN,
			      },
		'menubar': [
			('Close', [
				('Close', CLOSE_WINDOW),
				]),
			('Edit', [
				('New node', [
					('Before focus', NEW_BEFORE),
					('After focus', NEW_AFTER),
					('Under focus', NEW_UNDER),
					('Above focus', [
						('Sequential', NEW_SEQ),
						('Parallel', NEW_PAR),
						('Choice', NEW_CHOICE),
						('Alternate', NEW_ALT),
						]),
					]),
				('Delete focus', DELETE),
				None,
				('Cut focus', CUT),
				('Copy focus', COPY),
				('Paste', [
					('Before focus', PASTE_BEFORE),
					('After focus', PASTE_AFTER),
					('Under focus', PASTE_UNDER),
					])
				]),
			('Node', [
				('Play node', PLAYNODE),
				('Play from node', PLAYFROM),
				None,
				('Node info...', INFO),
				('Node attr...', ATTRIBUTES),
				('Edit contents...', CONTENT),
				('Edit anchors...', ANCHORS),
				None,
				('Finish hyperlink...', FINISH_LINK)
				]),
			('Focus', [
				('Synchronize', PUSHFOCUS),
				None,
				('Zoom out', ZOOMOUT),
				('Zoom here', ZOOMHERE),
				('Zoom in', ZOOMIN)
				]),
			('View', [
				('Double height of canvas', CANVAS_HEIGHT),
				('Double width of canvas', CANVAS_WIDTH),
				('Reset canvas size', CANVAS_RESET),
				(('Show thumbnails', 'Hide thumbnails'),
				 THUMBNAIL, 't'),
				]),
			('Help', [
				('Help...', HELP),
				]),
			],
		'toolbar': None, # no images yet...
		'close': [ CLOSE_WINDOW, ],
		}

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
		title = 'Hierarchy View (%s)' % self.toplevel.basename
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title,
				pixmap = 1, adornments = self.adornments,
				canvassize = (w, h),
				commandlist = self.commands)
		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)

	def hide(self, *rest):
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = None
		self.new_displist = None

	def fixtitle(self):
		if self.is_showing():
			title = 'Hierarchy View (' + self.toplevel.basename + ')'
			self.window.settitle(title)

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)

	def setcommands(self, commandlist):
		self.window.set_commandlist(commandlist)
