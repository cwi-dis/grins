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
from Carbon import Res
from Carbon import Ctl
from Carbon import Dlg

# Find macfreeze directory
FREEZEDIR=os.path.join(sys.prefix, ":Mac:Tools:macfreeze")
sys.path.append(FREEZEDIR)
import macfreeze

#
# Resources for the dialog
#
RESFILE="macbuild.rsrc"
h = Res.FSpOpenResFile(RESFILE, 0)
DIALOG_ID=512
I_OK=1
I_CANCEL=2

I_G2PRO_FREEZE=4
I_G2PRO_BUILD=5

I_G2LITE_FREEZE=7
I_G2LITE_BUILD=8

I_PLAYER_FREEZE=10
I_PLAYER_BUILD=11

I_SMILPRO_FREEZE=13
I_SMILPRO_BUILD=14

I_QTPRO_FREEZE=16
I_QTPRO_BUILD=17

I_SMIL2PLAYER_FREEZE=19
I_SMIL2PLAYER_BUILD=20

N_BUTTONS=21                    # Last button plus one

#
# Names of the various files/folders
#
class PLAYER:
    FREEZE_I = I_PLAYER_FREEZE
    BUILD_I = I_PLAYER_BUILD

    SRC="macplayer.py"
    DIR="build.player"
    PROJECT="player.prj"
    #TARGET="Player FAT"
    TARGET="Player PPC"

class SMIL2PLAYER:
    FREEZE_I = I_SMIL2PLAYER_FREEZE
    BUILD_I = I_SMIL2PLAYER_BUILD

    SRC="macsmil2player.py"
    DIR="build.player-smil2"
    PROJECT="player.prj"
    #TARGET="Player FAT"
    TARGET="Player PPC"

class G2PRO:
    FREEZE_I = I_G2PRO_FREEZE
    BUILD_I = I_G2PRO_BUILD

    SRC="macg2pro.py"
    DIR="build.g2pro"
    PROJECT="g2pro.prj"
    #TARGET="Editor FAT"
    TARGET="Editor PPC"

class G2LITE:
    FREEZE_I = I_G2LITE_FREEZE
    BUILD_I = I_G2LITE_BUILD

    SRC="macg2lite.py"
    DIR="build.g2lite"
    PROJECT="g2lite.prj"
    #TARGET="Editor Lite FAT"
    TARGET="Editor Lite PPC"

class SMILPRO:
    FREEZE_I = I_SMILPRO_FREEZE
    BUILD_I = I_SMILPRO_BUILD

    SRC="macsmilpro.py"
    DIR="build.smilpro"
    PROJECT="smilpro.prj"
    #TARGET="Editor FAT"
    TARGET="Editor PPC"

class QTPRO:
    FREEZE_I = I_QTPRO_FREEZE
    BUILD_I = I_QTPRO_BUILD

    SRC="macqtpro.py"
    DIR="build.qtpro"
    PROJECT="qtpro.prj"
    #TARGET="Editor FAT"
    TARGET="Editor PPC"

ALL=(G2PRO, G2LITE, SMILPRO, QTPRO, PLAYER, SMIL2PLAYER)

#
# Names of the Attrdefs input file and module.
#
ATTRDEFS_INPUT=":::Lib:Attrdefs"
ATTRDEFS_OUTPUT=":::Lib:Attrdefs.py"

#
# AppleEvent stuff
#
import aetools
from Carbon import AppleEvents
OLDAESUPPORT = 0

if OLDAESUPPORT:
    from Metrowerks_Shell_Suite import Metrowerks_Shell_Suite
    from CodeWarrior_suite import CodeWarrior_suite
    from Metrowerks_Standard_Suite import Metrowerks_Standard_Suite
    from Required_Suite import Required_Suite

    class MwShell(Metrowerks_Shell_Suite, CodeWarrior_suite, Metrowerks_Standard_Suite,
                                    Required_Suite, aetools.TalkTo):
        pass
else:
    import CodeWarrior

    MwShell = CodeWarrior.CodeWarrior

MWERKS_CREATOR="CWIE"
#
#

def main():
    results = dodialog()
    if not results:
        sys.exit(0)

    workdir = os.path.split(sys.argv[0])[0]

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
