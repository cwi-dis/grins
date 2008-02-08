__version__ = "$Id$"

## ################################
# entry points for the core system
# and the other ../win32 folders
## ################################

import AppToplevel
import __main__
__main__.toplevel = AppToplevel._Toplevel()
toplevel= __main__.toplevel

newwindow = toplevel.newwindow
newcmwindow = toplevel.newwindow

close = toplevel.close

addclosecallback = toplevel.addclosecallback
removeclosecallback = toplevel.removeclosecallback

setcursor = toplevel.setcursor

getsize = toplevel.getsize

settimer = toplevel.settimer

select_setcallback = toplevel.select_setcallback

mainloop = toplevel.mainloop

getscreensize = toplevel.getscreensize

getscreendepth = toplevel.getscreendepth

canceltimer = toplevel.canceltimer
getcurtime = toplevel.getcurtime
settimevirtual = toplevel.settimevirtual

setready=toplevel.setready
setwaiting=toplevel.setwaiting

setidleproc=toplevel.setidleproc
cancelidleproc=toplevel.cancelidleproc
register_event=toplevel.register_event

genericwnd=toplevel.genericwnd
textwindow=toplevel.textwindow

htmlwindow=AppToplevel.htmlwindow
shell_execute=AppToplevel.shell_execute

# SDI-MDI Model Support
createmainwnd=toplevel.createmainwnd
newdocument=toplevel.newdocument
getmainwnd=toplevel.getmainwnd
getactivedocframe=toplevel.getActiveDocFrame
# /SDI-MDI Model Support

#
register_embedded = toplevel.register_embedded
unregister_embedded = toplevel.unregister_embedded

# constants
from appcon import *

# fonts
from Font import findfont,fonts

# dialogs
from AppToplevel import FileDialog
from win32dialog import *

# override some dialogs when embedded
import __main__
if hasattr(__main__,'embedded') and __main__.embedded:
    import embedding
    showmessage = embedding.showmessage
    ProgressDialog = embedding.ProgressDialog
    showquestion = embedding.showquestion
    GetYesNoCancel = embedding.GetYesNoCancel
    GetOKCancel = embedding.GetOKCancel
    GetYesNo = embedding.GetYesNo

# Auxiliary functions
from AppToplevel import beep

# needed directly?
GetImageSize=toplevel.GetImageSize
from win32dxm import GetVideoSize

def lopristarting():
    pass

import win32api
def RGB(c):return win32api.RGB(c[0],c[1],c[2])

def serve_events():
    import win32ui, win32con
    win32ui.PumpWaitingMessages(win32con.WM_MOUSEFIRST,win32con.WM_MOUSELAST)
    from __main__ import toplevel
    toplevel.serve_events()

def sleep(t):
    win32api.Sleep(int(t*1000.0+0.5))

def HasSvgSupport():
    import win32ui
    return win32ui.HasSvgSupport()

def is_embedded():
    import __main__
    return hasattr(__main__,'embedded') and __main__.embedded
