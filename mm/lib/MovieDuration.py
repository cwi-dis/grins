__version__ = "$Id$"

# Cache durations of movie files

import FileCache
import MMurl

def getduration(filename):
	try:
		filename = MMurl.urlretrieve(filename)[0]
		fp = open(filename, 'rb')
	except IOError:
		return 1.0
	import VFile
	import os
	VerrorList = VFile.Error, os.error, IOError, RuntimeError, EOFError
	try:
		vfile = VFile.RandomVinFile(fp)
		vfile.filename = filename
	except VerrorList, msg:
		return 1.0
	vfile.readcache()
	t, ds, cs = vfile.getrandomframeheader(len(vfile.index)-1)
	if t == 0: t = 1000
	return t * 0.001

duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
