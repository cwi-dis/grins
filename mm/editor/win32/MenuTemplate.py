__version__ = "$Id$"

#
# Command/menu mapping for the win32 GRiNS Editor
#

# @win32doc|MenuTemplate
# Contains the specification for player menu in the
# following Grammar:
# # entry: <simple_entry> | <sep_entry> | <dyn_cascade_entry> | <CASCADE_ENTRY>
# # simple_entry: (ENTRY | TOGGLE, LABEL, SHORTCUT, ID)
# # sep_enty: (SEP,)
# # dyn_cascade_entry: (DYNAMICCASCADE, LABEL, ID)
# # cascade_entry: (CASCADE,LABEL,menu_spec_list)
# # menubar_entry: (LABEL,menu_spec_list)
# # menu_spec_list: list of entry
# # menubar_spec_list: list of menubar_entry
# # menu_exec_list: (MENU,menu_spec_list)
# where ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE are type constants.
# LABEL and and SHORTCUT are strings
# ID is either an integer or an object that can be maped to an integer


from usercmd import *

# plus wnds arrange cmds
from wndusercmd import *

import features

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)

# Some commands are optional, depending on preference settings:
from flags import *

MENUBAR=(
	('&File', (
		(FLAG_ALL, ENTRY, '&New\tCtrl+N', 'N', NEW_DOCUMENT),
		(FLAG_ALL, ENTRY, '&Open...\tCtrl+O', 'O', OPENFILE),
		(FLAG_ALL, ENTRY, 'Open &URL...\tCtrl+L', 'O', OPEN),
		(FLAG_ALL, DYNAMICCASCADE, 'Open &recent', OPEN_RECENT),
		(FLAG_ALL, ENTRY, '&Close', None, CLOSE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Save\tCtrl+S', 'S', SAVE),
		(FLAG_ALL, ENTRY, 'Save &as...', None, SAVE_AS),
		(FLAG_ALL, ENTRY, 'Revert &to saved', None, RESTORE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, CASCADE, 'Publish', (
			((features.EXPORT_QT,), ENTRY, 'Publish for &QuickTime...', None, EXPORT_QT),
			((features.EXPORT_QT,), ENTRY, 'Pu&blish for QuickTime and upload...', None, UPLOAD_QT),
			((features.EXPORT_REAL,), ENTRY, 'Publish for &RealOne...', None, EXPORT_G2),
			((features.EXPORT_REAL,), ENTRY, 'Publish for RealOne and &upload...', None, UPLOAD_G2),
			# TODO: These should not appear on all versions of GRiNS!
			(0, ENTRY, 'Publish for &Windows Media...', None, EXPORT_WMP), # mjvdg 11-oct-2000
			(0, ENTRY, 'Publish for Windows &Media and upload...', None, UPLOAD_WMP),
			((features.EXPORT_HTML_TIME,), ENTRY, 'Publish for &IE-6 HTML+TIME...', None, EXPORT_HTML_TIME),
			(FLAG_ALL, SEP,),
			((features.EXPORT_REAL,), ENTRY, 'Publish for RealPlayer 8...', None, EXPORT_SMIL1),
			(FLAG_ALL, SEP,),
			((features.EXPORT_SMIL2,), ENTRY, '&Publish for GRiNS SMIL 2.0 Player...', None, EXPORT_SMIL),
			(0, ENTRY, 'Publish for &SMIL 2.0 and upload...', None, UPLOAD_SMIL),
			((features.EXPORT_WINCE,), ENTRY, '&Publish for GRiNS/PocketPC Player...', None, EXPORT_WINCE),
			(FLAG_ALL, SEP,),
			((features.EXPORT_3GPP,), ENTRY, 'P&rune and publish for 3GPP (PSS4)...', None, EXPORT_3GPP),
			(FLAG_PRO, ENTRY, 'P&rune and publish for generic SMIL 2.0...', None, EXPORT_PRUNE),
		)),
		(FLAG_SMIL_1_0 | FLAG_QT | FLAG_G2 | FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Document Properties...', None, PROPERTIES),
		((features.PREFERENCES,), ENTRY, 'Preferences...', None, PREFERENCES),
		(FLAG_DBG, SEP,),
		(FLAG_DBG, CASCADE, 'D&ebug', (
			(FLAG_DBG, ENTRY, 'Dump &scheduler data', None, SCHEDDUMP),
			(FLAG_DBG, TOGGLE, 'Enable call &tracing', None, TRACE),
			(FLAG_DBG, ENTRY, 'Enter &debugger', None, DEBUG),
			(FLAG_DBG, ENTRY, '&Abort', None, CRASH),
			(FLAG_DBG, TOGGLE, 'Show &log/debug window', None, CONSOLE),
			(FLAG_DBG, TOGGLE, 'Toggle Scheduler.debugevents', None, SCHEDDEBUG),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'E&xit', None, EXIT),
		)),

	('&Edit', (
		(FLAG_ALL, ENTRY, '&Undo\tCtrl+Z', 'Z', UNDO),
		(FLAG_ALL, ENTRY, '&Redo\tCtrl+Y', 'Y', REDO),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Cu&t\tCtrl+X', 'X', CUT),
		(FLAG_ALL, ENTRY, '&Copy\tCtrl+C', 'C', COPY),
		(FLAG_ALL, ENTRY, 'Copy Properties...', None, COPYPROPERTIES),
		(FLAG_ALL, ENTRY, '&Paste\tCtrl+V', 'V', PASTE_AFTER),
		(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, CASCADE, 'P&aste special', (
			(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, ENTRY, '&Before', None, PASTE_BEFORE),
			(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, ENTRY, '&Within', None, PASTE_UNDER),
			(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, ENTRY, '&After', None, PASTE_AFTER),
			)),
		(FLAG_ALL, ENTRY, 'Paste Properties', None, PASTEPROPERTIES),
		(FLAG_ALL, ENTRY, '&Delete\tDel', None, DELETE),
		(FLAG_ALL, ENTRY, '&Delete, but keep content', None, MERGE_CHILD),
		(FLAG_ALL, SEP,),
		((features.SOURCE_VIEW,), ENTRY, '&Find...\tCtrl+F', 'F', FIND),
		((features.SOURCE_VIEW,), ENTRY, 'Find Next\tF3', None, FINDNEXT),
		((features.SOURCE_VIEW_EDIT,), ENTRY, '&Replace...\tCtrl+R', None, REPLACE),
		((features.SOURCE_VIEW,), SEP,),
##		(FLAG_PRO, ENTRY, '&Info...', 'I', INFO),
		(FLAG_ALL, ENTRY, 'Propertie&s...', 'A', ATTRIBUTES),
		(FLAG_ALL, ENTRY, '&Edit Content...', 'E', CONTENT),
		)),

	# this whole section removed in Snap! below
	('&Insert', (
		(FLAG_ALL, CASCADE, '&Media', (
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_MEDIA),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_MEDIA),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_MEDIA),
		)),
		((features.EDIT_REALPIX,), CASCADE, 'Sli&deshow object', (
			((features.EDIT_REALPIX,), ENTRY, '&Before', None, NEW_BEFORE_SLIDESHOW),
			((features.EDIT_REALPIX,), ENTRY, '&After', None, NEW_AFTER_SLIDESHOW),
			((features.EDIT_REALPIX,), ENTRY, '&Within', None, NEW_UNDER_SLIDESHOW),
		)),
		(FLAG_ALL, CASCADE, '&Immediate Text', (
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_TEXT),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_TEXT),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_TEXT),
		)),
		(FLAG_ALL, CASCADE, '&Brush', (
			(FLAG_BOSTON, ENTRY, '&Before', None, NEW_BEFORE_BRUSH),
			(FLAG_BOSTON, ENTRY, '&After', None, NEW_AFTER_BRUSH),
			(FLAG_BOSTON, ENTRY, '&Within', None, NEW_UNDER_BRUSH),
		)),
		((features.ANIMATE,), CASCADE, '&Animate', (
			((features.ANIMATE,), ENTRY, '&Before', None, NEW_BEFORE_ANIMATE),
			((features.ANIMATE,), ENTRY, '&After', None, NEW_AFTER_ANIMATE),
			((features.ANIMATE,), ENTRY, '&Within', None, NEW_UNDER_ANIMATE),
		)),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, CASCADE, '&Parallel group', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_PAR),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PAR),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PAR),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_PAR),
		)),
		(FLAG_ALL, CASCADE, '&Sequential group', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_SEQ),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SEQ),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SEQ),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SEQ),
		)),
		(FLAG_ALL, CASCADE, 'S&witch group', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_SWITCH),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SWITCH),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SWITCH),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SWITCH),
		)),
		(FLAG_ALL, CASCADE, 'E&xcl group', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_EXCL),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_EXCL),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_EXCL),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_EXCL),
		)),
		(FLAG_ALL, CASCADE, 'Priorit&y class group', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_PRIO),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PRIO),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PRIO),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_PRIO),
		)),
		(FLAG_PRO, SEP,),
