__version__ = "$Id$"


""" @win32doc|_CmifView
This module exports the important classes:
_CmifView or (_Window), _SubWindow.
_CmifStructView a specialization of _CmifView for smooth drawing
_CmifPlayerView a specialization of _CmifView for limiting 'if' programming

The _CmifView is used for toplevel childs of
the MainFrame that have a display list.
The HierarchyView, the Timeline view and the
Toplevel Layout channels are alias to _CmifView
(see ViewServer.py)

The _SubWindow class is used solely for window channels

Both classes inherit from _CmifWnd
(see cmifwnd.py for the functionality this mixin 
class has to offer)

"""

import win32ui, win32con, win32api
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()
import os

from types import *
from WMEVENTS import *
from appcon import *
import grinsRC

from DisplayList import DisplayList

import win32mu

# constants to select web browser control
[IE_CONTROL, WEBSTER_CONTROL]=0, 1

###########################################################
# import window core stuff
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl
import cmifwnd	
import afxexttb # part of generated afxext.py

class _CmifView(cmifwnd._CmifWnd,docview.ScrollView):

	# Class contructor. initializes base classes
	def __init__(self,doc):
		cmifwnd._CmifWnd.__init__(self)
		docview.ScrollView.__init__(self,doc)

	# Initialization after the OS window has been created
	# The window is attached to its parent list
	# and the messages that interest us us are hooked
	def OnInitialUpdate(self):
		if not self._parent:
			self._parent=(self.GetParent()).GetMDIFrame()
		self._do_init(self._parent)
		self._is_active = 0
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

		r= {win32con.WM_RBUTTONDOWN:self.onRButtonDown,
			win32con.WM_LBUTTONDBLCLK:self.onLButtonDblClk,
			win32con.WM_LBUTTONDOWN:self.onLButtonDown,
			win32con.WM_LBUTTONUP:self.onLButtonUp,
			win32con.WM_MOUSEMOVE:self.onMouseMove,
			win32con.WM_SIZE:self.onSize,
			}
		self._enable_response(r)
	
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
		if self.in_create_box_mode():return
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
		#cs.style=cs.style|win32con.WS_CLIPCHILDREN
		return cs.to_csd()

	# The response of the view for the WM_SIZE (Resize) message						
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		self._rect=0,0,msg.width(),msg.height()
		self.fitCanvas(msg.width(),msg.height())
		self._resize_tree()

	def fitCanvas(self,width,height):		
		x,y,w,h=self._canvas
		if width>w:w=width
		if height>h:h=height	
		self._canvas = (x,y,w,h)
		self._scroll(-1)
		
	# Adjusts the scroll sizes of the scroll view. Part of the set canvas sequence. 
	def _scroll(self,how):
		if self._canscroll==0: return
		w,h=self._canvas[2:]
		self.SetScrollSizes(win32con.MM_TEXT,(w,h))
		if how==RESET_CANVAS:
			self.ResizeParentToFit()
		self.InvalidateRect()
			
	# convert from client (device) coordinates to canvas (logical). Meanifull for scrollin views
	def _DPtoLP(self,pt):
		dc=self.GetDC()
		# PyCView.GetDC has called OnPrepareDC(dc)
		pt=dc.DPtoLP(pt)
		self.ReleaseDC(dc)
		return pt

	# It is called by the core system when it wants to create a child window
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z, units)

	# It is called by the core system when it wants to create a child window
	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z, units)	

	# Sets the dynamic commands by delegating to its parent
	def set_dynamiclist(self, cmd, list):
		self._parent.set_dynamiclist(cmd,list)

	# Sets the adornments by delegating to its parent
	def set_adornments(self, adornments):
		self._parent.set_adornments(adornments)

	# Toggles menu entries by delegating to its parent
	def set_toggle(self, command, onoff):
		self._parent.set_toggle(command,onoff)
		
	# Sets the acceptable command list by delegating to its parent keeping a copy.
	def set_commandlist(self, list):
		self._commandlist=list
		self._parent.set_commandlist(list,self._strid)

	# Set the title of this window
	def settitle(self,title):
		self._title=title
		#self._parent.settitle(title,'view')

	# Called when the view is activated/deactivated 
	def onActivate(self,f):
		pass

	# Initialize the view using the arguments passed by the core system 
	def init(self,rc,title='View',units= UNIT_MM,adornments=None,canvassize=None,commandlist=None):
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
		self._is_active=1
		return self
	
	# Sets the scroll mode. Enables or dissables scrolling
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
		self.set_commandlist(None)

		self._parent._subwindows.remove(self)
		self._parent = None
		del self._topwindow
		del self.arrowcache

	# get the doc of this instance
	def GetCmifDoc(self):
		if not self._parent:
			self._parent=(self.GetParent()).GetMDIFrame()
		return self._parent._cmifdoc

	# Returns true if the window is closed
	def is_closed(self):
		return not (self._obj_ and self.IsWindow())

	# Bring window in front of peers
	def pop(self):
		# Do nothing
		# Improperly used by core system
		pass

	# Bring window in front of peers
	def activate(self):
		self._parent.ActivateFrame()
		self._parent.MDIActivate(self.GetParent())
		
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
		if self.in_create_box_mode() and self.get_box_modal_wnd()==self:
			self.notifyListener('OnDraw',dc)
			return
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
		# default is:
		# if self._transparent==0:return self._obj_.OnEraseBkgnd(dc)
		if self.in_create_box_mode() and self.get_box_modal_wnd()==self:
			return
		rc=dc.GetClipBox()
		if self._active_displist:color=self._active_displist._bgcolor
		else: color=self._bgcolor
		dc.FillSolidRect(rc,win32mu.RGB(color))
		return 1

	# Returns the coordinates of this window in pix
	# override cmifwnd method to adjust/mangle for frame
	def getpixgeometry(self):
		(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
			self.GetWindowPlacement()
		rc=win32mu.Rect(rcNormalPosition)
		ptList=[(0,0),]
		townd=self._parent.GetMDIClient()
		x,y= self.MapWindowPoints(townd,ptList)[0]
		from sysmetrics import cycaption,cyborder,cxborder,cxframe
		y=y-cycaption-8
		x=x-2*cxframe
		return x,y,rc.width(),rc.height()


#################################################
# Specialization of _CmifView for player
# i.e Resizing/Closing		
class _CmifPlayerView(_CmifView):
	# Class contructor. initializes base classes
	def __init__(self,doc):
		_CmifView.__init__(self,doc)
		self._canclose=1
		self._tid=None

	def OnInitialUpdate(self):
		_CmifView.OnInitialUpdate(self)
		#self.HookMessage(self.onPostResize,win32con.WM_USER)

	# Do not close and recreate topwindow, due to flushing screen
	# and loose of focus. 
	# Nobody would excpect to destroy a window by resizing it!
	def close(self):
		if self._canclose:
			_CmifView.close(self)
					
	# The response of the view for the WM_SIZE (Resize) message						
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return

		# This historic function does not need to be
		# called since the channels are now destroyed
		# and re-created. The effect of calling it is
		# a flickering screen 
#		self._do_resize(msg.width(),msg.height())
		
		# destroy displists while dragging?
		# i.e repaint previous content while dragging?
		# Its a preference. 
#		self._destroy_displists_tree()

		# after _do_resize because it uses old self._rect
		self._rect=0,0,msg.width(),msg.height()
		self.fitCanvas(msg.width(),msg.height())

		# Do not use PostMessage. ChannelWindow.resize
		# fails to save_geometry if the sys attribute
		# 'Show Window Contents While Dragging' is set
		# since then this function is called to often
#		self.PostMessage(win32con.WM_USER)
		from __main__ import toplevel
		if self._tid:
			toplevel.canceltimer(self._tid)
		self._tid=toplevel.settimer(0.2,(self.onPostResize,()))

	def onPostResize(self,params=None):
		self._tid=None
		self._canclose=0
		self._resize_tree()
		self._canclose=1


#################################################
# Specialization of _CmifView for smooth drawing		
class _CmifStructView(_CmifView):
	# Class contructor. initializes base classes
	def __init__(self,doc):
		_CmifView.__init__(self,doc)
		self._button_down=0
		self._drag_cmd_send=0

	def PaintOn(self,dc):
		# only paint the rect that needs repainting
		rect=win32mu.Rect(dc.GetClipBox())

		# draw to offscreen bitmap for fast looking repaints
		dcc=win32ui.CreateDC()
		dcc.CreateCompatibleDC(dc)

		bmp=win32ui.CreateBitmap()
		bmp.CreateCompatibleBitmap(dc,rect.width(),rect.height())
		
		# called by win32ui
		#self.OnPrepareDC(dcc)
		
		# offset origin more because bitmap is just piece of the whole drawing
		dcc.OffsetViewportOrg((-rect.left, -rect.top))
		oldBitmap = dcc.SelectObject(bmp)
		dcc.SetBrushOrg((rect.left % 8, rect.top % 8))
		dcc.IntersectClipRect(rect.tuple())

		# background decoration on dcc
		dcc.FillSolidRect(rect.tuple(),win32mu.RGB(self._active_displist._bgcolor))

		# draw objects on dcc
		if self._active_displist:
			self._active_displist._render(dcc,rect.tuple())

		# copy bitmap
		dcc.SetViewportOrg((0, 0))
		dcc.SetWindowOrg((0,0))
		dcc.SetMapMode(win32con.MM_TEXT)
		dc.BitBlt(rect.pos(),rect.size(),dcc,(0, 0), win32con.SRCCOPY)

		# clean up
		dcc.SelectObject(oldBitmap)
		dcc.DeleteDC()
		del bmp

	def OnEraseBkgnd(self,dc):
		return 1

	# Response to left button double click
	def onLButtonDblClk(self, params):
		import usercmd, usercmdui
		#self._parent.PostMessage(win32con.WM_COMMAND,usercmdui.INFO_UI.id)
		callAttr=0
		for cmd in self._commandlist:
			if cmd.__class__==usercmd.INFO:
				self._parent.PostMessage(win32con.WM_COMMAND,usercmdui.INFO_UI.id)
				return
			if cmd.__class__==usercmd.ATTRIBUTES:
				callAttr=1
		if callAttr:
			self._parent.PostMessage(win32con.WM_COMMAND,usercmdui.ATTRIBUTES_UI.id)

	# Response to mouse move
	def onMouseMove(self, params):
		_CmifView.onMouseMove(self, params)
		if not self._button_down or self._drag_cmd_send: return
		import usercmd,usercmdui
		for cmd in self._commandlist:
			if cmd.__class__==usercmd.MOVE_CHANNEL:
				self._parent.PostMessage(win32con.WM_COMMAND,usercmdui.MOVE_CHANNEL_UI.id)
				self._drag_cmd_send=1
				break

	# Response to left button down
	def onLButtonDown(self, params):
		_CmifView.onLButtonDown(self, params)
		self._button_down=1
				
	# Response to left button up
	def onLButtonUp(self, params):
		_CmifView.onLButtonUp(self, params)
		self._button_down=0
		if self._drag_cmd_send:
			msg=win32mu.Win32Msg(params)
			self.onMouseEvent(msg.pos(),Mouse0Press)
			self.onMouseEvent(msg.pos(),Mouse0Release)
			self._drag_cmd_send=0

				
#################################################
class _SubWindow(cmifwnd._CmifWnd,window.Wnd):

	# Class contructor. Initializes the class and creates the OS window
	def __init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z=0, units=None):
		cmifwnd._CmifWnd.__init__(self)
		self._do_init(parent)

		self._window_type = type_channel
		self._topwindow = parent._topwindow
		self._z = z
		x, y, w, h = parent._convert_coordinates(rel_coordinates,
					crop = 1, units = units)
		self._rect = 0, 0, w, h
		self._canvas = 0, 0, w, h
		self._rectb = x, y, w, h
		self._sizes = parent._inverse_coordinates(self._rectb)

		# create an artificial name 
		self._num = len(parent._subwindows)+1
		self._title = 'c%d'%self._num

		
		# insert window in _subwindows list at correct z-order
		for i in range(len(parent._subwindows)):
			if self._z > parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:parent._subwindows.append(self)
			

		# if a parent is transparent all of its childs must be transparent	
		if parent._transparent in (1,-1):
			self._transparent = parent._transparent
		else:
			if transparent not in (-1, 0, 1):
				raise error, 'invalid value for transparent arg'
				self._transparent = -1
			else: self._transparent=transparent

		self._convert_color = parent._convert_color

		### Create the real OS window
		if type_channel==HTM:self.CreateHtmlWnd()
		else:self.CreatePlainWindow()		
		
		# rearange subwindows in the correct relative z-position
		self.z_order_subwindows()
			
		# do not enter WM_PAINT since we have provided the virtual OnPaint
		# that will be automatically called by the framework
		self._msg_cbs= {
			win32con.WM_RBUTTONDOWN:self.onRButtonDown,
			win32con.WM_LBUTTONDBLCLK:self.onLButtonDblClk,
			win32con.WM_LBUTTONDOWN:self.onLButtonDown,
			win32con.WM_LBUTTONUP:self.onLButtonUp,
			win32con.WM_MOUSEMOVE:self.onMouseMove,
			win32con.WM_SIZE:self.onSize,}
		self._enable_response(self._msg_cbs)
		self.show()

	# Called by the core system to create a child window to the subwindow
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z, units)

	# Called by the core system to create a child window to the subwindow
	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		return _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z, units)
	
	# Report string for this class
	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)

	# Sets the title of the subwindow (internal use)
	def settitle(self, title):
		self._title=title

	# Arrange siblings subwindows in their correct z-order
	def z_order_subwindows(self):
		# rearange subwindows in the correct relative z-order
		parent=self._parent
		flags=win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOACTIVATE|win32con.SWP_ASYNCWINDOWPOS		
		n=len(parent._subwindows)
		for i in range(1,n):
			parent._subwindows[i].SetWindowPos(parent._subwindows[i-1].GetSafeHwnd(), 
				(0,0,0,0),flags)
	
	# Bring the subwindow infront of windows with the same z	
	def pop(self):
		self._topwindow.activate()
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
		# rearange subwindows in the correct relative z-position
		self.z_order_subwindows()

	# Send the subwindow back of the windows with the same z	
	def push(self):
		parent = self._parent
		# put self behind all siblings with equal or higher z
		if self is parent._subwindows[-1]:
			# already at the end
			return
		if self not in parent._subwindows:return
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)-1,-1,-1):
			if self._z <= parent._subwindows[i]._z:
				parent._subwindows.insert(i+1, self)
				break
		else:
			parent._subwindows.insert(0, self)
		
		# rearange subwindows in the correct relative z-position
		self.z_order_subwindows()

	# return the coordinates of this subwindow
	def getgeometry(self, units = UNIT_SCREEN):
		import __main__
		toplevel=__main__.toplevel
		if units == UNIT_PXL:
			return self._rectb
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
	
	def isclient(self):
		if self._sizes[0]==0.0 and self._sizes[1]==0.0 and\
			self._sizes[2]==1.0 and self._sizes[3]==1.0 and\
			self._parent==self._topwindow:
			return 1
		else:return 0

	# Called by the framework (OS) when it decided that part of the subwindow needs to be painted	
	# paint the ws visible part (not covered by ws with higher z-order)
	# during BeginPaint the OnEraseBkgnd will be called
	# to prepare self ws visible background
	def OnPaint(self):
		dc, paintStruct = self._obj_.BeginPaint()
		self.PaintOn(dc)
		self._obj_.EndPaint(paintStruct)
	
	# Part of the paint sequence but separated in order to implement an update mechanism for the transparent windows
	# called from self.OnPaint method and for transparent ws 
	# also from <wnd with higher z-order that ovelaps self>.OnEraseBkgnd
	def PaintOn(self,dc):
		if self.in_create_box_mode() and self.get_box_modal_wnd()==self:
			self.notifyListener('OnDraw',dc)
			return
		rc=dc.GetClipBox()
		if self._redrawfunc:
			self._redrawfunc()
		elif self._active_displist:
			self._active_displist._render(dc,rc)
		if self._showing: # i.e. we must draw a frame around as
			self.showwindow_on(dc)
	
	# Called by the framework (OS) to erase the background of this subwindow.
	# Part of our mechanism for correctly updatinh overlapping transparent windows					
	# returns 1 to indicate 'done'	
	def OnEraseBkgnd(self,dc):
		
		# while in create box mode special handling
		if self.in_create_box_mode() and self.get_box_modal_wnd()==self:
			return

		# do not erase bkgnd for video channel when active
		if self._active_displist and (self._window_type==MPEG or self._window_type==HTM): 
			return 1

		# default is:
		# if self._transparent==0:return self._obj_.OnEraseBkgnd(dc)
		rc=dc.GetClipBox()
		if self._transparent==0:
			if self._active_displist:color=self._active_displist._bgcolor
			else: color=self._bgcolor
			dc.FillSolidRect(rc,win32mu.RGB(color))
			return 1
		if self._transparent==-1 and self._active_displist:
			dc.FillSolidRect(rc,win32mu.RGB(self._active_displist._bgcolor))
			return 1

		# if we are transparent without an active displist we are actualy out of the game
		if self._transparent in (1,-1) and not self._active_displist:
			return 1
		
		# the window is transparent 
		# we must draw everything in client rect that self is responsible
		# i.e client area not covered by a window with higher z

		# first draw everything with lower or equal z-order
		# use parent to erase background
