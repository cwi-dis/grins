__version__ = "$Id$"

""" @win32doc|FormServer
This module implements a form server apropriate to 
the architecture chosen.
The other modules request from this server a form 
using a standard interface.

The purpose of this module is to simplify the 
application's MainFrame
and to isolate dependencies between 
forms implementation and modules that use them.
"""

# forms served
from AttrEditForm import AttrEditForm
from AnchorEditForm import AnchorEditForm
from NodeInfoForm import NodeInfoForm
from ArcInfoForm import ArcInfoForm

appform={
	0:{'cmd':-1,'hosted':0,'title':'Property Editor','id':'attr_edit','obj':None,'class':AttrEditForm},
	1:{'cmd':-1,'hosted':0,'title':'Anchor Editor','id':'anchor_edit','obj':None,'class':AnchorEditForm,'freezesize':1},
	2:{'cmd':-1,'hosted':0,'title':'NodeInfo Editor','id':'node_info','obj':None,'class':NodeInfoForm,'freezesize':1},
	3:{'cmd':-1,'hosted':1,'title':'ArcInfo Editor','id':'arc_info','obj':None,'class':ArcInfoForm},
	}

# interface needed for FormServer contructor argument
class IFormServerContext:
	def getdoc(self):
		return None
	def createChildFrame(self,form):
		return None
	def GetClientRect(self):
		return (0,0,1,1)
	def Activate(self,form):
		pass
	def getPrefRect(self):
		return (0,0,1,1)

import win32ui,win32con,win32mu
from pywin.mfc import window,object,docview,dialog

# The ChildFrame purpose is to host the forms in its client area
class ChildFrame(window.MDIChildWnd):
	def __init__(self,form=None, freezesize=0):
		window.MDIChildWnd.__init__(self,win32ui.CreateMDIChild())
		self._form=form
		self._freezesize=freezesize

	# Create the OS window
	def Create(self, title, rect = None, parent = None, maximize=0):
		self._title=title
		style = win32con.WS_CHILD | win32con.WS_OVERLAPPEDWINDOW
		self.CreateWindow(None, title, style, rect, parent,None)
		#if maximize and parent:parent.maximize(self)
		self.HookMessage(self.onMdiActivate,win32con.WM_MDIACTIVATE)
		self.ShowWindow(win32con.SW_SHOW)

	# Change window style before creation
	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)
		if self._freezesize:
			cs.style = win32con.WS_CHILD|win32con.WS_OVERLAPPED |win32con.WS_CAPTION|win32con.WS_BORDER|win32con.WS_SYSMENU|win32con.WS_MINIMIZEBOX
		return cs.to_csd()
	
	# Called by the framework when this is activated or deactivated
	def onMdiActivate(self,params):
		msg=win32mu.Win32Msg(params)
		if msg._lParam==self._hwnd:
			if self._form: 
				self._form.onActivate(1)
		elif msg._wParam==self._hwnd:
			if self._form:
				self._form.onActivate(0)
	
	# Creates and sets the view 	
	# create view (will be created by default if)
	def OnCreateClient(self, cp, context):
		if context is not None and context.template is not None:
			context.template.CreateView(self, context)
		elif self._form:
			v=self._form
			v.createWindow(self)
			self.SetActiveView(v)
			self.RecalcLayout()
			v.OnInitialUpdate()
		self._hwnd=self.GetSafeHwnd()

	# Set the view from the argument view class
	def setview(self,viewclass,id=None):
		doc=docview.Document(docview.DocTemplate())
		v = viewclass(doc)
		v.CreateWindow(self)
		self.SetActiveView(v)
		self.RecalcLayout()
		v.OnInitialUpdate()

	# Response to user close command
	# the user is closing the wnd directly
	def OnClose(self):
		# we must let the view to decide:
		if hasattr(self._form,'OnClose'):
			self._form.OnClose()
		else:
			self._obj_.OnClose()

	# Called by the framework before destroying the window
	def OnDestroy(self, msg):
		window.MDIChildWnd.OnDestroy(self, msg)

	# Called by the framework after the window has been created
	def InitialUpdateFrame(self, doc, makeVisible):
		pass

	# Returns the parent MDIFrameWnd	
	def getMDIFrame(self):
		return self.GetMDIFrame()

	# Target for commands that are enabled
	def OnUpdateCmdEnable(self,cmdui):
		cmdui.Enable(1)

	# Target for commands that are dissabled
	def OnUpdateCmdDissable(self,cmdui):
		cmdui.Enable(0)

# This class implements a Form Server. Any client can request
# a form by passing its string id
class FormServer:
	def __init__(self,context):
		self._context=context

	# Returns a new form object
	def newformobj(self,strid):
		formno=self.getformno(strid)
		if 'hosted' in appform[formno].keys() and appform[formno]['hosted']:
			formclass=appform[formno]['class']
			return formclass()
		else:
			return self._newformobj(formno)

	# Show the form passed as argument
	def showform(self,form,strid):
		if not form or not form._obj_:
			return
		formno=self.getformno(strid)
		self.frameform(form,formno)

	# Create the form with string id
	def createform(self,strid):
		formno=self.getformno(strid)
		form=self._newformobj(formno)
		self.frameform(form,formno)
		return form

	# Create a new form with formno
	def _newformobj(self,formno):
		formclass=appform[formno]['class'] 
		return formclass(self._context.getdoc())

	# Returns the form number from the string id
	def getformno(self,strid):
		for formno in appform.keys():
			if appform[formno]['id']==strid:
				return formno
		raise error,'undefined requested form'
	
	# Create a ChildFrame to host this view
	def frameform(self,form,formno):
		freezeSize=0
		if 'freezesize' in appform[formno].keys():
			freezeSize=appform[formno]['freezesize']
		f=ChildFrame(form,freezeSize)
		rc=self._context.getPrefRect()
		f.Create(form._title,rc,self._context,0)
		self._context.Activate(f)


