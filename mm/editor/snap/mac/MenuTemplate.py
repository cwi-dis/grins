__version__ = "$Id$"

#
#    Menu mapping for the GRiNS Snap! editor.
#


from usercmd import *
from Menus import *

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE, SPECIAL] = range(6)

# Types of menu entries
[ENTRY, TOGGLE, SEP, CASCADE, DYNAMICCASCADE] = range(5)

# Some commands are optional, depending on preference settings:
from flags import *

UNUSED_COMMANDS=()

MENUBAR=(
	(FLAG_ALL, CASCADE, 'File', (
		(FLAG_ALL, ENTRY, 'New', 'N', NEW_DOCUMENT),
		(FLAG_ALL, ENTRY, 'Open...', 'O', OPENFILE),
		(FLAG_ALL, ENTRY, 'Open URL...', 'O', OPEN),
		(FLAG_ALL, DYNAMICCASCADE, 'Open recent', OPEN_RECENT),
		(FLAG_ALL, ENTRY, 'Close', None, CLOSE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Save', 'S', SAVE),
		(FLAG_ALL, ENTRY, 'Save as...', None, SAVE_AS),
		(FLAG_ALL, ENTRY, 'Revert to saved', None, RESTORE),
		(FLAG_ALL, SEP,),
		(FLAG_QT, ENTRY, 'Publish for QuickTime...', None, EXPORT_QT),
		(FLAG_QT, ENTRY, 'Publish for QuickTime and upload...', None, UPLOAD_QT),
		(FLAG_G2, ENTRY, 'Publish for G2...', None, EXPORT_G2),
		(FLAG_G2, ENTRY, 'Publish for G2 and upload...', None, UPLOAD_G2),
                # TODO: These should not appear on all versions of GRiNS!
                (FLAG_ALL, ENTRY, 'Publish for Windows Media...', None, EXPORT_WMP), # mjvdg 11-oct-2000
                (FLAG_ALL, ENTRY, 'Publish for Windows Media and upload...', None, UPLOAD_WMP),
                
		(FLAG_SMIL_1_0, ENTRY, 'Publish for SMIL 2.0...', None, EXPORT_SMIL),
		(FLAG_SMIL_1_0, ENTRY, 'Publish for SMIL 2.0 and upload...', None, UPLOAD_SMIL),
		(FLAG_SMIL_1_0 | FLAG_QT | FLAG_G2, SEP,),
		(FLAG_ALL, ENTRY, 'Document Properties...', None, PROPERTIES),
		(FLAG_DBG, SEP,),
		(FLAG_DBG, CASCADE, 'Debug', (
			(FLAG_DBG, ENTRY, 'Dump scheduler data', None, SCHEDDUMP),
			(FLAG_DBG, TOGGLE, 'Enable call tracing', None, TRACE),
			(FLAG_DBG, ENTRY, 'Enter debugger', None, DEBUG),
			(FLAG_DBG, ENTRY, 'Abort', None, CRASH),
			(FLAG_DBG, TOGGLE, 'Show log/debug window', None, CONSOLE),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Check for GRiNS update...', None, CHECKVERSION),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Quit', 'Q', EXIT),
		)),

	(FLAG_ALL, CASCADE, 'Edit', (
		(FLAG_ALL, ENTRY, 'Undo', 'Z', UNDO),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Cut', 'X', CUT),
		(FLAG_ALL, ENTRY, 'Copy', 'C', COPY),
		(FLAG_ALL, ENTRY, 'Paste', 'V', PASTE),
#		(FLAG_ALL, CASCADE, 'Paste special', (
#			(FLAG_ALL, ENTRY, 'Before', None, PASTE_BEFORE),
##			(FLAG_ALL, ENTRY, 'After', None, PASTE_AFTER),
#			(FLAG_ALL, ENTRY, 'Within', None, PASTE_UNDER),
#			)),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
		(FLAG_ALL, SEP,),
		# (FLAG_PRO, ENTRY, 'New node...', None, NEW_AFTER),
		# (FLAG_PRO, ENTRY, 'New channel', None, NEW_CHANNEL),

## Windows dialogs apparently don't use usercmd commands.
##		# (FLAG_PRO, ENTRY, 'New layout', None, NEW_LAYOUT),
		# (FLAG_PRO, SEP,),
		# (FLAG_PRO, ENTRY, 'Move channel', None, MOVE_CHANNEL),
		# (FLAG_PRO, ENTRY, 'Copy channel', None, COPY_CHANNEL),
		(FLAG_CMIF, ENTRY, 'Toggle channel state', None, TOGGLE_ONOFF),
##		# (FLAG_PRO, ENTRY, 'Edit Source...', None, EDITSOURCE),
		# (FLAG_PRO, SEP,),
##		# (FLAG_PRO, ENTRY, 'Info...', 'I', INFO),
		(FLAG_ALL, ENTRY, 'Properties...', 'A', ATTRIBUTES),
		(FLAG_ALL, ENTRY, 'Edit Content...', 'E', CONTENT),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Preferences...', None, PREFERENCES),
		)),

# 	(FLAG_ALL, CASCADE, 'Insert', (
# 		(FLAG_ALL, CASCADE, 'Image node', (
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_IMAGE),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_IMAGE),
# 		)),
# 		(FLAG_G2, CASCADE, 'Slideshow node', (
# 			(FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
# 			(FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
# 			(FLAG_G2, ENTRY, 'Within', None, NEW_UNDER_SLIDESHOW),
# 		)),
# 		(FLAG_ALL, CASCADE, 'Text node', (
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_TEXT),
# 		)),
# 		(FLAG_SMIL_1_0, CASCADE, 'HTML node', (
# 			(FLAG_SMIL_1_0, ENTRY, 'Before', None, NEW_BEFORE_HTML),
# 			(FLAG_SMIL_1_0, ENTRY, 'After', None, NEW_AFTER_HTML),
# 			(FLAG_SMIL_1_0, ENTRY, 'Within', None, NEW_UNDER_HTML),
# 			)),
# 		(FLAG_ALL, CASCADE, 'Sound node', (
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SOUND),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SOUND),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SOUND),
# 		)),
# 		(FLAG_ALL, CASCADE, 'Video node', (
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_VIDEO),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_VIDEO),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_VIDEO),
# 		)),
# 		(FLAG_ALL, CASCADE, 'Animation node', (
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ANIMATION),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ANIMATION),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ANIMATION),
# 		)),
# 		(FLAG_ALL, CASCADE, 'Parallel node', (
# 			(FLAG_ALL, ENTRY, 'Parent', None, NEW_PAR),
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PAR),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PAR),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_PAR),
# 		)),
# 		(FLAG_ALL, CASCADE, 'Sequential node', (
# 			(FLAG_ALL, ENTRY, 'Parent', None, NEW_SEQ),
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SEQ),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SEQ),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SEQ),
# 		)),
# 		(FLAG_ALL, CASCADE, 'Switch node', (
# 			(FLAG_ALL, ENTRY, 'Parent', None, NEW_ALT),
# 			(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ALT),
# 			(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ALT),
# 			(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ALT),
# 		)),
# 		(FLAG_CMIF, CASCADE, 'Choice node', (
# 			(FLAG_CMIF, ENTRY, 'Parent', None, NEW_CHOICE),
# 			(FLAG_CMIF, ENTRY, 'Before', None, NEW_BEFORE_CHOICE),
# 			(FLAG_CMIF, ENTRY, 'After', None, NEW_AFTER_CHOICE),
# 			(FLAG_CMIF, ENTRY, 'Within', None, NEW_UNDER_CHOICE),
# 		)),
# 		# (FLAG_PRO, ENTRY, 'Before...', None, NEW_BEFORE),
# 		# (FLAG_PRO, ENTRY, 'Within...', None, NEW_UNDER),
# 		)),
	(FLAG_ALL, CASCADE, 'Play', (
		(FLAG_ALL, ENTRY, 'Play', 'P', PLAY),
		(FLAG_ALL, ENTRY, 'Pause', 'U', PAUSE),
		(FLAG_ALL, ENTRY, 'Stop', 'H', STOP),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Play node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from node', None, PLAYFROM),
		(FLAG_BOSTON|FLAG_CMIF, SEP,),
		(FLAG_BOSTON, DYNAMICCASCADE, 'Custom tests', USERGROUPS),
		(FLAG_CMIF, DYNAMICCASCADE, 'Visible channels', CHANNELS),
		)),


	(FLAG_ALL, CASCADE, 'Linking', (
		(FLAG_ALL, ENTRY, 'Create whole node anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish hyperlink to selection', None, FINISH_LINK),
##		# (FLAG_PRO, ENTRY, 'Anchors...', 'T', ANCHORS),
		# (FLAG_PRO, SEP,),
		# (FLAG_PRO, ENTRY, 'Create sync arc from selection...', None, FINISH_ARC),
		# (FLAG_PRO, DYNAMICCASCADE, 'Select sync arc', SYNCARCS),
		)),

	(FLAG_ALL, CASCADE, 'View', (
		(FLAG_ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
		(FLAG_ALL, ENTRY, 'Expand all', None, EXPANDALL),
		(FLAG_ALL, ENTRY, 'Collapse all', None, COLLAPSEALL),
		# (FLAG_PRO, SEP,),
		# (FLAG_PRO, ENTRY, 'Zoom in', None, CANVAS_WIDTH),
		# (FLAG_PRO, ENTRY, 'Fit in Window', None, CANVAS_RESET),
		# (FLAG_PRO, SEP,),
		# (FLAG_PRO, ENTRY, 'Synchronize selection', None, PUSHFOCUS),
		(FLAG_ALL, SEP,),
#		# (FLAG_PRO, TOGGLE, 'Show/Hide unused channels', None, TOGGLE_UNUSED),
		(FLAG_ALL, TOGGLE, 'Sync arcs', None, TOGGLE_ARCS),
		(FLAG_ALL, TOGGLE, 'Image thumbnails', None, THUMBNAIL),
		(FLAG_ALL, ENTRY, 'Check bandwidth usage', None, COMPUTE_BANDWIDTH),
		(FLAG_ALL, TOGGLE, 'Bandwidth usage strip', None, TOGGLE_BWSTRIP),
		(FLAG_ALL, TOGGLE, 'Show Playable', None, PLAYABLE),
		(FLAG_ALL, TOGGLE, 'Show Durations', None, TIMESCALE),
#		(FLAG_CMIF, SEP,),
#		(FLAG_CMIF, TOGGLE, 'Timeline view follows player', None, SYNCCV),
#		(FLAG_CMIF, CASCADE, 'Minidoc navigation', (
#			(FLAG_CMIF, ENTRY, 'Next', None, NEXT_MINIDOC),
#			(FLAG_CMIF, ENTRY, 'Previous', None, PREV_MINIDOC),
#			(FLAG_CMIF, DYNAMICCASCADE, 'Ancestors', ANCESTORS),
#			(FLAG_CMIF, DYNAMICCASCADE, 'Descendants', DESCENDANTS),
#			(FLAG_CMIF, DYNAMICCASCADE, 'Siblings', SIBLINGS),
#			)),
##		(FLAG_ALL, DYNAMICCASCADE, 'Layout navigation', LAYOUTS),
                )
         ),
 
	(FLAG_ALL, CASCADE, 'Windows', (
		(FLAG_ALL, ENTRY, 'Close', 'W', CLOSE_WINDOW),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Player', '1', PLAYERVIEW),
##		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Presentation view', '3', HIERARCHYVIEW),
#		# (FLAG_PRO, ENTRY, 'Timeline view', '4', CHANNELVIEW),
#		# (FLAG_PRO, ENTRY, 'Layout view', '2', LAYOUTVIEW),
##		(FLAG_ALL, SEP,),
#		# (FLAG_PRO, ENTRY, 'Hyperlinks', '5', LINKVIEW),
#		(FLAG_BOSTON, ENTRY, 'User groups', '6', USERGROUPVIEW),
#		(FLAG_BOSTON, ENTRY, 'Transitions', None, TRANSITIONVIEW),
#		(FLAG_BOSTON, ENTRY, 'layout view 2', None, LAYOUTVIEW2),
##		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Source', '7', SOURCE),
		)),

        )


