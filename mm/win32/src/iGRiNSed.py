# Run GRiNS interactively
[PLAYER,EDITOR]=range(2)


WHAT=EDITOR
CMIFDIR="d:\\cmif"

#
# Win32 CMIF Editor wrapper
#
# Can be executed from "python.exe" or "wpython.exe"
# Pythonwin should use "grins_app.py", which uses this.

import os
import sys
import string
import win32api
from win32con import *
import win32ui
import traceback

def SafeCallbackCaller(fn, args):
	try:
		return apply(fn, args)
	except SystemExit, rc:
		# We trap a system exit, and translate it to the "official" way to bring down a GUI.
		try:
			rc = int(rc[0])
		except (ValueError, TypeError):
			rc = 0
		# use afx to unload com/ole lib
		(win32ui.GetAfx()).PostQuitMessage(rc)
	except:
		# We trap all other errors, ensure the main window is shown, then
		# print the traceback.
		try:
			win32ui.GetMainFrame().ShowWindow(SW_SHOW)
		except win32ui.error:
			print "Cant show the main frame!"
		traceback.print_exc()
		return


win32ui.InstallCallbackCaller(SafeCallbackCaller)

def Boot( bEditor = 0 ):
	print 'Running CMIF Multimedia presentation'
	if len(sys.argv)>1:
		print sys.argv[1]
	
	#CMIFDIR = win32api.GetFullPathName(os.path.join(os.path.split(sys.argv[0])[0], "." ))
	
	# TEMP TEST FOLDER
	print "Main GRiNS directory is", CMIFDIR
	if bEditor:
		specificPath = "editor"
	else:
		specificPath = "grins"

	CMIFPATH = [
		os.path.join(CMIFDIR, '%s\\win32' % specificPath),
		os.path.join(CMIFDIR, 'common\\win32'),
		os.path.join(CMIFDIR, 'lib\\win32'),
		os.path.join(CMIFDIR, '%s' % specificPath),
		os.path.join(CMIFDIR, 'common'),
		os.path.join(CMIFDIR, 'lib'),
		os.path.join(CMIFDIR, 'pylib'),
		os.path.join(CMIFDIR, 'pylib\\audio'),
		os.path.join(CMIFDIR, 'win32\\src\\Build'),
	]
	CMIF_USE_WIN32="ON"
	#CHANNELDEBUG="ON"

	sys.path[0:0] = CMIFPATH

	os.environ["CMIF"] = CMIFDIR
	#os.environ["CHANNELDEBUG"] = "ON"
	os.environ["CMIF_USE_WIN32"] = "ON"
	os.environ['GRiNSApp']='GRiNSed'

	# Locate the GRiNSRes.dll file.  This is presumably in the same directory as
	# the extensionmodules, or if frozen, in the main directory
	# This call allows Pythonwin to automatically find resources in it.
	import win32ui
	print "win32ui loaded from:",win32ui.__file__
	dllPath = os.path.split(win32ui.__file__)[0]
	try:
		global dll
		dll = win32ui.LoadLibrary(os.path.join(dllPath, "GRiNSRes.dll"))
		print "Loaded", dll, "from", dllPath
		dll.AttachToMFC()
	except win32ui.error:
		win32ui.MessageBox("The application resource DLL 'GRiNSRes.dll' can not be located\r\n\r\nPlease correct this problem, and restart the application")
		# For now just continue!?!?!

	# run the given cmif file
	if bEditor:
		import cmifed
	else:
		import grins

Boot(WHAT)

