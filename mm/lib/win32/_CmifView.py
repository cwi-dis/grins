import win32ui, win32con, win32api
from win32modules import grinsRC
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()
import os

from types import *
from WMEVENTS import *
from appcon import *

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


	def onSizeScale_OLD(self, width,height):
		self.arrowcache = {}
		import rbtk
		w = rbtk._in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			try:
				w._rb_cancel()
			except rbtk._rb_done:
				pass
			w._next_create_box[0:0] = next_create_box
		self._do_resize(width, height)
		if w:
			w._rb_end()
			raise rbtk._rb_done

	def _scroll(self,how):
		if self._canscroll==0: return
		w,h=self._canvas[2:]
		self.SetScrollSizes(win32con.MM_TEXT,(w,h))
		if how==RESET_CANVAS:
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

	def onActivate(self,f):
		if f:
			self._is_active=1
			self.settitle(self._title)
			self.set_commandlist(self._commandlist)
		else:
			if IsEditor:
				# remove view title and 
				# disable view-context commands 
				self.settitle(None)
				self._commandlist=self._parent.get_commandlist('view')
				self.set_commandlist(None)
				self._is_active=0

	# recycling of views
	def init(self,rc,title='View',units= UNIT_MM,adornments=None,canvassize=None,commandlist=None):
		self.settitle(title)
		self.set_commandlist(commandlist)
		self._title=title
		self._commandlist=commandlist
								
		if canvassize==None:self._canscroll=0
		else: self._canscroll=1

		l,t,r,b=self.GetClientRect()
		self._rect=self._canvas=(l,t,r-l,b-t)
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
		# 1. clean self contends
		self._close()

		# 2. destroy OS window if it exists
		if hasattr(self,'_obj_') and self._obj_:
			self.GetParent().DestroyWindow()
		
	def _close(self):
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
		self._is_active=0
		return

	def is_closed(self):
		return self._is_active==0
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
		if self.in_create_box():
			self.notifyListener('OnDraw',dc)
			return
		rc=dc.GetClipBox()
		if self._active_displist:
			self._active_displist._render(dc,rc,1)
		#self.notifyListener('OnDraw',dc)
		#if self._showing: # i.e. we must draw a frame around as
		#	self.showwindow_on(dc)

	# return 1 to indicate 'done'
	# overwrites  DrawLayer		
	def OnEraseBkgnd(self,dc):
		# default is:
		# if self._transparent==0:return self._obj_.OnEraseBkgnd(dc)
		if self.in_create_box():
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
		self._title = 'c%d'%self._num

		
		# insert window in _subwindows list at correct z-order
		for i in range(len(parent._subwindows)):
			if self._z > parent._subwindows[i]._z:
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
		if 1: # self._transparent==0:
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
#		else:
#			# self._transparent is in (1,-1)
#			# wnds with -1 are when empty transparent
#			window.Wnd.__init__(self,win32ui.CreateWnd())
#			self._brush= Sdk.GetStockObject(win32con.NULL_BRUSH)
#			self._cursor=Afx.GetApp().LoadStandardCursor(win32con.IDC_ARROW)
#			self._icon=0
#			self._clstyle=win32con.CS_DBLCLKS
#			self._style=win32con.WS_CHILD 
#			self._exstyle = win32con.WS_EX_TRANSPARENT 
#			self._strclass=Afx.RegisterWndClass(self._clstyle,self._cursor,self._brush,self._icon)
#			self.CreateWindowEx(self._exstyle,self._strclass,self._title,self._style,
#				(x,y,x+w,y+h),self._parent,0)

		self._wnd=self._obj_ # historic alias but useful to markup externals
		self._hWnd=self.GetSafeHwnd()

		
		# rearange subwindows in the correct relative z-position
		self.z_order_subwindows()

			
		# do not enter WM_PAINT since we have provided the virtual OnPaint
		# that will be automatically called by the framework
		rc= {
			win32con.WM_RBUTTONDOWN:self.onRButtonDown,
			win32con.WM_LBUTTONDBLCLK:self.onLButtonDblClk,
			win32con.WM_LBUTTONDOWN:self.onLButtonDown,
			win32con.WM_LBUTTONUP:self.onLButtonUp,
			win32con.WM_MOUSEMOVE:self.onMouseMove,}
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


	def z_order_subwindows(self):
		# rearange subwindows in the correct relative z-order
		if not self._parent._subwindows:return
		parent=self._parent
		flags=win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOACTIVATE|win32con.SWP_ASYNCWINDOWPOS		
		n=len(parent._subwindows)
		for i in range(1,n):
			parent._subwindows[i].SetWindowPos(parent._subwindows[i-1].GetSafeHwnd(), 
				(0,0,0,0),flags)
		self.InvalidateParentRect()
		
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
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)-1,-1,-1):
			if self._z <= parent._subwindows[i]._z:
				parent._subwindows.insert(i+1, self)
				break
		else:
			parent._subwindows.insert(0, self)
		
		# rearange subwindows in the correct relative z-position
		self.z_order_subwindows()

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
		rc=dc.GetClipBox()
		if self._active_displist:
			self._active_displist._render(dc,rc,1)
		if self._showing: # i.e. we must draw a frame around as
			self.showwindow_on(dc)
		self.notifyListener('OnDraw',dc)

	# paint under overlaping transparent siblings with higher z-order
	# * applies to transparent wnds
	# * should not be called by the std wnds paint mechanism
	#   but from our update mechanism only
	# * for the os our windows are all not trasparent so the std wnds paint mechanism
	#   has no access in this area 
	def PaintUnderTrasparentSiblings(self,rc):
		p=self._parent;ws=p._subwindows
		ix=ws.index(self)
		for i in range(0,ix): # all z-higher
			if ws[i]._transparent==1 or (ws[i]._transparent==-1 and ws[i]._active_displist==None):
				# the ws[i] is trasparent
				rc_self=self.MapCoordTo(rc,ws[i])
				rc_other= ws[i].GetClientRect() #ws[i].MapCoordTo(ws[i].GetClientRect(),p)
				rc_common,ans= Sdk.IntersectRect(rc_self,rc_other)
				if ans: # they ovelap
					ws[i].InvalidateRect(rc_common,1) # update common pixel map
		
	def InvalidateParentRect(self):
		l,t,r,b=self.GetClientRect()
		ptList=[(l,t),(r,b)]
		[(l,t),(r,b)] = self.MapWindowPoints(self._parent,ptList)
		self._parent.InvalidateRect((l,t,r,b))
	
	# return 1 to indicate 'done'	
	def OnEraseBkgnd(self,dc):
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
		# self._transparent==1 or (self._transparent==-1 and self._active_displist==None)
		# we must draw everything in client rect that self is responsible
		# i.e client area not covered by a window with higher z

		# first draw everything with lower z-order
		# use parent to erase background
		parent = self.GetParent()
		ptList=[(0,0),]
		ptOffset = self.MapWindowPoints(parent,ptList)[0]
		ptOldOrg=dc.OffsetWindowOrg(ptOffset)
		parent.SendMessage(win32con.WM_ERASEBKGND,dc.GetSafeHdc())
		dc.SetWindowOrg(ptOldOrg)

		p=self._parent;ws=p._subwindows;n=len(ws)
		ix=ws.index(self)
		for i in range(n-1,ix,-1):
			# we should check for overlap before we make we elaborate on
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




