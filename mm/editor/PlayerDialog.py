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
		self.__window = None
		self.__displist = None
		self.__title = title
		self.__coords = coords
		self.__subwins = []
		self.__state = STOPPED
		self.__channels = []
		self.__options = []

	def settitle(self, title):
		self.__title = title
		if self.__window is not None:
			self.__window.settitle(title)

	def setchannels(self, channels):
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
		i = self.__channeldict.get(channel)
		if i is None:
			raise RuntimeError, 'unknown channel'
		if self.__channels[i][1] == onoff:
			return
		self.__channels[i] = channel, onoff
		if self.__window is not None:
			self.setchannels(self.__channels)

	def setoptions(self, options):
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
		if self.__window is None:
			return
		self.__window.close()
		self.__window = None
		self.__subwins = []
		self.__displist = None
		
	def show(self):
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
		if self.__window is not None:
			return self.__window.getgeometry()

	def setwaiting(self):
		if self.__window is not None:
			return self.__window.setcursor('watch')

	def setready(self):
		if self.__window is not None:
			return self.__window.setcursor('')

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
