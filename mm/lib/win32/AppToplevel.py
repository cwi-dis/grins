__version__ = "$Id$"

import win32ui, win32con, win32api
from win32modules import cmifex,cmifex2,timerex

import AppWnds

toplevel = None

ReadMask, WriteMask = 1, 2
[SINGLE, HTM, TEXT, MPEG] = range(4)
FALSE, TRUE = 0, 1
UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2
WM_MAINLOOP = 200

#module sysmet:

def GetSystemMetrics():
	cxframe=win32api.GetSystemMetrics(win32con.SM_CXFRAME)
	cyframe=win32api.GetSystemMetrics(win32con.SM_CYFRAME)
	cxborder=win32api.GetSystemMetrics(win32con.SM_CXBORDER)
	cyborder=win32api.GetSystemMetrics(win32con.SM_CYBORDER)
	cycaption=win32api.GetSystemMetrics(win32con.SM_CYCAPTION)

def GetDeviceCaps():
	wnd=GetMainWnd()
	dc = win32ui.GetDC();
	width=dc.GetDeviceCaps(win32con.HORZRES)
	height=dc.GetDeviceCaps(win32con.VERTRES)
	dpix=dc.GetDeviceCaps(win32con.LOGPIXELSX)
	dpiy=dc.GetDeviceCaps(win32con.LOGPIXELSY)
	depth=dc.GetDeviceCaps(win32con.BITSPIXEL)
	wnd.ReleaseDC(dc);


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

		self.xborder = win32api.GetSystemMetrics(win32con.SM_CXFRAME) + 2*win32api.GetSystemMetrics(win32con.SM_CXBORDER)
		self.yborder = win32api.GetSystemMetrics(win32con.SM_CYFRAME) + 2*win32api.GetSystemMetrics(win32con.SM_CYBORDER)
		self.caption = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
	
		self._screenwidth = cmifex.GetScreenWidth()
		self._screenheight = cmifex.GetScreenHeight()
		self._dpi_x = cmifex.GetScreenXDPI()
		self._dpi_y = cmifex.GetScreenYDPI()
		
		self._mscreenwidth = (float(self._screenwidth)*25.4) / self._dpi_x
		self._mscreenheight = (float(self._screenheight)*25.4) / self._dpi_y
		self._hmm2pxl = float(self._screenwidth) / self._mscreenwidth
		self._vmm2pxl = float(self._screenheight) / self._mscreenheight
		self._hfactor = self._vfactor = 1.000

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

	# in the following calls UNITS are ignored
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE, units = UNIT_MM, pixmap = 0, menubar = None, canvassize = None):
		global toplevel
		if toplevel == None:
			toplevel = self
		return	AppWnds.Window(self, x, y, w, h, title, visible_channel, type_channel, 0, pixmap, 0, units, menubar, canvassize)


	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE, units = UNIT_MM, pixmap = 0, menubar = None, canvassize = None):
		pixmap=0 # enforce until problem resolved
		return AppWnds.Window(self, x, y, w, h, title, visible_channel, type_channel, 1, pixmap, 0, units, menubar, canvassize)

	def getsize(self):
		return toplevel._mscreenwidth, toplevel._mscreenheight

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
		if (self.serving == 0): return
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
		self.timerid = timerex.SetTimer(int(0.001 * 1000))

	
	def _timer_callback(self, params):
		timerex.KillTimer(self.timerid)		
		self.serve_events()
		

	def _message_callback(self, params):
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


toplevel = _Toplevel()
AppWnds.toplevel=toplevel

import AppForms
AppForms.toplevel=toplevel
