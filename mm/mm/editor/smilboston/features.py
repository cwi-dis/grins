__version__ = "$Id$"

# Features for GRiNS for G2, pro version

from compatibility import *
from FeatureSet import *
import sys

feature_set = [
	EXPORT_SMIL2,
##	EXPORT_SMIL1,
	EXPORT_REAL,
##	EXPORT_QT, EXPORT_WMP,
	EXPORT_HTML_TIME,
	EXPORT_3GPP,			# unimplemented
	EXPORT_WINCE,
	PLAYER_VIEW, STRUCTURE_VIEW, LAYOUT_VIEW, HYPERLINKS_VIEW,
	SOURCE_VIEW, ASSETS_VIEW,
	SOURCE_VIEW_EDIT,
	ERRORS_VIEW,
	USER_GROUPS,
	TRANSITION_VIEW,
	UNIFIED_FOCUS,
	H_MODIFY_STRUCTURE, CUSTOM_REGIONS,
	H_ASSIGN_NAME,
	CREATE_TEMPLATES,
	ADVANCED_PROPERTIES,
	PREFERENCES,
	ALIGNTOOL,
	SHOW_MEDIA_CHILDREN,
	MULTIPLE_TOPLAYOUT,
	INTERNAL_LINKS,
##	AUTO_EVALUATE,
	]

##auto_evaluate_period = 7	# 7 days auto-evaluate
version = 'pro'
compatibility = Boston
compatibility_short = 'SMIL2'
cmif = 0
lightweight = 0
editor = 1
license_features_needed = ('smil2pro', sys.platform)
