__version__ = "$Id$"

from RealWindowChannel import RealWindowChannel
import tempfile
import os
import MMurl

class RealPixChannel(RealWindowChannel):
	node_attrs = RealWindowChannel.node_attrs + \
		     ['size', 'aspect', 'bitrate', 'maxfps', 'preroll', 'href', 'captionchannel']

	def getfileurl(self, node):
		if hasattr(node, 'tmpfile'):
			import MMurl, realsupport
			realsupport.writeRP(node.tmpfile, node.slideshow.rp, node)
			return MMurl.pathname2url(node.tmpfile)
		return RealWindowChannel.getfileurl(self, node)

	def getduration(self, node):
		# use duration attribute if different from what's in the file
		duration = RealWindowChannel.getduration(self, node)
		if hasattr(node, 'slideshow') and \
		   node.slideshow.rp.duration == duration:
			return 0
		return duration

	# overrides for parallel play
	def arm(self, node):
		self.optional_parallel_arm(node)
		RealWindowChannel.arm(self, node)
		
	def play(self, node):
		self.optional_parallel_play(node)
		RealWindowChannel.play(self, node)
		
	def stopplay(self, node):
		self.optional_parallel_stopplay(node)
		RealWindowChannel.stopplay(self, node)
		
	def stoparm(self):
		self.optional_parallel_stoparm()
		RealWindowChannel.stoparm(self)
		
	def optional_parallel_arm(self, node):
		return
		self.__parallel_channel = None
		self.__parallel_url = None
		captionchannel = node.GetAttrDef('captionchannel', None)
		if not captionchannel or captionchannel == 'undefined':
			return
		ch = self._player.channels.get(captionchannel, None)
		if not ch:
			self.errormsg(node, 'Caption channel "%s" does not exist'%captionchannel)
			return
		self.__parallel_channel = ch
		rtfilename = tempfile.mktemp()
		import realsupport
		realsupport.writeRT(rtfilename, node.slideshow.rp, node)
		self.__parallel_url = MMurl.pathname2url(rtfilename)
		self.__parallel_channel.parallel_arm(node, self.__parallel_url)
		
	def optional_parallel_play(self, node):
		return
		if not self.__parallel_channel:
			return
		print 'parallel play', node
		self.__parallel_channel.parallel_play(node, self.__parallel_url)

	def optional_parallel_stopplay(self, node):
		return
		if not self.__parallel_channel:
			return
		print 'parallel stopplay', node
		self.__parallel_channel.parallel_stopplay(node)
		self.__parallel_channel = None
		if self.__parallel_url:
			try:
				os.remove(MMurl.url2pathname(self.__parallel_url))
			except:
				pass
			self.__parallel_url = None
		
	def optional_parallel_stoparm(self):
		return
		if not self.__parallel_channel:
			return
		print 'parallel stoparm'
		self.__parallel_channel.parallel_stoparm()
		self.__parallel_channel = None
		if self.__parallel_url:
			try:
				os.remove(MMurl.url2pathname(self.__parallel_url))
			except:
				pass
			self.__parallel_url = None
