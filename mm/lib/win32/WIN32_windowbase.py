import cmifex, timerex, imageex, textex, Htmlex, cmifex2
import win32ui, win32con, win32api
import MainDialogRC
import string

from types import *

Continue = 'Continue'

error = 'windowinterface.error'
FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2
WM_MAINLOOP = 200


UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2

RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH = 0, 1, 2

Version = 'WIN32_DBG'
toplevel = None

_size_cache = {}

pseudo_id = 100

a_window=None

[_X, _Y, _WIDTH, _HEIGHT] = range(4)
[PAINT, SIZE, LBUTTONDOWN, MM_MCI_NOTIFY, SET_CURSOR, WIN_DESTROY, LBUTTONUP] = range(7)
[OPAQUE, TRANSPARENT] = range(2)
[HIDDEN, SHOWN] = range(2)
[ARROW, WAIT, HAND, START, G_HAND, U_STRECH,
D_STRECH, L_STRECH, R_STRECH, UL_STRECH,
UR_STRECH, DR_STRECH, DL_STRECH, PUT] = range(14)

[SINGLE, HTM, TEXT, MPEG] = range(4)

win32Cursors = { 'hand':HAND, 'watch':WAIT, '':ARROW, 'start':START,
				'g_hand':G_HAND, 'ustrech':U_STRECH, 'dstrech':D_STRECH,
				'lstrech':L_STRECH, 'rstrech':R_STRECH, 'ulstrech':UL_STRECH,
				'urstrech':UR_STRECH, 'drstrech':DR_STRECH,
				'dlstrech':DL_STRECH, 'channel':PUT }

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

		#indicates wheather sr-events are being served by the timer interface
		self.serving = 0

	def forcePaint(self):
		for w in self._subwindows:
			w._forcePaint()

	def close(self):
##		raise 'kaboo kaboo'
##		self._timerWnd.MessageBox("Toplevel.Close!", "Debug", win32con.MB_OK)
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		self._closecallbacks = []
		self._subwindows = []

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	# in the following calls UNITS are ignored
	def newwindow(self, x, y, w, h, title, visible_channel, type_channel, units, pixmap = 0, menubar = None, canvassize = None):
		return _Window(self, x, y, w, h, title, visible_channel, type_channel, 0, pixmap, 0, units, menubar, canvassize)

	def newcmwindow(self, x, y, w, h, title, visible_channel, type_channel, units, pixmap = 0, menubar = None, canvassize = None):
		return _Window(self, x, y, w, h, title, visible_channel, type_channel, 1, pixmap, 0, units, menubar, canvassize)

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
		#self._inputWnd.MessageBox("Show Toplevel", "Debug", win32con.MB_OK)
		for w in self._subwindows:
			w.show()

	def hide(self):
		self._inputWnd.MessageBox("Hide Toplevel", "Debug", win32con.MB_OK)
		for w in self._subwindows:
			w.hide()


	def usewindowlock(self, lock):
		pass

	def mainloop(self):
		# new lines
		if len(self._subwindows) == 1:
			self.show()
		# end of new lines
		self._timerWnd.PostMessage(WM_MAINLOOP, 0, 0)

		# Main Dialog object has been created, on player's
		# module demand if we are in the player
		# It is time to show the main dialog, but first check
		# that the player is running, not the editor
		if self.MainDialog <> None :
			self.MainDialog.show()



	def serve_events(self):

		if (self.serving == 0):
			return

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
		print 'message callback called'
		self.serving = 1
		self.serve_events()

	def _stopserve_callback(self, params):
		self.serving = 0


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
			try:
				t, cb, tid = self._timers[i]
				if tid == id:
					del self._timers[i]
					if i < len(self._timers):
						tt, cb, tid = self._timers[i]
						self._timers[i] = (tt + t, cb, tid)
			except IndexError:
				pass
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
		return color
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


	def getscreensize(self):
		"""Return screen size in pixels"""
		return self._screenwidth, self._screenheight

	def getscreendepth(self):
		"""Return screen depth"""
		return 8 #self._visual.depth



