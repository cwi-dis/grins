__version__ = "$Id$"

#
# Commands, editor version, ui
#

# @win32doc|usercmdui
# Associates identifiers to commands.
# For commands that have toolbar icons the identifiers
# are predefined. For the rest are assigned identifiers
# continously starting from the first avalaible value.
# This value is taken from grinsRC and is automatically
# updated by the resource editor.
# This module creates and exports a map from cmd classes 
# to CommandUI instances that contain the identifier and 
# the cascade commands ranges.

#
# public interface
#

def usercmd2id(cmdcl):
	if class2ui.has_key(cmdcl):
		return class2ui[cmdcl].id
	else: 
		return 0

def getusercmds():
	return class2ui.keys()

def id2usercmd(id):
	for cmd, cmdui in class2ui.items():
		if cmdui.id == id:
			return cmd
	return None

def getcmdids():
	L = []
	for cmdui in class2ui.values():
		L.append(cmdui.id)
	return L


################################
# Private implementation

from usercmd import *

# plus wnds arrange cmds
from wndusercmd import *

# import resource ids for user cmds IDUC_<cmd class>
import grinsRC, afxres

from grinsRC import *

# set starting id for buttons without resources
idbegin = grinsRC._APS_NEXT_COMMAND_VALUE

# map from cmd classes to CommandUI instances
class2ui={}

# cascade commands ranges
m=20
idc=((idbegin+100)/m+1)*m
casc2ui={
LAYOUTS:idc+1*m,
CHANNELS:idc+2*m,
USERGROUPS:idc+3*m,
OPEN_RECENT:idc+4*m,
}

# this is currently also public
def get_cascade(id):
	global idc, m, casc2ui
	ind=id-id%m
	for c in casc2ui.keys():
		if casc2ui[c]==ind:
			return c
	
idend=idc + (len(casc2ui)+1)*m

class CommandUI:
	def __init__(self, cmdcl, iduc=None):
		if iduc:
			self.id=iduc
			self.iduc=iduc
		else: 
			global idend
			self.id = idend
			self.iduc = None
			idend = idend + 1
		class2ui[cmdcl] = self	

#
# Global commands
#

CommandUI(UNDO,IDUC_UNDO)
CommandUI(REDO,IDUC_REDO)
CommandUI(CUT,IDUC_CUT)
CommandUI(COPY,IDUC_COPY)
CommandUI(PASTE,IDUC_PASTE)
CommandUI(DELETE,IDUC_DELETE)
CommandUI(HELP,IDUC_HELP)

CommandUI(FIND,IDUC_FIND)
CommandUI(FINDNEXT,IDUC_FINDNEXT)
CommandUI(REPLACE,IDUC_REPLACE)

CommandUI(ZOOMIN, IDUC_ZOOMIN)
CommandUI(ZOOMOUT, IDUC_ZOOMOUT)

# win32++

CommandUI(CASCADE_WNDS,afxres.ID_WINDOW_CASCADE)
CommandUI(TILE_HORZ,afxres.ID_WINDOW_TILE_HORZ)
CommandUI(TILE_VERT,afxres.ID_WINDOW_TILE_VERT)
CommandUI(CLOSE_ACTIVE_WINDOW,IDUC_CLOSE_WINDOW)


#
# MainDialog commands
#
CommandUI(NEW_DOCUMENT,IDUC_NEW_DOCUMENT)
CommandUI(OPEN,IDUC_OPENURL)
CommandUI(OPENFILE, IDUC_OPEN)
CommandUI(OPEN_RECENT,casc2ui[OPEN_RECENT])
CommandUI(SAVE,IDUC_SAVE)
CommandUI(RESTORE,IDUC_RESTORE)
CommandUI(CLOSE,IDUC_CLOSE)

#
# TopLevel commands
#
CommandUI(PLAYERVIEW, IDUC_PLAYER)
CommandUI(HIERARCHYVIEW, IDUC_HVIEW)
CommandUI(LAYOUTVIEW2, IDUC_LAYOUT)
CommandUI(SOURCEVIEW, IDUC_SOURCE)


#
# Player commands
#
CommandUI(PLAY,IDUC_PLAY)
CommandUI(PAUSE,IDUC_PAUSE)
CommandUI(STOP,IDUC_STOP)
CommandUI(MAGIC_PLAY,IDUC_MAGIC_PLAY)
CommandUI(CHANNELS,casc2ui[CHANNELS])
CommandUI(USERGROUPS,casc2ui[USERGROUPS])


#
# Hierarchy view commands
#
CommandUI(TOPARENT,IDUC_TOPARENT)
CommandUI(TOCHILD,IDUC_TOCHILD)
CommandUI(NEXTSIBLING,IDUC_NEXTSIBLING)
CommandUI(PREVSIBLING,IDUC_PREVSIBLING)
CommandUI(MARK, IDUC_MARK)

CommandUI(DRAG_PAR, IDUC_PAR)
CommandUI(DRAG_SEQ, IDUC_SEQ)
CommandUI(DRAG_SWITCH, IDUC_SWITCH)
CommandUI(DRAG_EXCL, IDUC_EXCL)
CommandUI(DRAG_PRIO, IDUC_PRIO)
CommandUI(DRAG_MEDIA, IDUC_MEDIA)
CommandUI(DRAG_ANIMATE, IDUC_ANIMATE)
CommandUI(DRAG_BRUSH, IDUC_BRUSH)
CommandUI(DRAG_REGION, IDUC_REGION)
CommandUI(DRAG_TOPLAYOUT, IDUC_TOPLAYOUT)
#
# Command to hierarchy/channel view
#
CommandUI(ATTRIBUTES,IDUC_ATTRIBUTES)
CommandUI(CREATEANCHOR, IDUC_CREATE_ANCHOR)
CommandUI(CREATEANCHOREXTENDED, IDUC_CREATE_ANCHOREXTENDED)
CommandUI(CREATEANCHOR_CONTEXT, IDUC_CREATE_ANCHOR_CONTEXT)
CommandUI(CREATEANCHOR_BROWSER, IDUC_CREATE_ANCHOR_BROWSER)
CommandUI(FINISH_LINK, IDUC_FINISH_LINK)
CommandUI(CREATE_EVENT_SOURCE, IDUC_EVENT_SOURCE)
CommandUI(CREATE_BEGIN_EVENT, IDUC_BEGIN_EVENT)
CommandUI(CREATE_END_EVENT, IDUC_END_EVENT)
#
# Channel view commands
#
CommandUI(LAYOUTS, casc2ui[LAYOUTS])

#
# Layout view commands
#
CommandUI(ALIGN_LEFT, IDUC_ALIGN_LEFT)
CommandUI(ALIGN_CENTER, IDUC_ALIGN_CENTER)
CommandUI(ALIGN_RIGHT, IDUC_ALIGN_RIGHT)
CommandUI(ALIGN_TOP, IDUC_ALIGN_TOP)
CommandUI(ALIGN_MIDDLE, IDUC_ALIGN_MIDDLE)
CommandUI(ALIGN_BOTTOM, IDUC_ALIGN_BOTTOM)
CommandUI(DISTRIBUTE_HORIZONTALLY, IDUC_DISTRIBUTE_HORIZONTALLY)
CommandUI(DISTRIBUTE_VERTICALLY, IDUC_DISTRIBUTE_VERTICALLY)

#

#
# Add the rest without a predefined id
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
