__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
import sys

from FeatureSet import *

feature_set = [EXPORT_CMIF, EXPORT_SMIL2, EXPORT_QT, EXPORT_WMP,
               PLAYER_VIEW, STRUCTURE_VIEW, TIMELINE_VIEW, LAYOUT_VIEW, HYPERLINKS_VIEW, CHANNEL_VIEW,
               USER_GROUPS, TRANSITION_VIEW,
               #H_NIPPLES, H_VBANDWIDTH,
               H_MODIFY_STRUCTURE
               ];

#
version = 'pro'
compatibility = G2
compatibility_short = 'G2'
cmif = 0
lightweight = 0
editor = 1
level = 'pro'
license_features_needed = ('pro', sys.platform)
