__version__ = "$Id$"

# Features for GRiNS for G2, lite version

from compatibility import *
from FeatureSet import *
import sys

# Warning: removing some of these will stop different parts of the program from working.
feature_set = [EXPORT_CMIF, EXPORT_SMIL2, EXPORT_QT, EXPORT_WMP,
               PLAYER_VIEW, STRUCTURE_VIEW, LINKEDIT_LIGHT, #TRANSITION_VIEW, HYPERLINKS_VIEW, CHANNEL_VIEW, USER_GROUPS,
	       LAYOUT_VIEW,
	       TEMPORAL_VIEW,
	       CHANNEL_VIEW,
               UNIFIED_FOCUS,
               H_MODIFY_STRUCTURE,
               H_TRANSITIONS, H_VBANDWIDTH,
               H_DROPBOX,
               H_COLLAPSE,
               H_TIMESTRIP,         
               ]

# These can be deprecated when I've multilated most of the source code.
#
version = 'Snap!'
compatibility = Boston
compatibility_short = 'SMIL2'
cmif = 0
lightweight = 0                         # er.. so why can I still edit structure?
editor = 1
level = 'lite'
license_features_needed = ('smil2light', sys.platform)

grins_snap = 1
