__version__ = "$Id$"

# @win32doc|_UsergroupView
# This module contains the ui implementation of the UsergroupView.
# It is implemented as a Form view.
# The MFC CFormView is essentially a view that contains controls. 
# These controls are laid out based on a dialog-template resource
# similar to a dialog box.
# Objects of this class are exported to Python through the win32ui pyd
# as objects of type PyCFormView.
# The _UsergroupView extends the GenFormView which is an extension to PyCFormView.

# The _UsergroupView is created using the resource dialog template with identifier IDD_USERGROUP.
# To edit this template, open it using the resource editor. 
# Like all resources it can be found in cmif\win32\src\GRiNSRes\GRiNSRes.rc.
# The resource project is cmif\win32\src\GRiNSRes\GRiNSRes.dsp which creates
# the run time GRiNSRes.dll

# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu, components, win32dialog

# std mfc windows stuf
from pywinlib.mfc import window,object,docview,dialog
import afxres,commctrl

# UserCmds
from usercmd import *
from usercmdui import *

# GRiNS resource ids
import grinsRC

from GenFormView import GenFormView

class _UsergroupView(GenFormView):
	def __init__(self,doc,bgcolor=None):
		GenFormView.__init__(self,doc,grinsRC.IDD_USERGROUP)	
		self['Groups']=components.ListBox(self,grinsRC.IDC_GROUPS)
		self['New']=components.Button(self,grinsRC.IDCMD_NEW_GROUP)
		self['Edit']=components.Button(self,grinsRC.IDCMD_EDIT_GROUP)
		self['Delete']=components.Button(self,grinsRC.IDCMD_DELETE_GROUP)

		self._init_ugroups=[]
		self._init_pos=None

	# Sets the acceptable commands. 
	def set_cmddict(self,cmddict):
		self._cmddict=cmddict

	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		self.EnableCmd('Groups',1)
		self.EnableCmd('New',1)
		if len(self._init_ugroups):
			self.setgroups(self._init_ugroups,self._init_pos)

	# Reponse to message WM_COMMAND
	def OnCmd(self,params):
		# crack message
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		
		# special response	
		if id==self['Groups']._id:self.OnListCmd(id,nmsg)

		# std stuff
		for k in self.keys():
			if self[k]._id==id:
				if self._cmddict.has_key(k):
					apply(apply,self._cmddict[k])
				return

	# Response to a selection change of the listbox
	# and selection dblclick 
	def OnListCmd(self,id,code):
		if code==win32con.LBN_SELCHANGE:
			pos=self['Groups'].getcursel()
			if pos==None or pos<0:
				self.EnableCmd('Edit',0)
				self.EnableCmd('Delete',0)
			else:
				self.EnableCmd('Edit',1)
				self.EnableCmd('Delete',1)
		if code==win32con.LBN_DBLCLK:				
			apply(apply,self._cmddict['Edit'])


	def getgroup(self):
		# Return name of currently selected user group.
		if self.is_oswindow():
			ix=self['Groups'].getcursel()
			if ix==None or ix<0: return None
			return self['Groups'].gettext(ix)
		else:
			if not self._init_pos: return None
			return self._init_ugroups[self._init_pos]

	def setgroups(self, ugroups, pos):
		# Set the list of user groups.
		# Arguments (no defaults):
		# ugroups -- list of strings giving the names of the user groups
		# pos -- None or index in ugroups list--the initially
		# 	selected element in the list
		if self.is_oswindow():
			l=self['Groups']
			l.delalllistitems()
			l.addlistitems(ugroups, 0)
			l.selectitem(pos)
			self.OnListCmd(l._id,win32con.LBN_SELCHANGE)
		else:
			self._init_ugroups=ugroups
			self._init_pos=pos
				



class UsergroupEditDialog(win32dialog.ResDialog,components.ControlsDict):
	def __init__(self,parent=None):
		win32dialog.ResDialog.__init__(self,grinsRC.IDD_EDIT_USERGROUP,parent)
		components.ControlsDict.__init__(self)
		self['Name']=components.Edit(self,grinsRC.IDC_EDIT1)
		self['Title']=components.Edit(self,grinsRC.IDC_EDIT2)
		self['State']=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self['Override']=components.ComboBox(self,grinsRC.IDC_COMBO2)
		self['UID']=components.Edit(self,grinsRC.IDC_EDIT3)
		self['Cancel']=components.Button(self,win32con.IDCANCEL)
		self['Restore']=components.Button(self,grinsRC.IDC_RESTORE)
		self['Apply']=components.Button(self,grinsRC.IDC_APPLY)
		self['OK']=components.Button(self,win32con.IDOK)

		self.CreateWindow()
		self.attach_handles_to_subwindows()	
		self.HookCommand(self.OnRestore,self['Restore']._id)
		self.HookCommand(self.OnApply,self['Apply']._id)

	def do_init(self, ugroup, title, ustate, override, cbdict, uid):
		ls=['NOT RENDERED', 'RENDERED']
		self['State'].initoptions(ls)
		lo=['hidden', 'visible']
		self['Override'].initoptions(lo)
		self.setstate(ugroup, title, ustate, override, uid)
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
		# Show the dialog (pop it up again).
		self.CenterWindow()
		self.ShowWindow(win32con.SW_SHOW)
		self.UpdateWindow()

	def close(self):
		# Close the dialog.
		self.DestroyWindow()

	def setstate(self, ugroup, title, ustate, override, uid):
		# Set the values in the dialog.
		# Arguments (no defaults):
		# ugroup -- string name of the user group
		# title -- string title of the user group
		# ustate -- string 'RENDERED' or 'NOT RENDERED'
		# override -- string 'visible' or 'hidden'
		# uid -- string URI
		self['Name'].settext(ugroup)
		self['Title'].settext(title)
		self['UID'].settext(uid)
		if ustate == 'RENDERED':
			upos = 1
		else:
			upos = 0
		self['State'].setpos(upos)
		if override == 'visible':
			opos = 1
		else:
			opos = 0
		self['Override'].setpos(opos)

	def getstate(self):
		# Return the current values in the dialog.
		return self['Name'].gettext(), \
		       self['Title'].gettext(), \
		       self['State'].getvalue(), \
		       self['Override'].getvalue(), \
		       self['UID'].gettext()
