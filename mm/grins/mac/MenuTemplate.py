#
# Menubar template for the Mac player
#
from usercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE, SPECIAL] = range(6)

# Some commands are optional, depending on preference settings:
ALL=''
CMIF='cmif'
DEBUG='debug'
#
# Commands that we know are not implemented on the mac:
UNUSED_COMMANDS=(MAGIC_PLAY,)   # Is implemented, but the check code doesn't know it

#
# Menu structure
#
MENUBAR=(
	(ALL, CASCADE, 'File', (
		(ALL, ENTRY, 'Open...', 'O', OPEN),
		(ALL, DYNAMICCASCADE, 'Open recent', OPEN_RECENT),
		(ALL, ENTRY, 'Close Window', 'W', CLOSE_WINDOW),
		(ALL, ENTRY, 'Close Document', None, CLOSE),
		(ALL, SEP,),
		(ALL, ENTRY, 'Preferences...', None, PREFERENCES),
		(ALL, SEP,),
		(DEBUG, CASCADE, 'Debug', (
			(DEBUG, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(DEBUG, TOGGLE, 'Enable call tracing', None, TRACE),
			(DEBUG, ENTRY, 'Enter debugger', None, DEBUG),
			(DEBUG, ENTRY, 'Crash', None, CRASH),
			(DEBUG, ENTRY, 'Show log/debug window', None, CONSOLE))),
		(DEBUG, SEP,),
		(ALL, ENTRY, 'Quit', 'Q', EXIT))),

	(ALL, CASCADE, 'Edit', (
		(ALL, ENTRY, 'Undo', 'Z', UNDO),
		(ALL, SEP,),
		(ALL, ENTRY, 'Cut', 'X', CUT),
		(ALL, ENTRY, 'Copy', 'C', COPY),
		(ALL, ENTRY, 'Paste', 'V', PASTE),
		(ALL, ENTRY, 'Clear', None, DELETE))),
		
	(ALL, CASCADE, 'Play', (
		(ALL, TOGGLE, 'Play', 'P', PLAY),
		(ALL, TOGGLE, 'Stop', 'H', STOP),
		(ALL, TOGGLE, 'Pause', 'B', PAUSE))),
		
	(ALL, CASCADE, 'Views', (
		(ALL, SPECIAL, 'Open documents', 'documents'),
		(ALL, SPECIAL, 'Open windows', 'windows'),
		(CMIF, SEP,),
		(CMIF, DYNAMICCASCADE, 'User groups', USERGROUPS),
		(CMIF, DYNAMICCASCADE, 'Channel visibility', CHANNELS),
		(ALL, SEP,),
		(ALL, ENTRY, 'View source', None, SOURCE),
		(ALL, ENTRY, 'View help window', '?', HELP))))
		
			
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
		
