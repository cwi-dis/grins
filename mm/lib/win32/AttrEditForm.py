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

error = 'lib.win32.AttrEditForm.error'

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
##################################################
##################################################
# AttrEditor as a tab-dialog

class AttrCtrl:
	def __init__(self,wnd,attr,resid):
		self._wnd=wnd
		self._attr=attr
		self._resid=resid
		self._initctrl=None

	def sethelp(self):
		if not self._initctrl: return
		if not hasattr(self._wnd,'_attrinfo'): return
		infoc=self._wnd._attrinfo
		a=self._attr
		hd=a.gethelpdata()
		if hd[1]:
			infoc.settext(hd[2]+' - default: ' + hd[1])
		else:
			infoc.settext(hd[2])
	
	def getcurrent(self):
		return self._attr.getcurrent()

	def a2tuple(self,str):
		if not str: return ()
		l=string.split(str, ' ')
		n=[]
		for e in l:
			if e: n.append(string.atoi(e))
		if len(n)==1:
			return (n[0],)
		elif len(n)==2:
			return (n[0],n[1])
		elif len(n)==3:
			return (n[0],n[1],n[2])
		elif len(n)==4:
			return (n[0],n[1],n[2],n[3])
		return ()


##################################
class OptionsCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._options=components.ComboBox(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._options.attach_to_parent()
		self._attrname.settext(self._attr.getlabel())
		list = self._attr.getoptions()
		val = self._attr.getcurrent()
		self.setoptions(list,val)
		self._wnd.HookCommand(self.OnCombo,self._resid[1])
		self._wnd.HookCommand(self.OnReset,self._resid[2])
	
	def setoptions(self,list,val):
		if val not in list:
			val = list[0]
		ix=list.index(val)
		if self._initctrl:
			self._options.resetcontent()
			self._options.setoptions(list)
			self._options.setcursel(ix)
		
	def setvalue(self, val):
		if not self._initctrl: return
		list = self._attr.getoptions()
		if val not in list:
			raise error, 'value not in list'
		ix=list.index(val)
		self._options.setcursel(ix)

	def getvalue(self):
		if self._initctrl:
			return self._options.getvalue() 
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnCombo(self,id,code):
		self.sethelp()

class OptionsRadioCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Control(wnd,resid[0])
		n = len(self._attr.getoptions())
		self._radio=[]
		for ix in range(n):
			self._radio.append(components.RadioButton(wnd,resid[ix+1]))

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrname.settext(self._attr.getlabel())
		list = self._attr.getoptions()
		n = len(list)
		for ix in range(n):
			self._radio[ix].attach_to_parent()
			self._radio[ix].hookcommand(self._wnd,self.OnRadio)
		self._wnd.HookCommand(self.OnReset,self._resid[n+1])
		val = self._attr.getcurrent()
		self.setoptions(list,val)
	
	def setoptions(self,list,val):
		if val not in list:
			val = list[0]
		if self._initctrl:
			for i in range(len(list)):
				self._radio[i].settext(list[i])
				self._radio[i].setcheck(0)
			ix=list.index(val)
			self._radio[ix].setcheck(1)
		
	def setvalue(self, val):
		if not self._initctrl: return
		list = self._attr.getoptions()
		if val not in list:
			val = list[0]
		ix=list.index(val)
		for i in range(len(list)):
			self._radio[i].setcheck(0)
		self._radio[ix].setcheck(1)

	def getvalue(self):
		if self._initctrl:
			list = self._attr.getoptions()
			for ix in range(len(list)):
				if self._radio[ix].getcheck():
					return list[ix]	
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnRadio(self,id,code):
		self.sethelp()

##################################
class FileCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		self._attrname.settext(self._attr.getlabel())
		self._attrval.settext(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])
		self._wnd.HookCommand(self.OnReset,self._resid[3])

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.settext(val)
	def getvalue(self):
		if self._initctrl:
			return self._attrval.gettext()
		return self._attr.getcurrent()

	def OnBrowse(self,id,code):
		self._attr.browser_callback()

	def OnReset(self,id,code):
		if self._attr:self._attr.reset_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()

