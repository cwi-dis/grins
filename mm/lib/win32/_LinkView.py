import win32ui,win32con
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()
import win32mu,wc

import grinsRC,win32menu
import components
import usercmd

from pywin.mfc import window,object,docview
import afxres,commctrl

class ControlsDict:
	def __init__(self):
		self._subwindows={}	
	def __nonzero__(self):return 1
	def __len__(self): return len(self._subwindows)
	def __getitem__(self, key): return self._subwindows[key]
	def __setitem__(self, key, item): self._subwindows[key] = item
	def keys(self): return self._subwindows.keys()
	def items(self): return self._subwindows.items()
	def values(self): return self._subwindows.values()
	def has_key(self, key): return self._subwindows.has_key(key)

class FormViewBase(docview.FormView,ControlsDict):
	def __init__(self,doc,id):
		docview.FormView.__init__(self,doc,id)
		ControlsDict.__init__(self)
		self._close_cmd_list=[]

	def createWindow(self,parent):
		self.CreateWindow(parent)
		self.attach_handles_to_subwindows()

	def OnInitialUpdate(self):
		self._mdiframe=(self.GetParent()).GetMDIFrame()

	def onActivate(self,f):
		if f:self._mdiframe.set_commandlist(self._close_cmd_list)
		else:self._mdiframe.set_commandlist(None)

	def is_oswindow(self):
		return (hasattr(self,'GetSafeHwnd') and self.GetSafeHwnd())

	def OnClose(self):
		if self._closecmdid>0:
			self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND,self._closecmdid)
		else:
			self.GetParent().DestroyWindow()

	# called directly from cmif-core
	# to close window
	def close(self):
		# 1. clean self contends
		# self._close()

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()

	def GetUserCmdId(self,cmdcl):
		if hasattr(self,'GetParent'):
			return self.GetParent().GetUserCmdId(cmdcl)
		return -1

	# the close sequence must be delegated to parent
	def set_commandlist(self,commandlist):
		contextcmds=self._activecmds
		for id in contextcmds.keys():
			cmd=contextcmds[id]
			usercmd_ui = self._class2ui[cmd.__class__]
			usercmd_ui.enable(0)
		contextcmds.clear()
		self._close_cmd_list=[]
		if not commandlist: return
		for cmd in commandlist:
			usercmd_ui = self._class2ui[cmd.__class__]
			id=usercmd_ui._id
			usercmd_ui.enable(1)
			contextcmds[id]=cmd
			if cmd.__class__==usercmd.CLOSE_WINDOW:
				self._close_cmd_list.append(cmd)
		self._mdiframe.set_commandlist(self._close_cmd_list)

	def show(self):
		pass

	def is_showing(self):
		if not self._obj_: return 0
		return self.GetSafeHwnd()

	def hide(self):
		pass

	def setcursor(self, cursor):
		if cursor == self._cursor:
			return
		win32mu.SetCursor(cursor)
		self._cursor = cursor


	# delegate to parent for cmds and adorment functionality
	def set_dynamiclist(self, cmd, list):
		self._parent.set_dynamiclist(cmd,list)
	def set_adornments(self, adornments):
		self._parent.set_adornments(adornments)
	def set_toggle(self, command, onoff):
		self._parent.set_toggle(command,onoff)
		
	def set_commandlist(self, list):
		self._parent.set_commandlist(list,self._strid)
	def settitle(self,title):
		self._parent.settitle(title,self._strid)


