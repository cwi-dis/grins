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
