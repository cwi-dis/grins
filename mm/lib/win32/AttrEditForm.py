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
Sdk=win32ui.GetWin32Sdk()

# win32 lib modules
import win32mu,components,sysmetrics

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

# App constants
import appcon
from win32mu import Point,Size,Rect # shorcuts
from appcon import UNIT_MM, UNIT_SCREEN, UNIT_PXL

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

	def drawOn(self,dc):
		pass

# temp stuff not safe
def atoft(str):
	# convert string into tuple of floats
	return tuple(map(string.atof, string.split(str)))

def fttoa(t,n,prec):
	if not t or len(t) != n:
		return ''
	return ((' %%.%df' % prec) * n) % t

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
		elif code==win32con.EN_CHANGE:
			if hasattr(self._wnd,'onAttrChange'):
				self._wnd.onAttrChange()

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
		self.calcIndicatorRC()

	def calcIndicatorRC(self):
		place='edit'
		pos='bottom'
		l,t,r,b=self._wnd.GetWindowRect()
		if place=='button':
			s=components.Control(self._wnd,self._resid[2])
			s.attach_to_parent()
			lc,tc,rc,bc=s.getwindowrect()
		else:
			lc,tc,rc,bc=self._attrval.getwindowrect()
		if pos=='top':
			self._indicatorRC=(lc-l,tc-t-12,lc-l+rc-lc,tc-t-4)
		else:
			self._indicatorRC=(lc-l,bc-t+4,lc-l+rc-lc,bc-t+16)

	def drawOn(self,dc):
		rc=self._indicatorRC
		ct=self.getdispcolor()
		dc.FillSolidRect(rc, win32mu.RGB(ct))
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle(rc,br)
		Sdk.DeleteObject(br)

	def invalidateInd(self):
		self._wnd.InvalidateRect(self._indicatorRC)

	def setvalue(self, val):
		if self._initctrl:
			self._attrval.settext(val)
			self.invalidateInd()

	def getvalue(self):
		if self._initctrl:
			return self._attrval.gettext()
		return self._attr.getcurrent()

	def OnReset(self,id,code):
		if self._attr:self._attr.reset_callback()

	def getdispcolor(self):
		colorstring = self._attrval.gettext()
		from colors import colors
		if colors.has_key(colorstring):
			return colors[colorstring]
		list = string.split(string.strip(colorstring))
		r = g = b = 0
		if len(list) == 3:
			try:
				r = string.atoi(list[0])
				g = string.atoi(list[1])
				b = string.atoi(list[2])
			except ValueError:
				pass
		return (r,g,b)

	def OnBrowse(self,id,code):
		if not self._initctrl: return
		r,g,b=self.getdispcolor()
		rv = self.ColorSelect(r, g, b)
		if rv != None:
			colorstring = "%d %d %d"%rv
			self._attrval.settext(colorstring)
			self.invalidateInd()
	
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
		elif code==win32con.EN_CHANGE:
			self.invalidateInd()

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

class TupleCtrl(AttrCtrl):
	def __init__(self,wnd,attr,resid):
		AttrCtrl.__init__(self,wnd,attr,resid)
		self._attrname=components.Edit(wnd,resid[0])
		self._nedit=len(resid)-2
		self._attrval=[]
		for i in range(self._nedit):
			self._attrval.append(components.Edit(wnd,resid[i+1]))

	def OnInitCtrl(self):
		self._initctrl=self
		self._attrname.attach_to_parent()
		self._attrname.settext(self._attr.getlabel())
		for i in range(self._nedit):		
			self._attrval[i].attach_to_parent()
		strxy=self._attr.getcurrent()
		self.setvalue(strxy)
		for i in range(self._nedit):
			self._attrval[i].hookcommand(self._wnd,self.OnEdit)
		self._wnd.HookCommand(self.OnReset,self._resid[self._nedit+1])

	def setvalue(self, val):
		if self._initctrl:
			t=self.atoi_tuple(val)
			st=self.dtuple2stuple(t,self._nedit)
			for i in range(self._nedit):
				self._attrval[i].settext(st[i])

	def getvalue(self):
		if not self._initctrl:
			return self._attr.getcurrent()
		st=[]
		for i in range(self._nedit):
			st.append(self._attrval[i].gettext())
		s=st[0]
		for i in range(1,self._nedit):
			s = s + ' ' + st[i]
		return s

	def OnReset(self,id,code):
		if self._attr:
			self._attr.reset_callback()

	def OnEdit(self,id,code):
		if code==win32con.EN_SETFOCUS:
			self.sethelp()

