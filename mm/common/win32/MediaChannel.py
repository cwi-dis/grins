__version__ = "$Id$"

""" @win32doc|MediaChannel

This module encapsulates a sufficient part
of the DirectShow infrastructure to
implement win32 audio and video media channels.

Any media type supported by Windows Media Player is also supported by
this module: (.avi,.asf,.rmi,.wav,.mpg,.mpeg,.m1v,.mp2,.mpa,.mpe,.mid,
.rmi,.qt,.aif,.aifc,.aiff,.mov,.au,.snd)

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
import win32dxm

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
		self.__fiber_id=None
		self.__playdone=1

		# notification mechanism for not window channels
		self.__notifyWindow = None
		self.__window = None
		
	def release_player(self):
		if self.__playBuilder:
			self.__playBuilder=None
		if self.__notifyWindow and self.__notifyWindow.IsWindow():
			self.__notifyWindow.DestroyWindow()
		self.__notifyWindow=None

	def release_armed_player(self):
		if self.__armBuilder:
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
	def prepare_player(self, node = None, window=None):	
		self.release_armed_player()
		try:
			self.__armBuilder = win32dxm.GraphBuilder()
		except:
			self.__armBuilder=None

		if not self.__armBuilder:
			raise error, 'failed to create GraphBuilder'

		url=self.__channel.getfileurl(node)
		if not url:
			raise error, 'No URL on node'
		
		if MMurl.urlretrieved(url):
			url = MMurl.urlretrieve(url)[0]
		else:
			url = MMurl.canonURL(url)
			url = urllib.unquote(url)

		if not self.__armBuilder.RenderFile(url, self.__channel._exporter):
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

		# get duration in secs (float)
		duration = node.GetAttrDef('duration', None)
		clip_begin = self.__channel.getclipbegin(node,'sec')
		clip_end = self.__channel.getclipend(node,'sec')
		self.__playBegin = clip_begin

		if duration is not None and duration >= 0:
			if not clip_end:
				clip_end = self.__playBegin + duration
			else:
				clip_end = min(clip_end, self.__playBegin + duration)
		if clip_end:
			self.__playBuilder.SetStopTime(clip_end)
			self.__playEnd = clip_end
		else:
			self.__playEnd = self.__playBuilder.GetDuration()

		t0 = self.__channel._scheduler.timefunc()
		if t0 > node.start_time and not self.__channel._exporter:
			if __debug__:
				print 'skipping',node.start_time,t0,t0-node.start_time
			mediadur = self.__playEnd - self.__playBegin
			late = t0 - node.start_time
			if late > mediadur:
				self.playdone(0, node.start_time + mediadur)
				return 1
			clip_begin = clip_begin + late
		self.__playBuilder.SetPosition(clip_begin)

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
		self.__playBuilder.Run()
		self.__register_for_timeslices()
		return 1

	def pauseit(self, paused):
		if self.__playBuilder:
			if paused:
				self.__playBuilder.Pause()
			else:
				self.__playBuilder.Run()

	def stopit(self):
		if self.__playBuilder:
			self.__playBuilder.Stop()
		
	def freezeit(self):
		if self.__playBuilder:
			self.__playBuilder.Pause()
		
	def showit(self,window):
		if self.__playBuilder: 
			self.__playBuilder.SetVisible(1)

	def destroy(self):
		self.__unregister_for_timeslices()
		self.release_player()

	def setsoundlevel(self, lev):
		print 'setsoundlevel', lev
		pass

	# Set Window Media window size from scale and center, and coordinates attributes
	def adjustMediaWnd(self,node,window,builder):
		if not window: return
		builder.SetWindowPosition(self.__channel.getMediaWndRect())

	def paint(self):
		if not hasattr(self.__channel,'window'): return
		window = self.__channel.window
		if window and self.__playFileHasBeenRendered:
			window.paint()
	
	# capture end of media
	def OnGraphNotify(self,params):
		if self.__playBuilder and not self.__playdone:
			t=self.__playBuilder.GetPosition()
			if t>=self.__playEnd:self.OnMediaEnd()

	def OnMediaEnd(self):
		if not self.__playBuilder:
			return		
		self.__playdone=1
		self.__channel.playdone(0, self.__channel._played_node.start_time + self.__playEnd - self.__playBegin)
		
	def onIdle(self):
		if self.__playBuilder and not self.__playdone:
			t_sec=self.__playBuilder.GetPosition()
			if t_sec>=self.__playEnd:self.OnMediaEnd()
			self.paint()
	
	def __register_for_timeslices(self):
		if self.__fiber_id is None:
			self.__fiber_id = windowinterface.setidleproc(self.onIdle)

	def __unregister_for_timeslices(self):
		if self.__fiber_id is not None:
			windowinterface.cancelidleproc(self.__fiber_id)
			self.__fiber_id = None


###################################

class VideoStream:
	def __init__(self, channel):
		self.__channel = channel
		self.__mmstream = None
		self.__window = None
		self.__playBegin=0
		self.__playEnd=0
		self.__playdone=1
		self.__fiber_id=None
		self.__rcMediaWnd = None
		self.__qid = self.__dqid = None

	def destroy(self):
		if self.__window:
			self.__window.removevideo()
		del self.__mmstream
		self.__mmstream = None

	def prepare_player(self, node, window):
		if not window:
			raise error, 'not a window'
		ddobj = window._topwindow.getDirectDraw()
		self.__mmstream = win32dxm.MMStream(ddobj)

		url=self.__channel.getfileurl(node)
		if not url:
			raise error, 'No URL on node'
		
		if MMurl.urlretrieved(url):
			url = MMurl.urlretrieve(url)[0]
		else:
			url = MMurl.canonURL(url)
			url = urllib.unquote(url)

		if not self.__mmstream.open(url, self.__channel._exporter):
			raise error, 'Failed to render %s'% url

		return 1

	def playit(self, node, window):
		if not window: return 0
		if not self.__mmstream: return 0

		self.__pausedelay = 0
		self.__pausetime = 0
		duration = node.GetAttrDef('duration', None)
		self.__duration = duration
		clip_begin = self.__channel.getclipbegin(node,'sec')
		clip_end = self.__channel.getclipend(node,'sec')
		self.__playBegin = clip_begin

		if duration is not None and duration >= 0:
			if not clip_end:
				clip_end = clip_begin + duration
			else:
				clip_end = min(clip_end, clip_begin + duration)
		if clip_end:
			self.__playEnd = clip_end
		else:
			self.__playEnd = self.__mmstream.getDuration()

		t0 = self.__channel._scheduler.timefunc()
		if t0 > node.start_time and not self.__channel._exporter:
##			print 'skipping',node.start_time,t0,t0-node.start_time
			mediadur = self.__playEnd - self.__playBegin
			late = t0 - node.start_time
			if late > mediadur:
				self.playdone(0, node.start_time + mediadur)
				return 1
			clip_begin = clip_begin + late
		self.__mmstream.seek(clip_begin)
		
		self.__playdone=0

		window.setvideo(self.__mmstream._dds, self.__channel.getMediaWndRect(), self.__mmstream._rect)
		self.__window = window
		if self.__duration:
			self.__node = node
			self.__dqid = self.__channel._scheduler.enterabs(node.start_time + (self.__iteration + 1) * self.__duration, 0, self.onMediaEnd, ())
		self.__mmstream.run()
		self.__mmstream.update()
		self.__window.update()
		self.__register_for_timeslices()

		return 1

	def stopit(self):
		if self.__dqid:
			try:
				self.__channel._scheduler.cancel(self.__dqid)
			except:
				pass
			self.__dqid = None
		if self.__qid:
			try:
				self.__channel._scheduler.cancel(self.__qid)
			except:
				pass
			self.__qid = None
		if self.__mmstream:
			self.__mmstream.stop()
			self.__unregister_for_timeslices()

	def pauseit(self, paused):
		if self.__mmstream:
			t0 = self.__channel._scheduler.timefunc()
			if paused:
				if self.__dqid:
					try:
						self.__channel._scheduler.cancel(self.__dqid)
					except:
						pass
					self.__dqid = None
				if self.__qid:
					try:
						self.__channel._scheduler.cancel(self.__qid)
					except:
						pass
					self.__qid = None
				self.__mmstream.stop()
				self.__unregister_for_timeslices()
				self.__pausetime = t0
			else:
				self.__pausedelay = self.__pausedelay + t0 - self.__pausetime
				self.__mmstream.run()
				self.__register_for_timeslices()
				if self.__duration:
					self.__dqid = self.__channel._scheduler.enterabs(self.__node.start_time + self.__pausedelay + (self.__iteration + 1) * self.__duration, 0, self.onMediaEnd, ())

	def freezeit(self):
		if self.__mmstream:
			self.__mmstream.stop()
			self.__unregister_for_timeslices()

	def onMediaEnd(self):
		if not self.__mmstream:
			return		
		self.__playdone=1
		self.__channel.playdone(0, self.__channel._played_node.start_time + self.__playEnd - self.__playBegin)
		self.__node = None
		del self.__node

	def onIdle(self):
		if self.__mmstream and not self.__playdone:
			running = self.__mmstream.update()
			t_sec = self.__mmstream.getTime()
			if self.__window:
				self.__window.update(self.__window.getwindowpos())
			if not running or t_sec >= self.__playEnd:
				if not self.__duration:
					self.onMediaEnd()
	
	def __register_for_timeslices(self):
		if self.__fiber_id is None:
			self.__fiber_id = windowinterface.setidleproc(self.onIdle)

	def __unregister_for_timeslices(self):
		if self.__fiber_id is not None:
			windowinterface.cancelidleproc(self.__fiber_id)
			self.__fiber_id = None


