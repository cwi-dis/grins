# Win32 CMIF script to run cmif applications interactively
# Executed from "Pythonwin.exe"
# cmd: Pythonwin /run iGRiNS.py

[PLAYER,EDITOR,SUBSYSTEM]=range(3)


##################### Settings

WHAT=EDITOR  # <-- What to run

# if WHAT is SUBSYSTEM specify subsystemModuleName
subsystemModuleName='dslab'


# Global Application Object
toplevel=None

##################### Main Script
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

def Boot(what = 0):
	print 'Running CMIF Multimedia presentation'
	#if len(sys.argv)>1:
	#	print sys.argv[1]
	
	CMIFDIR=GuessCMIFRoot()

	# TEMP TEST FOLDER
	print "Main GRiNS directory is", CMIFDIR

	if what==PLAYER:
		specificPath = "grins"
		os.environ['GRiNSApp']='GRiNS'
	else:
		specificPath = "editor"
		os.environ['GRiNSApp']='GRiNSed'


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
	sys.path[0:0] = CMIFPATH

	os.environ["CMIF"] = CMIFDIR
	os.environ["CMIF_USE_WIN32"] = "ON"
	if not os.environ.has_key('HOME'):
		os.environ['HOME']=CMIFDIR
	

	# Locate the GRiNSRes.dll file.  This is presumably in the same directory as
	# the extensionmodules, or if frozen, in the main directory
	# This call allows Pythonwin to automatically find resources in it.
	import win32ui
	print "win32ui loaded from:",win32ui.__file__
	dllPath = os.path.split(win32ui.__file__)[0]
	try:
		global resdll
		resdll = win32ui.LoadLibrary(os.path.join(dllPath, "GRiNSRes.dll"))
		print "Loaded", resdll, "from", dllPath
		resdll.AttachToMFC()
	except win32ui.error:
		win32ui.MessageBox("The application resource DLL 'GRiNSRes.dll' can not be located\r\n\r\nPlease correct this problem, and restart the application")
		# For now just continue!?!?!
	# run the given cmif file
	if what==PLAYER:
		import grins
	elif what==SUBSYSTEM:
		exec 'import %s\n' % subsystemModuleName
	else:
		import cmifed


def GuessCMIFRoot():
	selfDir = win32api.GetFullPathName(os.path.join(os.path.split(sys.argv[0])[0], "." ))
	print 'selfDir',selfDir
	l=string.split(selfDir,'\\')
	found=0;dir=''
	for s in l:
		dir=dir+s
		if s=='cmif':
			found=1
			break
		dir=dir+'\\'
	if found:return dir
	return 'd:\\ufs\\mm\\cmif'

Boot(WHAT)