class IntTupleCtrl(TupleCtrl):
	def setvalue(self, val):
		if self._initctrl:
			st = string.split(val)
			# XXX could check that len(st) == self._nedit
			for i in range(self._nedit):
				# this checks that the strings are all ints
				s = '%d' % string.atoi(st[i])
				self._attrval[i].settext(s)

class FloatTupleCtrl(TupleCtrl):
	def setvalue(self, val):
		if self._initctrl:
			st = string.split(val)
			if len(st) != self._nedit:
				st = ('',) * self._nedit
			# XXX could check that len(st) == self._nedit
			for i in range(self._nedit):
				# this checks that the strings are all floats
				# and also normalizes them
				if st[i]:
					try:
						s = '%.2f' % string.atof(st[i])
					except string.atof_error:
						s = ''
					else:
						if s[-3:] == '.00':
							# remove trailing .00
							s = s[:-3]
				else:
					s = st[i]
				self._attrval[i].settext(s)
	
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
		
	def OnPaint(self):
		dc, paintStruct = self.BeginPaint()
		self.drawOn(dc)
		self.EndPaint(paintStruct)

	def drawOn(self,dc):
		for ctrl in self._cd.values():
			ctrl.drawOn(dc)
					
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
			return grinsRC.IDD_EDITATTR_R2
		elif a.getname()=='visible' or a.getname()=='drawbox' or a.getname()=='popup':
			return grinsRC.IDD_EDITATTR_R3
		elif a.getname()=='transparent':
			return grinsRC.IDD_EDITATTR_R4			
		elif SingleAttrPage.ctrlmap.has_key(t):
			return SingleAttrPage.idmap[t]
		else:
			return SingleAttrPage.idmap['string']
	ctrlmap={
		'option':(OptionsCtrl,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3)),
		'file':(FileCtrl,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'color':(ColorCtrl,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4)),
		'string':(StringCtrl,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13))}
	idmap={'option':grinsRC.IDD_EDITATTR_O1,
		'file':grinsRC.IDD_EDITATTR_F1,
		'color':grinsRC.IDD_EDITATTR_C1,
		'string':grinsRC.IDD_EDITATTR_S1}

