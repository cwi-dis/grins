# Get the duration of a node.
# This module knows which channel types need special treatment.

import MMAttrdefs

def get(node):
	context = node.GetContext()
	cname = MMAttrdefs.getattr(node, 'channel')
	if cname in context.channelnames:
		cattrs = node.context.channeldict[cname]
		if cattrs.has_key('type'):
			ctype = cattrs['type']
			filename = MMAttrdefs.getattr(node, 'file')
			filename = context.findfile(filename)
			if ctype == 'movie':
				import MovieDuration
				try:
					return MovieDuration.get(filename)
				except IOError, msg:
					print filename, msg
			elif ctype == 'sound':
				import SoundDuration
				try:
					return SoundDuration.get(filename)
				except IOError, msg:
					print filename, msg
	return MMAttrdefs.getattr(node, 'duration')
