__version__ = "$Id$"

import MMurl
import winmm

def get(url):
	import urlcache
	cache = urlcache.urlcache[url]
	dur = cache.get('duration')
	if dur is None:
		mtype = urlcache.mimetype(url)
		if mtype and mtype.find('mpeg') >= 0:
			try:
				fn = MMurl.urlretrieve(url)[0]
			except IOError, arg:
				print arg
				dur = 10
			else:	
				try:
					dur = winmm.GetVideoDuration(fn)
				except winmm.error, msg:
					print msg
					dur = 10
		if dur is None:
			dur = 10
	cache['duration'] = dur
	return dur
