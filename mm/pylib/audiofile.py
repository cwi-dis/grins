Error = 'audiofile.Error'

def open(filename, mode):
	if mode[:1] == 'r':
		import whatsound
		res = whatsound.whathdr(filename)
		if not res:
			raise Error, 'unknown audio format'
		fmt = res[0]
		if fmt == 'aiff' or fmt == 'aifc':
			import aifc
			aifc.Error = Error
			return aifc.open(filename, mode)
		if fmt == 'wav':
			import wave
			wave.Error = Error
			return wave.open(filename, mode)
		if fmt == 'au':
			import sunau
			sunau.Error = Error
			return sunau.open(filename, mode)
		raise Error, 'unknown audio format'
	else:
		raise Error, 'use specific module for writing'
