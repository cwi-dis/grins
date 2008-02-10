__version__ = "$Id$"

#
# Commands, player version, ui
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
OPEN_RECENT:idc+2*m

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

CommandUI(HELP,IDUC_HELP)

# win32++
CommandUI(PASTE_DOCUMENT,IDUC_PASTEFILE)

CommandUI(CLOSE_ACTIVE_WINDOW,IDUC_CLOSE_WINDOW)

#
# MainDialog commands
#
CommandUI(OPEN,IDUC_OPENURL)
CommandUI(OPENFILE, IDUC_OPEN)
CommandUI(OPEN_RECENT,casc2ui[OPEN_RECENT])
CommandUI(CLOSE,IDUC_CLOSE)
CommandUI(RELOAD, IDUC_RESTORE)



#
# Player view commands
#
CommandUI(PLAY,IDUC_PLAY)
CommandUI(PAUSE,IDUC_PAUSE)
CommandUI(STOP,IDUC_STOP)
CommandUI(MAGIC_PLAY,IDUC_MAGIC_PLAY)
CommandUI(USERGROUPS, casc2ui[USERGROUPS])
CommandUI(CHANNELS, casc2ui[CHANNELS])


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
