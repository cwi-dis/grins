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

	def do_play(self, node):
		self.playit(node)

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelAsync.setpaused(self, paused)
		self.pauseit(paused)

	def stopplay(self, node):
		self.stopit()
		Channel.ChannelAsync.stopplay(self, node)
