__version__ = "$Id$"

from patchlevel import patchlevel
import settings
if settings.get('lightweight'):
	version = 'Lite for RealSystem G2, v1.5 beta ' + patchlevel
else:
	version = 'Editor 1.5 beta ' + patchlevel
