import Win
import Qd
import Fm
import time
import Evt
import Events
import Windows
import MacOS
import string
import QuickDraw
import mac_image
import imgformat
import img
import imageop

#
# The cursors we need
#
_arrow = Qd.arrow
_watch = Qd.GetCursor(4).data

#
# The fontfaces (which are unfortunately not defined in QuickDraw.py)
_qd_bold = 1
_qd_italic = 2

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

Version = 'mac'

from EVENTS import *

# Routines to save/restore complete textfont info
def savefontinfo(wid):
	"""Return all font-pertaining info for a macos window"""
	port = wid.GetWindowPort()
	return port.txFont, port.txFace, port.txMode, port.txSize, port.spExtra
	
def restorefontinfo(wid, (font, face, mode, size, spextra)):
	"""Set all font-pertaining info for a macos window"""
	old = Qd.GetPort()
	Qd.SetPort(wid)
	Qd.TextFont(font)
	Qd.TextFace(face)
	Qd.TextMode(mode)
	Qd.TextSize(size)
	Qd.SpaceExtra(spextra)
	Qd.SetPort(old)

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
		wid, w, h = self._openwindow(x, y, w, h, title)
		rv = _Window(self, wid, 0, 0, w, h, 0, pixmap, transparent)
		self._wid_to_window[wid] = rv
		return rv

	def newcmwindow(self, x, y, w, h, title, pixmap = 0, transparent = 0):
		wid, w, h = self._openwindow(x, y, w, h, title)
		rv = _Window(self, wid, 0, 0, w, h, 1, pixmap, transparent)
		self._wid_to_window[wid] = rv
		return rv
		
	def _openwindow(self, x, y, w, h, title):
		"""Internal - Open window given xywh, title. Returns window-id"""
		x = int(x*_x_pixel_per_mm)
		y = int(y*_y_pixel_per_mm)
		w = int(w*_x_pixel_per_mm)
		h = int(h*_y_pixel_per_mm)
##		print 'TOPLEVEL WINDOW', x, y, w, h, title
		rBounds = (x-_window_left_offset, y-_window_top_offset, 
				x+w+_window_right_offset, y+h+_window_bottom_offset)
##		print 'macos bounds', rBounds
		wid = Win.NewCWindow(rBounds, title, 1, 0, -1, 1, 0 )
		return wid, w, h
		
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
		
class _CommonWindow:
	"""Code common to toplevel window and subwindow"""
		
	def __init__(self, parent, wid):
		parent._subwindows.insert(0, self)
		self._parent = parent
		self._wid = wid
		self._subwindows = []
		self._displists = []
		self._bgcolor = parent._bgcolor
		self._fgcolor = parent._fgcolor
		self._clip = None
		self._active_displist = None

	def close(self):
		"""Close window and all subwindows"""
		if self._parent is None:
			return		# already closed
		self._parent._subwindows.remove(self)
		self._parent._close_wid(self._wid)
		self._wid = None
		self._parent = None
		for win in self._subwindows[:]:
			win.close()
		for dl in self._displists[:]:
			dl.close()
			
	def _close_wid(self, wid):
		"""Called by children to close wid. Only implements real close
		at TopLevel"""
		pass

	def _clipchanged(self):
		"""Called when the clipping region is possibly changed"""
		if not self._parent or not self._wid or not self._clip:
			return
##		print '_clipchanged', self
		Qd.DisposeRgn(self._clip)
		self._clip = None
		# XXXX Needed?
		for ch in self._subwindows:
			ch._clipchanged()
			
	def is_closed(self):
		"""Return true if window is closed"""
		return self._parent is None

	def newwindow(self, (x, y, w, h), pixmap = 0, transparent = 0):
		"""Create a new subwindow"""
##		print 'SUB WINDOW', x, y, w, h
		rv = _SubWindow(self, self._wid, (x, y, w, h), 0, pixmap, transparent)
		self._clipchanged()
		return rv

	def necmwwindow(self, (x, y, w, h), pixmap = 0, transparent = 0):
		"""Create a new subwindow"""
