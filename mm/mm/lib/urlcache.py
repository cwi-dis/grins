__version__ = "$Id$"

from UserDict import UserDict

import settings
import sys

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
		checkext = settings.get('checkext')
		mtype = None
		if checkext:
			import MMmimetypes
			mtype = MMmimetypes.guess_type(url)[0]
		if not mtype:
			try:
				u = MMurl.urlopen(url)
			except (IOError, OSError):
				pass
			else:
				# On the Mac urllib may guess the mimetype wrong. Correct.
				if u.headers.type == 'text/plain' and sys.platform == 'mac':
					import MMmimetypes
					u.headers.type = MMmimetypes.guess_type(url)[0]
				mtype = u.headers.type
		if not mtype and sys.platform == 'mac':
			# On the mac we do something extra: for local files we attempt to
			# get creator and type, and if they are us we assume we're looking
			# at a SMIL file.
			import urlparse
			utype, host, path, params, query, fragment = urlparse.urlparse(url)
			if (not utype or utype == 'file') and \
			   (not host or host == 'localhost'):
				# local file
				import MacOS
				fn = MMurl.url2pathname(path)
				try:
					ct, tp = MacOS.GetCreatorAndType(fn)
				except:
					pass
				else:
					if ct == 'GRIN' and tp == 'TEXT':
						mtype = 'application/x-grins-project'
		if not mtype and not checkext:
			# last resort, try extension if not done so already
			import MMmimetypes
			mtype = MMmimetypes.guess_type(url)[0]
		if not mtype:
			# failed, don't cache
			return None
		if mtype.count('/') != 1:
			# don't cache bad MIME type
			return None
		cache['mimetype'] = mtype
	return cache['mimetype']
