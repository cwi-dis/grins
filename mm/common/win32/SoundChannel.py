__version__ = "$Id$"

#
# WIN32 Sound Channel
#

# the core
import Channel

# common component
import MediaChannel

# node attributes
import MMAttrdefs

debug=0

class SoundChannel(Channel.ChannelAsync,MediaChannel.MediaChannel):
	node_attrs = Channel.ChannelAsync.node_attrs + ['duration',
						'clipbegin', 'clipend']
	def __init__(self, name, attrdict, scheduler, ui):
		MediaChannel.MediaChannel.__init__(self)
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def do_hide(self):
		self.release_player()
		Channel.ChannelAsync.do_hide(self)

	def destroy(self):
		self.release_player()
		self.unregister_for_timeslices()
		Channel.ChannelAsync.destroy(self)


	def do_arm(self, node, same=0):
		if debug:print 'SoundChannel.do_arm('+`self`+','+`node`+'same'+')'
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		if not self.prepare_player(node):
			self.showwarning(node,'System missing infrastructure to playback')
		return 1


	def do_play(self, node):
		if debug: print 'SoundChannel.do_play('+`self`+','+`node`+')'
		self.playit(node)

	# part of stop sequence
	def stopplay(self, node):
		self.stopit()
		Channel.ChannelAsync.stopplay(self, node)

	# toggles between pause and run
	def setpaused(self, paused):
		self.pauseit(paused)


############################ 
# showwarning if the infrastucture is missing.
# The user should install Windows Media Player
# since then this infrastructure is installed

	def showwarning(self,node,inmsg):
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		chtype = self.__class__.__name__[:-7] # minus "Channel.ChannelAsync"
		windowinterface.showmessage('%s\n'
						    '%s node %s on Channel.ChannelAsync %s' % (inmsg, chtype, name, self._name), mtype = 'warning')