#
# Popup menus for various states
#
POPUP_HVIEW_LEAF = (
		# XXXX Need to add the "new xxx node" commands for the
		# light version
		# (FLAG_PRO, ENTRY, 'New node...', None, NEW_AFTER),
		# (FLAG_PRO, ENTRY, 'New node before...', None, NEW_BEFORE),
		# (FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, 'Cut', None, CUT),
		(FLAG_ALL, ENTRY, 'Copy', None, COPY),
		(FLAG_ALL, ENTRY, 'Paste', None, PASTE_AFTER),
		(FLAG_ALL, ENTRY, 'Paste before', None, PASTE_BEFORE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
		(FLAG_ALL, CASCADE, 'Insert', (
			(FLAG_ALL, CASCADE, 'Image node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_IMAGE),
				)),
			(FLAG_G2, CASCADE, 'Slideshow node', (
				(FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
				(FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
				)),
			(FLAG_ALL, CASCADE, 'Text node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
				)),
			(FLAG_SMIL_1_0, CASCADE, 'HTML node', (
				(FLAG_SMIL_1_0, ENTRY, 'Before', None, NEW_BEFORE_HTML),
				(FLAG_SMIL_1_0, ENTRY, 'After', None, NEW_AFTER_HTML),
				)),
			(FLAG_ALL, CASCADE, 'Sound node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SOUND),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SOUND),
				)),
			(FLAG_ALL, CASCADE, 'Video node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_VIDEO),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_VIDEO),
				)),
			(FLAG_ALL, CASCADE, 'Animation node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ANIMATION),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ANIMATION),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ANIMATION),
				)),
			(FLAG_ALL, CASCADE, 'Parallel node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_PAR),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PAR),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PAR),
				)),
			(FLAG_ALL, CASCADE, 'Sequential node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_SEQ),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SEQ),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SEQ),
				)),
			(FLAG_ALL, CASCADE, 'Switch node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_ALT),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ALT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ALT),
				)),
			(FLAG_CMIF, CASCADE, 'Choice node', (
				(FLAG_CMIF, ENTRY, 'Parent', None, NEW_CHOICE),
				(FLAG_CMIF, ENTRY, 'Before', None, NEW_BEFORE_CHOICE),
				(FLAG_CMIF, ENTRY, 'After', None, NEW_AFTER_CHOICE),
				)),
			# (FLAG_PRO, ENTRY, 'Before...', None, NEW_BEFORE),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Play node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Create whole node anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish hyperlink to selection', None, FINISH_LINK),
		(FLAG_ALL, SEP,),
