__version__ = "$Id$"

""" @win32doc|cmifwnd
The _CmifWnd class is a mixin class providing
to concrete classes that inherit from it
a standard interface required by most of the application's 
windows. These windows include the Chierarchy view 
the Timeline view, the Player view and the window channels.

main facilities offered by this class:
parent-child management
popup menu
events registration
response to mouse events
image preparation
resizing iteration
cursor setting
conversion from/to relative to parent coordinates
"""

# gen lib
import math
from types import *

# lib
import win32ui, win32con, win32api 
Sdk = win32ui.GetWin32Sdk()

# utilities
import win32mu,win32menu

# constants
from appcon import *
from WMEVENTS import *
from win32ig import win32ig
import grinsRC

# commands for popups
import usercmd,usercmdui

# globals 
import __main__

import  rbtk
import DrawTk
from DisplayList import DisplayList

class _CmifWnd(rbtk._rbtk,DrawTk.DrawLayer):
	def __init__(self):
		rbtk._rbtk.__init__(self)
		DrawTk.DrawLayer.__init__(self)
		self._subwindows = []
		self._displists = []
		self._active_displist = None
		self._curcursor = ''
		self._curpos = None
		self._callbacks = {}
		self._accelerators = {}
		self._menu = None		# Dynamically created rightmousemenu
		self._popupmenu = None	# Statically created rightmousemenu (for views)
		self._transparent = 0
		self._redrawfunc = None
		self._title = None
		self._topwindow = None
		self.arrowcache = {}
		self._old_callbacks = {}
		self._cbld = {}
		self._align = ' '		
		self._scale = 0.0
		self._region = None
		self._window_type = SINGLE
		self._resize_flag = 0
		self._render_flag = 0		
		self._sizes = None
		self._canvas=None
		self._canscroll = 0

		self._parent = None
		self._bgcolor = __main__.toplevel._bgcolor
		self._fgcolor = __main__.toplevel._fgcolor
		self._cursor = ''

		# frame wnd indicator if not None
		# contains the color of the frame
		self._showing = None

		# default z-order
		self._z=0

		# temp sigs
		self._wnd = None
		self._hWnd = 0

	# part of the constructor initialization
	def _do_init(self,parent):
		self._parent = parent
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor

	# Called by the core system to create a subwindow
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		raise error, 'override newwindow'
		return None

	# Called by the core system to create a subwindow
	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE, units = None):
		raise error, 'override newcmwindow'
		return None
		
	# Called by the core system to craete a new display list
	def newdisplaylist(self, *bgcolor):
		if bgcolor != ():
			bgcolor = bgcolor[0]
		else:
			bgcolor = self._bgcolor
		return  DisplayList(self, bgcolor)

	# Sets the window title
	def settitle(self, title):
		if self._obj_ != None:
			if self._title != title:
				self._title = title
				self.SetWindowText(title)	

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
	
	# Returns true if this a top window
	def is_topwindow(self):
		return self._topwindow == self

	# Response to channel highlight
	def showwindow(self,color=(255,0,0)):
		self._showing = color
		dc=self.GetDC()
		if self._topwindow != self: 
			win32mu.FrameRect(dc,self.GetClientRect(),self._showing)
