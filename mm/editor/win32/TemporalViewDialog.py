__version__ = "$Id$"

from ViewDialog import ViewDialog
import WMEVENTS, windowinterface
import MMAttrdefs
from usercmd import *

class TemporalViewDialog(ViewDialog):
	adornments = {}

	def __init__(self):
		ViewDialog.__init__(self, 'cview_')

	def show(self):
		title = 'Temporal View (' + self.toplevel.basename + ')'
		self.load_geometry()
		x,y,w,h = self.last_geometry
		toplevel_window = self.toplevel.window
		self.window = toplevel_window.newview(x,y,w,h,title,
						      adornments = self.adornments,
						      canvassize = (w,h),
						      strid='cview_' # I don't understand this one -mjvdg
						      )
		self._reg_events()

	def hide(self, *rest):
		print "TODO: hide."

	def _reg_events(self):
		# Register events for this window.
		pass;

	def setcommands(self, commandlist, title):
		self.window.set_commandlist(commandlist)
