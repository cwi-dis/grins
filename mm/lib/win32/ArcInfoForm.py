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

# Base dialog bar class
class DlgBar(window.Wnd,components.ControlsDict):
	AFX_IDW_DIALOGBAR=0xE805
	# Class constructor. Calls base constructors
	def __init__(self):
		AFX_IDW_DIALOGBAR=0xE805
		window.Wnd.__init__(self,win32ui.CreateDialogBar())
		components.ControlsDict.__init__(self)
	# Creates the OS window
	def create(self,frame,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		self._obj_.CreateWindow(frame,resid,
			align,self.AFX_IDW_DIALOGBAR)

# Implementation of the ArcInfoDialog needed by the core system.
# It is implemented as a dialog bar
class ArcInfoForm(DlgBar):
	# Class constructor. Calls base class constructor and associates controls to ids
	def __init__(self):
		DlgBar.__init__(self)
		self['Title']=components.Static(self,grinsRC.IDC_STATIC1)	
		self['From']=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self['To']=components.ComboBox(self,grinsRC.IDC_COMBO2)
		self['Delay']=components.Edit(self,grinsRC.IDC_EDIT1)
		self['Cancel']=components.Button(self,grinsRC.IDC_CANCEL)
		self['Restore']=components.Button(self,grinsRC.IDUC_RESTORE)
		self['Apply']=components.Button(self,grinsRC.IDUC_APPLY)
		self['OK']=components.Button(self,grinsRC.IDC_OK)

	# Create the OS window and hooks commands
	def create(self,frame):
		DlgBar.create(self,frame,grinsRC.IDD_ARC_INFO_BAR,afxres.CBRS_ALIGN_TOP)
		for i in self.keys():
			frame.HookCommand(self.onCmd,self[i]._id)
			self[i].attach_to_parent()
		self.setparams()
		frame.RecalcLayout()

	# Response to commands
	def onCmd(self,id,code):
		for i in self.keys():
			if id==self[i]._id:
				self[i].callcb()

	#########################################################
	# cmif specific interface
	# Called by the core to close this window
	def close(self):
		frame=self.GetParent()
		self.DestroyWindow()
		frame.RecalcLayout()

	# Called by the core to show this window
	def show(self):
		self.pop() # for now

	# Called by the core to bring to front this window
	def pop(self):
		frame=self.GetParent()
		frame.MDIActivate()

	# Called by the core to hide this window
	def hide(self):
		self.close()

	# Sets the parameters from the core system 
	def do_init(self, title, srclist, srcinit, dstlist, dstinit, delay, adornments=None):
		self._title=title
		self._srclist=srclist
		self._srcinit=srcinit
		self._dstlist=dstlist
		self._dstinit=dstinit
		self._delay=delay
		self._adornments=adornments

		cbdict=adornments['callbacks']
		for k in self.keys():
			if k in cbdict.keys():
				self[k].setcb(cbdict[k])

	# initialize controls
	def setparams(self,params=None):
		self['Title'].settext(self._title)
		self['From'].initoptions(self._srclist,self._srcinit)
		self['To'].initoptions(self._dstlist,self._dstinit)
		self['Delay'].settext('%d' % self._delay)
	
	# Set title control text			
	def settitle(self, title):
		self['Title'].settext(self._title)

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
		return float(self['Delay'].gettext())
