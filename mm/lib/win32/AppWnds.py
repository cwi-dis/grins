__version__ = "$Id$"

# Objects defined in this module:
# class _CmifScrollView(cmifwnd._CmifWnd,_rbtk,docview.ScrollView):
# class GRiNSToolbar(window.Wnd):
# class _FrameWnd(cmifwnd._CmifWnd,window.FrameWnd):
# class _Window(cmifwnd._CmifWnd,_rbtk,window.Wnd):
# class _SubWindow(cmifwnd._CmifWnd,window.Wnd):
# class WebBrowser(window.Wnd):
# class _BrowserSubWindow(_SubWindow):



import win32ui, win32con, win32api
from win32modules import grinsRC
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()
import os

from types import *
from WMEVENTS import *
from appcon import *
from sysmetrics import *

from DisplayList import DisplayList

import win32mu,AppMenu
import usercmd,usercmdui

toplevel=None # global set by AppTopLevel

from rbtk import _rbtk,_rb_done,_in_create_box,_rb_message

 
###########################################################
# import window core stuff
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl
import cmifwnd	
import afxexttb # part of generated afxext.py


###########################################################
class _VoidView(docview.ScrollView):
	def __init__(self,doc):
		docview.ScrollView.__init__(self,doc)
	def OnInitialUpdate(self):
		l,t,r,b=self.GetClientRect()
		self.SetScaleToFitSize((r-l,b-t))
	def close(self):
		pass
	def createWindow(self,parent):
		self.CreateWindow(parent)

class _SourceView(docview.EditView):
	def __init__(self,doc):
		docview.EditView.__init__(self,doc)
		self._text=''
	def OnInitialUpdate(self):
		edit=self.GetEditCtrl()
		edit.SetWindowText(self._text)
		edit.SetReadOnly(1)
	def createWindow(self,parent):
		self.CreateWindow(parent)

	# cmif interface
	def settext(self,text):
		self._text=text
	def close(self):
		del self._text
		self._text=None
		pass
	def is_closed(self):
		if self._obj_==None: return 1
		if self.GetSafeHwnd()==0: return 1
		return self.IsWindowVisible()

class _CmifScrollView(cmifwnd._CmifWnd,_rbtk,docview.ScrollView):
	def __init__(self,doc):
		cmifwnd._CmifWnd.__init__(self)
		_rbtk.__init__(self)
		docview.ScrollView.__init__(self,doc)

	def OnInitialUpdate(self):
		if not self._parent:
			self._parent=self.GetParent()
		self._do_init(self._parent)
		self._is_active = 0
		self._canscroll = 0
		# init dims
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)

		# create view
		#self._doc=docview.Document(docview.DocTemplate())
		#docview.ScrollView.__init__(self,self._doc)
		#self.CreateWindow(parent)

		# set std attributes
		self._title = ''	
		self._window_type = SINGLE
		self._sizes = 0, 0, 1, 1

		self._topwindow = self # from the app's view this is a topwindow
		self._parent._subwindows.insert(0, self)

		r= {win32con.WM_RBUTTONDOWN:self.onRButtonDown,
			win32con.WM_LBUTTONDBLCLK:self.onLButtonDblClk,
			win32con.WM_LBUTTONDOWN:self.onLButtonDown,
			win32con.WM_LBUTTONUP:self.onLButtonUp,
			win32con.WM_MOUSEMOVE:self.onMouseMove,
			win32con.WM_SIZE:self.onSize,			
			}
		self._enable_response(r)

	def OnDraw(self,dc):
		rc=dc.GetClipBox()
		if self._active_displist:
			self._active_displist._render(dc,rc,1)

	def createWindow(self,parent):
		self.CreateWindow(parent)

	def OnCreate(self,params):
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)
		self.SetScrollSizes(win32con.MM_TEXT,(r-l,b-t))
		self.ResizeParentToFit()
							
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		if self._canscroll==1 or self._is_active==0:
			self._rect=0,0,msg.width(),msg.height()
		else:
			self.onSizeScale(params)

	def onSizeScale(self, params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		width,height=msg.width(), msg.height()
		self.arrowcache = {}
		w = _in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			try:
				w._rb_cancel()
			except _rb_done:
				pass
			w._next_create_box[0:0] = next_create_box
		self._do_resize(width, height)
		if w:
			w._rb_end()
			raise _rb_done

	def _scroll(self,how):
		if self._canscroll==0: return
		w,h=self._canvas[2:]
		self.SetScrollSizes(win32con.MM_TEXT,(w,h))
		if how==RESET_CANVAS:self.ResizeParentToFit()
			
	# convert from client (device) coordinates to canvas (logical)
	def _DPtoLP(self,pt):
		dc=self.GetDC()
		# PyCView.GetDC has called OnPrepareDC(dc)
		pt=dc.DPtoLP(pt)
		self.ReleaseDC(dc)
		return pt

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		if type_channel==HTM:
			win= _BrowserSubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		else:
			win= _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		return win

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)
		return win
	
	# delegate to parent for cmds and adorment functionality
	def set_dynamiclist(self, cmd, list):
		self._parent.set_dynamiclist(cmd,list)
	def set_adornments(self, adornments):
		self._parent.set_adornments(adornments)
	def set_toggle(self, command, onoff):
		self._parent.set_toggle(command,onoff)
		
	def set_commandlist(self, list):
		self._parent.set_commandlist(list,'view')
	def settitle(self,title):
		self._parent.settitle(title,'view')


	# recycling of views
	def init(self,rc,title='View',units= UNIT_MM,adornments=None,canvassize=None,commandlist=None):
		#if self._is_active==1:
		#	self._parent.closeview()
			#self.close()

		self.settitle(title)
		self.set_commandlist(commandlist)
				
		if canvassize==None:self._canscroll=0
		else: self._canscroll=1

		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(l,t,r-l,b-t)
		if canvassize!=None:
			pass # self._canvas= set_from(canvassize)

		if self._canscroll:
			self.SetScrollSizes(win32con.MM_TEXT,(self._canvas[2],self._canvas[3]))
			self.SetScrollSizes(win32con.MM_TEXT,(r-l,b-t))
		else:
			self.SetScaleToFitSize((r-l,b-t))
		if canvassize==None:
			self.ResizeParentToFit()		
		self._is_active=1
		return self
		
	def close(self):
		#if self._is_active==0:return
		#else: print 'closing active view'

		# old stuff remaining since we are recycling
		self.arrowcache = {}
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		self.destroy_menu()

		# not highligted (misleading name!)
		self._showing=0

		# remove view title and 
		# disable view-context commands 
		self.settitle(None)
		self.set_commandlist(None)
		#if self._parent.GetActiveView()==self:
		#	self._parent.setview('eview_')
		return

		# Fit view in client rect
		self._canscroll=0
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)
		self.SetScrollSizes(win32con.MM_TEXT,(r-l,b-t))
		self.ResizeParentToFit()

		# reset flag, i.e. the view is void
		self._is_active=0

	def is_closed(self):
		return self._is_active==0
	def pop(self):
		self._parent.ActivateFrame()
	def push(self):
		pass

