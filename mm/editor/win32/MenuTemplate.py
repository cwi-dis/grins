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
		(ENTRY, 'New', 'N', NEW_DOCUMENT),
		(ENTRY, 'Open...', 'O', OPEN),
		(ENTRY, 'Close document', None, CLOSE),
		(SEP,),
		(ENTRY, 'Save', 'S', SAVE),
		(ENTRY, 'Save as...', None, SAVE_AS),
		(ENTRY, 'Restore', None, RESTORE),
		(SEP,),
		(ENTRY, 'Preferences...', None, PREFERENCES),
		(ENTRY, 'Charset...', 'C', SELECT_CHARSET),
		(SEP,),
		(CASCADE, 'Debug', (
			(ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(TOGGLE, 'Enable call tracing', None, TRACE),
			(ENTRY, 'Enter debugger', None, DEBUG),
			(ENTRY, 'Abort', None, CRASH),
			(TOGGLE, 'Show log/debug window', None, CONSOLE),
			)),
		(SEP,),
		(ENTRY, 'Exit', 'Q', EXIT),
		)),

	('&Edit', (
		(ENTRY, 'Undo', 'Z', UNDO),
		(SEP,),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Paste', 'V', PASTE),
		(CASCADE, 'Paste node', (
			(ENTRY, 'Before', None, PASTE_BEFORE),
			(ENTRY, 'After', None, PASTE_AFTER),
			(ENTRY, 'Under', None, PASTE_UNDER),
			)),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(CASCADE, 'New node', (
			(ENTRY, 'Before', None, NEW_BEFORE),
			(ENTRY, 'After', 'K', NEW_AFTER),
			(ENTRY, 'Under', 'D', NEW_UNDER),
			(ENTRY, 'Par parent', None, NEW_PAR),
			(ENTRY, 'Seq parent', None, NEW_SEQ),
			(ENTRY, 'Choice parent', None, NEW_CHOICE),
			(ENTRY, 'Alt parent', None, NEW_ALT)
			)),
		(ENTRY, 'New channel', 'M', NEW_CHANNEL),
		(ENTRY, 'New layout', None, NEW_LAYOUT),
		(SEP,),
		(ENTRY, 'Move channel', None, MOVE_CHANNEL),
		(ENTRY, 'Copy channel', None, COPY_CHANNEL),
		(ENTRY, 'Toggle channel state', None, TOGGLE_ONOFF),
		)),

	('&View', (
		(TOGGLE, 'Player', '1', PLAYERVIEW),
		(TOGGLE, 'Layout view', '2', LAYOUTVIEW),
		(TOGGLE, 'Hierarchy view', '3', HIERARCHYVIEW),
		(TOGGLE, 'Timeline view', '4', CHANNELVIEW),
		(TOGGLE, 'Hyperlink view', '5', LINKVIEW),
		(TOGGLE, 'Source', '6', SOURCE),
		(SEP,),
		(ENTRY, 'More horizontal detail', None, CANVAS_WIDTH),
		(ENTRY, 'More vertical detail', None, CANVAS_HEIGHT),
		(ENTRY, 'Reset to document', None, CANVAS_RESET),
		(ENTRY, 'Fit in window', None, CANVAS_FIT),
		(SEP,),
		(ENTRY, 'Zoom in', None, ZOOMIN),
		(ENTRY, 'Zoom out', None, ZOOMOUT),
		(ENTRY, 'Zoom to focus', 'Z', ZOOMHERE),
		(SEP,),
		(ENTRY, 'Send focus to other views', 'F', PUSHFOCUS),
		(DYNAMICCASCADE, 'Select syncarc', SYNCARCS),
		(SEP,),
		(TOGGLE, 'Display unused channels', 'T', TOGGLE_UNUSED),
		(TOGGLE, 'Display sync arcs', None, TOGGLE_ARCS),
		(TOGGLE, 'Display image thumbnails', None, THUMBNAIL),
		(SEP,),
		(TOGGLE, 'Timeline view follows player', None, SYNCCV),
		(CASCADE, 'Minidoc navigation', (
			(ENTRY, 'Next', None, NEXT_MINIDOC),
			(ENTRY, 'Previous', None, PREV_MINIDOC),
			(DYNAMICCASCADE, 'Ancestors', ANCESTORS),
			(DYNAMICCASCADE, 'Descendants', DESCENDANTS),
			(DYNAMICCASCADE, 'Siblings', SIBLINGS),
			)),
		(DYNAMICCASCADE, 'Layout navigation', LAYOUTS),
		)),

	('&Play', (
		(ENTRY, 'Play document', 'P', PLAY),
		(ENTRY, 'Pause', None, PAUSE),
		(ENTRY, 'Stop', None, STOP),
		(SEP,),
		(ENTRY, 'Play node', None, PLAYNODE),
		(ENTRY, 'Play from node', None, PLAYFROM),
		(SEP,),
		(DYNAMICCASCADE, 'Visible channels', CHANNELS),
		)),


	('&Tools', (
		(ENTRY, 'Show info...', 'I', INFO),
		(ENTRY, 'Show attributes...', 'A', ATTRIBUTES),
		(ENTRY, 'Show anchors...', 'T', ANCHORS),
		(ENTRY, 'Edit content...', 'E', CONTENT),
		(SEP,),
		(ENTRY, 'Finish hyperlink to focus...', 'H', FINISH_LINK),
		(ENTRY, 'Create syncarc from focus...', 'L', FINISH_ARC),
		)),

	('&Window', (
		(ENTRY, 'Close', 'X', CLOSE_ACTIVE_WINDOW),
		(SEP,),
		(ENTRY, '&Cascade', 'C', CASCADE_WNDS),
		(ENTRY, 'Tile &Horizontally', 'H', TILE_HORZ),
		(ENTRY, '&Tile Vertically', 'T', TILE_VERT),
		)),

	('&Help', (
		(ENTRY, 'Help...', None, HELP),
		(SEP,),
		(ENTRY, 'About...', None, ABOUT_GRINS))))
		
		
