

# views types
from _LayoutView import _LayoutView
from _LinkView import _LinkView
from _CmifView import _CmifView
from _SourceView import _SourceView

# views served
_PlayerView=_CmifView
_HierarchyView=_CmifView
_ChannelView=_CmifView
_LinkView=_LinkView
_LayoutView=_LayoutView
_SourceView=_SourceView

# imports
import win32ui,win32con,win32mu
from pywin.mfc import window,object,docview,dialog
import appcon

from usercmd import *
import usercmdui

if not appcon.IsEditor:
	PLAYERVIEW=CLOSE
	HIERARCHYVIEW=None
	CHANNELVIEW=None
	LINKVIEW=None
	LAYOUTVIEW=None
	SOURCE=None
appview={
	0:{'cmd':PLAYERVIEW,'hosted':0,'title':'Player','id':'pview_','obj':None,'class':_PlayerView,'maximize':1},
	1:{'cmd':HIERARCHYVIEW,'hosted':0,'title':'Hierarchy view','id':'hview_','obj':None,'class':_HierarchyView,'maximize':1},
	2:{'cmd':CHANNELVIEW,'hosted':0,'title':'Channel view','id':'cview_','obj':None,'class':_ChannelView,'maximize':1},
	3:{'cmd':LINKVIEW,'hosted':0,'title':'Link view','id':'leview_','obj':None,'class':_LinkView,'maximize':1},
	4:{'cmd':LAYOUTVIEW,'hosted':1,'title':'Layout view','id':'lview_','obj':None,'class':_LayoutView},
	5:{'cmd':SOURCE,'hosted':0,'title':'Source','id':'sview_','obj':None,'class':_SourceView,'maximize':1},
}

class ChildFrame(window.MDIChildWnd):
	def __init__(self,view=None,decor=None):
		window.MDIChildWnd.__init__(self,win32ui.CreateMDIChild())
		self._view=view
		self._decor=decor

	def Create(self, title, rect = None, parent = None, maximize=0):
		self._title=title
		style = win32con.WS_CHILD | win32con.WS_OVERLAPPEDWINDOW
		self.CreateWindow(None, title, style, rect, parent)
		if maximize and parent:parent.maximize(self)
		self.HookMessage(self.onMdiActivate,win32con.WM_MDIACTIVATE)
		self.ShowWindow(win32con.SW_SHOW)

	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)
		return cs.to_csd()

	def onMdiActivate(self,params):
		msg=win32mu.Win32Msg(params)
		if msg._lParam==self._hwnd:
			for viewno in appview.keys():
				if appview[viewno]['obj']==self:
					self.GetMDIFrame().setviewtab(viewno)
					v=self.GetActiveView()
					if v: 
						v.onActivate(1)
					break
		elif msg._wParam==self._hwnd:
			for viewno in appview.keys():
				if appview[viewno]['obj']==self:
					self.GetMDIFrame().setviewtab(0)
					v=self.GetActiveView()
					if v:v.onActivate(0)

	# create view (will be created by default if)
	def OnCreateClient(self, cp, context):
		if context is not None and context.template is not None:
			context.template.CreateView(self, context)
		elif self._view:
			v=self._view
			v.createWindow(self)
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
		# create an artificial close cmd
		# the cmif-core should delete the window
		# i.e. should result in view.close() call
		for viewno in appview.keys():
			if appview[viewno]['obj']==self:
				if 'close' in appview[viewno].keys():
					cmdcl=appview[viewno]['close']
				else: cmdcl=appview[viewno]['cmd']
				if not cmdcl:
					self.DestroyWindow()
				else:
					id=usercmdui.class2ui[cmdcl].id
					self.GetMDIFrame().PostMessage(win32con.WM_COMMAND,id)

	def OnDestroy(self, msg):
		for viewno in appview.keys():
			if appview[viewno]['obj']==self:
				appview[viewno]['obj']=None
		window.MDIChildWnd.OnDestroy(self, msg)

	def InitialUpdateFrame(self, doc, makeVisible):
		pass
	
	def getMDIFrame(self):
		return self.GetMDIFrame()

	def GetUserCmdId(self,cmdcl):
		return self.GetMDIFrame().GetUserCmdId(cmdcl)

class ViewServer:
	def __init__(self,context):
		self._context=context

	def newview(self, x, y, w, h, title, units = appcon.UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, strid='xview_'):
		viewno=self.getviewno(strid)
		view=self._newviewobj(viewno)
		self.frameview(view,viewno)
		view.init((x,y,w,h),title,units,adornments,canvassize,commandlist)
		return view

	def newviewobj(self,strid):
		viewno=self.getviewno(strid)
		if not self.hosted(viewno):
			return self._newviewobj(viewno)
		else:
			viewclass=appview[viewno]['class']
			return viewclass()

	def showview(self,view,strid):
		if not view or not view._obj_:
			return
		viewno=self.getviewno(strid)
		if not appview[viewno]['obj']:
			self.frameview(view,viewno)

	def createview(self,strid):
		viewno=self.getviewno(strid)
		view=self._newviewobj(viewno)
		self.frameview(view,viewno)
		return view

	def _newviewobj(self,viewno):
		if appview[viewno]['obj']:
			return appview[viewno]['obj'].GetActiveView()
		viewclass=appview[viewno]['class'] 
		return viewclass(self.getdoc())

	def getviewno(self,strid):
		for viewno in appview.keys():
			if appview[viewno]['id']==strid:
				return viewno
		raise error,'undefined requested view'
	
	def frameview(self,view,viewno):
		decor=''
		if not appview[viewno]['obj']:
			if viewno==self.getviewno('pview_'): decor='lview_'
			f=ChildFrame(view,decor)
			rc=self._context.getPrefRect()
			if 'maximize' in appview[viewno].keys():
				maximize=1
				rc=self._context.GetClientRect()
			else: maximize=0
			f.Create(appview[viewno]['title'],rc,self._context,maximize)
			appview[viewno]['obj']=f
		self._context.MDIActivate(appview[viewno]['obj'])
	
	# returns None if not exists
	def getviewframe(self,strid):
		viewno=self.getviewno(strid)
		return appview[viewno]['obj']

	def hosted(self,viewno):
		return appview[viewno]['hosted']