# Names that start with `_' are for internal use only.

import gl, GL, DEVICE
from fl_or_gl import fl_or_gl
import fm
import string
from EVENTS import *
from debug import debug

error = 'windowinterface.error'

# Cursors
_ARROW = 0				# predefined
_WATCH = 1

# Colors
_DEF_BGCOLOR = 255,255,255		# white
_DEF_FGCOLOR =   0,  0,  0		# black

_window_list = {}			# mapping from window ID to object
_image_cache = {}			# cache of prepared images

gl.foreground()
_screenwidth = gl.getgdesc(GL.GD_XPMAX)
_screenheight = gl.getgdesc(GL.GD_YPMAX)
_mscreenwidth = gl.getgdesc(GL.GD_XMMAX)
_mscreenheight = gl.getgdesc(GL.GD_YMMAX)
if _screenwidth == 1024 and \
	  _screenheight == 768 and \
	  gl.getgdesc(GL.GD_BITS_NORM_SNG_RED) == 3 and \
	  gl.getgdesc(GL.GD_BITS_NORM_SNG_GREEN) == 3 and \
	  gl.getgdesc(GL.GD_BITS_NORM_SNG_BLUE) == 2:
	_is_entry_indigo = 1
else:
	_is_entry_indigo = 0

_watch = [0x0ff0, 0x1ff8, 0x381c, 0x718e, \
	  0xe187, 0xc183, 0xc183, 0xc1f3, \
	  0xc1f3, 0xc003, 0xc003, 0xe007, \
	  0x700e, 0x381c, 0x1ff8, 0x0ff0, \
	 ]
_watch.reverse()			# Turn it upside-down
gl.defcursor(_WATCH, _watch*8)
gl.curorigin(_WATCH, 8, 8)

class _Toplevel:
	def init(self):
		if debug: print 'TopLevel.init()'
		self._parent_window = None
		self._subwindows = []
		self._fgcolor = _DEF_FGCOLOR
		self._bgcolor = _DEF_BGCOLOR
		self._cursor = ''
		self._win_lock = None
		return self

	def close(self):
		if debug: print 'TopLevel.close()'
		import posix
		global _image_cache
		for win in self._subwindows[:]:
			win.close()
		for key in _image_cache.keys():
			try:
				posix.unlink(_image_cache[key][-1])
			except posix.error:
				pass
		_image_cache = {}

	def setcursor(self, cursor):
		if debug: print 'TopLevel.setcursor('+`cursor`+')'
		for win in self._subwindows:
			win._setcursor(cursor)
		self._cursor = cursor

	def newwindow(self, x, y, w, h, title):
		if debug: print 'TopLevel.newwindow'+`x, y, w, h, title`
		window = _Window().init(self, x, y, w, h, title)
		_event._qdevice()
		self._subwindows.append(window)
		window._parent_window = self
		window._toplevel = window
		dummy = testevent()
		return window

	def getsize(self):
		if debug: print 'TopLevel.getsize()'
		return _mscreenwidth, _mscreenheight

	def usewindowlock(self, lock):
		if debug: print 'TopLevel.usewindowlock()'
		self._win_lock = lock

class _Event:
	def init(self):
		if debug: print 'Event.init()'
		self._queue = []
		self._curwin = None
		self._savemouse = None
		self._savex = None
		return self

	def _qdevice(self):
		if debug: print 'Event.qdevice()'
##		if _toplevel._win_lock:
##			_toplevel._win_lock.acquire()
		fl_or_gl.qdevice(DEVICE.REDRAW)
		fl_or_gl.qdevice(DEVICE.INPUTCHANGE)
		fl_or_gl.qdevice(DEVICE.WINQUIT)
		fl_or_gl.qdevice(DEVICE.WINSHUT)
		fl_or_gl.qdevice(DEVICE.KEYBD)
		fl_or_gl.qdevice(DEVICE.LEFTMOUSE)
		fl_or_gl.qdevice(DEVICE.MIDDLEMOUSE)
		fl_or_gl.qdevice(DEVICE.RIGHTMOUSE)
		gl.tie(DEVICE.LEFTMOUSE, DEVICE.MOUSEX, DEVICE.MOUSEY)
		gl.tie(DEVICE.MIDDLEMOUSE, DEVICE.MOUSEX, DEVICE.MOUSEY)
		gl.tie(DEVICE.RIGHTMOUSE, DEVICE.MOUSEX, DEVICE.MOUSEY)
