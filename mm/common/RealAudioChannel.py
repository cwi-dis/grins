__version__ = "$Id$"

from Channel import Channel

class RealAudioChannel(Channel):
	def do_play(self, node):
		import windowinterface, MMAttrdefs
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		windowinterface.showmessage('No playback support for RealAudio in this version\n'
					    'node %s on channel %s' % (name, self._name), mtype = 'warning')
