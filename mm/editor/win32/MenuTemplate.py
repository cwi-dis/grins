__version__ = "$Id$"

#
# Command/menu mapping for the win32 GRiNS Editor
#

""" @win32doc|MenuTemplate
Contains the specification for player menu in the
following Grammar:
# entry: <simple_entry> | <sep_entry> | <dyn_cascade_entry> | <CASCADE_ENTRY>
# simple_entry: (ENTRY | TOGGLE, LABEL, SHORTCUT, ID)
# sep_enty: (SEP,)
# dyn_cascade_entry: (DYNAMICCASCADE, LABEL, ID)
# cascade_entry: (CASCADE,LABEL,menu_spec_list)
# menubar_entry: (LABEL,menu_spec_list)
# menu_spec_list: list of entry
# menubar_spec_list: list of menubar_entry
# menu_exec_list: (MENU,menu_spec_list)
where ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE are type constants.
LABEL and and SHORTCUT are strings
ID is either an integer or an object that can be maped to an integer
"""


from usercmd import *

# plus wnds arrange cmds
from wndusercmd import *

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
		(FLAG_QT, ENTRY, 'Publish for &QuickTime...', None, EXPORT_QT),
		(FLAG_QT, ENTRY, 'Pu&blish for QuickTime and upload...', None, UPLOAD_QT),
		(FLAG_G2|FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for &G2...', None, EXPORT_G2),
		(FLAG_G2|FLAG_PRO|FLAG_SNAP, ENTRY, 'Pu&blish for G2 and upload...', None, UPLOAD_G2),
		# TODO: These should not appear on all versions of GRiNS!
		(FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for &Windows Media...', None, EXPORT_WMP), # mjvdg 11-oct-2000
		(FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for Windows Media and upload...', None, UPLOAD_WMP),
		(FLAG_PRO|FLAG_SNAP, ENTRY, 'Publish for Internet Explorer HTML+TIME...', None, EXPORT_HTML_TIME),
		
		(FLAG_SMIL_1_0|FLAG_PRO, ENTRY, '&Publish for SMIL 2.0...', None, EXPORT_SMIL),
		(FLAG_SMIL_1_0|FLAG_PRO, ENTRY, 'Pu&blish for SMIL 2.0 and upload...', None, UPLOAD_SMIL),
		(FLAG_SMIL_1_0 | FLAG_QT | FLAG_G2 | FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Document Properties...', None, PROPERTIES),
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
		(FLAG_ALL, ENTRY, 'C&heck for GRiNS update...', None, CHECKVERSION),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'E&xit', None, EXIT),
		)),

	('&Edit', (
		(FLAG_ALL, ENTRY, '&Undo\tCtrl+Z', 'Z', UNDO),
		(FLAG_ALL, ENTRY, '&Redo\tCtrl+Y', 'Y', REDO),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Cu&t\tCtrl+X', 'X', CUT),
		(FLAG_ALL, ENTRY, '&Copy\tCtrl+C', 'C', COPY),
		(FLAG_ALL, ENTRY, '&Paste\tCtrl+V', 'V', PASTE_UNDER),
		(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, CASCADE, 'P&aste special', (
			(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, ENTRY, '&Before', None, PASTE_BEFORE),
			(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, ENTRY, '&Within', None, PASTE_UNDER),
			(FLAG_G2|FLAG_QT|FLAG_CMIF|FLAG_SMIL_1_0|FLAG_BOSTON, ENTRY, '&After', None, PASTE_AFTER),
			)),
		(FLAG_ALL, ENTRY, '&Delete\tCtrl+Del', None, DELETE),
		(FLAG_ALL, SEP,),
		(FLAG_PRO, ENTRY, '&New node...', None, NEW_AFTER),
		(FLAG_PRO, ENTRY, 'New &Region', None, NEW_REGION),
		(FLAG_BOSTON, ENTRY, 'New &TopLayout', 'T', NEW_TOPLAYOUT),

## Windows dialogs apparently do not use usercmd commands.
##		(FLAG_PRO, ENTRY, 'New &layout', None, NEW_LAYOUT),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, '&Move region', None, MOVE_REGION),
		(FLAG_PRO, ENTRY, 'C&opy region', None, COPY_REGION),
		(FLAG_CMIF, ENTRY, 'To&ggle channel state', None, TOGGLE_ONOFF),
##		(FLAG_PRO, ENTRY, 'Edit Source...', None, EDITSOURCE),
		(FLAG_PRO, SEP,),
##		(FLAG_PRO, ENTRY, '&Info...', 'I', INFO),
		(FLAG_ALL, ENTRY, 'Propertie&s...', 'A', ATTRIBUTES),
		(FLAG_ALL, ENTRY, '&Edit Content...', 'E', CONTENT),
		(FLAG_PRO, ENTRY, 'Con&vert to SMIL 2.0', None, RPCONVERT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Pre&ferences...', None, PREFERENCES),
		)),

	# this whole section removed in Snap! below
	('&Insert', (
		(FLAG_ALL, CASCADE, '&Image node', (
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_IMAGE),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_IMAGE),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_IMAGE),
		)),
		(FLAG_G2, CASCADE, 'Sli&deshow node', (
			(FLAG_G2, ENTRY, '&Before', None, NEW_BEFORE_SLIDESHOW),
			(FLAG_G2, ENTRY, '&After', None, NEW_AFTER_SLIDESHOW),
			(FLAG_G2, ENTRY, '&Within', None, NEW_UNDER_SLIDESHOW),
		)),
		(FLAG_ALL, CASCADE, '&Text node', (
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_TEXT),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_TEXT),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_TEXT),
		)),
		(FLAG_SMIL_1_0, CASCADE, '&HTML node', (
			(FLAG_SMIL_1_0, ENTRY, '&Before', None, NEW_BEFORE_HTML),
			(FLAG_SMIL_1_0, ENTRY, '&After', None, NEW_AFTER_HTML),
			(FLAG_SMIL_1_0, ENTRY, '&Within', None, NEW_UNDER_HTML),
			)),
		(FLAG_ALL, CASCADE, 'S&ound node', (
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SOUND),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SOUND),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SOUND),
		)),
		(FLAG_ALL, CASCADE, '&Video node', (
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_VIDEO),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_VIDEO),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_VIDEO),
		)),
		(FLAG_ALL, CASCADE, 'Animation node', (
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_ANIMATION),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_ANIMATION),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_ANIMATION),
		)),
		(FLAG_ALL, CASCADE, '&Parallel node', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_PAR),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PAR),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PAR),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_PAR),
		)),
		(FLAG_ALL, CASCADE, '&Sequential node', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_SEQ),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SEQ),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SEQ),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SEQ),
		)),
		(FLAG_ALL, CASCADE, 'S&witch node', (
			(FLAG_ALL, ENTRY, '&Parent', None, NEW_SWITCH),
			(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SWITCH),
			(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SWITCH),
			(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SWITCH),
		)),
		(FLAG_PRO, ENTRY, '&Before...', None, NEW_BEFORE),
		(FLAG_PRO, ENTRY, '&Within...', None, NEW_UNDER),
		)),
	('&Play', (
		(FLAG_ALL, ENTRY, '&Play\tCtrl+P', 'P', PLAY),
		(FLAG_ALL, ENTRY, 'Pa&use\tCtrl+U', 'U', PAUSE),
		(FLAG_ALL, ENTRY, '&Stop\tCtrl+H', 'H', STOP),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Play &node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play &from node', None, PLAYFROM),
		(FLAG_BOSTON|FLAG_CMIF|FLAG_SNAP, SEP,),
		(FLAG_BOSTON|FLAG_SNAP, DYNAMICCASCADE, 'Custom &tests', USERGROUPS),
		(FLAG_CMIF, DYNAMICCASCADE, 'Visible &channels', CHANNELS),
		)),


	('&Linking', (
		(FLAG_ALL, ENTRY, 'C&reate whole node anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, '&Finish hyperlink to selection', None, FINISH_LINK),
##		(FLAG_PRO, ENTRY, '&Anchors...', 'T', ANCHORS),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, 'Create s&ync arc from selection...', None, FINISH_ARC),
		(FLAG_PRO, DYNAMICCASCADE, 'Select &sync arc', SYNCARCS),
		)),

	('&View', (
		(FLAG_ALL, ENTRY, '&Expand/Collapse\tCtrl+I', None, EXPAND),
		(FLAG_ALL, ENTRY, 'E&xpand all', None, EXPANDALL),
		(FLAG_ALL, ENTRY, '&Collapse all', None, COLLAPSEALL),
		(FLAG_PRO, SEP,),
		(FLAG_PRO, ENTRY, '&Zoom in', None, CANVAS_WIDTH),
		(FLAG_PRO, ENTRY, '&Fit in Window', None, CANVAS_RESET),
		(FLAG_ALL, SEP,),
		(FLAG_PRO, TOGGLE, 'Show/Hide unused c&hannels', None, TOGGLE_UNUSED),
		(FLAG_PRO, TOGGLE, 'Sync &arcs', None, TOGGLE_ARCS),
		(FLAG_PRO, TOGGLE, '&Image thumbnails', None, THUMBNAIL),
		(FLAG_ALL, ENTRY, 'Check bandwidth &usage', None, COMPUTE_BANDWIDTH),
		(FLAG_PRO, TOGGLE, '&Bandwidth usage strip', None, TOGGLE_BWSTRIP),
		(FLAG_PRO, TOGGLE, 'Show &Playable', None, PLAYABLE),
		(FLAG_ALL, CASCADE, 'Sho&w Time in Structure', (
			(FLAG_ALL, TOGGLE, '&Whole Document, Adaptive', None, TIMESCALE),
			(FLAG_ALL, TOGGLE, '&Selection Only, Adaptive', None, LOCALTIMESCALE),
			(FLAG_ALL, TOGGLE, 'Selection Only, &Fixed', None, CORRECTLOCALTIMESCALE),
			)),
		(FLAG_CMIF, SEP,),
		(FLAG_CMIF, TOGGLE, '&Timeline view follows player', None, SYNCCV),
##		(FLAG_ALL, DYNAMICCASCADE, '&Layout navigation', LAYOUTS),
		(FLAG_ALL, TOGGLE, 'Show A&ll Properties', None, SHOWALLPROPERTIES),
		)
	 ),
 
	('&Window', (
		(FLAG_ALL, ENTRY, 'Cl&ose\tCtrl+W', 'W', CLOSE_ACTIVE_WINDOW),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Cascade', 'C', CASCADE_WNDS),
		(FLAG_ALL, ENTRY, 'Tile &Horizontally', 'H', TILE_HORZ),
		(FLAG_ALL, ENTRY, 'Tile &Vertically', 'T', TILE_VERT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Player\tF5', '1', PLAYERVIEW),
##		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Structure view\tF6', '3', HIERARCHYVIEW),
		(FLAG_ALL, ENTRY, '&Timeline view\tF7', '4', CHANNELVIEW),
		(FLAG_PRO|FLAG_SNAP, ENTRY, '&Layout view\tF8', '2', LAYOUTVIEW2),
##		(FLAG_PRO, ENTRY, '&Layout view\tF8', '2', LAYOUTVIEW),
#		(FLAG_ALL, ENTRY, 'Temporal view', '8', TEMPORALVIEW),
##		(FLAG_ALL, SEP,),
		(FLAG_PRO, ENTRY, 'H&yperlinks', '5', LINKVIEW),
		(FLAG_BOSTON, ENTRY, 'C&ustom tests', '6', USERGROUPVIEW),
		(FLAG_BOSTON, ENTRY, 'T&ransitions', None, TRANSITIONVIEW),
##		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'SMIL Sourc&e...', '7', SOURCEVIEW),
		)),

	('&Help', (
		(FLAG_ALL, ENTRY, '&Contents', None, HELP_CONTENTS),
		(FLAG_ALL, ENTRY, 'Context &Help', None, HELP),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'GRiNS on the &Web', None,GRINS_WEB),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Quick Start Guide', None, GRINS_QSG),
		(FLAG_ALL, ENTRY, '&Tutorial', None, GRINS_TUTORIAL),#		(FLAG_ALL, ENTRY, 'Paste &before', None, PASTE_BEFORE),
#		(FLAG_ALL, ENTRY, 'Paste &in

		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&About GRiNS...', None, ABOUT_GRINS))))

NODOC_MENUBAR=(MENUBAR[0],MENUBAR[7])
if curflags() & FLAG_SNAP:
	# remove Insert menu in Snap! version
	MENUBAR = MENUBAR[:2] + MENUBAR[3:]

#
# Popup menus for various states
#

POPUP_HVIEW_LEAF = (
		# XXXX Need to add the "new xxx node" commands for the
		# light version
		(FLAG_PRO, ENTRY, '&New node...', None, NEW_AFTER),
		(FLAG_PRO, ENTRY, 'New node &before...', None, NEW_BEFORE),
		(FLAG_PRO, ENTRY, 'Con&vert to SMIL 2.0', None, RPCONVERT),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
###		(FLAG_ALL, ENTRY, '&Paste', None, PASTE_UNDER),
		(FLAG_ALL, ENTRY, 'Paste bef&ore', None, PASTE_BEFORE),
		(FLAG_ALL, ENTRY, 'Paste a&fter', None, PASTE_AFTER),
		(FLAG_ALL, ENTRY, 'Pa&ste file', None, PASTE_FILE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_ALL, CASCADE, '&Insert', (
			(FLAG_ALL, CASCADE, '&Image node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_IMAGE),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_IMAGE),
				)),
			(FLAG_G2, CASCADE, 'Sli&deshow node', (
				(FLAG_G2, ENTRY, '&Before', None, NEW_BEFORE_SLIDESHOW),
				(FLAG_G2, ENTRY, '&After', None, NEW_AFTER_SLIDESHOW),
				)),
			(FLAG_ALL, CASCADE, '&Text node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_TEXT),
				)),
			(FLAG_SMIL_1_0, CASCADE, '&HTML node', (
				(FLAG_SMIL_1_0, ENTRY, '&Before', None, NEW_BEFORE_HTML),
				(FLAG_SMIL_1_0, ENTRY, '&After', None, NEW_AFTER_HTML),
				)),
			(FLAG_ALL, CASCADE, 'S&ound node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SOUND),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SOUND),
				)),
			(FLAG_ALL, CASCADE, '&Video node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_VIDEO),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_VIDEO),
				)),
			(FLAG_ALL, CASCADE, 'Animation node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_ANIMATION),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_ANIMATION),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_ANIMATION),
				)),
			(FLAG_ALL, CASCADE, '&Parallel node', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_PAR),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PAR),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PAR),
				)),
			(FLAG_ALL, CASCADE, '&Sequential node', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SEQ),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SEQ),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SEQ),
				)),
			(FLAG_ALL, CASCADE, 'S&witch node', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SWITCH),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SWITCH),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SWITCH),
				)),
			(FLAG_PRO, ENTRY, '&Before...', None, NEW_BEFORE),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'P&lay node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play &from node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Set this node as current begin event &source', None, CREATE_BEGIN_EVENT_SOURCE),
		(FLAG_ALL, ENTRY, 'Create begin event on this node', None, CREATE_BEGIN_EVENT_DESTINATION),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Create &whole node anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish &hyperlink to selection', None, FINISH_LINK),
		(FLAG_ALL, SEP,),
