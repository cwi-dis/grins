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

#
# MainDialog commands
#
class NEW_DOCUMENT(_CommandBase):
	help = 'Create new document'
class OPEN(_CommandBase):
	help = 'Open existing document'
class OPEN_LOCAL_FILE(_CommandBase):
	help = 'Open existing document'
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
class RESTORE(_CommandBase):
	help = 'Restore document from file (undo all unsaved changes)'
class SOURCE(_CommandBase):
	help = 'Show source'
class CLOSE(_CommandBase):
	help = 'Close current document'

#
# TopLevel commands
#
class PLAYERVIEW(_CommandBase):
	help = 'Show/hide Player View'
class HIERARCHYVIEW(_CommandBase):
	help = 'Show/hide Hierarchy View'
class CHANNELVIEW(_CommandBase):
	help = 'Show/hide Channel View'
class LINKVIEW(_CommandBase):
	help = 'Show/hide Hyperlink View'

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
class CHANNELS(_DynamicCascade):
	help = 'Toggle channels on/off'
class CALCTIMING(_CommandBase):
	help = 'Recalculate document timing'
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
class PASTE_UNDER(_CommandBase):
	help = 'Paste copied/cut node under selected node'
class NEW_BEFORE(_CommandBase):
	help = 'Create new node before selected node'
class NEW_AFTER(_CommandBase):
	help = 'Create new node after selected node'
class NEW_UNDER(_CommandBase):
	help = 'Create new node under selected node'
class NEW_SEQ(_CommandBase):
	help = 'Create new sequential node above selected node'
class NEW_PAR(_CommandBase):
	help = 'Create new parallel node above selected node'
class NEW_CHOICE(_CommandBase):
	help = 'Create new choice node above selected node'
class NEW_ALT(_CommandBase):
	help = 'Create new alt node above selected node'
class ZOOMIN(_CommandBase):
	help = 'Zoom in one level'
class ZOOMOUT(_CommandBase):
	help = 'Zoom out one level'
class ZOOMHERE(_CommandBase):
	help = 'Zoom in to selected node'

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
	help = 'Display the Attributes editor for the selected object'
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
class FINISH_LINK(_CommandBase): 
	help = 'Create hyperlink from recent anchor to focus'
class FINISH_ARC(_CommandBase): 
	help = 'Lock focus, create sync arc to next selected node' 
class THUMBNAIL(_CommandBase):
	help = 'Toggle between showing and not showing thumbnails'

#
# Channel view commands
#
class NEW_CHANNEL(_CommandBase):
	help = 'Create a new channel'
class TOGGLE_UNUSED(_CommandBase):
	help = 'Toggle showing unused channels'
class TOGGLE_ARCS(_CommandBase):
	help = 'Toggle showing synchronization arcs'
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
