#
# DOS  CMIF Player wrapper
#
# d:\cmifdoc\ams\amsmpeg.cmif
# d:\cmifdoc\ams\amsmpeg2.cmif
# d:\cmifdoc\ams\amsmpeg4.cmif
# d:\cmifdoc\anchor.cmif
# d:\cmifdoc\anchort.cmif
# d:\cmifdoc\mondrian\mon2.cmif
# d:\cmifdoc\cartermill\meddir.cmif

import os
import sys
import string
import win32api, win32con
from win32con import *

print 'Running CMIF Multimedia presentation'
if len(sys.argv)>1:
	print sys.argv[1]
	
# For now:
#progdir=os.path.split(sys.argv[0])[0]
#CMIFDIR=os.path.split(progdir)[0]

try:
	CMIFDIR = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifPath")
except win32api.error:
	CMIFDIR = win32api.GetFullPathName(os.path.join(os.path.split(sys.argv[0])[0], "." ))

# TEMP TEST FOLDER
print "CMIFDIR = ", CMIFDIR

CMIFPATH = [
	os.path.join(CMIFDIR, 'grins\\win32'),
	os.path.join(CMIFDIR, 'grins'),
	os.path.join(CMIFDIR, 'common\\win32'),
	os.path.join(CMIFDIR, 'common'),
	os.path.join(CMIFDIR, 'lib\\win32'),
	os.path.join(CMIFDIR, 'lib'),
	os.path.join(CMIFDIR, 'pylib'),
	os.path.join(CMIFDIR, 'pylib\\audio'),
	os.path.join(CMIFDIR, 'PyDLLs'),
]
CMIF_USE_WIN32="ON"
#CHANNELDEBUG="ON"

sys.path[0:0] = CMIFPATH

os.environ["CMIF"] = CMIFDIR
#os.environ["CHANNELDEBUG"] = "ON"
os.environ["CMIF_USE_WIN32"] = "ON"

# run the given cmif file
#import main
print "sys.argv-->", sys.argv
import cmifex
for i in range(1,len(sys.argv)):
	sys.argv[i]=cmifex.ToLongName(sys.argv[i])
print "long sys.argv-->", sys.argv

import grins
