__version__ = "$Id$"

# @win32doc|TopLevelDialog
# There is one to one corespondance between a TopLevelDialog
# instance and a document, and a TopLevelDialog
# instance with an MDIFrameWnd. The document level commands
# are enabled. This class has acces to the document and
# can display its source view

import windowinterface, WMEVENTS
from usercmd import *

class TopLevelDialog:
	def show(self):
		sensitive = len(self.main.tops) > 1
		for top in self.main.tops:
			top.__set_close_sensitive(sensitive)
		if not hasattr(self,'window'):
			self.window=None
		if not self.window:
			self.window = windowinterface.newdocument(self, 
				adornments = None,commandlist = self.commandlist)

	def hide(self):
		if hasattr(self,'window') and self.window:
			self.window.set_toggle(SOURCEVIEW,0)
			self.window.close() 
			self.window=None
		sensitive = len(self.main.tops) > 1
		for top in self.main.tops:
			top.__set_close_sensitive(sensitive)

	def showsource(self, source):
		if self.source is not None:
			self.source.close()
			self.source = None
			self.window.set_toggle(SOURCEVIEW,0)
		else:
			self.source = self.window.textwindow(source, readonly = 1, close_callback = (self.__close_source, ()))
			self.window.set_toggle(SOURCEVIEW,1)

	def setplayerstate(self, state):
		if hasattr(self, 'window') and self.window:
			self.window.setplayerstate(state)
			
	def setusergroupsmenu(self, menu):
		w = self.window
		if w is not None:
			w.set_dynamiclist(USERGROUPS, menu)
			
	def __close_source(self):
		if self.source is not None:
			self.source.close()
			self.source = None
			self.window.set_toggle(SOURCEVIEW,0)

	def __set_close_sensitive(self, sensitive):
		# CLOSE is the first entry in commandlist
		if sensitive:
			# sensitive: include CLOSE
			self.player.topcommandlist(self.commandlist)
		else:
			# insensitve: exclude CLOSE
			self.player.topcommandlist(self.commandlist[1:])
