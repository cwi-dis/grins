__version__ = "$Id$"

##################################
# entry points for the core system
# and the other ../win32 folders
##################################

from AppToplevel import toplevel

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

genericwnd=toplevel.genericwnd
textwindow=toplevel.textwindow

# SDI-MDI Model Support

createmainwnd=toplevel.createmainwnd
getmainwnd=toplevel.getmainwnd

newdocument=toplevel.newdocument

newviewobj=toplevel.newviewobj
newview=toplevel.newview
showview=toplevel.showview
createview=toplevel.createview

getformserver=toplevel.getformserver
getviewframe=toplevel.getviewframe

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
