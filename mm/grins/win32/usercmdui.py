
#
# Commands, editor version, ui
#

from usercmd import *

import win32ui,win32con

# import resource ids for user cmds IDUC_<cmd class>
from grinsRC import *

# set starting id for buttons without resources
idbegin=1001 
id=idbegin

# for now import adorment preferences 
from adornpref import stdmenu,menuconfig

# map from cmd classes to CommandUI instances
class2ui={}

class CommandUI:
	def __init__(self,cmdcl,cat=None,dispstr=None,iduc=None,sep=0):
		if not cat:
			self.cat='Tools'
		else:
			self.cat=cat

		if not dispstr:
			self.dispstr= cmdcl.help
		else:
			self.dispstr = dispstr

		if iduc:
			self.id=iduc
			self.iduc=iduc
		else: 
			global id
			self.id= id
			self.iduc=None
			id=id+1
		if sep:
			stdmenu[self.cat].AppendMenu(win32con.MF_SEPARATOR,0,'')
		stdmenu[self.cat].AppendMenu(win32con.MF_STRING,self.id,self.dispstr)
		class2ui[cmdcl]=self
			

#
# Global commands
#

CLOSE_WINDOW_UI=CommandUI(CLOSE_WINDOW,'Window','Close')
HELP_UI=CommandUI(HELP,'Help','Help',IDUC_HELP)


#
# MainDialog commands
#
OPEN_UI=CommandUI(OPEN,'File','Open...',IDUC_OPEN)
TRACE_UI=CommandUI(TRACE,'Debug','Trace')
DEBUG_UI=CommandUI(DEBUG,'Debug','Debug')
CONSOLE_UI=CommandUI(CONSOLE,'Debug','Show log')
SOURCE_UI=CommandUI(SOURCE,'View','Source')
CLOSE_UI=CommandUI(CLOSE,'File','Close',IDUC_CLOSE)
EXIT_UI=CommandUI(EXIT,'File','Exit',1)



#
# Player view commands
#
PLAY_UI=CommandUI(PLAY,'Play','Play',IDUC_PLAY)
PAUSE_UI=CommandUI(PAUSE,'Play','Pause',IDUC_PAUSE)
STOP_UI=CommandUI(STOP,'Play','Stop',IDUC_STOP)
MAGIC_PLAY_UI=CommandUI(MAGIC_PLAY,'Play','Magic')
CHANNELS_UI=CommandUI(CHANNELS)
CALCTIMING_UI=CommandUI(CALCTIMING)
CRASH_UI=CommandUI(CRASH,'Debug','Crash GRiNS')
SCHEDDUMP_UI=CommandUI(SCHEDDUMP)



