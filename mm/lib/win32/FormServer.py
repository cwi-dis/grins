
# forms served
from AttrEditForm import AttrEditForm
from AnchorEditForm import AnchorEditForm
from NodeInfoForm import NodeInfoForm
from ArcInfoForm import ArcInfoForm

appform={
	0:{'cmd':-1,'hosted':0,'title':'Attribute Editor','id':'attr_edit','obj':None,'class':AttrEditForm,'maximize':1},
	1:{'cmd':-1,'hosted':0,'title':'Anchor Editor','id':'anchor_edit','obj':None,'class':AnchorEditForm},
	2:{'cmd':-1,'hosted':0,'title':'NodeInfo Editor','id':'node_info','obj':None,'class':NodeInfoForm},
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

class ChildFrame(window.MDIChildWnd):
	def __init__(self,form=None):
		window.MDIChildWnd.__init__(self,win32ui.CreateMDIChild())
		self._form=form

	def Create(self, title, rect = None, parent = None, maximize=0):
		self._title=title
		style = win32con.WS_CHILD | win32con.WS_OVERLAPPEDWINDOW
		self.CreateWindow(None, title, style, rect, parent,None)
		#if maximize and parent:parent.maximize(self)
		self.HookMessage(self.onMdiActivate,win32con.WM_MDIACTIVATE)
		self.ShowWindow(win32con.SW_SHOW)

	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)
		#cs.style =cs.style & (~win32con.WS_THICKFRAME)
		#cs.style =cs.style | win32con.WS_BORDER;

		# remove the minimize and maximize buttons
		# so that the MDI child frame "snaps" to the dialog.

		#cs.style =cs.style & (~(win32con.WS_MINIMIZEBOX|win32con.WS_MAXIMIZEBOX))

		return cs.to_csd()

	def onMdiActivate(self,params):
		msg=win32mu.Win32Msg(params)
		if msg._lParam==self._hwnd:
			if self._form: 
				self._form.onActivate(1)
		elif msg._wParam==self._hwnd:
			if self._form:
				self._form.onActivate(0)
		
	# create view (will be created by default if)
	def OnCreateClient(self, cp, context):
		if context is not None and context.template is not None:
			context.template.CreateView(self, context)
		elif self._form:
			v=self._form
			v.CreateWindow(self)
			self.SetActiveView(v)
			self.RecalcLayout()
			v.OnInitialUpdate()
		self._hwnd=self.GetSafeHwnd()
	def setview(self,viewclass,id=None):
		doc=docview.Document(docview.DocTemplate())
		v = viewclass(doc)
		v.CreateWindow(self)
		self.SetActiveView(v)
		self.RecalcLayout()
		v.OnInitialUpdate()

	# the user is closing the wnd directly
	def OnClose(self):
		# we must let the view to decide:
		if hasattr(self._form,'OnClose'):
			self._form.OnClose()
		else:
			self._obj_.OnClose()

	def OnDestroy(self, msg):
		window.MDIChildWnd.OnDestroy(self, msg)

	def InitialUpdateFrame(self, doc, makeVisible):
		pass
	
	def getMDIFrame(self):
		return self.GetMDIFrame()

class FormServer:
	def __init__(self,context):
		self._context=context

	def newformobj(self,strid):
		formno=self.getformno(strid)
		if not self.hosted(formno):
			return self._newformobj(formno)
		else:
			formclass=appform[formno]['class']
			return formclass()

	def showform(self,form,strid):
		if not form or not form._obj_:
			return
		formno=self.getformno(strid)
		self.frameform(form,formno)

	def createform(self,strid):
		formno=self.getformno(strid)
		form=self._newformobj(formno)
		self.frameform(form,formno)
		return form

	def _newformobj(self,formno):
		formclass=appform[formno]['class'] 
		return formclass(self._context.getdoc())

	def getformno(self,strid):
		for formno in appform.keys():
			if appform[formno]['id']==strid:
				return formno
		raise error,'undefined requested form'
	
	def frameform(self,form,formno):
		f=ChildFrame(form)
		rc=self._context.getPrefRect()
		if 'maximize' in appform[formno].keys():
			maximize=1
		else: maximize=0
		f.Create(form._title,rc,self._context,0)
		self._context.Activate(f)

	def hosted(self,formno):
		return appform[formno]['hosted']

