import Win
import Qd
import time
import Evt
import Events
import Windows
import MacOS

#
# The cursors we need
#
_arrow = Qd.arrow
_watch = Qd.GetCursor(4).data

#
# Conversion factors for mm->pixels
#
_x_pixel_per_inch, _y_pixel_per_inch = Qd.ScreenRes()
_x_pixel_per_mm = _x_pixel_per_inch / 25.4
_y_pixel_per_mm = _y_pixel_per_inch / 25.4
#
# Conversion from inner-window coordinates (as in cmif) to outer
# XXXX Not correct
#
_window_left_offset=2
_window_right_offset=2
_window_top_offset=2
_window_bottom_offset=2

#
# Assorted constants
#
error = 'windowinterface.error'
FALSE, TRUE = 0, 1
ReadMask, WriteMask = 1, 2

EVENTMASK=0xffff

_X=0
_Y=1
_WIDTH=2
_HEIGHT=3

_size_cache = {}

Version = 'dummy'

from EVENTS import *

class _Event:
	"""This class is only used as a base-class for toplevel.
	the separation is for clarity only."""
	
	def __init__(self):
		# timer handling
		self._timers = []
		self._timer_id = 0
		self._timerfunc = None
		self._time = time.time()

	def mainloop(self):
		while 1:
			while self._timers:
				t = time.time()
				sec, cb, tid = self._timers[0]
				sec = sec - (t - self._time)
				self._time = t
				if sec <= 0:
##					print 'BEFORE DEL', len(self._timers), self._timers[0][0]
					del self._timers[0]
##					print 'AFTER DEL', len(self._timers), self._timers[0][0]
					func, args = cb
					apply(func, args)
				else:
					self._timers[0] = sec, cb, tid
					break
			if self._timers:
				timeout = self._timers[0][0]
			else:
				timeout = 100000
			gotone, event = Evt.WaitNextEvent(EVENTMASK, timeout)
			if gotone:
				self._handle_event(event)
				what, message, when, where, modifiers = event
				
	def _handle_event(self, event):
		"""Handle a single MacOS event"""
		what, message, when, where, modifiers = event
		if what == Events.mouseDown:
			self._handle_mousedown(event)
		elif what == Events.keyDown:
			self._handle_keydown(event)
		elif what == Events.updateEvt:
			wid = Win.WhichWindow(message)
			if not wid:
				MacOS.HandleEvent(event)
			else:
				ourwin = self._find_wid(wid)
				if not ourwin:
					MacOS.HandleEvent(event)
				else:
					Qd.SetPort(wid)
					wid.BeginUpdate()
					ourwin._redraw()
					wid.EndUpdate()
		else:
			MacOS.HandleEvent(event)

	def _handle_mousedown(self, event):
		"""Handle a MacOS mouseDown event"""
		what, message, when, where, modifiers = event
		partcode, wid = Win.FindWindow(where)
		if not wid:
			# It is not ours.
			MacOS.HandleEvent(event)
			return
		if partcode == Windows.inMenuBar:
			pass # XXXX
		elif partcode == Windows.inContent:
			if wid == Win.FrontWindow():
				# Frontmost. Handle click.
				pass # XXXX
			else:
				# Not frontmost. Activate.
				wid.SelectWindow()
				return
		elif partcode == Windows.inDrag:
			if wid == Win.FrontWindow():
				# Frontmost. Handle click.
				pass # XXXX
			else:
				# Not frontmost. Activate.
				wid.SelectWindow()
				return
		elif partcode == Windows.inGrow:
			pass # XXXX
		elif partcode == Windows.inGoAway:
			if not wid.TrackGoAway(where):
				return
			sys.exit(0) # XXXX, incorrect
		elif partcode == Windows.inZoomIn:
			pass # XXXX
		elif partcode == Windows.inZoomOut:
			pass # XXXX
		else:
			# In desk or syswindow. Pass on.
			MacOS.HandleEvent(event)

	def _handle_keydown(self, event):
		"""Handle a MacOS keyDown event"""
		MacOS.HandleEvent(event)

	# timer interface
	def settimer(self, sec, cb):
		t0 = time.time()
		if self._timers:
			t, a, i = self._timers[0]
			t = t - (t0 - self._time) # can become negative
			self._timers[0] = t, a, i
		self._time = t0
		self._timer_id = self._timer_id + 1
		t = 0
		for i in range(len(self._timers)):
			time0, dummy, tid = self._timers[i]
			if t + time0 > sec:
				self._timers[i] = (time0 - sec + t, dummy, tid)
				self._timers.insert(i, (sec - t, cb, self._timer_id))
				return self._timer_id
			t = t + time0
		self._timers.append(sec - t, cb, self._timer_id)
		return self._timer_id

	def canceltimer(self, id):
		for i in range(len(self._timers)):
			t, cb, tid = self._timers[i]
			if tid == t:
				del self._timers[i]
				if i < len(self._timers):
					tt, cb, tid = self._timers[i]
					self._timers[i] = (tt + t, cb, tid)
				return

	# file descriptor interface
	def select_setcallback(self, fd, func, args, mask = ReadMask):
		raise error, 'No select_setcallback for the mac'