##		if _toplevel._win_lock:
##			_toplevel._win_lock.release()

	def _readevent(self):
		if debug: print 'Event.readevent()'
		dev, val = gl.qread()
		return self._dispatch(dev, val)

	def _dispatch(self, dev, val):
		if debug: print 'Event.dispatch'+`dev,val`
		if dev == DEVICE.REDRAW:
			self._savemouse = None
			if _window_list.has_key(val):
				win = _window_list[val]
				win._must_redraw = 1
				if win._parent_window == _toplevel:
					if _toplevel._win_lock:
						_toplevel._win_lock.acquire()
					gl.winset(win._window_id)
					w, h = gl.getsize()
					if _toplevel._win_lock:
						_toplevel._win_lock.release()
					if (w, h) != (win._width, win._height):
						win._resize()
						return win, ResizeWindow, None
##			else:
##				print 'redraw event for unknown window '+`val`
			return None
		elif dev == DEVICE.INPUTCHANGE:
			self._savemouse = None
			if val == 0:
				self._curwin = None
			elif not _window_list.has_key(val):
##				print 'inputchange to unknown window '+`val`
				self._curwin = None
			else:
				self._curwin = _window_list[val]
			return None
		elif dev == DEVICE.KEYBD:
			self._savemouse = None
			if gl.getvaluator(DEVICE.LEFTALTKEY) or \
				  gl.getvaluator(DEVICE.RIGHTALTKEY):
				val = val + 128
			return self._curwin, KeyboardInput, chr(val)
		elif dev in (DEVICE.LEFTMOUSE, DEVICE.MIDDLEMOUSE, DEVICE.RIGHTMOUSE):
			self._savemouse = dev, val
		elif dev == DEVICE.MOUSEX:
			self._savex = val
		elif dev == DEVICE.MOUSEY:
			if not self._curwin or not self._savemouse:
##				print 'mouse event when not in known window'
				return None
			y = val
			dev, val = self._savemouse
			x = self._savex
			if _toplevel._win_lock:
				_toplevel._win_lock.acquire()
			gl.winset(self._curwin._window_id)
			x0, y0 = gl.getorigin()
			if _toplevel._win_lock:
				_toplevel._win_lock.release()
			x = float(x - x0) / self._curwin._width
			y = 1.0 - float(y - y0) / self._curwin._height
			buttons = []
			adl = self._curwin._active_display_list
			if adl:
				for but in adl._buttonlist:
					if but._inside(x, y):
						buttons.append(but)
			if dev == DEVICE.LEFTMOUSE:
				if val:
					dev = Mouse0Press
				else:
					dev = Mouse0Release
			elif dev == DEVICE.MIDDLEMOUSE:
				if val:
					dev = Mouse1Press
				else:
					dev = Mouse1Release
			else:
				if val:
					dev = Mouse2Press
				else:
					dev = Mouse2Release
			return self._curwin, dev, (x, y, buttons)
		elif dev in (DEVICE.MOUSEX, DEVICE.MOUSEY):
			raise error, 'got mouse position event'
		elif dev in (DEVICE.WINSHUT, DEVICE.WINQUIT):
			return self._curwin, WindowExit, None
