__version__ = "$Id$"

# Cache info about sound files

import MMurl
import urllib
import MMmimetypes

# Used to get full info
def getfullinfo(url):
	duration = 0
	mtype = MMmimetypes.guess_type(url)[0]
	if mtype and (mtype.find('x-aiff') >= 0 or mtype.find('quicktime')):
		import winqt
		if winqt.HasQtSupport():
			try:
				fn = MMurl.urlretrieve(url)[0]
			except IOError, arg:
				print arg
			else:
				player = winqt.QtPlayer()
				player.open(fn)
				duration = player.getDuration()
	if not duration:
		url = MMurl.canonURL(url)
		url = urllib.unquote(url)
		import win32dxm
		duration = win32dxm.GetMediaDuration(url)
	if duration < 0:
		duration = 0
	bandwidth = 1
	markers = []
	return duration, bandwidth, markers

def get(url):
	nframes, framerate, markers = getfullinfo(url)
	if nframes == 0: nframes = framerate
	duration = float(nframes) / framerate
	return duration

def getmarkers(url):
	nframes, framerate, markers = getfullinfo(url)
	if not markers:
		return []
	xmarkers = []
	invrate = 1.0 / framerate
	for id, pos, name in markers:
		xmarkers.append((id, pos*invrate, name))
	return xmarkers
