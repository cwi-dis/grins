# grins_app_core.py  - The Pythonwin Application class for the GRINS Player and Editor.
#
import sys, os
import win32ui, win32con
from pywin.framework import app, intpyapp
import traceback

try:
	os.environ['GRINS_REMOTE_TRACE']
	bRemoteTracing = 1
except KeyError:
	bRemoteTracing = 0

if bRemoteTracing:
	import win32traceutil

def SafeCallbackCaller(fn, args):
	try:
		return apply(fn, args)
	except SystemExit, rc:
		# We trap a system exit, and translate it to the "official" way to bring down a GUI.
		try:
			rc = int(rc[0])
		except (ValueError, TypeError):
			rc = 0
		#import win32api
		#win32api.PostQuitMessage(rc)
		# use afx to free com/ole libs
		Afx=win32ui.GetAfx()
		Afx.PostQuitMessage(rc)
	
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

# AppParent = app.CApp 
class GrinsApp(app.CApp):
	def HookCommands(self):
		app.CApp.HookCommands(self)
		
	def CreateMainFrame(self):
		return app.MainFrame()

	def LoadMainFrame(self):
		" Create the main applications frame "
		self.frame = self.CreateMainFrame()
		self.SetMainFrame(self.frame)
		self.frame.LoadFrame(win32ui.IDR_MAINFRAME, win32con.WS_OVERLAPPEDWINDOW)
		self.frame.DragAcceptFiles()	# we can accept these.

#		self.frame.ShowWindow(win32ui.GetInitialStateRequest());
#		self.frame.UpdateWindow();
		
		self.frame.SetWindowText("GRiNS Debugging Terminal")
		self.HookCommands()

		
	def InitInstance(self):
		afx=win32ui.GetAfx()
		afx.OleInit()
		afx.EnableControlContainer()
		win32ui.SetAppName("GRiNS")
		self.LoadMainFrame()
		if not bRemoteTracing:
			from pywin.framework import interact
			interact.CreateInteractiveWindow()
			# Maximize the interactive window.
			interact.edit.currentView.GetParent().ShowWindow(win32con.SW_MAXIMIZE)
		# Boot up CMIF!
		self.BootGrins()

	def ExitInstance(self):
#		rc = app.CApp.ExitInstance(self)
		if self.frame:
			self.frame.DestroyWindow()
			self.frame = None
		self.SetMainFrame(None)
		return 0

	def BootGrins(self):
		raise RuntimeError, "You must subclass this object"

def BootApplication(appClass):

	# Create the application itself.
	gapp = appClass()

	# If we are not hosted by Pythonwin.exe, we need to simulate an MFC startup.
	if win32ui.GetApp().IsInproc():
		print "Not hosted by pythonwin - simulating MFC startup..."
		rc = gapp.InitInstance()
		print "InitInstance returned", rc
		if not rc: # None or 0 mean "this is OK"
			gapp.Run()
			print "Calling ExitInstance"
			gapp.ExitInstance()


