__version__ = "$Id$"

import windowinterface, usercmd
from usercmd import *

class SourceViewDialog:
	def __init__(self):
		self.__textwindow = None
		self.__setCommandSelClipNotEmpty()
		self.__setCommandSelClipEmpty()
		self.__setCommandUnselClipNotEmpty()
		self.__setCommandUnselClipEmpty()

	def __addCommonCommand(self, list):
		pass
	
	def __setCommandSelClipNotEmpty(self):
		# Add the user-interface commands that are used for this window.
		self.commandSelClipNotEmpty = []
		self.__addCommonCommand(self.commandSelClipNotEmpty)
		self.commandSelClipNotEmpty.append(COPY(callback = (self.onCopy, ())))
		self.commandSelClipNotEmpty.append(CUT(callback = (self.onCut, ())))
		self.commandSelClipNotEmpty.append(PASTE(callback = (self.onPaste, ())))

	def __setCommandSelClipEmpty(self):
		# Add the user-interface commands that are used for this window.
		self.commandSelClipEmpty = []
		self.__addCommonCommand(self.commandSelClipNotEmpty)
		self.commandSelClipEmpty.append(COPY(callback = (self.onCopy, ())))
		self.commandSelClipEmpty.append(CUT(callback = (self.onCut, ())))

	def __setCommandUnselClipNotEmpty(self):
		# Add the user-interface commands that are used for this window.
		self.commandUnselClipNotEmpty = []
		self.__addCommonCommand(self.commandUnselClipNotEmpty)
		self.commandUnselClipNotEmpty.append(PASTE(callback = (self.onPaste, ())))

	def __setCommandUnselClipEmpty(self):
		# Add the user-interface commands that are used for this window.
		self.commandUnselClipEmpty = []
		self.__addCommonCommand(self.commandUnselClipEmpty)
		
	def destroy(self):
		self.__textwindow = None
		
	def show(self):
		if not self.__textwindow:
			self.__textwindow = self.toplevel.window.textwindow("", readonly=0)
			self.__textwindow.set_mother(self)
		else:
			# Pop it up
			pass
		self.__updateCommandList()
		self.__textwindow.setListener(self)

	def __updateCommandList(self):
		if self.__textwindow.isSelected():
			if self.__textwindow.isClipboardEmpty():
				self.setcommandlist(self.commandSelClipEmpty)
			else:
				self.setcommandlist(self.commandSelClipNotEmpty)
		elif self.__textwindow.isClipboardEmpty():
			self.setcommandlist(self.commandUnselClipEmpty)
		else:
			self.setcommandlist(self.commandUnselClipNotEmpty)
						
	def is_showing(self):
		if self.__textwindow:
			return 1
		else:
			return 0

	def hide(self):
		if self.__textwindow:
			self.__textwindow.removeListener()
			self.__textwindow.close()
			self.__textwindow = None

	def setcommandlist(self, commandlist):
		self.__textwindow.set_commandlist(commandlist)

	def get_text(self):
		if self.__textwindow:
			return self.__textwindow.gettext()
		else:
			print "ERROR (get_text): No text window."

	def set_text(self, text):
		if self.__textwindow:
			return self.__textwindow.settext(text)
		else:
			print "ERROR (set text): No text window"

	def is_changed(self):
		if self.__textwindow:
			return self.__textwindow.isChanged()

	def select_chars(self, s, e):
		self.__textwindow.select_chars(s,e)

	#
	# text window listener interface
	#
	
	# this call back is called when the selection change
	def onSelChanged(self):
		self.__updateCommandList()

	# this call back is called when the content of the clipboard change
	# XXX: it's currently not working
	def onClipboardChanged(self):
		self.__updateCommandList()
			
	#
	# command listener interface
	#
	
	# note: these copy, paste and cut operation don't use the GRiNS clipboard
	def onCopy(self):
		self.__textwindow.Copy()

	def onCut(self):
		self.__textwindow.Cut()

	def onPaste(self):
		self.__textwindow.Paste()
