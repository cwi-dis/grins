__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *
import EasyDialogs

class TopLevelDialog:
	def __init__(self):
		self._do_show()
		
	def _do_show(self):
		if self.window is not None:
			return
		self.window = windowinterface.windowgroup(self.basename, self.commandlist)
		
	def show(self):
		self._do_show()

	def hide(self):
		if self.window is None:
			return
		self.window.close()
		self.window = None

	def setbuttonstate(self, command, showing):
		self.window.set_toggle(command, showing)

	def showsource(self, source):
		if self.source is not None and not self.source.is_closed():
			self.source.show()
			return
		self.source = windowinterface.textwindow(self.root.source)

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		b1 = 'Save'
		b2 = "Don't save"
		b3 = 'Cancel'
		return windowinterface.multchoice(prompt, [b1, b2, b3], -1)
##		rv = EasyDialogs.AskYesNoCancel(prompt, 1)
##		if rv < 0: return 2
##		if rv > 0: return 0
##		return 1

	def setcommands(self, commandlist):
		self.window.set_commandlist(commandlist)
