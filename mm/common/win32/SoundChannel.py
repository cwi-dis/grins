__version__ = "$Id$"

#
# WIN32 Sound channel.
#

""" @win32doc|SoundChannel
The SoundChannel extends Channel
(although it repeats the ChannelAsync implementation)

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


We have implemented an object that supports this interface 
by using the win32 DirectShow Sdk. 
The C++ module that exports to Python this object is GraphBuilder.cpp 
in thre folder cmif/win32/src/win32ext.
We get access to the this module from the win32ui 
which acts as a module server in this context by the call:
DirectShowSdk=win32ui.GetDS()
and request an object with the above interface with the call
builder=DirectShowSdk.CreateGraphBuilder()

Note that the same object is used for the NTVideoChannel.
The MidiChannel is an alias to the SoundChannel

For more on the DirectShow architecture see MS documentation.

"""

from Channel import *

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

class SoundChannel(Channel):
	node_attrs = Channel.node_attrs + ['duration',
						'clipbegin', 'clipend']
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.__init__(self, name, attrdict, scheduler, ui)
		
		# DirectShow Graph builders
		self._builders={}

		# active builder from self._builders
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
		Channel.do_hide(self)

	def destroy(self):
		self.release_res()
		self.unregister_for_timeslices()
		Channel.destroy(self)

	def release_res(self):
		for b in self._builders.values():
			b.Stop()
			b.Release()
		del self._builders
		self._builders={}
		self._playBuilder=None
		if self._notifyWindow and self._notifyWindow.IsWindow():
			self._notifyWindow.DestroyWindow()
		self._notifyWindow=None

	def do_arm(self, node, same=0):
		if debug:print 'SoundChannel.do_arm('+`self`+','+`node`+'same'+')'
		if node in self._builders.keys():
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		fn = self.getfileurl(node)
		try:
			fn = MMurl.urlretrieve(fn)[0]
		except IOError, arg:
			if type(arg) is type(self):
				arg = arg.strerror
			self.errormsg(node, 'Cannot resolve URL "%s": %s' % (fn, arg))
			return 1
##		fn = self.toabs(fn)
		fn = MMurl.canonURL(fn)
		builder=DirectShowSdk.CreateGraphBuilder()
		if builder:
			if not builder.RenderFile(fn):
				print 'Failed to render',fn
				builder=None
			self._builders[node]=builder
		else:
			print 'Failed to create GraphBuilder'
		return 1

	# Async Channel play
	def play(self, node):
		if debug:print 'SoundChannel.play('+`self`+','+`node`+')'
		self.play_0(node)
		if not self._is_shown or not node.IsPlayable() \
		   or self.syncplay:
			self.play_1()
			return
		if self._is_shown:
			self.do_play(node)
		self.armdone()

	def do_play(self, node):
		if debug: print 'SoundChannel.do_play('+`self`+','+`node`+')'
		if node not in self._builders.keys():
			print 'node not armed'
			self.playdone(0)
			return

		self.play_loop = self.getloop(node)

		# documentation correction
		# get duration in secs (float)
		duration = MMAttrdefs.getattr(node, 'duration')
		if duration > 0:
			self._scheduler.enter(duration, 0, self._stopplay, ())

		self._playBuilder=self._builders[node]
		if not self._playBuilder:
			self.playdone(0)
			return
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

#		if self.play_loop == 0 and duration == 0:
#			self.__playdone=1
#			self.playdone(0)

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
			self._playBuilder.Stop()
			self._playBuilder=None
		Channel.stopplay(self, node)

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
		if self._playBuilder and not self.__playdone:
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

	def toabs(self,url):
		# no need to duplicate code...
		import Help_
		return Help_.toabs(url)
