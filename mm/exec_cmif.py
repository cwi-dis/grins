#
# Win32 CMIF Player wrapper
#
# Can be executed from "python.exe" or "wpython.exe"
# Pythonwin should use "grins_app.py", which uses this.

import os
import sys
import string
import win32api
from win32con import *

from __main__ import resdll

def Boot( bEditor = 0 ):
	CMIFDIR = win32api.GetFullPathName(os.path.join(os.path.split(sys.argv[0])[0], "." ))

	# TEMP TEST FOLDER
	if bEditor:
		specificPath = "editor"
		os.environ['GRiNSApp']='GRiNSed'
	else:
		specificPath = "grins"
		os.environ['GRiNSApp']='GRiNS'

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

	# Locate the GRiNSRes.dll file.  This is presumably in the same directory as
	# the extensionmodules, or if frozen, in the main directory
	# This call allows Pythonwin to automatically find resources in it.
	from version import registrykey, registryname, dllname
	import win32ui
	dllPath = os.path.split(win32ui.__file__)[0]
	win32ui.GetWin32Sdk().SetCurrentDirectory(dllPath)
	try:
		global resdll
		resdll = win32ui.LoadLibrary(os.path.join(dllPath, dllname))
		resdll.AttachToMFC()
	except win32ui.error:
		win32ui.MessageBox("The application resource DLL '%s' can not be located\r\n\r\nPlease correct this problem, and restart the application" % dllname)
		# For now just continue!?!?!

	# set app registry root to GRiNS
	win32ui.SetAppName(registryname)
	win32ui.SetRegistryKey(registrykey)

	# run the given cmif file
	if bEditor:
		import cmifed
	else:
		import grins
