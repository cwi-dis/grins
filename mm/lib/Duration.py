__version__ = "$Id$"

# Get the duration of a node.
# This module knows which channel types need special treatment.

import MMAttrdefs
import ChannelMap
from sys import platform

def get(node, ignoreloop=0):
	# If node has "fduration" attribute, use that.  This attribute
	# is set in mkcmifcache and nowhere else, so is only available
	# in the player.
	if hasattr(node.attrdict, 'fduration'):
		return node.attrdict['fduration']
	duration = MMAttrdefs.getattr(node, 'duration')
	channel = node.GetChannel()
	if duration == 0 and channel is not None and channel.has_key('type'):
		if ignoreloop:
			loop = 1
		else:
			loop = MMAttrdefs.getattr(node, 'loop')
			if loop == 0:
				return 0
		context = node.GetContext()
		ctype = channel['type']
		filename = MMAttrdefs.getattr(node, 'file')
		filename = context.findurl(filename)
		if ctype in ('video', 'mpeg') or (platform == 'mac' and ctype == 'movie'):
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
		elif ctype == 'sound':
			import SoundDuration
			try:
				return loop * SoundDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype not in ChannelMap.channelhierarchy['text'] and \
		     ctype not in ChannelMap.channelhierarchy['image']:
			# give them a duration
			return 5
	return duration
