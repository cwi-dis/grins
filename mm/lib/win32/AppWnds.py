__version__ = "$Id$"

# the application uses the objects defined here
# to create channel wnds and document views (Channel,Hierarchy)
# using newwindow and newcmwindow

# Public Objects
# class Window

# Private Objects
# class _SubWindow(Window):

# note:
# instances of Window are created by windowinterface.newwindow(...) and windowinterface.newcmwindow(...)
# instances of _SubWindow are created indirectly by (windowinterface.newwindow(...)).newwindow(...) 
# and (windowinterface.newwindow(...)).newcmwindow(...)


import win32ui, win32con, win32api 
from win32modules import timerex, imageex, Htmlex, cmifex, cmifex2
import math

from types import *
from WMEVENTS import *

from DisplayList import DisplayList

from appcon import *
import win32mu


[_X,_Y,_WIDTH,_HEIGHT] = range(4)


toplevel=None

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""

_rb_done = '_rb_done' # exception to stop create_box loop

_in_create_box = None

#################################################
class Window:
	def __init__(self, parent, x, y, w, h, title, visible, type_channel, defcmap=0,pixmap, transparent=0, units = UNIT_MM, menubar = None, canvassize = None):
		self._canv = None
		self.arrowcache = {}
		self.box_created = 0     # indicates wheather box has been created or not
		self.box_started = 0     # indicates wheather create_box procedure has begun
		self._next_create_box = []
		self._old_callbacks = {}
		self._do_init(parent)
		self._cbld = {}
		self._align = ' '		
		self._scale = 0.0
		self._title = title
		self._topwindow = self
		self._window_state = HIDDEN
		self._parent = parent
		self._hWnd = None
		self._placement = []
		self._region = None
		self._subwindows = []
		self._displists = []
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._redrawfunc = None
		self._window_type = type_channel
		self._resize_flag = 0
		self._render_flag = 0		
		#self._sizes = x, y, w, h

		# conversion factors to convert from mm to relative size
		# (this uses the fact that _hfactor == _vfactor == 1.0
		# in toplevel)
		self._depth = 8

		# convert mm to pixels and adjust for border and caption
		x,y,w,h = to_pixels(x,y,w,h,units)
		
		self._setcursor('watch')
		
		# create OS Wnd
		self._hWnd = createChannelWnd(type_channel,title,x,y,w,h)

		a, b, w, h = self._hWnd.GetClientRect()	
		
		try:
			self._hfactor = parent._hfactor / (w/toplevel._hmm2pxl)
			self._vfactor = parent._vfactor / (h/toplevel._vmm2pxl)
		except ZeroDivisionError:
			self._hfactor = self._vfactor = 1.0

		self._rect = 0, 0, w, h
		
		self._placement = self._hWnd.GetWindowPlacement()

		self._event_list = [PAINT, SIZE, LBUTTONDOWN, SET_CURSOR, WIN_DESTROY, LBUTTONUP]
		self._enable_events()


		self._canv = None
		if canvassize is not None:
			width, height = canvassize
			# convert to pixels
			width, height = to_pixelsize(width,height,units)
			self._canv = (0, 0, width, height)
		
		self._menu = None
		if menubar is not None:
			self.create_menu(menubar)

		if visible:
			self._hWnd.ShowWindow(win32con.SW_SHOW)
		
	def _do_init(self, parent):
		parent._subwindows.insert(0, self)
		self._parent = parent
		self._subwindows = []
		self._displists = []
		self._active_displist = None
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._cursor = parent._cursor
		self._callbacks = {}
		self._old_callbacks = {}
		self._accelerators = {}
		self._menu = None
		self._transparent = 0
		self._showing = 0

	def newwindow(self, coordinates, transparent = 0, type_channel, pixmap = 0, z=0):
		win = _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		win._window_state = HIDDEN
		return win


	def newcmwindow(self, coordinates, transparent = 0, type_channel, pixmap = 0, z=0):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap, z)
		win._window_state = HIDDEN
		return win

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
		if self._hWnd :
			self.destroy_menu()
			self._hWnd.DestroyWindow()
		del self._topwindow
		self._hWnd = None

	def newdisplaylist(self, *bgcolor):
		if bgcolor != ():
			bgcolor = bgcolor[0]
		else:
			bgcolor = self._bgcolor
		return DisplayList(self, bgcolor)

	def settitle(self, title):
		if self._hWnd != None:
			if self._title != title:
				self._title = title
				self._hWnd.SetWindowText(title)	

	def show(self):
		if self._hWnd is None:
			return 
		else:
			self._window_state = SHOWN
			self._hWnd.ShowWindow(win32con.SW_SHOW)
			self.pop()

	def hide(self):
		if self._hWnd is None:
			return
		else:
			self._window_state = HIDDEN
			mes = "Hide %s"%self._title 
			self._hWnd.ShowWindow(win32con.SW_HIDE)

	def is_closed(self):
		return self._parent is None

	def showwindow(self):
		self._showing = 1
		x, y, w, h = self._hWnd.GetClientRect()
		#cmifex.DrawRectangle(self._hWnd, (x, y, w, h), (255,0,0), " ")

	def dontshowwindow(self):
		#print "Don't highlight show the window"
		if self._showing:
			self._showing = 0
			x, y, w, h = self._hWnd.GetClientRect()
			#cmifex.DrawRectangle(self._hWnd, (x, y, w, h), self._bgcolor, " ")

	def setcanvassize(self, code):
		pass

	def pop(self):
		self._hWnd.SetWindowPos(win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)

	def push(self):
		self._hWnd.SetWindowPos( win32con.HWND_BOTTOM, (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)

	def setredrawfunc(self, func):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'

	def destroy_menu(self):
		if self._menu:
			cmifex2.DestroyMenu(self._menu)
		self._menu = None
		self._accelerators = {}

	def create_menu(self, list, title = None):
		self.destroy_menu()
#		menu = self._form.CreatePopupMenu('menu',
#				{'colormap': self._colormap,
#				 'visual': self._visual,
#				 'depth': self._visual.depth})
		menu = cmifex2.CreateMenu()
		float = cmifex2.CreateMenu()
		cmifex2.PopupAppendMenu(menu,float,"menu")
#		if self._visual.depth == 8:
#			# make sure menu is readable, even on Suns
#			menu.foreground = self._convert_color((0,0,0))
#			menu.background = self._convert_color((255,255,255))
		
		if title:
			list = [title, None] + list
		
		if not hasattr(self,'_cbld'):
			self._cbld = {}
		
		#self._accelerators = {}
		if hasattr(self,'_cbld'):
			win32mu._create_menu(float, list, 1, self._cbld,
					self._accelerators)
		
		self._hWnd.HookAllKeyStrokes(self._char_callback)
		self._menu = menu

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	def bgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b
		if not self._active_displist and self._transparent == 0:
			cmifex.FillRectangle(self._hWnd,self._hWnd.GetClientRect(),self._bgcolor)
		#cmifex.SetBGColor(self._hWnd, r, g, b)

	def setcursor(self, cursor):
		if cursor == self._cursor:
			return
		win32mu._win_setcursor(self._hWnd, cursor)
		for win in self._subwindows:
			if (win._window_type == HTM):
				if (cursor == ''):
					Htmlex.EndWaitCursor(win._hWnd)
				else:
					Htmlex.BeginWaitCursor(win._hWnd)
			else:
				win.setcursor(cursor)
		self._cursor = cursor

	def _setcursor(self, cursor = ''):
		if cursor == '':
			cursor = self._cursor
		win32mu._win_setcursor(self._hWnd, cursor)

	def getgeometry(self, units = UNIT_MM):
		#print "GetGeometry for Window, ", self._title
		# client coordinates are used
		x, y, x1, y1 = self._hWnd.GetWindowPlacement()[4]
		x1, y1 , w, h = self._hWnd.GetClientRect()
		#px, py = self._inverse_coordinates((x, y))
		#pw, ph = self._inverse_coordinates((w, h))
		
		if units == UNIT_MM:
			return x / toplevel._hmm2pxl, y / toplevel._vmm2pxl, \
				   w / toplevel._hmm2pxl, h / toplevel._vmm2pxl
		elif units == UNIT_SCREEN:
			return float(x) / toplevel._screenwidth, \
			       float(y) / toplevel._screenheight, \
			       float(w) / toplevel._screenwidth, \
			       float(h) / toplevel._screenheight
		elif units == UNIT_PXL:
			return x, y, w, h

#====================================== Register callbacks
	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in (ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release, WindowExit):
			self._callbacks[event] = func, arg
		#elif event == WindowExit:
			#try:
			#	widget = self._shell
			#except AttributeError:
			#	raise error, 'only WindowExit event for top-level windows'
			#widget.deleteResponse = Xmd.DO_NOTHING
			#self._callbacks[event] = func, arg
		else:
			raise error, 'Internal error in Register Callback'

	def unregister(self, event):
		try:
			del self._callbacks[event]
		except KeyError:
			pass

#====================================== HookMessage
	def _enable_events(self):
		self._hWnd.HookMessage(self._rdblclk_callback, win32con.WM_RBUTTONDOWN)
		self._hWnd.HookMessage(self._mouseDBLClick_callback, win32con.WM_LBUTTONDBLCLK)
		for event in self._event_list:
			if event == PAINT:	
				self._hWnd.HookMessage(self._expose_callback, win32con.WM_PAINT)
			elif event == SIZE:
				self._hWnd.HookMessage(self._resize_callback, win32con.WM_SIZE)
			elif event == LBUTTONDOWN:
				self._hWnd.HookMessage(self._mouseLClick_callback, win32con.WM_LBUTTONDOWN)
			elif event == LBUTTONUP:
				#pass
				self._hWnd.HookMessage(self._mouseLButtonUp_callback, win32con.WM_LBUTTONUP)
			elif event == SET_CURSOR:
				self._hWnd.HookMessage(self._setcursor_callback, win32con.WM_MOUSEMOVE)
			elif event == WIN_DESTROY:
				self._hWnd.HookMessage(self._destroy_callback, win32con.WM_CLOSE)

#====================================== Char
	def _char_callback(self, params):
		#if _in_create_box == None:
			if hasattr(self,'_accelerators'):
				#print params
				#print self._accelerators
				key = chr(params)
				#print "key-->", key
				if self._accelerators.has_key(key):
					func, arg = self._accelerators[key]
					apply(func,arg)

#====================================== Mouse
	def _do_MouseEvent(self, window, point, ev):
		if window._callbacks.has_key(ev):
			func, arg = window._callbacks[ev]
			x, y = point
			disp = window._active_displist
			buttons = []
			if disp:
				if disp._buttons ==[]:
					x, y = self._inverse_coordinates(point)
					try:
						func(arg, window, ev, (x, y, buttons))
					except Continue:
						pass
					return
				else:
					for button in disp._buttons:
						if cmifex.ScreenToBox(window._hWnd, point, button._box):
							buttons.append(button)
			x, y = self._inverse_coordinates(point)
			try:
				func(arg, window, ev, (x, y, buttons))
			except Continue:
				pass
		return


	def _mouseLClick_callback(self, params):
		ev = Mouse0Press
		point = params[5]
		self._do_MouseEvent(self, point, ev)

	def _mouseLButtonUp_callback(self, params):
		ev = Mouse0Release	
		px, py = params[5]
		point = (px, py)
		self._do_MouseEvent(self, point, ev)

	def _rdblclk_callback(self, params):
			xpos = win32api.LOWORD(params[3])
			ypos = win32api.HIWORD(params[3])
			if self._menu:
				#kk: self._do_expose(dc,rc)
				id = cmifex2.FloatMenu(self._hWnd, self._menu, xpos, ypos)
				#print "id = ", id
				if self._cbld.has_key(id) :
					callback = self._cbld[id]
					apply(callback[0], callback[1])
			self._hWnd.ReleaseCapture()

	def _mouseDBLClick_callback(self, params):
		#try:
		#	from windowinterface import _in_create_box
		#except ImportError:
		#	_in_create_box = None
		#	pass
		#if _in_create_box == None or _in_create_box._hWnd== self._hWnd:
			ev = Mouse0Press
			point = params[5]
			self._do_MouseEvent(self, point, ev)
			self._do_MouseEvent(self, point, ev)
			#for win in self._subwindows:
			#	if win._window_state != SHOWN:
			#		self._do_MouseEvent(win, point, ev)


#====================================== Resize
	def _resize_callback(self, params):
		self.arrowcache = {}
		w = _in_create_box
		if w:
			raised = 1
			next_create_box = w._next_create_box
			w._next_create_box = []
			w._rb_cancel(0,0)
			w._next_create_box[0:0] = next_create_box
		a, b, width, height = self._hWnd.GetClientRect()
		if width==0 or height==0:
			#We've been Iconified
			return
		toplevel._setcursor('watch')
		a, b, oldWidth, oldHeight = self._rect
		self._rect = 0, 0, width, height
		# convert pixels to mm
		parent = self._parent
		w = float(width) / toplevel._hmm2pxl
		h = float(height) / toplevel._vmm2pxl
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
		
		cmifex.ResizeAllChilds(self._hWnd, width, height, oldWidth, oldHeight)

		for w in self._subwindows:
			w._do_resize1()

		# call resize callbacks		
		self._do_resize2()
		
		toplevel._setcursor('')

		if w: self._rb_end()

	def _do_resize1(self):
		# calculate new size of subwindow after resize
		# close all display lists
		
		parent = self._parent
		if parent == None:
			return
		x, y, w, h = parent._convert_coordinates(self._sizes)
		if w == 0: w = 1
		if h == 0: h = 1
		self._rect = x, y, w, h

		#the code used for  h,v factor is used in the Text Channel
		w, h = self._sizes[2:]
		if w == 0:
			w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
		if h == 0:
			h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h

		self._active_displist = None
		for d in self._displists[:]:
			d.close()

		#resize all subwindows
		for w in self._subwindows:
			#print 'SUB RESIZED'
			#if w._window_state != HIDDEN:
			w._do_resize1()

	def _do_resize2(self):
		try:
			func, arg = self._callbacks[ResizeWindow]			
		except KeyError:
			pass
		else:
			func(arg,self,ResizeWindow, None)

		for w in self._subwindows:						
			w._do_resize2()

#====================================== SetCursor
	def _setcursor_callback(self, params):
		if self._cursor == '':
			disp = self._active_displist
			buttons = []
			point = params[5]
			found = 0
			if disp:
				for button in disp._buttons:
					if cmifex.ScreenToBox(self._hWnd, point, button._box):
						win32mu._win_setcursor(self._hWnd, 'hand')
						found = 1
						break
			if not found:
				win32mu._win_setcursor(self._hWnd, '')
		else:
			win32mu._win_setcursor(self._hWnd, self._cursor)


#====================================== Destroy
	def _destroy_callback(self, params):
		#try:
		#	from windowinterface import _in_create_box
		#except ImportError:
		#	_in_create_box = None
		#	pass

		#if _in_create_box != None:
		#	cmifex.SetFlag(1)
		#	textex.SetFlag(1)
		#	Htmlex.SetFlag(1)
		#else:
		#	cmifex.SetFlag(0)
		#	textex.SetFlag(0)
		#	Htmlex.SetFlag(0)
			try:
				func, arg = self._callbacks[WindowExit]			
			except KeyError:
				pass
			else:
				func(arg, self, WindowExit, None)

#====================================== Paint
	def _expose_callback(self, params):
		dc, ps = self._hWnd.BeginPaint()

		if self._redrawfunc is None:
			if (self._window_type != HTM) or (self._hWnd.GetWindow(win32con.GW_CHILD)==None):			
				self._do_expose(dc,ps[2])
			# REWRITE AS NEEDED: self._check_expose_site_effects()
		else:
			self._redrawfunc(params)			

		self._hWnd.EndPaint(ps)

	def _do_expose(self, dc, rc, recursive = 0):
		if self._active_displist:			
			self._active_displist._render(dc, rc, 1)
		
		# CHECK:
		#else:
		#	if self._transparent == 0:
		#		cmifex.FillRectangle(self._hWnd,self._hWnd.GetClientRect(),self._bgcolor)
		if self._showing:
			self.showwindow()	

	def _forcePaint(self):
		self._hWnd.InvalidateRect()
		for w in self._subwindows:
			w._forcePaint()

	# must be checked
	def showwindow(self):
		self._showing = 1
		x, y, w, h = self._hWnd.GetClientRect()
		cmifex.DrawRectangle(self._hWnd, (x, y, w, h), (255,0,0), " ")

	# must be checked
	def dontshowwindow(self):
		#print "Don't highlight show the window"
		if self._showing:
			self._showing = 0
			x, y, w, h = self._hWnd.GetClientRect()
			cmifex.DrawRectangle(self._hWnd, (x, y, w, h), self._bgcolor, " ")


	# must be checked 
	# part of the paint code before restruct in 
	# _expose_callback that needs clarification
	# some code has no effect
	def _check_expose_site_effects(self):
		if self._topwindow is not self and self._transparent != 1 and self._active_displist!=None:
			windows = self._parent._subwindows[:]
			windows.reverse()
			for w in windows:
				if w._active_displist!=None and w._transparent == 1 and w != self and self._z <= w._z:
					rect1 = w._hWnd.GetClientRect()
					rect2 = w._hWnd.ScreenToClient(self._hWnd.ClientToScreen(self._hWnd.GetClientRect()))
					if rect2[0] < 0 and rect2[2] < 0:
						continue
					if rect2[1] < 0 and rect2[3] < 0:
						continue
					if rect2[2] < rect1[0] and rect2[3] < rect1[1]:
						continue
					if rect2[0] > rect1[2] and rect2[1] > rect1[3]:
						continue
					if rect2[0] > rect1[2] and rect2[2] > rect1[2]:
						continue
					if rect2[1] > rect1[3] and rect2[3] > rect1[3]:
						continue
		else:
			windows = self._subwindows[:]
			for w in windows:
				if w._transparent and w._active_displist!=None:
					pass #w._hWnd.PostMessage(win32con.WM_PAINT)


###############################################################################
###############################################################################
###############################################################################

	def create_box(self, msg, callback, box = None):

		global _in_create_box	
		if _in_create_box:
			_in_create_box._next_create_box.append((self, msg, callback, box))
			return

		if self.is_closed():
			apply(callback, ())
			return

		_in_create_box = self
		self.pop()

		import win32con
		for win in self._subwindows :
			win._hWnd.ShowWindow(win32con.SW_HIDE)

		if msg:
			msg = msg + '\n\n' + _rb_message
		else:
			msg = _rb_message

		self._rb_dl = self._active_displist
		if self._rb_dl:
			d = self._rb_dl.clone()
		else:
			d = self.newdisplaylist()

		ls = []
		top_w, c_name  = self.find_topwin_channel(box)
		#print top_w, c_name
		self.find_channels(top_w.hierarchyview.root,ls,c_name)
		#print ls
		tmp = []
		tmp = self.find_windows(top_w,ls)
		if tmp == []:
			tmp = self._subwindows
		#print tmp
		
		#for win in self._subwindows:
		for win in tmp:
			b = win._sizes
			if b != (0, 0, 1, 1):
				d.drawbox(b)
		self._rb_display = d.clone()
		d.fgcolor((255, 0, 0))
		if box:
			d.drawbox(box)
		d.render()
		self._rb_curdisp = d
				
		self._rb_dialog = dialog.Dialog(CloseDialogRC.IDD_CREATE_BOX, dll)
		self._rb_dialog.HookCommand(self._rb_cancel, win32con.IDCANCEL)
		self._rb_dialog.HookCommand(self._rb_done, win32con.IDOK)
		self._rb_dialog.CreateWindow()
		label = self._rb_dialog.GetDlgItem(CloseDialogRC.IDC_BOX_LABEL)
		label.SetWindowText(msg)
		
		wind = self
		while wind._parent != toplevel:
			wind = wind._parent

		wli, wti, wri, wbi = wind._hWnd.GetWindowPlacement()[4]
		wl, wt, wr, wb = (wli, wti, wri, wbi)
		
		if wl-310<0:
			if wr+320<cmifex.GetScreenWidth():
				wl = wr+320
			else:
				if wt-210>0:
					wt = wt-210
				elif wb+210<cmifex.GetScreenHeight():
					wt = wb+10
				wl = 310

		if wt+200>cmifex.GetScreenHeight() and wt==wti:
			wt = wt - 210

		self._rb_dialog.MoveWindow((wl-310, wt, wl-10, wt+200))	
		self._rb_dialog.ShowWindow(win32con.SW_SHOW)
		self._rb_callback = callback
		#form = self._form
		form = self._hWnd

		
		#save existing message handlers (callbacks)
		for k in self._callbacks.keys():
			self._old_callbacks[k] = self._callbacks[k]

		# enable mouse events
		form.HookMessage(self._do_rb, win32con.WM_MOUSEMOVE)
		#form.HookMessage(self._end_rb, win32con.WM_LBUTTONUP)
		self.register(WMEVENTS.Mouse0Press, self._start_rb, None)
		self.register(WMEVENTS.Mouse0Release, self._end_rb, None)
		
		
		print "---START OF create_box---"
		print "box--->", box
		
		if box:
			x, y, w, h = self._convert_coordinates(box)
			#wx, wy, ww, wh = self._hWnd.GetClientRect()
			#x = int(box[0]*ww)
			#y = int(box[1]*wh)
			#w = int(box[2]*ww)
			#h = int(box[3]*wh)
			#print "x, y, w, h--->", x, y, w, h
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			print "x, y, w, h is now--->", x, y, w, h
			self._rb_box = x, y, w, h
			self._rb_start_x = x
			self._rb_start_y = y
			self._rb_width = w
			self._rb_height = h
		else:
			self._rb_start_x, self._rb_start_y, self._rb_width, \
					  self._rb_height = self._rect
			self._rb_box = self._rect
			print "self._rect of create_box--->", self._rect
		#Htmlex.SetCursor(self._hWnd, 2)
		cmifex.SetCursor(win32Cursors['hand'])
		self._cur_cur = 2
		print "---END OF create_box---"
	
	
	def find_topwin_channel(self, box):
		import TopLevel
		found = 0
		top_w = None
		c_name = None
		for top in TopLevel.opentops:
			for i in top.views[0].channels.keys():
				if hasattr(top.views[0].channels[i],'window'):
					if hasattr(top.views[0].channels[i].window,'_hWnd'):
						if top.views[0].channels[i].window==self:
							found = 1
							top_w = top
							break
			if found:
				break
		
		sub = None
		for win in self._subwindows:
			b = win._sizes
			if b != (0, 0, 1, 1):
				if b == box:
					sub = win

		for i in top_w.views[0].channels.keys():
			if hasattr(top_w.views[0].channels[i],'window'):
				if hasattr(top_w.views[0].channels[i].window,'_hWnd'):
					if top_w.views[0].channels[i].window==sub:
						c_name = top_w.views[0].channels[i]._name
						break
		return top_w, c_name
	
	def find_channels(self, node, ls, name):
		for c_list in node.GetAllChannels():
			if c_list != None:
				if name in c_list and len(c_list)>1:
					for item in c_list:
						if item not in ls:
							ls.append(item)
		for n in node.GetChildren():
			self.find_channels(n,ls,name)
			
	def find_windows(self, top, ls):
		import TopLevel
		tmp = []
		for i in top.views[0].channels.keys():
			if hasattr(top.views[0].channels[i],'window'):
				if top.views[0].channels[i]._name in ls and \
					top.views[0].channels[i].window in self._subwindows:
						tmp.append(top.views[0].channels[i].window)
		return tmp


	
	def hitarrow(self, point, src, dst):
		# return 1 iff (x,y) is within the arrow head
		sx, sy = self._convert_coordinates(src)
		dx, dy = self._convert_coordinates(dst)
		x, y = self._convert_coordinates(point)
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


	# supporting methods for create_box
	def _rb_finish(self):
		#Htmlex.SetCursor(self._hWnd, 0)
		cmifex.SetCursor(0)
		global _in_create_box
		_in_create_box = None
		form = self._hWnd
		
		#self._rb_dialog.close()
		self._rb_dialog.DestroyWindow()
		self._rb_dialog = None

		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		self._rb_display.close()
		self._rb_curdisp.close()
		#del self._rb_callback
		del self._rb_dialog
		del self._rb_dl
		del self._rb_display
		#del self._gc_rb
		# show all hidden windows since drawing is done
		for win in self._subwindows :
			win._hWnd.ShowWindow(win32con.SW_SHOW)

	def _rb_cvbox(self):
		x0 = self._rb_start_x
		y0 = self._rb_start_y
		x1 = x0 + self._rb_width
		y1 = y0 + self._rb_height
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, width, height = self._rect
		
		if self._parent != toplevel:
			x = 0
			y = 0
		
		if x0 < x: x0 = x
		if x0 >= x + width: x0 = x + width - 1
		if x1 < x: x1 = x
		if x1 >= x + width: x1 = x + width - 1
		if y0 < y: y0 = y
		if y0 >= y + height: y0 = y + height - 1
		if y1 < y: y1 = y
		if y1 >= y + height: y1 = y + height - 1
		return float(x0 - x) / (width - 1), \
		       float(y0 - y) / (height - 1), \
		       float(x1 - x0) / (width - 1), \
		       float(y1 - y0) / (height - 1)

	
	def _null_rb(self, params):
		return

	
	def _rb_done(self, par1, par2):
		print 'Create box done'
		self.unregister(WMEVENTS.Mouse0Release)
		self.unregister(WMEVENTS.Mouse0Press)
		self._hWnd.HookMessage(self._null_rb, win32con.WM_MOUSEMOVE)

		callback = self._rb_callback
		self._rb_finish()
		print 'BOX IS:'
		print self._rb_cvbox()
		print self._rect
		apply(callback, self._rb_cvbox())
		
		print 'BEFORE RESTORING :'
		print self._old_callbacks
		print self._callbacks 		
		#restore message handlers (callbacks)
		for k in self._old_callbacks.keys(): 
			self._callbacks[k] = self._old_callbacks[k]
		print 'restoring------------', self._callbacks
		for k in self._old_callbacks.keys(): 
			del self._old_callbacks[k]

		self.box_created = 1
		self._rb_end()

	def _rb_cancel(self, par1, par2):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())
		self.box_created = 1
		self._rb_end()

	def _rb_end(self):
		#execute pending create_box calls
		next_create_box = self._next_create_box
		self._next_create_box = []
		for win, msg, cb, box in next_create_box:
			win.create_box(msg, cb, box)
		

	def _rb_draw(self, flag=0):
		x = self._rb_start_x
		y = self._rb_start_y
		w = self._rb_width
		h = self._rb_height
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		if flag==1:
			cmifex.DrawRectangle(self._hWnd, (x, y, x+w, y+h), self._bgcolor, " ")	
		else:
			cmifex.DrawRectangle(self._hWnd, (x, y, x+w, y+h), (0,0,0), "d")
		#self.DrawRectangle((x, y, x+w, y+h))
				
	
	def DrawRectangle(self, rect):
		x0, y0, x1, y1 = rect	
		#cmifex.BeginPaint(self._hWnd, 0)
		dcd = self._hWnd.GetDC()
		#dcd = dc
		col = win32api.RGB(255, 255, 255)
		dcd.FillSolidRect(self._hWnd.GetClientRect(), col)
		dcd.MoveTo(x0, y0)
		dcd.LineTo(x0, y1)
		dcd.LineTo(x1, y1)
		dcd.LineTo(x1, y0)
		dcd.LineTo(x0, y0)
		self._hWnd.ReleaseDC(dcd)
		#cmifex.EndPaint(self._hWnd, 0)

	def _rb_constrain(self, event):
		#print "---START OF _rb_constrain---"
		x, y, w, h = self._rect
		if self._parent != toplevel:
			x = 0
			y = 0
		#print "x, y, w, h--->", x, y, w, h
		t0 = event[0]
		t1 = event[1]
		if event[0] < x:
			#event[0] = x
			t0 = x
		if event[0] >= x + w:
			#event[0] = x + w - 1
			t0 = x + w -1
		if event[1] < y:
			#event[1] = y
			t1 = y
		if event[1] >= y + h:
			#event[1] = y + h - 1
			t1 = y + h -1

		#print "event--->", event
		#print "---END OF _rb_constrain---"		
		return (t0, t1)
		

	def _rb_common(self, event):
		#print "---START OF _rb_common---" 
		if not hasattr(self, '_rb_cx'):
			a = []
			ev = 0
			val = []
			val.append(event[0])
			val.append(event[1])
			val.append(a)
			self._start_rb(0, self._hWnd, ev, val)
		#self._rb_draw()
		event = self._rb_constrain(event)
		if self._rb_cx and self._rb_cy:
			#print '_rb_cx and  _rb_cy EXIST' 
			x, y, w, h = self._rect
			if self._parent != toplevel:
				x = 0
				y = 0
			dx = event[0] - self._rb_last_x
			dy = event[1] - self._rb_last_y
			self._rb_last_x = event[0]
			self._rb_last_y = event[1]
			self._rb_start_x = self._rb_start_x + dx
			if self._rb_start_x + self._rb_width > x + w:
				self._rb_start_x = x + w - self._rb_width
			if self._rb_start_x < x:
				self._rb_start_x = x
			self._rb_start_y = self._rb_start_y + dy
			if self._rb_start_y + self._rb_height > y + h:
				self._rb_start_y = y + h - self._rb_height
			if self._rb_start_y < y:
				self._rb_start_y = y
		else:
			#print '_rb_cx and  _rb_cy DO NOT EXIST' 
			if not self._rb_cx:
				self._rb_width = event[0] - self._rb_start_x
				#print 'EVENT[0], START_X IS:', event[0], self._rb_start_x
				#print 'WIDTH IS:', self._rb_width
			if not self._rb_cy:
				self._rb_height = event[1] - self._rb_start_y
		self._rb_box = 1
		#print '_rb_common--->', self._rb_start_x, self._rb_start_y, self._rb_width, self._rb_height
		#print "---END OF _rb_common---"


	def convert_to_client(self, params):
		px, py = params[5]
		x0, y0, w0, h0 = self._hWnd.GetWindowPlacement()[4]
		x1, y1, z1, w1 = self._hWnd.ScreenToClient((px, py, px, py))
		return (x1, y1, z1, w1)

	def _start_rb(self, dummy, window, ev, val):
		print '---START OF start_rb---'
		# called on mouse press
		if  not _in_create_box:
			return
		point = (val[0], val[1])
		print "point--->", point
		vl = self._convert_coordinates(point)
		#wx, wy, ww, wh = self._hWnd.GetClientRect()
		#vl = (int(point[0]*ww), int(point[1]*wh))
		
		print "vl--->", vl

		#Just examine the case where we have 'nested' windows
		#That happens when an anchor lies on a child window
		#then we refer to the child window
		#parent = self._hWnd.GetParent()
		#x1 = 0
		#if (parent <> None):
		#	x1, x2, x3, x4 = parent.GetWindowPlacement()[4] 
		#	print 'PARENT EXISTS:'
		#	print parent.GetWindowPlacement()[4]
		#print x1

		px = vl[0]
		py = vl[1]
		

		self.box_started = 1
		import Htmlex
		event=(px, py)

		self._rb_display.render()
		self._rb_curdisp.close()
		event = self._rb_constrain(event)
		if self._rb_box:
			x = self._rb_start_x
			y = self._rb_start_y
			w = self._rb_width
			h = self._rb_height
			print 'START X, START Y, W, H :', x, y, w, h
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			if x + w/4 < event[0] < x + w*3/4:
				#print 'X-------------- took value'
				self._rb_cx = 1
			else:
				self._rb_cx = 0
				if event[0] >= x + w*3/4:
					x, w = x + w, -w
			if y + h/4 < event[1] < y + h*3/4:
				#print 'Y-------------- took value'
				self._rb_cy = 1
			else:
				self._rb_cy = 0
				if event[1] >= y + h*3/4:
					y, h = y + h, -h
			if self._rb_cx and self._rb_cy:
				self._rb_last_x = event[0]
				self._rb_last_y = event[1]
				self._rb_start_x = x
				self._rb_start_y = y
				self._rb_width = w
				self._rb_height = h
			else:
				if not self._rb_cx:
					self._rb_start_x = x + w
					self._rb_width = event[0] - self._rb_start_x
				if not self._rb_cy:
					self._rb_start_y = y + h
					self._rb_height = event[1] - self._rb_start_y
				print 'else of self._rb_cx and self._rb_cy --->', self._rb_start_x, self._rb_start_y, self._rb_width, self._rb_height

			if self._rb_cx or self._rb_cy:
				if self._rb_cx and self._rb_cy:
					self._cur_cur = win32Cursors['g_hand'] #hand
				elif self._rb_cx and self._rb_height>0:
					self._cur_cur = win32Cursors['dstrech'] #drag down
				elif self._rb_cx and self._rb_height<0:
					self._cur_cur = win32Cursors['ustrech'] #drag up
				elif self._rb_cy and self._rb_width>0:
					self._cur_cur = win32Cursors['rstrech'] #drag right
				elif self._rb_cy and self._rb_width<0:
					self._cur_cur = win32Cursors['lstrech'] #drag left
			else:
				if self._rb_width>0 and self._rb_height>0:
					self._cur_cur = win32Cursors['drstrech'] #drag right bottom corner
				if self._rb_width>0 and self._rb_height<0:
					self._cur_cur = win32Cursors['urstrech'] #drag right top corner
				if self._rb_width<0 and self._rb_height>0:
					self._cur_cur = win32Cursors['dlstrech'] #drag left bottom corner
				if self._rb_width<0 and self._rb_height<0:
					self._cur_cur = win32Cursors['ulstrech'] #drag left top corner
			#Htmlex.SetCursor(self._hWnd, self._cur_cur)
			cmifex.SetCursor(self._cur_cur)
		else:
			self._rb_start_x = event[0]
			self._rb_start_y = event[1]
			self._rb_width = self._rb_height = 0
			self._rb_cx = self._rb_cy = 0
			print 'else of if box--->', self._rb_start_x, self._rb_start_y, self._rb_width, self._rb_height
		self._rb_draw()
		print '---END OF start_rb---'

	def _do_rb(self, params):
		#print "---START OF _do_rb---"
		#print "params--->", params
		# called on mouse drag
		#Htmlex.SetCursor(self._hWnd, self._cur_cur)
		cmifex.SetCursor(self._cur_cur)
		if  not _in_create_box:
			return
		if (params[2] == 1):
			self._hWnd.SetCapture()
			self._rb_draw(1)
			if self._rb_display:
				self._rb_display._render(self._hWnd, 1)
			t = self.convert_to_client(params)
			event = (t[0], t[1])
			self._rb_common(event)
			self._rb_draw()
		#print "---END OF _do_rb---"
				

	def _end_rb(self, dummy, window, ev, val):
		# called on mouse release
		self._hWnd.ReleaseCapture()
		print "---START OF _end_rb---"
		self._cur_cur = 2
		if  not _in_create_box:
			return
		#t = self.convert_to_client(params)
		#event = (t[0], t[1])
		
		#x, y, w, h = self._convert_coordinates(box)
		#wx, wy, ww, wh = self._hWnd.GetClientRect()
				
		vl = self._convert_coordinates((val[0],val[1]))
		print "vl--->", vl
		
        #Just examine the case where we have 'nested' windows
		#That happens when an anchor lies on a child window
		#then we refer to the child window

		px = vl[0]
		py = vl[1]
		
		event = (px, py)
		
		self._rb_common(event)
		self._rb_curdisp = self._rb_display.clone()
		self._rb_curdisp.fgcolor((255, 0, 0))
		self._rb_curdisp.drawbox(self._rb_cvbox())
		self._rb_display.render()
		self._rb_curdisp.render()
		cmifex.SetCursor(0)
		print "---END OF _end_rb---"


	def _convert_color(self, color):
		#self._hWnd.MessageBox("convert_color", "Debug", win32con.MB_OK)
		return color #self._parent._convert_color(color, 0)


	def _convert_coordinates(self, coordinates):
		width, height = (self._rect[_WIDTH],self._rect[_HEIGHT])
		x, y = coordinates[:2]
		if self._parent == toplevel:
			px = int((width - 1) * x + 0.5) + self._rect[_X]
			py = int((height - 1) * y + 0.5) + self._rect[_Y]
		else:
			px = int((width - 1) * x + 0.5)
			py = int((height - 1) * y + 0.5)
		if len(coordinates) == 2:
			return px, py
		w, h = coordinates[2:]
		pw = int((width - 1) * w + 0.5)
		ph = int((height - 1) * h + 0.5)
		return px, py, pw, ph

	# inverse function of convert_coordinates
	# converts pixel sizes to relative sizes
	# ADDED BY SOL (MUADDIB) 
	# written only for points
	def _inverse_coordinates(self, point):		
		x = 0
		y = 0
		if (self._hWnd != None):	
			if self._parent == toplevel:
				px, py = point
				plcm = self._hWnd.GetWindowPlacement()	
				if plcm[1]==3:
					x0 = 0
					y0 = 0
				else:
					x0, y0, x1, y1 = plcm[4]
				
				par1, par2, w, h = self._hWnd.GetClientRect()

				caption = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
				xborder = win32api.GetSystemMetrics(win32con.SM_CXEDGE)
				yborder = win32api.GetSystemMetrics(win32con.SM_CYEDGE)
				border = win32api.GetSystemMetrics(win32con.SM_CYBORDER)

				# substract the window caption, because GetWindowPlacement ignores it
				rect = (x0+2*xborder+border, y0+caption+2*yborder+border, w, h)

				x = (float)((px-rect[_X]-0.5)/(rect[_WIDTH]-1))	
				y = (float)((py-rect[_Y]-0.5)/(rect[_HEIGHT]-1))
			else:
				px, py = point	
				x0, y0, x1, y1 = self._hWnd.GetWindowPlacement()[4]
				
				plcm = self._parent._hWnd.GetWindowPlacement()
				if plcm[1]==3:
					px0 = 0
					py0 = 0
				else:
					px0, py0, px1, py1 = plcm[4]

				par1, par2, w, h = self._hWnd.GetClientRect()

				x0 = x0 + px0
				y0 = y0 + py0
				#x1 = x1 + px1
				#y1 = y1 + py1

				caption = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
				xborder = win32api.GetSystemMetrics(win32con.SM_CXEDGE)+win32api.GetSystemMetrics(win32con.SM_CXBORDER)
				yborder = win32api.GetSystemMetrics(win32con.SM_CYEDGE)+win32api.GetSystemMetrics(win32con.SM_CYBORDER)
				border = win32api.GetSystemMetrics(win32con.SM_CYBORDER)
				
				# substract the window caption, because GetWindowPlacement ignores it
				rect = (x0+2*xborder+border, y0+caption+2*yborder+border, w, h)

				x = (float)((px-rect[_X]-0.5)/(rect[_WIDTH]-1))	
				y = (float)((py-rect[_Y]-0.5)/(rect[_HEIGHT]-1))
		return x, y