##		# (FLAG_PRO, ENTRY, 'Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
##		# (FLAG_PRO, ENTRY, 'Anchors...', None, ANCHORS),
		(FLAG_ALL, ENTRY, 'Edit content', None, CONTENT),
)

POPUP_HVIEW_SLIDE = (
		# XXXX Need to add the "new xxx node" commands for the
		# light version
		(FLAG_G2, ENTRY, 'Cut', None, CUT),
		(FLAG_G2, ENTRY, 'Copy', None, COPY),
		(FLAG_G2, ENTRY, 'Paste', None, PASTE_AFTER),
		(FLAG_G2, ENTRY, 'Paste before', None, PASTE_BEFORE),
		(FLAG_G2, SEP,),
		(FLAG_G2, ENTRY, 'Delete', None, DELETE),
		(FLAG_G2, CASCADE, 'Insert Image Node', (
			(FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
			(FLAG_G2, ENTRY, 'After', None, NEW_AFTER_IMAGE),
			)),
		(FLAG_G2, SEP,),
		(FLAG_G2, ENTRY, 'Properties...', None, ATTRIBUTES),
		(FLAG_G2, ENTRY, 'Edit content', None, CONTENT),
)

POPUP_HVIEW_STRUCTURE = (
		# (FLAG_PRO, ENTRY, 'New node...', None, NEW_AFTER),
		# (FLAG_PRO, CASCADE, 'New node special', (
			# (FLAG_PRO, ENTRY, 'Before...', None, NEW_BEFORE),
			# (FLAG_PRO, ENTRY, 'Within...', None, NEW_UNDER),
                 #)

		# (FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, 'Cut', None, CUT),
		(FLAG_ALL, ENTRY, 'Copy', None, COPY),
		(FLAG_ALL, ENTRY, 'Paste', None, PASTE_AFTER),
		(FLAG_ALL, CASCADE, 'Paste special', (
			(FLAG_ALL, ENTRY, 'Before', None, PASTE_BEFORE),
			(FLAG_ALL, ENTRY, 'Within', None, PASTE_UNDER),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
		(FLAG_ALL, CASCADE, 'Insert', (
			(FLAG_ALL, CASCADE, 'Image node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_IMAGE),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_IMAGE),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_IMAGE),
				)),
			(FLAG_G2, CASCADE, 'Slideshow node', (
				(FLAG_G2, ENTRY, 'Before', None, NEW_BEFORE_SLIDESHOW),
				(FLAG_G2, ENTRY, 'After', None, NEW_AFTER_SLIDESHOW),
				(FLAG_G2, ENTRY, 'Within', None, NEW_UNDER_SLIDESHOW),
				)),
			(FLAG_ALL, CASCADE, 'Text node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_TEXT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_TEXT),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_TEXT),
				)),
			(FLAG_SMIL_1_0, CASCADE, 'HTML node', (
				(FLAG_SMIL_1_0, ENTRY, 'Before', None, NEW_BEFORE_HTML),
				(FLAG_SMIL_1_0, ENTRY, 'After', None, NEW_AFTER_HTML),
				(FLAG_SMIL_1_0, ENTRY, 'Within', None, NEW_UNDER_HTML),
				)),
			(FLAG_ALL, CASCADE, 'Sound node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SOUND),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SOUND),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SOUND),
				)),
			(FLAG_ALL, CASCADE, 'Video node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_VIDEO),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_VIDEO),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_VIDEO),
				)),
			(FLAG_ALL, CASCADE, 'Animation node', (
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ANIMATION),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ANIMATION),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ANIMATION),
				)),
			(FLAG_ALL, CASCADE, 'Parallel node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_PAR),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_PAR),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_PAR),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_PAR),
				)),
			(FLAG_ALL, CASCADE, 'Sequential node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_SEQ),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_SEQ),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_SEQ),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_SEQ),
				)),
			(FLAG_ALL, CASCADE, 'Switch node', (
				(FLAG_ALL, ENTRY, 'Parent', None, NEW_ALT),
				(FLAG_ALL, ENTRY, 'Before', None, NEW_BEFORE_ALT),
				(FLAG_ALL, ENTRY, 'After', None, NEW_AFTER_ALT),
				(FLAG_ALL, ENTRY, 'Within', None, NEW_UNDER_ALT),
				)),
			(FLAG_CMIF, CASCADE, 'Choice node', (
				(FLAG_CMIF, ENTRY, 'Parent', None, NEW_CHOICE),
				(FLAG_CMIF, ENTRY, 'Before', None, NEW_BEFORE_CHOICE),
				(FLAG_CMIF, ENTRY, 'After', None, NEW_AFTER_CHOICE),
				(FLAG_CMIF, ENTRY, 'Within', None, NEW_UNDER_CHOICE),
				)),
			# (FLAG_PRO, ENTRY, 'Before...', None, NEW_BEFORE),
			# (FLAG_PRO, ENTRY, 'Within...', None, NEW_UNDER),
			)),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Play node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Expand/Collapse', None, EXPAND),
		(FLAG_ALL, ENTRY, 'Expand all', None, EXPANDALL),
		(FLAG_ALL, ENTRY, 'Collapse all', None, COLLAPSEALL),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Finish hyperlink to selection', None, FINISH_LINK),
		(FLAG_ALL, SEP,),
