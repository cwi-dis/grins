__version__ = "$Id$"

# Cache info about sound files

# Used to get full info
def getfullinfo(url):
	from MMurl import urlretrieve
	try:
		filename = urlretrieve(url)[0]
	except (IOError), msg:
		print 'error in sound file', url, ':', msg
		return 0, 8000, []
	#return nframes, framerate, markers
	import windowinterface
	return windowinterface.GetMediaDuration(filename),1,[]

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
