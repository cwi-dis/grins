__version__ = "$Id$"

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
import Carbon.File
import MMurl
import windowinterface
import features
from compatibility import Boston

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
		import Help
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(
				usercmd.HELP(callback = (self.help_callback, ())))
		self.__window = w = windowinterface.windowgroup(title, self.commandlist, globalgroup=1)
		windowinterface.installaehandler('aevt', 'oapp', self._ae_openapp)
		windowinterface.installaehandler('aevt', 'quit', self._ae_quit)
		windowinterface.installaehandler('aevt', 'odoc', self._ae_opendoc)

	def set_recent_list(self, list):
		self.__window.set_dynamiclist(usercmd.OPEN_RECENT, list)
		
	def open_callback(self):
		import windowinterface
		windowinterface.InputURLDialog('Open location', self.last_location,
					    self.openURL_callback)

	def openfile_callback(self):
		"""Callback for OPENFILE menu command"""
		import windowinterface
		if features.compatibility == Boston:
			filetypes = ['/SMIL presentation', 'application/smil', 'application/x-grins-project']
		else:
			filetypes = ['/SMIL presentation', 'application/x-grins-project', 'application/smil']
		if not features.lightweight:
			filetypes.append('application/x-grins-cmif')
		windowinterface.FileDialog('', '', filetypes, '',
					   self.__openfile_done, None, 1)

	def __openfile_done(self, filename):
		"""End of OPENFILE menu command. Open the file (as url)"""
		url = self.__path2url(filename)
		if url:
			self.openURL_callback(url)

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

	# Callback functions.  These functions should be supplied by
	# the user of this class (i.e., the class that inherits from
	# this class).
	def openURL_callback(self, url):
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

	def help_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def _ae_openapp(self, *args, **kwargs):
		pass
		
	def _ae_opendoc(self, aliases, **kwargs):
		if not type(aliases) in (type(()), type([])):
			aliases=[aliases]
		for alias in aliases:
			try:
				fsr, changed = alias.FSResolveAlias(None)
			except Carbon.File.error, arg:
				windowinterface.message("Cannot resolve: %s"%str(arg))
				return
			pathname = fsr.as_pathname()
			url = MMurl.pathname2url(pathname)
			self.openURL_callback(url)
		
	def _ae_quit(self, *args, **kwargs):
		#
		# Obfuscated code ahead. We call do_close to check that the user wants to close
		# but in stead of actually doing the exit here, which would result in the
		# AE reply not being sent, we schedule the exit for a short while later.
		#
		exitcallback = (windowinterface.settimer, (0.1, (self._quitnow, ())))
		self.close_callback(exitcallback)
		
	def _quitnow(self):
		raise SystemExit, 0