##		print 'SUB CM WINDOW', x, y, w, h
		rv = _SubWindow(self, self._wid, (x, y, w, h), 1, pixmap, transparent)
		self._clipchanged()
		return rv

	def fgcolor(self, color):
		"""Set foregroundcolor to 3-tuple 0..255"""
		self._fgcolor = self._convert_color(color)

	def bgcolor(self, color):
		"""Set backgroundcolor to 3-tuple 0..255"""
		self._bgcolor = self._convert_color(color)

	def setcursor(self, cursor):
		raise 'window.setcursor called'
		for win in self._subwindows:
			win.setcursor(cursor)

	def newdisplaylist(self, *bgcolor):
		"""Return new, empty display list optionally specifying bgcolor"""
		if bgcolor != ():
			bgcolor = self._convert_color(bgcolor[0])
		else:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)

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
		"""Backward compatability: return wh of image given filename"""
		if _size_cache.has_key(file):
			return _size_cache[file]
		try:
			reader = img.reader(None, file)
		except img.error, arg:
			raise error, arg
		width = reader.width
		height = reader.height
		_size_cache[file] = width, height
		return width, height

	def _prepare_image(self, file, crop, scale):
		# width, height: width and height of window
		# xsize, ysize: width and height of unscaled (original) image
		# w, h: width and height of scaled (final) image
		# depth: depth of window (and image) in bytes
		oscale = scale
		format = imgformat.macrgb16
		depth = format.descr['size'] / 8

		try:
			reader = img.reader(format, file)
		except img.error, arg:
			raise error, arg
		xsize = reader.width
		ysize = reader.height
		_size_cache[file] = xsize, ysize
			
		top, bottom, left, right = crop
		top = int(top * ysize + 0.5)
		bottom = int(bottom * ysize + 0.5)
		left = int(left * xsize + 0.5)
		right = int(right * xsize + 0.5)
		x, y, width, height = self._rect
		
		if scale == 0:
			scale = min(float(width)/(xsize - left - right),
				    float(height)/(ysize - top - bottom))
				    
		top = int(top * scale + .5)
		bottom = int(bottom * scale + .5)
		left = int(left * scale + .5)
		right = int(right * scale + .5)

		if 0 and hasattr(reader, 'transparent'):	# XXXX To be done
			r = img.reader(imgformat.xrgb8, file)
			for i in range(len(r.colormap)):
				r.colormap[i] = 255, 255, 255
			r.colormap[r.transparent] = 0, 0, 0
			image = r.read()
			if scale != 1:
				w = int(xsize * scale + .5)
				h = int(ysize * scale + .5)
				image = imageop.scale(image, 1,
						xsize, ysize, w, h)
			bitmap = ''
			for i in range(h):
				# grey2mono doesn't pad lines :-(
				bitmap = bitmap + imageop.grey2mono(
					image[i*w:(i+1)*w], w, 1, 128)
			mask = tw._visual.CreateImage(1, X.XYPixmap, 0,
						bitmap, w, h, 8, 0)
		else:
			mask = None
		try:
			image = reader.read()
		except:
			raise error, 'unspecified error reading image'
		if scale != 1:
			w = int(xsize * scale + .5)
			h = int(ysize * scale + .5)
			image = imageop.scale(image, depth,
					      xsize, ysize, w, h)

		x, y = x + (width - (w - left - right)) / 2, \
		       y + (height - (h - top - bottom)) / 2
		xim = mac_image.mkpixmap(w, h, format, image)
		return xim, mask, left, top, x, y, w - left - right, h - top - bottom

	def _convert_coordinates(self, coordinates):
		"""Convert fractional xywh in our space to pixel-xywh
		in toplevel-window relative pixels"""
		
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
		
	def _convert_color(self, (r, g, b)):
		"""Convert 8-bit r,g,b tuple to 16-bit r,g,b tuple"""
		return r*0x101, g*0x101, b*0x101


	def _qdrect(self):
		"""return our xywh rect (in pixels) as quickdraw ltrb style"""
		return self._rect[0], self._rect[1], self._rect[0]+self._rect[2], \
			self._rect[1]+self._rect[3]
		
	def _redraw(self):
		"""Set clipping and color, redraw, redraw children"""
		if not self._clip:
			self._mkclip()
		saveclip = Qd.NewRgn()
		Qd.GetClip(saveclip)
		Qd.SetClip(self._clip)
		Qd.RGBBackColor(self._bgcolor)
		Qd.RGBForeColor(self._fgcolor)
		self._do_redraw()
		Qd.SetClip(saveclip)
		Qd.DisposeRgn(saveclip)
		for child in self._subwindows:
					child._redraw()
					
	def _do_redraw(self):
		"""Do actual redraw"""
