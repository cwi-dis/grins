__version__ = "$Id$"

from stat import *
import os

class FileCache:

    def __init__(self, func, rm = None, check = None):
        self.func = func
        self.rm = rm
        self.check = check
        self.cache = {}

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
                if self.check is None or \
                          self.check(file, res):
                    return res
            if self.rm:
                self.rm(file, res)
            del self.cache[file]
        result = self.func(file)
        self.cache[file] = mtime, size, result
        return result
