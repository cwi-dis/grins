__version__ = "$Id$"

from usercmd import *

from PlayerDialogBase import PlayerDialogBase, STOPPED, PAUSING, PLAYING

class PlayerDialog(PlayerDialogBase):
	adornments = {
		'shortcuts': {
			'p': PLAY,
			'P': PAUSE,
			's': STOP,
			' ': MAGIC_PLAY,
			},
		'menubar': [
			('File', [
				('Open...', OPEN),
				('View source...', SOURCE),
				None,
				('Close', CLOSE),
				('Exit', EXIT),
				]),
			('Play', [
				('Play', PLAY, 't'),
				('Pause', PAUSE, 't'),
				('Stop', STOP, 't'),
				]),
			('Channels', CHANNELS),
			('Options', [
				('Preferences...', PREFERENCES),
				('Dump scheduler data', SCHEDDUMP),
				]),
			('Help', [
				('Help', HELP),
				]),
			],
		'toolbar': PlayerDialogBase.adornments['toolbar'],
		'close': [ CLOSE_WINDOW, CLOSE, EXIT, ],
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

	if __debug__:
		adornments['menubar'][0][1][1:1] = [
			('Trace', TRACE, 't'),
			('Debug', DEBUG),
			('Crash CMIF', CRASH),
			]

	def __init__(self, coords, title):
		PlayerDialogBase.__init__(self, coords, title)
		self.__topcommandlist = []
		self.__has_window = 0
		
	def topcommandlist(self, list):
		if list != self.__topcommandlist:
			self.__topcommandlist = list
			self.setstate()

	def close(self):
		PlayerDialogBase.close(self)
		del self.__topcommandlist

	def show(self):
		if self.menu_created is None:
			self.__has_window = 1
			PlayerDialogBase.show(self)

	def setstate(self, state = None):
		commandlist = self.__topcommandlist + \
			      self.toplevel.main.commandlist
		savestoplist = self.stoplist
		saveplaylist = self.playlist
		savepauselist = self.pauselist
		self.stoplist = commandlist + self.stoplist
		self.playlist = commandlist + self.playlist
		self.pauselist = commandlist + self.pauselist

		PlayerDialogBase.setstate(self, state)

		self.stoplist = savestoplist
		self.playlist = saveplaylist
		self.pauselist = savepauselist

	def get_adornments(self, channel):
		if self.menu_created is not None or \
		   self.__has_window:
			return self.adornments2
		self.menu_created = channel
		return self.adornments
