__version__ = "$Id$"

#
# Commands, editor version
#

class _CommandBase:
	callback = None
	help = None
	dynamiccascade = 0
	def __init__(self, **kwargs):
		for attr, val in kwargs.items():
			setattr(self, attr, val)

class _DynamicCascade(_CommandBase):
	dynamiccascade = 1

#
# Global commands
#
class CLOSE_WINDOW(_CommandBase):
	help = 'Close this window'
class UNDO(_CommandBase): pass
class CUT(_CommandBase):
	help = 'Cut selected object'
class COPY(_CommandBase):
	help = 'Copy selected object'
class PASTE(_CommandBase):
	help = 'Paste copied/cut object'
class DELETE(_CommandBase):
	help = 'Delete selected object'
class HELP(_CommandBase):
	help = 'Display help'
class PREFERENCES(_CommandBase):
	help = 'Display application preferences'

#
# MainDialog commands
#
class NEW_DOCUMENT(_CommandBase):
	help = 'Create new document'
class OPEN(_CommandBase):
	help = 'Open existing document by URL'
class OPENFILE(_CommandBase):
	help = 'Open existing local file'
class OPEN_RECENT(_DynamicCascade):
	help = 'Open a recently used document'
class TRACE(_CommandBase):
	help = 'DEBUG: toggle trace flag'
class DEBUG(_CommandBase):
	help = 'DEBUG: enter Python debugger'
class CONSOLE(_CommandBase): pass
class EXIT(_CommandBase):
	help = 'Exit GRiNS'
class SAVE(_CommandBase):
	help = 'Save document'
class SAVE_AS(_CommandBase):
	help = 'Save document in new file'
class EXPORT_G2(_CommandBase):
	help = 'Create G2 SMIL file and media items'
class UPLOAD_G2(_CommandBase):
	help = 'Upload G2 SMIL file and media items to FTP server'
class EXPORT_QT(_CommandBase):
	help = 'Save document in new file as pure SMIL'
class UPLOAD_QT(_CommandBase):
	help = 'Upload pure SMIL document and media items to FTP server'
class EXPORT_SMIL(_CommandBase):
	help = 'Save document in new file as pure SMIL'
class UPLOAD_SMIL(_CommandBase):
	help = 'Upload pure SMIL document and media items to FTP server'
class EXPORT_WMP(_CommandBase):		# mjvdg 11-oct-2000
	help = 'Save document in a new file as a Windows Media document.'
class UPLOAD_WMP(_CommandBase):		# mjvdg 11-oct-2000
	help = 'Upload document as Windows Media document to FTP server';
class EXPORT_HTML(_CommandBase):
	help = 'Create a template webpage linking to your presentation'
class RESTORE(_CommandBase):
	help = 'Restore document from file (undo all unsaved changes)'
class PROPERTIES(_CommandBase):
	help = 'Edit document properties'
class SOURCE(_CommandBase):
	help = 'Show source'
class EDITSOURCE(_CommandBase):
	help = 'Edit source'
class CLOSE(_CommandBase):
	help = 'Close current document'
class CHECKVERSION(_CommandBase):
	help = 'Check for newer versions of the software'

#
# TopLevel commands
#
class PLAYERVIEW(_CommandBase):
	help = 'Show Player View'
class HIERARCHYVIEW(_CommandBase):
	help = 'Show Structure View'
class CHANNELVIEW(_CommandBase):
	help = 'Show Timeline View'
class LINKVIEW(_CommandBase):
	help = 'Show Hyperlink Editor'
class LAYOUTVIEW(_CommandBase):
	help = 'Show Layout View 2'
class USERGROUPVIEW(_CommandBase):
	help = 'Show User Group Editor'
class TRANSITIONVIEW(_CommandBase):
	help = 'Show Transition view'
class LAYOUTVIEW2(_CommandBase):
	help = 'Show new layout view'

# These are to hide the various views. They are basically
# a workaround for Windows, where the "close" command is
# implemented (for reasons unknown) by sending a command to
# the TopLevel.
class HIDE_PLAYERVIEW(_CommandBase): pass
class HIDE_HIERARCHYVIEW(_CommandBase): pass
class HIDE_CHANNELVIEW(_CommandBase): pass
class HIDE_LINKVIEW(_CommandBase): pass
class HIDE_LAYOUTVIEW(_CommandBase): pass
class HIDE_USERGROUPVIEW(_CommandBase): pass
class HIDE_SOURCE(_CommandBase): pass
class HIDE_TRANSITIONVIEW(_CommandBase): pass
class HIDE_LAYOUTVIEW2(_CommandBase): pass

#
# Player view commands
#
class PLAY(_CommandBase):
	help = 'Play document'
class PAUSE(_CommandBase):
	help = 'Pause playing document'
class STOP(_CommandBase):
	help = 'Stop playing document'
