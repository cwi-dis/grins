__version__ = "$Id$"

from usercmd import *
from flags import *

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
			(LIGHT, 'File', [
				(LIGHT, 'Open...', OPEN),
				(LIGHT, 'Close Document', CLOSE),
				(LIGHT, None),
				(LIGHT, 'Preferences...', PREFERENCES),
				(LIGHT|DBG, None),
				(LIGHT|DBG, 'Debug', [
					(LIGHT|DBG, 'Trace', TRACE, 't'),
					(LIGHT|DBG, 'Debug', DEBUG),
					(LIGHT|DBG, 'Crash CMIF', CRASH),
					(LIGHT|DBG, 'Dump Scheduler Data', SCHEDDUMP),
					]),
				(LIGHT, None),
				(LIGHT, 'Quit', EXIT),
				]),
			(LIGHT, 'View', [
				(LIGHT, 'View Source...', SOURCE),
				]),
			(LIGHT, 'Play', [
				(LIGHT, 'Play', PLAY, 't'),
				(LIGHT, 'Pause', PAUSE, 't'),
				(LIGHT, 'Stop', STOP, 't'),
				(CMIF, None),
				(CMIF, 'User Groups', USERGROUPS),
				(CMIF, 'Channels', CHANNELS),
				]),
			(LIGHT, 'Help', [
				(LIGHT, 'Help', HELP),
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
		else:
			self.setchannels()
			self.setusergroups()

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
			self.adornments2['flags'] = curflags()
			return self.adornments2
		self.menu_created = channel
		self.adornments['flags'] = curflags()
		return self.adornments
