__version__ = "$Id$"

# Cache durations of video files

""" @win32doc|getduration
For win32 please call windowinterface.GetMediaDuration(filename)
when you want the duration of a media file (audio and video).
"""

import MMurl
import MMmimetypes
import urllib

import win32dxm

def get(url):
	mtype = MMmimetypes.guess_type(url)[0]
	if mtype and mtype.find('quicktime') >= 0:
		import winqt
		if winqt.HasQtSupport():
			try:
				fn = MMurl.urlretrieve(url)[0]
			except IOError, arg:
				print arg
				return 0
			player = winqt.QtPlayer()
			player.open(fn)
			return player.getDuration()
	url = MMurl.canonURL(url)
	url = urllib.unquote(url)
	return win32dxm.GetMediaDuration(url)

