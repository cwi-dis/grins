__version__ = "$Id$"

# these colors depend of the configuration of your system, and so
# these tables are built dynamicly from init_colors method
# not to have a list of the supported system-colors, look at the CSS specification

import win32con
import winuser
import wingdi

colors = {
}

def __add_color(name, sysindex):
    rgb = None
    # make sure it doesn't crash if there is a problem
    try:
        color = winuser.GetSysColor(sysindex)
        if color != None and color >= 0:
            rgb = wingdi.GetRGBValues(color)
    except:
        print 'systemcolor: error to get color ',name

    if type(rgb) is type(()):
        colors[name] = rgb

def init_colors():
    __add_color('activeborder', win32con.COLOR_ACTIVEBORDER)
    __add_color('activecaption', win32con.COLOR_ACTIVECAPTION)
    __add_color('appworkspace', win32con.COLOR_APPWORKSPACE)
    __add_color('background', win32con.COLOR_BACKGROUND)
    __add_color('buttonface', win32con.COLOR_BTNFACE)
    __add_color('buttonhighlight', win32con.COLOR_BTNHIGHLIGHT)
    __add_color('buttonshadow', win32con.COLOR_BTNSHADOW)
    __add_color('buttontext', win32con.COLOR_BTNTEXT)
    __add_color('captiontext', win32con.COLOR_CAPTIONTEXT)
    __add_color('graytext', win32con.COLOR_GRAYTEXT)
    __add_color('highlight', win32con.COLOR_HIGHLIGHT)
    __add_color('highlighttext', win32con.COLOR_HIGHLIGHTTEXT)
    __add_color('inactiveborder', win32con.COLOR_INACTIVEBORDER)
    __add_color('inactivecaption', win32con.COLOR_INACTIVECAPTION)
    __add_color('inactivecaptiontext', win32con.COLOR_INACTIVECAPTIONTEXT)
    __add_color('infobackground', win32con.COLOR_INFOBK)
    __add_color('infotext', win32con.COLOR_INFOTEXT)
    __add_color('menu', win32con.COLOR_MENU)
    __add_color('menutext', win32con.COLOR_MENUTEXT)
    __add_color('scrollbar', win32con.COLOR_SCROLLBAR)
    __add_color('threeddarkshadow', win32con.COLOR_3DDKSHADOW)
    __add_color('threedface', win32con.COLOR_3DFACE)
    __add_color('threedhighlight', win32con.COLOR_3DHIGHLIGHT)
    __add_color('threedlightshadow', win32con.COLOR_3DLIGHT)
    __add_color('threedshadow', win32con.COLOR_3DSHADOW)
    __add_color('window', win32con.COLOR_WINDOW)
    __add_color('windowframe', win32con.COLOR_WINDOWFRAME)
    __add_color('windowtext', win32con.COLOR_WINDOWTEXT)

init_colors()
