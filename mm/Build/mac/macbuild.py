#
# Script to build Macintosh version of GRiNS player and editor.
#
# This script expects to live in the cmif/Build/mac folder.
# It performs the following actions:
# - Run macfreeze on macgrins.py, dropping the results in build.macgrins
# - build the GRiNS FAT target in macgrins.prj
# - Run macfreeze on maccmifed.py, output in build.maccmifed
# - build the cmifed FAT target in maccmifed.prj
#
# After this you will find the resulting fat programs in the build
# directories.
#
# NOTE: This script needs a rather hefty amount of memory. You may
# need to set the Python partition (cmd-I in the finder while having the
# interpreter selected) to something like 30Mb.
#
# A distribution consists only of either of these programs (an installer is
# not needed), and possibly a Templates folder, examples, etc.
#
import os
import sys
import macfs
import Res
import Ctl
import Dlg

# Find macfreeze directory
FREEZEDIR=os.path.join(sys.prefix, ":Mac:Tools:macfreeze")
sys.path.append(FREEZEDIR)
import macfreeze

#
# Resources for the dialog
#
RESFILE="macbuild.rsrc"
h = Res.OpenResFile(RESFILE)
DIALOG_ID=512
I_OK=1
I_CANCEL=2

I_CMIF_FREEZE=4
I_CMIF_BUILD=5

I_LITE_FREEZE=7
I_LITE_BUILD=8

I_GRINS_FREEZE=10
I_GRINS_BUILD=11

N_BUTTONS=12			# Last button plus one

#
# Names of the various files/folders
#
class GRINS:
	FREEZE_I = I_GRINS_FREEZE
	BUILD_I = I_GRINS_BUILD
	
	SRC="macplayer.py"
	DIR="build.player"
	PROJECT="player.prj"
	#TARGET="Player FAT"
	TARGET="Player PPC"

class CMIFED:
	FREEZE_I = I_CMIF_FREEZE
	BUILD_I = I_CMIF_BUILD
	
	SRC="maceditor.py"
	DIR="build.editor"
	PROJECT="editor.prj"
	#TARGET="Editor FAT"
	TARGET="Editor PPC"

class LITE:
	FREEZE_I = I_LITE_FREEZE
	BUILD_I = I_LITE_BUILD
	
	SRC="maclite.py"
	DIR="build.lite"
	PROJECT="lite.prj"
	#TARGET="Editor Lite FAT"
	TARGET="Editor Lite PPC"

ALL=(GRINS, CMIFED, LITE)

#
# Names of the Attrdefs input file and module.
#
ATTRDEFS_INPUT=":::Lib:Attrdefs"
ATTRDEFS_OUTPUT=":::Lib:Attrdefs.py"

#
# AppleEvent stuff
#
import aetools
import AppleEvents
from Metrowerks_Shell_Suite import Metrowerks_Shell_Suite
from CodeWarrior_Standard_Suite import CodeWarrior_Standard_Suite
from Required_Suite import Required_Suite

class MwShell(Metrowerks_Shell_Suite, CodeWarrior_Standard_Suite,
				Required_Suite, aetools.TalkTo):
	pass
MWERKS_CREATOR="CWIE"

#
#

def main():
	results = dodialog()
	do_grins_freeze = (I_GRINS_FREEZE in results)
	do_grins_build = (I_GRINS_BUILD in results)
	do_cmif_freeze = (I_CMIF_FREEZE in results)
	do_cmif_build = (I_CMIF_BUILD in results)
	do_lite_freeze = (I_CMIF_FREEZE in results)
	do_lite_build = (I_CMIF_BUILD in results)
##	print results
##	print do_grins_freeze, do_grins_build, do_cmif_freeze, do_cmif_build, do_rn_support
	if not results:
		sys.exit(0)

	workdir = os.path.split(sys.argv[0])[0]
##	print "workdir", workdir, sys.argv

##	grins_dir = myjoin(workdir, GRINS_DIR)
##	if do_rn_support:
##		grins_py = myjoin(workdir, GRINS_RN_SRC)
##		grins_prj = myjoin(grins_dir, GRINS_RN_PROJECT)
##	else:
##		grins_py = myjoin(workdir, GRINS_SRC)
##		grins_prj = myjoin(grins_dir, GRINS_PROJECT)
##
##	cmifed_dir = myjoin(workdir, CMIFED_DIR)
##	if do_rn_support:
##		cmifed_py = myjoin(workdir, CMIFED_RN_SRC)
##		cmifed_prj = myjoin(cmifed_dir, CMIFED_RN_PROJECT)
##	else:
##		cmifed_py = myjoin(workdir, CMIFED_SRC)
##		cmifed_prj = myjoin(cmifed_dir, CMIFED_PROJECT)
	
	checkattrdefs(myjoin(workdir, ATTRDEFS_INPUT),
				  myjoin(workdir, ATTRDEFS_OUTPUT))
	
	errors = 0
	for product in ALL:
		do_build = (product.BUILD_I in results)
		do_freeze = (product.FREEZE_I in results)
		src = myjoin(workdir, product.SRC)
		dir = myjoin(workdir, product.DIR)
		prj = myjoin(dir, product.PROJECT)
		e1 = build(src, dir, prj, product.TARGET, do_freeze, do_build)
		if e1:
			errors = errors + 1
	
	if errors:
		print "** Errors occurred during build"
		sys.exit(1)
	
def myjoin(dir, file):
	"""os.path.join that checks for file existence"""
	rv = os.path.join(dir, file)
	if not os.path.exists(rv):
		print "** Required file does not exist:", rv
		sys.exit(1)
	return rv
		
def build(src, dir, project, target, dofreeze, dobuild):
	rv = 0
	if dofreeze:
		print "-- Freezing", src
		macfreeze.process('source', src, dir, with_ifdef=1)

	if dobuild:
		print "-- Building", target, "in", project
		ide = MwShell(MWERKS_CREATOR, start=1)
		ide.send_timeout = AppleEvents.kNoTimeOut
		
		ide.open(macfs.FSSpec(project))
		ide.Set_Current_Target(target)
		try:
			ide.Make_Project()
		except aetools.Error, arg:
			print "** Failed:", arg
			rv = 1
		ide.Close_Project()
	return rv
	
def dodialog():
	d = Dlg.GetNewDialog(DIALOG_ID, -1)
	d.SetDialogDefaultItem(I_OK)
	d.SetDialogCancelItem(I_CANCEL)
	results = [0]*N_BUTTONS
	while 1:
		n = Dlg.ModalDialog(None)
		if n == I_OK:
			break
		if n == I_CANCEL:
			return []
		if n < N_BUTTONS:
			results[n] = (not results[n])
			h = d.GetDialogItemAsControl(n)
			h.SetControlValue(results[n])
	rv = []
	for i in range(len(results)):
		if results[i]:
			rv.append(i)
	return rv

def checkattrdefs(input, output):
	import stat
	try:
		in_info = os.stat(input)
	except IOError:
		print "Attrdefs input file not found:", input
		sys.exit(1)
	try:
		out_info = os.stat(output)
	except IOError:
		print "Attrdefs output file not found (run GRiNS once):", output
		sys.exit(1)
	if in_info[stat.ST_MTIME] > out_info[stat.ST_MTIME]:
		print "Attrdefs.py file outdated (run GRiNS once)"
		sys.exit(1)
	
if __name__ == '__main__':
	main()
	
	
