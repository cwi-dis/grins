__version__ = "$Id$"

# Cache durations of video files

import FileCache
import MMurl

def getduration(filename):
	import mv
	try:
		filename = MMurl.urlretrieve(filename)[0]
		f = mv.OpenFile(filename, mv.MV_MPEG1_PRESCAN_OFF)
	except (mv.error, IOError), msg:
		print 'error in video file', filename, ':', msg
		return 1.0
	if hasattr(f, 'GetEstMovieDuration'):
		# faster but not omnipresent
		duration = float(f.GetEstMovieDuration(1000)) / 1000
	else:
		# slower (and more accurate)
		duration = float(f.GetMovieDuration(1000)) / 1000
	f.Close()
	if duration == 0: duration = 1.0
	return duration

try:
	import mv
except ImportError:
	from MPEGVideoDuration import *
else:
	duration_cache = FileCache.FileCache(getduration)
	get = duration_cache.get
