__version__ = "$Id$"

# Cache info about sound files

import MMurl

# Used to get full info
def getfullinfo(url):
	url = MMurl.canonURL(url)
	import windowinterface
	#return nframes, framerate, markers
	duration = windowinterface.GetMediaDuration(url)
##	print 'SOUNDDURATION', url, duration
	if duration < 0:
		duration = 0
	bandwidth = 1
	markers = []
	return duration, bandwidth, markers

import FileCache
allinfo_cache = FileCache.FileCache(getfullinfo)

def get(url):
	nframes, framerate, markers = allinfo_cache.get(url)
	if nframes == 0: nframes = framerate
	duration = float(nframes) / framerate
	return duration

def getmarkers(url):
	nframes, framerate, markers = allinfo_cache.get(url)
	if not markers:
		return []
	xmarkers = []
	invrate = 1.0 / framerate
	for id, pos, name in markers:
		xmarkers.append((id, pos*invrate, name))
	return xmarkers
