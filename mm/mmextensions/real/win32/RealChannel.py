__version__ = "$Id$"

import windowinterface
import rma
import MMurl

class RealChannel:
	__engine = None
	__has_rma_support = 1

	def __init__(self):
		self.__rmaplayer = None
		if self.__engine is None and self.__has_rma_support:
			try:
				RealChannel.__engine = rma.CreateEngine()
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

	def playit(self, node, window = None):
		if not self.__rmaplayer:
			return
		self.__loop = self.getloop(node)
		url = MMurl.canonURL(self.getfileurl(node))
		self.__url = url
		self.__window = window
		self.__rmaplayer.SetStatusListener(self)
		if window is not None:
			self.__rmaplayer.SetOsWindow(window)
		self.__rmaplayer.OpenURL(url)
		self.__rmaplayer.Begin()

	def OnStop(self):
		if self.__loop:
			self.__loop = self.__loop - 1
			if self.__loop == 0:
				self.playdone(0)
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
		self.__rmaplayer = None
