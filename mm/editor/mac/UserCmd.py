#
# Command/menu mapping for the mac, editor version
#

class CommandID:
	number = 0
	
	def __init__(self):
		self.id = CommandID.number
		CommandID.number = CommandID.number + 1
		
# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE] = range(4)

#
# Global commands
#
CLOSE_WINDOW=CommandID()
UNDO=CommandID()
CUT=CommandID()
COPY=CommandID()
PASTE=CommandID()
DELETE=CommandID()
#
# MainDialog commands
#	
NEW_DOCUMENT=CommandID()
OPEN_URL=CommandID()
OPEN_FILE=CommandID()
TRACE=CommandID()
DEBUG=CommandID()
EXIT=CommandID()
SAVE=CommandID()
SAVE_AS=CommandID()
RESTORE=CommandID()
CLOSE=CommandID()
#
# TopLevel commands
#
PLAY=CommandID()
PLAYERVIEW=CommandID()
HIERARCHYVIEW=CommandID()
CHANNELVIEW=CommandID()
LINKVIEW=CommandID()
#
# Hierarchy view commands
#
PASTE_BEFORE=CommandID()
PASTE_AFTER=CommandID()
PASTE_UNDER=CommandID()
NEW_BEFORE=CommandID()
NEW_AFTER=CommandID()
NEW_UNDER=CommandID()
NEW_SEQ=CommandID()
NEW_PAR=CommandID()
NEW_CHOICE=CommandID()
NEW_ALT=CommandID()
ZOOMIN=CommandID()
ZOOMOUT=CommandID()
ZOOMHERE=CommandID()
#
# Command to hierarchy/channel view
#
CANVAS_WIDTH=CommandID()
CANVAS_HEIGHT=CommandID()
CANVAS_RESET=CommandID()
INFO=CommandID()
ATTRIBUTES=CommandID()
ANCHORS=CommandID()
CONTENT=CommandID()
PLAYNODE=CommandID()
PLAYFROM=CommandID()
PUSHFOCUS=CommandID()
FINISH_LINK=CommandID()
FINISH_ARC=CommandID()
#
# Channel view commands
#
NEW_CHANNEL=CommandID()
TOGGLE_UNUSED=CommandID()
NEXT_MINIDOC=CommandID()
PREV_MINIDOC=CommandID()
MOVE_CHANNEL=CommandID()
COPY_CHANNEL=CommandID()
TOGGLE_ONOFF=CommandID()

#
# Menu structure
#
MENUBAR=(
	('File', (
		(ENTRY, 'New', 'N', NEW_DOCUMENT),
		(ENTRY, 'Open URL...', 'U', OPEN_URL),
		(ENTRY, 'Open...', 'O', OPEN_FILE),
		(ENTRY, 'Close', 'W', CLOSE_WINDOW),
		(SEP,),
		(ENTRY, 'Save', 'S', SAVE),
		(ENTRY, 'Save as...', None, SAVE_AS),
		(ENTRY, 'Restore', None, RESTORE),
		(ENTRY, 'Close document', None, CLOSE),
		(SEP,),
		(TOGGLE, 'Trace', None, TRACE),
		(ENTRY, 'Debug', None, DEBUG),
		(SEP,),
		(ENTRY, 'Quit', 'Q', EXIT))),

	('Edit', (
		(ENTRY, 'Undo', 'Z', UNDO),
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
			(ENTRY, 'After', None, NEW_AFTER),
			(ENTRY, 'Under', None, NEW_UNDER),
			(ENTRY, 'Par parent', None, NEW_PAR),
			(ENTRY, 'Seq parent', None, NEW_SEQ),
			(ENTRY, 'Choice parent', None, NEW_CHOICE),
			(ENTRY, 'Alt parent', None, NEW_ALT))),
		(ENTRY, 'New channel', None, NEW_CHANNEL),
		(ENTRY, 'Move channel', None, MOVE_CHANNEL),
		(ENTRY, 'Copy channel', None, COPY_CHANNEL),
		(ENTRY, 'Toggle channel state', None, TOGGLE_ONOFF))),

	('View', (
		(TOGGLE, 'Player', '1', PLAYERVIEW),
		(TOGGLE, 'Hierarchy', '2', HIERARCHYVIEW),
		(TOGGLE, 'Channel/timeline', '3', CHANNELVIEW),
		(TOGGLE, 'Hyperlinks', '4', LINKVIEW),
		(SEP,),
		(CASCADE, 'Canvas size', (
			(ENTRY, 'Enlarge width', None, CANVAS_WIDTH),
			(ENTRY, 'Enlarge height', None, CANVAS_HEIGHT),
			(ENTRY, 'Reset', None, CANVAS_RESET))),
		(ENTRY, 'Zoom in', None, ZOOMIN),
		(ENTRY, 'Zoom out', None, ZOOMOUT),
		(ENTRY, 'Zoom to focus', 'Z', ZOOMHERE),
		(SEP,),
		(ENTRY, 'Toggle unused channels', None, TOGGLE_UNUSED),
		(SEP,),
		(CASCADE, 'Mini-document', (
			(ENTRY, 'Next', None, NEXT_MINIDOC),
			(ENTRY, 'Previous', None, PREV_MINIDOC))))),
		
	('Play', (
		(ENTRY, 'Whole document', 'P', PLAY),
		(ENTRY, 'Node', None, PLAYNODE),
		(ENTRY, 'Starting at node', None, PLAYFROM))),

	('Focus', (
		(ENTRY, 'Synchronize', 'F', PUSHFOCUS),
		(SEP,),
		(ENTRY, 'Show info', 'I', INFO),
		(ENTRY, 'Show attributes', 'A', ATTRIBUTES),
		(ENTRY, 'Show anchors', 'T', ANCHORS),
		(ENTRY, 'Edit content', 'E', CONTENT),
		(SEP,),
		(ENTRY, 'Finish hyperlink to focus...', 'L', FINISH_LINK),
		(ENTRY, 'Finish syncarc to focus...', 'L', FINISH_ARC))))
		
			
		
