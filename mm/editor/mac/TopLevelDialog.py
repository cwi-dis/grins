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

	def showsource(self, source = None, optional=0):
		if optional and self.source and self.source.is_closed():
			self.source = None
			return
		if source is None:
			if self.source is not None:
				if not self.source.is_closed():
					self.source.close()
				self.source = None
			return
		if self.source is not None:
			self.source.settext(source)
			self.source.show()
			return
		self.source = windowinterface.textwindow(source)

	# in the source view, the user may have done some changements without apply them.
	# return 1 if the user want to continue (not cancel)
	def closeSourceView(self):
		return 1

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		return windowinterface.GetYesNoCancel(prompt)
##		rv = EasyDialogs.AskYesNoCancel(prompt, 1)
##		if rv < 0: return 2
##		if rv > 0: return 0
##		return 1

	def setcommands(self, commandlist):
		self.window.set_commandlist(commandlist)