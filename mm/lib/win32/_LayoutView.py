# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# UserCmds
from usercmd import *

# GRiNS resource ids
import grinsRC

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

class DlgBar(window.Wnd,ControlsDict):
	AFX_IDW_DIALOGBAR=0xE805
	def __init__(self):
		ControlsDict.__init__(self)
		AFX_IDW_DIALOGBAR=0xE805
		window.Wnd.__init__(self,win32ui.CreateDialogBar())
	def create(self,frame,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		self._obj_.CreateWindow(frame,resid,
			align,self.AFX_IDW_DIALOGBAR)
	def show(self):
		self.ShowWindow(win32con.SW_SHOW)
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)

class _LayoutView(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
		self._lnames=l=('LayoutList','ChannelList','OtherList')
		self[l[0]]=components.ListBox(self,grinsRC.IDC_LAYOUTS)
		self[l[1]]=components.ListBox(self,grinsRC.IDC_LAYOUT_CHANNELS)
		self[l[2]]=components.ListBox(self,grinsRC.IDC_OTHER_CHANNELS)

		self[NEW_LAYOUT]=components.Button(self,grinsRC.IDCMD_NEW_LAYOUT)
		self[RENAME]=components.Button(self,grinsRC.IDCMD_RENAME)
		self[DELETE]=components.Button(self,grinsRC.IDCMD_DELETE)
		self[NEW_CHANNEL]=components.Button(self,grinsRC.IDCMD_NEW_CHANNEL)
		self[REMOVE_CHANNEL]=components.Button(self,grinsRC.IDCMD_REMOVE_CHANNEL)
		self[ATTRIBUTES]=components.Button(self,grinsRC.IDCMD_ATTRIBUTES)
		self[ADD_CHANNEL]=components.Button(self,grinsRC.IDCMD_ADD_CHANNEL)
		self[CLOSE_WINDOW]=components.Button(self,grinsRC.IDUC_CLOSE_WINDOW)
		
		self._activecmds={}

	def create(self,frame):
		DlgBar.create(self,frame,grinsRC.IDD_LAYOUT1,afxres.CBRS_ALIGN_LEFT)
		for i in self.keys():self[i].attach_to_parent()
		frame.RecalcLayout()
		for cl in self.keys():
			if cl in self._lnames:
				frame.HookCommand(self.OnListCmd,self[cl]._id)
			else:
				frame.HookCommand(self.OnCmd,self[cl]._id)
		# disable all buttons
		for cl in self.keys():
			if cl not in self._lnames: 
				usercmd_ui=self[cl]
				usercmd_ui.enable(0)

	# the close sequence must be delegated to parent
	def set_commandlist(self,commandlist):
		contextcmds=self._activecmds
		for id in contextcmds.keys():
			cmd=contextcmds[id]
			usercmd_ui = self[cmd.__class__]
			usercmd_ui.enable(0)
		contextcmds.clear()
		if not commandlist: return
		for cmd in commandlist:
			usercmd_ui = self[cmd.__class__]
			id=usercmd_ui._id
			usercmd_ui.enable(1)
			contextcmds[id]=cmd
	
	def OnListCmd(self,id,code):
		if code==win32con.LBN_SELCHANGE:
			for s in self._lnames:
				if self[s]._id==id:
					self[s].callcb()
					break
	def OnCmd(self,id,code):
		cmd=None
		contextcmds=self._activecmds
		if contextcmds.has_key(id):
			cmd=contextcmds[id]
		if cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)

	# cmif common interface
	def is_showing(self):
		return self.GetSafeHwnd() and self.IsWindowVisible()
	def close(self):
		frame=self.GetParent()
		self.DestroyWindow()
		frame.RecalcLayout()
	def show(self):
		if self.GetSafeHwnd():
			frame=self.GetParent()
			self.ShowWindow(win32con.SW_SHOW)
			frame.RecalcLayout()
	def hide(self):
		if self.GetSafeHwnd():
			frame=self.GetParent()
			self.ShowWindow(win32con.SW_HIDE)
			frame.RecalcLayout()