# The _Toplevel class represents the root of all windows.  It is never
# accessed directly by any user code.
class _Toplevel(_Event):
	def __init__(self):
		_Event.__init__(self)
		self._closecallbacks = []
		self._subwindows = []
		self._wid_to_window = {}
		self._bgcolor = 0xffff, 0xffff, 0xffff # white
		self._fgcolor =      0,      0,      0 # black
		self._hfactor = self._vfactor = 1.0

	def close(self):
		for func, args in self._closecallbacks:
			apply(func, args)
		for win in self._subwindows[:]:
			win.close()
		self.__init__()		# clears all lists

	def addclosecallback(self, func, args):
		self._closecallbacks.append(func, args)

	def newwindow(self, x, y, w, h, title, pixmap = 0, transparent = 0):
		x = int(x*_x_pixel_per_mm)
		y = int(y*_y_pixel_per_mm)
		w = int(w*_x_pixel_per_mm)
		h = int(h*_y_pixel_per_mm)
		print 'TOPLEVEL WINDOW', x, y, w, h, title
		rBounds = (x-_window_left_offset, y-_window_top_offset, 
				x+w+_window_right_offset, y+h+_window_bottom_offset)
		wid = Win.NewCWindow(rBounds, title, 1, 0, -1, 1, 0 )
		rv = _Window(self, wid, x, y, w, h, 0, pixmap, transparent)
		self._wid_to_window[wid] = rv
		return rv

	def newcmwindow(self, x, y, w, h, title, pixmap = 0, transparent = 0):
		x = int(x*_x_pixel_per_mm)
		y = int(y*_y_pixel_per_mm)
		w = int(w*_x_pixel_per_mm)
		h = int(h*_y_pixel_per_mm)
		print 'TOPLEVEL CM WINDOW', x, y, w, h, title
		rBounds = (x-_window_left_offset, y-_window_top_offset, 
				x+w+_window_right_offset, y+h+_window_bottom_offset)
		wid = Win.NewCWindow(rBounds, title, 1, 0, -1, 1, 0 )
		rv = _Window(self, wid, x, y, w, h, 1, pixmap, transparent)
		self._wid_to_window[wid] = rv
		return rv
		
	def _close_wid(self, wid):
		"""Close a MacOS window and remove references to it"""
		del self._wid_to_window[wid]
		wid.CloseWindow()
		
	def _find_wid(self, wid):
		"""Map a MacOS window to our window object, or None"""
		if self._wid_to_window.has_key(wid):
			return self._wid_to_window[wid]
		return None

	def setcursor(self, cursor):
		if cursor == 'watch':
			Qd.SetCursor(_watch)
		else:
			Qd.SetCursor(_arrow)

	def pop(self):
		pass

	def push(self):
		pass

	def usewindowlock(self, lock):
		pass

