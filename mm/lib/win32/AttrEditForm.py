__version__ = "$Id$"


""" @win32doc|AttrEditForm
This module contains the ui implementation of the AttrEditDialog
It is implemented as a ListView with dialog bars.

The MFC class that offers the list view functionality is the CListView
Objects of this class are exported to Python through the win32ui pyd
as objects of type PyCView. The AttrEditForm extends the PyCListView.

The MFC class that offers the dialog bar functionality is the CDialogBar
Objects of this class are exported to Python through the win32ui pyd
as objects of type PyCDialogBar. The dialog bars used by the AttrEditForm 
extend the PyCDialogBar.

The AttrEditForm dialog bars are created using the resource dialog templates 
with identifiers IDD_EDITSTRINGATTR,IDD_EDITOPTIONSATTR,IDD_EDITFILEATTR and IDD_STDDLGBAR.
Like all resources these templates can be found in cmif\win32\src\GRiNSRes\GRiNSRes.rc.

"""

import string
# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components,sysmetrics

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC


# Base dialog bar
class DlgBar(window.Wnd):
	# Class constructor. Calls base class constructor and creates the OS window
	def __init__(self,parent,resid):
		AFX_IDW_DIALOGBAR=0xE805
		wndDlgBar = win32ui.CreateDialogBar()
		window.Wnd.__init__(self,wndDlgBar)
		wndDlgBar.CreateWindow(parent,resid,
			afxres.CBRS_ALIGN_BOTTOM,AFX_IDW_DIALOGBAR)

