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
license_features_needed = ('player', sys.platform)
expiry_date = (2001, 1, 15)