#		if self._topwindow != self:
#			self._display_info(dc)
		self.ReleaseDC(dc)

	# Highlight the window
	def showwindow_on(self,dc):
		if self._topwindow != self: 
			win32mu.FrameRect(dc,self.GetClientRect(),self._showing)
		if self._topwindow != self and self._active_displist==None:
			self._display_info(dc)

	# Highlight the window using ext DC
	def showwindowEx(self):
		rgn=win32ui.CreateRgn()
		rgn.CreateRectRgn(self.GetClientRect())
		dcx=self.GetDCEx(rgn,win32con.DCX_CACHE|win32con.DCX_CLIPSIBLINGS)
		win32mu.FrameRect(dcx,self.GetClientRect(),self._showing)
		if self._topwindow != self:		
			self._display_info(dcx)
		self.ReleaseDC(dcx)
		rgn.DeleteObject()
		del rgn

	# Response to channel unhighlight
	def dontshowwindow(self):
		self.showwindow(self._bgcolor)
		self._showing=None
		self.update()

	# Return true if this window highlighted
	def is_showing(self):
		return self._showing
	
	# Highlight/unhighlight all channels
	def showall(self,f):
		if f: self.showwindow()
		else: self.dontshowwindow()
		w=self.GetWindow(win32con.GW_CHILD)
		while w!=None:
			if not hasattr(w,'showwindow'):break
			if f: w.showwindow()
			else: w.dontshowwindow()
			w=w.GetWindow(win32con.GW_HWNDNEXT)	

	def WndsHierarchy(self):
		print self._title
		w=self.GetWindow(win32con.GW_CHILD)
		while w:
			print '\t',w._title,'t=',w._transparent,'wt=',w.isWndTransparent(),w._active_displist
			w=w.GetWindow(win32con.GW_HWNDNEXT)	

	# Helper function to display window info
	def _display_info(self,dc):
		if self._active_displist: return
		rc=win32mu.Rect(self.GetClientRect())	
		DrawTk.drawTk.SetSmallFont(dc)
		if self._showing:
			old=dc.SetTextColor(win32mu.RGB(self._showing))
		if hasattr(self,'_z'):
			s = '%s (z=%d)'%(self._title,self._z)
		else:
			s = self._title
		rc.inflateRect(-2,-2)
		dc.SetBkMode(win32con.TRANSPARENT)
		dc.DrawText(s,rc.tuple(),win32con.DT_SINGLELINE|win32con.DT_TOP|win32con.DT_CENTER)
		if self._showing:
			old=dc.SetTextColor(old)
		DrawTk.drawTk.RestoreFont(dc)

	def dump_active_displist(self):
		print 'active_displist:',self._active_displist
		for d in self._displists:
			print 'displist:',d
		self.update()

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

	# Called by the core to close the window
	def close(self):
		if self._parent is None:
			return		# already closed

		self.setcursor('arrow')
		for dl in self._displists[:]:
			dl.close()
		for win in self._subwindows[:]:
			win.close()

		if self._obj_ and self.IsWindow():
			rc=self.GetClientRect()
			l,t,r,b=rc
			ptList=[(l,t),(r,b)]
			[(l,t),(r,b)] = self.MapWindowPoints(self._topwindow,ptList)
			self.destroy_menu()
			self._destroy_popupmenu()
			self.DestroyWindow()
			self._topwindow.InvalidateRect((l,t,r,b))

		self._parent._subwindows.remove(self)
		self._parent = None
		del self._topwindow
		del self.arrowcache
		self._obj_ = None

	# Return true if this window is closed
	def is_closed(self):
		return self._parent is None

	# Bring window in front of sibling with equal z
	def pop(self):
		print 'override pop for',self

	# Bring window back of siblings with equal z
	def push(self):
		print 'override push for',self

	# Set the function that takes the painting responsiblities 
	def setredrawfunc(self, func):
		if func is None or callable(func):
			self._redrawfunc = func
		else:
			raise error, 'invalid function'

	# Sets this window to OS transparent
	def setWndTransparent(self):
		#print 'setWndTransparent for',self._title
		style = self.GetWindowLong(win32con.GWL_EXSTYLE)
		style = style | win32con.WS_EX_TRANSPARENT;
		self.SetWindowLong(win32con.GWL_EXSTYLE,style)
	# Sets this window to OS not transparent
	def setWndNotTransparent(self):
		#print 'setWndNotTransparent for',self._title
		style = self.GetWindowLong(win32con.GWL_EXSTYLE)
		style = style & ~win32con.WS_EX_TRANSPARENT;
		self.SetWindowLong(win32con.GWL_EXSTYLE,style)
	# Return true if this window is OS transparent
	def isWndTransparent(self):
		style = self.GetWindowLong(win32con.GWL_EXSTYLE)
		return (style & win32con.WS_EX_TRANSPARENT)!=0
	# Return true if is transparent without active display list
	def isNull(self):
		return (self._transparent in (-1,1) and self._active_displist==None)

	# Destroy popup menu
	def destroy_menu(self):
		if self._menu:
			self._menu.DestroyMenu()
			del self._menu 
		self._menu = None
		self._accelerators = {}

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

	# Create the popup menu from the argument list
	# cb_entry: (ACCELERATOR,NAME,callback_tuple) | None
	# callback_tuple: (callback,(arg,))
	# arg list is a list of cb_entry
	def create_menu(self, list, title = None):
		self._title=title #+ '-' + self._title
		istr = '%s (z=%d t=%d)'%(self._title,self._z,self._transparent)

		self.SetWindowText(title)
