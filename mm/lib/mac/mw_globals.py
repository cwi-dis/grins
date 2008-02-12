__version__ = "$Id$"

#
# Global constants/variables used by all modules
#

FALSE, TRUE = 0, 1
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
class error(Exception):
    pass

#
# Another exception, used when searching through the window tree.
# Raised by transparent windows to signal that searching must continue
# under this window.
#
class Continue(Exception):
    pass

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
# Indices into (x, y, w, h) tuples
_X, _Y, _WIDTH, _HEIGHT = 0, 1, 2, 3

#
# Constants for arrow drawing
#
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

#
# The width (in pixels) of a 3D button border
#
SIZE_3DBORDER=2

#
# The size (in pixels) of an icon
ICONSIZE_PXL=16

#
# Flags for the various offscreen/onscreen bitmaps
#
BM_ONSCREEN=-1
BM_DRAWING=0
BM_PASSIVE=1
BM_TEMP=2
#
# The single _Toplevel instance. Note that modules should not
# use import from for this one: it is set when all mw_ modules
# have been imported.
#

toplevel = None

#
# A dictionary where the keys are all known usercmd commands.
# Used for warnings when commands are not bound to any menu or button.
#
_all_commands = {}
