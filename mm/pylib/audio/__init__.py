__version__ = "$Id$"

Error = 'audio.Error'

def reader(filename, dstfmts = None, dstrates = None, loop=1):
	import file, convert
	rdr = file.reader(filename)
	return convert.convert(rdr, dstfmts, dstrates, loop)
