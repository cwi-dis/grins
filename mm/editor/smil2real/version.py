__version__ = "$Id$"

import sys
from patchlevel import patchlevel
import features

shortversion = 'grins2real-%s-2.1'%sys.platform
version = ('Editor for RealONE, Version 2.1 %s' % patchlevel).strip()
macpreffilename = 'GRiNS-%s-2.0 Prefs' % features.compatibility_short
title = 'GRiNS Editor for RealONE'
registrykey = 'Oratrix GRiNS'
registryname = 'RealONE'

# Note: this GUID *must* be different for each version
# and each product!

guid = '{C3469539-EB6C-4b3c-838D-B7AD6B0DEBCA}'
