__version__ = "$Id$"

# app constants
from appcon import *

# Registration function for close callbacks
def addclosecallback(func, args):
	pass

def removeclosecallback(func, args):
	pass

def register_event(ev, cb, arg):
	pass

# Embedding Support	
def register_embedded(event, func, arg):
	_get_toplevel().register_embedded(event, func, arg)

def unregister_embedded(event):
	_get_toplevel().unregister_embedded(event)

def close():
	pass

# return main dialog
# main dialog should support 
# def set_dynamiclist(self, command, list): pass
def createmainwnd(title = None, adornments = None, commandlist = None):
	return _get_toplevel().createmainwnd(title, adornments, commandlist)

# return new document frame for doc
def newdocument(cmifdoc, adornments=None, commandlist=None):
	return _get_toplevel().newdocument(cmifdoc, adornments, commandlist)

def getactivedocframe():
	return _get_toplevel().getactivedocframe()
	
def getmainwnd():
	return _get_toplevel().getmainwnd()

def getscreensize():
	return 800, 600

def mainloop():
	pass

def settimer(sec, cb):
	return _get_toplevel().settimer(sec, cb)

def canceltimer(id):
	_get_toplevel().canceltimer(id)

def setwaiting():
	pass

def setidleproc(cb):
	return _get_toplevel().setidleproc(cb)

def cancelidleproc(id):
	return _get_toplevel().cancelidleproc(id)

# dialogs
from wintk_dialog import showmessage, showquestion
from wintk_dialog import ProgressDialog
from FileDialog import FileDialog

# new viewport
def newwindow(x, y, w, h, title,
		      pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1, bgcolor = None):
	import wintk_window
	context = wintk_window.ViewportContext(0, w, h, units, bgcolor or (0,0,0))
	return context._viewport

newcmwindow = newwindow

def GetImageSize(filename):
	from win32ig import win32ig
	img = win32ig.load(filename) 
	return win32ig.size(img)[:2]


##
## toplevel
##
def _get_toplevel():
	import __main__
	return __main__.toplevel

def __create_toplevel():
	from AppToplevel import _Toplevel
	import __main__
	__main__.toplevel = _Toplevel()

__create_toplevel()
