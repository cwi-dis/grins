__version__ = "$Id$"

#
# Template file for the application toolbars.
# The template is a list of toolbars. Each toolbar
# has a name, a type (normally 'toolbar'), an initial
# state ('docked', 'floating' or 'hidden')
# a menu-command-id (to show/hide it),
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
from ToolbarIcons import *
import features

#
# This is a hack by Jack. We need fixed ID values
# for the toolbars, because that is how their state
# is saved in the registry. However, I couldn't find
# a reasonable way to get these values into GRiNSRes.
# The values are magic and deduced from afxres.h and from
# the docktool example in the MSDN library.
IDW_TOOLBAR_GENERAL=0xe800
IDW_TOOLBAR_PLAYER=0xe801
IDW_TOOLBAR_ALIGNMENT=0xe802
IDW_TOOLBAR_LINKING=0xe803
IDW_TOOLBAR_CONTAINERS=0xe804
IDW_TOOLBAR_PLAYER_PANEL = 0xe805

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
		Button(usercmd.NEW_DOCUMENT, TBICON_NEW),
		Separator(6),
		Button(usercmd.OPENFILE, TBICON_OPENFILE),
		Button(usercmd.SAVE, TBICON_SAVE),
		Separator(6),
		Button(usercmd.RESTORE, TBICON_RESTORE),
		Button(usercmd.CLOSE, TBICON_CLOSE),
		Button(wndusercmd.CLOSE_ACTIVE_WINDOW, TBICON_CLOSE_WINDOW),
		Separator(6),
		Button(usercmd.ZOOMIN, TBICON_ZOOMIN),
		Button(usercmd.ZOOMOUT, TBICON_ZOOMOUT),
		Button(usercmd.ZOOMRESET, TBICON_ZOOMRESET),
		Separator(6),
		Button(usercmd.HELP, TBICON_HELP),
		)
	)
)

FRAME_TEMPLATE = (
	('General', 'toolbar', 'docked', wndusercmd.TOOLBAR_GENERAL, IDW_TOOLBAR_GENERAL, grinsRC.IDR_TB_COMMON, 0, (
		Button(usercmd.NEW_DOCUMENT, TBICON_NEW),
		Separator(6),
		Button(usercmd.OPENFILE, TBICON_OPENFILE),
		Button(usercmd.SAVE, TBICON_SAVE),
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

buttonlist = [
	Button(usercmd.CREATEANCHOREXTENDED, TBICON_CREATE_ANCHOREXTENDED),
	Separator(6),
	Button(usercmd.CREATE_EVENT_SOURCE, TBICON_EVENT_SOURCE),
	Button(usercmd.CREATE_BEGIN_EVENT, TBICON_BEGIN_EVENT),
	Button(usercmd.CREATE_END_EVENT, TBICON_END_EVENT),
	]
if features.EXPORT_REAL in features.feature_set:
	# add animate button between media and brush
	buttonlist.insert(1, Button(usercmd.CREATEANCHOR_CONTEXT, TBICON_CREATE_ANCHOR_CONTEXT))
	buttonlist.insert(2, Button(usercmd.CREATEANCHOR_BROWSER, TBICON_CREATE_ANCHOR_BROWSER))
if features.INTERNAL_LINKS in features.feature_set:
	buttonlist.insert(0, Button(usercmd.CREATEANCHOR, TBICON_CREATE_ANCHOR))
	buttonlist.insert(1, Button(usercmd.FINISH_LINK, TBICON_FINISH_LINK))
	buttonlist.insert(2, Separator(6))

LINKING_TEMPLATE = (
	('Linking and Timing', 'toolbar', 'docked', wndusercmd.TOOLBAR_LINKING, IDW_TOOLBAR_LINKING, grinsRC.IDR_TB_EDITOR, 0, tuple(buttonlist)
	)
)


ALIGN_TEMPLATE = (
	('Region alignment', 'toolbar', 'docked', wndusercmd.TOOLBAR_ALIGNMENT, IDW_TOOLBAR_ALIGNMENT, grinsRC.IDR_TB_EDITOR, 0, (
		Button(usercmd.ALIGN_LEFT, TBICON_ALIGN_LEFT),
		Button(usercmd.ALIGN_CENTER, TBICON_ALIGN_VERTICAL),
		Button(usercmd.ALIGN_RIGHT, TBICON_ALIGN_RIGHT),
		Separator(6),
		Button(usercmd.ALIGN_TOP, TBICON_ALIGN_TOP),
		Button(usercmd.ALIGN_MIDDLE, TBICON_ALIGN_HORIZONTAL),
		Button(usercmd.ALIGN_BOTTOM, TBICON_ALIGN_BOTTOM),
		Separator(6),
		Button(usercmd.DISTRIBUTE_HORIZONTALLY, TBICON_DISTRIBUTE_HORIZONTAL),
		Button(usercmd.DISTRIBUTE_VERTICALLY, TBICON_DISTRIBUTE_VERTICAL),
		)
	)
)

buttonlist = [
	Button(usercmd.DRAG_PAR, TBICON_PAR),
	Button(usercmd.DRAG_SEQ, TBICON_SEQ),
	Button(usercmd.DRAG_SWITCH, TBICON_SWITCH),
	Button(usercmd.DRAG_EXCL, TBICON_EXCL),
	Button(usercmd.DRAG_PRIO, TBICON_PRIO),
	Separator(6),
	Button(usercmd.DRAG_MEDIA, TBICON_MEDIA),
	Button(usercmd.DRAG_BRUSH, TBICON_BRUSH),
	Separator(6),
	Button(usercmd.DRAG_TOPLAYOUT, TBICON_TOPLAYOUT),
	Button(usercmd.DRAG_REGION, TBICON_REGION),
	]
if features.ANIMATE in features.feature_set:
	# add animate button between media and brush
	buttonlist.insert(7, Button(usercmd.DRAG_ANIMATE, TBICON_ANIMATE))

CONTAINERS_TEMPLATE = (
	('Containers', 'toolbar', 'docked', wndusercmd.TOOLBAR_CONTAINERS, IDW_TOOLBAR_CONTAINERS, grinsRC.IDR_TB_EDITOR, 1, tuple(buttonlist)
	)
)
del buttonlist

TOOLBARS=[
	GENERAL_TEMPLATE,
##	PLAYER_TEMPLATE,
	CONTAINERS_TEMPLATE,
	LINKING_TEMPLATE,
]
if features.ALIGNTOOL in features.feature_set:
	TOOLBARS.append(ALIGN_TEMPLATE)

TOOLBARS.reverse()  # For now...