class DlgBar(window.Wnd,ControlsDict):
	AFX_IDW_DIALOGBAR=0xE805
	def __init__(self):
		AFX_IDW_DIALOGBAR=0xE805
		window.Wnd.__init__(self,win32ui.CreateDialogBar())
		ControlsDict.__init__(self)
	def create(self,frame,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		self._obj_.CreateWindow(frame,resid,
			align,self.AFX_IDW_DIALOGBAR)

class OkCancelDlgBar(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
		self['OK']=components.Button(self,win32con.IDOK)
		self['Cancel']=components.Button(self,win32con.IDCANCEL)
	def create(self,frame,cmdtgt):
		DlgBar.create(self,frame,grinsRC.IDD_OKCANCELBARV,afxres.CBRS_ALIGN_RIGHT)
		for i in self.keys():
			frame.HookCommand(cmdtgt.onBarCmd,self[i]._id)
			self[i].attach_to_parent()

class _LinkView(FormViewBase):
	def __init__(self,doc):
		FormViewBase.__init__(self,doc,grinsRC.IDD_LINKS)
		self['LeftList']=components.ListBox(self,grinsRC.IDC_LIST1)
		self['RightList']=components.ListBox(self,grinsRC.IDC_LIST2)
		self['LinkList']=components.ListBox(self,grinsRC.IDC_LIST_LINKS)

		self['LeftPushFocus']=components.Button(self,grinsRC.IDC_PUSH_FOCUS1)
		self['RightPushFocus']=components.Button(self,grinsRC.IDC_PUSH_FOCUS2)

		self['LeftAnchorEd']=components.Button(self,grinsRC.IDC_ANCHOR_EDITOR1)
		self['RightAnchorEd']=components.Button(self,grinsRC.IDC_ANCHOR_EDITOR2)

		self['AddLink']=components.Button(self,grinsRC.IDC_ADD_LINK)
		self['EditLink']=components.Button(self,grinsRC.IDC_EDIT_LINK)
		self['DeleteLink']=components.Button(self,grinsRC.IDC_DELETE_LINK)

		self['LeftLabel']=components.Static(self,grinsRC.IDC_STATIC_LEFT)
		self['RightLabel']=components.Static(self,grinsRC.IDC_STATIC_RIGHT)

		self['D0']=components.RadioButton(self,grinsRC.IDC_RADIO1)
		self['D1']=components.RadioButton(self,grinsRC.IDC_RADIO2)
		self['D2']=components.RadioButton(self,grinsRC.IDC_RADIO3)

		self['T0']=components.RadioButton(self,grinsRC.IDC_RADIO4)
		self['T1']=components.RadioButton(self,grinsRC.IDC_RADIO5)
		self['T2']=components.RadioButton(self,grinsRC.IDC_RADIO6)
	
		self['LeftMenu']=components.Button(self,grinsRC.IDC_LEFT_MENU)
		self['RightMenu']=components.Button(self,grinsRC.IDC_RIGHT_MENU)
	
		# cash lists  
		self._lists_ids=(self['LeftList']._id,self['RightList']._id,self['LinkList']._id)
		self._dirs=(self['D0']._id,self['D1']._id,self['D2']._id)
		self._types=(self['T0']._id,self['T1']._id,self['T2']._id)

		self['OK']=components.Button(self,win32con.IDOK)
		self['Cancel']=components.Button(self,win32con.IDCANCEL)

	def createWindow(self,parent):
		self._parent=parent
		self.CreateWindow(parent)
		for ck in self.keys():
			self[ck].attach_to_parent()
		self.HookMessage(self.onCmd,win32con.WM_COMMAND)

	def OnInitialUpdate(self):
		frame=self.GetParent()
		self._mdiframe=frame.GetMDIFrame()
		#self._stdDlgBar=OkCancelDlgBar()
		#self._stdDlgBar.create(frame,self)# pass self as cmdtarget
		frame.RecalcLayout()

		# predent that they are ours
		#self['OK']=self._stdDlgBar['OK']
		#self['Cancel']=self._stdDlgBar['Cancel']
		
		# temp patch
		closecmd=usercmd.CLOSE_WINDOW(callback = (self.close_window_callback,()))
		self._close_cmd_list.append(closecmd)
		self.onActivate(1)

	def close_window_callback(self):
		self._mdiframe.SendMessage(win32con.WM_COMMAND,self.GetUserCmdId(usercmd.LINKVIEW))

	def call(self,strcmd):
		if strcmd in self._callbacks.keys():
			apply(apply,self._callbacks[strcmd])


	def onCmd(self,params):
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		if id in self._mcb.keys():
			self.menu_callback(id,0)
			return
		for key in self.keys():
			if id==self[key]._id:
				if id in self._lists_ids:
					if nmsg==win32con.LBN_SELCHANGE:self.call(key)
				elif id in self._dirs:
					self.call('LinkDir')
				elif id in self._types:
					self.call('LinkType')
				else:
					self.call(key)
				break

	def on_menu(self,menu,str):
		lc,tc,rc,bc=self[str].getwindowrect()
		menu.TrackPopupMenu((rc,tc),
			win32con.TPM_LEFTALIGN|win32con.TPM_LEFTBUTTON,self) 
	def menu_callback(self,id,code):
		if id in self._mcb.keys(): 
			apply(apply,self._mcb[id])

	# called directly from cmif-core
	# to close window
	def close(self):
		# 1. clean self contends
		del self._leftmenu
		del self._rightmenu

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()

	# must return 1 if self is an os window
	def is_showing(self):
		if not hasattr(self,'GetSafeHwnd'):
			return 0
		return self.GetSafeHwnd()

	def show(self):
		if hasattr(self,'GetSafeHwnd'):
			if self.GetSafeHwnd():
				self.GetParent().GetMDIFrame().MDIActivate(self.GetParent())

	def hide(self):
		self.close()

		
	#########################################
	def do_init(self, title, dirstr, typestr, menu1, cbarg1, menu2, cbarg2, adornments):
		self._title=title

		# hard res-coded values
		# ignore dirstr <- -> <->
		# ignore typestr

		# menu callbacks dict
		self._mcb={}
		self._mid=grinsRC._APS_NEXT_RESOURCE_VALUE
		
		self._leftmenu=self.create_menu(menu1)
		self._left_data = cbarg1

		self._rightmenu=self.create_menu(menu2)
		self._right_data = cbarg2
		
		self._callbacks=adornments['callbacks']

		# add callbacks for show menu buttons
		self._callbacks['LeftMenu']=(self.on_menu,(self._leftmenu,'LeftMenu'))
		self._callbacks['RightMenu']=(self.on_menu,(self._rightmenu,'RightMenu'))

	# create a menu from a list of pairs (str,callback)
	def create_menu(self,mcl):
		list=[]
		for item in mcl:
			list.append((0,item[0],None,self._mid))
			self._mcb[self._mid]=item[1]
			self._mid=self._mid+1
		menu=win32menu.Menu('popup')
		menu.create_from_menu_spec_list(list)
		return menu

	# Interface to the left list and associated buttons.
	def lefthide(self):
		"""Hide the left list with associated buttons."""
		self['LeftList'].enable(0)
		self['LeftPushFocus'].enable(0) 
		self['LeftAnchorEd'].enable(0) 

	def leftshow(self):
		"""Show the left list with associated buttons."""
		self['LeftList'].enable(1)
		self['LeftPushFocus'].enable(1) 
		self['LeftAnchorEd'].enable(1) 

	def leftsetlabel(self, label):
		"""Set the label for the left list.

		Arguments (no defaults):
		label -- string -- the label to be displayed
		"""
		self['LeftLabel'].settext(label)

	def leftdellistitems(self, poslist):
		"""Delete items from left list.

		Arguments (no defaults):
		poslist -- list of integers -- the indices of the
			items to be deleted
		"""
		poslist = poslist[:]
		poslist.sort()
		poslist.reverse()
		l=self['LeftList']
		for pos in poslist:
			l.deletestring(pos)

	def leftdelalllistitems(self):
		"""Delete all items from the left list."""
		self['LeftList'].resetcontent()

	def leftaddlistitems(self, items, pos):
		"""Add items to the left list.

		Arguments (no defaults):
		items -- list of strings -- the items to be added
		pos -- integer -- the index of the item before which
			the items are to be added (-1: add at end)
		"""
		self['LeftList'].addlistitems(items, pos)

	def leftreplacelistitem(self, pos, newitem):
		"""Replace an item in the left list.

		Arguments (no defaults):
		pos -- the index of the item to be replaced
		newitem -- string -- the new item
		"""
		self['LeftList'].replace(pos, newitem)
		
	def leftselectitem(self, pos):
		"""Select an item in the left list.

		Arguments (no defaults):
		pos -- integer -- the index of the item to be selected
		"""
		self['LeftList'].setcursel(pos)

	def leftgetselected(self):
		"""Return the index of the currently selected item or None."""
		return self['LeftList'].getcursel()

	def leftgetlist(self):
		"""Return the left list as a list of strings."""
		return self['LeftList'].getlist()

	def leftmakevisible(self, pos):
		"""Maybe scroll list to make an item visible.

		Arguments (no defaults):
		pos -- index of item to be made visible.
		"""
		pass
		
	def leftbuttonssetsensitive(self, sensitive):
		"""Make the left buttons (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['LeftPushFocus'].enable(sensitive) 
		self['LeftAnchorEd'].enable(sensitive) 

	# Interface to the right list and associated buttons.
	def righthide(self):
		"""Hide the right list with associated buttons."""
		self['RightList'].enable(0)
		self['RightPushFocus'].enable(0) 
		self['RightAnchorEd'].enable(0) 

	def rightshow(self):
		"""Show the right list with associated buttons."""
		self['RightList'].enable(1)
		self['RightPushFocus'].enable(1) 
		self['RightAnchorEd'].enable(1) 

	def rightsetlabel(self, label):
		"""Set the label for the right list.

		Arguments (no defaults):
		label -- string -- the label to be displayed
		"""
		self['RightLabel'].settext(label)

	def rightdellistitems(self, poslist):
		"""Delete items from right list.

		Arguments (no defaults):
		poslist -- list of integers -- the indices of the
			items to be deleted
		"""
		poslist = poslist[:]
		poslist.sort()
		poslist.reverse()
		for pos in poslist:
			self['RightList'].deletestring(pos)

	def rightdelalllistitems(self):
		"""Delete all items from the right list."""
		self['RightList'].resetcontent()

	def rightaddlistitems(self, items, pos):
		"""Add items to the right list.

		Arguments (no defaults):
		items -- list of strings -- the items to be added
		pos -- integer -- the index of the item before which
			the items are to be added (-1: add at end)
		"""
		self['RightList'].addlistitems(items,pos)

	def rightreplacelistitem(self, pos, newitem):
		"""Replace an item in the right list.

		Arguments (no defaults):
		pos -- the index of the item to be replaced
		newitem -- string -- the new item
		"""
		self['RightList'].replace(pos, newitem)
		
	def rightselectitem(self, pos):
		"""Select an item in the right list.

		Arguments (no defaults):
		pos -- integer -- the index of the item to be selected
		"""
		self['RightList'].setcursel(pos)

	def rightgetselected(self):
		"""Return the index of the currently selected item or None."""
		return self['RightList'].getcursel()

	def rightgetlist(self):
		"""Return the right list as a list of strings."""
		return self['RightList'].getlist()

	def rightmakevisible(self, pos):
		"""Maybe scroll list to make an item visible.

		Arguments (no defaults):
		pos -- index of item to be made visible.
		"""
		pass

	def rightbuttonssetsensitive(self, sensitive):
		"""Make the right buttons (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['RightPushFocus'].enable(sensitive) 
		self['RightAnchorEd'].enable(sensitive) 

	# Interface to the middle list and associated buttons.
	def middlehide(self):
		"""Hide the middle list with associated buttons."""
		self['LinkList'].enable(0) 
		self['AddLink'].enable(0) 
		self['EditLink'].enable(0) 
		self['DeleteLink'].enable(0) 
		for i in range(3):
			self['D%d'%i].enable(0)
			self['T%d'%i].enable(0)

	def middleshow(self):
		"""Show the middle list with associated buttons."""
		self['LinkList'].enable(1) 
		self['AddLink'].enable(1) 
		self['EditLink'].enable(1) 
		self['DeleteLink'].enable(1) 
		for i in range(3):
			self['D%d'%i].enable(1)
			self['T%d'%i].enable(1)

	def middledelalllistitems(self):
		"""Delete all items from the middle list."""
		self['LinkList'].resetcontent()

	def middleaddlistitems(self, items, pos):
		"""Add items to the middle list.

		Arguments (no defaults):
		items -- list of strings -- the items to be added
		pos -- integer -- the index of the item before which
			the items are to be added (-1: add at end)
		"""
		self['LinkList'].addlistitems(items,pos)

	def middleselectitem(self, pos):
		"""Select an item in the middle list.

		Arguments (no defaults):
		pos -- integer -- the index of the item to be selected
		"""
		self['LinkList'].setcursel(pos)

	def middlegetselected(self):
		"""Return the index of the currently selected item or None."""
		return self['LinkList'].getcursel()

	def middlemakevisible(self, pos):
		"""Maybe scroll list to make an item visible.

		Arguments (no defaults):
		pos -- index of item to be made visible.
		"""
		pass

	def addsetsensitive(self, sensitive):
		"""Make the Add button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['AddLink'].enable(sensitive) 

	def editsetsensitive(self, sensitive):
		"""Make the Edit button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['EditLink'].enable(sensitive) 

	def deletesetsensitive(self, sensitive):
		"""Make the Delete button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['DeleteLink'].enable(sensitive) 

	# Interface to the edit group.
	def editgrouphide(self):
		"""Hide the edit group."""
		pass 

	def editgroupshow(self):
		"""Show the edit group."""
		pass 

	def oksetsensitive(self, sensitive):
		"""Make the OK button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['OK'].enable(sensitive) 

	def cancelsetsensitive(self, sensitive):
		"""Make the Cancel button (in)sensitive.

		Arguments (no defaults):
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		self['Cancel'].enable(sensitive) 

	def linkdirsetsensitive(self, pos, sensitive):
		"""Make an entry in the link dir menu (in)sensitive.

		Arguments (no defaults):
		pos -- the index of the entry to be made (in)sensitve
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		name='D%d'%pos
		self[name].enable(sensitive)

	def linkdirsetchoice(self, choice):
		"""Set the current choice of the link dir list.

		Arguments (no defaults):
		choice -- index of the new choice
		"""
		for i in range(3):
			name='D%d'%i
			if i == choice:
				self[name].setcheck(1)
			else:
				self[name].setcheck(0)

	def linkdirgetchoice(self):
		"""Return the current choice in the link dir list."""
		for i in range(3):
			name='D%d'%i
			if self[name].getcheck():
				return i
		raise 'No direction set?'

	def linktypesetsensitive(self, pos, sensitive):
		"""Make an entry in the link type menu (in)sensitive.

		Arguments (no defaults):
		pos -- the index of the entry to be made (in)sensitve
		sensitive -- boolean indicating whether to make
			sensitive or insensitive
		"""
		pass 

	def linktypesetchoice(self, choice):
		"""Set the current choice of the link type list.

		Arguments (no defaults):
		choice -- index of the new choice
		"""
		for i in range(3):
			name='T%d'%i
			if self[name].getcheck():
				return i
		raise 'No direction set?'

	def linktypegetchoice(self):
		"""Return the current choice in the link type list."""
		for i in range(3):
			name='D%d'%i
			if self[name].getcheck():
				return i
		raise 'No type set?'
