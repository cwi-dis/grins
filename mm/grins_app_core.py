# grins_app_core.py  - The Pythonwin Application class for the GRINS Player and Editor.
#
import sys, os
import win32ui, win32con, win32api
from pywinlib.mfc import window, dialog, thread, afxres

import traceback
import longpath

def fix_argv():
	# Turn pathnames into their full NT version
	for i in range(1, len(sys.argv)):
		if os.path.exists(sys.argv[i]):
			sys.argv[i] = longpath.short2longpath(sys.argv[i])

def SafeCallbackCaller(fn, args):
	try:
		return apply(fn, args)
	except SystemExit, rc:
		# We trap a system exit, and translate it to the "official" way to bring down a GUI.
		try:
			rc = int(rc[0])
		except (ValueError, TypeError):
			rc = 0
		win32api.PostQuitMessage(rc)
	except:
		# We trap all other errors, ensure the main window is shown, then
		# print the traceback.
		try:
			win32ui.GetMainFrame().ShowWindow(win32con.SW_SHOW)
		except win32ui.error:
			print "Cant show the main frame!"
		traceback.print_exc()
		return


win32ui.InstallCallbackCaller(SafeCallbackCaller)


# The Main Frame of the application.
class MainFrame(window.MDIFrameWnd):
	sectionPos = "Main Window"
	statusBarIndicators = ( afxres.ID_SEPARATOR, #// status line indicator
	                        afxres.ID_INDICATOR_CAPS,
	                        afxres.ID_INDICATOR_NUM,
	                        afxres.ID_INDICATOR_SCRL,
	                        win32ui.ID_INDICATOR_LINENUM,
	                        win32ui.ID_INDICATOR_COLNUM )

	def OnCreate(self, cs):
		self._CreateStatusBar()
		return 0

	def _CreateStatusBar(self):
		self.statusBar = win32ui.CreateStatusBar(self)
		self.statusBar.SetIndicators(self.statusBarIndicators)
		self.HookCommandUpdate(self.OnUpdatePosIndicator, win32ui.ID_INDICATOR_LINENUM)
		self.HookCommandUpdate(self.OnUpdatePosIndicator, win32ui.ID_INDICATOR_COLNUM)

	def OnUpdatePosIndicator(self, cmdui):
		try:
			childFrame, bIsMaximised = self.MDIGetActive()
			childWnd = childFrame.GetWindow(win32con.GW_CHILD)
			try:
				editControl = childWnd.GetRichEditCtrl()
			except AttributeError:
				try:
					editControl = childWnd.GetEditCtrl()
				except AttributeError:
					if hasattr(childWnd, "hWndScintilla"):
						editControl = childWnd
					else:
						editControl = None
			if editControl:
				startChar, endChar = editControl.GetSel()
				lineNo = editControl.LineFromChar(startChar)
				colNo = endChar - editControl.LineIndex(lineNo)

				if cmdui.m_nID==win32ui.ID_INDICATOR_LINENUM:
					value = "%0*d" % (5, lineNo + 1)
				else:
					value = "%0*d" % (3, colNo + 1)
			else:
				value = " " * 5
		except win32ui.error:
			value = " " * 5

		cmdui.SetText(value)
		cmdui.Enable()


