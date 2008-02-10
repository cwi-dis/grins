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
class UNDO(_CommandBase):
    help = 'Undo'
class REDO(_CommandBase):
    help = 'Redo'
class CUT(_CommandBase):
    help = 'Cut selected object'
class COPY(_CommandBase):
    help = 'Copy selected object'
class COPYPROPERTIES(_CommandBase):
    help = 'Copy properties of selected object'
class PASTE(_CommandBase):
    help = 'Paste copied/cut object'
class PASTEPROPERTIES(_CommandBase):
    help = 'Assign properties to object'
class DELETE(_CommandBase):
    help = 'Delete selected object'
class HELP(_CommandBase):
    help = 'Display help'
class PREFERENCES(_CommandBase):
    help = 'Display application preferences'

# Help commands
class GRINS_WEB(_CommandBase):
    help = 'GRiNS on the Web'
class GRINS_QSG(_CommandBase):
    help = 'GRiNS QuickStart Guide'
class GRINS_TUTORIAL(_CommandBase):
    help = 'GRiNS Tutorial Users Guide'
class GRINS_TDG(_CommandBase):
    help = 'GRiNS Template Design Guide'
class GRINS_REFERENCE(_CommandBase):
    help = 'GRiNS Reference Manual'
class GRINS_DEMOS(_CommandBase):
    help = 'GRiNS Demo Documents'

# Find/Replace commands
class FIND(_CommandBase):
    help = 'Find a object'
class FINDNEXT(_CommandBase):
    help = 'Find the next object'
class REPLACE(_CommandBase):
    help = 'Replace an object'

# Alignment commands
class ALIGN_LEFT(_CommandBase):
    help = 'Align the left borders'
class ALIGN_CENTER(_CommandBase):
    help = 'Align the horizontal center axes'
class ALIGN_RIGHT(_CommandBase):
    help = 'Align the right borders'
class ALIGN_TOP(_CommandBase):
    help = 'Align the top borders'
class ALIGN_MIDDLE(_CommandBase):
    help = 'Align the vertical center axes'
class ALIGN_BOTTOM(_CommandBase):
    help = 'Align the bottom borders'

# Distribute commands
class DISTRIBUTE_HORIZONTALLY(_CommandBase):
    help = 'Distribute horizontally'
class DISTRIBUTE_VERTICALLY(_CommandBase):
    help = 'Distribute vertically'

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
class DUMPWINDOWS(_CommandBase):
    help = 'DEBUG: dump window hierarchy'
class CONSOLE(_CommandBase):
    help = 'DEBUG: toggle debug window'
class SCHEDDEBUG(_CommandBase):
    help = 'DEBUG: toggle scheduler debug flag'
class EXIT(_CommandBase):
    help = 'Exit GRiNS'
class SAVE(_CommandBase):
    help = 'Save document'
class SAVE_AS(_CommandBase):
    help = 'Save document in new file'
class EXPORT_G2(_CommandBase):
    help = 'Create RealPlayer SMIL file and media items'
class UPLOAD_G2(_CommandBase):
    help = 'Upload RealPlayer SMIL file and media items to FTP server'
class EXPORT_QT(_CommandBase):
    help = 'Save document in new file as pure SMIL'
class UPLOAD_QT(_CommandBase):
    help = 'Upload pure SMIL document and media items to FTP server'
class EXPORT_SMIL(_CommandBase):
    help = 'Save document in new file as pure SMIL'
class EXPORT_3GPP(_CommandBase):
    help = 'Save document in new file for 3GPP'
class EXPORT_PRUNE(_CommandBase):
    help = 'Save document in new file as pure SMIL, pruning unused parts'
class EXPORT_SMIL1(_CommandBase):
    help = 'Save document in new file as pure SMIL 1.0'
class UPLOAD_SMIL(_CommandBase):
    help = 'Upload pure SMIL document and media items to FTP server'
class UPLOAD_3GPP(_CommandBase):
    help = 'Upload 3GPP document and media items to FTP server'
class EXPORT_WMP(_CommandBase):         # mjvdg 11-oct-2000
    help = 'Save document in a new file as a Windows Media document.'
class UPLOAD_WMP(_CommandBase):         # mjvdg 11-oct-2000
    help = 'Upload document as Windows Media document to FTP server';
class EXPORT_HTML_TIME(_CommandBase):
    help = 'Save document in a new file as an Internet Explorer HTML+TIME document.'
