import win32ui,win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()
import win32mu,wc

import components
import usercmd

from pywin.mfc import window,object,docview
import afxres,commctrl

class _SourceView(docview.EditView):
	def __init__(self,doc):
		docview.EditView.__init__(self,doc)
		self._text=''
		self._close_cmd_list=[]

	def createWindow(self,parent):
		self.CreateWindow(parent)

	def OnInitialUpdate(self):
		edit=self.GetEditCtrl()
		edit.SetWindowText(self._text)
		edit.SetReadOnly(1)
		self._mdiframe=(self.GetParent()).GetMDIFrame()
#		self._close_cmd_list=[
#			usercmd.CLOSE_WINDOW(callback = (self.close, ())),]

	def onActivate(self,f):
		return
		import appcon
		if appcon.IsEditor:
			if f: self._mdiframe.set_commandlist(self._close_cmd_list)
			else: self._mdiframe.set_commandlist(None,'view')

	def set_close_commandlist(self):
		self._mdiframe.set_commandlist(self._close_cmd_list,'view')

	# cmif interface
	def settext(self,text):
		self._text=text

	def close(self):
		# 1. clean self contends
		del self._text
		self._text=None
		self.onActivate(0)

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()

	def is_closed(self):
		if self._obj_==None: return 1
		if self.GetSafeHwnd()==0: return 1
		return self.IsWindowVisible()