##########
# view classes
import formvw
_PlayerView=_CmifScrollView
_HierarchyView=_CmifScrollView
_ChannelView=_CmifScrollView
_LinkEditView=formvw.FormView
_LayoutView=formvw.LayoutView
#_SourceView=_SourceView
viewcmd=[usercmd.PLAYERVIEW,usercmd.HIERARCHYVIEW,
		usercmd.CHANNELVIEW,usercmd.LINKVIEW,usercmd.LAYOUTVIEW,
		usercmd.SOURCE,usercmd.CLOSE_WINDOW]
viewstrid=['pview_','hview_',
		'cview_','leview_','lview_',
		'sview_','vview_']


##########
class GRiNSToolbar(window.Wnd):
	def __init__(self, parent):
		style = win32con.WS_CHILD |\
			win32con.WS_VISIBLE |\
			afxres.CBRS_TOP |\
			afxres.CBRS_TOOLTIPS|\
			afxres.CBRS_FLYBY|\
			afxres.CBRS_SIZE_DYNAMIC
		wndToolBar = win32ui.CreateToolBar(parent,style,afxres.AFX_IDW_TOOLBAR)
		#wndToolBar.LoadToolBar(grinsRC.IDB_GRINSED1)
		wndToolBar.LoadBitmap(grinsRC.IDB_GRINSED1)
		wndToolBar.EnableDocking(afxres.CBRS_ALIGN_ANY)
		wndToolBar.SetWindowText(AppDispName)
		wndToolBar.ModifyStyle(0, commctrl.TBSTYLE_FLAT)
		window.Wnd.__init__(self,wndToolBar)

class GRiNSDlgBar(window.Wnd):
	def __init__(self, parent):
		AFX_IDW_DIALOGBAR=0xE805
		wndDlgBar = win32ui.CreateDialogBar()
		window.Wnd.__init__(self,wndDlgBar)
		wndDlgBar.CreateWindow(parent,grinsRC.IDD_GRINSEDBAR,
			afxres.CBRS_ALIGN_BOTTOM,AFX_IDW_DIALOGBAR)
		#tabwnd=self.GetDlgItem(grinsRC.IDC_TAB_GRINSVIEWS)
		#hrab=Sdk.GetDlgItem(self.GetSafeHwnd(),grinsRC.IDC_TAB_GRINSVIEWS)
		import components
		self._tab=components.TabCtrl(self,grinsRC.IDC_TAB_GRINSVIEWS)
		self._tab.attach_to_parent()

		self._tab.insertitem(0,'Player')
		self._tab.insertitem(1,'Hierarchy view')
		self._tab.insertitem(2,'Channel view')
		self._tab.insertitem(3,'Link view')
		self._tab.insertitem(4,'Layout view')
		self._tab.insertitem(5,'Source')

		rc=win32mu.Rect(parent.GetClientRect())
		self.sizeto(rc.width(),rc.height())
	def getid(self):
		return grinsRC.IDD_GRINSEDBAR
	def sizeto(self,w,h):
		rc=win32mu.Rect(self._tab.getwindowrect())
		self._tab.setwindowpos(0,(0,0,w,rc.height()),
			win32con.SWP_NOMOVE|win32con.SWP_NOZORDER)
	def postcmd(self,wnd,ix):
		usercmd_ui = usercmdui.class2ui[viewcmd[ix]]
		wnd.PostMessage(win32con.WM_COMMAND,usercmd_ui.id)
	def settab(self,id):
		ix=0
		for s in viewstrid:
			if s==id:
				self._tab.setcursel(ix)
				return
			ix=ix+1
		
