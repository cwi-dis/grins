__version__ = "$Id$"

import windowinterface, X, Xm, Xmd

_BLACK = 0, 0, 0
_GREY = 100, 100, 100
_GREEN = 0, 255, 0
_YELLOW = 255, 255, 0
_BGCOLOR = 200, 200, 200
_FOCUSLEFT = 244, 244, 244
_FOCUSTOP = 204, 204, 204
_FOCUSRIGHT = 40, 40, 40
_FOCUSBOTTOM = 91, 91, 91

STOPPED, PAUSING, PLAYING = range(3)

class DrawnButton(windowinterface._Widget):
	def __init__(self, parent, callback, exposecb,
		     name = 'windowDrawnButton', **options):
		self.armed = 0
		attrs = {'shadowType': Xmd.SHADOW_OUT,
			 'traversalOn': X.FALSE}
		self._attachments(attrs, options)
		button = parent._form.CreateManagedWidget(name, Xm.DrawnButton,
							  attrs)
		button.AddCallback('activateCallback',
				   self.__callback, callback)
		button.AddCallback('exposeCallback',
				   self.__expose, exposecb)
		button.AddCallback('armCallback',
				   self.__armcallback, None)
		button.AddCallback('disarmCallback',
				   self.__disarmcallback, None)
		windowinterface._Widget.__init__(self, parent, button)

	def __armcallback(self, widget, client_data, call_data):
		self.armed = 1
		widget.shadowType = Xmd.SHADOW_IN

	def __disarmcallback(self, widget, client_data, call_data):
		self.armed = 0
		widget.shadowType = Xmd.SHADOW_OUT

	def __callback(self, widget, callback, call_data):
		if self.is_closed():
			return
		widget.shadowType = Xmd.SHADOW_IN
		apply(apply, callback)

	def __expose(self, widget, callback, call_data):
		if self.is_closed():
			return
		callback(widget, call_data)

class PlayerDialog:
	def __init__(self, coords, title):
		x, y, w, h = coords
		self.__window = window = windowinterface.Window(
			title, resizable = 1,
			width = w, height = h, x = x, y = y,
			deleteCallback = (self.close_callback, ()))
		self.__menu = m = window.PulldownMenu(
			[('Close', [('Close', (self.close_callback, ()))]),
			 ('Play', [('Play', (self.play_callback, ())),
				   ('Pause', (self.pause_callback, ())),
				   ('Stop', (self.stop_callback, ()))]),
			 ('Channels', []),
			 ('Options', [])],
			top = None, left = None, right = None)
		f = window.SubWindow(top = m, bottom = None,
				left = None, right = None)
		self.__play = DrawnButton(f, (self.play_callback, ()),
					  self.__drawplay,
					  name = 'playButton',
					  top = None, bottom = .5, left = None,
					  right = .5)
		self.__pause = DrawnButton(f, (self.pause_callback, ()),
					   self.__drawpause,
					   name = 'pauseButton',
					   top = None, bottom = .5,
					   left = self.__play, right = None)
		self.__stop = DrawnButton(f, (self.stop_callback, ()),
					  self.__drawstop,
					  name = 'stopButton',
					  top = self.__play, left = None,
					  bottom = None, right = None)

	def close(self):
		self.__window.close()
		self.__window = None
		del self.__menu
		del self.__play
		del self.__pause
		del self.__stop

	def __drawplay(self, widget, call_data):
		if self.__state == STOPPED:
			color = _GREY
			shadow = Xmd.SHADOW_OUT
		else:
			color = _GREEN
			shadow = Xmd.SHADOW_IN
		if self.__play.armed:
			shadow = Xmd.SHADOW_IN
		widget.shadowType = shadow
		gc = widget.GetGC({'foreground': windowinterface.toplevel._convert_color(color, 1)})
		w = widget.width
		h = widget.height
		gc.FillPolygon([(int(w*.4),int(h*.2)),(int(w*.4),int(h*.8)),(int(w*.6),int(h*.5))], X.Convex,
			       X.CoordModeOrigin)

	def __drawpause(self, widget, call_data):
		if self.__state == PAUSING:
			color = _YELLOW
			shadow = Xmd.SHADOW_IN
		else:
			color = _GREY
			shadow = Xmd.SHADOW_OUT
		if self.__pause.armed:
			shadow = Xmd.SHADOW_IN
		widget.shadowType = shadow
		gc = widget.GetGC({'foreground': windowinterface.toplevel._convert_color(color, 1)})
		w = widget.width
		h = widget.height
		gc.FillRectangle(int(w*.4), int(h*.2), int(w*.06), int(h*.6))
		gc.FillRectangle(int(w*.54), int(h*.2), int(w*.06), int(h*.6))

	def __drawstop(self, widget, call_data):
		if self.__state == STOPPED:
			color = _BLACK
			shadow = Xmd.SHADOW_IN
		else:
			color = _GREY
			shadow = Xmd.SHADOW_OUT
		if self.__stop.armed:
			shadow = Xmd.SHADOW_IN
		widget.shadowType = shadow
		gc = widget.GetGC({'foreground': windowinterface.toplevel._convert_color(color, 1)})
		w = widget.width
		h = widget.height
		gc.FillRectangle(int(w*.2), int(h*.2), int(w*.6), int(h*.6))

	def show(self):
		self.__window.setcursor('watch')
		self.__window.show()

	def hide(self):
		self.__window.hide()

	def setchannels(self, channels):
		self.__menu.setmenu(2,
				    map(lambda c, cb = self.channel_callback:
					(c[0], (cb, (c[0],)), 't', c[1]),
					channels))

	def setchannel(self, channel, onoff):
		self.__menu.setmenuentry(2, [channel], onoff = onoff)

	def setoptions(self, options):
		menu = []
		for opt in options:
			if type(opt) is type(()):
				name, onoff = opt
				menu.append((name,
					     (self.option_callback, (name,)),
					     't', onoff))
			else:
				menu.append((opt,
					     (self.option_callback, (opt,))))
		self.__menu.setmenu(3, menu)

	def settitle(self, title):
		self.__window.settitle(title)

	def setstate(self, state):
		self.__state = state
		self.__drawplay(self.__play._form, None)
		self.__drawpause(self.__pause._form, None)
		self.__drawstop(self.__stop._form, None)

	def getgeometry(self):
		return self.__window.getgeometry()

	def setcursor(self, cursor):
		if self.__window:
			self.__window.setcursor(cursor)
