__version__ = "$Id$"

import windowinterface, usercmd

class SourceViewDialog:
	def __init__(self):
		self.__textwindow = None
		
	def destroy(self):
		self.__textwindow = None
	def show(self):
		if not self.__textwindow:
			print "DEBUG: creating a new text window."
			self.__textwindow = self.toplevel.window.textwindow("", readonly=0)
			self.__textwindow.setmother(self)
		else:
			# Pop it up
			pass

	def is_showing(self):
		if self.__textwindow:
			return 1
		else:
			return 0

	def hide(self):
		if self.__textwindow:
			self.__textwindow.close()
			self.__textwindow = None

	def get_text(self):
		if self.__textwindow:
			return self.__textwindow.get_text()
		else:
			print "ERROR (get_text): No text window."

	def set_text(self, text):
		if self.__textwindow:
			return self.__textwindow.settext(text)
		else:
			print "ERROR (set text): No text window"

	def is_changed(self):
		if self.__textwindow:
			return self.__textwindow.is_changed()
