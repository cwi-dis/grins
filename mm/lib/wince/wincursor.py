__version__ = "$Id$"

import grinsRC
import winuser

if 1:
    # use application
    resdll = 0
else:
    # use resource dll loaded in main
    import __main__
    resdll = __main__.resdll

def getcursorhandle(strid):
    if strid == 'hand':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_POINT_HAND)
    elif strid == 'darrow':
        cursor = winuser.LoadStandardCursor(wincon.IDC_SIZEWE)
    elif strid == 'channel':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_DRAGMOVE)
    elif strid == 'stop':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_STOP)
    elif strid == 'link':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_DRAGLINK)
    elif strid == 'draghand':
        cursor = winuser.LoadCursor(resdll, grinsRC.IDC_DRAG_HAND)
    elif strid == 'sizenwse':
        cursor = winuser.LoadStandardCursor(wincon.IDC_SIZENWSE)
    elif strid == 'sizens':
        cursor = winuser.LoadStandardCursor(wincon.IDC_SIZENS)
    elif strid == 'sizenesw':
        cursor = winuser.LoadStandardCursor(wincon.IDC_SIZENESW)
    elif strid == 'sizewe':
        cursor = winuser.LoadStandardCursor(wincon.IDC_SIZEWE)
    elif strid == 'cross':
        cursor = winuser.LoadStandardCursor(wincon.IDC_CROSS)
    else:
        cursor = winuser.LoadStandardCursor(wincon.IDC_ARROW)
    return cursor
