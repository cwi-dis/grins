# This file contains features for the various features available
# in GRiNS. This is an enumerated list of individual features only.
#
# These are enabled and disabled in <product>/features.py by including
# or not including them in the feature_set list.
#
# For large segments of code, it is much better to use an import statement
# where the PYTHONPATH is used to determine which file to import.
#
# To use them within the source code, test for their presence in the feature_set
# list.
# mjvdg 11-oct-2000

__version__ = "$Id$";

[
	EXPORT_SMIL1,			# not implemented
	EXPORT_SMIL2,
	EXPORT_REAL,
	EXPORT_QT,			# export to Quicktime-capable SMIL
	EXPORT_WMP,			# export to windows media player
	EXPORT_3GPP,			# export to 3GPP PSS4
	EXPORT_HTML_TIME,		# export to Internet Explorer HTML+TIME
	EXPORT_WINCE,			# export to Handheld Device

	# If these do not appear in feature_set, they don't apper in GRiNS.
	PREFERENCES,			# enable editing of GRiNS Preferences
	STRUCTURE_VIEW,
	PLAYER_VIEW,
	TRANSITION_VIEW,
	LAYOUT_VIEW,
	HYPERLINKS_VIEW,
	ASSETS_VIEW,
	SOURCE_VIEW,			# show the source view for editing smil source.
	SOURCE_VIEW_EDIT,		# allow editing of the source in the source view
	USER_GROUPS,
	ERRORS_VIEW,

	UNIFIED_FOCUS,			# All views share their focus
	CUSTOM_REGIONS,			# Allow to create/delete its own region
	MULTIPLE_TOPLAYOUT,		# Allow multiple toplayout

	CREATE_TEMPLATES,		# Enable template creation features
	ADVANCED_PROPERTIES,		# Enable advanced property editing

	ANIMATE,			# enable insertion of animate object
	SEPARATE_ANIMATE_NODE,		# show separate animate nodes
	EDIT_REALPIX,			# enable editing of RealPix media (XXX probably non-functional)
	CONVERT2REALPIX,		# conversion to RealPix

	ALIGNTOOL,			# enable align tools

	EDIT_TYPE,			# allow editing of node type
	EDIT_BASE,			# allow editing of base attribute

	# Different capabilities within the hierarchy view
	H_TRANSITIONS,
	H_MODIFY_STRUCTURE,		# This is the biggy - decides between templates or not.
	H_DROPBOX,			# Show an empty drop box at the end of a sequence.
	H_TIMESTRIP,			# Show snap!-like documents with correct toplevel par/seq
	H_PLAYABLE,			# Toggle showing of playability of nodes
	H_THUMBNAILS,			# Toggle showing of image thumbnails
	SHOW_MEDIA_CHILDREN,

	AUTO_EVALUATE,			# Don't need trial license to evaluate

	INTERNAL_LINKS,			# allow creation of internal hyperlinks
	UNSUPPORTED_ERROR,		# unsupported features cause fatal errors
] = range(41)				# don't forget to update this range!
