__version__ = "$Id$"

""" @win32doc|_SourceView
This module contains the ui implementation of the source
viewer. It is an MFC EditView with the read only attribute set.
It is exposed to Python through the win32ui pyd as PyCEditView
"""

import win32ui,win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()
import win32mu

import usercmd

from pywinlib.mfc import window,object,docview
import windowinterface
import afxres,commctrl
import GenFormView

class _SourceView(GenFormView.GenFormView):
	def __init__(self, doc, bgcolor = None):
		self._textEditor = _SourceViewTextEditor(doc, bgcolor)
		self.set_readonly = self._textEditor.set_readonly
		self.OnInitialUpdate = self._textEditor.OnInitialUpdate
		self.gettext = self._textEditor.gettext
		self.select_chars = self._textEditor.select_chars
		self.is_changed = self._textEditor.is_changed
		self.set_mother = self._textEditor.set_mother
		self.is_closed = self._textEditor.is_closed
		self._obj_ = None

	def create(self, parent):
		print "_SourceView.create called."
		GenFormView.GenFormView.create(parent)
		self._textEditor.CreateWindow(self)

	def createWindow(self, parent):
		print "_SourceView.createWindow called."

	# Called by the framework to close this window.
	def OnClose(self):
		if self.mother:
			self.mother.close_callback()

	def settext(self, text):
		self._textEditor.settext(text)


class _SourceViewTextEditor(docview.RichEditView):
	# Class contructor. Calls the base RichEditView constructor
	def __init__(self,doc,bgcolor=None):
		docview.RichEditView.__init__(self,doc)
		self._text=''
		self._close_cmd_list=[]
		self.mother = None
		self.readonly = 0
		self.__editctrl = self.GetRichEditCtrl()

	def setclosecmd(self, cmdid):
		self._closecmdid = cmdid

	# Create the OS window
	def createWindow(self,parent):
		self.CreateWindow(parent)

	def set_readonly(self, readonly):
		self.readonly = readonly
		self.SetReadOnly(readonly)
	
	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		edit=self.__editctrl	# Is it just me, or does this only return self?
		edit.SetWindowText(self._text)
		if self.readonly:
			edit.SetReadOnly(1)

	# Called when the view is activated 
	def activate(self):
		pass

	# Called when the view is deactivated 
	def deactivate(self):
		pass

	# cmif interface
	# Set the text to be shown
	def settext(self,text):
		f = win32ui.CreateFont({"name":"courier new", "width":12, "height":12,})
		self.__editctrl.SetFont(f)
		self.__editctrl.SetWordWrap(0) # helps if you are psycic.
		self._text=self.convert2ws(text)
		# if already visible, update text in window
		self.__editctrl.SetWindowText(self._text)
		self.__editctrl.SetModify(0) # No, this document has not been modified yet.

	def gettext(self):
		return self.__editctrl.GetWindowText()

	def select_chars(self, startchar, endchar):
		# the text between startchar and endchar will be selected.
		e = self.__editctrl
		e.SetSel(startchar,endchar) # Automatically scrolls.
		e.LineScroll(min(e.LineFromChar(startchar) - e.GetFirstVisibleLine(), 0), -1000)

	def is_changed(self):
		# Return true or false depending on whether the source view has been changed.
		modified = self.__editctrl.GetModify()
		return modified
	
	def set_mother(self, mother):
		self.mother = mother

	# Convert the text from unix or mac to windows
	def convert2ws(self,text):
		return text
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
		print "DEBUG: _SourceView.close() called."
		# 1. clean self contends
		del self._text
		self._text=None
		self.mother = None

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()

	# Returns true if this view is already closed
	def is_closed(self):
		if self._obj_==None: return 1
		if self.GetSafeHwnd()==0: return 1
		return (not self.IsWindowVisible())
