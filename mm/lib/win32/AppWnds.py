__version__ = "$Id$"

# the application uses the objects defined here
# to create channel wnds and document views (Channel,Hierarchy)
# using newwindow and newcmwindow

# Public Objects
# class _Window,_FrameWnd

# Private Objects
# class _SubWindow(_Window):

# note:
# instances of _Window are created by windowinterface.newwindow(...) and windowinterface.newcmwindow(...)
# instances of _SubWindow are created indirectly by (windowinterface.newwindow(...)).newwindow(...) 
# and (windowinterface.newwindow(...)).newcmwindow(...)


import win32ui, win32con, win32api 
from win32modules import imageex, cmifex2, grinsRC
Afx=win32ui.GetAfx()
Sdk=win32ui.GetWin32Sdk()

from types import *
from WMEVENTS import *
from appcon import *
from sysmetrics import *

from DisplayList import DisplayList

import win32mu,AppMenu


toplevel=None # set by AppTopLevel

from rbtk import _rbtk,_rb_done,_in_create_box,_rb_message

# text copy from X_window.. 
# class _Window(window.Wnd):
	# Instances of this class represent top-level windows.  This
	# class is also used as base class for subwindows, but then
	# some of the methods are overridden.
	#
	# The following instance variables are used.  Unless otherwise
	# noted, the variables are used both in top-level windows and
	# subwindows.
	# _shell: the Xt.ApplicationShell widget used for the window
	#	(top-level windows only)
	# _form: the Xm.DrawingArea widget used for the window
	# _scrwin: the Xm.ScrolledWindow widget used for scrolling the canvas
	# _clipcanvas: the Xm.DrawingArea widget used by the Xm.ScrolledWindow
	# _colormap: the colormap used by the window (top-level
	#	windows only)
	# _visual: the visual used by the window (top-level windows
	#	only)
	# _depth: the depth of the window in pixels (top-level windows
	#	only)
	# _pixmap: if present, the backing store pixmap for the window
	# _gc: the graphics context with which the window (or pixmap)
	#	is drawn
	# _title: the title of the window (top-level window only)
	# _topwindow: the top-level window
	# _subwindows: a list of subwindows.  This list is also the
	#	stacking order of the subwindows (top-most first).
	#	This list is manipulated by the subwindow.
	# _parent: the parent window (for top-level windows, this
	#	refers to the instance of _Toplevel).
	# _displists: a list of _DisplayList instances
	# _active_displist: the currently rendered _displayList
	#	instance or None
	# _bgcolor: background color of the window
	# _fgcolor: foreground color of the window
	# _transparent: 1 if window has a transparent background (if a
	#	window is transparent, all its subwindows should also
	#	be transparent) -1 if window should be transparent if
	#	there is no active display list
	# _sizes: the position and size of the window in fractions of
	#	the parent window (subwindows only)
	# _rect: the position and size of the window in pixels
	# _region: _rect as an X Region
	# _clip: an X Region representing the visible area of the
	#	window
	# _hfactor: horizontal multiplication factor to convert pixels
	#	to relative sizes
	# _vfactor: vertical multipliction factor to convert pixels to
	#	relative sizes
	# _cursor: the desired cursor shape (only has effect for
	#	top-level windows)
	# _callbacks: a dictionary with callback functions and
	#	arguments
	# _accelerators: a dictionary of accelarators
	# _menu: the pop-up menu for the window
	# _showing: 1 if a box is shown to indicate the size of the
	#	window
	# _exp_reg: a region in which the exposed area is built up
	#	(top-level window only)

# kk: ADD

# Default units for top level windows _Window is mm (UNIT_MM)
# The _SubWindow coords are relative coordinates wrt its parent (UNIT_PARENT)


# To convert relative coord to pixel f subwindows  relative to
# the upper-left corner of the parent window call:
# parent._convert_coordinates(coord)
# these coordinates are cashed in _rect member
# To convert from pixels back to relative sizes call
# use _inverse_coordinates(self, point)


# definition of symbols as used here
# _rect (GetClientRect)
#	pos and dim of the the client area of the window in pixels with origin its parent left-top corner
#	Changes on resize	
# _canvas 
#	drawing rect (pos and dim) in pixels with origin the top-left corner of the window 
#	(if not scrollable it is usually the client rect)
#	This is the rect that display lists are rendered
#	Changes on resize	
# _sizes: 
#	original pos and dim of the window in relative coordinates with respect to its parent 
#	with origin the parent left-top corner
# _rectb 
#   same as _sizes at creation but in pixel coord
#	pos and dim of the the window in pixels with origin its parent left-top corner
#	For top level windows includes borders, caption, etc
#	Changes on resize	

# NOTE: all rects are tuples containing: (left,top,width,height)
#		for the top-level window the parent is the desktop window with _rect=(0,0,scr_width_pxl,scr_height_pxl)
#		external convention: if canvassize==None: _canscroll = 0
#		for subwindows _rectb==_rect==_canvas
#		the only rect that remains unchanged is _sizes
# WARN: in win32 the name rect is used for the tuple (left,top,right,bottom) 
#
 
###########################################################
# import window core stuff
from pywin.mfc import window,object,docview,dialog
import cmifwnd	
###########################################################
###########################################################
###########################################################
class _Window(cmifwnd._CmifWnd,_rbtk,window.Wnd):
	def __init__(self,parent,x, y, w, h, title, 
				visible_channel = TRUE,
				type_channel = SINGLE, pixmap = 1, units = UNIT_MM,
				menubar = None, canvassize = None):
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

		self._menu = None
		if menubar is not None:
			self.create_menu(menubar)

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


