__version__ = "$Id$"

""" @win32doc|AppTopLevel
An instance of the _Toplevel class defined in this module
represents the platform dependent part of the application.
(The other part is platform independent and is an instance of Main)
It contains the main message loop of the application which beyond dispatching messages
it serves a delta timer (see tcp process) and tasks registered for timeslices.
This class is also the main interface between the core part of the system
that is platform independent with the part of the system that is 
platform dependent. This interface is exposed to the core system through
a module (windowinterface.py) which contains mainly alias to members of this class
"""
import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

import sysmetrics

import MainFrame

from appcon import *
from win32ig import win32ig


# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel:
	# Trap use in order to initialize the class properly
	def __getattr__(self, attr):
		if not self._initialized: # had better exist...
			self._do_init()
			try:
				return self.__dict__[attr]
			except KeyError:
				pass
		raise AttributeError, attr

	# Class constructor. Initalizes class members
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
	
		# generic wnd class
		import GenWnd
		self.genericwnd=GenWnd.GenWnd
		
		self._in_create_box=None
		self._do_init()

	# Part of the constructor initialization
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
		self._image_docmap = {None:[],}
				
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._idles = []
		self._time = float(Sdk.GetTickCount())/TICKS_PER_SECOND

		# fibers serving

		self._apptitle=None
		self._appadornments=None
		self._appcommandlist=None

	# Paint all the windows now
	def forcePaint(self):
		for w in self._subwindows:
			w._forcePaint()

	# Call by the core to close the application
	def close(self):
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
			if hasattr(win,'DestroyWindow'):
				win.DestroyWindow()
		self._closecallbacks = []
		self._subwindows = []

		win32ig.deltemp()

		import Font
		Font.delfonts()

		import DrawTk
		del DrawTk.drawTk

		import __main__
		del __main__.resdll



	# Registration function for close callbacks
	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	# Called by the core to create a window
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
	# Called by win32 modules to create the main frame
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

	# Called by win32 modules for every open document
	def newdocument(self,cmifdoc,adornments=None,commandlist=None):
		for frame in self._subwindows:
			if not frame._cmifdoc:
				frame.setdocument(cmifdoc,adornments,commandlist)
				return frame
		frame = MainFrame.MDIFrameWnd()
		frame.create(self._apptitle)
		frame.init_cmif(None, None, 0, 0,self._apptitle,
			UNIT_MM,self._appadornments,self._appcommandlist)
		frame.setdocument(cmifdoc,adornments,commandlist)
		return frame
	
	# Returns the active mainwnd
	def getmainwnd(self):
		if len(self._subwindows)==0:
			self.createmainwnd()
		return self._subwindows[0] # return the active
		
	############ /SDI-MDI Model Support	

	# Displays a text viewer
	def textwindow(self,text):
		print 'you must request textwindow from a frame'
		sv=self.newviewobj('sview_')
		sv.settext(text)
		self.showview(sv,'sview_')
		if IsEditor: sv.set_close_commandlist()
		return sv

	# Returns screen size in mm	
	def getsize(self):
		"""size of the screen in mm"""
		return self._scr_width_mm, self._scr_height_mm

	# Returns screen size in pixel
	def getscreensize(self):
		"""Return screen size in pixels"""
		return self._scr_width_pxl, self._scr_height_pxl

	# Returns screen depth
	def getscreendepth(self):
		"""Return screen depth"""
		return sysmetrics.depth


	# Set the application cursor to the cursor with string id
	def setcursor(self, strid):
		if strid!='arrow':
			print 'AppTopLevel.setcursor',strid
		App=win32ui.GetApp()
		import grinsRC
		if strid=='hand':
			cursor = App.LoadCursor(grinsRC.IDC_POINT_HAND)
		elif strid=='stop':
			cursor = App.LoadCursor(grinsRC.IDC_STOP)
		elif strid=='channel':
			cursor = App.LoadCursor(grinsRC.IDC_DRAGMOVE)
		else:
			cursor = App.LoadStandardCursor(win32con.IDC_ARROW)
			strid='arrow'
		(win32ui.GetWin32Sdk()).SetCursor(cursor);
		self._cursor = strid

	# To support the same interface as windows
	def pop(self):
		pass

	# To support the same interface as windows
	def push(self):
		pass

	# To support the same interface as windows
	# It calls show for each window in the list
	def show(self):
		for w in self._subwindows:
			w.show()
				
	# To support the same interface as windows
	# It calls hide for each window in the list
	def hide(self):
		for w in self._subwindows:		
			w.hide()
	
	# To support the same interface as windows (does nothing)
	def _convert_color(self, color, defcm):
		return color

	# To support the same interface as windows
	# returns desktop size
	def GetWindowRect(self):
		return (0,0,sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl)

	# To support the same interface as windows
	# returns desktop size
	def GetClientRect(self):
		return (0,0,sysmetrics.scr_width_pxl,sysmetrics.scr_height_pxl)

	# To support the same interface as windows
	# returns desktop size in relative coordinates
	def getsizes(self):
		return (0,0,1,1)

	# Part of the interface. Does nothing on win32. 
	def usewindowlock(self, lock):
		pass

	#########################################
	# Main message loop of the application
	def mainloop(self):
		if len(self._subwindows) == 1:self.show()
		self.serve_events(())
		win32ui.GetApp().AddIdleHandler(self.monitor)

		wnd=self.genericwnd()
		wnd.create()
		wnd.HookMessage(self.serve_events,win32con.WM_USER)
		win32ui.GetApp().RunLoop(wnd)
		wnd.DestroyWindow()

		self.close()

		(win32ui.GetAfx()).PostQuitMessage(0)

	def monitor(self,handler,count):
		self.serve_events()
		return 0 # no more, next time

	# It is actualy part of the main loop and part of a delta timer 
	def serve_events(self,params=None):	
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

	# Called by the core sustem to set the waiting cursor
	_waiting=0
	def setwaiting(self):
		if not self._waiting:
			win32ui.GetApp().BeginWaitCursor()

	# Called by the core sustem to remove the waiting cursor
	def setready(self):
		if self._waiting:
			win32ui.GetApp().EndWaitCursor()

	#
	# delta timer interface
	#
	# Register a timer even
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
		Afx.GetMainWnd().PostMessage(WM_KICKIDLE)
		return self._timer_id


	# Unregister a timer even
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
	# Register for receiving timeslices
	def register(self,check,cb):
		self._fiber_id = self._fiber_id + 1
		self._registry[self._fiber_id]=(check,cb)
		return self._fiber_id
	# Register for receiving timeslices
	def unregister(self,id):
		if id in self._registry.keys():
			del self._registry[id]
	# Dispatch timeslices
	def serve_timeslices(self):
		for check,call in self._registry.values():
			if apply(apply,check):apply(apply,call)

	################################
		
	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		raise error, 'No select_setcallback for win32'


	################################
	
	#utility functions
	def cleardocmap(self,doc):
		if doc not in self._image_docmap.keys(): return
		imglist=self._image_docmap[doc]
		for file in imglist:
			if file not in self._image_cache.keys():continue
			img=self._image_cache[file]
			del self._image_cache[file]
			del self._image_size_cache[file]
			win32ig.delete(img)
		del self._image_docmap[doc]

			
	# Returns the size of an image	
	def GetImageSize(self,file):
		try:
			xsize, ysize = self._image_size_cache[file]
		except KeyError:
			try:
				img = win32ig.load(file)
				self._image_docmap[None]=file
			except img.error, arg:
				raise error, arg
			xsize,ysize,depth=win32ig.size(img)
			self._image_size_cache[file] = xsize, ysize
			self._image_cache[file] = img
		return xsize, ysize

	# Returns the size of a video	
	def GetVideoSize(self,file):
		DirectShowSdk=win32ui.GetDS()
		builder=DirectShowSdk.CreateGraphBuilder()
		width, height=100,100
		if builder:
			builder.RenderFile(file)
			width, height=builder.GetWindowPosition()[2:]
		return (width, height)
	
	# Returns the length of a string in pixels	
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

