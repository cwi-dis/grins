#
# Mac CMIF Player wrapper
#
import os
import sys
import string
import macfs
import addpack

# For now:
CMIFDIR="Moes:Development:Jack:cmif"

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

os.environ["CMIF"] = CMIFDIR
os.environ["CMIF_USE_DUMMY"] = "1"
os.environ["CHANNELDEBUG"] = "1"

fss, ok = macfs.StandardGetFile('TEXT')
if not ok: sys.exit(0)

sys.argv = ["maccmifplay", fss.as_pathname()]

print "ENVIRON:", os.environ
print "PATH:", sys.path

import main
