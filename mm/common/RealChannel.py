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
elif os.name == 'posix':
	NEEDTICKER = 1
else:
	NEEDTICKER = 0

# check implicitly rma version
if rma and hasattr(rma,'CreateClientContext'):
	HAS_PRECONFIGURED_PLAYER = 0
else:
	HAS_PRECONFIGURED_PLAYER = 1
		
error = 'RealChannel.error'

realenginedebug=0

class RealEngine:
	# This class holds the RMA engine and a useage counter. This counter is
	# needed because on the mac (and maybe on unix) whenever any player is active
	# we should periodically pass events to the engine to keep it ticking.
	# XXXX Eventually we should probably also pass redraw events and such.
	def __init__(self):
		self.usagecount = 0
		self.engine = rma.CreateEngine()
		self.__tid = None
		windowinterface.addclosecallback(self.close, ())
		
	def close(self):
		self.engine = None
		if self.usagecount and NEEDTICKER:
			windowinterface.cancelidleproc(self._tick)
		
	def __del__(self):
		self.close()
		
	def CreatePlayer(self, window, winpossize):
		if HAS_PRECONFIGURED_PLAYER:
			return self.engine.CreatePlayer(window, winpossize)
		else:
			return RealPlayer(self.engine)

	def startusing(self):
		if NEEDTICKER and self.usagecount == 0:
			self._startticker()
		self.usagecount = self.usagecount + 1
		
	def stopusing(self):
		if self.usagecount <= 0:
			raise error, 'RealEngine usage count <= 0'
		self.usagecount = self.usagecount - 1
		if NEEDTICKER and self.usagecount == 0:
			self._stopticker()
			
	def _startticker(self):
		self.__tid = windowinterface.setidleproc(self._tick)
		
	def _stopticker(self):
		if self.__tid is None:
			windowinterface.cancelidleproc(self._tick)
		else:
			windowinterface.cancelidleproc(self.__tid)
		
	def _tick(self, *dummy):
		if os.name == 'mac':
			# XXXX Mac-specific
			self.engine.EventOccurred((0, 0, Evt.TickCount(), (0, 0), 0))
		elif os.name == 'posix':
			self.engine.EventOccurred((0, 0, 0, (0, 0), 0))
		else:
			raise error, 'Unknown environment (_tick)'

class RealPlayer:
	# This class is for use with the new rma pyd. 
	# The new rma pyd has not a preconfigured player. 
	# An object of this class exposes to clients
	# the same interface as the previous rma buildin player
	def __init__(self, rmengine):
		p=rmengine.CreatePlayer()
		self.__dict__['_obj_'] = p

		# create client context objects
		# player is an optional arg
		# passing a player as arg we implicitly request 
		# part of the config to happen automatically (see source)
		adviseSink = rma.CreateClientAdviseSink(p)
		errorSink = rma.CreateErrorSink(p)
		authManager = rma.CreateAuthenticationManager(p)
		siteSupplier = rma.CreateSiteSupplier(p)

		# create player's client context with what interfaces
		# we would like to support
		clientContext = rma.CreateClientContext()
		clientContext.AddInterface(adviseSink.QueryIUnknown())
		clientContext.AddInterface(errorSink.QueryIUnknown())
		clientContext.AddInterface(authManager.QueryIUnknown())
		clientContext.AddInterface(siteSupplier.QueryIUnknown())
	
		# and give it to player
		# the player will use this context to request
		# available client interfaces (through QueryInterface)
		p.SetClientContext(clientContext)
		del clientContext # now belongs to player

		# keep refs to our client context objects
		# so that we can configure them later
		self._adviseSink = adviseSink
		self._errorSink = errorSink
		self._authManager = authManager
		self._siteSupplier = siteSupplier

	def __del__(self):
		self._obj_.Stop()
		del self._obj_

	def __getattr__(self, attr):	
		try:	
			if attr != '__dict__':
				o = self.__dict__['_obj_']
				if o:
					return getattr(o, attr)
		except KeyError:
			pass
		raise AttributeError, attr
			
	def SetStatusListener(self, listener):
		self._adviseSink.SetPyListener(listener)
		self._errorSink.SetPyListener(listener)

	def SetPyAdviceSink(self, listener):
		self._adviseSink.SetPyListener(listener)

	def SetPyErrorSink(self, listener):
		self._errorSink.SetPyListener(listener)

	def SetOsWindow(self, window):
		self._siteSupplier.SetOsWindow(window)

	def SetPositionAndSize(self, pos, size):
		self._siteSupplier.SetPositionAndSize(pos, size)


