__version__ = "$Id$"

import cmifex, timerex, imageex, textex, Htmlex
import win32ui, win32con, win32api
import dialog, MainDialogRC
import string

from windowinterface import *
from types import *

error = 'windowinterface.error'
FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2
WM_MAINLOOP = 200

try:
	dll=win32ui.LoadLibrary('\\cmif\\PyDlls\\cmifex.pyd')
except win32ui:
	print "Could not Locate CmifEx.Pyd"	

Version = 'WIN32_DBG'
toplevel = None

_size_cache = {}

pseudo_id = 100

a_window=None

[_X, _Y, _WIDTH, _HEIGHT] = range(4)
[PAINT, SIZE, LBUTTONDOWN, MM_MCI_NOTIFY, SET_CURSOR, WIN_DESTROY] = range(6)
[OPAQUE, TRANSPARENT] = range(2)
[HIDDEN, SHOWN] = range(2)
[ARROW, WAIT, HAND, START] = range(4)

[SINGLE, HTM, TEXT, MPEG] = range(4)

win32Cursors = { 'hand':HAND, 'watch':WAIT, '':ARROW, 'start':START }

from WMEVENTS import *

# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel:
	# we actually need it.
	def __getattr__(self, attr):
		if not self._initialized: # had better exist...
			self._do_init()
			try:
				return self.__dict__[attr]
			except KeyError:
				pass
		raise AttributeError, attr
	def __init__(self):
		self._initialized = 0
		global toplevel
		if toplevel:
			raise error, 'only one Toplevel allowed'
		toplevel = self

		self.xborder = win32api.GetSystemMetrics(win32con.SM_CXFRAME) + 2*win32api.GetSystemMetrics(win32con.SM_CXBORDER)
		self.yborder = win32api.GetSystemMetrics(win32con.SM_CYFRAME) + 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)
		self.caption = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
		
		self._timerWnd = timerex.CreateTimerWindow()
		self._timerWnd.HookMessage(self._timer_callback, win32con.WM_TIMER)
		self._timerWnd.HookMessage(self._message_callback, WM_MAINLOOP)
	#self._inputWnd = inputex.CreateInputWindow()
	#self._inputWnd.HookMessage(self._input_callback, win32con.WM_TIMER)

	def _do_init(self):
		if self._initialized:
			raise error, 'can only initialize once'
		self._initialized = 1	
		self._closecallbacks = []
		self._subwindows = []
		self._bgcolor = 255, 255, 255 # white
		self._fgcolor =   0,   0,   0 # black
		self._running = 0
		self._pseudo_id_list = []
		self._cursor = ''
		self._image_size_cache = {}
		self._image_cache = {}
		self._screenwidth = cmifex.GetScreenWidth()
		self._screenheight = cmifex.GetScreenHeight()
		self._dpi_x = cmifex.GetScreenXDPI()
		self._dpi_y = cmifex.GetScreenYDPI()
		self._mscreenwidth = (float(self._screenwidth)*25.4) / self._dpi_x
		self._mscreenheight = (float(self._screenheight)*25.4) / self._dpi_y
		self._hmm2pxl = float(self._screenwidth) / self._mscreenwidth
		self._vmm2pxl = float(self._screenheight) / self._mscreenheight
		self._hfactor = self._vfactor = 1.000

		#import pdb
		#pdb.set_trace()
		
		self._immediate = []
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._timerDict = {}
		self._timerfunc = None
		import time
		self._time = time.time()
		self.timerid = None
		# file descriptor handlin
		self._fdiddict = {}
		self._ifddict = {}
		self._ofddict = {}
		self._inputDict = {}
		self._inputs = []
		self.MainDialog = None

	def forcePaint(self):
		for w in self._subwindows:
			w._forcePaint()

	def close(self):
		self._timerWnd.MessageBox("Toplevel.Close!", "Debug", win32con.MB_OK)
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		self._closecallbacks = []
		self._subwindows = []
		self.__init__()		# clears all lists

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	def newwindow(self, x, y, w, h, title, pixmap = 0, visible_channel = TRUE, type_channel = SINGLE):
		return _Window(self, x, y, w, h, title, visible_channel, type_channel, 0, pixmap, 0)

	def newcmwindow(self, x, y, w, h, title, pixmap = 0, visible_channel = TRUE, type_channel = SINGLE):
		return _Window(self, x, y, w, h, title, visible_channel, type_channel, 1, pixmap, 0)

	def setcursor(self, cursor):
		for win in self._subwindows:
			if (win._window_type == HTM):
				if (cursor ==''):
					Htmlex.EndWaitCursor(win._hWnd)
				else:
					Htmlex.BeginWaitCursor(win._hWnd)
			else:
				win.setcursor(cursor)
		self._cursor = cursor

	def pop(self):
		self._inputWnd.MessageBox("POP Toplevel", "Debug", win32con.MB_OK)
		pass

	def push(self):
		self._inputWnd.MessageBox("PUSH Toplevel", "Debug", win32con.MB_OK)
		pass

	def show(self):
		self._inputWnd.MessageBox("Show Toplevel", "Debug", win32con.MB_OK)
		for w in self._subwindows:
			w.show()
	
	def hide(self):
		self._inputWnd.MessageBox("Hide Toplevel", "Debug", win32con.MB_OK)
		for w in self._subwindows:		
			w.hide()


	def usewindowlock(self, lock):
		pass

	def mainloop(self):
		self.MainDialog.show()	
		#f = open("d:\\tmp\\paint.log", "a")
		#f.write("Toplevel.Mainloop -\n")	
		self._timerWnd.PostMessage(WM_MAINLOOP, 0, 0)
		#f.write("Toplevel.Mainloop - Message Sent\n")
		#f.close()

	def serve_events(self):
		#print 'Time to serve events', '\n'
		import time, select
		while self._timers:
				t = time.time()
				sec, cb, tid = self._timers[0]
				sec = sec - (t - self._time)
				self._time = t
				if sec <= 0:
					del self._timers[0]
					func, args = cb
					#print 'timer applied'
					apply(func, args)
				else:
					self._timers[0] = sec, cb, tid
					break
				ifdlist = self._ifddict.keys()
				ofdlist = self._ofddict.keys()
				
		#self._timerWnd.PostMessage(WM_MAINLOOP, 0, 0)
		#		print 'serve events - SetTimer'
		self.timerid = timerex.SetTimer(int(0.001 * 1000))
		#self.timerid = timerex.SetTimer(int(0.001 * 1000000))
				#timerex.KillTimer(self.timerid)		
			#if self._timers:
			#	timeout = self._timers[0][0]
			#	ifdlist, ofdlist, efdlist = select.select(
			#		ifdlist, ofdlist, [], timeout)
			#else:
			#	ifdlist, ofdlist, efdlist = select.select(
			#		ifdlist, ofdlist, [])
			#for fd in ifdlist:
			#	try:
			#		func, args = self._ifddict[fd]
			#	except KeyError:
			#		pass
			#	else:
			#		apply(func, args)
			#for fd in ofdlist:
			#	try:
			#		func, args = self._ofddict[fd]
			#	except KeyError:
			#		pass
			#	else:
			#		apply(func, args)

	
	def _timer_callback(self, params):
		#print 'timer callback called'
		timerex.KillTimer(self.timerid)		
		self.serve_events()
		#print self.timerid 
		

	def _message_callback(self, params):
		#print 'message callback called'
		self.serve_events()
		

	# timer interface
	def settimer(self, sec, cb):
		#print 'timer set'
		import time
		t0 = time.time()
		if self._timers:
			t, a, i = self._timers[0]
			t = t - (t0 - self._time) # can become negative
			self._timers[0] = t, a, i
		self._time = t0
		self._timer_id = self._timer_id + 1
		t = 0
		for i in range(len(self._timers)):
			time, dummy, tid = self._timers[i]
			if t + time > sec:
				self._timers[i] = (time - sec + t, dummy, tid)
				self._timers.insert(i, (sec - t, cb, self._timer_id))
				return self._timer_id
			t = t + time
		self._timers.append(sec - t, cb, self._timer_id)
		#self._timerWnd.PostMessage(WM_MAINLOOP, 0, 0)
		return self._timer_id

	def canceltimer(self, id):
		#print 'timer canceled'
		for i in range(len(self._timers)):
			t, cb, tid = self._timers[i]
			if tid == id:
				del self._timers[i]
				if i < len(self._timers):
					tt, cb, tid = self._timers[i]
					self._timers[i] = (tt + t, cb, tid)
		return

	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		pass
		#if type(fd) is not type(0):
		#	fd = fd.fileno()
		#try:
		#	del self._ifddict[fd]
		#except KeyError:
		#	pass
		#try:
		#	del self._ofddict[fd]
		#except KeyError:
		#	pass
		#if mask & ReadMask:
		#	if func:
		#		self._ifddict[fd] = func, args
		#if mask & WriteMask:
		#	if func:
		#		self._ofddict[fd] = func, args


	
	#utility functions
	def _convert_color(self, color, defcm):
		r, g, b = color
		c = 12
		return c
		if defcm:
			if self._cm_cache.has_key(`r,g,b`):
				return self._cm_cache[`r,g,b`]
			ri = int(r / 255.0 * 65535.0)
			gi = int(g / 255.0 * 65535.0)
			bi = int(b / 255.0 * 65535.0)
			cm = self._default_colormap
			try:
				color = cm.AllocColor(ri, gi, bi)
			except RuntimeError:
				# can't allocate color; find closest one
				m = 0
				color = None
				# use floats to guard against overflow
				rf = float(ri)
				gf = float(gi)
				bf = float(bi)
				for c in cm.QueryColors(range(256)):
					# calculate distance
					d = (rf-c[1])*(rf-c[1]) + \
					    (gf-c[2])*(gf-c[2]) + \
					    (bf-c[3])*(bf-c[3])
					if color is None or d < m:
						# found one that's closer
						m = d
						color = c
				color = self._colormap.AllocColor(color[1],
							color[2], color[3])
				#print "Warning: colormap full, using 'close' color",
				#print 'original:',`r,g,b`,'new:',`int(color[1]/65535.0*255.0),int(color[2]/65535.0*255.0),int(color[3]/65535.0*255.0)`
			# cache the result
			self._cm_cache[`r,g,b`] = color[0]
			return color[0]
		r = int(float(r) / 255. * float(self._red_mask) + .5)
		g = int(float(g) / 255. * float(self._green_mask) + .5)
		b = int(float(b) / 255. * float(self._blue_mask) + .5)
		c = (r << self._red_shift) | \
		    (g << self._green_shift) | \
		    (b << self._blue_shift)
		return c

	def _setcursor(self, cursor = ''):
		for win in self._subwindows:
			if (win._window_type == HTM):
				if (cursor ==''):
					Htmlex.EndWaitCursor(win._hWnd)
				else:
					Htmlex.BeginWaitCursor(win._hWnd)
			else:
				win.setcursor(cursor)


