__version__ = "$Id$"

""" @win32doc|wc
This module defines in one place
the creation attributes and styles of 
the win32 controls (edit,button,etc)
in order to simplify the process of creating
controls in other modules
"""

import win32ui
from win32con import *
Sdk=win32ui.GetWin32Sdk()

# Base class for controls creation classes
class WndClass:
	classid = None
	style = 0
	exstyle = 0
	def __init__(self, **kwargs):
		for attr, val in kwargs.items():
			setattr(self, attr, val)

# Edit control creation class 
class EDIT(WndClass):
	def __init__(self,style=0,exstyle=0):
		WndClass.__init__(self,
			classid='EDIT',
			style=WS_CHILD | WS_CLIPSIBLINGS | WS_VISIBLE | WS_TABSTOP  | style,
			exstyle=WS_EX_CONTROLPARENT| WS_EX_CLIENTEDGE | exstyle)

# Button control creation class 
class BUTTON(WndClass):
	def __init__(self,style=0,exstyle=0):
		WndClass.__init__(self,
			classid='BUTTON',
			style=WS_CHILD | WS_CLIPSIBLINGS | WS_VISIBLE | WS_TABSTOP |  style,
			exstyle=WS_EX_CONTROLPARENT| exstyle)

# PushButton control creation class 
# for left justification init with style BS_LEFTTEXT
class PUSHBUTTON(BUTTON):
	def __init__(self,style=0,exstyle=0):
		BUTTON.__init__(self,BS_PUSHBUTTON | style,exstyle)

# RadioButton control creation class 
# to change order of text and control init with BS_RIGHT (BS_LEFT is the default)
class RADIOBUTTON(BUTTON):
	def __init__(self,style=0,exstyle=0):
		BUTTON.__init__(self,BS_RADIOBUTTON | style,exstyle)
# CheckBox control creation class 
class AUTOCHECKBOX(BUTTON):
	def __init__(self,style=0,exstyle=0):
		BUTTON.__init__(self,BS_AUTOCHECKBOX | style,exstyle)
CHECKBOX=AUTOCHECKBOX		

# Create a window from its control class
def createwnd(wc,name,pos,size,parent,id):
	if hasattr(parent,'GetSafeHwnd'):
		hwnd=parent.GetSafeHwnd()
	else:
		hwnd=parent
	pl=(pos[0],pos[1],size[0],size[1])
	return Sdk.CreateWindowEx(wc.exstyle,wc.classid,name,wc.style,
			pl,hwnd,id)
