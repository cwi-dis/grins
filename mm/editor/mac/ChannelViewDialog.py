from ViewDialog import ViewDialog
import windowinterface
import WMEVENTS
import MMAttrdefs
from usercmd import *

begend = ('begin', 'end')

class ChannelViewDialog(ViewDialog):
	
	def __init__(self):
		ViewDialog.__init__(self, 'cview_')

	def show(self, title):
		self.load_geometry()
		x, y, w, h = self.last_geometry
		self.window = windowinterface.newcmwindow(x, y, w, h, title, pixmap=1, canvassize = (w, h))
		self.window.set_toggle(THUMBNAIL, self.thumbnails)
		self.window.set_toggle(TOGGLE_UNUSED, self.showall)
		self.window.set_toggle(TOGGLE_ARCS, self.showarcs)
		self.window.register(WMEVENTS.Mouse0Press, self.mouse, None)
		self.window.register(WMEVENTS.ResizeWindow, self.resize, None)
		self.window.register(WMEVENTS.WindowExit, self.hide, None)

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

	def helpcall(self):
		import Help
		Help.givehelp('timeline')
		
class GOCommand:
	def __init__(self):
		pass
		
class ChannelBoxCommand:
	def __init__(self):
		pass
		
class NodeBoxCommand:
	def __init__(self, mother, node):
		pass
		
class ArcBoxCommand:
	def __init__(self):
		pass

