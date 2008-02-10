__version__ = "$Id$"
import sys
from patchlevel import patchlevel

if sys.platform == 'mac':
    shortversion = 'grinslite-%s-1.5beta'%sys.platform
    version = 'Lite for QuickTime, v1.5beta ' + patchlevel
    macpreffilename = 'GRiNS-lite-%s-1.5 Prefs' % features.compatibility_short
else:
    shortversion = 'grinslite-%s-1.5'%sys.platform
    version = 'Lite for QuickTime, v1.5 ' + patchlevel
    macpreffilename = 'GRiNS-pro-%s-1.5 Prefs' % features.compatibility_short

title = 'GRiNS Editor Lite'
registrykey = 'Oratrix GRiNS'
registryname = 'Editor 2.0 Lite'