class RealChannel:
	__engine = None
	__has_rma_support = rma is not None

	def __init__(self, channel):
		if not self.__has_rma_support:
			raise error, "No RealPlayer G2 playback support in this version"
		self.__channel = channel
		self.__rmaplayer = None
		self.__qid = None
		self.__using_engine = 0
		if self.__engine is None:
			try:
				RealChannel.__engine = RealEngine()
			except:
				RealChannel.__has_rma_support = 0
				raise error, "Cannot initialize RealPlayer G2 playback. G2 installation problem?"
##		# release any resources on exit
##		windowinterface.addclosecallback(self.release_player,())
		
	def destroy(self):
		del self.__channel

	def release_player(self):
		self.__rmaplayer = None

	def prepare_player(self, node = None):
		if not self.__has_rma_support:
			return 0
		return 1

	def playit(self, node, window = None, winpossize=None, url=None):
		if not self.__rmaplayer:
			try:
				self.__rmaplayer = self.__engine.CreatePlayer(window, winpossize)
			except:
				self.__channel.errormsg(node, 'Cannot initialize RealPlayer G2 playback.')
				return 0
		self.__loop = self.__channel.getloop(node)
		duration = self.__channel.getduration(node)
		if url is None:
			url = self.__channel.getfileurl(node)
		if not url:
			self.__channel.errormsg(node, 'No URL set on this node')
			return 0
		url = MMurl.canonURL(url)
##		try:
##			u = MMurl.urlopen(url)
##		except:
##			self.errormsg(node, 'Cannot open '+url)
##			return 0
##		else:
##			u.close()
##			del u
		self.__url = url
		self.__rmaplayer.SetStatusListener(self)
		if duration > 0:
			self.__qid = self.__channel._scheduler.enter(duration, 0,
							   self.__stop, ())
		self.__playdone_called = 0
		# WARNING: RealMedia player doesn't unquote, so we must do it
		url = MMurl.unquote(url)
		if realenginedebug:
			print 'RealChannel.playit', self, `url`
		self.__rmaplayer.OpenURL(url)
		self.__rmaplayer.Begin()
		self.__engine.startusing()
		self.__using_engine = 1
		self._playargs = (node, window, winpossize, url)
		return 1


	def replay(self):
		if not self._playargs:
			return
		node, window, winpossize, url = self._playargs
		temp = self.__rmaplayer
		self.__rmaplayer = None
		self.prepare_player(node)
		self.__rmaplayer.SetStatusListener(self)
		if window is not None:
			self.__rmaplayer.SetOsWindow(window)
		if winpossize is not None:
			pos, size = winpossize
			self.__rmaplayer.SetPositionAndSize(pos, size)
		self.__rmaplayer.OpenURL(url)
		self.__rmaplayer.Begin()


	def __stop(self):
		self.__qid = None
		if self.__rmaplayer:
			if realenginedebug:
				print 'RealChannel.__stop', self
			self.__loop = 1
			self.__rmaplayer.Stop()
			# This may cause OnStop to be called, and it may not....
			if not self.__playdone_called:
				self.__channel.playdone(0)
				self.__playdone_called = 1
		else:
			self.__channel.playdone(0)

	def OnStop(self):
		if self.__loop:
			self.__loop = self.__loop - 1
			if self.__loop == 0:
				if realenginedebug:
					print 'RealChannel.OnStop', self
				if self.__qid is None:
					if not self.__playdone_called:
						self.__channel.playdone(0)
						self.__playdone_called = 1
				return
##		print 'looping'
#		windowinterface.settimer(0.1,(self.__rmaplayer.Begin,()))
		windowinterface.settimer(0.1,(self.replay,()))
#		self.__rmaplayer.Stop()
#		self.__rmaplayer.Begin()

	def ErrorOccurred(self,str):
		if realenginedebug:
			print 'RealChannel.ErrorOccurred', self
		windowinterface.settimer(0.1,(self.__channel.errormsg,(None,str)))

	def pauseit(self, paused):
		if self.__rmaplayer:
			if realenginedebug:
				print 'RealChannel.pauseit', self, paused
			if paused:
				self.__rmaplayer.Pause()
			else:
				self.__rmaplayer.Begin()

	def stopit(self):
		if self.__rmaplayer:
			if realenginedebug:
				print 'RealChannel.stopit', self
			self.__rmaplayer.Stop()
			if self.__using_engine:
				self.__engine.stopusing()
			self.__using_engine = 0
			self.__rmaplayer = None
