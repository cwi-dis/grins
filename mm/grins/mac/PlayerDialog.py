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
	adornments2 = MenuTemplate.CHANNEL_ADORNMENTS
	
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
		self.__topcommandlist = []
		self.__title = title
		self.__coords = coords
		self.__state = -1
		self.__menu_created = None
		self.__channels = []
		self.__options = []
		self.__windowgroup = None
		self.__all_windows = []

	def topcommandlist(self, list):
		if list != self.__topcommandlist:
			self.__topcommandlist = list
			self.setstate(self.__state)
		
	def preshow(self):
		# Note: on the mac we have to create our (non-)window before we open any
		# of the channels. This is so that the channels are parented to us.
		self.__windowgroup = windowinterface.windowgroup(self.__title, [])
		
	def close(self):
		"""Close the dialog and free resources."""
		if self.__window is not None:
			self.__window.close()
		self.__window = None
		self.__menu_created = None
		self.__windowgroup.close() # XXXX test
		self.__windowgroup = None
		del self.__channels
		del self.__options

	def __create(self):
		x, y, w, h = self.__coords
		self.__window = window = windowinterface.newwindow(
			x, y, 0, 0, self.__title, resizable = 0,
			adornments = self.adornments)
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
		self.__all_windows = []

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
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
			w.set_dynamiclist(usercmd.CHANNELS, menu)

	def setchannel(self, channel, onoff):
		i = self.__channeldict.get(channel)
		if i is None:
			return
		if self.__channels[i][1] == onoff:
			return
		self.__channels[i] = channel, onoff
		self.setchannels(self.__channels)

	def after_chan_show(self, channel=None):
		# XXX This is rather inefficient.
		self.showstate()
		
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

		ostate = self.__state
		self.__state = state
		w = self.__window
		if w is None and self.__menu_created is not None:
			if hasattr(self.__menu_created, 'window'):
				w = self.__menu_created.window
		if w is not None:
			commandlist = [
				usercmd.CLOSE(callback=(self.toplevel.close_callback, ())),
				usercmd.CLOSE_WINDOW(callback=(self.toplevel.close_callback, ())),
				] + self.alllist + self.__topcommandlist
			self.setchannels(self.__channels)
			for w in self._getallwindows():
				w.set_commandlist(commandlist)
				w.set_toggle(usercmd.PLAY, state != STOPPED)
				w.set_toggle(usercmd.PAUSE, state == PAUSING)
				w.set_toggle(usercmd.STOP, state == STOPPED)

	def _getallwindows(self):
		rv = []
		if self.__window:
			rv.append(self.__window)
		for w in self.__all_windows:
			if hasattr(w, 'window') and w.window:
				rv.append(w.window)
		return rv
		
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
		self.__all_windows.append(channel)
		if self.__menu_created is not None:
			return self.adornments #2
		self.__menu_created = channel
		return self.adornments