class EXPORT_HTML(_CommandBase):
    help = 'Create a template webpage linking to your presentation'
class EXPORT_WINCE(_CommandBase):
    help = 'Create SMIL file for Handheld Device'
class EXPORT_TEMPLATE(_CommandBase):
    help = 'Create GRiNS template'
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
class REGISTER(_CommandBase):
    help = 'Register this product with Oratrix'

#
# TopLevel commands
#
class PLAYERVIEW(_CommandBase):
    help = 'Show Player View'
class HIERARCHYVIEW(_CommandBase):
    help = 'Show Structure View'
class LINKVIEW(_CommandBase):
    help = 'Show Hyperlink Editor'
class LAYOUTVIEW(_CommandBase):
    help = 'Show Layout View 2'
class USERGROUPVIEW(_CommandBase):
    help = 'Show Custom Test Editor'
class TRANSITIONVIEW(_CommandBase):
    help = 'Show Transition view'
class LAYOUTVIEW2(_CommandBase):
    help = 'Show new layout view'
#class TEMPORALVIEW(_CommandBase):
#       help = 'Show time-based view'
class SOURCEVIEW(_CommandBase):
    help = 'Show the SMiL source'
class ERRORSVIEW(_CommandBase):
    help = 'Show the list of the source errors'
class ASSETSVIEW(_CommandBase):
    help = 'Show Assets View'

# These are to hide the various views. They are basically
# a workaround for Windows, where the "close" command is
# implemented (for reasons unknown) by sending a command to
# the TopLevel.
class HIDE_PLAYERVIEW(_CommandBase): pass
class HIDE_HIERARCHYVIEW(_CommandBase): pass
class HIDE_LINKVIEW(_CommandBase): pass
class HIDE_LAYOUTVIEW(_CommandBase): pass
class HIDE_USERGROUPVIEW(_CommandBase): pass
class HIDE_SOURCE(_CommandBase): pass
class HIDE_TRANSITIONVIEW(_CommandBase): pass
class HIDE_LAYOUTVIEW2(_CommandBase): pass
#class HIDE_TEMPORALVIEW(_CommandBase):pass
class HIDE_SOURCEVIEW(_CommandBase): pass
class HIDE_ERRORSVIEW(_CommandBase): pass
class HIDE_ASSETSVIEW(_CommandBase): pass
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
    help = 'Custom tests'
class CHANNELS(_DynamicCascade):
    help = 'Toggle channels on/off'
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
PASTE=PASTE_AFTER
class PASTE_UNDER(_CommandBase):
    help = 'Paste copied/cut node under selected node'
## class EDIT_TVIEW(_CommandBase):
##     help = 'Edit this node in the temporal view.'
class NEW_BEFORE(_CommandBase):
    help = 'Create new node before selected node'
class NEW_BEFORE_MEDIA(_CommandBase):
    help = 'Create new media before selected node'
class NEW_BEFORE_IMAGE(_CommandBase):
    help = 'Create new image node before selected node'
class NEW_BEFORE_SVG(_CommandBase):
    help = 'Create new SVG node before selected node'
class NEW_BEFORE_TEXT(_CommandBase):
    help = 'Create new text node before selected node'
class NEW_BEFORE_HTML(_CommandBase):
    help = 'Create new HTML node before selected node'
class NEW_BEFORE_SOUND(_CommandBase):
    help = 'Create new sound node before selected node'
class NEW_BEFORE_VIDEO(_CommandBase):
    help = 'Create new video node before selected node'
class NEW_BEFORE_BRUSH(_CommandBase):
    help = 'Create new brush node before selected node'
class NEW_BEFORE_SLIDESHOW(_CommandBase):
    help = 'Create new slideshow node before selected node'
class NEW_BEFORE_SEQ(_CommandBase):
    help = 'Create new sequential node before selected node'
class NEW_BEFORE_PAR(_CommandBase):
    help = 'Create new parallel node before selected node'
class NEW_BEFORE_EXCL(_CommandBase):
    help = 'Create new exclusive node before selected node'
class NEW_BEFORE_PRIO(_CommandBase):
    help = 'Create new priority class node before selected node'
class NEW_BEFORE_SWITCH(_CommandBase):
    help = 'Create new alt node before selected node'
class NEW_BEFORE_ANIMATE(_CommandBase):
    help = 'Create new animate node before selected node'
class NEW_AFTER(_CommandBase):
    help = 'Create new node after selected node'
