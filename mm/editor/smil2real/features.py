__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
from FeatureSet import *
import sys

feature_set = [
	ADVANCED_PROPERTIES,
	ASSETS_VIEW,
	CHANNEL_VIEW,
	CUSTOM_REGIONS,
	EXPORT_HTML_TIME,
	EXPORT_REAL,
	HYPERLINKS_VIEW,
	H_MODIFY_STRUCTURE,
	LAYOUT_VIEW,
	PLAYER_VIEW,
	SOURCE_VIEW,
	STRUCTURE_VIEW,
	TRANSITION_VIEW,
	UNIFIED_FOCUS,
	]

version = 'Real'
compatibility = Boston
compatibility_short = 'SMIL2Real'
cmif = 0
lightweight = 0
editor = 1
license_features_needed = ('smil2real', sys.platform)