##		else:
##			print 'huh!',`dev,val`
		return self._curwin, dev, val

	def _getevent(self, block):
		if debug: print 'Event.getevent('+`block`+')'
		qtest = gl.qtest()
		while 1:
			while qtest:
				event = self._readevent()
				if event:
					self._queue.append(event)
				qtest = gl.qtest()
			for winkey in _window_list.keys():
				win = _window_list[winkey]
				if win._must_redraw:
					win._redraw()
			if self._queue:
				return 1
			if not block:
				return 0
			qtest = 1	# block on next round

	def _doevent(self, dev, val):
		if debug: print 'Event.doevent'+`dev,val`
		event = self._dispatch(dev, val)
		for winkey in _window_list.keys():
			win = _window_list[winkey]
			if win._must_redraw:
				win._redraw()
		return event
		
	def enterevent(self, win, event, arg):
		if debug: print 'Event.enterevent'+`win,event,arg`
		self._queue.append((win, event, arg))

	def readevent(self):
		if debug: print 'Event.readevent()'
		dummy = self._getevent(1)
		event = self._queue[0]
		del self._queue[0]
		return event

	def testevent(self):
		if debug: print 'Event.testevent()'
		return self._getevent(0)

	def pollevent(self):
		if debug: print 'Event.pollevent()'
		# Return the first event in the queue if there is one.
		if self.testevent():
			return self.readevent()
		else:
			return None

	def peekevent(self):
		if debug: print 'Event.peekevent()'
		# Return the first event in the queue if there is one,
		# but don't remove it.
		if self.testevent():
			return self._queue[0]
		else:
			return None

	def waitevent(self):
		if debug: print 'Event.waitevent()'
		# Wait for an event to occur, but don't return it.
		dummy = self._getevent(1)

	def getfd(self):
		return gl.qgetfd()
			
class _Font:
	def init(self, fontname, size):
		self._font = _findfont(fontname, size)
		self._baseline, self._fontheight, = self._fontparams()
		self._pointsize = size
		self._closed = 0
##		self._pointsize = float(self.fontheight()) * 72.0 / 25.4
##		print '_Font().init() pointsize:',size,self._pointsize
		return self

	def close(self):
		self._closed = 1

	def is_closed(self):
		return self._closed

	def strsize(self, str):
		if self.is_closed():
			raise error, 'font object already closed'
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * self._fontheight
		for str in strlist:
			width = self._font.getstrwidth(str)
			if width > maxwidth:
				maxwidth = width
		return float(maxwidth) * _mscreenwidth / _screenwidth, \
			  float(maxheight) * _mscreenheight / _screenheight

	def baseline(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return float(self._baseline) * _mscreenheight / _screenheight

	def fontheight(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return float(self._fontheight) * _mscreenheight / _screenheight

	def pointsize(self):
		if self.is_closed():
			raise error, 'font object already closed'
		return self._pointsize

	def _fontparams(self):
		(printermatched, fixed_width, xorig, yorig, xsize, ysize, \
			  fontheight, nglyphs) = self._font.getfontinfo()
		baseline = fontheight - yorig
		return baseline, fontheight

class _Button:
	def init(self, dispobj, x, y, w, h):
		self._dispobj = dispobj
		window = dispobj._window
		self._corners = x, y, x + w, y + h
		self._coordinates = window._convert_coordinates(x, y, w, h)
		self._color = dispobj._fgcolor
		self._hicolor = dispobj._fgcolor
		self._linewidth = dispobj._linewidth
		self._hiwidth = self._linewidth
		d = dispobj._displaylist
		if dispobj._curcolor != self._color:
			d.append(gl.RGBcolor, self._color)
			dispobj._curcolor = self._color
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.recti, self._coordinates)
		return self

	def close(self):
		dispobj = self._dispobj
		if dispobj:
			dispobj._buttonlist.remove(self)
		self._dispobj = None

	def is_closed(self):
		return self._dispobj == None

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, *color):
		if self.is_closed():
			raise error, 'button already closed'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._hicolor = color

# XXXX Jack says:
# is this code correct? It seems that it only highlights the button once,
# without altering the display list. Also, in the current incarnation if
# highlighting is done by changing line thickness the unhighlight doesn't work.
	def highlight(self):
		if self.is_closed():
			raise error, 'button already closed'
		dispobj = self._dispobj
		if dispobj._window._active_display_list != dispobj:
			raise error, 'can only highlight rendered button'
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(self._dispobj._window._window_id)
		gl.RGBcolor(self._hicolor)
		gl.linewidth(self._hiwidth)
		gl.recti(self._coordinates)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def unhighlight(self):
		if self.is_closed():
			raise error, 'button already closed'
		dispobj = self._dispobj
		if dispobj._window._active_display_list != dispobj:
			raise error, 'can only unhighlight rendered button'
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(self._dispobj._window._window_id)
		gl.RGBcolor(self._color)
		gl.linewidth(self._linewidth)
		gl.recti(self._coordinates)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def _inside(self, x, y):
		# return 1 iff the given coordinates fall within the button
		if (self._corners[0] <= x <= self._corners[2]) and \
			  (self._corners[1] <= y <= self._corners[3]):
			return 1
		else:
			return 0