###########################################################
###########################################################
###########################################################
class _CmifView(docview.View):
	def __init__(self,frame):
		d=docview.Document(docview.DocTemplate())
		v=win32ui.CreateView(d)
		docview.View.__init__(self,v)
		self.CreateWindow(frame)
		self._frame=frame

	def OnDraw(self,dc):
		rc=dc.GetClipBox()
		if self._frame._active_displist:
			self._frame._active_displist._render(dc,rc,1)

##########
class _CmifScrollView(docview.ScrollView):
	def __init__(self,frame):
		d=docview.Document(docview.DocTemplate())
		docview.ScrollView.__init__(self,d)
		self.CreateWindow(frame)
		self._frame=frame
		
	def OnDraw(self,dc):
		rc=dc.GetClipBox()
		if self._frame._active_displist:
			self._frame._active_displist._render(dc,rc,1)


##########
class _WindowFrm(cmifwnd._CmifWnd,_rbtk,window.FrameWnd):
	def __init__(self,parent,x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 1, units = UNIT_MM,
		      menubar = None, canvassize = None):
		cmifwnd._CmifWnd.__init__(self,parent)
		_rbtk.__init__(self)
		window.FrameWnd.__init__(self,win32ui.CreateFrame())
		self._view=None
		if canvassize: self._canscroll = 1
		self._title = title		
		self._topwindow = self
		self._window_type = type_channel
		self._sizes = 0, 0, 1, 1
		parent._subwindows.insert(0, self)
		if not x:x=0
		if not y:y=0
		xp,yp,wp,hp = to_pixels(x,y,w,h,units)
		self._rectb= xp,yp,wp,hp
		self._sizes = (float(xp)/scr_width_pxl,float(yp)/scr_height_pxl,float(wp)/scr_width_pxl,float(hp)/scr_height_pxl)
		
		self._depth = toplevel.getscreendepth()

		canvas_is_client_rect=0
		if canvassize and canvassize[0]==w and canvassize[1]==h:
			canvas_is_client_rect=1
		self.setcursor('watch')
		

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
		self._wnd=self._obj_ # historic alias but useful to markup externals
		self._hWnd=self.GetSafeHwnd()

		# create apropriate views
		if canvassize:self._view=_CmifScrollView(self)
		else:self._view=_CmifView(self)
		self.RecalcLayout()

		if canvassize:
			if self._view and canvas_is_client_rect:
				l,t,r,b=self._view.GetClientRect()
				wc,hc=r-l,b-t
				self._view.SetScrollSizes(win32con.MM_TEXT,(wc,hc))
				self._view.ResizeParentToFit(); 
				self._canvas_reset=self._canvas=(0,0,wc,hc)  
			else:
				wc,hc=size2pix(canvassize,units)
				self._view.SetScrollSizes(win32con.MM_TEXT,(wc,hc))	
				self._canvas_reset=self._canvas=(0,0,wc,hc)
		l,t,r,b=self._view.GetClientRect()
		self._rect=(l,t,r-l,b-t)

		# delegate user input to view
		r= {
			win32con.WM_RBUTTONDOWN:self.onRButtonDown,
			win32con.WM_LBUTTONDBLCLK:self.onLButtonDblClk,
			win32con.WM_LBUTTONDOWN:self.onLButtonDown,
			win32con.WM_LBUTTONUP:self.onLButtonUp,
			win32con.WM_MOUSEMOVE:self.onMouseMove,
			
			}
		self._enable_response(r,self._view)

		# but do not delegate Close
		r= {
			win32con.WM_CLOSE:self.onClose,
			win32con.WM_SIZE:self.onSize,
			}
		self._enable_response(r)

		self._menu = None
		if menubar is not None:
			self.create_menu(menubar)

		if visible_channel:
			self.RecalcLayout()
			self.ShowWindow(win32con.SW_SHOW)
		for id in range(0,100):
			self.EnableCmdX(id)
	
	# for now just enable all commands
	def EnableCmdX(self,id):
		self.HookCommandUpdate(self.OnUpdateCmdX,id)
	def OnUpdateCmdX(self,cmdui):
		cmdui.Enable()

	def _scroll(self):
		w,h=self._canvas[2:]
		w0,h0=self._canvas_reset[2:] 
		self._view.SetScrollSizes(win32con.MM_TEXT,(w,h))
		if w==w0 and h==h0:self._view.ResizeParentToFit();

	# convert from client (device) coordinates to canvas (logical)
	def _DPtoLP(self,pt):
		dc=self._view.GetDC()
		# python view.GetDC has called OnPrepareDC(dc)
		pt=dc.DPtoLP(pt)
		self._view.ReleaseDC(dc)
		return pt
		
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		win= _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		return win

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)
		return win

	def onSize(self,params):
		msg=win32mu.Win32Msg(params)
		if msg.minimized(): return
		self._rect=msg.width(),msg.height()


###########################################################
###########################################################
###########################################################
class _SubWindow(cmifwnd._CmifWnd,window.Wnd):
	def __init__(self, parent, rel_coordinates, transparent, type_channel, defcmap, pixmap, z=0):

		cmifwnd._CmifWnd.__init__(self,parent)
		self._window_type = type_channel
		self._next_create_box = []
		self._topwindow = parent._topwindow

		if z < 0:
			raise error, 'invalid z argument'
		self._z = z
		self._align = ' '

		x, y, w, h = rel_coordinates
		if not x:x=0
		if not y:y=0
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

