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
import UserCmd

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

		cmdlist = [
			(UserCmd.NEW_DOCUMENT, (self.new_callback, ())),
			(UserCmd.OPEN_URL, (self.__openURL_callback, ())),
			(UserCmd.OPEN_FILE, (self.__openfile_callback, ())),
			(UserCmd.TRACE, (self.trace_callback, ())),
			(UserCmd.DEBUG, (self.debug_callback, ())),
			(UserCmd.CONSOLE, (self.console_callback, ())),
			(UserCmd.EXIT, (self.close_callback, ()))]
		self.__window = w = windowinterface.windowgroup(title, cmdlist, globalgroup=1)

	def __del__(self):
		print 'CLOSING?'
		import pdb ; pdb.set_trace()
	def __openURL_callback(self):
		import windowinterface
		windowinterface.InputDialog('Open location', '',
					    self.open_callback)

	def __openfile_callback(self):
		import windowinterface
		windowinterface.FileDialog('Open file', '.', '*.smil', '',
					   self.__filecvt, None, 1)

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
		self.open_callback('file:'+MMurl.pathname2url(filename))

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def new_callback(self):
		pass

	def open_callback(self, url):
		pass

	def close_callback(self):
		pass

	def trace_callback(self):
		pass

	def debug_callback(self):
		pass
		
	def console_callback(self):
		import quietconsole
		quietconsole.revert()