# Display List.  A window may have several display lists.  When the
# list is rendered, it becomes the active display list.
class _DisplayList:
	def init(self, window):
		self._window = window	# window to which this belongs
		self._rendered = 0	# 1 iff rendered at some point
		self._bgcolor = window._bgcolor
		self._fgcolor = window._fgcolor
		self._font = None
		self._fontheight = 0
		self._baseline = 0
		self._curfont = None
		self._curcolor = self._bgcolor
		self._displaylist = []
		self._buttonlist = []
		self._linewidth = 1
		self._curpos = 0, 0
		self._xpos = 0
		return self

	def close(self):
		for button in self._buttonlist[:]:
			button.close()
		window = self._window
		if window:
			window._displaylists.remove(self)
			if window._active_display_list == self:
				window._active_display_list = None
				window._redraw()
		self._window = None
		self._rendered = 0
		self._displaylist = []

	def is_closed(self):
		return self._window == None

	def render(self):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		window._active_display_list = self
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(window._window_id)
		gl.RGBcolor(self._bgcolor)
		gl.clear()
		for funcargs in self._displaylist:
			if type(funcargs) == type(()):
				func, args = funcargs
				func(args)
			else:
				funcargs()
		gl.gflush()
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		self._rendered = 1

	def clone(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		new = _DisplayList().init(self._window)
		new._displaylist = self._displaylist[:]
		new._fgcolor = self._fgcolor
		new._bgcolor = self._bgcolor
		new._curcolor = self._curcolor
		new._font = self._font
		new._fontheight = self._fontheight
		new._baseline = self._baseline
		new._curfont = self._curfont
		return new

	def fgcolor(self, *color):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color

	def linewidth(self, width):	# XXX--should use a better unit
		self._linewidth = int(width)

	def newbutton(self, *coordinates):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		button = _Button().init(self, x, y, w, h)
		self._buttonlist.append(button)
		return button

	def drawbox(self, *coordinates):
		window = self._window
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		d = self._displaylist
		x0, y0, x1, y1 = window._convert_coordinates(x, y, w, h)
		if self._curcolor != self._fgcolor:
			d.append(gl.RGBcolor, self._fgcolor)
			self._curcolor = self._fgcolor
		d.append(gl.linewidth, self._linewidth)
		d.append(gl.recti, (x0, y0, x1, y1))

	def display_image_from_file(self, file, *crop):
		if self.is_closed():
			raise error, 'displaylist already closed'
		window = self._window
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(crop) == 4:
			top, bottom, left, right = crop
			if top + bottom >= 1 or left + right >= 1:
				raise TypeError, 'arg count mismatch'
		elif len(crop) == 0:
			top, bottom, left, right = 0, 0, 0, 0
		else:
			raise TypeError, 'arg count mismatch'
		win_x, win_y, win_w, win_h, im_x, im_y, im_w, im_h, \
			  depth, scale, image = \
				  window._prepare_image_from_file(file, \
					  top, bottom, left, right)
		d = self._displaylist
		d.append(gl.rectzoom, (scale, scale))
		if depth == 1:
			d.append(gl.pixmode, (GL.PM_SIZE, 8))
		else:
			d.append(gl.pixmode, (GL.PM_SIZE, 32))
			depth = 4
		if (im_x, im_y) == (0, 0):
			d.append(gl.lrectwrite, (win_x, win_y, \
				  win_x+win_w-1, win_y+win_h-1, image))
		else:
			d.append(gl.pixmode, (GL.PM_STRIDE, im_w))
			d.append(gl.lrectwrite, (win_x, win_y, \
				  win_x+win_w-1, win_y+win_h-1, \
				  image[(im_w*im_y+im_x)*depth:]))
			d.append(gl.pixmode, (GL.PM_STRIDE, 0))
		return float(win_x) / window._width, \
			  float(win_y) / window._height, \
			  float(win_w) / window._width, \
			  float(win_h) / window._height

	def usefont(self, fontobj):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		self._font = fontobj
		f = float(_screenheight) / _mscreenheight / window._height
		self._baseline = fontobj.baseline() * f
		self._fontheight = fontobj.fontheight() * f
		return self._baseline, self._fontheight, fontobj.pointsize()

	def setfont(self, font, size):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, *opt_margin):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if len(opt_margin) == 0:
			margin = 0
		elif len(opt_margin) == 1:
			margin = opt_margin[0]
		else:
			raise error, 'too many arguments'
		if margin < 0 or margin >= 1:
			raise error, 'rediculous margin: ' + `margin`
		mfac = 1 - margin
		window = self._window
		strlist = string.splitfields(str, '\n')
		nlines = len(strlist)
		fontobj = findfont(fontname, 100)
		firsttime = 1
		height = fontobj.fontheight() * _screenheight / _mscreenheight
		while firsttime or height > window._height*mfac:
			firsttime = 0
			ps = float(window._height*mfac*_mscreenheight*fontobj.pointsize())/\
				  float(nlines*fontobj.fontheight()*_screenheight)
			fontobj.close()
			if ps <= 0:
				raise error, 'string does not fit in window'
			fontobj = findfont(fontname, ps)
			height = fontobj.fontheight() * _screenheight / _mscreenheight
		for str in strlist:
			width, height = fontobj.strsize(str)
			width = width * _screenwidth / _mscreenwidth
			while width > window._width * mfac:
				ps = float(window._width) * mfac * fontobj.pointsize() / width
				if ps <= 0:
					raise error, 'string does not fit in window'
				fontobj.close()
				fontobj = findfont(fontname, ps)
				width, height = fontobj.strsize(str)
				width = width * _screenwidth / _mscreenwidth
		return self.usefont(fontobj)

	def strsize(self, str):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = 0
		for str in strlist:
			width, height = self._font.strsize(str)
			width = width * _screenwidth / _mscreenwidth
			if width > maxwidth:
				maxwidth = width
			maxheight = maxheight + self._fontheight
		return float(maxwidth) / self._window._width, maxheight

	def strfit(self, text, width, height):
		# this could be made more efficient
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		for i in range(1, len(text)):
			w, h = self.strsize(text[:i])
			if w > width or h > height:
				return i - 1
		return len(text)

	def setpos(self, x, y):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._curpos = x, y
		self._xpos = x

	def getpos(self):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self._curpos

	def writestr(self, str):
		if self.is_closed():
			raise error, 'displaylist already closed'
		if self._rendered:
			raise error, 'displaylist already rendered'
		if not self._font:
			raise error, 'font not set'
		strlist = string.splitfields(str, '\n')
		d = self._displaylist
		if self._curcolor != self._fgcolor:
			d.append(gl.RGBcolor, self._fgcolor)
			self._curcolor = self._fgcolor
		if self._curfont != self._font._font:
			d.append(self._font._font.setfont)
			self._curfont = self._font._font
		x, y = self._curpos
		oldx, oldy = self._curpos
		oldy = oldy - self._baseline
		maxx = oldx
		for str in strlist:
			x0, y0, x1, y1 = \
				  self._window._convert_coordinates(x, y, 0, 0)
			d.append(gl.cmov2, (x0, y0))
			d.append(fm.prstr, str)
			self._curpos = x + float(self._font._font.getstrwidth(\
				  str)) / self._window._width, y
			x = self._xpos
			y = y + self._fontheight
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, \
			  newy - oldy + self._fontheight - self._baseline

