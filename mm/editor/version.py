__version__ = "$Id$"
import sys
from patchlevel import patchlevel
import settings
if settings.get('lightweight'):
	version = 'Lite for RealSystem G2, v1.5 ' + patchlevel
	shortversion = 'grinslite-%s-1.5beta'%sys.platform
else:
	version = 'Pro for RealSystem G2, v1.5 ' + patchlevel
	shortversion = 'grinspro-%s-1.5alpha'%sys.platform
	
