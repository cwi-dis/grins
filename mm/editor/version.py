__version__ = "$Id$"
import sys
from patchlevel import patchlevel
import settings
if settings.get('lightweight'):
	version = 'Lite for RealSystem G2, v1.5.1 ' + patchlevel
	if sys.platform == 'mac':
		shortversion = 'grinslite-%s-1.5beta'%sys.platform
	else:
		shortversion = 'grinslite-%s-1.5.1'%sys.platform
else:
	version = 'Pro for RealSystem G2, v1.5.1 ' + patchlevel
	if sys.platform == 'mac':
		shortversion = 'grinspro-%s-1.5beta'%sys.platform
	else:
		shortversion = 'grinspro-%s-1.5.1'%sys.platform
	
