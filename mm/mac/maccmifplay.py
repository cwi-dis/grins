#
# Mac CMIF Player wrapper
#
# This new comment line tests MacCVS in remote mode
print
import MacOS
MacOS.splash(512)
import os
import sys
import string
import macfs

#
# Set variable for standalone cmif:
#
try:
	import MMNode
except ImportError:
	STANDALONE=0
else:
	STANDALONE=1
	print 'Standalone, path=', sys.path

if not STANDALONE:
	# For now:
	progdir=os.path.split(sys.argv[0])[0]
	CMIFDIR=os.path.split(progdir)[0]
	
	CMIFPATH = [
		CMIFDIR+":mac",
		CMIFDIR+":player",
		CMIFDIR+":common",
		CMIFDIR+":lib",
	# Overrides for Python distribution
		CMIFDIR+":pylib",
		CMIFDIR+":pylib:audio"
	]
	sys.path[0:0] = CMIFPATH
	
	os.environ["CMIF"] = CMIFDIR
	#os.environ["CHANNELDEBUG"] = "1"

if len(sys.argv) < 2:
	MacOS.splash()
	fss, ok = macfs.StandardGetFile('TEXT')
	if not ok: sys.exit(0)
	
	sys.argv = ["maccmifplay", fss.as_pathname()]

##print "ENVIRON:", os.environ
##print "PATH:", sys.path

import main
