__version__ = "$Id$"

# Cache durations of movie files

import FileCache
import MMurl

def getduration(filename):
	filename = MMurl.urlretrieve(filename)[0]
	fp = open(filename, 'rb')
	import VFile
	import os
	VerrorList = VFile.Error, os.error, IOError, RuntimeError, EOFError
	try:
		vfile = VFile.RandomVinFile(fp)
		vfile.filename = filename
	except VerrorList, msg:
		raise IOError, (0, 'bad movie file: ' + str(msg))
	vfile.readcache()
	t, ds, cs = vfile.getrandomframeheader(len(vfile.index)-1)
	return t * 0.001

duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
