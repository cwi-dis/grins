import string, MMurl, urlcache

def GetSize(url, maintype = None, subtype = None):
	cache = urlcache.urlcache[url]
	width = cache.get('width')
	height = cache.get('height')
	if width is not None and height is not None:
		return width, height
	u = None
	if maintype is None:
		if cache.has_key('mimetype'):
			maintype, subtype = cache['mimetype']
		else:
			try:
				u = MMurl.urlopen(url)
			except IOError:
				# don't cache non-existing file
				return 0, 0
			maintype = u.headers.getmaintype()
			subtype = u.headers.getsubtype()
			cache['mimetype'] = maintype, subtype
	if string.find(string.lower(subtype), 'real') >= 0 or string.find(subtype, 'shockwave') >= 0:
		# any RealMedia type
		import realsupport
		info = realsupport.getinfo(url, u)
		width = info.get('width', 0)
		height = info.get('height', 0)
	elif maintype == 'image':
		if u is not None:
			u.close()
		del u
		try:
			file = MMurl.urlretrieve(url)[0]
		except IOError:
			return 0, 0
		width, height = GetImageSize(file)
	elif maintype == 'video':
		if u is not None:
			u.close()
		del u
		try:
			file = MMurl.urlretrieve(url)[0]
		except IOError:
			return 0, 0
		width, height = GetVideoSize(file)
	else:
		width = height = 0
	if width != 0 and height != 0:
		cache['width'] = width
		cache['height'] = height
	return width, height

def GetImageSize(file):
	import windowinterface
	try:
		return windowinterface.GetImageSize(file)
	except:
		return 0, 0

def GetVideoSize(file):
	import windowinterface
	try:
		width, height = windowinterface.GetVideoSize(file)
	except:
		width = height = 0
	return width, height
