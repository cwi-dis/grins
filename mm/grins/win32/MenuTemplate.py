#
# Command/menu mapping for the win32 GRiNS Player
#

from usercmd import *

# plus about cmd
from wndusercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)


MENUBAR=(
	('&File', (
		(ENTRY, 'Open...', 'O', OPEN),
		(ENTRY, 'Close Document', None, CLOSE),
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
		(ENTRY, 'Exit', 'x', EXIT))),


	('&View', (
		(TOGGLE, 'Source', '1', SOURCE),)),
		
	('&Play', (
		(TOGGLE, 'Play', 'P', PLAY),
		(TOGGLE, 'Pause', 'B', PAUSE),
		(TOGGLE, 'Stop', 'H', STOP),
		(SEP,),
		(DYNAMICCASCADE, 'Visible channels', CHANNELS),
		)),

	('&Window', (
		(ENTRY, 'Close', 'o', CLOSE_ACTIVE_WINDOW),)),
		
	('&Help', (
		(ENTRY, 'Help...', None, HELP),
		(SEP,),
		(ENTRY, 'About...', None, ABOUT_GRINS))))
			
		
