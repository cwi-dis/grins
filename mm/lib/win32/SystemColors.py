# these colors depend of the configuration of your system, and so
# these tables are built dynamicly from init_colors method
# not to have a list of the supported system-colors, look at the CSS specification

import win32con, win32api, win32ui
sdk = win32ui.GetWin32Sdk()

colors = {
}

rcolors = {
}

def __add_color(name, sysindex):
	rgb = None
	# make sure it doesn't crash if there is a problem
	try:
		color = win32api.GetSysColor(sysindex)
		if color != None and color >= 0:
			rgb = sdk.GetRGBValues(color)
	except:
		print 'systemcolor: error to get color ',name
		
	if type(rgb) is type(()):
		colors[name] = rgb
	
def init_colors():
	__add_color('ActiveBorder', win32con.COLOR_ACTIVEBORDER)
	__add_color('ActiveCaption', win32con.COLOR_ACTIVECAPTION)
	__add_color('AppWorkspace', win32con.COLOR_APPWORKSPACE)
	__add_color('Background', win32con.COLOR_BACKGROUND)
	__add_color('ButtonFace', win32con.COLOR_BTNFACE)
	__add_color('ButtonHighlight', win32con.COLOR_BTNHIGHLIGHT)
	__add_color('ButtonShadow', win32con.COLOR_BTNSHADOW)
	__add_color('ButtonText', win32con.COLOR_BTNTEXT)
	__add_color('CaptionText', win32con.COLOR_CAPTIONTEXT)
	__add_color('GrayText', win32con.COLOR_GRAYTEXT)
	__add_color('Highlight', win32con.COLOR_HIGHLIGHT)
	__add_color('HighlightText', win32con.COLOR_HIGHLIGHTTEXT)
	__add_color('InactiveBorder', win32con.COLOR_INACTIVEBORDER)
	__add_color('InactiveCaption', win32con.COLOR_INACTIVECAPTION)
	__add_color('InactiveCaptionText', win32con.COLOR_INACTIVECAPTIONTEXT)
	__add_color('InfoBackground', win32con.COLOR_INFOBK)
	__add_color('InfoText', win32con.COLOR_INFOTEXT)
	__add_color('Menu', win32con.COLOR_MENU)
	__add_color('MenuText', win32con.COLOR_MENUTEXT)
	__add_color('Scrollbar', win32con.COLOR_SCROLLBAR)
	__add_color('ThreeDDarkShadow', win32con.COLOR_3DDKSHADOW)
	__add_color('ThreeDFace', win32con.COLOR_3DFACE)
	__add_color('ThreeDHighlight', win32con.COLOR_3DHIGHLIGHT)
	__add_color('ThreeDLightShadow', win32con.COLOR_3DLIGHT)
	__add_color('ThreeDShadow', win32con.COLOR_3DSHADOW)
	__add_color('Window', win32con.COLOR_WINDOW)
	__add_color('WindowFrame', win32con.COLOR_WINDOWFRAME)
	__add_color('WindowText', win32con.COLOR_WINDOWTEXT)
	
	
	# initialize the reverse table	
	for name, color in colors.items():
		rcolors[color] = name
