__version__ = "$Id$"

""" @win32doc|MediaChannel

This module encapsulates some of the DirectShow infrastructure.
Contains the common part used by Video and Sound Channels.

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

import windowinterface
import MMurl

# node attributes
import MMAttrdefs

# std win32 libs 
import win32ui,win32con

# DirectShow support
DirectShowSdk=win32ui.GetDS()

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# private message to redraw video after resize
WM_REDRAW=win32con.WM_USER+102

# generic wnd for implementing notification mechanism
from windowinterface import genericwnd

class MediaChannel:
	def __init__(self):
		# DirectShow Graph builder
		self._playBuilder=None
		self._playBegin=0
		self._playEnd=0

		# scheduler notification mechanism
		self.__qid=None

		# main thread monitoring fiber id
		self._fiber_id=0
		self.__playdone=1

		# notification mechanism for not window channels
		self._notifyWindow = None

		# release any resources on exit
		import windowinterface
		windowinterface.addclosecallback(self.release_player,())


	def release_player(self):
		if self._playBuilder:
			self._playBuilder.Stop()
			self._playBuilder.Release()
			self._playBuilder=None
		if self._notifyWindow and self._notifyWindow.IsWindow():
			self._notifyWindow.DestroyWindow()
		self._notifyWindow=None

	def prepare_player(self, node = None):
		if not self._playBuilder:
			try:
				self._playBuilder = DirectShowSdk.CreateGraphBuilder()
			except:
				self._playBuilder=None
		if not self._playBuilder:
			return 0
		return 1

	def playit(self, node, window = None):
		if not self._playBuilder:
			return

		url = MMurl.canonURL(self.getfileurl(node))
		if not self._playBuilder.RenderFile(url):
			print 'Failed to render',url
			return

		self.play_loop = self.getloop(node)

		# get duration in secs (float)
		# cancel pending event
		if self.__qid is not None:
			self._scheduler.cancel(self.__qid)
		duration = MMAttrdefs.getattr(node, 'duration')
		if duration > 0:
			self.__qid=self._scheduler.enter(duration, 0, self._stopplay, ())
			
		clip_begin = self.getclipbegin(node,'sec')
		clip_end = self.getclipend(node,'sec')
		self._playBuilder.SetPosition(int(clip_begin*1000))
		self._playBegin = int(clip_begin*1000)
		if clip_end:
			self._playBuilder.SetStopTime(int(clip_end*1000))
			self._playEnd = int(clip_end)*1000
		else:
			self._playEnd=self._playBuilder.GetDuration()

		if window is not None:
			self.adjustMediaWnd(node,window)
			self._playBuilder.SetWindow(window,WM_GRPAPHNOTIFY)
			window.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
			self.window.HookMessage(self.redraw,WM_REDRAW)
			self._playBuilder.Run()
			self._playBuilder.SetVisible(1)
			window.PostMessage(WM_REDRAW)
		elif self._notifyWindow is None:
			self._notifyWindow = genericwnd()
			self._notifyWindow.create()
			self._notifyWindow.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
			self._playBuilder.SetNotifyWindow(self._notifyWindow,WM_GRPAPHNOTIFY)
			self._playBuilder.Run()
		self.register_for_timeslices()
		self.__playdone=0


	def pauseit(self, paused):
		if self._playBuilder:
			if paused:
				self._playBuilder.Pause()
			else:
				self._playBuilder.Run()

	def stopit(self):
		if self.__qid is not None:
			self._scheduler.cancel(self.__qid)
			self.__qid = None
		self.release_player()

	def showit(self,wnd):
		if self._playBuilder:
			self._playBuilder.SetWindow(wnd,WM_GRPAPHNOTIFY)
		if wnd:wnd.RedrawWindow()

	# scheduler callback, at end of duration
	def _stopplay(self):
		self.__qid = None
		self.__playdone=1
		self.playdone(0)

	# Set Window Media window size from scale and center attributes
	def adjustMediaWnd(self,node,window):
		if not window: return
		left,top,width,height=self._playBuilder.GetWindowPosition()
		left,top,right,bottom = window.GetClientRect()
		x,y,w,h=left,top,right-left,bottom-top

		# node attributes
		import MMAttrdefs
		scale = MMAttrdefs.getattr(node, 'scale')
		center = MMAttrdefs.getattr(node, 'center')

		if scale > 0:
			width = min(width * scale, w)
			height = min(height * scale, h)
			if center:
				x = x + (w - width) / 2
				y = y + (h - height) / 2
		else:
			# fit in window
			width = w
			height = h

		rcMediaWnd=(x, y, width,height)
		self._playBuilder.SetWindowPosition(rcMediaWnd)

	def redraw(self,params):
		if self.window:
			self.window.RedrawWindow()

	# capture end of media
	def OnGraphNotify(self,params):
		if self._playBuilder and not self.__playdone:
			t_msec=self._playBuilder.GetPosition()
			if t_msec>=self._playEnd:self.OnMediaEnd()

	def OnMediaEnd(self):
		if debug: print 'VideoChannel: OnMediaEnd',`self`
		if not self._playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self._playBuilder.SetPosition(self._playBegin)
				self._playBuilder.Run()
				return
			# no more loops
			self.__freeze()
			self.__playdone=1
			# if event wait scheduler
			if self.__qid is not None:return
			# else end
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self._playBuilder.SetPosition(0)
		self._playBuilder.Run()


############################### 
# ui delays management
# scheduled to be removed when we find a simpler mechanism 

	def on_idle_callback(self):
		if self._playBuilder and not self.__playdone:
			t_msec=self._playBuilder.GetPosition()
			if t_msec>=self._playEnd:self.OnMediaEnd()

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
