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
class _CmifScrollView(cmifwnd._CmifWnd,_rbtk,docview.ScrollView):
	def __init__(self,parent, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1):
		cmifwnd._CmifWnd.__init__(self,parent)
		_rbtk.__init__(self)
		self._is_active = 0
		self._canscroll = 0
		# init dims
		l,t,r,b=self._parent.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)

		# create view
		self._doc=docview.Document(docview.DocTemplate())
		docview.ScrollView.__init__(self,self._doc)
		self.CreateWindow(parent)

		# set std attributes
		self._title = title		
		self._window_type = type_channel
		self._sizes = 0, 0, 1, 1

		# do not allow childs to go beyond me
		# since they suppose that I am a toplevel
		# (side effect of previews ui!)
		self._topwindow = self # from the app's view this is a topwindow
		parent._subwindows.insert(0, self)

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

	def OnCreate(self,params):
		print 'OnCreate',params
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
		# python view.GetDC has called OnPrepareDC(dc)
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
	def new(self,rc,title='View',units= UNIT_MM,adornments=None,canvassize=None,commandlist=None):
		if self._is_active==1:
			print 'Closing active view in order to create new'
			self.close()
			# we must notify editor.view or
			# or use a different policy

		print 'creating view',title,rc
		print 'canvassize',canvassize

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
		if self._is_active==0:return
		else: print 'closing active view'

		# old stuff remaining since we are recycling
		self.arrowcache = {}
		for win in self._subwindows[:]:
			win.close()
		self._subwindows=[]
		for dl in self._displists[:]:
			dl.close()
		self._displists=[]
		self.destroy_menu()
	
		# assert
		self._callbacks = {}
		self._accelerators = {}
		self.arrowcache = {}
		self._old_callbacks = {}
		self._cbld = {}

		# not highligted (misleading name!)
		self._showing=0

		# remove view title and 
		# disable view-context commands 
		self.settitle(None)
		self.set_commandlist(None)

		# Fit view in client rect
		self._canscroll=0
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)
		self.SetScrollSizes(win32con.MM_TEXT,(r-l,b-t))
		self._parent.RecalcLayout()
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
class GRiNSToolbar(window.Wnd):
	def __init__(self, parent):
		style = win32con.WS_CHILD |\
			win32con.WS_VISIBLE |\
			afxres.CBRS_TOP |\
			afxres.CBRS_TOOLTIPS|\
			afxres.CBRS_FLYBY|\
			afxres.CBRS_SIZE_DYNAMIC
		wndToolBar = win32ui.CreateToolBar(parent,style,afxres.AFX_IDW_TOOLBAR+1)
		#wndToolBar.LoadToolBar(grinsRC.IDB_GRINSED1)
		wndToolBar.LoadBitmap(grinsRC.IDB_GRINSED1)
		wndToolBar.EnableDocking(afxres.CBRS_ALIGN_ANY)
		wndToolBar.SetWindowText(AppDispName)
		wndToolBar.ModifyStyle(0, commctrl.TBSTYLE_FLAT)
		window.Wnd.__init__(self,wndToolBar)


