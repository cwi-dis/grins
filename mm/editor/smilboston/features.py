__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
import sys

#
version = 'pro'                         # I'm not sure here.. mjvdg
compatibility = Boston
compatibility_short = 'SMIL2'
cmif = 0
lightweight = 0
editor = 1
# XXX do we require sys.platform?
license_features_needed = ('editor', sys.platform)
