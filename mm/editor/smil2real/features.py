__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
from FeatureSet import *
import sys

feature_set = [
	ADVANCED_PROPERTIES,
	ASSETS_VIEW,
	CUSTOM_REGIONS,
	EXPORT_REAL,
	HYPERLINKS_VIEW,
	H_MODIFY_STRUCTURE,
	LAYOUT_VIEW,
	PLAYER_VIEW,
	SOURCE_VIEW,
	STRUCTURE_VIEW,
	TRANSITION_VIEW,
	UNIFIED_FOCUS,
	AUTO_EVALUATE,
	SHOW_MEDIA_CHILDREN,
	UNSUPPORTED_ERROR,
	]

version = 'Real'
compatibility = Boston
compatibility_short = 'SMIL2Real'
cmif = 0
lightweight = 0
editor = 1
license_features_needed = ('smil2real', sys.platform)

auto_evaluate_period = 7	# 7 days auto-evaluate

# URL to be used for buying the product
buyurl = 'http://www.realnetworks.com/special/partners/upsell.html?act=orx'
