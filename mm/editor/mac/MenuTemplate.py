#
# Command/menu mapping for the mac, editor version
#

from usercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE, SPECIAL] = range(6)

# Some commands are optional, depending on preference settings:
ALL=''
CMIF='cmif'
DEBUG='debug'
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
		(ALL, DYNAMICCASCADE, 'Open recent', OPEN_RECENT),
		(ALL, ENTRY, 'Close window', 'W', CLOSE_WINDOW),
		(ALL, ENTRY, 'Close document', None, CLOSE),
		(ALL, SEP,),
		(ALL, ENTRY, 'Save', 'S', SAVE),
		(ALL, ENTRY, 'Save as...', None, SAVE_AS),
		(ALL, ENTRY, 'Export SMIL...', None, EXPORT_SMIL),
		(ALL, ENTRY, 'Restore', None, RESTORE),
		(ALL, SEP,),
		(ALL, ENTRY, 'Preferences...', None, PREFERENCES),
		(ALL, ENTRY, 'Document properties...', None, PROPERTIES),
		(ALL, SEP,),
		(DEBUG, CASCADE, 'Debug', (
			(ALL, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(ALL, TOGGLE, ('Enable call tracing','Disable call tracing'), None, TRACE),
			(ALL, ENTRY, 'Enter debugger', None, DEBUG),
			(ALL, ENTRY, 'Abort', None, CRASH),
			(ALL, ENTRY, 'Show log/debug window', None, CONSOLE))),
		(DEBUG, SEP,),
		(ALL, ENTRY, 'Quit', 'Q', EXIT))),

	(ALL, CASCADE, 'Edit', (
		(ALL, ENTRY, 'Undo', 'Z', UNDO),
		(ALL, SEP,),
		(ALL, ENTRY, 'Cut', 'X', CUT),
		(ALL, ENTRY, 'Copy', 'C', COPY),
		(ALL, ENTRY, 'Paste', 'V', PASTE),
		(ALL, CASCADE, 'Paste node', (
			(ALL, ENTRY, 'Before', None, PASTE_BEFORE),
			(ALL, ENTRY, 'Within', None, PASTE_UNDER))),
		(ALL, ENTRY, 'Delete', None, DELETE),
		(ALL, SEP,),
		(ALL, CASCADE, 'New node', (
			(ALL, ENTRY, 'Before', None, NEW_BEFORE),
			(ALL, ENTRY, 'After', 'K', NEW_AFTER),
			(ALL, ENTRY, 'Within', 'D', NEW_UNDER),
			(ALL, ENTRY, 'Par parent', None, NEW_PAR),
			(ALL, ENTRY, 'Seq parent', None, NEW_SEQ),
			(ALL, ENTRY, 'Switch parent', None, NEW_ALT),
			(CMIF, ENTRY, 'Choice parent', None, NEW_CHOICE))),
		(ALL, ENTRY, 'New channel', 'M', NEW_CHANNEL),
		(ALL, ENTRY, 'New screen', None, NEW_LAYOUT),
		(ALL, SEP,),
		(ALL, ENTRY, 'Move channel', None, MOVE_CHANNEL),
		(ALL, ENTRY, 'Copy channel', None, COPY_CHANNEL),
		(CMIF, ENTRY, 'Toggle channel state', None, TOGGLE_ONOFF))),

		
	(ALL, CASCADE, 'Play', (
		(ALL, ENTRY, 'Play document', 'P', PLAY),
		(ALL, ENTRY, 'Pause', None, PAUSE),
		(ALL, ENTRY, 'Stop', None, STOP),
		(ALL, SEP,),
		(ALL, ENTRY, 'Play node', None, PLAYNODE),
		(ALL, ENTRY, 'Play from node', None, PLAYFROM),
		(CMIF, SEP,),
		(CMIF, DYNAMICCASCADE, 'User groups', USERGROUPS),
		(CMIF, DYNAMICCASCADE, 'Channel visibility', CHANNELS))),

	(ALL, CASCADE, 'Tools', (
		(ALL, ENTRY, 'Info...', 'I', INFO),
		(ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ALL, ENTRY, 'Anchors...', 'T', ANCHORS),
		(ALL, ENTRY, 'Edit content', 'E', CONTENT),
		(ALL, SEP,),
		(ALL, ENTRY, 'Create simple anchor', 'R', CREATEANCHOR),
		(ALL, ENTRY, 'Finish hyperlink to focus', 'H', FINISH_LINK),
		(ALL, ENTRY, 'Create syncarc from focus...', None, FINISH_ARC))),
		
	(ALL, CASCADE, 'Navigate', (
		(ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
		(ALL, ENTRY, 'Expand recursively', None, EXPANDALL),
		(ALL, ENTRY, 'Collapse recursively', None, COLLAPSEALL),
		(ALL, SEP,),
		(ALL, ENTRY, 'Zoom in', None, CANVAS_WIDTH),
		(ALL, ENTRY, 'Show whole timeline', None, CANVAS_RESET),
		(ALL, SEP,),
		(ALL, ENTRY, 'Send focus to other views', 'F', PUSHFOCUS),
		(ALL, DYNAMICCASCADE, 'Select syncarc', SYNCARCS),
		(ALL, SEP,),
		(ALL, TOGGLE, 'Display unused channels', None, TOGGLE_UNUSED),
		(ALL, TOGGLE, 'Display sync arcs', None, TOGGLE_ARCS),
		(ALL, TOGGLE, 'Display image thumbnails', None, THUMBNAIL),
		(ALL, TOGGLE, 'Display bandwidth usage', None, TOGGLE_BWSTRIP),
		(CMIF, SEP,),
		(CMIF, TOGGLE, 'Timeline view follows player', None, SYNCCV),
		(CMIF, CASCADE, 'Minidoc navigation', (
			(CMIF, ENTRY, 'Next', None, NEXT_MINIDOC),
			(CMIF, ENTRY, 'Previous', None, PREV_MINIDOC),
			(CMIF, DYNAMICCASCADE, 'Ancestors', ANCESTORS),
			(CMIF, DYNAMICCASCADE, 'Descendants', DESCENDANTS),
			(CMIF, DYNAMICCASCADE, 'Siblings', SIBLINGS))),
		)),
		
	(ALL, CASCADE, 'Views', (
		(ALL, TOGGLE, ('Show Player', 'Hide Player'), '5', PLAYERVIEW),
		(ALL, SEP,),
		(ALL, TOGGLE, ('Show Structure view', 'Hide Structure view'), '6', HIERARCHYVIEW),
		(ALL, TOGGLE, ('Show Timeline view', 'Hide Timeline view'), '7', CHANNELVIEW),
		(ALL, TOGGLE, ('Show Layout view', 'Hide Layout view'), '8', LAYOUTVIEW),
		(ALL, SEP,),
		(ALL, TOGGLE, ('Show Hyperlinks', 'Hide Hyperlink view'), '9', LINKVIEW),
		(ALL, TOGGLE, ('Show User groups', 'Hide User group view'), '0', USERGROUPVIEW),
		(ALL, SEP,),
		(ALL, ENTRY, 'View source', None, SOURCE),
		(ALL, ENTRY, 'View help window', '?', HELP),
		(ALL, SEP,),
		(ALL, SPECIAL, 'Open windows', 'windows'),
		(ALL, SPECIAL, 'Open documents', 'documents'),
		)),
)