#		list.append(None)
#		list.append(('','highlight all',(self.showall,(1,))))
#		list.append(('','unhighlight all',(self.showall,(0,))))
#		list.append(('','dump hierarchy',(self._topwindow.WndsHierarchy,())))
#		list.append(('','dump displist',(self.dump_active_displist,())))

		self.destroy_menu()
		menu = win32menu.Menu() 
		float = win32menu.Menu() 
		menu.AppendPopup(float,"menu")
		
		if title:
			list = [istr, None] + list
		
		if not hasattr(self,'_cbld'):
			self._cbld = {}
		
		self._accelerators = {}
		if hasattr(self,'_cbld'):
			win32menu._create_menu(float, list, 1, self._cbld,
					self._accelerators)

		self.HookAllKeyStrokes(self._char_callback)
		self._menu = menu
	
	# return commnds class id
	def get_cmdclass_id(self,cmdcl):
		if cmdcl in usercmdui.class2ui.keys():
			return usercmdui.class2ui[cmdcl].id
		else: 
			print 'CmdClass not found',cmdcl
			return -1

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
		

	# Sets the forground color
	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	# Sets the background color
	def bgcolor(self, color):
		self._bgcolor = self._convert_color(color)

	# Returns the relative coordinates of a wnd with respect to its parent
	def getsizes(self,rc_child=None):
		if not rc_child:rc=win32mu.Rect(self.GetWindowRect())
		else: rc=rc_child
		rcParent=win32mu.Rect(self._parent.GetWindowRect())
		return self._inverse_coordinates(rc.tuple_ps(),rcParent.tuple_ps())
	# Returns the relative coordinates of a wnd with respect to its parent with 2 decimal digits
	def getsizes100(self):
		ps=self.getsizes()
		return float(int(100.0*ps[0]+0.5)/100.0),float(int(100.0*ps[1]+0.5)/100.0),float(int(100.0*ps[2]+0.5)/100.0),float(int(100.0*ps[3]+0.5)/100.0)

	# Returns the pixel coordinates from argument the relative coordinates
	def get_pixel_coords(self,box):
		return  self._convert_coordinates(box,self._canvas)

	# Returns the pixel coordinates of this window
	def get_relative_coords(self,box):
		return self._inverse_coordinates(box,self._canvas)
	# Returns the relative coordinates of the box with 2 decimal digits
	def get_relative_coords100(self,box, units = UNIT_SCREEN):
		if units == UNIT_PXL:
			return box
		elif units == UNIT_SCREEN:
			ps=self._inverse_coordinates(box,self._canvas)
			return float(int(100.0*ps[0]+0.5)/100.0),float(int(100.0*ps[1]+0.5)/100.0),float(int(100.0*ps[2]+0.5)/100.0),float(int(100.0*ps[3]+0.5)/100.0)
		elif units == UNIT_MM:
			x, y, w, h = self._canvas
			return float(x) / toplevel._pixel_per_mm_x, \
			       float(y) / toplevel._pixel_per_mm_y, \
			       float(w) / toplevel._pixel_per_mm_x, \
			       float(h) / toplevel._pixel_per_mm_y
		else:
			raise error, 'bad units specified'

	# Returns true if the point is inside the window
	def inside(self,pt):
		rc=win32mu.Rect(self.GetClientRect())
		return rc.isPtInRect(win32mu.Point(pt))

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

	# Returns the coordinates of this window in pix
	def getpixgeometry(self):
		(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
			self.GetWindowPlacement()
		rc=rcNormalPosition
		return rc[0],rc[1],rc[2]-rc[0],rc[3]-rc[1]
		
	# Returns the coordinates of this window
	def getgeometry(self, units = UNIT_MM):
		x,y,w,h=self.getpixgeometry()
		toplevel=__main__.toplevel
		if units == UNIT_MM:
			return float(x) / toplevel._pixel_per_mm_x, float(y) / toplevel._pixel_per_mm_y, \
				   float(w) / toplevel._pixel_per_mm_x, float(h) / toplevel._pixel_per_mm_y
		elif units == UNIT_SCREEN:
			return float(x) / toplevel._scr_width_pxl, \
			       float(y) / toplevel._scr_height_pxl, \
			       float(w) / toplevel._scr_width_pxl, \
			       float(h) / toplevel._scr_height_pxl
		elif units == UNIT_PXL:
			return x, y, w, h

#====================================== Register callbacks
	# Register user input callbacks
	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in(ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release, WindowExit):
			self._callbacks[event] = func, arg
		else:
			raise error, 'Internal error in Register Callback'

	# Unregister user input callbacks
	def unregister(self, event):
		try:
			del self._callbacks[event]
		except KeyError:
			pass

	# Call registered callback
	def onEvent(self,event,params=None):
		try:
			func, arg = self._callbacks[event]			
		except KeyError:
			pass
		else:
			try:
				func(arg, self, event, params)
			except Continue:
				pass
			
	# Hook messages
	def _enable_response(self,dict,wnd=None):
		if not wnd:wnd=self
		msgs = dict.keys()
		for msg in msgs:
			wnd.HookMessage(dict[msg],msg)

#====================================== Mouse input
	# Response to mouse events
#	the coordinates coming here are client rect pixel coordinates
	def onMouseEvent(self,point, ev):
		disp = self._active_displist
		if not disp: return 0
		point = self._DPtoLP(point)
		x,y = self._inverse_coordinates(point,self._canvas)
		buttons = []
		for button in disp._buttons:
			if button._inside(x,y):
				buttons.append(button)
		self.onEvent(ev,(x, y, buttons))
		return len(buttons)>0

	# Response to left button down
	def onLButtonDown(self, params):
		if self.in_create_box_mode():
			self.notifyListener('onLButtonDown',params)
			return
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Press)

	# Response to left button up
	def onLButtonUp(self, params):
		if self.in_create_box_mode():
			self.notifyListener('onLButtonUp',params)
			return
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Release)

	# Response to right button down
	def onRButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		xpos,ypos=msg.pos()

		if self._menu:
			id = self._menu.FloatMenu(self,xpos, ypos)
			if self._cbld.has_key(id) :
				callback = self._cbld[id]
				apply(callback[0], callback[1])
		elif self._topwindow==self:
			if self._popupmenu:
				menu = self._popupmenu
			else:
				menu=self._parent.get_submenu('&Tools')
			if not menu:return
			pt=(xpos,ypos)
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
		if not self.cursorCanChangeOnMove():return
		if self.in_create_box_mode():
			self.notifyListener('onMouseMove',params)
			return
		msg=win32mu.Win32Msg(params)
		point=msg.pos()
		if not self.setcursor_from_point(point,self):
			self.setcursor('arrow')

	# Set the cursor for the window passed as argument 
	# to 'hand' if the point lies in a box
	def setcursor_from_point(self,point,w):
		if not self._active_displist:return 0
		point = self._DPtoLP(point)
		x,y = self._inverse_coordinates(point,self._canvas)
		for button in self._active_displist._buttons:
			if button._inside(x,y):
				w.setcursor('hand')
				return 1
		else: return 0


	# Set the cursor given its string id		
	def setcursor(self, strid):
		if strid=='hand':
			#cursor=Sdk.LoadStandardCursor(win32con.IDC_HAND)
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_POINT_HAND)
		elif strid=='channel':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_DRAGMOVE)
		elif strid=='stop':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_STOP)
		elif strid=='link':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_DRAGLINK)
		elif strid=='' or strid=='arrow':
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
			strid='arrow'
		else:
			print 'cmifwnd:: missing cursor ',strid
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
			strid='arrow'
		if self._window_type==MPEG:Sdk.SetCursor(cursor)
		else: self.SetWndCursor(cursor)
		self.setsyscursor(strid)

	# set/get current cursor string identifier
	def setsyscursor(self,strid):
		self._curcursor=strid
