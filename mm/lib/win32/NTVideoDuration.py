__version__ = "$Id$"

# Cache durations of video files

""" @win32doc|getduration
For win32 please call windowinterface.GetMediaDuration(filename)
when you want the duration of a media file (audio and video).
"""

import FileCache
import MMurl
import urllib

def getduration(url):
	url = MMurl.canonURL(url)
	url = urllib.unquote(url)
	import windowinterface
	return windowinterface.GetMediaDuration(url)

duration_cache = FileCache.FileCache(getduration)
get = duration_cache.get
