__version__ = "$Id$"

from RealWindowChannel import RealWindowChannel

class RealPixChannel(RealWindowChannel):
	node_attrs = RealWindowChannel.node_attrs + \
		     ['size', 'aspect', 'bitrate', 'maxfps', 'preroll', 'href']

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
