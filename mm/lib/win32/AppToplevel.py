__version__ = "$Id$"

# @win32doc|AppTopLevel
# An instance of the _Toplevel class defined in this module
# represents the platform dependent part of the application.
#  (The other part is platform independent and is an instance of Main)
# It contains the main message loop of the application which beyond dispatching messages
# it serves a delta timer (see tcp process) and tasks registered for timeslices.
# This class is also the main interface between the core part of the system
# that is platform independent with the part of the system that is 
# platform dependent. This interface is exposed to the core system through
# a module (windowinterface.py) which contains mainly alias to members of this class

import win32ui, win32con, win32api
Sdk=win32ui.GetWin32Sdk()
Afx=win32ui.GetAfx()

import sysmetrics

import MainFrame

from appcon import *
from win32ig import win32ig
import string
import MMmimetypes
import grins_mimetypes
import GenWnd

import os
from stat import ST_MTIME
import features
import version

def beep():
	win32api.MessageBeep()

################
		 
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
	
		self._waiting=0
		self._idles = {}

		# generic wnd class
		self.genericwnd=GenWnd.GenWnd
		
		self._in_create_box=None
		self._do_init()

	# Part of the constructor initialization
	def _do_init(self):
		if self._initialized:
			raise error, 'can only initialize once'
		self._initialized = 1	
		self._closecallbacks = []
		self._subwindows = []	# A list of child windows, each are of type
		self._bgcolor = 255, 255, 255 # white
		self._fgcolor =   0,   0,   0 # black
		self._running = 0
		self._pseudo_id_list = []
		self._cursor = ''

		self._image_cache = {}
		self._image_docmap = {}
				
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._idles = {}
		self.__idleid = 0
		self._time = float(Sdk.GetTickCount())/TICKS_PER_SECOND

		self._apptitle=None
		self._appadornments=None
		self._appcommandlist=None

		self._activeDocFrame=None
		self._register_entries=[]

		# embedding support state
		self._peerdocid = 0
		self._embeddedcallbacks = {}
		self._most_recent_docframe = None

		# os timer
		self._os_timer_id = 0
		self._os_timer_wnd = None

	# set/get active doc frame (MDIFrameWnd)
	def setActiveDocFrame(self,frame):
		self._activeDocFrame=frame
	def getActiveDocFrame(self):
		return self._activeDocFrame

	# Paint all the windows now
	def forcePaint(self):
		for w in self._subwindows:
			w._forcePaint()
		
	# Call by the core to close the application
	def close(self):
		if self._subwindows:
			self._subwindows[0].onApplicationExit()
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
			if hasattr(win,'DestroyWindow'):
				win.DestroyWindow()
		self._closecallbacks = []
		self._subwindows = []

		import Font
		Font.delfonts()
		

	# Registration function for close callbacks
	def addclosecallback(self, func, args):
		self._closecallbacks.append((func, args))

	def removeclosecallback(self, func, args):
		self._closecallbacks.remove((func, args))

	# Called by the core to create a window
	def newwindow(self, x, y, w, h, title,
		      pixmap = 0, units = UNIT_MM,
		      adornments = None, canvassize = None,
		      commandlist = None, resizable = 1, bgcolor = None):
		frame = adornments.get('frame')
		if frame is None:
			raise error, 'newwindow without frame specification'
		wnd = frame.newwindow(x, y, w, h, title,
		      pixmap, units,
		      adornments, canvassize,
		      commandlist, resizable, bgcolor)
		if hasattr(wnd, '_viewport'):
			return wnd._viewport
		return wnd


	############ SDI/MDI Model Support
	# Called by win32 modules to create the main frame
	def createmainwnd(self,title = None, adornments = None, commandlist = None):
		self._apptitle = version.title
		if adornments:
			self._appadornments=adornments
		if commandlist:
			self._appcommandlist=commandlist
		if len(self._subwindows)==0:
			frame = MainFrame.MDIFrameWnd()
			frame.createOsWnd(self._apptitle)
			frame.init_cmif(None, None, 0, 0, self._apptitle,
				UNIT_MM, self._appadornments,self._appcommandlist)
			self.setActiveDocFrame(frame)
			for r in self._register_entries:
				ev,cb,arg=r
				frame.register(ev,cb,arg)
		return self._subwindows[0]

	# associate the document (TopLevel) with a wnd
	# return the wnd
	# argument cmifdoc is an instance of TopLevel
	def newdocument(self, cmifdoc, adornments=None, commandlist=None):
		for frame in self._subwindows:
			if not frame._cmifdoc:
				frame.setdocument(cmifdoc,adornments,commandlist, self._peerdocid)
				self._most_recent_docframe = frame
				return frame
		frame = MainFrame.MDIFrameWnd()
		frame.createOsWnd(self._apptitle)
		frame.init_cmif(None, None, 0, 0,self._apptitle,
			UNIT_MM,self._appadornments,self._appcommandlist)
		frame.setdocument(cmifdoc, adornments, commandlist, self._peerdocid)
		self._most_recent_docframe = frame
		for r in self._register_entries:
			ev,cb,arg=r
			frame.register(ev,cb,arg)
		return frame
	
	# Returns the active mainwnd
	def getmainwnd(self):
		if len(self._subwindows)==0:
			self.createmainwnd()
		return self.getActiveDocFrame() # return the active

	def get_most_recent_docframe(self):
		return self._most_recent_docframe # of type MainFrame.MDIFrameWnd

	# register events for all main frames (top level wnds)
	def register_event(self,ev,cb,arg):
		self._register_entries.append((ev,cb,arg))
	
	############ /SDI-MDI Model Support	

	#
	# Embedding Support	
	#
	def register_embedded(self, event, func, arg):
		self._embeddedcallbacks[event] = func, arg

	def unregister_embedded(self, event):
		try:
			del self._embeddedcallbacks[event]
		except KeyError:
			pass

	def get_embedded(self, event):
		return self._embeddedcallbacks.get(event)

	def is_embedded(self):
		import __main__
		return hasattr(__main__,'embedded') and __main__.embedded
	
	def enableCOMAutomation(self):
		import __main__
		if hasattr(__main__,'commodule') and __main__.commodule is not None:
			import embedding
			listenerWnd = embedding.ListenerWnd(self)
			self.addclosecallback(listenerWnd.DestroyWindow, ())
			commodule = __main__.commodule
			commodule.SetListener(listenerWnd.GetSafeHwnd())
			commodule.RegisterClassObjects()
	
	#
	# Std interface
	#
	# Displays a text viewer
	# Not used.
	def textwindow(self,text):
		print 'you must request textwindow from a frame'
		sv=self.newviewobj('sview_')
		sv.settext(text)
		self.showview(sv,'sview_')
		if features.editor:
			sv.set_close_commandlist()
		return sv

	# Returns screen size in mm	
	def getsize(self):
		# size of the screen in mm
		return self._scr_width_mm, self._scr_height_mm

	# Returns screen size in pixel
	def getscreensize(self):
		# Return screen size in pixels
		return self._scr_width_pxl, self._scr_height_pxl

	# Returns screen depth
	def getscreendepth(self):
		# Return screen depth
		return sysmetrics.depth


	# Set the application cursor to the cursor with string id
	def setcursor(self, strid):
		if strid == self._cursor:
			return
		App=win32ui.GetApp()
		import win32window
		cursor = win32window.getcursorhandle(strid)
		win32ui.GetWin32Sdk().SetCursor(cursor)
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


	#########################################
	# Main message loop of the application
	def mainloop(self):
		if len(self._subwindows) == 1:
			self.show()
		self._os_timer_wnd = self.genericwnd()
		self._os_timer_wnd.create()
		self._os_timer_wnd.HookMessage(self.OnTimer, win32con.WM_TIMER)
		
		# com automation support
		self.enableCOMAutomation()

		# enter application loop
		win32ui.GetApp().RunLoop()

		# cleanup
		self.StopTimer()
		self._os_timer_wnd.DestroyWindow()
		self._os_timer_wnd = None

	def StartTimer(self):
		if self._os_timer_id == 0 and self._os_timer_wnd is not None:
			self._os_timer_id = self._os_timer_wnd.SetTimer(1,10)

	def StopTimer(self):
		if self._os_timer_id != 0 and self._os_timer_wnd is not None:
			self._os_timer_wnd.KillTimer(self._os_timer_id)
			self._os_timer_id = 0

	def OnTimer(self, params):
		self.serve_events()
		
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
		if not self._timers and not self._idles:
			self.StopTimer()
		if self._waiting:self.setready()				

	# Called by the core sustem to set the waiting cursor
	def setwaiting(self):
		if not self._waiting:
			win32ui.GetApp().BeginWaitCursor()
			self._waiting = 1
			self.StartTimer()

	# Called by the core sustem to remove the waiting cursor
	def setready(self):
		if self._waiting:
			# if you take one call, the end cursor doesn't hide
			win32ui.GetApp().EndWaitCursor()
			win32ui.GetApp().EndWaitCursor()
			self._waiting = 0

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
		self._timers.append((sec - t, cb, self._timer_id))
		#print 'new event:',self._timer_id,sec - t,cb
		self.StartTimer()
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
				if not self._timers and not self._idles:
					self.StopTimer()
				return
		raise 'unknown timer', id
	
	def getcurtime(self):
		return float(Sdk.GetTickCount())/TICKS_PER_SECOND
		
	def settimevirtual(self, virtual):
		pass

	# Register for receiving timeslices
	def setidleproc(self, cb):
		id = self.__idleid
		self.__idleid = self.__idleid + 1
		self._idles[id] = cb
		self.StartTimer()
		return id

	# Register for receiving timeslices
	def cancelidleproc(self, id):
		del self._idles[id]
		if not self._timers and not self._idles:
			self.StopTimer()

	# Dispatch timeslices
	def serve_timeslices(self):
		for onIdle in self._idles.values():
			onIdle()

	################################
		
	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		raise error, 'No select_setcallback for win32'


	################################
	#utility functions
	
	def __check_image_cache(self, file, doc):
		try:
			stat = os.stat(file)
		except:
			stmtime = -1
		else:
			stmtime = stat[ST_MTIME]
		if self._image_cache.has_key(file):
			img, size, mtime = self._image_cache[file]
			if mtime == stmtime:
				# cached value is valid
				return
			win32ig.delete(img)
			del self._image_cache[file]
		if stmtime == -1:
			raise error, 'file does not exist'
		img = win32ig.load(file) # raises error if unsuccessful
		xsize, ysize, depth = win32ig.size(img)
		self._image_cache[file] = img, (xsize, ysize, depth), stmtime
		if self._image_docmap.has_key(doc):
			if file not in self._image_docmap[doc]:
				self._image_docmap[doc].append(file)
		else:
			self._image_docmap[doc]=[file,]

	def _image_size(self, file, doc):
		self.__check_image_cache(file, doc)
		try:
			xsize, ysize, depth = self._image_cache[file][1]
		except KeyError:
			xsize, ysize, depth = win32ig.size(-1)
		return xsize, ysize

	def _image_depth(self, file, doc):
		self.__check_image_cache(file, doc)
		try:
			xsize, ysize, depth = self._image_cache[file][1]
		except KeyError:
			xsize, ysize, depth = win32ig.size(-1)
		return depth

	def _image_handle(self, file, doc):
		self.__check_image_cache(file, doc)
		try:
			return  self._image_cache[file][0]
		except:
			return -1

	def cleardoccache(self, doc):
		if not self._image_docmap.has_key(doc): return
		imglist=self._image_docmap[doc]
		otherimglist=[]
		for otherdoc in self._image_docmap.keys():
			if otherdoc!=doc:
				otherimglist.extend(self._image_docmap[otherdoc])					
		for file in imglist:
			if not self._image_cache.has_key(file):continue
			if file in otherimglist:continue
			img=self._image_cache[file][0]
			del self._image_cache[file]
			win32ig.delete(img)
		del self._image_docmap[doc]

			
	# Returns the size of an image	
	def GetImageSize(self, file):
		f = self.getActiveDocFrame()
		return f._image_size(file)
	
	# Returns the length of a string in pixels	
	def GetStringLength(wnd,str):
		dc = wnd.GetDC()
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
			flags=win32con.OFN_HIDEREADONLY|win32con.OFN_OVERWRITEPROMPT
		if not parent:
			import __main__
			try:
				parent=__main__.toplevel._subwindows[0]
			except IndexError:
				pass
		if not filter or type(filter) == type('') and not '/' in filter:
			# Old style (pattern) filter
			if not filter or filter == '*':
				filter = 'All files (*.*)|*.*||'
				dftext = None
			else:
				filter = '%s|%s||'%(filter, filter)
				dftext = string.split(filter, '.')[-1]
		else:
			# New-style mimetype filter
			descr = None
			if type(filter) == type(''):
				filter = [filter]
			elif filter and filter[0][:1] == '/':
				descr = filter[0][1:]
				filter = filter[1:]
			dftext = None
			newfilter = []
			allext = []
			for f in filter:
				extlist = MMmimetypes.get_extensions(f)
				if not extlist:
					extlist = ('.*',)
				else:
					if not dftext:
						dftext = extlist[0]
					allext = allext + extlist
				description = grins_mimetypes.descriptions.get(f, f)
				# Turn the extension list into the ; separated pattern list
				extlist = string.join(map(lambda x:"*"+x, extlist), ';')
				newfilter.append('%s (%s)|%s'%(description, extlist, extlist))
			if descr:
				extlist = string.join(map(lambda x:"*"+x, allext), ';')
				newfilter.insert(0, '%s|%s'%(descr, extlist))
				if len(newfilter) == 2:
					# special case: don't display two
					# entries that are basically the same
					del newfilter[1]
			elif file and dftext:
				# remove extension
				file = os.path.splitext(file)[0]
			newfilter.append('All files (*.*)|*.*')
			filter = string.join(newfilter, '|') + '||'