class NEW_AFTER_MEDIA(_CommandBase):
    help = 'Create new media after selected node'
class NEW_AFTER_IMAGE(_CommandBase):
    help = 'Create new image node after selected node'
class NEW_AFTER_SVG(_CommandBase):
    help = 'Create new SVG node after selected node'
class NEW_AFTER_TEXT(_CommandBase):
    help = 'Create new text node after selected node'
class NEW_AFTER_HTML(_CommandBase):
    help = 'Create new HTML node after selected node'
class NEW_AFTER_SOUND(_CommandBase):
    help = 'Create new sound node after selected node'
class NEW_AFTER_VIDEO(_CommandBase):
    help = 'Create new video node after selected node'
class NEW_AFTER_BRUSH(_CommandBase):
    help = 'Create new brush node after selected node'
class NEW_AFTER_SLIDESHOW(_CommandBase):
    help = 'Create new slideshow node after selected node'
class NEW_AFTER_SEQ(_CommandBase):
    help = 'Create new sequential node after selected node'
class NEW_AFTER_PAR(_CommandBase):
    help = 'Create new parallel node after selected node'
class NEW_AFTER_EXCL(_CommandBase):
    help = 'Create new exclusive node after selected node'
class NEW_AFTER_PRIO(_CommandBase):
    help = 'Create new priority class node after selected node'
class NEW_AFTER_SWITCH(_CommandBase):
    help = 'Create new alt node after selected node'
class NEW_AFTER_ANIMATE(_CommandBase):
    help = 'Create new animate node after selected node'
class NEW_UNDER(_CommandBase):
    help = 'Create new node under selected node'
class NEW_UNDER_MEDIA(_CommandBase):
    help = 'Create new media under selected node'
class NEW_UNDER_IMAGE(_CommandBase):
    help = 'Create new image under selected node'
class NEW_UNDER_SVG(_CommandBase):
    help = 'Create new SVG under selected node'
class NEW_UNDER_TEXT(_CommandBase):
    help = 'Create new text node under selected node'
class NEW_UNDER_HTML(_CommandBase):
    help = 'Create new HTML node under selected node'
class NEW_UNDER_SOUND(_CommandBase):
    help = 'Create new sound node under selected node'
class NEW_UNDER_VIDEO(_CommandBase):
    help = 'Create new video node under selected node'
class NEW_UNDER_BRUSH(_CommandBase):
    help = 'Create new brush node under selected node'
class NEW_UNDER_SLIDESHOW(_CommandBase):
    help = 'Create new slideshow node under selected node'
class NEW_UNDER_SEQ(_CommandBase):
    help = 'Create new sequential node under selected node'
class NEW_UNDER_PAR(_CommandBase):
    help = 'Create new parallel node under selected node'
class NEW_UNDER_EXCL(_CommandBase):
    help = 'Create new exclusive node under selected node'
class NEW_UNDER_PRIO(_CommandBase):
    help = 'Create new priority class node under selected node'
class NEW_UNDER_SWITCH(_CommandBase):
    help = 'Create new alt node under selected node'
class NEW_UNDER_ANIMATE(_CommandBase):
    help = 'Create new animate node under selected node'
class NEW_SEQ(_CommandBase):
    help = 'Create new sequential node above selected node'
class NEW_PAR(_CommandBase):
    help = 'Create new parallel node above selected node'
class NEW_EXCL(_CommandBase):
    help = 'Create new exclusive node above selected node'
class NEW_PRIO(_CommandBase):
    help = 'Create new priority class node above selected node'
class NEW_SWITCH(_CommandBase):
    help = 'Create new alt node above selected node'
class NEW_ANIMATE(_CommandBase):
    help = 'Create new animate node above selected node'
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
class RPCONVERT(_CommandBase):
    help = 'Convert RealPix node to SMIL 2.0'
class CONVERTRP(_CommandBase):
    help = 'Convert seq node to RealPix file'
class FIND_EVENT_SOURCE(_CommandBase):
    help = 'Find the source of this event'
class ZOOMIN(_CommandBase):
    help = 'Zoom in'
class ZOOMIN2(_CommandBase):
    help = 'Zoom in'
class ZOOMIN4(_CommandBase):
    help = 'Zoom in'
class ZOOMIN8(_CommandBase):
    help = 'Zoom in'
class ZOOMOUT(_CommandBase):
    help = 'Zoom out'
class ZOOMOUT2(_CommandBase):
    help = 'Zoom out'
