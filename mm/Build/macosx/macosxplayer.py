__version__ = "$Id$"

#
# Mac GRiNS Player wrapper
#

DEBUG=0

import sys
import os
import MacOS
if not MacOS.WMAvailable():
	raise 'No access to the window manager'
	
progdir=os.path.split(sys.argv[0])[0]	# This is cmif:build:macosx
if not progdir:
	progdir = os.getcwd()

ID_SPLASH_DIALOG=513
# Assure the resource file is available
from Carbon import Res
try:
	Res.GetResource('DLOG', ID_SPLASH_DIALOG)
except:
	import macresource
	macdir = os.path.join(os.path.split(progdir)[0], 'mac')
	macresource.open_pathname(os.path.join(macdir, 'player.rsrc'), 1)
	macresource.open_pathname(os.path.join(macdir, 'playercontrols.rsrc'), 1)
	macresource.open_pathname(os.path.join(macdir, 'common.rsrc'), 1)
Res.GetResource('DLOG', ID_SPLASH_DIALOG)
	
# Now time for real work.
import string

#
# Set variable for standalone cmif:
#
try:
	import SR
except ImportError:
	STANDALONE=0
else:
	STANDALONE=1
#
# Mangle sys.path. Here are the directives for macfreeze:
#
# macfreeze: path :
# macfreeze: path :::grins:mac
# macfreeze: path :::grins
# macfreeze: path :::common:mac
# macfreeze: path :::common
# macfreeze: path :::lib:mac
# macfreeze: path :::lib
# macfreeze: path :::pylib
#
# and some modules we don't want:
# macfreeze: exclude BandwidthCompute
# macfreeze: exclude X_window
# macfreeze: exclude X_windowbase
# macfreeze: exclude GL_window
# macfreeze: exclude GL_windowbase
# macfreeze: exclude WIN32_window
# macfreeze: exclude WIN32_windowbase
# macfreeze: exclude fastimp
# macfreeze: exclude fm
# macfreeze: exclude gl
# macfreeze: exclude Xlib
# macfreeze: exclude Xt
# macfreeze: exclude Xm
# macfreeze: exclude Xtdefs
# macfreeze: exclude glXconst
# macfreeze: exclude mv
# macfreeze: exclude SOCKS
# macfreeze: exclude signal
# macfreeze: exclude mm
# macfreeze: exclude thread
# macfreeze: exclude SUNAUDIODEV
# macfreeze: exclude Xcursorfont
# macfreeze: exclude FCNTL
# macfreeze: exclude sunaudiodev
# macfreeze: exclude X
# macfreeze: exclude newdir
# macfreeze: exclude glX
# macfreeze: exclude dummy_window
# macfreeze: exclude mpegex
# macfreeze: exclude al
# macfreeze: exclude imageex
# macfreeze: exclude Xmd
# macfreeze: exclude VFile
# macfreeze: exclude NTVideoDuration
# macfreeze: exclude MpegDuration
# macfreeze: exclude fcntl
# macfreeze: exclude MovieChannel
# macfreeze: exclude MpegChannel
# macfreeze: exclude MidiChannel
# macfreeze: exclude VcrChannel
# macfreeze: exclude MPEGVideoChannel
# macfreeze: exclude audio.hcom
# macfreeze: exclude audio.svx8
# macfreeze: exclude audio.sdnr
# macfreeze: exclude audio.sndt
# macfreeze: exclude audio.sndr
# macfreeze: exclude audio.voc
# macfreeze: exclude audio.Error
# macfreeze: exclude msvcrt
# macfreeze: exclude termios
# macfreeze: exclude TERMIOS
# macfreeze: exclude cmifex
# macfreeze: exclude readline
# macfreeze: exclude CORBA.services
# macfreeze: exclude win32ig
# macfreeze: exclude win32ui
# macfreeze: optional rma
# macfreeze: exclude HierarchyView
# macfreeze: exclude dshow
# macfreeze: exclude producer
# macfreeze: exclude SMILTreeWrite
# macfreeze: exclude linuxaudiodev
#
# And here's the code for non-standalone version of the editor:

if not STANDALONE:
	# For now:
	builddir=os.path.split(progdir)[0]		# this is cmif:build
	CMIFDIR=os.path.split(builddir)[0]		# and this is cmif
	
	CMIFPATH = [
		os.path.join(CMIFDIR, "mac"),
		os.path.join(CMIFDIR, "grins", "mac"),
		os.path.join(CMIFDIR, "grins"),
		os.path.join(CMIFDIR, "common", "mac"),
		os.path.join(CMIFDIR, "common"),
		os.path.join(CMIFDIR, "lib", "mac"),
		os.path.join(CMIFDIR, "lib"),
	# Overrides for Python distribution
		os.path.join(CMIFDIR, "pylib"),
	]
	sys.path[0:0] = CMIFPATH
	
	os.environ["CMIF"] = CMIFDIR
	#os.environ["CHANNELDEBUG"] = "1"

# Next, show the splash screen
import splash
splash.splash('loadprog')
import settings
license = settings.get('license')
user = settings.get('license_user')
org = settings.get('license_organization')
splash.setuserinfo(user, org, license)
	
if len(sys.argv) > 1 and sys.argv[1] == '-p':
	profile = 1
	del sys.argv[1]
	print '** Profile **'
else:
	profile = 0


##import trace
##trace.set_trace()

##if len(sys.argv) < 2:
##	splash.splash()
##	fss, ok = macfs.PromptGetFile('SMIL file (cancel for URL)', 'TEXT')
##	if ok:
##		sys.argv = ["macgrins", fss.as_pathname()]
##	else:
##		import EasyDialogs
##		url = EasyDialogs.AskString("SMIL URL")
##		if url is None:
##			sys.exit(0)
##		sys.argv = ["macgrins", url]
		
no_exception=0
try:
	if profile:
		import profile
		proffilename = EasyDialogs.AskFileForSave("Profile output:")
		if not proffilename: sys.exit(1)
		profile.run("import grins", proffilename)
	else:
		import grins
	no_exception=1
except SystemExit:
	no_exception=1