##		(FLAG_PRO, ENTRY, '&Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
##		(FLAG_PRO, ENTRY, '&Anchors...', None, ANCHORS),
		(FLAG_ALL, ENTRY, '&Edit content', None, CONTENT),
)

POPUP_HVIEW_NONE = (
	(FLAG_ALL, ENTRY, '&New node...', None, NEW_AFTER)
	)

POPUP_HVIEW_TRANS = (
		(FLAG_ALL, DYNAMICCASCADE, '&Transition', TRANSITION),
		)

POPUP_HVIEW_SLIDE = (
		# XXXX Need to add the "new xxx node" commands for the
		# light version
		(FLAG_G2, ENTRY, 'Cu&t', None, CUT),
		(FLAG_G2, ENTRY, '&Copy', None, COPY),
		(FLAG_G2, ENTRY, '&Paste', None, PASTE_AFTER),
		(FLAG_G2, ENTRY, 'Paste bef&ore', None, PASTE_BEFORE),
		(FLAG_G2, ENTRY, 'Pa&ste file', None, PASTE_FILE),
		(FLAG_G2, SEP,),
		(FLAG_G2, ENTRY, '&Delete', None, DELETE),
		(FLAG_G2, CASCADE, 'Insert Image &Node', (
			(FLAG_G2, ENTRY, '&Before', None, NEW_BEFORE_IMAGE),
			(FLAG_G2, ENTRY, '&After', None, NEW_AFTER_IMAGE),
			)),
		(FLAG_G2, SEP,),
		(FLAG_G2, ENTRY, 'P&roperties...', None, ATTRIBUTES),
		(FLAG_G2, ENTRY, '&Edit content', None, CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		(FLAG_PRO, ENTRY, '&New node...', None, NEW_AFTER),
		(FLAG_PRO, CASCADE, 'Ne&w node special', (
			(FLAG_PRO, ENTRY, '&Before...', None, NEW_BEFORE),
			(FLAG_PRO, ENTRY, '&Within...', None, NEW_UNDER),
			)),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, 'Cu&t', None, CUT),
		(FLAG_ALL, ENTRY, '&Copy', None, COPY),
		(FLAG_ALL, ENTRY, '&Paste', None, PASTE_UNDER),
#		(FLAG_ALL, CASCADE, 'Paste &special', (
#			(FLAG_ALL, ENTRY, '&Before', None, PASTE_BEFORE),
#			(FLAG_ALL, ENTRY, '&Within', None, PASTE_UNDER),
#			)),
		(FLAG_ALL, ENTRY, 'Paste &file', None, PASTE_FILE),
		(FLAG_ALL, SEP,),
#		(FLAG_PRO, ENTRY, 'Edit in Temporal view', None, EDIT_TVIEW),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_ALL, CASCADE, '&Insert', (
			(FLAG_ALL, CASCADE, '&Image node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_IMAGE),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_IMAGE),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_IMAGE),
				)),
			(FLAG_G2, CASCADE, 'Sli&deshow node', (
				(FLAG_G2, ENTRY, '&Before', None, NEW_BEFORE_SLIDESHOW),
				(FLAG_G2, ENTRY, '&After', None, NEW_AFTER_SLIDESHOW),
				(FLAG_G2, ENTRY, '&Within', None, NEW_UNDER_SLIDESHOW),
				)),
			(FLAG_ALL, CASCADE, '&Text node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_TEXT),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_TEXT),
				)),
			(FLAG_SMIL_1_0, CASCADE, '&HTML node', (
				(FLAG_SMIL_1_0, ENTRY, '&Before', None, NEW_BEFORE_HTML),
				(FLAG_SMIL_1_0, ENTRY, '&After', None, NEW_AFTER_HTML),
				(FLAG_SMIL_1_0, ENTRY, '&Within', None, NEW_UNDER_HTML),
				)),
			(FLAG_ALL, CASCADE, 'S&ound node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SOUND),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SOUND),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SOUND),
				)),
			(FLAG_ALL, CASCADE, '&Video node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_VIDEO),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_VIDEO),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_VIDEO),
				)),
			(FLAG_ALL, CASCADE, 'Animation node', (
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_ANIMATION),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_ANIMATION),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_ANIMATION),
				)),
			(FLAG_ALL, CASCADE, '&Parallel node', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_PAR),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_PAR),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_PAR),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_PAR),
				)),
			(FLAG_ALL, CASCADE, '&Sequential node', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SEQ),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SEQ),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SEQ),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SEQ),
				)),
			(FLAG_ALL, CASCADE, 'S&witch node', (
				(FLAG_ALL, ENTRY, '&Parent', None, NEW_SWITCH),
				(FLAG_ALL, ENTRY, '&Before', None, NEW_BEFORE_SWITCH),
				(FLAG_ALL, ENTRY, '&After', None, NEW_AFTER_SWITCH),
				(FLAG_ALL, ENTRY, '&Within', None, NEW_UNDER_SWITCH),
				)),
			(FLAG_PRO, ENTRY, '&Before...', None, NEW_BEFORE),
			(FLAG_PRO, ENTRY, '&Within...', None, NEW_UNDER),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'P&lay node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Pla&y from node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Expand/Collapse', None, EXPAND),
		(FLAG_ALL, ENTRY, 'E&xpand all', None, EXPANDALL),
		(FLAG_ALL, ENTRY, 'C&ollapse all', None, COLLAPSEALL),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Set this node as current begin event &source', None, CREATE_BEGIN_EVENT_SOURCE),
		(FLAG_ALL, ENTRY, 'Create begin event on this node', None, CREATE_BEGIN_EVENT_DESTINATION),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Finish hyperlin&k to selection', None, FINISH_LINK),
		(FLAG_ALL, SEP,),
