__version__ = "$Id$"

""" @win32doc|MediaChannel

This module encapsulates a sufficient part
of the DirectShow infrastructure to
implement win32 audio and video media channels.

Any media type supported by Windows Media Player
is also supported by this module:
(.avi,.asf,.rmi,.wav,.mpg,.mpeg,.m1v,.mp2,.mpa, 
.mpe,.mid,.rmi,.qt,.aif,.aifc,.aiff,.mov,.au,.snd)

Note that DirectShow builds a graph of filters
appropriate to parse-render each media type from those filters
available on the machine. A new parsing filter installed enhances 
the media types that can be played both by GRiNS and Windows MediaPlayer.

"""

# node attributes
import MMAttrdefs

# URL module
import MMurl, urllib

# use: addclosecallback, genericwnd, register, unregister
import windowinterface

# DirectShow support
from win32dxm import GraphBuilder

# we need const WM_USER
import win32con

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# private redraw message
WM_REDRAW=win32con.WM_USER+102

error = 'MediaChannel.error'


class MediaChannel:
	def __init__(self, channel):

		# DirectShow Graph builders
		self.__channel = channel
		self.__armBuilder=None
		self.__playBuilder=None
		self.__playBegin=0
		self.__playEnd=0
		self.__armFileHasBeenRendered=0
		self.__playFileHasBeenRendered=0
		
		# main thread monitoring fiber id
		self.__fiber_id=0
		self.__playdone=1
		self.__paused=1

		# notification mechanism for not window channels
		self.__notifyWindow = None
		self.__window = None
		
	def release_player(self):
		if self.__playBuilder:
			self.__playBuilder.Stop()
			self.__playBuilder=None
		if self.__notifyWindow and self.__notifyWindow.IsWindow():
			self.__notifyWindow.DestroyWindow()
		self.__notifyWindow=None

	def release_armed_player(self):
		if self.__armBuilder:
			self.__armBuilder.Stop()
			self.__armBuilder=None
	
	def release_res(self):
		self.release_armed_player()
		self.release_player()
		self.__channel = None

	# We must start downloading here,
	# show a message on the media subwindow
	# and return immediately.
	# For local files we don't have to do anything. 
	# Do not use  MMurl.urlretrieve since as it
	# is now implemented blocks the application.
	def prepare_player(self, node = None):	
		self.release_armed_player()
		try:
			self.__armBuilder = GraphBuilder()
		except:
			self.__armBuilder=None

		if not self.__armBuilder:
			raise error, 'failed to create GraphBuilder'

		url=self.__channel.getfileurl(node)
		if not url:
			raise error, 'No URL on node'
		
		url = MMurl.canonURL(url)
		url=urllib.unquote(url)
		if not self.__armBuilder.RenderFile(url):
			self.__armFileHasBeenRendered=0
			raise error, 'Failed to render '+url

		self.__armFileHasBeenRendered=1
		return 1


	def playit(self, node, window = None):
		if not self.__armBuilder:
			return 0

		self.release_player()
		self.__playBuilder=self.__armBuilder
		self.__armBuilder=None
		if not self.__armFileHasBeenRendered:
			self.__playFileHasBeenRendered=0
			return 0
		self.__playFileHasBeenRendered=1
		self.play_loop = self.__channel.getloop(node)

		# get duration in secs (float)
		duration = node.GetAttrDef('duration', None)
		repeatdur = MMAttrdefs.getattr(node, 'repeatdur')
		if repeatdur and self.play_loop == 1:
			self.play_loop = 0
		clip_begin = self.__channel.getclipbegin(node,'sec')
		clip_end = self.__channel.getclipend(node,'sec')
		self.__playBuilder.SetPosition(clip_begin)
		self.__playBegin = clip_begin
		if duration is not None and duration >= 0:
			if not clip_end:
				clip_end = clip_begin + duration
			else:
				clip_end = min(clip_end, clip_begin + duration)
		if clip_end:
			self.__playBuilder.SetStopTime(clip_end)
			self.__playEnd = clip_end
		else:
			self.__playEnd = self.__playBuilder.GetDuration()

		if window:
			self.adjustMediaWnd(node,window, self.__playBuilder)
			self.__playBuilder.SetWindow(window,WM_GRPAPHNOTIFY)
			window.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)			
		elif not self.__notifyWindow:
			self.__notifyWindow = windowinterface.genericwnd()
			self.__notifyWindow.create()
			self.__notifyWindow.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
			self.__playBuilder.SetNotifyWindow(self.__notifyWindow,WM_GRPAPHNOTIFY)
		self.__playdone=0
		self.__paused=0
		self.__playBuilder.Run()
		self.register_for_timeslices()
		if repeatdur > 0:
			self.__qid = self.__channel._scheduler.enter(repeatdur, 0, self.__channel.playdone, (0,))
		elif self.play_loop == 0 and repeatdur == 0:
			self.__channel.playdone(0)
		return 1

					
	def pauseit(self, paused):
		if self.__playBuilder:
			if paused:
				self.__playBuilder.Pause()
			else:
				self.__playBuilder.Run()
		self.__paused=paused

	def stopit(self):
		self.release_player()
		
	def showit(self,window):
		if self.__playBuilder: 
			self.__playBuilder.SetVisible(1)

	# Define the anchor area for visible medias
	def prepare_anchors(self, node, window, coordinates):
		if not window: return
	
		# it should be nice to verify this calcul !!!
		
