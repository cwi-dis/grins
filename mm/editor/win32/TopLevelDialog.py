__version__ = "$Id$"

import windowinterface, WMEVENTS
from usercmd import *

""" @win32doc|TopLevelDialog
There is one to one corespondance between a TopLevelDialog
instance and a document, and a TopLevelDialog
instance with an MDIFrameWnd. The document level commands
are enabled. This class has acces to the document and
can display its various views and its source
"""

class TopLevelDialog:
	adornments = {}

	def __init__(self):
		pass

	def show(self):
		print 'show document',self.filename
		if self.window is not None:
			return
		self.window = windowinterface.newdocument(self, 
			adornments = self.adornments,commandlist = self.commandlist)

	def hide(self):
		if self.window is None:
			return
		print 'close document',self.filename
		self.window.close()
		self.window = None

	def setbuttonstate(self, command, showing):
		self.window.set_toggle(command, showing)

	def showsource(self, source):
		if self.source:
			self.source.close()
			self.source=None
			self.window.set_toggle(SOURCE,0)
		else:
			self.source = self.window.textwindow(self.root.source)
			self.window.set_toggle(SOURCE,1)

	def mayclose(self):
		prompt = 'You haven\'t saved your changes yet;\n' + \
			 'do you want to save them before closing?'
		return windowinterface.GetYesNoCancel(prompt,self.window)

	# doesn't seem to work
	# kk: you must pass a context string as a second arg
	def setcommands(self, commandlist):
		self.window.set_commandlist(commandlist,'document')