##################################
class LayoutScale:
	def __init__(self, wnd, xs, ys, offset = (0,0)):
		self._wnd=wnd
		self._xscale=xs
		self._yscale=ys
		self._offset = offset
		
	# rc is a win32mu.Rect in pixels
	# return coord string in units
	def orgrect_str(self, rc, units):
		str_units=''
		if units == UNIT_PXL:
			scaledrc=self.scaleCoord(rc)
			box = scaledrc.tuple_ps()
			box = box[0]-self._offset[0], \
			      box[1]-self._offset[1], \
			      box[2], box[3]
			s='(%.0f,%.0f,%.0f,%.0f)' %  box
		elif units == UNIT_SCREEN:
			s='(%.2f,%.2f,%.2f,%.2f)' %  self._wnd.inverse_coordinates(rc.tuple_ps(),units=units)
		else:
			str_units='mm'
			scaledrc=self.scaleCoord(rc)
			s='(%.1f,%.1f,%.1f,%.1f)' % self._wnd.inverse_coordinates(scaledrc.tuple_ps(),units=units)
		return s, str_units

	# rc is a win32mu.Rect in pixels
	# we return box=(x,y,w,h) in units (in arg)
	def orgrect(self, rc, units):
		if units == UNIT_PXL:
			scaledrc=self.scaleCoord(rc)
			return scaledrc.tuple_ps()
		elif units == UNIT_SCREEN:
			return self._wnd.inverse_coordinates(rc.tuple_ps(),units=units)
		else:
			scaledrc=self.scaleCoord(rc)
			return self._wnd.inverse_coordinates(scaledrc.tuple_ps(),units=units)


	# box is in units and scaled
	# return original box
	def orgbox(self, box, units):
		if units == UNIT_SCREEN:
			return box
		elif units == UNIT_PXL:
			rc=Rect((box[0],box[1],box[0]+box[2],box[1]+box[3]))
			scaledrc=self.scaleCoord(rc)
			return scaledrc.tuple_ps()
		else:
			rc=Rect((box[0],box[1],box[0]+box[2],box[1]+box[3]))
			scaledrc=self.scaleCoord(rc)
			return scaledrc.tuple_ps()
	

	# box is in units and unscaled
	# return scaled in the same units
	def layoutbox(self,box,units):
		if not box: return box
		if units==UNIT_SCREEN:
			return box
		else:
			x=self._xscale
			y=self._yscale
			if units==UNIT_PXL:
				return (box[0]/x,box[1]/y,box[2]/x,box[3]/y)
			else:
				return (box[0]/x,box[1]/y,box[2]/x,box[3]/y)

	def scaleCoord(self,rc):
		l=rc.left*float(self._xscale)
		t=rc.top*float(self._yscale)
		w=rc.width()*float(self._xscale)
		h=rc.height()*float(self._yscale)
		return Rect((l,t,l+w,t+h))


##################################
# LayoutPage
import cmifwnd, _CmifView
import appcon, sysmetrics
import string
import DrawTk

DIALOG_WINDOW_WIDTH = 240
DIALOG_WINDOW_HEIGHT = DIALOG_WINDOW_WIDTH * 3 / 4

