
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
UNDO_UI=CommandUI(UNDO,'Edit','Undo')
CUT_UI=CommandUI(CUT,'Edit','Cut')
COPY_UI=CommandUI(COPY,'Edit','Copy')
PASTE_UI=CommandUI(PASTE,'Edit','Paste')
DELETE_UI=CommandUI(DELETE,'Edit','Delete')
HELP_UI=CommandUI(HELP,'Help','Help',IDUC_HELP)


#
# MainDialog commands
#
NEW_DOCUMENT_UI=CommandUI(NEW_DOCUMENT,'File','New',IDUC_NEW_DOCUMENT)
OPEN_UI=CommandUI(OPEN,'File','Open...',IDUC_OPEN)
TRACE_UI=CommandUI(TRACE,'Debug','Trace')
DEBUG_UI=CommandUI(DEBUG,'Debug','Debug')
CONSOLE_UI=CommandUI(CONSOLE,'Debug','Show log')
SAVE_UI=CommandUI(SAVE,'File','Save\tCtrl+S',IDUC_SAVE)
SAVE_AS_UI=CommandUI(SAVE_AS,'File','Save As...')
RESTORE_UI=CommandUI(RESTORE,'File','Restore',IDUC_RESTORE)
SOURCE_UI=CommandUI(SOURCE,'View','Source')
CLOSE_UI=CommandUI(CLOSE,'File','Close',IDUC_CLOSE)
EXIT_UI=CommandUI(EXIT,'File','Exit',1)



#
# TopLevel commands
#
PLAYERVIEW_UI=CommandUI(PLAYERVIEW,'View','Player View')
HIERARCHYVIEW_UI=CommandUI(HIERARCHYVIEW,'View','Hierarchy View')
CHANNELVIEW_UI=CommandUI(CHANNELVIEW,'View','Channels View')
LINKVIEW_UI=CommandUI(LINKVIEW,'View','Link View')
LAYOUTVIEW_UI=CommandUI(LAYOUTVIEW,'View','Layout View')


#
# Player commands
#
PLAY_UI=CommandUI(PLAY,'Play','Play',IDUC_PLAY)
PAUSE_UI=CommandUI(PAUSE,'Play','Pause',IDUC_PAUSE)
STOP_UI=CommandUI(STOP,'Play','Stop',IDUC_STOP)
MAGIC_PLAY_UI=CommandUI(MAGIC_PLAY,'Play','Magic')
CHANNELS_UI=CommandUI(CHANNELS)
SYNCCV_UI=CommandUI(SYNCCV)
CRASH_UI=CommandUI(CRASH,'Debug','Crash GRiNS')
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
CANVAS_WIDTH_UI=CommandUI(CANVAS_WIDTH,'Canvas','Double  width')
CANVAS_HEIGHT_UI=CommandUI(CANVAS_HEIGHT,'Canvas','Double  height')
CANVAS_RESET_UI=CommandUI(CANVAS_RESET,'Canvas','Reset to fit')

INFO_UI=CommandUI(INFO)
ATTRIBUTES_UI=CommandUI(ATTRIBUTES)
ANCHORS_UI=CommandUI(ANCHORS)
CONTENT_UI=CommandUI(CONTENT)
PLAYNODE_UI=CommandUI(PLAYNODE)
PLAYFROM_UI=CommandUI(PLAYFROM)
PUSHFOCUS_UI=CommandUI(PUSHFOCUS)
FINISH_LINK_UI=CommandUI(FINISH_LINK) 
FINISH_ARC_UI=CommandUI(FINISH_ARC) 
THUMBNAIL_UI=CommandUI(THUMBNAIL)


#
# Channel view commands
#
NEW_CHANNEL_UI=CommandUI(NEW_CHANNEL)
TOGGLE_UNUSED_UI=CommandUI(TOGGLE_UNUSED)
TOGGLE_ARCS_UI=CommandUI(TOGGLE_ARCS)
NEXT_MINIDOC_UI=CommandUI(NEXT_MINIDOC)
PREV_MINIDOC_UI=CommandUI(PREV_MINIDOC) 
MOVE_CHANNEL_UI=CommandUI(MOVE_CHANNEL) 
COPY_CHANNEL_UI=CommandUI(COPY_CHANNEL) 
TOGGLE_ONOFF_UI=CommandUI(TOGGLE_ONOFF) 
HIGHLIGHT_UI=CommandUI(HIGHLIGHT) 
UNHIGHLIGHT_UI=CommandUI(UNHIGHLIGHT) 
SYNCARCS_UI=CommandUI(SYNCARCS)
ANCESTORS_UI=CommandUI(ANCESTORS)
SIBLINGS_UI=CommandUI(SIBLINGS)
DESCENDANTS_UI=CommandUI(DESCENDANTS)
LAYOUTS_UI=CommandUI(LAYOUTS)


#
# Layout view commands
#
NEW_LAYOUT_UI=CommandUI(NEW_LAYOUT)
REMOVE_CHANNEL_UI=CommandUI(REMOVE_CHANNEL)
ADD_CHANNEL_UI=CommandUI(ADD_CHANNEL)
RENAME_UI=CommandUI(RENAME)



