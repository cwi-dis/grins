__version__ = "$Id$"

# Cache durations of video files

import FileCache
import urllib

def getduration(filename):
	import mv
	filename = urllib.urlretrieve(filename)[0]
	try:
		f = mv.OpenFile(filename, 0)
	except mv.error, msg:
		print 'error in video file', filename, ':', msg
		return 0
	duration = float(f.GetEstMovieDuration(1000)) / 1000
	f.Close()
	return duration

try:
	import mv
except ImportError:
	from MpegDuration import *
else:
	duration_cache = FileCache.FileCache(getduration)
	get = duration_cache.get
