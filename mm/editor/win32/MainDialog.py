"""Dialog for the Main window.

This is a very simple dialog, it consists of four choices and three
callback functions.

The choices are labeled `New', `Open Location...', `Open File...', and
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

__version__ = "$Id$"

from usercmd import *

class MainDialog:
	adornments = {
		'toolbar' : [
			('New', NEW_DOCUMENT),
			('Open...', OPEN),
			('Exit', EXIT),
			],
		'close': [ EXIT, ],
		}
	if __debug__:
		adornments['toolbar'][2:2] = [
			('Trace', TRACE, 't'),
			('Debug', DEBUG),
			('Crash', CRASH),
			]

	def __init__(self, title):
		"""Create the Main dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		"""

		import windowinterface, WMEVENTS

		self.__window = w = windowinterface.newcmwindow(None, None, 0, 0,
				title, adornments = self.adornments,
				commandlist = self.commandlist, context='frame')

	def open_callback(self):
		callbacks={
			'Browse':(self.__openfile_callback, ()),
			'Open': (self.__tcallback, ()),
			'Cancel':(self.__ccallback, ()),
			}
		import windowinterface
		self.__owindow=windowinterface.OpenLocationDlg(callbacks)
		self.__owindow.DoModal()

	def __ccallback(self):
		self.__owindow = None

	def __tcallback(self):
		text = self.__owindow.gettext()
		self.__ccallback()
		if text:
			self.openURL_callback(text)

	def __openfile_callback(self):
		import windowinterface
		windowinterface.FileDialog('Open file', '.', '*.smil', '',
					   self.__filecvt, None, 1,
					   parent = self.__owindow)

	def __filecvt(self, filename):
		import os, MMurl
		if os.path.isabs(filename):
			cwd = os.getcwd()
			if os.path.isdir(filename):
				dir, file = filename, os.curdir
			else:
				dir, file = os.path.split(filename)
			# XXXX maybe should check that dir gets shorter!
			while len(dir) > len(cwd):
				dir, f = os.path.split(dir)
				file = os.path.join(f, file)
			if dir == cwd:
				filename = file
		self.__owindow.settext(MMurl.pathname2url(filename))

	def setbutton(self, button, value):
		pass			# for now...

