from stat import *
import os

class FileCache:

	def init(self, func):
		self.cache = {}
		self.func = func
		return self

	def flushall(self):
		self.cache = {}

	def flush(self, file):
		if self.cache.has_key(file):
			del self.cache[file]

	def get(self, file):
		try:
			st = os.stat(file)
			mtime, size = st[ST_MTIME], st[ST_SIZE]
		except os.error:
			mtime, size = None, None
		if self.cache.has_key(file):
			entry = self.cache[file]
			mt, sz, res = entry
			if mt == mtime and sz == size:
				return res
			del self.cache[file]
		result = self.func(file)
		self.cache[file] = mtime, size, result
		return result
