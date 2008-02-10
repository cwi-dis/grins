__version__ = "$Id$"

# these colors depend of the configuration of your system, and so
# these tables are built dynamicly from init_colors method
# not to have a list of the supported system-colors, look at the CSS specification

import wincon
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
    __add_color('activeborder', wincon.COLOR_ACTIVEBORDER)
    __add_color('activecaption', wincon.COLOR_ACTIVECAPTION)
    __add_color('appworkspace', wincon.COLOR_APPWORKSPACE)
    __add_color('background', wincon.COLOR_BACKGROUND)
    __add_color('buttonface', wincon.COLOR_BTNFACE)
    __add_color('buttonhighlight', wincon.COLOR_BTNHIGHLIGHT)
    __add_color('buttonshadow', wincon.COLOR_BTNSHADOW)
    __add_color('buttontext', wincon.COLOR_BTNTEXT)
    __add_color('captiontext', wincon.COLOR_CAPTIONTEXT)
    __add_color('graytext', wincon.COLOR_GRAYTEXT)
    __add_color('highlight', wincon.COLOR_HIGHLIGHT)
    __add_color('highlighttext', wincon.COLOR_HIGHLIGHTTEXT)
    __add_color('inactiveborder', wincon.COLOR_INACTIVEBORDER)
    __add_color('inactivecaption', wincon.COLOR_INACTIVECAPTION)
    __add_color('inactivecaptiontext', wincon.COLOR_INACTIVECAPTIONTEXT)
    __add_color('infobackground', wincon.COLOR_INFOBK)
    __add_color('infotext', wincon.COLOR_INFOTEXT)
    __add_color('menu', wincon.COLOR_MENU)
    __add_color('menutext', wincon.COLOR_MENUTEXT)
    __add_color('scrollbar', wincon.COLOR_SCROLLBAR)
    __add_color('threeddarkshadow', wincon.COLOR_3DDKSHADOW)
    __add_color('threedface', wincon.COLOR_3DFACE)
    __add_color('threedhighlight', wincon.COLOR_3DHIGHLIGHT)
    __add_color('threedlightshadow', wincon.COLOR_3DLIGHT)
    __add_color('threedshadow', wincon.COLOR_3DSHADOW)
    __add_color('window', wincon.COLOR_WINDOW)
    __add_color('windowframe', wincon.COLOR_WINDOWFRAME)
    __add_color('windowtext', wincon.COLOR_WINDOWTEXT)

init_colors()
