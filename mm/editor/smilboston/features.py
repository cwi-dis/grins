__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
from FeatureSet import *
import sys

feature_set = [EXPORT_CMIF, EXPORT_SMIL2, EXPORT_QT, EXPORT_WMP,
				PLAYER_VIEW, STRUCTURE_VIEW, TIMELINE_VIEW, LAYOUT_VIEW, HYPERLINKS_VIEW, CHANNEL_VIEW,
				USER_GROUPS, TRANSITION_VIEW,
				UNIFIED_FOCUS,
#				H_VBANDWIDTH,
				H_MODIFY_STRUCTURE, CUSTOM_REGIONS,
				];
#
if sys.platform == 'win32':
	feature_set.append(TEMPORAL_VIEW)

version = 'pro'                         # I'm not sure here.. mjvdg
compatibility = Boston
compatibility_short = 'SMIL2'
cmif = 0
lightweight = 0
editor = 1
# XXX do we require sys.platform?
license_features_needed = ('smil2pro', sys.platform)
