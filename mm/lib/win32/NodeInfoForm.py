# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl

# GRiNS resource ids
import grinsRC

class ControlsDict:
	def __init__(self):
		self._subwnddict={}	
	def __nonzero__(self):return 1
	def __len__(self): return len(self._subwnddict)
	def __getitem__(self, key): return self._subwnddict[key]
	def __setitem__(self, key, item): self._subwnddict[key] = item
	def keys(self): return self._subwnddict.keys()
	def items(self): return self._subwnddict.items()
	def values(self): return self._subwnddict.values()
	def has_key(self, key): return self._subwnddict.has_key(key)

class DlgBar(window.Wnd,ControlsDict):
	AFX_IDW_DIALOGBAR=0xE805
	def __init__(self):
		ControlsDict.__init__(self)
		AFX_IDW_DIALOGBAR=0xE805
		window.Wnd.__init__(self,win32ui.CreateDialogBar())
	def create(self,frame,resid,align=afxres.CBRS_ALIGN_BOTTOM):
		self._obj_.CreateWindow(frame,resid,
			align,self.AFX_IDW_DIALOGBAR)
	def show(self):
		self.ShowWindow(win32con.SW_SHOW)
	def hide(self):
		self.ShowWindow(win32con.SW_HIDE)
	def set_cbd(self,cbd):
		self._cbd=cbd

