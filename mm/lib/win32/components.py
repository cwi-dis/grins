__version__ = "$Id$"

""" @win32doc|components
The components defined in this module are:
	1. a sufficient family of light-weight controls (Button,Edit,etc)
	2. various helper independent dialogs 
The controls are not based on MFC but on win32 Sdk.
They are at the same level as MFC is to the Sdk 
(a fact that justifies the name light weight)
This is in contrast to all the objects exported by the 
win32ui pyd which exports inherited from MFC objects
"""

import win32ui,win32con
from pywin.mfc import dialog
import commctrl
Sdk=win32ui.GetWin32Sdk()
import grinsRC
from usercmd import *
import win32mu

[FALSE, TRUE] = range(2)
error = 'lib.win32.components.error'

# Base class for SDK based controls
class LightWeightControl:
	def __init__(self,parent=None,id=-1,hwnd=None):
		self._id=id
		self._parent=parent
		if parent and hasattr(parent,'_subwndlist'):
			parent._subwndlist.append(self)
		self._hwnd=hwnd
		self._cb=None
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
		if f==None:f=0
		Sdk.EnableWindow(self._hwnd,f)
	def show(self):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.ShowWindow(self._hwnd,win32con.SW_SHOW)
	def hide(self):
		if not self._hwnd: raise error, 'os control has not been created'
		Sdk.ShowWindow(self._hwnd,win32con.SW_HIDE)
	def attach(self,hwnd):
		self._hwnd=hwnd
	def attach_to_parent(self):
		if not self._parent: raise error, 'attach_to_parent without parent'	
		hparent = self._parent.GetSafeHwnd()
		self.attach(Sdk.GetDlgItem(hparent,self._id))
	def init(self):
		"""called when os wnd exists"""
		pass
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

	def setcb(self,cb):
		self._cb=cb
	def callcb(self):
		if self._cb: 
			apply(apply,self._cb)

# shortcut
Control = LightWeightControl

# Button control class
class Button(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)

