__version__ = "$Id$"

#
# WIN32 Sound Channel
#

# the core
import Channel

# common component
import MediaChannel
import RealChannel

# node attributes
import MMAttrdefs

debug=0

class SoundChannel(Channel.ChannelAsync):
	node_attrs = Channel.ChannelAsync.node_attrs + [
		'duration', 'clipbegin', 'clipend',
		'project_audiotype', 'project_targets',
		'project_perfect', 'project_mobile']

	def __init__(self, name, attrdict, scheduler, ui):
		self.__mc = None
		self.__rc = None
		self.need_armdone = 0
		self.__playing = None
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def do_show(self, pchan):
		if not Channel.ChannelAsync.do_show(self, pchan):
			return 0
		return 1

	def do_hide(self):
		self.__playing = None
		if self.__mc:
			self.__mc.stopit()
			self.__mc.destroy()
			self.__mc = None
		if self.__rc:
			self.__rc.stopit()
			self.__rc.destroy()
			self.__rc = None
		Channel.ChannelAsync.do_hide(self)

	def do_arm(self, node, same=0):
		self.__ready = 0
		node.__type = ''
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		url = self.getfileurl(node)
		if not url:
			self.errormsg(node, 'No URL set on node')
			return 1
		import MMmimetypes, string
		mtype = MMmimetypes.guess_type(url)[0]
		if mtype and string.find(mtype, 'real') >= 0:
			node.__type = 'real'
			if self.__rc is None:
				try:
					self.__rc = RealChannel.RealChannel(self)
				except RealChannel.error, msg:
					# can't do RealAudio
##					self.__rc = 0 # don't try again
					self.errormsg(node, msg)
			if self.__rc:
				if self.__rc.prepare_player(node):
					self.__ready = 1
		else:
			if not self.__mc:
				self.__mc = MediaChannel.MediaChannel(self)
			try:
				self.__mc.prepare_player(node)
				self.__ready = 1
			except MediaChannel.error, msg:
				self.errormsg(node, msg)
		return 1

	def do_play(self, node):
		self.__playing = node
		self.__type = node.__type
		if not self.__ready:
			# arming failed, so don't even try playing
			self.playdone(0)
			return
		if node.__type == 'real':
			if not self.__rc:
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
			self.errormsg(node,'Can not play')
			self.playdone(0)

	def playstop(self):
		self.__stopplayer()
		self.playdone(1)		
				
	def __stopplayer(self):
		if self.__playing:
			if self.__type == 'real':
				if self.__rc:
					self.__rc.stopit()
			else:
				self.__mc.stopit()
		self.__playing = None

	def endoftime(self):
		self.__stopplayer()
		self.playdone(0)

	# toggles between pause and run
	def setpaused(self, paused):
		if self.__rc:
			self.__rc.pauseit(paused)
		if self.__mc is not None:
			self.__mc.pauseit(paused)
		Channel.ChannelAsync.setpaused(self, paused)


	def playdone(self, outside_induced):
		if self.need_armdone:
			self.need_armdone = 0
			self.armdone()
		Channel.ChannelAsync.playdone(self, outside_induced)
		if not outside_induced:
			self.__playing = None

	def stopplay(self, node, no_extend = 0):
		if self.__mc:
			self.__mc.stopit()
		if self.__rc:
			self.__rc.stopit()
		Channel.ChannelAsync.stopplay(self, node, no_extend)

	def updatesoundlevel(self, val):
		if self.__mc:
			self.__mc.setsoundlevel(val)
		if self.__rc:
			pass


		