class _Window:
	def __init__(self, parent, x, y, w, h, title, visible, type_channel, defcmap = 0, pixmap = 0,
			transparent = 0, units = UNIT_MM, menubar = None, canvassize = None):
		#parent._subwindows.append(self)
		self._do_init(parent)
		self._last_paint_time = 0
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
		#self._depth = self._visual.depth
		self._depth = 8
		# convert mm to pixels
		if x==None: x=0
		if y==None: y=0
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
			cmifex.SetScrollInfo(self._hWnd,win32con.SB_VERT,0,0,0,0,1)
			cmifex.SetScrollInfo(self._hWnd,win32con.SB_HORZ,0,0,0,0,1)
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
			cmifex.SetScrollInfo(self._hWnd,win32con.SB_VERT,0,0,0,0,1)
			cmifex.SetScrollInfo(self._hWnd,win32con.SB_HORZ,0,0,0,0,1)

		#x, y, a, b = self._hWnd.GetWindowRect()
		a, b, w, h = self._hWnd.GetClientRect()
		#r, g, b = self._bgcolor
		#cmifex.SetBGColor(self._hWnd, r, g, b)

		try:
			self._hfactor = parent._hfactor / (w/toplevel._hmm2pxl)
			self._vfactor = parent._vfactor / (h/toplevel._vmm2pxl)
		except ZeroDivisionError:
			#rare event! prevent a crach!!
			self._hfactor = self._vfactor = 1.0
		self._rect = 0, 0, w, h

		#self._placement = x, y, width, height
		self._placement = self._hWnd.GetWindowPlacement()
		#self._expose_callback(100)
		self._event_list = [PAINT, SIZE, LBUTTONDOWN, SET_CURSOR, WIN_DESTROY, LBUTTONUP]
		self._enable_events()
		self._menu = None
		self._canv = None
		if canvassize is not None:
			width, height = canvassize
			# convert to pixels
			if units == UNIT_MM:
				width = int(float(width) * toplevel._hmm2pxl + 0.5)
				height = int(float(height) * toplevel._vmm2pxl + 0.5)
			elif units == UNIT_SCREEN:
				width = int(float(width) * toplevel._screenwidth + 0.5)
				height = int(float(height) * toplevel._screenheight + 0.5)
			elif units == UNIT_PXL:
				width = int(width)
				height = int(height)
			self._canv = (0, 0, width, height)
			print "self._canv--->", self._canv, self._rect

		if menubar is not None:
			self.create_menu(menubar)
		if visible:
			self._hWnd.ShowWindow(win32con.SW_SHOW)

	def _forcePaint(self):
		#print "@@@@: ", self._title, self._hWnd
		self._hWnd.InvalidateRect()
		for w in self._subwindows:
			w._forcePaint()

	def _rdblclk_callback(self, params):
		#try:
		#	from windowinterface import _in_create_box
		#except ImportError:
		#	_in_create_box = None
		#	pass
		#if _in_create_box != None:
		#	self._hWnd.ReleaseCapture()
		#else:
			print "\n------------------RDBLCLK--------------\n"
			#print self._cbld
			#xpos, ypos = params[5]
			self._do_expose(self._hWnd)
			xpos = win32api.LOWORD(params[3])
			ypos = win32api.HIWORD(params[3])
			if self._menu:
				self._do_expose(self._hWnd)
				id = cmifex2.FloatMenu(self._hWnd, self._menu, xpos, ypos)
				print "id = ", id
				if self._cbld.has_key(id) :
					callback = self._cbld[id]
					apply(callback[0], callback[1])
			self._hWnd.ReleaseCapture()


	#def _focus_callback(self, params):
	#	self._do_expose(self._hWnd)


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


	def _enable_events(self):
		#self._hWnd.HookMessage(self._rdblclk_callback, win32con.WM_RBUTTONDBLCLK)
		self._hWnd.HookMessage(self._rdblclk_callback, win32con.WM_RBUTTONDOWN)
		#self._hWnd.HookMessage(self._focus_callback, win32con.WM_SETFOCUS)
		self._hWnd.HookMessage(self._mouseDBLClick_callback, win32con.WM_LBUTTONDBLCLK)
		for event in self._event_list:
			if event == PAINT:
				self._hWnd.HookMessage(self._expose_callback, win32con.WM_PAINT)
			if event == SIZE:
				self._hWnd.HookMessage(self._resize_callback, win32con.WM_SIZE)
			if event == LBUTTONDOWN:
				self._hWnd.HookMessage(self._mouseLClick_callback, win32con.WM_LBUTTONDOWN)
			if event == LBUTTONUP:
				#pass
				self._hWnd.HookMessage(self._mouseLButtonUp_callback, win32con.WM_LBUTTONUP)
			if event == SET_CURSOR:
				self._hWnd.HookMessage(self._setcursor_callback, win32con.WM_MOUSEMOVE)
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
		self._old_callbacks = {}
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
			self.pop()

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
		if self._hWnd :
			self.destroy_menu()
			self._hWnd.DestroyWindow()
		del self._topwindow
		self._hWnd = None

	def is_closed(self):
		return self._parent is None

	def newwindow(self, coordinates, transparent = 0, type_channel, pixmap = 0, z = 0):
		win = _SubWindow(self, coordinates, transparent, type_channel, 0, pixmap, z)
		win._window_state = HIDDEN
		return win

	def newcwindow(self, coordinates, transparent = 0, type_channel, pixmap = 0):
		win = _SubWindow(self, coordinates, transparent, type_channel, 1, pixmap)
		win._window_state = HIDDEN
		return win

	def showwindow(self):
		print "Highlight Show the window"
		self._showing = 1
		x, y, w, h = self._hWnd.GetClientRect()
		cmifex.DrawRectangle(self._hWnd, (x, y, w, h), (255,0,0), " ")

	def dontshowwindow(self):
		print "Don't highlight show the window"
		if self._showing:
			self._showing = 0
			x, y, w, h = self._hWnd.GetClientRect()
			cmifex.DrawRectangle(self._hWnd, (x, y, w, h), self._bgcolor, " ")


	def _convert_color(self, color):
		#self._hWnd.MessageBox("convert_color", "Debug", win32con.MB_OK)
		return color #self._parent._convert_color(color, 0)

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
		_win_setcursor(self._hWnd, cursor)
		for win in self._subwindows:
			if (win._window_type == HTM):
				if (cursor == ''):
					Htmlex.EndWaitCursor(win._hWnd)
				else:
					Htmlex.BeginWaitCursor(win._hWnd)
			else:
				win.setcursor(cursor)
		self._cursor = cursor

	def newdisplaylist(self, bgcolor = None):
		if bgcolor is None:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)

	def settitle(self, title):
		if self._parent is not toplevel:
			raise error, 'can only settitle at top-level'
		if hasattr(self, '_hWnd'):
			if self._hWnd:
				self._hWnd.SetWindowText(title)

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
		#rect = (x, y, w, h)
		#return rect
		#return self._sizes

	def setcanvassize(self, code):
		pass



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
#		if self._menu:
#			self._menu.DestroyWidget()
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
			_create_menu(float, list, 1, self._cbld,
					self._accelerators)

		self._hWnd.HookAllKeyStrokes(self._char_callback)
		self._menu = menu
