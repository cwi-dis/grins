# intpyapp.py  - Interactive Python application class
#
import win32con
import win32api
import win32ui
import __main__
import sys
import string
import app
import traceback
from pywin.mfc import window, afxres, dialog
import commctrl

lastLocateFileName = ".py" # used in the "File/Locate" dialog...

class MainFrame(app.MainFrame):
	def OnCreate(self, createStruct):
		if app.MainFrame.OnCreate(self, createStruct)==-1:
			return -1
		style = win32con.WS_CHILD | win32con.WS_VISIBLE | \
		    afxres.CBRS_SIZE_DYNAMIC | afxres.CBRS_TOP | afxres.CBRS_TOOLTIPS | afxres.CBRS_FLYBY

		tb = win32ui.CreateToolBar (self, style)
		tb.ModifyStyle(0, commctrl.TBSTYLE_FLAT)
		tb.LoadToolBar(win32ui.IDR_MAINFRAME)
		tb.EnableDocking(afxres.CBRS_ALIGN_ANY)
		tb.SetWindowText("Standard")
		self.EnableDocking(afxres.CBRS_ALIGN_ANY)
		self.DockControlBar(tb)
		self.LoadBarState("ToolbarDefault")
	def OnDestroy(self, msg):
		app.MainFrame.OnDestroy(self, msg)
		self.SaveBarState("ToolbarDefault")


