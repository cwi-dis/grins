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

# map from cmd classes to CommandUI instances
class2ui={}



# cascade commands ranges
m=100
idc=((idbegin+100)/m+1)*m
casc2ui={
SYNCARCS:idc,
LAYOUTS:idc+1*m,
CHANNELS:idc+2*m,
USERGROUPS:idc+3*m,
OPEN_RECENT:idc+4*m,
}
def get_cascade(id):
	global idc,m,casc2ui
	ind=id-id%m
	for c in casc2ui.keys():
		if casc2ui[c]==ind:return c
	
idend=idc + len(casc2ui)*m

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

CommandUI(CLOSE_WINDOW)
CommandUI(UNDO,IDUC_UNDO)
CommandUI(CUT,IDUC_CUT)
CommandUI(COPY,IDUC_COPY)
CommandUI(PASTE,IDUC_PASTE)
CommandUI(DELETE,IDUC_DELETE)
CommandUI(HELP,IDUC_HELP)
CommandUI(PREFERENCES)

# win32++
CommandUI(HELP_CONTENTS)
CommandUI(GRINS_WEB)
CommandUI(PASTE_DOCUMENT)
CommandUI(PASTE_FILE)

CommandUI(CASCADE_WNDS,afxres.ID_WINDOW_CASCADE)
CommandUI(TILE_HORZ,afxres.ID_WINDOW_TILE_HORZ)
CommandUI(TILE_VERT,afxres.ID_WINDOW_TILE_VERT)
CommandUI(ABOUT_GRINS)
CommandUI(CLOSE_ACTIVE_WINDOW,IDUC_CLOSE_WINDOW)
CommandUI(SELECT_CHARSET)

#
# MainDialog commands
#
CommandUI(NEW_DOCUMENT,IDUC_NEW_DOCUMENT)
CommandUI(OPEN,IDUC_OPENURL)
CommandUI(OPENFILE, IDUC_OPEN)
CommandUI(OPEN_RECENT,casc2ui[OPEN_RECENT])
CommandUI(TRACE)
CommandUI(DEBUG)
CommandUI(CONSOLE)
CommandUI(SAVE,IDUC_SAVE)
CommandUI(SAVE_AS)
CommandUI(RESTORE,IDUC_RESTORE)
CommandUI(CLOSE,IDUC_CLOSE)
CommandUI(EXIT)
CommandUI(PROPERTIES)
CommandUI(EDITSOURCE)
#
# TopLevel commands
#
CommandUI(PLAYERVIEW, IDUC_PLAYER)
CommandUI(HIERARCHYVIEW, IDUC_HVIEW)
CommandUI(CHANNELVIEW, IDUC_CVIEW)
CommandUI(LINKVIEW)
CommandUI(LAYOUTVIEW, IDUC_LAYOUT)
#CommandUI(TEMPORALVIEW)
CommandUI(USERGROUPVIEW)
CommandUI(SOURCEVIEW)
#
CommandUI(HIDE_PLAYERVIEW)
CommandUI(HIDE_HIERARCHYVIEW)
CommandUI(HIDE_CHANNELVIEW)
CommandUI(HIDE_LINKVIEW)
CommandUI(HIDE_LAYOUTVIEW)
CommandUI(HIDE_USERGROUPVIEW)
CommandUI(HIDE_SOURCE)
CommandUI(HIDE_LAYOUTVIEW2)
#CommandUI(HIDE_TEMPORALVIEW)
CommandUI(HIDE_SOURCEVIEW)

#
# Player commands
#
CommandUI(TB_PLAY,IDUC_PLAY)
CommandUI(TB_PAUSE,IDUC_PAUSE)
CommandUI(TB_STOP,IDUC_STOP)
CommandUI(MAGIC_PLAY,IDUC_MAGIC_PLAY)
CommandUI(CHANNELS,casc2ui[CHANNELS])
CommandUI(USERGROUPS,casc2ui[USERGROUPS])
CommandUI(SYNCCV)
CommandUI(CRASH)
CommandUI(SCHEDDUMP)


#
# Hierarchy view commands
#
CommandUI(PASTE_BEFORE)
##PASTE_AFTER_UI=CommandUI(PASTE_AFTER)
#PASTE_AFTER_UI=PASTE_UI

