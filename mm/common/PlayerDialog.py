"""Dialog for the Player control panel.

The PlayerDialog is a window that displays VCR-like controls to
control the player plus an interface to turn channels on and off and
an interface to turn options on and off.

"""

__version__ = "$Id$"

import windowinterface, WMEVENTS

_BLACK = 0, 0, 0
_GREY = 100, 100, 100
_GREEN = 0, 255, 0
_YELLOW = 255, 255, 0
_BGCOLOR = 200, 200, 200
_FOCUSLEFT = 244, 244, 244
_FOCUSTOP = 204, 204, 204
_FOCUSRIGHT = 40, 40, 40
_FOCUSBOTTOM = 91, 91, 91

_titles = 'Channels', 'Options'

STOPPED, PAUSING, PLAYING = range(3)

class PlayerDialog:
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
		self.__displist = None
		self.__title = title
		self.__coords = coords
		self.__subwins = []
		self.__state = STOPPED
		self.__channels = []
		self.__options = []

	def close(self):
		"""Close the dialog and free resources."""
		if self.__window is not None:
			self.__window.close()
		self.__window = None
		del self.__displist
		del self.__subwins
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

		self.__channels = channels
		self.__channeldict = {}
		menu = []
		for channel, onoff in channels:
			self.__channeldict[channel] = len(menu)
			menu.append(('', channel,
				     (self.__channel_callback, (channel,)),
				     't', onoff))
		if self.__window is not None:
			self.__subwins[0].create_menu(menu, title = _titles[0])

	def __channel_callback(self, channel):
		i = self.__channeldict[channel]
		self.__channels[i] = channel, not self.__channels[i][1]
		self.channel_callback(channel)

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
		if self.__window is not None:
			self.setchannels(self.__channels)

	def setoptions(self, options):
		"""Set the list of options.

		Arguments (no defaults):
		options -- a list of options.  An option is either a
			tuple (name, onoff) or a string "name".  The
			name is to be presented to the user.  If the
			option is a tuple, the option is a toggle
			and onoff is the initial value of the toggle
		"""

		self.__options = options
		if self.__window is not None:
			menu = []
			for opt in options:
				if type(opt) is type(()):
					name, onoff = opt
					menu.append(('', name,
						(self.option_callback, (name,)),
						't', onoff))
				else:
					menu.append(('', opt,
						(self.option_callback, (opt,))))
			self.__subwins[1].create_menu(menu, title = _titles[1])

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
			d = self.__displist.clone()
			d.fgcolor(_BGCOLOR)
			self.__drawplaybutton(d)
			self.__drawpausebutton(d)
			self.__drawstopbutton(d)
			d.render()
			self.__displist.close()
			self.__displist = d

	def hide(self):
		"""Hide the control panel."""

		if self.__window is None:
			return
		self.__window.close()
		self.__window = None
		self.__subwins = []
		self.__displist = None
		
	def show(self):
		"""Show the control panel."""

		if self.__window is not None:
			self.__window.pop()
			return
		x, y, w, h = self.__coords
		self.__window = w = windowinterface.newcmwindow(x, y, w, h,
								self.__title)
		w.bgcolor(_BGCOLOR)
		w.setcursor('watch')
		w.register(WMEVENTS.Mouse0Release, self.__mouse_callback, None)
		w.register(WMEVENTS.ResizeWindow, self.__resize_callback, None)
		w.register(WMEVENTS.WindowExit, self.__close_callback, None)
		self.__resize_callback(None, w, None, None)

	def __close_callback(self, dummy, window, event, val):
		self.close_callback()

	def getgeometry(self):
		"""Get the coordinates of the control panel.

		The return value is a tuple giving the coordinates
		(x, y, width, height) in mm of the player control
		panel.
		"""

		if self.__window is not None:
			return self.__window.getgeometry()

	def setcursor(self, cursor):
		"""Set the cursor to a named shape.

		Arguments (no defaults):
		cursor -- string giving the name of the desired cursor shape
		"""
		if self.__window is not None:
			return self.__window.setcursor(cursor)

	def __resize_callback(self, dummy, window, event, val):
		import StringStuff
		window = self.__window
		for w in self.__subwins:
			w.close()
		font = windowinterface.findfont('Helvetica', 10)
		d = window.newdisplaylist()
		dummy = d.usefont(font)
		mw, mh = 0, 0
		for t in _titles:
			w, h = d.strsize(t)
			if w > mw: mw = w
			if h > mh: mh = h
		if mw > .5: mw = .5
		self.__width = 1.0 - mw	# useful width
		d.fgcolor(_BGCOLOR)
		self.__drawplaybutton(d)
		self.__drawpausebutton(d)
		self.__drawstopbutton(d)
		d.render()
		self.__displist = d
		self.__subwins = []
		n = len(_titles)
		for i in range(n):
			w = window.newcmwindow(
				(1.0 - mw, i / float(n), mw, 1.0 / float(n)))
			self.__subwins.append(w)
			t = _titles[i]
			d = w.newdisplaylist()
			dummy = d.usefont(font)
			StringStuff.centerstring(d, 0, 0, 1, 1, t)
			d.render()
		self.setchannels(self.__channels)
		self.setoptions(self.__options)

	def __drawplaybutton(self, d):
		self.__playbutton = d.newbutton((.0, .0,
						 .5 * self.__width, .5))
		if self.__state != STOPPED:
			color = _GREEN
			cl, ct, cr, cb = _FOCUSRIGHT, _FOCUSBOTTOM, _FOCUSLEFT, _FOCUSTOP
		else:
			color = _GREY
			cl, ct, cr, cb = _FOCUSLEFT, _FOCUSTOP, _FOCUSRIGHT, _FOCUSBOTTOM
		points = []
		for x, y in [(.2, .1), (.2, .4), (.3, .25)]:
			points.append(x * self.__width, y)
		d.drawfpolygon(color, points)
		d.draw3dbox(cl, ct, cr, cb,
			    (.01 * self.__width, .01, .48 * self.__width, .48))

	def __drawpausebutton(self, d):
		self.__pausebutton = d.newbutton((.5 * self.__width, .0,
						  .5 * self.__width, .5))
		if self.__state == PAUSING:
			color = _YELLOW
			cl, ct, cr, cb = _FOCUSRIGHT, _FOCUSBOTTOM, _FOCUSLEFT, _FOCUSTOP
		else:
			color = _GREY
			cl, ct, cr, cb = _FOCUSLEFT, _FOCUSTOP, _FOCUSRIGHT, _FOCUSBOTTOM
		d.drawfbox(color, (.7 * self.__width, .1, .03 * self.__width, .3))
		d.drawfbox(color, (.77 * self.__width, .1, .03 * self.__width, .3))
		d.draw3dbox(cl, ct, cr, cb,
			    (.51 * self.__width, .01, .48 * self.__width, .48))

	def __drawstopbutton(self, d):
		self.__stopbutton = d.newbutton((.0, .5,
						 self.__width, .5))
		if self.__state == STOPPED:
			color = _GREY
			cl, ct, cr, cb = _FOCUSLEFT, _FOCUSTOP, _FOCUSRIGHT, _FOCUSBOTTOM
		else:
			color = _BLACK
			cl, ct, cr, cb = _FOCUSRIGHT, _FOCUSBOTTOM, _FOCUSLEFT, _FOCUSTOP
		d.drawfbox(color, (.2 * self.__width, .6, .6 * self.__width, .3))
		d.draw3dbox(cl, ct, cr, cb,
			    (.01 * self.__width, .51, .98 * self.__width, .48))

	def __mouse_callback(self, dummy, window, event, val):
		if window is not self.__window:
			return
		b = val[2]
		if len(b) == 0:
			return
		b = b[0]
		if b is self.__playbutton:
			self.play_callback()
		elif b is self.__pausebutton:
			self.pause_callback()
		elif b is self.__stopbutton:
			self.stop_callback()
