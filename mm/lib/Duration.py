__version__ = "$Id$"

# Get the duration of a node.
# This module knows which channel types need special treatment.

import MMAttrdefs
import ChannelMap
from sys import platform
import urlcache

def get(node, ignoreloop=0):
	duration = MMAttrdefs.getattr(node, 'duration')
	if hasattr(node, 'slideshow') and \
	   node.slideshow.rp.duration == duration:
		duration = 0
	ctype = node.GetChannelType()
	if duration == 0 and ctype:
		if ignoreloop:
			loop = 1
		else:
			loop = MMAttrdefs.getattr(node, 'loop')
			if loop == 0:
				return 0
		context = node.GetContext()
		filename = MMAttrdefs.getattr(node, 'file')
		filename = context.findurl(filename)
		dur = urlcache.urlcache[filename].get('duration')
		if dur is not None:
			return loop * dur
		if ctype in ('video', 'mpeg') or (platform == 'mac' and ctype == 'movie'):
			import VideoDuration
			try:
				dur = VideoDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype == 'movie':
			import MovieDuration
			try:
				dur = MovieDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype == 'sound':
			import SoundDuration
			try:
				dur = SoundDuration.get(filename)
			except IOError, msg:
				print filename, msg
		elif ctype[:4] == 'Real':
			import realsupport
			info = realsupport.getinfo(filename)
			dur = info.get('duration', 0)
		elif ctype not in ChannelMap.channelhierarchy['text'] and \
		     ctype not in ChannelMap.channelhierarchy['image']:
			# give them a duration
			return 5
		if dur is not None:
			urlcache.urlcache[filename]['duration'] = dur
			return loop * dur
	return duration
