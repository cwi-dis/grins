__version__ = "$Id$"

""" @win32doc|appcon
This module contains all the win32 constants peculiar to
the cmif application
The more general win32 constants are mainly in win32con.py
and of mfc in afxres.py
"""

[UNIT_MM, UNIT_SCREEN, UNIT_PXL] = 0, 1, 2
[PAINT, SIZE, LBUTTONDOWN, MM_MCI_NOTIFY, SET_CURSOR, WIN_DESTROY, LBUTTONUP] = range(7)
[OPAQUE, TRANSPARENT] = range(2)
[HIDDEN, SHOWN] = range(2)
[FALSE, TRUE] = range(2)
[RESET_CANVAS, DOUBLE_HEIGHT, DOUBLE_WIDTH, DOUBLE_SIZE, FIT_WINDOW] = range(5)
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

Continue = 'Continue'

error = 'windowinterface.error'

import os
GRiNSApp=os.environ['GRiNSApp']
IsEditor = (GRiNSApp=='GRiNSed')
IsPlayer = (GRiNSApp=='GRiNS')
AppDispName = GRiNSApp
if IsEditor:
	AppDisplayName='GRiNS Editor'
else:
	AppDisplayName='GRiNS Player'
	
# win32con or mfccon ++
MLF_NOIDLEMSG      = 0x0001  # don't send WM_ENTERIDLE messages
MLF_NOKICKIDLE     = 0x0002  # don't send WM_KICKIDLE messages
MLF_SHOWONIDLE     = 0x0004  # show window if not visible at idle time