class _Window:
	"""Base window, also base class for subwindows (eventually)"""
	
	def __init__(self, parent, wid, x, y, w, h, defcmap = 0, pixmap = 0, 
			transparent = 0):
		parent._subwindows.append(self)
		self._parent = parent
		self._wid = wid
		self._subwindows = []
		self._displists = []
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._transparent = transparent
		# conversion factors to convert from mm to relative size
		# (this uses the fact that _hfactor == _vfactor == 1.0
		# in toplevel)
		self._hfactor = parent._hfactor / w
		self._vfactor = parent._vfactor / h
		self._rect = 0, 0, w, h
		self._clip = None

	def close(self):
		if self._parent is None:
			return		# already closed
		self._parent._subwindows.remove(self)
		self._parent._close_wid(self._wid)
		self._parent = None
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
			
	def _close_wid(self, wid):
		pass	# Not needed for subwindows

	def is_closed(self):
		return self._parent is None

	def newwindow(self, (x, y, w, h), pixmap = 0, transparent = 0):
		print 'SUB WINDOW', x, y, w, h
		rv = _Window(self, None, x, y, w, h, 0, pixmap, transparent)
		self._clip = None
		return rv

	def necmwwindow(self, (x, y, w, h), pixmap = 0, transparent = 0):
		print 'SUB CM WINDOW', x, y, w, h
		rv = _Window(self, None, x, y, w, h, 1, pixmap, transparent)
		self._clip = None
		return rv

	def fgcolor(self, color):
		r, g, b = color
		self._fgcolor = r*0x101, g*0x101, b*0x101

	def bgcolor(self, color):
		r, g, b = color
		self._bgcolor = r*0x101, g*0x101, b*0x101

	def setcursor(self, cursor):
		raise 'window.setcursor called'
		for win in self._subwindows:
			win.setcursor(cursor)

	def newdisplaylist(self, *bgcolor):
		if bgcolor != ():
			bgcolor = bgcolor[0]
			bgcolor = bgcolor[0]*0x101, bgcolor[1]*0x101, bgcolor[2]*0x101
		else:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)

	def settitle(self, title):
		if self._parent != toplevel:
			raise error, 'can only settitle at top-level'
		pass

	def pop(self):
		if self._parent:
			self._parent._clip = None
		self._clip = None
		pass

	def push(self):
		if self._parent:
			self._parent._clip = None
		self._clip = None
		pass

	def setredrawfunc(self, func):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'

	def register(self, event, func, arg):
		if func is None or callable(func):
			pass
		else:
			raise error, 'invalid function'

	def unregister(self, event):
		pass

	def destroy_menu(self):
		pass

	def create_menu(self, list, title = None):
		pass

	def _image_size(self, file):
		if _size_cache.has_key(file):
			return _size_cache[file]
		import img
		try:
			reader = img.reader(None, file)
		except img.error, arg:
			raise error, arg
		width = reader.width
		height = reader.height
		_size_cache[file] = width, height
		return width, height
	def _convert_coordinates(self, coordinates):
		# convert relative sizes to pixel sizes relative to
		# upper-left corner of the window
		x, y = coordinates[:2]
##		if not (0 <= x <= 1 and 0 <= y <= 1):
##			raise error, 'coordinates out of bounds'
		px = int((self._rect[_WIDTH] - 1) * x + 0.5) + self._rect[_X]
		py = int((self._rect[_HEIGHT] - 1) * y + 0.5) + self._rect[_Y]
		if len(coordinates) == 2:
			return px, py
		w, h = coordinates[2:]
##		if not (0 <= w <= 1 and 0 <= h <= 1 and
##			0 <= x + w <= 1 and 0 <= y + h <= 1):
##			raise error, 'coordinates out of bounds'
		pw = int((self._rect[_WIDTH] - 1) * w + 0.5)
		ph = int((self._rect[_HEIGHT] - 1) * h + 0.5)
		return px, py, pw, ph

	def _qdrect(self):
		"""return our xywh-style rect in quickdraw ltrb style"""
		return self._rect[0], self._rect[1], self._rect[0]+self._rect[2], \
			self._rect[1]+self._rect[3]
			
	def _mkclip(self):
		if not self._parent:
			return
		# create region for whole window
		if self._clip:
			Qd.DisposeRgn(self._clip)
		self._clip = Qd.NewRgn()
		Qd.RectRgn(self._clip, self._qdrect())
		# subtract all subwindows
		for w in self._subwindows:
			if not w._transparent:
				r = Qd.NewRgn()
				Qd.RectRgn(r, w._qdrect())
				Qd.DiffRgn(self._clip, r, self._clip)
				Qd.DisposeRgn(r)
			w._mkclip()
		
	def _redraw(self):
		if not self._clip:
			self._mkclip()
		saveclip = Qd.NewRgn()
		Qd.GetClip(saveclip)
		Qd.SetClip(self._clip)
		Qd.RGBBackColor(self._bgcolor)
		Qd.RGBForeColor(self._fgcolor)
		Qd.EraseRect(self._rect)
		Qd.SetClip(saveclip)
		Qd.DisposeRgn(saveclip)
		print 'REDRAW', self._bgcolor
		

