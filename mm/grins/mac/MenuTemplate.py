#
# Menubar template for the Mac player
#
from usercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE] = range(4)

#
# Commands that we know are not implemented on the mac:
UNUSED_COMMANDS=()

#
# Menu structure
#
MENUBAR=(
	('File', (
		(ENTRY, 'Open...', 'O', OPEN),
		(ENTRY, 'Close Window', 'W', CLOSE_WINDOW),
		(ENTRY, 'Close Document', None, CLOSE),
		(SEP,),
		(CASCADE, 'Debug', (
			(TOGGLE, 'Enable call tracing', None, TRACE),
			(ENTRY, 'Enter debugger', None, DEBUG),
			(ENTRY, 'Show log/debug window', None, CONSOLE))),
		(SEP,),
		(ENTRY, 'Quit', 'Q', EXIT))),

	('Edit', (
		(ENTRY, 'Undo', 'Z', UNDO),
		(SEP,),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Paste', 'V', PASTE),
		(ENTRY, 'Clear', None, DELETE))),
		
	('Play', (
		(TOGGLE, 'Play', 'P', PLAY),
		(TOGGLE, 'Stop', 'H', STOP),
		(TOGGLE, 'Pause', 'B', PAUSE))))
		
			
#
# Adornments
#
PLAYER_ADORNMENTS = {
	'toolbar': (
		(TOGGLE, 1000, STOP),
		(TOGGLE, 1500, PLAY),
		(TOGGLE, 2000, PAUSE),
		)
}

#
# CNTL resource for the toolbar and its height
TOOLBAR=(2500, 22)
		
