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


MENUBAR=(
	('&File', (
		(ENTRY, '&Open...\tCtrl+O', 'O', OPEN),
		(ENTRY, '&Close Document', None, CLOSE),
		(SEP,),
		(ENTRY, '&Preferences...', None, PREFERENCES),
		(SEP,),
		(CASCADE, '&Debug', (
			(ENTRY, 'Dump &scheduler data', None, SCHEDDUMP),
			(TOGGLE, 'Enable call &tracing', None, TRACE),
			(ENTRY, 'Enter &debugger', None, DEBUG),
			(ENTRY, '&Abort', None, CRASH),
			(TOGGLE, 'Show &log/debug window', None, CONSOLE),
			)),
		(SEP,),
		(ENTRY, 'E&xit', None, EXIT))),


	('&View', (
		(TOGGLE, '&Source', None, SOURCE),)),
		
	('&Play', (
		(ENTRY, '&Play\tCtrl+P', 'P', PLAY),
		(ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(SEP,),
		(DYNAMICCASCADE, 'User &groups', USERGROUPS),
		(DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),

	('&Window', (
		(ENTRY, 'Cl&ose', None, CLOSE_ACTIVE_WINDOW),)),
		
	('&Help', (
		(ENTRY, '&Contents', None, HELP_CONTENTS),
		(ENTRY, 'Context &Help', None, HELP),
		(SEP,),
		(ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(SEP,),
		(ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))
		
MAIN_FRAME_POPUP = (
		(ENTRY, '&Paste document\tCtrl+Shift+V', None, PASTE_FILE),
		(SEP,),
		(ENTRY, '&Open...\tCtrl+O', 'O', OPEN),
		(ENTRY, '&Close document', None, CLOSE),
)
