__version__ = "$Id$"
import sys
from patchlevel import patchlevel

if sys.platform == 'mac':
	shortversion = 'grinslite-%s-1.5beta'%sys.platform
	version = 'Lite for QuickTime, v1.5beta ' + patchlevel
else:
	shortversion = 'grinslite-%s-1.5'%sys.platform
	version = 'Lite for QuickTime, v1.5 ' + patchlevel
	