class _FrameWnd(window.FrameWnd,cmifwnd._CmifWnd):
	def __init__(self):
		window.FrameWnd.__init__(self,win32ui.CreateFrame())
		cmifwnd._CmifWnd.__init__(self)
		self._do_init(toplevel)

	def create(self,title):
		strclass=self.registerwndclass()		
		self._obj_.Create(strclass,title)

		# toolbar
		self.EnableDocking(afxres.CBRS_ALIGN_ANY)
		self._wndToolBar=GRiNSToolbar(self)
		self.DockControlBar(self._wndToolBar)
		if IsEditor:
			self.setEditorFrameToolbar()
		else:
			self.setPlayerToolbar()	
						
		self.setviewcl(_VoidView)
		v=self.GetActiveView()
		self._VoidViewclass=v.__class__

	def registerwndclass(self):
		# register top frame class
		clstyle=win32con.CS_DBLCLKS
		exstyle=0
		icon=Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED)
		cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		return Afx.RegisterWndClass(clstyle,cursor,brush,icon)

	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)

		# sizes
		cs.cx,cs.cy=(3*scr_width_pxl/4),(3*scr_height_pxl/4)
		cs.x,cs.y=x=scr_width_pxl/8,scr_height_pxl/8

		# menu
		menu=win32ui.CreateMenu()
		for key in usercmdui.menuconfig:
			menu.AppendMenu(win32con.MF_POPUP,usercmdui.stdmenu[key].GetHandle(),"&%s"%key)
		cs.hMenu=menu.GetHandle()

		return cs.to_csd()
	
	# this is called after CWnd::OnCreate 
	def OnCreate(self, createStruct):
		self.HookMessage(self.onSize,win32con.WM_SIZE)
		self.HookMessage(self.onClose,win32con.WM_CLOSE)

		# the view is responsible for user input
		# so do not hook other messages

		# direct all cmds to self.OnUserCmd but dissable them
		for cmdcl in usercmdui.class2ui.keys():
			id=usercmdui.class2ui[cmdcl].id
			self.HookCommand(self.OnUserCmd,id)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)

		# hook tab sel change
		self.HookNotify(self.OnNotifyTcnSelChange,formvw.TCN_SELCHANGE)

		return 0

	def OnNotifyTcnSelChange(self, nm, nmrest=(0,)):
		hwndFrom,idFrom,code=nm
		if idFrom==grinsRC.IDC_TAB_GRINSVIEWS:
			newview=self._wndDlgBar._tab.getcursel()
			self._wndDlgBar.postcmd(self,newview)
			return 1
		print 'other',nm,nmrest
		return 0

	def init_cmif(self, x, y, w, h, title,units = UNIT_MM,
		      adornments = None,commandlist = None):	
		if not w or w==0:
			w=(3*scr_width_mm/4)
		if not h or h==0:
			h=(3*scr_height_mm/4)
		if not x: x=scr_width_mm/8
		if not y: y=scr_height_mm/8

		self.newcmwindow=self.newwindow #alias
		self._canscroll = 0
		self._title = title		
		self._topwindow = self
		self._window_type = SINGLE # actualy not applicable
		self._sizes = 0, 0, 1, 1
		self._parent._subwindows.insert(0, self)
		xp,yp,wp,hp = to_pixels(x,y,w,h,units)
		self._rectb= xp,yp,wp,hp
		self._sizes = (float(xp)/scr_width_pxl,float(yp)/scr_height_pxl,float(wp)/scr_width_pxl,float(hp)/scr_height_pxl)
		self._depth = toplevel.getscreendepth()
		
		# all, are historic alias but useful to markup externals
		# the symbol self._obj_ reresents the os-mfc window object
		self._wnd=self._obj_ 
		self._hWnd=self.GetSafeHwnd()

		# set adorments and cmdlist
		self._qtitle={'frame':title,'document':None,'view':None}
		self._activecmds={'frame':{},'document':{},'view':{}}
		self._dynamiclists={}
		self.set_commandlist(commandlist,'frame')

		l,t,r,b=self.GetClientRect()
		self._canvas=self._rect=(l,t,r-l,b-t)
		if hasattr(self,'_wndDlgBar'):
			self._wndDlgBar.sizeto(r-l,b-t)
	

	def newdocument(self,title,adornments,commandlist):
		self.GetActiveView().close()
		self.settitle(title,'document')
		self.set_commandlist(commandlist,'document')
		if IsEditor:
			self.setEditorDocumentToolbar()
			self._wndDlgBar=GRiNSDlgBar(self)

		usercmd_ui = usercmdui.class2ui[viewcmd[0]]
		self.PostMessage(win32con.WM_COMMAND,usercmd_ui.id)

		self.ActivateFrame()
		return self
	
	def newwindow(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
		     units = UNIT_MM, adornments = None,
		     canvassize = None, commandlist = None, resizable = 1):
		return self.GetActiveView()
		return _Window(parent, x, y, w, h, title, defcmap, pixmap,
		     units,adornments,canvassize, commandlist, resizable)

	def newview(self, x, y, w, h, title, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, context='vview_'):
		v=self.GetActiveView()
		if self.isappview(v):
			self.closeview()
		view=self.newviewobj(context)
		view.createWindow(self)
		self.SetActiveView(view)
		self.setviewtab(context)
		self.RecalcLayout()
		view.OnInitialUpdate()
		view.ShowWindow(win32con.SW_SHOW)
		if v and v._obj_ and v.GetSafeHwnd():
			v.DestroyWindow()
		view.init((x,y,w,h),title,units,adornments,canvassize,commandlist)
		return view

	def showview(self,view,context='vview_'):
		if not view or not view._obj_:
			return
		v=self.GetActiveView()
		if self.isappview(v):
			self.closeview()
		if view.GetSafeHwnd()==0:
			view.createWindow(self)
		self.SetActiveView(view)
		self.setviewtab(context)
		self.RecalcLayout()
		view.OnInitialUpdate()
		view.ShowWindow(win32con.SW_SHOW)
		if v and v._obj_ and v.GetSafeHwnd():
			v.DestroyWindow()
	def createview(self,view):
		if not view or not view._obj_: 
			raise error, 'createview called with not a view'
			return
		if view.GetSafeHwnd()==0:
			view.createWindow(self)

	def setview(self,context='vview_'):
		v=self.GetActiveView()
		view=self.newviewobj(context)
		view.createWindow(self)
		self.SetActiveView(view)
		self.setviewtab(context)
		self.RecalcLayout()
		view.OnInitialUpdate()
		v.ShowWindow(win32con.SW_SHOW)
		if v and v._obj_ and v.GetSafeHwnd():
			v.DestroyWindow()

	def newviewobj(self,context='vview_'):
		doc=self.GetActiveDocument()
		if context=='cview_':
			return _ChannelView(doc)
		elif context=='hview_':
			return _HierarchyView(doc)
		elif context=='pview_':
			return _PlayerView(doc)
		elif context=='leview_':
			return _LinkEditView(doc)
		elif context=='lview_':
			return _LayoutView(doc)
		elif context=='sview_':
			return _SourceView(doc)
		elif context=='vview_':
			return _VoidView(doc)
		else:
			return _VoidView(doc)

	def isappview(self,v):
		return v.__class__!=self._VoidViewclass

	def closeview(self):
		id=usercmdui.class2ui[usercmd.CLOSE_WINDOW].id
		self.OnUserCmd(id,0)

	def setviewtab(self,viewid):
		if hasattr(self,'_wndDlgBar'):
			self._wndDlgBar.settab(viewid)

	def setviewcl(self,viewclass,id=None,context='vview_'):
		doc=self.GetActiveDocument()
		if not doc:doc=docview.Document(docview.DocTemplate())
		if not id: v = viewclass(doc)
		else: v = viewclass(doc,id)			
		v.CreateWindow(self)
		self.SetActiveView(v)
		self.setviewtab(context)
		self.RecalcLayout()
		v.OnInitialUpdate()
		v.ShowWindow(win32con.SW_SHOW)
	def replaceviewcl(self,classobj,id=None,context='vview_'):
		v=self.GetActiveView()
		self.setviewcl(classobj,id,context)
		v.DestroyWindow()

	def setwaiting(self,context='view'):
		pass

	def setready(self,context='view'):
		self.ActivateFrame()
		pass

	def close(self):
		self.set_commandlist(None,'document')
		self.settitle(None,'document')
		if IsEditor: 
			self.setEditorFrameToolbar()
			if hasattr(self,'_wndDlgBar'):
				self._wndDlgBar.DestroyWindow()
				self.RecalcLayout()
						
	def onSize(self,params):
		self.RecalcLayout()
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		self._rect=self._canvas=0,0,msg.width(),msg.height()
		if hasattr(self,'_wndDlgBar'):
			self._wndDlgBar.sizeto(msg.width(),msg.height())

	def set_commandlist(self,commandlist,context='view'):
		contextcmds=self._activecmds[context]
		menu=self.GetMenu()
		for id in contextcmds.keys():
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)
			menu.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_UNCHECKED)
		contextcmds.clear()
		toolsmenu=AppMenu.ClearSubmenu(menu,5)
		if not commandlist: return
		for cmd in commandlist:
			usercmd_ui = usercmdui.class2ui[cmd.__class__]
			id=usercmd_ui.id
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id)
			contextcmds[id]=cmd
			if usercmd_ui.cat=='Tools' and usercmd_ui.dispstr:
				toolsmenu.AppendMenu(win32con.MF_STRING,id,usercmd_ui.dispstr)


	def set_toggle(self, cmdcl, onoff):
		id=usercmdui.class2ui[cmdcl].id
		flags = win32con.MF_BYCOMMAND
		if onoff==0:flags = flags | win32con.MF_UNCHECKED
		else:flags = flags | win32con.MF_CHECKED
		(self.GetMenu()).CheckMenuItem(id,flags)

	# placeholder for 
	def set_dynamiclist(self, cmd, list):
		return
		self._dynamiclists[cmd]=list
		print '=========dynamic list for',cmd
		for item in list:
			print item

	def OnUpdateCmdEnable(self,cmdui):
		cmdui.Enable(1)

	def OnUpdateCmdDissable(self,cmdui):
		cmdui.Enable(0)

	def OnUserCmd(self,id,code):
		cmd=None
		for context in self._activecmds.keys():
			contextcmds=self._activecmds[context]
			if contextcmds.has_key(id):
				cmd=contextcmds[id]
		if cmd is not None and cmd.callback is not None:
			apply(apply,cmd.callback)

	def settitle(self,title,context='view'):
		self._qtitle[context]=title
		qtitle=''
		if self._qtitle['document']:
			qtitle= qtitle + self._qtitle['document'] + ' - '
		elif self._qtitle['view']:
				qtitle=qtitle + self._qtitle['view'] + ' - '
		qtitle=qtitle + self._qtitle['frame']
		self.SetWindowText(qtitle)

	# not implemented
	def set_adornments(self, adornments):
		return
		print "_FrameWnd.set_adornments",adornments
		if not adornments: return
		if adornments.has_key('toolbar') and adornments['toolbar']:
			submenu=win32ui.CreateMenu()
			for item in adornments['toolbar']:
				submenu.AppendMenu(win32con.MF_STRING,self._nextcmdid,item[0])
				self.HookCommand(self.OnCmdX,self._nextcmdid)
				self._id2class[self._nextcmdid]=item[1]
				self._nextcmdid=self._nextcmdid+1
			menu=self.GetMenu()
			menu.AppendMenu(win32con.MF_POPUP,submenu.GetHandle(),"&File")
			self.DrawMenuBar()
			

	def onClose(self, params):
		self.OnUserCmd(usercmdui.EXIT_UI.id,0)
		self.onEvent(WindowExit)

	# should be set from adornments
	# but for now...
	def setEditorFrameToolbar(self):
		self._wndToolBar.AllocateButtons(4)

		id=usercmdui.class2ui[usercmd.NEW_DOCUMENT].id
		self._wndToolBar.SetButtonInfo(0,id,afxexttb.TBBS_BUTTON,0)

		self._wndToolBar.SetButtonInfo(1,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.OPEN].id
		self._wndToolBar.SetButtonInfo(2,id,afxexttb.TBBS_BUTTON, 1)

		id=usercmdui.class2ui[usercmd.SAVE].id
		self._wndToolBar.SetButtonInfo(3,id,afxexttb.TBBS_BUTTON, 2)
				
		self.ShowControlBar(self._wndToolBar,1,0)

	# should be set from from adornments
	# but for now...
	def setEditorDocumentToolbar(self):
		self._wndToolBar.AllocateButtons(13)

		id=usercmdui.class2ui[usercmd.NEW_DOCUMENT].id
		self._wndToolBar.SetButtonInfo(0,id,afxexttb.TBBS_BUTTON,0)

		self._wndToolBar.SetButtonInfo(1,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.OPEN].id
		self._wndToolBar.SetButtonInfo(2,id,afxexttb.TBBS_BUTTON, 1)

		id=usercmdui.class2ui[usercmd.SAVE].id
		self._wndToolBar.SetButtonInfo(3,id,afxexttb.TBBS_BUTTON, 2)
	
		# Play Toolbar
		self._wndToolBar.SetButtonInfo(4,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.RESTORE].id
		self._wndToolBar.SetButtonInfo(5,id,afxexttb.TBBS_BUTTON, 6)

		id=usercmdui.class2ui[usercmd.CLOSE].id
		self._wndToolBar.SetButtonInfo(6,id,afxexttb.TBBS_BUTTON, 7)

		self._wndToolBar.SetButtonInfo(7,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.PLAY].id
		self._wndToolBar.SetButtonInfo(8,id,afxexttb.TBBS_BUTTON, 9)

		id=usercmdui.class2ui[usercmd.PAUSE].id
		self._wndToolBar.SetButtonInfo(9,id,afxexttb.TBBS_BUTTON, 10)

		id=usercmdui.class2ui[usercmd.STOP].id
		self._wndToolBar.SetButtonInfo(10,id,afxexttb.TBBS_BUTTON, 11)

		self._wndToolBar.SetButtonInfo(11,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,12);
	
		id=usercmdui.class2ui[usercmd.HELP].id
		self._wndToolBar.SetButtonInfo(12,id,afxexttb.TBBS_BUTTON, 12)

		self.ShowControlBar(self._wndToolBar,1,0)


	# should be set from from adornments
	# but for now...
	def setPlayerToolbar(self):
		self._wndToolBar.AllocateButtons(9)

		id=usercmdui.class2ui[usercmd.OPEN].id
		self._wndToolBar.SetButtonInfo(0,id,afxexttb.TBBS_BUTTON, 1)

		# Play Toolbar
		self._wndToolBar.SetButtonInfo(1,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.CLOSE].id
		self._wndToolBar.SetButtonInfo(2,id,afxexttb.TBBS_BUTTON, 7)

		self._wndToolBar.SetButtonInfo(3,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.PLAY].id
		self._wndToolBar.SetButtonInfo(4,id,afxexttb.TBBS_BUTTON, 9)

		id=usercmdui.class2ui[usercmd.PAUSE].id
		self._wndToolBar.SetButtonInfo(5,id,afxexttb.TBBS_BUTTON, 10)

		id=usercmdui.class2ui[usercmd.STOP].id
		self._wndToolBar.SetButtonInfo(6,id,afxexttb.TBBS_BUTTON, 11)
	
		self._wndToolBar.SetButtonInfo(7,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.HELP].id
		self._wndToolBar.SetButtonInfo(8,id,afxexttb.TBBS_BUTTON, 12)
	
		self.ShowControlBar(self._wndToolBar,1,0)