# Implementation of the FileDialog 
class FileDialog:
	# Remember last location when the program does not request a specific
	# location
	last_location = None

	# Class constructor. Creates abd displays a std FileDialog
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

		# get/set current directory since the core assumes remains the same
		# The Windows filebrowser modifies the current directory, and
		# since the rest of GRiNS doesn't expect that we save/restore
		# it,
		#
		import os
		curdir = os.getcwd()
		default_dir = directory in ('.', '')
		if default_dir and FileDialog.last_location:
			directory = FileDialog.last_location
		dlg.SetOFNInitialDir(directory)
		result=dlg.DoModal()
		if default_dir:
			FileDialog.last_location = os.getcwd()
		os.chdir(curdir)
		if result==win32con.IDOK:
			if cb_ok: cb_ok(dlg.GetPathName())
		else:
			if cb_cancel: cb_cancel()
	# Returns the filename selected. Must be called after the dialog dismised.
	def GetPathName(self):
		return self._dlg.GetPathName()

#######################################

""" @win32doc|shell_execute
The shell function calls the win32 functions ShellExecute with the given url and verb
The verb can be one of 'open','edit','print'
"""

# url parsing
import MMurl,ntpath, urllib

def shell_execute(url,verb='open'):
	utype, _url = MMurl.splittype(url)
	host, _url = MMurl.splithost(_url)
	islocal = (not utype and not host)
	if islocal:
		filename=MMurl.url2pathname(MMurl.splithost(url)[1])
		if os.path.isfile(filename):
			if not os.path.isabs(filename):
				filename=os.path.join(os.getcwd(),filename)
				filename=ntpath.normpath(filename)
		else: 
			win32ui.MessageBox(filename+'\nnot found')
			return
		url=filename
	rc,msg=Sdk.ShellExecute(0,verb,url,None,"", win32con.SW_SHOW)
	if rc<=32:win32ui.MessageBox('Cannot '+ verb +' '+url+'\n'+msg,'GRiNS')


""" @win32doc|htmlwindow
Class htmlwindow just calls the shell to open the given file
"""

class htmlwindow:
	def __init__(self,url):
		self.goto_url(url)
	def goto_url(self,url):
		shell_execute(url,'open')	
	def close(self):pass
	def is_closed(self):return 1
		