class LayoutPage(AttrPage,cmifwnd._CmifWnd):
	def __init__(self,form):
		AttrPage.__init__(self,form)
		cmifwnd._CmifWnd.__init__(self)
		self.createLayoutContext(self._form._winsize)
		self._units=self._form.getunits()
		self._layoutctrl=None
		self._isintscale=1
		self._boxoff = 0, 0
			
	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		self._layoutctrl=self.createLayoutCtrl()
		t=components.Static(self,grinsRC.IDC_SCALE1)
		t.attach_to_parent()
		if self._isintscale:
			t.settext('scale 1 : %.0f' % self._xscale)
		else:
			t.settext('scale 1 : %.1f' % self._xscale)
		self.create_box(self.getcurrentbox())

	def OnSetActive(self):
		if not self._layoutctrl.in_create_box_mode():
			self.create_box(self.getcurrentbox())
		return self._obj_.OnSetActive()

	def OnDestroy(self,params):
		self._layoutctrl.exit_create_box()

	def createLayoutCtrl(self):
		v=_CmifView._CmifPlayerView(docview.Document(docview.DocTemplate()))
		v.createWindow(self)
		x,y,w,h=self.getboundingbox()
		rc=(20,20,w,h)
		v.SetWindowPos(self.GetSafeHwnd(),rc,
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
		v.init(rc)
		v.OnInitialUpdate()
		v.ShowWindow(win32con.SW_SHOW)
		v.UpdateWindow()	
		self.init_tk(v)
		return v
	
	def init_tk(self, v):
		v.drawTk.SetLayoutMode(0)
		self._scale=LayoutScale(v,self._xscale,self._yscale,self._boxoff)
		v.drawTk.SetScale(self._scale)

		(x,y,w,h),bunits=self._form.GetBBox()
		rc=(x,y,x+w,y+h)
		rc = v._convert_coordinates(rc, units = bunits)
		rc=self._scale.layoutbox(rc,UNIT_PXL)
		v.drawTk.SetBRect(rc)

		(x,y,w,h),bunits=self._form.GetCBox()
		rc=(x,y,x+w,y+h)
		rc = v._convert_coordinates(rc, units = bunits)
		rc=self._scale.layoutbox(rc,UNIT_PXL)
		v.drawTk.SetCRect(rc)
	
	def createLayoutContext(self,winsize=None,units=appcon.UNIT_PXL):
		if winsize:
			sw,sh=winsize
		else:
			sw,sh=sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl
		
		# try first an int scale
		n = max(1, (sw+DIALOG_WINDOW_WIDTH-1)/DIALOG_WINDOW_WIDTH, (sh+DIALOG_WINDOW_HEIGHT-1)/DIALOG_WINDOW_HEIGHT)
		scale=float(n)
		self._xmax=int(sw/scale+0.5)
		self._ymax=int(sh/scale+0.5)
		self._isintscale=1
		if n!=1 and (self._xmax<3*DIALOG_WINDOW_WIDTH/4 or self._ymax<3*DIALOG_WINDOW_HEIGHT/4):
			# try to find a better scale
			scale = max(1, float(sw)/DIALOG_WINDOW_WIDTH, float(sh)/DIALOG_WINDOW_HEIGHT)
			self._xmax=int(sw/scale+0.5)
			self._ymax=int(sh/scale+0.5)
			self._isintscale=0
		
		# finally the exact scale:
		self._xscale=float(sw)/self._xmax
		self._yscale=float(sh)/self._ymax
	
	def getboundingbox(self):
		return (0,0,self._xmax,self._ymax)

	def create_box(self,box):
		self._layoutctrl.exit_create_box()
		if box and (box[2]==0 or box[3]==0):box=None
		# call create box against layout control but be modeless and cool!
		modeless=1;cool=1;
		self._layoutctrl.create_box('',self.update,box,self._units,modeless,cool)
		self.check_units()

	def check_units(self):
		units=self._form.getunits()
		if units!=self._units:
			self._units=units
			v=self._layoutctrl
			v.drawTk.SetUnits(self._units)
			v.InvalidateRect()
			if v._objects:
				drawObj=v._objects[0]
				rb=v.inverse_coordinates(drawObj._position.tuple_ps(), units = self._units)
				apply(self.update, rb)
				from __main__ import toplevel
				toplevel.settimer(0.1,(self.OnApply,(0,0)))

			
	def setvalue(self, attr, val):
		if not self._initdialog: return
		self._cd[attr].setvalue(val)
		if self.islayoutattr(attr):
			self.setvalue2layout(val)
			

	######################
	# subclass overrides

	def getcurrentbox(self):
		lc=self.getctrl('base_winoff')
		val=lc.getcurrent()
		box=self.val2box(val)
		lbox=self._scale.layoutbox(box,self._units)
		return lbox

	def setvalue2layout(self,val):
		box=self.val2box(val)
		lbox=self._scale.layoutbox(box,self._units)
		self.create_box(lbox)
	
	def val2box(self,val):
		if not val:
			box=None
		else:
			lc=self.getctrl('base_winoff')
			box=atoft(val)
		return box
		
	def islayoutattr(self,attr):
		if self._group:
			return self._group.islayoutattr(attr)
		else:
			return 0

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def update(self,*box):
		if self._initdialog:
			lc=self.getctrl('base_winoff')
			if not box:
				lc.setvalue('')
			else:	
				box=self._scale.orgbox(box,self._units)
				if self._units==UNIT_PXL:prec=0
				elif self._units==UNIT_SCREEN:prec=1
				else: prec=2
				a=fttoa(box,4,prec)
				lc.setvalue(a)


class PosSizeLayoutPage(LayoutPage):
	def __init__(self,form):
		LayoutPage.__init__(self,form)
		self._xy=None
		self._wh=None
		ch = form._node.parent.GetChannel()
		if ch.has_key('base_window'):
			self._boxoff = ch.get('base_winoff', (0,0,0,0))[:2]

	def getcurrentbox(self):
		self._xy=self.getctrl('subregionxy')
		self._wh=self.getctrl('subregionwh')
		sxy=self._xy.getcurrent()
		if not sxy:sxy='0 0'
		swh=self._wh.getcurrent()
		if not swh:swh='0 0'
		val = sxy + ' ' + swh
		box=atoft(val)
		box = box[0]+self._boxoff[0], box[1]+self._boxoff[1], box[2], box[3]
		box=self._scale.layoutbox(box,self._units)
		return box

	def setvalue2layout(self,val):
		sxy=self._xy.getvalue()
		if not sxy:sxy='0 0'
		swh=self._wh.getvalue()
		if not swh:swh='0 0'
		val= sxy + ' ' + swh
		box=atoft(val)
		x, y = self._boxoff
		box = box[0]+x, box[1]+y, box[2], box[3]
		box=self._scale.layoutbox(box,self._units)
		self.create_box(box)

	# called back by create_box on every change
	# the user can press reset to cancel changes
	def update(self,*box):
		if self._initdialog:
			lc=self.getctrl('base_winoff')
			if not box:
				self._xy.setvalue('')
				self._wh.setvalue('')
			else:	
				box=self._scale.orgbox(box,self._units)
				x, y = self._boxoff
				box = box[0]-x, box[1]-y, box[2], box[3]
				if self._units==UNIT_PXL:prec=0
				elif self._units==UNIT_SCREEN:prec=1
				else: prec=2
				axy=fttoa(box[:2],2,prec)
				awh=fttoa(box[2:],2,prec)
				self._xy.setvalue(axy)
				self._wh.setvalue(awh)

############################
# Base class for media renderers

class Renderer:
	def __init__(self,wnd,rc,baseURL=''):
		self._wnd=wnd
		self._rc=rc
		self._baseURL=baseURL
		self._bgcolor=(0,0,0)

	def urlqual(self,rurl):
		if not rurl:return rurl
		if len(rurl)>5 and rurl[:6]=='file:/': 
			url=rurl
		elif self._baseURL:
			url = self._baseURL + '/' + rurl
		else:
			url=rurl
		return url

	def urlretrieve(self,url):
		if not url:return None
		import MMurl
		try:
			f = MMurl.urlretrieve(url)[0]
		except IOError, arg:
			f=None 
		return f
	
	def isfile(self,f):
		try:list = win32api.FindFiles(f)
		except:return 0
		if not list or len(list) > 1:return 0
		return 1

	def update(self):
		self._wnd.InvalidateRect(self.inflaterc(self._rc))

	# borrow cmifwnd's _prepare_image but make some adjustments
	def adjustSize(self, size, crop = (0,0,0,0), scale = 0, center = 1):
		xsize, ysize = size
		x,y,r,b=self._rc
		width, height=r-x,b-y

		# check for valid crop proportions
		top, bottom, left, right = crop
		if top + bottom >= 1.0 or left + right >= 1.0 or \
		   top < 0 or bottom < 0 or left < 0 or right < 0:
			raise error, 'bad crop size'

		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		rcKeep=left,top,xsize-right,ysize-bottom

		# compute scale taking into account the hint (0,-1)
		if scale == 0:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -1:
			scale = max(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -2:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
			if scale > 1:
				scale = 1

		# scale crop sizes
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)

		mask=None
		w=xsize
		h=ysize
		if scale != 1:
			w = int(xsize * scale + .5)
			h = int(ysize * scale + .5)

		if center:
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
		return left, top, x, y, w - left - right, h - top - bottom, rcKeep

	def inflaterc(self,rc,dl=1,dt=1,dr=1,db=1):
		l,t,r,b=rc
		l=l-dl
		t=t-dt
		r=r+dr
		b=b+db
		return (l,t,r,b)


	# overrides
	def load(self,f):
		pass

	def render(self,dc):
		pass

	def play(self):
		pass

	def pause(self):
		pass

	def stop(self):
		pass

	
###############################
from win32ig import win32ig

class ImageRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._ig=-1
			
	def __del__(self):
		if self._ig>=0:
			win32ig.delete(self._ig)
	
	def load(self,rurl):
		if self._ig>=0:
			win32ig.delete(self._ig)
			self._ig=-1
		if not rurl:
			self.update()
			return

		url=self.urlqual(rurl)
		f=self.urlretrieve(url)
		if not f or not self.isfile(f):
			self.update()
			return
		try:
			self._ig=win32ig.load(f)
		except:
			self._ig=-1
		if self._ig<0:
			print 'failed to load',f
		else:
			self._imgsize=win32ig.size(self._ig)
		self.update()

	def render(self,dc):
		if self._ig<0: return
		src_x, src_y, dest_x, dest_y, width, height,rcKeep = self.adjustSize(self._imgsize[:2])
		win32ig.render(dc.GetSafeHdc(),self._bgcolor,
			None, self._ig, src_x, src_y,dest_x, dest_y, width, height,rcKeep)
		br=Sdk.CreateBrush(win32con.BS_SOLID,0,0)	
		dc.FrameRectFromHandle((dest_x, dest_y, dest_x + width, dest_y+height),br)
		Sdk.DeleteObject(br)

#################################
DirectShowSdk=win32ui.GetDS()

class VideoRenderer(Renderer):
	def __init__(self,wnd,rc,baseURL=''):
		Renderer.__init__(self,wnd,rc,baseURL)
		self._builder=None
	
	def __del__(self):
		self.release()
			
	def release(self):
		if self._builder:
			self._builder.Stop()
			self._builder.Release()
			self._builder=None

	def load(self,rurl):
		self.release()
		try:
			self._builder = DirectShowSdk.CreateGraphBuilder()
		except:
			self._builder=None

		if not self._builder:
			self.update()
			return
		url=self.urlqual(rurl)
		import MMurl,urllib
		url = MMurl.canonURL(url)
		url=urllib.unquote(url)
		if not self._builder.RenderFile(url):
			self.update()
			return
		left,top,width,height=self._builder.GetWindowPosition()
		src_x, src_y, dest_x, dest_y, width, height,rcKeep=\
			self.adjustSize((width,height))
		self._builder.SetWindowPosition((dest_x, dest_y, width, height))
		self._builder.SetWindow(self._wnd,win32con.WM_USER+101)
		self.update()
	

	def play(self):
		if not self._builder: return
		d=self._builder.GetDuration()
		t=self._builder.GetPosition()
		if t>=d:
			self._builder.SetPosition(0)
		self._builder.Run()

	def pause(self):
		if not self._builder: return
		self._builder.Pause()
	def stop(self):
		if not self._builder: return
		self._builder.Stop()


#################################

class PreviewPage(AttrPage):
	def __init__(self,form,mtype='image',aname='file'):
		AttrPage.__init__(self,form)
		self._prevrc=(20,20,DIALOG_WINDOW_WIDTH,DIALOG_WINDOW_HEIGHT)
		self._aname=aname
		if mtype=='video':
			self._renderer=VideoRenderer(self,self._prevrc,self._form._baseURL)
		else:
			self._renderer=ImageRenderer(self,self._prevrc,self._form._baseURL)

	def OnInitDialog(self):
		AttrPage.OnInitDialog(self)
		c=self.getctrl(self._aname)
		rurl=string.strip(c.getvalue())
		self._renderer.load(rurl)

	def OnDestroy(self,params):
		del self._renderer

	def OnSetActive(self):
		self._renderer.play()
		return self._obj_.OnSetActive()

	def OnKillActive(self):
		self._renderer.pause()
		return self._obj_.OnKillActive()

	def drawOn(self,dc):
		self._renderer.render(dc)

	def setvalue(self, attr, val):
		if not self._initdialog: return
		if self._cd.has_key(attr): 
			self._cd[attr].setvalue(val)
		if attr.getname()==self._aname:
			self._renderer.load(string.strip(val))

	def onAttrChange(self):
		if not self._initdialog: return
		c=self.getctrl(self._aname)
		rurl=string.strip(c.getvalue())
		self._renderer.load(rurl)

class ImagePreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self,form,'image')

