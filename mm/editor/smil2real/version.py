__version__ = "$Id$"

import sys
from patchlevel import patchlevel
import features

shortversion = 'grins2real-%s-2.0'%sys.platform
version = ('Editor for RealONE %s' % patchlevel).strip()
macpreffilename = 'GRiNS-%s-2.0 Prefs' % features.compatibility_short
title = 'GRiNS Editor for RealONE'
