__version__ = "$Id$"
import sys
from patchlevel import patchlevel

if sys.platform == 'mac':
	shortversion = 'grinsqtpro-%s-1.5beta'%sys.platform
	version = 'Pro for QuickTime, v1.5beta ' + patchlevel
else:
	shortversion = 'grinsqtpro-%s-1.5'%sys.platform
	version = 'Pro for QuickTime, v1.5 ' + patchlevel
	