CommandUI(PASTE_UNDER)

CommandUI(NEW_BEFORE)
CommandUI(NEW_BEFORE_IMAGE)
CommandUI(NEW_BEFORE_TEXT)
CommandUI(NEW_BEFORE_SOUND)
CommandUI(NEW_BEFORE_VIDEO)
CommandUI(NEW_BEFORE_SLIDESHOW)
CommandUI(NEW_AFTER)
CommandUI(NEW_AFTER_IMAGE)
CommandUI(NEW_AFTER_TEXT)
CommandUI(NEW_AFTER_SOUND)
CommandUI(NEW_AFTER_VIDEO)
CommandUI(NEW_AFTER_SLIDESHOW)
CommandUI(NEW_UNDER)
CommandUI(NEW_UNDER_IMAGE)
CommandUI(NEW_UNDER_TEXT)
CommandUI(NEW_UNDER_SOUND)
CommandUI(NEW_UNDER_VIDEO)
CommandUI(NEW_UNDER_SLIDESHOW)
CommandUI(NEW_SEQ)
CommandUI(NEW_PAR)
CommandUI(NEW_SWITCH)
CommandUI(EXPAND,IDUC_EXPAND)
CommandUI(EXPANDALL)
CommandUI(COLLAPSEALL)
CommandUI(TOPARENT,IDUC_TOPARENT)
CommandUI(TOCHILD,IDUC_TOCHILD)
CommandUI(NEXTSIBLING,IDUC_NEXTSIBLING)
CommandUI(PREVSIBLING,IDUC_PREVSIBLING)


#
# Command to hierarchy/channel view
#
CommandUI(CANVAS_WIDTH)
CommandUI(CANVAS_HEIGHT)
CommandUI(CANVAS_RESET)

CommandUI(INFO,IDUC_INFO)
CommandUI(ATTRIBUTES,IDUC_ATTRIBUTES)
CommandUI(ANCHORS)
CommandUI(CONTENT)
CommandUI(PLAYNODE)
CommandUI(PLAYFROM)
CommandUI(PUSHFOCUS)
CommandUI(CREATEANCHOR)
CommandUI(FINISH_LINK) 
CommandUI(FINISH_ARC) 
CommandUI(THUMBNAIL)
CommandUI(PLAYABLE)
CommandUI(TIMESCALE)


#
# Channel view commands
#
CommandUI(NEW_REGION)
CommandUI(NEW_TOPLAYOUT)
CommandUI(TOGGLE_UNUSED)
CommandUI(TOGGLE_ARCS)
CommandUI(TOGGLE_BWSTRIP)
CommandUI(MOVE_REGION) 
CommandUI(COPY_REGION) 
CommandUI(TOGGLE_ONOFF) 
CommandUI(HIGHLIGHT) 
CommandUI(UNHIGHLIGHT) 
CommandUI(SYNCARCS,casc2ui[SYNCARCS])
CommandUI(LAYOUTS,casc2ui[LAYOUTS])
CommandUI(BANDWIDTH_14K4)
CommandUI(BANDWIDTH_28K8)
CommandUI(BANDWIDTH_ISDN)
CommandUI(BANDWIDTH_T1)
CommandUI(BANDWIDTH_LAN)
CommandUI(BANDWIDTH_OTHER)

#
# Layout view commands
#
CommandUI(NEW_LAYOUT)
CommandUI(REMOVE_REGION)
CommandUI(ADD_REGION)
CommandUI(RENAME)

# The temporal view specific commands..
CommandUI(CANVAS_ZOOM_IN, IDUC_CANVAS_ZOOM_IN)
CommandUI(CANVAS_ZOOM_OUT, IDUC_CANVAS_ZOOM_OUT)

#
CommandUI(SHOWALLPROPERTIES)
#
# Add the rest without a predefined id
# 
#
def addui(cmdmod):
	for s in dir(cmdmod):
		a=getattr(cmdmod,s)
		if type(a) == type(cmdmod._CommandBase):
			if a.__name__ != '_CommandBase' and a.__name__ != '_DynamicCascade':
				if not class2ui.has_key(a):
					CommandUI(a)

import usercmd, wndusercmd
addui(usercmd)
addui(wndusercmd)
