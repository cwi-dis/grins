__version__ = "$Id$"

# Cache durations of mpeg files

import FileCache
import MMurl
import string

VidRateNum = [30., 24., 24., 25., 30., 30., 50., 60.,
	      60., 15., 30., 30., 30., 30., 30., 30.]

def getduration(filename, bufsiz = 10240):
	# sanity check
	if bufsiz < 1024:
		bufsiz = 1024

	filename = MMurl.urlretrieve(filename)[0]
	fp = open(filename, 'rb')
	nframes = 0
        rate = 0

	# for efficiency, cache attribute lookups
	find = string.find
	read = fp.read

	data = read(bufsiz)
	i = find(data, '\000\000\001')
	while i >= 0:
		i = i + 3
		try:
			w = data[i]
		except IndexError:
			data = read(bufsiz)
			i = 0
			w = data[0]
		if w == '\000':
			# PICTURE_START_CODE
			nframes = nframes + 1
		elif w == '\263':
			# SEQ_START_CODE
			try:
				rate = ord(data[i+2]) & 0x0F
			except IndexError:
				data = data[i:] + read(bufsiz)
				i = 0
				rate = ord(data[i+2]) & 0x0F
		elif w == '\267':
			# SEQ_END_CODE
			break
		i = find(data, '\000\000\001', i+1)
		while i < 0:
			data = data[-2:] + read(bufsiz)
			if len(data) <= 2:
				break
			i = find(data, '\000\000\001')
	try:
		rate = VidRateNum[rate]
	except IndexError:
		# unknown frame rate, assume 30
		rate = 30.0
	if nframes == 0: nframes = rate
	return nframes / rate
	
duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