#		parent = self.GetParent()
#		ptList=[(0,0),]
#		ptOffset = self.MapWindowPoints(parent,ptList)[0]
#		ptOldOrg=dc.OffsetWindowOrg(ptOffset)
#		parent.SendMessage(win32con.WM_ERASEBKGND,dc.GetSafeHdc())
#		dc.SetWindowOrg(ptOldOrg)

		p=self._parent;ws=p._subwindows;n=len(ws)
		ix=ws.index(self)
		for i in range(n-1,ix,-1):
			if ws[i]._transparent in (1,-1) and ws[i]._active_displist==None:
				# they are os transparent, so ignore them
				continue
			rc_self=self.MapCoordTo(rc,ws[i])
			rc_other= ws[i].GetClientRect() 
			rc_common,ans= Sdk.IntersectRect(rc_self,rc_other)
			if ans: # they ovelap
				ptList=[(0,0),]
				ptOffset = self.MapWindowPoints(ws[i],ptList)[0]
				ptOldOrg=dc.OffsetWindowOrg(ptOffset)
				ws[i].PaintOn(dc)
				dc.SetWindowOrg(ptOldOrg)
		return 1
	

	# Helper function to create the OS window
	def CreatePlainWindow(self):
		x,y,w,h=self._rectb
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		self._icon=0
		self._clstyle=win32con.CS_DBLCLKS
		self._style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS
		self._exstyle = 0 
		if self._transparent in (-1,1):
			self._exstyle=win32con.WS_EX_TRANSPARENT
		self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		self.CreateWindowEx(self._exstyle,self._strclass,self._title,self._style,
			(x,y,x+w,y+h),self._parent,0)
		
	# Helper function to create a window capable to host an Html control
	# Part of WebBrowsing support
	def CreateHtmlWnd(self):
		x,y,w,h=self._rectb
		if hasattr(self,'_obj_') and self.IsWindow():
			(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
				self.GetWindowPlacement()
			l,t,r,b=rcNormalPosition
			x,y,w,h=l,t,r-l,b-t
			self.DestroyWindow()
		window.Wnd.__init__(self,win32ui.CreateHtmlWnd())
		self._brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		self._icon=0
		self._clstyle=win32con.CS_DBLCLKS
		self._style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS
		self._exstyle = 0 
		self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		x,y,w,h=self._rectb
		self.CreateWindow(self._strclass,self._title,self._style,
			(x,y,x+w,y+h),self._parent,0)
		if self._transparent in (-1,1):
			self.setWndTransparent()
		if self.isclient():self.SetClient(1)
		import settings
		self.UseHtmlCtrl(not settings.get('html_control'))

	# Called by the Html channel. The request is delegated to the Html control
	# Part of WebBrowsing support
	def RetrieveUrl(self,fileOrUrl):	
		if not hasattr(self,'Navigate'):
			self.CreateHtmlWnd()
			self.show()
			self._enable_response(self._msg_cbs)
		self.HookMessage(self.onUserUrl,win32con.WM_USER)
		self.Navigate(fileOrUrl)

	# Called by the Html channel to set the callback to be called on cmif links
	# Part of WebBrowsing support
	def setanchorcallback(self,cb):
		self._anchorcallback=cb

	# Called by the HtmlWnd when a cmif anchor has fired. It is a callback but implemented
	# using the std windows message mechanism
	# Part of WebBrowsing support
	def onUserUrl(self,params):
		url=self.GetForeignUrl()
		if hasattr(self,'_anchorcallback') and self._anchorcallback:
			self._anchorcallback(url)

	
	###########################################
	# Dispatch mouse events group of functions
	# Later they will be unified with the respective functions in cmifwnd.py			
	
	# Response to left button down
	def onLButtonDown(self, params):
		if self.in_create_box_mode():
			self.notifyListener('onLButtonDown',params)
			return
		msg=win32mu.Win32Msg(params)
		point=msg.pos()
		self.dispatchMouseEvent(point,Mouse0Press)

	# Response to left button up
	def onLButtonUp(self, params):
		if self.in_create_box_mode():
			self.notifyListener('onLButtonUp',params)
			return
		msg=win32mu.Win32Msg(params)
		point=msg.pos()
		self.dispatchMouseEvent(point,Mouse0Release)

	# Dispatch mouse events
	def dispatchMouseEvent(self,point,ev):
		ws=self._parent._subwindows;n=len(ws);ix=ws.index(self)
		rc=self.GetClientRect()
		for i in range(0,n):
			if ws[i]._transparent in (1,-1) and ws[i]._active_displist==None:
				continue
			if not ws[i]._active_displist:
				continue
			rc_self=self.MapCoordTo(rc,ws[i])
			rc_other= ws[i].GetClientRect() 
			rc_common,ans= Sdk.IntersectRect(rc_self,rc_other)
			if ans: # they ovelap
				ptList=[point,]
				wspt = self.MapWindowPoints(ws[i],ptList)[0]
				if ws[i].inside(wspt):
					if ws[i].onMouseEvent(wspt,ev):return 1
		else: return 0


	def onMouseMove(self, params):
		if self.in_create_box_mode():
			self.notifyListener('onMouseMove',params)
			return
		msg=win32mu.Win32Msg(params)
		point=msg.pos()

		p=self._parent;ws=p._subwindows;n=len(ws)
		ix=ws.index(self)
		rc=self.GetClientRect()
		f=0
		for i in range(0,n):
			if ws[i]._transparent in (1,-1) and ws[i]._active_displist==None:
				continue
			if not ws[i]._active_displist:
				continue
			rc_self=self.MapCoordTo(rc,ws[i])
			rc_other= ws[i].GetClientRect() 
			rc_common,ans= Sdk.IntersectRect(rc_self,rc_other)
			if ans: # they ovelap
				ptList=[point,]
				ptOffset = self.MapWindowPoints(ws[i],ptList)[0]
				if ws[i].inside(ptOffset):
					f=ws[i].setcursor_from_point(ptOffset,self)
				if f: break
		if not f:self.setcursor('arrow')
			

	# RM support
	def OnCreate(self,params):
		self._rect=self.GetClientRect()
		self._can_change_size=0

	def onSize(self,params):
		if self._can_change_size: return
		msg=win32mu.Win32Msg(params)
		l,t,r,b=self._rect
		self.SetWindowPos(self.GetSafeHwnd(),(0,0,r,b),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | win32con.SWP_NOMOVE)

	def AllowResize(self,f):
		self._can_change_size=f
