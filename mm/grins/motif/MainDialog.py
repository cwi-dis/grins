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

class MainDialog:
	def __init__(self, title):
		"""Create the Main dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		"""

		pass

	def open_callback(self):
		import windowinterface
		w = windowinterface.Window('Open location', resizable = 1,
					   grab = 1, horizontalSpacing = 5,
					   verticalSpacing = 5)
		l = w.Label('Open location', top = None, left = None,
			    right = None)
		f = w.SubWindow(left = None, top = l, right = None,
				horizontalSpacing = 5, verticalSpacing = 5)
		t = f.TextInput(None, '', None, (self.__tcallback, ()),
				left = None, top = None, bottom = None)
		f.Button('Browse...', (self.__openfile_callback, ()),
			 top = None, left = t, right = None, bottom = None)
		s = w.Separator(top = f, left = None, right = None)
		r = w.ButtonRow([('Open', (self.__tcallback, ())),
				 ('Cancel', (self.__ccallback, ()))],
				vertical = 0, tight = 1, top = f, left = None,
				right = None, bottom = None)
		self.__text = t
		self.__owindow = w
		w.show()

	def __ccallback(self):
		self.__owindow.close()
		self.__owindow = None
		self.__text = None

	def __tcallback(self):
		text = self.__text.gettext()
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
		self.__text.settext(MMurl.pathname2url(filename))

	def setbutton(self, button, value):
		pass			# for now...

	def menubar(self):
		return [('File', [
			('', 'Open Location...', (self.__openURL_callback, ())),
			('', 'Open File...', (self.__openfile_callback, ())),
			('', 'Trace', (self.trace_callback, ()), 't'),
			('', 'Debug', (self.debug_callback, ())),
			None,
			('', 'Exit', (self.close_callback, ())),
			])]
