__version__ = "$Id$"

#
# WIN32 RealWindowChannel.
#

""" @win32doc|RealWindowChannel

"""
import Channel, RealChannel

class RealWindowChannel(Channel.ChannelWindowAsync, RealChannel.RealChannel):
	def __init__(self, name, attrdict, scheduler, ui):
		RealChannel.RealChannel.__init__(self)
		Channel.ChannelWindowAsync.__init__(self, name, attrdict, scheduler, ui)

	def do_arm(self, node, same = 0):
		if not self.prepare_player(node):
			import MMAttrdefs
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			chtype = self.__class__.__name__[:-7] # minus "Channel"
			msg = 'Warning:\nNo playback support for %s in this version\n' \
			      'node %s on channel %s' % (chtype, name, self._name)
			parms = self.armed_display.fitfont('Times-Roman', msg)
			w, h = self.armed_display.strsize(msg)
			self.armed_display.setpos((1.0 - w) / 2, (1.0 - h) / 2)
			self.armed_display.fgcolor((255, 0, 0))		# red
			box = self.armed_display.writestr(msg)
		return 1

	def do_play(self, node):
		if not self.playit(node, self._getoswindow()):
			self.playdone(0)

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelWindowAsync.setpaused(self, paused)
		self.pauseit(paused)

	def stopplay(self, node):
		self.stopit()
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
