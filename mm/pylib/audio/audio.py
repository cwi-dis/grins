Error = 'audio.Error'

def reader(filename, dstfmts = None, dstrates = None):
	import audiofile, audioconvert
	rdr = audiofile.reader(filename)
	return audioconvert.convert(rdr, dstfmts, dstrates)