#		pass


	def _char_callback(self, params):
		#try:
		#	from windowinterface import _in_create_box
		#except ImportError:
		#	_in_create_box = None
		#	pass
		#if _in_create_box == None:
			if hasattr(self,'_accelerators'):
				#print params
				#print self._accelerators
				key = chr(params)
				#print "key-->", key
				if self._accelerators.has_key(key):
					func, arg = self._accelerators[key]
					apply(func,arg)


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

	def _prepare_image(self, file, crop, scale, center, transp = -1):
		imageHandle, l, t, r, b = imageex.PrepareImage(self._hWnd, file, scale, center,transp)
		return imageHandle, l, t, r, b

	def _setcursor_callback(self, params):
		if self._cursor == '':
			disp = self._active_displist
			buttons = []
			point = params[5]
			found = 0
			if disp:
				for button in disp._buttons:
					if cmifex.ScreenToBox(self._hWnd, point, button._box):
						_win_setcursor(self._hWnd, 'hand')
						found = 1
						break
			if not found:
				_win_setcursor(self._hWnd, '')
		else:
			_win_setcursor(self._hWnd, self._cursor)

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

	def _expose_callback(self, params):
		if self._last_paint_time == params[4] and params[4]!=0:
			return
		else:
			if params[4]!=0 and params[4]-self._last_paint_time<50:
				return
			self._last_paint_time = params[4]
			#print self._title, "-->" , params
		if self._parent is None:
			cmifex.BeginPaint(self._hWnd, 0)
			#r, g, b = self._bgcolor
			#cmifex.SetBGColor(self._hWnd, r, g, b)
			cmifex.FillRectangle(self._hWnd,self._hWnd.GetClientRect(),self._bgcolor)
			cmifex.EndPaint(self._hWnd, 0)
			return
		if self._redrawfunc is None:
			cmifex.BeginPaint(self._hWnd, 0)
			if (self._window_type != HTM) or (self._hWnd.GetWindow(win32con.GW_CHILD)==None):
				if params[3]!=1:
					self._do_expose(self._hWnd)
			cmifex.EndPaint(self._hWnd, 0)
			if self._topwindow is not self and self._transparent != 1 and self._active_displist!=None:
				i = self._parent._subwindows.index(self)
				windows = self._parent._subwindows[:i]
				#windows.reverse()
				for w in windows:
					if w._active_displist!=None and w._transparent == 1 and w != self:
						#w._forcePaint()
						#w._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
						rect1 = self._hWnd.GetClientRect()
						rect2 = self._hWnd.ClientToScreen(rect1)
						rect2 = w._hWnd.ScreenToClient(rect2)
						rect1 = w._hWnd.GetClientRect()
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
						#print "rect1, rect2 --->", w._title, "-->", rect1, self._title, "-->", rect2
						#print self._title, "-->", self._active_displist._list
						#w._do_expose(w._hWnd, 1)
						w._hWnd.PostMessage(win32con.WM_PAINT)
					#elif w._z > self._z and w._active_displist!=None:
					#	#w._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
					#	w._do_expose(w._hWnd, 1)
			elif self._topwindow is self and self._transparent != 1:
				windows = self._subwindows[:]
				windows.reverse()
				for w in windows:
					if w._active_displist!=None:
						#w._forcePaint()
						#w._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
						#w._do_expose(w._hWnd, 1)
						w._hWnd.PostMessage(win32con.WM_PAINT)
		else:
			self._redrawfunc()

	def _do_expose(self, hWnd, recursive = 0):
		#r, g, b = self._bgcolor
		#cmifex.SetBGColor(self._hWnd, r, g, b)

		#print "Exposed: ", self._title
		if self._active_displist:
			#self._active_displist.exposerender()
			self._active_displist._render(hWnd, 1)
		else:
			if self._transparent == 0:
				cmifex.FillRectangle(self._hWnd,self._hWnd.GetClientRect(),self._bgcolor)
		if self._showing:
			self.showwindow()

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

		toplevel._setcursor('')


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
		#try:
		#	from windowinterface import _in_create_box
		#except ImportError:
		#	_in_create_box = None
		#	pass
		#if _in_create_box == None or _in_create_box._hWnd== self._hWnd:
			print 'MOUSE LBUTTON CLICKED:'
			ev = Mouse0Press
			#convert from client to pixel coordinates
			point = params[5]
			#x, y = self._inverse_coordinates(point)
			self._do_MouseEvent(self, point, ev)
			#for win in self._subwindows:
			#	if win._window_state != SHOWN:
			#		self._do_MouseEvent(win, point, ev)


	def _mouseLButtonUp_callback(self, params):
		ev = Mouse0Release
		print 'BUTTON UP parameters:'
		#
		#point = params[5]
		px, py = params[5]
		point = (px, py)
		print point
		self._do_MouseEvent(self, point, ev)
		#for win in self._subwindows:
		#	if win._window_state != SHOWN:
		#		self._do_MouseEvent(win, point, ev)



	def _do_MouseEvent(self, window, point, ev):
		print 'Callbacks for the window : '
		print window._callbacks
		print ev
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



