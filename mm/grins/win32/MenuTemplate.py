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
		(LIGHT, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(LIGHT, ENTRY, '&Open URL...\tCtrl+L', 'O', OPEN),
		(LIGHT, DYNAMICCASCADE, 'Open recent', OPEN_RECENT),
		(LIGHT, ENTRY, '&Close Document', None, CLOSE),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Preferences...', None, PREFERENCES),
		(LIGHT|DBG, SEP,),
		(LIGHT|DBG, CASCADE, '&Debug', (
			(LIGHT|DBG, ENTRY, 'Dump &scheduler data', None, SCHEDDUMP),
			(LIGHT|DBG, TOGGLE, 'Enable call &tracing', None, TRACE),
			(LIGHT|DBG, ENTRY, 'Enter &debugger', None, DEBUG),
			(LIGHT|DBG, ENTRY, '&Abort', None, CRASH),
			(LIGHT|DBG, TOGGLE, 'Show &log/debug window', None, CONSOLE),
			)),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'E&xit', None, EXIT))),


	('&View', (
		(LIGHT, TOGGLE, '&Source', None, SOURCE),)),

	('&Play', (
		(LIGHT, ENTRY, '&Play\tCtrl+P', 'P', PLAY),
		(LIGHT, ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(LIGHT, ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(CMIF, SEP,),
		(CMIF, DYNAMICCASCADE, 'User &groups', USERGROUPS),
		(CMIF, DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),

	('&Window', (
		(LIGHT, ENTRY, 'Cl&ose', None, CLOSE_ACTIVE_WINDOW),)),

	('&Help', (
		(LIGHT, ENTRY, '&Contents', None, HELP_CONTENTS),
		(LIGHT, ENTRY, 'Context &Help', None, HELP),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))

MAIN_FRAME_POPUP = (
		(LIGHT, ENTRY, '&Paste document', None, PASTE_DOCUMENT),
		(LIGHT, SEP,),
		(LIGHT, ENTRY, '&Open...\tCtrl+O', 'O', OPEN),
		(LIGHT, ENTRY, '&Close document', None, CLOSE),
)
