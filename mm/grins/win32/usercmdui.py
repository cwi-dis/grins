__version__ = "$Id$"

#
# Commands, player version, ui
#

""" @win32doc|usercmdui
Associates identifiers to commands.
For commands that have toolbar icons the identifiers
are predefined. For the rest are assigned identifiers
continously starting from the first avalaible value.
This value is taken from grinsRC and is automatically
updated by the resource editor.
This module creates and exports a
map from cmd classes to CommandUI instances that 
contain the identifier and the cascade commands ranges.
"""

from usercmd import *

# plus about cmd
from wndusercmd import *

import win32ui,win32con

# import resource ids for user cmds IDUC_<cmd class>
import grinsRC, afxres
from grinsRC import *

# set starting id for buttons without resources
idbegin=grinsRC._APS_NEXT_COMMAND_VALUE
idend=idbegin

# cascade commands ranges
m=100
idc=((idbegin+100)/m+1)*m
casc2ui={
CHANNELS:idc,
USERGROUPS:idc+m,
}
def get_cascade(id):
	global idc,m,casc2ui
	ind=id-id%m
	for c in casc2ui.keys():
		if casc2ui[c]==ind:return c


# map from cmd classes to CommandUI instances
class2ui={}

class CommandUI:
	def __init__(self,cmdcl,iduc=None):
		if iduc:
			self.id=iduc
			self.iduc=iduc
		else: 
			global idend
			self.id= idend
			self.iduc=None
			idend=idend+1
		class2ui[cmdcl]=self
			

#
# Global commands
#

CLOSE_WINDOW_UI=CommandUI(CLOSE_WINDOW)
HELP_UI=CommandUI(HELP,IDUC_HELP)
PREFERENCES_UI=CommandUI(PREFERENCES)

# win32++
HELP_CONTENTS_UI=CommandUI(HELP_CONTENTS)
GRINS_WEB_UI=CommandUI(GRINS_WEB)

ABOUT_GRINS_UI=CommandUI(ABOUT_GRINS)
CLOSE_ACTIVE_WINDOW_UI=CommandUI(CLOSE_ACTIVE_WINDOW,IDUC_CLOSE_WINDOW)
SELECT_CHARSET_UI=CommandUI(SELECT_CHARSET)


#
# MainDialog commands
#
OPEN_UI=CommandUI(OPEN,IDUC_OPEN)
TRACE_UI=CommandUI(TRACE)
DEBUG_UI=CommandUI(DEBUG)
CONSOLE_UI=CommandUI(CONSOLE)
SOURCE_UI=CommandUI(SOURCE)
CLOSE_UI=CommandUI(CLOSE,IDUC_CLOSE)
EXIT_UI=CommandUI(EXIT)



#
# Player view commands
#
PLAY_UI=CommandUI(PLAY,IDUC_PLAY)
PAUSE_UI=CommandUI(PAUSE,IDUC_PAUSE)
STOP_UI=CommandUI(STOP,IDUC_STOP)
MAGIC_PLAY_UI=CommandUI(MAGIC_PLAY)
USERGROUPS_UI=CommandUI(USERGROUPS,casc2ui[USERGROUPS])
CHANNELS_UI=CommandUI(CHANNELS,casc2ui[CHANNELS])
#CALCTIMING_UI=CommandUI(CALCTIMING)
CRASH_UI=CommandUI(CRASH)
SCHEDDUMP_UI=CommandUI(SCHEDDUMP)