class _Window:
	def init(self, parent, x, y, w, h, title):
		if debug: print 'Window.init'+`parent, x, y, w, h, title`
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		try:
			import calcwmcorr
			wmcorr_x, wmcorr_y = calcwmcorr.calcwmcorr()
		except ImportError:
			wmcorr_x, wmcorr_y = 0, 0
		x0, y0 = x, y
		x1, y1 = x0 + w, y0 + h
		x0 = int(float(x0)/_mscreenwidth*_screenwidth+0.5)
		y0 = int(float(y0)/_mscreenheight*_screenheight+0.5)
		x1 = int(float(x1)/_mscreenwidth*_screenwidth+0.5)
		y1 = int(float(y1)/_mscreenheight*_screenheight+0.5)
		gl.prefposition(x0 - wmcorr_x, x1 - wmcorr_x, \
			  _screenheight - y1 - 1 + wmcorr_y, \
			  _screenheight - y0 - 1 + wmcorr_y)
		if not title:
			gl.noborder()
			title = ''
		self._window_id = gl.winopen(title)
		gl.winconstraints()
		self._parent_window = parent
		return self._init2()

	def _init2(self):
		if debug: print 'Window.init2()'
		# we are already locked on entry, we are unlocked on return
		gl.RGBmode()
		gl.gconfig()
		gl.reshapeviewport()
		self._width, self._height = gl.getsize()
		gl.ortho2(-0.5, self._width-0.5, -0.5, self._height-0.5)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		self._bgcolor = self._parent_window._bgcolor
		self._fgcolor = self._parent_window._fgcolor
		self._subwindows = []
		self._displaylists = []
		self._active_display_list = None
		_window_list[self._window_id] = self
		self._redraw()
		self._setcursor(self._parent_window._cursor)
		return self

	def newwindow(self, *coordinates):
		if debug: print 'Window.newwindow'+`coordinates`
		if len(coordinates) == 1 and type(coordinates) == type(()):
			coordinates = coordinates[0]
		if len(coordinates) != 4:
			raise TypeError, 'arg count mismatch'
		x, y, w, h = coordinates
		x0, y0, x1, y1 = self._convert_coordinates(x, y, w, h)
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(self._toplevel._window_id)
		tx, ty = gl.getorigin()
		gl.winset(self._window_id)
		wx, wy = gl.getorigin()
		wx, wy = wx - tx, wy - ty
		x0, y0 = x0 + wx, y0 + wy
		x1, y1 = x1 + wx, y1 + wy
		new_window = _Window()
		new_window._window_id = gl.swinopen(self._window_id)
		gl.winposition(x0, x1, y0, y1)
		self._subwindows.append(new_window)
		new_window._parent_window = self
		new_window._sizes = x, y, w, h
		new_window._toplevel = self._toplevel
		new_window = new_window._init2()
		dummy = testevent()
		return new_window

	def close(self):
		if debug: print 'Window.close()'
		if not _window_list.has_key(self._window_id):
			# apparently already closed
			return
		for win in self._subwindows[:]:
			win.close()
		for displist in self._displaylists:
			displist.close()
		self._displaylists = []
		gl.winclose(self._window_id)
		del _window_list[self._window_id]
		parent = self._parent_window
		self._parent_window = None
		if parent:
			parent._subwindows.remove(self)

	def is_closed(self):
		return not _window_list.has_key(self._window_id)

	def fgcolor(self, *color):
		if debug: print 'Window.fgcolor()'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._fgcolor = color

	def bgcolor(self, *color):
		if debug: print 'Window.bgcolor()'
		if len(color) == 1 and type(color[0]) == type(()):
			color = color[0]
		if len(color) != 3:
			raise TypeError, 'arg count mismatch'
		self._bgcolor = color
		if not self._active_display_list:
			if _toplevel._win_lock:
				_toplevel._win_lock.acquire()
			gl.winset(self._window_id)
			gl.RGBcolor(self._bgcolor)
			gl.clear()
			if _toplevel._win_lock:
				_toplevel._win_lock.release()

	def settitle(self, title):
		if self._parent_window != _toplevel:
			raise error, 'can only settitle at top-level'
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.wintitle(title)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def newdisplaylist(self, *bgcolor):
		list = _DisplayList().init(self)
		self._displaylists.append(list)
		if len(bgcolor) == 1 and type(bgcolor[0]) == type(()):
			bgcolor = bgcolor[0]
		if len(bgcolor) == 3:
			list._bgcolor = list._curcolor = bgcolor
		elif len(bgcolor) != 0:
			raise TypeError, 'arg count mismatch'
		return list

	def pop(self):
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		gl.winpop()
		if _toplevel._win_lock:
			_toplevel._win_lock.release()

	def getgeometry(self):
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		x, y = gl.getorigin()
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		h = float(_mscreenheight) / _screenheight
		w = float(_mscreenwidth) / _screenwidth
		return float(x) * w, (_screenheight - y - self._height) * h, \
			  self._width * w, self._height * h

	def _resize(self):
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		if self._parent_window != _toplevel:
			x, y, w, h = self._sizes
			x0, y0, x1, y1 = \
				  self._parent_window._convert_coordinates(\
					  x, y, w, h)
			gl.winset(self._window_id)
			gl.winposition(x0, x1, y0, y1)
		gl.winset(self._window_id)	# just to be sure
		gl.reshapeviewport()
		self._width, self._height = gl.getsize()
		gl.ortho2(-0.5, self._width-0.5, -0.5, self._height-0.5)
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		# close all display objects after a resize
		for displist in self._displaylists[:]:
			displist.close()
		for win in self._subwindows:
			win._resize()

	def _redraw(self):
		if self._active_display_list:
			self._active_display_list.render()
		else:
			if _toplevel._win_lock:
				_toplevel._win_lock.acquire()
			gl.winset(self._window_id)
			gl.RGBcolor(self._bgcolor)
			gl.clear()
			if _toplevel._win_lock:
				_toplevel._win_lock.release()
		self._must_redraw = 0

	def _setcursor(self, cursor):
		for win in self._subwindows:
			win._setcursor(cursor)
		if _toplevel._win_lock:
			_toplevel._win_lock.acquire()
		gl.winset(self._window_id)
		if cursor == 'watch':
			gl.setcursor(_WATCH, 0, 0)
		elif cursor == '':	# default is arrow cursor
			gl.setcursor(_ARROW, 0, 0)
		else:
			if _toplevel._win_lock:
				_toplevel._win_lock.release()
			raise error, 'unknown cursor glyph'
		if _toplevel._win_lock:
			_toplevel._win_lock.release()
		self._cursor = cursor

	def _prepare_image_from_file(self, file, top, bottom, left, right):
		cachekey = `file`+':'+`self._width`+'x'+`self._height`
		if _image_cache.has_key(cachekey):
			retval = _image_cache[cachekey]
			filename = retval[-1]
			try:
				import imgfile
				image = imgfile.read(filename)
				return retval[:-1] + (image,)
			except:		# any error...
				del _image_cache[cachekey]
		f = open(file, 'r')
		magic = f.read(4)
		if magic[:2] == '\001\332':
			f.close()
			retval = self._prepare_RGB_image_from_file(file, \
				  top, bottom, left, right)
		elif magic == '\377\330\377\340':
			f.seek(0)
			retval = self._prepare_JPEG_image_from_filep(f, \
				  top, bottom, left, right)
			f.close()
		else:
			f.close()
			import torgb
			try:
				f = torgb.torgb(file)
			except torgb.error, msg:
				raise error, msg
			retval = self._prepare_RGB_image_from_file(f, \
				  top, bottom, left, right)
			if f != file:
				import os
				os.unlink(f)
		import tempfile
		filename = tempfile.mktemp()
		try:
			import imgfile
			imgfile.write(filename, retval[10], retval[6], \
				  retval[7], retval[8])
		except:			# any error...
			print 'Warning: caching image failed'
			return retval
		_image_cache[cachekey] = retval[:-1] + (filename,)
		return retval

	def _prepare_RGB_image_from_file(self, file, top, bottom, left, right):
		import imgfile
		xsize, ysize, zsize = imgfile.getsizes(file)
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		width, height = self._width, self._height
		scale = min(float(width)/(xsize - left - right), \
			    float(height)/(ysize - top - bottom))
		if scale == int(scale):
			image = imgfile.read(file)
			width, height = xsize, ysize
		else:
			width = int(xsize * scale)
			height = int(ysize * scale)
			image = imgfile.readscaled(file, width, height, 'box')
			top = int(top * scale)
			bottom = int(bottom * scale)
			left = int(left * scale)
			right = int(right * scale)
			scale = 1.0
		x, y = (self._width-(width-left-right))/2, \
			  (self._height-(height-top-bottom))/2
		return x, y, width - left - right, height - top - bottom, \
			  left, bottom, width, height, zsize, scale, image

	def _prepare_JPEG_image_from_filep(self, filep, top, bottom, left, right):
		import cl, CL
		header = filep.read(16)
		filep.seek(0)
		scheme = cl.QueryScheme(header)
		decomp = cl.OpenDecompressor(scheme)
		header = filep.read(cl.QueryMaxHeaderSize(scheme))
		filep.seek(0)
		headersize = decomp.ReadHeader(header)
		xsize = decomp.GetParam(CL.IMAGE_WIDTH)
		ysize = decomp.GetParam(CL.IMAGE_HEIGHT)
		if _is_entry_indigo:
			original_format = CL.RGB
			zsize = 1
		else:
			original_format = CL.RGBX
			zsize = 4
		params = [CL.ORIGINAL_FORMAT, original_format, \
			  CL.ORIENTATION, CL.BOTTOM_UP, \
			  CL.FRAME_BUFFER_SIZE, \
				 xsize*ysize*CL.BytesPerPixel(original_format)]
		decomp.SetParams(params)
		image = decomp.Decompress(1, filep.read())
		decomp.CloseDecompressor()

		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		width, height = self._width, self._height
		scale = min(float(width)/(xsize - left - right), \
			  float(height)/(ysize - top - bottom))
		if scale != int(scale):
			import imageop
			width = int(xsize * scale)
			height = int(ysize * scale)
			image = imageop.scale(image, zsize, xsize, ysize, \
					      width, height)
			top = int(top * scale)
			bottom = int(bottom * scale)
			left = int(left * scale)
			right = int(right * scale)
			scale = 1.0
		else:
			width, height = xsize, ysize
		# here width and height are the width and height in
		# pixels of the scaled image, top, bottom, left, right
		# are the amount to crop off the image in pixels.
		x, y = (self._width-(width-left-right))/2, \
			  (self._height-(height-top-bottom))/2
		return x, y, width - left - right, height - top - bottom, \
			  left, bottom, width, height, zsize, scale, image

	def _convert_coordinates(self, x, y, w, h):
		x0, y0 = x, y
		x1, y1 = x + w, y + h
		# convert relative sizes to pixel sizes relative to
		# lower-left corner of the window
		x0 = int(self._width * x0 + 0.5)
		y0 = int(self._height * y0 + 0.5)
		x1 = int((self._width - 1) * x1 + 0.5)
		y1 = int((self._height - 1) * y1 + 0.5)
		y0, y1 = self._height - y1 - 1, self._height - y0 - 1
		return x0, y0, x1, y1


