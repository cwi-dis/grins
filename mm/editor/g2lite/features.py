__version__ = "$Id$"

# Features for GRiNS for G2, lite version

from compatibility import *
from FeatureSet import *
import sys

feature_set = []

#
version = 'lite'
compatibility = G2
compatibility_short = 'G2'
cmif = 0
lightweight = 1
editor = 1
level = 'lite'
license_features_needed = ('light', sys.platform)
