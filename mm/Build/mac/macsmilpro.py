__version__ = "$Id$"

#
# Mac GRiNS for SMIL wrapper
#

# First, immedeately disable the console window
import sys
DEBUG=0
if DEBUG:
	print '** Verbose **'
	quietconsole=None
elif len(sys.argv) > 1 and sys.argv[1] == '-v':
	del sys.argv[1]
	print '** Verbose **'
	quietconsole=None
else:
	import quietconsole
	quietconsole.install()
	
# XXXX Temp: enable Navigation
import macfsn
macfsn._install()

ID_SPLASH_DIALOG=513
# XXXX Debugging code: assure the resource file is available
from Carbon import Res
try:
	Res.GetResource('DLOG', ID_SPLASH_DIALOG)
except:
	Res.FSpOpenResFile(':macsmilpro.rsrc', 0)
	Res.FSpOpenResFile(':editor.rsrc', 0)
	Res.FSpOpenResFile(':playercontrols.rsrc', 0)
	Res.FSpOpenResFile(':common.rsrc', 0)
	Res.FSpOpenResFile(':editorballoons.rsrc', 0)
Res.GetResource('DLOG', ID_SPLASH_DIALOG)

# Now time for real work.
import os
import string
import macfs

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
# macfreeze: path :::editor:smil10
# macfreeze: path :::editor:mac
# macfreeze: path :::editor
# macfreeze: path :::common:mac
# macfreeze: path :::common
# macfreeze: path :::lib:mac
# macfreeze: path :::lib
# macfreeze: path :::pylib
# xxxx macfreeze: path :::mmpython:producer:mac:bin
#
# and some modules we don't want:
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
# macfreeze: optional rma
# macfreeze: exclude NodeInfoHelper
# macfreeze: exclude dshow
# macfreeze: exclude win32ui
# macfreeze: exclude linuxaudiodev
# macfreeze: exclude NodeInfo
# macfreeze: exclude AnchorEdit

#
# And here's the code for non-standalone version of the editor:

if not STANDALONE:
	# For now:
	progdir=os.path.split(sys.argv[0])[0]	# This is cmif:build:mac
	progdir=os.path.split(progdir)[0]		# this is cmif:build
	CMIFDIR=os.path.split(progdir)[0]		# and this is cmif
	
	CMIFPATH = [
		CMIFDIR+":mac",
		CMIFDIR+":editor:smil10",
		CMIFDIR+":editor:mac",
		CMIFDIR+":editor",
		CMIFDIR+":common:mac",
		CMIFDIR+":common",
		CMIFDIR+":lib:mac",
		CMIFDIR+":lib",
	# Overrides for Python distribution
		CMIFDIR+":pylib",
##	# XXXX Testing purposes only
##		CMIFDIR+":mmpython:producer:mac:bin",
	]
	sys.path[0:0] = CMIFPATH
	
	os.environ["CMIF"] = CMIFDIR
	#os.environ["CHANNELDEBUG"] = "1"
else:
	progdir=os.path.split(sys.argv[0])[0]
	os.environ["CMIF"] = progdir

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
##	MacOS.splash()
##	fss, ok = macfs.PromptGetFile('CMIF/SMIL file (cancel for URL)', 'TEXT')
##	if ok:
##		sys.argv = ["macgrins", fss.as_pathname()]
##	else:
##		import EasyDialogs
##		url = EasyDialogs.AskString("CMIF/SMIL URL")
##		if url is None:
##			sys.exit(0)
##		sys.argv = ["maccmifed", url]
		
no_exception=0
try:
	try:
		if profile:
			import profile
			fss, ok = macfs.StandardPutFile("Profile output:")
			if not ok: sys.exit(1)
			profile.run("import cmifed", fss.as_pathname())
		else:
			import cmifed
		no_exception=1
	except SystemExit:
		no_exception=1
finally:
	if not no_exception:
		if quietconsole:
			quietconsole.revert()
##		if DEBUG:
##			import pdb
##			pdb.post_mortem(sys.exc_info()[2])
##		elif quietconsole:
##			quietconsole.revert()
##			print 'Type return to exit-',
##			sys.stdin.readline()
	
