__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *

class TopLevelDialog:
	adornments = {
		'toolbar': [
			('Play', PLAY),
			('Player', PLAYERVIEW, 't'),
			('Hierarchy view', HIERARCHYVIEW, 't'),
			('Channel view', CHANNELVIEW, 't'),
			('Hyperlinks', LINKVIEW, 't'),
			('Source...', SOURCE),
			('Save', SAVE),
			('Save as...', SAVE_AS),
			('Restore', RESTORE),
			('Close', CLOSE),
			('Help', HELP),
			],
		'toolbarvertical': 1,
		'close': [ CLOSE, ],
		}

	def __init__(self):
		pass

	def show(self):
		if self.window is not None:
			return
		self.window = w = windowinterface.newdocument(self.basename, 
			adornments = self.adornments,commandlist = self.commandlist)

	def hide(self):
		if self.window is None:
			return
		self.window.close()
		self.window = None

	def setbuttonstate(self, command, showing):
		self.window.set_toggle(command, showing)

	def showsource(self, source):
		if self.source:
			self.source.close()
			self.source=None
			windowinterface.getmainwnd().set_toggle(SOURCE,0)
		else:
			self.source = windowinterface.textwindow(self.root.source)
			windowinterface.getmainwnd().set_toggle(SOURCE,1)
	def mayclose_X(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		b1 = 'Save'
		b2 = "Don't save"
		b3 = 'Cancel'
		return windowinterface.multchoice(prompt, [b1, b2, b3], -1)

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		return windowinterface.GetYesNoCancel(prompt,self.window)


