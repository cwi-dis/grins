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

"""@win32doc|MainDialog
There is only one instance of the MainDialog class per application.
The MainDialog constructor creates an MDIFraneWnd with a toolbar
and menu. The application level commands Open and Exit
are enabled. When there are documents open there is a one to one
correspondance between an MDIFrameWnd and a document. The MDIFrameWnd
created is reused by the first document that will be opened.
The only case that the 1:1 corespondance between an MDIFrameWnd
and a document is not valid is when the application has no
open documents 
"""


__version__ = "$Id$"

from usercmd import *
from wndusercmd import *

import WMEVENTS

class MainDialog:
	def __init__(self, title):
		"""Create the Main dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		"""
		if __debug__:
			import usercmd
			self.commandlist.append(
					usercmd.CONSOLE(callback=(self.console_callback, ())))
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(
				HELP_CONTENTS(callback = (self.help_contents_callback, ())))
			self.commandlist.append(
				GRINS_WEB(callback = (self.grins_web_callback, ('http://www.oratrix.com/GRiNS/index.html',))))
		# register events for all frame wnds
		import windowinterface
		windowinterface.register_event(WMEVENTS.DropFile, self.dropfile, None)
		windowinterface.register_event(WMEVENTS.PasteFile, self.dropfile, None)
		import windowinterface
		windowinterface.createmainwnd(title,
			adornments = None,
			commandlist = self.commandlist)

	def open_callback(self):
		callbacks={
			'Browse':(self.__openfile_callback, ()),
			'Open': (self.__tcallback, ()),
			'Cancel':(self.__ccallback, ()),
			}
		import windowinterface
		f=windowinterface.getmainwnd()
		self.__owindow=windowinterface.OpenLocationDlg(callbacks,f)
		self.__text=self.__owindow._text
		self.__owindow.show()

	def dropfile(self, arg, window, event, value):
		x,y,filename=value
		url=self.__path2url(filename)
		import mimetypes, windowinterface
		mimetype = mimetypes.guess_type(url)[0]
		if mimetype in ('application/smil', 'application/x-grins-cmif'):
			self.openURL_callback(url)
		else:
			windowinterface.showmessage('Incorrect filetype for drop/paste')


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
		f=windowinterface.getmainwnd()
		windowinterface.FileDialog('Open file', '.', '*.smil', '',
					   self.__filecvt, None, 1,
					   parent = f)

	def __filecvt(self, filename):
		text=self.__path2url(filename)
		self.__text.settext(text)

	def __path2url(self, filename):
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
		return MMurl.pathname2url(filename)

	def console_callback(self):
		import win32ui,win32con
		cwnd=win32ui.GetAfx().GetMainWnd()
		if cwnd.IsWindowVisible():
			cwnd.ShowWindow(win32con.SW_HIDE)
		else:
			cwnd.ShowWindow(win32con.SW_RESTORE)
			cwnd.ShowWindow(win32con.SW_SHOW)
			cwnd.BringWindowToTop()

	def help_contents_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def grins_web_callback(self, url):
		import windowinterface
		helpwindow = windowinterface.shell_execute(url,'open')
