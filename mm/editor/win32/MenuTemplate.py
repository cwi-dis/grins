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
		(SEP,),
		(ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(ENTRY, 'Save &as...', None, SAVE_AS),
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
			(ENTRY, 'As &child', None, PASTE_UNDER),
			)),
		(ENTRY, '&Delete\tCtrl+Del', None, DELETE),
		(SEP,),
		(CASCADE, '&New node', (
			(ENTRY, '&Before', None, NEW_BEFORE),
			(ENTRY, '&After', None, NEW_AFTER),
			(ENTRY, '&Child', None, NEW_UNDER),
			(ENTRY, '&Par parent', None, NEW_PAR),
			(ENTRY, '&Seq parent', None, NEW_SEQ),
			(ENTRY, 'S&witch parent', None, NEW_ALT),
			(ENTRY, 'C&hoice parent', None, NEW_CHOICE),
			)),
		(ENTRY, 'New &channel', None, NEW_CHANNEL),
		(ENTRY, 'New &layout', None, NEW_LAYOUT),
		(SEP,),
		(ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(ENTRY, 'C&opy channel', None, COPY_CHANNEL),
		(ENTRY, '&Toggle channel state', None, TOGGLE_ONOFF),
		)),

	('&View', (
		(TOGGLE, '&Player', '1', PLAYERVIEW),
		(TOGGLE, '&Layout view', '2', LAYOUTVIEW),
		(TOGGLE, '&Structure view', '3', HIERARCHYVIEW),
		(TOGGLE, '&Timeline view', '4', CHANNELVIEW),
		(TOGGLE, '&Hyperlinks', '5', LINKVIEW),
		(TOGGLE, 'User &groups', '6', USERGROUPVIEW),
		(TOGGLE, 'Source', '7', SOURCE),
		(SEP,),
		(ENTRY, 'More hori&zontal detail', None, CANVAS_WIDTH),
		(ENTRY, 'More &vertical detail', None, CANVAS_HEIGHT),
		(ENTRY, '&Fit in window', None, CANVAS_RESET),
		(SEP,),
		(ENTRY, 'Zoom &in', None, ZOOMIN),
		(ENTRY, 'Zoom &out', None, ZOOMOUT),
		(ENTRY, 'Zoom to foc&us', None, ZOOMHERE),
		(SEP,),
		(ENTRY, 'Send focus to other vie&ws', None, PUSHFOCUS),
		(DYNAMICCASCADE, 'Select s&ync arc', SYNCARCS),
		(SEP,),
		(TOGGLE, 'Display unused &channels', None, TOGGLE_UNUSED),
		(TOGGLE, 'Display sync &arcs', None, TOGGLE_ARCS),
		(TOGGLE, 'Display image thum&bnails', None, THUMBNAIL),
		(SEP,),
		(TOGGLE, 'Timelin&e view follows player', None, SYNCCV),
		(CASCADE, '&Minidoc navigation', (
			(ENTRY, '&Next', None, NEXT_MINIDOC),
			(ENTRY, '&Previous', None, PREV_MINIDOC),
			(DYNAMICCASCADE, '&Ancestors', ANCESTORS),
			(DYNAMICCASCADE, '&Descendants', DESCENDANTS),
			(DYNAMICCASCADE, '&Siblings', SIBLINGS),
			)),
		(DYNAMICCASCADE, 'Layout navigation', LAYOUTS),
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
		(ENTRY, 'Show &info...', 'I', INFO),
		(ENTRY, 'Show &properties...', 'A', ATTRIBUTES),
		(ENTRY, 'Show &anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit &content...', 'E', CONTENT),
		(SEP,),
		(ENTRY, '&Edit content with registered application', None, CONTENT_EDIT_REG),
		(ENTRY, '&Open content with registered application', None, CONTENT_OPEN_REG),
		(SEP,),
		(ENTRY, '&Finish hyperlink to focus...', None, FINISH_LINK),
		(ENTRY, 'Create s&ync arc from focus...', None, FINISH_ARC),
		)),

	('&Window', (
		(ENTRY, 'Cl&ose', 'X', CLOSE_ACTIVE_WINDOW),
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
		(ENTRY, '&Cut', None, CUT),
		(ENTRY, 'Cop&y', None, COPY),
		(ENTRY, '&Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Paste &Before', None, PASTE_BEFORE),
		(ENTRY, 'Paste &After', None, PASTE_AFTER),
		(SEP,),
		(ENTRY, 'New node B&efore', None, NEW_BEFORE),
		(ENTRY, 'New node A&fter', None, NEW_AFTER),
		(SEP,),
		(ENTRY, '&Play node', None, PLAYNODE),
		(ENTRY, 'P&lay from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, '&Zoom in', None, ZOOMIN),
		(ENTRY, 'Zoom o&ut', None, ZOOMOUT),
		(SEP,),
		(ENTRY, '&Show info', None, INFO),
		(ENTRY, 'Show proper&ties', None, ATTRIBUTES),
		(ENTRY, 'Sho&w anchors', None, ANCHORS),
		(ENTRY, 'Edit c&ontent', None, CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		(ENTRY, '&Cut', None, CUT),
		(ENTRY, 'Cop&y', None, COPY),
		(ENTRY, '&Delete', None, DELETE),
		(SEP,),
		(ENTRY, 'Paste &Before', None, PASTE_BEFORE),
		(ENTRY, 'Paste &After', None, PASTE_AFTER),
		(ENTRY, 'Paste As c&hild', None, PASTE_UNDER),
		(SEP,),
		(ENTRY, 'New node B&efore', None, NEW_BEFORE),
		(ENTRY, 'New node A&fter', 'K', NEW_AFTER),
		(ENTRY, '&New Child', 'D', NEW_UNDER),
		(SEP,),
		(ENTRY, '&Play node', None, PLAYNODE),
		(ENTRY, 'P&lay from node', None, PLAYFROM),
		(SEP,),
		(ENTRY, '&Zoom in', None, ZOOMIN),
		(ENTRY, 'Zoom o&ut', None, ZOOMOUT),
		(ENTRY, 'Zoo&m to focus', 'Z', ZOOMHERE),
		(SEP,),
		(ENTRY, '&Show info', 'I', INFO),
		(ENTRY, 'Show proper&ties', 'A', ATTRIBUTES),
		(ENTRY, 'Sho&w anchors', 'T', ANCHORS),
)

POPUP_CVIEW_NONE = (
		(ENTRY, '&New channel', 'M', NEW_CHANNEL),
)

POPUP_CVIEW_CHANNEL = (
		(ENTRY, '&Move channel', None, MOVE_CHANNEL),
		(ENTRY, '&Copy channel', None, COPY_CHANNEL),
		(ENTRY, '&Toggle channel state', None, TOGGLE_ONOFF),
		(SEP,),
		(ENTRY, '&Delete', None, DELETE),

)

POPUP_CVIEW_NODE = (
		(ENTRY, 'Finish &hyperlink to focus...', 'H', FINISH_LINK),
		(ENTRY, 'Create s&yncarc from focus...', 'L', FINISH_ARC),
		(SEP,),
		(ENTRY, '&Play node', None, PLAYNODE),
		(ENTRY, 'Play from &node', None, PLAYFROM),
		(SEP,),
		(ENTRY, 'Show &info', 'I', INFO),
		(ENTRY, '&Show properties', 'A', ATTRIBUTES),
		(ENTRY, 'Show &anchors', 'T', ANCHORS),
		(ENTRY, 'Edit &content', 'E', CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		(ENTRY, '&Show info', 'I', INFO),
		(SEP,),
		(ENTRY, '&Delete', None, DELETE),
)