#====================================== Image
	def _image_size(self, file):
		if toplevel._image_size_cache.has_key(file):
			return toplevel._image_size_cache[file]
		import gifex
		isgif = 0
		nf = file
		of = None
		if gifex.TestGIF(file)==1:
				nf = file + ".bmp"
				gifex.ReadGIF(file,nf)
				isgif = 1
		try:
			width, height = imageex.SizeOfImage(nf)
			if isgif:
				import win32api
				win32api.DeleteFile(nf)
		except:
			width, height = (0,100)
		toplevel._image_size_cache[file] = width, height
		return width, height

	def _prepare_image(self, file, crop, scale, center, coordinates, transp = -1):
		imageHandle, l, t, r, b = imageex.PrepareImage(self._hWnd, file, scale, center,transp)
		return imageHandle, l, t, r, b


#====================================== Not Used
	# have to override these for create_box
	def _input_callback(self, form, client_data, call_data):
		if _in_create_box:
			return
		
	def _delete_callback(self, form, client_data, call_data):
		self.arrowcache = { }
		w = _in_create_box
		if w:
			raised = 1
			next_create_box = w._next_create_box
			w._next_create_box = []
			w._rb_cancel(0,0)
			w._next_create_box[0:0] = next_create_box
		if w: self._rb_end()







