#
# Command/menu mapping for the mac, editor version
#

from usercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)

#
# commands we know are not useable on the Mac:
UNUSED_COMMANDS=(
	MAGIC_PLAY,
)

#
# Menu structure
#

MENUBAR=(
	(CASCADE, 'File', (
		(ENTRY, 'New', 'N', NEW_DOCUMENT),
		(ENTRY, 'Open...', 'O', OPEN),
		(ENTRY, 'Close window', 'W', CLOSE_WINDOW),
		(ENTRY, 'Close document', None, CLOSE),
		(SEP,),
		(ENTRY, 'Save', 'S', SAVE),
		(ENTRY, 'Save as...', None, SAVE_AS),
		(ENTRY, 'Restore', None, RESTORE),
		(SEP,),
		(ENTRY, 'Preferences...', None, PREFERENCES),
		(SEP,),
		(CASCADE, 'Debug', (
			(TOGGLE, ('Enable call tracing','Disable call tracing'), None, TRACE),
			(ENTRY, 'Enter debugger', None, DEBUG),
			(ENTRY, 'Abort', None, CRASH),
			(ENTRY, 'Show log/debug window', None, CONSOLE))),
		(SEP,),
		(ENTRY, 'Quit', 'Q', EXIT))),

	(CASCADE, 'Edit', (
		(ENTRY, 'Undo', 'Z', UNDO),
		(SEP,),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Paste', 'V', PASTE),
		(CASCADE, 'Paste node', (
			(ENTRY, 'Before', None, PASTE_BEFORE),
			(ENTRY, 'After', None, PASTE_AFTER),
			(ENTRY, 'Under', None, PASTE_UNDER))),
		(ENTRY, 'Delete', None, DELETE),
		(SEP,),
		(CASCADE, 'New node', (
			(ENTRY, 'Before', None, NEW_BEFORE),
			(ENTRY, 'After', 'K', NEW_AFTER),
			(ENTRY, 'Under', 'D', NEW_UNDER),
			(ENTRY, 'Par parent', None, NEW_PAR),
			(ENTRY, 'Seq parent', None, NEW_SEQ),
			(ENTRY, 'Choice parent', None, NEW_CHOICE),
			(ENTRY, 'Alt parent', None, NEW_ALT))),
		(ENTRY, 'New channel', 'M', NEW_CHANNEL),
		(ENTRY, 'Move channel', None, MOVE_CHANNEL),
		(ENTRY, 'Copy channel', None, COPY_CHANNEL),
		(ENTRY, 'Toggle channel state', None, TOGGLE_ONOFF))),

	(CASCADE, 'View', (
		(TOGGLE, ('Open Player', 'Close Player'), '1', PLAYERVIEW),
		(TOGGLE, ('Open Layout view', 'Close Layout view'), '2', LAYOUTVIEW),
		(TOGGLE, ('Open Hierarchy view', 'Close Hierarchy view'), '3', HIERARCHYVIEW),
		(TOGGLE, ('Open Timeline view', 'Close Timeline view'), '4', CHANNELVIEW),
		(TOGGLE, ('Open Hyperlink view', 'Close Hyperlink view'), '5', LINKVIEW),
		(SEP,),
		(ENTRY, 'Zoom in', None, ZOOMIN),
		(ENTRY, 'Zoom out', None, ZOOMOUT),
		(ENTRY, 'Zoom to focus', 'Z', ZOOMHERE),
		(CASCADE, 'Canvas size', (
			(ENTRY, 'Enlarge width', None, CANVAS_WIDTH),
			(ENTRY, 'Enlarge height', None, CANVAS_HEIGHT),
			(ENTRY, 'Reset', None, CANVAS_RESET))),
		(SEP,),
		(TOGGLE, 'Display unused channels', 'T', TOGGLE_UNUSED),
		(TOGGLE, 'Display sync arcs', None, TOGGLE_ARCS),
		(TOGGLE, 'Display image thumbnails', None, THUMBNAIL),
		(SEP,),
		(CASCADE, 'Minidoc navigation', (
			(ENTRY, 'Next', None, NEXT_MINIDOC),
			(ENTRY, 'Previous', None, PREV_MINIDOC),
			(DYNAMICCASCADE, 'Ancestors', ANCESTORS),
			(DYNAMICCASCADE, 'Descendants', DESCENDANTS),
			(DYNAMICCASCADE, 'Siblings', SIBLINGS))),
		(DYNAMICCASCADE, 'Layout navigation', LAYOUTS))),
		
		
	(CASCADE, 'Play', (
		(ENTRY, 'Play document', 'P', PLAY),
		(ENTRY, 'Pause', None, PAUSE),
		(ENTRY, 'Stop', None, STOP),
		(SEP,),
		(ENTRY, 'Play node', None, PLAYNODE),
		(ENTRY, 'Play from node', None, PLAYFROM),
		(SEP,),
		(DYNAMICCASCADE, 'Channel visibility', CHANNELS))),

	(CASCADE, 'Focus', (
		(ENTRY, 'Synchronize', 'F', PUSHFOCUS),
		(SEP,),
		(ENTRY, 'Show info', 'I', INFO),
		(ENTRY, 'Show attributes', 'A', ATTRIBUTES),
		(ENTRY, 'Show anchors', 'T', ANCHORS),
		(ENTRY, 'Edit content', 'E', CONTENT),
		(SEP,),
		(DYNAMICCASCADE, 'Select syncarc', SYNCARCS),
		(SEP,),
		(ENTRY, 'Finish hyperlink to focus...', 'H', FINISH_LINK),
		(ENTRY, 'Create syncarc from focus...', 'L', FINISH_ARC))))
		
			
		
