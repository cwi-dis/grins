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
import MMNode
import windowinterface

from usercmd import *
from MenuTemplate import POPUP_HVIEW_LEAF, POPUP_HVIEW_TRANS, POPUP_HVIEW_SLIDE, POPUP_HVIEW_STRUCTURE, POPUP_EVENT

class HierarchyViewDialog(ViewDialog):
	adornments = {}
	interior_popupmenu = POPUP_HVIEW_STRUCTURE
	leaf_popupmenu = POPUP_HVIEW_LEAF
	slide_popupmenu = POPUP_HVIEW_SLIDE
	transition_popupmenu = POPUP_HVIEW_TRANS
	event_popupmenu = POPUP_EVENT

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

		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.Mouse0Release, self.mouse0release, None)
		self.window.register(WMEVENTS.ResizeWindow, self.redraw, None)
		self.window.register(WMEVENTS.PasteFile, self.pastefile, None)
		self.window.register(WMEVENTS.DragFile, self.dropeffect, None)
		self.window.register(WMEVENTS.DropFile, self.dropfile, None)

		self.window.register(WMEVENTS.DragNode, self.dragnode, None)
		self.window.register(WMEVENTS.DropNode, self.dropnode, None)

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
		self.window.set_dynamiclist(TRANSITION, self.translist or [])
		self.window.set_commandlist(commandlist)

	def setpopup(self, template):
		self.window.setpopupmenu(template)

	def setstate(self):
		w = self.window
		w.set_toggle(THUMBNAIL, self.thumbnails)
		w.set_toggle(PLAYABLE, self.showplayability)
		w.set_toggle(TIMESCALE, self.timescale == 'global')
		w.set_toggle(LOCALTIMESCALE, self.timescale == 'focus')

	def helpcall(self):
		import Help
		Help.givehelp('Hierarchy')

	def dropeffect(self, dummy, window, event, params):
		# event handler for mouse moves while dragging a file over the window.
		x, y, filename = params
		if x < 1.0 and y < 1.0:
			x = x * self.mcanvassize[0]
			y = y * self.mcanvassize[1]		
		obj = self.whichhit(x, y)
		if not obj:
			return windowinterface.DROPEFFECT_NONE
		elif obj.node.GetType() in MMNode.leaftypes:
			return windowinterface.DROPEFFECT_MOVE
		else:
			return windowinterface.DROPEFFECT_COPY
	
	def pastefile(self, maybenode, window, event, params):
		import MMurl
		x, y, filename = params
		url = MMurl.pathname2url(filename)
		params = (x, y, url)
		self.dropfile(maybenode, window, event, params)

	def dragnode(self, dummy, window, event, params):
		# event handler for dragging a node over the window.
		x, y, cmd, xf, yf = params
		if x < 1.0 and y < 1.0:
			x = x * self.mcanvassize[0]
			y = y * self.mcanvassize[1]
			xf = xf * self.mcanvassize[0]
			yf = yf * self.mcanvassize[1]
		obj = self.whichhit(x, y)
		objSrc = self.whichhit(xf, yf)
		if obj and obj.node.GetType() in MMNode.interiortypes:
			if cmd=='move':
				if objSrc.node.IsAncestorOf(obj.node):
					return windowinterface.DROPEFFECT_NONE
				return windowinterface.DROPEFFECT_MOVE
			else: 
				return windowinterface.DROPEFFECT_COPY
		return windowinterface.DROPEFFECT_NONE
			
	def dropnode(self, dummy, window, event, params):
		# event handler for dropping the node.
		x, y, cmd, xf, yf = params
		if x < 1.0 and y < 1.0:
			x = x * self.mcanvassize[0]
			y = y * self.mcanvassize[1]
			xf = xf * self.mcanvassize[0]
			yf = yf * self.mcanvassize[1]
		objSrc = self.whichhit(xf, yf)
		objDst = self.whichhit(x, y)
		if objSrc and objDst and objDst.node.GetType() in MMNode.interiortypes:
			if cmd=='move':
				if objSrc.node.IsAncestorOf(objDst.node):
					return 0
				self.movenode((x, y), (xf, yf))
			else:
				self.copynode((x, y), (xf, yf))
			return 1
		return 0
