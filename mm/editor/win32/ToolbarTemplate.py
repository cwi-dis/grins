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
#
# Quick instructions on adding a toolbar:
# - Make sure all commands have their IDUC_ equivalent in usercmdui.
# - Create the toolbar and the buttons in the VC++ resource editor,
#   name the bmp file res/tb_xxx.bmp, name the resource IDR_TB_XXX.
# - Add the TOOLBAR_XXX command to wndusercmd and MenuTemplate
# - Add the toolbar template here
# - Add the template to TOOLBARS (at the bottom of this file).
#

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
	def __init__(self, name, width=None):
		self.type = 'pulldown'
		self.name = name
		self.width = width

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
		Separator(12),
		Pulldown('Bitrate'),
		Pulldown('Language'),
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
PLAYER_TEMPLATE = (
	('Player Controls', wndusercmd.TOOLBAR_PLAYER, grinsRC.IDR_TB_PLAYER, (
		Button(usercmd.PLAY, 0),
		Button(usercmd.PAUSE, 1),
		Button(usercmd.STOP, 2),
		)
	)
)

ALIGN_TEMPLATE = (
	('Region alignment', wndusercmd.TOOLBAR_ALIGNMENT, grinsRC.IDR_TB_ALIGNMENT, (
		Button(usercmd.ALIGN_LEFT, 0),
		Button(usercmd.ALIGN_CENTER, 1),
		Button(usercmd.ALIGN_RIGHT, 2),
		Separator(6),
		Button(usercmd.ALIGN_TOP, 3),
		Button(usercmd.ALIGN_MIDDLE, 4),
		Button(usercmd.ALIGN_BOTTOM, 5),
		Separator(6),
		Button(usercmd.DISTRIBUTE_HORIZONTALLY, 6),
		Button(usercmd.DISTRIBUTE_VERTICALLY, 7),
		)
	)
)

TOOLBARS=[
	GENERAL_TEMPLATE,
	PLAYER_TEMPLATE,
	ALIGN_TEMPLATE
]

TOOLBARS.reverse()  # For now...
