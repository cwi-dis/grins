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
OPEN_URL=CommandID()
OPEN_FILE=CommandID()
TRACE=CommandID()
DEBUG=CommandID()
CONSOLE=CommandID()
EXIT=CommandID()
CLOSE=CommandID()
#
# TopLevel commands
#
PLAY=CommandID()
STOP=CommandID()
PAUSE=CommandID()

#
# Menu structure
#
MENUBAR=(
	('File', (
		(ENTRY, 'Open URL...', 'U', OPEN_URL),
		(ENTRY, 'Open...', 'O', OPEN_FILE),
		(ENTRY, 'Close', 'W', CLOSE_WINDOW),
		(SEP,),
		(ENTRY, 'Close document', None, CLOSE),
		(SEP,),
		(CASCADE, 'Debug', (
			(TOGGLE, 'Enable call tracing', None, TRACE),
			(ENTRY, 'Enter debugger', None, DEBUG),
			(ENTRY, 'Show log/debug window', None, CONSOLE))),
		(SEP,),
		(ENTRY, 'Quit', 'Q', EXIT))),

	('Edit', (
		(ENTRY, 'Undo', 'Z', UNDO),
		(ENTRY, 'Cut', 'X', CUT),
		(ENTRY, 'Copy', 'C', COPY),
		(ENTRY, 'Paste', 'V', PASTE))),
		
	('Play', (
		(TOGGLE, 'Play', 'P', PLAY),
		(TOGGLE, 'Stop', 'H', STOP),
		(TOGGLE, 'Pause', 'B', PAUSE))))
		
			
		
