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

# kk: instead of setting cursors directly
setready=toplevel.setready
setwaiting=toplevel.setwaiting


# TEMPORARY HERE
import win32con
from pywin.mfc import dialog
import grinsRC

class OpenLocationDlg(dialog.Dialog):
	def __init__(self,callbacks):
		dialog.Dialog.__init__(self,grinsRC.IDD_DIALOG_OPENLOCATION)
		self._callbacks=callbacks
	def OnInitDialog(self):
		self.HookCommand(self.OnBrowse,grinsRC.IDC_BUTTON_BROWSE)
		self.HookCommand(self.OnEditChange,grinsRC.IDC_EDIT_LOCATION)
		item=self.GetDlgItem(win32con.IDOK)
		item.EnableWindow(0)
		item=self.GetDlgItem(grinsRC.IDC_EDIT_LOCATION)
		item.SetFocus()
		dialog.Dialog.OnInitDialog(self)
		return 0
	def OnOK(self):
		if len(self.gettext())==0:return
		self.onEvent('Open')
		self._obj_.OnOK()
	def OnCancel(self):
		self.onEvent('Cancel')
		self._obj_.OnCancel()
	def OnBrowse(self,id,code):
		self.onEvent('Browse')
	def OnEditChange(self,id,code):
		if id==grinsRC.IDC_EDIT_LOCATION and code==win32con.EN_CHANGE:
			if len(self.gettext()):
				item=self.GetDlgItem(win32con.IDOK)
				item.EnableWindow(1)
			else:
				item=self.GetDlgItem(win32con.IDOK)
				item.EnableWindow(0)				
	def settext(self,str):
		item=self.GetDlgItem(grinsRC.IDC_EDIT_LOCATION)
		item.SetWindowText(str)
	def gettext(self):
		item=self.GetDlgItem(grinsRC.IDC_EDIT_LOCATION)
		return item.GetWindowText()
	def onEvent(self,event):
		try:
			func, arg = self._callbacks[event]			
		except KeyError:
			pass
		else:
			apply(func,arg)


