__version__ = "$Id$"

import Channel
import MMAttrdefs
from MMurl import urlretrieve

# for timer support
import windowinterface

import winmm

class SoundChannel(Channel.ChannelAsync):
	def __init__(self, name, attrdict, scheduler, ui):
		Channel.ChannelAsync.__init__(self, name, attrdict, scheduler, ui)
		self.__playing = None

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def do_play(self, node, curtime):
		Channel.ChannelAsync.do_play(self, node, curtime)

		if node.type != 'ext':
			self.errormsg(node, 'Node must be external.')
			return 1
		f = self.getfileurl(node)
		if not f:
			self.errormsg(node, 'No URL set on node.')
			return 1
		try:
			f = urlretrieve(f)[0]
		except IOError, arg:
			if type(arg) is type(self):
				arg = arg.strerror
			self.errormsg(node, 'Cannot open: %s\n\n%s.' % (f, arg))
			return 1
		try:
			winmm.SndPlaySound(f)
		except winmm.error, arg:
			print arg
			self.playdone(0, curtime)
			return
		else:
			self.__playing = node

	def setpaused(self, paused, timestamp):
		Channel.ChannelAsync.setpaused(self, paused, timestamp)
		if paused:
			winmm.SndStopSound()
		else:
			self.do_play(self.__playing, timestamp)

	def playstop(self, curtime):
		if self.__playing:
			winmm.SndStopSound()
			self.__playing = None
		Channel.ChannelAsync.playstop(self, curtime)

	def stopplay(self, node, curtime):
		if self.__playing:
			winmm.SndStopSound()
			self.__playing = None
		Channel.ChannelAsync.stopplay(self, node, curtime)