###########################################################
###########################################################
###########################################################

class _SubWindow(Window):
	def __init__(self, parent, coordinates, transparent, type_channel, defcmap, pixmap, z=0):
		if z < 0:
			raise error, 'invalid z argument'
		self._z = z
		self._align = ' '
		x, y, w, h = coordinates
		if x >= 1.0: 
			x = 0
		if y >= 1.0: 
			y = 0
		if w <= 0: 
			w = 1.0
		if h <= 0: 
			h = 1.0
		coord = (x, y, w, h)
		px, py, pw, ph = parent._convert_coordinates(coord)
		if pw == 0: pw = 1
		if ph == 0: ph = 1	
		self._num = len(parent._subwindows)+1
		self._title = "Child "+ `self._num`+" of " + parent._title 
		self._rect = px, py, pw, ph
		self._sizes = coord
		if w == 0 or h == 0:
			showmessage('Creating subwindow with zero dimension',
				    mtype = 'warning')
		if w == 0:
			w = float(self._rect[_WIDTH]) / parent._rect[_WIDTH]
		if h == 0:
			h = float(self._rect[_HEIGHT]) / parent._rect[_HEIGHT]
		# conversion factors to convert from mm to relative size
		# (this uses the fact that _hfactor == _vfactor == 1.0
		# in toplevel)
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h

		#self._xfactor = parent._xfactor
		#self._yfactor = parent._yfactor	

		#6/2A
		#self._convert_color = parent._convert_color
		for i in range(len(parent._subwindows)):
			if self._z >= parent._subwindows[i]._z:
				parent._subwindows.insert(i, self)
				break
		else:
			parent._subwindows.insert(0, self)
		self._do_init(parent)
		self._topwindow = parent._topwindow

		if parent._transparent:
			self._transparent = parent._transparent
		else:
			if transparent not in (-1, 0, 1):
				raise error, 'invalid value for transparent arg'
			self._transparent = transparent
		
		#MUADDIB
		#self._form = parent._form
		#self._gc = parent._gc
		try:
			self._pixmap = parent._pixmap
		except AttributeError:
			have_pixmap = 0
		else:
			have_pixmap = 1

		self._resize_flag = 0
		self._render_flag = 0
		self._window_type = type_channel		
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._redrawfunc = None

		# create OS Child Wnd
		self._hWnd = createChannelChildWnd(type_channel,self._title,parent._hWnd,px,py,pw,ph)

		x, y, a, b = self._hWnd.GetWindowRect()
		a, b, width, height = self._hWnd.GetClientRect()
		width = width-12
		#self._placement = x, y, width, height
		self._placement = self._hWnd.GetWindowPlacement()
		#r, g, b = self._bgcolor
		#cmifex.SetBGColor(self._hWnd, r, g, b)

		self._event_list = [PAINT, LBUTTONDOWN, LBUTTONUP, SET_CURSOR, WIN_DESTROY]
		self._enable_events()

		#parent._mkclip()
		#if not self._transparent:
		#	self._do_expose(self._region)
		#	if have_pixmap:
		#		x, y, w, h = self._rect
		#		self._gc.SetRegion(self._region)
		#		self._pixmap.CopyArea(self._form, self._gc,
		#				      x, y, w, h, x, y)
		if self._transparent in (-1,1) and self._window_type != HTM:
			cmifex.SetSiblings(self._hWnd, 1)
		self.show()

		self.arrowcache = {}
		self._next_create_box = []
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			if transparent not in (-1, 0, 1):
				raise error, 'invalid value for transparent arg'
			self._transparent = transparent 


	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)

	def _destroy_callback(self, params):
		#try:
		#	from windowinterface import _in_create_box
		#except ImportError:
		#	_in_create_box = None
		#	pass

		#if _in_create_box != None:
		#	cmifex.SetFlag(1)
		#	textex.SetFlag(1)
		#	Htmlex.SetFlag(1)
		#else:
		#	cmifex.SetFlag(0)
		#	textex.SetFlag(0)
		#	Htmlex.SetFlag(0)
			try:
				func, arg = self._callbacks[WindowExit]			
			except KeyError:
				pass
			else:
				func(arg, self, WindowExit, None)

	def close(self):
		parent = self._parent
		self.hide()
		if parent is None:
			return		# already closed
		for dl in self._displists[:]:
			dl.close()
		self._parent = None
		parent._subwindows.remove(self)
		for win in self._subwindows[:]:
			win.close()
		#parent._mkclip()
		#parent._do_expose(self._hWnd)
		if self._hWnd :
			self.destroy_menu()
			self._hWnd.DestroyWindow()
		if hasattr(self, '_pixmap'):
			x, y, w, h = self._rect
			#self._gc.SetRegion(self._region)
			#self._pixmap.CopyArea(self._form, self._gc,
			#		      x, y, w, h, x, y)
			del self._pixmap
		del self._topwindow
		self._hWnd = None

	def settitle(self, title):
		raise error, 'can only settitle at top-level'

	def getgeometry(self, units = UNIT_MM):
		#print "GetGeometry for BareSubWindow, ", self._title
		x, y, x1, y1 = self._hWnd.GetWindowPlacement()[4]
		x1, y1 , w, h = self._hWnd.GetClientRect()
		#px, py = self._inverse_coordinates((x, y))
		#pw, ph = self._inverse_coordinates((w, h))
		
		return x / toplevel._hmm2pxl, y / toplevel._vmm2pxl, \
		       w / toplevel._hmm2pxl, h / toplevel._vmm2pxl


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
		ind = parent._subwindows.index(self)
		if ind != 0: #len(parent._subwindows)-1:
			self._hWnd.SetWindowPos(parent._subwindows[ind-1]._hWnd.GetSafeHwnd(), (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
		else:
			self._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
		#parent.pop()
	

	def push(self):
		parent = self._parent
		# put self behind all siblings with equal or higher z
		#if self is parent._subwindows[-1]:
		#	# already at the end
		#	return
		parent._subwindows.remove(self)
		for i in range(len(parent._subwindows)-1,-1,-1):
			if self._z <= parent._subwindows[i]._z:
				parent._subwindows.insert(i+1, self)
				break
		else:
			parent._subwindows.insert(0, self)
		
		ind = parent._subwindows.index(self)
		if ind != 0: #len(parent._subwindows)-1:
			self._hWnd.SetWindowPos(parent._subwindows[ind-1]._hWnd.GetSafeHwnd(), (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		else:
			self._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		
		#if self._topwindow is not self:
		#	#i = self._parent._subwindows.index(self)
		#	windows = self._parent._subwindows[:]
		#	#windows.reverse()
		#	for w in windows:
		#		if w._active_displist!=None and w != self and self._z >= w._z:
		#			#w._forcePaint()
		#			#w._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
		#			rect1 = self._hWnd.GetClientRect()
		#			rect2 = self._hWnd.ClientToScreen(rect1)
		#			rect2 = w._hWnd.ScreenToClient(rect2)
		#			rect1 = w._hWnd.GetClientRect()
		#			if rect2[0] < 0 and rect2[2] < 0:
		#				return
		#			if rect2[1] < 0 and rect2[3] < 0:
		#				return
		#			if rect2[2] < rect1[0] and rect2[3] < rect1[1]:
		#				return
		#			if rect2[0] > rect1[2] and rect2[1] > rect1[3]:
		#				return
		#			if rect2[0] > rect1[2] and rect2[2] > rect1[2]:
		#				return
		#			if rect2[1] > rect1[3] and rect2[3] > rect1[3]:
		#				return
		#			# add lines to render
		#			#print "rect1, rect2 --->", w._title, "-->", rect1, self._title, "-->", rect2
		#			#print self._title, "-->", self._active_displist._list
		#			w._do_expose(w._hWnd, 1)
		#self._hWnd.SetWindowPos( win32con.HWND_BOTTOM , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		
	def _mkclip(self):
		self._hWnd.MessageBox("BareSunWnd CLip", "Debug", win32con.MB_OK)
		if not self._parent:
			return
		return
		Window._mkclip(self)
		region = self._clip
		# subtract overlapping siblings
		for w in self._parent._subwindows:
			if w is self:
				break
			#if not w._transparent:
			#	r = Xlib.CreateRegion()
			#	apply(r.UnionRectWithRegion, w._rect)
			#	region.SubtractRegion(r)






###########################################################
###########################################################
###########################################################
# Utilities
def to_pixels(x,y,w,h,units):
	if x==None: x=0
	if y==None: y=0
	global toplevel
	if units == UNIT_MM:
		if x is not None:
			x = int(float(x) * toplevel._hmm2pxl + 0.5)
		if y is not None:
			y = int(float(y) * toplevel._vmm2pxl + 0.5)
		w = int(float(w) * toplevel._hmm2pxl + 0.5)
		h = int(float(h) * toplevel._vmm2pxl + 0.5)
	elif units == UNIT_SCREEN:
		if x is not None:
			x = int(float(x) * toplevel._screenwidth + 0.5)
		if y is not None:
			y = int(float(y) * toplevel._screenheight + 0.5)
		w = int(float(w) * toplevel._screenwidth + 0.5)
		h = int(float(h) * toplevel._screenheight + 0.5)
	elif units == UNIT_PXL:
		if x is not None:
			x = int(x)
		if y is not None:
			y = int(y)
		w = int(w)
		h = int(h)
	else:
		raise error, 'bad units specified'

	# adjust
	xborder = toplevel.xborder
	yborder = toplevel.yborder
	caption = toplevel.caption
	x = x-xborder 
	y = y-(yborder+caption)
	w = w
	h = h+(2*yborder+caption) 
	if x<0: x=0
	if y<0: y=0
	if x>toplevel._screenwidth-xborder: x=toplevel._screenwidth-xborder
	if y>toplevel._screenheight-caption: y=toplevel._screenheight-caption

	return (x,y,w,h)

def to_pixelsize(width,height,units):
	if units == UNIT_MM:
		width = int(float(width) * toplevel._hmm2pxl + 0.5)
		height = int(float(height) * toplevel._vmm2pxl + 0.5)
	elif units == UNIT_SCREEN:
		width = int(float(width) * toplevel._screenwidth + 0.5)
		height = int(float(height) * toplevel._screenheight + 0.5)
	elif units == UNIT_PXL:
		width = int(width)
		height = int(height)
	return (width,height)

################################
def createChannelWnd(type_channel,title,x,y,w,h):
	print "createChannelWnd",type_channel,title,x,y,w,h
	if (type_channel == SINGLE) :
		wnd = cmifex.CreateWindow(title, x, y, w, h, 0)
		cmifex.SetScrollInfo(wnd,win32con.SB_VERT,0,0,0,0,1)
		cmifex.SetScrollInfo(wnd,win32con.SB_HORZ,0,0,0,0,1)
	elif (type_channel == HTM) :
		wnd = Htmlex.CreateWindow(title, x, y, w, h, 0)
	elif (type_channel == TEXT) :
		wnd = cmifex.CreateWindow(title, x, y, w, h, 0)
	else :
		wnd = cmifex.CreateWindow(title, x, y, w, h, 0)
		cmifex.SetScrollInfo(wnd,win32con.SB_VERT,0,0,0,0,1)
		cmifex.SetScrollInfo(wnd,win32con.SB_HORZ,0,0,0,0,1)
	return wnd

def createChannelChildWnd(type_channel,title,parentwnd,px,py,pw,ph):
	if (type_channel == SINGLE) :
		wnd = cmifex.CreateChildWindow(title, parentwnd, px, py, pw, ph)
	elif (type_channel == HTM) :
		wnd = Htmlex.CreateChildWindow(title, parentwnd, px, py, pw, ph)
	elif (type_channel == TEXT) :
		wnd = cmifex.CreateChildWindow(title, parentwnd, px, py, pw, ph)
	else :
		wnd = cmifex.CreateChildWindow(title, parentwnd, px, py, pw, ph)
	return wnd
