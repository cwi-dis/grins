__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
from FeatureSet import *
import sys

feature_set = [];

#
version = 'pro'
compatibility = G2
compatibility_short = 'G2'
cmif = 0
lightweight = 0
editor = 1
level = 'pro'
license_features_needed = ('pro', sys.platform)