class _BareSubWindow:
	def __init__(self, parent, coordinates, transparent, type_channel, defcmap, pixmap,z):
		if z < 0:
			raise error, 'invalid z argument'
		self._last_paint_time = 0
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
		#self._hWnd = cmifex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
		if (type_channel == SINGLE) :
			self._hWnd = cmifex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
		elif (type_channel == HTM) :
			self._hWnd = Htmlex.CreateChildWindow(self._title, parent._hWnd, px, py, pw, ph)
			print 'HTM clild created'
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
		#r, g, b = self._bgcolor
		#cmifex.SetBGColor(self._hWnd, r, g, b)

		#self._event_list = [PAINT, SIZE, LBUTTONDOWN]
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

	def __repr__(self):
		return '<_BareSubWindow instance at %x>' % id(self)

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
		#self._hWnd.MessageBox("_BareSubWindow %s"%self._title, "Debug", win32con.MB_OK)
		#print "_BareSubWindow.Close %s"%self._title
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

		#rect = (x, y, w, h)
		#return rect
		#return self._sizes

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

		ind = parent._subwindows.index(self)
		if ind != 0: #len(parent._subwindows)-1:
			self._hWnd.SetWindowPos(parent._subwindows[ind-1]._hWnd.GetSafeHwnd(), (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
		else:
			self._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)

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
		#print "in do_resize1 " , parent , self
		#print "in do_resize1 " , self._sizes
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
		self._curfg = window._fgcolor
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._linewidth = 1
		#self._gcattr = {'foreground': window._convert_color(self._fgcolor),
		#		'background': window._convert_color(bgcolor),
		#		'line_width': 1}
		self._list = []
		if (window._window_type != HTM):
			if window._transparent <= 0:
				self._list.append(('clear',))
				cmifex.SetSiblings(window._hWnd, 0)
			else:
				cmifex.SetSiblings(window._hWnd, 1)
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
		ls = self._list
		for b in self._buttons[:]:
			b.close()
		win._displists.remove(self)

		ls = self._list
		for i in range(len(ls)):
			if ls[i][0]=='image':
				fou = 1
				for dl in win._displists:
					for y in range(len(dl._list)):
						if dl._list[y][0]=='image':
							if ls[i][2]==dl._list[y][2]:
								fou = 0
								break
					if fou:
						imageex.Destroy(ls[i][2])

		self._window = None
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			#win.push()
			if win._transparent == -1:
				cmifex.SetSiblings(win._hWnd, 1)
			if win._transparent == 1 or win._transparent == -1:
				f = 0
				if win._topwindow is not win:
					#cmifex.LockWindowUpdate(win._parent._hWnd)
					cmifex.FillRectangle(win._hWnd,win._hWnd.GetClientRect(),win._parent._bgcolor)
					i = win._parent._subwindows.index(win)
					windows = win._parent._subwindows[i:]
					#windows.reverse()
					for w in windows:
						if w._active_displist!=None and w._transparent != 1 and w != win:
							rect1 = win._hWnd.GetClientRect()
							rect2 = win._hWnd.ClientToScreen(rect1)
							rect2 = w._hWnd.ScreenToClient(rect2)
							rect1 = w._hWnd.GetClientRect()
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
							f = 1
							w._hWnd.PostMessage(win32con.WM_PAINT)
							#w._do_expose(w._hWnd, 1)
					#cmifex.UnLockWindowUpdate(win._parent._hWnd)

				if f == 0:
					win._parent._hWnd.PostMessage(win32con.WM_PAINT,0,1)
				#	win.hide()
				#	win.show()
			else:
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

		for b in self._buttons:
			b._highlighted = 0
		# draw our bit
		self._render(window._hWnd, 1)
		# now draw transparent windows that lie on top of us
		#if window._topwindow is not window:
		#	i = window._parent._subwindows.index(window)
		#	windows = window._parent._subwindows[:i]
		#	#windows.reverse()
		#	for w in windows:
		#		if w._z > window._z and w._active_displist!=None:
		#			#w._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
		#			w._do_expose(w._hWnd, 1)
		#		if w._transparent and w._active_displist!=None and w != window:
		#			#w._forcePaint()
		#			w._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
		#			w._do_expose(window._hWnd, 1)
		#else:
		#	windows = window._subwindows[:]
		#	#windows.reverse()
		#	for w in windows:
		#		if w._transparent:
		#			#w._forcePaint()
		#			w._hWnd.SetWindowPos( win32con.HWND_TOP , (0, 0, 0, 0), win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOREDRAW)
		#			w._do_expose(window._hWnd, 1)
		# finally, re-highlight window
		#if window._showing:
		#	window.showwindow()

		if hasattr(window, '_pixmap'):
			x, y, width, height = window._rect
			#window._pixmap.CopyArea(window._form, window._gc,
			#			x, y, width, height, x, y)
		#window._forcePaint()

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
		#handle = self._list[1]
		w._active_displist = self
		if show==1:
			for i in range(clonestart, len(self._list)):
				self._do_render(self._list[i], hWnd)
			self._curfg = self._window._fgcolor


	def clear_back(self, w, image):
		wx, wy, ww, wh = w._hWnd.GetClientRect()
		il, it, ir, ib = imageex.ImageRect(image)
		tup1 = (0,0,0,ib)
		tup2 = (il,0,ww,it)
		tup3 = (0,ib,ir,wh)
		tup4 = (ir,it,ww,wh)
		cmifex.FillRectangle(w._hWnd,tup1,self._bgcolor)
		cmifex.FillRectangle(w._hWnd,tup2,self._bgcolor)
		cmifex.FillRectangle(w._hWnd,tup3,self._bgcolor)
		cmifex.FillRectangle(w._hWnd,tup4,self._bgcolor)


	def _do_render(self, entry, hWnd):
		#print "--____DO____Render ____________ ", self._window._title
		cmd = entry[0]
		#win32ui.MessageBox(cmd, "Test", win32con.MB_OK)
		#print "Rendering ", self._window._title
		w = self._window
		if cmd == 'clear':
			f = 0
			for i in range(len(self._list)):
				if self._list[i][0]=='image':
					image = self._list[i][2]
					f = 1
					self.clear_back(w,image)
					break
			if f==0:
				cmifex.FillRectangle(w._hWnd,w._hWnd.GetClientRect(),self._bgcolor)
			#pass
			#fg = gc.foreground
			#gc.foreground = gc.background
			#apply(gc.FillRectangle, w._rect)
			#gc.foreground = fg
		elif cmd == 'fg':
			self._curfg = entry[1]
			#gc.foreground = entry[1]
			pass
		elif cmd == 'image':
			mask = entry[1]
			r, g, b = self._bgcolor
			imageex.PutImage(w._hWnd, entry[2], r, g, b, w._scale, entry[3])
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
			fg = entry[1]
			points = entry[2]
			x0, y0 = points[0]
			for x, y in points[1:]:
				#gc.DrawLine(x0, y0, x, y)
				cmifex.DrawLine(w._hWnd, (x0, y0, x, y), fg)
				x0, y0 = x, y
			#gc.foreground = fg
		elif cmd == 'box':
			#mcolor = self._fgcolor #255, 0, 0	w._fgcolor
			cmifex.DrawRectangle(w._hWnd, entry[1], self._curfg, " ")
		elif cmd == 'fbox':
			#fg = gc.foreground
			#gc.foreground = entry[1]
			#apply(gc.FillRectangle, entry[2])
			#gc.foreground = fg
			cmifex.FillRectangle(w._hWnd, entry[2], entry[1])
			pass
		elif cmd == 'font':
			#gc.SetFont(entry[1])
			pass
		elif cmd == 'text':
			#print "Text at :", entry[3:]
			fontname = entry[1]
			pointsize = entry[2]
			id = entry[3]
			str = entry[4]
			x, y = entry[5:]
			#print "x,y--->", x,y
			#fontColor = 0, 0, 0
			fontColor = w._fgcolor
			#print 'Put Text params: '
			#print 'Parameters: ', str, fontname, pointsize, TRANSPARENT, self._bgcolor, fontColor,w._align,(x,y)
			if (str == None or str==''):
				str =' '
			textex.PutText(id, w._hWnd, str, fontname, pointsize, TRANSPARENT, self._bgcolor, fontColor,w._align,(x,y))
			#textex.PutText(id, w._hWnd, str, fontname, pointsize, TRANSPARENT, self._bgcolor, fontColor)
			self.update_boxes(w._hWnd)
			pass
		elif cmd == 'linewidth':
			#gc.line_width = entry[1]
			pass
		elif cmd == 'video':
			func = entry[2]
			apply(func,(entry[1],))
		#w.show()



	def update_boxes(self, hWnd):
		#print "in update_boxes"
		if self._window._window_type == TEXT:
			ydif = textex.GetScrollPos(hWnd)
		else:
			ydif = 0
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
				#self._buttons[button]._setcoords(x1,y1,x2,y2)
				#button = button+1
		for i in range(0, len(self._buttons)):
			l = self._buttons[i]._box
			tuple = l
			x1 = tuple[0]
			y1 = tuple[1]+ydif
			x2 = tuple[2]
			y2 = tuple[3]+ydif
			temptuple = (x1,y1,x2,y2)
			self._buttons[button]._setcoords(x1,y1,x2,y2)
			button = button+1
		#print "out of update_boxes"


	def fgcolor(self, color):
		#r, g, b = color
		self._list.append('fg', color)
		self._fgcolor = color

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
		self._optimize(2)
		#Assume that the image is stretched to the window so there is no conversion needed
		#x, y, w, h = 0, 0, 1, 1
		#return x, y, w, h
		x, y, w, h = w._rect
		a, b = float(dest_x) / w, float(dest_y) / h,
		c, d = float(width) / w, float(height) / h
		print "--------- ", a, b, c, d
		return a, b, c, d

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0, center = 1, tras = -1):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, l, t, r, b = w._prepare_image(file, crop, scale, center, transp = tras)
		dest_x = l
		dest_y = t
		width = r-l
		height = b-t
		mask, src_x, src_y = 0, 0, 0
		#dest_x, dest_y, width, height = w._rect
		self._list.append('image', mask, image, center, src_y,
				  dest_x, dest_y, width, height)
		self._optimize(2)
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
			coordinates = self._window._convert_coordinates(point)
			X, Y, W, H = self._window._rect
			x, y = coordinates
			x = x - X
			y = y - Y
			coordinates = x, y
			p.append((x, y))

		self._list.append('line', color, p)

	def drawbox(self, coordinates, do_draw=1):
		#print "DrawBox Before: ", coordinates
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		#print "DrawBox After: ", coordinates
		#print "Window Rect: ", self._window._rect
		#X, Y, W, H = self._window._rect
		x, y, w, h = coordinates
		#x = x - X
		#y = y - Y
		w = x + w
		h = y + h
		coordinates = x, y, w, h
		if do_draw:
			self._list.append('box', coordinates)
			self._optimize()
		return coordinates

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		#X, Y, W, H = self._window._rect
		x, y, w, h = coordinates
		#x = x - X
		#y = y - Y
		w = x + w
		h = y + h
		coordinates = x, y, w, h
		#6/2A
		#self._list.append('fbox', self._window._convert_color(color),
		#		self._window._convert_coordinates(coordinates))
		self._list.append('fbox', color, coordinates)
		self._optimize(1)
		return coordinates

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

	def writeText(self, font, size, id, str, x, y):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		list.append('text', font, size, id, str, x, y)

	def centerstring(self, left, top, right, bottom, str):
		wx, wy, wid, heig = self._window._hWnd.GetClientRect()
		if heig == 0:
			heig = 1
		#fontheight = self.fontheight()
		fontheight = self._font._pointsize
		baseline = self.baseline()
		width = int((right - left)*wid)
		height = int((bottom - top)*heig)
		curlines = [str]
		if height >= 2*fontheight:
			import StringStuff
			curlines = StringStuff.calclines([str], self.strsize, right - left)[0]
		nlines = len(curlines)
		needed = nlines * fontheight
		if nlines > 1 and needed > height:
			nlines = max(1, int(height / fontheight))
			curlines = curlines[:nlines]
			curlines[-1] = curlines[-1] + '...'
		x0 = (left + right) * 0.5	# x center of box
		y0 = (top + bottom) * 0.5	# y center of box
		y = y0 - nlines * fontheight * 0.5/heig
		for i in range(nlines):
			str = string.strip(curlines[i])
			# Get font parameters:
			w = self.strsize(str)[0]	# Width of string
			while str and w > right - left:
				str = str[:-1]
				w = self.strsize(str)[0]
			x = x0 - 0.5*w
			#y = y + baseline
			#y = y + self._font._pointsize/heig
			self.setpos(x, y)
			dstx = int(x * wid + 0.5)
			dsty = int(y * heig + 0.5)+self._font._pointsize*i
			#self.writestr(str)
			self.writeText(self._font._fontname, self._font._pointsize, -1, str, dstx, dsty)

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
		#print 'NEW _Button to be created -- Coordinates:'
		#print coordinates
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
		#if self._color == dispobj._bgcolor:
		#	return
		#self._box = dispobj.drawbox(self._coordinates)
		bw = self._coordinates[2] #- self._coordinates[0]
		bh = self._coordinates[3] #- self._coordinates[1]
		bx = self._coordinates[0]
		by = self._coordinates[1]
		self._box = dispobj.drawbox((bx,by,bw,bh),self._color != dispobj._bgcolor)

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
		#self._box = x, y, w-x, h-y
		self._box = x, y, w, h

	def close(self):
		#wnd = self._dispobj._window._hWnd
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
		self._height, self._ascent, self._maxWidth, self._aveWidth = cmifex.GetTextMetrics()
		self._pointsize = pointsize
		self._fontname = fontname

	def close(self):
		self._font = None

	def is_closed(self):
		return self._font is None

	def strsize(self, str):
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		#maxheight = len(strlist) * (self._height)
		maxheight = len(strlist) * (self._pointsize)
		for str in strlist:
			#width = cmifex.GetTextWidth(str)
			#width = len(str)*self._maxWidth
			width = len(str)*self._aveWidth
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
	def __init__(self, text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'information',
		     title = 'message'):
		#if grab:
		#		dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
		#		w = grab
		#		if type(w) is IntType:
		#			w = toplevel
		#		while 1:
		#			if hasattr(w, '_shell'):
		#				w = w._shell
		#				break
		#			if hasattr(w, '_main'):
		#				w = w._main
		#				break
		#			w = w._parent
		#else:
		#	dialogStyle = Xmd.DIALOG_MODELESS
		#	w = toplevel._main
		#if mtype == 'error':
		#	func = w.CreateErrorDialog
		#elif mtype == 'warning':
		#	func = w.CreateWarningDialog
		#elif mtype == 'information':
		#	func = w.CreateInformationDialog
		#elif mtype == 'question':
		#	func = w.CreateQuestionDialog
		#else:
		#	func = w.CreateMessageDialog
		self._grab = grab
		#w = func(name, {'messageString': text,
		#		'title': title,
		#		'dialogStyle': dialogStyle,
		#		'resizePolicy': Xmd.RESIZE_NONE,
		#		'visual': toplevel._default_visual,
		#		'depth': toplevel._default_visual.depth,
		#		'colormap': toplevel._default_colormap})
		#w.MessageBoxGetChild(Xmd.DIALOG_HELP_BUTTON).UnmanageChild()
		#if mtype == 'question' or cancelCallback:
		#	w.AddCallback('cancelCallback',
		#			  self._callback, cancelCallback)
		#else:
		#	w.MessageBoxGetChild(Xmd.DIALOG_CANCEL_BUTTON).UnmanageChild()
		#w.AddCallback('okCallback', self._callback, callback)
		#w.AddCallback('destroyCallback', self._destroy, None)
		#w.ManageChild()
		#self._widget = w

		res = 0
		style = " "

		if mtype == 'error':
			style = style+"e"

		if mtype == 'warning':
			style = style+"w"

		if mtype == 'information':
			style = style+"i"

		if mtype == 'message':
			style = style+"m"

		if mtype == 'question':
			style = style+"q"

		if mtype != 'question' and cancelCallback:
			style = style+"c"

		if grab:
			res = cmifex2.MesBox(text,title,style)
		else:
			#ls = string.splitfields(text ,'\n')
			#max = 0;
			#for line in ls:
			#	length = len(line)
			#	if length>max:
			#		max = length
			#height = (len(ls)+1)*15
			#width = max*13

			#dwidth = width + 2*win32api.GetSystemMetrics(win32con.SM_CXBORDER)
			#dheight = height + 3*win32api.GetSystemMetrics(win32con.SM_CYBORDER) + win32api.GetSystemMetrics(win32con.SM_CYCAPTION) + 70
			#dx = (win32api.GetSystemMetrics(win32con.SM_CXSCREEN)-dwidth)/2
			#dy = (win32api.GetSystemMetrics(win32con.SM_CYSCREEN)-dheight)/2

			#print 'Win32_winbase.py title is:'
			#print title
			#print dx, dy
			#w = cmifex2.CreateDialogbox(title,0,dx,dy,dwidth,dheight,1)
			#mes = cmifex2.CreateStatic("",w,0,0,width,height,'center')
			#cmifex2.SetFont(mes,"Arial",10)
			#cmifex2.SetCaption(mes,text)

			if mtype == 'question' or cancelCallback:
				st = win32con.MB_OKCANCEL
			else:
				st = win32con.MB_OK

			if mtype == 'error':
				st = st|win32con.MB_ICONERROR

			if mtype == 'warning':
				st = st|win32con.MB_ICONWARNING

			if mtype == 'information':
				st = st|win32con.MB_ICONINFORMATION

			if mtype == 'message':
				st = st|win32con.MB_ICONINFORMATION

			if mtype == 'question':
				st = MB_YESNO|win32con.MB_ICONQUESTION

			res = win32ui.MessageBox(text,title,st)


		if res==win32con.IDOK or res==win32con.IDYES:
			if callback:
				apply(callback[0], callback[1])
		elif res==win32con.IDCANCEL or res==win32con.IDNO:
			if cancelCallback:
				apply(cancelCallback[0], cancelCallback[1])



	def close(self):
		if self._widget:
			w = self._widget
			self._widget = None
			w.UnmanageChild()
			w.DestroyWidget()

	def _callback(self, widget, callback, call_data):
		if not self._widget:
			return
		if callback:
			apply(callback[0], callback[1])
		if self._grab:
			self.close()

	def _destroy(self, widget, client_data, call_data):
		self._widget = None



