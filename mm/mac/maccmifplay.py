#
# Mac CMIF Player wrapper
#
import os
import sys
import string
import macfs
import addpack

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

addpack.addpack('Tools')
addpack.addpack('bgen')
addpack.addpack('snd')
addpack.addpack('evt')
addpack.addpack('win')

os.environ["CMIF"] = CMIFDIR
#os.environ["CHANNELDEBUG"] = "1"

fss, ok = macfs.StandardGetFile('TEXT')
if not ok: sys.exit(0)

sys.argv = ["maccmifplay", fss.as_pathname()]

print "ENVIRON:", os.environ
print "PATH:", sys.path

import main