#		(FLAG_PRO, ENTRY, '&New object...', None, NEW_AFTER),
		(FLAG_ALL, CASCADE, '&Region', (
			(FLAG_PRO, ENTRY, '&Within', None, NEW_REGION),
		)),
		(FLAG_BOSTON, ENTRY, '&TopLayout', 'T', NEW_TOPLAYOUT),
#		(FLAG_PRO, SEP,),

## Windows dialogs apparently do not use usercmd commands.
##		(FLAG_PRO, ENTRY, 'New &layout', None, NEW_LAYOUT),
#		(FLAG_PRO, SEP,),
#		(FLAG_PRO, ENTRY, '&Move region', None, MOVE_REGION),
#		(FLAG_PRO, ENTRY, 'C&opy region', None, COPY_REGION),
#		(FLAG_CMIF, ENTRY, 'To&ggle channel state', None, TOGGLE_ONOFF),
##		(FLAG_PRO, ENTRY, 'Edit Source...', None, EDITSOURCE),
#		(FLAG_PRO, ENTRY, '&Before...', None, NEW_BEFORE),
#		(FLAG_PRO, ENTRY, '&Within...', None, NEW_UNDER),
		)),
	('&Preview', (
		(FLAG_ALL, ENTRY, '&Preview\tCtrl+P', 'P', PLAY),
		(FLAG_ALL, ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(FLAG_ALL, ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Preview single &object', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Preview &from object', None, PLAYFROM),
		((features.USER_GROUPS, features.PREFERENCES,), SEP,),
		((features.USER_GROUPS,), DYNAMICCASCADE, 'Custom &tests', USERGROUPS),
#		((features.PREFERENCES,), ENTRY, 'GRiNS previewer properties...', None, PREFERENCES),
		)),


	('&Linking', (
		((features.INTERNAL_LINKS,), ENTRY, 'Create simple link source', None, CREATEANCHOR),
		((features.INTERNAL_LINKS,), ENTRY, '&Finish simple link to selection', None, FINISH_LINK),
		((features.INTERNAL_LINKS,), SEP,),
		((features.EXPORT_REAL,), ENTRY, 'Create link to context window...', None, CREATEANCHOR_CONTEXT),
		((features.EXPORT_REAL,), ENTRY, 'Create link to browser window...', None, CREATEANCHOR_BROWSER),
		(FLAG_ALL, ENTRY, 'Create full link source and edit...', None, CREATEANCHOREXTENDED),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Use as event &source', None, CREATE_EVENT_SOURCE),
		(FLAG_ALL, ENTRY, 'Create &begin event', None, CREATE_BEGIN_EVENT),
		(FLAG_ALL, ENTRY, 'Create &end event', None, CREATE_END_EVENT),
		)),

	('&Tools', (
		(FLAG_ALL, ENTRY, 'Check bandwidth &usage', None, COMPUTE_BANDWIDTH),
		(FLAG_ALL, SEP,),
		(FLAG_BOSTON, ENTRY, 'RealPix to S&MIL 2.0', None, RPCONVERT),
		(FLAG_PRO, ENTRY, 'SMIL 2.0 to RealPi&x', None, CONVERTRP),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Mark on timeline\tCtrl+M', 'M', MARK),		
		(FLAG_ALL, ENTRY, '&Clear marks', None, CLEARMARKS),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Select object from source', 'S', SELECTNODE_FROM_SOURCE),		
		(FLAG_ALL, SEP,),
		((features.ALIGNTOOL,), CASCADE, '&Align', (
			((features.ALIGNTOOL,), ENTRY, '&Left', 'L', ALIGN_LEFT),
			((features.ALIGNTOOL,), ENTRY, '&Center', 'C', ALIGN_CENTER),
			((features.ALIGNTOOL,), ENTRY, '&Right', 'R', ALIGN_RIGHT),
			((features.ALIGNTOOL,), SEP,),
			((features.ALIGNTOOL,), ENTRY, '&Top', 'T', ALIGN_TOP),
			((features.ALIGNTOOL,), ENTRY, '&Middle', 'M', ALIGN_MIDDLE),
			((features.ALIGNTOOL,), ENTRY, '&Bottom', 'B', ALIGN_BOTTOM),
			)),
		((features.ALIGNTOOL,), CASCADE, '&Distribute', (
			((features.ALIGNTOOL,), ENTRY, '&Horizontally', 'H', DISTRIBUTE_HORIZONTALLY),
			((features.ALIGNTOOL,), ENTRY, '&Vertically', 'V', DISTRIBUTE_VERTICALLY),
			)),
		((features.ALIGNTOOL,), SEP,),
		# XXX temporare
		(FLAG_PRO, TOGGLE, 'Enable animation', None, ENABLE_ANIMATION),
		)),

	('&View', (
		(FLAG_ALL, CASCADE, 'T&oolbars', (
			(FLAG_ALL, ENTRY, '&General', None, TOOLBAR_GENERAL),
##			(FLAG_ALL, ENTRY, '&Player Controls', None, TOOLBAR_PLAYER),
			(FLAG_ALL, ENTRY, '&Containers', None, TOOLBAR_CONTAINERS),
			(FLAG_ALL, ENTRY, '&Timing and Linking', None, TOOLBAR_LINKING),
			((features.ALIGNTOOL,), ENTRY, '&Region alignment', None, TOOLBAR_ALIGNMENT),
			(FLAG_ALL, SEP,),
			(FLAG_ALL, ENTRY, 'Pre&viewer Control Panel', None, PLAYER_PANEL),
			)),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Expand/Collapse\tCtrl+I', None, EXPAND),
		(FLAG_ALL, ENTRY, 'E&xpand all', None, EXPANDALL),
		(FLAG_ALL, ENTRY, '&Collapse all', None, COLLAPSEALL),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, CASCADE, '&Zoom', (
			(FLAG_PRO, ENTRY, '&Zoom in 2x', None, ZOOMIN2),
			(FLAG_PRO, ENTRY, '&Zoom in 4x', None, ZOOMIN4),
			(FLAG_PRO, ENTRY, '&Zoom in 8x', None, ZOOMIN8),
			(FLAG_PRO, SEP,),
			(FLAG_PRO, ENTRY, '&Zoom out 2x', None, ZOOMOUT2),
			(FLAG_PRO, ENTRY, '&Zoom out 4x', None, ZOOMOUT4),
			(FLAG_PRO, ENTRY, '&Zoom out 8x', None, ZOOMOUT8),
			(FLAG_PRO, SEP,),
			(FLAG_PRO, ENTRY, '&Fit in Window', None, ZOOMRESET),
			)),
		(FLAG_ALL, SEP,),
#		(FLAG_PRO, TOGGLE, 'Show/Hide unused c&hannels', None, TOGGLE_UNUSED),
#		(FLAG_PRO, TOGGLE, 'Sync &arcs', None, TOGGLE_ARCS),
		((features.H_THUMBNAILS,), TOGGLE, '&Image thumbnails', None, THUMBNAIL),
		((features.H_PLAYABLE,), TOGGLE, 'Show &Playable', None, PLAYABLE),
##		(FLAG_ALL, TOGGLE, 'Sho&w Time in Structure', None, CORRECTLOCALTIMESCALE),
		(FLAG_ALL, ENTRY, 'Show Timeline/Bandwidth Usage', None, TOGGLE_TIMESCALE),
##		(FLAG_ALL, TOGGLE, 'Show &Bandwidth Usage', None, TOGGLE_BWSTRIP),
		(FLAG_ALL, TOGGLE, 'Show Animation &Path', None, SHOW_ANIMATIONPATH),
##		(FLAG_ALL, CASCADE, 'Sho&w Time in Structure', (
##			(FLAG_ALL, TOGGLE, '&Whole Document, Adaptive', None, TIMESCALE),
##			(FLAG_ALL, TOGGLE, '&Selection Only, Adaptive', None, LOCALTIMESCALE),
##			(FLAG_ALL, TOGGLE, 'Selection Only, &Fixed', None, CORRECTLOCALTIMESCALE),
##			)),
		(FLAG_CMIF, SEP,),
##		(FLAG_ALL, DYNAMICCASCADE, '&Layout navigation', LAYOUTS),
#		(FLAG_ALL, TOGGLE, 'Show A&ll Properties', None, SHOWALLPROPERTIES),
		)
	 ),
 
	('&Window', (
		(FLAG_ALL, ENTRY, 'Cl&ose\tCtrl+W', 'W', CLOSE_ACTIVE_WINDOW),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Cascade', 'C', CASCADE_WNDS),
		(FLAG_ALL, ENTRY, 'Tile &Horizontally', 'H', TILE_HORZ),
		(FLAG_ALL, ENTRY, 'Tile &Vertically', 'T', TILE_VERT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Previewer\tF5', '1', PLAYERVIEW),
		(FLAG_ALL, ENTRY, '&Structured timeline\tF6', '3', HIERARCHYVIEW),
		(FLAG_PRO, ENTRY, '&Layout\tF7', '2', LAYOUTVIEW2),
		(FLAG_ALL, ENTRY, 'Sourc&e\tF8', '7', SOURCEVIEW),
		(FLAG_ALL, SEP,),
		(FLAG_PRO, ENTRY, '&Assets', '2', ASSETSVIEW),
		(FLAG_PRO, ENTRY, 'H&yperlinks', '5', LINKVIEW),
		((features.USER_GROUPS,), ENTRY, 'C&ustom tests', '6', USERGROUPVIEW),
		(FLAG_BOSTON, ENTRY, 'T&ransitions', None, TRANSITIONVIEW),
		((features.ERRORS_VIEW,), ENTRY, 'Error &messages', '8', ERRORSVIEW),
		)),

	('&Help', (
		(FLAG_ALL, ENTRY, '&Contents', None, HELP_CONTENTS),
##		(FLAG_ALL, ENTRY, 'Context &Help', None, HELP),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Quick Start Guide', None, GRINS_QSG),
		(FLAG_ALL, ENTRY, '&Tutorial', None, GRINS_TUTORIAL),
		(FLAG_ALL, ENTRY, 'Template Guide', None, GRINS_TDG),
		(FLAG_ALL, ENTRY, 'GRiNS Reference Manual', None, GRINS_REFERENCE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'C&heck for GRiNS update...', None, CHECKVERSION),
		(FLAG_ALL, ENTRY, '&Register GRiNS...', None, REGISTER),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))

NODOC_MENUBAR=(MENUBAR[0],MENUBAR[7])

#
# Popup menus for various states
#

POPUP_HVIEW_LEAF = (
		# XXXX Need to add the "new xxx node" commands for the
		# light version
#		(FLAG_PRO, ENTRY, '&New object...', None, NEW_AFTER),
#		(FLAG_PRO, ENTRY, 'New object &before...', None, NEW_BEFORE),
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, 'Copy Properties...', None, COPYPROPERTIES),
		(FLAG_ALL, ENTRY, '&Paste within', None, PASTE_UNDER),
		(FLAG_ALL, ENTRY, 'Paste bef&ore', None, PASTE_BEFORE),
		(FLAG_ALL, ENTRY, 'Paste a&fter', None, PASTE_AFTER),
		(FLAG_ALL, ENTRY, 'Pa&ste file', None, PASTE_FILE),
		(FLAG_ALL, ENTRY, 'Paste Properties', None, PASTEPROPERTIES),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, CASCADE, '&Insert', (
			(FLAG_ALL, CASCADE, '&Media', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_MEDIA),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_MEDIA),
			)),
			((features.EDIT_REALPIX,), CASCADE, 'Sli&deshow object', (
				((features.EDIT_REALPIX,), ENTRY, '&Before', None, NEW_BEFORE_SLIDESHOW),
				((features.EDIT_REALPIX,), ENTRY, '&After', None, NEW_AFTER_SLIDESHOW),
			)),
			(FLAG_ALL, CASCADE, '&Immediate Text', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_TEXT),
			)),
			(FLAG_ALL, CASCADE, '&Brush', (
				(FLAG_BOSTON, ENTRY, '&Before', None, NEW_BEFORE_BRUSH),
				(FLAG_BOSTON, ENTRY, '&After', None, NEW_AFTER_BRUSH),
			)),
			((features.ANIMATE,), CASCADE, 'Animate', (
				((features.ANIMATE,), ENTRY, '&Before', None, NEW_BEFORE_ANIMATE),
				((features.ANIMATE,), ENTRY, '&After', None, NEW_AFTER_ANIMATE),
				((features.ANIMATE,), ENTRY, '&Within', None, NEW_UNDER_ANIMATE),
			)),
			(FLAG_ALL, SEP,),
			(FLAG_ALL, CASCADE, '&Parallel group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_PAR),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PAR),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PAR),
				)),
			(FLAG_ALL, CASCADE, '&Sequential group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SEQ),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SEQ),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SEQ),
				)),
			(FLAG_ALL, CASCADE, 'S&witch group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SWITCH),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SWITCH),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SWITCH),
				)),
			(FLAG_ALL, CASCADE, 'E&xcl group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_EXCL),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_EXCL),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_EXCL),
			)),
			(FLAG_ALL, CASCADE, 'Priorit&y class group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_PRIO),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PRIO),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PRIO),
			)),
		)),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_ALL, ENTRY, 'Delete, but keep content', None, MERGE_CHILD),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'P&review single object', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Preview &from object', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Use as event &source', None, CREATE_EVENT_SOURCE),
		(FLAG_ALL, ENTRY, 'Create &begin event', None, CREATE_BEGIN_EVENT),
		(FLAG_ALL, ENTRY, 'Create &end event', None, CREATE_END_EVENT),
		((features.INTERNAL_LINKS,), SEP,),
		((features.INTERNAL_LINKS,), ENTRY, 'Create simple link source', None, CREATEANCHOR),
		((features.INTERNAL_LINKS,), ENTRY, 'Finish simple link to selection', None, FINISH_LINK),
		(FLAG_PRO, SEP,),
		((features.EXPORT_REAL,), ENTRY, 'Create link to context window...', None, CREATEANCHOR_CONTEXT),
		((features.EXPORT_REAL,), ENTRY, 'Create link to browser window...', None, CREATEANCHOR_BROWSER),
		(FLAG_ALL, ENTRY, 'Create full link source and edit...', None, CREATEANCHOREXTENDED),
		(FLAG_PRO, SEP,),
		(FLAG_BOSTON, ENTRY, 'RealPix to S&MIL 2.0', None, RPCONVERT),
		(FLAG_ALL, SEP,),
