cache = {}

def GetImageSize(file):
	if cache.has_key(file):
		return cache[file]
	try:
		import img
	except ImportError:
		import imageex
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
		import mpegex
		width, height = mpegex.SizeOfImage(file)
	else:
		movie = mv.OpenFile(file, mv.MV_MPEG1_PRESCAN_OFF)
		track = movie.FindTrackByMedium(mv.DM_IMAGE)
		width, height = track.GetImageWidth(), track.GetImageHeight()
	cache[file] = width, height
	return width, height
