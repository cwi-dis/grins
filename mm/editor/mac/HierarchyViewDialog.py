# HierarchyView dialog - Mac version
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

from ViewDialog import ViewDialog
from usercmd import *
import windowinterface
import WMEVENTS
from MenuTemplate import POPUP_HVIEW_LEAF, POPUP_HVIEW_STRUCTURE

class HierarchyViewDialog(ViewDialog):
	
	interior_popupmenu = POPUP_HVIEW_STRUCTURE
	leaf_popupmenu = POPUP_HVIEW_LEAF
	
	def __init__(self):
		ViewDialog.__init__(self, 'hview_')

	def show(self):
		if self.is_showing():
			return
		self.toplevel.showstate(self, 1)
		title = 'Structure View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1, commandlist=self.commands, canvassize = (w, h))
		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
		self.window.register(WMEVENTS.WindowExit, self.hide, None)
		self.window.register(WMEVENTS.DropFile, self.dropfile, None)

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
		
	def helpcall(self):
		import Help
		Help.givehelp('hierarchy')
