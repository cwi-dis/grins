__version__ = "$Id$"

Error = 'audio.Error'

def reader(filename, dstfmts = None, dstrates = None, loop=1):
	import audiofile, audioconvert
	rdr = audiofile.reader(filename)
	return audioconvert.convert(rdr, dstfmts, dstrates, loop)
