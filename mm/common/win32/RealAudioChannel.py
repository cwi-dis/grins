__version__ = "$Id$"

#
# WIN32 RealAudioChannel.
#

""" @win32doc|RealAudioChannel

"""
import Channel, RealChannel

class RealAudioChannel(Channel.ChannelAsync, RealChannel.RealChannel):
	def __init__(self, name, attrdict, scheduler, ui):
		RealChannel.RealChannel.__init__(self)
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)

	def do_arm(self, node, same = 0):
		self.prepare_player(node)
		return 1

	def do_play(self, node):
		if not self.playit(node):
			import windowinterface, MMAttrdefs
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			chtype = self.__class__.__name__[:-7] # minus "Channel"
			windowinterface.showmessage('No playback support for %s in this version\n'
						    'node %s on channel %s' % (chtype, name, self._name), mtype = 'warning')
			self.playdone(0)

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelAsync.setpaused(self, paused)
		self.pauseit(paused)

	def stopplay(self, node):
		self.stopit()
		Channel.ChannelAsync.stopplay(self, node)