class VideoPreviewPage(PreviewPage):
	def __init__(self,form):
		PreviewPage.__init__(self,form,'video')	
	
############################

from Attrgrs import attrgrs

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
		for ix in range(len(self._al)):
			a=self._al[ix]
			CtrlCl=self.getctrlclass(a)
			cd[a]=CtrlCl(wnd,a,self.getctrlids(ix+1))
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
	
class StringGroup(AttrGroup):
	def __init__(self,data):
		AttrGroup.__init__(self,data)

	def createctrls(self,wnd):
		cd={}
		for ix in range(len(self._al)):
			a=self._al[ix]
			cd[a]=StringCtrl(wnd,a,self.getctrlids(ix+1))
		return cd

	def getctrlids(self,ix):
		return getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+2)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+3))

	def getpageresid(self):
		return getattr(grinsRC, 'IDD_EDITATTR_S%d' % len(self._al))

	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])

class InfoGroup(StringGroup):
	data=attrgrsdict['infogroup']
	def __init__(self):
		StringGroup.__init__(self,InfoGroup.data)

class UploadGroup(StringGroup):
	data=attrgrsdict['upload_info']
	def __init__(self):
		StringGroup.__init__(self,UploadGroup.data)

class WebserverGroup(StringGroup):
	data=attrgrsdict['webserver']
	def __init__(self):
		StringGroup.__init__(self,WebserverGroup.data)