#
# Popup menus for various states
#
POPUP_HVIEW_LEAF = (
		(ENTRY, 'New node Before', None, NEW_BEFORE),
		(ENTRY, 'New node After', 'K', NEW_AFTER),
		(SEP,),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Paste Before', None, PASTE_BEFORE),
		(ENTRY, 'Paste After', None, PASTE_AFTER),
		(SEP,),
		(ENTRY, 'Play node', None, PLAYNODE),
		(ENTRY, 'Play from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Create simple anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish hyperlink', None, FINISH_LINK),
		(SEP,),
		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit content', 'E', CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		(ENTRY, 'New node Before', None, NEW_BEFORE),
		(ENTRY, 'New node After', 'K', NEW_AFTER),
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
		(ENTRY, 'Play node', None, PLAYNODE),
		(ENTRY, 'Play from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Expand/Collapse', None, EXPAND),
		(ENTRY, 'Expand recursively', None, EXPANDALL),
		(ENTRY, 'Collapse recursively', None, COLLAPSEALL),
		(SEP,),
		(ENTRY, 'Create simple anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish hyperlink', None, FINISH_LINK),
		(SEP,),
		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
)

POPUP_CVIEW_NONE = (
		(ENTRY, 'Create new channel', 'M', NEW_CHANNEL),
)

POPUP_CVIEW_CHANNEL = (
		(ENTRY, 'Toggle channel state', None, TOGGLE_ONOFF),
		(ENTRY, 'Properties...', None, ATTRIBUTES),
		(SEP,),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Move channel', None, MOVE_CHANNEL),
		(ENTRY, 'Copy channel', None, COPY_CHANNEL),

)

POPUP_CVIEW_NODE = (
		(ENTRY, 'Play node', None, PLAYNODE),
		(ENTRY, 'Play from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Create simple anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish hyperlink to focus', 'H', FINISH_LINK),
		(ENTRY, 'Create syncarc from focus...', None, FINISH_ARC),
		(SEP,),
		(ENTRY, 'Info...', 'I', INFO),
		(ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit content', 'E', CONTENT),
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