class InteractivePythonApp(app.CApp):
#	def Run(self):
#		return self._obj_.Run()

	def HookCommands(self):
		app.CApp.HookCommands(self)
		self.HookCommand(self.OnViewBrowse,win32ui.ID_VIEW_BROWSE)
		self.HookCommand(self.OnFileImport,win32ui.ID_FILE_IMPORT)
		self.HookCommand(self.OnFileCheck,win32ui.ID_FILE_CHECK)
		self.HookCommandUpdate(self.OnUpdateFileCheck, win32ui.ID_FILE_CHECK)
		self.HookCommand(self.OnFileRun,win32ui.ID_FILE_RUN)
		self.HookCommand(self.OnFileLocate,win32ui.ID_FILE_LOCATE)
		self.HookCommand(self.OnInteractiveWindow, win32ui.ID_VIEW_INTERACTIVE)
		self.HookCommandUpdate(self.OnUpdateInteractiveWindow, win32ui.ID_VIEW_INTERACTIVE)
		self.HookCommand(self.OnViewOptions, win32ui.ID_VIEW_OPTIONS)
		self.HookCommand(self.OnHelpIndex, afxres.ID_HELP_INDEX)
		
	def CreateMainFrame(self):
		return MainFrame()
		
	def MakeExistingDDEConnection(self):
		# Use DDE to connect to an existing instance
		# Return None if no existing instance
		try:
			import intpydde
		except ImportError:
			# No dde support!
			return None
		conv = intpydde.CreateConversation(self.ddeServer)
		try:
			conv.ConnectTo("Pythonwin", "System")
			return conv
		except intpydde.error:
			return None
	
	def InitDDE(self):
		# Do all the magic DDE handling.  
		# Returns TRUE if we have pumped the arguments to our
		# remote DDE app, and we should terminate.
		try:
			import intpydde
		except ImportError:
			self.ddeServer = None
			intpydde = None
		if intpydde is not None:
			self.ddeServer = intpydde.DDEServer(self)
			self.ddeServer.Create("Pythonwin", intpydde.CBF_FAIL_SELFCONNECTIONS )
			try:
				# If there is an existing instance, pump the arguments to it.
				connection = self.MakeExistingDDEConnection()
				if connection is not None:
					if self.ProcessArgs(sys.argv, connection) is None:
						return 1
			except:
				win32ui.MessageBox("There was an error in the DDE conversation with Pythonwin")
				traceback.print_exc()

	def InitInstance(self):
		# Allow "/nodde" to optimize this!
		if "/nodde" not in sys.argv:
			if self.InitDDE():
				return 1 # A remote DDE client is doing it for us!
		else:
			self.ddeServer = None

		win32ui.SetRegistryKey('Python') # MFC automatically puts the main frame caption on!
		app.CApp.InitInstance(self)

		# Create the icon toolbar			
		win32ui.CreateDebuggerThread()
		
		# Allow Pythonwin to host OCX controls.
		win32ui.EnableControlContainer()
		
		# Display the interactive window if the user wants it.
		import interact
		interact.CreateInteractiveWindowUserPreference()
		
		# Load the modules we use internally.
		self.LoadSystemModules()
		
		# Load additional module the user may want.
		self.LoadUserModules()
		
		# Finally process the command line arguments.
		self.ProcessArgs(sys.argv)
		
	def ExitInstance(self):
		win32ui.DestroyDebuggerThread()
		import interact
		interact.DestroyInteractiveWindow()
		if self.ddeServer is not None:
			self.ddeServer.Shutdown()
			self.ddeServer = None
		return app.CApp.ExitInstance(self)

	def Activate(self):
		# Bring to the foreground.  Mainly used when another app starts up, it asks
		# this one to activate itself, then it terminates.
		frame = win32ui.GetMainFrame()
		frame.SetForegroundWindow()
		if frame.GetWindowPlacement()[1]==win32con.SW_SHOWMINIMIZED:
			frame.ShowWindow(win32con.SW_RESTORE)
		
	def ProcessArgs(self, args, dde = None):
		# If we are going to talk to a remote app via DDE, then
		# activate it!
		if dde is not None: dde.Exec("self.Activate()")
		if len(args) and args[0]=='/nodde': del args[0] # already handled.
		if len(args)<1 or not args[0]: # argv[0]=='' when started without args, just like Python.exe!
			return
		try:
			if args[0] and args[0][0]!='/':
				argStart = 0
				argType = string.lower(win32ui.GetProfileVal("Python","Default Arg Type","/edit"))
			else:
				argStart = 1
				argType = args[0]
			if argStart >= len(args):
				raise TypeError, "The command line requires an additional arg."
			if argType=="/edit":
				# Load up the default application.
				if dde:
					fname = win32api.GetFullPathName(args[argStart])
					print fname
					dde.Exec("win32ui.GetApp().OpenDocumentFile(%s)" % (`fname`))
				else:
					win32ui.GetApp().OpenDocumentFile(args[argStart])
			elif argType=="/rundlg":
				if dde:
					dde.Exec("import scriptutils;scriptutils.RunScript('%s', '%s', 1)" % (args[argStart], string.join(args[argStart+1:])))
				else:
					import scriptutils
					scriptutils.RunScript(args[argStart], string.join(args[argStart+1:]))
			elif argType=="/run":
				if dde:
					dde.Exec("import scriptutils;scriptutils.RunScript('%s', '%s', 0)" % (args[argStart], string.join(args[argStart+1:])))
				else:
					import scriptutils
					scriptutils.RunScript(args[argStart], string.join(args[argStart+1:]), 0)
			elif argType=="/app":
				raise RuntimeError, "/app only supported for new instances of Pythonwin.exe"
			elif argType=='/new': # Allow a new instance of Pythonwin
				return 1
			elif argType=='/dde': # Send arbitary command
				if dde is not None:
					dde.Exec(args[argStart])
				else:
					win32ui.MessageBox("The /dde command can only be used\r\nwhen Pythonwin is already running")
			else:
				raise TypeError, "Command line arguments not recognised"
		except:
			typ, val, tb = sys.exc_info()
			print "There was an error processing the command line args"
			traceback.print_exception(typ, val, tb, None, sys.stdout)
			win32ui.OutputDebug("There was a problem with the command line args - %s: %s" % (`typ`,`val`))


	def LoadSystemModules(self):
		self.DoLoadModules("editor")

	def LoadUserModules(self, moduleNames = None):
		# Load the users modules.
		if moduleNames is None:
			default = "sgrepmdi,bitmap"
			moduleNames=win32ui.GetProfileVal('Python','Startup Modules',default)
		self.DoLoadModules(moduleNames)

	def DoLoadModules(self, moduleNames): # ", sep string of module names.
		if not moduleNames: return
		modules = string.splitfields(moduleNames,",")
		for module in modules:
			try:
				exec "import "+module
			except: # Catch em all, else the app itself dies! 'ImportError:
				traceback.print_exc()
				msg = 'Startup import of user module "%s" failed' % module
				print msg
				win32ui.MessageBox(msg)

	#
	# DDE Callback
	#
	def OnDDECommand(self, command):
