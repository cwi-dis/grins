__version__ = "$Id$"

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
import version
import features

if settings.user_settings.get('use_nodoc_menubar'):
	USE_NODOC_MENUBAR = 1
else:
	USE_NODOC_MENUBAR = 0

# show a play seek control for player
# when doc duration is resolved
SHOW_PLAYER_SEEK = 0

###########################################################

from MainFrameSpecific import appview


#########################################################
from pywinlib.mfc import window, docview

# mixins
import win32window
import DropTarget
import Toolbars

class MDIFrameWnd(window.MDIFrameWnd, win32window.Window, 
			DropTarget.DropTarget, Toolbars.ToolbarMixin):
	wndpos=None
	wndsize=None
	wndismax=0
	def __init__(self):
		window.MDIFrameWnd.__init__(self)
		win32window.Window.__init__(self)
		DropTarget.DropTarget.__init__(self)
		Toolbars.ToolbarMixin.__init__(self)
		
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
		self.__playerstate = None

		#
		self._registry = {}

		# 
		self._peerdocid = 0
		self._peerviewports = {}

		#
		self._viewCreationListeners = []

		self._defaultwinpos = (0, 0)
		
	# Create the OS window and set the toolbar	
	def createOsWnd(self,title):
		strclass=self.registerwndclass()
		if __main__.toplevel.is_embedded():
			self._obj_.Create(strclass, title, win32con.WS_OVERLAPPEDWINDOW)
		else:		
			self._obj_.Create(strclass, title, win32con.WS_VISIBLE | win32con.WS_OVERLAPPEDWINDOW)

		# toolbar
		self.CreateToolbars()
		# Accellerators
		if features.editor:
			self.LoadAccelTable(grinsRC.IDR_GRINSED)
		else:
			self.LoadAccelTable(grinsRC.IDR_GRINS)


	# Register the window class
	def registerwndclass(self):
		# register top frame class
		clstyle=win32con.CS_DBLCLKS
		toplevel = __main__.toplevel
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
		self._mainmenu.create_from_menubar_spec_list(template,  usercmdui.usercmd2id)
		cs.hMenu=self._mainmenu.GetHandle()
		return cs.to_csd()


	# Called after the window has been created for further initialization
	# Called after CWnd::OnCreate
	def OnCreate(self, createStruct):
		toplevel = __main__.toplevel
		self.HookMessage(self.onSize,win32con.WM_SIZE)
		self.HookMessage(self.onMove,win32con.WM_MOVE)
		self.HookMessage(self.onKey,win32con.WM_KEYDOWN)
		self.HookMessage(self.onInitMenu,win32con.WM_INITMENU)
		self.HookMessage(self.onActivate,win32con.WM_ACTIVATE)

		# the view is responsible for user input
		# so do not hook other messages

		# direct all cmds to self.OnUserCmd but disable them
		L = usercmdui.getcmdids()
		for id in L:
			self.HookCommand(self.OnUserCmd,id)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_CASCADE)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_TILE_VERT)
		self.HookCommand(self.OnWndUserCmd,afxres.ID_WINDOW_TILE_HORZ)

		self.HookCommand(self.OnCloseActiveWindow,usercmdui.usercmd2id(wndusercmd.CLOSE_ACTIVE_WINDOW))
	
		id = usercmdui.usercmd2id(wndusercmd.ABOUT_GRINS)
		self.HookCommand(self.OnAbout,id)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,id)

		id = usercmdui.usercmd2id(wndusercmd.SELECT_CHARSET)
		self.HookCommand(self.OnCharset,id)
		self.HookCommandUpdate(self.OnUpdateCmdEnable,id)

		client=self.GetMDIClient()
		client.HookMessage(self.OnMdiRefreshMenu, win32con.WM_MDIREFRESHMENU)
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
		id = usercmdui.usercmd2id(wndusercmd.PASTE_DOCUMENT)
		self.HookCommand(self.OnPasteFile,id)
		self.HookCommandUpdate(self.OnUpdateEditPaste,id)
		Toolbars.ToolbarMixin.OnCreate(self, createStruct)
		return 0

	# override DropTarget.OnDragOver to protect childs
	def OnDragOver(self,dataobj,kbdstate,x,y):
		flavor, url = DropTarget.DecodeDragData(dataobj)
		if flavor != 'FileName' or not url:
			return DROPEFFECT_NONE

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
		return self.onEventEx(DragFile,(x, y, url))

	# drag and drop files support for MainFrame
	# enable drop files
	def dragAcceptFiles(self):
		self.DragAcceptFiles(1)
		self.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)
		client=self.GetMDIClient()
		client.DragAcceptFiles(1)
		client.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)

	# disable drop files
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

		id = usercmdui.usercmd2id(wndusercmd.CLOSE_ACTIVE_WINDOW)
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
		dlg=win32dialog.AboutDlg(arg=0,version = 'GRiNS ' + version.version,parent=self)
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
		client=self.GetMDIClient()
		if id==afxres.ID_WINDOW_TILE_HORZ:
			client.SendMessage(win32con.WM_MDITILE, win32con.MDITILE_HORIZONTAL)			
		elif id==afxres.ID_WINDOW_TILE_VERT:
			client.SendMessage(win32con.WM_MDITILE, win32con.MDITILE_VERTICAL)			
		elif id==afxres.ID_WINDOW_CASCADE:
			client.SendMessage(win32con.WM_MDICASCADE)			
	
	# Response to command to close the active window
	def OnCloseActiveWindow(self,id,code):
		t = self.MDIGetActive()
		if not t: return
		f, ismax=t
		if self._active_child and\
			hasattr(self._active_child._view, '_commandlist') and\
			self._active_child._view._commandlist:
			id = usercmdui.usercmd2id(usercmd.CLOSE_WINDOW)
			self.PostMessage(win32con.WM_COMMAND, id)
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
		self._title = version.title # ignore title		
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
	

	# Associate this frame with the document
	def setdocument(self, cmifdoc, adornments, commandlist, peerdocid=0):
		self._peerdocid = peerdocid
		self._cmifdoc = cmifdoc
		self.assertPanelVisible()
		import MMurl
		basename=MMurl.unquote(cmifdoc.basename)
		self.settitle(basename,'document')
		self.set_commandlist(commandlist,'document')
		import Player
		self.setplayerstate(Player.STOPPED)
		if adornments and adornments.has_key('pulldown'):
			pulldownmenus = adornments['pulldown']
		else:
			pulldownmenus = None
		self.setToolbarPulldowns(pulldownmenus)
		if features.editor:
			self.setEditorDocumentMenu(1)
		self.RecalcLayout()
		if not __main__.toplevel.is_embedded():		
			self.ActivateFrame(win32con.SW_SHOW)
		if not features.editor and SHOW_PLAYER_SEEK:
			player = self._cmifdoc.player
			ctx = player.userplayroot.GetContext()
			fulldur = self._cmifdoc.player.userplayroot.calcfullduration(ctx)
			if fulldur>0:
				self.__slider = win32dialog.SeekDialog('Seek', self)
				self.__slider.setRange(0, fulldur)
				self.__slider.updateposcallback = player.setstarttime
				self.__slider.timefunction = player.scheduler.timefunc
				self.__slider.canusetimefunction = player.isplaying

	def settoolbarpulldowns(self, pulldownmenus):
		self.setToolbarPulldowns(pulldownmenus)

	def setEditorDocumentMenu(self, flag):
		if USE_NODOC_MENUBAR:
			temp=self._mainmenu
			self._mainmenu=win32menu.Menu()
			if not flag and hasattr(MenuTemplate,'NODOC_MENUBAR'):
				template=MenuTemplate.NODOC_MENUBAR
			else:
				template=MenuTemplate.MENUBAR
			self._mainmenu.create_from_menubar_spec_list(template, usercmdui.usercmd2id)
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
	def newwindow(self, x, y, w, h, title,
		      pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1, bgcolor = None):
		if adornments.has_key('view'): strid = adornments['view']
		else:  raise "undefined view request"
		if strid=='pview_':
			exporting = adornments.get('exporting')
			toplevel = __main__.toplevel
			if toplevel.is_embedded() or self._peerdocid:
				return self.newEmbedded(x, y, w, h, title, units, adornments, canvassize, commandlist, strid, bgcolor)
			elif exporting:
				return self.newExport(x, y, w, h, title, units, adornments,canvassize, commandlist,strid, bgcolor)
		return self.newview(x, y, w, h, title, units, adornments, canvassize, commandlist, strid, bgcolor)


	def newExport(self, x, y, w, h, title, units = UNIT_MM, adornments=None, canvassize=None, commandlist=None, strid='cmifview_', bgcolor=None):
		return win32window.ViewportContext(self, w, h, units, bgcolor)

	def newEmbedded(self, x, y, w, h, title, units = UNIT_MM, adornments=None, canvassize=None, commandlist=None, strid='cmifview_', bgcolor=None):
		import embedding
		wnd = embedding.EmbeddedWnd(self, w, h, units, bgcolor, title, self._peerdocid)
		self._peerviewports[id(wnd)] = wnd
		return wnd

	def setEmbeddedHwnd(self, wndid, hwnd):
		ewnd = self._peerviewports.get(wndid)
		if ewnd: ewnd.setPeerWindow(hwnd)

	def getEmbeddedWnd(self, wndid):
		return self._peerviewports.get(wndid)

	# Return the framework document object associated with this frame
	def getdoc(self):
		if self.countMDIChildWnds()==0:
			self._doc=docview.Document(docview.DocTemplate())
		return self._doc

	# Create a text viewer
	def textwindow(self, text, xywh=None, readonly = 0, close_callback = None, title = ''):
		sv=self.newviewobj('sview_')
		sv.settext(text)
		sv.set_readonly(readonly)
		sv.set_closecallback(close_callback)
		self.showview(sv,'sview_', xywh)
		if self._cmifdoc:
			sv.GetParent().SetWindowText(title)
		return sv

	# Creates a new ChildFrame 
	def newChildFrame(self,view,decor=None):
		return ChildFrame(view, decor)

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
		if not __main__.toplevel.is_embedded():		
			self.ActivateFrame(win32con.SW_SHOW)

	# Close the opened document
	def close(self):
		# 1. destroy cascade menus
		exceptions=[usercmd.OPEN_RECENT,]
		self._mainmenu.clear_cascade_menus(exceptions)

		# 2. then the document
		__main__.toplevel.cleardoccache(self._cmifdoc)
		self._cmifdoc=None
		self.set_commandlist(None,'document')
		self.settitle(None,'document')
		if features.editor and len(__main__.toplevel._subwindows)==1:
