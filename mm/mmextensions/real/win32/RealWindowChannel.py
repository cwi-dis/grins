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
		self.prepare_player(node)
		return 1

	def do_play(self, node):
		self.playit(node, self.window.GetSafeHwnd())

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelWindowAsync.setpaused(self, paused)
		self.pauseit(paused)

	def stopplay(self, node):
		self.stopit()
		Channel.ChannelAsync.stopplay(self, node)
