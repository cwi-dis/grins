__version__ = "$Id$"

# Cache durations of mpeg files

import MMurl

def getsize(url, bufsiz = 10240):
	# sanity check
	if bufsiz < 1024:
		bufsiz = 1024

	filename = MMurl.urlretrieve(url)[0]
	fp = open(filename, 'rb')
	nframes = 0

	# for efficiency, cache attribute lookups
	read = fp.read

	data = read(bufsiz)
	i = data.find('\000\000\001')
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
				wh = data[i+1:i+4]
			except IndexError:
				data = data[i:] + read(bufsiz)
				i = 0
				wh = data[i+1:i+4]
			width = (ord(wh[0]) << 4) + (ord(wh[1]) >> 4)
			height = ((ord(wh[1]) & 0xF) << 8) + ord(wh[2])
			fp.close()
			return width, height
		elif w == '\267':
			# SEQ_END_CODE
			break
		i = data.find('\000\000\001', i+1)
		while i < 0:
			data = data[-2:] + read(bufsiz)
			if len(data) <= 2:
				break
			i = data.find('\000\000\001')
	fp.close()
	return 0, 0
