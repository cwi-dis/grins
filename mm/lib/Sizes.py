__version__ = "$Id$"

import string, MMurl, urlcache

def GetSize(url, maintype = None, subtype = None):
	if not url:
		return 0, 0
	cache = urlcache.urlcache[url]
	width = cache.get('width')
	height = cache.get('height')
	if width is not None and height is not None:
		return width, height
	u = None
	if maintype is None:
		mtype = urlcache.mimetype(url)
		if not mtype:
			return 0, 0
		maintype, subtype = mtype.split('/')
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
		import ChannelMap
		if ChannelMap.channelmap.has_key('svg') and subtype == 'svg-xml':
			width, height = GetSvgSize(url)
		else:
			try:
				file = MMurl.urlretrieve(url)[0]
			except IOError:
				return 0, 0
			width, height = GetImageSize(file)
	elif maintype == 'video':
		if u is not None:
			u.close()
		del u
		width, height = GetVideoSize(url)
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
	except Exception, arg:
		print 'GetImageSize raised Exception', arg
		return 0, 0

def GetSvgSize(url):
	import svgdom
	try:
		return svgdom.GetSvgSize(url)
	except Exception, arg:
		print 'GetSvgSize raised Exception', arg
		return 0, 0
		
def GetVideoSize(url, subtype=None):
	import windowinterface
	try:
		width, height = windowinterface.GetVideoSize(url)
	except Exception, arg:
		print 'GetVideoSize raised Exception', arg
		width = height = 0
	return width, height
