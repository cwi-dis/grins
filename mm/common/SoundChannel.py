from Channel import *
from debug import debug
from urllib import urlretrieve


class SoundChannel(ChannelThread):
	def init(self, name, attrdict, scheduler, ui):
		return ChannelThread.init(self, name, attrdict, scheduler, ui)

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def threadstart(self):
		import soundchannel
		return soundchannel.init()

	def do_arm(self, node):
		filename = self.getfilename(node)
		filename = urlretrieve(filename)[0]
		import SoundDuration
		try:
			f, nchannels, nsampframes, sampwidth, samprate, format = \
				  SoundDuration.getinfo(filename)
		except IOError:
			return 1
		self.threads.arm(f, 0, 0, \
			  {'nchannels': int(nchannels), \
			   'nsampframes': int(nsampframes), \
			   'sampwidth': int(sampwidth), \
			   'samprate': int(samprate), \
			   'format': format, \
			   'offset': int(f.tell())}, \
			  None, self.syncarm)
		return self.syncarm
