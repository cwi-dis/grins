__version__ = "$Id$"

#
# Mac CMIF Player wrapper
#

# First, immedeately disable the console window
import sys
if len(sys.argv) > 1 and sys.argv[1] == '-v':
	del sys.argv[1]
	print '** Verbose **'
else:
	import quietconsole
	quietconsole.install()

# Next, show the splash screen
import MacOS
MacOS.splash(513)

# Now time for real work.
import os
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
	
if len(sys.argv) > 1 and sys.argv[1] == '-p':
	profile = 1
	del sys.argv[1]
	print '** Profile **'
else:
	profile = 0

if len(sys.argv) < 2:
	MacOS.splash()
	fss, ok = macfs.StandardGetFile('TEXT')
	if not ok: sys.exit(0)
	
	sys.argv = ["maccmifplay", fss.as_pathname()]

##print "ENVIRON:", os.environ
##print "PATH:", sys.path

if profile:
	import profile
	fss, ok = macfs.StandardPutFile("Profile output:")
	if not ok: sys.exit(1)
	profile.run("import main", fss.as_pathname())
else:
	import main
