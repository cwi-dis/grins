__version__ = "$Id$"

# Cache info about sound files

# Used to get full info
def getfullinfo(url):
	import audio
	from MMurl import urlretrieve
	try:
		filename = urlretrieve(url)[0]
		a = audio.reader(filename)
	except (audio.Error, IOError), msg:
		print 'error in sound file', url, ':', msg
		return 0, 8000, []
	return a.getnframes(), a.getframerate(), a.getmarkers()

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