##################################
class ColorCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		self._attrname.settext(self._attr.getlabel())
		self._attrval.settext(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnBrowse,self._resid[2])
		self._wnd.HookCommand(self.OnReset,self._resid[3])

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.settext(val)

	def getvalue(self):
		if self._initctrl:
			return self._attrval.gettext()
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:self._attr.reset_callback()

	def OnBrowse(self,id,code):
		if not self._initctrl: return
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
		dlg = win32ui.CreateColorDialog(win32api.RGB(r,g,b),win32con.CC_ANYCOLOR,self._wnd)
		if dlg.DoModal() == win32con.IDOK:
			newcol = dlg.GetColor()
			r, g, b = win32ui.GetWin32Sdk().GetRGBValues(newcol)
			return r, g, b
		return None

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()

##################################
class StringCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval=components.Edit(wnd,resid[1])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval.attach_to_parent()
		self._attrname.settext(self._attr.getlabel())
		self._attrval.settext(self._attr.getcurrent())
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnReset,self._resid[2])

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.settext(val)

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		return self._attrval.gettext()

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()

class IntPairCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._attrval1=components.Edit(wnd,resid[1])
		self._attrval2=components.Edit(wnd,resid[2])

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrval1.attach_to_parent()
		self._attrval2.attach_to_parent()
		self._attrname.settext(self._attr.getlabel())

		strxy=self._attr.getcurrent()
		x,y=self.a2tuple(strxy)
		self._attrval1.settext('%s' % x)
		self._attrval2.settext('%s' % y)
		self._wnd.HookCommand(self.OnEdit,self._resid[1])
		self._wnd.HookCommand(self.OnEdit,self._resid[2])
		self._wnd.HookCommand(self.OnReset,self._resid[3])

	def setvalue(self, val):
		if self._initctrl:
			x,y=self.a2tuple(val)
			self._attrval1.settext('%s' % x)
			self._attrval2.settext('%s' % y)

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		sx=self._attrval1.gettext()
		sy=self._attrval2.gettext()
		return sx + ' ' + sy

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()

##################################
class AttrPage(dialog.PropertyPage):
	def __init__(self,form):
		self._form=form
		self._cd={}
		self._group=None
		self._tabix=-1
		self._title='Untitled page'
		self._initdialog=None
		self._attrinfo=components.Static(self,grinsRC.IDC_ATTR_INFO)
		
	def do_init(self):
		id=self.getpageresid()
		self.createctrls()
		import __main__
		dll=__main__.resdll
		dialog.PropertyPage.__init__(self,id,dll,grinsRC.IDR_GRINSED)
		
	def OnInitDialog(self):
		self._initdialog=self
		dialog.PropertyPage.OnInitDialog(self)
		self.HookCommand(self.OnRestore,grinsRC.IDUC_RESTORE)
		self.HookCommand(self.OnApply,grinsRC.IDUC_APPLY)
		self.HookCommand(self.OnCancel,win32con.IDCANCEL)
		self.HookCommand(self.OnOK,win32con.IDOK)
		self._attrinfo.attach_to_parent()
		for ctrl in self._cd.values():ctrl.OnInitCtrl()
		if self._group:
			self._group.oninitdialog(self)
				
	def OnRestore(self,id,code): self._form.call('Restore')
	def OnApply(self,id,code): self._form.call('Apply')
	def OnCancel(self,id,code): self._form.call('Cancel')
	def OnOK(self,id,code): self._form.call('OK')

	def setvalue(self, attr, val):
		if self._cd.has_key(attr): 
			self._cd[attr].setvalue(val)
	def getvalue(self, attr):
		if self._cd.has_key(attr):
			return self._cd[attr].getvalue()
	def setoptions(self,attr, list,val):
		if self._cd.has_key(attr):
			self._cd[attr].setoptions(list,val)
	
	def setgroup(self,group):
		self._group=group
	

	# override for not group attributes
	def createctrls(self):
		if not self._group:
			raise error, 'you must override createctrls for page',self
			return
		self._title=self._group.gettitle()
		self._cd=self._group.createctrls(self)
	
	# override for not group pages
	def getpageresid(self):
		if not self._group:
			raise error,'you must override getpageresid for page',self
			return -1
		return self._group.getpageresid() 

	def getctrl(self,aname):
		for a in self._cd.keys():
			if a.getname()==aname:
				return self._cd[a]
		return None

	def settabix(self,ix):
		self._tabix=ix
	def settabtext(self,tabctrl):
		if self._tabix<0:
			raise error,'tab index is uninitialized'
		tabctrl.SetItemText(self._tabix,self._title)


