__version__ = "$Id$"

from UserDict import UserDict

import settings

# specialized dictionary that creates entries as soon as they are referred to
class URLCache(UserDict):
	def __getitem__(self, url):
		if url[:5] == 'data:' or settings.get('no_image_cache'):
			# don't cache data URLs, and
			# don't cache if we're not allowed to cache
			return {}
		if not self.has_key(url):
			self[url] = {}
		return UserDict.__getitem__(self, url)
	def get(self, url, default = None):
		return self[url]

urlcache = URLCache()

import MMurl
def mimetype(url):
	cache = urlcache[url]
	if not cache.has_key('mimetype'):
		try:
			u = MMurl.urlopen(url)
		except IOError:
			# don't cache non-existing file
			return None
		mtype = u.headers.type
		if mtype.count('/') != 1:
			# don't cache bad MIME type
			return None
		cache['mimetype'] = mtype
	return cache['mimetype']