# The application object.
class GrinsApp(thread.WinApp):
	def __init__(self):
		self.oldCallbackCaller = None
		thread.WinApp.__init__(self, win32ui.GetApp() )
		self.idleHandlers = []
		
	def CreateMainFrame(self):
		return MainFrame()

	def LoadMainFrame(self):
		" Create the main applications frame "
		self.frame = self.CreateMainFrame()
		self.SetMainFrame(self.frame)
		self.frame.LoadFrame(win32ui.IDR_MAINFRAME, win32con.WS_OVERLAPPEDWINDOW)
		self.frame.DragAcceptFiles()	# we can accept these.

		self.frame.ShowWindow(win32ui.GetInitialStateRequest());
		self.frame.UpdateWindow();

		self.frame.SetWindowText("GRiNS Debugging Terminal")
		self.HookCommands()

		
	def InitInstance(self):
		#win32ui.MessageBox('InitInstance')
		afx=win32ui.GetAfx()
		afx.OleInit()
		afx.EnableControlContainer()
		win32ui.SetAppName("GRiNS")
		self.LoadMainFrame()
		from pywinlib.framework import interact
		interact.CreateInteractiveWindow()
		# Maximize the interactive window.
		interact.edit.currentView.GetParent().ShowWindow(win32con.SW_MAXIMIZE)

	def Run(self):
		self.BootGrins()
		return self.ExitInstance()

	def ExitInstance(self):
		#win32ui.MessageBox('Exit Instance')
		if self.frame and hasattr(self.frame,'DestroyWindow'):
			self.frame.DestroyWindow()
		self.frame = None
		if hasattr(self,'SetMainFrame'):
			self.SetMainFrame(None)
		import __main__
		if hasattr(__main__,'resdll'):
			del __main__.resdll
		return self.ExitInstanceBase(self)

	def ExitInstanceBase(self):
		" Called as the app dies - too late to prevent it here! "
		win32ui.OutputDebug("Application shutdown\n")
		# Restore the callback manager, if any.
		try:
			win32ui.InstallCallbackCaller(self.oldCallbackCaller)
		except AttributeError:
			pass
		if self.oldCallbackCaller:
			del self.oldCallbackCaller
		self.frame=None	# clean Python references to the now destroyed window object.
		self.idleHandlers = []
		# Attempt cleanup if not already done!
		if self._obj_: self._obj_.AttachObject(None)
		self._obj_ = None
		return 0

	def BootGrins(self):
		raise RuntimeError, "You must subclass this object"

	#
	#
	#

	def HaveIdleHandler(self, handler):
		return handler in self.idleHandlers
	def AddIdleHandler(self, handler):
		self.idleHandlers.append(handler)
	def DeleteIdleHandler(self, handler):
		self.idleHandlers.remove(handler)
	def OnIdle(self, count):
		try:
			ret = 0
			handlers = self.idleHandlers[:] # copy list, as may be modified during loop
			for handler in handlers:
				try:
					thisRet = handler(handler, count)
				except:
					print "Idle handler %s failed" % (`handler`)
					traceback.print_exc()
					print "Idle handler removed from list"
					self.DeleteIdleHandler(handler)
					thisRet = 0
				ret = ret or thisRet
			return ret
		except KeyboardInterrupt:
			pass

	def HookCommands(self):
		self.frame.HookMessage(self.OnDropFiles,win32con.WM_DROPFILES)
		self.HookCommand(self.HandleOnFileOpen,win32ui.ID_FILE_OPEN)
		self.HookCommand(self.HandleOnFileNew,win32ui.ID_FILE_NEW)
		self.HookCommand(self.OnFileMRU,win32ui.ID_FILE_MRU_FILE1)
		self.HookCommand(self.OnHelpAbout,win32ui.ID_APP_ABOUT)
		#self.HookCommand(self.OnHelp, win32ui.ID_HELP_PYTHON)
		#self.HookCommand(self.OnHelp, win32ui.ID_HELP_GUI_REF)
		# Hook for the right-click menu.
		self.frame.GetWindow(win32con.GW_CHILD).HookMessage(self.OnRClick,win32con.WM_RBUTTONDOWN)

	def OnRClick(self,params):
		" Handle right click message "
		# put up the entire FILE menu!
		menu = win32ui.LoadMenu(win32ui.IDR_TEXTTYPE).GetSubMenu(0)
		menu.TrackPopupMenu(params[5]) # track at mouse position.
		return 0

	def OnDropFiles(self,msg):
		" Handle a file being dropped from file manager "
		hDropInfo = msg[2]
		self.frame.SetActiveWindow()	# active us
		nFiles = win32api.DragQueryFile(hDropInfo)
		try:
			for iFile in range(0,nFiles):
				fileName = win32api.DragQueryFile(hDropInfo, iFile)
				win32ui.GetApp().OpenDocumentFile( fileName )
		finally:
			win32api.DragFinish(hDropInfo);

		return 0

	# Command handlers.
	def OnFileMRU( self, id, code ):
		" Called when a File 1-n message is recieved "
		fileName = win32ui.GetRecentFileList()[id - win32ui.ID_FILE_MRU_FILE1]
		win32ui.GetApp().OpenDocumentFile(fileName)

	def HandleOnFileOpen( self, id, code ):
		" Called when FileOpen message is received "
		win32ui.GetApp().OnFileOpen()

	def HandleOnFileNew( self, id, code ):
		" Called when FileNew message is received "
		win32ui.GetApp().OnFileNew()

	def OnHelpAbout( self, id, code ):
		" Called when HelpAbout message is received.  Displays the About dialog. "
		dlg=AboutBox()
		dlg.DoModal()

# The About Box
class AboutBox(dialog.Dialog):
	def __init__(self, idd=win32ui.IDD_ABOUTBOX):
		dialog.Dialog.__init__(self, idd)
	def OnInitDialog(self):
		self.SetDlgItemText(win32ui.IDC_ABOUT_COPYRIGHT_GUI, win32ui.copyright)
		self.SetDlgItemText(win32ui.IDC_ABOUT_COPYRIGHT, sys.copyright)
		# Get the build number
		try:
			ver = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "SOFTWARE\\Python\\Pythonwin\\Build")
			ver = "Pythonwin build " + ver
		except:
			ver = "Unknown build number"
		self.SetDlgItemText(win32ui.IDC_ABOUT_VERSION, ver)


def BootApplication(appClass):

	# Create the application itself.
	gapp = appClass()

	# If we are not hosted by Pythonwin.exe, we need to simulate an MFC startup.
	if win32ui.GetApp().IsInproc():
		#print "Not hosted by pythonwin - simulating MFC startup..."
		#win32ui.MessageBox('Not hosted by pythonwin - simulating MFC startup...')
		rc = gapp.InitInstance()
		#print "InitInstance returned", rc
		if not rc: # None or 0 mean "this is OK"
			gapp.Run()


