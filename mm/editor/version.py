__version__ = "$Id$"
import sys
from patchlevel import patchlevel
import features

if features.version == 'Snap!':
	shortversion = 'grinssnap-%s-2.0'%sys.platform
	version = 'Snap! for %s, v2.0 %s' % (features.compatibility, patchlevel)
	macpreffilename = 'GRiNS-Snap!-%s-2.0 Prefs' % features.compatibility_short	
elif features.lightweight:		# TODO: change this to..? mjvdg.
	shortversion = 'grinslite-%s-2.0'%sys.platform
	version = 'Lite for %s, v2.0 %s' % (features.compatibility, patchlevel)
	macpreffilename = 'GRiNS-lite-%s-2.0 Prefs' % features.compatibility_short
else:
	shortversion = 'grinspro-%s-2.0'%sys.platform
	version = 'Pro for %s, v2.0 %s' % (features.compatibility, patchlevel)
	macpreffilename = 'GRiNS-pro-%s-2.0 Prefs' % features.compatibility_short

title = 'GRiNS Editor'
registrykey = 'Oratrix GRiNS'
registryname = 'Editor 2.0'