class MediaserverGroup(StringGroup):
	data=attrgrsdict['mediaserver']
	def __init__(self):
		StringGroup.__init__(self,MediaserverGroup.data)


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

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('base_winoff')
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_14,grinsRC.IDC_15,grinsRC.IDC_16))
		return cd

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

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('base_winoff')
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_14,grinsRC.IDC_15,grinsRC.IDC_16))
		a=self.getattr('units')
		cd[a]=OptionsCtrl(wnd,a,(grinsRC.IDC_21,grinsRC.IDC_22,grinsRC.IDC_23))
		return cd

class SubregionGroup(AttrGroup):
	data=attrgrsdict['subregion']
	def __init__(self):
		AttrGroup.__init__(self,SubregionGroup.data)

	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_LS1O2

	def createctrls(self,wnd):
		cd={}
		a=self.getattr('subregionxy')
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_12,grinsRC.IDC_13,grinsRC.IDC_16))
		a=self.getattr('subregionwh')
		cd[a]=FloatTupleCtrl(wnd,a,(grinsRC.IDC_11,grinsRC.IDC_14,grinsRC.IDC_15,grinsRC.IDC_17))
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
		return grinsRC.IDD_EDITATTR_S1R3S5

	def getctrlids(self,ix):
		ids = getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
			  getattr(grinsRC, 'IDC_%d' % (ix*10+2)), \
			  getattr(grinsRC, 'IDC_%d' % (ix*10+3))
		if ix == 2:
			ids = ids + (getattr(grinsRC, 'IDC_%d' % (ix*10+4)),
						 getattr(grinsRC, 'IDC_%d' % (ix*10+5)))
		return ids

	def getpageclass(self):
		return AttrPage

