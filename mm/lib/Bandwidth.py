__version__ = "$Id$"

# Get the prearm size and bandwidth of a node, in bits and bps.
# This module knows which channel types need special treatment.
# XXXX This is a quick-and-dirty solution. We assume that for dynamic
# media we do no preloading, and the whole media file is streamed to us
# at a continuous rate.

import MMAttrdefs
import os
from stat import ST_SIZE
import Duration
import MMurl
from urlcache import urlcache
import string

Error="Bandwidth.Error"

CONTINUOUS_CHANNELS = ['video', 'mpeg', 'movie', 'sound',  'RealAudio',
			     'RealVideo']
REAL_CHANNELS = ['RealAudio', 'RealVideo', 'RealText', 'RealPix', 'RealFlash']

def get(node, target=0):
	ntype = node.GetType()
	if ntype not in ('ext', 'slide'):
		# Nodes that are not external consume no bandwidth
		return 0, 0
	if ntype == 'slide':
		raise Error, 'Cannot compute bandwidth for slide'
	
	context = node.GetContext()
	ctype = node.GetChannelType()
	url = MMAttrdefs.getattr(node, 'file')
	url = context.findurl(url)
	val = urlcache[url].get('bandwidth')
	if val is not None:
		return val

	# We skip bandwidth retrieval for nonlocal urls (too expensive)
	type, rest = MMurl.splittype(url)
	if type and type != 'file':
##		print "DBG: Bandwidth.get: skip nonlocal", url
		return None, None
	host, rest = MMurl.splithost(rest)
	if host and host != 'localhost':
##		print "DBG: Bandwidth.get: skip nonlocal", url
		return None, None

	if ctype in REAL_CHANNELS:
		# For real channels we parse the header and such
		# XXXX If we want to do real-compatible calculations
		# we have to take preroll time and such into account.
		import realsupport
		info = realsupport.getinfo(url)
		prearm = 0
		bandwidth = 0
		if info.has_key('bitrate'):
			bandwidth = info['bitrate']
##		print "DBG: Bandwidth.get: real:", url, prearm, bandwidth
		urlcache[url]['bandwidth'] = prearm, bandwidth
		return prearm, bandwidth

	attrs = {'project_quality':MMAttrdefs.getattr(node, 'project_quality')}
	filesize = GetSize(url, target, attrs)

	if ctype in CONTINUOUS_CHANNELS:
		if filesize == None:
			return 0, None
		try:
			duration = Duration.get(node, ignoreloop=1, wanterror=1)
		except IOError:
			raise Error, 'Media item does not exist'
		if duration == 0:
			return 0, 0
##		print 'DBG: Bandwidth.get: continuous',filename, filesize, float(filesize)*8/duration
		urlcache[url]['bandwidth'] = 0, float(filesize)*8/duration
		return 0, float(filesize)*8/duration
	else:
		if filesize == None:
			return None, 0
##		print 'DBG: Bandwidth.get: discrete',filename, filesize, float(filesize)*8
		urlcache[url]['bandwidth'] = float(filesize)*8, 0
		return float(filesize)*8, 0

def GetSize(url, target=0, attrs = {}):
	val = urlcache[url].get('filesize')
	if val is not None:
		return val

	# We skip bandwidth retrieval for nonlocal urls (too expensive)
	type, rest = MMurl.splittype(url)
	if type and type != 'file':
##		print "DBG: Bandwidth.GetSize: skip nonlocal", url
		return None
	host, rest = MMurl.splithost(rest)
	if host and host != 'localhost':
##		print "DBG: Bandwidth.GetSize: skip nonlocal", url
		return None

	# Okay, get the filesize
	try:
		filename, hdrs = MMurl.urlretrieve(url)
	except IOError:
		raise Error, 'Media item does not exist'
	tmp = None
	if target:
		if hdrs.maintype == 'image':
			import tempfile, realconvert
			tmp = tempfile.mktemp('.jpg')
			dir, file = os.path.split(tmp)
			file = realconvert.convertimagefile(None, url, dir, file, attrs)
			filename = tmp = os.path.join(dir, file)
	try:
		# XXXX Incorrect for mac (resource fork size)
		statb = os.stat(filename)
	except os.error:
##		print "DBG: Bandwidth.get: nonexisting", filename
		raise Error, 'Media item does not exist'
	if tmp:
		os.unlink(tmp)
	filesize = statb[ST_SIZE]
	urlcache[url]['filesize'] = filesize
	return filesize