###############################	
class SingleAttrPage(AttrPage):
	def __init__(self,form,attr):
		AttrPage.__init__(self,form)
		self._attr=attr

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		ctrl=self._cd[self._attr]
		ctrl.OnInitCtrl()
		ctrl.sethelp()

	def createctrls(self):
		a=self._attr
		self._title=a.getlabel()
		t = a.gettype()
		if a.getname()=='layout':
			self._cd[a] = OptionsRadioCtrl(self,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4))
		elif a.getname()=='visible' or a.getname()=='drawbox' or a.getname()=='popup':
			self._cd[a] = OptionsRadioCtrl(self,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4,grinsRC.IDC_5))
		elif a.getname()=='transparent':
			self._cd[a] = OptionsRadioCtrl(self,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4,grinsRC.IDC_5,grinsRC.IDC_6))
		elif SingleAttrPage.ctrlmap.has_key(t):
			self._cd[a] = SingleAttrPage.ctrlmap[t][0](self,a,SingleAttrPage.ctrlmap[t][1])
		else:
			self._cd[a] = SingleAttrPage.ctrlmap['string'][0](self,a,SingleAttrPage.ctrlmap['string'][1])

	def getpageresid(self):
		a=self._attr
		t = a.gettype()
		if a.getname()=='layout':
			return grinsRC.IDD_EDITATTR_O1_R2
		elif a.getname()=='visible' or a.getname()=='drawbox' or a.getname()=='popup':
			return grinsRC.IDD_EDITATTR_O1_R3
		elif a.getname()=='transparent':
			return grinsRC.IDD_EDITATTR_O1_R4			
		elif SingleAttrPage.ctrlmap.has_key(t):
			return SingleAttrPage.idmap[t]
		else:
			return SingleAttrPage.idmap['string']
	ctrlmap={
		'option':(OptionsCtrl,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'file':(FileCtrl,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'color':(ColorCtrl,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'string':(StringCtrl,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3))}
	idmap={'option':grinsRC.IDD_EDITATTR_O1,
		'file':grinsRC.IDD_EDITATTR_F1,
		'color':grinsRC.IDD_EDITATTR_C1,
		'string':grinsRC.IDD_EDITATTR_S1}

##################################

import sysmetrics

# Layout context class (helper)
class ScreenLayoutContext:
	def __init__(self):
		self._units=appcon.UNIT_PXL

		sw,sh=sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl
		self._aspect=sw/float(sh)

		self._ymax=190
		self._xmax=int(self._ymax*self._aspect)

		self._xscale=sw/float(self._xmax)
		self._yscale=sh/float(self._ymax)

	def getboundingbox(self):
		return (0,0,self._xmax,self._ymax)

	def getunits(self):
		return self._units

	def getxscale(self):
		return self._xscale
	def getyscale(self):
		return self._yscale


	def fromlayout(self,box):
		if not box: return box
		x=self._xscale
		y=self._yscale
		return int(box[0]*x+0.5),int(box[1]*y+0.5),int(box[2]*x+0.5),int(box[3]*y+0.5)

	def tolayout(self,box):
		if not box: return box
		x=self._xscale
		y=self._yscale
		return (int(0.5+box[0]/x),int(0.5+box[1]/y),int(0.5+box[2]/x),int(0.5+box[3]/y))

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
	def __init__(self,form,layoutcontext=None):
		AttrPage.__init__(self,form)
		cmifwnd._CmifWnd.__init__(self)
		if not layoutcontext:
			self._layoutcontext=ScreenLayoutContext()
		else:
			self._layoutcontext=layoutcontext
		lc=self._layoutcontext
		DrawTk.drawTk.SetScale(lc.getxscale(),lc.getyscale())
		
	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		self._layoutctrl=self.createLayoutCtrl()
		self.create_box(self.getcurrentbox())

	def createLayoutCtrl(self):
		v=_CmifView._CmifPlayerView(docview.Document(docview.DocTemplate()))
		v.createWindow(self)
		x,y,w,h=self._layoutcontext.getboundingbox()
		rc=(20,20,w,h)
		v.init(rc)
		v.SetWindowPos(self.GetSafeHwnd(),rc,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
		v.OnInitialUpdate()
		v.ShowWindow(win32con.SW_SHOW)
		v.UpdateWindow()	
		return v
		
	def create_box(self,box):
		# call create box against layout control but be modeless and cool!
		self._layoutctrl.assert_not_in_create_box()
		if box and (box[2]==0 or box[3]==0):box=None	
		modeless=1;cool=1
		self._layoutctrl.create_box('',self.update,box,self._layoutcontext.getunits(),modeless,cool)
		
	def fromlayout(self,box):
		return self._layoutcontext.fromlayout(box)

	def tolayout(self,box):
		return self._layoutcontext.tolayout(box)
	
	def setvalue(self, attr, val):
		if not self._initdialog: return
		self._cd[attr].setvalue(val)
		if self.islayoutattr(attr):
			self.setvalue2layout(val)

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


	######################
	# subclass overrides

	def getcurrentbox(self):
		lc=self.getctrl('base_winoff')
		val=lc.getcurrent()
		if not val:
			box=None
		else:
			box=self.a2tuple(val)
			box=self.tolayout(box)		
		return box
	
	def setvalue2layout(self,val):
		if not val:
			box=()
		else:
			box=self.a2tuple(val)
			box=self.tolayout(box)
		self.create_box(box)
	
	def islayoutattr(self,attr):
		if self._group:
			return self._group.islayoutattr(attr)
		else:
			return 0

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def update(self,*box):
		if self._initdialog and box:
			box=self.fromlayout(box)
			lc=self.getctrl('base_winoff')
			lc.setvalue('%d %d %d %d' % box)


class PosSizeLayoutPage(LayoutPage):
	def __init__(self,form,layoutcontext=None):
		LayoutPage.__init__(self,form,layoutcontext)
		self._xy=None
		self._wh=None

	def getcurrentbox(self):
		self._xy=self.getctrl('subregionxy')
		self._wh=self.getctrl('subregionwh')
		sxy=self._xy.getcurrent()
		if not sxy:sxy='0 0'
		swh=self._wh.getcurrent()
		if not swh:swh='0 0'
		val = sxy + ' ' + swh
		box=self.a2tuple(val)
		box=self.tolayout(box)
		return box

	def setvalue2layout(self,val):
		sxy=self._xy.getvalue()
		if not sxy:sxy='0 0'
		swh=self._wh.getvalue()
		if not swh:swh='0 0'
		val= sxy + ' ' + swh
		box=self.a2tuple(val)
		box=self.tolayout(box)
		self.create_box(box)

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def update(self,*box):
		if self._initdialog and box:
			box=self.fromlayout(box)
			self._xy.setvalue('%d %d' % box[:2])
			self._wh.setvalue('%d %d' % box[2:])



############################
#  goes in:  Attrgrs.py

# order of groups in the file is important (first match first)
# all attributes not in complete groups 
# will be displayed on their own page

attrgrs=(
	{'name':'infogroup',
	'title': 'Info',
	'match': 'first', # can be: 'all', 'part', 'first' default: 'all'
	'attrs':[
		'title',
		'abstract',
		'alt',
		'longdesc',
		'author',
		'copyright',
		'comment'
		]},


	{'name':'subregion',
	'title':'Destination region',
	'attrs':[
		'subregionxy',
		'subregionwh',
		'displayfull',
		'subregionanchor',
		]},

	{'name':'base_winoff_and_units',
	'title':'Position and size',
	'attrs':[
		'base_winoff',
		'units',
		]},

	{'name':'base_winoff',
	'title':'Position and size',
	'attrs':[
		'base_winoff',
		]},

	{'name':'system',
	'title': 'System properties',
	'attrs':[
		'system_bitrate',
		'system_captions',
		'system_language',
		'system_overdub_or_caption',
		'system_required',
		'system_screen_depth',
		'system_screen_size',
		]},

	{'name':'name',
	'title':'Node name',
	'attrs':[
		'name',
		'channel',
		]},

	{'name':'.cname',
	'title':'Channel name',
	'attrs':[
		'.cname',
		'type',
		]},

	{'name':'duration_and_loop',
	'title':'Duration and loop',
	'attrs':[
		'duration',
		'loop',
		]},

	)

attrgrsdict={}
for d in attrgrs:
	attrgrsdict[d['name']]=d


############################
# platform and implementation dependent group
# one per group
class AttrGroup:
	def __init__(self,data):
		self._data=data
		self._al=[]

	# decision interface (may be platform independent)
	def visit(self,al):
		self._al=[]
		for a in al:
			if a.getname() in self._data['attrs']:
				self._al.append(a)

	def matches(self):
		if not self._data.has_key('match'):
			return len(self._al)==len(self._data['attrs'])
		if self._data['match']=='part':
			return len(self._al)>1
		elif self._data['match']=='first':
			fa=	self._data['attrs'][0]
			return (fa in self.alnames())
		else:
			return len(self._al)==len(self._data['attrs'])

	def alnames(self):
		l=[]
		for a in self._al:
			l.append(a.getname())
		return l
	def getattr(self,aname):
		for a in self._al:
			if a.getname()==aname:
				return a
		return None

	def gettitle(self):
		return self._data['title']

	def islayoutattr(self,attr):
		return 0

	def getpageclass(self):
		return AttrPage

	# auto create
	# override for special cases
	def createctrls(self,wnd):
		cd={}
		for a in self._al:
			CtrlCl=self.getctrlclass(a)
			cd[a]=CtrlCl(wnd,a,self.getctrlids(a))
		return cd

	special_attrcl={
		'system_captions':OptionsRadioCtrl,
		'layout':OptionsRadioCtrl,
		'visible':OptionsRadioCtrl,
		'drawbox':OptionsRadioCtrl,
		}

	def getctrlclass(self,a):
		n = a.getname()
		if AttrGroup.special_attrcl.has_key(n):
			return AttrGroup.special_attrcl[n]
		t = a.gettype()
		if t=='option':return OptionsCtrl
		elif t=='file': return FileCtrl
		elif t=='color': return ColorCtrl
		else: return StringCtrl
	
	# part of page initialization
	# do whatever not default
	def oninitdialog(self,wnd):
		pass
	

class InfoGroup(AttrGroup):
	data=attrgrsdict['infogroup']

	def __init__(self,data=None):
		if data:
			AttrGroup.__init__(self,data)
		else:
			AttrGroup.__init__(self,InfoGroup.data)
		self._ix=1

	def getctrlids(self,a):
		ix=self._ix
		exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*10+1,ix*10+2,ix*10+3)
		self._ix=self._ix+1
		return ids

	def getpageresid(self):
		n=len(self._al)
		exec 'id=grinsRC.IDD_EDITATTR_S%d' % n
		return id


# base_winoff
class LayoutGroup(AttrGroup):
	data=attrgrsdict['base_winoff']
	def __init__(self,data=None):
		if data:
			AttrGroup.__init__(self,data)
		else:
			AttrGroup.__init__(self,LayoutGroup.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1
	def getctrlids(self,a):
		ix=self._data['attrs'].index(a.getname())
		exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*10+1,ix*10+2,ix*10+3)
		return ids
	def getpageclass(self):
		return LayoutPage
	def islayoutattr(self,attr):
		return (attr.getname()=='base_winoff')

# base_winoff, units
class LayoutGroupWithUnits(LayoutGroup):
	data=attrgrsdict['base_winoff_and_units']
	def __init__(self):
		LayoutGroup.__init__(self,LayoutGroupWithUnits.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O1
	def getctrlids(self,a):
		if a.getname()=='base_winoff':
			ids=(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)
		elif a.getname()=='units':
			ids=(grinsRC.IDC_4,grinsRC.IDC_5,grinsRC.IDC_6)
		else:
			raise error,'LayoutGroup2 resource conflict'
		return ids


class SubregionGroup(AttrGroup):
	data=attrgrsdict['subregion']
	def __init__(self):
		AttrGroup.__init__(self,SubregionGroup.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O2
	def getctrlids(self,a):
		ix=self._data['attrs'].index(a.getname())
		exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*3+1,ix*3+2,ix*3+3)
		return ids

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('subregionxy')
		cd[a]=IntPairCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_16))
		a=self.getattr('subregionwh')
		cd[a]=IntPairCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_14,grinsRC.IDC_15,grinsRC.IDC_17))
		a=self.getattr('displayfull')
		cd[a]=OptionsRadioCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22,grinsRC.IDC_23,grinsRC.IDC_24,grinsRC.IDC_25))		
		a=self.getattr('subregionanchor')
		cd[a]=OptionsCtrl(wnd,a,(grinsRC.IDC_31,grinsRC.IDC_32,grinsRC.IDC_33))		
		return cd

	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_11)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])

	def getpageclass(self):
		return PosSizeLayoutPage
	def islayoutattr(self,attr):
		return (attr.getname()=='subregionxy') or (attr.getname()=='subregionwh')

