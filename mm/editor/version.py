__version__ = "$Id$"
import sys
from patchlevel import patchlevel
import features
if features.lightweight:
	shortversion = 'grinslite-%s-1.5.1'%sys.platform
	version = 'Lite for %s, v1.5.1 %s' % (features.compatibility, patchlevel)
	macpreffilename = 'GRiNS-lite-%s-1.5 Prefs' % features.compatibility_short
else:
	shortversion = 'grinspro-%s-1.5.1'%sys.platform
	version = 'Pro for %s, v1.5.1 %s' % (features.compatibility, patchlevel)
	macpreffilename = 'GRiNS-pro-%s-1.5 Prefs' % features.compatibility_short