class NodeInfoDlgBar(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
	def create(self,parent,cbd=None):
		DlgBar.create(self,parent,grinsRC.IDD_NODE_INFO_BAR,afxres.CBRS_ALIGN_TOP)
		self['Name']=components.Edit(self,grinsRC.IDC_NODE_NAME)
		self['Type']=components.ComboBox(self,grinsRC.IDC_NODE_TYPE)
		self['Channel']=components.ComboBox(self,grinsRC.IDC_CHANNEL)		
		for i in self.keys():self[i].attach_to_parent()
		parent.HookCommand(self.OnName,self['Name']._id)
		parent.HookCommand(self.OnType,self['Type']._id)
		parent.HookCommand(self.OnChannel,self['Channel']._id)
		self._cbd=cbd
	def call(self,cbid):
		if self._cbd and cbid in self._cbd.keys():
			apply(apply,self._cbd[cbid])
	def OnName(self,id,code):
		if code==win32con.EN_CHANGE:self.call('Name')
	def OnType(self,id,code):
		if code==win32con.CBN_SELCHANGE:self.call('Type')
	def OnChannel(self,id,code):
		if code==win32con.CBN_SELCHANGE :self.call('Channel')
			

class StdDlgBar(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
	def create(self, parent,cbd=None):
		DlgBar.create(self,parent,grinsRC.IDD_NODE_INFO_CMDBAR,afxres.CBRS_ALIGN_TOP)
		self['Cancel']=components.Button(self,grinsRC.IDUC_CANCEL)
		self['Restore']=components.Button(self,grinsRC.IDUC_RESTORE)
		self['ChanAttr']=components.Button(self,grinsRC.IDUC_ATTRIBUTES)
		self['Anchors']=components.Button(self,grinsRC.IDUC_ANCHORS)
		self['Apply']=components.Button(self,grinsRC.IDUC_APPLY)
		self['OK']=components.Button(self,grinsRC.IDUC_OK)
		self._cbd=cbd
		for i in self.keys():
			parent.HookCommand(self.onCmd,self[i]._id)
			self[i].attach_to_parent()
	def call(self,k):
		d=self._cbd
		if d and k in d.keys() and d[k]:
			apply(apply,d[k])
	def onCmd(self,id,code):
		for i in self.keys():
			if id==self[i]._id:
				self.call(i)
	def enable(self,strid,f):
		self[strid].enable(f)
							


class ImmGroup(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
		self._edit=components.Edit(self,grinsRC.IDC_IMM_EDIT)
		self._support={'settext':self.settext,'gettext':self.gettext,'gettextlines':self.gettextlines}
	def create(self, parent,cbd=None):
		DlgBar.create(self,parent,grinsRC.IDD_IMM_GROUP,afxres.CBRS_ALIGN_TOP)
		self._edit.attach_to_parent()
		self._cbd=cbd

	# Interface to the immediate part.  This part consists of an
	# editable text area.  There are no callbacks.
	def settext(self, immtext):
		"""Set the current text.

		Arguments (no defaults):
		immtext -- list of strings or a single string with
			embedded linefeeds
		"""
		if not immtext:immtext=''
		if type(immtext)==type([]):
			str=immtext[0]
			for i in range(1,len(immtext)):
				str=str+'\r\n'+immtext[i]
			self._edit.settext(str)
		else:
			self._edit.settext(immtext)

	def gettext(self):
		"""Return the current text as one string."""
		str= self._edit.gettext()

	def gettextlines(self):
		"""Return the current text as a list of strings."""
		return self._edit.getlines()


class ExtGroup(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
		self._edit=components.Edit(self,grinsRC.IDC_EXT_EDIT)
		self._browse=components.Button(self,grinsRC.IDUC_BROWSE)
		self._call_ed=components.Button(self,grinsRC.IDUC_EDIT)
		self._support={'setfilename':self.setfilename,'getfilename':self.getfilename}
	def create(self, parent,cbd=None):
		DlgBar.create(self,parent,grinsRC.IDD_EXT_GROUP,afxres.CBRS_ALIGN_TOP)
		self._edit.attach_to_parent()
		self._browse.attach_to_parent()
		self._call_ed.attach_to_parent()
		parent.HookCommand(self.OnBrowse,self._browse._id)
		parent.HookCommand(self.OnCallEditor,self._call_ed._id)
		self._cbd=cbd
	def OnBrowse(self,id,code):
		if self._cbd and 'Browse' in self._cbd.keys():
			apply(apply,self._cbd['Browse'])
	def OnCallEditor(self,id,code):
		if self._cbd and 'CallEditor' in self._cbd.keys():
			apply(apply,self._cbd['CallEditor'])
		
	# Interface to the external part.  This part consists of a
	# text field with a URL (with or without the protocol, and if
	# without protocol, absolute or relative) and a `Browser...'
	# button which triggers a callback function.
	def setfilename(self, filename):
		"""Set the value of the filename (URL).

		Arguments (no defaults):
		filename -- string giving the URL
		"""
		self._edit.settext(filename)

	def getfilename(self):
		"""Return the value of the filename text field."""
		return self._edit.gettext()


class IntGroup(DlgBar):
	def __init__(self):
		DlgBar.__init__(self)
		self._list=components.ListBox(self,grinsRC.IDC_INT_LIST)
		self._open=components.Button(self,grinsRC.IDC_OPENCHILD)
		self._support={'setchildren':self.setchildren,'getchild':self.getchild}
	def create(self, parent,cbd=None):
		DlgBar.create(self,parent,grinsRC.IDD_INT_GROUP,afxres.CBRS_ALIGN_TOP)
		self._list.attach_to_parent()
		self._open.attach_to_parent()
		parent.HookCommand(self.OnOpenChild,self._open._id)
		self._cbd=cbd
	def OnOpenChild(self,id,code):
		if self._cbd and 'OpenChild' in self._cbd.keys():
			apply(apply,self._cbd['OpenChild'])

	# Interface to the interior part.  This part consists of a
	# list of strings and an interface to select one item in the
	# list.
	def setchildren(self, children, initchild=None):
		"""Set the list of children.

		Arguments (no defaults):
		children -- list of strings
		initchild -- 0 <= initchild < len(children) or None --
			the initial selection (no selection igf None)
		"""
		self._list.resetcontent()
		if children:
			self._list.addlistitems(children, -1)
			if initchild:
				self._list.setcursel(initchild)

	def getchild(self):
		"""Return the index of the current selection or None."""
		return self._list.getcursel()

				
					
class FormViewBase(docview.FormView,ControlsDict):
	def __init__(self,doc,id):
		docview.FormView.__init__(self,doc,id)
		ControlsDict.__init__(self)
				
class NodeInfoForm(FormViewBase):
	def __init__(self,doc):
		FormViewBase.__init__(self,doc,grinsRC.IDD_FORM)
		self._title='NodeInfo Editor'
		self._nodeinfo=NodeInfoDlgBar()
		self._cmdbar=StdDlgBar()
		self._ext_group=ExtGroup()
		self._imm_group=ImmGroup()
		self._int_group=IntGroup()
		self._cur_group=None

		# predent we own groups methods
		for entry in self._imm_group._support.keys():
			self.__dict__[entry]= self._imm_group._support[entry]
		for entry in self._int_group._support.keys():
			self.__dict__[entry]= self._int_group._support[entry]
		for entry in self._ext_group._support.keys():
			self.__dict__[entry]= self._ext_group._support[entry]		

	def OnInitialUpdate(self):
		frame=self.GetParent()
		self._nodeinfo.create(frame)
		self._cmdbar.create(frame)
		self._ext_group.create(frame)
		self._imm_group.create(frame)
		self._int_group.create(frame)


	def fitbars(self):
		if not self._nodeinfo or not self._cmdbar or not self._cur_group: return
		rc1=win32mu.Rect(self._nodeinfo.GetWindowRect())
		rc2=win32mu.Rect(self._cmdbar.GetWindowRect())
		rc3=win32mu.Rect(self._cur_group.GetWindowRect())
		from sysmetrics import cycaption,cyborder
		h=rc1.height()+rc2.height()+rc3.height()+cycaption+2*cyborder+ cycaption/2
		w=rc1.width()
		if rc2.width()>w:w=rc2.width()
		if rc3.width()>w:w=rc3.width()
		flags=win32con.SWP_NOZORDER|win32con.SWP_NOACTIVATE|win32con.SWP_NOMOVE
		self.GetParent().SetWindowPos(0, (0,0,w,h),flags)
		#self.GetParent().RecalcLayout()

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
		self.ShowWindow(win32con.SW_SHOW)
		self.pop() 

	def pop(self):
		if not hasattr(self,'GetParent'):return
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

	def do_init(self, title, channelnames, initchannel, types, inittype,
		     name, filename, children, immtext, adornments):
		"""Create the NodeInfo dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) and pop it up (i.e. display it on the
		screen).

		Arguments (no defaults):
		title -- string to be displayed as window title
		channelnames -- list of strings, one of which is
			always selected
		initchannel -- 0 <= initchannel < len(channelnames) --
			the initial selection of the channelnames
		types -- list of strings, one of which is always
			selected
		inittype -- 0 <= inittype < len(types) -- the initial
			selection of the types
		name -- string, the initial value for the name field
		filename -- string, the initial value for the file
			name field, to be displayed as the file name
			in the exterior part
		children -- list of strings -- the list of strings to
			be displayed in the interior part
		immtext -- list of strings or a single string with
			embedded linefeeds -- the text to be displayed
			in the immediate part
		"""
		self._cbdict=adornments['callbacks']
		# gen node info 
		self._title=title
		self._channelnames=channelnames
		self._initchannel=initchannel
		self._types=types
		self._inittype=inittype
		self._name=name

		# spec data 
		self._immtext=immtext
		self._children=children
		self._filename=filename


	def setdata(self):	
		self.settitle(self._title)
		self.setchannelnames(self._channelnames,self._initchannel)
		self.settypes(self._types,self._inittype)
		if self._name: self.setname(self._name)
		if self._immtext:
			self._imm_group.settext(self._immtext)
		elif self._children:
			self._int_group.setchildren(self._children)
		elif self._filename:
			self._ext_group.setfilename(self._filename)
		
	def enable_cbs(self):
		self._nodeinfo.set_cbd(self._cbdict)
		self._cmdbar.set_cbd(self._cbdict)
		self._ext_group.set_cbd(self._cbdict)
		self._imm_group.set_cbd(self._cbdict)
		self._int_group.set_cbd(self._cbdict)

	# Interface to the list of channel names.  This part consists
	# of a label and a list of strings of which one is always the
	# current selection.  Only one element of the list needs to be
	# visible (the current selection) but it must be possible to
	# choose from the list.
	def setchannelnames(self, channelnames, initchannel):
		"""Set the list of strings and the initial selection.

		Arguments (no defaults):
		channelnames -- list of strings
		initchannel -- 0 <= initchannel < len(channelnames) --
			the initial selection
		"""
		self._nodeinfo['Channel'].initoptions(channelnames, initchannel)

	def getchannelname(self):
		"""Get the string which is the current selection."""
		return self._nodeinfo['Channel'].getvalue()


	# Interface to the list of node types.  This part consists of
	# a label and a list of strings of which one is always the
	# current selection.  Only one element of the list needs to be
	# visible (the current selection) but it must be possible to
	# choose from the list.
	def settypes(self, types, inittype):
		"""Set the list of strings and the initial selection.

		Arguments (no defaults):
		types -- list of strings
		inittype -- 0 <= inittype < len(types) -- the initial
			selection
		"""
		self._nodeinfo['Type'].initoptions(types, inittype)

	def gettype(self):
		"""Get the string which is the current selection."""
		return self._nodeinfo['Type'].getvalue()

	def settype(self, inittype):
		"""Set the current selection.

		Arguments (no defaults):
		inittype -- 0 <= inittype < len(types) -- the new
			current selection
		"""
		self._nodeinfo['Type'].setpos(inittype)

	# Interface to the name field.  This part consists of an
	# editable text field.
	def setname(self, name):
		"""Set the value of the name field.

		Arguments (no defaults):
		name -- string
		"""
		self._nodeinfo['Name'].settext(name)

	def getname(self):
		"""Return the current value of the name field."""
		return self._nodeinfo['Name'].gettext()

	# The following methods choose between the three variable
	# parts.  One of the parts is active (the others need not be
	# shown), and when one of the parts is made the active part,
	# the others are automatically made inactive (possibly
	# hidden).
	# In Motif, this is done by using the same screen area for the
	# three parts.

	def imm_group_show(self):
		"""Make the immediate part visible."""
		frame=self.GetParent()
		frame.LockWindowUpdate()
		if not self._imm_group.IsWindowVisible():
			self._imm_group.show()
		if self._int_group.IsWindowVisible():
			self._int_group.hide()
		if self._ext_group.IsWindowVisible():
			self._ext_group.hide()
		self._cur_group=self._imm_group
		self.fitbars()
		frame.UnlockWindowUpdate()

	def int_group_show(self):
		"""Make the interior part visible."""
		frame=self.GetParent()
		frame.LockWindowUpdate()
		if not self._int_group.IsWindowVisible():
			self._int_group.show()
		if self._ext_group.IsWindowVisible():
			self._ext_group.hide()
		if self._imm_group.IsWindowVisible():
			self._imm_group.hide()
		self._cur_group=self._int_group
		self.fitbars()
		frame.UnlockWindowUpdate()
		
	def ext_group_show(self):
		"""Make the external part visible."""
		frame=self.GetParent()
		frame.LockWindowUpdate()
		if not self._ext_group.IsWindowVisible():
			self._ext_group.show()
		if self._int_group.IsWindowVisible():
			self._int_group.hide()
		if self._imm_group.IsWindowVisible():
			self._imm_group.hide()
		self._cur_group=self._ext_group
		self.fitbars()
		frame.UnlockWindowUpdate()