###########################################################
###########################################################
###########################################################
class _SubWindow(cmifwnd._CmifWnd,window.Wnd):
	def __init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z=0):
		#print 'SubWindow created with parent',parent
		cmifwnd._CmifWnd.__init__(self)
		self._do_init(parent)
		self._window_type = type_channel
		self._next_create_box = []
		self._topwindow = parent._topwindow

		if z < 0:
			raise error, 'invalid z argument'
		self._z = z
		self._align = ' '

		x, y, w, h = rel_coordinates
		if not x or x<0:x=0
		if not y or w<0:y=0
		if not w:w=100
		if not h:h=100
		if w == 0 or h == 0:
			showmessage('Creating subwindow with zero dimension',mtype = 'warning')
		if w == 0:w = float(self._rect[WIDTH]) / parent._rect[WIDTH]
		if h == 0:h = float(self._rect[HEIGHT]) / parent._rect[HEIGHT]
		rel_coordinates=x, y, w, h
		x, y,w,h = parent._convert_coordinates(rel_coordinates)

		self._rect = 0, 0, w, h
		self._canvas = 0, 0, w, h
		self._sizes = rel_coordinates
		self._rectb = x, y, w, h
		
		self._convert_color = parent._convert_color

		# create an artificial name 
		self._num = len(parent._subwindows)+1
		self._title = "Child "+ `self._num`+" of " + parent._title 

		
		# insert window in _subwindows list at correct z-order
		for i in range(len(parent._subwindows)):
			if self._z >= parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.append(self)
			
		# if a parent is transparent all of its childs must be transparent	
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			if transparent not in (-1, 0, 1):
				raise error, 'invalid value for transparent arg'
			self._transparent = transparent

		### Create the real OS window
		### taking into account the window type and transparency flag
		x,y,w,h=self._rectb
		if self._transparent==0:
			window.Wnd.__init__(self,win32ui.CreateWnd())
			self._brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
			self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
			self._icon=0
			self._clstyle=win32con.CS_DBLCLKS
			self._style=win32con.WS_CHILD #|win32con.WS_CLIPSIBLINGS
			self._exstyle = win32con.WS_EX_CONTROLPARENT
			self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
			self.CreateWindowEx(self._exstyle,self._strclass,self._title,self._style,
				(x,y,x+w,y+h),self._parent,0)
		else:
			# self._transparent is in (1,-1)
			# wnds with -1 are initially transparent
			window.Wnd.__init__(self,win32ui.CreateWnd())
			self._brush=Sdk.GetStockObject(win32con.NULL_BRUSH)
			self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
			self._icon=0
			self._clstyle=win32con.CS_DBLCLKS
			self._style=win32con.WS_CHILD 
			self._exstyle = win32con.WS_EX_TRANSPARENT # | win32con.WS_EX_CONTROLPARENT
			self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
			self.CreateWindowEx(self._exstyle,self._strclass,self._title,self._style,
				(x,y,x+w,y+h),self._parent,0)

		self._wnd=self._obj_ # historic alias but useful to markup externals
		self._hWnd=self.GetSafeHwnd()

		# set the newly created OS window in the correct relative z-position
		ix = parent._subwindows.index(self)
		if ix != 0: 
			self.SetWindowPos(parent._subwindows[ix-1].GetSafeHwnd(), 
				(0,0,0,0),win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		else:
			self.SetWindowPos(win32con.HWND_TOP ,(0,0,0,0),
				win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
			
		# do not enter WM_PAINT since we have provided the virtual OnPaint
		# that will be automatically called by the framework
		rc= {
			win32con.WM_RBUTTONDOWN:self.onRButtonDown,
			win32con.WM_LBUTTONDBLCLK:self.onLButtonDblClk,
			win32con.WM_LBUTTONDOWN:self.onLButtonDown,
			win32con.WM_LBUTTONUP:self.onLButtonUp,
			win32con.WM_MOUSEMOVE:self.onMouseMove,
			win32con.WM_CLOSE:self.onClose}
		self._enable_response(rc)

		self.show()

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		win= _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		return win

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)
		return win

	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)


	def settitle(self, title):
		raise error, 'can only settitle at top-level'


	def pop(self):
		parent = self._parent	
		# put self in front of all siblings with equal or lower z
		if self is not parent._subwindows[0]:
			parent._subwindows.remove(self)
			for i in range(len(parent._subwindows)):
				if self._z >= parent._subwindows[i]._z:
					parent._subwindows.insert(i, self)
					break
			else:
				parent._subwindows.append(self)
		ix = parent._subwindows.index(self)
		if ix != 0: 
			self.SetWindowPos(parent._subwindows[ix-1]._wnd.GetSafeHwnd(), 
				(0,0,0,0),win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		else:
			self.SetWindowPos(win32con.HWND_TOP ,(0,0,0,0),
				win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		#parent.pop()
	

	def push(self):
		parent = self._parent
		# put self behind all siblings with equal or higher z
		if self is parent._subwindows[-1]:
			# already at the end
			return
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)-1,-1,-1):
			if self._z <= parent._subwindows[i]._z:
				parent._subwindows.insert(i+1, self)
				break
		else:
			parent._subwindows.insert(0, self)
		
		ix = parent._subwindows.index(self)
		if ix != 0: 
			self.SetWindowPos(parent._subwindows[ix-1]._wnd.GetSafeHwnd(),
				(0,0,0,0),win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		else:
			self.SetWindowPos(win32con.HWND_TOP ,
				(0,0,0,0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)

	def OnPaint(self):
		dc, paintStruct = self._obj_.BeginPaint()
		if self._active_displist:
			self._active_displist._render(dc,paintStruct[2],1)
		self._obj_.EndPaint(paintStruct)

	def OnEraseBkgnd(self,dc):
		if self._transparent==0: 
			return self._obj_.OnEraseBkgnd(dc)
		parent = self.GetParent()
		ptList=[(0,0),]
		ptOffset = self.MapWindowPoints(parent,ptList)[0]
		ptOldOrg=dc.OffsetWindowOrg(ptOffset)
		parent.SendMessage(win32con.WM_ERASEBKGND,dc.GetSafeHdc())
		dc.SetWindowOrg(ptOldOrg)
		return 1

	# Browsing support
	def RetrieveUrl(self,url):
		if not hasattr(self, '_browser'):
			self._browser=WebBrowser()
			self._browser.create(self._canvas,self)	
		# temp test !!!!!!
		import os
		if url[:2] != '//' or url[2:3] == '/' or url[2:3]=='\\':
			if url[2:3] == '/' or url[2:3]=='\\':
				pass #url = 'file:///' +  url[:1] + '|' + url[3:]
			else:
				url = os.getcwd()+'\\'+ url
				pass #url = 'file:///' +  url[:1] + '|' + url[3:]
		self._browser.Navigate(url)
		self._browser.show()

	def _resize_controls(self):
		if hasattr(self, '_browser'):
			if self._browser:self._browser.resize(self._canvas)
	def CreateCallback(self,cbcmifanchor):
		if not hasattr(self, '_web_callbacks'):
			self._web_callbacks=[]
		self._web_callbacks.append(cbcmifanchor)
	def SetBkColor(self,bg):
		pass
	def SetFgColor(self,fg):
		pass

################################
class WebBrowser(window.Wnd):
	def __init__(self):
		window.Wnd.__init__(self,win32ui.CreateWebBrowser())
	def create(self,rc,parent):
		x,y,w,h=rc
		self.CreateBrowserWnd((x,y,x+w,y+h),parent)	
	def hide(self):
		if self.IsWindow():self.ShowWindow(win32con.SW_HIDE)
	def show(self):
		if self.IsWindow():self.ShowWindow(win32con.SW_SHOW)
	def resize(self,rc):
		self.SetWidth(rc[2])
		self.SetHeight(rc[3])
			
class _BrowserSubWindow(_SubWindow):
	def __init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z=0):
		_SubWindow.__init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z)
		x,y,w,h=self._canvas
		self._web_callbacks=[]
		# postpone create WebBrowser 
		self._browser=None

	def CreateCallback(self,cbcmifanchor):
		self._web_callbacks.append(cbcmifanchor)
	def SetBkColor(self,bg):
		pass
	def SetFgColor(self,fg):
		pass

	def RetrieveUrl(self,url):
		if not self._browser:
			self._browser=WebBrowser()
			self._browser.create(self._canvas,self)	
		# temp test !!!!!!
		import os
		if url[:2] != '//' or url[2:3] == '/' or url[2:3]=='\\':
			if url[2:3] == '/' or url[2:3]=='\\':
				pass #url = 'file:///' +  url[:1] + '|' + url[3:]
			else:
				url = os.getcwd()+'\\'+ url
				pass #url = 'file:///' +  url[:1] + '|' + url[3:]
		self._browser.Navigate(url)
		self._browser.show()

	def _resize_controls(self):
		if self._browser:self._browser.resize(self._canvas)

	def OnEraseBkgnd(self,dc):
		pass

	def _destroy_displists_tree(self):
		pass
	def _create_displists_tree(self):
		pass

	def onMouseMove(self, params):
		pass

	def close(self):
		self.arrowcache = {}
		self.hide()
		if self._parent is None:
			return		# already closed
		self._parent._subwindows.remove(self)
		self._parent = None
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		if self._browser:
			self._browser.hide()
		if self._obj_ and self.IsWindow():
			self.destroy_menu()
			self.DestroyWindow()			
		del self._topwindow
		self._obj_ = None


