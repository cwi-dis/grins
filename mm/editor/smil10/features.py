__version__ = "$Id$"

# Features for GRiNS for SMIL 1.0, pro version

from compatibility import *
from FeatureSet import *
feature_set = []

#
version = ""                            # I'm not sure here - mjvdg.
compatibility = SMIL10
compatibility_short = 'SMIL'
cmif = 0
lightweight = 0
editor = 1
level = ''

# no sys.platform required in this product
license_features_needed = ('editor',)