class NameGroup(AttrGroup):
	data=attrgrsdict['name']
	def __init__(self):
		AttrGroup.__init__(self,NameGroup.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1
	def getctrlids(self,ix):
		return getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+2)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+3))
	def getpageclass(self):
		return AttrPage
	
class CNameGroup(AttrGroup):
	data=attrgrsdict['.cname']
	def __init__(self):
		AttrGroup.__init__(self,CNameGroup.data)
	def getpageresid(self):
		return grinsRC.IDD_EDITATTR_S1O1
	def getctrlids(self,ix):
		return getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+2)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+3))

	def getpageclass(self):
		return AttrPage
		

class DurationGroup(AttrGroup):
	data=attrgrsdict['duration_and_loop']

	def __init__(self,data=None):
		AttrGroup.__init__(self,DurationGroup.data)

	def getctrlids(self,ix):
		return getattr(grinsRC, 'IDC_%d' % (ix*10+1)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+2)), \
			   getattr(grinsRC, 'IDC_%d' % (ix*10+3))

	def getpageresid(self):
		return getattr(grinsRC, 'IDD_EDITATTR_S%d' % len(self._al))
	
	def oninitdialog(self,wnd):
		ctrl=components.Control(wnd,grinsRC.IDC_GROUP1)
		ctrl.attach_to_parent()
		ctrl.settext(self._data['title'])
		