# RadioButton control class
class RadioButton(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def setcheck(self,i):
		if i>0:f=win32con.BST_CHECKED
		elif i==0:f=win32con.BST_UNCHECKED
		else:f=win32con.BST_INDETERMINATE
		self.sendmessage(win32con.BM_SETCHECK,i)
	def getcheck(self):
		i=self.sendmessage(win32con.BM_GETCHECK)
		if i==win32con.BST_CHECKED:return 1
		elif i==win32con.BST_UNCHECKED:return 0
		return -1

# CheckButton control class
class CheckButton(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def setcheck(self,i):
		if i>0:f=win32con.BST_CHECKED
		elif i==0:f=win32con.BST_UNCHECKED
		else:f=win32con.BST_INDETERMINATE
		self.sendmessage(win32con.BM_SETCHECK,i)
	def getcheck(self):
		i=self.sendmessage(win32con.BM_GETCHECK)
		if i==win32con.BST_CHECKED:return 1
		elif i==win32con.BST_UNCHECKED:return 0
		return -1

# Static control class
class Static(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def settext(self,str):
		self.sendmessage_ls(win32con.WM_SETTEXT,0,str)

# Edit control class 				
class Edit(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
	def settext(self,str):
		self.sendmessage_ls(win32con.WM_SETTEXT,0,str)
	def gettextlength(self):
		return self.sendmessage(win32con.WM_GETTEXTLENGTH)
	def gettext(self):
		n=self.gettextlength()+1
		return self.sendmessage_rs(win32con.WM_GETTEXT,n,n)	
	def getlinecount(self):
		return self.sendmessage(win32con.EM_GETLINECOUNT)
	def getline(self,ix):
		n=self.sendmessage(win32con.EM_LINELENGTH)+1
		return self.sendmessage_rs(win32con.EM_GETLINE,ix,n)
	def getmodify(self):
		return self.sendmessage(win32con.EM_GETMODIFY)
	
	def getlines(self):
		if hasattr(self,'_textlines'):
			if self.getmodify()==0:
				return self._textlines
		self._textlines=[]
		nl=self.getlinecount()
		for ix in range(nl):
			line=self.getline(ix)
			self._textlines.append(line)
		return self._textlines

	# cmif interface
	# gettext
	# settext

# Listbox control class
class ListBox(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
		self.__icmif() 
	def setcursel(self,index):
		if index==None: index=-1
		self.sendmessage(win32con.LB_SETCURSEL,index)
	def getcursel(self):
		return self.sendmessage(win32con.LB_GETCURSEL)
	def getcount(self):
		return self.sendmessage(win32con.LB_GETCOUNT)
	def deletestring(self,index):
		self.sendmessage(win32con.LB_DELETESTRING,index)
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
	# initialize cmif related part
	def __icmif(self):
		self.getlistitem=self.gettext
		self.selectitem=self.setcursel
		self.getselection=self.getcursel
		self.delalllistitems=self.resetcontent
	# Add a list item
	def addlistitem(self, item, pos):
		if pos < 0:
			pos = self.getcount()
		self.insertstring(pos,item)
	
	# Replace the item at position
	def replace(self, pos, newitem):
		self.deletestring(pos)
		self.insertstring(pos,newitem)
	
	# Return the list
	def getlist(self):
		l=[]
		for ix in range(self.getcount()):
			l.append(self.gettext(ix))
		return l

	# Add the list of entries
	def addlistitems(self,list,ix=0):
		if type(list)==type(''): 
			self.insertstring(ix,list)
			return
		if ix==-1:
			for pos in range(len(list)):
				self.insertstring(-1,list[pos])
		elif ix>=0:
			for pos in range(ix,len(list)):
				self.insertstring(pos,list[pos])

	# Return  the selection index				
	def getselected(self):
		pos = self.getselection()
		if pos<0:return None
		return pos

	# Return the item at the index
	def getlistitem(self,ix):
		return self.gettext(ix)


# CompoBox control class
class ComboBox(Control):
	def __init__(self,owner=None,id=-1):
		Control.__init__(self,owner,id)
		self.__icmif() 
	def setcursel(self,index):
		if index==None: index=-1
		self.sendmessage(win32con.CB_SETCURSEL,index)
	def getcursel(self):
		return self.sendmessage(win32con.CB_GETCURSEL)
	def getcount(self):
		return self.sendmessage(win32con.CB_GETCOUNT)
	def insertstring(self,ix,str):
		if not str:str='<none>'
		self.sendmessage_ls(win32con.CB_INSERTSTRING,ix,str)
	def addstring(self,str):
		if not str:str='<none>'
		return self.sendmessage_ls(win32con.CB_ADDSTRING,0,str)
	def gettextlen(self,ix):
		return self.sendmessage(win32con.CB_GETLBTEXTLEN,ix)
	def gettext(self,ix):
		n = self.gettextlen(ix) + 1
		return self.sendmessage_rs(win32con.CB_GETLBTEXT,ix,n)
	def resetcontent(self):
		self.sendmessage(win32con.CB_RESETCONTENT)
	def deletestring(self,index):
		self.sendmessage(win32con.CB_DELETESTRING,index)

	# cmif interface
	def __icmif(self):
		self._optionlist=[]
		
	# it is called when os wnd exists
	def init(self):
		for s in self._optionlist:
			self.addstring(s)
		self.setcursel(0)

	def getpos(self):
		'''Get the index of the currently selected option.'''
		return self.getcursel()
	def setpos(self,pos):
		'''Set the index of the selected option.'''
		self.setcursel(pos)

	def getvalue(self):
		'''Get the value of the currently selected option.'''
		sel=self.getcursel()
		return self.gettext(sel)

	def setoptions(self, optionlist, startpos=0):
		if not optionlist: return
		for pos in range(startpos,len(optionlist)):
			self.insertstring(pos,optionlist[pos])
			self._optionlist.append(optionlist[pos])
	def initoptions(self, optionlist,seloption=None):
		if not optionlist: return
		self.setoptions(optionlist)
		self.setcursel(seloption)	
	def setoptions_cb(self, optionlist):
		for item in optionlist:
			if type(item)==type(()):
				self.addstring(item[0])
				self._optionlist.append(item[0])
		self.setcursel(0)
	def setsensitive(self,pos,f):
		seloption=self.getcursel()
		str=self._optionlist[pos]
		if f:
			self.deletestring(pos)
			self.insertstring(pos,str) # add it
		else: 
			self.deletestring(pos) # remove it
			str='['+str+']'
			self.insertstring(pos,str)
		self.setcursel(seloption)

####################################################
# TAB CONTROL STUFF

# Tab control class
class TabCtrl(Control):
	TCM_FIRST  =            0x1300      # Tab control messages
	TCN_FIRST =-550       
	TCN_LAST=-580
	TCN_SELCHANGE  = TCN_FIRST - 1
	TCN_SELCHANGING= TCN_FIRST - 2

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

# Any class derved from this class behaves as a dictionary
class ControlsDict:
	def __init__(self):
		self._subwnddict={}	
	def __nonzero__(self):return 1
	def __len__(self): return len(self._subwnddict)
	def __getitem__(self, key): return self._subwnddict[key]
	def __setitem__(self, key, item): self._subwnddict[key] = item
	def keys(self): return self._subwnddict.keys()
	def items(self): return self._subwnddict.items()
	def values(self): return self._subwnddict.values()
	def has_key(self, key): return self._subwnddict.has_key(key)
	
##############################
# Base class for dialogs created using a resource template 
class ResDialog(dialog.Dialog):
	def __init__(self,id,parent=None,resdll=None):
		if not resdll:
			import __main__
			resdll=__main__.resdll
		dialog.Dialog.__init__(self,id,resdll,parent)
		self._subwndlist = [] # controls add thrmselves to this list

	# Get from the OS and set the window handles to the controls
	def attach_handles_to_subwindows(self):
		hdlg = self.GetSafeHwnd()
		for ctrl in self._subwndlist:
			ctrl.attach(Sdk.GetDlgItem(hdlg,ctrl._id))
	# Call init method for each window
	def init_subwindows(self):
		for w in self._subwndlist:
			w.init()

	# Helper method that calls the callback given the event
	def onevent(self,event):
		try:
			func, arg = self._callbacks[event]			
		except KeyError:
			pass
		else:
			apply(func,arg)

# A special class that it is both an MFC window and A LightWeightControl
from pywin.mfc import window
class WndCtrl(LightWeightControl,window.Wnd):
	def create_wnd_from_handle(self):
		window.Wnd.__init__(self,win32ui.CreateWindowFromHandle(self._hwnd))

# Implementation of the splash screen
class SplashDlg(ResDialog):
	def __init__(self,arg,version):
		ResDialog.__init__(self,grinsRC.IDD_SPLASH)
		self._splash = WndCtrl(self,grinsRC.IDC_SPLASH)
		self._versionc = Static(self,grinsRC.IDC_VERSION_MSG)
		self._msgc = Static(self,grinsRC.IDC_MESSAGE)
		self._version=version

		self.CreateWindow()
		self.CenterWindow()
		self.ShowWindow(win32con.SW_SHOW)
		self.UpdateWindow()

	def OnInitDialog(self):	
		self.attach_handles_to_subwindows()	
		self._versionc.settext(self._version)
		self._splash.create_wnd_from_handle()
		self.HookMessage(self.OnDrawItem,win32con.WM_DRAWITEM)
		self.loadbmp()
		return ResDialog.OnInitDialog(self)

	def close(self):
		if hasattr(self,'DestroyWindow'):
			self.DestroyWindow()
			
	# draw splash
	def OnDrawItem(self,params):
		lParam=params[3]
		hdc=Sdk.ParseDrawItemStruct(lParam)
		dc=win32ui.CreateDCFromHandle(hdc)
		rct=self._splash.GetClientRect()
		win32mu.BitBltBmp(dc,self._bmp,rct)
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(rct,br)
		Sdk.DeleteObject(br)
		dc.DeleteDC()

	# load splash
	def loadbmp(self):
		import __main__
		resdll=__main__.resdll
		self._bmp=win32ui.CreateBitmap()
		self._bmp.LoadBitmap(grinsRC.IDB_SPLASH,resdll)

# Implementation of the about dialog
class AboutDlg(ResDialog):
	def __init__(self,arg,version,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_ABOUT,parent)
		self._splash = WndCtrl(self,grinsRC.IDC_SPLASH)
		self._versionc = Static(self,grinsRC.IDC_VERSION_MSG)
		self._version=version
	def OnInitDialog(self):	
		self.attach_handles_to_subwindows()	
		self._splash.create_wnd_from_handle()
		self.SetWindowText("About GRiNS")
		self._versionc.settext(self._version)
		self.HookMessage(self.OnDrawItem,win32con.WM_DRAWITEM)
		self.loadbmp()
		return ResDialog.OnInitDialog(self)

	# Response to the WM_DRAWITEM
	# draw splash
	def OnDrawItem(self,params):
		lParam=params[3]
		hdc=Sdk.ParseDrawItemStruct(lParam)
		dc=win32ui.CreateDCFromHandle(hdc)
		rct=self._splash.GetClientRect()
		win32mu.BitBltBmp(dc,self._bmp,rct)
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(rct,br)
		Sdk.DeleteObject(br)
		dc.DeleteDC()

	# load splash bmp
	def loadbmp(self):
		import __main__
		resdll=__main__.resdll
		self._bmp=win32ui.CreateBitmap()
		self._bmp.LoadBitmap(grinsRC.IDB_SPLASH,resdll)

# Implementation of the open loaction dialog
class OpenLocationDlg(ResDialog):
	def __init__(self,callbacks=None,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_DIALOG_OPENLOCATION,parent)
		self._callbacks=callbacks

		self._text= Edit(self,grinsRC.IDC_EDIT_LOCATION)
		self._bcancel = Button(self,win32con.IDCANCEL)
		self._bopen = Button(self,win32con.IDOK)
		self._bbrowse= Button(self,grinsRC.IDC_BUTTON_BROWSE)

	def OnInitDialog(self):	
		self.attach_handles_to_subwindows()	
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

# Implementation of the Layout name dialog

class LayoutNameDlg(ResDialog):
	def __init__(self,promp,default_text,cb_ok,cancelCallback=None,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_LAYOUT_NAME,parent)
		self._text= Edit(self,grinsRC.IDC_EDIT1)
		self._cb_ok=cb_ok
		self._cbd_cancel=cancelCallback
		self._default_text=default_text

	def OnInitDialog(self):
		self.attach_handles_to_subwindows()
		self._text.settext(self._default_text)
		return ResDialog.OnInitDialog(self)

	def show(self):
		self.DoModal()

	def OnOK(self):
		text=self._text.gettext()
		self._obj_.OnOK()
		if self._cb_ok:
			apply(self._cb_ok,(text,))

	def OnCancel(self):
		self._obj_.OnCancel()
		if self._cbd_cancel:
			apply(apply,self._cbd_cancel)

		self.__chantype=w._chantype
		w._cbd_ok=(self.__okchannel, (0,))
		w._cbd_cancel=(self.__okchannel, (1,))

# Implementation of the new channel dialog
class NewChannelDlg(ResDialog):
	def __init__(self,title,default,grab=1,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_NEW_CHANNEL,parent)
		self._title=title
		self._default_name=default
		self._parent=parent
		self._chantext= Edit(self,grinsRC.IDC_CHANNEL_NAME)
		self._chantype=ComboBox(self,grinsRC.IDC_CHANNEL_TYPE)
		self._cbd_ok=None
		self._cbd_cancel=None

	def OnInitDialog(self):
		self.attach_handles_to_subwindows()
		self.init_subwindows()
		self._chantext.settext(self._default_name)
		return ResDialog.OnInitDialog(self)

	def show(self):
		self.DoModal()
	def close(self):
		self.EndDialog(win32con.IDCANCEL)

	def OnOK(self):
		if self._cbd_ok:
			apply(apply,self._cbd_ok)
	def OnCancel(self):
		if self._cbd_cancel:
			apply(apply,self._cbd_cancel)

# Implementation of a modeless message box
class ModelessMessageBox(ResDialog):
	def __init__(self,text,title,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_MESSAGE_BOX,parent)
		self._text= Static(self,grinsRC.IDC_STATIC1)
		self.CreateWindow()
		self._text.attach_to_parent()
		self.SetWindowText(title)
		self._text.settext(text)

# Implementation of the showmessage dialog needed by the core
class showmessage:
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message', parent = None):
		self._wnd=None
		if grab==0:
			self._wnd=ModelessMessageBox(text,title,parent)
			return
		if mtype == 'error':
			style = win32con.MB_OK |win32con.MB_ICONERROR
				
		elif mtype == 'warning':
			style = win32con.MB_OK |win32con.MB_ICONWARNING
			
		elif mtype == 'information':
			style = win32con.MB_OK |win32con.MB_ICONINFORMATION
	
		elif mtype == 'message':
			style = win32con.MB_OK|win32con.MB_ICONINFORMATION
			
		elif mtype == 'question':
			style = win32con.MB_OKCANCEL|win32con.MB_ICONQUESTION
		
		if not parent:	
			self._res = win32ui.MessageBox(text,title,style)
		else:
			self_res = parent.MessageBox(text,title,style)
		if callback and self._res==win32con.IDOK:
			apply(apply,callback)
		elif cancelCallback and self._res==win32con.IDCANCEL:
			apply(apply,cancelCallback)

	# Returns user response
	def getresult(self):
		return self._res

# Implementation of a question message box
class _Question:
	def __init__(self, text, parent = None):
		self.answer = None
		self.answer=showmessage(text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)),
			    parent = parent)

	def callback(self, answer):
#		if _in_create_box:
#			return
		self.answer = answer

# Shows a question to the user and returns the response
def showquestion(text, parent = None):
	q=_Question(text, parent = parent)
	return q.answer

# A Multiple choice dialog implementation		
class _MultChoice:
	def __init__(self, prompt, msg_list, defindex, parent = None):
		#self.looping = FALSE
		self.answer = None
		self.msg_list = msg_list
		list = []
#		for msg in msg_list:
#			list.append(msg, (self.callback, (msg,)))
		str='_MultChoice request'+prompt
		win32ui.MessageBox(str)

# Displays multiple choice dialog
def multchoice(prompt, list, defindex, parent = None):
	m=_MultChoice(prompt, list, defindex, parent = parent)
	return None

# A general one line modal input dialog implementation
# use DoModal
class InputDialog(dialog.Dialog):
	def __init__(self, prompt, defValue, title ):
		self.title=title
		dialog.Dialog.__init__(self, win32ui.IDD_SIMPLE_INPUT)
		self.AddDDX(win32ui.IDC_EDIT1,'result')
		self.AddDDX(win32ui.IDC_PROMPT1, 'prompt')
		self._obj_.data['result']=defValue
		self._obj_.data['prompt']=prompt
	def OnInitDialog(self):
		self.SetWindowText(self.title)
		return dialog.Dialog.OnInitDialog(self)

#
# A general one line modeless input dialog implementation
# if not closed by def OK,Cancel call DestroyWindow()
# design decision: Dlg closes itself or the callback? 
class ModelessInputDialog(InputDialog):
	def __init__(self, prompt, defValue, title):
		InputDialog.__init__(self, prompt, defValue, title)
		self._ok_callback=None
		self._cancel_callback=None
	def OnOK(self):
		self._obj_.UpdateData(1) # do DDX
		if self._ok_callback:
			self._ok_callback(self)
		return self._obj_.OnOK()
	def OnCancel(self):
		if self._cancel_callback:
			self._cancel_callback(self)
		return self._obj_.OnCancel()

# Displays a message and requests from the user to select Yes or No or Cancel
def GetYesNoCancel(promp,parent=None):
	if parent:m=parent
	else: m=win32ui
	res=m.MessageBox(promp,'GRiNS Editor',win32con.MB_YESNOCANCEL|win32con.MB_ICONQUESTION)
	if res==win32con.IDYES:return 0
	elif res==win32con.IDNO:return 1
	else: return 2
	
# The create box dialog implementation
class CreateBoxDlg(ResDialog):
	def __init__(self,text,callback,cancelCallback,parent=None):
		ResDialog.__init__(self,grinsRC.IDD_CREATE_BOX1,parent)
		self._text= Static(self,grinsRC.IDC_STATIC1)
		self.CreateWindow()
		self._text.attach_to_parent()
		self._text.settext(text)
		self._callback=callback
		self._cancelCallback=cancelCallback
		self.ShowWindow(win32con.SW_SHOW)
		self.UpdateWindow()
	def OnOK(self):
		self._obj_.OnOK()
		if self._callback:
			apply(apply,self._callback)
	def OnCancel(self):
		self._obj_.OnCancel()
		if self._cancelCallback:
			apply(apply,self._cancelCallback)

# A general dialog that displays a combo with options for the user to select.
class SimpleSelectDlg(ResDialog):
	def __init__(self,list, title = '', prompt = None,parent = None):
		ResDialog.__init__(self,grinsRC.IDD_SELECT_ONE,parent)
		self._prompt_ctrl= Static(self,grinsRC.IDC_STATIC1)
		self._list_ctrl= ComboBox(self,grinsRC.IDC_COMBO1)
		self._list=list
		self._title=title
		self._prompt=prompt
		
	def OnInitDialog(self):
		dialog.Dialog.OnInitDialog(self)

		self._prompt_ctrl.attach_to_parent()
		if not self._prompt:self._prompt='Select:'
		self._prompt_ctrl.settext(self._prompt)

		if not self._title:
			if self._prompt:self._title=self._prompt
			else: self._title='Select'
		self.SetWindowText(self._title)
		
		self._list_ctrl.attach_to_parent()
		self._list_ctrl.setoptions_cb(self._list)

	def OnOK(self):
		ix=self._list_ctrl.getcursel()
		res=self._obj_.OnOK()
		if ix>=0:
			item=self._list[ix]
			if type(item)==type(()):
				apply(apply,item[1])
		return res

	def OnCancel(self):
		# nothing
		return self._obj_.OnCancel()
	
	def HookKeyStroke(self,cb,key):
		if hasattr(self,'_obj_') and self._obj_:	
			self.HookKeyStroke(cb,key)

# Displays a dialog with options for the user to select
def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1,
	   parent = None):
	dlg=SimpleSelectDlg(list,title,prompt,parent)
	if grab==1:dlg.DoModal()
	else:dlg.CreateWindow()
	return dlg

#####################################
# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

# Base class for dialog bars
class DlgBar(window.Wnd,ControlsDict):
	AFX_IDW_DIALOGBAR=0xE805
	def __init__(self):
		ControlsDict.__init__(self)
		window.Wnd.__init__(self,win32ui.CreateDialogBar())
	def create(self,frame,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		self._obj_.CreateWindow(frame,resid,
			align,self.AFX_IDW_DIALOGBAR)
	def show(self):
		self.ShowWindow(win32con.SW_SHOW)
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)

# A dialog bar with a message to be displayed while in the create box mode
class CreateBoxBar(DlgBar):
	def __init__(self,frame,text,callback=None,cancelCallback=None):
		DlgBar.__init__(self)
		DlgBar.create(self,frame,grinsRC.IDD_CREATE_BOX,afxres.CBRS_ALIGN_TOP)
		
		static= Static(self,grinsRC.IDC_STATIC1)
		cancel=Button(self,grinsRC.IDUC_CANCEL)
		ok=Button(self,grinsRC.IDUC_OK)
		
		static.attach_to_parent()
		cancel.attach_to_parent()
		ok.attach_to_parent()
		
		frame.HookCommand(self.onCancel,cancel._id)
		frame.HookCommand(self.onOK,ok._id)

		static.settext(text)
		self._callback=callback
		self._cancelCallback=cancelCallback
		
		self._frame=frame
		frame.RecalcLayout()

	def close(self):
		self.DestroyWindow()
		self._frame.RecalcLayout()
		del self._obj_
		
	def onOK(self,id,code):
		self.close()
		if self._callback:
			apply(apply,self._callback)

	def onCancel(self,id,code):
		self.close()
		if self._cancelCallback:
			apply(apply,self._cancelCallback)