##		else:
##			if existing:
##				filter = 'smil files (*.smil;*.smi)|*.smil;*.smi|cmif files (*.cmif)|*.cmif|All files *.*|*.*||'
##			else:
##				filter = 'smil or cmif file (*.smil;*.smi;*.cmif)|*.smil;*.smi;*.cmif|All files *.*|*.*||'
##			dftext = '.smil'
		self._dlg =dlg= win32ui.CreateFileDialog(existing,dftext,file,flags,filter,parent)
		dlg.SetOFNTitle(prompt)

		# get/set current directory since the core assumes remains the same
		# The Windows filebrowser modifies the current directory, and
		# since the rest of GRiNS doesn't expect that we save/restore
		# it,
		#
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

# @win32doc|shell_execute
# The shell function calls the win32 functions ShellExecute with the given url and verb
# The verb can be one of 'open','edit','print'

# url parsing
import MMurl, urlparse

def shell_execute(url,verb='open', showmsg=1):
	utype, host, path, params, query, fragment = urlparse.urlparse(url)
	islocal = (not utype or utype == 'file') and (not host or host == 'localhost')
	if islocal:
		filename=MMurl.url2pathname(path)
		if not os.path.isabs(filename):
			filename=os.path.join(os.getcwd(),filename)
			filename=os.path.normpath(filename)
		if not os.path.exists(filename):
			if os.path.exists(filename+'.lnk'):
				filename = filename + '.lnk'
			else:
				rv = win32con.IDCANCEL
				if verb == 'edit':
					rv = win32ui.MessageBox(filename+': not found.\nCreate?',
						 '', win32con.MB_OKCANCEL)
				if rv == win32con.IDCANCEL:
					return -1
				try:
					open(filename, 'w').close()
				except:
					pass
		url=filename
	rc,msg=Sdk.ShellExecute(0,verb,url,None,"", win32con.SW_SHOW)
	if rc<=32:
		if showmsg:
			win32ui.MessageBox('Explorer cannot '+ verb +' '+url+':\n'+msg,'GRiNS')
		return rc
	return 0

# @win32doc|htmlwindow
# Class htmlwindow just calls the shell to open the given file

class htmlwindow:
	def __init__(self,url):
		self.goto_url(url)
	def goto_url(self,url):
		shell_execute(url,'open')	
	def close(self):pass
	def is_closed(self):return 1
