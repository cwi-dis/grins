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
ALL=''
CMIF='cmif'
DEBUG='debug'

MENUBAR=(
	('&File', (
		(ALL, ENTRY, '&New\tCtrl+N', 'N', NEW_DOCUMENT),
		(ALL, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(ALL, ENTRY, '&Open URL...\tCtrl+L', 'O', OPEN),
		(ALL, DYNAMICCASCADE, 'Open &recent', OPEN_RECENT),
		(ALL, ENTRY, '&Close', None, CLOSE),
 		(ALL, SEP,),
		(ALL, ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(ALL, ENTRY, 'Save &as...', None, SAVE_AS),
		(ALL, CASCADE, '&Export', (
			(ALL, ENTRY, '&RealSystem G2...', None, EXPORT_SMIL),
			)),
		(ALL, ENTRY, 'Revert &to saved', None, RESTORE),
		(ALL, SEP,),
        (ALL, ENTRY, 'Document &Properties...', None, PROPERTIES),
		(DEBUG, SEP,),
		(DEBUG, CASCADE, 'Debug', (
			(ALL, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(ALL, TOGGLE, 'Enable call tracing', None, TRACE),
			(ALL, ENTRY, 'Enter debugger', None, DEBUG),
			(ALL, ENTRY, 'Abort', None, CRASH),
			(ALL, TOGGLE, 'Show log/debug window', None, CONSOLE),
			)),
		(ALL, SEP,),
		(ALL, ENTRY, 'E&xit', None, EXIT),
		)),

	('&Edit', (
		(ALL, ENTRY, '&Undo\tCtrl+Z', 'Z', UNDO),
		(ALL, SEP,),
		(ALL, ENTRY, 'Cu&t\tCtrl+X', 'X', CUT),
		(ALL, ENTRY, '&Copy\tCtrl+C', 'C', COPY),
		(ALL, ENTRY, '&Paste\tCtrl+V', 'V', PASTE),
		(ALL, CASCADE, 'P&aste special', (
			(ALL, ENTRY, '&Before', None, PASTE_BEFORE),
##			(ALL, ENTRY, '&After', None, PASTE_AFTER),
			(ALL, ENTRY, '&Within', None, PASTE_UNDER),
			)),
		(ALL, ENTRY, '&Delete\tCtrl+Del', None, DELETE),
		(ALL, SEP,),
		(ALL, ENTRY, '&New node...', None, NEW_AFTER),
		(ALL, CASCADE, 'Ne&w node special', (
			(ALL, ENTRY, '&Before...', None, NEW_BEFORE),
			(ALL, ENTRY, '&Within...', None, NEW_UNDER),
			(ALL, ENTRY, '&Par parent', None, NEW_PAR),
			(ALL, ENTRY, '&Seq parent', None, NEW_SEQ),
			(ALL, ENTRY, 'Sw&itch parent', None, NEW_ALT),
			(CMIF, ENTRY, 'C&hoice parent', None, NEW_CHOICE),
			)),
		(ALL, ENTRY, 'New &channel', None, NEW_CHANNEL),

## Windows dialogs apparently don't use usercmd commands.
##		(ENTRY, 'New &layout', None, NEW_LAYOUT),
		(ALL, SEP,),
		(ALL, ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(ALL, ENTRY, 'C&opy channel', None, COPY_CHANNEL),
		(CMIF, ENTRY, '&Toggle channel state', None, TOGGLE_ONOFF),
##		(ALL, ENTRY, 'Edit Source...', None, EDITSOURCE),
		(ALL, SEP,),
		(ALL, ENTRY, '&Info...', 'I', INFO),
		(ALL, ENTRY, '&Properties...', 'A', ATTRIBUTES),
		(ALL, ENTRY, 'Edit &Content...', 'E', CONTENT),
		(ALL, SEP,),
		(ALL, ENTRY, '&Preferences...', None, PREFERENCES),
		)),

	('&Play', (
		(ALL, ENTRY, '&Play\tCtrl+P', 'P', PLAY),
		(ALL, ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(ALL, ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(ALL, SEP,),
		(ALL, ENTRY, 'Play &node', None, PLAYNODE),
		(ALL, ENTRY, 'Play &from node', None, PLAYFROM),
		(CMIF, SEP,),
		(CMIF, DYNAMICCASCADE, 'User &groups', USERGROUPS),
		(CMIF, DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),


	('&Linking', (
		(ALL, ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(ALL, ENTRY, '&Finish hyperlink to selection', None, FINISH_LINK),
		(ALL, ENTRY, '&Anchors...', 'T', ANCHORS),
		(ALL, SEP,),
		(ALL, ENTRY, 'Create s&ync arc from selection...', None, FINISH_ARC),
		(ALL, DYNAMICCASCADE, 'Select &sync arc', SYNCARCS),
		)),

	('&View', (
		(ALL, ENTRY, 'Expand/Collapse\tCtrl+I', None, EXPAND),
		(ALL, ENTRY, 'Expand all', None, EXPANDALL),
		(ALL, ENTRY, 'Collapse all', None, COLLAPSEALL),
		(ALL, SEP,),
		(ALL, ENTRY, 'Zoom in', None, CANVAS_WIDTH),
		(ALL, ENTRY, 'Fit in Window', None, CANVAS_RESET),
		(ALL, SEP,),
		(ALL, ENTRY, 'Synchronize selection', None, PUSHFOCUS),
		(ALL, SEP,),
		(ALL, TOGGLE, 'Unused &channels', None, TOGGLE_UNUSED),
		(ALL, TOGGLE, 'Sync &arcs', None, TOGGLE_ARCS),
		(ALL, TOGGLE, 'Image thum&bnails', None, THUMBNAIL),
		(ALL, TOGGLE, 'Bandwidth &usage strip', None, TOGGLE_BWSTRIP),
		(CMIF, SEP,),
		(CMIF, TOGGLE, '&Timeline view follows player', None, SYNCCV),
		(CMIF, CASCADE, '&Minidoc navigation', (
			(CMIF, ENTRY, '&Next', None, NEXT_MINIDOC),
			(CMIF, ENTRY, '&Previous', None, PREV_MINIDOC),
			(CMIF, DYNAMICCASCADE, '&Ancestors', ANCESTORS),
			(CMIF, DYNAMICCASCADE, '&Descendants', DESCENDANTS),
			(CMIF, DYNAMICCASCADE, '&Siblings', SIBLINGS),
			)),
##		(ALL, DYNAMICCASCADE, '&Layout navigation', LAYOUTS),
		)),

##	('&View', (
##		)),

	('&Window', (
		(ALL, ENTRY, 'Cl&ose\tCtrl+W', 'W', CLOSE_ACTIVE_WINDOW),
		(ALL, SEP,),
		(ALL, ENTRY, '&Cascade', 'C', CASCADE_WNDS),
		(ALL, ENTRY, 'Tile &Horizontally', 'H', TILE_HORZ),
		(ALL, ENTRY, 'Tile &Vertically', 'T', TILE_VERT),
		(ALL, SEP,),
		(ALL, ENTRY, '&Player\tF5', '1', PLAYERVIEW),
##		(ALL, SEP,),
		(ALL, ENTRY, '&Structure view\tF6', '3', HIERARCHYVIEW),
		(ALL, ENTRY, '&Timeline view\tF7', '4', CHANNELVIEW),
		(ALL, ENTRY, '&Layout view\tF8', '2', LAYOUTVIEW),
##		(ALL, SEP,),
		(ALL, ENTRY, 'H&yperlinks', '5', LINKVIEW),
		(CMIF, ENTRY, 'User &groups', '6', USERGROUPVIEW),
##		(ALL, SEP,),
		(ALL, ENTRY, 'Sourc&e', '7', SOURCE),
		)),

	('&Help', (
		(ALL, ENTRY, '&Contents', None, HELP_CONTENTS),
		(ALL, ENTRY, 'Context &Help', None, HELP),
		(ALL, SEP,),
		(ALL, ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(ALL, SEP,),
		(ALL, ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))
		
		
#
# Popup menus for various states
#
POPUP_HVIEW_LEAF = (
		(ENTRY, '&New node...', None, NEW_AFTER),
		(ENTRY, 'New node &before...', None, NEW_BEFORE),
		(SEP,),
		(ENTRY, 'Cu&t', None, CUT),
		(ENTRY, '&Copy', None, COPY),
		(ENTRY, '&Paste', None, PASTE_AFTER),
		(ENTRY, 'Paste before', None, PASTE_BEFORE),
		(ENTRY, 'Paste file', None, PASTE_FILE),
		(SEP,),
		(ENTRY, '&Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'P&lay node', None, PLAYNODE),
		(ENTRY, 'Play &from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(ENTRY, '&Finish hyperlink to selection', None, FINISH_LINK),
		(SEP,),
		(ENTRY, '&Info...', None, INFO),
		(ENTRY, 'P&roperties...', None, ATTRIBUTES),
		(ENTRY, '&Anchors...', None, ANCHORS),
		(ENTRY, '&Edit content', None, CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		(ENTRY, '&New node...', None, NEW_AFTER),
		(CASCADE, '&New node special', (
			(ENTRY, '&Before...', None, NEW_BEFORE),
			(ENTRY, '&Within...', None, NEW_UNDER),
			)),
		(SEP,),
		(ENTRY, 'Cu&t', None, CUT),
		(ENTRY, '&Copy', None, COPY),
		(ENTRY, '&Paste', None, PASTE_AFTER),
		(CASCADE, '&Paste special', (
			(ENTRY, '&Before', None, PASTE_BEFORE),
			(ENTRY, '&Within', None, PASTE_UNDER),
			)),
		(ENTRY, 'Paste file', None, PASTE_FILE),
		(SEP,),
		(ENTRY, '&Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'P&lay node', None, PLAYNODE),
		(ENTRY, 'Play &from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Expand/Collapse', '\t', EXPAND),
		(ENTRY, 'Expand recursively', None, EXPANDALL),
		(ENTRY, 'Collapse recursively', None, COLLAPSEALL),
		(SEP,),
		(ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(ENTRY, '&Finish hyperlink to selection', None, FINISH_LINK),
		(SEP,),
		(ENTRY, '&Info...', None, INFO),
		(ENTRY, 'P&roperties...', None, ATTRIBUTES),
		(ENTRY, '&Anchors...', None, ANCHORS),
)

POPUP_CVIEW_NONE = (
		(ENTRY, '&New channel', 'M', NEW_CHANNEL),
)

POPUP_CVIEW_BWSTRIP = (
		(ENTRY, "&14k4", None, BANDWIDTH_14K4),
		(ENTRY, "&28k8", None, BANDWIDTH_28K8),
		(ENTRY, "&ISDN", None, BANDWIDTH_ISDN),
		(ENTRY, "&T1 (1 Mbps)", None, BANDWIDTH_T1),
		(ENTRY, "&LAN (10 Mbps)", None, BANDWIDTH_LAN),
		(SEP,),
		(ENTRY, "&Other...", None, BANDWIDTH_OTHER),
		)

POPUP_CVIEW_CHANNEL = (
		(ENTRY, '&Delete', None, DELETE),
		(SEP,),
		(ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(ENTRY, '&Copy channel', None, COPY_CHANNEL),
		(SEP,),
		(ENTRY, '&Properties...', 'A', ATTRIBUTES),

)

POPUP_CVIEW_NODE = (
		(ENTRY, '&Play node', None, PLAYNODE),
		(ENTRY, 'Play from &node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Create simple anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish &hyperlink to selection...', 'H', FINISH_LINK),
		(ENTRY, 'Create &syncarc from selection...', 'L', FINISH_ARC),
		(SEP,),
		(ENTRY, '&Info...', 'I', INFO),
		(ENTRY, 'P&roperties...', 'A', ATTRIBUTES),
		(ENTRY, '&Anchors...', 'T', ANCHORS),
		(ENTRY, '&Edit content', 'E', CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		(ENTRY, '&Info...', 'I', INFO),
		(SEP,),
		(ENTRY, '&Delete', None, DELETE),
)

MAIN_FRAME_POPUP = (
		(ENTRY, '&Paste document', None, PASTE_DOCUMENT),
		(SEP,),
		(ALL, ENTRY, '&New\tCtrl+N', 'N', NEW_DOCUMENT),
		(ALL, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(ALL, ENTRY, '&Open URL...\tCtrl+L', 'O', OPEN),
		(ALL, DYNAMICCASCADE, 'Open &recent', OPEN_RECENT),
		(ALL, SEP,),
		(ALL, ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(ALL, ENTRY, 'Save &as...', None, SAVE_AS),
		(ALL, CASCADE, '&Export', (
			(ALL, ENTRY, '&RealSystem G2...', None, EXPORT_SMIL),
			)),
		(ALL, ENTRY, 'Revert &to saved', None, RESTORE),
		(ALL, SEP,),
        (ALL, ENTRY, 'Document &Properties...', None, PROPERTIES),
		(DEBUG, SEP,),
		(DEBUG, CASCADE, 'Debug', (
			(ALL, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(ALL, TOGGLE, 'Enable call tracing', None, TRACE),
			(ALL, ENTRY, 'Enter debugger', None, DEBUG),
			(ALL, ENTRY, 'Abort', None, CRASH),
			(ALL, TOGGLE, 'Show log/debug window', None, CONSOLE),
			)),
		(ALL, SEP,),
		(ALL, ENTRY, '&Close', None, CLOSE),
 		(ALL, ENTRY, 'E&xit', None, EXIT),
)
