__version__ = "$Id$"

from sys import platform

if platform == 'irix6':
	try:
		from SGIVideoDuration import *
	except ImportError:
		from MPEGVideoDuration import *
elif platform == 'sunos5' or platform == 'irix5':
	from MPEGVideoDuration import *
elif platform == 'mac':
	from MACVideoDuration import *
elif platform == 'nt':
	from NTVideoDuration import *
else:
	raise ImportError('No appropriate VideoDuration for this platform')
