__version__ = "$Id$"

# app win constants
from appcon import *

# app toplevel repository
# provides the interface to create channel wnds
from AppToplevel import toplevel

# forms
from AppForms import Window

# dlgs
from AppMessages import showmessage,showquestion,multchoice
from AppDialog import MainDialog, Dialog
from FileDialog import FileDialog
from SelectionDialog import SelectionDialog
#from SelectionMenuDialog import SelectionMenuDialog
from InputDialog import InputDialog

# font utilities
from Font import findfont,fonts

#################################################
# useful functions
# some are defined here to import only windowinterface and not pyds 

def beep():
	import sys
	sys.stderr.write('\7')

def lopristarting():
	pass

def GetStringLength(wnd,str):
	dc = wnd.GetDC();
	cx,cy=dc.GetTextExtent(str)
	wnd.ReleaseDC(dc)
	return cx

def textwindow(text):
	from win32modules import cmifex2
	w = Window('Source', resizable = 1, deleteCallback = 'hide', havpar = 0)
	t = w.TextEdit(text, None, editable = 0, top = 35, left = 0, right = 80*7, bottom = 300, rows = 30, columns = 80)
	b = w.ButtonRow([('Close', (w.hide, ()))], top = 5, left = 5, right = 150, bottom = 30, vertical = 0)
	cmifex2.ResizeWindow(w._wnd, 80*7+20, 380)
	w.show()
	return w

def ResizeWindow(wnd,w, h):
	from win32modules import cmifex2
	cmifex2.ResizeWindow(wnd,w,h)

def MesBox(text,title,style):
	from win32modules import cmifex2
	cmifex2.MesBox(text,title,style)

def SetFlag(i):
	from win32modules import cmifex2
	cmifex2.SetFlag(i)

def GetImageSize(file):
	from win32modules import imageex
	try:
		xsize, ysize = toplevel._image_size_cache[file]
	except KeyError:
		try:
			img = imageex.load(file)
		except img.error, arg:
			raise error, arg
		xsize,ysize,depth=imageex.size(img)
		toplevel._image_size_cache[file] = xsize, ysize
		toplevel._image_cache[file] = img
	return xsize, ysize

def GetVideoSize(file):
	from win32modules import mpegex
	import AppWnds
	w=MfcOsWnd()
	w.create()
	width, height = mpegex.SizeOfImage(w,file)
	w.DestroyWindow()
	return (width, height)


def SetFont(wnd,facename,poitsize):
	from win32modules import cmifex2
	cmifex2.SetFont(wnd,facename,poitsize)

from AppMenu import FloatMenu

def GetString(l):
	from win32modules import cmifex2
	return cmifex2.Get(l)

def SetCaption(wnd,str):
	wnd.SetWindowText(str)

#########################################
# Shortcuts

newwindow = toplevel.newwindow

newcmwindow = toplevel.newcmwindow

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

