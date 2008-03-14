__version__ = "$Id$"

#
# Command/menu mapping for the mac, editor version
#

from usercmd import *
from Menus import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE, SPECIAL] = range(6)

from flags import *
#
# commands we know are not useable on the Mac:
UNUSED_COMMANDS=(
        MAGIC_PLAY,
)

#
# Menu structure
#

MENUBAR=(
        (FLAG_ALL, CASCADE, 'File', (
                (FLAG_ALL, ENTRY, 'New', 'N', NEW_DOCUMENT),
                (FLAG_ALL, ENTRY, 'Open...', 'O', OPENFILE),
                (FLAG_ALL, ENTRY, 'Open URL...', 'L', OPEN),
                (FLAG_ALL, DYNAMICCASCADE, 'Open Recent', OPEN_RECENT),
                (FLAG_ALL, ENTRY, 'Close Document', (kMenuOptionModifier, 'W'), CLOSE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Save', 'S', SAVE),
                (FLAG_ALL, ENTRY, 'Save As...', (kMenuOptionModifier, 'S'), SAVE_AS),
                (FLAG_ALL, ENTRY, 'Revert to saved', None, RESTORE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, CASCADE, 'Publish', (
                        (FLAG_QT, ENTRY, 'Publish for QuickTime...', None, EXPORT_QT),
                        (FLAG_QT, ENTRY, 'Publish for QuickTime and upload...', None, UPLOAD_QT),
                        (FLAG_G2|FLAG_PRO, ENTRY, 'Publish for G2...', None, EXPORT_G2),
                        (FLAG_G2|FLAG_PRO, ENTRY, 'Publish for G2 and Upload...', None, UPLOAD_G2),
                        (FLAG_PRO, ENTRY, 'Publish for WMP', None, EXPORT_WMP),
                        (FLAG_PRO, ENTRY, 'Publish for WMP and Upload', None, UPLOAD_WMP),
                        (FLAG_PRO, ENTRY, 'Publish for HTML+Time', None, EXPORT_HTML_TIME),
                        (FLAG_SMIL_1_0|FLAG_PRO, ENTRY, 'Publish SMIL...', None, EXPORT_SMIL),
                        (FLAG_SMIL_1_0|FLAG_PRO, ENTRY, 'Publish SMIL and Upload...', None, UPLOAD_SMIL),
                )),
                (FLAG_SMIL_1_0|FLAG_QT|FLAG_G2|FLAG_PRO, SEP,),
                (FLAG_ALL, ENTRY, 'Document Properties...', (kMenuOptionModifier, 'A'), PROPERTIES),
                (FLAG_DBG, SEP,),
                (FLAG_DBG, CASCADE, 'Debug', (
                        (FLAG_DBG, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
                        (FLAG_DBG, TOGGLE, ('Enable call tracing','Disable call tracing'), None, TRACE),
                        (FLAG_DBG, ENTRY, 'Enter debugger', None, DEBUG),
                        (FLAG_DBG, ENTRY, 'Abort', None, CRASH),
                        (FLAG_DBG, ENTRY, 'Show log/debug window', None, CONSOLE),
                        (FLAG_DBG, ENTRY, 'Dump Window Hierarchy', None, DUMPWINDOWS),
                        )),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Check for GRiNS update...', None, CHECKVERSION),
                (FLAG_ALL, ENTRY, 'Register GRiNS...', None, REGISTER),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Quit', 'Q', EXIT),
                )),

        (FLAG_ALL, CASCADE, 'Edit', (
                (FLAG_ALL, ENTRY, 'Undo', 'Z', UNDO),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
                (FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
                (FLAG_ALL, ENTRY, 'Copy Properties...', (kMenuShiftModifier, 'C'), COPYPROPERTIES),
                (FLAG_ALL, ENTRY, 'Paste', 'V', PASTE),
                (FLAG_ALL, CASCADE, 'Paste Special', (
                        (FLAG_ALL, ENTRY, 'Before', (kMenuOptionModifier, 'V'), PASTE_BEFORE),
                        (FLAG_ALL, ENTRY, 'Within', None, PASTE_UNDER),
                        )),
                (FLAG_ALL, ENTRY, 'Paste Properties', (kMenuShiftModifier, 'V'), PASTEPROPERTIES),
                (FLAG_ALL, ENTRY, 'Delete', (kMenuNoCommandModifier, '\177', 0x0a), DELETE),

                (FLAG_PRO, SEP, ),
                (FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
                (FLAG_ALL, ENTRY, 'Edit Content', 'E', CONTENT),
                )),

        (FLAG_ALL, CASCADE, 'Insert', (
                (FLAG_ALL, CASCADE, 'Media', (
                        (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_MEDIA),
                        (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_MEDIA),
                        (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_MEDIA),
                )),
                (FLAG_G2, CASCADE, 'Slideshow node', (
                        (FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
                        (FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
                        (FLAG_G2, ENTRY, 'Within', None, NEW_UNDER_SLIDESHOW),
                )),
                (FLAG_ALL, CASCADE, 'Immediate Text', (
                        (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
                        (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
                        (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_TEXT),
                )),
                (FLAG_ALL, CASCADE, 'Brush', (
                        (FLAG_BOSTON, ENTRY, 'Before', None, NEW_BEFORE_BRUSH),
                        (FLAG_BOSTON, ENTRY, 'After', None, NEW_AFTER_BRUSH),
                        (FLAG_BOSTON, ENTRY, 'Within', None, NEW_UNDER_BRUSH),
                )),
                (FLAG_ALL, CASCADE, 'Animate', (
                        (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ANIMATE),
                        (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ANIMATE),
                        (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ANIMATE),
                )),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, CASCADE, 'Parallel node', (
                        (FLAG_ALL, ENTRY, 'Parent', None, NEW_PAR),
                        (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PAR),
                        (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PAR),
                        (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_PAR),
                )),
                (FLAG_ALL, CASCADE, 'Sequential node', (
                        (FLAG_ALL, ENTRY, 'Parent', None, NEW_SEQ),
                        (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SEQ),
                        (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SEQ),
                        (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SEQ),
                )),
                (FLAG_ALL, CASCADE, 'Switch node', (
                        (FLAG_ALL, ENTRY, 'Parent', None, NEW_SWITCH),
                        (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SWITCH),
                        (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SWITCH),
                        (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SWITCH),
                )),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, CASCADE, 'Region', (
#                       (FLAG_PRO, ENTRY, 'New node...', 'K', NEW_AFTER),
                        (FLAG_ALL, ENTRY, 'Within', None, NEW_REGION),
                )),
                (FLAG_BOSTON, ENTRY, 'TopLayout', 'T', NEW_TOPLAYOUT),
                (FLAG_PRO, SEP,),
#               (FLAG_PRO, ENTRY, 'Move Region', None, MOVE_REGION),
#               (FLAG_PRO, ENTRY, 'Copy Region', None, COPY_REGION),
#               (FLAG_CMIF, ENTRY, 'Toggle Channel State', None, TOGGLE_ONOFF),
                (FLAG_PRO, ENTRY, 'Before...', None, NEW_BEFORE),
                (FLAG_PRO, ENTRY, 'Within...', 'D', NEW_UNDER),
                )),

        (FLAG_ALL, CASCADE, 'Preview', (
                (FLAG_ALL, ENTRY, 'Preview', 'P', PLAY),
                (FLAG_ALL, ENTRY, 'Pause', None, PAUSE),
                (FLAG_ALL, ENTRY, 'Stop', None, STOP),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Preview Node', None, PLAYNODE),
                (FLAG_ALL, ENTRY, 'Preview from Node', None, PLAYFROM),
                (FLAG_CMIF, SEP,),
                (FLAG_BOSTON, DYNAMICCASCADE, 'Custom Tests', USERGROUPS),
                (FLAG_ALL, ENTRY, 'System Properties...', None, PREFERENCES),
                (FLAG_CMIF, DYNAMICCASCADE, 'Visible Channels', CHANNELS),
                )),

        (FLAG_ALL, CASCADE, 'Linking', (
                (FLAG_ALL, ENTRY, 'Create Whole Node Anchor', 'R', CREATEANCHOR),
                (FLAG_ALL, ENTRY, 'Finish Hyperlink', 'H', FINISH_LINK),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Use as Event Source', None, CREATE_EVENT_SOURCE),
                (FLAG_ALL, ENTRY, 'Create Begin Event', None, CREATE_BEGIN_EVENT),
                (FLAG_ALL, ENTRY, 'Create End Event', None, CREATE_END_EVENT),
                )),

        (FLAG_ALL, CASCADE, 'Tools', (
#               (FLAG_PRO, TOGGLE, 'Bandwidth Usage Strip', None, TOGGLE_BWSTRIP),
                (FLAG_ALL, ENTRY, 'Check Bandwidth', None, COMPUTE_BANDWIDTH),
                (FLAG_ALL, SEP,),
                (FLAG_PRO, ENTRY, 'RealPix to SMIL 2.0', None, RPCONVERT),
                (FLAG_PRO, ENTRY, 'SMIL 2.0 to RealPix', None, CONVERTRP),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Select node from source', 'S', SELECTNODE_FROM_SOURCE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, CASCADE, 'Align', (
                        (FLAG_ALL, ENTRY, 'Left', 'L', ALIGN_LEFT),
                        (FLAG_ALL, ENTRY, 'Center', 'C', ALIGN_CENTER),
                        (FLAG_ALL, ENTRY, 'Right', 'R', ALIGN_RIGHT),
                        (FLAG_ALL, SEP,),
                        (FLAG_ALL, ENTRY, 'Top', 'T', ALIGN_TOP),
                        (FLAG_ALL, ENTRY, 'Middle', 'M', ALIGN_MIDDLE),
                        (FLAG_ALL, ENTRY, 'Bottom', 'B', ALIGN_BOTTOM),
                        )),
                (FLAG_ALL, CASCADE, 'Distribute', (
                        (FLAG_ALL, ENTRY, 'Horizontally', 'H', DISTRIBUTE_HORIZONTALLY),
                        (FLAG_ALL, ENTRY, 'Vertically', 'V', DISTRIBUTE_VERTICALLY),
                        )),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, '&Merge with parent', None, MERGE_PARENT),
                )),

        (FLAG_ALL, CASCADE, 'View', (
                (FLAG_ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
                (FLAG_ALL, ENTRY, 'Expand All', None, EXPANDALL),
                (FLAG_ALL, ENTRY, 'Collapse All', None, COLLAPSEALL),
                (FLAG_ALL, SEP,),
                (FLAG_PRO, ENTRY, 'Zoom in', None, ZOOMIN),
                (FLAG_PRO, ENTRY, 'Zoom out', None, ZOOMOUT),
                (FLAG_PRO, ENTRY, 'Fit in Window', None, ZOOMRESET),
                (FLAG_PRO, SEP,),
                (FLAG_PRO, TOGGLE, 'Unused Channels', None, TOGGLE_UNUSED),
#               (FLAG_PRO, TOGGLE, 'Sync Arcs', None, TOGGLE_ARCS),
                (FLAG_PRO, TOGGLE, 'Image Thumbnails', None, THUMBNAIL),
                (FLAG_PRO, TOGGLE, 'Show Playable', None, PLAYABLE),
                (FLAG_ALL, TOGGLE, 'Show Time in Structure', None, TIMESCALE),
                (FLAG_ALL, TOGGLE, 'Show Bandwidth Usage', None, TOGGLE_BWSTRIP),
##         (FLAG_ALL, CASCADE, 'Show Time in Structure', (
##             (FLAG_ALL, TOGGLE, 'Whole Document, Adaptive', None, TIMESCALE),
##             (FLAG_ALL, TOGGLE, 'Selection Only, Adaptive', None, LOCALTIMESCALE),
##             (FLAG_ALL, TOGGLE, 'Selection Only, Fixed', None, CORRECTLOCALTIMESCALE),
##             )),
##         (FLAG_CMIF, SEP,),
                )),

        (FLAG_ALL, CASCADE, 'Windows', (
                (FLAG_ALL, ENTRY, 'Close Window', 'W', CLOSE_WINDOW),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Previewer View', '5', PLAYERVIEW),
                (FLAG_ALL, ENTRY, 'Structure View', '6', HIERARCHYVIEW),
                (FLAG_PRO, ENTRY, 'Layout View', '8', LAYOUTVIEW),
                (FLAG_PRO, ENTRY, 'Hyperlinks', '9', LINKVIEW),
                (FLAG_BOSTON, ENTRY, 'Custom Tests', '0', USERGROUPVIEW),
                (FLAG_BOSTON, ENTRY, 'Transitions', None, TRANSITIONVIEW),
                (FLAG_BOSTON, ENTRY, 'Paramgroups', None, PARAMGROUPVIEW),
                (FLAG_ALL, ENTRY, 'Source View', None, SOURCEVIEW),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'View Help Window', None, HELP),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, SPECIAL, 'Open Windows', 'windows'),
                (FLAG_ALL, SPECIAL, 'Open Documents', 'documents'),
                )),
)

#
# Popup menus for various states
#
POPUP_HVIEW_LEAF = (
#               (FLAG_PRO, ENTRY, 'New Node Before', None, NEW_BEFORE),
#               (FLAG_PRO, ENTRY, 'New Node After', 'K', NEW_AFTER),
                (FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
                (FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
                (FLAG_ALL, ENTRY, 'Paste', None, PASTE_AFTER),
                (FLAG_ALL, ENTRY, 'Paste Before', None, PASTE_BEFORE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, CASCADE, 'Insert', (
                        (FLAG_ALL, CASCADE, 'Media', (
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_MEDIA),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_MEDIA),
                        )),
                        (FLAG_G2, CASCADE, 'Slideshow node', (
                                (FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
                                (FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
                        )),
                        (FLAG_ALL, CASCADE, 'Immediate Text', (
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
                        )),
                        (FLAG_ALL, CASCADE, 'Brush', (
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_BRUSH),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_BRUSH),
                        )),
                        (FLAG_ALL, CASCADE, 'Animate', (
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ANIMATE),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ANIMATE),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ANIMATE),
                                )),
                        (FLAG_ALL, SEP,),
                        (FLAG_ALL, CASCADE, 'Parallel node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_PAR),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PAR),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PAR),
                        )),
                        (FLAG_ALL, CASCADE, 'Sequential node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_SEQ),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SEQ),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SEQ),
                        )),
                        (FLAG_ALL, CASCADE, 'Switch node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_SWITCH),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SWITCH),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SWITCH),
                        )),
                        (FLAG_ALL, CASCADE, 'Excl node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_EXCL),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_EXCL),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_EXCL),
                        )),
                        (FLAG_ALL, CASCADE, 'Priority class node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_PRIO),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PRIO),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PRIO),
                        )),
                )),
                (FLAG_ALL, ENTRY, 'Delete', None, DELETE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Preview Node', None, PLAYNODE),
                (FLAG_ALL, ENTRY, 'Preview from Node', None, PLAYFROM),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Create Whole Node Anchor', None, CREATEANCHOR),
                (FLAG_ALL, ENTRY, 'Finish Hyperlink', None, FINISH_LINK),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Use as Event Source', None, CREATE_EVENT_SOURCE),
                (FLAG_ALL, ENTRY, 'Create Begin Event', None, CREATE_BEGIN_EVENT),
                (FLAG_ALL, ENTRY, 'Create End Event', None, CREATE_END_EVENT),
                (FLAG_ALL, SEP,),
                (FLAG_PRO, ENTRY, 'RealPix to SMIL 2.0', None, RPCONVERT),
                (FLAG_PRO, SEP,),
                (FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
##         (FLAG_PRO, ENTRY, 'Anchors...', 'T', ANCHORS),
                (FLAG_ALL, ENTRY, 'Edit Content', 'E', CONTENT),
)

POPUP_HVIEW_SLIDE = (
                (FLAG_G2, ENTRY, 'Cut', 'X', CUT),
                (FLAG_G2, ENTRY, 'Copy', 'C', COPY),
                (FLAG_G2, ENTRY, 'Paste', None, PASTE_AFTER),
                (FLAG_G2, ENTRY, 'Paste Before', None, PASTE_BEFORE),
                (FLAG_G2, SEP,),
                (FLAG_G2, ENTRY, 'Delete', None, DELETE),
                (FLAG_G2, CASCADE, 'Insert Image', (
                        (FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
                        (FLAG_G2, ENTRY, 'After', None, NEW_AFTER_IMAGE),
                )),
                (FLAG_G2, SEP,),
                (FLAG_G2, ENTRY, 'Properties...', 'A', ATTRIBUTES),
                (FLAG_G2, ENTRY, 'Edit Content', 'E', CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
#               (FLAG_PRO, ENTRY, 'New Node', 'K', NEW_AFTER),
#               (FLAG_PRO, ENTRY, 'New Node Before', None, NEW_BEFORE),
#               (FLAG_PRO, ENTRY, 'New Within', 'D', NEW_UNDER),
                (FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
                (FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
                (FLAG_ALL, ENTRY, 'Paste', None, PASTE_AFTER),
                (FLAG_ALL, ENTRY, 'Paste Before', None, PASTE_BEFORE),
                (FLAG_ALL, ENTRY, 'Paste Within', None, PASTE_UNDER),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, CASCADE, 'Insert', (
                        (FLAG_ALL, CASCADE, 'Media', (
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_MEDIA),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_MEDIA),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_MEDIA),
                        )),
                        (FLAG_G2, CASCADE, 'Slideshow node', (
                                (FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
                                (FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
                                (FLAG_G2, ENTRY, 'Within', None, NEW_UNDER_SLIDESHOW),
                        )),
                        (FLAG_ALL, CASCADE, 'Immediate Text', (
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_TEXT),
                        )),
                        (FLAG_ALL, CASCADE, 'Brush', (
                                (FLAG_BOSTON, ENTRY, 'Before', None, NEW_BEFORE_BRUSH),
                                (FLAG_BOSTON, ENTRY, 'After', None, NEW_AFTER_BRUSH),
                                (FLAG_BOSTON, ENTRY, 'Within', None, NEW_UNDER_BRUSH),
                        )),
                        (FLAG_ALL, CASCADE, 'Animate', (
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ANIMATE),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ANIMATE),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ANIMATE),
                                )),
                        (FLAG_ALL, SEP,),
                        (FLAG_ALL, CASCADE, 'Parallel node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_PAR),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PAR),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PAR),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_PAR),
                        )),
                        (FLAG_ALL, CASCADE, 'Sequential node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_SEQ),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SEQ),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SEQ),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SEQ),
                        )),
                        (FLAG_ALL, CASCADE, 'Switch node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_SWITCH),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SWITCH),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SWITCH),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SWITCH),
                        )),
                        (FLAG_ALL, CASCADE, 'Excl node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_EXCL),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_EXCL),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_EXCL),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_EXCL),
                        )),
                        (FLAG_ALL, CASCADE, 'Priority class node', (
                                (FLAG_ALL, ENTRY, 'Parent', None, NEW_PRIO),
                                (FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PRIO),
                                (FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PRIO),
                                (FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_PRIO),
                        )),
                )),
                (FLAG_ALL, ENTRY, 'Delete', None, DELETE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Preview Node', None, PLAYNODE),
                (FLAG_ALL, ENTRY, 'Preview from Node', None, PLAYFROM),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
                (FLAG_ALL, ENTRY, 'Expand All', None, EXPANDALL),
                (FLAG_ALL, ENTRY, 'Collapse All', None, COLLAPSEALL),
                (FLAG_ALL, SEP,),
##         (FLAG_ALL, ENTRY, 'Create Whole Node Anchor', None, CREATEANCHOR),
                (FLAG_ALL, ENTRY, 'Finish Hyperlink', None, FINISH_LINK),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Use as Event Source', None, CREATE_EVENT_SOURCE),
                (FLAG_ALL, ENTRY, 'Create Begin Event', None, CREATE_BEGIN_EVENT),
                (FLAG_ALL, ENTRY, 'Create End Event', None, CREATE_END_EVENT),
                (FLAG_PRO, SEP),
                (FLAG_PRO, ENTRY, 'SMIL 2.0 to RealPix', None, CONVERTRP),
                (FLAG_ALL, SEP,),
##         (FLAG_ALL, ENTRY, 'Info...', 'I', INFO),
                (FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
##         (FLAG_PRO, ENTRY, 'Anchors...', 'T', ANCHORS),
)

POPUP_HVIEW_TRANS = (
                (FLAG_ALL, DYNAMICCASCADE, 'Transition', TRANSITION),
                )

POPUP_MULTI = (
                (FLAG_ALL, ENTRY, 'Cut', None, CUT),
                (FLAG_ALL, ENTRY, 'Copy', None, COPY),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Delete', None, DELETE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Event Source', None, CREATE_EVENT_SOURCE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
)

POPUP_EVENT_DEST = (
        (FLAG_ALL, ENTRY, 'Find Event Source', None, FIND_EVENT_SOURCE),
#       (FLAG_ALL, ENTRY, 'Remove event', None, REMOVE_EVENT), # This points to many events..
        (FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
        )

POPUP_EVENT_SOURCE = (
        (FLAG_ALL, ENTRY, 'Find Event Destination', None, FIND_EVENT_SOURCE),
#       (FLAG_ALL, ENTRY, 'Remove event', None, CRASH),
#       (FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
        )


#
# Adornments
#
PLAYER_ADORNMENTS = {
        'toolbar': (
                (TOGGLE, 1001, STOP),
                (TOGGLE, 1501, PLAY),
                (TOGGLE, 2001, PAUSE),
                ),
        'shortcuts': {
                ' ': MAGIC_PLAY
        }
}
CHANNEL_ADORNMENTS = {
        'shortcuts': {
                ' ': MAGIC_PLAY
        }
}

#
# CNTL resource for the toolbar and its height
TOOLBAR=(None, 66, 24)
