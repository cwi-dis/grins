__version__ = "$Id$"

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
# and menu. The application level commands New, Open and Exit
# are enabled. When there are documents open there is a one to one
# correspondance between an MDIFrameWnd and a document. The MDIFrameWnd
# created is reused by the first document that will be opened.

from usercmd import *
from wndusercmd import *
import WMEVENTS
import features
import version

class MainDialog:
	adornments = {}
	def __init__(self, title, hasarguments=1):
		# Create the Main dialog.

		# Create the dialog window (non-modal, so does not grab
		# the cursor) and pop it up (i.e. display it on the
		# screen).

		# Arguments (no defaults):
		# title -- string to be displayed as window title
		if __debug__:
			self.commandlist.append(
				CONSOLE(callback=(self.console_callback, ())))
			self.commandlist.append(
				SCHEDDEBUG(callback=(self.scheddebug_callback, ())))
		import Help
		import cmif, MMurl, os
		if hasattr(Help, 'hashelp') and Help.hashelp():
			self.commandlist.append(
				HELP_CONTENTS(callback = (self.help_contents_callback, ())))
		self.commandlist.append(
			GRINS_WEB(callback = (self.grins_web_callback, ('http://www.oratrix.com/GRiNS/',))))
		for qsg in ('QuickStart.pdf', 'QuickStart.html'):
			qsg = cmif.findfile(qsg)
			if os.path.exists(qsg):
				qsg = MMurl.pathname2url(qsg)
				self.commandlist.append(
					GRINS_QSG(callback = (self.grins_web_callback, (qsg,))))
				break
		for tutorial in ('tutorials.pdf', 'tutorials.html'):
			tutorial = cmif.findfile(tutorial)
			if os.path.exists(tutorial):
				tutorial = MMurl.pathname2url(tutorial)
				self.commandlist.append(
					GRINS_TUTORIAL(callback = (self.grins_web_callback, (tutorial,))))
				break
		for tdg in ('TDG.pdf', 'TDG.html'):
			tdg = cmif.findfile(tdg)
			if os.path.exists(tdg):
				tdg = MMurl.pathname2url(tdg)
				self.commandlist.append(
					GRINS_TDG(callback = (self.grins_web_callback, (tdg,))))
				break
		for refm in ('REFM.pdf', 'REFM.html'):
			refm = cmif.findfile(refm)
			if os.path.exists(refm):
				refm = MMurl.pathname2url(refm)
				self.commandlist.append(
					GRINS_REFERENCE(callback = (self.grins_web_callback, (refm,))))
				break
		import windowinterface
		# register events for all frame wnds
		windowinterface.register_event(WMEVENTS.PasteFile, self.pastefile, None)
		windowinterface.register_event(WMEVENTS.DragFile, self.dropeffect, None)
		windowinterface.register_event(WMEVENTS.DropFile, self.dropfile, None)
		windowinterface.createmainwnd(title,
			adornments = self.adornments,
			commandlist = self.commandlist)
		import settings
		if not hasarguments and settings.get('initial_dialog'):
			f = windowinterface.getmainwnd()
			doclist = self.get_recent_files()
			# if we can't edit the GRiNS preferences, we shouldn't allow this check mark
			if features.PREFERENCES in features.feature_set:
				never_again = self.never_again
			else:
				never_again = None
			windowinterface.OpenAppDialog(version.title, self.new_callback, 
				self.openfile_callback, never_again,
				doclist, self.openURL_callback, parent=f)
		
	def getparentwindow(self):
		# Used by machine-independent code to pass as parent
		# parameter to dialogs
		import windowinterface
		return windowinterface.getmainwnd()

	def open_callback(self):
		if not self.canopennewtop():
			return
		callbacks={
			'Browse':(self.__openfile_callback, ()),
			'Open': (self.__tcallback, ()),
			'Cancel':(self.__ccallback, ()),
			}
		import windowinterface
		f=windowinterface.getmainwnd()
		self.__owindow=windowinterface.OpenLocationDlg(callbacks, f, self.last_location, recent_files=self.get_recent_files())
		self.__text=self.__owindow
		self.__owindow.show()

	def openfile_callback(self):
		# Callback for OPENFILE menu command
		if not self.canopennewtop():
			return
		import windowinterface
		f=windowinterface.getmainwnd()
		filetypes = ['/All presentations', 'application/x-grins-project', 'application/smil']
		windowinterface.FileDialog('Open file', 'Desktop', filetypes, '',
					   self.__openfile_done, None, 1,
					   parent = f)

	def __openfile_done(self, filename):
		# End of OPENFILE menu command. Open the file (as url)
		url = self.__path2url(filename)
		if url:
			self.openURL_callback(url)

	def dropfile(self, arg, window, event, value):
		if not self.canopennewtop():
			return
		x,y,filename=value
		url=self.__path2url(filename)
		import urlcache
		mimetype = urlcache.mimetype(url)
		if mimetype in ('application/x-grins-project', 'application/smil'):
			self.openURL_callback(url)
		else:
			import windowinterface
			windowinterface.showmessage('Only GRiNS or SMIL files can be dropped.')
	
	def pastefile(self, arg, window, event, value):
		if not self.canopennewtop():
			return
		x,y,filename=value
		url=self.__path2url(filename)
		self.openURL_callback(url)
		
	def dropeffect(self, dummy, window, event, params):
		import windowinterface, urlcache
		x,y,filename=params
		url=self.__path2url(filename)
		mimetype = urlcache.mimetype(url)
		if mimetype in ('application/x-grins-project', 'application/smil', 'application/x-grins-cmif'):
			return windowinterface.DROPEFFECT_COPY
		else:
			return windowinterface.DROPEFFECT_NONE

	def set_recent_list(self, list):
		import windowinterface
		f=windowinterface.getactivedocframe()
		f.set_dynamiclist(OPEN_RECENT, list)

	def __ccallback(self):
		self.__owindow.close()
		self.__owindow = None
		self.__text = None

	def __tcallback(self):
		# Callback from the "open" button on the Open URL... dialog.
		text = self.__text.gettext()
		self.__ccallback()
		if text:
			self.openURL_callback(text)

	def __openfile_callback(self):
		# Callback used by "browse" button in open url
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
		filetypes = ['/All presentations', 'application/x-grins-project', 'application/smil']
		windowinterface.FileDialog('Open file', dir, filetypes, file,
					   self.__filecvt, None, 1,
					   parent = f)

	def __filecvt(self, filename):
		# End of "browse" in "open url" dialog. Set URL
		text=self.__path2url(filename)
		self.__text.settext(text)

	def __path2url(self, filename):
		# this method is called also from the drop stuff
		# so check for UNC names before calling pathname2url
		# otherwise it will fail.
		import longpath, MMurl
##		import os
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

	def console_callback(self):
		import win32ui,win32con
		cwnd=win32ui.GetAfx().GetMainWnd()
		if cwnd.IsWindowVisible():
			cwnd.ShowWindow(win32con.SW_HIDE)
		else:
			cwnd.ShowWindow(win32con.SW_RESTORE)
			cwnd.ShowWindow(win32con.SW_SHOW)
			cwnd.BringWindowToTop()

	def scheddebug_callback(self):
		import Scheduler
		Scheduler.debugevents = not Scheduler.debugevents

	def help_contents_callback(self, params=None):
		import Help
		Help.showhelpwindow()

	def grins_web_callback(self, url):
		import windowinterface
		helpwindow = windowinterface.shell_execute(url,'open')

