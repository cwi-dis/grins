__version__ = "$Id$"

#
# Command/menu mapping for the win32 GRiNS Editor
#
# (adapted from mac original)
#

""" @win32doc|MenuTemplate
Contains the specification for player menu in the
following Grammar:
# entry: <simple_entry> | <sep_entry> | <dyn_cascade_entry> | <CASCADE_ENTRY>
# simple_entry: (ENTRY | TOGGLE, LABEL, SHORTCUT, ID)
# sep_enty: (SEP,)
# dyn_cascade_entry: (DYNAMICCASCADE, LABEL, ID)
# cascade_entry: (CASCADE,LABEL,menu_spec_list)
# menubar_entry: (LABEL,menu_spec_list)
# menu_spec_list: list of entry
# menubar_spec_list: list of menubar_entry
# menu_exec_list: (MENU,menu_spec_list)
where ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE are type constants.
LABEL and and SHORTCUT are strings
ID is either an integer or an object that can be maped to an integer
"""


from usercmd import *

# plus wnds arrange cmds
from wndusercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)

# Some commands are optional, depending on preference settings:
from flags import *

MENUBAR=(
	('&File', (
		(LIGHT, ENTRY, '&New\tCtrl+N', 'N', NEW_DOCUMENT),
		(LIGHT, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(LIGHT, ENTRY, '&Open URL...\tCtrl+L', 'O', OPEN),
		(LIGHT, DYNAMICCASCADE, 'Open &recent', OPEN_RECENT),
		(LIGHT, ENTRY, '&Close', None, CLOSE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(LIGHT, ENTRY, 'Save &as...', None, SAVE_AS),
		(LIGHT, CASCADE, '&Export', (
			(LIGHT, ENTRY, '&RealSystem G2...', None, EXPORT_SMIL),
			)),
		(LIGHT, ENTRY, 'Revert &to saved', None, RESTORE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Document &Properties...', None, PROPERTIES),
		(LIGHT|DBG, SEP,),
		(LIGHT|DBG, CASCADE, 'Debug', (
			(LIGHT, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(LIGHT, TOGGLE, 'Enable call tracing', None, TRACE),
			(LIGHT, ENTRY, 'Enter debugger', None, DEBUG),
			(LIGHT, ENTRY, 'Abort', None, CRASH),
			(LIGHT, TOGGLE, 'Show log/debug window', None, CONSOLE),
			)),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'E&xit', None, EXIT),
		)),

	('&Edit', (
		(LIGHT, ENTRY, '&Undo\tCtrl+Z', 'Z', UNDO),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Cu&t\tCtrl+X', 'X', CUT),
		(LIGHT, ENTRY, '&Copy\tCtrl+C', 'C', COPY),
		(LIGHT, ENTRY, '&Paste\tCtrl+V', 'V', PASTE),
		(LIGHT, CASCADE, 'P&aste special', (
			(LIGHT, ENTRY, '&Before', None, PASTE_BEFORE),
##			(LIGHT, ENTRY, '&After', None, PASTE_AFTER),
			(LIGHT, ENTRY, '&Within', None, PASTE_UNDER),
			)),
		(LIGHT, ENTRY, '&Delete\tCtrl+Del', None, DELETE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&New node...', None, NEW_AFTER),
		(LIGHT, CASCADE, 'Ne&w node special', (
			(LIGHT, ENTRY, '&Before...', None, NEW_BEFORE),
			(LIGHT, ENTRY, '&Within...', None, NEW_UNDER),
			(LIGHT, ENTRY, '&Par parent', None, NEW_PAR),
			(LIGHT, ENTRY, '&Seq parent', None, NEW_SEQ),
			(LIGHT, ENTRY, 'Sw&itch parent', None, NEW_ALT),
			(CMIF, ENTRY, 'C&hoice parent', None, NEW_CHOICE),
			)),
		(SMIL, ENTRY, 'New &channel', None, NEW_CHANNEL),

## Windows dialogs apparently don't use usercmd commands.
##		(SMIL, ENTRY, 'New &layout', None, NEW_LAYOUT),
		(SMIL, SEP,),
		(SMIL, ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(SMIL, ENTRY, 'C&opy channel', None, COPY_CHANNEL),
		(CMIF, ENTRY, '&Toggle channel state', None, TOGGLE_ONOFF),
##		(SMIL, ENTRY, 'Edit Source...', None, EDITSOURCE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Info...', 'I', INFO),
		(LIGHT, ENTRY, '&Properties...', 'A', ATTRIBUTES),
		(LIGHT, ENTRY, 'Edit &Content...', 'E', CONTENT),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Preferences...', None, PREFERENCES),
		)),

	('&Play', (
		(LIGHT, ENTRY, '&Play\tCtrl+P', 'P', PLAY),
		(LIGHT, ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(LIGHT, ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Play &node', None, PLAYNODE),
		(LIGHT, ENTRY, 'Play &from node', None, PLAYFROM),
		(CMIF, SEP,),
		(CMIF, DYNAMICCASCADE, 'User &groups', USERGROUPS),
		(CMIF, DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),


	('&Linking', (
		(LIGHT, ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(LIGHT, ENTRY, '&Finish hyperlink to selection', None, FINISH_LINK),
		(LIGHT, ENTRY, '&Anchors...', 'T', ANCHORS),
		(SMIL, SEP,),
		(SMIL, ENTRY, 'Create s&ync arc from selection...', None, FINISH_ARC),
		(SMIL, DYNAMICCASCADE, 'Select &sync arc', SYNCARCS),
		)),

	('&View', (
		(LIGHT, ENTRY, 'Expand/Collapse\tCtrl+I', None, EXPAND),
		(LIGHT, ENTRY, 'Expand all', None, EXPANDALL),
		(LIGHT, ENTRY, 'Collapse all', None, COLLAPSEALL),
		(SMIL, SEP,),
		(SMIL, ENTRY, 'Zoom in', None, CANVAS_WIDTH),
		(SMIL, ENTRY, 'Fit in Window', None, CANVAS_RESET),
		(SMIL, SEP,),
		(SMIL, ENTRY, 'Synchronize selection', None, PUSHFOCUS),
		(LIGHT, SEP,),
		(SMIL, TOGGLE, 'Unused &channels', None, TOGGLE_UNUSED),
		(SMIL, TOGGLE, 'Sync &arcs', None, TOGGLE_ARCS),
		(LIGHT, TOGGLE, 'Image thum&bnails', None, THUMBNAIL),
		(SMIL, TOGGLE, 'Bandwidth &usage strip', None, TOGGLE_BWSTRIP),
		(LIGHT, TOGGLE, 'Show Playable', None, PLAYABLE),
		(LIGHT, TOGGLE, 'Show Durations', None, TIMESCALE),
		(CMIF, SEP,),
		(CMIF, TOGGLE, '&Timeline view follows player', None, SYNCCV),
		(CMIF, CASCADE, '&Minidoc navigation', (
			(CMIF, ENTRY, '&Next', None, NEXT_MINIDOC),
			(CMIF, ENTRY, '&Previous', None, PREV_MINIDOC),
			(CMIF, DYNAMICCASCADE, '&Ancestors', ANCESTORS),
			(CMIF, DYNAMICCASCADE, '&Descendants', DESCENDANTS),
			(CMIF, DYNAMICCASCADE, '&Siblings', SIBLINGS),
			)),
##		(LIGHT, DYNAMICCASCADE, '&Layout navigation', LAYOUTS),
		)),

##	('&View', (
##		)),

	('&Window', (
		(LIGHT, ENTRY, 'Cl&ose\tCtrl+W', 'W', CLOSE_ACTIVE_WINDOW),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Cascade', 'C', CASCADE_WNDS),
		(LIGHT, ENTRY, 'Tile &Horizontally', 'H', TILE_HORZ),
		(LIGHT, ENTRY, 'Tile &Vertically', 'T', TILE_VERT),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Player\tF5', '1', PLAYERVIEW),
##		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Structure view\tF6', '3', HIERARCHYVIEW),
		(SMIL, ENTRY, '&Timeline view\tF7', '4', CHANNELVIEW),
		(SMIL, ENTRY, '&Layout view\tF8', '2', LAYOUTVIEW),
##		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'H&yperlinks', '5', LINKVIEW),
		(CMIF, ENTRY, 'User &groups', '6', USERGROUPVIEW),
##		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Sourc&e', '7', SOURCE),
		)),

	('&Help', (
		(LIGHT, ENTRY, '&Contents', None, HELP_CONTENTS),
		(LIGHT, ENTRY, 'Context &Help', None, HELP),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))


#
# Popup menus for various states
#
POPUP_HVIEW_LEAF = (
		(LIGHT, ENTRY, '&New node...', None, NEW_AFTER),
		(LIGHT, ENTRY, 'New node &before...', None, NEW_BEFORE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Cu&t', None, CUT),
		(LIGHT, ENTRY, '&Copy', None, COPY),
		(LIGHT, ENTRY, '&Paste', None, PASTE_AFTER),
		(LIGHT, ENTRY, 'Paste before', None, PASTE_BEFORE),
		(LIGHT, ENTRY, 'Paste file', None, PASTE_FILE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Delete', None, DELETE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'P&lay node', None, PLAYNODE),
		(LIGHT, ENTRY, 'Play &from node', None, PLAYFROM),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(LIGHT, ENTRY, '&Finish hyperlink to selection', None, FINISH_LINK),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Info...', None, INFO),
		(LIGHT, ENTRY, 'P&roperties...', None, ATTRIBUTES),
		(LIGHT, ENTRY, '&Anchors...', None, ANCHORS),
		(LIGHT, ENTRY, '&Edit content', None, CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		(LIGHT, ENTRY, '&New node...', None, NEW_AFTER),
		(LIGHT, CASCADE, '&New node special', (
			(LIGHT, ENTRY, '&Before...', None, NEW_BEFORE),
			(LIGHT, ENTRY, '&Within...', None, NEW_UNDER),
			)),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Cu&t', None, CUT),
		(LIGHT, ENTRY, '&Copy', None, COPY),
		(LIGHT, ENTRY, '&Paste', None, PASTE_AFTER),
		(LIGHT, CASCADE, '&Paste special', (
			(LIGHT, ENTRY, '&Before', None, PASTE_BEFORE),
			(LIGHT, ENTRY, '&Within', None, PASTE_UNDER),
			)),
		(LIGHT, ENTRY, 'Paste file', None, PASTE_FILE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Delete', None, DELETE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'P&lay node', None, PLAYNODE),
		(LIGHT, ENTRY, 'Play &from node', None, PLAYFROM),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Expand/Collapse', '\t', EXPAND),
		(LIGHT, ENTRY, 'Expand recursively', None, EXPANDALL),
		(LIGHT, ENTRY, 'Collapse recursively', None, COLLAPSEALL),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(LIGHT, ENTRY, '&Finish hyperlink to selection', None, FINISH_LINK),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Info...', None, INFO),
		(LIGHT, ENTRY, 'P&roperties...', None, ATTRIBUTES),
		(LIGHT, ENTRY, '&Anchors...', None, ANCHORS),
)

POPUP_CVIEW_NONE = (
		(LIGHT, ENTRY, '&New channel', 'M', NEW_CHANNEL),
)

POPUP_CVIEW_BWSTRIP = (
		(LIGHT, ENTRY, "&14k4", None, BANDWIDTH_14K4),
		(LIGHT, ENTRY, "&28k8", None, BANDWIDTH_28K8),
		(LIGHT, ENTRY, "&ISDN", None, BANDWIDTH_ISDN),
		(LIGHT, ENTRY, "&T1 (1 Mbps)", None, BANDWIDTH_T1),
		(LIGHT, ENTRY, "&LAN (10 Mbps)", None, BANDWIDTH_LAN),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, "&Other...", None, BANDWIDTH_OTHER),
		)

POPUP_CVIEW_CHANNEL = (
		(LIGHT, ENTRY, '&Delete', None, DELETE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(LIGHT, ENTRY, '&Copy channel', None, COPY_CHANNEL),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Properties...', 'A', ATTRIBUTES),

)

POPUP_CVIEW_NODE = (
		(LIGHT, ENTRY, '&Play node', None, PLAYNODE),
		(LIGHT, ENTRY, 'Play from &node', None, PLAYFROM),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Create simple anchor', None, CREATEANCHOR),
		(LIGHT, ENTRY, 'Finish &hyperlink to selection...', 'H', FINISH_LINK),
		(LIGHT, ENTRY, 'Create &syncarc from selection...', 'L', FINISH_ARC),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Info...', 'I', INFO),
		(LIGHT, ENTRY, 'P&roperties...', 'A', ATTRIBUTES),
		(LIGHT, ENTRY, '&Anchors...', 'T', ANCHORS),
		(LIGHT, ENTRY, '&Edit content', 'E', CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		(LIGHT, ENTRY, '&Info...', 'I', INFO),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Delete', None, DELETE),
)

MAIN_FRAME_POPUP = (
		(LIGHT, ENTRY, '&Paste document', None, PASTE_DOCUMENT),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&New\tCtrl+N', 'N', NEW_DOCUMENT),
		(LIGHT, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(LIGHT, ENTRY, '&Open URL...\tCtrl+L', 'O', OPEN),
		(LIGHT, DYNAMICCASCADE, 'Open &recent', OPEN_RECENT),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(LIGHT, ENTRY, 'Save &as...', None, SAVE_AS),
		(LIGHT, CASCADE, '&Export', (
			(LIGHT, ENTRY, '&RealSystem G2...', None, EXPORT_SMIL),
			)),
		(LIGHT, ENTRY, 'Revert &to saved', None, RESTORE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'Document &Properties...', None, PROPERTIES),
		(LIGHT|DBG, SEP,),
		(LIGHT|DBG, CASCADE, 'Debug', (
			(LIGHT|DBG, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(LIGHT|DBG, TOGGLE, 'Enable call tracing', None, TRACE),
			(LIGHT|DBG, ENTRY, 'Enter debugger', None, DEBUG),
			(LIGHT|DBG, ENTRY, 'Abort', None, CRASH),
			(LIGHT|DBG, TOGGLE, 'Show log/debug window', None, CONSOLE),
			)),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Close', None, CLOSE),
		(LIGHT, ENTRY, 'E&xit', None, EXIT),
)