#		print "DDE Executing", `command`
		try:
			exec command + "\n"
		except:
			print "ERROR executing DDE command: ", command
			traceback.print_exc()
			raise

	#
	# General handlers
	#
	def OnViewBrowse( self, id, code ):
		" Called when ViewBrowse message is received "
		from pywin.mfc import dialog
		from pywin.tools import browser
		obName = dialog.GetSimpleInput('Object', '__builtins__', 'Browse Python Object')
		if obName is None:
			return
		try:
			browser.Browse(eval(obName, __main__.__dict__, __main__.__dict__))
		except NameError:
			win32ui.MessageBox('This is no object with this name')
		except AttributeError:
			win32ui.MessageBox('The object has no attribute of that name')
		except:
			win32ui.MessageBox('This object can not be browsed')
		
	def OnFileImport( self, id, code ):
		" Called when a FileImport message is received. Import the current or specified file"
		import scriptutils
		scriptutils.ImportFile()

	def OnFileCheck( self, id, code ):
		" Called when a FileCheck message is received. Check the current file."
		import scriptutils
		scriptutils.CheckFile()

	def OnUpdateFileCheck(self, cmdui):
		import scriptutils
		cmdui.Enable( scriptutils.GetActiveFileName(0) is not None )
	
	def OnFileRun( self, id, code ):
		" Called when a FileRun message is received. "
		import scriptutils
		showDlg = win32api.GetKeyState(win32con.VK_SHIFT) >= 0
		scriptutils.RunScript(None, None, showDlg)

	def OnFileLocate( self, id, code ):
		from pywin.mfc import dialog
		import scriptutils
		import os
		global lastLocateFileName # save the new version away for next time...

		# Loop until a good name, or cancel
		while 1:
			name = dialog.GetSimpleInput('File name', lastLocateFileName, 'Locate Python File')
			if name is None: # Cancelled.
				break
			lastLocateFileName = name
			# if ".py" supplied, rip it off!
			if string.lower(lastLocateFileName[-3:])=='.py':
				lastLocateFileName = lastLocateFileName[:-3]
			lastLocateFileName = string.translate(lastLocateFileName, string.maketrans(".","\\"))
			newName = scriptutils.LocatePythonFile(lastLocateFileName)
			if newName is None:
				win32ui.MessageBox("The file '%s' can not be located" % lastLocateFileName)
			else:
				win32ui.GetApp().OpenDocumentFile(newName)
				break

	# Display all the "options" proprety pages we can find				
	def OnViewOptions(self, id, code):
		sheet = dialog.PropertySheet("Pythonwin Options")
		# Add property pages we know about that need manual work.
		from pywin.dialogs import ideoptions
		import interact
		sheet.AddPage( ideoptions.OptionsPropPage() )
		
		import toolmenu
		sheet.AddPage( toolmenu.ToolMenuPropPage() )

		# Get other dynamic pages from templates.
		pages = []
		for template in self.GetDocTemplateList():
			try:
				pages = pages + template.GetPythonPropertyPages()
			except AttributeError:
				# Template does not provide property pages!
				pass

		# Now simply add the pages, and display the dialog.
		for page in pages:
			sheet.AddPage(page)

		sheet.DoModal()
				
	def OnInteractiveWindow(self, id, code):
		# toggle the existing state.
		import interact
		if interact.edit is None:
			interact.CreateInteractiveWindow()
		else:
			# There is an interactive window object, but possibly not a window itself.
			# (ie, the window may have been closed, but the object remains, allowing us
			# to retain the text!)
			try:
				interact.edit.currentView.GetSafeHwnd()
				# Is currently open
				interact.edit.currentView.GetParent().DestroyWindow()
			except:
				interact.edit.Create()
	
	def OnUpdateInteractiveWindow(self, cmdui):
		try:
			interact=sys.modules['pywin.framework.interact']
			try:
				interact.edit.currentView.GetSafeHwnd()
				state = 1
			except:
				state = 0
		except KeyError:
			state = 0
		cmdui.Enable()
		cmdui.SetCheck(state)
		# while I track down memory leaks...
		sys.last_traceback = None
		sys.last_type = None
		sys.last_value = None
			
	def OnHelpIndex( self, id, code ):
		import help
		help.SelectAndRunHelpFile()

# As per the comments in app.py, this use is depreciated.
# app.AppBuilder = InteractivePythonApp

# Now all we do is create the application
thisApp = InteractivePythonApp()
