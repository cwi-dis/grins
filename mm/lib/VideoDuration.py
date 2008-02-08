__version__ = "$Id$"

from sys import platform

if platform == 'irix6':
    try:
        from SGIVideoDuration import *
    except ImportError:
        from MPEGVideoDuration import *
elif platform == 'sunos5' or platform == 'irix5' or platform[:5] == 'linux':
    from MPEGVideoDuration import *
elif platform in ('mac', 'darwin'):
    from MACVideoDuration import *
elif platform == 'nt' or platform == 'win32':
    from NTVideoDuration import *
else:
    raise ImportError('No appropriate VideoDuration for this platform')
