__version__ = "$Id$"

# gen lib
import math
from types import *

# lib
import win32ui, win32con, win32api 
from win32modules import imageex,grinsRC
from DisplayList import DisplayList
Sdk = win32ui.GetWin32Sdk()

# utilities
import win32mu,win32menu

# constants
from appcon import *
from WMEVENTS import *

# globals 
toplevel=None # set by AppTopLevel

import  rbtk
import DrawTk

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
		self._menu = None
		self._transparent = 0
		self._showing = 0
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
		self._bgcolor = toplevel._bgcolor
		self._fgcolor = toplevel._fgcolor
		self._cursor = ''

		# temp sigs
		self._wnd = None
		self._hWnd = 0


	def _do_init(self,parent):
		self._parent = parent
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor

	
	def newwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		raise error, 'overwrite newwindow'
		return None

	def newcmwindow(self, coordinates, pixmap = 0, transparent = 0, z = 0, type_channel = SINGLE):
		raise error, 'overwrite newcmwindow'
		return None
		
	def newdisplaylist(self, *bgcolor):
		if bgcolor != ():
			bgcolor = bgcolor[0]
		else:
			bgcolor = self._bgcolor
		return  DisplayList(self, bgcolor)

	def settitle(self, title):
		if self._obj_ != None:
			if self._title != title:
				self._title = title
				self.SetWindowText(title)	

	def show(self):
		if self._obj_ is None:
			return 
		else:
			self.ShowWindow(win32con.SW_SHOW)
			self.pop()

	def hide(self):
		if self._obj_ is None:
			return
		else:
			self.ShowWindow(win32con.SW_HIDE)

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
		if self._obj_ and self.IsWindow():
			self.destroy_menu()
			self.DestroyWindow()
		del self._topwindow
		self._obj_ = None

	def is_closed(self):
		return self._parent is None

	def pop(self):
		self.SetWindowPos(win32con.HWND_TOP,(0,0,0,0),
			win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)

	def push(self):
		self.SetWindowPos( win32con.HWND_BOTTOM,(0,0,0,0), 
			win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)

	def setredrawfunc(self, func):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'

	def setTransparent(self,enable):
		style = self.GetWindowLong(win32con.GWL_EXSTYLE)
		if enable:
			style = style | win32con.WS_EX_TRANSPARENT;
		else:
			style = style & ~win32con.WS_EX_TRANSPARENT;
		self.SetWindowLong(win32con.GWL_EXSTYLE,style)

	def isTransparent(self):
		style = self.GetWindowLong(win32con.GWL_EXSTYLE)
		if (style & win32con.WS_EX_TRANSPARENT)!=0:
			return 1
		else:
			return 0

	def destroy_menu(self):
		if self._menu:
			del self._menu 
		self._menu = None
		self._accelerators = {}

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = win32ui.CreateMenu()
		float = win32ui.CreateMenu()
		win32menu.PopupAppendMenu(menu,float,"menu")
		
		if title:
			list = [title, None] + list
		
		if not hasattr(self,'_cbld'):
			self._cbld = {}
		
		#self._accelerators = {}
		if hasattr(self,'_cbld'):
			win32menu._create_menu(float, list, 1, self._cbld,
					self._accelerators)

		self.HookAllKeyStrokes(self._char_callback)
		self._menu = menu

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	def bgcolor(self, color):
		self._bgcolor = self._convert_color(color)

	def setcursor(self, cursor):
		if cursor == self._cursor:
			return
		win32mu.SetCursor(cursor)
		self._cursor = cursor

	def getgeometry(self, units = UNIT_MM):
		if self._obj_==None or self.IsWindow()==0:return
		(flags,showCmd,ptMinPosition,ptMaxPosition,rcNormalPosition)=\
			self.GetWindowPlacement()
		rc=rcNormalPosition
		x,y,w,h=rc[0],rc[1],rc[2]-rc[0],rc[3]-rc[1]
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

	def unregister(self, event):
		try:
			del self._callbacks[event]
		except KeyError:
			pass

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
			

	def _enable_response(self,dict,wnd=None):
		if not wnd:wnd=self
		msgs = dict.keys()
		for msg in msgs:
			wnd.HookMessage(dict[msg],msg)

