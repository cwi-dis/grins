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

#import pdb
#pdb.set_trace()

#import fixreg
import os
import sys
import string
import win32api, win32con
from win32con import *

# For now:
#progdir=os.path.split(sys.argv[0])[0]
#CMIFDIR=os.path.split(progdir)[0]

import win32ui
h1 = win32ui.GetMainFrame()
#h1.ShowWindow(win32con.SW_HIDE)


#CMIFDIR = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Python\\PythonCore\\CmifPath")
CMIFDIR = win32api.RegQueryValue(win32con.HKEY_LOCAL_MACHINE, "Software\\Chameleon\\CmifPath")
CMIFPATH = [
        os.path.join(CMIFDIR, 'editor\\win32'),
        os.path.join(CMIFDIR, 'editor'),
        os.path.join(CMIFDIR, 'common\\win32'),
        os.path.join(CMIFDIR, 'common'),
        os.path.join(CMIFDIR, 'lib\\win32'),
        os.path.join(CMIFDIR, 'lib'),
        os.path.join(CMIFDIR, 'pylib'),
        os.path.join(CMIFDIR, 'pylib\\audio'),
]
CMIF_USE_WIN32="ON"
#CHANNELDEBUG="ON"

# create blank html file
dir1 = CMIFDIR+'\\tmp.htm'
fp = open(dir1, 'w')
fp.write('<HTML> </HTML> ')
fp.close()

# create error html file
dir2 = CMIFDIR+'\\error.htm'
fp = open(dir2, 'w')
fp.write(' ')
fp.close()


sys.path[0:0] = CMIFPATH

os.environ["CMIF"] = CMIFDIR
#os.environ["CHANNELDEBUG"] = "ON"
os.environ["CMIF_USE_WIN32"] = "ON"

# run the given cmif file
#import main

import cmifex
for i in range(1,len(sys.argv)):
    sys.argv[i]=cmifex.ToLongName(sys.argv[i])

import cmifed
