"""Dialog for the Player control panel.

The PlayerDialog is a window that displays VCR-like controls to
control the player plus an interface to turn channels on and off and
an interface to turn options on and off.

"""

__version__ = "$Id$"

from usercmd import *

from PlayerDialogBase import PlayerDialogBase, STOPPED, PAUSING, PLAYING

class PlayerDialog(PlayerDialogBase):
	adornments = {
		'shortcuts': {
			'p': PLAY,
			'P': PAUSE,
			's': STOP,
			},
		'menubar': [
			('Close', [
				('Close', CLOSE_WINDOW),
				]),
			('Play', [
				('Play', PLAY, 't'),
				('Pause', PAUSE, 't'),
				('Stop', STOP, 't'),
				]),
			('Channels', CHANNELS),
			('Options', [
				('Keep Channel View in sync', SYNCCV, 't'),
				('Dump scheduler data', SCHEDDUMP),
				]),
			],
		'toolbar': PlayerDialogBase.adornments['toolbar'],
		'close': [ CLOSE_WINDOW, ],
		}
	adornments2 = {
		'close': [ CLOSE_WINDOW, ],
		}

	def show(self, subwindowof=None):
		PlayerDialogBase.show(self, subwindowof)
		self._window.set_toggle(SYNCCV, self.sync_cv)

	def get_adornments(self, channel):
		return self.adornments2
