__version__ = "$Id$"

import windowinterface, usercmd

class SourceViewDialog:
	def __init__(self):
		print "TODO: SourceViewDialog.init"
		self.__textwindow = None
	def destroy(self):
		self.__textwindow = None
	def show(self):
		print "DEBUG: show called."
		if not self.__textwindow:
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
