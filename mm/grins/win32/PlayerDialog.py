__version__ = "$Id$"

import windowinterface
from usercmd import *

STOPPED, PAUSING, PLAYING = range(3)

class PlayerDialog:
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
		self.__window = None
		self.__title = title
		self.__coords = coords
		self.__state = -1
		self.__menu_created = None
		self.__topcommandlist = []
		self.__commandlist = []
		self.__channels = []
		self.__channeldict = {}
		
	def preshow(self):
		# If anything has to be done before showing the channels do it here.		
		self.__create()

	def topcommandlist(self, list):
		if list != self.__topcommandlist:
			self.__topcommandlist = list
			self.setstate(self.__state)

	def close(self):
		if self.__window is not None:
			self.__window.close()
			self.__window = None
		del self.__menu_created
		del self.__topcommandlist
		del self.__commandlist
		del self.__channels
		del self.__channeldict

	def __create(self):
		x, y, w, h = self.__coords
	
		self.__window = windowinterface.newview(
			x, y, w, h, self.__title,
			adornments = self.adornments,
			commandlist = None,context='pview_')
		if self.__channels:
			self.setchannels(self.__channels)

	def show(self):
		if self.__menu_created is None:
			if self.__window is None:
				self.__create()

	def hide(self):
		if self.__window is not None:
			self.__window.close()
			self.__window = None

	def settitle(self, title):
		self.__title = title
		if self.__window is not None:
			self.__window.settitle(title)

	def setchannels(self, channels):
		self.__channels = channels
		self.__channeldict = {}
		menu = []
		for i in range(len(channels)):
			channel, onoff = channels[i]
			self.__channeldict[channel] = i
			if self.__menu_created is not None and \
			   channel == self.__menu_created._name:
				continue
			menu.append((channel, (channel,), 't', onoff))
		w = self.__window
		if w is None and self.__menu_created is not None:
			if hasattr(self.__menu_created, 'window'):
				w = self.__menu_created.window
		if w is not None:
			w.set_dynamiclist(CHANNELS, menu)

	def setchannel(self, channel, onoff):
		i = self.__channeldict.get(channel)
		if i is None:
			return
		if self.__channels[i][1] == onoff:
			return
		self.__channels[i] = channel, onoff
		self.setchannels(self.__channels)

	def setstate(self, state):
		ostate = self.__state
		self.__state = state
		w = self.__window
		if w is None and self.__menu_created is not None:
			if hasattr(self.__menu_created, 'window'):
				w = self.__menu_created.window
		commandlist = self.__topcommandlist + self.toplevel.main.commandlist
		self.__commandlist = commandlist
		if w is not None:
			if state == STOPPED:
				w.set_commandlist(commandlist + self.stoplist)
			if state == PLAYING:
				w.set_commandlist(commandlist + self.playlist)
			if state == PAUSING:
				w.set_commandlist(commandlist + self.pauselist)
			self.setchannels(self.__channels)
			if state != ostate:
				w.set_toggle(PLAY, state != STOPPED)
				w.set_toggle(PAUSE, state == PAUSING)
				w.set_toggle(STOP, state == STOPPED)

	def getgeometry(self):
		pass

	def get_adornments(self, channel):
		if self.__menu_created is not None or \
		   self.__window is not None:
			return self.adornments2
		self.__menu_created = channel
		return self.adornments