##		(FLAG_PRO, ENTRY, '&Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
##		(FLAG_PRO, ENTRY, '&Anchors...', None, ANCHORS),
)

POPUP_CVIEW_NONE = (
		(FLAG_ALL, ENTRY, '&New region', 'M', NEW_REGION),
)

POPUP_CVIEW_BWSTRIP = (
		(FLAG_ALL, ENTRY, "&14k4", None, BANDWIDTH_14K4),
		(FLAG_ALL, ENTRY, "&28k8", None, BANDWIDTH_28K8),
		(FLAG_ALL, ENTRY, "&ISDN", None, BANDWIDTH_ISDN),
		(FLAG_ALL, ENTRY, "&T1 (1 Mbps)", None, BANDWIDTH_T1),
		(FLAG_ALL, ENTRY, "&LAN (10 Mbps)", None, BANDWIDTH_LAN),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, "&Other...", None, BANDWIDTH_OTHER),
		)

POPUP_CVIEW_CHANNEL = (
		(FLAG_PRO, ENTRY, '&New', None, NEW_REGION),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Move region', None, MOVE_REGION),
		(FLAG_ALL, ENTRY, '&Copy region', None, COPY_REGION),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, '&Properties...', None, ATTRIBUTES),

)

POPUP_CVIEW_NODE = (
		(FLAG_ALL, ENTRY, '&Play node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from &node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Create &whole node anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish hyperlin&k to selection...', None, FINISH_LINK),
		(FLAG_ALL, ENTRY, 'Create &syncarc from selection...', None, FINISH_ARC),
		(FLAG_ALL, SEP,),
##		(FLAG_PRO, ENTRY, '&Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'P&roperties...', None, ATTRIBUTES),
##		(FLAG_PRO, ENTRY, '&Anchors...', None, ANCHORS),
		(FLAG_ALL, ENTRY, '&Edit content', None, CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		(FLAG_PRO, ENTRY, '&Properties...', None, ATTRIBUTES),
		(FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, '&Delete', None, DELETE),
)

POPUP_EVENT = (
	(FLAG_ALL, ENTRY, 'Find event source', None, FIND_EVENT_SOURCE),
	(FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
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
		(FLAG_QT, ENTRY, 'Publish for &QuickTime...', None, EXPORT_QT),
		(FLAG_QT, ENTRY, 'Pu&blish for QuickTime and upload...', None, UPLOAD_QT),
		(FLAG_G2, ENTRY, 'Publish for &G2...', None, EXPORT_G2),
		(FLAG_G2, ENTRY, 'Pu&blish for G2 and upload...', None, UPLOAD_G2),
		(FLAG_QT | FLAG_G2, SEP,),
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
