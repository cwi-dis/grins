# Cache durations of mpeg files

import FileCache
import urllib

def getduration(filename):
	try:
		import cl
	except ImportError:
		raise IOError, 'cannot import cl module'
	filename = urllib.url2pathname(filename)
	fp = open(filename, 'rb')
	hsize = cl.QueryMaxHeaderSize(cl.MPEG_VIDEO)
	hdr = fp.read(hsize)
	cmp = cl.OpenDecompressor(cl.MPEG_VIDEO)
	dummy = cmp.ReadHeader(hdr)
	pbuf = [cl.FRAME_RATE, 0, cl.NUMBER_OF_FRAMES, 0]
	cmp.GetParams(pbuf)
##	print 'mpeg: rate', pbuf[1], 'nframe', pbuf[3]
	return pbuf[3]/pbuf[1]
	
duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