##		Qd.EraseRect(self._qdrect())
		if self._active_displist:
			self._active_displist._render()
		else:
			Qd.EraseRect(self._qdrect())
			print 'Erased', self._qdrect(),'to', self._wid.GetWindowPort().rgbBkColor
			
	def _testclip(self, color):
		"""Test clipping region"""
		Qd.SetPort(self._wid)
		if not self._clip:
			self._mkclip()
		saveclip = Qd.NewRgn()
		Qd.GetClip(saveclip)
		Qd.SetClip(self._clip)
		Qd.RGBBackColor(color)
		Qd.RGBForeColor(self._fgcolor)
		Qd.EraseRect(self._qdrect())
		Qd.SetClip(saveclip)
		Qd.DisposeRgn(saveclip)

class _Window(_CommonWindow):
	"""Toplevel window"""
	
	def __init__(self, parent, wid, x, y, w, h, defcmap = 0, pixmap = 0, 
			transparent = 0):
		
		_CommonWindow.__init__(self, parent, wid)
		
		if transparent:
			raise 'Error: transparent toplevel window'
		self._transparent = 0
		
		# Note: the toplevel init routine is called with pixel coordinates,
		# not fractional coordinates
		self._rect = 0, 0, w, h
		
		self._hfactor = parent._hfactor / (float(w) / _x_pixel_per_mm)
		self._vfactor = parent._vfactor / (float(h) / _y_pixel_per_mm)
		
	def settitle(self, title):
		"""Set window title"""
		if not self._wid:
			return  # Or raise error?
		self._Wid.SetWTitle(title)

	def pop(self):
		"""Pop window to top of window stack"""
		if not self._wid or not self._parent:
			return
		self._wid.SelectWindow()

	def push(self):
		"""Push window to bottom of window stack"""
		if not self._wid or not self._parent:
			return
		self._wid.SendBehind(0)

	def _mkclip(self):
		if not self._wid or not self._parent:
			return
##		print '_mkclip', self
		# create region for whole window
		if self._clip:
##			print '*** Already had one!'
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

class _SubWindow(_Window):
	"""Window "living in" with a toplevel window"""

	def __init__(self, parent, wid, coordinates, defcmap = 0, pixmap = 0, 
			transparent = 0):
		
		_CommonWindow.__init__(self, parent, wid)
		
		x, y, w, h = parent._convert_coordinates(coordinates)
		self._rect = x, y, w, h
##		print 'subwin:', self._rect
		if w <= 0 or h <= 0:
			raise 'Empty subwindow', coordinates
		self._sizes = coordinates
		
		self._hfactor = parent._hfactor / self._sizes[_WIDTH]
		self._vfactor = parent._vfactor / self._sizes[_HEIGHT]
		
		if parent._transparent:
			self._transparent = parent._transparent
		else:
			self._transparent = transparent
			
		# XXXX pixmap to-be-done
		
		# XXXX Should we do redraw of parent or something??

	def settitle(self, title):
		"""Set window title"""
		raise error, 'can only settitle at top-level'

	def pop(self):
		"""Pop to top of subwindow stack"""
		if not self._parent:
			return
		if self._parent._subwindows[0] == self:
			return
		self._parent._subwindows.remove(self)
		self._parent._subwindows.insert(0, self)
		self._parent._clipchanged()
		# XXXX Pixmap?
##		self._parent._redraw() # XXXX Too aggressive...

	def push(self):
		"""Push to bottom of subwindow stack"""
		if not self._parent:
			return
		if self._parent._subwindows[-1] == self:
			return
		self._parent._subwindows.remove(self)
		self._parent._subwindows.append(self)
		self._parent._clipchanged()
		# XXXX Pixmap?
##		self._parent._redraw() # XXXX Too aggressive...

	def _mkclip(self):
		if not self._parent:
			return
