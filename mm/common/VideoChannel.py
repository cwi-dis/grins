__version__ = "$Id$"

from sys import platform

if platform == 'irix6':
	try:
		from SGIVideoChannel import *
	except ImportError:
		from MPEGVideoChannel import *
elif platform == 'sunos5' or platform == 'irix5':
	from MPEGVideoChannel import *
elif platform == 'mac':
	from MACVideoChannel import *
elif platform == 'nt' or platform == 'win32':
	from NTVideoChannel import *
else:
	raise ImportError('No appropriate VideoChannel for this platform')
