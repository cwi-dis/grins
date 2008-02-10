__version__ = "$Id$"

#
# Windowinterface for MacOS.
#
# This modules glues all the mw_ modules together and provides
# the only external interface.
#
import mw_globals
import mw_toplevel
import mw_fonts
import mw_windows
import mw_widgets
import mw_dialogs
import mw_menucmd
import mw_textwindow

def sleep(sec):
    pass                            # for now

#
# There is a cyclic dependency between mw_dialogs and mw_windows. Solve it
# by stuffing showmessage into mw_windows' namespace by hand.
#
mw_windows.showmessage = mw_dialogs.showmessage
mw_toplevel.showmessage = mw_dialogs.showmessage

#
# Initialize toplevel and make it available. Initializing the commands
# has to be done later (it depends on mw_globals.toplevel being available
# at some low level).
#
toplevel = mw_toplevel._Toplevel()
mw_globals.toplevel = toplevel
# toplevel._initcommands()

#
# Import a few other constants and such from mw_globals
from mw_globals import error, Continue
from mw_globals import UNIT_MM, UNIT_SCREEN, UNIT_PXL
from mw_globals import ReadMask, WriteMask
from mw_globals import RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH
from mw_globals import SINGLE, HTM, TEXT, MPEG
from mw_globals import TRUE, FALSE
from mw_globals import ICONSIZE_PXL
#
# Make various methods from toplevel available externally
#

newwindow = toplevel.newwindow
newcmwindow = toplevel.newcmwindow
windowgroup = toplevel.windowgroup
close = toplevel.close
addclosecallback = toplevel.addclosecallback
setcursor = toplevel.setcursor
setdragcursor = toplevel.setdragcursor
setwaiting = toplevel.setwaiting
getsize = toplevel.getsize
settimer = toplevel.settimer
select_setcallback = toplevel.select_setcallback
mainloop = toplevel.mainloop
canceltimer = toplevel.canceltimer
getscreensize = toplevel.getscreensize
getscreendepth = toplevel.getscreendepth
_getmmfactors = toplevel._getmmfactors
lopristarting = toplevel.lopristarting
setidleproc = toplevel.setidleproc
cancelidleproc = toplevel.cancelidleproc
installaehandler = toplevel.installaehandler
getcurtime = toplevel.getcurtime
settimevirtual = toplevel.settimevirtual
dumpwindows = toplevel.dumpwindows

#
# Make various other items from other modules available
#
fonts = mw_fonts.fonts
findfont = mw_fonts.findfont

DialogWindow = mw_windows.DialogWindow

FullPopupMenu = mw_menucmd.FullPopupMenu

MACDialog = mw_dialogs.MACDialog
FileDialog = mw_dialogs.FileDialog
InputDialog = mw_dialogs.InputDialog
InputURLDialog = mw_dialogs.InputURLDialog
NewChannelDialog = mw_dialogs.NewChannelDialog
TemplateDialog = mw_dialogs.TemplateDialog
ProgressDialog = mw_dialogs.ProgressDialog
BandwidthComputeDialog = mw_dialogs.BandwidthComputeDialog
Dialog = mw_dialogs.Dialog
multchoice = mw_dialogs.multchoice
mmultchoice = mw_dialogs.mmultchoice
GetYesNoCancel = mw_dialogs.GetYesNoCancel
GetOKCancel = mw_dialogs.GetOKCancel
GetYesNo = mw_dialogs.GetYesNo
showmessage = mw_dialogs.showmessage
showquestion = mw_dialogs.showquestion
TraceDialog = mw_dialogs.TraceDialog

beep = mw_toplevel.beep
_qtavailable = mw_toplevel._qtavailable

textwindow = mw_textwindow.textwindow
# htmlwindow = mw_textwindow.htmlwindow
def htmlwindow(url):
    # Workaround (hack) for Explorer bug, which doesn't recognize file:/disk/...
    if url[:6] == 'file:/' and url[6] != '/':
        url = 'file:///' + url[6:]
    try:
        import ic
        ic_instance = ic.IC()
        ic_instance.launchurl(url)
    except:
        showmessage('Cannot start webbrowser.\nInternet configuration error?')
    return None

# open an external application in order to manage the media specified in url
# verb is the action executed by the external application. may be print, ... (for now ignore)
def shell_execute(url,verb='open'):
    htmlwindow(url)

from imgimagesize import GetImageSize
from mw_toplevel import GetVideoSize
