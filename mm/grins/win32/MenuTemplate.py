#
# Command/menu mapping for the win32 GRiNS Player
#

__version__ = "$Id$"

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

# plus about cmd
from wndusercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)

# Some commands are optional, depending on preference settings:
from flags import *

MENUBAR=(
	('&File', (
		(ALL, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(ALL, ENTRY, '&Open URL...\tCtrl+L', 'O', OPEN),
		(ALL, DYNAMICCASCADE, 'Open recent', OPEN_RECENT),
		(ALL, ENTRY, '&Close Document', None, CLOSE),
		(ALL, SEP,),
		(ALL, ENTRY, '&Preferences...', None, PREFERENCES),
		(DBG, SEP,),
		(DBG, CASCADE, '&Debug', (
			(ALL, ENTRY, 'Dump &scheduler data', None, SCHEDDUMP),
			(ALL, TOGGLE, 'Enable call &tracing', None, TRACE),
			(ALL, ENTRY, 'Enter &debugger', None, DEBUG),
			(ALL, ENTRY, '&Abort', None, CRASH),
			(ALL, TOGGLE, 'Show &log/debug window', None, CONSOLE),
			)),
		(ALL, SEP,),
		(ALL, ENTRY, 'E&xit', None, EXIT))),


	('&View', (
		(ALL, TOGGLE, '&Source', None, SOURCE),)),

	('&Play', (
		(ALL, ENTRY, '&Play\tCtrl+P', 'P', PLAY),
		(ALL, ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(ALL, ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(CMIF, SEP,),
		(CMIF, DYNAMICCASCADE, 'User &groups', USERGROUPS),
		(CMIF, DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),

	('&Window', (
		(ALL, ENTRY, 'Cl&ose', None, CLOSE_ACTIVE_WINDOW),)),

	('&Help', (
		(ALL, ENTRY, '&Contents', None, HELP_CONTENTS),
		(ALL, ENTRY, 'Context &Help', None, HELP),
		(ALL, SEP,),
		(ALL, ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(ALL, SEP,),
		(ALL, ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))

MAIN_FRAME_POPUP = (
		(ALL, ENTRY, '&Paste document', None, PASTE_DOCUMENT),
		(ALL, SEP,),
		(ALL, ENTRY, '&Open...\tCtrl+O', 'O', OPEN),
		(ALL, ENTRY, '&Close document', None, CLOSE),
)