class ZOOMOUT4(_CommandBase):
    help = 'Zoom out'
class ZOOMOUT8(_CommandBase):
    help = 'Zoom out'
class ZOOMRESET(_CommandBase):
    help = 'Reset zoom factor'

# Pseudo-commands for drag/drop
class DRAG_NODE(_CommandBase): pass
class DRAG_NODEUID(_CommandBase): pass
class DRAG_PAR(_CommandBase): pass
class DRAG_SEQ(_CommandBase): pass
class DRAG_SWITCH(_CommandBase): pass
class DRAG_EXCL(_CommandBase): pass
class DRAG_PRIO(_CommandBase): pass
class DRAG_MEDIA(_CommandBase): pass
class DRAG_ANIMATE(_CommandBase): pass
class DRAG_BRUSH(_CommandBase): pass
class DRAG_REGION(_CommandBase): pass
class DRAG_TOPLAYOUT(_CommandBase): pass

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
class CREATEANCHOREXTENDED(_CommandBase):
    help = 'Create an anchor on the selection and edit the properties'
class CREATEANCHOR_BROWSER(_CommandBase):
    help = 'Create a link to the Browser subwindow'
class CREATEANCHOR_CONTEXT(_CommandBase):
    help = 'Create a link to the Context subwindow'
class FINISH_LINK(_CommandBase):
    help = 'Create hyperlink from recent anchor to selection'
class CREATE_EVENT_SOURCE(_CommandBase):
    help = 'Set the source of any created events to this node.'
class CREATE_BEGIN_EVENT(_CommandBase):
    help = 'Create a begin event for this node.'
class CREATE_END_EVENT(_CommandBase):
    help = 'Create an end event for this node.'
class THUMBNAIL(_CommandBase):
    help = 'Toggle between showing and not showing thumbnails'
class PLAYABLE(_CommandBase):
    help = 'Toggle between showing and not showing whether nodes\nwill be played using current system attributes'
class TIMESCALE(_CommandBase):
    help = 'Toggle duration-dependent structure view'
class LOCALTIMESCALE(_CommandBase):
    help = 'Show durations on focus node in structure view'
class CORRECTLOCALTIMESCALE(_CommandBase):
    help = 'Show consistent durations on focus node in structure view'
class MERGE_PARENT(_CommandBase):
    help = 'Merge this node and it\'s parent'
class MERGE_CHILD(_CommandBase):
    help = 'Delete this item but keep its contents'
class MARK(_CommandBase):
    help = 'Mark the current playback time on the timeline'
class CLEARMARKS(_CommandBase):
    help = 'Clear all timeline markers'

#
# Channel view commands
#
class NEW_REGION(_CommandBase):
    help = 'Create a new region'
class NEW_TOPLAYOUT(_CommandBase):
    help = 'Create a new top layout'
class TOGGLE_UNUSED(_CommandBase):
    help = 'Toggle showing unused channels'
class TOGGLE_ARCS(_CommandBase):
    help = 'Toggle showing synchronization arcs'
class TOGGLE_TIMESCALE(_CommandBase):
    help = 'Toggle showing timeline and bandwidth usage strip'
class TOGGLE_BWSTRIP(_CommandBase):
    help = 'Toggle showing bandwidth usage strip'
class MOVE_REGION(_CommandBase): pass
class COPY_REGION(_CommandBase): pass
class TOGGLE_ONOFF(_CommandBase): pass
class HIGHLIGHT(_CommandBase): pass
class UNHIGHLIGHT(_CommandBase): pass
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
class REMOVE_REGION(_CommandBase):
    help = 'Remove region from layout'
class ADD_REGION(_CommandBase):
    help = 'Add region to layout'
class RENAME(_CommandBase):
    help = 'Rename the current layout'

class ATTRIBUTES_ANCHORS(_CommandBase):
    help = 'Edit anchors'
class ATTRIBUTES_LAYOUT(_CommandBase):
    help = 'Edit layout'

class ENABLE_ANIMATION(_CommandBase):
    help = 'Enable animation'
class SHOW_ANIMATIONPATH(_CommandBase):
    help = 'Show animation path'

#
# Property dialog commands
class SHOWALLPROPERTIES(_CommandBase):
    help = 'Toggle between showing all properties and used ones only'

#
# Source view commands
#
class SELECTNODE_FROM_SOURCE(_CommandBase):
    help = 'Select the node which is pointed by the cursor'
