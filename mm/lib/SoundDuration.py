__version__ = "$Id$"

# Cache info about sound files

# Used to get full info
def getfullinfo(filename):
	import audio
	from urllib import urlretrieve
	filename = urlretrieve(filename)[0]
	try:
		a = audio.reader(filename)
	except (audio.Error, IOError), msg:
		print 'error in sound file', filename, ':', msg
		return 0, 8000, []
	return a.getnframes(), a.getframerate(), a.getmarkers()

import FileCache
allinfo_cache = FileCache.FileCache(getfullinfo)

def get(filename):
	nframes, framerate, markers = allinfo_cache.get(filename)
	duration = float(nframes) / framerate
	return duration

def getmarkers(filename):
	nframes, framerate, markers = allinfo_cache.get(filename)
	if not markers:
		return []
	xmarkers = []
	invrate = 1.0 / framerate
	for id, pos, name in markers:
		xmarkers.append((id, pos*invrate, name))
	return xmarkers
