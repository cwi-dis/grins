__version__ = "$Id$"

import win32ui, win32con, win32api
import sysmetrics

import win32mu,AppWnds

toplevel = None

ReadMask, WriteMask = 1, 2
FALSE, TRUE = 0, 1
SINGLE, HTM, TEXT, MPEG = 0, 1, 2, 3
UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2
WM_MAINLOOP = 200
ID_MAIN_TIMER=100


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
		self.xborder = sysmetrics.cxframe+2*sysmetrics.cxborder
		self.yborder = sysmetrics.cyframe + 2* sysmetrics.cyborder
		self.caption = sysmetrics.cycaption
		self._scr_width_pxl = sysmetrics.scr_width_pxl
		self._scr_height_pxl = sysmetrics.scr_height_pxl
		self._dpi_x = sysmetrics.dpi_x
		self._dpi_y = sysmetrics.dpi_y
		
		self._scr_width_mm = sysmetrics.scr_width_mm
		self._scr_height_mm = sysmetrics.scr_height_mm
		self._pixel_per_mm_x = sysmetrics.pixel_per_mm_x
		self._pixel_per_mm_y = sysmetrics.pixel_per_mm_y
		self._hfactor = self._vfactor = 1.000

		self._timerWnd=AppWnds.MfcOsWnd()
		self._timerWnd.create()
		self._timerWnd.HookMessage(self._timer_callback, win32con.WM_TIMER)
		self._timerWnd.HookMessage(self._message_callback,WM_MAINLOOP)
	
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
		from win32modules import imageex
		imageex.__del__()
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		self._closecallbacks = []
		self._subwindows = []

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	def newwindow(self, x, y, w, h, title, visible_channel = TRUE,
		      type_channel = SINGLE, pixmap = 1, units = UNIT_MM,
		      menubar = None, canvassize = None):
		if canvassize==None:
			return AppWnds._Window(self, x, y, w, h, title,visible_channel,type_channel,
				pixmap, units, menubar, canvassize)
		else:
			return AppWnds._WindowFrm(self, x, y, w, h, title,visible_channel,type_channel,
				pixmap, units, menubar, canvassize)

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE,
			type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
			menubar = None, canvassize = None):
		if canvassize==None:
			return AppWnds._Window(self, x, y, w, h, title,visible_channel,type_channel,
				pixmap, units, menubar, canvassize)
		else:
			return AppWnds._WindowFrm(self, x, y, w, h, title,visible_channel,type_channel,
				pixmap, units, menubar, canvassize)

	def getsize(self):
		"""size of the screen in mm"""
		return toplevel._scr_width_mm, toplevel._scr_height_mm

	def getscreensize(self):
		"""Return screen size in pixels"""
		return self._scr_width_pxl, self._scr_height_pxl

	def getscreendepth(self):
		"""Return screen depth"""
		return sysmetrics.depth

	def setcursor(self, cursor):
		win32mu.SetCursor(cursor)
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
					apply(func, args)
				else:
					self._timers[0] = sec, cb, tid
					break
				ifdlist = self._ifddict.keys()
				ofdlist = self._ofddict.keys()			
		self.timerid = self._timerWnd.SetTimer(ID_MAIN_TIMER,int(0.001 * 1000))

	
	def _timer_callback(self, params):
		self._timerWnd.KillTimer(self.timerid)		
		self.serve_events()
		

	def _message_callback(self, params):
		self.serving = 1
		self.serve_events()

	def _stopserve_callback(self, params):
		self.serving = 0
		

	# timer interface
	def settimer(self, sec, cb):
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

	

toplevel = _Toplevel()
AppWnds.toplevel=toplevel

import cmifwnd
cmifwnd.toplevel=toplevel

import AppForms
AppForms.toplevel=toplevel

import InputDialog
InputDialog.toplevel= toplevel