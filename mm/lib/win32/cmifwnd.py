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
import usercmd,wndusercmd,usercmdui

# globals 
import __main__

import  rbtk
import DrawTk
from DropTarget import DropTarget

import win32window

class _CmifWnd(win32window.Window, DropTarget, rbtk._rbtk, DrawTk.DrawLayer):
	def __init__(self):
		win32window.Window.__init__(self)
		DropTarget.__init__(self)
		rbtk._rbtk.__init__(self)
		DrawTk.DrawLayer.__init__(self)

		# menu support
		self._menu = None		# Dynamically created rightmousemenu
		self._popupmenu = None	# Statically created rightmousemenu (for views)
		self._popup_point =(0,0)
		self._cbld = {}
		
		# window title
		self._title = None

		# scroll indicator
		self._canscroll = 0

	# part of the constructor initialization
	def _do_init(self,parent):
		self._parent = parent
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor
	
	# drag and drop files support
	# enable drop
	def dragAcceptFiles(self):
		self.DragAcceptFiles(1)
		self.HookMessage(self.onDropFiles,win32con.WM_DROPFILES)

	# dissable drop
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
##		rc=win32mu.Rect(self.GetClientRect())	
##		DrawTk.drawTk.SetSmallFont(dc)
##		if self._showing:
##			old=dc.SetTextColor(win32mu.RGB(self._showing))
##		if hasattr(self,'_z'):
##			s = '%s (z=%d)'%(self._title,self._z)
##		else:
##			s = self._title
##		rc.inflateRect(-2,-2)
##		dc.SetBkMode(win32con.TRANSPARENT)
##		dc.DrawText(s,rc.tuple(),win32con.DT_SINGLELINE|win32con.DT_TOP|win32con.DT_CENTER)
##		if self._showing:
##			old=dc.SetTextColor(old)
##		DrawTk.drawTk.RestoreFont(dc)

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

		self.assert_not_in_create_box()

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
		self._obj_ = None


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

	# return commnds class id
	def get_cmdclass_id(self,cmdcl):
		if usercmdui.class2ui.has_key(cmdcl):
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

	# convert from client (device) coordinates to canvas (logical)
	def _DPtoLP(self,pt):
		if self._canscroll:
			print 'You must override _DPtoLP function for',self
		return pt

	def _convert_color(self, color):
		return color 

#====================================== Register callbacks
	# Register user input callbacks
	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in(ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release, 
				 DropFile, PasteFile, DragFile,
				 WindowExit):
			self._callbacks[event] = func, arg
			if event == DropFile:
				self.registerDropTarget()
		else:
			raise error, 'Unregister event',event

	# Unregister user input callbacks
	def unregister(self, event):
		try:
			del self._callbacks[event]
			if event == DropFile:
				self.revokeDropTarget()
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
				return 0
		return 1
	
	# Call registered callback with return value
	def onEventEx(self,event,params=None):
		ret=None
		try:
			func, arg = self._callbacks[event]			
		except KeyError:
			pass
		else:
			try:
				ret=func(arg, self, event, params)
			except Continue:
				pass
		return ret
			
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
##		if not disp: return 0
		point = self._DPtoLP(point)
		x,y = self._pxl2rel(point,self._canvas)
		buttons = []
		if disp is not None:
			for button in disp._buttons:
				if button._inside(x,y):
					buttons.append(button)
		return self.onEvent(ev,(x, y, buttons))

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
			self.onLButtonDown(params)
			id = self._menu.FloatMenu(self,xpos, ypos)
			if self._cbld.has_key(id) :
				callback = self._cbld[id]
				apply(callback[0], callback[1])
		elif self._topwindow==self:
			menu=None
			if self._popupmenu:
				self.onLButtonDown(params)
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
		if not self.cursorCanChangeOnMove():return
		if self.in_create_box_mode():
			self.notifyListener('onMouseMove',params)
			return
		msg=win32mu.Win32Msg(params)
		point=msg.pos()
		if not self.setcursor_from_point(point,self):
			self.setcursor(self._cursor)

	# Set the cursor for the window passed as argument 
	# to 'hand' if the point lies in a box
	def setcursor_from_point(self,point,w):
		if not self._active_displist:return 0
		point = self._DPtoLP(point)
		x,y = self._pxl2rel(point,self._canvas)
		for button in self._active_displist._buttons:
			if button._inside(x,y):
				w.setcursor('hand')
				return 1
		else: 
			return 0


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
		elif strid=='draghand':
			cursor = win32ui.GetApp().LoadCursor(grinsRC.IDC_DRAG_HAND)
		else:
			cursor=Sdk.LoadStandardCursor(win32con.IDC_ARROW)
			strid='arrow'

		self.SetWndCursor(cursor)
		self._curcursor = strid

	# return true if the cursor can change on move
	def cursorCanChangeOnMove(self):
		return self._curcursor in ('','arrow','hand', 'draghand')

	# Apply window cursor
	def SetWndCursor(self,cursor):
		if cursor!=Sdk.GetCursor():
			Sdk.SetClassLong(self.GetSafeHwnd(),win32con.GCL_HCURSOR,cursor)


