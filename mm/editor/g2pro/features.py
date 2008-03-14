__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
import sys

from FeatureSet import *

feature_set = [EXPORT_SMIL1, EXPORT_SMIL20, EXPORT_REAL,
               PLAYER_VIEW, STRUCTURE_VIEW, LAYOUT_VIEW, HYPERLINKS_VIEW,
               USER_GROUPS, TRANSITION_VIEW, PARAMGROUP_VIEW,
               H_MODIFY_STRUCTURE
               ]

#
version = 'pro'
compatibility = G2
compatibility_short = 'G2'
cmif = 0
lightweight = 0
editor = 1
level = 'pro'
license_features_needed = ('pro', sys.platform)
