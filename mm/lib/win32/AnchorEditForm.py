__version__ = "$Id$"

""" @win32doc|AnchorEditForm
This module contains the ui implementation of the Anchor Editor
It is implemented as a FormView.
"""

# std win32 modules
import win32ui,win32con,win32api

# win32 python lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC


from GenFormView import GenFormView

# Implementation of the AnchorEditDialog needed by the core system. It is based on the framework class ListView				
class AnchorEditForm(GenFormView):
	# Class constructor. Calls base class constructor and initializes members
	def __init__(self,doc):
		GenFormView.__init__(self,doc,grinsRC.IDD_EDIT_ANCHORS)	
		self._title='Anchor Editor'

		self['Anchor']=components.ListBox(self,grinsRC.IDC_LIST1)

		self['New']=components.Button(self,grinsRC.IDUC_NEW)
		self['Edit']=components.Button(self,grinsRC.IDUC_EDIT)
		self['Delete']=components.Button(self,grinsRC.IDUC_DELETE)
		self['Export']=components.Button(self,grinsRC.IDUC_EXPORT)

		self['Cancel']=components.Button(self,win32con.IDCANCEL)
		self['Restore']=components.Button(self,grinsRC.IDUC_RESTORE)
		self['Apply']=components.Button(self,grinsRC.IDUC_APPLY)
		self['OK']=components.Button(self,win32con.IDOK)

		self['EditId']=components.Edit(self,grinsRC.IDC_EDIT1)
		self['Type']=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self['Composite']=components.Static(self,grinsRC.IDC_STATIC1)

		self._itemlist=[]
		self._selecteditem=None
		self._itemlist
		self._cbdict={}
		self._typelabels=None
		self._choice_sens={}

		self._cursel=None

		# FLAGS NEEDED TO MANAGE THE PECULIARITIES OF THE CORE INTERFACE DESIGN
		self._enableEdCb=1 # flags to control editor notifications
		self._enableLiCb=1
		self._callEditId=0
				
	# part of the constructor initialization	
	def do_init(self, title, typelabels, list, initial, adornments):
		self._title=title
		self._itemlist=list
		self._itemlist_initial=initial
		self._typelabels=typelabels
		self._cbdict=adornments['callbacks']


	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		self.GetParent().freezeSize()
		self.EnableCmd('New',1)
		self.EnableCmd('Anchor',1)

		self.EnableCmd('Restore',1)
		self.EnableCmd('Apply',1)
		self.EnableCmd('OK',1)
		self.EnableCmd('Cancel',1)

		if self._typelabels:
			self['Type'].initoptions(self._typelabels,-1)
		if self._itemlist:
			self.selection_setlist(self._itemlist,self._itemlist_initial)

	# Reponse to message WM_COMMAND
	def OnCmd(self,params):
		# crack message
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		
		# delegate list notifications
		if id==self['Anchor']._id:
			self.OnListCmd(id,nmsg)
			return

		if id==self['EditId']._id:
			self.OnEdit(id,nmsg)
			return

		if id==self['Type']._id:
			self.OnChangeOption(id,nmsg)
			return

		if id==self['OK']._id:
			if self._callEditId:self.call('EditId')
					
		# process rest
		for i in self.keys():
			if id==self[i]._id:
				self.call(i)

	# Response to a selection change of the listbox 
	def OnListCmd(self,id,code):
		if code==win32con.LBN_SELCHANGE and self._enableLiCb:
			self._cursel=self['Anchor'].getcursel()
			self.ItemToEditor()
			self.call('Anchor')

	# Response to a change in the text of the edit box	
	def OnEdit(self,id,code):
		if code==win32con.EN_CHANGE:
			if self._enableEdCb and self._cursel!=None:
				text=self['EditId'].gettext()
				if text:
					self._callEditId=1
					self._enableLiCb=0
					self['Anchor'].replace(self._cursel,text)
					self._enableLiCb=1
		if code==win32con.EN_KILLFOCUS:
			self._callEditId=0
			self.call('EditId')

	# Response to combo box change
	def OnChangeOption(self,id,code):
		if not hasattr(self,'_prevsel'):self._prevsel=0
		if code==win32con.CBN_DROPDOWN:
			self._prevsel=self['Type'].getcursel()
		if code==win32con.CBN_SELCHANGE:
			strsel=self['Type'].getvalue()
			if strsel[0]!='[' and strsel!='---':
				self.call('Type')
			else:self['Type'].setcursel(self._prevsel)

	# Helper function that calls a callback given a string id
	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])				

	# Transfer date from the list to the edit area
	def ItemToEditor(self):
		text=self['Anchor'].gettext(self._cursel)
		self._enableEdCb=0
		self['EditId'].settext(text)
		self._enableEdCb=1

	# cmif general interface
	# Called by the core to close this window
	def close(self):
		if hasattr(self,'GetParent'):
			self.GetParent().ShowWindow(win32con.SW_HIDE)
			self.GetParent().DestroyWindow()

	# Called by the core to set the title of this view
	def settitle(self,title):
		self._title=title
		if hasattr(self,'GetParent'):
			if self.GetParent().GetSafeHwnd():
				self.GetParent().SetWindowText(title)

	# Called by the core to show this view
	def show(self):
		self.pop() # for now

	# Called by the core to bring this window  to the front
	def pop(self):
		childframe=self.GetParent()
		childframe.ShowWindow(win32con.SW_SHOW)
		frame=childframe.GetMDIFrame()
		frame.MDIActivate(childframe)

	# Called by the core to hide this view
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)

	# Response to parent request to close
	# the parent frame delegates the responcibility to us
	# we must decide what to do (OK,Cancel,..)
	# interpret it as a Cancel for now (we should ask, save or not)
	def OnClose(self):
		self.call('Cancel')

							

	#########################################################
	# cmif specific interface

	# Interface to the composite part of the window.  This part
	# consists of just a single label (piece of text) which can be
	# hidden or shown.  The text in the label can be changed at
	# run time and is initially just `Composite:'.
	def composite_hide(self):
		"""Hide the composite part of the dialog."""
		self['Composite'].hide()

	def composite_show(self):
		"""Show the composite part of the dialog."""
		self['Composite'].show()

	def composite_setlabel(self, label):
		"""Set the composite label.

		Arguments (no defaults):
		label -- string to display
		"""
		self['Composite'].settext(label)

	# Interface to the type_choice part of the dialog.  This is a
	# part of the dialog that indicates to the user which of a
	# list of strings is currently selected, and it gives the user
	# the possibility to choose another item.  In Motif this is
	# implemented as a so-called OptionMenu.  It should be
	# possible to hide or deactivate this part of the window.
	def type_choice_hide(self):
		"""Hide the type choice part of the dialog."""
		#self['Type'].hide()
		self.EnableCmd('Type',0)

	def type_choice_show(self):
		"""Show the type choice part of the dialog."""
		#self['Type'].show()
		self.EnableCmd('Type',1)

	def type_choice_setchoice(self, choice):
		"""Set the current choice.

		Arguments (no defaults):
		choice -- index in the list of choices that is to be
			the current choice
		"""
		self['Type'].setcursel(choice)

	def type_choice_getchoice(self):
		"""Return the current choice (the index into the list)."""
		return self['Type'].getcursel()

	def type_choice_setsensitive(self, pos, sensitive):
		"""Make a choice sensitive or insensitive.

		Arguments (no defaults):
		pos -- index of the choice to be made (in)sensitive
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['Type'].setsensitive(pos, sensitive)


	# Interface to the selection area.  The selection area
	# consists of a list of strings with the possibility to select
	# one of these strings, and to edit the value of the selected
	# string.  In some cases, the string should not be editable
	# (see below).  If a string is selected a callback should be
	# called; if the string is edited, another callback should be
	# called.
	def selection_seteditable(self, editable):
		"""Make the selected string editable or not."""
		self.EnableCmd('EditId',editable)

	def selection_setlist(self, list, initial):
		"""Set the list of strings.

		Arguments (no defaults):
		list -- list of strings
		initial -- 0 <= initial < len(list) or None -- this is
			the index of the element in list which should
			be the selected item (no element is selected
			if None)
		"""
		self['Anchor'].resetcontent()
		self['Anchor'].addlistitems(list,0)
		self.selection_setselection(initial)

	def selection_setselection(self, pos):
		"""Set the selection to the item indicated.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) or None -- the index of
			the item to be selected
		"""
		self['Anchor'].setcursel(pos)
		self._cursel=pos
		self.ItemToEditor() # window is not notified for selection change if we append item

	def selection_getselection(self):
		"""Return the index of the currently selected item.

		The return value is the index of the currently
		selected item, or None if no item is selected.
		"""
		return self._cursel


	def selection_append(self, item):
		"""Append an item to the end of the list.

		Which item is selected after the element is added is
		undefined.  The list which was given to
		selection_setlist or __init__ (whichever was last) is
		modified.
		"""
		self['Anchor'].addlistitem(item,-1)
		
	def selection_gettext(self):
		"""Return the string value of the currently selected item.

		When no item is selected, the behavior is undefined.
		[ This method is called in the id_callback to get the
		new value of the currently selected item. ]
		"""
		return self['Anchor'].gettext(self._cursel)

	def selection_replaceitem(self, pos, item):
		"""Replace the indicated item with a new value.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be changed
		item -- string to replace the item with
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		self['Anchor'].replace(pos,item)

	def selection_deleteitem(self, pos):
		"""Delete the indicated item from the list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be deleted
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		self['Anchor'].deletestring(pos)

	# Interface to the various button.
	def edit_setsensitive(self, sensitive):
		"""Make the `Edit' button (in)sensitive."""
		self.EnableCmd('Edit',sensitive)

	def delete_setsensitive(self, sensitive):
		"""Make the `Delete' button (in)sensitive."""
		self.EnableCmd('Delete',sensitive)

	def export_setsensitive(self, sensitive):
		"""Make the `Export...' button (in)sensitive."""
		self.EnableCmd('Export',sensitive)


