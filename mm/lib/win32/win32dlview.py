__version__ = "$Id$"


# @win32doc|DisplayListView

# win32 libs
import win32ui, win32con, win32api
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()
from win32ig import win32ig

# app constants
from types import *
from WMEVENTS import *
from appcon import *
import __main__

# resource constants
import grinsRC

# win32 structures helpers
import win32mu
import win32menu

# usercmd
import usercmd, usercmdui, wndusercmd

# draw box imports
import win32dialog
from win32mu import Point, Rect

# base classes
from pywinlib.mfc import docview
import win32window
	
# mixins
import DropTarget

class DisplayListView(docview.ScrollView, win32window.Window, DropTarget.DropTarget):
	def __init__(self, doc):
		docview.ScrollView.__init__(self,doc)
		win32window.Window.__init__(self)
		DropTarget.DropTarget.__init__(self)

		self._curcursor = 'arrow'

		self._usesLightSubWindows = 0

		# menu support
		self._menu = None		# Dynamically created rightmousemenu
		self._popupmenu = None	# Statically created rightmousemenu (for views)
		self._popup_point =(0,0)
		self._cbld = {}
		
		# window title
		self._title = None

		# scroll indicator
		self._canscroll = 0

		# tooltip control
		self._tooltip = None

	#
	# Creation attributes
	#
	def isResizable(self):
		return 1

	# part of the constructor initialization
	def _do_init(self,parent):
		self._parent = parent
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor

	# Initialization after the OS window has been created
	# The window is attached to its parent list
	# and the messages that interest us are hooked
	def OnInitialUpdate(self):
		if not self._parent:
			self._parent=self.GetParent()
			if hasattr(self._parent,'GetMDIFrame'):
				self._parent=self._parent.GetMDIFrame()
		self._do_init(self._parent)

		self._is_active = 0
		self._cmd_state={}

		self._canscroll = 0
		# init dims
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)

		# set std attributes
		self._title = ''	
		self._window_type = SINGLE
		self._sizes = 0, 0, 1, 1
		self._dc=None

		self._topwindow = self # from the app's view this is a topwindow

		self._parent._subwindows.insert(0, self)

		self.HookMessage(self.onLButtonDown, win32con.WM_LBUTTONDOWN)
		self.HookMessage(self.onLButtonUp, win32con.WM_LBUTTONUP)
		self.HookMessage(self.onMouseMove, win32con.WM_MOUSEMOVE)

		self.HookMessage(self.onLButtonDblClk, win32con.WM_LBUTTONDBLCLK)

		self.HookMessage(self.onRButtonDown, win32con.WM_RBUTTONDOWN)

		self.HookMessage(self.onSize, win32con.WM_SIZE)

	# create the real OS window	
	def createWindow(self,parent):
		self.CreateWindow(parent)
		self._commandlist=None

	# Part of the initialization after the OS window has been created
	def OnCreate(self,params):
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)
		self.SetScrollSizes(win32con.MM_TEXT,(r-l,b-t))
		self.ResizeParentToFit()

	# called by the framework before the window is closed
	def OnClose(self):
		if self._closecmdid>0:
			self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND,self._closecmdid)
		else:
			self.GetParent().DestroyWindow()
	
	# Called by the framework. A last chance to change the window style before it is created			
	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)
		# if WS_CLIPCHILDREN is set we must
		# redraw the background of transparent children 
		if self._usesLightSubWindows:
			cs.style=cs.style | win32con.WS_CLIPCHILDREN
		return cs.to_csd()

	# The response of the view for the WM_SIZE (Resize) message						
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		self._rect=0,0,msg.width(),msg.height()
		if self.fitCanvas(msg.width(),msg.height()):
			self._resize_tree()

	def fitCanvas(self,width,height):
		changed = 0		
		import settings
		no_canvas_resize = settings.get('no_canvas_resize')
		if not no_canvas_resize:
			x,y,w,h=self._canvas
			if width>w:w=width
			if height>h:h=height
			self._canvas = (x,y,w,h)
			changed = 1
		# Otherwise we only have to update scroll position	
		self._scroll(-1)
		return changed
		
	# Adjusts the scroll sizes of the scroll view. Part of the set canvas sequence. 
	def _scroll(self,how):
		if self._canscroll==0: return
		w,h=self._canvas[2:]
		self.SetScrollSizes(win32con.MM_TEXT,(w,h))
		if how==RESET_CANVAS:
			self.ResizeParentToFit()
		self.InvalidateRect()
			
	def getscrollposition(self, units=UNIT_PXL):
		assert units == UNIT_PXL
		return self.GetScrollPosition()+self._rect[2:]

	def scrollvisible(self, coordinates, units = UNIT_SCREEN):
		if not self._canscroll:
			return
		box = self._convert_coordinates(coordinates, self._canvas, units = units)
		x, y = box[:2]
		if len(box) == 2:
			w = h = 0
		else:
			w, h = box[2:4]
		fwidth, fheight = self._canvas[2:]
		cwidth, cheight = self._rect[2:]
		xpos, ypos = self.GetScrollPosition()
		changed = 0
		if fwidth > cwidth:
			if w < cwidth:
				if xpos <= x:
					if x + w > xpos + cwidth:
						xpos = x + w - cwidth
						changed = 1
				else:
					xpos = x
					changed = 1
			else:
				if xpos != x:
					xpos = x
					changed = 1
		if fheight > cheight:
			if h < cheight:
				if ypos <= y:
					if y + h > ypos + cheight:
						ypos = y + h - cheight
						changed = 1
				else:
					ypos = y
					changed = 1
			else:
				if ypos != y:
					ypos = y
					changed = 1
		if changed:
			self.ScrollToPosition((xpos, ypos))

	# convert from client (device) coordinates to canvas (logical). Meanifull for scrollin views
	def _DPtoLP(self,pt):
		dc=self.GetDC()
		# PyCView.GetDC has called OnPrepareDC(dc)
		pt=dc.DPtoLP(pt)
		self.ReleaseDC(dc)
		return pt

	def getClipRgn(self, rel=None):
		x, y, w, h = self._canvas
		rgn = win32ui.CreateRgn()
		rgn.CreateRectRgn((x,y,x+w,y+h))
		return rgn

	# It is called by the core system when it wants to create a child window
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, units = None, bgcolor=None):
		return win32window.Region(parent, coordinates, transparent, z, units, bgcolor)

	# It is called by the core system when it wants to create a child window
	newcmwindow = newwindow

	# Sets the dynamic commands by delegating to its parent
	def set_dynamiclist(self, cmd, list):
		self._parent.set_dynamiclist(cmd,list)

	# Sets the adornments by delegating to its parent
	def set_adornments(self, adornments):
		self._parent.set_adornments(adornments)		

	# Set the title of this window
	def settitle(self,title):
		import MMurl
		title=MMurl.unquote(title)
		self._title=title
		self.GetParent().SetWindowText(title)

	# Sets the acceptable command list by delegating to its parent keeping a copy.
	def set_commandlist(self, list):
		self._commandlist=list
		if self._is_active:
			self.activate()
		# else wait until activate is called

	# Called when the view is activated 
	def activate(self):
		self._is_active=1
		self._parent.set_commandlist(self._commandlist,self._strid)
		self.set_menu_state()
		self._parent.LoadAccelTable(grinsRC.IDR_STRUCT_EDIT)

	# Called when the view is deactivated 
	def deactivate(self):
		self._is_active=0
		self._parent.set_commandlist(None,self._strid)
		self._parent.LoadAccelTable(grinsRC.IDR_GRINSED)

	# Toggles menu entries by delegating to its parent
	def set_toggle(self, command, onoff):
		self._cmd_state[command]=onoff
		if self._is_active:
			self._parent.set_toggle(command,onoff)
	def set_menu_state(self):
		for command in self._cmd_state.keys():
			onoff=self._cmd_state[command]
			self._parent.set_toggle(command,onoff)

	# Initialize the view using the arguments passed by the core system 
	def init(self, rc, title='View', units= UNIT_MM, adornments=None, canvassize=None, commandlist=None, bgcolor=None):
		self.settitle(title)
		self._title=title
		self._commandlist=commandlist
								
		if canvassize==None:self._canscroll=0
		else: self._canscroll=1

		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(l,t,r-l,b-t)
		self._doc_rect=self._rect # for RESET_CANVAS
		if canvassize!=None:
			pass # self._canvas= set_from(canvassize)

		if self._canscroll:
			self.SetScrollSizes(win32con.MM_TEXT,(self._canvas[2],self._canvas[3]))
		else:
			self.SetScaleToFitSize((r-l,b-t))
		if canvassize==None:
			self.ResizeParentToFit()
		
		if bgcolor:
			self._bgcolor = bgcolor
					
		return self
	
	# Sets the scroll mode. Enables or disables scrolling
	def setScrollMode(self,f):
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(l,t,r-l,b-t)
		self._canscroll=f
		if f:
			self.SetScrollSizes(win32con.MM_TEXT,(self._canvas[2],self._canvas[3]))
		else:
			self.SetScaleToFitSize((r-l,b-t))
			self.ResizeParentToFit()
		
	# Called directly from the core to close window. It cleans all resources and destroys the window
	def close(self):
		if self._parent is None:
			return		# already closed

		self.setcursor('arrow')
		for dl in self._displists[:]:
			dl.close()
		for win in self._subwindows[:]:
			win.close()

		if self._obj_ and self.IsWindow():
			self.destroy_menu()
			self.GetParent().DestroyWindow()

		# not highligted 
		self._showing=0

		# remove view title and 
		# disable view-context commands 
		self.deactivate()
		#self.set_commandlist(None)

		self._parent._subwindows.remove(self)
		self._parent = None
		del self._topwindow

	# get the doc of this instance
	def GetCmifDoc(self):
		if not self._parent:
			self._parent=(self.GetParent()).GetMDIFrame()
		return self._parent._cmifdoc

	# Returns true if the window is closed
	def is_closed(self):
		return not (self._obj_ and self.IsWindow())

	# Bring window in front of peers
	def pop(self, poptop=0):
		# ignore calls from core system, they produce undesired visual effects.
		# it seems that the situation is different for other platforms  
		# let the user do the activation of top windows
		# he knows better what he wants to see in front
		if poptop:
			self.do_activate()

	# Bring window in front of peers
	def do_activate(self):
		if not self._obj_: return
		mdichild = self.GetParent()
		frame = mdichild.GetMDIFrame()
		frame.ActivateFrame()
		frame.MDIActivate(mdichild)
		
	# Send window back of the peers
	def push(self):
		pass

	# Called by the framework (indirectly the OS) when has decided that the window or part of it needs to be redrawn
	def OnDraw(self,dc):
		self.PaintOn(dc)

	# Part of the drraw/update sequence.
	# Separate from OnDraw because can be 
	# called with different dc that is possible from the OnDraw
	# due to clipping mechanism. The OnDraw is called by the std ws mechanism
	def PaintOn(self,dc):
		rc=dc.GetClipBox()
		if self._redrawfunc:
			self._redrawfunc()
		elif self._active_displist:
			self._active_displist._render(dc,rc)
		if self._showing: # i.e. we must draw a frame around as
			self.showwindow_on(dc)

	# Called by the framework (indirectly the OS) to erase the background
	# return 1 to indicate 'done'
	# overwrites  DrawLayer		
	def OnEraseBkgnd(self,dc):
		rc=dc.GetClipBox()
		if self._active_displist:color=self._active_displist._bgcolor
		else: color=self._bgcolor
		dc.FillSolidRect(rc,win32mu.RGB(color))
		return 1

	###########################
	# drag and drop files support
	# enable drop
	def dragAcceptFiles(self):
		self.DragAcceptFiles(1)
		self.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)

	# disable drop
	def dragRefuseFiles(self):
		self.DragAcceptFiles(0)

	# response to drop files
	def onDropFiles(self,params):
		msg=win32mu.Win32Msg(params)	
		hDrop=msg._wParam
		inclient,point=Sdk.DragQueryPoint(hDrop)
		# convert from client to canvas pixel coordinates
		# for the benefit of scrolling views
		x,y=self._DPtoLP(point)
		# accept only drops in client area
		if inclient:
			numfiles=win32api.DragQueryFile(hDrop,-1)
			for ix in range(numfiles):
				filename=win32api.DragQueryFile(hDrop,ix)
				self.onDropEvent(DropFile,(x, y, filename))
		win32api.DragFinish(hDrop)
	
	def onDropEvent(self, event, (x, y, filename)):
		x,y = self._pxl2rel((x, y),self._canvas)
