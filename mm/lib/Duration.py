__version__ = "$Id$"

# Get the duration of a node.
# This module knows which channel types need special treatment.

import MMAttrdefs
import ChannelMap
from sys import platform
import urlcache
import string

def get(node, ignoreloop=0, wanterror=0, ignoredur=0):
	if ignoredur:
		duration = 0
	else:
		duration = MMAttrdefs.getattr(node, 'duration')
	if hasattr(node, 'slideshow') and \
	   node.slideshow.rp.duration == duration:
		duration = 0
	if duration == 0:
		if ignoreloop:
			loop = 1
		else:
			loop = MMAttrdefs.getattr(node, 'loop')
			if loop == 0:
				return 0
		context = node.GetContext()
		url = MMAttrdefs.getattr(node, 'file')
		if node.GetChannelType() == 'RealPix' and hasattr(node, 'slideshow'):
			import base64, realnode
			node.SetAttr('file', 'dummy.rp')
			data = realnode.writenode(node, tostring = 1, silent = 1)
			node.DelAttr('file')
			if url:
				node.SetAttr('file', url)
			url = 'data:image/vnd.rn-realpix;base64,' + \
			       string.join(string.split(base64.encodestring(data), '\n'), '')
		url = context.findurl(url)
		cache = urlcache.urlcache[url]
		dur = cache.get('duration')
		if ignoredur and dur is not None:
			return loop * dur
		if cache.has_key('mimetype'):
			maintype, subtype = cache['mimetype']
		else:
			import MMurl
			try:
				u = MMurl.urlopen(url)
			except IOError, arg:
				# don't cache non-existing file
				if wanterror:
					raise IOError, arg
				return 0
			maintype = u.headers.getmaintype()
			subtype = u.headers.getsubtype()
			cache['mimetype'] = maintype, subtype
			u.close()
			del u
		if string.find(subtype, 'real') >= 0:
			import realsupport
			info = realsupport.getinfo(url)
			dur = info.get('duration', 0)
		elif maintype == 'video':
			import VideoDuration
			try:
				dur = VideoDuration.get(url)
			except IOError, msg:
				if wanterror:
					raise IOError, msg
				print url, msg
		elif maintype == 'audio':
			import SoundDuration
			try:
				dur = SoundDuration.get(url)
			except IOError, msg:
				if wanterror:
					raise IOError, msg
				print url, msg
		elif maintype in ('image', 'text'):
			# static media doesn't have a duration
			return 0
		if ignoredur and dur is not None:
			cache['duration'] = dur
		try:
			clipbegin = node.GetClip('clipbegin', 'sec')
		except ValueError:
			clipbegin = 0
		try:
			clipend = node.GetClip('clipend', 'sec')
		except ValueError:
			clipend = 0
		if clipend:
			if dur is None:
				dur = clipend
			else:
				dur = min(dur, clipend)
		if dur is None:
			dur = 100	# XXX we have no clue, but we don't want to crash
		dur = max(dur - clipbegin, 0)
		return loop * dur
	return duration
