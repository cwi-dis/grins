__version__ = "$Id$"


""" @win32doc|ArcInfoForm
This module contains the ui implementation of the ArcInfoDialog.
It is implemented as a dialog bar.

The MFC class that offers the dialog bar functionality is the CDialogBar
Objects of this class are exported to Python through the win32ui pyd
as objects of type PyCDialogBar. The ArcInfoForm extends the PyCDialogBar.

The ArcInfoForm is created using the resource dialog template 
with identifier IDD_ARC_INFO_BAR.
Like all resources it can be found in cmif\win32\src\GRiNSRes\GRiNSRes.rc.

"""

# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

from GenFormView import GenFormView

class ArcInfoForm(GenFormView):
	# Class constructor. Calls base class constructor and initializes members
	def __init__(self,doc):
		GenFormView.__init__(self,doc,grinsRC.IDD_ARC_INFO_FORM)	
		self['From']=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self['To']=components.ComboBox(self,grinsRC.IDC_COMBO2)
		self['Delay']=components.Edit(self,grinsRC.IDC_EDIT1)
		self['Cancel']=components.Button(self,win32con.IDCANCEL)
		self['Restore']=components.Button(self,grinsRC.IDUC_RESTORE)
		self['Apply']=components.Button(self,grinsRC.IDUC_APPLY)
		self['OK']=components.Button(self,win32con.IDOK)

	# Part of init: sets the parameters from the core system 
	def do_init(self, title, srclist, srcinit, dstlist, dstinit, delay, adornments=None):
		self._title=title
		self._srclist=srclist
		self._srcinit=srcinit
		self._dstlist=dstlist
		self._dstinit=dstinit
		self._delay=delay
		cbd=adornments['callbacks']
		self._idcbdict={}
		for k in self.keys():
			if k in cbd.keys():
				self._idcbdict[self[k]._id]=cbd[k]

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		self.setparams()
		for k in self.keys():
			self.EnableCmd(k,1)

	# set values to controls
	def setparams(self,params=None):
		self.settitle(self._title)
		self['From'].initoptions(self._srclist,self._srcinit)
		self['To'].initoptions(self._dstlist,self._dstinit)
		self['Delay'].settext('%d' % self._delay)

	# Reponse to message WM_COMMAND
	def OnCmd(self,params):
		# crack message
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		if id in self._idcbdict.keys():
			apply(apply,self._idcbdict[id])
	
	# Called by the core to set the title of this view
	def settitle(self,title):
		self._title=title
		if hasattr(self,'GetParent'):
			if self.GetParent().GetSafeHwnd():
				self.GetParent().SetWindowText(title)

	# Interface to the source list.
	# Set 'from' position
	def src_setpos(self, pos):
		self['From'].setcursel(pos)

	# Get 'from' position
	def src_getpos(self):
		return self['From'].getcursel()

	# Interface to the destination list.
	# Set 'to' position
	def dst_setpos(self, pos):
		self['To'].setcursel(pos)

	# Get 'to' position
	def dst_getpos(self):
		return self['To'].getcursel()

	# Interface to the delay value.
	# Set delay value
	def delay_setvalue(self, delay):
		self['Delay'].settext('%d' % delay)

	# Get delay value
	def delay_getvalue(self):
		try:
			rv = float(self['Delay'].gettext())
		except ValueError:
			win32ui.MessageBox("Illegal delay, 0.0 used")
			rv = 0.0
		return rv