class Dialog:
	def __init__(self, list, title = '', prompt = None, grab = 1,
		     vertical = 1, del_Callback = None):
		if not title:
			title = ''
		#if grab:
		#	dialogStyle = Xmd.DIALOG_FULL_APPLICATION_MODAL
		#else:
		#	dialogStyle = Xmd.DIALOG_MODELESS
		#w = toplevel._main.CreateFormDialog('dialog',
		#		{'title': title,
		#		 'dialogStyle': dialogStyle,
		#		 'resizePolicy': Xmd.RESIZE_NONE,
		#		 'visual': toplevel._default_visual,
		#		 'depth': toplevel._default_visual.depth,
		#		 'colormap': toplevel._default_colormap})
		#if vertical:
		#	orientation = Xmd.VERTICAL
		#else:
		#	orientation = Xmd.HORIZONTAL
		#attrs = {'entryAlignment': Xmd.ALIGNMENT_CENTER,
		#	 'traversalOn': FALSE,
		#	 'orientation': orientation,
		#	 'topAttachment': Xmd.ATTACH_FORM,
		#	 'leftAttachment': Xmd.ATTACH_FORM,
		#	 'rightAttachment': Xmd.ATTACH_FORM}
		#if prompt:
		#	l = w.CreateManagedWidget('label', Xm.LabelGadget,
		#			{'labelString': prompt,
		#			 'topAttachment': Xmd.ATTACH_FORM,
		#			 'leftAttachment': Xmd.ATTACH_FORM,
		#			 'rightAttachment': Xmd.ATTACH_FORM})
		#	sep = w.CreateManagedWidget('separator',
		#			Xm.SeparatorGadget,
		#			{'topAttachment': Xmd.ATTACH_WIDGET,
		#			 'topWidget': l,
		#			 'leftAttachment': Xmd.ATTACH_FORM,
		#			 'rightAttachment': Xmd.ATTACH_FORM})
		#	attrs['topAttachment'] = Xmd.ATTACH_WIDGET
		#	attrs['topWidget'] = sep
		#row = w.CreateManagedWidget('buttonrow', Xm.RowColumn, attrs)

		if del_Callback == None :
			del_Callback = (self.close, ())
			
		import windowinterface


		self.window = w = windowinterface.Window(title,
				deleteCallback = del_Callback, havpar = 0)
		constant = 3*win32api.GetSystemMetrics(win32con.SM_CXBORDER)+win32api.GetSystemMetrics(win32con.SM_CYCAPTION)+5
		constant2 = 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)+5
		self._w = constant2
		self._h = constant
		butw = 0
		max = 0
		ls = []
		for item in list :
			if item is None:
				continue
			else :
				ls.append(item[0])

		#ls = ['Open...', 'Close', 'Debug', 'Trace']

		#if hasattr(self.root, 'source') and \
		#   hasattr(windowinterface, 'TextEdit'):
		#	ls.insert(0, 'View Source...')

		length = 0
		for item in ls:
			label = item
			if label:
				length = cmifex2.GetStringLength(w._hWnd, label)
				if length>max:
					max = length

		butw = max + 60
		self._w = self._w + butw
		self._h = self._h + len(ls)*25+10

		buttons = list

		self._buttons = self.window.ButtonRow(
			buttons,
			top = 0, bottom = self._h-constant, left = 0, right = butw,
			vertical = 1)

		cmifex2.ResizeWindow(w._hWnd, self._w, self._h)
		self.window.show()


		#self._buttons = []
		#for entry in list:
		#	if entry is None:
		#		if vertical:
		#			attrs = {'orientation': Xmd.HORIZONTAL}
		#		else:
		#			attrs = {'orientation': Xmd.VERTICAL}
		#		dummy = row.CreateManagedWidget('separator',
		#					Xm.SeparatorGadget,
		#					attrs)
		#		continue
		#	if type(entry) is TupleType:
		#		label, callback = entry[:2]
		#	else:
		#		label, callback = entry, None
		#	if callback and type(callback) is not TupleType:
		#		callback = (callback, (label,))
		#	b = row.CreateManagedWidget('button',
		#				    Xm.PushButtonGadget,
		#				    {'labelString': label})
		#	if callback:
		#		b.AddCallback('activateCallback',
		#			      self._callback, callback)
		#	self._buttons.append(b)
		self._widget = w
		self._menu = None
		#w.AddCallback('destroyCallback', self._destroy, None)
		#w.ManageChild()

	# destruction
	def _destroy(self, widget, client_data, call_data):
		self._widget = None
		self._menu = None
		self._buttons = []

	def close(self):
		w = self._widget
		w.close()
		self._widget = None
		#w.UnmanageChild()
		#w.DestroyWidget()

	# pop up menu
	def destroy_menu(self):
		if self._menu:
			#self._widget.RemoveEventHandler(X.ButtonPressMask,
			#			FALSE, self._post_menu, None)
			#self._menu.DestroyWidget()
			cmifex2.DestroyMenu(self._menu)
		self._menu = None

	def create_menu(self, list, title = None):
		self.destroy_menu()
		menu = self._widget.CreatePopupMenu('dialogMenu',
				{'colormap': toplevel._default_colormap,
				 'visual': toplevel._default_visual,
				 'depth': toplevel._default_visual.depth})
		if title:
			list = [title, None] + list
		_create_menu(menu, list, toplevel._default_visual,
			     toplevel._default_colormap)
		self._menu = menu
		self._widget.AddEventHandler(X.ButtonPressMask, FALSE,
					     self._post_menu, None)

	def _post_menu(self, widget, client_data, call_data):
		if not self._menu:
			return
		if call_data.button == X.Button3:
			self._menu.MenuPosition(call_data)
			self._menu.ManageChild()

	# buttons
	def _callback(self, widget, callback, call_data):
		if callback:
			apply(callback[0], callback[1])

	def getbutton(self, button):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		return self._buttons[button].set

	def setbutton(self, button, onoff = 1):
		if not 0 <= button < len(self._buttons):
			raise error, 'button number out of range'
		self._buttons[button].set = onoff