#====================================== Mouse input
#	the coordinates coming here are client rect pixel coordinates
	def onMouseEvent(self,point, ev):
		disp = self._active_displist
		if not disp: return
		point = self._DPtoLP(point)
		x,y = self._inverse_coordinates(point,self._canvas)
		buttons = []
		for button in disp._buttons:
			if button._inside(x,y):
				buttons.append(button)
		self.onEvent(ev,(x, y, buttons))

	def onLButtonDown(self, params):
		self.notifyListener('onLButtonDown',params)
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Press)

	def onLButtonUp(self, params):
		self.notifyListener('onLButtonUp',params)
		msg=win32mu.Win32Msg(params)
		self.onMouseEvent(msg.pos(),Mouse0Release)

	def onRButtonDown(self, params):
		msg=win32mu.Win32Msg(params)
		xpos,ypos=msg.pos()
		if self._menu:
			id = win32menu.FloatMenu(self,self._menu, xpos, ypos)
			if self._cbld.has_key(id) :
				callback = self._cbld[id]
				apply(callback[0], callback[1])
		self.ReleaseCapture()

	def onLButtonDblClk(self, params):
		msg=win32mu.Win32Msg(params);pt=msg.pos()
		self.onMouseEvent(pt,Mouse0Press)
		self.onMouseEvent(pt,Mouse0Press)

	def onMouseMove(self, params):
		self.notifyListener('onMouseMove',params)
		#if self._cursor!='': return
		if not self._active_displist: return
		buttons = []
		msg=win32mu.Win32Msg(params)
		x,y = self._inverse_coordinates(self._DPtoLP(msg.pos()),self._canvas)
		for button in self._active_displist._buttons:
			if button._inside(x,y):
				self.setcursor('hand')
				break

	def notifyListener(self,key,params):
		if rbtk._in_create_box==None: return
		if key=='onLButtonDown':DrawTk.DrawLayer.onLButtonDown(self,params)
		elif key=='onLButtonUp':DrawTk.DrawLayer.onLButtonUp(self,params)
		elif key=='onMouseMove':DrawTk.DrawLayer.onMouseMove(self,params)
		elif key=='OnDraw':DrawTk.DrawLayer.OnDraw(self,params)

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
	def _char_callback(self, params):
		#if _in_create_box == None:
			if hasattr(self,'_accelerators'):
				key = chr(params)
				if self._accelerators.has_key(key):
					func, arg = self._accelerators[key]
					apply(func,arg)


#====================================== Destroy
	def OnClose_X(self):
		self.onEvent(WindowExit)

#====================================== Paint

	# not used any more (same as OnPaint)
	def onPaint(self, params):
		if self._parent is None or self._window_type == HTM:
			return		# already closed
		dc, paintStruct = self.BeginPaint()
		if self._active_displist:
			self._active_displist._render(dc,paintStruct[2],1)
		self.EndPaint(paintStruct)

	# render display list at any time other than OnPaint
	def _do_expose(self,region=None,show=0):
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
			self._active_displist._render(dc,region,show)
		self.ReleaseDC(dc)
		

	# response to channel highlight
	def showwindow(self,color=(255,0,0)):
		self._showing = 1
		win32mu.DrawWndRectangle(self, self.GetClientRect(), color, " ")
	# response to channel unhighlight
	def dontshowwindow(self):
		if self._showing:
			self._showing = 0
			win32mu.DrawWndRectangle(self,self.GetClientRect(),self._bgcolor, " ")
	def is_showing(self):
		return self._showing

	def setcanvassize(self, how):
		x,y,w,h=self._canvas
		if how == DOUBLE_WIDTH:
			w = w * 2
		elif how == DOUBLE_HEIGHT:
			h = h * 2
		elif how == DOUBLE_SIZE:
			w = w * 2
			h = h * 2
		else: # RESET_CANVAS
			w, h = self._rect[2],self._rect[3]
		self._canvas = (x,y,w,h)

		self._scroll(how)
		self._destroy_displists_tree()
		self._create_displists_tree()

	def _scroll(self,how):
		if self._canscroll:
			print 'You must overwrite _scroll for ',self
		else:
			print 'Scroll called for the unscrollable ',self
				
