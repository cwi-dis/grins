# Cache durations of mpeg files

import FileCache
import cl
import CL

def getduration(filename):
	fp = open(filename, 'r')
	hsize = cl.QueryMaxHeaderSize(CL.MPEG_VIDEO)
	hdr = fp.read(hsize)
	cmp = cl.OpenDecompressor(CL.MPEG_VIDEO)
	dummy = cmp.ReadHeader(hdr)
	pbuf = [CL.FRAME_RATE, 0, CL.NUMBER_OF_FRAMES, 0]
	cmp.GetParams(pbuf)
##	print 'mpeg: rate', pbuf[1], 'nframe', pbuf[3]
	return pbuf[3]/pbuf[1]
	
duration_cache = FileCache.FileCache(getduration)

get = duration_cache.get
