__version__ = "$Id$"

import win32ui,win32con

import win32mu
import components

# mfc docview stuff
from pywin.mfc import window,object,docview

class GenFormView(docview.FormView,components.ControlsDict):
	# Class constructor. Initializes base class and associates controls to ids
	def __init__(self,doc,idd,freezesize=1):
		docview.FormView.__init__(self,doc,idd)
		components.ControlsDict.__init__(self)
		self._idd=idd
		self._closecmdid=-1
		self._freezesize=freezesize

	# Creates the actual OS window
	def create(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
	def createWindow(self,parent):
		self.create(parent)

	def EnableCmd(self,strcmd,f):
		p=self._parent
		if f:
			self[strcmd].enable(1)
			p.HookCommandUpdate(p.OnUpdateCmdEnable,self[strcmd]._id)
		else:
			p.HookCommandUpdate(p.OnUpdateCmdDissable,self[strcmd]._id)
			self[strcmd].enable(0)
			
	# Called after the OS window has been created to initialize the view
	def OnInitialUpdate(self):
		frame=self.GetParent()
		if self._freezesize:
			self.fittemplate()
			frame.RecalcLayout()
		for ck in self.keys():
			self[ck].attach_to_parent()
			self.EnableCmd(ck,0)
		self.HookMessage(self.OnCmd,win32con.WM_COMMAND)

	# Called by the framework when this view is activated
	def onActivate(self,f):
		return

	# Called by the frame work before closing this View
	def OnClose(self):
		if self._closecmdid>0:
			self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND,self._closecmdid)
		else:
			self.GetParent().DestroyWindow()

	# Returns true if the OS window exists
	def is_oswindow(self):
		return (hasattr(self,'GetSafeHwnd') and self.GetSafeHwnd())


	# Return the user cmd from the command class
	def GetUserCmdId(self,cmdcl):
		if hasattr(self,'GetParent'):
			return self.GetParent().GetUserCmdId(cmdcl)
		return -1

	# Adjust dimensions to fit resource template
	def fittemplate(self):
		frame=self.GetParent()
		rc=win32mu.DlgTemplate(self._idd).getRect()
		if not rc: return
		from sysmetrics import cycaption,cyborder,cxborder,cxframe
		h=rc.height() + cycaption + 2*cyborder + 16
		w=rc.width() + 2*cxborder + 16
		flags=win32con.SWP_NOZORDER|win32con.SWP_NOACTIVATE|win32con.SWP_NOMOVE
		frame.SetWindowPos(0, (0,0,w,h),flags)
	
	# Helper function that given the string id of the control calls the callback
	def call(self,strcmd):
		if self._cbdict.has_key(strcmd):
			apply(apply,self._cbdict[strcmd])

	# Reponse to message WM_COMMAND
	def OnCmd(self,params):
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		for k in self.keys():
			if self[k]._id==id:
				if k in self._cbdict.keys():
					apply(apply,self._cbdict[k])
				return	

	# Called directly from cmif-core to close window
	def close(self):
		# 1. clean self contents

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()

	# Return 1 if self is an os window
	def is_showing(self):
		if not hasattr(self,'GetSafeHwnd'):
			return 0
		return self.GetSafeHwnd()and self.IsWindowVisible()

	# Called by the core system to show this view
	def show(self):
		if hasattr(self,'GetSafeHwnd'):
			if self.GetSafeHwnd():
				self.GetParent().ShowWindow(win32con.SW_SHOW)
				self.GetParent().getMDIFrame().MDIActivate(self.GetParent())

	# Called by the core system to hide this view
	def hide(self):
		self.close()

	# Bring window in front of peers
	def pop(self):
		if not hasattr(self,'GetParent'):return
		childframe=self.GetParent()
		childframe.ShowWindow(win32con.SW_SHOW)
		frame=childframe.GetMDIFrame()
		frame.MDIActivate(childframe)
