from Channel import *
import urllib


class SoundChannel(ChannelThread):
	chan_attrs = ChannelThread.chan_attrs + ['queuesize']

	def __repr__(self):
		return '<SoundChannel instance, name=' + `self._name` + '>'

	def threadstart(self):
		import soundchannel
		return soundchannel.init()

	def do_arm(self, node, same=0):
		if node.type != 'ext':
			self.errormsg(node, 'Node must be external')
			return 1
		filename = self.getfileurl(node)
		try:
			filename = urllib.urlretrieve(filename)[0]
		except IOError:
			self.errormsg(node, 'Cannot open ' + filename)
			return 1
		import SoundDuration
		try:
			f, nchannels, nsampframes, sampwidth, samprate, format = \
				  SoundDuration.getinfo(filename)
		except IOError:
			self.errormsg(node, 'Error reading ' + filename)
			return 1
		if format in ('eof', 'error'):
			self.errormsg(node, 'Format error in ' + filename)
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
