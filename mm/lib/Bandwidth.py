__version__ = "$Id$"

# Get the prearm size and bandwidth of a node, in bits and bps.
# This module knows which channel types need special treatment.
# XXXX This is a quick-and-dirty solution. We assume that for dynamic
# media we do no preloading, and the whole media file is streamed to us
# at a continuous rate.

import MMAttrdefs
import os
from stat import ST_SIZE
import MMurl
import urlcache
import string

Error="Bandwidth.Error"

# This value has to be determined.
DEFAULT_STREAMING_MEDIA_PRELOAD=5
DEFAULT_STATIC_MEDIA_BITRATE=12000

# These rates are derived from the Real Producer SDK documentation.
# Later we may want to give the user the ability to change the bitrates.
TARGET_BITRATES = [
	20 * 1024,			# 28k8 modem
	34 * 1024,			# 56k modem
	45 * 1024,			# Single ISDN
	80 * 1024,			# Dual ISDN
	220 * 1024,			# Cable modem
	150 * 1024,			# LAN
	]

def getstreamdata(node, target=0):
	ntype = node.GetType()
	if ntype not in ('ext', 'slide'):
		# Nodes that are not external consume no bandwidth
		return 0, 0, 0, 0
	if ntype == 'slide':
		raise Error, 'Cannot compute bandwidth for slide.'
	
	context = node.GetContext()
	ctype = node.GetChannelType()

	if ntype == 'ext' and ctype == 'RealPix':
		# Get information from the attributes
		bitrate = MMAttrdefs.getattr(node, 'bitrate')
		# XXX Incorrect
		return 0, bitrate, bitrate, 0

	url = MMAttrdefs.getattr(node, 'file')
	url = context.findurl(url)
	val = urlcache.urlcache[url].get('bandwidth')
	if val is not None:
		return val

	# We skip bandwidth retrieval for nonlocal urls (too expensive)
	type, rest = MMurl.splittype(url)
	if type and type != 'file':
##		print "DBG: Bandwidth.get: skip nonlocal", url
		return None, None, None, None
	host, rest = MMurl.splithost(rest)
	if host and host != 'localhost':
##		print "DBG: Bandwidth.get: skip nonlocal", url
		return None, None, None, None

	mtype = urlcache.mimetype(url)
	if not mtype:
		raise Error, 'Cannot open: %s'%url
	maintype, subtype = mtype.split('/')
	if string.find(subtype, 'real') >= 0:
		# For real channels we parse the header and such
		# XXXX If we want to do real-compatible calculations
		# we have to take preroll time and such into account.
		import realsupport
		info = realsupport.getinfo(url)
		bandwidth = 0
		if info.has_key('bitrate'):
			bandwidth = info['bitrate']
		if info.has_key('preroll'):
			prerolltime = info['preroll']
		else:
			prerolltime = DEFAULT_STREAMING_MEDIA_PRELOAD
		prerollbits = prerolltime*bandwidth
##		print "DBG: Bandwidth.get: real:", url, prearm, bandwidth
		urlcache.urlcache[url]['bandwidth'] = prerollbits, prerolltime, bandwidth, bandwidth
		return prerollbits, prerolltime, bandwidth, bandwidth
	if maintype == 'audio' or maintype == 'video':
		targets = MMAttrdefs.getattr(node, 'project_targets')
		bitrate = TARGET_BITRATES[0] # default: 28k8 modem
		for i in range(len(TARGET_BITRATES)):
			if targets & (1 << i):
				bitrate = TARGET_BITRATES[i]
		# don't cache since the result depends on project_targets
		prerollseconds = DEFAULT_STREAMING_MEDIA_PRELOAD
		prerollbits = prerollseconds*bitrate
		return prerollbits, prerollseconds, bitrate, bitrate

	# XXXX Need to pass more args (crop, etc)
	attrs = {'project_quality':MMAttrdefs.getattr(node, 'project_quality')}
	filesize = GetSize(url, target, attrs, MMAttrdefs.getattr(node, 'project_convert'))
	if filesize is None:
		return None, None, None, None

##	print 'DBG: Bandwidth.get: discrete',filename, filesize, float(filesize)*8
	bits = float(filesize)*8
	prerollbitrate = DEFAULT_STATIC_MEDIA_BITRATE
	urlcache.urlcache[url]['bandwidth'] = bits, None, prerollbitrate, None
	return bits, None, prerollbitrate, None

##def GetSize(url, target=0, attrs = {}, convert = 1):
##	val = urlcache.urlcache[url].get('filesize')
##	if val is not None:
##		return val

##	# We skip bandwidth retrieval for nonlocal urls (too expensive)
##	type, rest = MMurl.splittype(url)
##	if type and type != 'file':
####		print "DBG: Bandwidth.GetSize: skip nonlocal", url
##		return None
##	host, rest = MMurl.splithost(rest)
##	if host and host != 'localhost':
####		print "DBG: Bandwidth.GetSize: skip nonlocal", url
##		return None

##	# Okay, get the filesize
##	try:
##		filename, hdrs = MMurl.urlretrieve(url)
##	except IOError:
##		raise Error, 'Cannot open: %s'%url
##	tmp = None
##	if target and hdrs.maintype == 'image' and hdrs.subtype != 'svg-xml' and convert:
##		import tempfile
##		tmp = tempfile.mktemp('.jpg')
##		dir, file = os.path.split(tmp)
##		try:
##			import realconvert
##			cfile = realconvert.convertimagefile(None, url, dir, file, attrs)
##		except:
##			# XXXX Too many different errors can occur in convertimagefile:
##			# I/O errors, image file errors, etc.
##			raise Error, 'Cannot convert to RealMedia.'
##		if cfile: file = cfile
##		filename = tmp = os.path.join(dir, file)
##	try:
##		# XXXX Incorrect for mac (resource fork size)
##		statb = os.stat(filename)
##	except os.error:
####		print "DBG: Bandwidth.get: nonexisting", filename
##		raise Error, 'Tempfile does not exist: %s'%filename
##	if tmp:
##		try:
##			os.unlink(tmp)
##		except:
##			pass
##	filesize = statb[ST_SIZE]
##	urlcache.urlcache[url]['filesize'] = filesize
##	return filesize