class _FrameWnd(cmifwnd._CmifWnd,window.FrameWnd):
	def __init__(self,parent, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1):
		if not w or w==0:
			w=(3*scr_width_mm/4)
		if not h or h==0:
			h=(3*scr_height_mm/4)
		if not x: x=scr_width_mm/8
		if not y: y=scr_height_mm/8
		
		cmifwnd._CmifWnd.__init__(self,parent)
		self.newcmwindow=self.newwindow #alias
		window.FrameWnd.__init__(self,win32ui.CreateFrame())
		self._view=None
		self._canscroll = 0
		self._title = title		
		self._topwindow = self
		self._window_type = type_channel
		self._sizes = 0, 0, 1, 1
		parent._subwindows.insert(0, self)
		xp,yp,wp,hp = to_pixels(x,y,w,h,units)
		self._rectb= xp,yp,wp,hp
		self._sizes = (float(xp)/scr_width_pxl,float(yp)/scr_height_pxl,float(wp)/scr_width_pxl,float(hp)/scr_height_pxl)
		self._depth = toplevel.getscreendepth()

		# register top frame class
		self._clstyle=win32con.CS_DBLCLKS
		self._exstyle=0
		self._icon=Afx.GetApp().LoadIcon(grinsRC.IDI_GRINS_ED)
		self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		self._brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)

		# create a toplevel OS FrameWnd
		self._style=win32con.WS_OVERLAPPEDWINDOW
		rc=(xp,yp,xp+wp,yp+hp)
		self._obj_.Create(self._strclass,self._title,self._style,rc)
		
		# all, are historic alias but useful to markup externals
		# the symbol self._obj_ reresents the os-mfc window object
		self._wnd=self._obj_ 
		self._hWnd=self.GetSafeHwnd()

		l,t,r,b=self.GetClientRect()
		self._canvas=self._rect=(l,t,r-l,b-t)

		#create menu and toolbar
		menu=win32ui.CreateMenu()
		for key in usercmdui.menuconfig:
			menu.AppendMenu(win32con.MF_POPUP,usercmdui.stdmenu[key].GetHandle(),"&%s"%key)
		self.SetMenu(menu)
		self.DrawMenuBar()

		# direct all cmds to self.OnUserCmd but dissable them
		for cmdcl in usercmdui.class2ui.keys():
			id=usercmdui.class2ui[cmdcl].id
			self.HookCommand(self.OnUserCmd,id)
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)

		# set adorments and cmdlist
		self._qtitle={'frame':'GRiNSed','document':None,'view':None}
		self._activecmds={'frame':{},'document':{},'view':{}}
		self._dynamiclists={}
		self.set_commandlist(commandlist,'frame')

		l,t,r,b=self.GetClientRect()
		self._canvas=self._rect=(l,t,r-l,b-t)

		# the view is responsible for user input
		# but do not for Close
		r= {
			win32con.WM_CLOSE:self.onClose,
			win32con.WM_SIZE:self.onSize,
			}
		self._enable_response(r)

		if visible_channel:
			self.RecalcLayout()
			self.ShowWindow(win32con.SW_SHOW)
		
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		print 'Inproper call to FrameWnd.newwindow '
		win= _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		return win

	def newview(self,parent, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1):
		rc=(x, y, w, h)
		return self._view.new(rc,title,units,adornments,canvassize,commandlist)
	
	def newdocument(self,title,adornments,commandlist):
		self._view.close()
		self.settitle(title,'document')
		self.set_commandlist(commandlist,'document')
		if IsEditor:self.setEditorDocumentToolbar()
		self.ActivateFrame()
		return self

	def setwaiting(self,context='view'):
		pass

	def setready(self,context='view'):
		self.ActivateFrame()
		pass

	def close(self):
		self.set_commandlist(None,'document')
		self.settitle(None,'document')
		if IsEditor: self.setEditorFrameToolbar()
		self._view.RedrawWindow()
			
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		self._rect=self._canvas=0,0,msg.width(),msg.height()

	def set_commandlist(self,commandlist,context='view'):
		contextcmds=self._activecmds[context]
		menu=self.GetMenu()
		for id in contextcmds.keys():
			self.HookCommandUpdate(self.OnUpdateCmdDissable,id)
			menu.CheckMenuItem(id,win32con.MF_BYCOMMAND | win32con.MF_UNCHECKED)
		contextcmds.clear()
		if not commandlist: return
		for cmd in commandlist:
			id=usercmdui.class2ui[cmd.__class__].id
			self.HookCommandUpdate(self.OnUpdateCmdEnable,id)
			contextcmds[id]=cmd

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

	# this is called after CWnd::OnCreate 
	def OnCreate(self, createStruct):
		self.createToolbar()
		if IsEditor:self.setEditorFrameToolbar()
		else:self.setPlayerToolbar()
		return 0

	# GRiNS Toolbar
	def createToolbar(self):
		self.EnableDocking(afxres.CBRS_ALIGN_ANY)
		self._wndToolBar=GRiNSToolbar(self)
		self.DockControlBar(self._wndToolBar)
			
	# View
	def OnCreateClient(self,createStruct,createContext):
		self._view=_CmifScrollView(self,0,0,100,100,'view')
		return 1

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
		self._wndToolBar.AllocateButtons(12)

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
	
		id=usercmdui.class2ui[usercmd.HELP].id
		self._wndToolBar.SetButtonInfo(11,id,afxexttb.TBBS_BUTTON, 12)
	
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
		print 'SubWindow created with parent',parent
		cmifwnd._CmifWnd.__init__(self,parent)
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

	# debuging
	def getinfo(self):
		str= "trans=%d z=%d" % (self._transparent, self._z)
		win32ui.MessageBox(str)

################################
class WebBrowser(window.Wnd):
	def __init__(self, wnd):
		window.Wnd.__init__(self, wnd)

class _BrowserSubWindow(_SubWindow):
	def __init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z=0):
		_SubWindow.__init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z)
		x,y,w,h=self._canvas
		self._web_callbacks=[]
		# create WebBrowser 
		self._browser=WebBrowser(win32ui.CreateWebBrowser())
		self._browser.CreateBrowserWnd((x,y,x+w,y+h),self._obj_)	

	def CreateCallback(self,cbcmifanchor):
		self._web_callbacks.append(cbcmifanchor)
	def SetBkColor(self,bg):
		pass
	def SetFgColor(self,fg):
		pass

	def RetrieveUrl(self,url):
		# temp test !!!!!!
		import os
		if url[:2] != '//' or url[2:3] == '/' or url[2:3]=='\\':
			if url[2:3] == '/' or url[2:3]=='\\':
				pass #url = 'file:///' +  url[:1] + '|' + url[3:]
			else:
				url = os.getcwd()+'\\'+ url
				pass #url = 'file:///' +  url[:1] + '|' + url[3:]
		self._browser.Navigate(url)

	def _resize_controls(self):
		self._browser.SetWidth(self._canvas[2]);
		self._browser.SetHeight(self._canvas[3]);

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
			self._browser.DestroyWindow()
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
	def __init__(self,parent, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 0):
		cmifwnd._CmifWnd.__init__(self,parent)
		_rbtk.__init__(self)
		window.Wnd.__init__(self,win32ui.CreateWnd())
		parent._subwindows.insert(0, self)

		self._title = title		
		self._topwindow = self
		self._window_type = type_channel
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

		if visible_channel:
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
		