#====================================== Resize
	
	# it resizes all childs with this wnd as top level
	# defined for the benefit of the top level windows
	# that are not scrollable	
	def _do_resize(self,new_width,new_height):
		if self._topwindow != self:
			print '_do_resize called from the non-toplevel wnd',self
		self._destroy_displists_tree()

		rc=win32mu.Rect(self._rect)# rem: self has not been resized yet
		old_width,old_height=rc.width(),rc.height()
		self._rect=self._canvas=0,0,new_width,new_height

		if old_width<=0:old_width=1 # raise error
		if old_height<=0:old_height=1
		xf = float(new_width)/old_width;
		yf = float(new_height)/old_height;
		hdwp = Sdk.BeginDeferWindowPos(8);
		for w in self._subwindows:
			hdwp=w._resize_wnds_tree(hdwp,xf,yf)
		Sdk.EndDeferWindowPos(hdwp);
		self._create_displists_tree()
		self.LockWindowUpdate()
		for w in self._subwindows:
			w._resize_controls()
		self.UnlockWindowUpdate()
		


	# destroy all display lists for this wnd and iteratively 
	# for its childs, for the childs of its childs, etc	
	def _destroy_displists_tree(self):
		self._active_displist = None
		for d in self._displists[:]:
			d.close()
		for w in self._subwindows:
			w._destroy_displists_tree()

	# create all display lists for this wnd and iteratively 
	# for its childs, for the childs of its childs, etc
	def _create_displists_tree(self):
		self.onEvent(ResizeWindow)
		for w in self._subwindows:
			w._create_displists_tree()

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
		flags = win32con.SWP_NOZORDER
		hdwp=Sdk.DeferWindowPos(hdwp,self.GetSafeHwnd(),0,\
			(l,t,w,h),flags)
		for w in self._subwindows:
			hdwp=w._resize_wnds_tree(hdwp,xf,yf)
		return hdwp
	
	def _resize_controls(self):
		pass

#=========================================================
#======= Conversions between relative and pixel coordinates
	
	# convert relative coordinates to pixel coordinates
	# using as rect of reference for relative coord
	# this wnd client rect (default) and as pixel origin
	# the left top corner of the client rect
	def _convert_coordinates(self, coordinates,ref_rect=None):
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		
		if ref_rect:
			rx, ry, rw, rh = ref_rect
		else: 
			rx, ry, rw, rh = self._rect
			
		px = int((rw - 1) * x + 0.5) + rx
		py = int((rh - 1) * y + 0.5) + ry
		if len(coordinates) == 2:
			return px, py

		pw = int((rw - 1) * w + 0.5) 
		ph = int((rh - 1) * h + 0.5)
		return px, py, pw, ph

	# convert pixel coordinates to relative coordinates
	# using as rect of reference for relative coord
	# this wnd client rect (default) and as pixel origin
	# the left top corner of the client rect
	def _inverse_coordinates(self,coordinates,ref_rect=None):		
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		
		if ref_rect:rx, ry, rw, rh = ref_rect
		else: rx, ry, rw, rh = self._rect

		px = float(x-rx)/rw
		py = float(y-ry)/rh
		if len(coordinates) == 2:
			return px, py
		
		pw = float(w)/rw
		ph = float(h)/rh
		return px, py, pw, ph

	# convert from client (device) coordinates to canvas (logical)
	def _DPtoLP(self,pt):
		if self._canscroll:
			print 'You must overwrite _DPtoLP function for',self
		return pt

	def _convert_color(self, color):
		return color 

#====================================== Image
	def _image_size(self, file):
		try:
			xsize, ysize = toplevel._image_size_cache[file]
		except KeyError:
			img = imageex.load(file)
			xsize,ysize,depth=imageex.size(img)
			toplevel._image_size_cache[file] = xsize, ysize
			toplevel._image_cache[file] = img
		return xsize, ysize

	def _prepare_image(self, file, crop, scale, center, coordinates):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes
		oscale = scale
		tw = self._topwindow
		#format = toplevel._imgformat
		#depth = format.descr['align'] / 8
		reader = None

		# get image size. If it can't be found in the cash read it.
		if toplevel._image_size_cache.has_key(file):
			xsize, ysize = toplevel._image_size_cache[file]
		else:
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

		image = toplevel._image_cache[file]
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
