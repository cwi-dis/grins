__version__ = "$Id$"


""" @win32doc|MainFrame
The main class in this module is the MDIFrameWnd.
There is one to one corespondance between an MDIFrameWnd
instance and a document, and between a document to a 
TopLevelDialog instance. When the application has
open documents an instance of an MDIFrameWnd represents 
visually the open document. 
When there no documents open the MDIFrameWnd
just holds the toolbar and the menu and represents visualy 
the application and its main control panel.

The main purpose of an MDIFrameWnd instance is to provide 
controls to the user (the menu and  the toolbars)
and visually confine the document's views and other windows

The Multiple Document Interface (MDI) is a specification for applications that handle
multiple documents or views in MS Windows. This specification has also an operating system
support. When you create an MDI window the operating system recognizes the fact and
delivers to the application a standard
set of messages concerning mainly the 
parent-child structure, the windows menu and the child activation.

There is an MFC wrapper class for an MDI window, the CMDIFrameWnd. 
Objects of this class are exported
to python through the win32ui pyd as objects of type PyMDIFrameWnd.
The MDIFrameWnd defined in this module inherits from this class.

MDIFrameWnd decoration:
Main Menu: contains application level commands, 
	document level commands and active view commands.
	It contains also dynamic submenus depending on the document
	and the active view.
Dynamic Toolbar with states: Player,Editor no doc,Editor with doc
"""


# win32 libs
import win32ui, win32con, win32api 
Sdk = win32ui.GetWin32Sdk()
Afx = win32ui.GetAfx()
from win32ig import win32ig

# constants
from types import *
from appcon import *
from WMEVENTS import *
import afxexttb
import grinsRC
import sysmetrics
import afxres, commctrl

# utilities
import win32mu
import math

# commands
import usercmd, wndusercmd, usercmdui

# globals 
import __main__

# menus
import win32menu, MenuTemplate

# dialogs
import win32dialog


import settings
if settings.user_settings.get('use_nodoc_menubar'):
	USE_NODOC_MENUBAR = 1
else:
	USE_NODOC_MENUBAR = 0
import features

###########################################################

# views types
from _LayoutView import _LayoutView
from _LayoutView2 import _LayoutView2
from _UsergroupView import _UsergroupView
from _TransitionView import _TransitionView
from _LinkView import _LinkView
from _StructView import _StructView
from _SourceView import _SourceView

#  Player views
from _PlayerView import _PlayerView  
_SourceView=_SourceView

# editor document views
_HierarchyView=_StructView
_ChannelView=_StructView
_LinkView=_LinkView
_LayoutView=_LayoutView
_LayoutView2=_LayoutView2

# player document views
if IsPlayer:
	usercmd.HIDE_PLAYERVIEW=usercmd.CLOSE
	usercmd.HIDE_HIERARCHYVIEW=None
	usercmd.HIDE_CHANNELVIEW=None
	usercmd.HIDE_LINKVIEW=None
	usercmd.HIDE_LAYOUTVIEW=None
	usercmd.HIDE_USERGROUPVIEW=None
	usercmd.HIDE_TRANSITIONVIEW=None
	usercmd.HIDE_SOURCE=usercmd.SOURCE
	usercmd.HIDE_LAYOUTVIEW2=None
	usercmd.HIDE_TEMPORALVIEW=None

appview={
	0:{'cmd':usercmd.HIDE_PLAYERVIEW,'title':'Player','id':'pview_','class':_PlayerView,},
	1:{'cmd':usercmd.HIDE_HIERARCHYVIEW,'title':'Structure view','id':'hview_','class':_HierarchyView,},
	2:{'cmd':usercmd.HIDE_CHANNELVIEW,'title':'Timeline view','id':'cview_','class':_ChannelView,},
	3:{'cmd':usercmd.HIDE_LINKVIEW,'title':'Hyperlinks','id':'leview_','class':_LinkView,'freezesize':1},
	4:{'cmd':usercmd.HIDE_LAYOUTVIEW,'title':'Layout view','id':'lview_','class':_LayoutView,'freezesize':1},
	5:{'cmd':usercmd.HIDE_USERGROUPVIEW,'title':'User groups','id':'ugview_','class':_UsergroupView,'freezesize':1},
	6:{'cmd':usercmd.HIDE_TRANSITIONVIEW,'title':'Transitions','id':'trview_','class':_TransitionView,'freezesize':1},
	7:{'cmd':usercmd.HIDE_SOURCE,'title':'Source','id':'sview_','class':_SourceView,'hosted':0},
	8:{'cmd':usercmd.HIDE_LAYOUTVIEW2,'title':'Source','id':'lview2_','class':_LayoutView2,'hosted':0},
	9:{'cmd':usercmd.HIDE_TEMPORALVIEW,'title':'Temporal view','id':'tview_','class':_ChannelView,},
}


###########################################################

# forms served
if features.editor:
	from AttrEditForm import AttrEditForm

	appform={
		'attr_edit':{'cmd':-1,'title':'Property Editor','id':'attr_edit','obj':None,'class':AttrEditForm,'freezesize':1},
		}
else:
	appform={}

import features
if not features.lightweight:
##	from NodeInfoForm import NodeInfoForm
##	from AnchorEditForm import AnchorEditForm
	from ArcInfoForm import ArcInfoForm
##	appform['node_info']={'cmd':-1,'title':'NodeInfo Editor','id':'node_info','obj':None,'class':NodeInfoForm,'freezesize':1}
##	appform['anchor_edit']={'cmd':-1,'title':'Anchor Editor','id':'anchor_edit','obj':None,'class':AnchorEditForm,'freezesize':1}
	appform['arc_info']={'cmd':-1,'title':'ArcInfo Editor','id':'arc_info','obj':None,'class':ArcInfoForm,'freezesize':1}

# controls whether to remove or not the minimize button 
# when resize is not allowed. (my preference is NO_MINIMIZEBOX = 1)
NO_MINIMIZEBOX = 0


# temporary:
SHOW_TOOLBAR_COMBO = 1
ID_TOOLBAR_COMBO = grinsRC._APS_NEXT_COMMAND_VALUE + 1000
TOOLBAR_COMBO_WIDTH = 144
TOOLBAR_COMBO_HEIGHT = 10*18 # drop down height

###########################################################
from pywinlib.mfc import window, docview

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
		wndToolBar.EnableDocking(afxres.CBRS_ALIGN_ANY)
		wndToolBar.SetWindowText(AppDispName)
		wndToolBar.ModifyStyle(0, commctrl.TBSTYLE_FLAT)
		window.Wnd.__init__(self,wndToolBar)

		# enable/dissable tools draging
		self._enableToolDrag = 1
		# shortcut for GRiNS private clipboard format
		self.CF_TOOL = Sdk.RegisterClipboardFormat('Tool')
		if self._enableToolDrag:
			self.hookMessages()
			self._dragging = None

	def hookMessages(self):
		self.HookMessage(self.onLButtonDown,win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp,win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove,win32con.WM_MOUSEMOVE)

	def onLButtonDown(self, params):
		if self._enableToolDrag:
			msgpos=win32mu.Win32Msg(params).pos()
			self._dragging = msgpos
		return 1 # continue normal processing

	def onLButtonUp(self, params):
		if self._enableToolDrag:
			if self._dragging: 
				self._dragging = None
		return 1 # continue normal processing
	
	def onMouseMove(self, params):
		if self._enableToolDrag and self._dragging:
			xp, yp = self._dragging
			x, y =win32mu.Win32Msg(params).pos()
			if math.fabs(xp-x)>4 or math.fabs(yp-y)>4:
				str='%d %d' % (xp, yp)
				# start drag and drop
				self.DoDragDrop(self.CF_TOOL, str)
				self._dragging = None
				self.ReleaseCapture()
		return 1 # continue normal processing