# Base class for attribute edit bars
class AttrDlgBar(DlgBar):
	# Class constructor. Calls base constructor and associates controlst with ids
	def __init__(self,parent,resid,change_cb,reset_cb):
		DlgBar.__init__(self,parent,resid)
		self._reset=components.Button(self,grinsRC.IDUC_RESET)
		self._reset.attach_to_parent()
		self._attrname=components.Edit(self,grinsRC.IDC_EDIT1)
		self._attrname.attach_to_parent()
		parent.HookCommand(self.OnReset,grinsRC.IDUC_RESET)

		# mechanism to tab to different wnds
		self._null=components.Button(self,grinsRC.IDC_NULL)
		self._null.attach_to_parent()
		self._null.setstyleflag(win32con.BS_NOTIFY)
		parent.HookCommand(self.OnNull,grinsRC.IDC_NULL)

		self._change_cb=change_cb
		self._reset_cb=reset_cb

	# Response to reset button
	def OnReset(self,id,code):
		apply(self._reset_cb,())

	# Response to internal-null button
	def OnNull(self,id,code):
		if code==win32con.BN_SETFOCUS:
			AttrEditForm.instance.SetFocus()
			
	def resize(self,cx):
		rc=win32mu.Rect(self.GetWindowRect())
		wnd=self.GetDlgItem(grinsRC.IDUC_RESET)
		rc1=win32mu.Rect(wnd.GetWindowRect())
		x=cx-rc1.width();y=rc1.top-rc.top
		wnd.SetWindowPos(self.GetSafeHwnd(),(x,y,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOSIZE)
		
# Dialog bar to edit string attributes
class StringAttrDlgBar(AttrDlgBar):
	# Class constructor. Calls base constructor and associates controlst with ids
	def __init__(self,parent,change_cb,reset_cb):
		AttrDlgBar.__init__(self,parent,grinsRC.IDD_EDITSTRINGATTR,change_cb,reset_cb)
		self._attrval=components.Edit(self,grinsRC.IDC_EDIT2)
		self._attrval.attach_to_parent()
		parent.HookCommand(self.OnEdit,grinsRC.IDC_EDIT2)
	# Response to edit change
	def OnEdit(self,id,code):
		if code==win32con.EN_CHANGE:
			apply(self._change_cb,(self._attrval.gettext(),))

	def resize(self,cx):
		AttrDlgBar.resize(self,cx)
		wnd=self.GetDlgItem(grinsRC.IDC_EDIT2)
		rc1=win32mu.Rect(self.GetDlgItem(grinsRC.IDUC_RESET).GetWindowRect())
		rc2=win32mu.Rect(wnd.GetWindowRect())
		cx=rc1.left-rc2.left-4;cy=rc2.height()
		wnd.SetWindowPos(self.GetSafeHwnd(),(0,0,cx,cy),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)

# Dialog bar to edit options attributes
class OptionsAttrDlgBar(AttrDlgBar):
	# Class constructor. Calls base constructor and associates controlst with ids
	def __init__(self,parent,change_cb,reset_cb):
		AttrDlgBar.__init__(self,parent,grinsRC.IDD_EDITOPTIONSATTR,change_cb,reset_cb)
		self._options=components.ComboBox(self,grinsRC.IDC_COMBO1)
		self._options.attach_to_parent()
		parent.HookCommand(self.OnChangeOption,grinsRC.IDC_COMBO1)
	
	# Response to combo selection change
	def OnChangeOption(self,id,code):
		if code==win32con.CBN_SELCHANGE:
			apply(self._change_cb,(self._options.getvalue(),))

	def resize(self,cx):
		AttrDlgBar.resize(self,cx)
		wnd=self.GetDlgItem(grinsRC.IDC_COMBO1)
		rc1=win32mu.Rect(self.GetDlgItem(grinsRC.IDUC_RESET).GetWindowRect())
		rc2=win32mu.Rect(wnd.GetWindowRect())
		cx=rc1.left-rc2.left-4;cy=rc2.height()
		wnd.SetWindowPos(self.GetSafeHwnd(),(0,0,cx,cy),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)
			
# Dialog bar to edit file attributes
class FileAttrDlgBar(AttrDlgBar):
	# Class constructor. Calls base constructor and associates controlst with ids
	def __init__(self,parent,change_cb,reset_cb):
		AttrDlgBar.__init__(self,parent,grinsRC.IDD_EDITFILEATTR,change_cb,reset_cb)
		self._attrval=components.Edit(self,grinsRC.IDC_EDIT2)
		self._attrval.attach_to_parent()
		parent.HookCommand(self.OnEdit,grinsRC.IDC_EDIT2)
		parent.HookCommand(self.OnBrowse,grinsRC.IDUC_BROWSE)
		self._browsecb=None
	# Response to edit box change
	def OnEdit(self,id,code):
		if code==win32con.EN_CHANGE:
			apply(self._change_cb,(self._attrval.gettext(),))

	# Response to button browse
	def OnBrowse(self,id,code):
		if self._browsecb:
			apply(apply,self._browsecb)

	def resize(self,cx):
		if cx<360:return
		AttrDlgBar.resize(self,cx)
		wnd=self.GetDlgItem(grinsRC.IDUC_BROWSE)
		rc=win32mu.Rect(self.GetWindowRect())
		rc1=win32mu.Rect(self.GetDlgItem(grinsRC.IDUC_RESET).GetWindowRect())
		rc2=win32mu.Rect(wnd.GetWindowRect())
		x=rc1.left-rc.left-rc2.width()-4;y=rc2.top-rc.top
		wnd.SetWindowPos(self.GetSafeHwnd(),(x,y,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOSIZE)

		wnd=self.GetDlgItem(grinsRC.IDC_EDIT2)
		rc1=win32mu.Rect(self.GetDlgItem(grinsRC.IDUC_BROWSE).GetWindowRect())
		rc2=win32mu.Rect(wnd.GetWindowRect())
		cx=rc1.left-rc2.left-4;cy=rc2.height()
		wnd.SetWindowPos(self.GetSafeHwnd(),(0,0,cx,cy),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)

# Dialog bar to edit color attributes
class ColorAttrDlgBar(AttrDlgBar):
	# Class constructor. Calls base constructor and associates controlst with ids
	def __init__(self,parent,change_cb,reset_cb):
		AttrDlgBar.__init__(self,parent,grinsRC.IDD_EDITCOLORATTR,change_cb,reset_cb)
		self._attrval=components.Edit(self,grinsRC.IDC_EDIT2)
		self._attrval.attach_to_parent()
		parent.HookCommand(self.OnEdit,grinsRC.IDC_EDIT2)
		parent.HookCommand(self.OnBrowse,grinsRC.IDUC_BROWSE)
		self._parent=parent
		self._browsecb=None
	# Response to edit box change
	def OnEdit(self,id,code):
		if code==win32con.EN_CHANGE:
			apply(self._change_cb,(self._attrval.gettext(),))

	# Response to button browse
	def OnBrowse(self,id,code):
		oldcolorstring = self._attrval.gettext()
		list = string.split(string.strip(oldcolorstring))
		r = g = b = 0
		if len(list) == 3:
			try:
				r = string.atoi(list[0])
				g = string.atoi(list[1])
				b = string.atoi(list[2])
			except ValueError:
				pass
		rv = self.ColorSelect(r, g, b)
		if rv != None:
			colorstring = "%d %d %d"%rv
			self._attrval.settext(colorstring)
	
	def ColorSelect(self, r, g, b):
		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self._parent)
		if dlg.DoModal() == win32con.IDOK:
			newcol = dlg.GetColor()
			r, g, b = win32ui.GetWin32Sdk().GetRGBValues(newcol)
			return r, g, b
		return None

	def resize(self,cx):
		if cx<360:return
		AttrDlgBar.resize(self,cx)
		wnd=self.GetDlgItem(grinsRC.IDUC_BROWSE)
		rc=win32mu.Rect(self.GetWindowRect())
		rc1=win32mu.Rect(self.GetDlgItem(grinsRC.IDUC_RESET).GetWindowRect())
		rc2=win32mu.Rect(wnd.GetWindowRect())
		x=rc1.left-rc.left-rc2.width()-4;y=rc2.top-rc.top
		wnd.SetWindowPos(self.GetSafeHwnd(),(x,y,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOSIZE)

		wnd=self.GetDlgItem(grinsRC.IDC_EDIT2)
		rc1=win32mu.Rect(self.GetDlgItem(grinsRC.IDUC_BROWSE).GetWindowRect())
		rc2=win32mu.Rect(wnd.GetWindowRect())
		cx=rc1.left-rc2.left-4;cy=rc2.height()
		wnd.SetWindowPos(self.GetSafeHwnd(),(0,0,cx,cy),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)

# Dialog bar with the buttons Restore,Apply,Cancel,OK
class StdDlgBar(window.Wnd):
	# Class constructor. Calls base constructor and associates controlst with ids
	def __init__(self, parent,cbdict):
		AFX_IDW_DIALOGBAR=0xE805
		wndDlgBar = win32ui.CreateDialogBar()
		window.Wnd.__init__(self,wndDlgBar)
		wndDlgBar.CreateWindow(parent,grinsRC.IDD_STDDLGBAR,
			afxres.CBRS_ALIGN_BOTTOM,AFX_IDW_DIALOGBAR)
		parent.HookCommand(self.OnRestore,grinsRC.IDUC_RESTORE)
		parent.HookCommand(self.OnApply,grinsRC.IDUC_APPLY)
		parent.HookCommand(self.OnCancel,win32con.IDCANCEL)
		parent.HookCommand(self.OnOK,win32con.IDOK)
		self._cbdict=cbdict

	# Helper function to call a callback given a strin id
	def call(self,k):
		d=self._cbdict
		if d and d.has_key(k) and d[k]:
			apply(apply,d[k])				

	# Response to button Restore
	def OnRestore(self,id,code):self.call('Restore')
	# Response to button Apply
	def OnApply(self,id,code):self.call('Apply')
	# Response to button OK
	def OnOK(self,id,code):self.call('OK')
	# Response to button Cancel
	def OnCancel(self,id,code):self.call('Cancel')

	def resize(self,cx):
		wndApply=self.GetDlgItem(grinsRC.IDUC_APPLY)
		wndOK=self.GetDlgItem(win32con.IDOK)
		rc=win32mu.Rect(self.GetWindowRect())
		rc1=win32mu.Rect(wndOK.GetWindowRect())
		rc2=win32mu.Rect(wndApply.GetWindowRect())
		x=cx-rc1.width() 	
		y=rc1.top-rc.top
		wndOK.SetWindowPos(self.GetSafeHwnd(),(x,y,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOSIZE)
		wndApply.SetWindowPos(self.GetSafeHwnd(),(x-rc2.width()-4,y,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOSIZE)

# Implementation of the AttrEditDialog needed by the core system
# The implementation is based on the framework class CListView				
class AttrEditForm(docview.ListView):
	# class variables to store user preferences
	last_cx=None
	last_cy=None
	colWidthList=(132, 96, 82, 400)
	instance=None

	# Class constructor. Calls base constructor and nullify members
	def __init__(self,doc):
		docview.ListView.__init__(self,doc)
		self._title='Properties'
		self._attriblist=None
		self._cbdict=None

	# Change window style attributes before it is created
	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)
		if AttrEditForm.last_cx:cs.cx=AttrEditForm.last_cx
		if AttrEditForm.last_cy:cs.cy=AttrEditForm.last_cy
		return cs.to_csd()

	# Creates the actual OS window
	def createWindow(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
		AttrEditForm.instance=self

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		hwnd = self._obj_.GetSafeHwnd()
		style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE);
		win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, 
			(style & ~commctrl.LVS_TYPEMASK) | commctrl.LVS_SINGLESEL | commctrl.LVS_REPORT | commctrl.LVS_SHOWSELALWAYS)
		self.SetExStyle(commctrl.LVS_EX_FULLROWSELECT)
		
		l=AttrEditForm.colWidthList
		header_list=[("Property",l[0]),("Current Value",l[1]),("Default",l[2]),("Explanation",l[3]),]
		self.InsertListHeader(header_list)
		self.FillAttrList()
		
		self.selecteditem=None
		self._dlgBar=None
		self._attr_type=None
		self.SetStdDlgBar()
		self.GetParent().HookNotify(self.OnNotifyItemChanged,commctrl.LVN_ITEMCHANGED)

		# use tab to set focus
		self.HookKeyStroke(self.onTabKey,9)    #tab
		self.HookKeyStroke(self.onEnter,13)
		self.HookKeyStroke(self.onEsc,27)
		
		# resize 
		self.GetParent().HookMessage(self.onSize,win32con.WM_SIZE)

		# select first element
		# self.SelectItem(0)

	# Response to a list control selection change
	def OnNotifyItemChanged(self,nm, nmrest):
		(hwndFrom, idFrom, code), (itemNotify, sub, newState, oldState, change, point, lparam) = nm, nmrest
		oldSel = (oldState & commctrl.LVIS_SELECTED)<>0
		newSel = (newState & commctrl.LVIS_SELECTED)<>0
		if oldSel != newSel and self.selecteditem!=itemNotify:
			try:
				self.selecteditem = itemNotify
				self.ItemToEditor()
			except win32ui.error:
				self.selecteditem = None

	# Response to keyboard input
	# set focus to dlg on Tab
	def onTabKey(self,key):
		if self._dlgBar:self._dlgBar.SetFocus()
	def onEnter(self,key):
		self.call('OK')
	def onEsc(self,key):
		self.call('Cancel')

	# Helper function to set the extented style of the list control
	def SetExStyle(self,or_style):
		style=self.GetListCtrl().SendMessage(commctrl.LVM_GETEXTENDEDLISTVIEWSTYLE)
		style = style | or_style
		self.GetListCtrl().SendMessage(commctrl.LVM_SETEXTENDEDLISTVIEWSTYLE,0,style)

	# Get the list control selection 
	def GetSelected(self):
		try:
			index = self.GetNextItem(-1, commctrl.LVNI_SELECTED)
		except win32ui.error:
			index=None
		return index

	# Helper to position the std dialog
	def SetStdDlgBar(self):
		frame=self.GetParent()
		self._stdDlgBar=StdDlgBar(frame,self._cbdict)
		l,t,r,b=self.GetWindowRect()
		self._stdDlgBar.resize(r-l-4)
		frame.RecalcLayout()

	
	# Helper to position the attribute edit dialog bar
	def SetAttrDlgBar(self,t):
		#if t==self._attr_type:
		#	return
		if self._dlgBar:
			self._dlgBar.DestroyWindow()
		frame=self.GetParent()

		if t == 'option':EditDlgBar=OptionsAttrDlgBar
		elif t == 'file':EditDlgBar=FileAttrDlgBar
		elif t == 'color':EditDlgBar=ColorAttrDlgBar
		else:EditDlgBar=StringAttrDlgBar # all other types
		self._dlgBar=EditDlgBar(frame,self.UpdateValue,self.OnReset)
		self._attr_type=t
		frame.RecalcLayout()
		self.doResize()
	
	# Date tranfer from the list to the edit area
	def ItemToEditor(self):
		sel=self.selecteditem
		if sel==None:return
		try:
			attrname = self.GetItemText(sel,0)
		except win32ui.error:
			attrname=''
		try:
			attrval = self.GetItemText(sel,1)
		except win32ui.error:
			attrval=''

		a = self._attriblist[sel]
		t = a.gettype()
		self.SetAttrDlgBar(t)
		d=self._dlgBar
		if t == 'option':
			d._attrname.settext(attrname)
			list = a.getoptions()
			val = a.getcurrent()
			if val not in list:
				val = list[0]
			ix=list.index(val)
			d._options.setoptions(list)
			d._options.setcursel(ix)
		elif t == 'file':
			d._attrname.settext(attrname)
			d._attrval.settext(attrval)
			d._browsecb=(a.browser_callback, ())
		else: # all other types
			d._attrname.settext(attrname)
			d._attrval.settext(attrval)
		self.SetFocus()

	# Updates a list item text			
	def UpdateValue(self,str):
		self.SetItemText(self.selecteditem, 1, str)
	# Response to reset button	
	def OnReset(self):
		if self.selecteditem:
			self._attriblist[self.selecteditem].reset_callback()
	# insert column headers in the list control
	def InsertListHeader(self,header_list):
		for ix in range(len(header_list)):
			t=header_list[ix]
			format=(commctrl.LVCFMT_LEFT, t[1], t[0], 0)
			self.InsertColumn(ix, format)
	# Fill the list with the attributes
	def FillAttrList(self):
		attriblist=self._attriblist
		for i in range(len(attriblist)):
			self.insertAttr(i,attriblist[i])

	# Insert the atrribute at the index
	def insertAttr(self,i,a):	
		self.InsertItem(i,a.getlabel())
		self.SetItemText(i,1,a.getcurrent())
		hd=a.gethelpdata()
		self.SetItemText(i,2,hd[1])
		self.SetItemText(i,3,hd[2])

	# Set the selction on the list control to the index	
	def SelectItem(self,nItem=0):
		nMask=commctrl.LVIF_STATE
		nState=commctrl.LVIS_SELECTED | commctrl.LVIS_FOCUSED
		(self.GetListCtrl()).SetItemState(nItem,nState,nMask)

	# Response to WM_SIZE
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		cx=msg.width()
		if cx<360:cx=360
		cx=cx-2*sysmetrics.cxframe
		self._cx=cx
		if self._dlgBar:
			self._dlgBar.resize(cx)
		if self._stdDlgBar:
			self._stdDlgBar.resize(cx)

	def doResize(self):
		if hasattr(self,'_cx'):
			self._dlgBar.resize(self._cx)
			self._stdDlgBar.resize(self._cx)

	# Called when the view is activated 
	def activate(self):
		pass

	# Called when the view is deactivated 
	def deactivate(self):
		pass

	# cmif general interface
	# Called by the core system to close this window
	def close(self):
		AttrEditForm.instance=None
		self.savegeometry()
		if hasattr(self,'GetParent'):
			self.GetParent().DestroyWindow()

	# Called by the core system to set the title of this window
	def settitle(self,title):
		self._title=title
		if hasattr(self,'GetParent'):
			if self.GetParent().GetSafeHwnd():
				self.GetParent().SetWindowText(title)

	# Called by the core system to show this window
	def show(self):
		self.pop() # for now

	# Called by the core system to bring to front this window
	def pop(self):
		childframe=self.GetParent()
		childframe.ShowWindow(win32con.SW_SHOW)
		frame=childframe.GetMDIFrame()
		frame.MDIActivate(childframe)

	# Called by the core system to hide this window
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)

	# hold user preferences for size and columns width in class variables
	def savegeometry(self):
		l,t,r,b=self.GetParent().GetWindowRect()
		AttrEditForm.last_cx=r-l
		AttrEditForm.last_cy=b-t
		f=self.GetColumnWidth
		AttrEditForm.colWidthList=(f(0),f(1),f(2),f(3))
	def getcreatesize(self):
		return AttrEditForm.last_cx,AttrEditForm.last_cy

	# Part of the closing mechanism
	# the parent frame delegates the responcibility to us
	# we must decide what to do (OK,Cancel,..)
	# interpret it as a Cancel for now (we should ask, save or not)
	def OnClose(self):
		self.savegeometry()
		self.call('Cancel')

	# Helper to call a callback given its string id
	def call(self,k):
		d=self._cbdict
		if d and d.has_key(k) and d[k]:
			apply(apply,d[k])				

	# cmif specific interface
	# Called by the core system to get a value from the list
	def getvalue(self,attrobj):
		ix=self._attriblist.index(attrobj)
		try:
			attrval = self.GetItemText(ix,1)
		except win32ui.error:
			attrval=''
		return attrval
	# Called by the core system to set a value on the list
	def setvalue(self,attrobj,newval):
		if not self._obj_:
			raise error, 'os window not exists'
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		ix=self._attriblist.index(attrobj)
		self.SetItemText(ix,1,newval)	
		if ix==self.selecteditem:
			self.ItemToEditor()
	# Called by the core system to set attribute options
	def setoptions(self,attrobj,list,val):
		ix_item=self._attriblist.index(attrobj)
		t = attrobj.gettype()
		if ix_item==self.selecteditem and t == 'option':
			if val not in list:
				val = list[0]
			ix_sel=list.index(val)
			self._dlgBar._options.resetcontent()
			self._dlgBar._options.setoptions(list)
			self._dlgBar._options.setcursel(ix_sel)
			self.SetItemText(ix_item,1,val)




##################################################
# AttrEditor as a tab-dialog

class AttrPage(dialog.PropertyPage):
	def __init__(self,id,form,attr):
		import __main__
		dll=__main__.resdll
		dialog.PropertyPage.__init__(self,id,dll,grinsRC.IDR_GRINSED)
		self._form=form
		self._attr=attr
		self._initdialog=None
		self._attrname=components.Edit(self,grinsRC.IDC_EDIT1)
		self._attrinfo=components.Static(self,grinsRC.IDC_ATTR_INFO)

	def OnInitDialog(self):
		self._initdialog=self
		dialog.PropertyPage.OnInitDialog(self)
		self.HookCommand(self.OnRestore,grinsRC.IDUC_RESTORE)
		self.HookCommand(self.OnApply,grinsRC.IDUC_APPLY)
		self.HookCommand(self.OnCancel,win32con.IDCANCEL)
		self.HookCommand(self.OnOK,win32con.IDOK)
		self.HookCommand(self.OnReset,grinsRC.IDUC_RESET)
		if not self._attr: return
		self._attrname.attach_to_parent()
		self._attrinfo.attach_to_parent()
		a=self._attr
		self._attrname.settext(a.getlabel())
		hd=a.gethelpdata()
		if hd[1]:
			self._attrinfo.settext(hd[2]+' - default: ' + hd[1])
		else:
			self._attrinfo.settext(hd[2])
				
	def OnRestore(self,id,code): self._form.call('Restore')
	def OnApply(self,id,code): self._form.call('Apply')
	def OnCancel(self,id,code): self._form.call('Cancel')
	def OnOK(self,id,code): self._form.call('OK')
	def OnReset(self,id,code):
		if self._attr:self._attr.reset_callback()

class OptionPage(AttrPage):
	def __init__(self,form,attr):
		AttrPage.__init__(self,grinsRC.IDD_EDITOPTIONSATTR1,form,attr)
		self._options=components.ComboBox(self,grinsRC.IDC_COMBO1)

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		self._options.attach_to_parent()
		if not self._options._hwnd: return
		a=self._attr
		list = a.getoptions()
		val = a.getcurrent()
		if val not in list:
			val = list[0]
		ix=list.index(val)
		self._options.setoptions(list)
		self._options.setcursel(ix)
	
	def setoptions(self,list,val):
		if val not in list:
			val = list[0]
		ix=list.index(val)
		if self._initdialog:
			self._options.resetcontent()
			self._options.setoptions(list)
			self._options.setcursel(ix)
		
	def setvalue(self, val):
		pass
	def getvalue(self):
		if not self._initdialog:
			return self._attr.getcurrent()
		return self._options.getvalue() 

class FilePage(AttrPage):
	def __init__(self,form,ixattr):
		AttrPage.__init__(self,grinsRC.IDD_EDITFILEATTR1,form,ixattr)
		self._attrval=components.Edit(self,grinsRC.IDC_EDIT2)
		self._browsecb=None

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		self._attrval.attach_to_parent()
		if not self._attrval._hwnd: retrun
		a=self._attr
		self._attrval.settext(a.getcurrent())
		self.HookCommand(self.OnBrowse,grinsRC.IDUC_BROWSE)

	def setvalue(self, val):
		if self._initdialog:
			self._attrval.settext(val)
	def getvalue(self):
		if not self._initdialog:
			return self._attr.getcurrent()
		return self._attrval.gettext()

	def OnBrowse(self,id,code):
		self._attr.browser_callback()

class ColorPage(AttrPage):
	def __init__(self,form,attr):
		AttrPage.__init__(self,grinsRC.IDD_EDITCOLORATTR1,form,attr)
		self._attrval=components.Edit(self,grinsRC.IDC_EDIT2)

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		self._attrval.attach_to_parent()
		self._attrval.settext(self._attr.getcurrent())
		self.HookCommand(self.OnBrowse,grinsRC.IDUC_BROWSE)

	def setvalue(self, val):
		if self._initdialog:
			self._attrval.settext(val)

	def getvalue(self):
		if not self._initdialog:
			return self._attr.getcurrent()
		return self._attrval.gettext()

	# Response to button browse
	def OnBrowse(self,id,code):
		oldcolorstring = self._attrval.gettext()
		list = string.split(string.strip(oldcolorstring))
		r = g = b = 0
		if len(list) == 3:
			try:
				r = string.atoi(list[0])
				g = string.atoi(list[1])
				b = string.atoi(list[2])
			except ValueError:
				pass
		rv = self.ColorSelect(r, g, b)
		if rv != None:
			colorstring = "%d %d %d"%rv
			self._attrval.settext(colorstring)
	
	def ColorSelect(self, r, g, b):
		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self._form)
		if dlg.DoModal() == win32con.IDOK:
			newcol = dlg.GetColor()
			r, g, b = win32ui.GetWin32Sdk().GetRGBValues(newcol)
			return r, g, b
		return None