#	 	left,top,width,height=self.__armBuilder.GetWindowPosition()
#	 	print left,top,width,height
#		left,top,right,bottom = window.GetClientRect()
		left,top,w_width,w_height = window.GetClientRect()
#	 	print left,top,right,bottom
#		x,y,w,h=left,top,right-left,bottom-top

		left,top,width,height = window._convert_coordinates(coordinates)
		x,y,w,h = left,top,width,height
		
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

		self._rcMediaWnd=(x, y, width,height)
		return (x/float(w_width), y/float(w_height), width/float(w_width), height/float(w_height))
		
	# Set Window Media window size from scale and center, and coordinates attributes
	def adjustMediaWnd(self,node,window,builder):
		if not window: return
#		left,top,width,height=builder.GetWindowPosition()
#		left,top,right,bottom = window.GetClientRect()
#		x,y,w,h=left,top,right-left,bottom-top
#		if coordinates is not None:
#			left,top,width,height = window._convert_coordinates(coordinates)
#			x,y,w,h = left,top,width,height
		# node attributes
#		import MMAttrdefs
#		scale = MMAttrdefs.getattr(node, 'scale')
#		center = MMAttrdefs.getattr(node, 'center')

#		if scale > 0:
#			width = int(width * scale)
#			height = int(height * scale)
#			if width>w or height>h:
#				wscale=float(w)/width
#				hscale=float(h)/height
#				scale=min(wscale,hscale)
#				width = min(int(width * scale), w)
#				height = min(int(height * scale), h)
#				center=1	
#			if center:
#				x = x + (w - width) / 2
#				y = y + (h - height) / 2
#		else:
			# fit in window
#			wscale=float(w)/width
#			hscale=float(h)/height
#			scale=min(wscale,hscale)
#			width = min(int(width * scale), w)
#			height = min(int(height * scale), h)
#			x = x + (w - width) / 2
#			y = y + (h - height) / 2

#		rcMediaWnd=(x, y, width,height)
		builder.SetWindowPosition(self._rcMediaWnd)

	# XXX: Is it needed?
	def paint(self):
		return 
		if hasattr(self.__channel,'window') and self.__channel.window and self.__playFileHasBeenRendered:
			self.__channel.window.UpdateWindow()

	# XXX: Is it needed?
	def update(self,dc=None):
		return
		if self.__playBuilder and self.__playFileHasBeenRendered and (self.__playdone or self.__paused):
			self.__channel.window.RedrawWindow()
	
	# capture end of media
	def OnGraphNotify(self,params):
		if self.__playBuilder and not self.__playdone:
			t=self.__playBuilder.GetPosition()
			if t>=self.__playEnd:self.OnMediaEnd()

	def OnMediaEnd(self):
		if not self.__playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self.__playBuilder.SetPosition(self.__playBegin)
				self.__playBuilder.Run()
				return
			# no more loops
			self.__playdone=1
			self.__channel.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self.__playBuilder.SetPosition(0)
		self.__playBuilder.Run()

		
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
		if self.__playBuilder and not self.__playdone:
			t_sec=self.__playBuilder.GetPosition()
			if t_sec>=self.__playEnd:self.OnMediaEnd()
			self.paint()

	def is_callable(self):
		return self.__playBuilder
	def register_for_timeslices(self):
		if self.__fiber_id: return
		import windowinterface
		self.__fiber_id=windowinterface.register((self.is_callable,()),(self.on_idle_callback,()))
	def unregister_for_timeslices(self):
		if not self.__fiber_id: return
		import windowinterface
		windowinterface.unregister(self.__fiber_id)
		self.__fiber_id=0

