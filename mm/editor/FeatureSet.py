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

#DEFINE... :-)
EXPORT_CMIF = 0;
EXPORT_SMIL1 = 1;
EXPORT_SMIL2 = 2;
EXPORT_QT = 3;                          # export to Quicktime-capable SMIL
EXPORT_WMP = 4;                         # export to windows media player

# If these do not appear in feature_set, they don't apper in GRiNS.
PLAYER_VIEW = 16;
STRUCTURE_VIEW = 17;
TIMELINE_VIEW = 18;
LAYOUT_VIEW = 19;
HYPERLINKS_VIEW = 20;
USER_GROUPS = 21;
TRANSITIONS = 22;
SOURCE = 23;

# Different capabilities within the hierarchy view
H_NIPPLES = 32;
H_BANDWIDTH = 33;                       # Shows whether a node will complete downloading in time.
H_VBANDWIDTH = 34;                      # Shows the download time, variable.


# TODO: add more as needed. Remember to space the enum numbers nicely.
