__version__ = "$Id$"

import win32ui,win32con
from pywin.mfc import dialog
import commctrl
Sdk=win32ui.GetWin32Sdk()
import grinsRC
from usercmd import *

class LightWeightControl:
	def __init__(self,parent=None,id=-1,hwnd=None):
		self._id=id
		self._parent=parent
		if parent and hasattr(parent,'_subwindows'):
			parent._subwindows.append(self)
		self._hwnd=hwnd
	def sendmessage(self,msg,wparam=0,lparam=0):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessage(self._hwnd,msg,wparam,lparam)
	def sendmessage_ls(self,msg,wparam,lparam):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageLS(self._hwnd,msg,wparam,lparam)
	def sendmessage_rs(self,msg,wparam,lparam):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.SendMessageRS(self._hwnd,msg,wparam,lparam)
	def enable(self,f):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.EnableWindow(self._hwnd,f)
	def show(self):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.ShowWindow(self._hwnd,SW_SHOW)
	def hide(self):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.ShowWindow(self._hwnd,SW_HIDE)
	def attach(self,hwnd):
		self._hwnd=hwnd
	def attach_to_parent(self):
		if not self._parent: raise error, 'attach_to_parent without parent'	
		hparent = self._parent.GetSafeHwnd()
		self.attach(Sdk.GetDlgItem(hparent,self._id))
	def detach(self):
		hwnd=self._hwnd
		self._hwnd=None
		return hwnd
	def fromhandle(self,hwnd):
		return self._class__(hwnd)
	def hookcommand(self,obj,cb):
		obj.HookCommand(cb,self._id)
	def hookmessage(self,obj,cb):
		obj.HookMessage(cb,self._id)
	def hasid(self,id):
		return id==self._id
	def create(self,wc,name,pos,size,parent,id):
		if hasattr(parent,'GetSafeHwnd'):
			hwnd=parent.GetSafeHwnd()
		else:
			hwnd=parent
		pl=(pos[0],pos[1],size[0],size[1])
		self._hwnd=Sdk.CreateWindowEx(wc.exstyle,wc.classid,name,wc.style,
				pl,hwnd,id)
	def setwindowpos(self,hInsertAfter,rc,flags):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.SetWindowPos(self._hwnd,hInsertAfter,rc,flags)
	def getwindowrect(self):
		if not self._hwnd: raise error, 'os control has not been created'
		return Sdk.GetWindowRect(self._hwnd)

# shortcut
Control = LightWeightControl