##			self.setEditorFrameToolbar()
			self.setEditorDocumentMenu(0)
		# and document's views
		self.close_all_views()
		self.setplayerstate(None)

		# 3. if there is another top-level frame
		# we should close self frame
		if len(__main__.toplevel._subwindows)>1:
			__main__.toplevel._subwindows.remove(self)
			self.DestroyWindow()	
		else:
			self.onApplicationExit()

	# XXXXXXXXXXXXXXXXXXXXXXXXXX
	# application's ui exit hook
	# XXXXXXXXXXXXXXXXXXXXXXXXXX
	def onApplicationExit(self):
		Toolbars.ToolbarMixin.OnClose(self)

	# Called by the framework when the user closes the window
	def OnClose(self):
		if len(__main__.toplevel._subwindows)>1:
			self.PostMessage(win32con.WM_COMMAND, usercmdui.usercmd2id(usercmd.CLOSE))
		else:
			self.PostMessage(win32con.WM_COMMAND, usercmdui.usercmd2id(usercmd.EXIT))

	# Response to resizing		
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized():
			self.setMDIChildWndsMinimizedFlag(1)
			return
		self.setMDIChildWndsMinimizedFlag(0)
		self.RecalcLayout()
		self._rect=self._canvas=0,0,msg.width(),msg.height()
		MDIFrameWnd.wndismax=msg.maximized()
		if not msg.maximized():
			rc=self.GetWindowRect()
			MDIFrameWnd.wndsize=win32mu.Point((rc[2]-rc[0],rc[3]-rc[1]))

	# Response to mouse move
	def onMove(self,params):
		rc=self.GetWindowRect()
		MDIFrameWnd.wndpos = win32mu.Point((rc[0],rc[1]))

	# Resize window
	def setcoords(self,coords, units=UNIT_MM):
		x, y, w, h = coords
		x,y,w,h = sysmetrics.to_pixels(x,y,w,h,units)
		rc = x, y, x+w, y+h
		#l,t,r,b = self.CalcWindowRect(rc, 0)
		#w=r-l+2*cxframe+4
		#h=b-t+3*cycaption+16+4
		self.RecalcLayout()
		flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE
		self.SetWindowPos(0, (0,0,w,h), flags)
		

	# Maximize window
	def maximize(self,child):
		client=self.GetMDIClient()
		client.SendMessage(win32con.WM_MDIMAXIMIZE, child.GetSafeHwnd())


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
	def append_menu_entry(self, entry=None):
		if not self._menu: 
			return
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
		self._popupmenu.create_popup_from_menubar_spec_list(menutemplate, usercmdui.usercmd2id)
		
	def _destroy_popupmenu(self):
		# Free resources held by self._popupmenu and set it to None
		if self._popupmenu:
			self._popupmenu.DestroyMenu()
		self._popupmenu = None		

	# Returns a submenu from its string id (e.g 'File','Edit',etc)
	def get_submenu(self,strid):
		return self._mainmenu._submenus_dict.get(strid)

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
		return __main__.toplevel._image_size(file, self.getgrinsdoc())

	def _image_handle(self, file):
		return __main__.toplevel._image_handle(file, self.getgrinsdoc())


	###############################################
	# BEGIN CMD LIST SECTION

	# Set/reset commandlist for context
	def set_commandlist(self,commandlist,context):
		# we have a new commandlist for this context 
		# so, disable previous
		self.dissable_context(context)

		# enable cmds in commandlist
		# cash ids to cmd map for OnUserCmd
		if commandlist:
			for cmd in commandlist:
				id = usercmdui.usercmd2id(cmd.__class__)
				self.enable_cmd(id)
				self._activecmds[context][id]=cmd
		self.setplayerstate(self.__playerstate)

	# Disable context commands
	def dissable_context(self, context):
		# assert there is an entry for this context
		if not self._activecmds.has_key(context):
			self._activecmds[context]={}
			return
		contextcmds=self._activecmds[context]
		# we must clean here so that disable_cmd does its job
		self._activecmds[context]={}
		commandlist=contextcmds.values()
		for cmd in commandlist:
			self.dissable_cmd(usercmdui.usercmd2id(cmd.__class__))
		
	def enable_cmd(self,id):
		self.HookCommandUpdate(self.OnUpdateCmdEnable,id)

	# disable a cmd only if not in self._activecmds
	def dissable_cmd(self,id):
		for context in self._activecmds.keys():
			if self._activecmds[context].has_key(id):
				return
		# not in other command lists
		self.HookCommandUpdate(self.OnUpdateCmdDissable,id)

	# Toggle commands (check/uncheck menu entries)		
	def set_toggle(self, cmdcl, onoff):
		id = usercmdui.usercmd2id(cmdcl)
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
		id_play = usercmdui.usercmd2id(usercmd.PLAY)
		id_pause = usercmdui.usercmd2id(usercmd.PAUSE)
		id_stop = usercmdui.usercmd2id(usercmd.STOP)
		if state == Player.PLAYING:
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndUncheck,id_pause)
			self.HookCommandUpdate(self.OnUpdateCmdDissableAndUncheck,id_play)
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndUncheck,id_stop)
		elif state == Player.PAUSING:
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndUncheck,id_play)
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndCheck,id_pause)
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndUncheck,id_stop)
		elif state == Player.STOPPED:
			self.HookCommandUpdate(self.OnUpdateCmdEnableAndUncheck,id_play)
			self.HookCommandUpdate(self.OnUpdateCmdDissableAndUncheck,id_stop)
			self.HookCommandUpdate(self.OnUpdateCmdDissableAndUncheck,id_pause)
		else:
			self.HookCommandUpdate(self.OnUpdateCmdDissableAndUncheck,id_pause)
			self.HookCommandUpdate(self.OnUpdateCmdDissableAndUncheck,id_play)
			self.HookCommandUpdate(self.OnUpdateCmdDissableAndUncheck,id_stop)
		# XXX WARNING: if you uncomment that method, you get some ramdom python crash
		try:
			self.updatePanelCmdUI()
		except:
			pass

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

	def OnUpdateCmdEnableAndUncheck(self,cmdui):
		cmdui.SetCheck(0)
		cmdui.Enable(1)

	def OnUpdateCmdDissableAndUncheck(self,cmdui):
		cmdui.SetCheck(0)
		cmdui.Enable(0)

	def OnUpdateCmdDissable(self,cmdui):
		# WARNING. Don't call the SetCheck method here.
		# If you do this, it's turn a button from the PushBotton the to the CheckBox type (see MFC spec.),
		# (and the button would stay push after an action of the user, instead to back automaticly)
		# Currently the only buttons who needs to keep the 'push' state are : Play, Pause, and Stop
		# for this three button, we have a special method (OnUpdateCmdDissableAndUncheck) with uncheck as well
		# the control
		# note: to change the state of any check marks (in menu), use a different method
		cmdui.Enable(0)
		cmdui.ContinueRouting()

	# Response to a user command (menu selection)
	def OnUserCmd(self,id,code):
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

	# Get the user command class instance
	def GetUserCmd(self, cmdcl):
		id = usercmdui.usercmd2id(cmdcl)
		cmd=None
		for context in self._activecmds.keys():
			contextcmds=self._activecmds[context]
			if contextcmds.has_key(id):
				cmd = contextcmds[id]
				break
		return cmd

	# END CMD LIST SECTION
	###############################################



	###############################################
	# BEGIN DYNAMIC CMD LIST SECTION

	# Set the dynamic commands associated with the command class
	def set_dynamiclist(self, command, list):
		self._dynamiclists[command] = list
		submenu = self._mainmenu.get_cascade_menu(command)
		idstart = usercmdui.usercmd2id(command) + 1
		cmd = self.GetUserCmd(command)
		if cmd is None:
			# disable submenu cmds?
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
			win32menu._create_menu(submenu, menuspec, idstart, self._dyncmds[command])
			self.set_dyncbd(self._dyncmds[command], submenu)
		
		# update popupmenu
		if self._popupmenu:
			submenu = self._popupmenu.get_cascade_menu(command)
			if submenu:
				self._popupmenu.clear_cascade(command)
				win32menu._create_menu(submenu, menuspec, idstart, self._dyncmds[command])
		
	# Helper function to return the dynamic submenu
	def get_cascade_menu(self,id):
		cl = usercmdui.get_cascade(id)
		return self._mainmenu.get_cascade_menu(cl)
	
	# Response to dynamic menus commands	
	def OnUserDynCmd(self,id,code):
		for cbd in self._dyncmds.values():
			if cbd.has_key(id):
				if not cbd[id]:return
				# call check_cascade_menu_entry before
				# apply because the call may result
				# in a call to set_dynamiclist
				self.check_cascade_menu_entry(id)
				apply(apply, cbd[id])
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
		id = usercmdui.usercmd2id(cmdcl)
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

	# Bring to top of peers
	def pop(self):
		self.BringWindowToTop()

	# Send to back of peers
	def push(self):
		pass

	# Called by the framework before destroying the window
	def OnDestroy(self, msg):
		self.DestroyToolbars()
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

	def isplayer(self,f):
		if not hasattr(f,'_view'): return 0
		return f._view._strid=='pview_'

	# Show or hide all childs but the player
	def showChilds(self,flag):
		# XXXX Jack thinks this may not be needed anymore,
		# and part of the old rb_ stuff.
		self.ShowToolbars(flag)

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


	###########################################################
	# General MDI childs navigation utilities

	# Return the number of childs
	def countMDIChildWnds(self):
		currentChild=None
		count=0
		while 1:
			currentChild=self.getNextMDIChildWnd(currentChild)
			if currentChild:count=count+1
			else: break
		return count

	def setMDIChildWndsMinimizedFlag(self, flag):
		currentChild=None
		while 1:
			currentChild = self.getNextMDIChildWnd(currentChild)
			if currentChild:
				if hasattr(currentChild, 'SetMinimizedFlag'):
					currentChild.SetMinimizedFlag(flag)
				else:
					currentChild._isminimized = flag
			else: 
				break

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
		viewclass = appview[strid]['class'] 
		
		viewid = strid+title
		if self._registry.has_key(viewid):
			x, y = self._registry[viewid]

		# viewclass is a class that is initialised here now.
		# For example, it is a _StructView (from _StructView.py) for the HierarchyView.
		# -mjvdg.
		view=viewclass(self.getdoc(), bgcolor)
		self.add_common_interface(view,strid)

		rcFrame = self._makeframecoords((x,y,w,h),units)
		f=ChildFrame(view)	# This is where most child MDI windows get made.
		f.Create(title,rcFrame,self,0)

		view.init((0,0,w,h),title,units,adornments,canvassize,commandlist,bgcolor)
		self.MDIActivate(f)
		return view

	# Create a new view object 
	def newviewobj(self, strid):
		viewobj = None
		viewdict =  appview.get(strid)
		if viewdict:
			viewclass = viewdict['class'] 
			viewobj = viewclass(self.getdoc())
			if viewdict['cmd'] > 0:
				self.add_common_interface(viewobj, strid)
			return viewobj
		return None

	# Show the view passed as argument
	def showview(self, view, strid, xywh=None):
		if not view or not view._obj_:
			return
		self.frameview(view, strid, xywh)

	# Create the view with string id
	def createview(self, strid):
		view = self.newviewobj(strid)
		self.frameview(view, strid)
		return view

	# Create the child frame that will host this view
	def frameview(self, view, strid, xywh=None):
		if not appview.has_key(strid):
			print 'Unknown frameview name:', view
			return
		ltrb = self._makeframecoords(xywh)
		if strid == 'lview2_':
			f = SplitterBrowserChildFrame(view, not view.isResizeable())
			f.Create(appview[strid]['title'],ltrb,self,0)
		else:
			f = ChildFrame(view, not view.isResizeable())
			f.Create(appview[strid]['title'],ltrb,self,0)
		self.MDIActivate(f)
		self.updateViewCreationListeners(view, strid)
	
	def _makeframecoords(self, xywh, units=UNIT_PXL):
		# Convert GRiNS xywh-style coordinates to ltrb-style.
		# The w and h are also the sizes for the inner area, they
		# should be offset for the outer area
		if xywh is None:
			return None
		x, y, w, h = xywh
		if x <= 0 or y <= 0:
			x, y = self._defaultwinpos
			if y > 50:
				self._defaultwinpos = (0, y)
			else:
				self._defaultwinpos = (x+10, y+10)
		if w<=0 or h<= 0:
			w = sysmetrics.scr_width_pxl/2
			h = sysmetrics.scr_height_pxl/2

		x,y,w,h=sysmetrics.to_pixels(x,y,w,h,units)
		dw=2*win32api.GetSystemMetrics(win32con.SM_CXEDGE)+2*sysmetrics.cxframe
		dh=sysmetrics.cycaption + 2*win32api.GetSystemMetrics(win32con.SM_CYEDGE)+2*sysmetrics.cyframe
		rcFrame=(x,y,x+w+dw,y+h+dh)
		return rcFrame

	# Adds to the view interface some common attributes
	def add_common_interface(self, viewobj, strid):
		viewobj._strid = strid
		viewobj._commandlist = []
		viewobj._title = appview[strid]['title']
		cmd =  appview[strid]['cmd']
		viewobj._closecmdid = usercmdui.usercmd2id(cmd)

	def registerPos(self, view):
		cframe = view.GetParent()
		mdilient = self.GetMDIClient()
		viewid = view._strid + cframe.GetWindowText()
		l, t, r, b = cframe.GetWindowRect()
		l, t = mdilient.ScreenToClient((l,t))
		self._registry[viewid] = l, t

	###########################################
	# Experimental view creation notification interface
	# Registered listeners are notified when a view is created

	def addViewCreationListener(self, listener):
		if not hasattr(listener, 'onViewCreated'):
			print 'object', listener, 'should implement method onViewCreated'
			return
		if listener not in self._viewCreationListeners:
			self._viewCreationListeners.append(listener)

	def removeViewCreationListener(self, listener):
		if listener in self._viewCreationListeners:
			self._viewCreationListeners.remove(listener)

	def updateViewCreationListeners(self, view, strid):
		for listener in self._viewCreationListeners:
			listener.onViewCreated(self, view, strid)

