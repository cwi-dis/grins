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

#
# Initialize toplevel and make it available. Initializing the commands
# has to be done later (it depends on mw_globals.toplevel being available
# at some low level).
#
toplevel = mw_toplevel._Toplevel()
mw_globals.toplevel = toplevel
toplevel._initcommands()

#
# Import a few other constants and such from mw_globals
from mw_globals import error, Continue
from mw_globals import UNIT_MM, UNIT_SCREEN, UNIT_PXL
from mw_globals import ReadMask, WriteMask
from mw_globals import RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH
from mw_globals import SINGLE, HTM, TEXT, MPEG
from mw_globals import TRUE, FALSE
#
# Make various methods from toplevel available externally
#

newwindow = toplevel.newwindow
newcmwindow = toplevel.newcmwindow
windowgroup = toplevel.windowgroup
close = toplevel.close
addclosecallback = toplevel.addclosecallback
setcursor = toplevel.setcursor
getsize = toplevel.getsize
usewindowlock = toplevel.usewindowlock
settimer = toplevel.settimer
select_setcallback = toplevel.select_setcallback
mainloop = toplevel.mainloop
canceltimer = toplevel.canceltimer
getscreensize = toplevel.getscreensize
getscreendepth = toplevel.getscreendepth
lopristarting = toplevel.lopristarting
setidleproc = toplevel.setidleproc
cancelidleproc = toplevel.cancelidleproc

#
# Make various other items from other modules available
#
fonts = mw_fonts.fonts
findfont = mw_fonts.findfont

DialogWindow = mw_windows.DialogWindow

SelectWidget = mw_widgets.SelectWidget

FullPopupMenu = mw_menucmd.FullPopupMenu

MACDialog = mw_dialogs.MACDialog
FileDialog = mw_dialogs.FileDialog
SelectionDialog = mw_dialogs.SelectionDialog
SingleSelectionDialog = mw_dialogs.SingleSelectionDialog
InputDialog = mw_dialogs.InputDialog
InputURLDialog = mw_dialogs.InputURLDialog
Dialog = mw_dialogs.Dialog
multchoice = mw_dialogs.multchoice
showmessage = mw_dialogs.showmessage
showquestion = mw_dialogs.showquestion

