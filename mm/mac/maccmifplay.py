#
# Mac CMIF Player wrapper
#
# This new comment line tests MacCVS in remote mode
import os
import sys
import string
import macfs

# For now:
progdir=os.path.split(sys.argv[0])[0]
CMIFDIR=os.path.split(progdir)[0]

CMIFPATH = [
	CMIFDIR+":mac",
	CMIFDIR+":player",
	CMIFDIR+":common",
	CMIFDIR+":lib"
]
sys.path[0:0] = CMIFPATH

os.environ["CMIF"] = CMIFDIR
#os.environ["CHANNELDEBUG"] = "1"

print

if len(sys.argv) < 2:
	fss, ok = macfs.StandardGetFile('TEXT')
	if not ok: sys.exit(0)
	
	sys.argv = ["maccmifplay", fss.as_pathname()]

##print "ENVIRON:", os.environ
##print "PATH:", sys.path

import main