class SystemGroup(AttrGroup):
	data=attrgrsdict['system']
	def __init__(self):
		AttrGroup.__init__(self,SystemGroup.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1S5_R3
	def getctrlids(self,a):
		ix=self._data['attrs'].index(a.getname())
		ix=ix+1 # 1 based
		if ix==2:
			exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*10+1,ix*10+2,ix*10+3,ix*10+4,ix*10+5)
		else:
			exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*10+1,ix*10+2,ix*10+3)
		return ids
	def getpageclass(self):
		return AttrPage

class NameGroup(AttrGroup):
	data=attrgrsdict['name']
	def __init__(self):
		AttrGroup.__init__(self,NameGroup.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1
	def getctrlids(self,a):
		ix=self._data['attrs'].index(a.getname())
		ix=ix+1 # 1 based
		exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*10+1,ix*10+2,ix*10+3)
		return ids
	def getpageclass(self):
		return AttrPage
	
class CNameGroup(AttrGroup):
	data=attrgrsdict['.cname']
	def __init__(self):
		AttrGroup.__init__(self,CNameGroup.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1
	def getctrlids(self,a):
		ix=self._data['attrs'].index(a.getname())
		ix=ix+1 # 1 based
		exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*10+1,ix*10+2,ix*10+3)
		return ids
	def getpageclass(self):
		return AttrPage
		

