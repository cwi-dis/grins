__version__ = "$Id$"


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

import win32mu
import usercmd,usercmdui
from components import *

import win32menu, MenuTemplate

toplevel=None # global set by AppTopLevel

 
###########################################################
# import window core stuff
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl
import cmifwnd	
import afxexttb # part of generated afxext.py


##################################
from FormServer import FormServer
from ViewServer import ViewServer,appview

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
		wndToolBar.LoadToolBar(grinsRC.IDR_GRINSED)
		#wndToolBar.LoadBitmap(grinsRC.IDB_GRINSED1)
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
		import components
		self._tab=components.TabCtrl(self,grinsRC.IDC_TAB_GRINSVIEWS)
		self._tab.attach_to_parent()
		for viewno in range(len(appview.keys())):
			self._tab.insertitem(viewno,appview[viewno]['title'])
		rc=win32mu.Rect(parent.GetClientRect())
		self.sizeto(rc.width(),rc.height())

	def getid(self):
		return grinsRC.IDD_GRINSEDBAR
	def sizeto(self,w,h):
		rc=win32mu.Rect(self._tab.getwindowrect())
		self._tab.setwindowpos(0,(0,0,w,rc.height()),
			win32con.SWP_NOMOVE|win32con.SWP_NOZORDER)
	def postcmd(self,wnd,viewno):
		if viewno==0: return
		cmdcl=appview[viewno]['cmd']
		usercmd_ui = usercmdui.class2ui[cmdcl]
		wnd.PostMessage(win32con.WM_COMMAND,usercmd_ui.id)
	def settab(self,ix):
		self._tab.setcursel(ix)

####################################
		