class MainDialog(Dialog):
	pass
	#def __init__(self, list, title = None, prompt = None, grab = 1,
	#	     vertical = 1):
	#	self._do_init(list, title = None, prompt = None, grab = 1,
	#	     vertical = 1)
	#	toplevel.MainDialog = self

def multchoice(prompt, list, defindex):
	return defindex

def beep():
	import sys
	sys.stderr.write('\7')

def lopristarting():
	pass

def _win_setcursor(form, cursor):
	keys = win32Cursors.keys()
	if not cursor in keys:
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

def _create_menu(menu, list, menuid, cbdict, acc = None):
	accelerator = None
	length = 0
	i = 0
	id = menuid
	dict  = cbdict
	buts = []
	while i < len(list):
		entry = list[i]
		i = i + 1
		if entry is None:
#			dummy = menu.CreateManagedWidget('separator',
#							 Xm.SeparatorGadget,
#							 {})
			cmifex2.AppendMenu(menu, '', 0)
			continue
#		if length == 20 and i < len(list) - 3:
#			entry = ('More', list[i-1:])
#			i = len(list)
#			if acc is not None:
#				entry = ('',) + entry
		length = length + 1
		if type(entry) is StringType:
#			dummy = menu.CreateManagedWidget(
#				'menuLabel', Xm.LabelGadget,
#				{'labelString': entry})
			cmifex2.AppendMenu(menu, entry, id)
			id = id + 1
			buts.append((entry,None))
			continue
		btype = 'p'		# default is pushbutton
		initial = 0
		if acc is None:
			labelString, callback = entry[:2]
			if len(entry) > 2:
				btype = entry[2]
				if len(entry) > 3:
					initial = entry[3]
		else:
			if len(entry)==2:
				accelerator = None
				labelString, callback = entry
			else:
				accelerator, labelString, callback = entry[:3]
			if len(entry) > 3:
				btype = entry[3]
				if len(entry) > 4:
					initial = entry[4]

		if type(callback) is ListType:
