__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
import sys

#
compatibility = Boston
compatibility_short = 'SMIL2'
cmif = 0
lightweight = 0
editor = 0
# XXX do we require sys.platform?
license_features_needed = ('smil2player', sys.platform)
# Expiry date not relevant anymore since the Player requires a license.
# On Windows in the frozen version, we get a crash when the player
# tries to exit because it expired.
#expiry_date = (2001, 1, 15)

# RTIPA start
RTIPA = 0
# RTIPA end