class _Window:
	def __init__(self, parent, x, y, w, h, title, visible, type_channel, defcmap = 0, pixmap = 0, 
			transparent = 0):
		#parent._subwindows.append(self)
		self._do_init(parent)

		self._align = ''		
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
		self._sizes = x, y, w, h

		# conversion factors to convert from mm to relative size
		# (this uses the fact that _hfactor == _vfactor == 1.0
		# in toplevel)
		#self._depth = self._visual.depth
		self._depth = 8
		# convert mm to pixels
		
		x = int(float(x) * toplevel._hmm2pxl + 0.5)
		y = int(float(y) * toplevel._vmm2pxl + 0.5)
		w = int(float(w) * toplevel._hmm2pxl + 0.5)
		h = int(float(h) * toplevel._vmm2pxl + 0.5)	

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

		

		#self._xfactor = self._yfactor = 1.0
		
		self._setcursor('watch')
		#self._hWnd = cmifex.CreateWindow(title, x, y, w, h, 0)

		if (type_channel == SINGLE) :
			#print "Window"
			self._hWnd = cmifex.CreateWindow(title, x, y, w, h, 0)
		elif (type_channel == HTM) :
			#print "Html Window"
			self._hWnd = Htmlex.CreateWindow(title, x, y, w, h, 0)
		elif (type_channel == TEXT) :
			#print "Text Window"
			self._hWnd = textex.CreateWindow(title, x, y, w, h, 0)
			#self._hWnd = cmifex.CreateWindow(title, x, y, w, h, 0)
		else :
			print 'UnKnown window type - SINGLE USED AS BACKUP'
			self._hWnd = cmifex.CreateWindow(title, x, y, w, h, 0)

		#x, y, a, b = self._hWnd.GetWindowRect()
		a, b, w, h = self._hWnd.GetClientRect()	
		r, g, b = self._bgcolor
		cmifex.SetBGColor(self._hWnd, r, g, b)

		self._hfactor = parent._hfactor / (w/toplevel._hmm2pxl)
		self._vfactor = parent._vfactor / (h/toplevel._vmm2pxl)
		self._rect = 0, 0, w, h
		
		#self._placement = x, y, width, height
		self._placement = self._hWnd.GetWindowPlacement()
		#self._expose_callback(100)
		self._event_list = [PAINT, SIZE, LBUTTONDOWN, SET_CURSOR, WIN_DESTROY]
		self._enable_events()
		if visible:
			self._hWnd.ShowWindow(win32con.SW_SHOW)

	def _forcePaint(self):
		#print "@@@@: ", self._title, self._hWnd
		self._hWnd.InvalidateRect()
		for w in self._subwindows:
			w._forcePaint()
	
	def _rdblclk_callback(self, params):
		print "\n------------------RDBLCLK--------------\n"

	def _enable_events(self):
		self._hWnd.HookMessage(self._rdblclk_callback, win32con.WM_RBUTTONDBLCLK)
		for event in self._event_list:
			if event == PAINT:	
				self._hWnd.HookMessage(self._expose_callback, win32con.WM_PAINT)
			if event == SIZE:
				self._hWnd.HookMessage(self._resize_callback, win32con.WM_SIZE)
			if event == LBUTTONDOWN:
				self._hWnd.HookMessage(self._mouseLClick_callback, win32con.WM_LBUTTONDOWN)
			if event == SET_CURSOR:
				self._hWnd.HookMessage(self._setcursor_callback, win32con.WM_SETCURSOR)
			if event == WIN_DESTROY:
				self._hWnd.HookMessage(self._destroy_callback, win32con.WM_CLOSE)

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
		self._accelerators = {}
		self._menu = None
		self._transparent = 0
		self._showing = 0

	def create_box(self, string, func):	
		#print "CreateBox: ", string, " calling: ", func
		self._hWnd.MessageBox("Create_Box", "Debug", win32con.MB_OK)
		return

	def show(self):
		if self._hWnd is None:
			return 
		else:
			self._window_state = SHOWN
			self._hWnd.ShowWindow(win32con.SW_SHOW)

	def hide(self):
		if self._hWnd is None:
			return
		else:
			self._window_state = HIDDEN
			mes = "Hide %s"%self._title 
			#self._hWnd.MessageBox(mes, "Debug", win32con.MB_OK)
			self._hWnd.ShowWindow(win32con.SW_HIDE)
			#flags = win32con.SWP_NOSIZE|win32con.SWP_NOMOVE|win32con.SWP_HIDEWINDOW|win32con.SWP_NOREPOSITION|win32con.SWP_NOREDRAW
			#self._hWnd.SetWindowPos(win32con.HWND_BOTTOM, (0, 0, 0, 0), flags)
			#logmes = "---------HIDE:  " + self._title + "\n"
			

	def close(self):
		self.hide()
		#self._hWnd.MessageBox("_Window.Close %s"%self._title, "Debug", win32con.MB_OK)
		print "_Window.Close %s"%self._title
		if self._parent is None:
			return		# already closed
		self._parent._subwindows.remove(self)
		self._parent = None
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		del self._topwindow
		#self._hWnd = None

	def is_closed(self):
		return self._parent is None

	def newwindow(self, coordinates, transparent = 0, pixmap = 0, type_channel = SINGLE):
		win = _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap)
		win._window_state = HIDDEN
		return win

	def newcwindow(self, coordinates, transparent = 0, pixmap = 0, type_channel = SINGLE):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap)
		win._window_state = HIDDEN
		return win
		
	def showwindow(self):
		#print "Highlight Show the window"
		pass
		
	def dontshowwindow(self):
		print "Don't highlight show the window"
		pass

	def _convert_color(self, color):
		#self._hWnd.MessageBox("convert_color", "Debug", win32con.MB_OK)
		return self._parent._convert_color(color, 0)

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r, g, b

	def bgcolor(self, color):
		r, g, b = color
		self._bgcolor = r, g, b		
		cmifex.SetBGColor(self._hWnd, r, g, b)

	def setcursor(self, cursor):
		for win in self._subwindows:
			if (win._window_type == HTM):
				if (cursor == ''):
					Htmlex.EndWaitCursor(win._hWnd)
				else:
					Htmlex.BeginWaitCursor(win._hWnd)
			else:
				win.setcursor(cursor)
		self._cursor = cursor


	def newdisplaylist(self, _bgcolor):
		if _bgcolor == ():
			_bgcolor = self._bgcolor
		return _DisplayList(self, _bgcolor)

	def settitle(self, title):
		if self._parent is not toplevel:
			raise error, 'can only settitle at top-level'
		pass

	def getgeometry(self):
		#print "GetGeometry for Window, ", self._title
		return self._sizes

	def pop(self):
		#self._hWnd.MessageBox("POP Window", "Debug", win32con.MB_OK)
		self._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		#print 'Show in pop'
		#self.show()

	def push(self):
		#self._hWnd.MessageBox("PUSH Window", "Debug", win32con.MB_OK)
		self._hWnd.SetWindowPos( win32con.HWND_BOTTOM, (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		#self.hide()

	def setredrawfunc(self, func):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'

	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'
		if event in (ResizeWindow, KeyboardInput, Mouse0Press,
			     Mouse0Release, Mouse1Press, Mouse1Release,
			     Mouse2Press, Mouse2Release, WindowExit):
				 ##Take out WindowExit
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

	def destroy_menu(self):
		pass

	def create_menu(self, list, title = None):
		pass

	def _image_size(self, file):
		if toplevel._size_cache.has_key(file):
			return toplevel._size_cache[file]
		try:
			width, height = imageex.SizeOfImage(file)
		except img.error, arg:
			raise error, arg
		toplevel._size_cache[file] = width, height
		return width, height

	def _convert_coordinates(self, coordinates):
		# convert relative sizes to pixel sizes relative to
		# upper-left corner of the window
		x, y = coordinates[:2]
##		if not (0 <= x <= 1 and 0 <= y <= 1):
##			raise error, 'coordinates out of bounds'
		px = int((self._rect[_WIDTH] - 1) * x + 0.5) + self._rect[_X]
		py = int((self._rect[_HEIGHT] - 1) * y + 0.5) + self._rect[_Y]
		if len(coordinates) == 2:
			return px, py
		w, h = coordinates[2:]
##		if not (0 <= w <= 1 and 0 <= h <= 1 and
##			0 <= x + w <= 1 and 0 <= y + h <= 1):
##			raise error, 'coordinates out of bounds'
		pw = int((self._rect[_WIDTH] - 1) * w + 0.5)
		ph = int((self._rect[_HEIGHT] - 1) * h + 0.5)
		return px, py, pw, ph
		
	def _prepare_image(self, file, crop, scale):
		imageHandle, l, t, r, b = imageex.PrepareImage(self._hWnd, file, scale)
		return imageHandle, l, t, r, b

	def _setcursor_callback(self, params):
		_win_setcursor(self._hWnd, self._cursor)

	def _destroy_callback(self, params):
		try:
			func, arg = self._callbacks[WindowExit]			
		except KeyError:
			pass
		else:
			func(arg, self, WindowExit, None)

	def _expose_callback(self, params):
		if self._parent is None:
			cmifex.BeginPaint(self._hWnd, 0)
			r, g, b = self._bgcolor
			cmifex.SetBGColor(self._hWnd, r, g, b)
			cmifex.EndPaint(self._hWnd, 0)
			return
		if self._redrawfunc is None:
			cmifex.BeginPaint(self._hWnd, 0)					
			if self._window_type != HTM:			
				self._do_expose(self._hWnd)
			cmifex.EndPaint(self._hWnd, 0)
		else:
			self._redrawfunc()			

	def _do_expose(self, hWnd, recursive = 0):
		r, g, b = self._bgcolor
		cmifex.SetBGColor(self._hWnd, r, g, b)		
		#print "Exposed: ", self._title
		if self._active_displist:			
			#self._active_displist.exposerender()	
			self._active_displist._render(hWnd, 1)	
					
	def _resize_callback(self, params):	
		#print "_______Resize Callback: ", self._title
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
		
		#print 'RESIZE FROM', oldWidth, oldHeight, 'TO', width, height
		cmifex.ResizeAllChilds(self._hWnd, width, height, oldWidth, oldHeight)

		#f = open("d:\\tmp\\paint.log", "a")
		#f.write("Window._Resize_Callback %s\n"%self._title)
		#f.close()

		for w in self._subwindows:
			#print "Parent ", self._title, " Windows: ", w, "\n"
			#if w._window_state != HIDDEN:				
			w._do_resize1()

		# call resize callbacks		
		self._do_resize2()
		
		toplevel._setcursor()

		
	def _do_resize2(self):
		try:
			func, arg = self._callbacks[ResizeWindow]			
		except KeyError:
			pass
		else:
			#f = open("d:\\tmp\\paint.log", "a")
			#f.write("Window._Do_Resize2 %s\n"%self._title)
			#f.close()
			func(arg, self, ResizeWindow, None)

		for w in self._subwindows:						
			#if w._window_type != MPEG:
			w._do_resize2()


	def _setcursor(self, cursor = ''):
		if cursor == '':
			cursor = self._cursor
		_win_setcursor(self._hWnd, cursor)

	def _mouseLClick_callback(self, params):
		ev = Mouse0Press
		point = params[5]
		self._do_MouseEvent(self, point, ev)
		for win in self._subwindows:
			if win._window_state != SHOWN:
				self._do_MouseEvent(win, point, ev)
		
	def _do_MouseEvent(self, window, point, ev):				
		func, arg = window._callbacks[ev]
		x, y = point
		disp = window._active_displist
		buttons = []
		if disp:
			if disp._buttons ==[]:
				func(arg, window, ev, (x, y, buttons))
				return
			else:
				for button in disp._buttons:
					if cmifex.ScreenToBox(window._hWnd, point, button._box):
						buttons.append(button)
		func(arg, window, ev, (x, y, buttons))
		
		

class _BareSubWindow:
	def __init__(self, parent, coordinates, transparent, type_channel, defcmap, pixmap):
		px, py, pw, ph = parent._convert_coordinates(coordinates)
		if pw == 0: pw = 1
		if ph == 0: ph = 1	
		self._num = len(parent._subwindows)+1
		self._title = "Child "+ `self._num`+" of " + parent._title 
		self._rect = px, py, pw, ph
		self._sizes = coordinates
		x, y, w, h = coordinates
		if w == 0 or h == 0:
			showmessage('Creating subwindow with zero dimension',
				    type = 'warning')
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
		self._do_init(parent)
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			self._transparent = transparent
		self._topwindow = parent._topwindow

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
		#self._hWnd = cmifex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
		if (type_channel == SINGLE) :
			self._hWnd = cmifex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
		elif (type_channel == HTM) :
			self._hWnd = Htmlex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
		elif (type_channel == TEXT) :
			self._hWnd = textex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
			#self._hWnd = cmifex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
		else :
			print 'UnKnown window type - SINGLE USED AS BACKUP'
			self._hWnd = cmifex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)

		x, y, a, b = self._hWnd.GetWindowRect()
		a, b, width, height = self._hWnd.GetClientRect()
		width = width-12
		#self._placement = x, y, width, height
		self._placement = self._hWnd.GetWindowPlacement()
		r, g, b = self._bgcolor
		cmifex.SetBGColor(self._hWnd, r, g, b)

		#self._event_list = [PAINT, SIZE, LBUTTONDOWN]
		self._event_list = [PAINT, LBUTTONDOWN, SET_CURSOR, WIN_DESTROY]
		self._enable_events()

		#parent._mkclip()
		#if not self._transparent:
		#	self._do_expose(self._region)
		#	if have_pixmap:
		#		x, y, w, h = self._rect
		#		self._gc.SetRegion(self._region)
		#		self._pixmap.CopyArea(self._form, self._gc,
		#				      x, y, w, h, x, y)
		self.show()

	def __repr__(self):
		return '<_BareSubWindow instance at %x>' % id(self)

	def _destroy_callback(self, params):
		try:
			func, arg = self._callbacks[WindowExit]			
		except KeyError:
			pass
		else:
			func(arg, self, WindowExit, None)

	def close(self):
		#self._hWnd.MessageBox("_BareSubWindow %s"%self._title, "Debug", win32con.MB_OK)
		#print "_BareSubWindow.Close %s"%self._title
		parent = self._parent
		self.hide()
		if parent is None:
			return		# already closed
		self._parent = None
		parent._subwindows.remove(self)
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
		#MUADDIB
		#parent._mkclip()
		#parent._do_expose(self._hWnd)
		if hasattr(self, '_pixmap'):
			x, y, w, h = self._rect
			#self._gc.SetRegion(self._region)
			#self._pixmap.CopyArea(self._form, self._gc,
			#		      x, y, w, h, x, y)
			del self._pixmap
		del self._topwindow
		#self._hWnd = None

	def settitle(self, title):
		raise error, 'can only settitle at top-level'

	def getgeometry(self):
		#print "GetGeometry for BareSubWindow, ", self._title
		return self._sizes

	def pop(self):
		#self._hWnd.MessageBox("POP BareSub", "Debug", win32con.MB_OK)
		self._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		#print 'Show in subpop'
		#self.show()
		self._parent.pop()
		return
		parent = self._parent
		# move self to front of _subwindows
		if self is parent._subwindows[0]:
			return		# no-op
		parent._subwindows.remove(self)
		parent._subwindows.insert(0, self)
		# recalculate clipping regions
		#parent._mkclip()
		# draw the window's contents
		if not self._transparent or self._active_displist:
			self._region = None
			#self._do_expose(self._region)
			if hasattr(self, '_pixmap'):
				x, y, w, h = self._rect
				#self._gc.SetRegion(self._region)
				#self._pixmap.CopyArea(self._form, self._gc,
				#		      x, y, w, h, x, y)
		parent.pop()

	def push(self):
		#self._hWnd.MessageBox("PUSH BareSub", "Debug", win32con.MB_OK)
		self._hWnd.SetWindowPos( win32con.HWND_BOTTOM, (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
		#self.hide()
		return
		parent = self._parent
		# move self to end of _subwindows
		if self is parent._subwindows[-1]:
			return		# no-op
		parent._subwindows.remove(self)
		parent._subwindows.append(self)
		# recalculate clipping regions
		#parent._mkclip()
		# draw exposed windows
		for w in self._parent._subwindows:
			if w is not self:
				#w._do_expose(self._region)
				pass
		if hasattr(self, '_pixmap'):
			x, y, w, h = self._rect
		#	self._gc.SetRegion(self._region)
		#	self._pixmap.CopyArea(self._form, self._gc,
		#			      x, y, w, h, x, y)

	def _mkclip(self):
		self._hWnd.MessageBox("BareSunWnd CLip", "Debug", win32con.MB_OK)
		if not self._parent:
			return
		return
		_Window._mkclip(self)
		region = self._clip
		# subtract overlapping siblings
		for w in self._parent._subwindows:
			if w is self:
				break
			#if not w._transparent:
			#	r = Xlib.CreateRegion()
			#	apply(r.UnionRectWithRegion, w._rect)
			#	region.SubtractRegion(r)

	def _do_resize1(self):
		# calculate new size of subwindow after resize
		# close all display lists
		parent = self._parent
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

		#f = open("d:\\tmp\\paint.log", "a")
		#f.write("BareSubWindow._Do_Resize1 %s\n"%self._title)
		#f.close()		
		
			
		#resize all subwindows
		for w in self._subwindows:
			#print 'SUB RESIZED'
			#if w._window_state != HIDDEN:
			w._do_resize1()

class _SubWindow(_BareSubWindow, _Window):
	def __repr__(self):
		return '<_SubWindow instance at %x>' % id(self)


class _DisplayList:
	def __init__(self, window, bgcolor):
		r, g, b = bgcolor
		self._window = window
		window._displists.append(self)
		self._buttons = []
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._linewidth = 1
		#self._gcattr = {'foreground': window._convert_color(self._fgcolor),
		#		'background': window._convert_color(bgcolor),
		#		'line_width': 1}
		self._list = []
		if not window._transparent:
			self._list.append(('clear',))
		self._optimdict = {}
		self._cloneof = None
		self._clonestart = 0
		self._rendered = FALSE
		self._font = None
		self._imagemask = None

	def close(self):
		win = self._window
		#win._hWnd.MessageBox("DisplayList.Close!", "Debug", MB_OK)
		#print "DisplayList.Close!"
		if win is None:
			return
		#win.hide()		
		for b in self._buttons[:]:
			b.close()
		win._displists.remove(self)
		self._window = None
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			win._do_expose(None)
			#if hasattr(win, '_pixmap'):
			#	x, y, w, h = win._rect
			#	win._gc.SetRegion(win._region)
			#	win._pixmap.CopyArea(win._form, win._gc,
			#			     x, y, w, h, x, y)
		del self._cloneof
		try:
			del self._clonedata
		except AttributeError:
			pass
		del self._optimdict
		del self._list
		del self._buttons
		del self._font
		del self._imagemask

	def is_closed(self):
		return self._window is None

	def clone(self):
		w = self._window
		new = _DisplayList(w, self._bgcolor)
		# copy all instance variables
		new._list = self._list[:]
		new._font = self._font
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
			new._clonedata = self._fgcolor, self._font
			new._imagemask = self._imagemask
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def render_now(self):
		self.render()		
	
	def render(self):
		window = self._window
		#print "-----Render ____________ ", window._title		
		#f = open("d:\\tmp\\paint.log", "a")
		#f.write("Render %s\n"%self._window._title)
		#f.close()

		#import pdb
		#pdb.set_trace()
		for b in self._buttons:
			b._highlighted = 0	
		# draw our bit
		self._render(window._hWnd, 0)
		# now draw transparent windows that lie on top of us
		if window._topwindow is not window:
			i = window._parent._subwindows.index(window)
			windows = window._parent._subwindows[:i]
			windows.reverse()
			#for w in windows:
			#	if w._transparent:
			#		w._do_expose(window._hWnd, 1)
		# finally, re-highlight window
		if window._showing:
			window.showwindow()

		if hasattr(window, '_pixmap'):
			x, y, width, height = window._rect
			#window._pixmap.CopyArea(window._form, window._gc,
			#			x, y, width, height, x, y)		
		window._forcePaint()
				
	def _render(self, hWnd, show):
		#f = open("d:\\tmp\\paint.log", "a")
		#f.write("DisplayList._Render %s, Show %d\n"%(self._window._title, show))
		#f.close()

		self._rendered = TRUE
		w = self._window
		clonestart = self._clonestart
		#print "_RENDER"
		#print "CLONE: ", self._cloneof
		if not self._cloneof or self._cloneof is not w._active_displist:
			clonestart = 0
		if w._active_displist and self is not w._active_displist and clonestart == 0:
			w._active_displist = None

		if clonestart > 0:
			fg, font = self._clonedata			
		handle = self._list[1]
		w._active_displist = self
		if show==1:
			for i in range(clonestart, len(self._list)):
				self._do_render(self._list[i], hWnd)
		

	def _do_render(self, entry, hWnd):
		#print "--____DO____Render ____________ ", self._window._title
		cmd = entry[0]
		#win32ui.MessageBox(cmd, "Test", win32con.MB_OK)
		#print "Rendering ", self._window._title
		w = self._window
		if cmd == 'clear':
			pass
			#fg = gc.foreground
			#gc.foreground = gc.background
			#apply(gc.FillRectangle, w._rect)
			#gc.foreground = fg
		elif cmd == 'fg':
			#gc.foreground = entry[1]
			pass
		elif cmd == 'image':		
			mask = entry[1]
			r, g, b = w._bgcolor
			imageex.PutImage(w._hWnd, entry[2], r, g, b, w._scale)
#			if mask:
#				# mask is clip mask for image
#				width, height = w._topwindow._rect[2:]
#				p = w._form.CreatePixmap(width, height, 1)
#				g = p.CreateGC({'foreground': 0})
#				g.FillRectangle(0, 0, width, height)
#				g.SetRegion(region)
#				g.foreground = 1
#				g.FillRectangle(0, 0, width, height)
#				apply(g.PutImage, (mask,) + entry[3:])
#				gc.SetClipMask(p)
#			else:
#				gc.SetRegion(region)
#			if mask:
#				gc.SetRegion(region)
		elif cmd == 'line':
			#fg = gc.foreground
			#gc.foreground = entry[1]
			points = entry[2]
			x0, y0 = points[0]
			for x, y in points[1:]:
				#gc.DrawLine(x0, y0, x, y)
				x0, y0 = x, y
			#gc.foreground = fg
		elif cmd == 'box':
			mcolor = 255, 0, 0			
			cmifex.DrawRectangle(w._hWnd, entry[1], mcolor)		
			pass
		elif cmd == 'fbox':
			#fg = gc.foreground
			#gc.foreground = entry[1]
			#apply(gc.FillRectangle, entry[2])
			#gc.foreground = fg
			pass
		elif cmd == 'font':
			#gc.SetFont(entry[1])
			pass
		elif cmd == 'text':
			#print "Text at :", entry[3:]
			fontname = entry[1]
			pointsize = entry[2]
			id, str = entry[3:]
			#fontColor = 0, 0, 0
			fontColor = w._fgcolor
			textex.PutText(id, w._hWnd, str, fontname, pointsize, TRANSPARENT, self._bgcolor, fontColor,w._align)
			#textex.PutText(id, w._hWnd, str, fontname, pointsize, TRANSPARENT, self._bgcolor, fontColor)
			self.update_boxes(w._hWnd)
			pass
		elif cmd == 'linewidth':
			#gc.line_width = entry[1]
			pass
		#w.show()



	def update_boxes(self, hWnd):
		print "in update_boxes"
		ydif = textex.GetScrollPos(hWnd)
		if ydif == 0:
			return
		textex.ClearXY(hWnd)
		print "ydif-->", ydif
		#dif = oldscrollpos-scrollpos
		#print "self._buttons[0]->>>", self._buttons[0]
		if self._buttons==[]:
			return
		button = 0
		for i in range(0, len(self._list)):
			l = self._list[i]
			#print "before buttons-->", l
			if l[0] == 'box':				
				tuple = l[1]
				x1 = tuple[0]
				y1 = tuple[1]+ydif
				x2 = tuple[2]
				y2 = tuple[3]+ydif
				temptuple = (x1,y1,x2,y2)
				l = ('box', temptuple)
				self._list[i] = l
				#print tuple
				#if len(self._buttons)<=button:
				#	self._buttons.append('box', (x1,y1,x2,y2))
				self._buttons[button]._setcoords(x1,y1,x2,y2)
				button = button+1
		#print "out of update_boxes"


	def fgcolor(self, color):
		r, g, b = color

	def newbutton(self, coordinates):
		return _Button(self, coordinates)

	
	def old_display_image_from_file(self, file, crop = (0,0,0,0), scale = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, left, top, right, bottom = w._prepare_image(file, crop, scale)
		mask, src_x, src_y  = 0, 0, 0
		dest_x, dest_y, width, height = left, top, right-left, bottom-top
		self._list.append('image', mask, image, src_x, src_y,
				  dest_x, dest_y, width, height)
		#self._optimize(2)
		#Assume that the image is stretched to the window so there is no conversion needed
		#x, y, w, h = 0, 0, 1, 1
		#return x, y, w, h
		x, y, w, h = w._rect
		a, b = float(dest_x) / w, float(dest_y) / h,
		c, d = float(width) / w, float(height) / h
		print "--------- ", a, b, c, d
		return a, b, c, d

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, l, t, r, b = w._prepare_image(file, crop, scale)	
		dest_x = l
		dest_y = t
		width = r-l
		height = b-t
		mask, src_x, src_y = 0, 0, 0
		#dest_x, dest_y, width, height = w._rect
		self._list.append('image', mask, image, src_x, src_y,					
				  dest_x, dest_y, width, height)
		#self._optimize(2)
		#Assume that the image is stretched to the window so there is no conversion needed
		#x, y, w, h = 0, 0, 1, 1
		#return x, y, w, h
		x, y, w, h = w._rect
		#a1 = float(dest_x - x) / w
		#b1 = float(dest_y - y) / h
		a1 = float(dest_x) / w
		b1 = float(dest_y) / h
		c1 = float(width) / w
		d1 = float(height) / h
		return a1, b1, c1, d1

	def _resize_image_buttons(self):
		type = self._list[1]
		if type[0]!='image':
			return
		

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		#color = w._convert_color(color)
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append('line', color, p)

	def drawbox(self, coordinates):
		#print "DrawBox Before: ", coordinates
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		#print "DrawBox After: ", coordinates
		#print "Window Rect: ", self._window._rect
		X, Y, W, H = self._window._rect
		x, y, w, h = coordinates 
		x = x - X
		y = y - Y
		coordinates = x, y, w, h
		self._list.append('box', coordinates)	
		#self._optimize()
		return coordinates

	def drawfbox(self, color, coordinates):	
		if self._rendered:
			raise error, 'displaylist already rendered'
		#6/2A
		#self._list.append('fbox', self._window._convert_color(color),
		#		self._window._convert_coordinates(coordinates))
		self._list.append('fbox', None,	self._window._convert_coordinates(coordinates))
		#self._optimize(1)

	def usefont(self, fontobj):
		self._font = fontobj
		return self.baseline(), self.fontheight(), self.pointsize()

	def setfont(self, font, size):
		jnk = self.usefont(findfont(font, size))
		return jnk

	def fitfont(self, fontname, str, margin = 0):
		return self.usefont(findfont(fontname, 10))

	def baseline(self):
		return self._font.baseline() * self._window._vfactor

	def fontheight(self):
		return self._font.fontheight() * self._window._vfactor

	def pointsize(self):
		return self._font.pointsize()

	def strsize(self, str):
		width, height = self._font.strsize(str)
		return float(width) * self._window._hfactor, \
		       float(height) * self._window._vfactor

	def setpos(self, x, y):
		self._curpos = x, y
		self._xpos = x

	def old_writestr(self, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		base = self.baseline()
		height = self.fontheight()
		strlist = string.splitfields(str, '\n')
		oldx, oldy = x, y = self._curpos
		if len(strlist) > 1 and oldx > self._xpos:
			oldx = self._xpos
		oldy = oldy - base
		maxx = oldx
		for str in strlist:
			x0, y0 = w._convert_coordinates((x, y))
			list.append('text', x0, y0, str)
			self._curpos = x + float(12*len(str)) / w._rect[_WIDTH], y
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, newy - oldy + height - base
	
	def writeText(self, font, size, id, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		list.append('text', font, size, id, str)	

	def _optimize(self, ignore = []):
		if type(ignore) is IntType:
			ignore = [ignore]
		entry = self._list[-1]
		x = []
		for i in range(len(entry)):
			if i not in ignore:
				z = entry[i]
				if type(z) is ListType:
					z = tuple(z)
				x.append(z)
		x = tuple(x)
		try:
			i = self._optimdict[x]
		except KeyError:
			pass
		else:
			del self._list[i]
			del self._optimdict[x]
			if i < self._clonestart:
				self._clonestart = self._clonestart - 1
			for key, val in self._optimdict.items():
				if val > i:
					self._optimdict[key] = val - 1
		self._optimdict[x] = len(self._list) - 1


class _Button:
	def __init__(self, dispobj, coordinates):		
		self._dispobj = dispobj
		dispobj._buttons.append(self)
		window = dispobj._window
		self._coordinates = coordinates
		x, y, w, h = coordinates
		self._corners = x, y, x + w, y + h
		self._box = 0, 0, 0, 0
		self._color = self._hicolor = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		self._newdispobj = None
		self._highlighted = 0
		if self._color == dispobj._bgcolor:
			return
		self._box = dispobj.drawbox(self._coordinates)

	def _resize(self, xfactor, yfactor):
		wnd = self._dispobj._window._hWnd
		list = self._dispobj._list[1]
		if list[0]!='image':
			return
		#wnd.MessageBox("ButtonResize", "Debug", win32con.MB_OK)
		x, y, z, k = self._box
		x = (int)(float(x)*xfactor+0.5)
		y = (int)(float(y)*yfactor+0.5)
		z = (int)(float(z)*xfactor+0.5)
		k = (int)(float(k)*yfactor+0.5)
		self._box = x, y, z, k
	
	def _setcoords(self, x, y, w, h):
		self._box = x, y, w, h

	def close(self):
		wnd = self._dispobj._window._hWnd
		#print "Buttons.Close!"
		if self._dispobj is None:
			return
		self._dispobj._buttons.remove(self)
		self._dispobj = None
		if self._newdispobj:
			self._newdispobj.close()
			self._newdispobj = None

	def is_closed(self):
		return self._dispobj is None

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, color):
		self._hicolor = color

	def highlight(self):
		dispobj = self._dispobj
		if dispobj is None:
			return
		window = dispobj._window
		if window._active_displist is not dispobj:
			raise error, 'can only highlight rendered button'
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		self._highlighted = 1
		self._do_highlight()
#		if hasattr(window, '_pixmap'):
#			x, y, w, h = window._rect
#			window._pixmap.CopyArea(window._form, window._gc,
#						x, y, w, h, x, y)
#		toplevel._main.UpdateDisplay()

	def _do_highlight(self):
		window = self._dispobj._window
	#	gc = window._gc
	#	gc.foreground = window._convert_color(self._hicolor)
	#	gc.line_width = self._hiwidth
	#	gc.SetRegion(window._clip)
	#	apply(gc.DrawRectangle, window._convert_coordinates(self._coordinates))

	def unhighlight(self):
		dispobj = self._dispobj
		if dispobj is None:
			return
		window = dispobj._window
		if window._active_displist is not dispobj:
			return
		if not self._highlighted:
			return
		self._highlighted = 0
		# calculate region to redisplay
		x, y, w, h = window._convert_coordinates(self._coordinates)
		lw = self._hiwidth / 2
	#	r = Xlib.CreateRegion()
	#	r.UnionRectWithRegion(x - lw, y - lw,
	#			      w + 2*lw + 1, h + 2*lw + 1)
	#	r1 = Xlib.CreateRegion()
	#	r1.UnionRectWithRegion(x + lw + 1, y + lw + 1,
	#			       w - 2*lw - 1, h - 2*lw - 1)
	#	r.SubtractRegion(r1)
	#	window._do_expose(r)
	#	if hasattr(window, '_pixmap'):
	#		x, y, w, h = window._rect
	#		window._pixmap.CopyArea(window._form, window._gc,
	#					x, y, w, h, x, y)
	#	toplevel._main.UpdateDisplay()

	def _inside(self, x, y):
		# return 1 if the given coordinates fall within the button
		if (self._corners[0] <= x <= self._corners[2]) and \
			  (self._corners[1] <= y <= self._corners[3]):
			return TRUE
		else:
			return FALSE

_pt2mm = 25.4 / 96			# 1 inch == 96 points == 25.4 mm
							# original 72
_fontmap = {
	  'Times-Roman': 'Times New Roman',
	  'Times-Italic': 'Times New Roman',
	  'Times-Bold': 'Times New Roman',
	  'Utopia': 'System',
	  'Utopia-Italic': 'System',
	  'Utopia-Bold': 'System',
	  'Palatino': 'Century Schoolbook',
	  'Palatino-Italic': 'Century Schoolbook',
	  'Palatino-Bold': 'Century Schoolbook',
	  'Helvetica': 'Arial',
	  'Helvetica-Bold': 'Arial',
	  'Helvetica-Oblique': 'Arial',
	  'Courier': 'Courier New',
	  'Courier-Bold': 'Courier New',
	  'Courier-Oblique': 'Courier New',
	  'Courier-Bold-Oblique': 'Courier New',
	  'Greek': 'Arial',
	  'Greek-Italic': 'Arial',
	  }
fonts = _fontmap.keys()

_FOUNDRY = 1
_FONT_FAMILY = 2
_WEIGHT = 3
_SLANT = 4
_SET_WIDTH = 5
_PIXELS = 7
_POINTS = 8
_RES_X = 9
_RES_Y = 10
_SPACING = 11
_AVG_WIDTH = 12
_REGISTRY = 13
_ENCODING = 14

def _parsefontname(fontname):
	list = string.splitfields(fontname, '-')
	if len(list) != 15:
		raise error, 'fontname not well-formed'
	return list

def _makefontname(font):
	return string.joinfields(font, '-')

_fontcache = {}

def findfont(fontname, pointsize):
	key = fontname + `pointsize`
	fontobj = _Font(fontname, pointsize)
	_fontcache[key] = fontobj
	return fontobj	
	###########
	key = fontname + `pointsize`
	try:
		return _fontcache[key]
	except KeyError:
		pass
	try:
		fontnames = _fontmap[fontname]
	except KeyError:
		raise error, 'Unknown font ' + `fontname`
	fontname = 'Arial'
	pointsize = 12
	pixelsize = pointsize * toplevel._dpi_y / 96.0
	bestsize = 0
	fontobj = _Font(fontname, pointsize)
	_fontcache[key] = fontobj
	return fontobj	
	
class _Font:
	def __init__(self, fontname, pointsize):
		self._height, self._ascent, self._maxWidth = cmifex.GetTextMetrics()
		self._pointsize = pointsize
		self._fontname = fontname

	def close(self):
		self._font = None

	def is_closed(self):
		return self._font is None

	def strsize(self, str):
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * (self._height)
		for str in strlist:
			#width = cmifex.GetTextWidth(str)
			width = len(str)*self._maxWidth
			if width > maxwidth:
				maxwidth = width
		return float(maxwidth) / toplevel._hmm2pxl, \
		       float(maxheight) / toplevel._vmm2pxl

	def baseline(self):
		return float(self._ascent) / toplevel._vmm2pxl

	def fontheight(self):
		return float(self._height) / toplevel._vmm2pxl

	def pointsize(self):
		return self._pointsize

class showmessage:
	def __init__(self, text, type = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message'):
		pass

	def close(self):
		pass

class Dialog:
	def __init__(self, list, title = None, prompt = None, grab = 1,
		     vertical = 1):
		_do_init(list, title = None, prompt = None, grab = 1, vertical = 1)

	def _do_init(self, list, title = None, prompt = None, grab = 1,
		     vertical = 1):
		self._dialog = dialog.Dialog(MainDialogRC.IDD_PLAYER, dll)
		self.counter=0
		for entry in list:
			if entry is None:
				continue
			if type(entry) is TupleType:
				label, callback = entry[:2]
			else:
				label, callback = entry, None
			if callback and type(callback) is TupleType:
				callback_func, callback_arg = callback
			else:
				callback_func = callback
			if callback_func:
				if label == 'Play':
					self._dialog.HookCommand(callback_func, MainDialogRC.IDC_PLAY)	
				if label == 'Stop':
					self._dialog.HookCommand(callback_func, MainDialogRC.IDC_STOP)	
				if label == 'Pause':
					self._dialog.HookCommand(callback_func, MainDialogRC.IDC_PAUSE)	
				if label == 'Quit':
					self._dialog.HookCommand(callback_func, MainDialogRC.IDC_EXIT)	
			## Use a local Callback to change the cursor and then check who called to 
			## activate actual callback
		self._menu = None
		self.edit=None	

	def show(self):
		#self._dialog.DoModal()
		self._dialog.CreateWindow()
		self._dialog.ShowWindow()

	def close(self):
		pass

	def destroy_menu(self):
		pass

	def create_menu(self, list, title = None):
		pass

	def getbutton(self, button):
		return set

	def setbutton(self, button, onoff = 1):
		pass

class MainDialog(Dialog):
	def __init__(self, list, title = None, prompt = None, grab = 1,
		     vertical = 1):
		self._do_init(list, title = None, prompt = None, grab = 1,
		     vertical = 1)
		toplevel.MainDialog = self

def multchoice(prompt, list, defindex):
	return defindex

def beep():
	import sys
	sys.stderr.write('\7')

def _win_setcursor(form, cursor):
	if cursor != '':
		print "+++++++++++++++: Cursor: ", cursor
	if cursor!='watch' and cursor!='start' and cursor!='hand':
		cursor = ''
	cmifex.SetCursor(win32Cursors[cursor])
	return
	if cursor == 'watch':
		form.DefineCursor(toplevel._watchcursor)
	elif cursor == 'channel':
		form.DefineCursor(toplevel._channelcursor)
	elif cursor == 'link':
		form.DefineCursor(toplevel._linkcursor)
	elif cursor == 'stop':
		form.DefineCursor(toplevel._stopcursor)
	elif cursor == '':
		form.UndefineCursor()
	else:
		raise error, 'unknown cursor glyph'

