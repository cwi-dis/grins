#
# Command/menu mapping for the mac, editor version
#

from usercmd import *
from Menus import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE, SPECIAL] = range(6)

# Some commands are optional, depending on preference settings:
ALL=''			# Available in all versions
FULL='full'		# available only if setting(lightweight) zero
CMIF='cmif'		# available only if setting(cmif) nonzero
DBG='debug'		# available only if setting(debug) nonzero
#
# commands we know are not useable on the Mac:
UNUSED_COMMANDS=(
	MAGIC_PLAY,
)

#
# Menu structure
#

MENUBAR=(
	(ALL, CASCADE, 'File', (
		(ALL, ENTRY, 'New', 'N', NEW_DOCUMENT),
		(ALL, ENTRY, 'Open...', 'O', OPENFILE),
		(ALL, ENTRY, 'Open URL...', 'L', OPEN),
		(ALL, DYNAMICCASCADE, 'Open Recent', OPEN_RECENT),
		(ALL, ENTRY, 'Close Document', (kMenuOptionModifier, 'W'), CLOSE),
		(ALL, SEP,),
		(ALL, ENTRY, 'Save', 'S', SAVE),
		(ALL, ENTRY, 'Save As...', (kMenuOptionModifier, 'S'), SAVE_AS),
		(ALL, ENTRY, 'Publish RealSystem G2...', None, EXPORT_SMIL),
		(ALL, ENTRY, 'Upload RealSystem G2...', None, UPLOAD_SMIL),
		(ALL, ENTRY, 'Revert to saved', None, RESTORE),
		(ALL, SEP,),
		(ALL, ENTRY, 'Document Properties...', (kMenuOptionModifier, 'A'), PROPERTIES),
		(ALL, SEP,),
		(DBG, CASCADE, 'Debug', (
			(ALL, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(ALL, TOGGLE, ('Enable call tracing','Disable call tracing'), None, TRACE),
			(ALL, ENTRY, 'Enter debugger', None, DEBUG),
			(ALL, ENTRY, 'Abort', None, CRASH),
			(ALL, ENTRY, 'Show log/debug window', None, CONSOLE),
			)),
		(DBG, SEP,),
		(ALL, ENTRY, 'Quit', 'Q', EXIT),
		)),

	(ALL, CASCADE, 'Edit', (
		(ALL, ENTRY, 'Undo', 'Z', UNDO),
		(ALL, SEP,),
		(ALL, ENTRY, 'Cut', 'X', CUT),
		(ALL, ENTRY, 'Copy', 'C', COPY),
		(ALL, ENTRY, 'Paste', 'V', PASTE),
		(ALL, CASCADE, 'Paste Special', (
			(ALL, ENTRY, 'Before', (kMenuOptionModifier, 'V'), PASTE_BEFORE),
			(ALL, ENTRY, 'Within', None, PASTE_UNDER),
			)),
		(ALL, ENTRY, 'Delete', (kMenuNoCommandModifier, '\177', 0x0a), DELETE),
		(ALL, SEP,),
		(FULL, ENTRY, 'New node...', 'K', NEW_AFTER),
		(FULL, ENTRY, 'New Channel', 'M', NEW_CHANNEL),
		(FULL, ENTRY, 'New Screen', None, NEW_LAYOUT),
		(FULL, SEP,),
		(FULL, ENTRY, 'Move Channel', None, MOVE_CHANNEL),
		(FULL, ENTRY, 'Copy Channel', None, COPY_CHANNEL),
		(CMIF, ENTRY, 'Toggle Channel State', None, TOGGLE_ONOFF),
		(FULL, SEP, ),
		(ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ALL, ENTRY, 'Edit Content', 'E', CONTENT),
		(ALL, SEP, ),
		(ALL, ENTRY, 'Preferences...', None, PREFERENCES),
		)),

	(ALL, CASCADE, 'Insert', (
		(ALL, CASCADE, 'Image node', (
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
			(ALL, ENTRY, 'After', None, NEW_AFTER_IMAGE),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_IMAGE),
		)),
		(ALL, CASCADE, 'Slideshow node', (
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
			(ALL, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_SLIDESHOW),
		)),
		(ALL, CASCADE, 'Text node', (
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
			(ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_TEXT),
		)),
		(ALL, CASCADE, 'Sound node', (
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_SOUND),
			(ALL, ENTRY, 'After', None, NEW_AFTER_SOUND),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_SOUND),
		)),
		(ALL, CASCADE, 'Video node', (
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_VIDEO),
			(ALL, ENTRY, 'After', None, NEW_AFTER_VIDEO),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_VIDEO),
		)),
		(ALL, CASCADE, 'Parallel node', (
			(ALL, ENTRY, 'Parent', None, NEW_PAR),
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_PAR),
			(ALL, ENTRY, 'After', None, NEW_AFTER_PAR),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_PAR),
		)),
		(ALL, CASCADE, 'Sequential node', (
			(ALL, ENTRY, 'Parent', None, NEW_SEQ),
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_SEQ),
			(ALL, ENTRY, 'After', None, NEW_AFTER_SEQ),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_SEQ),
		)),
		(ALL, CASCADE, 'Switch node', (
			(ALL, ENTRY, 'Parent', None, NEW_ALT),
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_ALT),
			(ALL, ENTRY, 'After', None, NEW_AFTER_ALT),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_ALT),
		)),
		(CMIF, CASCADE, 'Choice node', (
			(ALL, ENTRY, 'Parent', None, NEW_CHOICE),
			(ALL, ENTRY, 'Before', None, NEW_BEFORE_CHOICE),
			(ALL, ENTRY, 'After', None, NEW_AFTER_CHOICE),
			(ALL, ENTRY, 'Within', None, NEW_UNDER_CHOICE),
		)),
		(FULL, ENTRY, 'Before...', None, NEW_BEFORE),
		(FULL, ENTRY, 'Within...', 'D', NEW_UNDER),
		)),

	(ALL, CASCADE, 'Play', (
		(ALL, ENTRY, 'Play', 'P', PLAY),
		(ALL, ENTRY, 'Pause', None, PAUSE),
		(ALL, ENTRY, 'Stop', None, STOP),
		(ALL, SEP,),
		(ALL, ENTRY, 'Play Node', None, PLAYNODE),
		(ALL, ENTRY, 'Play from Node', None, PLAYFROM),
		(CMIF, SEP,),
		(CMIF, DYNAMICCASCADE, 'User Groups', USERGROUPS),
		(CMIF, DYNAMICCASCADE, 'Channel Visibility', CHANNELS),
		)),

	(ALL, CASCADE, 'Linking', (
		(ALL, ENTRY, 'Create Simple Anchor', 'R', CREATEANCHOR),
		(ALL, ENTRY, 'Finish Hyperlink to Selection', 'H', FINISH_LINK),
		(FULL, ENTRY, 'Anchors...', 'T', ANCHORS),
		(FULL, SEP,),
		(FULL, ENTRY, 'Create Syncarc from Selection...', None, FINISH_ARC),
		(FULL, DYNAMICCASCADE, 'Select Sync Arc', SYNCARCS),
		)),

	(ALL, CASCADE, 'View', (
		(ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
		(ALL, ENTRY, 'Expand All', None, EXPANDALL),
		(ALL, ENTRY, 'Collapse All', None, COLLAPSEALL),
		(ALL, SEP,),
		(FULL, ENTRY, 'Zoom In', None, CANVAS_WIDTH),
		(FULL, ENTRY, 'Fit in Window', None, CANVAS_RESET),
		(FULL, SEP,),
		(FULL, ENTRY, 'Synchronize Selection', 'F', PUSHFOCUS),
		(FULL, SEP,),
		(FULL, TOGGLE, 'Unused Channels', None, TOGGLE_UNUSED),
		(FULL, TOGGLE, 'Sync Arcs', None, TOGGLE_ARCS),
		(FULL, TOGGLE, 'Image Thumbnails', None, THUMBNAIL),
		(FULL, TOGGLE, 'Bandwidth Usage Strip', None, TOGGLE_BWSTRIP),
		(ALL, TOGGLE, 'Check Bandwidth', None, COMPUTE_BANDWIDTH),
		(FULL, TOGGLE, 'Show Playable', None, PLAYABLE),
		(FULL, TOGGLE, 'Show Durations', None, TIMESCALE),
		(CMIF, SEP,),
		(CMIF, TOGGLE, 'Timeline view follows player', None, SYNCCV),
		(CMIF, CASCADE, 'Minidoc navigation', (
			(CMIF, ENTRY, 'Next', None, NEXT_MINIDOC),
			(CMIF, ENTRY, 'Previous', None, PREV_MINIDOC),
			(CMIF, DYNAMICCASCADE, 'Ancestors', ANCESTORS),
			(CMIF, DYNAMICCASCADE, 'Descendants', DESCENDANTS),
			(CMIF, DYNAMICCASCADE, 'Siblings', SIBLINGS),
			)),
		)),

	(ALL, CASCADE, 'Windows', (
		(ALL, ENTRY, 'Close Window', 'W', CLOSE_WINDOW),
		(ALL, SEP,),
		(ALL, ENTRY, 'Player', '5', PLAYERVIEW),
		(ALL, ENTRY, 'Structure View', '6', HIERARCHYVIEW),
		(FULL, ENTRY, 'Timeline View', '7', CHANNELVIEW),
		(FULL, ENTRY, 'Layout View', '8', LAYOUTVIEW),
		(FULL, ENTRY, 'Hyperlinks', '9', LINKVIEW),
		(CMIF, ENTRY, 'User Groups', '0', USERGROUPVIEW),
		(ALL, SEP,),
		(ALL, ENTRY, 'Source', None, SOURCE),
		(ALL, ENTRY, 'View Help Window', None, HELP),
		(ALL, SEP,),
		(ALL, SPECIAL, 'Open Windows', 'windows'),
		(ALL, SPECIAL, 'Open Documents', 'documents'),
		)),
)

