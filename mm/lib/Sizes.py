cache = {}

def GetImageSize(file):
	if cache.has_key(file):
		return cache[file]
	try:
		import img
	except ImportError:
		try:
			import imageex
		except ImportError:
			return 0, 0
		else:
			width, height = imageex.SizeOfImage(file)
	else:
		rdr = img.reader(None, file)
		width, height = rdr.width, rdr.height
	cache[file] = width, height
	return width, height

def GetVideoSize(file):
	if cache.has_key(file):
		return cache[file]
	try:
		import mv
	except ImportError:
		import windowinterface
		width, height = windowinterface.GetVideoSize(h,file)
	else:
		movie = mv.OpenFile(file, mv.MV_MPEG1_PRESCAN_OFF)
		track = movie.FindTrackByMedium(mv.DM_IMAGE)
		width = track.GetImageWidth()
		height = track.GetImageHeight()
	cache[file] = width, height
	return width, height