##		(FLAG_PRO, ENTRY, '&Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
##		(FLAG_PRO, ENTRY, '&Anchors...', None, ANCHORS),
		(FLAG_ALL, ENTRY, '&Edit content', None, CONTENT),
)

POPUP_HVIEW_NONE = (
	(FLAG_ALL, ENTRY, '&New object...', None, NEW_AFTER)
	)

POPUP_HVIEW_TRANS = (
		(FLAG_ALL, DYNAMICCASCADE, '&Transition', TRANSITION),
		)

POPUP_HVIEW_SLIDE = (
		# XXXX Need to add the "new xxx node" commands for the
		# light version
		((features.EDIT_REALPIX,), ENTRY, 'Cu&t', None, CUT),
		((features.EDIT_REALPIX,), ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, 'Copy Properties...', None, COPYPROPERTIES),
		((features.EDIT_REALPIX,), ENTRY, '&Paste', None, PASTE_AFTER),
		((features.EDIT_REALPIX,), ENTRY, 'Paste bef&ore', None, PASTE_BEFORE),
		((features.EDIT_REALPIX,), ENTRY, 'Pa&ste file', None, PASTE_FILE),
		(FLAG_ALL, ENTRY, 'Paste Properties', None, PASTEPROPERTIES),
		((features.EDIT_REALPIX,), SEP,),
		((features.EDIT_REALPIX,), ENTRY, '&Delete', None, DELETE),
		((features.EDIT_REALPIX,), CASCADE, 'Insert image &object', (
			((features.EDIT_REALPIX,), ENTRY, '&Before', None, NEW_BEFORE_IMAGE),
			((features.EDIT_REALPIX,), ENTRY, '&After', None, NEW_AFTER_IMAGE),
			)),
		((features.EDIT_REALPIX,), SEP,),
		((features.EDIT_REALPIX,), ENTRY, 'P&roperties...', None, ATTRIBUTES),
		((features.EDIT_REALPIX,), ENTRY, '&Edit content', None, CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
#		(FLAG_PRO, ENTRY, '&New object...', None, NEW_AFTER),
#		(FLAG_PRO, CASCADE, 'Ne&w object special', (
#			(FLAG_PRO, ENTRY, '&Before...', None, NEW_BEFORE),
#			(FLAG_PRO, ENTRY, '&Within...', None, NEW_UNDER),
#			)),
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, 'Copy Properties...', None, COPYPROPERTIES),
		(FLAG_ALL, ENTRY, '&Paste', None, PASTE_UNDER),
#		(FLAG_ALL, CASCADE, 'Paste &special', (
#			(FLAG_ALL, ENTRY, '&Before', None, PASTE_BEFORE),
#			(FLAG_ALL, ENTRY, '&Within', None, PASTE_UNDER),
#			)),
		(FLAG_ALL, ENTRY, 'Paste &file', None, PASTE_FILE),
		(FLAG_ALL, ENTRY, 'Paste Properties', None, PASTEPROPERTIES),
		(FLAG_ALL, SEP,),
#		(FLAG_PRO, ENTRY, 'Edit in Temporal view', None, EDIT_TVIEW),
		(FLAG_ALL, CASCADE, '&Insert', (
			(FLAG_ALL, CASCADE, '&Media', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_MEDIA),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_MEDIA),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_MEDIA),
			)),
			((features.EDIT_REALPIX,), CASCADE, 'Sli&deshow object', (
				((features.EDIT_REALPIX,), ENTRY, '&Before', None, NEW_BEFORE_SLIDESHOW),
				((features.EDIT_REALPIX,), ENTRY, '&After', None, NEW_AFTER_SLIDESHOW),
				((features.EDIT_REALPIX,), ENTRY, '&Within', None, NEW_UNDER_SLIDESHOW),
			)),
			(FLAG_ALL, CASCADE, '&Immediate Text', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_TEXT),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_TEXT),
			)),
			(FLAG_ALL, CASCADE, '&Brush', (
				(FLAG_BOSTON, ENTRY, '&Before', None, NEW_BEFORE_BRUSH),
				(FLAG_BOSTON, ENTRY, '&After', None, NEW_AFTER_BRUSH),
				(FLAG_BOSTON, ENTRY, '&Within', None, NEW_UNDER_BRUSH),
			)),
			((features.ANIMATE,), CASCADE, '&Animate', (
				((features.ANIMATE,), ENTRY, '&Before', None, NEW_BEFORE_ANIMATE),
				((features.ANIMATE,), ENTRY, '&After', None, NEW_AFTER_ANIMATE),
				((features.ANIMATE,), ENTRY, '&Within', None, NEW_UNDER_ANIMATE),
			)),
			(FLAG_ALL, SEP,),
			(FLAG_ALL, CASCADE, '&Parallel group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_PAR),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PAR),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PAR),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_PAR),
				)),
			(FLAG_ALL, CASCADE, '&Sequential group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SEQ),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SEQ),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SEQ),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SEQ),
				)),
			(FLAG_ALL, CASCADE, 'S&witch group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SWITCH),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SWITCH),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SWITCH),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SWITCH),
				)),
			(FLAG_ALL, CASCADE, 'E&xcl group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_EXCL),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_EXCL),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_EXCL),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_EXCL),
			)),
			(FLAG_ALL, CASCADE, 'Priorit&y class group', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_PRIO),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PRIO),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PRIO),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_PRIO),
			)),
		)),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_ALL, ENTRY, 'Delete, but keep content', None, MERGE_CHILD),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'P&review single object', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Preview &from object', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Expand/Collapse', None, EXPAND),
		(FLAG_ALL, ENTRY, 'E&xpand all', None, EXPANDALL),
		(FLAG_ALL, ENTRY, 'C&ollapse all', None, COLLAPSEALL),
		(FLAG_ALL, TOGGLE, 'S&how Time in Structure', None, CORRECTLOCALTIMESCALE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Use as event &source', None, CREATE_EVENT_SOURCE),
		(FLAG_ALL, ENTRY, 'Create &begin event', None, CREATE_BEGIN_EVENT),
		(FLAG_ALL, ENTRY, 'Create &end event', None, CREATE_END_EVENT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Finish simple link to selection', None, FINISH_LINK),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, 'SMIL 2.0 to RealPi&x', None, CONVERTRP),
		(FLAG_ALL, SEP,),
##		(FLAG_PRO, ENTRY, '&Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
##		(FLAG_PRO, ENTRY, '&Anchors...', None, ANCHORS),
)

POPUP_MULTI = (
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Event &source', None, CREATE_EVENT_SOURCE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
)

POPUP_EVENT_DEST = (
	(FLAG_ALL, ENTRY, 'Find event source', None, FIND_EVENT_SOURCE),
#	(FLAG_ALL, ENTRY, 'Remove event', None, REMOVE_EVENT), # This points to many events..
	(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
	)

POPUP_EVENT_SOURCE = (
	(FLAG_ALL, ENTRY, 'Find event destination', None, FIND_EVENT_SOURCE),
#	(FLAG_ALL, ENTRY, 'Remove event', None, CRASH),
#	(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
	)

POPUP_REGIONTREE_TOPLAYOUT = (
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, '&Paste', None, PASTE_AFTER),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Insert region', None, NEW_REGION),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_PRO, SEP,),
#		(FLAG_ALL, ENTRY, 'Layout...', None, ATTRIBUTES_LAYOUT),
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
)

POPUP_REGIONTREE_REGION = (
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, '&Paste', None, PASTE_AFTER),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Insert region', None, NEW_REGION),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_PRO, SEP,),
#		(FLAG_ALL, ENTRY, 'Layout...', None, ATTRIBUTES_LAYOUT),
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
)