###########################################################
###########################################################
###########################################################

class _Window(cmifwnd._CmifWnd,window.Wnd):
	def __init__(self, parent, x, y, w, h, title, defcmap = 0, pixmap = 0,
		     units = UNIT_MM, adornments = None,
		     canvassize = None, commandlist = None, resizable = 1):
		cmifwnd._CmifWnd.__init__(self)
		window.Wnd.__init__(self,win32ui.CreateWnd())
		self._do_init(parent)
		parent._subwindows.insert(0, self)

		self._title = title		
		self._topwindow = self
		self._window_type = SINGLE
		self._depth = sysmetrics.depth

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
			win32con.WM_MOUSEMOVE:self.onMouseMove,}
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
		self.notifyListener('OnDraw',dc)
		self._obj_.EndPaint(paintStruct)

	def onSize(self, params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		width,height=msg.width(), msg.height()
		self.arrowcache = {}

		# take into account create box mode
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


	################ TO BE IMPLEMENTED (NEEDED?)
	def set_dynamiclist(self, cmd, list):
		print '_Window.set_dynamiclist',cmd, list


	def set_adornments(self, adornments):
		print "_Window.set_adornments",adornments

	def set_commandlist(self, list):
		print "_Window.set_commandlist",list

	def set_toggle(self, command, onoff):
		print "_Window.set_toggle",command, onoff
		
