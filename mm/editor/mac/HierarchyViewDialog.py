# HierarchyView dialog - Mac version
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

from ViewDialog import ViewDialog
import UserCmd
import windowinterface
import WMEVENTS

class HierarchyViewDialog(ViewDialog):

	def __init__(self):
		ViewDialog.__init__(self, 'hview_')
		self.commands = [
			(UserCmd.CANVAS_HEIGHT, (self.canvascall,
					(windowinterface.DOUBLE_HEIGHT,))),
			(UserCmd.CANVAS_WIDTH, (self.canvascall,
					(windowinterface.DOUBLE_WIDTH,))),
			(UserCmd.CANVAS_RESET, (self.canvascall,
					(windowinterface.RESET_CANVAS,))),

			(UserCmd.NEW_BEFORE, (self.createbeforecall, ())),
			(UserCmd.NEW_AFTER, (self.createaftercall, ())),
			(UserCmd.NEW_UNDER, (self.createundercall, ())),
			(UserCmd.NEW_SEQ, (self.createseqcall, ())),
			(UserCmd.NEW_PAR, (self.createparcall, ())),
			(UserCmd.NEW_CHOICE, (self.createbagcall, ())),
			(UserCmd.NEW_ALT, (self.createaltcall, ())),

			(UserCmd.DELETE, (self.deletecall, ())),

			(UserCmd.CUT, (self.cutcall, ())),
			(UserCmd.COPY, (self.copycall, ())),
			(UserCmd.PASTE_BEFORE, (self.pastebeforecall, ())),
			(UserCmd.PASTE_AFTER, (self.pasteaftercall, ())),
			(UserCmd.PASTE_UNDER, (self.pasteundercall, ())),

			(UserCmd.PLAYNODE, (self.playcall, ())),
			(UserCmd.PLAYFROM, (self.playfromcall, ())),
			(UserCmd.INFO, (self.infocall, ())),
			(UserCmd.ATTRIBUTES, (self.attrcall, ())),
			(UserCmd.CONTENT, (self.editcall, ())),
			(UserCmd.ANCHORS, (self.anchorcall, ())),
			(UserCmd.FINISH_LINK, (self.hyperlinkcall, ())),

			(UserCmd.PUSHFOCUS, (self.focuscall, ())),
			(UserCmd.ZOOMOUT, (self.zoomoutcall, ())),
			(UserCmd.ZOOMIN, (self.zoomherecall, ())),
			(UserCmd.ZOOMHERE, (self.zoomincall, ()))]

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Hierarchy View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1, menubar=self.commands, canvassize = (w, h))
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

