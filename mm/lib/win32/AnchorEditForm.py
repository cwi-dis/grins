__version__ = "$Id$"

""" @win32doc|AnchorEditForm
This module contains the ui implementation of the Anchor Editor
It is implemented as a ListView with dialog bars.
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

# Base class for dialog bars
class DlgBar(window.Wnd):
	# Class constructor. Calls the base constructors and creates the OS window
	def __init__(self,parent,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		AFX_IDW_DIALOGBAR=0xE805
		wndDlgBar = win32ui.CreateDialogBar()
		window.Wnd.__init__(self,wndDlgBar)
		wndDlgBar.CreateWindow(parent,resid,
			align,AFX_IDW_DIALOGBAR)

# A dialog bar to Edit Anchors
class EditAnchorDlgBar(DlgBar):
	# Class constructor. Calls base class constructor and associates controls to ids
	def __init__(self,parent,id_cb,opt_cb):
		DlgBar.__init__(self,parent,grinsRC.IDD_EDIT_ANCHOR_BAR,afxres.CBRS_ALIGN_BOTTOM)
		self._id_cb=id_cb;self._opt_cb=opt_cb

		self._idedit=components.Edit(self,grinsRC.IDC_EDIT1)
		self._idedit.attach_to_parent()
		parent.HookCommand(self.OnEdit,grinsRC.IDC_EDIT1)

		self._options=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self._options.attach_to_parent()
		parent.HookCommand(self.OnChangeOption,grinsRC.IDC_COMBO1)

		self._composite=components.Static(self,grinsRC.IDC_STATIC1)
		self._composite.attach_to_parent()
		self._idedit_cb=1
		self._prevsel=0
		self._parent=parent

	# Response to a chenge in the text of the edit box	
	def OnEdit(self,id,code):
		if not self._idedit_cb:return
		if code==win32con.EN_CHANGE and self._id_cb:
			apply(self._id_cb,(self._idedit.gettext(),))

	# Response to combo box change
	def OnChangeOption(self,id,code):
		if code==win32con.CBN_DROPDOWN:
			self._prevsel=self._options.getcursel()
		if code==win32con.CBN_SELCHANGE and self._opt_cb:
			strsel=self._options.getvalue()
			if strsel[0]!='[' and strsel!='---':
				apply(self._opt_cb,(strsel,))
			else:self._options.setcursel(self._prevsel)

	def setid(self,id):
		self._idedit_cb=None
		self._idedit.settext(id)
		self._idedit_cb=1

	def enableEdit(self,flag):
		id=self._idedit._id
		frame=self._parent
		if flag:
			frame.HookCommandUpdate(frame.OnUpdateCmdEnable,id)
		else:
			frame.HookCommandUpdate(frame.OnUpdateCmdDissable,id)
			
# A dialog bar containing the buttons New,Edit,Delete,Export.
class AnchorDlgBar(DlgBar):
	# Class constructor. Call base class constructor and associates controls to ids
	def __init__(self, parent,cbdict):
		DlgBar.__init__(self,parent,grinsRC.IDD_ANCHOR_BAR,afxres.CBRS_ALIGN_RIGHT)
		self._cbdict=cbdict
		self._buttons=b={
			'New':components.Button(self,grinsRC.IDUC_NEW),
			'Edit':components.Button(self,grinsRC.IDUC_EDIT),
			'Delete':components.Button(self,grinsRC.IDUC_DELETE),
			'Export':components.Button(self,grinsRC.IDUC_EXPORT),
			}
		for strid in self._buttons.keys():
			parent.HookCommand(self.onCmd,b[strid]._id)
			b[strid].attach_to_parent()
			parent.HookCommandUpdate(parent.OnUpdateCmdEnable,b[strid]._id)
		
	# helper function that given a string id calls the command
	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])	
	# Response to controls notification		
	def onCmd(self,id,code):
		for i in self._buttons.keys():
			if id==self._buttons[i]._id:
				self.call(i)

	# Enables/disables the control with string id.
	def enable(self,strid,f):
		if strid in self._buttons.keys():
			parent=self.GetParent()
			id=self._buttons[strid]._id
			if f: parent.HookCommandUpdate(parent.OnUpdateCmdEnable,id)
			else:parent.HookCommandUpdate(parent.OnUpdateCmdDissable,id)


# A dialog bar containing the buttons Restore,Apply,Cancel,OK.
class StdDlgBar(DlgBar):
	# Class constructor. Calls base class constructor and associates controls with ids
	def __init__(self, parent,cbdict):
		DlgBar.__init__(self,parent,grinsRC.IDD_STDDLGBAR,afxres.CBRS_ALIGN_TOP)
		parent.HookCommand(self.OnRestore,grinsRC.IDUC_RESTORE)
		parent.HookCommand(self.OnApply,grinsRC.IDUC_APPLY)
		parent.HookCommand(self.OnCancel,win32con.IDCANCEL)
		parent.HookCommand(self.OnOK,win32con.IDOK)
		self._cbdict=cbdict
	# helper function that given a string id of a command calls the callback
	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])
	# Response to button Restore				
	def OnRestore(self,id,code):self.call('Restore')
	# Response to button Apply				
	def OnApply(self,id,code):self.call('Apply')
	# Response to button OK				
	def OnOK(self,id,code):self.call('OK')
	# Response to button Cancel				
	def OnCancel(self,id,code):self.call('Cancel')


# Implementation of the AnchorEditDialog needed by the core system. It is based on the framework class ListView				
class AnchorEditForm(docview.ListView):
	# Class constructor. Calls base class constructor and initializes members
	def __init__(self,doc):
		docview.ListView.__init__(self,doc)
		self._title='Anchor Editor'
		self._itemlist=[]
		self._selecteditem=None
		self._itemlist
		self._cbdict={}
		self._typelabels=None
		self._choice_sens={}

	# part of the constructor initialization	
	def do_init(self, title, typelabels, list, initial, adornments):
		self._title=title
		self._itemlist=list
		self._itemlist_initial=initial
		self._typelabels=typelabels
		self._cbdict=adornments['callbacks']

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		hwnd = self._obj_.GetSafeHwnd()
		style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE);
		win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, 
			(style & ~commctrl.LVS_TYPEMASK) | commctrl.LVS_SINGLESEL | commctrl.LVS_REPORT | commctrl.LVS_SHOWSELALWAYS)
		self.SetExStyle(commctrl.LVS_EX_FULLROWSELECT)
		
		header_list=[("ID",400)]
		self.InsertListHeader(header_list)
		self.SetItemList()

		frame=self.GetParent()
		self._stdDlgBar=StdDlgBar(frame,self._cbdict)
		self._editBar=EditAnchorDlgBar(frame,self.UpdateID,self.UpdateType)
		self._itemBar=AnchorDlgBar(frame,self._cbdict)

		self.fittemplate()
		frame.RecalcLayout()
		
		if self._typelabels:
			self._editBar._options.initoptions(self._typelabels,-1)

		self.GetParent().HookNotify(self.OnNotifyItemChanged,commctrl.LVN_ITEMCHANGED)
		self.SelectItem(self._itemlist_initial)
		return 0

	# Adjust dimensions to fit resource template
	def fittemplate(self):
		frame=self.GetParent()
		rc=win32mu.DlgTemplate(grinsRC.IDD_EDIT_ANCHOR_BAR).getRect()
		if not rc: return
		from sysmetrics import cycaption,cyborder,cxborder,cxframe
		h= 268 #rc.height() + 2*cycaption+ 2*cyborder
		w=rc.width()+2*cxframe+2*cxborder
		flags=win32con.SWP_NOZORDER|win32con.SWP_NOACTIVATE|win32con.SWP_NOMOVE
		frame.SetWindowPos(0, (0,0,w,h),flags)

	# Called by the framework when the ListView selection has changed
	def OnNotifyItemChanged(self,nm, nmrest):
		(hwndFrom, idFrom, code), (itemNotify, sub, newState, oldState, change, point, lparam) = nm, nmrest
		oldSel = (oldState & commctrl.LVIS_SELECTED)<>0
		newSel = (newState & commctrl.LVIS_SELECTED)<>0
		if oldSel != newSel and self._selecteditem!=itemNotify:
			try:
				self._selecteditem = itemNotify
				self.ItemToEditor()
				self.call('Anchor')
			except win32ui.error:
				self._selecteditem = None

	# Response to key presed
	def OnKeyDown(self,params):
		msg=win32mu.Win32Msg(params)
		print params
		# set focus to dlg on Tab and Enter

	# Set the extended style of the list control
	def SetExStyle(self,or_style):
		style=self.GetListCtrl().SendMessage(commctrl.LVM_GETEXTENDEDLISTVIEWSTYLE)
		style = style | or_style
		self.GetListCtrl().SendMessage(commctrl.LVM_SETEXTENDEDLISTVIEWSTYLE,0,style)

	# Returns the index of the selected item
	def GetSelected(self):
		try:
			index = self.GetNextItem(-1, commctrl.LVNI_SELECTED)
		except win32ui.error:
			index=None
		return index

	# Transfer date from the list to the edit area
	def ItemToEditor(self):
		sel=self._selecteditem
		if sel==None:return
		try:
			id = self.GetItemText(sel,0)
		except win32ui.error:
			id=''

		self._editBar.setid(id)
		self.SetFocus()

	# Felper function that calls the callback given a string id
	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])

	# Update the id column of the list		
	def UpdateID(self,str):
		if str:
			self.SetItemText(self._selecteditem, 0, str)
		self.call('EditId')

	# Update the Type column of the list
	def UpdateType(self,str):
		self.call('Type')

	# Inserts a column header to the list control
	def InsertListHeader(self,header_list):
		for ix in range(len(header_list)):
			t=header_list[ix]
			format=(commctrl.LVCFMT_LEFT, t[1], t[0], 0)
			self.InsertColumn(ix, format)

	# Insert the itemlist in the list control
	def SetItemList(self):
		itemlist=self._itemlist
		for i in range(len(itemlist)):
			l = itemlist[i]
			if type(l)==type(''):
				self.InsertItem(i,l)

	# Select a row in the list cntrol			
	def SelectItem(self,nItem=None):
		if nItem==None:nItem=-1
		#args: nItem,nSubItem,nMask,szItem,nImage,nState,nStateMask,lParam
		nSubItem=nImage=lParam=0;szItem=''
		nMask=commctrl.LVIF_STATE
		nState=nStateMask=commctrl.LVIS_SELECTED|commctrl.LVIS_FOCUSED
		self.SetItem(nItem,nSubItem,nMask,szItem,nImage,nState,nStateMask,lParam)

	# Called by the farmework when the view is activated or deactivated
	def onActivate(self,f):
		pass

	# cmif general interface
	# Called by the core to close this window
	def close(self):
		if hasattr(self,'GetParent'):
			self.GetParent().ShowWindow(win32con.SW_HIDE)
			self._stdDlgBar.DestroyWindow()
			self._editBar.DestroyWindow()
			self._itemBar.DestroyWindow()
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

	# Helper function that calls a callback given a string id
	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])				


	#########################################################
	# cmif specific interface

	# Interface to the composite part of the window.  This part
	# consists of just a single label (piece of text) which can be
	# hidden or shown.  The text in the label can be changed at
	# run time and is initially just `Composite:'.
	def composite_hide(self):
		"""Hide the composite part of the dialog."""
		self._editBar._composite.hide()

	def composite_show(self):
		"""Show the composite part of the dialog."""
		self._editBar._composite.show()

	def composite_setlabel(self, label):
		"""Set the composite label.

		Arguments (no defaults):
		label -- string to display
		"""
		self._editBar._composite.settext(label)

	# Interface to the type_choice part of the dialog.  This is a
	# part of the dialog that indicates to the user which of a
	# list of strings is currently selected, and it gives the user
	# the possibility to choose another item.  In Motif this is
	# implemented as a so-called OptionMenu.  It should be
	# possible to hide or deactivate this part of the window.
	def type_choice_hide(self):
		"""Hide the type choice part of the dialog."""
		self._editBar._options.hide()

	def type_choice_show(self):
		"""Show the type choice part of the dialog."""
		self._editBar._options.show()

	def type_choice_setchoice(self, choice):
		"""Set the current choice.

		Arguments (no defaults):
		choice -- index in the list of choices that is to be
			the current choice
		"""
		self._editBar._options.setcursel(choice)

	def type_choice_getchoice(self):
		"""Return the current choice (the index into the list)."""
		return self._editBar._options.getcursel()

	def type_choice_setsensitive(self, pos, sensitive):
		"""Make a choice sensitive or insensitive.

		Arguments (no defaults):
		pos -- index of the choice to be made (in)sensitive
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self._editBar._options.setsensitive(pos, sensitive)


	# Interface to the selection area.  The selection area
	# consists of a list of strings with the possibility to select
	# one of these strings, and to edit the value of the selected
	# string.  In some cases, the string should not be editable
	# (see below).  If a string is selected a callback should be
	# called; if the string is edited, another callback should be
	# called.
	def selection_seteditable(self, editable):
		"""Make the selected string editable or not."""
		self._editBar.enableEdit(editable)

	def selection_setlist(self, list, initial):
		"""Set the list of strings.

		Arguments (no defaults):
		list -- list of strings
		initial -- 0 <= initial < len(list) or None -- this is
			the index of the element in list which should
			be the selected item (no element is selected
			if None)
		"""
		self.DeleteAllItems()
		self._itemlist=list
		self._itemlist_initial=initial
		self.SetItemList()
		self.SelectItem(self._itemlist_initial)

	def selection_setselection(self, pos):
		"""Set the selection to the item indicated.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) or None -- the index of
			the item to be selected
		"""
		if pos==None:pos=-1
		self.SelectItem(pos)

	def selection_getselection(self):
		"""Return the index of the currently selected item.

		The return value is the index of the currently
		selected item, or None if no item is selected.
		"""
		self._selecteditem=self.GetSelected()
		return self._selecteditem


	def selection_append(self, item):
		"""Append an item to the end of the list.

		Which item is selected after the element is added is
		undefined.  The list which was given to
		selection_setlist or __init__ (whichever was last) is
		modified.
		"""
		i=self.GetItemCount()
		self.InsertItem(i,item)
		self.SelectItem(i)
		
	def selection_gettext(self):
		"""Return the string value of the currently selected item.

		When no item is selected, the behavior is undefined.
		[ This method is called in the id_callback to get the
		new value of the currently selected item. ]
		"""
		self._selecteditem=self.GetSelected()
		txt='None'
		if self._selecteditem!=None:
			try:
				txt= self.GetItemText(self._selecteditem,0)
			except:
				txt = 'Except'
		return txt

	def selection_replaceitem(self, pos, item):
		"""Replace the indicated item with a new value.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be changed
		item -- string to replace the item with
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		if not item:item=' '
		self.SetItemText(pos,0,item)

	def selection_deleteitem(self, pos):
		"""Delete the indicated item from the list.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be deleted
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		self.DeleteItem(pos)


	# Interface to the various button.
	def edit_setsensitive(self, sensitive):
		"""Make the `Edit' button (in)sensitive."""
		self._itemBar.enable('Edit',sensitive)

	def delete_setsensitive(self, sensitive):
		"""Make the `Delete' button (in)sensitive."""
		self._itemBar.enable('Delete',sensitive)

	def export_setsensitive(self, sensitive):
		"""Make the `Export...' button (in)sensitive."""
		self._itemBar.enable('Export',sensitive)
