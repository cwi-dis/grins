__version__ = "$Id$"

#
# Menubar template for the Mac player
#
from usercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE, SPECIAL] = range(6)

from flags import *
#
# Commands that we know are not implemented on the mac:
UNUSED_COMMANDS=(MAGIC_PLAY,)   # Is implemented, but the check code doesn't know it

#
# Menu structure
#
MENUBAR=(
        (FLAG_ALL, CASCADE, 'File', (
                (FLAG_ALL, ENTRY, 'Open...', 'O', OPENFILE),
                (FLAG_ALL, ENTRY, 'Open URL...', 'L', OPEN),
                (FLAG_ALL, DYNAMICCASCADE, 'Open recent', OPEN_RECENT),
                (FLAG_ALL, ENTRY, 'Close Window', 'W', CLOSE_WINDOW),
                (FLAG_ALL, ENTRY, 'Close Document', None, CLOSE),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Preferences...', None, PREFERENCES),
                (FLAG_ALL, SEP,),
                (FLAG_DBG, CASCADE, 'Debug', (
                        (FLAG_DBG, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
                        (FLAG_DBG, TOGGLE, 'Enable call tracing', None, TRACE),
                        (FLAG_DBG, ENTRY, 'Enter debugger', None, DEBUG),
                        (FLAG_DBG, ENTRY, 'Crash', None, CRASH),
                        (FLAG_DBG, ENTRY, 'Show log/debug window', None, CONSOLE))),
                (FLAG_DBG, SEP,),
                (FLAG_ALL, ENTRY, 'Check for Player update...', None, CHECKVERSION),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Quit', 'Q', EXIT))),

        (FLAG_ALL, CASCADE, 'Edit', (
                (FLAG_ALL, ENTRY, 'Undo', 'Z', UNDO),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
                (FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
                (FLAG_ALL, ENTRY, 'Paste', 'V', PASTE),
                (FLAG_ALL, ENTRY, 'Clear', None, DELETE))),

        (FLAG_ALL, CASCADE, 'Play', (
                (FLAG_ALL, TOGGLE, 'Play', 'P', PLAY),
                (FLAG_ALL, TOGGLE, 'Stop', 'H', STOP),
                (FLAG_ALL, TOGGLE, 'Pause', 'B', PAUSE),
                (FLAG_CMIF|FLAG_BOSTON, SEP,),
                (FLAG_BOSTON, DYNAMICCASCADE, 'Custom tests', USERGROUPS),
                (FLAG_CMIF, DYNAMICCASCADE, 'Channel visibility', CHANNELS))),

        (FLAG_ALL, CASCADE, 'Views', (
                (FLAG_ALL, SPECIAL, 'Open documents', 'documents'),
                (FLAG_ALL, SPECIAL, 'Open windows', 'windows'),
                (FLAG_ALL, SEP,),
                (FLAG_ALL, ENTRY, 'View source', None, SOURCEVIEW),
                (FLAG_ALL, ENTRY, 'View help page', '?', HELP))))


#
# Adornments
#
PLAYER_ADORNMENTS = {
        'toolbar': (
                (TOGGLE, 1001, STOP),
                (TOGGLE, 1501, PLAY),
                (TOGGLE, 2001, PAUSE),
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
TOOLBAR=(None, 66, 24)
