# Cache durations of mpeg files

import FileCache
import urllib
import string

VidRateNum = [30., 24., 24., 25., 30., 30., 50., 60.,
	      60., 15., 30., 30., 30., 30., 30., 30.]

def getduration(filename):
	filename = urllib.url2pathname(filename)
	fp = open(filename, 'rb')
	nframes = 0
        rate = 0
	for s in string.splitfields(fp.read(), '\000\000\001'):
		if not s: continue
		w = s[0]
		if w == '\000':
			# PICTURE_START_CODE
			nframes = nframes + 1
			continue
		if w == '\263':
			# SEQ_START_CODE
			rate = ord(s[2]) & 0x0F
			continue
		if w == '\267':
			# SEQ_END_CODE
			break
	try:
		return nframes / VidRateNum[rate]
	except IndexError:
		return nframes / 30.0
	
duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
