__version__ = "$Id$"

#
# WIN32 Sound Channel
#

# the core
import Channel

# common component
from MediaChannel import MediaChannel
from RealChannel import RealChannel

# node attributes
import MMAttrdefs

debug=0

class SoundChannel(Channel.ChannelAsync):
	node_attrs = Channel.ChannelAsync.node_attrs + ['duration',
						'clipbegin', 'clipend', 'project_audiotype', 'project_targets']

	def __init__(self, name, attrdict, scheduler, ui):
		self.__mc = None
		self.__rc = None
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelAsync.do_show(self, pchan):
			return 0
		self.__mc = MediaChannel(self)
		try:
			self.__rc = RealChannel(self)
		except:
			pass
		return 1

	def do_hide(self):
		self.__mc.unregister_for_timeslices()
		self.__mc.release_res()
		self.__mc = None
		if self.__rc is not None:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None
		Channel.ChannelAsync.do_hide(self)

	def do_arm(self, node, same=0):
		node.__type = ''
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		url = self.getfileurl(node)
		if not url:
			self.errormsg(node, 'No URL set on node')
			return 1
		import mimetypes, string
		mtype = mimetypes.guess_type(url)[0]
		if mtype and string.find(mtype, 'real') >= 0:
			node.__type = 'real'
			if self.__rc is None:
				self.errormsg(node, 'No playback support for RealAudio in this version')
			else:
				self.__rc.prepare_player(node)
		elif not self.__mc.prepare_player(node):
			self.showwarning(node,'System missing infrastructure to playback')
		return 1

	def do_play(self, node):
		self.__type = node.__type
		if node.__type == 'real':
			if self.__rc is None:
				self.playdone(0)
			elif not self.__rc.playit(node):
				import windowinterface, MMAttrdefs
				name = MMAttrdefs.getattr(node, 'name')
				if not name:
					name = '<unnamed node>'
				chtype = self.__class__.__name__[:-7] # minus "Channel"
				windowinterface.showmessage('No playback support for %s on this system\n'
							    'node %s on channel %s' % (chtype, name, self._name), mtype = 'warning')
				self.playdone(0)
		elif not self.__mc.playit(node):
			self.showwarning(node,'Can not play')
			self.playdone(0)

	# part of stop sequence
	def stopplay(self, node):
		if self.__type == 'real':
			if self.__rc is not None:
				self.__rc.stopit()
		else:
			self.__mc.stopit()
		Channel.ChannelAsync.stopplay(self, node)

	# toggles between pause and run
	def setpaused(self, paused):
		if self.__rc is not None:
			self.__rc.pauseit(paused)
		if self.__mc is not None:
			self.__mc.pauseit(paused)
		Channel.ChannelAsync.setpaused(self, paused)


############################ 
# showwarning if the infrastucture is missing.
# The user should install Windows Media Player
# since then this infrastructure is installed

	def showwarning(self,node,inmsg):
		name = MMAttrdefs.getattr(node, 'name')
		if not name:
			name = '<unnamed node>'
		chtype = self.__class__.__name__[:-7] # minus "Channel.ChannelAsync"
		import windowinterface
		windowinterface.showmessage('%s\n'
						    '%s node %s on Channel.ChannelAsync %s' % (inmsg, chtype, name, self._name), mtype = 'warning')

	def play(self, node):
		self.play_0(node)
		if not self._is_shown or not node.ShouldPlay() \
		   or self.syncplay:
			self.play_1()
			return
		if self._is_shown:
			self.do_play(node)
		if node.__type == 'real':
			self.need_armdone = 1
		else:
			self.armdone()

	def playdone(self, dummy):
		if self.need_armdone:
			self.armdone()
			self.need_armdone = 0
		Channel.ChannelAsync.playdone(self, dummy)
