__version__ = "$Id$"

# std win32 modules
import win32ui,win32con,win32api

# win32 lib modules
import win32mu,components
import sysmetrics

# std mfc windows stuf
from pywin.mfc import window,object,docview,dialog

# GRiNS resource ids
import grinsRC

# General libs
import string


""" @win32doc|NodeInfoForm
Implements the NodeInfo dialog for the win32 platform according to the specifications
represented by the interface class NodeInfoDialog in editor/win32/NodeInfoDialog.py
"""

from GenFormView import GenFormView

class NodeInfoForm(GenFormView):
	# Class constructor. Calls base class constructor and initializes members
	def __init__(self,doc):
		GenFormView.__init__(self,doc,grinsRC.IDD_NODE_INFO)

		self['Name']=components.Edit(self,grinsRC.IDC_NODE_NAME)
		self['Type']=components.ComboBox(self,grinsRC.IDC_NODE_TYPE)
		self['Channel']=components.ComboBox(self,grinsRC.IDC_CHANNEL)		

		self['Cancel']=components.Button(self,grinsRC.IDUC_CANCEL)
		self['Restore']=components.Button(self,grinsRC.IDUC_RESTORE)
		self['NodeAttr']=components.Button(self,grinsRC.IDUC_NODE_ATTRIBUTES)
		self['ChanAttr']=components.Button(self,grinsRC.IDUC_CHANNEL_ATTRIBUTES)
		self['Anchors']=components.Button(self,grinsRC.IDUC_ANCHORS)
		self['Apply']=components.Button(self,grinsRC.IDUC_APPLY)
		self['OK']=components.Button(self,grinsRC.IDUC_OK)

		self['URL']=components.Edit(self,grinsRC.IDC_EXT_EDIT)
		self['Browse']=components.Button(self,grinsRC.IDUC_BROWSE)
		self['CallEditor']=components.Button(self,grinsRC.IDUC_EDIT)

		self['ImmEdit']=components.Edit(self,grinsRC.IDC_IMM_EDIT)

		self['IntList']=components.ListBox(self,grinsRC.IDC_INT_LIST)
		self['OpenChild']=components.Button(self,grinsRC.IDC_OPENCHILD)

		# cash vars
		self._prevsel=None
		self._cursel=None

	# Called by the framework after the OS window has been created
	def OnInitialUpdate(self):
		frame=self.GetParent()
		if self._freezesize:
			self.fittemplate()
			frame.RecalcLayout()
		self.RePosControls()
		for ck in self.keys():
			self[ck].attach_to_parent()
			self.EnableCmd(ck,1)
		self.EnableCmd('OpenChild',0)
		self.setdata()
		self.HookMessage(self.OnCmd,win32con.WM_COMMAND)
		self.HookKeyStroke(self.OnEnter,13)
		self.HookKeyStroke(self.OnEsc,27)

	# Reponse to message WM_COMMAND
	def OnCmd(self,params):
		msg=win32mu.Win32Msg(params)
		id=msg.cmdid()
		nmsg=msg.getnmsg()
		if id==self['Name']._id:
			self.OnName(id,nmsg)
		if id==self['Type']._id:
			self.OnType(id,nmsg)
		elif id==self['Channel']._id:
			self.OnChannel(id,nmsg)
		elif id==self['IntList']._id:
			self.OnIntList(id,nmsg)
		elif id==self['URL']._id:
			self.OnURL(id,nmsg)		
		elif self._idcbdict.has_key(id):
			apply(apply,self._idcbdict[id])

	# Response to name change
	def OnName(self,id,code):
		if code==win32con.EN_CHANGE:self.call('Name')

	# Response to type change
	def OnType(self,id,code):
		if code==win32con.CBN_SELCHANGE:self.call('Type')

	# Response to channel change
	def OnChannel(self,id,code):
		if code==win32con.CBN_DROPDOWN:
			self._prevsel=self['Channel'].getcursel()			
		elif code==win32con.CBN_SELCHANGE :
			strsel=self['Channel'].getvalue()
			if strsel[0]!='[' and strsel!='---':
				self.call('Channel')
			else:self['Channel'].setcursel(self._prevsel)

	# Response to Url change
	def OnURL(self,id,code):
		if code==win32con.EN_CHANGE:self.call('URL')

	def OnIntList(self,id,code):
		if code==win32con.LBN_SELCHANGE:
			self._cursel=self['IntList'].getcursel()
			self.EnableCmd('OpenChild',1)
		elif code==win32con.LBN_DBLCLK:
			self.call('OpenChild')

	# Called by the frame work before closing this View
	def OnClose(self):self.call('Cancel')

	# rem: not working, kbd captured by form
	def OnEnter(self,key):self.call('OK')
	def OnEsc(self,key):self.call('Cancel')

	# Core system's initialization of this window
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
		cbd=self._cbdict=adornments['callbacks']
		self._idcbdict={}
		for k in self.keys():
			if cbd.has_key(k):
				self._idcbdict[self[k]._id]=cbd[k]

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

	# Display data
	def setdata(self):	
		self.settitle(self._title)
		self.setchannelnames(self._channelnames,self._initchannel)
		self.settypes(self._types,self._inittype)
		if self._name: self.setname(self._name)
		if self._immtext:
			self.settext(self._immtext)
		elif self._children:
			self.setchildren(self._children)
		elif self._filename:
			self.setfilename(self._filename)

	def settitle(self,title):
		self._title=title
		if hasattr(self,'GetParent'):
			if self.GetParent().GetSafeHwnd():
				self.GetParent().SetWindowText(title)


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
		self['Channel'].initoptions(channelnames, initchannel)

	def getchannelname(self):
		"""Get the string which is the current selection."""
		return self['Channel'].getvalue()


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
		self['Type'].initoptions(types, inittype)

	def gettype(self):
		"""Get the string which is the current selection."""
		return self['Type'].getvalue()

	def settype(self, inittype):
		"""Set the current selection.

		Arguments (no defaults):
		inittype -- 0 <= inittype < len(types) -- the new
			current selection
		"""
		self['Type'].setpos(inittype)

	# Interface to the name field.  This part consists of an
	# editable text field.
	def setname(self, name):
		"""Set the value of the name field.

		Arguments (no defaults):
		name -- string
		"""
		self['Name'].settext(name)

	def getname(self):
		"""Return the current value of the name field."""
		return self['Name'].gettext()

	# Interface to the external part.  This part consists of a
	# text field with a URL (with or without the protocol, and if
	# without protocol, absolute or relative) and a `Browser...'
	# button which triggers a callback function.
	def setfilename(self, filename):
		"""Set the value of the filename (URL).

		Arguments (no defaults):
		filename -- string giving the URL
		"""
		self['URL'].settext(filename)

	def getfilename(self):
		"""Return the value of the filename text field."""
		return self['URL'].gettext()

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
			str=string.join(immtext, '\r\n')
		else:
			str=self.convert2ws(immtext)
		self['ImmEdit'].settext(str)

	def gettext(self):
		"""Return the current text as one string."""
		text = self['ImmEdit'].gettext()
		text = string.join(string.split(text, '\r\n'), '\n')
		text = string.join(string.split(text, '\r'), '\n')
		return text

	def gettextlines(self):
		"""Return the current text as a list of strings."""
		return self['ImmEdit'].getlines()

	# Convert the text from unix or mac to windows
	def convert2ws(self,text):
		nl=string.split(text,'\n')
		rl=string.split(text,'\r')
		if len(nl)==len(rl):# line_separator='\r\n'
			return text
		if len(nl)>len(rl):	# line_separator='\n'
			return string.join(nl, '\r\n')
		if len(nl)<len(rl):	# line_separator='\r'
			return string.join(rl, '\r\n')

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
		self['IntList'].resetcontent()
		if children:
			self['IntList'].addlistitems(children, -1)
			if initchild==None:initchild=0
			self['IntList'].setcursel(initchild)
			self._cursel=initchild
			self.EnableCmd('OpenChild',1)
		else:
			self._cursel = None
			self.EnableCmd('OpenChild',0)

	def getchild(self):
		"""Return the index of the current selection or None."""
		return self._cursel

	# The following methods choose between the three variable
	# parts.  One of the parts is active (the others need not be
	# shown), and when one of the parts is made the active part,
	# the others are automatically made inactive (possibly
	# hidden).
	# In Motif, this is done by using the same screen area for the
	# three parts.

	def imm_group_show(self):
		"""Make the immediate part visible."""
		self.ext_group_hide()	
		self.int_group_hide()
		self.GetDlgItem(grinsRC.IDC_STATIC1).SetWindowText('Content:')
		self.GetDlgItem(grinsRC.IDC_IMM_EDIT).ShowWindow(win32con.SW_SHOW)

	def imm_group_hide(self):
		self.GetDlgItem(grinsRC.IDC_IMM_EDIT).ShowWindow(win32con.SW_HIDE)

	def int_group_show(self):
		"""Make the interior part visible."""
		self.ext_group_hide()	
		self.imm_group_hide()
		self.GetDlgItem(grinsRC.IDC_STATIC1).SetWindowText('Content:')
		self.GetDlgItem(grinsRC.IDC_INT_LIST).ShowWindow(win32con.SW_SHOW)
		self.GetDlgItem(grinsRC.IDC_OPENCHILD).ShowWindow(win32con.SW_SHOW)		

	def int_group_hide(self):
		self.GetDlgItem(grinsRC.IDC_INT_LIST).ShowWindow(win32con.SW_HIDE)
		self.GetDlgItem(grinsRC.IDC_OPENCHILD).ShowWindow(win32con.SW_HIDE)		

	def ext_group_show(self):
		"""Make the external part visible."""
		self.GetDlgItem(grinsRC.IDC_STATIC1).SetWindowText('URL:')
		self.int_group_hide()	
		self.imm_group_hide()

		rcDlg=win32mu.Rect(self.GetWindowRect())
		rc=win32mu.Rect(self.GetDlgItem(grinsRC.IDC_EXT_EDIT).GetWindowRect())
		self.GetDlgItem(grinsRC.IDC_EXT_EDIT).ShowWindow(win32con.SW_SHOW)
		self.GetDlgItem(grinsRC.IDUC_BROWSE).ShowWindow(win32con.SW_SHOW)
		self.GetDlgItem(grinsRC.IDUC_EDIT).ShowWindow(win32con.SW_SHOW)

	def ext_group_hide(self):
		self.GetDlgItem(grinsRC.IDC_EXT_EDIT).ShowWindow(win32con.SW_HIDE)
		self.GetDlgItem(grinsRC.IDUC_BROWSE).ShowWindow(win32con.SW_HIDE)
		self.GetDlgItem(grinsRC.IDUC_EDIT).ShowWindow(win32con.SW_HIDE)

	def RePosControls(self):
		rc=win32mu.Rect(self.GetWindowRect())
		rc1=win32mu.Rect(self.GetDlgItem(grinsRC.IDC_EXT_EDIT).GetWindowRect())	
		rc2=win32mu.Rect(self.GetDlgItem(grinsRC.IDUC_CANCEL).GetWindowRect())
		rc3=win32mu.Rect(self.GetDlgItem(grinsRC.IDC_INT_LIST).GetWindowRect())

		h=rc2.top-rc1.top-8;
		w=rc3.width();
		x=rc1.left-rc.left;
		y=rc1.top-rc.top;

		self.GetDlgItem(grinsRC.IDC_INT_LIST).SetWindowPos(self.GetSafeHwnd(),(x,y,w,h),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
		self.GetDlgItem(grinsRC.IDC_IMM_EDIT).SetWindowPos(self.GetSafeHwnd(),(x,y,w,h),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
