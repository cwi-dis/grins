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
import urllib

CONTINUOUS_CHANNELS = ['video', 'mpeg', 'movie', 'sound',  'RealAudio',
			     'RealVideo']
REAL_CHANNELS = ['RealAudio', 'RealVideo', 'RealText', 'RealPix', 'RealFlash']

def get(node):
	if node.GetType() != 'ext':
		# Nodes that are not external consume no bandwidth
		return 0, 0
	
	channel = node.GetChannel()
	context = node.GetContext()
	ctype = channel['type']
	url = MMAttrdefs.getattr(node, 'file')
	url = context.findurl(url)

	# We skip bandwidth retrieval for nonlocal urls (too expensive)
	type, rest = urllib.splittype(url)
	if type and type != 'file':
##		print "DBG: Bandwidth.get: skip nonlocal", url
		return 0, 0
	host, rest = urllib.splithost(rest)
	if host and host != 'localhost':
##		print "DBG: Bandwidth.get: skip nonlocal", url
		return 0, 0

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
		return prearm, bandwidth
	
	# Okay, get the filesize
	filename = urllib.url2pathname(rest)
	try:
		# XXXX Incorrect for mac (resource fork size)
		statb = os.stat(filename)
	except os.error:
##		print "DBG: Bandwidth.get: nonexisting", filename
		return 0, 0
	filesize = statb[ST_SIZE]

	if ctype in CONTINUOUS_CHANNELS:
		duration = Duration.get(node, ignoreloop=1)
		if duration == 0:
##			print "DBG: Bandwidth.get: zero-time node"
			return 0, 0
##		print 'CONT', filesize, float(filesize)*8/duration
		return 0, float(filesize)*8/duration
	else:
##		print 'STATIC', filesize, float(filesize)*8
		return float(filesize)*8, 0
