__version__ = "$Id$"

#
# WIN32 Sound Channel
#

""" @win32doc|SoundChannel
The SoundChannel extends Channel.ChannelAsync

In this module ue use an object called GraphBuilder
that supports the interface:

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

	def SetNotifyWindow(self,w):pass

Note that the same object is used for the NTVideoChannel.
The MidiChannel is an alias to the SoundChannel

For more on the DirectShow architecture see MS documentation.

"""

# the core
import Channel

# node attributes
import MMAttrdefs

# url parsing
import os, ntpath, urllib, MMurl

# std win32 libs 
import win32ui,win32con

# DirectShow support
DirectShowSdk=win32ui.GetDS()

# private graph notification message
WM_GRPAPHNOTIFY=win32con.WM_USER+101

# generic wnd for implementing notification mechanism
from windowinterface import genericwnd

debug=0

class SoundChannel(Channel.ChannelAsync):
	node_attrs = Channel.ChannelAsync.node_attrs + ['duration',
						'clipbegin', 'clipend']
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		
		# DirectShow Graph builder
		self._playBuilder=None
		self._playBegin=0
		self._playEnd=0

		# notification mechanism
		self._notifyWindow = None

		# scheduler notification mechanism
		self.__qid=None

		# main thread monitoring fiber id
		self._fiber_id=0
		self.__playdone=1

		# release any resources on exit
		import windowinterface
		windowinterface.addclosecallback(self.release_res,())

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def do_hide(self):
		self.release_res()
		Channel.ChannelAsync.do_hide(self)

	def destroy(self):
		self.release_res()
		self.unregister_for_timeslices()
		Channel.ChannelAsync.destroy(self)

	def release_res(self):
		if self._playBuilder:
			self._playBuilder.Stop()
			self._playBuilder.Release()
		self._playBuilder=None
		if self._notifyWindow and self._notifyWindow.IsWindow():
			self._notifyWindow.DestroyWindow()
		self._notifyWindow=None

	def do_arm(self, node, same=0):
		if debug:print 'SoundChannel.do_arm('+`self`+','+`node`+'same'+')'
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if not self._playBuilder:
			self._playBuilder=DirectShowSdk.CreateGraphBuilder()
		if not self._playBuilder:
			self.showwarning(node,'System missing infrastructure to playback')
		return 1


	def do_play(self, node):
		if debug: print 'SoundChannel.do_play('+`self`+','+`node`+')'
		if not self._playBuilder:
			return

		url = MMurl.canonURL(self.getfileurl(node))
		if not self._playBuilder.RenderFile(url):
			print 'Failed to render',url
			return

		self.play_loop = self.getloop(node)

		# documentation correction
		# get duration in secs (float)
		duration = MMAttrdefs.getattr(node, 'duration')
		if duration > 0:
			self.__qid = self._scheduler.enter(duration, 0, self._stopplay, ())

		clip_begin = self.getclipbegin(node,'sec')
		clip_end = self.getclipend(node,'sec')
		self._playBuilder.SetPosition(int(clip_begin*1000))
		self._playBegin = int(clip_begin*1000)
		if clip_end:
			self._playBuilder.SetStopTime(int(clip_end*1000))
			self._playEnd = int(clip_end)*1000
		else:
			self._playEnd=self._playBuilder.GetDuration()
		if not self._notifyWindow:
			self._notifyWindow = genericwnd()
			self._notifyWindow.create()
			self._notifyWindow.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)
		self._playBuilder.SetNotifyWindow(self._notifyWindow,WM_GRPAPHNOTIFY)
		self._playBuilder.Run()
		self.register_for_timeslices()
		self.__playdone=0

		if self.play_loop == 0 and duration == 0:
			self.__playdone=1
			self.playdone(0)

	# scheduler callback, at end of duration
	def _stopplay(self):
		self.__qid = None
		self.__playdone=1
		self.playdone(0)

	# part of stop sequence
	def stopplay(self, node):
		if self.__qid is not None:
			self._scheduler.cancel(self.__qid)
			self.__qid = None
		if self._playBuilder:
			self.release_res()
		Channel.ChannelAsync.stopplay(self, node)

	# toggles between pause and run
	def setpaused(self, paused):
		self._paused = paused
		if self._playBuilder:
			if self._paused:
				self._playBuilder.Pause()
			else:
				self._playBuilder.Run()

	# capture end of media
	def OnGraphNotify(self,params):
		if debug: print 'SoundChannel: OnGraphNotify',`self`
		if self._playBuilder:
			t_msec=self._playBuilder.GetPosition()
			if t_msec>=self._playEnd:self.OnMediaEnd()

	def OnMediaEnd(self):
		if debug: print 'SoundChannel: OnMediaEnd',`self`
		if not self._playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops
				self._playBuilder.SetPosition(self._playBegin)
				self._playBuilder.Run()
				return
			# no more loops
			self.__playdone=1
			# if event wait scheduler
			if self.__qid is not None:return
			# else end
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self._playBuilder.SetPosition(0)
		self._playBuilder.Run()


############################### ui delays management
	def on_idle_callback(self):
		if debug: print 'SoundChannel.on_idle_callback',`self`
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

############################ 
# showwarning if the infrastucture is missing.
# The user should install Windows Media Player
# since then this infrastructure is installed

	def showwarning(self,node,inmsg):
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		chtype = self.__class__.__name__[:-7] # minus "Channel.ChannelAsync"
		windowinterface.showmessage('%s\n'
						    '%s node %s on Channel.ChannelAsync %s' % (inmsg, chtype, name, self._name), mtype = 'warning')

