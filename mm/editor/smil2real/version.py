__version__ = "$Id$"

import sys
from patchlevel import patchlevel
import features

shortversion = 'grins2real-%s-2.2'%sys.platform
version = ('Editor for RealONE, Version 2.2 %s' % patchlevel).strip()
macpreffilename = 'GRiNS-%s-2.2 Prefs' % features.compatibility_short
title = 'GRiNS Editor for RealOne'
registrykey = 'Oratrix GRiNS'
registryname = 'RealONE'

# Note: this GUID *must* be different for each version
# and each product!
# Generate with \Program Files\Microsoft Visual Studio\Common\Tools\uuidgen

guid = '{bc0e9a31-95cb-49aa-b90a-a6079763afbe}'
