#
# Global constants/variables used by all modules
#

#
# These specify the units in which windw size is given
#
UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2

#
# Constants passed when the canvas is resized
#
RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH = 0, 1, 2

#
# General error
#
error = 'windowinterface.error'

#
# Another exception, used when searching through the window tree.
# Raised by transparent windows to signal that searching must continue
# under this window.
#
Continue = 'Continue'

#
# Masks for select()
#
ReadMask, WriteMask = 1, 2

#
# Constants meaningful to Win32 only
#
SINGLE, HTM, TEXT, MPEG = 0, 1, 2, 3

#
# Used by various channels to modify behaviour
#
Version = 'mac'

#
# Global variables used by all modules
#

toplevel = None
