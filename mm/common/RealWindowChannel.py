__version__ = "$Id$"

#
# WIN32 RealWindowChannel.
#

""" @win32doc|RealWindowChannel

"""
import Channel, RealChannel

class RealWindowChannel(Channel.ChannelWindowAsync):
	def __init__(self, name, attrdict, scheduler, ui):
		self.need_armdone = 0
		self.__rc = None
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def do_arm(self, node, same = 0):
		if self.__rc is None or not self.__rc.prepare_player(node):
			import MMAttrdefs
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			chtype = self.__class__.__name__[:-7] # minus "Channel"
			msg = 'Warning:\nNo playback support for %s\n' \
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
		except:
			self.__rc = None
		return 1
			
	def do_hide(self):
		if self.__rc is not None:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None
		Channel.ChannelWindowAsync.do_hide(self)
		
	def do_play(self, node):
		if self.__rc is None or \
		   not self.__rc.playit(node, self._getoswindow(), self._getoswinpos()):
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

	def play(self, node):
		self.need_armdone = 0
		self.play_0(node)
		if self._is_shown and node.ShouldPlay() \
		   and self.window and not self.syncplay:
			self.check_popup()
			if self.armed_display.is_closed():
				# assume that we are going to get a
				# resize event
				pass
			else:
				self.armed_display.render()
			if self.played_display:
				self.played_display.close()
			self.played_display = self.armed_display
			self.armed_display = None
			self.do_play(node)
			self.need_armdone = 1
		else:
			self.play_1()

	def playdone(self, dummy):
		if self.need_armdone:
			self.need_armdone = 0
			self.armdone()
		Channel.ChannelWindowAsync.playdone(self, dummy)
