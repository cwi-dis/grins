__version__ = "$Id$"

#
# Commands, editor version, ui
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

# plus wnds arrange cmds
from wndusercmd import *


import win32ui,win32con

# import resource ids for user cmds IDUC_<cmd class>
import grinsRC, afxres
from grinsRC import *

# set starting id for buttons without resources
idbegin=grinsRC._APS_NEXT_COMMAND_VALUE
idend=idbegin

# map from cmd classes to CommandUI instances
class2ui={}



# cascade commands ranges
m=100
idc=((idbegin+100)/m+1)*m
casc2ui={
SYNCARCS:idc,
ANCESTORS:idc+m,
DESCENDANTS:idc+2*m,
SIBLINGS:idc+3*m,
LAYOUTS:idc+4*m,
CHANNELS:idc+5*m,
USERGROUPS:idc+6*m,
}
def get_cascade(id):
	global idc,m,casc2ui
	ind=id-id%m
	for c in casc2ui.keys():
		if casc2ui[c]==ind:return c
	

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
UNDO_UI=CommandUI(UNDO,IDUC_UNDO)
CUT_UI=CommandUI(CUT,IDUC_CUT)
COPY_UI=CommandUI(COPY,IDUC_COPY)
PASTE_UI=CommandUI(PASTE,IDUC_PASTE)
DELETE_UI=CommandUI(DELETE,IDUC_DELETE)
HELP_UI=CommandUI(HELP,IDUC_HELP)
PREFERENCES_UI=CommandUI(PREFERENCES)

# win32++
HELP_CONTENTS_UI=CommandUI(HELP_CONTENTS)
GRINS_WEB_UI=CommandUI(GRINS_WEB)

CASCADE_WNDS_UI=CommandUI(CASCADE_WNDS,afxres.ID_WINDOW_CASCADE)
TILE_HORZ_UI=CommandUI(TILE_HORZ,afxres.ID_WINDOW_TILE_HORZ)
TILE_VERT_UI=CommandUI(TILE_VERT,afxres.ID_WINDOW_TILE_VERT)
ABOUT_GRINS_UI=CommandUI(ABOUT_GRINS)
CLOSE_ACTIVE_WINDOW_UI=CommandUI(CLOSE_ACTIVE_WINDOW,IDUC_CLOSE_WINDOW)
SELECT_CHARSET_UI=CommandUI(SELECT_CHARSET)

CONTENT_OPEN_REG_UI=CommandUI(CONTENT_OPEN_REG)
CONTENT_EDIT_REG_UI=CommandUI(CONTENT_EDIT_REG)

#
# MainDialog commands
#
NEW_DOCUMENT_UI=CommandUI(NEW_DOCUMENT,IDUC_NEW_DOCUMENT)
OPEN_UI=CommandUI(OPEN,IDUC_OPEN)
TRACE_UI=CommandUI(TRACE)
DEBUG_UI=CommandUI(DEBUG)
CONSOLE_UI=CommandUI(CONSOLE)
SAVE_UI=CommandUI(SAVE,IDUC_SAVE)
SAVE_AS_UI=CommandUI(SAVE_AS)
RESTORE_UI=CommandUI(RESTORE,IDUC_RESTORE)
CLOSE_UI=CommandUI(CLOSE,IDUC_CLOSE)
EXIT_UI=CommandUI(EXIT)



#
# TopLevel commands
#
PLAYERVIEW_UI=CommandUI(PLAYERVIEW, IDUC_PLAYER)
HIERARCHYVIEW_UI=CommandUI(HIERARCHYVIEW, IDUC_HVIEW)
CHANNELVIEW_UI=CommandUI(CHANNELVIEW, IDUC_CVIEW)
LINKVIEW_UI=CommandUI(LINKVIEW)
LAYOUTVIEW_UI=CommandUI(LAYOUTVIEW, IDUC_LAYOUT)
USERGROUPVIEW_UI=CommandUI(USERGROUPVIEW)
SOURCE_UI=CommandUI(SOURCE)


