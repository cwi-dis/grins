__version__ = "$Id$"

""" @win32doc|_UsergroupView
This module contains the ui implementation of the UsergroupView.
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

The _UsergroupView is created using the resource dialog template with identifier IDD_USERGROUP.
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


class _UsergroupView(components.DlgBar):

	# Class contructor. Associates member controls with their ids
	def __init__(self):
		components.DlgBar.__init__(self)
		self['Groups']=components.ListBox(self,grinsRC.IDC_GROUPS)
		self['New']=components.Button(self,grinsRC.IDCMD_NEW_GROUP)
		self['Edit']=components.Button(self,grinsRC.IDCMD_EDIT_GROUP)
		self['Delete']=components.Button(self,grinsRC.IDCMD_DELETE_GROUP)
		self['Close']=components.Button(self,grinsRC.IDCMD_CLOSE_USERGROUPVIEW)	
		self._activecmds={}
		self._init_ugroups=[]
		self._init_pos=None

	# Helper function to create the OS window.
	def create(self,frame):
		components.DlgBar.create(self,frame,grinsRC.IDD_USERGROUP,afxres.CBRS_ALIGN_LEFT)
		for i in self.keys():self[i].attach_to_parent()
		frame.RecalcLayout()
		frame.HookCommand(self.OnListCmd,self['Groups']._id)

		frame.HookCommand(self.OnCmd,self['New']._id)
		frame.HookCommand(self.OnCmd,self['Edit']._id)
		frame.HookCommand(self.OnCmd,self['Delete']._id)

		frame.HookCommand(self.OnCmd,self['Close']._id)

		frame.HookCommandUpdate(frame.OnUpdateCmdEnable,self['New']._id)
		frame.HookCommandUpdate(frame.OnUpdateCmdDissable,self['Edit']._id)
		frame.HookCommandUpdate(frame.OnUpdateCmdDissable,self['Delete']._id)

		frame.HookCommandUpdate(frame.OnUpdateCmdEnable,self['Close']._id)

		if len(self._init_ugroups):
			self.setgroups(self._init_ugroups,self._init_pos)

	# Sets the acceptable commands. 
	def set_cmddict(self,cmddict):
		self._cmddict=cmddict
	
	# Response to a selection change of the listbox 
	def OnListCmd(self,id,code):
		if code==win32con.LBN_SELCHANGE:
			frame=self.GetParent()
			pos=self['Groups'].getcursel()
			if pos==None or pos<0:
				frame.HookCommandUpdate(frame.OnUpdateCmdDissable,self['Edit']._id)
				frame.HookCommandUpdate(frame.OnUpdateCmdDissable,self['Delete']._id)
			else:
				frame.HookCommandUpdate(frame.OnUpdateCmdEnable,self['Edit']._id)
				frame.HookCommandUpdate(frame.OnUpdateCmdEnable,self['Delete']._id)
		if code==win32con.LBN_DBLCLK:				
			apply(apply,self._cmddict['Edit'])

	# Response to control notification
	def OnCmd(self,id,code):
		if id==self['Close']._id:
			self.GetParent().PostMessage(win32con.WM_COMMAND,USERGROUPVIEW_UI.id)
			return
		for k in self.keys():
			if self[k]._id==id:
				if k in self._cmddict.keys():
					apply(apply,self._cmddict[k])
				return	

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

	def is_oswnd(self):
		return self.IsWindow()

	def getgroup(self):
		"""Return name of currently selected user group."""
		if self.is_oswnd():
			ix=self['Groups'].getcursel()
			if ix==None or ix<0: return None
			return self['Groups'].gettext(ix)
		else:
			if not self._init_pos: return None
			return self._init_ugroups[self._init_pos]

	def setgroups(self, ugroups, pos):
		"""Set the list of user groups.

		Arguments (no defaults):
		ugroups -- list of strings giving the names of the user groups
		pos -- None or index in ugroups list--the initially
			selected element in the list
		"""
		if self.is_oswnd():
			l=self['Groups']
			l.delalllistitems()
			l.addlistitems(ugroups, 0)
			l.selectitem(pos)
			self.OnListCmd(l._id,win32con.LBN_SELCHANGE)
		else:
			self._init_ugroups=ugroups
			self._init_pos=pos
				



class UsergroupEditDialog(components.ResDialog,components.ControlsDict):
	def __init__(self,parent=None):
		components.ResDialog.__init__(self,grinsRC.IDD_EDIT_USERGROUP,parent)
		components.ControlsDict.__init__(self)
		self['Name']=components.Edit(self,grinsRC.IDC_EDIT1)
		self['Title']=components.Edit(self,grinsRC.IDC_EDIT2)
		self['State']=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self['Override']=components.ComboBox(self,grinsRC.IDC_COMBO2)
		self['Cancel']=components.Button(self,win32con.IDCANCEL)
		self['Restore']=components.Button(self,grinsRC.IDC_RESTORE)
		self['Apply']=components.Button(self,grinsRC.IDC_APPLY)
		self['OK']=components.Button(self,win32con.IDOK)

		self.CreateWindow()
		self.attach_handles_to_subwindows()	
		self.HookCommand(self.OnRestore,self['Restore']._id)
		self.HookCommand(self.OnApply,self['Apply']._id)

	def do_init(self, ugroup, title, ustate, override, cbdict):
		ls=['NOT RENDERED', 'RENDERED']	
		self['State'].initoptions(ls)
		lo=['not allowed', 'allowed']
		self['Override'].initoptions(lo)
		self.setstate(ugroup, title, ustate, override)
		self._cbdict=cbdict

	def OnOK(self):
		apply(apply,self._cbdict['OK'])
	def OnCancel(self):
		apply(apply,self._cbdict['Cancel'])
	def OnRestore(self,id,code):
		apply(apply,self._cbdict['Restore'])
	def OnApply(self,id,code):
		apply(apply,self._cbdict['Apply'])
		
	def show(self):
		"""Show the dialog (pop it up again)."""
		self.CenterWindow()
		self.ShowWindow(win32con.SW_SHOW)
		self.UpdateWindow()

	def close(self):
		"""Close the dialog."""
		self.DestroyWindow()

	def setstate(self, ugroup, title, ustate, override):
		"""Set the values in the dialog.

		Arguments (no defaults):
		ugroup -- string name of the user group
		title -- string title of the user group
		ustate -- string 'RENDERED' or 'NOT RENDERED'
		override -- string 'allowed' or 'not allowed'
		"""
		self['Name'].settext(ugroup)
		self['Title'].settext(title)
		self['State'].setpos(ustate == 'RENDERED')
		self['Override'].setpos(override == 'allowed')

	def getstate(self):
		"""Return the current values in the dialog."""
		return self['Name'].gettext(), \
		       self['Title'].gettext(), \
		       self['State'].getvalue(), \
		       self['Override'].getvalue()
