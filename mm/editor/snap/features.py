__version__ = "$Id$"

# Features for GRiNS for G2, lite version

from compatibility import *
from FeatureSet import *
import sys

feature_set = [EXPORT_CMIF, EXPORT_SMIL2, EXPORT_QT, EXPORT_WMP,
               PLAYER_VIEW, STRUCTURE_VIEW,
               UNIFIED_FOCUS, 
               #H_TRANSITIONS, H_VBANDWIDTH,
               #H_DROPBOX
               ]

# These can be deprecated when I've multilated most of the source code.
#
version = 'Snap!'
compatibility = Boston
compatibility_short = 'SMIL2'
cmif = 0
lightweight = 1                         # er.. so why can I still edit structure?
editor = 1
level = 'lite'
license_features_needed = ('light', sys.platform)

grins_snap = 1
