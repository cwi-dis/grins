__version__ = "$Id$"

# Cache info about sound files

import MMurl

__version__ = "$Id$"

# Cache info about sound files

# Used to get full info
def getfullinfo(url):
	u = MMurl.urlopen(url)
	if u.headers.subtype in ('mp3', 'mpeg', 'x-mp3'):
		u.close()
		return 80000, 8000, []
	u.close()

	import audio
	from MMurl import urlretrieve
	try:
		filename = urlretrieve(url)[0]
		a = audio.reader(filename)
		nframes = a.getnframes()
		framerate = a.getframerate()
		markers = a.getmarkers()
	except (audio.Error, IOError, EOFError), msg:
		print 'error in sound file', url, ':', msg
		return 0, 8000, []
	return nframes, framerate, markers

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

