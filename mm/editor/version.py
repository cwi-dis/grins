__version__ = "$Id$"
import sys
from patchlevel import patchlevel
import features

shortversion = 'grins2pro-%s-2.2'%sys.platform
version = 'Pro for %s, v2.2 %s' % (features.compatibility, patchlevel)
macpreffilename = 'GRiNS-pro-%s-2.0 Prefs' % features.compatibility_short

title = 'GRiNS Editor'
registrykey = 'Oratrix GRiNS'
registryname = 'Editor 2.0'
