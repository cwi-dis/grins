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


MENUBAR=(
	('&File', (
		(ENTRY, '&New\tCtrl+N', 'N', NEW_DOCUMENT),
		(ENTRY, '&Open...\tCtrl+O', 'O', OPEN),
		(ENTRY, '&Close document', None, CLOSE),
                (ENTRY, 'Document &Properties...', None, PROPERTIES),
		(SEP,),
		(ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(ENTRY, 'Save &as...', None, SAVE_AS),
		(ENTRY, '&Export SMIL...', None, EXPORT_SMIL),
		(ENTRY, '&Restore', None, RESTORE),
		(SEP,),
		(ENTRY, '&Preferences...', None, PREFERENCES),
		(SEP,),
		(CASCADE, '&Debug', (
			(ENTRY, 'Dump &scheduler data', None, SCHEDDUMP),
			(TOGGLE, 'Enable call &tracing', None, TRACE),
			(ENTRY, 'Enter &debugger', None, DEBUG),
			(ENTRY, '&Abort', None, CRASH),
			(TOGGLE, 'Show &log/debug window', None, CONSOLE),
			)),
		(SEP,),
		(ENTRY, 'E&xit', None, EXIT),
		)),

	('&Edit', (
		(ENTRY, '&Undo\tCtrl+Z', 'Z', UNDO),
		(SEP,),
		(ENTRY, 'Cu&t\tCtrl+X', 'X', CUT),
		(ENTRY, '&Copy\tCtrl+C', 'C', COPY),
		(ENTRY, '&Paste\tCtrl+V', 'V', PASTE),
		(CASCADE, 'P&aste node', (
			(ENTRY, '&Before', None, PASTE_BEFORE),
			(ENTRY, '&After', None, PASTE_AFTER),
			(ENTRY, '&Within', None, PASTE_UNDER),
			)),
		(ENTRY, '&Delete\tCtrl+Del', None, DELETE),
		(SEP,),
		(CASCADE, '&New node', (
			(ENTRY, '&Before', None, NEW_BEFORE),
			(ENTRY, '&After', None, NEW_AFTER),
			(ENTRY, '&Within', None, NEW_UNDER),
			(ENTRY, '&Par parent', None, NEW_PAR),
			(ENTRY, '&Seq parent', None, NEW_SEQ),
			(ENTRY, 'Sw&itch parent', None, NEW_ALT),
			(ENTRY, 'C&hoice parent', None, NEW_CHOICE),
			)),
		(ENTRY, 'New &channel', None, NEW_CHANNEL),

## Windows dialogs apparently don't use usercmd commands.
##		(ENTRY, 'New &layout', None, NEW_LAYOUT),
		(SEP,),
		(ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(ENTRY, 'C&opy channel', None, COPY_CHANNEL),
		(ENTRY, '&Toggle channel state', None, TOGGLE_ONOFF),
		(SEP,),
		(ENTRY, 'Edit Source...', None, EDITSOURCE),
		)),

	('&Play', (
		(ENTRY, '&Play document\tCtrl+P', 'P', PLAY),
		(ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(SEP,),
		(ENTRY, 'Play &node', None, PLAYNODE),
		(ENTRY, 'Play &from node', None, PLAYFROM),
		(SEP,),
		(DYNAMICCASCADE, 'User &groups', USERGROUPS),
		(DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),


	('&Tools', (
		(ENTRY, '&Info...', 'I', INFO),
		(ENTRY, '&Properties...', 'A', ATTRIBUTES),
		(ENTRY, '&Anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit &Content...', 'E', CONTENT),
		(SEP,),
		(ENTRY, '&Edit content', None, CONTENT_EDIT_REG),
		(ENTRY, '&Open content', None, CONTENT_OPEN_REG),
		(SEP,),
		(ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(ENTRY, '&Finish hyperlink to focus', None, FINISH_LINK),
		(ENTRY, 'Create s&ync arc from focus...', None, FINISH_ARC),
		)),

	('&Navigate', (
		(ENTRY, 'Expand/Collapse\tCtrl+I', None, EXPAND),
		(ENTRY, 'Expand recusively', None, EXPANDALL),
		(ENTRY, 'Collapse recusively', None, COLLAPSEALL),
		(CASCADE, '&Level of detail', (
			(ENTRY, 'More &horizontal detail', None, CANVAS_WIDTH),
			(ENTRY, 'More &vertical detail', None, CANVAS_HEIGHT),
			(ENTRY, 'Fit in &window', None, CANVAS_RESET),
			)),
		(SEP,),
		(ENTRY, 'Send &focus to other views', None, PUSHFOCUS),
		(DYNAMICCASCADE, 'Select &sync arc', SYNCARCS),
		(SEP,),
		(TOGGLE, 'Display unused &channels', None, TOGGLE_UNUSED),
		(TOGGLE, 'Display sync &arcs', None, TOGGLE_ARCS),
		(TOGGLE, 'Display image thum&bnails', None, THUMBNAIL),
		(TOGGLE, 'Display bandwidth &usage strip', None, TOGGLE_BWSTRIP),
		(SEP,),
		(TOGGLE, '&Timeline view follows player', None, SYNCCV),
		(ENTRY, '&Highlight channel in player', None, HIGHLIGHT),
		(ENTRY, '&Unhighlight channel in player', None, UNHIGHLIGHT),
		(CASCADE, '&Minidoc navigation', (
			(ENTRY, '&Next', None, NEXT_MINIDOC),
			(ENTRY, '&Previous', None, PREV_MINIDOC),
			(DYNAMICCASCADE, '&Ancestors', ANCESTORS),
			(DYNAMICCASCADE, '&Descendants', DESCENDANTS),
			(DYNAMICCASCADE, '&Siblings', SIBLINGS),
			)),
##		(DYNAMICCASCADE, '&Layout navigation', LAYOUTS),
		)),

	('&View', (
		(TOGGLE, '&Player\tF5', '1', PLAYERVIEW),
		(SEP,),
		(TOGGLE, '&Structure view\tF6', '3', HIERARCHYVIEW),
		(TOGGLE, '&Timeline view\tF7', '4', CHANNELVIEW),
		(TOGGLE, '&Layout view\tF8', '2', LAYOUTVIEW),
		(SEP,),
		(TOGGLE, '&Hyperlinks', '5', LINKVIEW),
		(TOGGLE, 'User &groups', '6', USERGROUPVIEW),
		(SEP,),
		(TOGGLE, 'Source', '7', SOURCE),
		)),

	('&Window', (
		(ENTRY, 'Cl&ose\tAlt+X', 'X', CLOSE_ACTIVE_WINDOW),
		(SEP,),
		(ENTRY, '&Cascade', 'C', CASCADE_WNDS),
		(ENTRY, 'Tile &Horizontally', 'H', TILE_HORZ),
		(ENTRY, 'Tile &Vertically', 'T', TILE_VERT),
		)),

	('&Help', (
		(ENTRY, '&Contents', None, HELP_CONTENTS),
		(ENTRY, 'Context &Help', None, HELP),
		(SEP,),
		(ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(SEP,),
		(ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))
		
		
#
# Popup menus for various states
#
POPUP_HVIEW_LEAF = (
		(CASCADE, '&New node', (
			(ENTRY, '&Before', None, NEW_BEFORE),
			(ENTRY, '&After', None, NEW_AFTER),
			)),
		(SEP,),
		(ENTRY, 'Cu&t', None, CUT),
		(ENTRY, '&Copy', None, COPY),
		(CASCADE, '&Paste', (
			(ENTRY, '&Before', None, PASTE_BEFORE),
			(ENTRY, '&After', None, PASTE_AFTER),
			)),
		(ENTRY, 'Paste file', None, PASTE_FILE),
		(SEP,),
		(ENTRY, '&Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'P&lay node', None, PLAYNODE),
		(ENTRY, 'Play &from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'C&reate simple anchor', None, CREATEANCHOR),
		(ENTRY, '&Finish hyperlink to focus', None, FINISH_LINK),
		(SEP,),
		(ENTRY, '&Info...', None, INFO),
		(ENTRY, 'P&roperties...', None, ATTRIBUTES),
		(ENTRY, '&Anchors...', None, ANCHORS),
		(ENTRY, '&Edit content', None, CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		(CASCADE, '&New node', (
			(ENTRY, '&Before', None, NEW_BEFORE),
			(ENTRY, '&After', None, NEW_AFTER),
			(ENTRY, '&Within', None, NEW_UNDER),
			)),
		(SEP,),
		(ENTRY, 'Cu&t', None, CUT),
		(ENTRY, '&Copy', None, COPY),
		(CASCADE, '&Paste', (
			(ENTRY, '&Before', None, PASTE_BEFORE),
			(ENTRY, '&After', None, PASTE_AFTER),
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
		(ENTRY, '&Finish hyperlink to focus', None, FINISH_LINK),
		(SEP,),
		(ENTRY, '&Info...', None, INFO),
		(ENTRY, 'P&roperties...', None, ATTRIBUTES),
		(ENTRY, '&Anchors...', None, ANCHORS),
)

POPUP_CVIEW_NONE = (
		(ENTRY, '&Create new channel', 'M', NEW_CHANNEL),
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
		(ENTRY, '&Toggle channel state', None, TOGGLE_ONOFF),
		(ENTRY, 'Show proper&ties', 'A', ATTRIBUTES),
		(SEP,),
		(ENTRY, '&Delete', None, DELETE),
		(SEP,),
		(ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(ENTRY, '&Copy channel', None, COPY_CHANNEL),

)

POPUP_CVIEW_NODE = (
		(ENTRY, '&Play node', None, PLAYNODE),
		(ENTRY, 'Play from &node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Create simple anchor', None, CREATEANCHOR),
		(ENTRY, 'Finish &hyperlink to focus...', 'H', FINISH_LINK),
		(ENTRY, 'Create &syncarc from focus...', 'L', FINISH_ARC),
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
		(ENTRY, '&New\tCtrl+N', 'N', NEW_DOCUMENT),
		(ENTRY, '&Open...\tCtrl+O', 'O', OPEN),
		(ENTRY, '&Close document', None, CLOSE),
                (ENTRY, 'Document &Properties...', None, PROPERTIES),
		(SEP,),
		(ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(ENTRY, 'Save &as...', None, SAVE_AS),
		(ENTRY, '&Export SMIL...', None, EXPORT_SMIL),
		(ENTRY, '&Restore', None, RESTORE),
)
