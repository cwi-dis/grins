__version__ = "$Id$"

# app constants
from appcon import *

import main_toplevel

toplevel = main_toplevel.Toplevel()
import __main__
__main__.toplevel = toplevel

# Registration function for close callbacks
def addclosecallback(func, args):
	pass

def removeclosecallback(func, args):
	pass

def register_event(ev, cb, arg):
	pass

# Embedding Support	
def register_embedded(event, func, arg):
	toplevel.register_embedded(event, func, arg)

def unregister_embedded(event):
	toplevel.unregister_embedded(event)

close = toplevel.close

# return main dialog
# main dialog should support 
# def set_dynamiclist(self, command, list): pass
def createmainwnd(title = None, adornments = None, commandlist = None):
	return toplevel.createmainwnd(title, adornments, commandlist)

# return new document frame for doc
def newdocument(cmifdoc, adornments=None, commandlist=None):
	return toplevel.newdocument(cmifdoc, adornments, commandlist)

def getactivedocframe():
	return toplevel.getactivedocframe()
	
def getmainwnd():
	return toplevel.getmainwnd()

def getscreensize():
	return 800, 600

def mainloop():
	pass

def settimer(sec, cb):
	return toplevel.settimer(sec, cb)

def canceltimer(id):
	toplevel.canceltimer(id)

def setwaiting():
	pass

def setidleproc(cb):
	return toplevel.setidleproc(cb)

def cancelidleproc(id):
	return toplevel.cancelidleproc(id)

# dialogs
from appdialogs import showmessage, showquestion
from appdialogs import ProgressDialog
from appdialogs import FileDialog

#htmlwindow = AppToplevel.htmlwindow
#shell_execute = AppToplevel.shell_execute

# new viewport
def newwindow(x, y, w, h, title,
		      pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1, bgcolor = None):
	return getmainwnd().newViewport(w, h, units, bgcolor)

newcmwindow = newwindow

def GetImageSize(filename):
	import mediainterface
	image = mediainterface.get_image(filename)
	return image.get_size()

