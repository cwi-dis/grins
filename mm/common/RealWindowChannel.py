__version__ = "$Id$"

#
# WIN32 RealWindowChannel.
#

""" @win32doc|RealWindowChannel

"""
import Channel, RealChannel

class RealWindowChannel(Channel.ChannelWindowAsync):
	def __init__(self, name, attrdict, scheduler, ui):
		self.__rc = None
		self.__override_url = None
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def do_arm(self, node, same = 0):
		if self.__rc is None:
			self.errormsg(node, 'No playback support for Real Media in this version')
			return 1
		if not self.__rc.prepare_player(node):
			import MMAttrdefs
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			chtype = self.__class__.__name__[:-7] # minus "Channel"
			msg = 'Warning:\nNo playback support for %s on this system\n' \
			      'node %s on channel %s' % (chtype, name, self._name)
			parms = self.armed_display.fitfont('Times-Roman', msg)
			w, h = self.armed_display.strsize(msg)
			self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
			self.armed_display.fgcolor((255, 0, 0))		# red
			box = self.armed_display.writestr(msg)
		return 1
		
	def do_show(self, pchan):
		if not Channel.ChannelWindowAsync.do_show(self, pchan):
			return 0
		try:
			self.__rc = RealChannel.RealChannel(self)
		except 'xxx':
			self.__rc = None
		return 1
			
	def do_hide(self):
		if self.__rc is not None:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None
		Channel.ChannelWindowAsync.do_hide(self)
		
	def do_play(self, node):
		url = None
		if self.__override_url:
			url = self.__override_url
			self.__override_url = None
		if self.__rc is None or \
		   not self.__rc.playit(node, self._getoswindow(), self._getoswinpos() , url=url):
			self.playdone(0)

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelWindowAsync.setpaused(self, paused)
		if self.__rc is not None:
			self.__rc.pauseit(paused)

	def stopplay(self, node):
		if self.__rc is not None:
			self.__rc.stopit()
		Channel.ChannelWindowAsync.stopplay(self, node)

	def _getoswindow(self):
		if hasattr(self.window, "GetSafeHwnd"):
			# Windows
			return self.window.GetSafeHwnd()
		elif hasattr(self.window, "_wid"):
			# Macintosh
			return self.window._wid
		else:
			return None
			
	def _getoswinpos(self):
		if hasattr(self.window, "qdrect"):
			x0, y0, x1, y1 = self.window.qdrect()
			return ((x0, y0), (x1-x0, y1-y0))
		return None

	def parallel_arm(self, node, url=None):
		"""Used by RealPix channel to play RealText captions in parallel"""
		self.arm(node)
		
	def parallel_play(self, node, url=None):
		# XXXX Is this safe, i.e. can we call playdone?
		self.__override_url = url
		self.play(node)
			
	def parallel_stopplay(self, node):
		self.stopplay(node)

	def parallel_stoparm(self):
		self.stoparm()

