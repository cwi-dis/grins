__version__ = "$Id$"

""" @win32doc|ChannelViewDialog
This class represents the interface between the ChannelView platform independent
class and its implementation class _ChannelView in lib/win32/_ChannelView.py which 
implements the actual view.

"""

from ViewDialog import ViewDialog
import WMEVENTS
import MMAttrdefs
from usercmd import *

class ChannelViewDialog(ViewDialog):
	adornments = {}

	def __init__(self):
		ViewDialog.__init__(self, 'cview_')

	def show(self, title):
		# change view name from Channel to Timeline
		title = 'Timeline View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x, y, w, h = self.last_geometry
		toplevel_window=self.toplevel.window
		self.window=toplevel_window.newview(x, y, w, h, title, 
			adornments = self.adornments,canvassize = (w, h),
			strid='cview_')
		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.set_toggle(TOGGLE_UNUSED, self.showall)
		self.window.set_toggle(TOGGLE_ARCS, self.showarcs)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)

	def hide(self, *rest):
		self.save_geometry()
		self.window.close()
		self.window = None
		self.displist = self.new_displist = None

	def setcommands(self, commandlist, title):
		self.window.set_commandlist(commandlist)
		self.window.set_dynamiclist(ANCESTORS, self.baseobject.ancestors)
		self.window.set_dynamiclist(SIBLINGS, self.baseobject.siblings)
		self.window.set_dynamiclist(DESCENDANTS, self.baseobject.descendants)
		self.window.set_dynamiclist(SYNCARCS, (self.focus and self.focus.arcmenu) or [])
		self.window.set_dynamiclist(LAYOUTS, self.layouts)

	def settoggle(self, command, onoff):
		self.window.set_toggle(command, onoff)


class GOCommand:
	def __init__(self):
		pass

	def helpcall(self):
		import Help
		Help.givehelp('Timeline')


class ChannelBoxCommand:
	def __init__(self):
		pass

class NodeBoxCommand:
	def __init__(self, mother, node):
		pass

class ArcBoxCommand:
	def __init__(self):
		pass
