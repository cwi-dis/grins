# Cache durations of sound files

import FileCache

def getinfo(filename):
	f = open(filename, 'r')
	import aifc
	try:
		a = aifc.openfp(f, 'r')
	except EOFError:
		print 'EOF on sound file', filename
		return f, 1, 0, 1, 8000, 'eof'
	except aifc.Error, msg:
		print 'error in sound file', filename, ':', msg
		return f, 1, 0, 1, 8000, 'error'
	dummy = a.readframes(0)		# sets file pointer to start of data
	if a.getcomptype() != 'NONE':
		print 'cannot read compressed AIFF-C files for now', filename
		return f, 1, 0, 1, 8000, 'error'
	return a.getfp(), a.getnchannels(), a.getnframes(), \
	       a.getsampwidth(), a.getframerate(), 'AIFF'

def getduration(filename):
	f, nchannels, nsampframes, sampwidth, samprate, format = \
		  getinfo(filename)
	f.close()
	if format not in ('AIFF', 'AIFC'):
		raise IOError, (0, 'bad sound file')
	duration = float(nsampframes) / samprate
	return duration

duration_cache = FileCache.FileCache().init(getduration)

get = duration_cache.get