class StringPage(AttrPage):
	def __init__(self,form,attr):
		AttrPage.__init__(self,grinsRC.IDD_EDITSTRINGATTR1,form,attr)
		self._attrval=components.Edit(self,grinsRC.IDC_EDIT2)

	def OnInitDialog(self):
		self._attrval.attach_to_parent()
		self._attrval.settext(self._attr.getcurrent())
		AttrPage.OnInitDialog(self)

	def setvalue(self, val):
		if self._initdialog:
			self._attrval.settext(val)

	def getvalue(self):
		if not self._initdialog:
			return self._attr.getcurrent()
		return self._attrval.gettext()

##################################
# LayoutPage
import cmifwnd, _CmifView
import appcon, sysmetrics
import string
import DrawTk

# for now: 
#	works only with pixels
#   works with reference the full screen instead of the parent layout

class LayoutPage(AttrPage,cmifwnd._CmifWnd):
	def __init__(self,form,attr):
		AttrPage.__init__(self,grinsRC.IDD_EDITRECTATTR,form,attr)
		cmifwnd._CmifWnd.__init__(self)
		self._attrval=components.Edit(self,grinsRC.IDC_EDIT2)
		self._layoutctrl=None

		# for now work only in pixels
		self._units=appcon.UNIT_PXL

		# try to preserve screen aspect ratio
		# but should be layout channel 
		sw,sh=sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl
		self._aspect=sw/float(sh)

		self._ymax=190
		self._xmax=int(self._ymax*self._aspect)

		self._xscale=sw/float(self._xmax)
		self._yscale=sh/float(self._ymax)

		DrawTk.drawTk.SetScale(self._xscale,self._yscale)

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		self._attrval.attach_to_parent()

		# get box and units from self._attr
		val=self._attr.getcurrent()
		self._attrval.settext(val)
		if not val:
			box=None
		else:
			box=self.a2tuple(val)
			box=self.tolayout(box)		

		# create layout control
		v=_CmifView._CmifPlayerView(docview.Document(docview.DocTemplate()))
		v.createWindow(self)
		rc=(20,20,self._xmax,self._ymax)
		v.init(rc)
		v.SetWindowPos(self.GetSafeHwnd(),rc,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
		v.OnInitialUpdate()
		v.ShowWindow(win32con.SW_SHOW)
		v.UpdateWindow()	
		self._layoutctrl=v

		# call create box against layout control but be modeless and cool!
		modeless=1;cool=1
		v.create_box('',self.update,box,self._units,modeless,cool)

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def update(self,*box):
		if self._initdialog and box:
			box=self.fromlayout(box)
			self._attrval.settext('%d %d %d %d' % box)

	def setvalue(self, val):
		if self._initdialog:
			self._attrval.settext(val)
			if not val:
				box=None
			else:
				box=self.a2tuple(val)
				box=self.tolayout(box)
			self._layoutctrl.assert_not_in_create_box()
			modeless=1;cool=1
			self._layoutctrl.create_box('',self.update,box,self._units,modeless,cool)

	def getvalue(self):
		if not self._initdialog:
			return self._attr.getcurrent()
		return self._attrval.gettext()
	
	def fromlayout(self,box):
		if not box: return
		x=self._xscale
		y=self._yscale
		return int(box[0]*x+0.5),int(box[1]*y+0.5),int(box[2]*x+0.5),int(box[3]*y+0.5)

	def tolayout(self,box):
		if not box: return
		x=self._xscale
		y=self._yscale
		return (int(0.5+box[0]/x),int(0.5+box[1]/y),int(0.5+box[2]/x),int(0.5+box[3]/y))
	
	# not validating
	def a2tuple(self,str):
		if not str: return ()
		l=string.split(str, ' ')
		n=[]
		for e in l:
			if e: n.append(string.atoi(e))
		return (n[0],n[1],n[2],n[3])

	def OnDestroy(self,params):
		DrawTk.drawTk.RestoreState()

###########################3
from  GenFormView import GenFormView

class AttrEditFormNew(GenFormView):
	# class variables to store user preferences
	# None
	# Class constructor. Calls base constructor and nullify members
	def __init__(self,doc):
		GenFormView.__init__(self,doc,grinsRC.IDD_FORM1)	
		self._title='Properties'
		self._attriblist=None
		self._cbdict=None
		self._prsht=None;
		self._pages={}

	# Creates the actual OS window
	def createWindow(self,parent):
		self._parent=parent
		import __main__
		dll=__main__.resdll
		prsht=dialog.PropertySheet(grinsRC.IDR_GRINSED,dll)
		prsht.EnableStackedTabs(1)
		al=self._attriblist
		page=None
		for i in range(len(al)):
			a=al[i]
			t = a.gettype()
			if t == 'option':
				page=OptionPage(self,a)
			elif t == 'file':
				page=FilePage(self,a)
			elif t == 'color':
				page=ColorPage(self,a)
			else:
				if a.getlabel()=='Position and size':
					page=LayoutPage(self,a)
				else:
					page=StringPage(self,a)
			self._pages[a]=page
			prsht.AddPage(page)

		self.CreateWindow(parent)
		prsht.CreateWindow(self,win32con.DS_CONTEXTHELP | win32con.DS_SETFONT | win32con.WS_CHILD | win32con.WS_VISIBLE)
		self.HookMessage(self.onSize,win32con.WM_SIZE)		
		rc=self.GetWindowRect()
		prsht.SetWindowPos(0,(0,0,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE)
		self._prsht=prsht
		tabctrl=prsht.GetTabCtrl()
		for i in range(len(al)):
			tabctrl.SetItemText(i,al[i].getlabel())

		# add an experimantal layout page
		# not needed since 'Position and size'
		#is such an example
		#layout=LayoutPage(self,None)
		#prsht.AddPage(layout)
		#tabctrl.SetItemText(len(al),'Layout test')

		prsht.SetActivePage(self._pages[al[0]])
		prsht.RedrawWindow()

	def OnInitialUpdate(self):
		GenFormView.OnInitialUpdate(self)
		
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		if not self._parent or not self._parent._obj_:return
		if not self._prsht or not self._prsht._obj_:return
		rc=self._prsht.GetWindowRect()
		frc=self._parent.CalcWindowRect(rc)
		mainframe=self._parent.GetMDIFrame()
		frc=mainframe.ScreenToClient(frc)
		frc=(30,20,frc[2]-frc[0]+30,frc[3]-frc[1]+20)
		self._parent.MoveWindow(frc)

		
	# Called when the view is activated 
	def activate(self):
		pass

	# Called when the view is deactivated 
	def deactivate(self):
		pass

	# cmif general interface
	# Called by the core system to close this window
	def close(self):
		if hasattr(self,'GetParent'):
			self.GetParent().DestroyWindow()

	# Called by the core system to set the title of this window
	def settitle(self,title):
		self._title=title
		if hasattr(self,'GetParent'):
			if self.GetParent().GetSafeHwnd():
				self.GetParent().SetWindowText(title)

	# Called by the core system to show this window
	def show(self):
		self.pop() # for now

	# Called by the core system to bring to front this window
	def pop(self):
		childframe=self.GetParent()
		childframe.ShowWindow(win32con.SW_SHOW)
		frame=childframe.GetMDIFrame()
		frame.MDIActivate(childframe)

	# Called by the core system to hide this window
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)

	# Part of the closing mechanism
	# the parent frame delegates the responcibility to us
	def OnClose(self):
		self.call('Cancel')

	# Helper to call a callback given its string id
	def call(self,k):
		d=self._cbdict
		if d and d.has_key(k) and d[k]:
			apply(apply,d[k])				

	# cmif specific interface
	# Called by the core system to get a value from the list
	def getvalue(self,attrobj):
		if not self._obj_:
			raise error, 'os window not exists'
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		if self._pages[attrobj]._attr!=attrobj:
			raise error, 'wrong redirection'
		return self._pages[attrobj].getvalue()

	# Called by the core system to set a value on the list
	def setvalue(self,attrobj,newval):
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		self._pages[attrobj].setvalue(newval)

	# Called by the core system to set attribute options
	def setoptions(self,attrobj,list,val):
		if not self._obj_:
			raise error, 'os window not exists'
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		t = attrobj.gettype()
		if t != 'option':
			raise error, 'item not an option'
		self._pages[attrobj].setoptions(list,val)


import __main__
if hasattr(__main__,'use_tab_attr_editor') and __main__.use_tab_attr_editor:
	AttrEditForm=AttrEditFormNew






################################
# code under development

# a group of controls for an attr
# StringCtrl, FileCtrl, ColorCtrl and OptionsCtrl are AttrCtrl
class AttrCtrl:
	def __init__(self, page, attr):
		self._page=page
		self._attr=attr
		self._initctrl=None

	# called by the parent page OnInitDialog
	def OnInitCtrl(self):
		self._initctrl=self
		# hook commands for this

	# response methods
	# ...

	# set/get methods
	def setvalue(self, val):
		pass
	def getvalue(self):
		return ''

# a property page with 1 or more attributes
class AttrGrPage:
	def __init__(self):
		self._title=''
		# maps attr to AttrCtrl
		# each AttrCtrl represents an attr
		self._attrctrl={}

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		for ctrl in self._attrctrl.values():
			ctrl.OnInitCtrl()

	def addattr(self,attr):
		# for each attr.gettype()
		self._attrctrl[attr]=AttrCtrl(self,attr)

	# select from the available templates
	# if none is found use 1 attr per page
	def __findtemplate(self):
		pass

	def setvalue(self, attr, val):
		self._attrctrl[attr].settext(val)

	def getvalue(self, attr):
		return self._attrctrl[attr].gettext()