###########################################################

# mixins
import win32window
import DropTarget

class MDIFrameWnd(window.MDIFrameWnd, win32window.Window, DropTarget.DropTarget):
	wndpos=None
	wndsize=None
	wndismax=0
	def __init__(self):
		window.MDIFrameWnd.__init__(self)
		win32window.Window.__init__(self)
		DropTarget.DropTarget.__init__(self)
		self._toolbarCombo = []

		# menu support
		self._menu = None		# Dynamically created rightmousemenu
		self._popupmenu = None	# Statically created rightmousemenu (for views)
		self._popup_point =(0,0)
		self._cbld = {}
		
		# window title
		self._title = None

		# scroll indicator
		self._canscroll = 0

		# player state
		self.__playerstate = wndusercmd.TB_STOP

		# full screen player
		self.__fsPlayer = None

	# Create the OS window and set the toolbar	
	def createOsWnd(self,title):
		strclass=self.registerwndclass()		
		self._obj_.Create(strclass,title)

		# toolbar
		self.EnableDocking(afxres.CBRS_ALIGN_ANY)
		self._wndToolBar=GRiNSToolbar(self)
		self.DockControlBar(self._wndToolBar)
		if IsPlayer:
			self.setPlayerToolbar()
			self.LoadAccelTable(grinsRC.IDR_GRINS)
		else:
			self.setEditorFrameToolbar()
			self.LoadAccelTable(grinsRC.IDR_GRINSED)

	# Register the window class
	def registerwndclass(self):
		# register top frame class
		clstyle=win32con.CS_DBLCLKS
		exstyle=0
		#icon=Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED)
		icon=Afx.GetApp().LoadIcon(grinsRC.IDR_GRINSED)
		cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		brush=0 #Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		return Afx.RegisterWndClass(clstyle,cursor,brush,icon)

	# Change window style attributes before it is created
	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)

		# Set sizes (balance forces)
		if not MDIFrameWnd.wndsize or MDIFrameWnd.wndismax:
			MDIFrameWnd.wndsize=win32mu.Point(((3*sysmetrics.scr_width_pxl/4),(3*sysmetrics.scr_height_pxl/4)))
		cs.cx,cs.cy=MDIFrameWnd.wndsize.tuple()
		cxmax=3*sysmetrics.scr_width_pxl/4
		cymax=3*sysmetrics.scr_height_pxl/4
		if cs.cx>cxmax:cs.cx=cxmax
		if cs.cy>cymax:cs.cy=cymax

		#win32window.Window.create(self, None, (0, 0, cs.cx, cs.cy), UNIT_PXL)

		# Set pos (balance forces)
		# if it is the first then center else leave the system to select
		if not MDIFrameWnd.wndpos:
			MDIFrameWnd.wndpos=win32mu.Point((sysmetrics.scr_width_pxl/8,sysmetrics.scr_height_pxl/8))
			cs.x,cs.y=MDIFrameWnd.wndpos.tuple()
		else:
			cs.x=win32con.CW_USEDEFAULT
			cs.y=win32con.CW_USEDEFAULT

		# menu from MenuTemplate
		# hold instance for dynamic menus
		self._mainmenu=win32menu.Menu()
		if USE_NODOC_MENUBAR and hasattr(MenuTemplate,'NODOC_MENUBAR'):
			template=MenuTemplate.NODOC_MENUBAR
		else:
			template=MenuTemplate.MENUBAR
		self._mainmenu.create_from_menubar_spec_list(template,self.get_cmdclass_id)
		cs.hMenu=self._mainmenu.GetHandle()
		return cs.to_csd()


	# Called after the window has been created for further initialization
	# Called after CWnd::OnCreate
	def OnCreate(self, createStruct):
		self.HookMessage(self.onSize,win32con.WM_SIZE)
		self.HookMessage(self.onMove,win32con.WM_MOVE)
		self.HookMessage(self.onKey,win32con.WM_KEYDOWN)
		self.HookMessage(self.onInitMenu,win32con.WM_INITMENU)
		self.HookMessage(self.onActivate,win32con.WM_ACTIVATE)

		# the view is responsible for user input
		# so do not hook other messages

		# direct all cmds to self.OnUserCmd but dissable them
		for cmdcl in usercmdui.class2ui.keys():
			id=usercmdui.class2ui[cmdcl].id
			self.HookCommand(self.OnUserCmd,id)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_CASCADE)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_TILE_VERT)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_TILE_HORZ)
		id=usercmdui.class2ui[wndusercmd.CLOSE_ACTIVE_WINDOW].id
		self.HookCommand(self.OnCloseActiveWindow,id)
	
		id=usercmdui.class2ui[wndusercmd.ABOUT_GRINS].id
		self.HookCommand(self.OnAbout,id)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,id)

		id=usercmdui.class2ui[wndusercmd.SELECT_CHARSET].id
		self.HookCommand(self.OnCharset,id)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,id)

		client=self.GetMDIClient()
		client.HookMessage(self.OnMdiRefreshMenu,win32con.WM_MDIREFRESHMENU)
		self._active_child=None
		# hook tab sel change
		#TCN_FIRST =-550;TCN_SELCHANGE  = TCN_FIRST - 1
		#self.HookNotify(self.OnNotifyTcnSelChange,TCN_SELCHANGE)
		
		# set main frame popup
		if hasattr(MenuTemplate,'MAIN_FRAME_POPUP'):
			client.HookMessage(self.onRButtonDown,win32con.WM_RBUTTONDOWN)
			self.setpopupmenu(MenuTemplate.MAIN_FRAME_POPUP)
		
		# enable mechanism to accept paste files
		# when the event PasteFile is registered
		id=usercmdui.class2ui[wndusercmd.PASTE_DOCUMENT].id
		self.HookCommand(self.OnPasteFile,id)
		self.HookCommandUpdate(self.OnUpdateEditPaste,id)
		return 0

	# override DropTarget.OnDragOver to protect childs
	def OnDragOver(self,dataobj,kbdstate,x,y):
		filename=dataobj.GetGlobalData(self.CF_FILE)
		if not filename:return DROPEFFECT_NONE

		client=self.GetMDIClient()
		wnd=client.ChildWindowFromPoint((x,y))
		
		# in the client area but over a child
		if wnd and wnd.GetSafeHwnd()!=client.GetSafeHwnd():
			return DROPEFFECT_NONE
			
		# allow drops on the window captions
		# if not wnd: # not in the client area
		#	return DROPEFFECT_NONE

		# in the free area
		x,y=self._DPtoLP((x,y))
		x,y = self._pxl2rel((x, y),self._canvas)
		return self.onEventEx(DragFile,(x, y, filename))

	# drag and drop files support for MainFrame
	# enable drop files
	def dragAcceptFiles(self):
		self.DragAcceptFiles(1)
		self.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)
		client=self.GetMDIClient()
		client.DragAcceptFiles(1)
		client.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)

	# dissable drop files
	def dragRefuseFiles(self):
		self.DragAcceptFiles(0)
		client=self.GetMDIClient()
		client.DragAcceptFiles(0)

	# response to drop files. Ignore x, y for docs
	def onDropFiles(self,params):
		msg=win32mu.Win32Msg(params)	
		hDrop=msg._wParam
		numfiles=win32api.DragQueryFile(hDrop,-1)
		for ix in range(numfiles):
			filename=win32api.DragQueryFile(hDrop,ix)
			self.onEvent(DropFile,(0, 0, filename))
		win32api.DragFinish(hDrop)

	def onDropEvent(self, event, (x, y, filename)):
		x,y = self._pxl2rel((x, y),self._canvas)
		self.onEvent(event, (x, y, filename))
	
	# copy/paste files support
	# to enable paste file for a wnd: 
	#	1. enable command mechanism
	#	2. register event 'PasteFile'
	def OnPasteFile(self,id,code):
		filename=Sdk.GetClipboardFileData()
		if filename:
			import longpath
			filename=longpath.short2longpath(filename)
			x,y=self._DPtoLP(self._popup_point)
			x,y = self._pxl2rel((x, y),self._canvas)
			self.onEvent(PasteFile,(x, y, filename))

	def OnUpdateEditPaste(self,cmdui):
		cmdui.Enable(Sdk.IsClipboardFileDataAvailable())

	def onInitMenu(self,params):
		if Sdk.IsClipboardFormatAvailable(win32con.CF_TEXT):
			pass # enable paste file
		self.PostMessage(WM_KICKIDLE)
		
	def onKey(self,key):
		self.PostMessage(WM_KICKIDLE)

	def onActivate(self,params):
		msg=win32mu.Win32Msg(params)
		flag=msg.LOWORD_wParam()
		if flag!=win32con.WA_INACTIVE:
			__main__.toplevel.setActiveDocFrame(self)
			self.SendMessage(win32con.WM_MDIREFRESHMENU)

	# Mirrors mdi window-menu to tab bar (not impl)
	# do ... on new activate	
	def OnMdiRefreshMenu(self,params):
		msg=win32mu.Win32Msg(params)
		try:
			f,m=self.MDIGetActive()
		except win32ui.error:
			f=None

		id=usercmdui.class2ui[wndusercmd.CLOSE_ACTIVE_WINDOW].id
		if not f:
			self._active_child=None
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,afxres.ID_WINDOW_CASCADE)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,afxres.ID_WINDOW_TILE_VERT)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,afxres.ID_WINDOW_TILE_HORZ)
			return

		if not self._active_child or self._active_child!=f:	
			if hasattr(f,'_view'):
				self._active_child=f
			else:
				self._active_child=None 

		self.HookCommandUpdate(self.OnUpdateCmdEnable,id)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,afxres.ID_WINDOW_CASCADE)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,afxres.ID_WINDOW_TILE_VERT)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,afxres.ID_WINDOW_TILE_HORZ)
		self.PostMessage(WM_KICKIDLE)

	# Displays the about dialog
	def OnAbout(self,id,code):
		#if self.in_modal_create_box_mode(): return
		#self.assert_not_in_create_box()
		from version import version
		dlg=win32dialog.AboutDlg(arg=0,version = 'GRiNS ' + version,parent=self)
		dlg.DoModal()

	# Displays the charset dialog
	def OnCharset(self,id,code):
		import Font
		prompt = 'Select Charset:'
		list = []
		for name in Font.win32_charsets_list:
			list.append((name, (Font.set_win32_charset, (name,))))
		win32dialog.Dialog(list, title = 'Select Charset', prompt = prompt, grab = 1, vertical = 1, parent = self)

	# Response to windows arrangement commands
	def OnWndUserCmd(self,id,code):
		#if self.in_modal_create_box_mode(): return
		#self.assert_not_in_create_box()
		client=self.GetMDIClient()
		if id==afxres.ID_WINDOW_TILE_HORZ:
			client.SendMessage(win32con.WM_MDITILE,win32con.MDITILE_HORIZONTAL)			
		elif id==afxres.ID_WINDOW_TILE_VERT:
			client.SendMessage(win32con.WM_MDITILE,win32con.MDITILE_VERTICAL)			
		elif id==afxres.ID_WINDOW_CASCADE:
			client.SendMessage(win32con.WM_MDICASCADE)			
	
	# Response to command to close the active window
	def OnCloseActiveWindow(self,id,code):
		t=self.MDIGetActive()
		if not t: return
		f,ismax=t
		if self._active_child and\
			hasattr(self._active_child._view,'_commandlist') and\
			self._active_child._view._commandlist:
			id=usercmdui.class2ui[usercmd.CLOSE_WINDOW].id
			self.PostMessage(win32con.WM_COMMAND,id)
		else:
			f.PostMessage(win32con.WM_CLOSE)
	
	# Called by the core system to initialize the frame			
	def init_cmif(self, x, y, w, h, title,units = UNIT_MM,
		      adornments = None,commandlist = None):	
		if not w or w==0:
			w=(3*sysmetrics.scr_width_mm/4)
		if not h or h==0:
			h=(3*sysmetrics.scr_height_mm/4)
		if not x: x=sysmetrics.scr_width_mm/8
		if not y: y=sysmetrics.scr_height_mm/8

		self.newcmwindow=self.newwindow #alias
		self._canscroll = 0
		self._title = AppDisplayName # ignore title		
		self._topwindow = self
		self._window_type = SINGLE # actualy not applicable
		self._sizes = 0, 0, 1, 1
		# we must check since we reuse
		if self not in __main__.toplevel._subwindows:
			__main__.toplevel._subwindows.insert(0, self)
		xp,yp,wp,hp = sysmetrics.to_pixels(x,y,w,h,units)
		self._rectb= xp,yp,wp,hp
		self._sizes = (float(xp)/sysmetrics.scr_width_pxl,float(yp)/sysmetrics.scr_height_pxl,float(wp)/sysmetrics.scr_width_pxl,float(hp)/sysmetrics.scr_height_pxl)
		self._depth = __main__.toplevel.getscreendepth()
		
		# all, are historic alias but useful to markup externals
		# the symbol self._obj_ reresents the os-mfc window object
		self._wnd=self._obj_ 
		self._hWnd=self.GetSafeHwnd()

		# set adorments and cmdlist
		self._cmifdoc=None
		self._qtitle={'frame':self._title,'document':None,'view':None}
		self._activecmds={'frame':{},'document':{},'view':{}}
		self._dynamiclists={}
		self._dyncmds={}
		self.set_commandlist(commandlist,'frame')

		l,t,r,b=self.GetClientRect()
		self._canvas=self._rect=(l,t,r-l,b-t)
	
	# Called when a new document is opened
	def newdocument(self,cmifdoc,adornments,commandlist):
		if not self._cmifdoc:
			self.setdocument(cmifdoc,adornments,commandlist)
			return self
		else:
			frame = MDIFrameWnd()
			frame.create(self._qtitle['frame'])
			frame.init_cmif(None, None, 0, 0,self._qtitle['frame'],
				UNIT_MM,None,self.get_commandlist('frame'))
			frame.setdocument(cmifdoc,adornments,commandlist)
			return frame

	# Associate this frame with the document
	def setdocument(self,cmifdoc,adornments,commandlist):
		self._cmifdoc=cmifdoc
		import urllib
		basename=urllib.unquote(cmifdoc.basename)
		self.settitle(basename,'document')
		self.set_commandlist(commandlist,'document')
		if not IsPlayer:
			self.setEditorDocumentToolbar(adornments)
			self.setEditorDocumentMenu(1)
			self.RecalcLayout()	
		self.ActivateFrame()

	def setEditorDocumentMenu(self,flag):
		if USE_NODOC_MENUBAR:
			temp=self._mainmenu
			self._mainmenu=win32menu.Menu()
			if not flag and hasattr(MenuTemplate,'NODOC_MENUBAR'):
				template=MenuTemplate.NODOC_MENUBAR
			else:
				template=MenuTemplate.MENUBAR
			self._mainmenu.create_from_menubar_spec_list(template,self.get_cmdclass_id)
			self.SetMenu(self._mainmenu)
			self.DrawMenuBar()
			if self._dynamiclists.has_key(usercmd.OPEN_RECENT):
				list = self._dynamiclists[usercmd.OPEN_RECENT]
				self.set_dynamiclist(usercmd.OPEN_RECENT, list)
			temp.DestroyMenu()		
		
	# Returns the grins document
	def getgrinsdoc(self):
		return self._cmifdoc

	# Called by the core system to create a view
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1, bgcolor = None):
		if adornments.has_key('view'):strid=adornments['view']
		else:  raise "undefined view request"
		if strid=='pview_':
			exporting = adornments.get('exporting')
			if exporting:
				return self.newExport(x, y, w, h, title, units, adornments,canvassize, commandlist,strid, bgcolor)
			elif adornments.has_key('show') and adornments['show']=='fullscreen':
				if not self.__fsPlayer:
					self.__fsPlayer = self.newFSPlayer(self, bgcolor)
				return self.__fsPlayer.newviewport(x, y, w, h, title, units, adornments,canvassize, commandlist,strid,bgcolor)
		return self.newview(x, y, w, h, title, units, adornments, canvassize, commandlist, strid, bgcolor)

	def newFSPlayer(self, frame, bgcolor):
		from _FSPlayerView import _FSPlayerView
		fsp = _FSPlayerView(frame, bgcolor)
		desktop = Sdk.GetDesktopWindow()
		dc = desktop.GetDC();
		width = dc.GetDeviceCaps(win32con.HORZRES)
		height = dc.GetDeviceCaps(win32con.VERTRES)
		fsp.create('GRiNS Player',0,0,width,height)
		fsp.ShowWindow(win32con.SW_SHOW)
		fsp.UpdateWindow()
		return fsp

	def delFSPlayer(self):
		self.__fsPlayer = None

	def newExport(self, x, y, w, h, title, units = UNIT_MM, adornments=None, canvassize=None, commandlist=None, strid='cmifview_', bgcolor=None):
		return win32window.ViewportContext(self, w, h, units, bgcolor)

	# Return the framework document object associated with this frame
	def getdoc(self):
		if self.countMDIChildWnds()==0:
			self._doc=docview.Document(docview.DocTemplate())
		return self._doc

	# Create a text viewer
	def textwindow(self,text):
		sv=self.newviewobj('sview_')
		sv.settext(text)
		self.showview(sv,'sview_')
		if self._cmifdoc:
			sv.GetParent().SetWindowText('Source (%s)'%self._cmifdoc.basename)
		return sv

	# Creates a new ChildFrame 
	def newChildFrame(self,view,decor=None):
		return ChildFrame(view,decor)
	# Called by the framework when the actvation changes
	def Activate(self,view):
		self.MDIActivate(view)
	# Returns the prefered client dimensions
	def getPrefRect(self):
		rc= win32mu.Rect(self.GetClientRect())
		return rc.width()/8,rc.height()/8,7*rc.width()/8,7*rc.height()/8

	# Close all views directly
	def close_all_views(self):
		currentChild=None
		count=0
		l=[]
		while 1:
			currentChild=self.getNextMDIChildWnd(currentChild)
			if currentChild:l.append(currentChild)
			else: break
		for w in l:
			w.DestroyWindow()

	# Set the waiting cursor
	def setwaiting(self):
		import windowinterface
		windowinterface.toplevel.setwaiting()
		
	# Remove waiting cursor
	def setready(self):
		import windowinterface
		windowinterface.toplevel.setready()
		self.ActivateFrame()

	# Close the opened document
	def close(self):
		# 1. destroy cascade menus
		exceptions=[usercmd.OPEN_RECENT,]
		self._mainmenu.clear_cascade_menus(exceptions)

		# 2. then the document
		__main__.toplevel.cleardocmap(self._cmifdoc)
		self._cmifdoc=None
		self.set_commandlist(None,'document')
		self.settitle(None,'document')
		if not IsPlayer and len(__main__.toplevel._subwindows)==1:
			self.setEditorFrameToolbar()
			self.setEditorDocumentMenu(0)
		# and document's views
		self.close_all_views()

		# 3. if there is another top-level frame
		# we should close self frame
		if len(__main__.toplevel._subwindows)>1:
			__main__.toplevel._subwindows.remove(self)
			self.DestroyWindow()	
		else:
			# clean image cache
			from win32ig import win32ig
			win32ig.deltemp()
			__main__.toplevel._image_size_cache = {}
			__main__.toplevel._image_cache = {}

			

	# Response to resizing		
	def onSize(self,params):
		self.RecalcLayout()
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		self._rect=self._canvas=0,0,msg.width(),msg.height()
		MDIFrameWnd.wndismax=msg.maximized()
		if not msg.maximized():
			rc=self.GetWindowRect()
			MDIFrameWnd.wndsize=win32mu.Point((rc[2]-rc[0],rc[3]-rc[1]))

	# Response to mouse move
	def onMove(self,params):
		rc=self.GetWindowRect()
		MDIFrameWnd.wndpos=win32mu.Point((rc[0],rc[1]))

	# Resize window
	def setcoords(self,coords,units=UNIT_MM):
		x, y, w, h = coords
		x,y,w,h=sysmetrics.to_pixels(x,y,w,h,units)
		rc=(x,y,x+w,y+h)
		#l,t,r,b=self.CalcWindowRect(rc,0)
		#w=r-l+2*cxframe+4
		#h=b-t+3*cycaption+16+4
		self.RecalcLayout()
		flags=win32con.SWP_NOZORDER|win32con.SWP_NOACTIVATE |win32con.SWP_NOMOVE
		self.SetWindowPos(0,(0,0,w,h),flags)
		

	# Maximize window
	def maximize(self,child):
		client=self.GetMDIClient()
		client.SendMessage(win32con.WM_MDIMAXIMIZE,child.GetSafeHwnd())


	###############################################
	#
	# Popup menu
	#

	# Destroy popup menu
	def destroy_menu(self):
		if self._menu:
			self._menu.DestroyMenu()
			del self._menu 
		self._menu = None

	# appent an entry to popup menu
	def append_menu_entry(self,entry=None):
		if not self._menu:return
		if not entry:
			self._menu.AppendMenu(win32con.MF_SEPARATOR)
		else:
			acc,label,cbt=entry
			id=self._menu.GetMenuItemCount()+1
			flags=win32con.MF_STRING|win32con.MF_ENABLED
			self._menu.AppendMenu(flags, id, label)
			self._cbld[id]=cbt

	def setpopupmenu(self, menutemplate):
		# Menutemplate is a MenuTemplate-style menu template.
		# It should be turned into an win32menu-style menu and put
		# into self._popupmenu.
		self._destroy_popupmenu()
		self._popupmenu = win32menu.Menu('popup')
		self._popupmenu.create_popup_from_menubar_spec_list(menutemplate,self.get_cmdclass_id)
		
	def _destroy_popupmenu(self):
		# Free resources held by self._popupmenu and set it to None
		if self._popupmenu:self._popupmenu.DestroyMenu()
		self._popupmenu = None		


	#
	# win32window.Window overrides
	#
	# Returns true if the point is inside the window
	def inside(self,pt):
		rc=win32mu.Rect(self.GetClientRect())
		return rc.isPtInRect(win32mu.Point(pt))

	def getwindowpos(self, rel=None):
		return self.GetClientRect()

	# Override win32window.Window method
	def update(self):
		pass

	# Returns the grins document
	def getgrinsdoc(self):
		return self._cmifdoc

	# Returns the grins frame
	def getgrinsframe(self):
		return self

	def _convert_color(self, color):
		return color 

	#
	# Image management section
	#
	# Returns the size of the image
	def _image_size(self, file):
		toplevel=__main__.toplevel
		try:
			xsize, ysize = toplevel._image_size_cache[file]
		except KeyError:
			img = win32ig.load(file)
			xsize,ysize,depth=win32ig.size(img)
			toplevel._image_size_cache[file] = xsize, ysize
			toplevel._image_cache[file] = img
		self.imgAddDocRef(file)
		return xsize, ysize

	def _image_handle(self, file):
		return __main__.toplevel._image_cache[file]

	# XXX: to be removed
	def imgAddDocRef(self,file):
		toplevel=__main__.toplevel
		doc=self.getgrinsdoc()
		if doc==None: doc="__Unknown"
		if toplevel._image_docmap.has_key(doc):
			if file not in toplevel._image_docmap[doc]:
				toplevel._image_docmap[doc].append(file)
		else:
			toplevel._image_docmap[doc]=[file,]


	# return commnds class id
	def get_cmdclass_id(self,cmdcl):
		if usercmdui.class2ui.has_key(cmdcl):
			return usercmdui.class2ui[cmdcl].id
		else: 
			print 'CmdClass not found',cmdcl
			return -1

	# Returns a submenu from its string id (e.g 'File','Edit',etc)
	def get_submenu(self,strid):
		return self._mainmenu._submenus_dict.get(strid)

	###############################################
	# BEGIN CMD LIST SECTION

	# Set/reset commandlist for context
	def set_commandlist(self,commandlist,context):
		# we have a new commandlist for this context 
		# so, dissable previous
		self.dissable_context(context)

		# enable cmds in commandlist
		# cash ids to cmd map for OnUserCmd
		if commandlist:
			for cmd in commandlist:
				usercmd_ui = usercmdui.class2ui[cmd.__class__]
				id=usercmd_ui.id
				self.enable_cmd(id)
				self._activecmds[context][id]=cmd
		self.setplayerstate(self.__playerstate)

	# Dissable context commands
	def dissable_context(self,context):
		# assert there is an entry for this context
		if not self._activecmds.has_key(context):
			self._activecmds[context]={}
			return
		contextcmds=self._activecmds[context]
		# we must clean here so that dissable_cmd does its job
		self._activecmds[context]={}
		commandlist=contextcmds.values()
		for cmd in commandlist:
			usercmd_ui = usercmdui.class2ui[cmd.__class__]
			self.dissable_cmd(usercmd_ui.id)
		
	def enable_cmd(self,id):
		self.HookCommandUpdate(self.OnUpdateCmdEnable,id)

	# dissable a cmd only if not in self._activecmds
	def dissable_cmd(self,id):
		for context in self._activecmds.keys():
			if self._activecmds[context].has_key(id):
				return
		# not in other command lists
		self.HookCommandUpdate(self.OnUpdateCmdDissable,id)

	# Toggle commands (check/uncheck menu entries)		
	def set_toggle(self, cmdcl, onoff):
		id=usercmdui.class2ui[cmdcl].id
		flags = win32con.MF_BYCOMMAND
		if onoff==0:
			flags = flags | win32con.MF_UNCHECKED
		else:
			flags = flags | win32con.MF_CHECKED
		(self.GetMenu()).CheckMenuItem(id,flags)
		self.PostMessage(WM_KICKIDLE)

	# Set item menu and toolbar relative to player in a specific state
	def setplayerstate(self, state):
		import Player

		self.__playerstate = state
		tb_id_play=usercmdui.class2ui[wndusercmd.TB_PLAY].id
		tb_id_pause=usercmdui.class2ui[wndusercmd.TB_PAUSE].id
		tb_id_stop=usercmdui.class2ui[wndusercmd.TB_STOP].id
			
		id_play=usercmdui.class2ui[usercmd.PLAY].id
		id_pause=usercmdui.class2ui[usercmd.PAUSE].id
		id_stop=usercmdui.class2ui[usercmd.STOP].id

		if state == Player.PLAYING:
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id_pause)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id_play)
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id_stop)

			self.HookCommandUpdate(self.OnUpdateCmdEnable,tb_id_pause)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,tb_id_play)
			self.HookCommandUpdate(self.OnUpdateCmdEnable,tb_id_stop)
		
		if state == Player.PAUSING:
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id_play)
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndCheck,id_pause)
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id_stop)
			
			self.HookCommandUpdate(self.OnUpdateCmdEnable,tb_id_play)
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndCheck,tb_id_pause)
			self.HookCommandUpdate(self.OnUpdateCmdEnable,tb_id_stop)
		
		if state == Player.STOPPED:
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id_play)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id_stop)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id_pause)

			self.HookCommandUpdate(self.OnUpdateCmdEnable,tb_id_play)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,tb_id_stop)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,tb_id_pause)


	# Return the commandlist for the context
	def get_commandlist(self,context):
		if self._activecmds.has_key(context):
			return self._activecmds[context].values()
		return None

	# Target for commands that are enabled
	def OnUpdateCmdEnable(self,cmdui):
		cmdui.Enable(1)

	def OnUpdateCmdEnableAndCheck(self,cmdui):
		cmdui.SetCheck(1)
		cmdui.Enable(1)

	def OnUpdateCmdDissable(self,cmdui):
		cmdui.SetCheck(0)
		cmdui.Enable(0)

	# Response to a user command (menu selection)
	def OnUserCmd(self,id,code):
		#if self.in_modal_create_box_mode(): return
		#self.assert_not_in_create_box()
		cmd=None
			
		# look first self._active_child cmds
		if self._active_child and self._activecmds.has_key(self._active_child._view._strid):
			contextcmds=self._activecmds[self._active_child._view._strid]
			if contextcmds.has_key(id):
				cmd=contextcmds[id]
				if cmd is not None and cmd.callback is not None:
					apply(apply,cmd.callback)
				return

		# the command does not belong to self._active_child
		# look to others (including dynamic menus)
		for context in self._activecmds.keys():
			contextcmds=self._activecmds[context]
			if contextcmds.has_key(id):
				cmd=contextcmds[id]
				if cmd is not None and cmd.callback is not None:
					apply(apply,cmd.callback)
				return
		self.PostMessage(WM_KICKIDLE)

	# Get the command class id
	def GetUserCmdId(self,cmdcl):
		return usercmdui.class2ui[cmdcl].id

	# Get the command class instance
	def GetUserCmd(self,cmdcl):
		id=usercmdui.class2ui[cmdcl].id
		for contextcmds in self._activecmds.values():
			if contextcmds.has_key(id):
				return contextcmds[id]
		return None

