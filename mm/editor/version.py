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

# Note: this GUID *must* be different for each version
# and each product!
# Generate with \Program Files\Microsoft Visual Studio\Common\Tools\uuidgen

guid = '{9d4a7905-82f5-477f-aaf0-71ad7446bd95}'