################################################
# The ChildFrame purpose is to host the views in its client area
# according to the MDIFrameWnd pattern
class ChildFrame(window.MDIChildWnd):
	def __init__(self, view, freezesize=0):
		# This is usually called from MDIFrameWnd.newview
		window.MDIChildWnd.__init__(self,win32ui.CreateMDIChild())
		self._view=view		# Currently, this is the only place that this Frame's view is assigned.
		self._freezesize = freezesize
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
		else:
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

	# Target for commands that are enabled
	def OnUpdateCmdEnable(self,cmdui):
		cmdui.Enable(1)

	# Target for commands that are disabled
	def OnUpdateCmdDissable(self,cmdui):
		cmdui.Enable(0)

	def SetMinimizedFlag(self, flag):
		self._isminimized = flag
		if self._view:
			self._view._isminimized = flag

#########################
from GenView import GenView

class BrowserPane(GenView, docview.TreeView):
	def __init__(self, doc, bgcolor=None):
		# base init
		GenView.__init__(self, bgcolor)
		docview.TreeView.__init__(self, doc)

	def OnCreate(self, params):
		l,t,r,b = self.GetClientRect()
		self._rect= self._canvas = (0,0,r-l,b-t)

	def OnClose(self):
		self.GetParent().GetParent().DestroyWindow()

class SplitterBrowserChildFrame(ChildFrame):
	def __init__(self, view, freezesize=0):
		ChildFrame.__init__(self, view, freezesize)
		self._splitter = win32ui.CreateSplitter()
	
	def OnCreateClient(self, cp, context):
		self._splitter.CreateStatic(self, 1, 2)
		doc = docview.Document(docview.DocTemplate())

		v1 = BrowserPane(doc)
		v1._parent = self
		v1._strid = 'test1'

		v2 = self._view
		v2._parent = self

		self._splitter.CreateView(v1, 0, 0, (150, 400))
		self._splitter.CreateView(v2, 0, 1, (300, 400))
		
		v1.OnInitialUpdate()
		v2.OnInitialUpdate()

	def OnClose(self):
		# we must let the view to decide:
		if hasattr(self._view,'OnClose'):
			self._view.OnClose()
		else:
			self.DestroyWindow()

	def SetMinimizedFlag(self, flag):
		self._isminimized = flag
		if self._view:
			self._view._isminimized = flag
