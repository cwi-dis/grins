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
		(FLAG_QT, ENTRY, 'Publish for QuickTime...', None, EXPORT_QT),
		(FLAG_QT, ENTRY, 'Publish for QuickTime and upload...', None, UPLOAD_QT),
		(FLAG_G2|FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for G2...', None, EXPORT_G2),
		(FLAG_G2|FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for G2 and Upload...', None, UPLOAD_G2),
		(FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for WMP', None, EXPORT_WMP),
		(FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for WMP and Upload', None, UPLOAD_WMP),
		(FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for HTML+Time', None, EXPORT_HTML_TIME),
		(FLAG_SMIL_1_0|FLAG_PRO, ENTRY, 'Publish SMIL...', None, EXPORT_SMIL),
		(FLAG_SMIL_1_0|FLAG_PRO, ENTRY, 'Publish SMIL and Upload...', None, UPLOAD_SMIL),
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
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Quit', 'Q', EXIT),
		)),

	(FLAG_ALL, CASCADE, 'Edit', (
		(FLAG_ALL, ENTRY, 'Undo', 'Z', UNDO),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
		(FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
		(FLAG_ALL, ENTRY, 'Paste', 'V', PASTE),
		(FLAG_ALL, CASCADE, 'Paste Special', (
			(FLAG_ALL, ENTRY, 'Before', (kMenuOptionModifier, 'V'), PASTE_BEFORE),
			(FLAG_ALL, ENTRY, 'Within', None, PASTE_UNDER),
			)),
		(FLAG_ALL, ENTRY, 'Delete', (kMenuNoCommandModifier, '\177', 0x0a), DELETE),
		(FLAG_ALL, SEP,),
		(FLAG_PRO, ENTRY, 'New node...', 'K', NEW_AFTER),
		(FLAG_PRO, ENTRY, 'New Channel', 'M', NEW_CHANNEL),
		(FLAG_PRO, ENTRY, 'New Screen', None, NEW_LAYOUT),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, 'Move Channel', None, MOVE_CHANNEL),
		(FLAG_PRO, ENTRY, 'Copy Channel', None, COPY_CHANNEL),
		(FLAG_CMIF, ENTRY, 'Toggle Channel State', None, TOGGLE_ONOFF),
		(FLAG_PRO, SEP, ),
		(FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(FLAG_ALL, ENTRY, 'Edit Content', 'E', CONTENT),
		(FLAG_PRO, ENTRY, 'Convert to SMIL 2.0', None, RPCONVERT),
		(FLAG_ALL, SEP, ),
		(FLAG_ALL, ENTRY, 'Preferences...', None, PREFERENCES),
		)),

	(FLAG_ALL, CASCADE, 'Insert', (
		(FLAG_ALL, CASCADE, 'Image node', (
			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_IMAGE),
			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_IMAGE),
		)),
		(FLAG_G2, CASCADE, 'Slideshow node', (
			(FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
			(FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
			(FLAG_G2, ENTRY, 'Within', None, NEW_UNDER_SLIDESHOW),
		)),
		(FLAG_ALL, CASCADE, 'Text node', (
			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_TEXT),
		)),
		(FLAG_SMIL_1_0, CASCADE, 'HTML node', (
			(FLAG_SMIL_1_0, ENTRY, 'Before', None, NEW_BEFORE_HTML),
			(FLAG_SMIL_1_0, ENTRY, 'After', None, NEW_AFTER_HTML),
			(FLAG_SMIL_1_0, ENTRY, 'Within', None, NEW_UNDER_HTML),
			)),
		(FLAG_ALL, CASCADE, 'Sound node', (
			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SOUND),
			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SOUND),
			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SOUND),
		)),
		(FLAG_ALL, CASCADE, 'Video node', (
			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_VIDEO),
			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_VIDEO),
			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_VIDEO),
		)),
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
			(FLAG_ALL, ENTRY, 'Parent', None, NEW_ALT),
			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ALT),
			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ALT),
			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ALT),
		)),
		(FLAG_CMIF, CASCADE, 'Choice node', (
			(FLAG_ALL, ENTRY, 'Parent', None, NEW_CHOICE),
			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_CHOICE),
			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_CHOICE),
			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_CHOICE),
		)),
		(FLAG_PRO, ENTRY, 'Before...', None, NEW_BEFORE),
		(FLAG_PRO, ENTRY, 'Within...', 'D', NEW_UNDER),
		)),

	(FLAG_ALL, CASCADE, 'Play', (
		(FLAG_ALL, ENTRY, 'Play', 'P', PLAY),
		(FLAG_ALL, ENTRY, 'Pause', None, PAUSE),
		(FLAG_ALL, ENTRY, 'Stop', None, STOP),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Play Node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from Node', None, PLAYFROM),
		(FLAG_CMIF, SEP,),
		(FLAG_BOSTON|FLAG_SNAP, DYNAMICCASCADE, 'Custom Tests', USERGROUPS),
		(FLAG_CMIF, DYNAMICCASCADE, 'Visible Channels', CHANNELS),
		)),

	(FLAG_ALL, CASCADE, 'Linking', (
		(FLAG_ALL, ENTRY, 'Create Whole Node Anchor', 'R', CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish Hyperlink', 'H', FINISH_LINK),
##		(FLAG_PRO, ENTRY, 'Anchors...', 'T', ANCHORS),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, 'Create Syncarc from Selection...', None, FINISH_ARC),
		(FLAG_PRO, DYNAMICCASCADE, 'Select Sync Arc', SYNCARCS),
		)),

	(FLAG_ALL, CASCADE, 'View', (
		(FLAG_ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
		(FLAG_ALL, ENTRY, 'Expand All', None, EXPANDALL),
		(FLAG_ALL, ENTRY, 'Collapse All', None, COLLAPSEALL),
		(FLAG_ALL, SEP,),
		(FLAG_PRO, ENTRY, 'Zoom In', None, CANVAS_WIDTH),
		(FLAG_PRO, ENTRY, 'Fit in Window', None, CANVAS_RESET),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, 'Synchronize Selection', 'F', PUSHFOCUS),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, TOGGLE, 'Unused Channels', None, TOGGLE_UNUSED),
		(FLAG_PRO, TOGGLE, 'Sync Arcs', None, TOGGLE_ARCS),
		(FLAG_PRO, TOGGLE, 'Image Thumbnails', None, THUMBNAIL),
		(FLAG_PRO, TOGGLE, 'Bandwidth Usage Strip', None, TOGGLE_BWSTRIP),
		(FLAG_ALL, ENTRY, 'Check Bandwidth', None, COMPUTE_BANDWIDTH),
		(FLAG_PRO, TOGGLE, 'Show Playable', None, PLAYABLE),
		(FLAG_ALL, CASCADE, 'Show Time in Structure', (
			(FLAG_ALL, TOGGLE, 'Whole Document, Adaptive', None, TIMESCALE),
			(FLAG_ALL, TOGGLE, 'Selection Only, Adaptive', None, LOCALTIMESCALE),
			(FLAG_ALL, TOGGLE, 'Selection Only, Fixed', None, CORRECTLOCALTIMESCALE),
			)),
		(FLAG_CMIF, SEP,),
		(FLAG_CMIF, TOGGLE, 'Timeline view follows player', None, SYNCCV),
		(FLAG_CMIF, CASCADE, 'Minidoc navigation', (
			(FLAG_CMIF, ENTRY, 'Next', None, NEXT_MINIDOC),
			(FLAG_CMIF, ENTRY, 'Previous', None, PREV_MINIDOC),
			(FLAG_CMIF, DYNAMICCASCADE, 'Ancestors', ANCESTORS),
			(FLAG_CMIF, DYNAMICCASCADE, 'Descendants', DESCENDANTS),
			(FLAG_CMIF, DYNAMICCASCADE, 'Siblings', SIBLINGS),
			)),
		)),

	(FLAG_ALL, CASCADE, 'Windows', (
		(FLAG_ALL, ENTRY, 'Close Window', 'W', CLOSE_WINDOW),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Player', '5', PLAYERVIEW),
		(FLAG_ALL, ENTRY, 'Structure View', '6', HIERARCHYVIEW),
		(FLAG_PRO, ENTRY, 'Timeline View', '7', CHANNELVIEW),
		(FLAG_PRO, ENTRY, 'Layout View', '8', LAYOUTVIEW),
		(FLAG_PRO, ENTRY, 'Hyperlinks', '9', LINKVIEW),
		(FLAG_BOSTON, ENTRY, 'User Groups', '0', USERGROUPVIEW),
		(FLAG_BOSTON, ENTRY, 'Transitions', None, TRANSITIONVIEW),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Source', None, SOURCE),
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
		(FLAG_PRO, ENTRY, 'New Node Before', None, NEW_BEFORE),
		(FLAG_PRO, ENTRY, 'New Node After', 'K', NEW_AFTER),
		(FLAG_PRO, ENTRY, 'Convert to SMIL 2.0', None, RPCONVERT),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
		(FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
		(FLAG_ALL, ENTRY, 'Paste', None, PASTE_AFTER),
		(FLAG_ALL, ENTRY, 'Paste Before', None, PASTE_BEFORE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
		(FLAG_ALL, CASCADE, 'Insert', (
			(FLAG_ALL, CASCADE, 'Image node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_IMAGE),
			)),
			(FLAG_G2, CASCADE, 'Slideshow node', (
				(FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
				(FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
			)),
			(FLAG_ALL, CASCADE, 'Text node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
			)),
			(FLAG_SMIL_1_0, CASCADE, 'HTML node', (
				(FLAG_SMIL_1_0, ENTRY, 'Before', None, NEW_BEFORE_HTML),
				(FLAG_SMIL_1_0, ENTRY, 'After', None, NEW_AFTER_HTML),
				)),
			(FLAG_ALL, CASCADE, 'Sound node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SOUND),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SOUND),
			)),
			(FLAG_ALL, CASCADE, 'Video node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_VIDEO),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_VIDEO),
			)),
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
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_ALT),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ALT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ALT),
			)),
			(FLAG_CMIF, CASCADE, 'Choice node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_CHOICE),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_CHOICE),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_CHOICE),
			)),
		)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Play Node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from Node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Create Whole Node Anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish Hyperlink', None, FINISH_LINK),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
