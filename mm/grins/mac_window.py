__version__ = "$Id$"

import mac_windowbase

_Toplevel = mac_windowbase._Toplevel
toplevel = _Toplevel()
mac_windowbase.toplevel = toplevel

from mac_windowbase import *

addclosecallback = toplevel.addclosecallback
canceltimer = toplevel.canceltimer
close = toplevel.close
mainloop = toplevel.mainloop
newcmwindow = toplevel.newcmwindow
newwindow = toplevel.newwindow
select_setcallback = toplevel.select_setcallback
setcursor = toplevel.setcursor
settimer = toplevel.settimer
usewindowlock = toplevel.usewindowlock
setidleproc = toplevel.setidleproc
cancelidleproc = toplevel.cancelidleproc
lopristarting = toplevel.lopristarting
getscreensize = toplevel.getscreensize
getscreendepth = toplevel.getscreendepth

# remove superfluous names
del mac_windowbase
del toplevel
