__version__ = "$Id$"

##################################
# entry points for the core system
# and the other ../win32 folders
##################################

import AppToplevel
import __main__
__main__.toplevel = AppToplevel._Toplevel()
toplevel= __main__.toplevel

newwindow = toplevel.newwindow
newcmwindow = toplevel.newwindow

close = toplevel.close

addclosecallback = toplevel.addclosecallback

setcursor = toplevel.setcursor

getsize = toplevel.getsize

usewindowlock = toplevel.usewindowlock

settimer = toplevel.settimer

select_setcallback = toplevel.select_setcallback

mainloop = toplevel.mainloop

getscreensize = toplevel.getscreensize

getscreendepth = toplevel.getscreendepth

canceltimer = toplevel.canceltimer

setready=toplevel.setready
setwaiting=toplevel.setwaiting

register=toplevel.register
unregister=toplevel.unregister

genericwnd=toplevel.genericwnd
textwindow=toplevel.textwindow

htmlwindow=AppToplevel.htmlwindow
shell_execute=AppToplevel.shell_execute

# SDI-MDI Model Support
createmainwnd=toplevel.createmainwnd
newdocument=toplevel.newdocument
getmainwnd=toplevel.getmainwnd
# /SDI-MDI Model Support


# constants
from appcon import *

# fonts
from Font import findfont,fonts

# dialogs
from AppToplevel import FileDialog
from components import *

# needed directly?
GetImageSize=toplevel.GetImageSize
GetVideoSize=toplevel.GetVideoSize
from _PreferencesDialog import PreferencesDialog

def beep():
	import sys
	sys.stderr.write('\7')

def lopristarting():
	pass
