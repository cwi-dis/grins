__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *

class TopLevelDialog:
	def show(self):
		sensitive = len(self.main.tops) > 1
		for top in self.main.tops:
			top.__set_close_sensitive(sensitive)
		if not hasattr(self,'_document'):
			self._document=None
		if not self._document:
			self._document = windowinterface.newdocument(self.basename, 
				adornments = None,commandlist = self.commandlist)

	def hide(self):
		if hasattr(self,'_document') and self._document:
			self._document.close() 
			self._document=None
		sensitive = len(self.main.tops) > 1
		for top in self.main.tops:
			top.__set_close_sensitive(sensitive)

	def showsource(self, source):
		if self.source:
			self.source.close()
			self.source=None
			windowinterface.getmainwnd().set_toggle(SOURCE,0)
		else:
			self.source = windowinterface.textwindow(self.root.source)
			windowinterface.getmainwnd().set_toggle(SOURCE,1)

	def showsource_(self, source):
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
