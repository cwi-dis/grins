__version__ = "$Id$"

import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()

import sysmetrics

import MainFrame

from appcon import *
from win32modules import imageex


# The AppObj class represents the root of all windows.  It is never
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
	
		# generic wnd class
		import GenWnd
		self.genericwnd=GenWnd.GenWnd
		
		self._in_create_box=None
		self._do_init()

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

				
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._idles = []
		self._time = float(Sdk.GetTickCount())/TICKS_PER_SECOND

		# fibers serving

		self._apptitle=None
		self._appadornments=None
		self._appcommandlist=None


	def forcePaint(self):
		for w in self._subwindows:
			w._forcePaint()

	def close(self):
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
		      type_channel = SINGLE, pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1):
		if 'frame' not in adornments.keys():
			raise 'error', 'newwindow without frame specification'
		frame=adornments['frame']
		return frame.newwindow(x, y, w, h, title, visible_channel,
		      type_channel, pixmap, units,
		      adornments, canvassize,
		      commandlist, resizable)


	############ SDI/MDI Model Support
	def createmainwnd(self,title = None, adornments = None, commandlist = None):
#		if title:
#			self._apptitle=title
		# ignore title from core under Martin sugestion
		self._apptitle=AppDisplayName
		if adornments:
			self._appadornments=adornments
		if commandlist:
			self._appcommandlist=commandlist
		if len(self._subwindows)==0:
			frame = MainFrame.MDIFrameWnd()
			frame.create(self._apptitle)
			frame.init_cmif(None, None, 0, 0, self._apptitle,
				UNIT_MM, self._appadornments,self._appcommandlist)
		return self._subwindows[0]

	def newdocument(self,cmifdoc,adornments=None,commandlist=None):
		for w in self._subwindows:
			if not w._cmifdoc:
				w.setdocument(cmifdoc,adornments,commandlist)
				return w
		frame = MainFrame.MDIFrameWnd()
		frame.create(self._apptitle)
		frame.init_cmif(None, None, 0, 0,self._apptitle,
			UNIT_MM,self._appadornments,self._appcommandlist)
		frame.setdocument(cmifdoc,adornments,commandlist)
		return frame
	
	# returns the active mainwnd
	def getmainwnd(self):
		if len(self._subwindows)==0:
			self.createmainwnd()
		return self._subwindows[0] # return the active
		
	############ /SDI-MDI Model Support	

	def textwindow(self,text):
		print 'you must request textwindow from a frame'
		sv=self.newviewobj('sview_')
		sv.settext(text)
		self.showview(sv,'sview_')
		if IsEditor: sv.set_close_commandlist()
		return sv
	
	def getsize(self):
		"""size of the screen in mm"""
		return self._scr_width_mm, self._scr_height_mm

	def getscreensize(self):
		"""Return screen size in pixels"""
		return self._scr_width_pxl, self._scr_height_pxl

	def getscreendepth(self):
		"""Return screen depth"""
		return sysmetrics.depth

	def setcursor(self, strid):
		if strid=='hand':
			import grinsRC
			cursor = App.LoadCursor(grinsRC.IDC_POINT_HAND)
		else:
			cursor = App.LoadStandardCursor(win32con.IDC_ARROW)
		(win32ui.GetWin32Sdk()).SetCursor(cursor);
		self._cursor = strid


	def pop(self):
		pass

	def push(self):
		pass

	def show(self):
		for w in self._subwindows:
			w.show()
				
	def hide(self):
		for w in self._subwindows:		
			w.hide()

	def _convert_color(self, color, defcm):
		return color

	def GetWindowRect(self):
		return (0,0,sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl)

	def GetClientRect(self):
		return (0,0,sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl)

	def getsizes(self):
		return (0,0,1,1)

	def usewindowlock(self, lock):
		pass

	#########################################
	def mainloop(self):
		if len(self._subwindows) == 1:self.show()
		self.serve_events(())
		#win32ui.GetApp().AddIdleHandler(self.monitor)
		wnd=self.genericwnd()
		wnd.create()
		self._autostop=0
		wnd.HookMessage(self.serve_events,win32con.WM_USER+999)
		win32ui.GetApp().RunLoop(wnd)
		wnd.DestroyWindow()
		(win32ui.GetAfx()).PostQuitMessage(0)

	def monitor(self,handler,count):
		return 0

	# actualy part of the main loop	
	# and part of a delta timer 
	def serve_events(self,params):	
		if self._waiting:self.setready()				
		while self._timers:
			t = float(Sdk.GetTickCount())/TICKS_PER_SECOND
			sec, cb, tid = self._timers[0]
			sec = sec - (t - self._time)
			self._time = t
			if sec <= 0.002:
				del self._timers[0]
				apply(apply, cb)
			else:
				self._timers[0] = sec, cb, tid
				break
		self._time=float(Sdk.GetTickCount())/TICKS_PER_SECOND
		self.serve_timeslices()

	_waiting=0
	def setwaiting(self,f=0):
		""" added flag to control win32 instance
		the core calls it to often while it is apropriate
		for long waiting times"""
		if not self._waiting and f:
			win32ui.GetApp().BeginWaitCursor()
		self._waiting = 1

	def setready(self,f=0):
		if self._waiting and f:
			win32ui.GetApp().EndWaitCursor()
		self._waiting = 0

	#
	# delta timer interface
	#
	def settimer(self, sec, cb):
		self._timer_id = self._timer_id + 1
		t0 = float(Sdk.GetTickCount())/TICKS_PER_SECOND
		if self._timers:
			t, a, i = self._timers[0]
			t = t - (t0 - self._time) # can become negative
			self._timers[0] = t, a, i
		self._time = t0
		t = 0
		for i in range(len(self._timers)):
			time0, dummy, tid = self._timers[i]
			if t + time0 > sec:
				self._timers[i] = (time0 - sec + t, dummy, tid)
				self._timers.insert(i, (sec - t, cb, self._timer_id))
				return self._timer_id
			t = t + time0
		self._timers.append(sec - t, cb, self._timer_id)
		#print 'new event:',self._timer_id,sec - t,cb
		return self._timer_id


	def canceltimer(self, id):
		if id == None: return
		for i in range(len(self._timers)):
			t, cb, tid = self._timers[i]
			if tid == id:
				del self._timers[i]
				if i < len(self._timers):
					tt, cb, tid = self._timers[i]
					self._timers[i] = (tt + t, cb, tid)
				return
		raise 'unknown timer', id

	# Monitoring Fibers	registration
	_registry={}
	_fiber_id=0
	def register(self,check,cb):
		self._fiber_id = self._fiber_id + 1
		self._registry[self._fiber_id]=(check,cb)
		return self._fiber_id
	def unregister(self,id):
		if id in self._registry.keys():
			del self._registry[id]
	def serve_timeslices(self):
		for check,call in self._registry.values():
			if apply(apply,check):apply(apply,call)

	################################
		
	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		raise error, 'No select_setcallback for win32'


	################################
	
	#utility functions
		
	def GetImageSize(self,file):
		try:
			xsize, ysize = self._image_size_cache[file]
		except KeyError:
			try:
				img = imageex.load(file)
			except img.error, arg:
				raise error, arg
			xsize,ysize,depth=imageex.size(img)
			self._image_size_cache[file] = xsize, ysize
			self._image_cache[file] = img
		return xsize, ysize

	def GetVideoSize(self,file):
		DirectShowSdk=win32ui.GetDS()
		builder=DirectShowSdk.CreateGraphBuilder()
		width, height=100,100
		if builder:
			builder.RenderFile(fn)
			width, height=builder.GetWindowPosition()[2:]
		return (width, height)
	
	def GetStringLength(wnd,str):
		dc = wnd.GetDC();
		cx,cy=dc.GetTextExtent(str)
		wnd.ReleaseDC(dc)
		return cx



