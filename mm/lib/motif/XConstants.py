__version__ = "$Id$"

from splash import error

Continue = 'Continue'

FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2
SINGLE, HTM, TEXT, MPEG = 0, 1, 2, 3

UNIT_MM, UNIT_SCREEN, UNIT_PXL = 0, 1, 2

RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH = 0, 1, 2

Version = 'X'

_WAITING_CURSOR = '_callback'
_READY_CURSOR = '_endcallback'

[_X, _Y, _WIDTH, _HEIGHT] = range(4)

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

#
# The size (in pixels) of an icon
ICONSIZE_PXL=16

[TOP, CENTER, BOTTOM] = range(3)

_def_useGadget = 1                      # whether to use gadgets or not
