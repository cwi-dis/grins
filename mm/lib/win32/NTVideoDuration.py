__version__ = "$Id$"

# Cache durations of video files

""" @win32doc|getduration
For win32 please call windowinterface.GetMediaDuration(filename)
when you want the duration of a media file (audio and video).
"""

import MMurl
import urllib

def get(url):
	url = MMurl.canonURL(url)
	url = urllib.unquote(url)
	import win32dxm
	return win32dxm.GetMediaDuration(url)
