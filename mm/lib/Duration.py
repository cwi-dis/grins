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
	duration = MMAttrdefs.getattr(node, 'duration')
	channel = node.GetChannel()
	if duration == 0 and channel is not None and channel.has_key('type'):
		context = node.GetContext()
		ctype = channel['type']
		filename = MMAttrdefs.getattr(node, 'file')
		filename = context.findurl(filename)
		loop = MMAttrdefs.getattr(node, 'loop')
		if loop == 0:
			# indefinite duration
			return -1
		if ctype == 'video':
			import VideoDuration
			try:
				return loop * VideoDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype == 'movie':
			import MovieDuration
			try:
				return loop * MovieDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype == 'mpeg':
			import VideoDuration
			try:
				return loop * VideoDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype == 'sound':
			import SoundDuration
			try:
				return loop * SoundDuration.get(filename)
			except IOError, msg:
				print filename, msg
	return duration
