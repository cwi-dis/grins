__version__ = "$Id$"

import sys
from patchlevel import patchlevel
import features

shortversion = 'grins2real-%s-2.0'%sys.platform
version = ('Editor for Real, Version 2.0 %s' % patchlevel).strip()
macpreffilename = 'GRiNS-%s-2.0 Prefs' % features.compatibility_short
