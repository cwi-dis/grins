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
import usercmd,usercmdui
import sysmetrics


###########################################################
# import window core stuff
from pywin.mfc import window,object,docview,dialog
import afxres,commctrl
import cmifwnd	
import afxexttb # part of generated afxext.py

class _CmifView(cmifwnd._CmifWnd,docview.ScrollView):
	def __init__(self,doc):
		cmifwnd._CmifWnd.__init__(self)
		docview.ScrollView.__init__(self,doc)

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
			win32con.WM_EXITSIZEMOVE:self.onExitSizeMove,
			}
		self._enable_response(r)
		
	def createWindow(self,parent):
		self.CreateWindow(parent)
		self._commandlist=None

	def OnCreate(self,params):
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(0,0,r-l,b-t)
		self.SetScrollSizes(win32con.MM_TEXT,(r-l,b-t))
		self.ResizeParentToFit()
	
	def OnClose(self):
		if self._closecmdid>0:
			self.GetParent().GetMDIFrame().PostMessage(win32con.WM_COMMAND,self._closecmdid)
		else:
			self.GetParent().DestroyWindow()
				
	def PreCreateWindow(self, csd):
		csd=self._obj_.PreCreateWindow(csd)
		cs=win32mu.CreateStruct(csd)
		# if WS_CLIPCHILDREN is set we must
		# redraw the background of transparent children 
		#cs.style=cs.style|win32con.WS_CLIPCHILDREN
		return cs.to_csd()
							
	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		if not self._canscroll:
			self._do_resize(msg.width(),msg.height())
		# after _do_resize because it uses old self._rect
		self._rect=0,0,msg.width(),msg.height()

	def onExitSizeMove(self,params):
		print 'onExitSizeMove'
#		if not self._canscroll and self._prevrect:
#			l,t,w,h=self._prevrect
#			self._do_resize(w,h)
#		self._rect=self._prevrect
		
	def _scroll(self,how):
		if self._canscroll==0: return
		w,h=self._canvas[2:]
		self.SetScrollSizes(win32con.MM_TEXT,(w,h))
		if how==RESET_CANVAS or FIT_WINDOW:
			self.ResizeParentToFit()
		self.InvalidateRect()
			
	# convert from client (device) coordinates to canvas (logical)
	def _DPtoLP(self,pt):
		dc=self.GetDC()
		# PyCView.GetDC has called OnPrepareDC(dc)
		pt=dc.DPtoLP(pt)
		self.ReleaseDC(dc)
		return pt

	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)	

	# delegate to parent for cmds and adorment functionality
	def set_dynamiclist(self, cmd, list):
		self._parent.set_dynamiclist(cmd,list)
	def set_adornments(self, adornments):
		self._parent.set_adornments(adornments)
	def set_toggle(self, command, onoff):
		self._parent.set_toggle(command,onoff)
		
	def set_commandlist(self, list):
		self._commandlist=list
		self._parent.set_commandlist(list,self._strid)
	def settitle(self,title):
		self._title=title
		#self._parent.settitle(title,'view')

	def onActivate(self,f):
		pass

	# recycling of views
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
	

	def setScrollMode(self,f):
		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(l,t,r-l,b-t)
		self._canscroll=f
		if f:
			self.SetScrollSizes(win32con.MM_TEXT,(self._canvas[2],self._canvas[3]))
		else:
			self.SetScaleToFitSize((r-l,b-t))
			self.ResizeParentToFit()
		
	# called directly from cmif-core
	# to close window
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

	def is_closed(self):
		return not self._obj_ or not self.IsWindow()

	def pop(self):
		self._parent.ActivateFrame()
		self.InvalidateRect()
	def push(self):
		pass


	def OnDraw(self,dc):
		self.PaintOn(dc)

	# separate from OnDraw because can be 
	# called with different dc that is possible from the OnDraw
	# due to clipping mechanism. The OnDraw is called by ws std mechanism
	def PaintOn(self,dc):
		if self.in_create_box_mode():
			self.notifyListener('OnDraw',dc)
			return
		rc=dc.GetClipBox()
		if self._active_displist:
			self._active_displist._render(dc,rc,1)
		if self._showing: # i.e. we must draw a frame around as
			self.showwindow_on(dc)

	# return 1 to indicate 'done'
	# overwrites  DrawLayer		
	def OnEraseBkgnd(self,dc):
		# default is:
		# if self._transparent==0:return self._obj_.OnEraseBkgnd(dc)
		if self.in_create_box_mode():
			return
		rc=dc.GetClipBox()
		if self._active_displist:color=self._active_displist._bgcolor
		else: color=self._bgcolor
		dc.FillSolidRect(rc,win32mu.RGB(color))
		return 1
		