#
# Player commands
#
PLAY_UI=CommandUI(PLAY,IDUC_PLAY)
PAUSE_UI=CommandUI(PAUSE,IDUC_PAUSE)
STOP_UI=CommandUI(STOP,IDUC_STOP)
MAGIC_PLAY_UI=CommandUI(MAGIC_PLAY,IDUC_MAGIC_PLAY)
CHANNELS_UI=CommandUI(CHANNELS,casc2ui[CHANNELS])
USERGROUPS_UI=CommandUI(USERGROUPS,casc2ui[USERGROUPS])
SYNCCV_UI=CommandUI(SYNCCV)
CRASH_UI=CommandUI(CRASH)
SCHEDDUMP_UI=CommandUI(SCHEDDUMP)


#
# Hierarchy view commands
#
PASTE_BEFORE_UI=CommandUI(PASTE_BEFORE)
PASTE_AFTER_UI=CommandUI(PASTE_AFTER)
PASTE_UNDER_UI=CommandUI(PASTE_UNDER)
NEW_BEFORE_UI=CommandUI(NEW_BEFORE)
NEW_AFTER_UI=CommandUI(NEW_AFTER)
NEW_UNDER_UI=CommandUI(NEW_UNDER)
NEW_SEQ_UI=CommandUI(NEW_SEQ)
NEW_PAR_UI=CommandUI(NEW_PAR)
NEW_CHOICE_UI=CommandUI(NEW_CHOICE)
NEW_ALT_UI=CommandUI(NEW_ALT)
ZOOMIN_UI=CommandUI(ZOOMIN)
ZOOMOUT_UI=CommandUI(ZOOMOUT)
ZOOMHERE_UI=CommandUI(ZOOMHERE)


#
# Command to hierarchy/channel view
#
CANVAS_WIDTH_UI=CommandUI(CANVAS_WIDTH)
CANVAS_HEIGHT_UI=CommandUI(CANVAS_HEIGHT)
CANVAS_RESET_UI=CommandUI(CANVAS_RESET)

INFO_UI=CommandUI(INFO)
ATTRIBUTES_UI=CommandUI(ATTRIBUTES)
ANCHORS_UI=CommandUI(ANCHORS)
CONTENT_UI=CommandUI(CONTENT)
PLAYNODE_UI=CommandUI(PLAYNODE)
PLAYFROM_UI=CommandUI(PLAYFROM)
PUSHFOCUS_UI=CommandUI(PUSHFOCUS)
CREATEANCHOR_UI=CommandUI(CREATEANCHOR)
FINISH_LINK_UI=CommandUI(FINISH_LINK) 
FINISH_ARC_UI=CommandUI(FINISH_ARC) 
THUMBNAIL_UI=CommandUI(THUMBNAIL)


#
# Channel view commands
#
NEW_CHANNEL_UI=CommandUI(NEW_CHANNEL)
TOGGLE_UNUSED_UI=CommandUI(TOGGLE_UNUSED)
TOGGLE_ARCS_UI=CommandUI(TOGGLE_ARCS)
TOGGLE_BWSTRIP_UI=CommandUI(TOGGLE_BWSTRIP)
NEXT_MINIDOC_UI=CommandUI(NEXT_MINIDOC)
PREV_MINIDOC_UI=CommandUI(PREV_MINIDOC) 
MOVE_CHANNEL_UI=CommandUI(MOVE_CHANNEL) 
COPY_CHANNEL_UI=CommandUI(COPY_CHANNEL) 
TOGGLE_ONOFF_UI=CommandUI(TOGGLE_ONOFF) 
HIGHLIGHT_UI=CommandUI(HIGHLIGHT) 
UNHIGHLIGHT_UI=CommandUI(UNHIGHLIGHT) 
SYNCARCS_UI=CommandUI(SYNCARCS,casc2ui[SYNCARCS])
ANCESTORS_UI=CommandUI(ANCESTORS,casc2ui[ANCESTORS])
SIBLINGS_UI=CommandUI(SIBLINGS,casc2ui[SIBLINGS])
DESCENDANTS_UI=CommandUI(DESCENDANTS,casc2ui[DESCENDANTS])
LAYOUTS_UI=CommandUI(LAYOUTS,casc2ui[LAYOUTS])


#
# Layout view commands
#
NEW_LAYOUT_UI=CommandUI(NEW_LAYOUT)
REMOVE_CHANNEL_UI=CommandUI(REMOVE_CHANNEL)
ADD_CHANNEL_UI=CommandUI(ADD_CHANNEL)
RENAME_UI=CommandUI(RENAME)



