"""Dialog for the Player control panel.

The PlayerDialog is a window that displays VCR-like controls to
control the player plus an interface to turn channels on and off and
an interface to turn options on and off.

"""

__version__ = "$Id$"

import windowinterface, WMEVENTS
import usercmd
import MenuTemplate

##_BLACK = 0, 0, 0
##_GREY = 100, 100, 100
##_GREEN = 0, 255, 0
##_YELLOW = 255, 255, 0
##_BGCOLOR = 200, 200, 200
##_FOCUSLEFT = 244, 244, 244
##_FOCUSTOP = 204, 204, 204
##_FOCUSRIGHT = 40, 40, 40
##_FOCUSBOTTOM = 91, 91, 91
##
##_titles = 'Channels', 'Options'
##
STOPPED, PAUSING, PLAYING = range(3)

class PlayerDialog:

	# Adornments for first channel window opened and further windows:
	adornments = MenuTemplate.PLAYER_ADORNMENTS
	adornments2 = {}
	
	def __init__(self, coords, title):
		"""Create the Player dialog.

		Create the dialog window (non-modal, so does not grab
		the cursor) but do not pop it up (i.e. do not display
		it on the screen).

		Arguments (no defaults):
		coords -- the coordinates (x, y, width, height) of the 
			control panel in mm
		title -- string to be displayed as window title
		"""

		self.__window = None
		self.__title = title
		self.__coords = coords
		self.__state = STOPPED
		self.__menu_created = None
		self.__channels = []
		self.__options = []
		
	def preshow(self):
		# Note: on the mac we have to create our (non-)window before we open any
		# of the channels. This is so that the channels are parented to us.
		PlayerDialog.show(self)
		
	def close(self):
		"""Close the dialog and free resources."""
		if self.__window is not None:
			self.__window.close()
		self.__window = None
		del self.__channels
		del self.__options

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
		self.__title = title
		if self.__window is not None:
			self.__window.settitle(title)

	def setchannels(self, channels):
		"""Set the list of channels.

		Arguments (no defaults):
		channels -- a list of tuples (name, onoff) where name
			is the channel name which is to be presented
			to the user, and onoff indicates whether the
			channel is on or off (1 if on, 0 if off)
		"""

##		self.__channels = channels
##		self.__channeldict = {}
##		menu = []
##		for channel, onoff in channels:
##			self.__channeldict[channel] = len(menu)
##			menu.append(('', channel,
##				     (self.__channel_callback, (channel,)),
##				     't', onoff))
##		if self.__window is not None:
##			self.__subwins[0].create_menu(menu, title = _titles[0])
##
##	def __channel_callback(self, channel):
##		i = self.__channeldict[channel]
##		self.__channels[i] = channel, not self.__channels[i][1]
##		self.channel_callback(channel)

	def setchannel(self, channel, onoff):
		"""Set the on/off status of a channel.

		Arguments (no defaults):
		channel -- the name of the channel whose status is to
			be set
		onoff -- the new status
		"""

##		i = self.__channeldict.get(channel)
##		if i is None:
##			raise RuntimeError, 'unknown channel'
##		if self.__channels[i][1] == onoff:
##			return
##		self.__channels[i] = channel, onoff
##		if self.__window is not None:
##			self.setchannels(self.__channels)

	def setoptions(self, options):
		"""Set the list of options.

		Arguments (no defaults):
		options -- a list of options.  An option is either a
			tuple (name, onoff) or a string "name".  The
			name is to be presented to the user.  If the
			option is a tuple, the option is a toggle
			and onoff is the initial value of the toggle
		"""

##		self.__options = options
##		if self.__window is not None:
##			menu = []
##			for opt in options:
##				if type(opt) is type(()):
##					name, onoff = opt
##					menu.append(('', name,
##						(self.option_callback, (name,)),
##						't', onoff))
##				else:
##					menu.append(('', opt,
##						(self.option_callback, (opt,))))
##			self.__subwins[1].create_menu(menu, title = _titles[1])

	def setstate(self, state):
		"""Set the playing state of the control panel.

		Arguments (no defaults):
		state -- the new state:
			STOPPED -- the player is in the stopped state
			PLAYING -- the player is in the playing state
			PAUSING -- the player is in the pausing state
		"""

		self.__state = state
		if self.__window is not None:
			self.__window.set_toggle(usercmd.PLAY, self.__state != STOPPED)
			self.__window.set_toggle(usercmd.STOP, self.__state == STOPPED)
			self.__window.set_toggle(usercmd.PAUSE, self.__state == PAUSING)
		if self.__menu_created is not None and \
				self.__menu_created.window is not None:
			w = self.__menu_created.window
			w.set_toggle(usercmd.PLAY, self.__state != STOPPED)
			w.set_toggle(usercmd.STOP, self.__state == STOPPED)
			w.set_toggle(usercmd.PAUSE, self.__state == PAUSING)

	def hide(self):
		"""Hide the control panel."""

		if self.__window is None:
			return
		self.__window.close()
		self.__window = None
		
	def show(self):
		"""Show the control panel."""

		if self.__window is not None:
			self.__window.pop()
			return
		cmdlist = [
			usercmd.PLAY(callback=(self.play_callback, ())),
			usercmd.STOP(callback=(self.stop_callback, ())),
			usercmd.PAUSE(callback=(self.pause_callback, ())),
			usercmd.CLOSE(callback=(self.toplevel.close_callback, ()))]
		self.__window = w = windowinterface.windowgroup(self.__title, cmdlist)

	def getgeometry(self):
		"""Get the coordinates of the control panel.

		The return value is a tuple giving the coordinates
		(x, y, width, height) in mm of the player control
		panel.
		"""
		return None

	def setcursor(self, cursor):
		"""Set the cursor to a named shape.

		Arguments (no defaults):
		cursor -- string giving the name of the desired cursor shape
		"""
		windowinterface.setcursor(cursor)

	def get_adornments(self, channel):
		if self.__menu_created is not None:
			return self.adornments2
		self.__menu_created = channel
		return self.adornments