##		(FLAG_PRO, ENTRY, 'Anchors...', 'T', ANCHORS),
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
		(FLAG_PRO, ENTRY, 'New Node', 'K', NEW_AFTER),
		(FLAG_PRO, ENTRY, 'New Node Before', None, NEW_BEFORE),
		(FLAG_PRO, ENTRY, 'New Within', 'D', NEW_UNDER),
		(FLAG_PRO, SEP),
		(FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
		(FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
		(FLAG_ALL, ENTRY, 'Paste', None, PASTE_AFTER),
		(FLAG_ALL, ENTRY, 'Paste Before', None, PASTE_BEFORE),
		(FLAG_ALL, ENTRY, 'Paste Within', None, PASTE_UNDER),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
		(FLAG_ALL, CASCADE, 'Insert', (
			(FLAG_ALL, CASCADE, 'Image node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_IMAGE),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_IMAGE),
			)),
			(FLAG_G2, CASCADE, 'Slideshow node', (
				(FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
				(FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
				(FLAG_G2, ENTRY, 'Within', None, NEW_UNDER_SLIDESHOW),
			)),
			(FLAG_ALL, CASCADE, 'Text node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_TEXT),
			)),
			(FLAG_SMIL_1_0, CASCADE, 'HTML node', (
				(FLAG_SMIL_1_0, ENTRY, 'Before', None, NEW_BEFORE_HTML),
				(FLAG_SMIL_1_0, ENTRY, 'After', None, NEW_AFTER_HTML),
				(FLAG_SMIL_1_0, ENTRY, 'Within', None, NEW_UNDER_HTML),
				)),
			(FLAG_ALL, CASCADE, 'Sound node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SOUND),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SOUND),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SOUND),
			)),
			(FLAG_ALL, CASCADE, 'Video node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_VIDEO),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_VIDEO),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_VIDEO),
			)),
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
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_ALT),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ALT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ALT),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ALT),
			)),
			(FLAG_CMIF, CASCADE, 'Choice node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_CHOICE),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_CHOICE),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_CHOICE),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_CHOICE),
			)),
		)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Play Node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from Node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
		(FLAG_ALL, ENTRY, 'Expand All', None, EXPANDALL),
		(FLAG_ALL, ENTRY, 'Collapse All', None, COLLAPSEALL),
		(FLAG_ALL, SEP,),
