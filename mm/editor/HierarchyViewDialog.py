# HierarchyView dialog - Version for standard windowinterface
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
import Help

class HierarchyViewDialog(ViewDialog):

	def __init__(self):
		ViewDialog.__init__(self, 'hview_')
		self.menu = [
			('Canvas', [
				(None, 'Double height',
				 (self.canvascall,
				  (windowinterface.DOUBLE_HEIGHT,))),
				(None, 'Double width',
				 (self.canvascall,
				  (windowinterface.DOUBLE_WIDTH,))),
				(None, 'Reset',
				 (self.canvascall,
				  (windowinterface.RESET_CANVAS,))),
				]),
			('Edit', [
				(None, 'New node', [
					(None, 'Before focus',
					 (self.createbeforecall, ())),
					(None, 'After focus',
					 (self.createaftercall, ())),
					(None, 'Under focus',
					 (self.createundercall, ())),
					(None, 'Above focus', [
						(None, 'Sequential',
						 (self.createseqcall, ())),
						(None, 'Parallel',
						 (self.createparcall, ())),
						(None, 'Choice',
						 (self.createbagcall, ())),
						(None, 'Alternate',
						 (self.createaltcall, ())),
						]),
					]),
				('d', 'Delete focus', (self.deletecall, ())),
				None,
				('x', 'Cut focus', (self.cutcall, ())),
				('c', 'Copy focus', (self.copycall, ())),
				(None, 'Paste', [
					(None, 'Before focus',
					 (self.pastebeforecall, ())),
					(None, 'After focus',
					 (self.pasteaftercall, ())),
					(None, 'Under focus',
					 (self.pasteundercall, ())),
					])
				]),
			('Node', [
				('p', 'Play node', (self.playcall, ())),
				('G', 'Play from node', (self.playfromcall, ())),
				None,
				('i', 'Node info...', (self.infocall, ())),
				('a', 'Node attr...', (self.attrcall, ())),
				('e', 'Edit contents...', (self.editcall, ())),
				('t', 'Edit anchors...', (self.anchorcall, ())),
				None,
				('L', 'Finish hyperlink...', (self.hyperlinkcall, ()))
				]),
			('Focus', [
				('f', 'Push focus', (self.focuscall, ())),
				('z', 'Zoom out', (self.zoomoutcall, ())),
				('.', 'Zoom here', (self.zoomherecall, ())),
				('Z', 'Zoom in', (self.zoomincall, ()))
				]),
			]
		if Help.hashelp():
			self.menu.append(('Help', [
				('h', 'Help...', (self.helpcall, ()))]))

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Hierarchy View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1, menubar=self.menu, canvassize = (w, h))
		if self.waiting:
			self.window.setcursor('watch')
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
		self.window.register(WMEVENTS.WindowExit, self.hide, None)

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

	def helpcall(self):
		Help.givehelp('Hierarchy_view')