class MDIFrameWnd(window.MDIFrameWnd,cmifwnd._CmifWnd,ViewServer):
	def __init__(self):
		window.MDIFrameWnd.__init__(self)
		cmifwnd._CmifWnd.__init__(self)
		ViewServer.__init__(self,self)
		self._do_init(toplevel)
		self._formServer=FormServer(self)

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

	def registerwndclass(self):
		# register top frame class
		clstyle=win32con.CS_DBLCLKS
		exstyle=0
		icon=Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED)
		cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		brush=0 #Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		return Afx.RegisterWndClass(clstyle,cursor,brush,icon)

	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)

		# sizes
		cs.cx,cs.cy=(3*scr_width_pxl/4),(3*scr_height_pxl/4)
		cs.x,cs.y=x=scr_width_pxl/8,scr_height_pxl/8

		# menu from MenuTemplate
		menu=win32menu.Menu()
		menu.create_from_menubar_spec_list(MenuTemplate.MENUBAR,self.get_cmdclass_id)
		cs.hMenu=menu.GetHandle()

		return cs.to_csd()
	
	def get_cmdclass_id(self,cmdcl):
		if cmdcl in usercmdui.class2ui.keys():
			return usercmdui.class2ui[cmdcl].id
		else: return -1

	# this is called after CWnd::OnCreate 
	def OnCreate(self, createStruct):
		self.HookMessage(self.onSize,win32con.WM_SIZE)

		# the view is responsible for user input
		# so do not hook other messages

		# direct all cmds to self.OnUserCmd but dissable them
		for cmdcl in usercmdui.class2ui.keys():
			id=usercmdui.class2ui[cmdcl].id
			self.HookCommand(self.OnUserCmd,id)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,afxres.ID_WINDOW_CASCADE)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,afxres.ID_WINDOW_TILE_VERT)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,afxres.ID_WINDOW_TILE_HORZ)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_CASCADE)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_TILE_VERT)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_TILE_HORZ)


		client=self.GetMDIClient()
		client.HookMessage(self.OnMdiRefreshMenu,win32con.WM_MDIREFRESHMENU)
		client.HookMessage(self.OnMdiActivate,win32con.WM_MDIACTIVATE)
		# hook tab sel change
		TCN_FIRST =-550;TCN_SELCHANGE  = TCN_FIRST - 1
		self.HookNotify(self.OnNotifyTcnSelChange,TCN_SELCHANGE)

		return 0
	
	# mirror mdi window-menu to tab bar	
	def OnMdiRefreshMenu(self,params):
		msg=win32mu.Win32Msg(params)
		#print 'OnMdiRefreshMenu',msg._wParam,msg._lParam
	def OnMdiActivate(self,params):
		msg=win32mu.Win32Msg(params)
		#print 'OnMdiActivate',msg._wParam,msg._lParam
		
	def OnNotifyTcnSelChange_X(self, nm, nmrest=(0,)):
		self.ActivateFrame()
		hwndFrom,idFrom,code=nm
		if idFrom==grinsRC.IDC_TAB_GRINSVIEWS:
			viewno=self._wndDlgBar._tab.getcursel()
			if viewno==0:
				self.close_all_views()
			elif appview[viewno]['obj']:
				self.MDIActivate(appview[viewno]['obj'])
			else:
				self._wndDlgBar.postcmd(self,viewno)
			return 1
		return 0
	def OnNotifyTcnSelChange(self, nm, nmrest=(0,)):
		self.ActivateFrame()
		hwndFrom,idFrom,code=nm
		if idFrom==grinsRC.IDC_TAB_GRINSVIEWS:
			viewno=self._wndDlgBar._tab.getcursel()
			if appview[viewno]['obj']:
				self.MDIActivate(appview[viewno]['obj'])
			return 1
		return 0

	def OnWndUserCmd(self,id,code):
		client=self.GetMDIClient()
		if id==afxres.ID_WINDOW_TILE_HORZ:
			client.SendMessage(win32con.WM_MDITILE,win32con.MDITILE_HORIZONTAL)			
		elif id==afxres.ID_WINDOW_TILE_VERT:
			client.SendMessage(win32con.WM_MDITILE,win32con.MDITILE_VERTICAL)			
		elif id==afxres.ID_WINDOW_CASCADE:
			client.SendMessage(win32con.WM_MDICASCADE)			
			
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
		self.settitle(title,'document')
		self.set_commandlist(commandlist,'document')
		if IsEditor:
			self.setEditorDocumentToolbar()
			#self._wndDlgBar=GRiNSDlgBar(self)
			self.RecalcLayout()			
		self.ActivateFrame()
		return self
	
	def newwindow(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
		     units = UNIT_MM, adornments = None,
		     canvassize = None, commandlist = None, resizable = 1):
		viewno=self.getviewno('pview_')
		vf=appview[viewno]['obj']
		self.MDIActivate(vf)
		return vf.GetActiveView()
		return _Window(parent, x, y, w, h, title, defcmap, pixmap,
		     units,adornments,canvassize, commandlist, resizable)

	def getdoc(self):
		if self.countMDIChildWnds()==0:
			self._doc=docview.Document(docview.DocTemplate())
		return self._doc

	def newChildFrame(self,view,decor=None):
		return ChildFrame(view,decor)
	def Activate(self,view):
		self.MDIActivate(view)		
	def getPrefRect(self):
		rc= win32mu.Rect(self.GetClientRect())
		return rc.width()/8,rc.height()/8,7*rc.width()/8,7*rc.height()/8

	# simulate user	closing
	def close_all_views(self):
		currentChild=None
		count=0
		l=[]
		while 1:
			currentChild=self.getNextMDIChildWnd(currentChild)
			if currentChild:l.append(currentChild)
			else: break
		for w in l:
			w.SendMessage(win32con.WM_CLOSE)

	def setviewtab(self,viewno):
		if hasattr(self,'_wndDlgBar'):
			self._wndDlgBar.settab(viewno)

	def setwaiting(self):
		self.BeginWaitCursor();

	def setready(self):
		self.EndWaitCursor();
		self.ActivateFrame()


	def close(self):
		# 1. first close all views
		self.close_all_views()

		# 2. then the document
		self.set_commandlist(None,'document')
		self.settitle(None,'document')
		if IsEditor: 
			self.setEditorFrameToolbar()
			if hasattr(self,'_wndDlgBar'):
				self._wndDlgBar.DestroyWindow()
				self.RecalcLayout()

		# 3. if there is another top-level frame
		# we should close self frame
		pass
		
		# enforce our design decision
		# for now at least 
		if IsPlayer:
			d=self._activecmds['frame']
			self.enable_commandlist('document',0)
			self._activecmds['document'].clear()
			self.enable_commandlist('view',0)
			self._activecmds['view'].clear()
			cmdlist=[]
			for k in d.keys():cmdlist.append(d[k])
			self.set_commandlist(cmdlist,'frame')

	def onSize(self,params):
		self.RecalcLayout()
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		self._rect=self._canvas=0,0,msg.width(),msg.height()
		if hasattr(self,'_wndDlgBar'):
			self._wndDlgBar.sizeto(msg.width(),msg.height())

	def maximize(self,child):
		client=self.GetMDIClient()
		client.SendMessage(win32con.WM_MDIMAXIMIZE,child.GetSafeHwnd())

	def set_commandlist(self,commandlist,context='view'):
		if IsPlayer and context=='view' and commandlist==None: return
		contextcmds=self._activecmds[context]
		menu=self.GetMenu()
		for id in contextcmds.keys():
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)
			menu.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_UNCHECKED)
		contextcmds.clear()
		if not commandlist: return
		for cmd in commandlist:
			usercmd_ui = usercmdui.class2ui[cmd.__class__]
			id=usercmd_ui.id
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id)
			contextcmds[id]=cmd

	def enable_commandlist(self,context,enable):
		contextcmds=self._activecmds[context]
		commandlist=contextcmds.values()
		if enable:
			for cmd in commandlist:
				usercmd_ui = usercmdui.class2ui[cmd.__class__]
				self.HookCommandUpdate(self.OnUpdateCmdEnable,usercmd_ui.id)
		else:
			menu=self.GetMenu()
			for cmd in commandlist:
				usercmd_ui = usercmdui.class2ui[cmd.__class__]
				self.HookCommandUpdate(self.OnUpdateCmdDissable,usercmd_ui.id)
				menu.CheckMenuItem(usercmd_ui.id,win32con.MF_BYCOMMAND | win32con.MF_UNCHECKED)
			
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

	def GetUserCmdId(self,cmdcl):
		return usercmdui.class2ui[cmdcl].id

	def GetUserCmd(self,cmdcl):
		id=usercmdui.class2ui[cmdcl].id
		cmd=None
		for context in self._activecmds.keys():
			contextcmds=self._activecmds[context]
			if contextcmds.has_key(id):
				cmd=contextcmds[id]
		return cmd

	# MUST BE CORRECTED
	# call first active cmd from close sequence
	def fire_cmd_close(self):
		id=usercmdui.class2ui[usercmd.CLOSE_WINDOW].id
		self.OnUserCmd(id,0)

	def fire_cmd(self,cmdcl):
		id=usercmdui.class2ui[cmdcl].id
		self.OnUserCmd(id,0)

		
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
			

	def OnClose(self):
		self.PostMessage(win32con.WM_COMMAND,usercmdui.EXIT_UI.id)

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
		self._wndToolBar.AllocateButtons(15)

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
	
		id=usercmdui.class2ui[usercmd.CLOSE_WINDOW].id
		self._wndToolBar.SetButtonInfo(12,id,afxexttb.TBBS_BUTTON, 14)

		self._wndToolBar.SetButtonInfo(13,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,12);

		id=usercmdui.class2ui[usercmd.HELP].id
		self._wndToolBar.SetButtonInfo(14,id,afxexttb.TBBS_BUTTON, 12)

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

	def countMDIChildWnds(self):
		currentChild=None
		count=0
		while 1:
			currentChild=self.getNextMDIChildWnd(currentChild)
			if currentChild:count=count+1
			else: break
		return count

	def getNextMDIChildWnd(self,currentChild=None):
		client=self.GetMDIClient()
		if not currentChild:
			# Get the first child window.
			currentChild=client.GetWindow(win32con.GW_CHILD)
		else:
			# Get the next child window in the list.
			currentChild=currentChild.GetWindow(win32con.GW_HWNDNEXT)
		if not currentChild:
			# No child windows exist in the MDIClient,
			# or we are at the end of the list. This check
			# will terminate any recursion.
			return None
		# Check the kind of window
		owner=currentChild.GetWindow(win32con.GW_OWNER)
		if not owner:
			if currentChild.IsKindOfMDIChildWnd():
	            # MDIChildWnd or a derived class.
				return currentChild
			else:
				# Window is foreign to the MFC framework.
				# Check the next window in the list recursively.
				return self.GetNextMDIChildWnd(currentChild)
		else:
			# Title window associated with an iconized child window.
			# Recurse over the window manager's list of windows.
			return self.GetNextMDIChildWnd(currentChild)	

