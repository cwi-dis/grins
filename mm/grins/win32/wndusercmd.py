__version__ = "$Id$"

""" @win32doc|usercmdui
Contains extensions to usercmd classes specific to the 
win32 ui. Specifically commands for windows arrangement,
the about command and the select charset command.
"""

from usercmd import _CommandBase

class CLOSE_ACTIVE_WINDOW(_CommandBase):
	help = 'Close active window'
class CASCADE(_CommandBase):
	help = 'Arrange windows as overlapping tiles'
class TILE_HORZ(_CommandBase):
	help = 'Arrange windows as horizontal, nonoverlapping tiles'
class TILE_VERT(_CommandBase):
	help = 'Arrange windows as vertical, nonoverlapping tiles'
class ABOUT_GRINS(_CommandBase):
	help = 'Displays program copyright'
class SELECT_CHARSET(_CommandBase):
	help = 'Select a charset'

class HELP_CONTENTS(_CommandBase):
	help = 'Display help contents'

class GRINS_WEB(_CommandBase):
	help = 'GRiNS on the Web'

class PASTE_FILE(_CommandBase):
	help = 'Paste file'