##		(FLAG_ALL, ENTRY, 'Create Whole Node Anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish Hyperlink', None, FINISH_LINK),
		(FLAG_ALL, SEP,),
##		(FLAG_ALL, ENTRY, 'Info...', 'I', INFO),
		(FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
##		(FLAG_PRO, ENTRY, 'Anchors...', 'T', ANCHORS),
)

POPUP_CVIEW_NONE = (
		(FLAG_ALL, ENTRY, 'New Channel...', 'M', NEW_CHANNEL),
)

POPUP_CVIEW_BWSTRIP = (
		(FLAG_ALL, ENTRY, "14k4", None, BANDWIDTH_14K4),
		(FLAG_ALL, ENTRY, "28k8", None, BANDWIDTH_28K8),
		(FLAG_ALL, ENTRY, "ISDN", None, BANDWIDTH_ISDN),
		(FLAG_ALL, ENTRY, "T1 (1 Mbps)", None, BANDWIDTH_T1),
		(FLAG_ALL, ENTRY, "LAN (10 Mbps)", None, BANDWIDTH_LAN),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, "Other...", None, BANDWIDTH_OTHER),
		)

POPUP_CVIEW_CHANNEL = (
		(FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Move Channel', None, MOVE_CHANNEL),
		(FLAG_ALL, ENTRY, 'Copy Channel', None, COPY_CHANNEL),

)

POPUP_CVIEW_NODE = (
		(FLAG_ALL, ENTRY, 'Play Node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from Node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Create Whole Node Anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish Hyperlink to Selection', 'H', FINISH_LINK),
		(FLAG_ALL, ENTRY, 'Create Sync Arc from Selection...', None, FINISH_ARC),
		(FLAG_ALL, SEP,),
##		(FLAG_ALL, ENTRY, 'Info...', 'I', INFO),
		(FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
##		(FLAG_ALL, ENTRY, 'Anchors...', 'T', ANCHORS),
		(FLAG_ALL, ENTRY, 'Edit Content', 'E', CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		(FLAG_ALL, ENTRY, 'Properties...', 'P', ATTRIBUTES),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
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
