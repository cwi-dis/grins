__version__ = "$Id$"
import sys
from patchlevel import patchlevel
import settings
if settings.get('lightweight'):
	version = 'Lite for RealSystem G2, v1.5 beta ' + patchlevel
	shortversion = 'grinslite-%s-1.5beta'%sys.platform
else:
	version = 'Editor 1.5 alpha ' + patchlevel
	shortversion = 'grinspro-%s-1.5alpha'%sys.platform
	
