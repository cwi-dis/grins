cache = {}

def GetSize(file, maintype, subtype):
	if cache.has_key(file):
		return cache[file]
	if subtype[:6] == 'vnd.rn':
		# any RealMedia type
		import realsupport
		info = realsupport.getinfo(file)
		width = info.get('width', 200)
		height = info.get('height', 200)
	elif maintype == 'image':
		width, height = GetImageSize(file)
	elif maintype == 'video':
		width, height = GetVideoSize(file)
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
