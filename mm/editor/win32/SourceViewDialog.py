__version__ = "$Id$"

import windowinterface, usercmd
from usercmd import *

class SourceViewDialog:
	def __init__(self):
		self.__textwindow = None
		self.__setCommonCommandList()

	def __setCommonCommandList(self):
		self._commonCommandList = [SELECTNODE_FROM_SOURCE(callback = (self.onRetrieveNode, ()))]
		
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

	def pop(self):
		if self.__textwindow != None:
			self.__textwindow.pop()
			
	def __updateCommandList(self):
		commandList = []

		# undo
		if self.__textwindow.canUndo():
			commandList.append(UNDO(callback = (self.onUndo, ())))

		# copy/paste/cut			
		if self.__textwindow.isSelected():
			if self.__textwindow.isClipboardEmpty():
				commandList.append(COPY(callback = (self.onCopy, ())))
				commandList.append(CUT(callback = (self.onCut, ())))
			else:
				commandList.append(COPY(callback = (self.onCopy, ())))
				commandList.append(CUT(callback = (self.onCut, ())))
				commandList.append(PASTE(callback = (self.onPaste, ())))
		elif not self.__textwindow.isClipboardEmpty():
			commandList.append(PASTE(callback = (self.onPaste, ())))

		# other operations all the time actived
		commandList = commandList+self._commonCommandList
		
		self.setcommandlist(commandList)
		
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
		if self.__textwindow:
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
		if self.__textwindow:
			self.__textwindow.select_chars(s,e)

	def select_lines(self, sLine, eLine):
		if self.__textwindow:
			self.__textwindow.select_line(sLine)

	# return the current line pointed by the carret
	def getCurrentCharIndex(self):
		if self.__textwindow:
			return self.__textwindow.getCurrentCharIndex()
		return -1

	#
	# text window listener interface
	#
	
	# this call back is called when the selection change
	def onSelChanged(self):
		self.__updateCommandList()

	# this call back is called when the content of the clipboard change (or may have changed)
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

	def onUndo(self):
		self.__textwindow.Undo()