# Cache info about sound files

import FileCache
from urllib import urlretrieve

# Used to get full info
def getfullinfo(filename):
	filename = urlretrieve(filename)[0]
	f = open(filename, 'r')
	import aifc
	try:
		a = aifc.openfp(f, 'r')
	except EOFError:
		print 'EOF on sound file', filename
		return f, 1, 0, 1, 8000, 'eof', []
	except aifc.Error, msg:
		print 'error in sound file', filename, ':', msg
		return f, 1, 0, 1, 8000, 'error', []
	dummy = a.readframes(0)		# sets file pointer to start of data
	if a.getcomptype() != 'NONE':
		print 'cannot read compressed AIFF-C files for now', filename
		return f, 1, 0, 1, 8000, 'error', []
	return a.getfp(), a.getnchannels(), a.getnframes(), \
	       a.getsampwidth(), a.getframerate(), 'AIFF', \
	       a.getmarkers()

# Used for compatibility (can't use cache, must open the file)
def getinfo(filename):
	return getfullinfo(filename)[:6]

# Used to get all info except open file
def getallinfo(filename):
	f, nchannels, nsampframes, sampwidth, samprate, format, markers = \
		  getfullinfo(filename)
	f.close()
	if format not in ('AIFF', 'AIFC'):
		raise IOError, (0, 'bad sound file')
	return nchannels, nsampframes, sampwidth, samprate, format, markers

allinfo_cache = FileCache.FileCache().init(getallinfo)

def get(filename):
	nchannels, nsampframes, sampwidth, samprate, format, markers = \
		  allinfo_cache.get(filename)
	duration = float(nsampframes) / samprate
	return duration

def getmarkers(filename):
	nchannels, nsampframes, sampwidth, samprate, format, markers = \
		  allinfo_cache.get(filename)
	if not markers:
		return []
	xmarkers = []
	invrate = 1.0 / samprate
	for id, pos, name in markers:
		xmarkers.append((id, pos*invrate, name))
	return xmarkers
