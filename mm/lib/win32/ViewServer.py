

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
import sysmetrics

if appcon.IsPlayer:
	PLAYERVIEW=CLOSE
	HIERARCHYVIEW=None
	CHANNELVIEW=None
	LINKVIEW=None
	LAYOUTVIEW=None
appview={
	0:{'cmd':PLAYERVIEW,'hosted':0,'title':'Player','id':'pview_','class':_PlayerView,'maximize':1},
	1:{'cmd':HIERARCHYVIEW,'hosted':0,'title':'Hierarchy view','id':'hview_','class':_HierarchyView,'maximize':1},
	2:{'cmd':CHANNELVIEW,'hosted':0,'title':'Channel view','id':'cview_','class':_ChannelView,'maximize':1},
	3:{'cmd':LINKVIEW,'hosted':0,'title':'Link view','id':'leview_','class':_LinkView,'maximize':1},
	4:{'cmd':LAYOUTVIEW,'hosted':1,'title':'Layout view','id':'lview_','class':_LayoutView},
	5:{'cmd':SOURCE,'hosted':0,'title':'Source','id':'sview_','class':_SourceView,'maximize':1},
	6:{'cmd':-1,'hosted':0,'title':'','id':'cmifview_','class':_CmifView},
}


class ChildFrame(window.MDIChildWnd):
	def __init__(self,view=None,decor=None):
		window.MDIChildWnd.__init__(self,win32ui.CreateMDIChild())
		self._view=view
		self._decor=decor
		self._context=None

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
		return
		msg=win32mu.Win32Msg(params)
		if msg._lParam==self._hwnd:
			self._view.onActivate(1)
		elif msg._wParam==self._hwnd:
			self._view.onActivate(0)

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
		# we must let the view to decide:
		if hasattr(self._view,'OnClose'):
			self._view.OnClose()
		else:
			self._obj_.OnClose()

	def InitialUpdateFrame(self, doc, makeVisible):
		pass
	
	def getMDIFrame(self):
		return self.GetMDIFrame()

	def GetUserCmdId(self,cmdcl):
		return self.GetMDIFrame().GetUserCmdId(cmdcl)

class ViewServer:
	def __init__(self,context):
		self._context=context

	def newview(self,x, y, w, h, title, units = appcon.UNIT_MM, adornments=None,canvassize=None, commandlist=None, strid='cmifview_'):
		viewno=self.getviewno(strid)
		viewclass=appview[viewno]['class'] 
		view=viewclass(self.getdoc())
		self.add_common_interface(view,viewno)
		x=0#if not x or x<0: x=0
		y=0#if not y or y<0: y=0
		if not w or not h:rc=None
		else:
			x,y,w,h=sysmetrics.to_pixels(x,y,w,h,units)
			rc=(x,y,x+w+2*sysmetrics.cxframe,y+h+sysmetrics.cycaption+2*sysmetrics.cyframe)
		f=ChildFrame(view)
		f.Create(title,rc,self._context,0)
		view.init((x,y,w,h),title,units,adornments,canvassize,commandlist)
		self._context.MDIActivate(f)
		if appcon.IsPlayer:
			self._context.setcoords((x, y, w, h),units)
		return view

	def newviewobj(self,strid):
		viewno=self.getviewno(strid)
		if not self.hosted(viewno):
			return self._newviewobj(viewno)
		else:
			viewclass=appview[viewno]['class']
			viewobj=viewclass()
			self.add_common_interface(viewobj,viewno)
			return viewobj


	def showview(self,view,strid):
		if not view or not view._obj_:
			return
		viewno=self.getviewno(strid)
		self.frameview(view,viewno)

	def createview(self,strid):
		viewno=self.getviewno(strid)
		view=self._newviewobj(viewno)
		self.frameview(view,viewno)
		return view

	def _newviewobj(self,viewno):
		viewclass=appview[viewno]['class'] 
		viewobj=viewclass(self.getdoc())
		self.add_common_interface(viewobj,viewno)
		return viewobj


	def getviewno(self,strid):
		for viewno in appview.keys():
			if appview[viewno]['id']==strid:
				return viewno
		raise error,'undefined requested view'
	
	def frameview(self,view,viewno):
		decor=''
		if viewno==self.getviewno('pview_'): decor='lview_'
		f=ChildFrame(view,decor)
		rc=self._context.getPrefRect()
		f.Create(appview[viewno]['title'],None,self._context,0)
		self._context.MDIActivate(f)
	
	# returns None if not exists
	def getviewframe(self,strid):
		viewno=self.getviewno(strid)
		return appview[viewno]['obj']

	def hosted(self,viewno):
		return appview[viewno]['hosted']


	def add_common_interface(self,viewobj,viewno):
		viewobj.getformserver=self._context.getformserver
		viewobj.getframe=viewobj.GetParent
		viewobj._strid=appview[viewno]['id']
		viewobj._commandlist=[]
		viewobj._title=appview[viewno]['title']
		viewobj._closecmdid=usercmdui.class2ui[appview[viewno]['cmd']].id