# Font stuff
def _findfont(fontname, size):
	if not _fontmap.has_key(fontname):
		print 'Warning: ' + `fontname` + ' not in fontmap'
	else:
		if int(size) == size:
			size = int(size)
		fontname = _fontmap[fontname]
	key = fontname + `size`
	if _fontcache.has_key(key):
		return _fontcache[key]
	key1 = fontname + `1`
	if _fontcache.has_key(key1):
		f1 = _fontcache[key1]
	else:
		f1 = _fontcache[key1] = fm.findfont(fontname)
	f = _fontcache[key] = f1.scalefont(size)
	return f

_fontcache = {}
_fontmap = { \
	  'Times-Roman':	'Times-Roman', \
	  'Times-Italic':	'Times-Italic', \
	  'Times-Bold':		'Times-Bold', \
	  'Utopia-Bold':	'Utopia-Bold', \
	  'Palatino-Bold':	'Palatino-Bold', \
	  }

_toplevel = _Toplevel().init()
_event = _Event().init()

# Interface routines for the top level.
def newwindow(x, y, w, h, title):
	return _toplevel.newwindow(x, y, w, h, title)

def close():
	_toplevel.close()

def setcursor(cursor):
	_toplevel.setcursor(cursor)

def getsize():
	return _toplevel.getsize()

def readevent():
	return _event.readevent()

def pollevent():
	return _event.pollevent()

def waitevent():
	_event.waitevent()

def peekevent():
	return _event.peekevent()

def testevent():
	return _event.testevent()

def enterevent(win, event, arg):
	_event.enterevent(win, event, arg)

def getfd():
	return _event.getfd()

def findfont(fontname, pointsize):
	return _Font().init(fontname, pointsize)

def beep():
	gl.ringbell()

def usewindowlock(lock):
	_toplevel.usewindowlock(lock)
