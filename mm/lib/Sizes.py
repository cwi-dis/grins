def GetImageSize(file):
	try:
		import img
	except ImportError:
		try:
			import imageex
		except ImportError:
			return 0, 0
		else:
			return imageex.something(file)
	else:
		rdr = img.reader(None, file)
		return rdr.width, rdr.height

def GetVideoSize(file):
	try:
		import mv
	except ImportError:
		try:
			import movieex
		except ImportError:
			return 0, 0
		else:
			return movieex.something(file)
	else:
		movie =mv.OpenFile(file, mv.MV_MPEG1_PRESCAN_OFF)
		track = movie.FindTrackByMedium(mv.DM_IMAGE)
		return track.GetImageWidth(), track.GetImageHeight()