#  	def set_grins_snap_features(self):
# 		# Assert features.version == 'grins snap!'
# 		id_openrecent = usercmdui.class2ui[usercmd.OPEN_RECENT].id
# 		self.HookCommandUpdate(self.OnUpdateCmdDissable, id_openrecent);

# 		print "DEBUG: I think it worked..";

	# END CMD LIST SECTION
	###############################################



	###############################################
	# BEGIN DYNAMIC CMD LIST SECTION

	# Set the dynamic commands associated with the command class
	def set_dynamiclist(self, command, list):
		self._dynamiclists[command]=list
		submenu=self._mainmenu.get_cascade_menu(command)
		idstart = usercmdui.class2ui[command].id+1
		cmd = self.GetUserCmd(command)
		if cmd is None:
			# dissable submenu cmds?
			# they are always active?
			return
		if not cmd.dynamiccascade:
			raise error, 'non-dynamic command in set_dynamiclist'

		callback = cmd.callback
		menuspec = []
		if not self._dyncmds.has_key(command):
			self._dyncmds[command]={}
		else:
			self._dyncmds[command].clear()
		for entry in list:
			entry = (entry[0], (callback, entry[1])) + entry[2:]
			menuspec.append(entry)			
		if submenu is not None:
			self._mainmenu.clear_cascade(command)
			win32menu._create_menu(submenu,menuspec,idstart,self._dyncmds[command])
			self.set_dyncbd(self._dyncmds[command],submenu)
		
		# update popupmenu
		if self._popupmenu:
			submenu=self._popupmenu.get_cascade_menu(command)
			if submenu:
				self._popupmenu.clear_cascade(command)
				win32menu._create_menu(submenu,menuspec,idstart,self._dyncmds[command])
		
	# Helper function to return the dynamic submenu
	def get_cascade_menu(self,id):
		cl=usercmdui.get_cascade(id)
		return self._mainmenu.get_cascade_menu(cl)
	
	# Response to dynamic menus commands	
	def OnUserDynCmd(self,id,code):
		#if self.in_modal_create_box_mode(): return
		#self.assert_not_in_create_box()
		for cbd in self._dyncmds.values():
			if cbd.has_key(id):
				if not cbd[id]:return
				# call check_cascade_menu_entry before
				# apply because the call may result
				# in a call to set_dynamiclist
				self.check_cascade_menu_entry(id)
				apply(apply,cbd[id])
				break
		self.PostMessage(WM_KICKIDLE)

	# items are checked/unchecked by the core system
	def check_cascade_menu_entry(self,id):
		submenu=self.get_cascade_menu(id)
		if not submenu:
			print 'failed to find cascade_menu with id',id
			return
		if not submenu._toggles.has_key(id):return
		state=submenu.GetMenuState(id,win32con.MF_BYCOMMAND)
		if state & win32con.MF_CHECKED:
			submenu.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_UNCHECKED)
		else:
			submenu.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_CHECKED)

	# Set callback for dynamic menu
	def set_dyncbd(self,cbd,menu):
		for id in cbd.keys():
			self.HookCommand(self.OnUserDynCmd,id)
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id)
	
	# Enable the dynamic commands associated with the command class	
	def EnableDynCmds(self,cmdcl):
		for cbd in self._dyncmds.values():
			if cbd.has_key(id):
				if cbd[id]:apply(apply,cbd[id])
				return

	# END DYNAMIC CMD LIST SECTION
	###############################################



	# Fire a command class instance
	def fire_cmd(self,cmdcl):
		id=usercmdui.class2ui[cmdcl].id
		self.OnUserCmd(id,0)
	
	# Compose and set the title  	
	def settitle(self,title,context='document'):
		self._qtitle[context]=title
		qtitle=''
		if self._qtitle['document']:
			qtitle= qtitle + self._qtitle['document'] + ' - '
		elif self._qtitle['view']:
				qtitle=qtitle + self._qtitle['view'] + ' - '
		qtitle=qtitle + self._qtitle['frame']
		self.SetWindowText(qtitle)

	# Set adornments
	def set_adornments(self, adornments):
		pass			

	# Called by the framework when the user closes the window
	def OnClose(self):
		if len(__main__.toplevel._subwindows)>1:
			self.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.CLOSE].id)
		else:
			self.PostMessage(win32con.WM_COMMAND,usercmdui.class2ui[usercmd.EXIT].id)

	# Bring to top of peers
	def pop(self):
		self.BringWindowToTop()

	# Send to back of peers
	def push(self):
		pass

	# Called by the framework before destroying the window
	def OnDestroy(self, msg):
		if self._wndToolBar:
			self._wndToolBar.DestroyWindow()
			del self._wndToolBar
		if self._mainmenu:
			self.SetMenu(None) 
			self._mainmenu.DestroyMenu()
			del self._mainmenu
		if self._popupmenu:
			self._popupmenu.DestroyMenu()
			del self._popupmenu
		if self in __main__.toplevel._subwindows:
			__main__.toplevel._subwindows.remove(self)
		window.MDIFrameWnd.OnDestroy(self, msg)

	# Response to right button down
	def onRButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		xpos,ypos=msg.pos()
		if self._menu:
			id = self._menu.FloatMenu(self,xpos, ypos)
			if self._cbld.has_key(id) :
				callback = self._cbld[id]
				apply(callback[0], callback[1])
		else:
			menu=None
			if self._popupmenu:
				self.onLButtonDown(params)
				menu = self._popupmenu
			if not menu:return
			pt=(xpos,ypos)
			pt=self.ClientToScreen(pt);
			menu.TrackPopupMenu(pt,win32con.TPM_RIGHTBUTTON|win32con.TPM_LEFTBUTTON,
				self)
	
	# Response to left button down
	def onLButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Press)

	# Response to left button up
	def onLButtonUp(self, params):
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Release)


	# Set the editor toolbar to the state without a document
	def setEditorFrameToolbar(self):
		self._wndToolBar.SetButtons(4)

		id=usercmdui.class2ui[usercmd.NEW_DOCUMENT].id
		self._wndToolBar.SetButtonInfo(0,id,afxexttb.TBBS_BUTTON,0)

		self._wndToolBar.SetButtonInfo(1,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.OPENFILE].id
		self._wndToolBar.SetButtonInfo(2,id,afxexttb.TBBS_BUTTON, 1)

		id=usercmdui.class2ui[usercmd.SAVE].id
		self._wndToolBar.SetButtonInfo(3,id,afxexttb.TBBS_BUTTON, 2)
				
		self.ShowControlBar(self._wndToolBar,1,0)
		self._wndToolBar.RedrawWindow()


	# Set the editor toolbar to the state with a document
	def setEditorDocumentToolbar(self, adornments):
		num_buttons = 18
		self._wndToolBar.SetButtons(num_buttons)

		id=usercmdui.class2ui[usercmd.NEW_DOCUMENT].id
		self._wndToolBar.SetButtonInfo(0,id,afxexttb.TBBS_BUTTON,0)

		self._wndToolBar.SetButtonInfo(1,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.OPENFILE].id
		self._wndToolBar.SetButtonInfo(2,id,afxexttb.TBBS_BUTTON, 1)

		id=usercmdui.class2ui[usercmd.SAVE].id
		self._wndToolBar.SetButtonInfo(3,id,afxexttb.TBBS_BUTTON, 2)
	
		# Play Toolbar
		self._wndToolBar.SetButtonInfo(4,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6);

		id=usercmdui.class2ui[usercmd.RESTORE].id
		self._wndToolBar.SetButtonInfo(5,id,afxexttb.TBBS_BUTTON, 6)

		id=usercmdui.class2ui[usercmd.CLOSE].id
		self._wndToolBar.SetButtonInfo(6,id,afxexttb.TBBS_BUTTON, 7)

		self._wndToolBar.SetButtonInfo(7,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6)

		id=usercmdui.class2ui[wndusercmd.TB_PLAY].id
		self._wndToolBar.SetButtonInfo(8,id,afxexttb.TBBS_BUTTON, 9)

		id=usercmdui.class2ui[wndusercmd.TB_PAUSE].id
		self._wndToolBar.SetButtonInfo(9,id,afxexttb.TBBS_BUTTON, 10)

		id=usercmdui.class2ui[wndusercmd.TB_STOP].id
		self._wndToolBar.SetButtonInfo(10,id,afxexttb.TBBS_BUTTON, 11)

		self._wndToolBar.SetButtonInfo(11,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,12)
	
		id=usercmdui.class2ui[wndusercmd.CLOSE_ACTIVE_WINDOW].id
		self._wndToolBar.SetButtonInfo(12,id,afxexttb.TBBS_BUTTON, 14)

		self._wndToolBar.SetButtonInfo(13,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,12)

		id = usercmdui.class2ui[usercmd.CANVAS_ZOOM_IN].id
		self._wndToolBar.SetButtonInfo(14,id,afxexttb.TBBS_BUTTON,15)
		id = usercmdui.class2ui[usercmd.CANVAS_ZOOM_OUT].id
		self._wndToolBar.SetButtonInfo(15,id,afxexttb.TBBS_BUTTON,16)

		self._wndToolBar.SetButtonInfo(16,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,12)

		id=usercmdui.class2ui[usercmd.HELP].id
		self._wndToolBar.SetButtonInfo(17,id,afxexttb.TBBS_BUTTON, 12)

		if adornments.has_key('pulldown'):
			index = num_buttons
			for list, cb, init in adornments['pulldown']:
				self._wndToolBar.SetButtonInfo(index,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,12)
				index = index + 1
				# the return object is a components.ComboBox
				global ID_TOOLBAR_COMBO
				tbcb = self.createToolBarCombo(index, ID_TOOLBAR_COMBO, TOOLBAR_COMBO_WIDTH, TOOLBAR_COMBO_HEIGHT, self.onToolbarCombo)
				ID_TOOLBAR_COMBO = ID_TOOLBAR_COMBO + 1
				index = index + 1
				self._toolbarCombo.append((tbcb, cb))
				for str in list:
					tbcb.addstring(str)
				tbcb.setcursel(list.index(init))

		self.ShowControlBar(self._wndToolBar,1,0)


	# Set the player toolbar
	def setPlayerToolbar(self):
		self._wndToolBar.SetButtons(9)

		id=usercmdui.class2ui[usercmd.OPENFILE].id
		self._wndToolBar.SetButtonInfo(0,id,afxexttb.TBBS_BUTTON, 1)

		# Play Toolbar
		self._wndToolBar.SetButtonInfo(1,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6)

		id=usercmdui.class2ui[usercmd.CLOSE].id
		self._wndToolBar.SetButtonInfo(2,id,afxexttb.TBBS_BUTTON, 7)

		self._wndToolBar.SetButtonInfo(3,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6)

		id=usercmdui.class2ui[wndusercmd.TB_PLAY].id
		self._wndToolBar.SetButtonInfo(4,id,afxexttb.TBBS_BUTTON, 9)

		id=usercmdui.class2ui[wndusercmd.TB_PAUSE].id
		self._wndToolBar.SetButtonInfo(5,id,afxexttb.TBBS_BUTTON, 10)

		id=usercmdui.class2ui[wndusercmd.TB_STOP].id
		self._wndToolBar.SetButtonInfo(6,id,afxexttb.TBBS_BUTTON, 11)
	
		self._wndToolBar.SetButtonInfo(7,afxexttb.ID_SEPARATOR,afxexttb.TBBS_SEPARATOR,6)

		id=usercmdui.class2ui[usercmd.HELP].id
		self._wndToolBar.SetButtonInfo(8,id,afxexttb.TBBS_BUTTON, 12)
	
		self.ShowControlBar(self._wndToolBar,1,0)


	def createToolBarCombo(self, index, ctrlid, width, ddheight, responseCb=None):
		self._wndToolBar.SetButtonInfo(index, ctrlid, afxexttb.TBBS_SEPARATOR, width)
		l, t, r, b = self._wndToolBar.GetItemRect(index)
		b = b + ddheight
		rc = l, t, r-l, b-t
		import components
		ctrl = components.ComboBox(self._wndToolBar,ctrlid)
		ctrl.create(components.COMBOBOX(), rc)
		if responseCb:
			self.HookCommand(responseCb,ctrlid)
		
		# set combo box font
		lf = {'name':'', 'pitch and family':win32con.FF_SWISS,'charset':win32con.ANSI_CHARSET}
		d = Sdk.EnumFontFamiliesEx(lf)
		logfont = None
		if d.has_key('Tahoma'): # win2k
			logfont = {'name':'Tahoma', 'height': 11, 'weight': win32con.FW_MEDIUM, 'charset':win32con.ANSI_CHARSET}
		elif d.has_key('Microsoft Sans Serif'): # not win2k
			logfont = {'name':'Microsoft Sans Serif', 'height': 11, 'weight': win32con.FW_MEDIUM, 'charset':win32con.ANSI_CHARSET}
		if logfont:
			ctrl.setfont(logfont)

		return ctrl

	def onToolbarCombo(self, id, code):
		if code==win32con.CBN_SELCHANGE:
			for tbcb, cb in self._toolbarCombo:
				if tbcb._id == id:
					cb(tbcb.getvalue())
					return

	def isplayer(self,f):
		if not hasattr(f,'_view'): return 0
		return f._view._strid=='pview_'

	# Show or hide all childs but the player
	def showChilds(self,flag):
		if flag:
			#self.SetMenu(self._mainmenu)
			self._wndToolBar.ShowWindow(win32con.SW_SHOW)
			self.ShowControlBar(self._wndToolBar,1,0)
			self._wndToolBar.RedrawWindow()
		else:
			self._wndToolBar.ShowWindow(win32con.SW_HIDE)

		clist=[]
		player=None
		c=None
		while 1:
			c=self.getNextMDIChildWnd(c)
			if c: 
				clist.append(c)
				if not self.isplayer(c):
					if flag:c.EnableWindow(1)
					else: c.EnableWindow(0)
				else: player=c
			else: break

		if flag:
			for c in clist:
				self.MDIActivate(c)
		else:
			pass #self.SetMenu(None)				
		if player:self.MDIActivate(player)


	# Return the number of childs
	def countMDIChildWnds(self):
		currentChild=None
		count=0
		while 1:
			currentChild=self.getNextMDIChildWnd(currentChild)
			if currentChild:count=count+1
			else: break
		return count

	# Returns the next child
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



	###########################################################
	# Views management

	# Create and initialize a new view object 
	# Keep instance of player
	def newview(self,x, y, w, h, title, units = UNIT_MM, adornments=None,canvassize=None, commandlist=None, strid='cmifview_', bgcolor=None):
		viewno=self.getviewno(strid)
		viewclass=appview[viewno]['class'] 
		view=viewclass(self.getdoc(), bgcolor)
		self.add_common_interface(view,viewno)
		if not x or x<0: x=0
		if not y or y<0: y=0
		if not w or w<0: w = sysmetrics.scr_width_pxl/2
		if not h or h<0: h = sysmetrics.scr_height_pxl/2

		x,y,w,h=sysmetrics.to_pixels(x,y,w,h,units)
		dw=2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)+2*sysmetrics.cxframe
		dh=sysmetrics.cycaption + 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)+2*sysmetrics.cyframe
		rcFrame=(x,y,x+w+dw,y+h+dh)
		f=ChildFrame(view)
		f.Create(title,rcFrame,self,0)

		view.init((0,0,w,h),title,units,adornments,canvassize,commandlist,bgcolor)
		self.MDIActivate(f)
		return view


	# Create a new view object 
	def newviewobj(self,strid):
		viewno=self.getviewno(strid)
		if appview[viewno].has_key('hosted') and appview[viewno]['hosted']:
			viewclass=appview[viewno]['class']
			viewobj=viewclass()
			self.add_common_interface(viewobj,viewno)
			return viewobj
		else:
			return self._newviewobj(viewno)

	# Show the view passed as argument
	def showview(self,view,strid):
		if not view or not view._obj_:
			return
		viewno=self.getviewno(strid)
		self.frameview(view,viewno)

	# Create the view with string id
	def createview(self,strid):
		viewno=self.getviewno(strid)
		view=self._newviewobj(viewno)
		self.frameview(view,viewno)
		return view

	# Create the view with view number
	def _newviewobj(self,viewno):
		viewclass=appview[viewno]['class'] 
		viewobj=viewclass(self.getdoc())
		self.add_common_interface(viewobj,viewno)
		return viewobj

	# Return the view number from its string id
	def getviewno(self,strid):
		for viewno in appview.keys():
			if appview[viewno]['id']==strid:
				return viewno
		raise error,'undefined requested view'

	# Create the child frame that will host this view
	def frameview(self,view,viewno):
		freezeSize = appview[viewno].get('freezesize', 0)
		f=ChildFrame(view,freezeSize)
		rc=self.getPrefRect()
		f.Create(appview[viewno]['title'],None,self,0)
		self.MDIActivate(f)
	
	# Returns the child frame that hosts this view
	# returns None if not exists
	def getviewframe(self,strid):
		return self.GetParent()

	# Adds to the view interface some common attributes
	def add_common_interface(self,viewobj,viewno):
		viewobj.getframe=viewobj.GetParent
		viewobj._strid=appview[viewno]['id']
		viewobj._commandlist=[]
		viewobj._title=appview[viewno]['title']
		cmd =  appview[viewno]['cmd']
		if usercmdui.class2ui.has_key(cmd):
			viewobj._closecmdid=usercmdui.class2ui[cmd].id


	###########################################################
	# Forms management

	# Returns a new form object
	def newformobj(self,strid):
		if appform[strid].get('hosted'):
			formclass=appform[strid]['class']
			return formclass()
		else:
			return self._newformobj(strid)

	# Show the form passed as argument
	def showform(self,form,strid):
		if not form or not form._obj_:
			return
		self.frameform(form,strid)

	# Create the form with string id
	def createform(self,strid):
		form=self._newformobj(strid)
		self.frameform(form,strid)
		return form

	# Create a new form with strid
	def _newformobj(self,strid):
		formclass=appform[strid]['class'] 
		return formclass(self.getdoc())

	# Create a ChildFrameForm to host this view
	def frameform(self,form,strid):
		freezeSize=appform[strid].get('freezesize', 0)
		f=ChildFrameForm(form,freezeSize)
		rc=self.getPrefRect()
		f.Create(form._title,rc,self,0)
		self.Activate(f)


