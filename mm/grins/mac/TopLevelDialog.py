__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *

class TopLevelDialog:
	#
	# Note that the TopLevel class on the Mac does not use any commands, everything
	# is done by the grins and player classes (a future "view source" command will
	# probably be implemented here). So, currently the self.commandlist set
	# by TopLevel is happily ignored.
	
	def show(self):
		self.player.topcommandlist(self.commandlist)

	def hide(self):
		pass

	def showsource(self, source):
		if self.source is not None and not self.source.is_closed():
			self.source.show()
			return
		self.source = windowinterface.textwindow(self.root.source)