#####################################
# OLD

"""
class FormViewBase(docview.FormView):
	def __init__(self,doc,id):
		docview.FormView.__init__(self,doc,id)
		self._cursor=''
		self._subwndlist=[]
		self._parent=None
		self._title='FormViewBase'
		self._close_cmd_list=[]

	def createWindow(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
		self.attach_handles_to_subwindows()

	def OnInitialUpdate(self):
		self._mdiframe=(self.GetParent()).GetMDIFrame()

	def onActivate(self,f):
		if f:self._mdiframe.set_commandlist(self._close_cmd_list)
		else:self._mdiframe.set_commandlist(None)

		
	# cmif interface

	# called directly from cmif-core
	# to close window
	def close(self):
		# 1. clean self contends
		# self._close()

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()

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

	def attach_handles_to_subwindows(self):
		hdlg = self.GetSafeHwnd()
		for ctrl in self._subwndlist:
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


class _LayoutView_X(FormViewBase):
	def __init__(self,doc):
		FormViewBase.__init__(self,doc,grinsRC.IDD_LAYOUT)

		self._layoutlist=ListBox(self,grinsRC.IDC_LAYOUTS)
		self._channellist=ListBox(self,grinsRC.IDC_LAYOUT_CHANNELS)
		self._otherlist=ListBox(self,grinsRC.IDC_OTHER_CHANNELS)
		self._id2list={
			grinsRC.IDC_LAYOUTS:self._layoutlist,
			grinsRC.IDC_LAYOUT_CHANNELS:self._channellist,
			grinsRC.IDC_OTHER_CHANNELS:self._otherlist,
			}

		self._class2ui={
			 NEW_LAYOUT:Button(self,grinsRC.IDCMD_NEW_LAYOUT),
			 RENAME:Button(self,grinsRC.IDCMD_RENAME),
			 DELETE:Button(self,grinsRC.IDCMD_DELETE),
			 NEW_CHANNEL:Button(self,grinsRC.IDCMD_NEW_CHANNEL),
			 REMOVE_CHANNEL:Button(self,grinsRC.IDCMD_REMOVE_CHANNEL),
			 ATTRIBUTES:Button(self,grinsRC.IDCMD_ATTRIBUTES),
			 ADD_CHANNEL:Button(self,grinsRC.IDCMD_ADD_CHANNEL),
			 CLOSE_WINDOW:Button(self,grinsRC.IDUC_CLOSE_WINDOW),
			 }
		self._activecmds={}

	def createWindow(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
		self.attach_handles_to_subwindows()
		for cl in self._class2ui.keys():
			usercmd_ui=self._class2ui[cl]
			usercmd_ui.enable(0)

	def OnInitialUpdate(self):
		self._mdiframe=(self.GetParent()).GetMDIFrame()
		self.HookMessage(self.OnUserCmd,WM_COMMAND)

	# the close sequence must be delegated to parent
	def set_commandlist(self,commandlist):
		contextcmds=self._activecmds
		for id in contextcmds.keys():
			cmd=contextcmds[id]
			usercmd_ui = self._class2ui[cmd.__class__]
			usercmd_ui.enable(0)
		contextcmds.clear()
		self._close_cmd_list=[]
		if not commandlist: return
		for cmd in commandlist:
			usercmd_ui = self._class2ui[cmd.__class__]
			id=usercmd_ui._id
			usercmd_ui.enable(1)
			contextcmds[id]=cmd
			if cmd.__class__==CLOSE_WINDOW:
				self._close_cmd_list.append(cmd)
		self._mdiframe.set_commandlist(self._close_cmd_list)
			
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

	# called directly from cmif-core
	# to close window
	def close(self):
		# 1. clean self contends
		self._mdiframe.set_commandlist(None)

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()
		
"""

