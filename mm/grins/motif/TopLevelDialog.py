__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *

class TopLevelDialog:
	def show(self):
		sensitive = len(self.main.tops) > 1
		for top in self.main.tops:
			top.__set_close_sensitive(sensitive)

	def hide(self):
		sensitive = len(self.main.tops) > 1
		for top in self.main.tops:
			top.__set_close_sensitive(sensitive)

	def showsource(self, source):
		if self.source is not None and not self.source.is_closed():
			self.source.show()
			return
		self.source = windowinterface.textwindow(self.root.source)

	def __set_close_sensitive(self, sensitive):
		# CLOSE is the first entry in commandlist
		if sensitive:
			# sensitive: include CLOSE
			self.player.topcommandlist(self.commandlist)
		else:
			# insensitve: exclude CLOSE
			self.player.topcommandlist(self.commandlist[1:])

	def setusergroupsmenu(self, menu):
		self.player.setusergroupsmenu(menu)

	def setsettingsdict(self, dict):
		pass