#		__main__.toplevel._cursor=strid
	def getsyscursor(self):
		return self._curcursor
		#return __main__.toplevel._cursor
	# return true if the cursor can change on move
	def cursorCanChangeOnMove(self):
		return self._curcursor in ('','arrow','hand')

	# Apply window cursor
	def SetWndCursor(self,cursor):
		if cursor!=Sdk.GetCursor():
			Sdk.SetClassLong(self.GetSafeHwnd(),win32con.GCL_HCURSOR,cursor)

	# Return true if an arrow has been hit
	def hitarrow(self, point, src, dst):
		# return 1 iff (x,y) is within the arrow head
		sx, sy = self._convert_coordinates(src,self._canvas)
		dx, dy = self._convert_coordinates(dst,self._canvas)
		x, y = self._convert_coordinates(point,self._canvas)
		lx = dx - sx
		ly = dy - sy
		if lx == ly == 0:
			angle = 0.0
		else:
			angle = math.atan2(lx, ly)
		cos = math.cos(angle)
		sin = math.sin(angle)
		# translate
		x, y = x - dx, y - dy
		# rotate
		nx = x * cos - y * sin
		ny = x * sin + y * cos
		# test
		if ny > 0 or ny < -ARR_LENGTH:
			return FALSE
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return FALSE
		return TRUE


