__version__ = "$Id$"

""" @win32doc|MediaChannel

This module encapsulates a sufficient part
of the DirectShow infrastructure in order to
implement GRiNS audio and video media channels.

Any media supported by Windows Media Player
are also supported by this module:
(.avi,.asf,.rmi,.wav,.mpg,.mpeg,.m1v,.mp2,.mpa, 
.mpe,.mid,.rmi,.qt,.aif,.aifc,.aiff,.mov,.au,.snd)
---	Exception: asx files can be played directly by MediaPlayer
	or the MediaPlayer control but not by this module. 
	(we could use the control for win32 but to leave open
	the porting to other platforms I prefer not to use it)
	This module can be used to play the asf streams 
	referenced in asx files. So, we need to parse the asx 
	files first using the ASXParser.
	(I am not sure of how asx support will evolve yet)

The GraphBuilder is a COM object that builds a graph of filters
appropriate to parse-render each media type from those filters
available on the machine. A new parsing filter installed enhances 
the media types that can be played both by GRiNS and Windows MediaPlayer.

The Python object exported by the Cpp module GraphBuilder
supports the interface:
interface IGraphBuilder:
	def RenderFile(self,fn):return 1

	def Run(self):pass
	def Stop(self):pass
	def Pause(self):pass

	def GetDuration(self):return 0
	def SetPosition(self,pos):pass
	def GetPosition(self):return 0
	def SetStopTime(self,pos):pass
	def GetStopTime(self):return 0

	def SetVisible(self,f):pass
	def SetWindow(self,w):pass

"""

# node attributes
import MMAttrdefs

# URL module
import MMurl, urllib

# std win32 libs 
import win32ui, win32con

# DirectShow support
DirectShowSdk=win32ui.GetDS()

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# private redraw message
WM_REDRAW=win32con.WM_USER+102

# use: addclosecallback, genericwnd, register, unregister
import windowinterface


