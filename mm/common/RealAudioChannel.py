__version__ = "$Id$"

#
# WIN32 RealAudioChannel.
#

""" @win32doc|RealAudioChannel

"""
import Channel, RealChannel

class RealAudioChannel(Channel.ChannelAsync):
	node_attrs = Channel.ChannelAsync.node_attrs + ['duration']

	def __init__(self, name, attrdict, scheduler, ui):
		self.__rc = RealChannel.RealChannel(self)
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)

	def do_hide(self):
		self.__rc.stopit()
		Channel.ChannelAsync.do_hide(self)
		self.__rc.destroy()
		del self.__rc
		
	def do_arm(self, node, same = 0):
		self.__rc.prepare_player(node)
		return 1

	def do_play(self, node, curtime):
		if not self.__rc.playit(node):
			import windowinterface, MMAttrdefs
			name = MMAttrdefs.getattr(node, 'name')
			if not name:
				name = '<unnamed node>'
			chtype = self.__class__.__name__[:-7] # minus "Channel"
			windowinterface.showmessage('No playback support for %s on this system\n'
						    'node %s on channel %s' % (chtype, name, self._name), mtype = 'warning')
			self.playdone(0, curtime)

	# toggles between pause and run
	def setpaused(self, paused):
		Channel.ChannelAsync.setpaused(self, paused)
		self.__rc.pauseit(paused)

	def stopplay(self, node, curtime):
		if node.GetType() == 'anchor':
			self.stop_anchor(node, curtime)
			return
		if node and self._played_node is not node:
##			print 'node was not the playing node '+`self,node,self._played_node`
			return
		self.__rc.stopit()
		Channel.ChannelAsync.stopplay(self, node, curtime)
