# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# UserCmds
from usercmd import *
from usercmdui import *

# GRiNS resource ids
import grinsRC


class _LayoutView(components.DlgBar):
	def __init__(self):
		components.DlgBar.__init__(self)
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
		self[CLOSE_WINDOW]=components.Button(self,grinsRC.IDCMD_CLOSE_WINDOW)
		
		self._activecmds={}


	def create(self,frame):
		components.DlgBar.create(self,frame,grinsRC.IDD_LAYOUT1,afxres.CBRS_ALIGN_LEFT)
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
				frame.HookCommandUpdate(frame.OnUpdateCmdDissable,self[cl]._id)

	# the close sequence must be delegated to parent
	def set_commandlist(self,commandlist):
		frame=self.GetParent()
		contextcmds=self._activecmds
		for cl in self.keys():
			if type(cl)!=type(''):
				frame.HookCommandUpdate(frame.OnUpdateCmdDissable,self[cl]._id)
		contextcmds.clear()
		if not commandlist: return
		for cmd in commandlist:
			id=self[cmd.__class__]._id
			frame.HookCommandUpdate(frame.OnUpdateCmdEnable,id)
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
		if cmd.__class__==CLOSE_WINDOW:
			self.GetParent().PostMessage(win32con.WM_COMMAND,LAYOUTVIEW_UI.id)
		elif cmd is not None and cmd.callback is not None:
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