#====================================== Char
	# Callback for keyboard input
	def _char_callback(self, params):
		#if _in_create_box == None:
			if hasattr(self,'_accelerators'):
				key = chr(params)
				if self._accelerators.has_key(key):
					func, arg = self._accelerators[key]
					apply(func,arg)



#====================================== Paint

	# not used any more (same as OnPaint)
	# Respont to message WM_PAINT
	def onPaint(self, params):
		if self._parent is None or self._window_type == HTM:
			return		# already closed
		dc, paintStruct = self.BeginPaint()
		if self._active_displist:
			self._active_displist._render(dc,paintStruct[2])
		self.EndPaint(paintStruct)

	# Renders the display list at any time other than OnPaint
	def _do_expose(self,region=None):
		dc=self.GetDC()
		if not region:
			region= self._canvas
		else:
			rgn=win32ui.CreateRgn()
			rgn.CreateRectRgn(region)
			dc.SelectClipRgn(rgn)
			rgn.DeleteObject()
			del rgn
		if self._active_displist:
			self._active_displist._render(dc,region)
		self.ReleaseDC(dc)
		
	# Called by the core to set canvas size
	def setcanvassize(self, how):
		x,y,w,h=self._canvas
		if how == DOUBLE_WIDTH:
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

		self._canvas = (x,y,w,h)

		self._scroll(how)
		self._destroy_displists_tree()
		self._resize_tree()

	# Set scroll range
	def _scroll(self,how):
		if self._canscroll:
			print 'You must override _scroll for ',self
		else:
			print 'Scroll called for the unscrollable ',self
	# Enable or disable scrolling
	def setScrollMode(self,f):
		self._topwindow.setScrollMode(f)
				
#====================================== Resize
	
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
	

#=========================================================
#======= Conversions between relative and pixel coordinates
	
	# convert relative coordinates to pixel coordinates
	# using as rect of reference for relative coord
	# this wnd client rect (default) and as pixel origin
	# the left top corner of the client rect
	def _convert_coordinates(self, coordinates, ref_rect = None, crop = 0,
				 units = UNIT_SCREEN):
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		
		if ref_rect:
			rx, ry, rw, rh = ref_rect
		else: 
			rx, ry, rw, rh = self._rect
