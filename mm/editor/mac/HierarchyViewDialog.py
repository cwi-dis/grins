# HierarchyView dialog - Mac version
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

from ViewDialog import ViewDialog
from usercmd import *
import windowinterface
import WMEVENTS
from MenuTemplate import POPUP_HVIEW_LEAF, POPUP_HVIEW_STRUCTURE, POPUP_HVIEW_SLIDE

class HierarchyViewDialog(ViewDialog):

	interior_popupmenu = POPUP_HVIEW_STRUCTURE
	leaf_popupmenu = POPUP_HVIEW_LEAF
	slide_popupmenu = POPUP_HVIEW_SLIDE

	def __init__(self):
		ViewDialog.__init__(self, 'hview_')

	def show(self):
		if self.is_showing():
			self.window.pop(poptop=1)
			return
		title = 'Structure View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x, y, w, h = self.last_geometry
		adornments = {'doubleclick': ATTRIBUTES}
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1, 
			commandlist=self.commands, canvassize = (w, h), adornments=adornments)
		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.register(WMEVENTS.Mouse0Release, self.mouse0release, None)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
		self.window.register(WMEVENTS.WindowExit, self.hide, None)
		self.window.register(WMEVENTS.DropFile, self.dropfile, None)
		self.window.register(WMEVENTS.DropURL, self.dropfile, None)
		self.window.register(WMEVENTS.DragFile, self.dragfile, None)

	def hide(self, *rest):
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = None
		self.new_displist = None
		
	def getparentwindow(self):
		return None

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

	def setstate(self):
		w = self.window
		w.set_toggle(THUMBNAIL, self.thumbnails)
		w.set_toggle(PLAYABLE, self.showplayability)
		w.set_toggle(TIMESCALE, self.root.showtime == 'focus')
		if self.selected_widget is None:
			w.set_toggle(LOCALTIMESCALE, 0)
			w.set_toggle(CORRECTLOCALTIMESCALE, 0)
		else:
			n = self.selected_widget.get_node()
			w.set_toggle(LOCALTIMESCALE, n.showtime == 'focus')
			w.set_toggle(CORRECTLOCALTIMESCALE, n.showtime == 'cfocus')

	def helpcall(self):
		import Help
		Help.givehelp('Hierarchy')