class _SubWindow(cmifwnd._CmifWnd,window.Wnd):
	def __init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z=0):
		cmifwnd._CmifWnd.__init__(self)
		self._do_init(parent)

		self._window_type = type_channel
		self._topwindow = parent._topwindow
		self._z = z

		self._sizes = rel_coordinates
		x, y, w, h = rel_coordinates
		if not x or x<0:x=0
		if not y or w<0:y=0
		if not w:w=100
		if not h:h=100
		rel_coordinates=x, y, w, h

		x, y,w,h = parent._convert_coordinates(rel_coordinates)
		self._rect = 0, 0, w, h
		self._canvas = 0, 0, w, h
		self._rectb = x, y, w, h

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
			win32con.WM_MOUSEMOVE:self.onMouseMove,}
		self._enable_response(self._msg_cbs)
		self.show()


	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		return _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)

	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)

	def settitle(self, title):
		self._title=title

	def z_order_subwindows(self):
		# rearange subwindows in the correct relative z-order
		parent=self._parent
		flags=win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOACTIVATE|win32con.SWP_ASYNCWINDOWPOS		
		n=len(parent._subwindows)
		for i in range(1,n):
			parent._subwindows[i].SetWindowPos(parent._subwindows[i-1].GetSafeHwnd(), 
				(0,0,0,0),flags)
		#self.InvalidateParentRect()
		
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
		# rearange subwindows in the correct relative z-position
		self.z_order_subwindows()

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

	def getgeometry(self, units=UNIT_MM):
		return self._sizes
		
	# paint the ws visible part (not covered by ws with higher z-order)
	# during BeginPaint the OnEraseBkgnd will be called
	# to prepare self ws visible background
	def OnPaint(self):
		dc, paintStruct = self._obj_.BeginPaint()
		self.PaintOn(dc)
		self._obj_.EndPaint(paintStruct)
	
	# called from self.OnPaint method and for transparent ws 
	# also from <wnd with higher z-order that ovelaps self>.OnEraseBkgnd
	def PaintOn(self,dc):
		if self.in_create_box_mode():
			self.notifyListener('OnDraw',dc)
			return
		rc=dc.GetClipBox()
		if self._active_displist:
			self._active_displist._render(dc,rc,1)
		if self._showing: # i.e. we must draw a frame around as
			self.showwindow_on(dc)
						
	# return 1 to indicate 'done'	
	def OnEraseBkgnd(self,dc):

		# do not erase bkgnd for video channel when active
		if self._window_type==MPEG: # and self._active_displist:
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
	
	def MapCoordTo(self,rc,wnd):
		l,t,r,b=rc
		ptList=[(l,t),(r,b)]
		[(l,t),(r,b)] = self.MapWindowPoints(wnd,ptList)
		return (l,t,r,b)

	def CreatePlainWindow(self):
		x,y,w,h=self._rectb
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._brush=Sdk.CreateBrush(win32con.BS_SOLID,win32mu.RGB(self._bgcolor),0)
		self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
		self._icon=0
		self._clstyle=win32con.CS_DBLCLKS
		self._style=win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS
		self._exstyle = 0 
		self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
		self.CreateWindowEx(self._exstyle,self._strclass,self._title,self._style,
			(x,y,x+w,y+h),self._parent,0)
		if self._transparent in (-1,1):
			self.setWndTransparent()	
		
	# WebBrowsing support
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

	def RetrieveUrl(self,fileOrUrl):
		if not hasattr(self,'Navigate'):
			self.CreateHtmlWnd()
			self.show()
			self._enable_response(self._msg_cbs)
		self.HookMessage(self.onUserUrl,win32con.WM_USER)
		self.Navigate(fileOrUrl)

	def setanchorcallback(self,cb):
		self._anchorcallback=cb

	def onUserUrl(self,params):
		url=self.GetForeignUrl()
		if hasattr(self,'_anchorcallback') and self._anchorcallback:
			self._anchorcallback(url)

