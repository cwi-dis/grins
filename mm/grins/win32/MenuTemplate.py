#
# Command/menu mapping for the win32 GRiNS Player
#

__version__ = "$Id$"

# @win32doc|MenuTemplate
# Contains the specification for player menu in the
# following Grammar:
# # entry: <simple_entry> | <sep_entry> | <dyn_cascade_entry> | <CASCADE_ENTRY>
# # simple_entry: (ENTRY | TOGGLE, LABEL, SHORTCUT, ID)
# # sep_enty: (SEP,)
# # dyn_cascade_entry: (DYNAMICCASCADE, LABEL, ID)
# # cascade_entry: (CASCADE,LABEL,menu_spec_list)
# # menubar_entry: (LABEL,menu_spec_list)
# # menu_spec_list: list of entry
# # menubar_spec_list: list of menubar_entry
# # menu_exec_list: (MENU,menu_spec_list)
# where ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE are type constants.
# LABEL and and SHORTCUT are strings
# ID is either an integer or an object that can be maped to an integer

from usercmd import *

# plus about cmd
from wndusercmd import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)

# Some commands are optional, depending on preference settings:
from flags import *

MENUBAR=(
	('&File', (
		(FLAG_ALL, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(FLAG_ALL, ENTRY, 'Open &URL...\tCtrl+L', 'O', OPEN),
		(FLAG_ALL, DYNAMICCASCADE, 'Open &recent', OPEN_RECENT),
		(FLAG_ALL, ENTRY, 'R&eload', 'R', RELOAD),
		(FLAG_ALL, ENTRY, '&Close Document', None, CLOSE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Preferences...', None, PREFERENCES),
		(FLAG_DBG, SEP,),
		(FLAG_DBG, CASCADE, '&Debug', (
			(FLAG_DBG, ENTRY, 'Dump &scheduler data', None, SCHEDDUMP),
			(FLAG_DBG, TOGGLE, 'Enable call &tracing', None, TRACE),
			(FLAG_DBG, ENTRY, 'Enter &debugger', None, DEBUG),
			(FLAG_DBG, ENTRY, '&Abort', None, CRASH),
			(FLAG_DBG, TOGGLE, 'Show &log/debug window', None, CONSOLE),
			)),
		(FLAG_DBG, SEP,),
		(FLAG_ALL, ENTRY, 'C&heck for Ambulant update...', None, CHECKVERSION),
		(FLAG_ALL, SEP,),
##		(FLAG_ALL, ENTRY, 'Choose skin...', None, CHOOSESKIN),
##		(FLAG_ALL, ENTRY, 'Choose components config file...', None, CHOOSECOMPONENTS)
##		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'E&xit', None, EXIT))),


	('&View', (
		(FLAG_ALL, CASCADE, 'T&oolbars', (
			(FLAG_ALL, ENTRY, '&General', None, TOOLBAR_GENERAL),
##			(FLAG_ALL, ENTRY, '&Player Controls', None, TOOLBAR_PLAYER),
			(FLAG_ALL, ENTRY, '&Player Controls', None, PLAYER_PANEL),
			)),
		(FLAG_ALL, TOGGLE, '&Source', None, SOURCEVIEW))),

	('&Play', (
		(FLAG_ALL, ENTRY, '&Play\tCtrl+P', 'P', PLAY),
		(FLAG_ALL, ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(FLAG_ALL, ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(FLAG_BOSTON|FLAG_CMIF, SEP,),
		(FLAG_BOSTON, DYNAMICCASCADE, 'Custom &tests', USERGROUPS),
		(FLAG_CMIF, DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),

	('&Window', (
		(FLAG_ALL, ENTRY, 'Cl&ose', None, CLOSE_ACTIVE_WINDOW),)),

	('&Help', (
		(FLAG_ALL, ENTRY, '&Contents', None, HELP_CONTENTS),
##		(FLAG_ALL, ENTRY, 'Context &Help', None, HELP),
##		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Ambulant on the &Web', None,GRINS_WEB),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&About Ambulant...', None, ABOUT_GRINS))))

MAIN_FRAME_POPUP = (
		(FLAG_ALL, ENTRY, '&Paste document', None, PASTE_DOCUMENT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Open...\tCtrl+O', 'O', OPEN),
		(FLAG_ALL, ENTRY, '&Close document', None, CLOSE),
)