##		# (FLAG_PRO, ENTRY, 'Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
##		# (FLAG_PRO, ENTRY, 'Anchors...', None, ANCHORS),
)

POPUP_CVIEW_NONE = (
		(FLAG_ALL, ENTRY, 'New channel', 'M', NEW_CHANNEL),
)

POPUP_CVIEW_BWSTRIP = (
		(FLAG_ALL, ENTRY, "14k4", None, BANDWIDTH_14K4),
		(FLAG_ALL, ENTRY, "28k8", None, BANDWIDTH_28K8),
		(FLAG_ALL, ENTRY, "ISDN", None, BANDWIDTH_ISDN),
		(FLAG_ALL, ENTRY, "T1 (1 Mbps)", None, BANDWIDTH_T1),
		(FLAG_ALL, ENTRY, "LAN (10 Mbps)", None, BANDWIDTH_LAN),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, "Other...", None, BANDWIDTH_OTHER),
		)

POPUP_CVIEW_CHANNEL = (
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Move channel', None, MOVE_CHANNEL),
		(FLAG_ALL, ENTRY, 'Copy channel', None, COPY_CHANNEL),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),

)

POPUP_CVIEW_NODE = (
		(FLAG_ALL, ENTRY, 'Play node', None, PLAYNODE),
		(FLAG_ALL, ENTRY, 'Play from node', None, PLAYFROM),
		(FLAG_ALL, SEP,),
		(FLAG_ALL, ENTRY, 'Create whole node anchor', None, CREATEANCHOR),
		(FLAG_ALL, ENTRY, 'Finish hyperlink to selection...', None, FINISH_LINK),
		(FLAG_ALL, ENTRY, 'Create syncarc from selection...', None, FINISH_ARC),
		(FLAG_ALL, SEP,),
##		# (FLAG_PRO, ENTRY, 'Info...', None, INFO),
		(FLAG_ALL, ENTRY, 'Properties...', None, ATTRIBUTES),
##		# (FLAG_PRO, ENTRY, 'Anchors...', None, ANCHORS),
		(FLAG_ALL, ENTRY, 'Edit content', None, CONTENT),
)

POPUP_CVIEW_SYNCARC = (
		# (FLAG_PRO, ENTRY, 'Properties...', None, ATTRIBUTES),
		# (FLAG_PRO, SEP,),
		(FLAG_ALL, ENTRY, 'Delete', None, DELETE),
)

#
# Adornments
#
PLAYER_ADORNMENTS = {
	'toolbar': (
		(TOGGLE, 1000, STOP),
		(TOGGLE, 1500, PLAY),
		(TOGGLE, 2000, PAUSE),
		),
	'shortcuts': {
		' ': MAGIC_PLAY
	}
}
CHANNEL_ADORNMENTS = {
	'shortcuts': {
		' ': MAGIC_PLAY
	}
}

#
# CNTL resource for the toolbar and its height
TOOLBAR=(2500, 62, 22)
