__version__ = "$Id$"

#
# WIN32 Sound channel.
#

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
		self._playBuilder=None

		# notification mechanism
		self._notifyWindow = genericwnd()
		self._notifyWindow.create()
		self._notifyWindow.HookMessage(self.OnGraphNotify,WM_GRPAPHNOTIFY)

		# scheduler notification mechanism
		self.__qid=None

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def do_hide(self):
		if self._playBuilder:
			self._playBuilder.Stop()
		Channel.do_hide(self)

	def destroy(self):
		del self._builders
		if self._notifyWindow.IsWindow():
			self._notifyWindow.DestroyWindow()
		Channel.destroy(self)

	def do_arm(self, node, same=0):
		if debug:print 'SoundChannel.do_arm('+`self`+','+`node`+'same'+')'
		if node in self._builders.keys():
			return 1
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		fn = self.getfileurl(node)
		fn = MMurl.urlretrieve(fn)[0]
		fn = self.toabs(fn)
		builder=DirectShowSdk.CreateGraphBuilder()
		if builder:
			builder.RenderFile(fn)
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
		# get duration in secs (float)
		duration = MMAttrdefs.getattr(node, 'duration')
		if duration > 0:
			self._scheduler.enter(duration, 0, self._stopplay, ())

		self._playBuilder=self._builders[node]
		self._playBuilder.SetPosition(0)
		self._playBuilder.SetNotifyWindow(self._notifyWindow,WM_GRPAPHNOTIFY)
		self._playBuilder.Run()

		if self.play_loop == 0 and duration == 0:
			self.playdone(0)

	# scheduler callback, at end of duration
	def _stopplay(self):
		self.__qid = None
		if self._playBuilder:
			self._playBuilder.Stop()
			self._playBuilder = None
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
		if self._playBuilder:
			duration=self._playBuilder.GetDuration()
			t_msec=self._playBuilder.GetPosition()
			if t_msec>=duration:self.OnMediaEnd()

	def OnMediaEnd(self):
		if debug: print 'SoundChannel: OnMediaEnd',`self`
		if not self._playBuilder:
			return		
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops
				self._playBuilder.SetPosition(0)
				self._playBuilder.Run()
				return
			# no more loops
			self._playBuilder.Stop()
			self._playBuilder=None
			# if event wait scheduler
			if self.__qid is not None:return
			# else end
			self.playdone(0)
			return
		# play_loop is 0 so play until duration if set
		self._playBuilder.SetPosition(0)
		self._playBuilder.Run()

	def islocal(self,url):
		utype, url = MMurl.splittype(url)
		host, url = MMurl.splithost(url)
		return not utype and not host

	def toabs(self,url):
		if not self.islocal(url):
			return url
		filename=MMurl.url2pathname(MMurl.splithost(url)[1])
		if os.path.isfile(filename):
			if not os.path.isabs(filename):
				filename=os.path.join(os.getcwd(),filename)
				filename=ntpath.normpath(filename)	
		return filename