POPUP_REGIONTREE_MEDIA = (
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_PRO, SEP,),
#		(FLAG_ALL, ENTRY, 'Layout...', None, ATTRIBUTES_LAYOUT),
#		(FLAG_ALL, ENTRY, 'Anchors...', None, ATTRIBUTES_ANCHORS),
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
		(FLAG_ALL, ENTRY, '&Edit Content...', 'E', CONTENT),
)

POPUP_REGIONTREE_ANCHOR = (
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
)

POPUP_REGIONPREVIEW_TOPLAYOUT = (
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, '&Paste', None, PASTE_AFTER),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Insert region', None, NEW_REGION),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_PRO, SEP,),
#		(FLAG_ALL, ENTRY, 'Layout...', None, ATTRIBUTES_LAYOUT),
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, '&Zoom in', None, ZOOMIN),
		(FLAG_PRO, ENTRY, '&Zoom out', None, ZOOMOUT),
)

POPUP_REGIONPREVIEW_REGION = (
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, '&Paste', None, PASTE_AFTER),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Insert region', None, NEW_REGION),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_PRO, SEP,),
#		(FLAG_ALL, ENTRY, 'Layout...', None, ATTRIBUTES_LAYOUT),
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, '&Zoom in', None, ZOOMIN),
		(FLAG_PRO, ENTRY, '&Zoom out', None, ZOOMOUT),
)

