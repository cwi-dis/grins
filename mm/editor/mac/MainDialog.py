"""Dialog for the Main window.

This is a very simple dialog, it consists of four choices and three
callback functions.

Thex choices are labeled `New', `Open Location...', `Open File...', and
`Exit'.  If either of the Open choices is selected, a dialog window
asks for a URL or a file name respectively, and if one is selected,
the callback self.open_callback is called with the selected location
(always passed in the form of a URL).

If the New choice is selected, the callback self.new_callback is
called without arguments.  If the Exit choice is selected, the
callback self.close_callback is called without arguments.  Also, if
the dialog window is closed in some other way, the callback
self.close_callback is also called.

"""
import usercmd
import os

class MainDialog:
	def __init__(self, title):
		"""Create the Main dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		"""

		import windowinterface

		if __debug__:
			self.commandlist.append(
				usercmd.CONSOLE(callback=(self.console_callback, ())))
		self.__window = w = windowinterface.windowgroup(title, self.commandlist, globalgroup=1)

	def open_callback(self):
		import windowinterface
		windowinterface.InputURLDialog('Open location', '',
					    self.openURL_callback)

	def setbutton(self, button, value):
		pass			# for now...

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
		
	def console_callback(self):
		import quietconsole
		quietconsole.revert()
