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


# import resource ids for user cmds IDUC_<cmd class>
import grinsRC

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

#
# MainDialog commands
#
CommandUI(OPENFILE, grinsRC.IDM_OPEN)
CommandUI(CLOSE, grinsRC.IDM_CLOSE)
CommandUI(CHOOSESKIN, grinsRC.IDM_SKIN)
CommandUI(EXIT, grinsRC.IDM_EXIT)


#
# Player view commands
#
CommandUI(PLAY,grinsRC.IDM_PLAY)
CommandUI(PAUSE,grinsRC.IDM_PAUSE)
CommandUI(STOP,grinsRC.IDM_STOP)

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

