from stat import *
import os

class FileCache:

	def init(self, *funcs):
		if len(funcs) == 1:
			self.func = funcs[0]
			self.rm = self.check = None
		elif len(funcs) == 2:
			self.func, self.rm = funcs
			self.check = None
		elif len(funcs) == 3:
			self.func, self.rm, self.check = funcs
		else:
			raise TypeError, 'FileCache().init() w. wrong #args'
		self.cache = {}
		return self

	def __repr__(self):
		return '<FileCache instance, func=' + self.func + '>'

	def flushall(self):
		if self.rm:
			for file in self.cache.keys():
				self.rm(file, self.cache[file][2])
		self.cache = {}

	def flush(self, file):
		if self.cache.has_key(file):
			if self.rm:
				self.rm(file, self.cache[file][2])
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
				if self.check == None or \
					  self.check(file, res):
					return res
			if self.rm:
				self.rm(file, res)
			del self.cache[file]
		result = self.func(file)
		self.cache[file] = mtime, size, result
		return result
