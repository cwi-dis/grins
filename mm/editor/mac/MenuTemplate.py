#
# Command/menu mapping for the mac, editor version
#

from usercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE, SPECIAL] = range(6)

# Some commands are optional, depending on preference settings:
ALL=''
CMIF='cmif'
DBG='debug'
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
		(ALL, ENTRY, 'Close Document', None, CLOSE),
		(ALL, SEP,),
		(ALL, ENTRY, 'Save', 'S', SAVE),
		(ALL, ENTRY, 'Save As...', None, SAVE_AS),
		(ALL, CASCADE, 'Export', (
			(ALL, ENTRY, 'RealSystem G2...', None, EXPORT_SMIL),
			)),
		(ALL, ENTRY, 'Restore', None, RESTORE),
		(ALL, SEP,),
		(ALL, ENTRY, 'Document Properties...', None, PROPERTIES),
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
			(ALL, ENTRY, 'Before', None, PASTE_BEFORE),
			(ALL, ENTRY, 'Within', None, PASTE_UNDER),
			)),
		(ALL, ENTRY, 'Delete', None, DELETE),
		(ALL, SEP,),
		(ALL, ENTRY, 'New node...', 'K', NEW_AFTER),
		(ALL, CASCADE, 'New node special', (
			(ALL, ENTRY, 'Before...', None, NEW_BEFORE),
			(ALL, ENTRY, 'Within...', 'D', NEW_UNDER),
			(ALL, ENTRY, 'Par Parent', None, NEW_PAR),
			(ALL, ENTRY, 'Seq Parent', None, NEW_SEQ),
			(ALL, ENTRY, 'Switch Parent', None, NEW_ALT),
			(CMIF, ENTRY, 'Choice Parent', None, NEW_CHOICE),
			)),
		(ALL, ENTRY, 'New Channel', 'M', NEW_CHANNEL),
		(ALL, ENTRY, 'New Screen', None, NEW_LAYOUT),
		(ALL, SEP,),
		(ALL, ENTRY, 'Move Channel', None, MOVE_CHANNEL),
		(ALL, ENTRY, 'Copy Channel', None, COPY_CHANNEL),
		(CMIF, ENTRY, 'Toggle Channel State', None, TOGGLE_ONOFF),
		(ALL, SEP, ),
		(ALL, ENTRY, 'Info...', 'I', INFO),
		(ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ALL, ENTRY, 'Edit Content', 'E', CONTENT),
##		(ALL, SEP, ),
##		(ALL, ENTRY, 'Edit Source...', None, EDITSOURCE),
		(ALL, SEP, ),
		(ALL, ENTRY, 'Preferences...', None, PREFERENCES),
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
		(ALL, ENTRY, 'Anchors...', 'T', ANCHORS),
		(ALL, SEP,),
		(ALL, ENTRY, 'Create Syncarc from Selection...', None, FINISH_ARC),
		(ALL, DYNAMICCASCADE, 'Select Sync Arc', SYNCARCS),
		)),

	(ALL, CASCADE, 'View', (
		(ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
		(ALL, ENTRY, 'Expand All', None, EXPANDALL),
		(ALL, ENTRY, 'Collapse All', None, COLLAPSEALL),
		(ALL, SEP,),
		(ALL, ENTRY, 'Zoom In', None, CANVAS_WIDTH),
		(ALL, ENTRY, 'Fit in Window', None, CANVAS_RESET),
		(ALL, SEP,),
		(ALL, ENTRY, 'Synchronize Selection', 'F', PUSHFOCUS),
		(ALL, SEP,),
		(ALL, TOGGLE, 'Unused Channels', None, TOGGLE_UNUSED),
		(ALL, TOGGLE, 'Sync Arcs', None, TOGGLE_ARCS),
		(ALL, TOGGLE, 'Image Thumbnails', None, THUMBNAIL),
		(ALL, TOGGLE, 'Bandwidth Usage', None, TOGGLE_BWSTRIP),
		(ALL, TOGGLE, 'Show Playable', None, PLAYABLE),
		(ALL, TOGGLE, 'Show Durations', None, TIMESCALE),
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
		(ALL, ENTRY, 'Timeline View', '7', CHANNELVIEW),
		(ALL, ENTRY, 'Layout View', '8', LAYOUTVIEW),
		(ALL, ENTRY, 'Hyperlinks', '9', LINKVIEW),
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
		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
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
		(ENTRY, 'Info...', 'I', INFO),
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
		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit Content', 'E', CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		(ENTRY, 'Info...', 'I', INFO),
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