#
# Popup menus for various states
#
POPUP_HVIEW_LEAF = (
		(ENTRY, 'New Node Before', None, NEW_BEFORE),
		(ENTRY, 'New Node After', 'K', NEW_AFTER),
		(SEP,),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Paste Before', None, PASTE_BEFORE),
		(ENTRY, 'Paste After', None, PASTE_AFTER),
		(SEP,),
		(ENTRY, 'Play Node', None, PLAYNODE),
		(ENTRY, 'Play from Node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Create Simple Anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish hyperlink', None, FINISH_LINK),
		(SEP,),
##		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit Content', 'E', CONTENT),
)

POPUP_HVIEW_SLIDE = (
		(ENTRY, 'New Node Before', None, NEW_BEFORE_IMAGE),
		(ENTRY, 'New Node After', 'K', NEW_AFTER_IMAGE),
		(SEP,),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Paste Before', None, PASTE_BEFORE),
		(ENTRY, 'Paste After', None, PASTE_AFTER),
		(SEP,),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Edit Content', 'E', CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		(ENTRY, 'New Node Before', None, NEW_BEFORE),
		(ENTRY, 'New Node After', 'K', NEW_AFTER),
		(ENTRY, 'New Within', 'D', NEW_UNDER),
		(SEP,),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Paste Before', None, PASTE_BEFORE),
		(ENTRY, 'Paste After', None, PASTE_AFTER),
		(ENTRY, 'Paste Within', None, PASTE_UNDER),
		(SEP,),
		(ENTRY, 'Play Node', None, PLAYNODE),
		(ENTRY, 'Play from Node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Expand/Collapse', None, EXPAND),
		(ENTRY, 'Expand All', None, EXPANDALL),
		(ENTRY, 'Collapse All', None, COLLAPSEALL),
		(SEP,),
		(ENTRY, 'Create Simple Anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish Hyperlink', None, FINISH_LINK),
		(SEP,),
##		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
)