class Button(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
				
class TextInput(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def settext(self,str):
		self.sendmessage_ls(win32con.WM_SETTEXT,0,str)
	def gettextlength(self):
		return self.sendmessage(win32con.WM_GETTEXTLENGTH)
	def gettext(self):
		n=self.gettextlength()+1
		return self.sendmessage_rs(win32con.WM_GETTEXT,n,n)	
	# cmif interface
	# gettext
	# settext

class List(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
		self.__icmif() 
	def setcursel(self,index):
		if not index: index=-1
		self.sendmessage(win32con.LB_SETCURSEL,index)
	def getcursel(self):
		return self.sendmessage(win32con.LB_GETCURSEL)
	def getcount(self):
		return self.sendmessage(win32con.LB_GETCOUNT)
	def insertstring(self,ix,str):
		self.sendmessage_ls(win32con.LB_INSERTSTRING,ix,str)
	def addstring(self,ix,str):
		return self.sendmessage_ls(win32con.LB_ADDSTRING,0,str)
	def gettextlen(self,ix):
		return self.sendmessage(win32con.LB_GETTEXTLEN,ix)
	def gettext(self,ix):
		n = self.gettextlen(ix) + 1
		return self.sendmessage_rs(win32con.LB_GETTEXT,ix,n)
	def resetcontent(self):
		self.sendmessage(win32con.LB_RESETCONTENT)

	# cmif interface
	def __icmif(self):
		self.getlistitem=self.gettext
		self.selectitem=self.setcursel
		self.getselection=self.getcursel
		self.delalllistitems=self.resetcontent
		self._cb=None		
	def addlistitem(self, item, pos):
		if pos < 0:
			pos = self.getcount()
		self.insertstring(pos,item)

	def getlist(self):
		l=[]
		for ix in range(self.getcount()):
			l.append(self.gettext(ix))
		return l

	def addlistitems(self,list,ix):
		for pos in range(ix,len(list)):
			self.insertstring(pos,list[pos])
					
	def getselected(self):
		pos = self.getselection()
		if pos<0:return None
		return pos

	def getlistitem(self,ix):
		return self.gettext(ix)

	def setcb(self,cb):
		self._cb=cb
	def callcb(self):
		if self._cb: 
			apply(apply,self._cb)


####################################################
# TAB CONTROL STUFF

# commctrl extensions tab control
LVM_FIRST  =            0x1000      # ListView messages
TV_FIRST   =            0x1100      # TreeView messages
HDM_FIRST  =            0x1200      # Header messages
TCM_FIRST  =            0x1300      # Tab control messages
TCN_FIRST =-550       
TCN_LAST=-580
TCN_SELCHANGE  = TCN_FIRST - 1
TCN_SELCHANGING= TCN_FIRST - 2

class TabCtrl(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def insertitem(self,ix,text):
		mask,ixImage,mp_appdata,text=(commctrl.TCIF_TEXT,-1,0,text)
		mp=Sdk.New('TCITEM',(mask,ixImage,mp_appdata,text))
		self.sendmessage(commctrl.TCM_INSERTITEM,ix,mp)
		Sdk.Delete(mp)
	def setcursel(self,ix):
		self.sendmessage(commctrl.TCM_SETCURSEL,ix)
	def getcursel(self):
		return self.sendmessage(commctrl.TCM_GETCURSEL)
	
##############################
class ResDialog(dialog.Dialog):
	def __init__(self,id,parent=None,resdll=None):
		if not resdll:
			import __main__
			resdll=__main__.resdll
		dialog.Dialog.__init__(self,id,resdll,parent)
		self._subwindows = []
	def attach_handles_to_controls(self):
		hdlg = self.GetSafeHwnd()
		for ctrl in self._subwindows:
			ctrl.attach(Sdk.GetDlgItem(hdlg,ctrl._id))
	def onevent(self,event):
		try:
			func, arg = self._callbacks[event]			
		except KeyError:
			pass
		else:
			apply(func,arg)

class OpenLocationDlg(ResDialog):
	def __init__(self,callbacks=None,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_DIALOG_OPENLOCATION,parent)
		self._callbacks=callbacks

		self._text= TextInput(self,grinsRC.IDC_EDIT_LOCATION)
		self._bcancel = Button(self,win32con.IDCANCEL)
		self._bopen = Button(self,win32con.IDOK)
		self._bbrowse= Button(self,grinsRC.IDC_BUTTON_BROWSE)

	def OnInitDialog(self):	
		self.attach_handles_to_controls()	
		self._bopen.enable(0)
		self._text.hookcommand(self,self.OnEditChange)
		self._bbrowse.hookcommand(self,self.OnBrowse)
		return ResDialog.OnInitDialog(self)

	def OnOK(self):
		self.onevent('Open')

	def OnCancel(self):
		self.onevent('Cancel')

	def close(self):
		self.EndDialog(win32con.IDOK)
	def show(self):
		self.DoModal()

	def OnBrowse(self,id,code):
		self.onevent('Browse')

	def OnEditChange(self,id,code):
		if code==win32con.EN_CHANGE and self._text.hasid(id):
			l=self._text.gettextlength()
			self._bopen.enable(l)


##############################
class LayoutDlg(ResDialog):
	def __init__(self,cmddict=None,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_LAYOUT,parent)
		self._parent=parent
		self._layoutlist=List(self,grinsRC.IDC_LAYOUTS)
		self._channellist=List(self,grinsRC.IDC_LAYOUT_CHANNELS)
		self._otherlist=List(self,grinsRC.IDC_OTHER_CHANNELS)
		self._usercmd_ui={
			 NEW_LAYOUT:Button(self,grinsRC.IDC_NEW_LAYOUT),
			 RENAME:Button(self,grinsRC.IDC_RENAME_LAYOUT),
			 DELETE:Button(self,grinsRC.IDC_DELETE_LAYOUT),
			 NEW_CHANNEL:Button(self,grinsRC.IDC_NEW_CHANNEL),
			 REMOVE_CHANNEL:Button(self,grinsRC.IDC_REMOVE_CHANNEL),
			 #ATTRIBUTES:Button(self,grinsRC.IDC_CHANNEL_ATTR),
			 ADD_CHANNEL:Button(self,grinsRC.IDC_ADD_CHANNEL),
			 }
		self.CreateWindow()
		
	def OnInitDialog(self):
		self.attach_handles_to_controls()
		return ResDialog.OnInitDialog(self)

	# cmif interface
	def create(self):
		if self.GetSafeHwnd()==0:
			self.CreateWindow()		
	def show(self):
		if self.GetSafeHwnd()==0:
			self.CreateWindow()
		self.ShowWindow(win32con.SW_SHOW)
	def close(self):
		if self.GetSafeHwnd():
			self.DestroyWindow() 
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)
	def setcursor(self,cursor):
		import win32mu
		win32mu.SetCursor(cursor)
	def is_showing(self):
		if self.GetSafeHwnd()==0: return 0
		return self.IsWindowVisible()
	def set_commandlist(self, list):
		if self._parent:
			self._parent.set_commandlist(list,'view')

class LayoutNameDlg(ResDialog):
	def __init__(self,callbacks=None,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_LAYOUT_NAME,parent)
		self._callbacks=callbacks
	def OnInitDialog(self):
		return ResDialog.OnInitDialog(self)
	def show(self):
		self.DoModal()

class NewChannelDlg(ResDialog):
	def __init__(self,callbacks=None,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_NEW_CHANNEL,parent)
		self._callbacks=callbacks
	def OnInitDialog(self):
		return ResDialog.OnInitDialog(self)
	def show(self):
		self.DoModal()

