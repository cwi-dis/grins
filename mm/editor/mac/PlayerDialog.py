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

LAYOUTS = {
	'normal': {
		'play':  (0.0, 0.0, 0.5, 0.5),
		'pause': (0.5, 0.0, 0.5, 0.5),
		'stop':  (0.0, 0.5, 1.0, 0.5),
		'buttons': 'vertical',
	},
	'horizontal': {
		'stop':  (0.0, 0.0, 0.33, 1.0),
		'play':  (0.33, 0.0, 0.34, 1.0),
		'pause': (0.67, 0.0, 0.33, 1.0),
		'buttons': 'horizontal',
	}
}

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
			self.__drawplaybutton(d, self.__layout['play'])
			self.__drawpausebutton(d, self.__layout['pause'])
			self.__drawstopbutton(d, self.__layout['stop'])
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

	def show(self, subwindowof=None):
		"""Show the control panel."""

		if self.__window is not None:
			self.__window.pop()
			return
		x, y, w, h = self.__coords
		if subwindowof is None:
			self.__window = w = windowinterface.newcmwindow(x, y, w, h,
								self.__title)
		else:
			raise 'kaboo kaboo'
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
		window = self.__window
		for w in self.__subwins:
			w.close()
		font = windowinterface.findfont('Helvetica', 10)
		d = window.newdisplaylist()
		dummy = d.usefont(font)
		self.__determine_layout(d, _titles)
		d.fgcolor(_BGCOLOR)
		self.__drawplaybutton(d, self.__layout['play'])
		self.__drawpausebutton(d, self.__layout['pause'])
		self.__drawstopbutton(d, self.__layout['stop'])
		d.render()
		self.__displist = d
		self.__subwins = []
		n = len(_titles)
		for i in range(n):
			w = window.newcmwindow(self.__menu_boxes[i])
			self.__subwins.append(w)
			t = _titles[i]
			d = w.newdisplaylist()
			dummy = d.usefont(font)
			d.centerstring(0, 0, 1, 1, t)
			d.render()
		self.setchannels(self.__channels)
		self.setoptions(self.__options)

	def __determine_layout(self, d, _titles):
		"""Determine which layout to use, horizontal or normal"""
		w, h = d.strsize('M')
##		print 'w,h', w, h
		# This is a bit of a guess, but it "looks good"
		if 8*w < h or h*len(_titles) > 1:
##			print 'try horizontal'
			# Determine width of menus
			mw = 0
			menuwidth = []
			for t in _titles:
				w, h = d.strsize(t+'  ')
				mw = mw + w
				menuwidth.append(w)
			if mw < .7:
				# XXXX Note: we leave the space from 0.3 to 1-mw free
				# XXXX it could be used for a timestrip or something...
				self.__width = 0.3
				self.__layout = LAYOUTS['horizontal']
				# And calculate boxes for menus
				self.__menu_boxes = []
				n = len(_titles)
				menupos = 1-mw
				for i in range(n):
					self.__menu_boxes.append(menupos, 0, menuwidth[i], 1)
					menupos = menupos + menuwidth[i]
				return
##		print 'normal'
		self.__layout = LAYOUTS['normal']
		# Determine width of menus
		mw = 0
		for t in _titles:
			w, h = d.strsize(t)
			if w > mw: mw = w
		if mw > .5: mw = .5
		self.__width = 1.0 - mw	# useful width
		# And calculate boxes for menus
		self.__menu_boxes = []
		n = len(_titles)
		for i in range(n):
			self.__menu_boxes.append(1.0 - mw, i / float(n), mw, 1.0 / float(n))

	def __drawplaybutton(self, d, (bx, by, bw, bh)):
		bw = bw * self.__width	# The menus are to the right
		bx = bx * self.__width
		self.__playbutton = d.newbutton((bx, by, bw, bh))
		# Select triangle color
		if self.__state != STOPPED:
			color = _GREEN
			cl, ct, cr, cb = _FOCUSRIGHT, _FOCUSBOTTOM, _FOCUSLEFT, _FOCUSTOP
		else:
			color = _GREY
			cl, ct, cr, cb = _FOCUSLEFT, _FOCUSTOP, _FOCUSRIGHT, _FOCUSBOTTOM
		# and draw it
		points = []
		for x, y in [(.4, .2), (.4, .8), (.6, .5)]:
			points.append(bx+(x * bw), by+(y*bh))
		d.drawfpolygon(color, points)
		# and draw our outline box
		d.draw3dbox(cl, ct, cr, cb,
			    (bx+.02 * bw, by+.02*bh, .96 * bw, .96 * bh))

	def __drawpausebutton(self, d, (bx, by, bw, bh)):
		bw = bw * self.__width
		bx = bx * self.__width
		self.__pausebutton = d.newbutton((bx, by, bw, bh))
		# select pause icon II color and draw it
		if self.__state == PAUSING:
			color = _YELLOW
			cl, ct, cr, cb = _FOCUSRIGHT, _FOCUSBOTTOM, _FOCUSLEFT, _FOCUSTOP
		else:
			color = _GREY
			cl, ct, cr, cb = _FOCUSLEFT, _FOCUSTOP, _FOCUSRIGHT, _FOCUSBOTTOM
		d.drawfbox(color, (bx+0.4*bw, by+0.2*bh, .06 * bw, .6*bh))
		d.drawfbox(color, (bx+.54*bw, by+0.2*bh, .06 * bw, .6*bh))
		# and draw our 3d box
		d.draw3dbox(cl, ct, cr, cb,
			    (bx+.02 * bw, by+.02*bh, .96 * bw, .96 * bh))

	def __drawstopbutton(self, d, (bx, by, bw, bh)):
		bw = bw * self.__width
		bx = bx * self.__width
		self.__stopbutton = d.newbutton((bx, by, bw, bh))
		if self.__state == STOPPED:
			color = _GREY
			cl, ct, cr, cb = _FOCUSLEFT, _FOCUSTOP, _FOCUSRIGHT, _FOCUSBOTTOM
		else:
			color = _BLACK
			cl, ct, cr, cb = _FOCUSRIGHT, _FOCUSBOTTOM, _FOCUSLEFT, _FOCUSTOP
		d.drawfbox(color, (bx+.2 * bw, by+.2*bh, .6 * bw, .6*bh))
		d.draw3dbox(cl, ct, cr, cb,
			    (bx+.02 * bw, by+.02*bh, .96 * bw, .96 * bh))

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
			
	def get_adornments(self, channel):
		return None
		
