cache = {}

def GetSize(file, maintype, subtype):
	if cache.has_key(file):
		return cache[file]
	if maintype == 'image':
		if subtype == 'vnd.rn-realpix':
			import realsupport
			rp = realsupport.RPParser(file)
			rp.feed(open(file).read())
			rp.close()
			width, height = rp.width, rp.height
		else:
			width, height = GetImageSize(file)
	elif maintype == 'video':
		width, height = GetVideoSize(file)
	elif maintype == 'text' and subtype == 'vnd.rn-realtext':
		import realsupport
		rp = realsupport.RTParser(file)
		rp.feed(open(file).read())
		rp.close()
		width, height = rp.width, rp.height
	else:
		width = height = 0
	cache[file] = width, height
	return width, height

def GetImageSize(file):
	try:
		import img
	except ImportError:
		import windowinterface
		width, height = windowinterface.GetImageSize(file)
	else:
		rdr = img.reader(None, file)
		width, height = rdr.width, rdr.height
	return width, height

def GetVideoSize(file):
	try:
		import mv
	except ImportError:
		import windowinterface
		width, height = windowinterface.GetVideoSize(file)
	else:
		movie = mv.OpenFile(file, mv.MV_MPEG1_PRESCAN_OFF)
		track = movie.FindTrackByMedium(mv.DM_IMAGE)
		width = track.GetImageWidth()
		height = track.GetImageHeight()
	return width, height
