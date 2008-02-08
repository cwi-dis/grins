__version__ = "$Id$"

import wincon

[UNIT_MM, UNIT_SCREEN, UNIT_PXL] = 0, 1, 2
[PAINT, SIZE, LBUTTONDOWN, MM_MCI_NOTIFY, SET_CURSOR, WIN_DESTROY, LBUTTONUP] = range(7)
[OPAQUE, TRANSPARENT] = range(2)
[HIDDEN, SHOWN] = range(2)
[FALSE, TRUE] = range(2)
[RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH, DOUBLE_SIZE] = range(4)
[SINGLE, HTM, TEXT, MPEG] = range(4)
[SAVE_CMIF, OPEN_FILE] = range(2)
[TOP, CENTER, BOTTOM] = range(3)
[VERTICAL, HORIZONTAL] = range(2)
[XPOS,YPOS,WIDTH,HEIGHT] = range(4)

ReadMask, WriteMask = 1, 2
TICKS_PER_SECOND=1000

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)
#
# The size (in pixels) of an icon
ICONSIZE_PXL=16

Continue = 'Continue'

error = 'windowinterface.error'

# DropEffects
DROPEFFECT_NONE   = 0
DROPEFFECT_COPY   = 1
DROPEFFECT_MOVE   = 2
DROPEFFECT_LINK   = 4
DROPEFFECT_SCROLL = 0x80000000

# Private window messages

# wincon or mfccon ++
MLF_NOIDLEMSG      = 0x0001  # don't send WM_ENTERIDLE messages
MLF_NOKICKIDLE     = 0x0002  # don't send WM_KICKIDLE messages
MLF_SHOWONIDLE     = 0x0004  # show window if not visible at idle time

WM_KICKIDLE        = 0x036A

WM_USER_CREATE_BOX_OK           = wincon.WM_USER + 1
WM_USER_CREATE_BOX_CANCEL       = wincon.WM_USER + 2

# constants to select web browser control
[IE_CONTROL, WEBSTER_CONTROL]=0, 1

# start of unnamed messages
WM_USER_GRINS                           = wincon.WM_USER + 100
