__version__ = "$Id$"
import sys
from patchlevel import patchlevel
import features

if features.lightweight:
	shortversion = 'grinslite-%s-1.5'%sys.platform
	version = 'Lite for %s, v1.5 %s' % (features.compatibility, patchlevel)
else:
	shortversion = 'grinspro-%s-2.0'%sys.platform
	version = 'Pro for %s, v2.0 %s' % (features.compatibility, patchlevel)