class _DisplayList:
	def __init__(self, window, bgcolor):
		r, g, b = bgcolor
		self._window = window
		window._displists.append(self)
		self._buttons = []

	def close(self):
		if self._window is None:
			return
		for b in self._buttons[:]:
			b.close()
		self._window._displists.remove(self)
		self._window = None

	def is_closed(self):
		return self._window is None

	def render(self):
		pass

	def fgcolor(self, color):
		r, g, b = color[0]*0x101, color[1]*0x101, color[2]*0x101

	def newbutton(self, coordinates):
		return _Button(self, coordinates)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0):
		return 0.0, 0.0, 1.0, 1.0

	def drawline(self, color, points):
		r, g, b = color[0]*0x101, color[1]*0x101, color[2]*0x101
		for x, y in points:
			pass

	def drawbox(self, coordinates):
		x, y, w, h = coordinates

	def drawfbox(self, color, coordinates):
		r, g, b = color[0]*0x101, color[1]*0x101, color[2]*0x101
		x, y, w, h = coordinates

	def usefont(self, fontobj):
		self._font = fontobj
		return self.baseline(), self.fontheight(), self.pointsize()

	def setfont(self, font, size):
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, margin = 0):
		return self.usefont(findfont(fontname, 10))

	def baseline(self):
		return self._font.baseline() * self._window._vfactor

	def fontheight(self):
		return self._font.fontheight() * self._window._vfactor

	def pointsize(self):
		return self._font.pointsize()

	def strsize(self, str):
		width, height = self._font.strsize(str)
		return float(width) * self._window._hfactor, \
		       float(height) * self._window._vfactor

	def setpos(self, x, y):
		self._curpos = x, y

	def writestr(self, str):
		x, y = self._curpos
		width, height = self.strsize(str)
		return x, y, width, height

class _Button:
	def __init__(self, dispobj, coordinates):
		x, y, w, h = coordinates
		self._dispobj = dispobj
		dispobj._buttons.append(self)

	def close(self):
		if self._dispobj is None:
			return
		self._dispobj._buttons.remove(self)
		self._dispobj = None

	def is_closed(self):
		return self._dispobj is None

	def hiwidth(self, width):
		pass

	def hicolor(self, color):
		r, g, b = color[0]*0x101, color[1]*0x101, color[2]*0x101

	def highlight(self):
		pass

	def unhighlight(self):
		pass

_pt2mm = 25.4 / 72			# 1 inch == 72 points == 25.4 mm

class findfont:
	def __init__(self, fontname, pointsize):
		self._pointsize = pointsize

	def close(self):
		pass

	def is_closed(self):
		return 0

	def strsize(self, str):
		import string
		strlist = string.splitfields(str, '\n')
		maxlen = 0
		for str in strlist:
			l = len(str)
			if l > maxlen:
				maxlen = l
		return maxlen * self._pointsize * .7 * _pt2mm, \
		       len(strlist) * self.fontheight()

	def baseline(self):
		return self._pointsize * _pt2mm

	def fontheight(self):
		return self._pointsize * 1.2 * _pt2mm

	def pointsize(self):
		return self._pointsize

fonts = [
	'Times-Roman',
	'Times-Italic',
	'Times-Bold',
	'Utopia-Bold',
	'Palatino-Bold',
	'Helvetica',
	'Helvetica-Bold',
	'Helvetica-Oblique',
	'Courier',
	'Courier-Bold',
	'Courier-Oblique',
	'Courier-Bold-Oblique',
	]

class showmessage:
	def __init__(self, text, type = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message'):
		pass

	def close(self):
		pass

class Dialog:
	def __init__(self, list, title = None, prompt = None, grab = 1,
		     vertical = 1):
		pass

	def close(self):
		pass

	def destroy_menu(self):
		pass

	def create_menu(self, list, title = None):
		pass

	def getbutton(self, button):
		return set

	def setbutton(self, button, onoff = 1):
		pass

def multchoice(prompt, list, defindex):
	return defindex

def beep():
	import sys
	sys.stderr.write('\7')