################################################
# The ChildFrame purpose is to host the views in its client area
# according to the MDIFrameWnd pattern
class ChildFrame(window.MDIChildWnd):
	def __init__(self,view,freezesize=0):
		window.MDIChildWnd.__init__(self,win32ui.CreateMDIChild())
		self._view=view
		self._freezesize=freezesize
		self._sizeFreeze=0

	# Create the OS window and hook messages
	def Create(self, title, rect = None, parent = None, maximize=0):
		self._title=title
		if rect:
			l,t,r,b=rect
			r=r+4;b=b+4
			rect=(l,t,r,b)
		style = win32con.WS_CHILD | win32con.WS_OVERLAPPEDWINDOW
		self.CreateWindow(None, title, style, rect, parent)
		if maximize and parent:parent.maximize(self)
		self.HookMessage(self.onMdiActivate,win32con.WM_MDIACTIVATE)
		self.ShowWindow(win32con.SW_SHOW)


	# Change window style before creation
	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)
		if self._freezesize:
			cs.style = win32con.WS_CHILD|win32con.WS_OVERLAPPED |win32con.WS_CAPTION|win32con.WS_BORDER|win32con.WS_SYSMENU|win32con.WS_MINIMIZEBOX
		return cs.to_csd()

	def GetNormalPosition(self):
		(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
			self.GetWindowPlacement()
		return rcNormalPosition
	
	def onMdiActivate(self,params):
		msg=win32mu.Win32Msg(params)
		hwndChildDeact = msg._wParam; # child being deactivated 
		hwndChildAct = msg._lParam; # child being activated
		if hwndChildAct == self.GetSafeHwnd():
			self._view.activate()
		elif hwndChildDeact == self.GetSafeHwnd():
			self._view.deactivate()
 
	# Creates and activates the view 	
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

	# Set the view from the view class passed as argument
	def setview(self,viewclass,id=None):
		doc=docview.Document(docview.DocTemplate())
		v = viewclass(doc)
		v.CreateWindow(self)
		self.SetActiveView(v)
		self.RecalcLayout()
		v.OnInitialUpdate()

	# Response to user close command. Delegate to view
	# the user is closing the wnd directly
	def OnClose(self):
		# we must let the view to decide:
		if hasattr(self._view,'OnClose'):
			self._view.OnClose()
		else:
			self._obj_.OnClose()

	# Called by the framework after the window has been created
	def InitialUpdateFrame(self, doc, makeVisible):
		pass
	
	# Returns the parent MDIFrameWnd	
	def getMDIFrame(self):
		return self.GetMDIFrame()

	# Returns the cmd class id	
	def GetUserCmdId(self,cmdcl):
		return self.GetMDIFrame().GetUserCmdId(cmdcl)

	# Target for commands that are enabled
	def OnUpdateCmdEnable(self,cmdui):
		cmdui.Enable(1)

	# Target for commands that are dissabled
	def OnUpdateCmdDissable(self,cmdui):
		cmdui.Enable(0)


	# Called by the framework before destroying the window
	# Used to keep instance counting for player
	def OnDestroy(self, msg):
		if self._view._strid=='pview_':
			self.GetMDIFrame()._player=None


################################################
# The ChildFrameForm purpose is to host the forms in its client area
class ChildFrameForm(window.MDIChildWnd):
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
		if hasattr(self._form,'getcreatesize'):
			cx,cy=self._form.getcreatesize()
			if cx:cs.cx=cx
			if cx:cs.cy=cy
		if self._freezesize:
			cs.style = win32con.WS_CHILD|win32con.WS_OVERLAPPED\
				|win32con.WS_CAPTION|win32con.WS_BORDER|win32con.WS_SYSMENU
			if not NO_MINIMIZEBOX:
				cs.style = cs.style |win32con.WS_MINIMIZEBOX
		return cs.to_csd()
	
	# Called by the framework when this is activated or deactivated
	def onMdiActivate(self,params):
		msg=win32mu.Win32Msg(params)
		hwndChildDeact = msg._wParam; # child being deactivated 
		hwndChildAct = msg._lParam; # child being activated
		if hwndChildAct == self.GetSafeHwnd():
			self._form.activate()
		elif hwndChildDeact == self.GetSafeHwnd():
			self._form.deactivate()
	
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
