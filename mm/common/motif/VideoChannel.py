__version__ = "$Id$"

from sys import platform

if platform == 'irix6':
    try:
        from SGIVideoChannel import *
    except ImportError:
        from MPEGVideoChannel import *
elif platform == 'sunos5' or platform == 'irix5' or platform[:5] == 'linux':
    from MPEGVideoChannel import *
else:
    raise ImportError('No appropriate VideoChannel for this platform')