#######################################################
# FileDialog
#
#
# Note:
# expected args from win32ui function CreateFileDialog:
# "i|zzizO",
#bFileOpen, // @pyparm int|bFileOpen||A flag indicating if the Dialog is a FileOpen or FileSave dialog.
#szDefExt,  // @pyparm string|defExt|None|The default file extension for saved files. If None, no extension is supplied.
#szFileName, // @pyparm string|fileName|None|The initial filename that appears in the filename edit box. If None, no filename initially appears.
#flags,     // @pyparm int|flags|win32con.OFN_HIDEREADONLY\|win32con.OFN_OVERWRITEPROMPT|The flags for the dialog.  See the API documentation for full details.
#szFilter, // @pyparm string|filter|None|A series of string pairs that specify filters you can apply to the file. 
#	                        // If you specify file filters, only selected files will appear 
#	                        // in the Files list box. The first string in the string pair describes 
#	                        // the filter; the second string indicates the file extension to use. 
#	                        // Multiple extensions may be specified using ';' as the delimiter. 
#	                        // The string ends with two '\|' characters.  May be None.
#obParent  // @pyparm <o PyCWnd>|parent|None|The parent or owner window of the dialog.

class FileDialog:
	def __init__(self, prompt,directory,filter,file, cb_ok, cb_cancel,existing = 0,parent=None):
		
		if existing: 
			flags=win32con.OFN_HIDEREADONLY|win32con.OFN_FILEMUSTEXIST
		else:
			flags=win32con.OFN_OVERWRITEPROMPT
		if not parent:
			import __main__
			parent=__main__.toplevel._subwindows[0]

		if not filter or filter=='*':
			filter = 'All files (*.*)|*.*||'
		else:
			filter = 'smil files (*.smi;*.smil)|*.smi;*.smil|cmif files (*.cmif)|*.cmif|All files *.*|*.*||'
			
		self._dlg =dlg= win32ui.CreateFileDialog(existing,None,file,flags,filter,parent)
		dlg.SetOFNTitle(prompt)

		if dlg.DoModal()==win32con.IDOK:
			if cb_ok: cb_ok(dlg.GetPathName())
		else:
			if cb_cancel: cb_cancel()
	def GetPathName(self):
		return self._dlg.GetPathName()

#######################################
#################################################
# useful functions
# some are defined here to import only windowinterface and not pyds 





