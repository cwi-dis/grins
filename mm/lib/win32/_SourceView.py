__version__ = "$Id$"

""" @win32doc|_SourceView
This module contains the ui implementation of the source
viewer. It is an MFC EditView with the read only attribute set.
It is exposed to Python through the win32ui pyd as PyCEditView
"""

import win32ui,win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()
import win32mu,wc

import components
import usercmd

from pywin.mfc import window,object,docview
import afxres,commctrl

class _SourceView(docview.EditView):
	# Class contructor. Calls the base EditView constructor
	def __init__(self,doc):
		self._mdiframe = None
		docview.EditView.__init__(self,doc)
		self._text=''
		self._close_cmd_list=[]

	# Create the OS window
	def createWindow(self,parent):
		self.CreateWindow(parent)
	
	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		edit=self.GetEditCtrl()
		edit.SetWindowText(self._text)
		edit.SetReadOnly(1)
		self._mdiframe=(self.GetParent()).GetMDIFrame()

	# Called by the framework before this window is closed
	def OnClose(self):
		if self._closecmdid>0:
			self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND,self._closecmdid)
		else:
			self.GetParent().DestroyWindow()

	# Called by the framework when this view is activated or deactivated
	def onActivate(self,f):
		pass
		#if f: self._mdiframe.set_commandlist(self._close_cmd_list)
		#else: self._mdiframe.set_commandlist(None,self._strid)


	# cmif interface
	# Set the text to be shown
	def settext(self,text):
		self._text=self.convert2ws(text)
		# if already visible, update text in window
		if self._mdiframe is not None:
			self.GetEditCtrl().SetWindowText(self._text)

	# Convert the text from unix or mac to windows
	def convert2ws(self,text):
		import string
		nl=string.split(text,'\n')
		rl=string.split(text,'\r')
		if len(nl)==len(rl):# line_separator='\r\n'
			return text
		if len(nl)>len(rl):	# line_separator='\n'
			return string.join(nl, '\r\n')
		if len(nl)<len(rl):	# line_separator='\r'
			return string.join(rl, '\r\n')
	
	# Called by the framework to close the view		
	def close(self):
		# 1. clean self contends
		del self._text
		self._text=None
		self.onActivate(0)

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()

	# Returns true if this view is already closed
	def is_closed(self):
		if self._obj_==None: return 1
		if self.GetSafeHwnd()==0: return 1
		return (not self.IsWindowVisible())