class DurationGroup(AttrGroup):
	data=attrgrsdict['duration_and_loop']

	def __init__(self,data=None):
		AttrGroup.__init__(self,DurationGroup.data)

	def getctrlids(self,a):
		ix=self._data['attrs'].index(a.getname())
		ix=ix+1 # 1 based
		exec 'ids=(grinsRC.IDC_%d,grinsRC.IDC_%d,grinsRC.IDC_%d)' % (ix*10+1,ix*10+2,ix*10+3)
		return ids

	def getpageresid(self):
		n=len(self._al)
		exec 'id=grinsRC.IDD_EDITATTR_S%d' % n
		return id
	
	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.ID_GROUP1)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])
		
	
############################
# platform dependent association
# what we have implemented, anything else goes as singleton
groupsui={
	'infogroup':InfoGroup,

	'base_winoff':LayoutGroup,
	'base_winoff_and_units':LayoutGroupWithUnits,
	'subregion':SubregionGroup,

	'system':SystemGroup,
	'name':NameGroup,
	'.cname':CNameGroup,

	'duration_and_loop':DurationGroup,
	}

###########################
from  GenFormView import GenFormView

class AttrEditFormNew(GenFormView):
	# class variables to store user preferences
	# None
	# Class constructor. Calls base constructor and nullify members
	def __init__(self,doc):
		GenFormView.__init__(self,doc,grinsRC.IDD_EDITATTR_SHEET)	
		self._title='Properties'
		self._attriblist=None
		self._cbdict=None
		self._prsht=None;
		self._a2p={}
		self._pages=[]

	# Creates the actual OS window
	def createWindow(self,parent):
		self._parent=parent
		import __main__
		dll=__main__.resdll
		prsht=dialog.PropertySheet(grinsRC.IDR_GRINSED,dll)
		prsht.EnableStackedTabs(1)

		self.buildcontext()

		grattrl=[] # list of attr in groups (may be all)
		# create groups pages
		grattrl=self.creategrouppages()
		
		# create singletons not desrciped by groups
		for i in range(len(self._attriblist)):
			a=self._attriblist[i]
			if a not in grattrl:
				page=SingleAttrPage(self,a)
				self._a2p[a]=page
				self._pages.append(page)

		# init pages
		for page in self._pages:
			page.do_init()

		# add pages to the sheet in the correct group order
		l=self._pages[:]
		self._pages=[]
		ix=0
		for i in range(len(self._attriblist)):
			a=self._attriblist[i]
			p=self._a2p[a]
			if p in l:
				p.settabix(ix)
				ix=ix+1
				self._pages.append(p)
				prsht.AddPage(p)
				l.remove(p)

		self.CreateWindow(parent)
		prsht.CreateWindow(self,win32con.DS_CONTEXTHELP | win32con.DS_SETFONT | win32con.WS_CHILD | win32con.WS_VISIBLE)
		self.HookMessage(self.onSize,win32con.WM_SIZE)		
		rc=self.GetWindowRect()
		prsht.SetWindowPos(0,(0,0,0,0),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOSIZE)
		self._prsht=prsht

		tabctrl=prsht.GetTabCtrl()
		for page in self._pages:
			page.settabtext(tabctrl)

		prsht.SetActivePage(self._pages[0])
		prsht.RedrawWindow()

	def creategrouppages(self):
		grattrl=[]	 # all attr in groups
		l=self._attriblist[:]
		for grdict in attrgrs:
			grname=grdict['name']
			if not groupsui.has_key(grname): continue
			group=groupsui[grname]()
			group.visit(l)
			if group.matches():
				PageCl=group.getpageclass()
				grouppage=PageCl(self)
				self._pages.append(grouppage)
				grouppage.setgroup(group)
				for a in group._al:
					self._a2p[a]=grouppage
					grattrl.append(a)
					l.remove(a)
		return grattrl

	def buildcontext(self):
		return
		a=self._attriblist[0]
		w=a.wrapper
		self.root=w.toplevel.root
		print dir(self.root)
		print dir(self.root.context)
		channels = self.root.context.channels
		for ch in channels:
			print ch.name,ch.attrdict

		if hasattr(w,'node'):
			self._node=w.node
			
		#print w,dir(w)
		if hasattr(w,'channel'):
			self._channel=w.channel

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
		frc=(30,4,frc[2]-frc[0]+30,frc[3]-frc[1]+4)
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
		return self._a2p[attrobj].getvalue(attrobj)

	# Called by the core system to set a value on the list
	def setvalue(self,attrobj,newval):
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		self._a2p[attrobj].setvalue(attrobj,newval)

	# Called by the core system to set attribute options
	def setoptions(self,attrobj,list,val):
		if not self._obj_:
			raise error, 'os window not exists'
		if attrobj not in self._attriblist:
			raise error, 'item not in list'
		t = attrobj.gettype()
		if t != 'option':
			raise error, 'item not an option'
		self._a2p[attrobj].setoptions(attrobj,list,val)


import __main__
if hasattr(__main__,'use_tab_attr_editor') and __main__.use_tab_attr_editor:
	AttrEditForm=AttrEditFormNew


