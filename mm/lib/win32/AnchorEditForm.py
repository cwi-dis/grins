# std win32 modules
import win32ui,win32con,win32api

# win32 python lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

class DlgBar(window.Wnd):
	def __init__(self,parent,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		AFX_IDW_DIALOGBAR=0xE805
		wndDlgBar = win32ui.CreateDialogBar()
		window.Wnd.__init__(self,wndDlgBar)
		wndDlgBar.CreateWindow(parent,resid,
			align,AFX_IDW_DIALOGBAR)

class EditAnchorDlgBar(DlgBar):
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
		
	def OnEdit(self,id,code):
		if code==win32con.EN_CHANGE and self._id_cb:
			apply(self._id_cb,(self._idedit.gettext(),))

	def OnChangeOption(self,id,code):
		if code==win32con.CBN_SELCHANGE and self._opt_cb:
			apply(self._opt_cb,(self._options.getvalue(),))

class AnchorDlgBar(DlgBar):
	def __init__(self, parent,cbdict):
		DlgBar.__init__(self,parent,grinsRC.IDD_ANCHOR_BAR,afxres.CBRS_ALIGN_RIGHT)
		self._cbdict=cbdict
		self._buttons=b={
			'New':components.Button(self,grinsRC.IDUC_NEW),
			'Edit':components.Button(self,grinsRC.IDUC_EDIT),
			'Delete':components.Button(self,grinsRC.IDUC_DELETE),
			'Export':components.Button(self,grinsRC.IDUC_EXPORT),
			}
		for i in self._buttons.keys():
			parent.HookCommand(self.onCmd,b[i]._id)
			b[i].attach_to_parent()
	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])			
	def onCmd(self,id,code):
		for i in self._buttons.keys():
			if id==self._buttons[i]._id:
				self.call(i)
	def enable(self,strid,f):
		self._buttons[strid].enable(f)

class StdDlgBar(DlgBar):
	def __init__(self, parent,cbdict):
		DlgBar.__init__(self,parent,grinsRC.IDD_STDDLGBAR,afxres.CBRS_ALIGN_TOP)
		parent.HookCommand(self.OnRestore,grinsRC.IDUC_RESTORE)
		parent.HookCommand(self.OnApply,grinsRC.IDUC_APPLY)
		parent.HookCommand(self.OnCancel,win32con.IDCANCEL)
		parent.HookCommand(self.OnOK,win32con.IDOK)
		self._cbdict=cbdict
	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])				
	def OnRestore(self,id,code):self.call('Restore')
	def OnApply(self,id,code):self.call('Apply')
	def OnOK(self,id,code):self.call('OK')
	def OnCancel(self,id,code):self.call('Cancel')

				
class AnchorEditForm(docview.ListView):
	def __init__(self,doc):
		docview.ListView.__init__(self,doc)
		self._title='Anchor Editor'
		self._itemlist=[]
		self._selecteditem=None
		self._itemlist
		self._cbdict={}
		self._typelabels=None
	
	def do_init(self, title, typelabels, list, initial, adornments):
		self._title=title
		self._itemlist=list
		self._itemlist_initial=initial
		self._typelabels=typelabels
		self._cbdict=adornments['callbacks']

	def OnInitialUpdate(self):
		hwnd = self._obj_.GetSafeHwnd()
		style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE);
		win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, 
			(style & ~commctrl.LVS_TYPEMASK) | commctrl.LVS_REPORT | commctrl.LVS_SHOWSELALWAYS)
		self.SetExStyle(commctrl.LVS_EX_FULLROWSELECT)
		
		header_list=[("ID",120),("Type",120),]
		self.InsertListHeader(header_list)
		self.SetItemList()

		frame=self.GetParent()
		self._stdDlgBar=StdDlgBar(frame,self._cbdict)
		self._editBar=EditAnchorDlgBar(frame,self.UpdateID,self.UpdateType)
		self._itemBar=AnchorDlgBar(frame,self._cbdict)
		frame.RecalcLayout()
		
		if self._typelabels:
			self._editBar._options.setoptions(self._typelabels)

		self.GetParent().HookNotify(self.OnNotifyItemChanged,commctrl.LVN_ITEMCHANGED)
		self.SelectItem(self._itemlist_initial)
		return 0

	def OnNotifyItemChanged(self,nm, nmrest):
		(hwndFrom, idFrom, code), (itemNotify, sub, newState, oldState, change, point, lparam) = nm, nmrest
		oldSel = (oldState & commctrl.LVIS_SELECTED)<>0
		newSel = (newState & commctrl.LVIS_SELECTED)<>0
		if oldSel != newSel and self._selecteditem!=itemNotify:
			try:
				self._selecteditem = itemNotify
				self.call('Anchor')
				self.ItemToEditor()
			except win32ui.error:
				self._selecteditem = None

	def OnKeyDown(self,params):
		msg=win32mu.Win32Msg(params)
		print params
		# set focus to dlg on Tab and Enter

	def SetExStyle(self,or_style):
		style=self.GetListCtrl().SendMessage(commctrl.LVM_GETEXTENDEDLISTVIEWSTYLE)
		style = style | or_style
		self.GetListCtrl().SendMessage(commctrl.LVM_SETEXTENDEDLISTVIEWSTYLE,0,style)


	def GetSelected(self):
		try:
			index = self.GetNextItem(-1, commctrl.LVNI_SELECTED)
		except win32ui.error:
			index=None
		return index


	def ItemToEditor(self):
		sel=self._selecteditem
		if sel==None:return
		try:
			id = self.GetItemText(sel,0)
		except win32ui.error:
			id=''
