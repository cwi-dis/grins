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
I_GRINS_FREEZE=1
I_GRINS_BUILD=2
I_CMIF_FREEZE=3
I_CMIF_BUILD=4
N_BUTTONS=6			# Last button plus one
I_OK=7
I_CANCEL=8

#
# Names of the various files/folders
#
GRINS_SRC="macgrins.py"
GRINS_DIR="build.macgrins"
GRINS_PROJECT="macgrins.prj"
GRINS_TARGET="GRiNS FAT"

CMIFED_SRC="maccmifed.py"
CMIFED_DIR="build.maccmifed"
CMIFED_PROJECT="maccmifed.prj"
CMIFED_TARGET="cmifed FAT"

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
	print results
	print do_grins_freeze, do_grins_build, do_cmif_freeze, do_cmif_build
	if not results:
		sys.exit(0)

	workdir = os.path.split(sys.argv[0])[0]
	print "workdir", workdir, sys.argv

	grins_py = myjoin(workdir, GRINS_SRC)
	grins_dir = myjoin(workdir, GRINS_DIR)
	grins_prj = myjoin(grins_dir, GRINS_PROJECT)

	cmifed_py = myjoin(workdir, CMIFED_SRC)
	cmifed_dir = myjoin(workdir, CMIFED_DIR)
	cmifed_prj = myjoin(cmifed_dir, CMIFED_PROJECT)
	
	checkattrdefs(myjoin(workdir, ATTRDEFS_INPUT),
				  myjoin(workdir, ATTRDEFS_OUTPUT))
	
	e1 = build(grins_py, grins_dir, grins_prj, GRINS_TARGET, do_grins_freeze,
				do_grins_build)
	e2 = build(cmifed_py, cmifed_dir, cmifed_prj, CMIFED_TARGET, do_cmif_freeze,
				do_cmif_build)
	
	if e1 or e2:
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
		macfreeze.process('source', src, dir)

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
			tp, h, rect = d.GetDialogItem(n)
			h.as_Control().SetControlValue(results[n])
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
	
	
