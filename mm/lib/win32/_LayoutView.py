__version__ = "$Id$"

""" @win32doc|_LayoutView
This module contains the ui implementation of the LayoutView.
It is implemented as a dialog bar.
The MFC CDialogBar class provides the functionality of 
a Windows modeless dialog box in a control bar. 
A dialog bar resembles a dialog box in that it contains 
standard Windows controls that the user can tab between. 
Another similarity is that you create a dialog template 
to represent the dialog bar.
Objects of this class are exported to Python through the win32ui pyd
as objects of type PyCDialogBar.
The _LayoutView extends the PyCDialogBar.

The _LayoutView is created using the resource dialog template with identifier IDD_LAYOUT1.
To edit this template, open it using the resource editor. 
Like all resources it can be found in cmif\win32\src\GRiNSRes\GRiNSRes.rc.
The resource project is cmif\win32\src\GRiNSRes\GRiNSRes.dsp which creates
the run time GRiNSRes.dll

"""

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

	# Class contructor. Associates member controls with their ids
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

	# Helper function to create the OS window.
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

	# Sets the acceptable commands. 
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
	
	# Response to a selection change of the listbox 
	def OnListCmd(self,id,code):
		if code==win32con.LBN_SELCHANGE:
			for s in self._lnames:
				if self[s]._id==id:
					self[s].callcb()
					break

	# Response to control notification
	def OnCmd(self,id,code):
		cmd=None
		contextcmds=self._activecmds
		if contextcmds.has_key(id):
			cmd=contextcmds[id]
		if cmd.__class__==CLOSE_WINDOW:
			self.GetParent().PostMessage(win32con.WM_COMMAND,LAYOUTVIEW_UI.id)
		elif cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)

	# Returns true if the window is visible
	def is_showing(self):
		return self.GetSafeHwnd() and self.IsWindowVisible()

	# Called by the core system to close this view
	def close(self):
		frame=self.GetParent()
		self.DestroyWindow()
		frame.RecalcLayout()

	# Called by the core system to show the view
	def show(self):
		if self.GetSafeHwnd():
			frame=self.GetParent()
			self.ShowWindow(win32con.SW_SHOW)
			frame.RecalcLayout()

	# Called by the core system to hide the view
	def hide(self):
		if self.GetSafeHwnd():
			frame=self.GetParent()
			self.ShowWindow(win32con.SW_HIDE)
			frame.RecalcLayout()