#		try:
#			type = self.GetItemText(sel,1)
#		except win32ui.error:
#			attrval=''

		d=self._editBar
		d._idedit.settext(id)
#		d._options.setcursel(ix)
		self.SetFocus()

	def call(self,k):
		d=self._cbdict
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])			
	def UpdateID(self,str):
		self.SetItemText(self._selecteditem, 0, str)
		self.call('EditId')
	
	def UpdateType(self,str):
		# not supported yet
		#self.SetItemText(self._selecteditem, 1, str)	
		self.call('Type')

	def InsertListHeader(self,header_list):
		for ix in range(len(header_list)):
			t=header_list[ix]
			format=(commctrl.LVCFMT_LEFT, t[1], t[0], 0)
			self.InsertColumn(ix, format)

	def SetItemList(self):
		itemlist=self._itemlist
		for i in range(len(itemlist)):
			l = itemlist[i]
			self.InsertItem(i,l)
			self.SetItemText(i,1,'')
				
	def SelectItem(self,nItem=None):
		if not nItem:nItem=-1
		#args: nItem,nSubItem,nMask,szItem,nImage,nState,nStateMask,lParam
		nSubItem=nImage=lParam=0;szItem=''
		nMask=commctrl.LVIF_STATE
		nState=nStateMask=commctrl.LVIS_SELECTED|commctrl.LVIS_FOCUSED
		self.SetItem(nItem,nSubItem,nMask,szItem,nImage,nState,nStateMask,lParam)

	# called by mainwnd
	def onActivate(self,f):
		pass

	# cmif general interface
	def close(self):
		if hasattr(self,'GetParent'):
			self.GetParent().DestroyWindow()
	def settitle(self,title):
		self._title=title
		if hasattr(self,'GetParent'):
			if self.GetParent().GetSafeHwnd():
				self.GetParent().SetWindowText(title)

	def show(self):
		self.pop() # for now

	def pop(self):
		childframe=self.GetParent()
		childframe.ShowWindow(win32con.SW_SHOW)
		frame=childframe.GetMDIFrame()
		frame.MDIActivate(childframe)

	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)

	# the parent frame delegates the responcibility to us
	# we must decide what to do (OK,Cancel,..)
	# interpret it as a Cancel for now (we should ask, save or not)
	def OnClose(self):
		self.call('Cancel')

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
		self._editBar._options.enable(0)

	def type_choice_show(self):
		"""Show the type choice part of the dialog."""
		self._editBar._options.enable(1)

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
		pass #self.__window.type_choice_setsensitive(pos, sensitive)


	# Interface to the selection area.  The selection area
	# consists of a list of strings with the possibility to select
	# one of these strings, and to edit the value of the selected
	# string.  In some cases, the string should not be editable
	# (see below).  If a string is selected a callback should be
	# called; if the string is edited, another callback should be
	# called.
	def selection_seteditable(self, editable):
		"""Make the selected string editable or not."""
		pass

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
		self.SelectItem(pos)

	def selection_getselection(self):
		"""Return the index of the currently selected item.

		The return value is the index of the currently
		selected item, or None if no item is selected.
		"""
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
		self.SetItemText(i,1,'')
		self.SelectItem(i)
		
	def selection_gettext(self):
		"""Return the string value of the currently selected item.

		When no item is selected, the behavior is undefined.
		[ This method is called in the id_callback to get the
		new value of the currently selected item. ]
		"""
		if self._selecteditem:
			return self.GetItemText(self._selecteditem,0)

	def selection_replaceitem(self, pos, item):
		"""Replace the indicated item with a new value.

		Arguments (no defaults):
		pos -- 0 <= pos < len(list) -- the index of the item
			that is to be changed
		item -- string to replace the item with
		The list which was given to selection_setlist or
		__init__ (whichever was last) is modified.
		"""
		if item:
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
