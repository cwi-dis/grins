import string, MMurl

cache = {}

def GetSize(url, maintype = None, subtype = None):
	if cache.has_key(url):
		return cache[url]
	u = None
	if maintype is None:
		u = MMurl.urlopen(url)
		maintype = u.headers.getmaintype()
		subtype = u.headers.getsubtype()
	if string.find(string.lower(subtype), 'real') >= 0:
		# any RealMedia type
		import realsupport
		info = realsupport.getinfo(url, u)
		width = info.get('width', 200)
		height = info.get('height', 200)
	elif maintype == 'image':
		file = MMurl.urlretrieve(url)[0]
		width, height = GetImageSize(file)
	elif maintype == 'video':
		file = MMurl.urlretrieve(url)[0]
		width, height = GetVideoSize(file)
	else:
		width = height = 0
	cache[url] = width, height
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
