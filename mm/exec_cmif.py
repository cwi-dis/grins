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

print 'Running CMIF Multimedia presentation'
if len(sys.argv)>1:
	print sys.argv[1]
	
try:
	CMIFDIR = win32api.RegQueryValue(HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifPath")
except win32api.error:
	CMIFDIR = win32api.GetFullPathName(os.path.join(os.path.split(sys.argv[0])[0], "." ))

# TEMP TEST FOLDER
print "Main GRiNS directory is", CMIFDIR

CMIFPATH = [
	os.path.join(CMIFDIR, 'grins\\win32'),
	os.path.join(CMIFDIR, 'common\\win32'),
	os.path.join(CMIFDIR, 'lib\\win32'),
	os.path.join(CMIFDIR, 'grins'),
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
import win32ui
try:
	import cmifex
	dllPath = os.path.split(cmifex.__file__)[0]
except AttributeError:
	# No __file__ attribute - must be frozen or built-in!
	dllPath = ""

try:
	dll = win32ui.LoadLibrary(os.path.join(dllPath, "GRiNSRes.dll"))
	dll.AttachToMFC()
except win32ui.error:
	win32ui.MessageBox("The application resource DLL 'GRiNSRes.dll' can not be located\r\n\r\nPlease correct this problem, and restart the application")
	# For now just continue!?!?!

# run the given cmif file
#import main
import win32ui # Import this before any dependants try to import!
import grins
