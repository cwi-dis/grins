"""Dialog for the Previewer control panel.

The PlayerDialog is a window that displays VCR-like controls to
control the player plus an interface to turn channels on and off and
an interface to turn options on and off.

"""

__version__ = "$Id$"

from usercmd import *

from PlayerDialogBase import PlayerDialogBase, STOPPED, PAUSING, PLAYING
from flags import *

class PlayerDialog(PlayerDialogBase):
    adornments = {
            'shortcuts': {
                    'p': PLAY,
                    'P': PAUSE,
                    's': STOP,
                    ' ': MAGIC_PLAY,
                    },
            'menubar': [
                    (FLAG_ALL, 'Close', [
                            (FLAG_ALL, 'Close', CLOSE_WINDOW),
                            ]),
                    (FLAG_ALL, 'Preview', [
                            (FLAG_ALL, 'Preview', PLAY, 't'),
                            (FLAG_ALL, 'Pause', PAUSE, 't'),
                            (FLAG_ALL, 'Stop', STOP, 't'),
                            ]),
                    (FLAG_BOSTON, 'Custom tests', USERGROUPS),
                    (FLAG_CMIF, 'Channels', CHANNELS),
                    (FLAG_ALL|FLAG_DBG, 'View', [
                            (FLAG_ALL|FLAG_DBG, 'Dump scheduler data', SCHEDDUMP),
                            ]),
                    ],
            'toolbar': PlayerDialogBase.adornments['toolbar'],
            'close': [ CLOSE_WINDOW, ],
            'flags': curflags(),
            }
    adornments2 = {
            'shortcuts': {
                    'p': PLAY,
                    'P': PAUSE,
                    's': STOP,
                    ' ': MAGIC_PLAY,
                    },
            'close': [ CLOSE_WINDOW, ],
            }

    def show(self, subwindowof=None):
        PlayerDialogBase.show(self, subwindowof)

    def get_adornments(self, channel):
        self.adornments2['flags'] = curflags()
        return self.adornments2
