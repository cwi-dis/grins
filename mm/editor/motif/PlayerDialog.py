"""Dialog for the Player control panel.

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
			},
		'menubar': [
			(FLAG_ALL, 'Close', [
				(FLAG_ALL, 'Close', CLOSE_WINDOW),
				]),
			(FLAG_ALL, 'Play', [
				(FLAG_ALL, 'Play', PLAY, 't'),
				(FLAG_ALL, 'Pause', PAUSE, 't'),
				(FLAG_ALL, 'Stop', STOP, 't'),
				]),
			(FLAG_CMIF, 'User Groups', USERGROUPS),
			(FLAG_CMIF, 'Channels', CHANNELS),
			(FLAG_ALL|FLAG_DBG, 'View', [
				(FLAG_CMIF, 'Timeline view follows player', SYNCCV, 't'),
				(FLAG_ALL|FLAG_DBG, 'Dump scheduler data', SCHEDDUMP),
				]),
			],
		'toolbar': PlayerDialogBase.adornments['toolbar'],
		'close': [ CLOSE_WINDOW, ],
		'flags': curflags(),
		}
	adornments2 = {
		'close': [ CLOSE_WINDOW, ],
		}

	def show(self, subwindowof=None):
		PlayerDialogBase.show(self, subwindowof)
		self._window.set_toggle(SYNCCV, self.sync_cv)

	def get_adornments(self, channel):
		self.adornments2['flags'] = curflags()
		return self.adornments2
