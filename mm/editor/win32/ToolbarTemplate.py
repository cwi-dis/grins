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
	def __init__(self):
		self.type = 'pulldown'
		self.cmdid = None
		self.arg = None

GENERAL_TEMPLATE = (
	('General', wndusercmd.TOOLBAR_GENERAL, grinsRC.IDR_GRINSED, (
		Button(usercmd.NEW_DOCUMENT, 0),
		Separator(6),
		Button(usercmd.OPENFILE, 1),
		Button(usercmd.SAVE, 2),
		Separator(6),
		Button(usercmd.RESTORE, 6),
		Button(usercmd.CLOSE, 7),
		Separator(6),
		Button(wndusercmd.CLOSE_ACTIVE_WINDOW, 11),
		Separator(12),
		Button(usercmd.CANVAS_ZOOM_IN, 12),
		Button(usercmd.CANVAS_ZOOM_OUT, 13),
		Separator(12),
		Button(usercmd.HELP, 9),
		Pulldown(),
		)
	)
)

FRAME_TEMPLATE = (
	('General', wndusercmd.TOOLBAR_GENERAL, grinsRC.IDR_GRINSED, (
		Button(usercmd.NEW_DOCUMENT, 0),
		Separator(6),
		Button(usercmd.OPENFILE, 1),
		Button(usercmd.SAVE, 2),
		)
	)
)
XXPLAYER_TEMPLATE = (
	('Player Controls', wndusercmd.TOOLBAR_PLAYER, grinsRC.IDR_TB_PLAYER, (
		Button(usercmd.PLAY, 0),
		Button(usercmd.PAUSE, 1),
		Button(usercmd.STOP, 2),
		)
	)
)

TOOLBARS=[
	GENERAL_TEMPLATE,
	XXPLAYER_TEMPLATE
]