##		if not (0 <= x <= 1 and 0 <= y <= 1):
##			raise error, 'coordinates out of bounds'
		if units == UNIT_PXL or (units is None and type(x) is type(0)):
			px = int(x)
		else:
			px = int(rw * x + 0.5)
		if units == UNIT_PXL or (units is None and type(y) is type(0)):
			py = int(y)
		else:
			py = int(rh * y + 0.5)
		pw = ph = 0
		if crop:
			if px < 0:
				px, pw = 0, px
			if px >= rw:
				px, pw = rw - 1, px - rw + 1
			if py < 0:
				py, ph = 0, py
			if py >= rh:
				py, ph = rh - 1, py - rh + 1
		if len(coordinates) == 2:
			return px+rx, py+ry
		if units == UNIT_PXL or (units is None and type(w) is type(0)):
			pw = int(w + pw)
		else:
			pw = int(rw * w + 0.5) + pw
		if units == UNIT_PXL or (units is None and type(h) is type(0)):
			ph = int(h + ph)
		else:
			ph = int(rh * h + 0.5) + ph
		if crop:
			if pw <= 0:
				pw = 1
			if px + pw > rw:
				pw = rw - px
			if ph <= 0:
				ph = 1
			if py + ph > rh:
				ph = rh - py
		return px+rx, py+ry, pw, ph

	# convert pixel coordinates to relative coordinates
	# using as rect of reference for relative coord
	# this wnd client rect (default) and as pixel origin
	# the left top corner of the client rect
	def _inverse_coordinates(self,coordinates,ref_rect=None):
		px, py = coordinates[:2]

		if ref_rect:
			rx, ry, rw, rh = ref_rect
		else:
			rx, ry, rw, rh = self._rect

		x = float(px - rx) / rw
		y = float(py - ry) / rh
		if len(coordinates) == 2:
			return x, y

		pw, ph = coordinates[2:]
		w = float(pw) / rw
		h = float(ph) / rh
		return x, y, w, h

	# convert from client (device) coordinates to canvas (logical)
	def _DPtoLP(self,pt):
		if self._canscroll:
			print 'You must override _DPtoLP function for',self
		return pt

	def _convert_color(self, color):
		return color 

#====================================== Image
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

	# Prepare an image for display (load,crop,scale, etc)
	def _prepare_image(self, file, crop, scale, center, coordinates):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes

		# get image size. If it can't be found in the cash read it.
		xsize, ysize = self._image_size(file)

		# check for valid crop proportions
		top, bottom, left, right = crop
		if top + bottom >= 1.0 or left + right >= 1.0 or \
		   top < 0 or bottom < 0 or left < 0 or right < 0:
			raise error, 'bad crop size'

		# convert the crop sizes (proportions of the image size) to pixels
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		rcKeep=left,top,xsize-right,ysize-bottom

		# get window sizes, and convert them to pixels
		if coordinates is None:
			x, y, width, height = self._canvas
		else:
			x, y, width, height = self._convert_coordinates(coordinates,self._canvas)

		# compute scale taking into account the hint (0,-1)
		if scale == 0:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
		elif scale == -1:
			scale = max(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))

		# scale crop sizes
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)

		image = __main__.toplevel._image_cache[file]
		mask=None
		w=xsize
		h=ysize
		if scale != 1:
			w = int(xsize * scale + .5)
			h = int(ysize * scale + .5)

		if center:
			x, y = x + (width - (w - left - right)) / 2, \
			       y + (height - (h - top - bottom)) / 2
	
		# x -- left edge of window (left edge of the display rect)
		# y -- top edge of window (top edge of the display rect)
		# width -- width of window
		# height -- height of window
		# w -- width of scaled image
		# h -- height of scaled image
		# left, right, top, bottom -- part to be cropped (offsets from edges)

		# return:
		# image, mask
		# left,top  of crop rect
		# x,y left-top of display rect
		# w_img,h_img crop rect of  width and height
		# rcKeep  image keep unscaled rectangle

		return image, mask, left, top, x, y,\
			w - left - right, h - top - bottom,rcKeep

	def imgAddDocRef(self,file):
		toplevel=__main__.toplevel
		doc=self.getgrinsdoc()
		if doc==None: doc="__Unknown"
		if toplevel._image_docmap.has_key(doc):
			if file not in toplevel._image_docmap[doc]:
				toplevel._image_docmap[doc].append(file)
		else:
			toplevel._image_docmap[doc]=[file,]