class MediaChannel:
	def __init__(self):

		# DirectShow Graph builders
		self._armBuilder=None
		self._playBuilder=None
		self._playBegin=0
		self._playEnd=0
		self._armFileHasBeenRendered=0
		self._playFileHasBeenRendered=0
		
		# main thread monitoring fiber id
		self._fiber_id=0
		self.__playdone=1
		self.__paused=1

		# notification mechanism for not window channels
		self._notifyWindow = None
		self.__window = None

		# asx support
		self.initASX()

		# release any resources on exit
		import windowinterface
		windowinterface.addclosecallback(self.release_res,())
		
	def release_player(self):
		if self._playBuilder:
			self._playBuilder.Stop()
			self._playBuilder.Release()
			self._playBuilder=None
		if self._notifyWindow and self._notifyWindow.IsWindow():
			self._notifyWindow.DestroyWindow()
		self._notifyWindow=None

	def release_armed_player(self):
		if self._armBuilder:
			self._armBuilder.Stop()
			self._armBuilder.Release()
			self._armBuilder=None
	
	def release_res(self):
		self.release_armed_player()
		self.release_player()

	# We must start downloading here,
	# show a message on the media subwindow
	# and return immediately.
	# For local files we don't have to do anything. 
	# Do not use  MMurl.urlretrieve since as it
	# is now implemented blocks the application.
	def prepare_player(self, node = None):	
		self.release_armed_player()
		try:
			self._armBuilder = DirectShowSdk.CreateGraphBuilder()
		except:
			self._armBuilder=None

		if not self._armBuilder:
			print 'failed to create GraphBuilder'
			return 0

		url=self.getfileurl(node)
		self._armIsAsx=0
		if self.isASX(url):
			self._armIsAsx=1
			return self.prepareASX(node)
		
		url = MMurl.canonURL(url)
		url=urllib.unquote(url)
		if not self._armBuilder.RenderFile(url):
			self._armFileHasBeenRendered=0
			print 'Failed to render',url
			return -1

		self._armFileHasBeenRendered=1
		return 1


	def playit(self, node, window = None):
		if not self._armBuilder:
			return 0

		self.release_player()
		self._playBuilder=self._armBuilder
		self._armBuilder=None
		if not self._armFileHasBeenRendered:
			self._playFileHasBeenRendered=0
			return 0
		self._playFileHasBeenRendered=1
		self.arm2playASX()		
		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		duration = MMAttrdefs.getattr(node, 'duration')
		clip_begin = self.getclipbegin(node,'sec')
		clip_end = self.getclipend(node,'sec')
		self._playBuilder.SetPosition(clip_begin)
		self._playBegin = clip_begin
		if clip_end:
			self._playBuilder.SetStopTime(clip_end)
			self._playEnd = clip_end
		else:
			self._playEnd=self._playBuilder.GetDuration()

		if window:
			self.adjustMediaWnd(node,window,self._playBuilder)
			self._playBuilder.SetWindow(window,WM_GRPAPHNOTIFY)
			window.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)			
		elif not self._notifyWindow:
			self._notifyWindow = windowinterface.genericwnd()
			self._notifyWindow.create()
			self._notifyWindow.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
			self._playBuilder.SetNotifyWindow(self._notifyWindow,WM_GRPAPHNOTIFY)
		self.__playdone=0
		self.__paused=0
		self._playBuilder.Run()
		self.register_for_timeslices()
		if duration > 0:
			self._qid = self._scheduler.enter(duration, 0, self.playdone, (0,))
		elif self.play_loop == 0:
			self.playdone(0)
		return 1

					
	def pauseit(self, paused):
		if self._playBuilder:
			if paused:
				self._playBuilder.Pause()
			else:
				self._playBuilder.Run()
		self.__paused=paused

	def stopit(self):
		self.release_player()
		
	def showit(self,window):
		if self._playBuilder: 
			self._playBuilder.SetVisible(1)

	def paint(self):
		if hasattr(self,'window') and self.window and self._playFileHasBeenRendered:
			self.window.UpdateWindow()

	# Set Window Media window size from scale and center attributes
	def adjustMediaWnd(self,node,window,builder):
		if not window: return
		left,top,width,height=builder.GetWindowPosition()
		left,top,right,bottom = window.GetClientRect()
		x,y,w,h=left,top,right-left,bottom-top

		# node attributes
		import MMAttrdefs
		scale = MMAttrdefs.getattr(node, 'scale')
		center = MMAttrdefs.getattr(node, 'center')

		if scale > 0:
			width = int(width * scale)
			height = int(height * scale)
			if width>w or height>h:
				wscale=float(w)/width
				hscale=float(h)/height
				scale=min(wscale,hscale)
				width = min(int(width * scale), w)
				height = min(int(height * scale), h)
				center=1	
			if center:
				x = x + (w - width) / 2
				y = y + (h - height) / 2
		else:
			# fit in window
			wscale=float(w)/width
			hscale=float(h)/height
			scale=min(wscale,hscale)
			width = min(int(width * scale), w)
			height = min(int(height * scale), h)
			x = x + (w - width) / 2
			y = y + (h - height) / 2

		rcMediaWnd=(x, y, width,height)
		builder.SetWindowPosition(rcMediaWnd)

	def update(self,dc=None):
		if self._playBuilder and self._playFileHasBeenRendered and (self.__playdone or self.__paused):
			self.window.RedrawWindow()
	
	# capture end of media
	def OnGraphNotify(self,params):
		if self._playBuilder and not self.__playdone:
			t=self._playBuilder.GetPosition()
			if t>=self._playEnd:self.OnMediaEnd()

	def OnMediaEnd(self):
		if not self._playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self._playBuilder.SetPosition(self._playBegin)
				self._playBuilder.Run()
				return
			# no more loops but check for ASX playlist
			self.__playdone=1
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self._playBuilder.SetPosition(0)
		self._playBuilder.Run()

	################## AFX support
	def initASX(self):
		self._armIsAsx=0
		self._armAsxPlayList=[]
		self._armAsxIndex=0
		self._playIsAsx=0
		self._playAsxPlayList=[]
		self._playAsxIndex=0

	def arm2playASX(self):
		self._playIsAsx=self._armIsAsx
		self._playAsxPlayList=self._armAsxPlayList
		self._playAsxIndex=self._armAsxIndex

	def isASX(self,url):
		import posixpath
		base, ext = posixpath.splitext(url)
		return ext=='.asx'
	
	def prepareASX(self,node):
		import ASXParser
		x=ASXParser.ASXParser()
		url=self.getfileurl(node)
		x.read(url)
		
		# set ASX armed info
		self._armAsxPlayList=x._playlist
		self._armAsxIndex=0

		if not self.armNextAsf():
			return -1
		return 1

	def armNextAsf(self):
		if self._armAsxIndex >= len(self._armAsxPlayList):
			return 0
		asf_url=self._armAsxPlayList[self._armAsxIndex]
		self._armAsxIndex=self._armAsxIndex+1
		if not self._armBuilder.RenderFile(asf_url):
			print 'Failed to render',asf_url
			return 0
		return 1
		
	############################################################## 
	# ui delays management:
	# What the following methods implement is a safe
	# way to dedect media end (by polling). 
	# The notification mechanism through OnGraphNotify should 
	# be enough but it is not since when the app enters a modal loop 
	# (which happens for example when we manipulate menus etc)
	# the notification for some unknown reason does not reach the window.
	# Needed until we have a simpler safe way to dedect media end.
	# A static way is not sufficient since we don't know the delays.
	def on_idle_callback(self):
		if self._playBuilder and not self.__playdone:
			t_sec=self._playBuilder.GetPosition()
			if t_sec>=self._playEnd:self.OnMediaEnd()
			self.paint()

	def is_callable(self):
		return self._playBuilder
	def register_for_timeslices(self):
		if self._fiber_id: return
		import windowinterface
		self._fiber_id=windowinterface.register((self.is_callable,()),(self.on_idle_callback,()))
	def unregister_for_timeslices(self):
		if not self._fiber_id: return
		import windowinterface
		windowinterface.unregister(self._fiber_id)
		self._fiber_id=0