POPUP_REGIONPREVIEW_MEDIA = (
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_PRO, SEP,),
#		(FLAG_ALL, ENTRY, 'Layout...', None, ATTRIBUTES_LAYOUT),
#		(FLAG_ALL, ENTRY, 'Anchors...', None, ATTRIBUTES_ANCHORS),
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
		(FLAG_ALL, ENTRY, '&Edit Content...', 'E', CONTENT),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, '&Zoom in', None, ZOOMIN),
		(FLAG_PRO, ENTRY, '&Zoom out', None, ZOOMOUT),
)

POPUP_REGIONPREVIEW_ANCHOR = (
#		(FLAG_ALL, ENTRY, 'Layout...', None, ATTRIBUTES_LAYOUT),
#		(FLAG_ALL, ENTRY, 'Anchors...', None, ATTRIBUTES_ANCHORS),
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, '&Zoom in', None, ZOOMIN),
		(FLAG_PRO, ENTRY, '&Zoom out', None, ZOOMOUT),
)

MAIN_FRAME_POPUP = (
		(FLAG_ALL, ENTRY, '&Paste document', None, PASTE_DOCUMENT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&New', None, NEW_DOCUMENT),
		(FLAG_ALL, ENTRY, '&Open...', None, OPENFILE),
		(FLAG_ALL, ENTRY, 'Open &URL...', None, OPEN),
		(FLAG_ALL, DYNAMICCASCADE, 'Open &recent', OPEN_RECENT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Save', None, SAVE),
		(FLAG_ALL, ENTRY, 'Save &as...', None, SAVE_AS),
		(FLAG_ALL, ENTRY, 'Revert &to saved', None, RESTORE),
		(FLAG_ALL, SEP,),
		((features.EXPORT_QT,), ENTRY, 'Publish for &QuickTime...', None, EXPORT_QT),
		((features.EXPORT_QT,), ENTRY, 'Pu&blish for QuickTime and upload...', None, UPLOAD_QT),
		((features.EXPORT_REAL,), ENTRY, 'Publish for &RealONE...', None, EXPORT_G2),
		((features.EXPORT_REAL,), ENTRY, 'Pu&blish for RealONE and upload...', None, UPLOAD_G2),
		((features.EXPORT_QT, features.EXPORT_REAL,), SEP,),
		(FLAG_ALL, ENTRY, '&Document Properties...', None, PROPERTIES),
		(FLAG_DBG, SEP,),
		(FLAG_DBG, CASCADE, 'D&ebug', (
			(FLAG_DBG, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(FLAG_DBG, TOGGLE, 'Enable call tracing', None, TRACE),
			(FLAG_DBG, ENTRY, 'Enter debugger', None, DEBUG),
			(FLAG_DBG, ENTRY, 'Abort', None, CRASH),
			(FLAG_DBG, TOGGLE, 'Show log/debug window', None, CONSOLE),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Close', None, CLOSE),
		(FLAG_ALL, ENTRY, 'E&xit', None, EXIT),
)

POPUP_SOURCEVIEW = (
		((features.SOURCE_VIEW_EDIT,), ENTRY, 'Cu&t\tCtrl+X', 'X', CUT),
		((features.SOURCE_VIEW,), ENTRY, '&Copy\tCtrl+C', 'C', COPY),
		((features.SOURCE_VIEW_EDIT,), ENTRY, '&Paste\tCtrl+V', 'V', PASTE_AFTER),
		((features.SOURCE_VIEW,), SEP,),
		((features.SOURCE_VIEW,), ENTRY, 'Find...', None, FIND),
		((features.SOURCE_VIEW,), ENTRY, 'Find Next', None, FINDNEXT),
		((features.SOURCE_VIEW_EDIT,), ENTRY, 'Replace...', None, REPLACE),
		((features.SOURCE_VIEW,), SEP,),
		((features.SOURCE_VIEW,), ENTRY, '&Select object from source', 'S', SELECTNODE_FROM_SOURCE),
)
