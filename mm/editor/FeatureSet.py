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
    EXPORT_CMIF, 
    EXPORT_SMIL1,
    EXPORT_SMIL2,
    EXPORT_QT,                           # export to Quicktime-capable SMIL
    EXPORT_WMP,                        # export to windows media player

    # If these do not appear in feature_set, they don't apper in GRiNS.
    PLAYER_VIEW,
    STRUCTURE_VIEW,
    TIMELINE_VIEW,
    LAYOUT_VIEW,
    HYPERLINKS_VIEW,
    USER_GROUPS,
    TRANSITIONS,
    SOURCE,
    
    UNIFIED_FOCUS,						# All views share their focus

    # Different capabilities within the hierarchy view
    H_TRANSITIONS,
    H_BANDWIDTH,                       # Shows whether a node will complete downloading in time.
    H_VBANDWIDTH,                      # Shows the download time, variable.
    H_MODIFY_STRUCTURE,                # This is the biggy - decides between templates or not.
    H_DROPBOX,                          # Show an empty drop box at the end of a sequence.

] = range(19)                           # don't forget to update the range!
