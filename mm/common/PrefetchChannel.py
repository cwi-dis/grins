__version__ = "$Id$"

# the core
import Channel

# urlopen
import MMurl

# for timing support
import windowinterface
import time

debug = 1

USE_IDLE_PROC=hasattr(windowinterface, 'setidleproc')

class PrefetchChannel(Channel.ChannelAsync):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__duration = None
		self.__fetching = None

	def __repr__(self):
		return '<PrefetchChannel instance, name=' + `self._name` + '>'

	#
	# Channel overrides
	#

	def do_hide(self):
		Channel.ChannelAsync.do_hide(self)
	
	def do_play(self, node):
		Channel.ChannelAsync.do_play(self, node)

		self.__initEngine(node)

		if not self.__ready():
			self.playdone(0)
			return
		
		self.__fetching = node

		# get timing
		self.play_loop = self.getloop(node)
		self.__duration = node.GetAttrDef('duration', None)
		
		self.__startFetch()
		
	def setpaused(self, paused):
		Channel.ChannelAsync.setpaused(self, paused)
		self.__pauseFetch(paused)

	def stopplay(self, node):
		if self.__fetching:
			self.__stopFetch()
			self.__fetching = None
		Channel.ChannelAsync.stopplay(self, node)

	#
	# Fetch engine
	#

	def __initEngine(self, node):
		self.__fiber_id = 0
		self.__start = None
		self.__pausedt = 0
		self.__urlopener = None
		self.__playdone = 0

		url = self.getfileurl(node)
		if not url:
			print 'No URL set on node'
			return
		self.__url = url
		
		self.__urlopener = MMurl.geturlopener()
		try:
			filename, headers = self.__urlopener.begin_retrieve(url)
		except:
			print 'Warning: cannot open url %s' % url
			self.__urlopener = None
		else:
			print filename, headers
			
	def __ready(self):
		return self.__urlopener!=None
			
	def __startFetch(self, repeat=0):
		self.__start = time.time()
		if repeat:
			self.__urlopener.begin_retrieve(self.__url)
		self.__fetch()
		self.__register_for_timeslices()

	def __stopFetch(self):
		if self.__fetching:
			self.__unregister_for_timeslices()
			self.__urlopener=None

	def __pauseFetch(self, paused):
		if self.__fetching:
			if paused:
				self.__pausedt = time.time() - self.__start
				self.__unregister_for_timeslices()
			else:
				self.__start = time.time() - self.__pausedt
				self.__register_for_timeslices()

	def __fetch(self):
		dt = time.time() - self.__start
		if self.__urlopener and self._playstate == PLAYING:
			if not self.__urlopener.do_retrieve(self.__url, 1024):
				self.__urlopener.end_retrieve(url)
				self.playdone(0)

	def __onFetchDur(self):
		if not self.__fetching:
			return
		if self.play_loop:
			self.play_loop = self.play_loop - 1
			if self.play_loop: # more loops ?
				self.__startFetch(repeat=1)
				return
			self.playdone(0)
			return
		# self.play_loop is 0 so repeat
		self.__startFetch(repeat=1)

	def onIdle(self):
		if not USE_IDLE_PROC:
			self.__fiber_id = 0
		if self.__fetching:
			t_sec = time.time() - self.__start
			if t_sec>=self.__duration:
				self.__onFetchDur()
				self.__unregister_for_timeslices()
			else:
				self.__fetch()
				self.__register_for_timeslices()
			
	def __register_for_timeslices(self):
		if not self.__fiber_id:
			if USE_IDLE_PROC:
				windowinterface.setidleproc(self.onIdle)
				self.__fiber_id = 1
			else:
				self.__fiber_id = windowinterface.settimer(0.05, (self.onIdle,()))

	def __unregister_for_timeslices(self):
		if self.__fiber_id:
			if USE_IDLE_PROC:
				windowinterface.cancelidleproc(self.onIdle)
			else:
				windowinterface.canceltimer(self.__fiber_id)
			self.__fiber_id = 0
