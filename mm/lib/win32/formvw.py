import win32ui
from win32con import *
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()
import win32mu,wc

import grinsRC
from components import *
from pywin.mfc import window,object,docview


class FormViewBase(docview.FormView):
	def __init__(self,doc,id):
		docview.FormView.__init__(self,doc,id)
		self._cursor=''
		self._subwindows=[]
		self._parent=None

	def createWindow(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
		self.attach_handles_to_controls()

	def OnInitialUpdate(self):
		pass
		
	# cmif interface
	def close(self):
		pass

	def show(self):
		pass

	def is_showing(self):
		if not self._obj_: return 0
		return self.GetSafeHwnd()

	def hide(self):
		pass

	def setcursor(self, cursor):
		if cursor == self._cursor:
			return
		win32mu.SetCursor(cursor)
		self._cursor = cursor

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

	# delegate to parent for cmds and adorment functionality
	def set_dynamiclist(self, cmd, list):
		self._parent.set_dynamiclist(cmd,list)
	def set_adornments(self, adornments):
		self._parent.set_adornments(adornments)
	def set_toggle(self, command, onoff):
		self._parent.set_toggle(command,onoff)
		
	def set_commandlist(self, list):
		self._parent.set_commandlist(list,'view')
	def settitle(self,title):
		self._parent.settitle(title,'view')


class LayoutView(FormViewBase):
	def __init__(self,doc):
		FormViewBase.__init__(self,doc,grinsRC.IDD_LAYOUT)

		self._layoutlist=List(self,grinsRC.IDC_LAYOUTS)
		self._channellist=List(self,grinsRC.IDC_LAYOUT_CHANNELS)
		self._otherlist=List(self,grinsRC.IDC_OTHER_CHANNELS)
		self._id2list={
			grinsRC.IDC_LAYOUTS:self._layoutlist,
			grinsRC.IDC_LAYOUT_CHANNELS:self._channellist,
			grinsRC.IDC_OTHER_CHANNELS:self._otherlist,
			}

		self._class2ui={
			 NEW_LAYOUT:Button(self,grinsRC.IDC_NEW_LAYOUT),
			 RENAME:Button(self,grinsRC.IDC_RENAME_LAYOUT),
			 DELETE:Button(self,grinsRC.IDC_DELETE_LAYOUT),
			 NEW_CHANNEL:Button(self,grinsRC.IDC_NEW_CHANNEL),
			 REMOVE_CHANNEL:Button(self,grinsRC.IDC_REMOVE_CHANNEL),
			 #ATTRIBUTES:Button(self,grinsRC.IDC_CHANNEL_ATTR),
			 ADD_CHANNEL:Button(self,grinsRC.IDC_ADD_CHANNEL),
			 CLOSE_WINDOW:Button(self,grinsRC.IDC_ADD_CHANNEL),
			 }
		self._activecmds={}

	def createWindow(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
		self.attach_handles_to_controls()
		for cl in self._class2ui.keys():
			usercmd_ui=self._class2ui[cl]
			usercmd_ui.enable(0)

	def OnInitialUpdate(self):
		self.HookMessage(self.OnUserCmd,WM_COMMAND)

	def set_commandlist(self,commandlist):
		contextcmds=self._activecmds
		for id in contextcmds.keys():
			cmd=contextcmds[id]
			usercmd_ui = self._class2ui[cmd.__class__]
			usercmd_ui.enable(0)
		contextcmds.clear()
		if not commandlist: return
		for cmd in commandlist:
			usercmd_ui = self._class2ui[cmd.__class__]
			id=usercmd_ui._id
			usercmd_ui.enable(1)
			contextcmds[id]=cmd

	def OnUserCmd(self,params):
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()

		#check for list message
		if msg.getnmsg()==LBN_SELCHANGE:
			if id in self._id2list.keys():
				self._id2list[id].callcb()
				return

		# a button		
		cmd=None
		contextcmds=self._activecmds
		if contextcmds.has_key(id):
			cmd=contextcmds[id]
		if cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)


import AppForms
class FormView(FormViewBase,AppForms.WindowV):
	def __init__(self,doc):
		FormViewBase.__init__(self,doc,grinsRC.IDD_FORM)

	def createWindow(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
		self.attach_handles_to_controls()
		AppForms.WindowV.__init__(self,self)
