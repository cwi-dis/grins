__version__ = "$Id$"

# Get the duration of a node.
# This module knows which channel types need special treatment.

import MMAttrdefs

def get(node):
	# If node has "fduration" attribute, use that.  This attribute
	# is set in mkcmifcache and nowhere else, so is only available
	# in the player.
	if hasattr(node.attrdict, 'fduration'):
		return node.attrdict['fduration']
	channel = node.GetChannel()
	if channel is not None and channel.has_key('type'):
		context = node.GetContext()
		ctype = channel['type']
		filename = MMAttrdefs.getattr(node, 'file')
		filename = context.findurl(filename)
		if ctype == 'movie':
			import MovieDuration
			try:
				return MovieDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype == 'mpeg':
			import MpegDuration
			try:
				return MpegDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype == 'sound':
			import SoundDuration
			try:
				return SoundDuration.get(filename)
			except IOError, msg:
				print filename, msg
	return MMAttrdefs.getattr(node, 'duration')
