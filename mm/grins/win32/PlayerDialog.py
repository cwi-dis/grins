__version__ = "$Id$"

"""Dialog for the Player control panel.

The PlayerDialog is a window that displays VCR-like controls to
control the player plus an interface to turn channels on and off and
an interface to turn options on and off.

"""

""" @win32doc|PlayerDialog
A PlayerDialog instance manages commands related
to play. This instance indirectly passes information to
the windows interface through the get_adornments method
called by the channel module.
"""

import windowinterface
from usercmd import *

STOPPED, PAUSING, PLAYING = range(3)

class PlayerDialog:
	adornments = {}
	def __init__(self, coords, title):
		self.__window = None
		self.__title = title
		self.__coords = coords
		self.__state = -1
		self.__menu_created = None
		self.__topcommandlist = []
		self.__commandlist = []
		self.__ugroups = []
		self.__ugroupdict = {}
		self.__channels = []
		self.__channeldict = {}
		self.__strid='player'
		self.__cmdtgt='pview_'
		
	def preshow(self):
		# If anything has to be done before showing the channels do it here.		
		self.__create()

	def topcommandlist(self, list):
		if list != self.__topcommandlist:
			self.__topcommandlist = list
			self.setstate(self.__state)

	def close(self):
		if self.__window is not None:
			#self.__window.close()
			self.__window = None
		del self.__menu_created
		del self.__topcommandlist
		del self.__commandlist
		del self.__channels
		del self.__channeldict

	def __create(self):
		x, y, w, h = self.__coords
		self.__window = self.toplevel.window
		self.__window.set_commandlist(self.stoplist,self.__cmdtgt)


	def show(self):
		if self.__menu_created is None:
			if self.__window is None:
				self.__create()

	def hide(self):
		if self.__window is not None:
			self.__window.set_commandlist(None,self.__cmdtgt)
			self.__window = None

	def settitle(self, title):
		self.__title = title
		if self.__window is not None:
			self.__window.settitle(title)

	def setusergroups(self, ugroups = None):
		if ugroups is None:
			ugroups = self.__ugroups
		else:
			self.__ugroups = ugroups
		menu = []
		self.__ugroupdict = {}
		for i in range(len(ugroups)):
			name, title, onoff = ugroups[i]
			self.__ugroupdict[name] = i
			menu.append((title, (name,), 't', onoff))
		w = self.__window
		if w is not None:
			w.set_dynamiclist(USERGROUPS, menu)

	def setusergroup(self, ugroup, onoff):
		i = self.__ugroupdict.get(ugroup)
		if i is None:
			raise RuntimeError, 'unknown user group'
		if self.__ugroups[i][2] == onoff:
			return
		self.__ugroups[i] = self.__ugroups[i][:2] + (onoff,)
		self.setusergroups()

	def setchannels(self, channels=None):
		"""Set the list of channels.

		Arguments (no defaults):
		channels -- a list of tuples (name, onoff) where name
			is the channel name which is to be presented
			to the user, and onoff indicates whether the
			channel is on or off (1 if on, 0 if off)
		"""
		if channels is None:
			channels = self.__channels
		else:
			self.__channels = channels

		self.__channeldict = {}
		menu = []
		for i in range(len(channels)):
			channel, onoff = channels[i]
			self.__channeldict[channel] = i
			menu.append((channel, (channel,), 't', onoff))
		w = self.__window
		if w is not None:
			w.set_dynamiclist(CHANNELS, menu)

	def setchannel(self, channel, onoff):
		"""Set the on/off status of a channel.

		Arguments (no defaults):
		channel -- the name of the channel whose status is to
			be set
		onoff -- the new status
		"""

		i = self.__channeldict.get(channel)
		if i is None:
			raise RuntimeError, 'unknown channel'
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
				w.set_commandlist(commandlist + self.stoplist,self.__cmdtgt)
			if state == PLAYING:
				w.set_commandlist(commandlist + self.playlist,self.__cmdtgt)
			if state == PAUSING:
				w.set_commandlist(commandlist + self.pauselist,self.__cmdtgt)
			self.setchannels(self.__channels)
			if state != ostate:
				w.set_toggle(PLAY, state != STOPPED)
				w.set_toggle(PAUSE, state == PAUSING)
				w.set_toggle(STOP, state == STOPPED)

	def getgeometry(self):
		pass

	def get_adornments(self, channel):
		self.inst_adornments = {
			'close': [ CLOSE_WINDOW, ],
			'frame':self.toplevel.window,
			'view':self.__cmdtgt,
			}
		return self.inst_adornments