class MAGIC_PLAY(_CommandBase):
	help = 'Continue when paused, pause when playing, play when stopped'
class USERGROUPS(_DynamicCascade):
	help = 'User groups'
class CHANNELS(_DynamicCascade):
	help = 'Toggle channels on/off'
class SYNCCV(_CommandBase):
	help = 'Keep Channel view synchronized with player'
class CRASH(_CommandBase):
	help = 'DEBUG: Force a crash'
class SCHEDDUMP(_CommandBase):
	help = 'DEBUG: Dump scheduler data'

#
# Hierarchy view commands
#
class PASTE_BEFORE(_CommandBase):
	help = 'Paste copied/cut node before selected node'
class PASTE_AFTER(_CommandBase):
	help = 'Paste copied/cut node after selected node'
#PASTE_AFTER=PASTE
class PASTE_UNDER(_CommandBase):
	help = 'Paste copied/cut node under selected node'
PASTE = PASTE_UNDER			# mjvdg 27-oct-2000
class NEW_BEFORE(_CommandBase):
	help = 'Create new node before selected node'
class NEW_BEFORE_IMAGE(_CommandBase):
	help = 'Create new image node before selected node'
class NEW_BEFORE_TEXT(_CommandBase):
	help = 'Create new text node before selected node'
class NEW_BEFORE_HTML(_CommandBase):
	help = 'Create new HTML node before selected node'
class NEW_BEFORE_SOUND(_CommandBase):
	help = 'Create new sound node before selected node'
class NEW_BEFORE_VIDEO(_CommandBase):
	help = 'Create new video node before selected node'
class NEW_BEFORE_SLIDESHOW(_CommandBase):
	help = 'Create new slideshow node before selected node'
class NEW_BEFORE_SEQ(_CommandBase):
	help = 'Create new sequential node before selected node'
class NEW_BEFORE_PAR(_CommandBase):
	help = 'Create new parallel node before selected node'
class NEW_BEFORE_EXCL(_CommandBase):
	help = 'Create new exclusive node before selected node'
class NEW_BEFORE_CHOICE(_CommandBase):
	help = 'Create new choice node before selected node'
class NEW_BEFORE_ALT(_CommandBase):
	help = 'Create new alt node before selected node'
class NEW_BEFORE_ANIMATION(_CommandBase):
	help = 'Create new animation node before selected node'
class NEW_AFTER(_CommandBase):
	help = 'Create new node after selected node'
class NEW_AFTER_IMAGE(_CommandBase):
	help = 'Create new image node after selected node'
class NEW_AFTER_TEXT(_CommandBase):
	help = 'Create new text node after selected node'
class NEW_AFTER_HTML(_CommandBase):
	help = 'Create new HTML node after selected node'
class NEW_AFTER_SOUND(_CommandBase):
	help = 'Create new sound node after selected node'
class NEW_AFTER_VIDEO(_CommandBase):
	help = 'Create new video node after selected node'
class NEW_AFTER_SLIDESHOW(_CommandBase):
	help = 'Create new slideshow node after selected node'
class NEW_AFTER_SEQ(_CommandBase):
	help = 'Create new sequential node after selected node'
class NEW_AFTER_PAR(_CommandBase):
	help = 'Create new parallel node after selected node'
class NEW_AFTER_EXCL(_CommandBase):
	help = 'Create new exclusive node after selected node'
class NEW_AFTER_CHOICE(_CommandBase):
	help = 'Create new choice node after selected node'
class NEW_AFTER_ALT(_CommandBase):
	help = 'Create new alt node after selected node'
class NEW_AFTER_ANIMATION(_CommandBase):
	help = 'Create new animation node after selected node'
class NEW_UNDER(_CommandBase):
	help = 'Create new node under selected node'
class NEW_UNDER_IMAGE(_CommandBase):
	help = 'Create new image under selected node'
class NEW_UNDER_TEXT(_CommandBase):
	help = 'Create new text node under selected node'
class NEW_UNDER_HTML(_CommandBase):
	help = 'Create new HTML node under selected node'
class NEW_UNDER_SOUND(_CommandBase):
	help = 'Create new sound node under selected node'
class NEW_UNDER_VIDEO(_CommandBase):
	help = 'Create new video node under selected node'
class NEW_UNDER_SLIDESHOW(_CommandBase):
	help = 'Create new slideshow node under selected node'
class NEW_UNDER_SEQ(_CommandBase):
	help = 'Create new sequential node under selected node'
class NEW_UNDER_PAR(_CommandBase):
	help = 'Create new parallel node under selected node'
class NEW_UNDER_EXCL(_CommandBase):
	help = 'Create new exclusive node under selected node'
class NEW_UNDER_CHOICE(_CommandBase):
	help = 'Create new choice node under selected node'
class NEW_UNDER_ALT(_CommandBase):
	help = 'Create new alt node under selected node'