POPUP_CVIEW_NONE = (
		(ENTRY, 'New Channel...', 'M', NEW_CHANNEL),
)

POPUP_CVIEW_CHANNEL = (
		(ENTRY, 'Properties...', None, ATTRIBUTES),
		(SEP,),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Move Channel', None, MOVE_CHANNEL),
		(ENTRY, 'Copy Channel', None, COPY_CHANNEL),

)

POPUP_CVIEW_NODE = (
		(ENTRY, 'Play Node', None, PLAYNODE),
		(ENTRY, 'Play from Node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Create Simple Anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish Hyperlink to Selection', 'H', FINISH_LINK),
		(ENTRY, 'Create Sync Arc from Selection...', None, FINISH_ARC),
		(SEP,),
##		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit Content', 'E', CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		(ENTRY, 'Properties...', 'P', ATTRIBUTES),
		(SEP,),
		(ENTRY, 'Delete', None, DELETE),
)

POPUP_CVIEW_BWSTRIP = (
		(ENTRY, "14k4", None, BANDWIDTH_14K4),
		(ENTRY, "28k8", None, BANDWIDTH_28K8),
		(ENTRY, "ISDN", None, BANDWIDTH_ISDN),
		(ENTRY, "T1 (1 Mbps)", None, BANDWIDTH_T1),
		(ENTRY, "LAN (10 Mbps)", None, BANDWIDTH_LAN),
		(SEP,),
		(ENTRY, "Other...", None, BANDWIDTH_OTHER),
		)

#
# Adornments
#
PLAYER_ADORNMENTS = {
	'toolbar': (
		(TOGGLE, 1000, STOP),
		(TOGGLE, 1500, PLAY),
		(TOGGLE, 2000, PAUSE),
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
TOOLBAR=(2500, 62, 22)
