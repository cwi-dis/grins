from UserDict import UserDict

# specialized dictionary that creates entries as soon as they are referred to
class URLCache(UserDict):
	def __getitem__(self, url):
		if url[:5] == 'data:':
			# don't cache data URLs
			return {}
		if not self.has_key(url):
			self[url] = {}
		return UserDict.__getitem__(self, url)
	def get(self, url, default = None):
		return self[url]

urlcache = URLCache()