class NEW_UNDER_ANIMATION(_CommandBase):
	help = 'Create new animation node under selected node'
class NEW_SEQ(_CommandBase):
	help = 'Create new sequential node above selected node'
class NEW_PAR(_CommandBase):
	help = 'Create new parallel node above selected node'
class NEW_EXCL(_CommandBase):
	help = 'Create new exclusive node above selected node'
class NEW_CHOICE(_CommandBase):
	help = 'Create new choice node above selected node'
class NEW_ALT(_CommandBase):
	help = 'Create new alt node above selected node'
class NEW_ANIMATION(_CommandBase):
	help = 'Create new animation node above selected node'
class EXPAND(_CommandBase):
	help = 'Expand or collapse selected node'
class EXPANDALL(_CommandBase):
	help = 'Expand selected node and all nodes below'
class COLLAPSEALL(_CommandBase):
	help = 'Collapse selected node and all nodes below'
class TOPARENT(_CommandBase):
	help = 'Go to parent node'
class TOCHILD(_CommandBase):
	help = 'Go to first child node'
class NEXTSIBLING(_CommandBase):
	help = 'Go to next sibling'
class PREVSIBLING(_CommandBase):
	help = 'Go to previous sibling'
class COMPUTE_BANDWIDTH(_CommandBase):
	help = 'Check bandwidth usage of presentation'
class TRANSITION(_DynamicCascade):
	help = 'Selection of available transitions'

#
# Command to hierarchy/channel view
#
class CANVAS_WIDTH(_CommandBase):
	help = 'Double the width of the canvas, adding scrollbars if necessary'
class CANVAS_HEIGHT(_CommandBase):
	help = 'Double the height of the canvas, adding scrollbars if necessary'
class CANVAS_RESET(_CommandBase):
	help = 'Reset the canvas size to fit in the window'
class INFO(_CommandBase):
	help = 'Display the Info editor for the selected object'
class ATTRIBUTES(_CommandBase):
	help = 'Display the properties editor for the selected object'
class ANCHORS(_CommandBase):
	help = 'Display the Anchor editor for the selected object'
class CONTENT(_CommandBase):
	help = 'Edit/show the contents of the selected object'
class PLAYNODE(_CommandBase):
	help = 'Play the selected node'
class PLAYFROM(_CommandBase):
	help = 'Start playing from the selected node'
class PUSHFOCUS(_CommandBase):
	help = 'Select the selected node in other views'
class CREATEANCHOR(_CommandBase):
	help = 'Create a simple fullnode anchor on the selection'
class FINISH_LINK(_CommandBase):
	help = 'Create hyperlink from recent anchor to selection'
class FINISH_ARC(_CommandBase):
	help = 'Lock selection, create sync arc to next selected node'
class THUMBNAIL(_CommandBase):
	help = 'Toggle between showing and not showing thumbnails'
class PLAYABLE(_CommandBase):
	help = 'Toggle between showing and not showing whether nodes\nwill be played using current system attributes'
class TIMESCALE(_CommandBase):
	help = 'Toggle duration-dependent structure view'

#
# Channel view commands
#
class NEW_CHANNEL(_CommandBase):
	help = 'Create a new channel'
class TOGGLE_UNUSED(_CommandBase):
	help = 'Toggle showing unused channels'
class TOGGLE_ARCS(_CommandBase):
	help = 'Toggle showing synchronization arcs'
class TOGGLE_BWSTRIP(_CommandBase):
	help = 'Toggle showing bandwidth usage strip'
class NEXT_MINIDOC(_CommandBase):
	help = 'Display next mini document'
class PREV_MINIDOC(_CommandBase): pass
class MOVE_CHANNEL(_CommandBase): pass
class COPY_CHANNEL(_CommandBase): pass
class TOGGLE_ONOFF(_CommandBase): pass
class HIGHLIGHT(_CommandBase): pass
class UNHIGHLIGHT(_CommandBase): pass
class SYNCARCS(_DynamicCascade): pass
class ANCESTORS(_DynamicCascade): pass
class SIBLINGS(_DynamicCascade): pass
class DESCENDANTS(_DynamicCascade): pass
class LAYOUTS(_DynamicCascade): pass

class BANDWIDTH_14K4(_CommandBase): pass
class BANDWIDTH_28K8(_CommandBase): pass
class BANDWIDTH_ISDN(_CommandBase): pass
class BANDWIDTH_T1(_CommandBase): pass
class BANDWIDTH_LAN(_CommandBase): pass
class BANDWIDTH_OTHER(_CommandBase): pass

#
# Layout view commands
#
class NEW_LAYOUT(_CommandBase):
	help = 'Create a new layout'
class REMOVE_CHANNEL(_CommandBase):
	help = 'Remove channel from layout'
class ADD_CHANNEL(_CommandBase):
	help = 'Add channel to layout'
class RENAME(_CommandBase):
	help = 'Rename the current layout'