##		print '_mkclip', self
		# create region for our subwindow
		if self._clip:
##			print '*** Already had one!'
			Qd.DisposeRgn(self._clip)
		self._clip = Qd.NewRgn()
		Qd.RectRgn(self._clip, self._qdrect())
		# subtract all our subsubwindows
		for w in self._subwindows:
			if not w._transparent:
				r = Qd.NewRgn()
				Qd.RectRgn(r, w._qdrect())
				Qd.DiffRgn(self._clip, r, self._clip)
				Qd.DisposeRgn(r)
			w._mkclip() # XXXX Needed??
		# subtract our higher-stacked siblings
		for w in self._parent._subwindows:
			if w == self:
				# Stop when we meet ourselves
				break
			if not w._transparent:
				r = Qd.NewRgn()
				Qd.RectRgn(r, w._qdrect())
				Qd.DiffRgn(self._clip, r, self._clip)
				Qd.DisposeRgn(r)

class _DisplayList:
	def __init__(self, window, bgcolor):
		self._window = window
		window._displists.append(self)
		self._bgcolor = bgcolor
		self._fgcolor = window._fgcolor
		self._linewidth = 1
		self._buttons = []
		self._list = []
		self._rendered = 0
		if not self._window._transparent:
			self._list.append(('clear',))
		self._font = None

	def close(self):
		if self._window is None:
			return
		for b in self._buttons[:]:
			b.close()
		self._window._displists.remove(self)
		if self._window._active_displist == self:
			self._window._active_displist = None
		self._window = None
		del self._buttons
		del self._list

	def is_closed(self):
		return self._window is None

	def render(self):
		self._rendered = 1
		# XXXX buttons?
		self._render()
		# XXXX render transparent sub/sibling windows?
		
	def _render(self):
		self._window._active_displist = self
		Qd.RGBBackColor(self._bgcolor)
		Qd.RGBForeColor(self._fgcolor)
		for i in self._list:
			self._render_one(i)
			
	def _render_one(self, entry):
		cmd = entry[0]
		window = self._window
		wid = window._wid
		
		print 'RENDER', cmd, entry[1:]
		if cmd == 'clear':
			Qd.EraseRect(window._qdrect())
			print 'Erased', window._qdrect(),'to', wid.GetWindowPort().rgbBkColor
		elif cmd == 'text':
			Qd.MoveTo(entry[1], entry[2])
			Qd.DrawString(entry[3]) # XXXX Incorrect for long strings
		elif cmd == 'font':
			entry[1]._setfont(wid)
		elif cmd == 'image':
			mask, image, srcx, srcy, dstx, dsty, w, h = entry[1:]
			if mask:
				raise 'kaboo kaboo'
			srcrect = srcx, srcy, srcx+w, srcy+h
			dstrect = dstx, dsty, dstx+w, dsty+h
			Qd.CopyBits(image, wid.GetWindowPort().portBits, srcrect, dstrect,
				QuickDraw.srcCopy, None)
			
	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('fg', self._window._convert_color(color))
		self._fgcolor = color


	def newbutton(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return _Button(self, coordinates)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       w._prepare_image(file, crop, scale)
		if mask:
			self._imagemask = mask, src_x, src_y, dest_x, dest_y, width, height
		else:
##			raise 'kaboo kaboo'
##			r = Xlib.CreateRegion()
##			r.UnionRectWithRegion(dest_x, dest_y, width, height)
##			self._imagemask = r
			pass
		self._list.append('image', mask, image, src_x, src_y,
				  dest_x, dest_y, width, height)
		x, y, w, h = w._rect
		return float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append('line', color, p)

	def drawbox(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('box',
				self._window._convert_coordinates(coordinates))
##		self._optimize()

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append('fbox', self._window._convert_color(color),
				self._window._convert_coordinates(coordinates))
##		self._optimize(1)

	def usefont(self, fontobj):
		self._font = fontobj
		self._font._initparams(self._window._wid)
		self._list.append('font', fontobj)
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
		width, height = self._font.strsize(self._window._wid, str)
##		print 'RELATIVE', float(width) * self._window._hfactor, \
##		       float(height) * self._window._vfactor
		return float(width) * self._window._hfactor, \
		       float(height) * self._window._vfactor

	def setpos(self, x, y):
		self._curpos = x, y
		self._xpos = x

	def writestr(self, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
##		f = self._font._font
		base = self.baseline()
		height = self.fontheight()
		strlist = string.splitfields(str, '\n')
		oldx, oldy = x, y = self._curpos
		if len(strlist) > 1 and oldx > self._xpos:
			oldx = self._xpos
		oldy = oldy - base
		maxx = oldx
		for str in strlist:
			x0, y0 = w._convert_coordinates((x, y))
			list.append('text', x0, y0, str)
##			self._curpos = x + float(f.TextWidth(str)) / w._rect[_WIDTH], y
			# XXXX Must have correct font set...
			self._curpos = x + float(Qd.TextWidth(str, 0, len(str))) / w._rect[_WIDTH], y
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, newy - oldy + height - base

class _Button:
	def __init__(self, dispobj, coordinates):
		x, y, w, h = coordinates
		self._dispobj = dispobj
		dispobj._buttons.append(self)
		self._hicolor = self._color = dispobj._fgcolor

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
		self._hicolor = color

	def highlight(self):
		pass

	def unhighlight(self):
		pass

_pt2mm = 25.4 / 72			# 1 inch == 72 points == 25.4 mm

_fontmap = {
	  'Times-Roman': ('Times', 0),
	  'Times-Italic': ('Times', _qd_italic),
	  'Times-Bold': ('Times', _qd_bold),
	  'Utopia-Bold': ('New York', _qd_bold),
	  'Palatino-Bold': ('Palatino', _qd_bold),
	  'Helvetica': ('Helvetica', 0),
	  'Helvetica-Bold': ('Helvetica', _qd_bold),
	  'Helvetica-Oblique': ('Helvetica', _qd_italic),
	  'Courier': ('Courier', 0),
	  'Courier-Bold': ('Courier', _qd_bold),
	  'Courier-Oblique': ('Courier', _qd_italic),
	  'Courier-Bold-Oblique': ('Courier', _qd_italic+_qd_bold)
	  }
	  
fonts = _fontmap.keys()

class findfont:
	def __init__(self, fontname, pointsize):
		if not _fontmap.has_key(fontname):
			raise error, 'Font not found: '+fontname
		self._fontnum = Fm.GetFNum(_fontmap[fontname][0])
		self._fontface = _fontmap[fontname][1]
		self._pointsize = pointsize
		self._inited = 0
		
	def _setfont(self, wid):
		"""Set our font, saving the old one for later"""
		self._old_fontinfo = savefontinfo(wid) # Save current font info
		Qd.TextFont(self._fontnum)
		Qd.TextFace(self._fontface)
		Qd.TextSize(self._pointsize)
		
	def _restorefont(self, wid):
		"""Restore the previous font"""
		restorefontinfo(wid, self._old_fontinfo)
		
	def _initparams(self, wid):
		"""Obtain font params like ascent/descent, if needed"""
		if self._inited:
			return
		self._inited = 1
		cur_fontinfo = savefontinfo(wid) # Save current font info
		self._setfont(wid)
		self.ascent, self.descent, widMax, self.leading = Qd.GetFontInfo()
		self._restorefont(wid)
		restorefontinfo(wid, cur_fontinfo)
##		print 'FONTPARS', self.ascent, self.descent, self.leading

	def close(self):
		pass

	def is_closed(self):
		return 0

	def strsize(self, wid, str):
		strlist = string.splitfields(str, '\n')
		maxwidth = 0
		maxheight = len(strlist) * (self.ascent + self.descent + self.leading)
		self._setfont(wid)
		for str in strlist:
			width = Qd.TextWidth(str, 0, len(str))
			if width > maxwidth:
				maxwidth = width
		self._restorefont(wid)
##		print 'WIDTH OF', strlist, 'IS', maxwidth, maxheight
		return float(maxwidth) / _x_pixel_per_mm, \
		       float(maxheight) / _y_pixel_per_mm

	def baseline(self):
		return float(self.ascent+self.leading) / _y_pixel_per_mm

	def fontheight(self):
		return float(self.ascent + self.descent + self.leading) \
			/ _y_pixel_per_mm

	def pointsize(self):
		return self._pointsize

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
