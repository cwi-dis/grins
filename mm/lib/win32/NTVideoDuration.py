__version__ = "$Id$"

# Cache durations of video files

""" @win32doc|getduration
For win32 please call windowinterface.GetMediaDuration(filename)
when you want the duration of a media file (audio and video).
"""

import FileCache
import MMurl

def getduration(filename):
	import windowinterface
	try:
		filename = MMurl.urlretrieve(filename)[0]
	except(IOError):
		return 1.0
	return windowinterface.GetMediaDuration(filename)

duration_cache = FileCache.FileCache(getduration)
get = duration_cache.get
