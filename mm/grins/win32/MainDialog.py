# Dialog for the Main window.

# This is a very simple dialog, it consists of four choices and three
# callback functions.

# The choices are labeled `New', `Open Location...', `Open File...', and
# `Exit'.  If either of the Open choices is selected, a dialog window
# asks for a URL or a file name respectively, and if one is selected,
# the callback self.open_callback is called with the selected location
#  (always passed in the form of a URL).

# If the New choice is selected, the callback self.new_callback is
# called without arguments.  If the Exit choice is selected, the
# callback self.close_callback is called without arguments.  Also, if
# the dialog window is closed in some other way, the callback
# self.close_callback is also called.

# @win32doc|MainDialog
# There is only one instance of the MainDialog class per application.
# The MainDialog constructor creates an MDIFraneWnd with a toolbar
# and menu. The application level commands Open and Exit
# are enabled. When there are documents open there is a one to one
# correspondance between an MDIFrameWnd and a document. The MDIFrameWnd
# created is reused by the first document that will be opened.
# The only case that the 1:1 corespondance between an MDIFrameWnd
# and a document is not valid is when the application has no
# open documents 

__version__ = "$Id$"

from usercmd import *
from wndusercmd import *
import features
from compatibility import Boston
import WMEVENTS
import MMurl

class MainDialog:
	def __init__(self, title):
		# Create the Main dialog.

		# Create the dialog window (non-modal, so does not grab
		# the cursor) and pop it up (i.e. display it on the
		# screen).

		# Arguments (no defaults):
		# title -- string to be displayed as window title
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
		windowinterface.register_event(WMEVENTS.DragFile, self.dropeffect, None)		
		windowinterface.register_event(WMEVENTS.DropFile, self.dropfile, None)
		windowinterface.register_event(WMEVENTS.PasteFile, self.dropfile, None)
		windowinterface.register_embedded('OnOpen', self.embeddedopenfile, None)
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
		self.__owindow=windowinterface.OpenLocationDlg(callbacks,f, self.last_location, recent_files=self.get_recent_files())
		self.__text=self.__owindow
		self.__owindow.show()

	def dropeffect(self, dummy, window, event, params):
		x,y,filename=params
		url=self.__path2url(filename)
		import urlcache, windowinterface
		mimetype = urlcache.mimetype(url)
		if mimetype in ('application/x-grins-project', 'application/smil', 'application/x-grins-cmif'):
			return windowinterface.DROPEFFECT_COPY
		else:
			return windowinterface.DROPEFFECT_NONE

	def dropfile(self, arg, window, event, value):
		x,y,filename=value
		url=self.__path2url(filename)
		import urlcache, windowinterface
		mimetype = urlcache.mimetype(url)
		if mimetype in ('application/x-grins-project', 'application/smil', 'application/x-grins-cmif'):
			self.openURL_callback(url)
		else:
			windowinterface.showmessage('Only GRiNS or SMIL files can be dropped.')

	def __skin_done(self, filename):
		if filename:
			import settings
			url = self.__path2url(filename)
			settings.set('skin', url)
			settings.save()

	def skin_callback(self):
		import windowinterface
		windowinterface.FileDialog('Open skin file', '.', ['text/x-grins-skin'], '',
					   self.__skin_done, None, 1,
					   parent = windowinterface.getmainwnd())

##	def components_callback(self):
##		import windowinterface
##		windowinterface.FileDialog('Open components file', '.', ['text/plain'], '',
##					   self.__components_done, None, 1,
##					   parent = windowinterface.getmainwnd())
##
##	def __components_done(self, filename):
##		if filename:
##			import settings
##			url = self.__path2url(filename)
##			settings.set('components', url)
##			settings.save()

	def openfile_callback(self):
		# Callback for OPENFILE menu command
		import windowinterface
		f=windowinterface.getmainwnd()
		if features.compatibility == Boston:
			filetypes = ['/All presentations', 'application/smil', 'application/x-grins-project', 'application/x-grins-binary-project']
		else:
			filetypes = ['/All presentations', 'application/x-grins-project', 'application/smil', 'application/x-grins-binary-project']
##		import features
##		if not features.lightweight:
##			filetypes.append('application/x-grins-cmif')
		windowinterface.FileDialog('Open file', '.', filetypes, '',
					   self.__openfile_done, None, 1,
					   parent = f)

	def __openfile_done(self, filename):
		# End of OPENFILE menu command. Open the file (as url)
		url = self.__path2url(filename)
		if url:
			self.openURL_callback(url)

	def embeddedopenfile(self, arg, window, event, value):
		if len(value)>7 and value[:6] == 'file:/':
			if value[7]==':':
				url = 'file:///%s|%s' % (value[6], value[8:])
			else:
				url = MMurl.canonURL(value)
		else:
			url = self.__path2url(value)
		if url:
			self.openURL_callback(url)
		
	def set_recent_list(self, list):
		import windowinterface
		f=windowinterface.getactivedocframe()
		f.set_dynamiclist(OPEN_RECENT, list)

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
		text = self.__text.gettext()
		dir, file = ',', ''
		if text:
			import urlparse
			utype, host, path, params, query, fragment = urlparse.urlparse(text)
			if (not utype or utype == 'file') and \
			   (not host or host == 'localhost') and \
			   path:
				import MMurl, os
				file = MMurl.url2pathname(path)
				dir, file = os.path.split(file)
		f=windowinterface.getmainwnd()
		filetypes = ['/All presentations', 'application/smil', 'application/x-grins-project', 'application/x-grins-binary-project']
		windowinterface.FileDialog('Open file', dir, filetypes, file,
					   self.__filecvt, None, 1,
					   parent = f)

	def __filecvt(self, filename):
		text=self.__path2url(filename)
		self.__text.settext(text)

	def __path2url(self, filename):
		# this method is called also from the drop stuff
		# so check for UNC names before calling pathname2url
		# otherwise it will fail.
		import os
		if os.name != 'ce':
			import longpath
			filename = longpath.short2longpath(filename)
##		if os.path.isabs(filename):
##			cwd = os.getcwd()
##			if os.path.isdir(filename):
##				dir, file = filename, os.curdir
##			else:
##				dir, file = os.path.split(filename)
##			# XXXX maybe should check that dir gets shorter!
##			while len(dir) > len(cwd):
##				dir, f = os.path.split(dir)
##				file = os.path.join(f, file)
##			if dir == cwd:
##				filename = file
		return MMurl.pathname2url(filename)

	if __debug__:
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
 
