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

import grinsRC, components
from GenFormView import GenFormView

class _SourceView(GenFormView):
	# Class contructor. Calls the base RichEditView constructor
	def __init__(self,doc,bgcolor=None):
		self.__showing = 0
		GenFormView.__init__(self, doc, grinsRC.IDD_SOURCEEDIT)
		self['edit'] = self.__editctrl = components.Edit(self, grinsRC.IDC_EDIT1)
		self['ok'] = self.__ok = components.Button(self,grinsRC.IDC_BUTTON1)
		self['apply'] = self.__apply = components.Button(self,grinsRC.IDC_BUTTON2)
		self['revert'] = self.__revert = components.Button(self,grinsRC.IDC_BUTTON3)
		self.__text=''
		self.__mother = None
		self.__readonly = 0
		self.__map0 = []
		self.__map1 = []
		# call back dictionary, used ne GenFormView
		self._cbdict = {'ok': (self.__ok_callback, ()),
				'apply': (self.__apply_callback, ()),
				'revert': (self.__revert_callback, ()),
##				'edit': (self.__edit_callback, ()),
				}

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		self.__showing = 1
		self.__editctrl.settext(self.__text)
		self.__editctrl.enable(not self.__readonly)
		self.__ok.enable(1)
		self.__apply.enable(0)
		self.__revert.enable(0)

	def OnCmd(self, params):
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		if id == self.__editctrl._id:
			nmsg=msg.getnmsg()
			if nmsg == win32con.EN_CHANGE:
				self.__apply.enable(1)
				self.__revert.enable(1)
		elif id == self.__ok._id:
			self.__ok_callback()
		elif id == self.__apply._id:
			self.__apply_callback()
		elif id == self.__revert._id:
			self.__revert_callback()

	def __ok_callback(self):
		if self.__mother:
			self.__mother.close_callback()

	def __apply_callback(self):
		if self.__mother:
			self.__mother.apply_callback()

	def __revert_callback(self):
		self.__editctrl.settext(self.__text)
		self.__apply.enable(0)
		self.__revert.enable(0)

	def setclosecmd(self, cmdid):
		self._closecmdid = cmdid

	def set_readonly(self, readonly):
		self.__readonly = readonly
		if self.__showing:
			self.__editctrl.enable(not readonly)

	# Called by the framework to close this window.
	def OnClose(self):
		if self.__mother:
			self.__mother.close_callback()
		else:
			print "ERROR: You need to call _SourceView.setmother(self)"

	# cmif interface
	# Set the text to be shown
	def settext(self,text):
		f = win32ui.CreateFont({"name":"courier new", "width":12, "height":12,})
##		self.__editctrl.SetFont(f)
##		self.__editctrl.SetWordWrap(0) # helps if you are psycic.
		self.__text=self.__convert2ws(text)
		# if already visible, update text in window
		if self.__showing:
			self.__editctrl.settext(self.__text)
##			self.__editctrl.setmodify(0) # No, this document has not been modified yet.

	def gettext(self):
		return self.__editctrl.gettext()

	def select_chars(self, startchar, endchar):
		# the text between startchar and endchar will be selected.
		e = self.__editctrl
		for p0, p1 in self.__map0:
			if p0 <= startchar:
				startchar = p1 + (startchar - p0)
				break
		for p0, p1 in self.__map0:
			if p0 <= endchar:
				endchar = p1 + (endchar - p0)
				break
		startline = len(self.__map1)
		for p0, p1 in self.__map1:
			if p0 <= startchar:
				startchar = p1 + (startchar - p0)
				break
			startline = startline - 1
		endline = len(self.__map1)
		for p0, p1 in self.__map1:
			if p0 <= endchar:
				endchar = p1 + (endchar - p0)
				break
			endline = endline - 1
		e.setsel(startchar,endchar)
		# magic number 23: number of lines in edit control
		if endline > e.getfirstvisibleline() + 23:
			# last line not visible, scroll down
			e.linescroll(endline - e.getfirstvisibleline() - 23)
		if startline < e.getfirstvisibleline():
			# first line not visible, scroll up
			e.linescroll(startline - e.getfirstvisibleline())

	def is_changed(self):
		# Return true or false depending on whether the source view has been changed.
		return self.__editctrl.getmodify()
	
	def set_mother(self, mother):
		self.__mother = mother

	# Convert the text from unix or mac to windows
	def __convert2ws(self,text):
		import string
		# together the following three mappings normalize
		# end-of-line sequences in any combination of the
		# three standards to the Windows standard

		# first map \r\n to \n (Windows to Unix)
		# must do this first since we don't want to convert
		# \r\n to \n\n in the next convertion
		rn = string.split(text, '\r\n')
		text = string.join(rn, '\n')
		# then map left over \r to \n (Mac to Unix)
		r = string.split(text, '\r')
		text = string.join(r, '\n')
		# finally map \n to \r\n (Unix to Windows)
		n = string.split(text, '\n')
		text = string.join(n, '\r\n')

		# calculate mappings of char positions
		pos0 = pos1 = 0
		for line in rn:
			self.__map0.append((pos0, pos1))
			pos0 = pos0 + len(line) + 2
			pos1 = pos1 + len(line) + 1
		self.__map0.reverse()
		pos0 = pos1 = 0
		for line in n:
			self.__map1.append((pos0, pos1))
			pos0 = pos0 + len(line) + 1
			pos1 = pos1 + len(line) + 2
		self.__map1.reverse()
		return text
	
	# Called by the framework to close the view		
	def close(self):
		# 1. clean self contents
		self.__text=None
		self.__mother = None

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()