#====================================== Paint

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
		
	def scrollvisible(self, coordinates, units = UNIT_MM):
		pass

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
#	animation section overrides

	def updatecoordinates(self, coordinates, units=UNIT_SCREEN):
		# first convert any coordinates to pixel
		coordinates = self._convert_coordinates(coordinates,units=units)
		#print 'window.updatecoordinates',coordinates
		
		x, y = coordinates[:2]
		
		# move or/and resize window
		flags = win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER
		if len(coordinates)==2:
			flags = flags | win32con.SWP_NOSIZE
			w, h = 0, 0
		elif len(coordinates)==4:
			w, h = coordinates[2:]
			# HACK : allow to update the "_canvas" variable as well
			# otherwise, the image scale is wrong
			#self.setcanvassize((UNIT_PXL,w,h))
			self._canvas = 0,0,w,h
			# end HACK
		else:
			raise AssertionError

		self.SetWindowPos(self.GetSafeHwnd(),(x,y,w,h),
			win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER)
	
	# HACK : allow to update all windows
	# not automaticly performed !!!
	def updateall(self):
		top = self._topwindow
		top.update( )   # work fir image, doesn't work for video
		top.UpdateWindow() # work for video, doesn't work for image
	# end HACK
			
	def updatezindex(self, z):
		# XXX: keep in sync with grins regions implementation
		self._z = z
		self.z_order_subwindows()
		#print 'window.updatezindex',z

	def updatebgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b
		#print 'window.updatebgcolor',color
		if self._active_displist:
			# XXX: new method DisplayList.updatebgcolor
			self._active_displist.updatebgcolor(color)
			rgn1 = win32ui.CreateRgn()
			rgn1.CreateRectRgn(self.GetClientRect())			
			rgn2 = self._active_displist._win32rgn
			rgn  = win32ui.CreateRgn()
			rgn.CreateRectRgn((0,0,0,0))
			rgn.CombineRgn(rgn1,rgn2,win32con.RGN_DIFF)
			self.RedrawWindow(None,rgn)			
			rgn1.DeleteObject()
			rgn.DeleteObject()

		
#=========================================================
#	geometry and coordinates convert section overrides
	
	# Returns the coordinates of this window in pix
	def getpixgeometry(self):
		(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
			self.GetWindowPlacement()
		rc=rcNormalPosition
		return rc[0],rc[1],rc[2]-rc[0],rc[3]-rc[1]
		
	# Returns the relative coordinates of a wnd with respect to its parent
	def getsizes(self,rc_child=None):
		if not rc_child:rc=win32mu.Rect(self.GetWindowRect())
		else: rc=rc_child
		rcParent=win32mu.Rect(self._parent.GetWindowRect())
		return self._pxl2rel(rc.tuple_ps(),rcParent.tuple_ps())


#	End of convert coordinates section
#=========================================================




#====================================== 
#	Image section overrides

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


# End of image section overrides
#########################