#			submenu = menu.CreatePulldownMenu('submenu',
#				{'colormap': colormap,
#				 'visual': visual,
#				 'depth': visual.depth})
#			button = menu.CreateManagedWidget(
#				'submenuLabel', Xm.CascadeButtonGadget,
#				{'labelString': label, 'subMenuId': submenu})
			submenu = cmifex2.CreateMenu()
			temp = _create_menu(submenu, callback, id, dict, acc)

			if temp:
				id = temp[0]
				dict2 = temp[1]
				dkeys = dict2.keys()
				for k in dkeys:
					if not dict.has_key(k):
						dict[k] = dict2[k]
			buts.append((labelString, temp[2]))
			cmifex2.PopupAppendMenu(menu, submenu, labelString)
		else:
			buts.append((labelString, None))
			if type(callback) is not TupleType:
				callback = (callback, (labelString,))
			attrs = {'labelString': labelString}
			if accelerator:
				if type(accelerator) is not StringType or \
				   len(accelerator) != 1:
					raise error, 'menu accelerator must be single character'
				acc[accelerator] = callback
				attrs['acceleratorText'] = accelerator
				labelString = labelString + '\t' + accelerator
			#button = menu.CreateManagedWidget('menuLabel',
			#			Xm.PushButtonGadget, attrs)
			#button.AddCallback('activateCallback',
			#		   _generic_callback, callback)
			cmifex2.AppendMenu(menu, labelString, id)
			dict[id] = callback
			if btype == 't':
				cmifex2.CheckMenuItem(menu,id,initial)
			#print "dict-->", dict
			id = id + 1

	t = (id, dict, buts)
	return t

def roundi(x):
	if x < 0:
		return roundi(x + 1024) - 1024
	return int(x + 0.5)
