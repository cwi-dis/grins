import string, MMurl, urlcache

def GetSize(url, maintype = None, subtype = None):
	cache = urlcache.urlcache[url]
	width = cache.get('width')
	height = cache.get('height')
	if width is not None and height is not None:
		return width, height
	u = None
	if maintype is None:
		try:
			u = MMurl.urlopen(url)
		except IOError:
			# don't cache non-existing file
			return 0, 0
		maintype = u.headers.getmaintype()
		subtype = u.headers.getsubtype()
	if string.find(string.lower(subtype), 'real') >= 0:
		# any RealMedia type
		import realsupport
		info = realsupport.getinfo(url, u)
		width = info.get('width', 200)
		height = info.get('height', 200)
	elif maintype == 'image':
		try:
			file = MMurl.urlretrieve(url)[0]
		except IOError:
			return 0, 0
		width, height = GetImageSize(file)
	elif maintype == 'video':
		try:
			file = MMurl.urlretrieve(url)[0]
		except IOError:
			return 0, 0
		width, height = GetVideoSize(file)
	else:
		width = height = 0
	cache['width'] = width
	cache['height'] = height
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