##		print 'DROP', (x, y, filename)
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
	

	# Called by the core system to show the window
	def show(self):
		if self._obj_ is None:
			return 
		else:
			if self.IsWindowVisible():
				self.update()
			else:
				self.ShowWindow(win32con.SW_SHOW)
			self.pop()

	# Called by the core system to hide the window
	def hide(self):
		#print 'hide',self,_title
		if self._obj_ is None:
			return
		else:
			self.ShowWindow(win32con.SW_HIDE)
	
	# Response to channel highlight
	def showwindow(self,color=(255,0,0)):
		self._showing = color
		dc=self.GetDC()
		if self._topwindow != self: 
			win32mu.FrameRect(dc,self.GetClientRect(),self._showing)
		self.ReleaseDC(dc)

	# Highlight the window
	def showwindow_on(self,dc):
		if self._topwindow != self: 
			win32mu.FrameRect(dc,self.GetClientRect(),self._showing)
		if self._topwindow != self and self._active_displist==None:
			self._display_info(dc)

	# Response to channel unhighlight
	def dontshowwindow(self):
		self.showwindow(self._bgcolor)
		self._showing=None
		self.update()
	
	# draw an XOR line between to given points (in pixels)
	def drawxorline(self, pt0, pt1, color=(0,0,0)):
		Sdk = win32ui.GetWin32Sdk()
		dc = self.GetDC()
		oldrop = dc.SetROP2(win32con.R2_NOTXORPEN)
		pen = Sdk.CreatePen(win32con.PS_SOLID,1,win32mu.RGB(color))
		oldpen = dc.SelectObjectFromHandle(pen)
		dc.MoveTo(pt0)
		dc.LineTo(pt1)
		dc.SelectObjectFromHandle(oldpen)
		Sdk.DeleteObject(pen)
		dc.SetROP2(oldrop)

	# Forced window update
	def update(self):
		self.InvalidateParentRect()

	# Invalidate Parent Rect that this window covers
	def InvalidateParentRect(self):
		if self._topwindow == self:
			self.InvalidateRect()
			return
		l,t,r,b=self.GetClientRect()
		ptList=[(l,t),(r,b)]
		[(l,t),(r,b)] = self.MapWindowPoints(self._parent,ptList)
		self._parent.InvalidateRect((l,t,r,b))

	# Change coordinates referense from this window to the window passed as argument
	def MapCoordTo(self,rc,wnd):
		l,t,r,b=rc
		ptList=[(l,t),(r,b)]
		[(l,t),(r,b)] = self.MapWindowPoints(wnd,ptList)
		return (l,t,r,b)


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
		self._popupmenu.create_popup_from_menubar_spec_list(menutemplate, usercmdui.usercmd2id)
		
	def _destroy_popupmenu(self):
		# Free resources held by self._popupmenu and set it to None
		if self._popupmenu:self._popupmenu.DestroyMenu()
		self._popupmenu = None		

	# Returns true if the point is inside the window
	def inside(self,pt):
		rc=win32mu.Rect(self.GetClientRect())
		return rc.isPtInRect(win32mu.Point(pt))

	def getwindowpos(self, rel=None):
		return self.GetClientRect()

	# Returns the grins document
	def getgrinsdoc(self):
		w=self._topwindow
		frame=(w.GetParent()).GetMDIFrame()		
		return frame._cmifdoc

	# Returns the grins frame
	def getgrinsframe(self):
		w=self._topwindow
		frame=(w.GetParent()).GetMDIFrame()		
		return frame


	def _convert_color(self, color):
		return color 

			
	#
	# Mouse input
	#

	# Response to left button down
	def onLButtonDown(self, params):
		if self._tooltip:
			self._tooltip.onLButtonDown(params)
		msg=win32mu.Win32Msg(params) # translate the message to a useful Python list.
		# Find modifier keys. Code gleaned from the way Michael did this in the
		# HierarchyView, I'm pretty sure there must be a better way to do this.
		keystatus = params[2] # is a bunch of boolean flags for each key.
		ctrlstatus = keystatus & win32con.MK_CONTROL # i.e. 0x8 or 0x0
		if ctrlstatus:
			params = 'add'
		else:
			params = None
		self.onMouseEvent(msg.pos(),Mouse0Press, params=params)

	# Response to left button up
	def onLButtonUp(self, params):
		if self._tooltip:
			self._tooltip.onLButtonUp(params)
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Release)

	# Response to right button down
	def onRButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		xpos,ypos=msg.pos()

		if self._menu:
			self.onLButtonDown(params, 0)
			id = self._menu.FloatMenu(self,xpos, ypos)
			if self._cbld.has_key(id) :
				callback = self._cbld[id]
				apply(callback[0], callback[1])
		elif self._topwindow==self:
			menu=None
			if self._popupmenu:
				self.onLButtonDown(params, 0)
				menu = self._popupmenu
			if not menu:return
			pt=(xpos,ypos)
			self._popup_point=pt;
			pt=self.ClientToScreen(pt);
			menu.TrackPopupMenu(pt,win32con.TPM_RIGHTBUTTON|win32con.TPM_LEFTBUTTON,
				self._parent)

	# Response to left button double click
	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params);pt=msg.pos()
		self.onMouseEvent(pt,Mouse0Press)
		self.onMouseEvent(pt,Mouse0Press)

	# Response to mouse move
	def onMouseMove(self, params):
		if self._tooltip:
			self._tooltip.onMouseMove(params)
		msg=win32mu.Win32Msg(params)
		point=msg.pos()
		if not self.setcursor_from_point(point):
			self.setcursor(self._cursor)

	# Set the cursor given its string id		
	def setcursor(self, strid):
		if self._curcursor == strid: 
			return
		self._curcursor = strid
		cursor = win32window.getcursorhandle(strid)
		Sdk.SetClassLong(self.GetSafeHwnd(),win32con.GCL_HCURSOR,cursor)
	
	#
	# Canvas and scrolling section
	#


	# Called by the core to get canvas size
	def getcanvassize(self, units = UNIT_MM):
		x,y,w,h=self._canvas
		toplevel=__main__.toplevel
		if units == UNIT_MM:
			return float(w) / toplevel._pixel_per_mm_x, \
			       float(h) / toplevel._pixel_per_mm_y
		elif units == UNIT_SCREEN:
			return float(w) / toplevel._scr_width_pxl, \
			       float(h) / toplevel._scr_height_pxl
		elif units == UNIT_PXL:
			return w, h

	# Called by the core to set canvas size
	def setcanvassize(self, how):
		x,y,w,h=self._canvas
		problem_before = (w > 0x7fff) or (h > 0x7fff)
		if type(how) is type(()):
			import sysmetrics, settings
			no_canvas_resize = settings.get('no_canvas_resize')
			units, width, height = how
			w, h = sysmetrics.to_pixels(0,0,width,height,units)[2:4]
			if not no_canvas_resize:
				rw, rh = self._rect[2:4]
				if w < rw: w = rw
				if h < rh: h = rh
		elif how == DOUBLE_WIDTH:
			w = w * 2
		elif how == DOUBLE_HEIGHT:
			h = h * 2
		elif how == DOUBLE_SIZE:
			w = w * 2
			h = h * 2
		elif how == RESET_CANVAS:
			w, h = self._rect[2],self._rect[3]
		else: # RESET_TODOC
			if hasattr(self,'_doc_rect'):
				w,h=self._doc_rect[2:4]

		if (w > 0x7fff) or (h > 0x7fff) and not problem_before:
			win32dialog.showmessage(
				"Warning: the window has grown too big (%dx%d).\nThis may cause problems."%(w, h), mtype="warning")
		self._canvas = (x,y,w,h)

		self._scroll(how)
		self._destroy_displists_tree()
		self._resize_tree()


				
	#
	#  Resize section
	#

	# Resizes all childs with this wnd as top level
	# defined for the benefit of the top level windows
	# that are not scrollable	
	def _do_resize(self,new_width=None,new_height=None):
		if self._topwindow != self:
			print '_do_resize called from the non-toplevel wnd',self
		self._destroy_displists_tree()
		rc=win32mu.Rect(self._rect)# rem: self has not been resized yet
		old_width,old_height=rc.width(),rc.height()
		self._rect=self._canvas=0,0,new_width,new_height

		if old_width<=0:old_width=1 # raise error
		if old_height<=0:old_height=1
		xf = float(new_width)/old_width;
		yf = float(new_height)/old_height

		self._resize_exec_list=[]
		hdwp = Sdk.BeginDeferWindowPos(8)
		for w in self._subwindows:
			hdwp=w._resize_wnds_tree(hdwp,xf,yf)
		Sdk.EndDeferWindowPos(hdwp)

		while len(self._resize_exec_list):
			exec_list=self._resize_exec_list[:]
			self._resize_exec_list=[]
			hdwp = Sdk.BeginDeferWindowPos(8)
			for w,xf,yf in exec_list:
				hdwp=w._resize_wnds_tree(hdwp,xf,yf)
			Sdk.EndDeferWindowPos(hdwp)

	# destroy all display lists for this wnd and iteratively 
	# for its childs, for the childs of its childs, etc	
	def _destroy_displists_tree(self):
		self._showing=None
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._destroy_displists_tree()

	# send ResizeWindow  for this and its subtree
	def _resize_tree(self):
		for w in self._subwindows:
			w._resize_tree()
		self.onEvent(ResizeWindow)
		
	# resize self wnd and iteratively 
	# all its childs, and for the childs all of their childs, etc
	def _resize_wnds_tree(self,hdwp,xf,yf):
		(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
			self.GetWindowPlacement()
		rc=win32mu.Rect(rcNormalPosition)
		l = int(float(rc.left)*xf+0.5)
		t = int(float(rc.top)*yf+0.5)
		w = int(float(rc.width())*xf+0.5)
		h = int(float(rc.height())*yf+0.5)
		self._rect=self._canvas=(0,0,w,h)
		flags=win32con.SWP_NOACTIVATE|win32con.SWP_NOZORDER|win32con.SWP_NOREDRAW| win32con.SWP_SHOWWINDOW
		hdwp=Sdk.DeferWindowPos(hdwp,self.GetSafeHwnd(),0,\
			(l,t,w,h),flags)

		# factors for self
		xf = float(w)/rc.width()
		yf = float(h)/rc.height()
		for w in self._subwindows:
			self._topwindow._resize_exec_list.append((w,xf,yf))

		return hdwp
	

	#
	# geometry and coordinates convert section overrides
	#
	
	# return the coordinates of this window in units
	def getgeometry(self, units = UNIT_MM):
		if units != UNIT_PXL:
			print 'Warning: non-UNIT_PXL getgeometry() call'
		placement = self.GetParent().GetWindowPlacement()
		outerrect = placement[4]
		out_l, out_t, out_r, out_b = outerrect
		out_w = out_r - out_l
		out_h = out_b - out_t
		in_w = out_w - 16
		in_h = out_h - 35
##		print 'getgeom', (out_l, out_t, in_w, in_h), self._rectb
		toplevel=__main__.toplevel
		if units == UNIT_PXL:
			return (out_l, out_t, in_w, in_h)
		elif units == UNIT_SCREEN:
			return self._sizes
		elif units == UNIT_MM:
			x, y, w, h = self._rectb
			return float(x) / toplevel._pixel_per_mm_x, \
			       float(y) / toplevel._pixel_per_mm_y, \
			       float(w) / toplevel._pixel_per_mm_x, \
			       float(h) / toplevel._pixel_per_mm_y
		else:
			raise error, 'bad units specified'
		
	# Returns the relative coordinates of a wnd with respect to its parent
	def getsizes(self,rc_child=None):
		if not rc_child:rc=win32mu.Rect(self.GetWindowRect())
		else: rc=rc_child
		rcParent=win32mu.Rect(self._parent.GetWindowRect())
		return self._pxl2rel(rc.xywh_tuple(),rcParent.xywh_tuple())

	#
	# Image section overrides
	#
	# Returns the size of the image
	def _image_size(self, file):
		return __main__.toplevel._image_size(file, self.getgrinsdoc())

	def _image_handle(self, file):
		return __main__.toplevel._image_handle(file, self.getgrinsdoc())


			
