__version__ = "$Id$"

#
# Template file for the application toolbars.
# The template is a list of toolbars. Each toolbar
# has a name, a menu-command-id (to show/hide it),
# a resource-id (of the toolbar resource with the bitmaps)
# and a list of "buttons".
# Each button has a type, command-id, and an icon-index
# (into the toolbar resource bitmap) for buttons or a width for
# separators.
# Type is one of the strings 'button', 'separator', or 'pulldown'.

import grinsRC
import usercmd
import wndusercmd
from ToolbarIcons import *

#
# This is a hack by Jack copied from the editor by Sjoerd. We need fixed ID values
# for the toolbars, because that is how their state
# is saved in the registry. However, I couldn't find
# a reasonable way to get these values into GRiNSRes.
# The values are magic and deduced from afxres.h and from
# the docktool example in the MSDN library.
IDW_TOOLBAR_GENERAL=0xe803
IDW_TOOLBAR_PLAYER=0xe804


class Button:
	def __init__(self, cmdid, iconindex):
		self.type = 'button'
		self.cmdid = cmdid
		self.arg = iconindex

class Separator:
	def __init__(self, width):
		self.type = 'separator'
		self.cmdid = None
		self.width = width

class Pulldown:
	def __init__(self, name, width=None):
		self.type = 'pulldown'
		self.name = name
		self.width = width

GENERAL_TEMPLATE = (
	('General', 'toolbar', 'docked', wndusercmd.TOOLBAR_GENERAL, IDW_TOOLBAR_GENERAL, grinsRC.IDR_TB_COMMON, 0, (
		Button(usercmd.OPENFILE, TBICON_OPENFILE),
		Button(usercmd.CLOSE, TBICON_CLOSE),
		Button(usercmd.RELOAD, TBICON_RESTORE),
		Separator(12),
		Button(usercmd.HELP, TBICON_HELP),
		)
	)
)

##PLAYER_TEMPLATE = (
##	('Player Controls', 'toolbar', 'docked', wndusercmd.TOOLBAR_PLAYER, IDW_TOOLBAR_PLAYER, grinsRC.IDR_TB_COMMON, 0, (
##		Button(usercmd.PLAY, TBICON_PLAY),
##		Button(usercmd.PAUSE, TBICON_PAUSE),
##		Button(usercmd.STOP, TBICON_STOP),
##		)
##	)
##)

TOOLBARS=[
	GENERAL_TEMPLATE,
##	PLAYER_TEMPLATE,
]

TOOLBARS.reverse()  # For now...
