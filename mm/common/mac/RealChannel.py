__version__ = "$Id$"

import windowinterface
try:
	import rma
except ImportError:
	# no Real support available
	rma = None
import MMurl
import os
if os.name == 'mac':
	import Evt
	NEEDTICKER = 1
else:
	NEEDTICKER = 0

class RealEngine:
	# This class holds the RMA engine and a useage counter. This counter is
	# needed because on the mac (and maybe on unix) whenever any player is active
	# we should periodically pass events to the engine to keep it ticking.
	# XXXX Eventually we should probably also pass redraw events and such.
	def __init__(self):
		self.engine = rma.CreateEngine()
		self.usagecount = 0
		
	def __del__(self):
		if self.usagecount:
			windowinterface.cancelidleproc(self._tick)
		
	def CreatePlayer(self):
		return self.engine.CreatePlayer()
		
	def startusing(self):
		if NEEDTICKER and self.usagecount == 0:
			self._startticker()
		self.usagecount = self.usagecount + 1
		
	def stopusing(self):
		if self.usagecount <= 0:
			raise 'RealEngine usage count <= 0'
		self.usagecount = self.usagecount - 1
		if NEEDTICKER and self.usagecount == 0:
			self._stopticker()
			
	def _startticker(self):
		print 'DBG startticker'
		windowinterface.setidleproc(self._tick)
		
	def _stopticker(self):
		print 'DBG stopticker'
		windowinterface.cancelidleproc(self._tick)
		
	def _tick(self):
		# XXXX Mac-specific
		self.engine.EventOccurred((0, 0, Evt.TickCount(), (0, 0), 0))

class RealChannel:
	__engine = None
	__has_rma_support = rma is not None

	def __init__(self):
		self.__rmaplayer = None
		if self.__engine is None and self.__has_rma_support:
			try:
				RealChannel.__engine = RealEngine()
			except:
				self.errormsg(None, 'No playback support for RealMedia on this system')
				RealChannel.__has_rma_support = 0
		# release any resources on exit
		windowinterface.addclosecallback(self.release_player,())

	def release_player(self):
		self.__rmaplayer = None

	def prepare_player(self, node = None):
		if not self.__has_rma_support:
			return 0
		if not self.__rmaplayer:
			try:
				self.__rmaplayer = self.__engine.CreatePlayer()
			except:
				self.errormsg(node, 'No playback support for RealMedia on this system')
				return 0
		return 1

	def playit(self, node, window = None, winpossize=None):
		if not self.__rmaplayer:
			return 0
		self.__loop = self.getloop(node)
		url = MMurl.canonURL(self.getfileurl(node))
		self.__url = url
		self.__window = window
		self.__rmaplayer.SetStatusListener(self)
		if window is not None:
			self.__rmaplayer.SetOsWindow(window)
		if winpossize is not None:
			pos, size = winpossize
			self.__rmaplayer.SetPositionAndSize(pos, size)
		self.__rmaplayer.OpenURL(url)
		self.__rmaplayer.Begin()
		self.__engine.startusing()
		return 1

	def OnStop(self):
		if self.__loop:
			self.__loop = self.__loop - 1
			if self.__loop == 0:
				self.playdone(0)
				##self.__engine.stopusing()
				return
		print 'looping'
		windowinterface.settimer(0.1,(self.__rmaplayer.Begin,()))
#		self.__rmaplayer.Stop()
#		self.__rmaplayer.Begin()

	def pauseit(self, paused):
		if self.__rmaplayer:
			if paused:
				self.__rmaplayer.Pause()
			else:
				self.__rmaplayer.Begin()

	def stopit(self):
		if self.__rmaplayer:
			self.__rmaplayer.Stop()
			self.__engine.stopusing()
		self.__rmaplayer = None
