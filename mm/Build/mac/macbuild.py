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

# Find macfreeze directory
FREEZEDIR=os.path.join(sys.prefix, ":Mac:Tools:macfreeze")
sys.path.append(FREEZEDIR)
import macfreeze

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
	workdir = os.path.split(sys.argv[0])[0]
	print "workdir", workdir, sys.argv

	grins_py = myjoin(workdir, GRINS_SRC)
	grins_dir = myjoin(workdir, GRINS_DIR)
	grins_prj = myjoin(grins_dir, GRINS_PROJECT)

	cmifed_py = myjoin(workdir, CMIFED_SRC)
	cmifed_dir = myjoin(workdir, CMIFED_DIR)
	cmifed_prj = myjoin(cmifed_dir, CMIFED_PROJECT)
	
	e1 = build(grins_py, grins_dir, grins_prj, GRINS_TARGET)
	e2 = build(cmifed_py, cmifed_dir, cmifed_prj, CMIFED_TARGET)
	
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
		
def build(src, dir, project, target):
	rv = 0
	print "-- Freezing", src
	macfreeze.process('source', src, dir)

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
	
if __name__ == '__main__':
	main()
	
	