class FileGroup(AttrGroup):
	data=attrgrsdict['file']
	def __init__(self):
		AttrGroup.__init__(self,FileGroup.data)
	def createctrls(self,wnd):
		cd={}
		a=self.getattr('file')
		cd[a]=FileCtrl(wnd,a,(grinsRC.IDC_1,grinsRC.IDC_2,grinsRC.IDC_3,grinsRC.IDC_4))
		return cd

	def canpreview(self):
		a=self.getattr('file')
		f=a.getcurrent()
		import mimetypes
		mtype = mimetypes.guess_type(f)[0]
		if mtype is None: return 0
		mtype, subtype = string.split(mtype, '/')
		if mtype=='image':can=1
		# we can preview videos but what about big videos? 
		# we should let the user select using a preview button.
		elif mtype=='video':can=1 
		else: can=0
		self._mtype=mtype
		return can

	def getpageresid(self):
		if self.canpreview():
			return getattr(grinsRC, 'IDD_EDITATTR_PF1')
		else:
			return getattr(grinsRC, 'IDD_EDITATTR_F1')

	def getpageclass(self):
		if not self.canpreview():
			return AttrPage
		if self._mtype=='image':
			return ImagePreviewPage
		elif self._mtype=='video':
			return VideoPreviewPage
		else:
			raise error,'see AttrEditForm.FileGroup'

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
	'upload_info':UploadGroup,
	'webserver':WebserverGroup,
	'mediaserver':MediaserverGroup,
	'file':FileGroup,
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
		self._tid=None

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

	# XXX: either the help string (default value for units) must be corrected 
	#      or the attrdict.get calls in Channel.py and LayoutView.py and here
	def getunits(self,ch=None):
		if not ch:
			return self._channel.attrdict.get('units',appcon.UNIT_SCREEN)
		else:
			return ch.attrdict.get('units',appcon.UNIT_SCREEN)
			
	def buildcontext(self):
		self._channels={}
		self._channels_rc={}

		self._winsize=None
		self._layoutch=None
		
		a=self._attriblist[0]
		channels = a.wrapper.toplevel.root.context.channels
		self._baseURL=a.wrapper.toplevel.dirname
		for ch in channels:
			self._channels[ch.name]=ch
			units=self.getunits(ch)
			t=ch.attrdict['type']
			if t=='layout' and ch.attrdict.has_key('winsize'):
				w,h=ch.attrdict['winsize']
				self._winsize=(w,h)
				self._channels_rc[ch.name]=((0,0,w,h),units)
				self._layoutch=ch
			elif ch.attrdict.has_key('base_winoff'):
				self._channels_rc[ch.name]=(ch.attrdict['base_winoff'],units)
			else:
				self._channels_rc[ch.name]=((0,0,0,0),0)
			
		if hasattr(a.wrapper,'node'):
			self._node=a.wrapper.node
			chname=self.getchannel(self._node)
			self._channel=self._channels[chname]
		else:
			self._node=None		

		if hasattr(a.wrapper,'channel'):
			self._channel=a.wrapper.channel

	
	def getchannel(self,node):
		if node.attrdict.has_key('channel'):
			return node.attrdict['channel']
		while node.parent:
			node=node.parent
			if node.attrdict.has_key('channel'):
				return node.attrdict['channel']
		return self._layoutch.name

	def GetBBox(self):
		if self._node:
			return self._channels_rc[self._channel.name]
		else:
			bw=self._channel.attrdict['base_window']
			return self._channels_rc[bw]

	def GetCBox(self):
		bw=self._channel.attrdict['base_window']
		return self._channels_rc[bw]
					
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

		# patch core's draw back
		if not self._tid:
			import __main__
			self._tid=__main__.toplevel.settimer(0.5,(self.onDirty,()))

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

	def onDirty(self):
		self._tid=None
		self.buildcontext()

	def OnDestroy(self,params):
		if self._tid:
			import __main__
			__main__.toplevel.canceltimer(self._tid)
		
import settings
if settings.get('use_tab_attr_editor'):
	AttrEditForm=AttrEditFormNew
