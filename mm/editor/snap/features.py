__version__ = "$Id$"

# Features for GRiNS for G2, lite version

from compatibility import *
import sys

#
version = 'Snap!'
compatibility = G2
compatibility_short = 'G2'
cmif = 0
lightweight = 1                         # This is a toggle between pro/lite. We need a switch. TODO - mjvdg
editor = 1
level = 'lite'
license_features_needed = ('light', sys.platform)

grins_snap = 1