############################################
# a generic wnd
class MfcOsWnd(window.Wnd):
	"""Generic MfcOsWnd class"""
	def __init__ (self):
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._clstyle=0
		self._style=0
		self._exstyle=0
		self._icon=0
		self._cursor=0
		self._brush=0

	def setClstyle(self,clstyle):
		self._clstyle=clstyle

	def setStyle(self,style):
		self._style=style

	def setExstyle(self,exstyle):
		self._exstyle=exstyle

	def setIcon(self,icon):
		self._icon=icon

	def setIconApplication(self):
		self._icon=Afx.GetApp().LoadIcon(win32con.IDI_APPLICATION)

	def setStandardCursor(self,cursor):
		self._cursor=Afx.GetApp().LoadStandardCursor(cursor)

	def setStockBrush(self,idbrush):
		self._brush=Sdk.GetStockObject(idbrush)
	def setBrush(self,brush):
		self._brush=brush

	def create(self,title='untitled',x=0,y=0,width=200,height=150,parent=None,id=0):
		# register
		strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		# create
		self.CreateWindowEx(self._exstyle,strclass,title,self._style,
			(x, y, width, height),parent,id)


###########################################################
###########################################################
###########################################################

class _Window(cmifwnd._CmifWnd,_rbtk,window.Wnd):
	def __init__(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
		     units = UNIT_MM, adornments = None,
		     canvassize = None, commandlist = None, resizable = 1):
		cmifwnd._CmifWnd.__init__(self)
		_rbtk.__init__(self)
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._do_init(parent)
		parent._subwindows.insert(0, self)

		self._title = title		
		self._topwindow = self
		self._window_type = SINGLE
		self._depth = toplevel.getscreendepth()

		if not x:x=0
		if not y:y=0
		if not w:w=100
		if not h:h=100
		x,y,w,h = to_pixels(x,y,w,h,units)
		self._sizes = (float(x)/scr_width_pxl,float(y)/scr_height_pxl,float(w)/scr_width_pxl,float(h)/scr_height_pxl)
		self._rectb=x,y,w,h
		self.setcursor('watch')
		
		# create a toplevel OS Wnd
		xp=x;yp=y
		self._clstyle=win32con.CS_DBLCLKS
		self._style=win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
		self._exstyle=0
		self._icon=Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED)
		self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		self._brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		self.CreateWindowEx(self._exstyle,self._strclass,self._title,self._style,
			(xp,yp,xp+w,yp+h),None,0)

		# historic alias that we keep only
		# to markup functions as external to this module
		# and as an attribute signiture
		self._wnd=self._obj_
		self._hWnd=self.GetSafeHwnd()

		l,t,r,b=self.GetClientRect()
		w,h=r-l,b-t
		self._canvas = self._rect=(0,0,w,h)

		rc= {
			win32con.WM_RBUTTONDOWN:self.onRButtonDown,
			win32con.WM_LBUTTONDBLCLK:self.onLButtonDblClk,
			win32con.WM_SIZE:self.onSize,
			win32con.WM_LBUTTONDOWN:self.onLButtonDown,
			win32con.WM_LBUTTONUP:self.onLButtonUp,
			win32con.WM_MOUSEMOVE:self.onMouseMove,
			win32con.WM_CLOSE:self.onClose}
		self._enable_response(rc)

#		self._menu = None
#		if menubar is not None:
#			self.create_menu(menubar)

		self.ShowWindow(win32con.SW_SHOW)

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		if type_channel==HTM:
			win= _BrowserSubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		else:
			win= _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		return win

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)
		return win


	def OnPaint(self):
		dc, paintStruct = self._obj_.BeginPaint()
		if self._active_displist:
			self._active_displist._render(dc,paintStruct[2],1)
		self._obj_.EndPaint(paintStruct)

	def onSize(self, params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		width,height=msg.width(), msg.height()

		self.arrowcache = {}
		w = _in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			try:
				w._rb_cancel()
			except _rb_done:
				pass
			w._next_create_box[0:0] = next_create_box
		self._do_resize(width, height)
		if w:
			w._rb_end()
			raise _rb_done


	################ TO BE IMPLEMENTED
	def set_dynamiclist(self, cmd, list):
		print '_Window.set_dynamiclist',cmd, list


	def set_adornments(self, adornments):
		print "_Window.set_adornments",adornments

	def set_commandlist(self, list):
		print "_Window.set_commandlist",list

	def set_toggle(self, command, onoff):
		print "_Window.set_toggle",command, onoff
		
