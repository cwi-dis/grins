__version__ = "$Id$"

# HierarchyView dialog - Version for standard windowinterface
# XXXX Note: the separation isn't correct: there are still things in HierarchyView
# that really belong here...

""" @win32doc|HierarchyViewDialog
This class represents the interface between the HierarchyView platform independent
class and its implementation class _HierarchyView in lib/win32/_HierarchyView.py which 
implements the actual view.

"""

from ViewDialog import ViewDialog
import WMEVENTS
from usercmd import *
from MenuTemplate import POPUP_HVIEW_LEAF, POPUP_HVIEW_SLIDE, POPUP_HVIEW_STRUCTURE

class HierarchyViewDialog(ViewDialog):
	adornments = {}
	interior_popupmenu = POPUP_HVIEW_STRUCTURE
	leaf_popupmenu = POPUP_HVIEW_LEAF
	slide_popupmenu = POPUP_HVIEW_SLIDE

	def __init__(self):
		ViewDialog.__init__(self, 'hview_')
	
	def show(self):
		if self.is_showing():
			self.window.pop(poptop=1)
			return
		title = 'Structure View (%s)' % self.toplevel.basename
		self.load_geometry()
		x, y, w, h = self.last_geometry
		toplevel_window=self.toplevel.window
		self.window = toplevel_window.newview(x, y, w, h, title,
				adornments = self.adornments,
				canvassize = (w, h),
				commandlist = self.commands,strid='hview_')

		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
		self.window.register(WMEVENTS.PasteFile, self.dropfile, None)
		self.window.register(WMEVENTS.DragFile, self.dropeffect, None)
		self.window.register(WMEVENTS.DropFile, self.dropfile, None)

	def getparentwindow(self):
		# Used by machine-independent code to pass as parent
		# parameter to dialogs
		##return self.window
		import windowinterface
		return windowinterface.getmainwnd()

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
		Help.givehelp('Hierarchy')

	def dropeffect(self, dummy, window, event, params):
		import MMNode
		import windowinterface
		x, y, filename = params
		obj = self.whichhit(x, y)
		if not obj:
			return windowinterface.DROPEFFECT_NONE
		elif obj.node.GetType() in MMNode.leaftypes:
			return windowinterface.DROPEFFECT_MOVE
		else:
			return windowinterface.DROPEFFECT_COPY
