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
		try:
			import mpegex, cmifex
		except ImportError:
			return 0, 0
		else:
			h = cmifex.CreateWindow("",10,10,100,100,0)
			width, height = mpegex.SizeOfImage(h,file)
			h.DestroyWindow()
	else:
		movie = mv.OpenFile(file, mv.MV_MPEG1_PRESCAN_OFF)
		track = movie.FindTrackByMedium(mv.DM_IMAGE)
		width = track.GetImageWidth()
		height = track.GetImageHeight()
	cache[file] = width, height
	return width, height
