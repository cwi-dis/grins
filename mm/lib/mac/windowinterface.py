__version__ = "$Id$"

import mac_windowbase
from mac_windowbase import TRUE, FALSE, SINGLE, UNIT_MM
import WMEVENTS
import UserCmd

from types import *
import math
import struct
import string
import macfs
import MacOS
import os
import Res
import List
MacList=List
import Win
import Dlg
import Dialogs
[_X, _Y, _WIDTH, _HEIGHT] = range(4)
_def_useGadget = 1


# Resource IDs
ID_ABOUT_DIALOG=512
ID_SELECT_DIALOG=516
ITEM_SELECT_OK=1
ITEM_SELECT_CANCEL=2
ITEM_SELECT_LISTPROMPT=3
ITEM_SELECT_ITEMLIST=4
ITEM_SELECT_SELECTPROMPT=5
ITEM_SELECT_ITEM=6

# For askstring re-use Pythons standard EasyDialogs resource
ID_INPUT_DIALOG=257
ITEM_INPUT_OK=1
ITEM_INPUT_CANCEL=2
ITEM_INPUT_PROMPT=3
ITEM_INPUT_TEXT=4

# For messages and questions:
ID_MESSAGE_DIALOG=521
ID_QUESTION_DIALOG=522
ITEM_QUESTION_OK=1
ITEM_QUESTION_TEXT=2
ITEM_QUESTION_CANCEL=3

# XXXX Debugging code: assure the resource file is available
try:
	Res.GetResource('DLOG', ID_ABOUT_DIALOG)
except:
	Res.OpenResFile('::mac:maccmifed.rsrc')
Res.GetResource('DLOG', ID_ABOUT_DIALOG)

_rb_message = """\
Use left mouse button to draw a box.
Click `OK' when ready or `Cancel' to cancel."""
_rb_done = '_rb_done'			# exception to stop create_box loop
_in_create_box = None

# size of arrow head
ARR_LENGTH = 18
ARR_HALFWIDTH = 5
ARR_SLANT = float(ARR_HALFWIDTH) / float(ARR_LENGTH)

class _Toplevel(mac_windowbase._Toplevel):
	
	def __init__(self,closing=0):
		mac_windowbase._Toplevel.__init__(self, closing)
		Dlg.SetUserItemHandler(None)
		if not closing:
			self._dialog_user_item_handler = Dlg.SetUserItemHandler(self._do_user_item)
		
	# We are overriding these only so we get the correct _Window (ours)
	
	def newwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE,
				pixmap = 0, transparent = 0, units=UNIT_MM, menubar=[], canvassize=None):
		wid, w, h = self._openwindow(x, y, w, h, title, units)
		rv = _Window(self, wid, 0, 0, w, h, 0, pixmap, transparent, title, menubar, canvassize)
		self._register_wid(wid, rv)
		return rv

	def newcmwindow(self, x, y, w, h, title, visible_channel = TRUE, type_channel = SINGLE,
				pixmap = 0, transparent = 0, units=UNIT_MM, menubar=[], canvassize=None):
		wid, w, h = self._openwindow(x, y, w, h, title, units)
		rv = _Window(self, wid, 0, 0, w, h, 1, pixmap, transparent, title, menubar, canvassize)
		self._register_wid(wid, rv)
		return rv
		
	def getsize(self):
		return toplevel._mscreenwidth, toplevel._mscreenheight
		
	# And we override a bit of eventhandling because we use dialogs
	def _handle_event(self, event):
		if Dlg.IsDialogEvent(event):
			if self._do_dialogevent(event):
				return
		mac_windowbase._Toplevel._handle_event(self, event)

	def _do_user_item(self, wid, item):
		try:
			win = self._wid_to_window[wid]
		except KeyError:
			print "Unknown dialog for user item redraw", wid, item
		else:
			try:
				redrawfunc = win.do_itemdraw
			except AttributeError:
				print "Dialog for user item redraw has no do_itemdraw()", win, item
			else:
				redrawfunc(item)
		
	def _do_dialogevent(self, event):
		what = event[0]
		if what == Events.keyDown:
			what, message, when, where, modifiers = event
			if modifiers & Events.cmdKey:
				return 0	# Let menu code handle it
			c = chr(message & Events.charCodeMask)
			pass # Do command-key processing
			# Do default key processing
			if c == '\r':
				wid = Win.FrontWindow()
				try:
					window = self._wid_to_window[wid]
				except KeyError:
					pass
				else:
					try:
						defaultcb = window._do_defaulthit
					except AttributeError:
						pass
					else:
						defaultcb()
						return 1
		gotone, wid, item = Dlg.DialogSelect(event)
		if gotone:
			if self._wid_to_window.has_key(wid):
				self._wid_to_window[wid].do_itemhit(item, event)
			else:
				print 'Dialog event for unknown dialog'
			return 1
		return 0		
		
class _CommonWindowMixin:
	# Again, only overriding to get the class of the objects (window, displaylist) correct.

	def newwindow(self, (x, y, w, h), pixmap = 0, transparent = 0, z=0, type_channel = SINGLE):
		"""Create a new subwindow"""
		rv = _SubWindow(self, self._wid, (x, y, w, h), 0, pixmap, transparent, z)
		self._clipchanged()
		return rv

	def newcmwindow(self, (x, y, w, h), pixmap = 0, transparent = 0, z=0, type_channel = SINGLE):
		"""Create a new subwindow"""
		rv = _SubWindow(self, self._wid, (x, y, w, h), 1, pixmap, transparent, z)
		self._clipchanged()
		return rv

	def newdisplaylist(self, *bgcolor):
		"""Return new, empty display list optionally specifying bgcolor"""
		if bgcolor != ():
			bgcolor = self._convert_color(bgcolor[0])
		else:
			bgcolor = self._bgcolor
		return _DisplayList(self, bgcolor)
		
class _CommonWindow(_CommonWindowMixin, mac_windowbase._CommonWindow):
	pass

class _Window(_CommonWindowMixin, mac_windowbase._Window):

	def __init__(self, parent, wid, x, y, w, h, defcmap = 0, pixmap = 0, transparent=0,
		     title=None, commands=[], canvassize=None):
		mac_windowbase._Window.__init__(self, parent, wid, x, y, w, h, 
					      defcmap, pixmap, transparent, title, commands, canvassize)
		self.arrowcache = {}
		self._next_create_box = []

	def close(self):
		self.arrowcache = {}
		mac_windowbase._Window.close(self)

	def create_box(self, msg, callback, box = None):
		showmessage("Channel coordinates unknown, set to full base window.\nChange in channel view")
		if box == None:
			box = (0, 0, 1, 1)
		apply(callback, box)
##		global _in_create_box
##		if _in_create_box:
##			_in_create_box._next_create_box.append((self, msg, callback, box))
##			return
##		if self.is_closed():
##			apply(callback, ())
##			return
##		_in_create_box = self
##		self.pop()
##		if msg:
##			msg = msg + '\n\n' + _rb_message
##		else:
##			msg = _rb_message
##		self._rb_dl = self._active_displist
##		if self._rb_dl:
##			d = self._rb_dl.clone()
##		else:
##			d = self.newdisplaylist()
##		self._rb_transparent = []
##		sw = self._subwindows[:]
##		sw.reverse()
##		r = Xlib.CreateRegion()
##		for win in sw:
##			if not win._transparent:
##				# should do this recursively...
##				self._rb_transparent.append(win)
##				win._transparent = 1
##				d.drawfbox(win._bgcolor, win._sizes)
##				apply(r.UnionRectWithRegion, win._rect) # XXXX
##		for win in sw:
##			b = win._sizes
##			if b != (0, 0, 1, 1):
##				d.drawbox(b)
##		self._rb_display = d.clone()
##		d.fgcolor((255, 0, 0))
##		if box:
##			d.drawbox(box)
##		if self._rb_transparent:
##			self._mkclip()
##			self._do_expose(r)
##			self._rb_reg = r
##		d.render()
##		self._rb_curdisp = d
##		self._rb_dialog = showmessage(
##			msg, mtype = 'message', grab = 0,
##			callback = (self._rb_done, ()),
##			cancelCallback = (self._rb_cancel, ()))
##		self._rb_callback = callback
##		raise 'not implemented'
##		form = self._form
##		form.AddEventHandler(X.ButtonPressMask, FALSE,
##				     self._start_rb, None)
##		form.AddEventHandler(X.ButtonMotionMask, FALSE,
##				     self._do_rb, None)
##		form.AddEventHandler(X.ButtonReleaseMask, FALSE,
##				     self._end_rb, None)
##		cursor = form.Display().CreateFontCursor(Xcursorfont.crosshair)
##		form.GrabButton(X.AnyButton, X.AnyModifier, TRUE,
##				X.ButtonPressMask | X.ButtonMotionMask
##					| X.ButtonReleaseMask,
##				X.GrabModeAsync, X.GrabModeAsync, form, cursor)
##		v = form.GetValues(['foreground', 'background'])
##		v['foreground'] = v['foreground'] ^ v['background']
##		v['function'] = X.GXxor
##		v['line_style'] = X.LineOnOffDash
##		self._gc_rb = form.GetGC(v)
##		self._rb_box = box
##		if box:
##			x, y, w, h = self._convert_coordinates(box)
##			if w < 0:
##				x, w = x + w, -w
##			if h < 0:
##				y, h = y + h, -h
##			self._rb_box = x, y, w, h
##			self._rb_start_x = x
##			self._rb_start_y = y
##			self._rb_width = w
##			self._rb_height = h
##		else:
##			self._rb_start_x, self._rb_start_y, self._rb_width, \
##					  self._rb_height = self._rect
##		try:
##			Xt.MainLoop()
##		except _rb_done:
##			pass

	def hitarrow(self, point, src, dst):
		# return 1 iff (x,y) is within the arrow head
		sx, sy = self._convert_coordinates(src)
		dx, dy = self._convert_coordinates(dst)
		x, y = self._convert_coordinates(point)
		lx = dx - sx
		ly = dy - sy
		if lx == ly == 0:
			angle = 0.0
		else:
			angle = math.atan2(lx, ly)
		cos = math.cos(angle)
		sin = math.sin(angle)
		# translate
		x, y = x - dx, y - dy
		# rotate
		nx = x * cos - y * sin
		ny = x * sin + y * cos
		# test
		if ny > 0 or ny < -ARR_LENGTH:
			return FALSE
		if nx > -ARR_SLANT * ny or nx < ARR_SLANT * ny:
			return FALSE
		return TRUE

##	# have to override these for create_box
##	def _input_callback(self, form, client_data, call_data):
##		if _in_create_box:
##			return
##		mac_windowbase._Window._input_callback(self, form, client_data,
##						     call_data)

	def _resize_callback(self, width, height):
		self.arrowcache = {}
		w = _in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			try:
				w._rb_cancel()
			except _rb_done:
				pass
			w._next_create_box[0:0] = next_create_box
		mac_windowbase._Window._resize_callback(self, width, height)
		if w:
			w._rb_end()
			raise _rb_done

	def _delete_callback(self, form, client_data, call_data):
		self.arrowcache = {}
		w = _in_create_box
		if w:
			next_create_box = w._next_create_box
			w._next_create_box = []
			try:
				w._rb_cancel()
			except _rb_done:
				pass
			w._next_create_box[0:0] = next_create_box
		mac_windowbase._Window._delete_callback(self, form, client_data,
						      call_data)
		if w:
			w._rb_end()
			raise _rb_done

	# supporting methods for create_box
	def _rb_finish(self):
		global _in_create_box
		_in_create_box = None
		if self._rb_transparent:
			for win in self._rb_transparent:
				win._transparent = 0
			self._mkclip()
			self._do_expose(self._rb_reg)
			del self._rb_reg
		del self._rb_transparent
		raise 'not yet implemented'
##		form = self._form
##		form.RemoveEventHandler(X.ButtonPressMask, FALSE,
##					self._start_rb, None)
##		form.RemoveEventHandler(X.ButtonMotionMask, FALSE,
##					self._do_rb, None)
##		form.RemoveEventHandler(X.ButtonReleaseMask, FALSE,
##					self._end_rb, None)
##		form.UngrabButton(X.AnyButton, X.AnyModifier)
		self._rb_dialog.close()
		if self._rb_dl and not self._rb_dl.is_closed():
			self._rb_dl.render()
		self._rb_display.close()
		self._rb_curdisp.close()
		del self._rb_callback
		del self._rb_dialog
		del self._rb_dl
		del self._rb_display
		del self._gc_rb

	def _rb_cvbox(self):
		x0 = self._rb_start_x
		y0 = self._rb_start_y
		x1 = x0 + self._rb_width
		y1 = y0 + self._rb_height
		if x1 < x0:
			x0, x1 = x1, x0
		if y1 < y0:
			y0, y1 = y1, y0
		x, y, width, height = self._rect
		if x0 < x: x0 = x
		if x0 >= x + width: x0 = x + width - 1
		if x1 < x: x1 = x
		if x1 >= x + width: x1 = x + width - 1
		if y0 < y: y0 = y
		if y0 >= y + height: y0 = y + height - 1
		if y1 < y: y1 = y
		if y1 >= y + height: y1 = y + height - 1
		return float(x0 - x) / (width - 1), \
		       float(y0 - y) / (height - 1), \
		       float(x1 - x0) / (width - 1), \
		       float(y1 - y0) / (height - 1)

	def _rb_done(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, self._rb_cvbox())
		self._rb_end()
		raise _rb_done

	def _rb_cancel(self):
		callback = self._rb_callback
		self._rb_finish()
		apply(callback, ())
		self._rb_end()
		raise _rb_done

	def _rb_end(self):
		# execute pending create_box calls
		next_create_box = self._next_create_box
		self._next_create_box = []
		for win, msg, cb, box in next_create_box:
			win.create_box(msg, cb, box)

	def _rb_draw(self):
		x = self._rb_start_x
		y = self._rb_start_y
		w = self._rb_width
		h = self._rb_height
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		raise 'not yet implemented'
##		self._gc_rb.DrawRectangle(x, y, w, h)

	def _rb_constrain(self, event):
		x, y, w, h = self._rect
		if event.x < x:
			event.x = x
		if event.x >= x + w:
			event.x = x + w - 1
		if event.y < y:
			event.y = y
		if event.y >= y + h:
			event.y = y + h - 1

	def _rb_common(self, event):
		if not hasattr(self, '_rb_cx'):
			self._start_rb(None, None, event)
		self._rb_draw()
		self._rb_constrain(event)
		if self._rb_cx and self._rb_cy:
			x, y, w, h = self._rect
			dx = event.x - self._rb_last_x
			dy = event.y - self._rb_last_y
			self._rb_last_x = event.x
			self._rb_last_y = event.y
			self._rb_start_x = self._rb_start_x + dx
			if self._rb_start_x + self._rb_width > x + w:
				self._rb_start_x = x + w - self._rb_width
			if self._rb_start_x < x:
				self._rb_start_x = x
			self._rb_start_y = self._rb_start_y + dy
			if self._rb_start_y + self._rb_height > y + h:
				self._rb_start_y = y + h - self._rb_height
			if self._rb_start_y < y:
				self._rb_start_y = y
		else:
			if not self._rb_cx:
				self._rb_width = event.x - self._rb_start_x
			if not self._rb_cy:
				self._rb_height = event.y - self._rb_start_y
		self._rb_box = 1

	def _start_rb(self, w, data, event):
		# called on mouse press
		self._rb_display.render()
		self._rb_curdisp.close()
		self._rb_constrain(event)
		if self._rb_box:
			x = self._rb_start_x
			y = self._rb_start_y
			w = self._rb_width
			h = self._rb_height
			if w < 0:
				x, w = x + w, -w
			if h < 0:
				y, h = y + h, -h
			if x + w/4 < event.x < x + w*3/4:
				self._rb_cx = 1
			else:
				self._rb_cx = 0
				if event.x >= x + w*3/4:
					x, w = x + w, -w
			if y + h/4 < event.y < y + h*3/4:
				self._rb_cy = 1
			else:
				self._rb_cy = 0
				if event.y >= y + h*3/4:
					y, h = y + h, -h
			if self._rb_cx and self._rb_cy:
				self._rb_last_x = event.x
				self._rb_last_y = event.y
				self._rb_start_x = x
				self._rb_start_y = y
				self._rb_width = w
				self._rb_height = h
			else:
				if not self._rb_cx:
					self._rb_start_x = x + w
					self._rb_width = event.x - self._rb_start_x
				if not self._rb_cy:
					self._rb_start_y = y + h
					self._rb_height = event.y - self._rb_start_y
		else:
			self._rb_start_x = event.x
			self._rb_start_y = event.y
			self._rb_width = self._rb_height = 0
			self._rb_cx = self._rb_cy = 0
		self._rb_draw()

	def _do_rb(self, w, data, event):
		# called on mouse drag
		self._rb_common(event)
		self._rb_draw()

	def _end_rb(self, w, data, event):
		# called on mouse release
		self._rb_common(event)
		self._rb_curdisp = self._rb_display.clone()
		self._rb_curdisp.fgcolor((255, 0, 0))
		self._rb_curdisp.drawbox(self._rb_cvbox())
		self._rb_curdisp.render()
		del self._rb_cx
		del self._rb_cy

class _SubWindow(_CommonWindowMixin, mac_windowbase._SubWindow):
	def __init__(self, parent, wid, coordinates, defcmap, pixmap, transparent, z):
		mac_windowbase._SubWindow.__init__(self, parent, wid, coordinates,
						     defcmap, pixmap, transparent, z)
		self.arrowcache = {}
		self._next_create_box = []

class _DisplayList(mac_windowbase._DisplayList):
	def _render_one(self, entry):
		cmd = entry[0]
		w = self._window
		wid = w._wid
##		gc = w._gc
		if cmd == 'fpolygon':
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(entry[1])
			polyhandle = self._polyhandle(entry[2])
			Qd.PaintPoly(polyhandle)
			Qd.RGBForeColor(fgcolor)
		elif cmd == '3dbox':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]
			r, b = l + w, t + h
			l = l+1
			t = t+1
			r = r-1
			b = b-1
			l1 = l - 1
			t1 = t - 1
			r1 = r
			b1 = b
			ll = l + 2
			tt = t + 2
			rr = r - 2
			bb = b - 3

			fgcolor = wid.GetWindowPort().rgbFgColor

			Qd.RGBForeColor(cl)
			polyhandle = self._polyhandle([(l1, t1), (ll, tt), (ll, bb), (l1, b1)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(ct)
			polyhandle = self._polyhandle([(l1, t1), (r1, t1), (rr, tt), (ll, tt)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(cr)
			polyhandle = self._polyhandle([(r1, t1), (r1, b1), (rr, bb), (rr, tt)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(cb)
			polyhandle = self._polyhandle([(l1, b1), (ll, bb), (rr, bb), (r1, b1)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(fgcolor)
			
##			fg = gc.foreground
##			gc.foreground = cl
##			gc.FillPolygon([(l1, t1), (ll, tt), (ll, bb), (l1, b1)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = ct
##			gc.FillPolygon([(l1, t1), (r1, t1), (rr, tt), (ll, tt)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = cr
##			gc.FillPolygon([(r1, t1), (r1, b1), (rr, bb), (rr, tt)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = cb
##			gc.FillPolygon([(l1, b1), (ll, bb), (rr, bb), (r1, b1)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = fg
		elif cmd == 'diamond':
			x, y, w, h = entry[1]
			Qd.MoveTo(x, y + h/2)
			Qd.LineTo(x + w/2, y)
			Qd.LineTo(x + w, y + h/2)
			Qd.LineTo(x + w/2, y + h)
			Qd.LineTo(x, y + h/2)
		elif cmd == 'fdiamond':
			x, y, w, h = entry[2]
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(entry[1])
			polyhandle = self._polyhandle([(x, y + h/2),
					(x + w/2, y),
					(x + w, y + h/2),
					(x + w/2, y + h),
					(x, y + h/2)])
			Qd.PaintPoly(polyhandle)
			Qd.RGBForeColor(fgcolor)
			
##			fg = gc.foreground
##			gc.foreground = entry[1]
##			x, y, w, h = entry[2]
##			gc.FillPolygon([(x, y + h/2),
##					(x + w/2, y),
##					(x + w, y + h/2),
##					(x + w/2, y + h),
##					(x, y + h/2)],
##				       X.Convex, X.CoordModeOrigin)
		elif cmd == '3ddiamond':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]
			r = l + w
			b = t + h
			x = l + w/2
			y = t + h/2
			n = int(3.0 * w / h + 0.5)
			ll = l + n
			tt = t + 3
			rr = r - n
			bb = b - 3

			fgcolor = wid.GetWindowPort().rgbFgColor

			Qd.RGBForeColor(cl)
			polyhandle = self._polyhandle([(l, y), (x, t), (x, tt), (ll, y)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(ct)
			polyhandle = self._polyhandle([(x, t), (r, y), (rr, y), (x, tt)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(cr)
			polyhandle = self._polyhandle([(r, y), (x, b), (x, bb), (rr, y)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(cb)
			polyhandle = self._polyhandle([(l, y), (ll, y), (x, bb), (x, b)])
			Qd.PaintPoly(polyhandle)
			
			Qd.RGBForeColor(fgcolor)

##			fg = gc.foreground
##			gc.foreground = cl
##			gc.FillPolygon([(l, y), (x, t), (x, tt), (ll, y)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = ct
##			gc.FillPolygon([(x, t), (r, y), (rr, y), (x, tt)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = cr
##			gc.FillPolygon([(r, y), (x, b), (x, bb), (rr, y)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = cb
##			gc.FillPolygon([(l, y), (ll, y), (x, bb), (x, b)],
##				       X.Convex, X.CoordModeOrigin)
##			gc.foreground = fg
		elif cmd == 'arrow':
			color = entry[1]
			points = entry[2]
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(color)
			apply(Qd.MoveTo, points[:2])
			apply(Qd.LineTo, points[2:])
			polyhandle = self._polyhandle(entry[3])
			Qd.PaintPoly(polyhandle)
			Qd.RGBForeColor(fgcolor)

##			fg = gc.foreground
##			gc.foreground = entry[1]
##			apply(gc.DrawLine, entry[2])
##			gc.FillPolygon(entry[3], X.Convex,
##				       X.CoordModeOrigin)
##			gc.foreground = fg
		else:
			mac_windowbase._DisplayList._render_one(self, entry)

	def clone(self):
		w = self._window
		new = _DisplayList(w, self._bgcolor)
		# copy all instance variables
		new._list = self._list[:]
		new._font = self._font
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
			new._clonedata = self._fgcolor, self._font
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def drawfpolygon(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		xvalues = []
		yvalues = []
		for point in points:
			x, y = w._convert_coordinates(point)
			p.append(x, y)
			xvalues.append(x)
			yvalues.append(y)
		self._list.append('fpolygon', color, p)
		self._optimize(1)
		self._update_bbox(min(xvalues), min(yvalues), max(xvalues), max(yvalues))

	def draw3dbox(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		coordinates = window._convert_coordinates(coordinates)
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append('3dbox', (cl, ct, cr, cb), coordinates)
		self._optimize(1)
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		self._list.append('diamond', coordinates)
		self._optimize()
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	def drawfdiamond(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		coordinates = window._convert_coordinates((x, y, w, h))
		color = window._convert_color(color)
		self._list.append('fdiamond', color, coordinates)
		self._optimize(1)
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)


	def draw3ddiamond(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		coordinates = window._convert_coordinates(coordinates)
		self._list.append('3ddiamond', (cl, ct, cr, cb), coordinates)
		self._optimize(1)
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	def drawarrow(self, color, src, dst):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		color = self._window._convert_color(color)
		try:
			nsx, nsy, ndx, ndy, points = window.arrowcache[(src,dst)]
		except KeyError:
			sx, sy = src
			dx, dy = dst
			nsx, nsy = window._convert_coordinates((sx, sy))
			ndx, ndy = window._convert_coordinates((dx, dy))
			if nsx == ndx and sx != dx:
				if sx < dx:
					nsx = nsx - 1
				else:
					nsx = nsx + 1
			if nsy == ndy and sy != dy:
				if sy < dy:
					nsy = nsy - 1
				else:
					nsy = nsy + 1
			lx = ndx - nsx
			ly = ndy - nsy
			if lx == ly == 0:
				angle = 0.0
			else:
				angle = math.atan2(ly, lx)
			rotation = math.pi + angle
			cos = math.cos(rotation)
			sin = math.sin(rotation)
			points = [(ndx, ndy)]
			points.append(roundi(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
				      roundi(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos))
			points.append(roundi(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
				      roundi(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos))
			window.arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		self._list.append('arrow', color, (nsx, nsy, ndx, ndy), points)
		self._optimize(1)
		self._update_bbox(nsx, nsy, ndx, ndy)
		
	def _polyhandle(self, pointlist):
		"""Return poligon structure"""
		# XXXX Note: This leaks handles like anything!!
		# Find the bounding box
		minx = maxx = pointlist[0][0]
		miny = maxy = pointlist[0][1]
		for x, y in pointlist:
			if x < minx: minx = x
			if y < miny: miny = y
			if x > maxx: maxx = x
			if y > maxy: maxy = y
		# Create structure head
		size = len(pointlist)*4 + 10
		data = struct.pack("hhhhh", size, miny, minx, maxy, maxx)
		self._update_bbox(minx, miny, maxx, maxy)
		for x, y in pointlist:
			data = data + struct.pack("hh", y, x)
		return Res.Resource(data)

toplevel = _Toplevel()
mac_windowbase.toplevel = toplevel
toplevel.initcommands(UserCmd.MENUBAR)
from mac_windowbase import *

class DialogWindow(_Window):
	def __init__(self, resid, title='Dialog'):
		wid = Dlg.GetNewDialog(resid, -1)
		x0, y0, x1, y1 = wid.GetWindowPort().portRect
		w, h = x1-x0, y1-y0
		cmdlist = [
			(UserCmd.COPY, (wid.DialogCopy, ())),
			(UserCmd.PASTE, (wid.DialogPaste, ())),
			(UserCmd.CUT, (wid.DialogCut, ())),
			(UserCmd.DELETE, (wid.DialogDelete, ())),
		]			
		_Window.__init__(self, toplevel, wid, 0, 0, w, h, commands=cmdlist)
		toplevel._register_wid(wid, self)
		Qd.SetPort(wid)
		self._widgetdict = {}
		self._is_shown = 0 # XXXX Is this always true??!?
		self.title = title
		
	def show(self):
		self.settitle(self.title)
		self._wid.ShowWindow()
		self._is_shown = 1
		
	def hide(self):
		self._wid.HideWindow()
		self.settitle(None)
		self._is_shown = 0
		
	def is_showing(self):
		return self._is_shown
		
	def close(self):
		self.hide()
		self._widgetdict = {}
		_Window.close(self)
		
	def addwidget(self, num, widget):
		self._widgetdict[num] = widget
		
	def do_itemhit(self, item, event):
		print 'Dialog %s item %d event %s'%(self, item, event)
		
	def do_itemdraw(self, item):
		try:
			w = self._widgetdict[item]
		except KeyError:
			print 'Unknown user item', item
		else:
			w._redraw()
		
	def _redraw(self, rgn):
		pass
			
	def _activate(self, onoff):
		for w in self._widgetdict.values():
			w._activate(onoff)
			
	def ListWidget(self, item, content=[]):
		widget = _ListWidget(self._wid, item, content)
		self.addwidget(item, widget)
		return widget
#
# XXXX Maybe the previous class should be combined with this one, or does that
# give too many stuff in one object (window, dialogwindow, per-dialog info, editor
# info)?
class MACDialog:
	def __init__(self, title, resid, allitems=[], default=None, cancel=None):
		self._itemlist_shown = allitems[:]
		self._window = DialogWindow(resid)
		self._dialog = self._window._wid
		# Override event handler:
		self._window.do_itemhit = self.do_itemhit
		self._window._do_defaulthit = self._do_defaulthit

		# Setup default key bindings
		self._default = default
		if not self._default is None:
			self._dialog.SetDialogDefaultItem(default)
		if not cancel is None:
			self._dialog.SetDialogCancelItem(cancel)

	def _do_defaulthit(self):
		self.do_itemhit(self._default, None)
		
	def _showitemlist(self, itemlist):
		"""Make sure the items in itemlist are visible and active"""
		for item in itemlist:
			if item in self._itemlist_shown:
				continue
			self._dialog.ShowDialogItem(item)
			tp, h, rect = self._dialog.GetDialogItem(item)
			if tp == 7:		# User control
				h.as_Control().ShowControl()
			self._itemlist_shown.append(item)
		
	def _hideitemlist(self, itemlist):
		"""Make items in itemlist inactive and invisible"""
		for item in itemlist:
			if item not in self._itemlist_shown:
				continue
			self._dialog.HideDialogItem(item)
			tp, h, rect = self._dialog.GetDialogItem(item)
			if tp == 7:		# User control
				h.as_Control().HideControl()
			self._itemlist_shown.remove(item)
			
	def _setsensitive(self, itemlist, sensitive):
		"""Set or reset item sensitivity to user input"""
		for item in itemlist:
			tp, h, rect = self._dialog.GetDialogItem(item)
			ctl = h.as_Control()
			if sensitive:
				ctl.HiliteControl(0)
			else:
				ctl.HiliteControl(255)
		if sensitive:
			self._showitemlist(itemlist)

	def _setctlvisible(self, itemlist, visible):
		"""Set or reset item visibility"""
		for item in itemlist:
			tp, h, rect = self._dialog.GetDialogItem(item)
			ctl = h.as_Control()
			if visible:
				ctl.ShowControl()
			else:
				ctl.HideControl()

	def _settextsensitive(self, itemlist, sensitive):
		"""Set or reset item sensitivity to user input"""
		for item in itemlist:
			tp, h, rect = self._dialog.GetDialogItem(item)
			if sensitive:
				tp = tp & ~128
			else:
				tp = tp | 128
			self._dialog.SetDialogItem(item, tp, h, rect)
		if sensitive:
			self._showitemlist(itemlist)
			
	def _setlabel(self, item, text):
		"""Set the text of a static text or edit text"""
		if '\n' in text:
			text = string.split(text, '\n')
			text = string.join(text, '\r')
		tp, h, rect = self._dialog.GetDialogItem(item)
		Dlg.SetDialogItemText(h, text)

	def _getlabel(self, item):
		"""Return the text of a static text or edit text"""
		tp, h, rect = self._dialog.GetDialogItem(item)
		text = Dlg.GetDialogItemText(h)
		if '\r' in text:
			text = string.split(text, '\r')
			text = string.join(text, '\n')
		return text

	def close(self):
		"""Close the dialog and free resources."""
		self._window.close()
		del self._window.do_itemhit
		del self._dialog

	def show(self):
		"""Show the dialog."""
		self._window.show()
		self._window.register(WMEVENTS.WindowExit, self.goaway, ())
		
	def pop(self):
		"""Pop window to front"""
		self._window.pop()
		
	def goaway(self, *args):
		"""Callback used when user presses go-away box of window"""
		self.hide()

	def hide(self):
		"""Hide the dialog."""
		self._window.hide()

	def settitle(self, title):
		"""Set (change) the title of the window.

		Arguments (no defaults):
		title -- string to be displayed as new window title.
		"""
		self._window.settitle(title)

	def is_showing(self):
		"""Return whether dialog is showing."""
		return self._window.is_showing()

	def setcursor(self, cursor):
		"""Set the cursor to a named shape.

		Arguments (no defaults):
		cursor -- string giving the name of the desired cursor shape
		"""
		self._window.setcursor(cursor)
		
			
class _ModelessDialog(MACDialog):
	def __init__(self, title, dialogid, text, okcallback, cancelcallback=None):
		MACDialog.__init__(self, title, dialogid, [], ITEM_QUESTION_OK, ITEM_QUESTION_CANCEL)
		self.okcallback = okcallback
		self.cancelcallback = cancelcallback
		self._setlabel(ITEM_QUESTION_TEXT, text)
		self.show()
		
	def do_itemhit(self, item, event):
		if item == ITEM_QUESTION_OK:
			self.close()
			if self.okcallback:
				func, arglist = self.okcallback
				apply(func, arglist)
		elif item == ITEM_QUESTION_CANCEL:
			self.close()
			if self.cancelcallback:
				func, arglist = self.cancelcallback
				apply(func, arglist)
		else:
			print 'Unknown modeless dialog event', item, event
			
def _ModalDialog(title, dialogid, text, okcallback, cancelcallback=None):
	d = Dlg.GetNewDialog(dialogid, -1)
	d.SetDialogDefaultItem(ITEM_QUESTION_OK)
	if cancelcallback:
		d.SetDialogCancelItem(ITEM_QUESTION_CANCEL)
	tp, h, rect = d.GetDialogItem(ITEM_QUESTION_TEXT)
	Dlg.SetDialogItemText(h, text)
	w = d.GetDialogWindow()
	w.ShowWindow()
	while 1:
		n = Dlg.ModalDialog(None)
		if n == ITEM_QUESTION_OK:
			del d
			del w
			if okcallback:
				func, arglist = okcallback
				apply(func, arglist)
			return
		elif n == ITEM_QUESTION_CANCEL:
			del d
			del w
			if cancelcallback:
				func, arglist = cancelcallback
				apply(func, arglist)
			return
		else:
			print 'Unknown modal dialog item', n
			
def showmessage(text, mtype = 'message', grab = 1, callback = None,
		     cancelCallback = None, name = 'message',
		     title = 'message'):
	if '\n' in text:
		text = string.join(string.split(text, '\n'), '\r')
	if mtype == 'question' or cancelCallback:
		dlgid = ID_QUESTION_DIALOG
	else:
		dlgid = ID_MESSAGE_DIALOG
	if grab:
		_ModalDialog(title, dlgid, text, callback, cancelCallback)
	else:
		_ModelessDialog(title, dlgid, text, callback, cancelCallback)

# XXXX Do we need a control-window too?

class FileDialog:
	def __init__(self, prompt, directory, filter, file, cb_ok, cb_cancel,
		     existing=0):
		# We implement this modally for the mac.
		macfs.SetFolder(os.path.join(directory + ':placeholder'))
		if existing:
			fss, ok = macfs.PromptGetFile(prompt)
		else:
			fss, ok = macfs.StandardPutFile(prompt, file)
		if ok:
			filename = fss.as_pathname()
			try:
				if cb_ok:
					ret = cb_ok(filename)
			except 'xxx':
				showmessage("Internal error:\nexception %s"%`sys.exc_info()`)
				ret = None
			if ret:
				if type(ret) is StringType:
					showmessage(ret)
		else:
			try:
				if cb_cancel:
					ret = cb_cancel()
				else:
					ret = None
			except:
				showmessage("Internal error:\nexception %s"%`sys.exc_info()`)
				ret = None
			if ret:
				if type(ret) is StringType:
					showmessage(ret)

	def close(self):
		pass

	def setcursor(self, cursor):
		pass

	def is_closed(self):
		return 1

class _Widget:
	def __init__(self, wid, item):
		tp, h, rect = wid.GetDialogItem(item)
		wid.SetDialogItem(item, tp, toplevel._dialog_user_item_handler, rect)
		
class _ListWidget(_Widget):
	def __init__(self, wid, item, content=[]):
		_Widget.__init__(self, wid, item)
		tp, h, rect = wid.GetDialogItem(item)
		# wid is the window (dialog) where our list is going to be in
		# rect is it's item rectangle (as in dialog item)
		self.rect = rect
		rect2 = rect[0]+1, rect[1]+1, rect[2]-16, rect[3]-1
		self.list = MacList.LNew(rect2, (0, 0, 1, len(content)), (0,0), 0, wid,
					0, 0, 0, 1)
		self._data = []
		self._setcontent(0, len(content), content)
		self.wid = wid
		self.list.LSetDrawingMode(1)
		Win.InvalRect(self.rect)
		self._redraw() # DBG
	
	def _setcontent(self, fr, to, content):
		for y in range(fr, to):
			item = content[y-fr]
			self.list.LSetCell(item, (0, y))
		self._data[fr:to] = content
		
	def _delete(self, fr=None, count=1):
		if fr is None:
			self.list.LDelRow(0,0)
			self._data = []
		else:
			self.list.LDelRow(count, fr)
			del self._data[fr:fr+count]
			
	def _insert(self, where=-1, count=1):
		if where == -1:
			where = 32766
			self._data = self._data + [None]*count
		else:
			self._data[where:where] = [None]*count
		return self.list.LAddRow(count, where)
		
	def delete(self, fr=None, count=1):
		self.list.LSetDrawingMode(0)
		self._delete(fr, count)
		self.list.LSetDrawingMode(1)
		Win.InvalRect(self.rect)
		self._redraw() # DBG
		
	def set(self, content):
		self.list.LSetDrawingMode(0)
		self._delete()
		self._insert(count=len(content))
		self._setcontent(0, len(content), content)
		self.list.LSetDrawingMode(1)
		Win.InvalRect(self.rect)
		self._redraw() # DBG
		
	def get(self):
		return self._data
		
	def getitem(self, item):
		return self._data[item]
		
	def insert(self, where=-1, content):
		self.list.LSetDrawingMode(0)
		where = self._insert(where, len(content))
		self._setcontent(where, where+len(content), content)
		self.list.LSetDrawingMode(1)
		Win.InvalRect(self.rect)
		self._redraw() # DBG
		
	def replace(self, where, what):
		self.list.LSetDrawingMode(0)
		self._setcontent(where, where+1, [what])
		self.list.LSetDrawingMode(1)
		Win.InvalRect(self.rect)
		self._redraw() # DBG
		
	def deselectall(self):
		while 1:
			ok, pt = self.list.LGetSelect(1, (0,0))
			if not ok: return
			self.list.LSetSelect(0, pt)
			
	def select(self, num):
		self.deselectall()
		if num is None or num < 0:
			return
		self.list.LSetSelect(1, (0, num))
		
	def getselect(self):
		ok, (x, y) = self.list.LGetSelect(1, (0,0))
		if not ok:
			return None
		return y
			
	def click(self, where, modifiers):
		is_double = self.list.LClick(where, modifiers)
		ok, (x, y) = self.list.LGetSelect(1, (0, 0))
		if ok:
			return y, is_double
		else:
			return None, is_double
			
	# draw a frame around the list, List Manager doesn't do that
	def drawframe(self):
		Qd.SetPort(self.wid)
		Qd.FrameRect(self.rect)
		
	def _redraw(self, rgn=None):
		if rgn == None:
			rgn = self.wid.GetWindowPort().visRgn
		self.drawframe()
		self.list.LUpdate(rgn)
		
	def _activate(self, onoff):
		self.list.LActivate(onoff)
		
class SelectWidget:
	def __init__(self, wid, ctlid, items=[], default=None, callback=None):
		self.wid = wid
		self.itemnum = ctlid
		self.menu = None
		self.choice = None
		tp, h, self.rect = self.wid.GetDialogItem(self.itemnum)
		self.control = h.as_Control()
		self.setitems(items, default)
		self.usercallback = callback
		
	def delete(self):
		self.menu.delete()
		del self.menu
		del self.wid
		del self.control
		
	def setitems(self, items=[], default=None):
		items = items[:]
		if not items:
			items.append('')
		self.choice = None
		self.data = items
		if self.menu:
			self.menu.delete()
			del self.menu
		self.menu = SelectPopupMenu(items)
		mhandle, mid = self.menu.getpopupinfo()
		self.control.SetPopupData(mhandle, mid)
		self.control.SetControlMinimum(1)
		self.control.SetControlMaximum(len(items)+1)
		if default != None:
			self.select(default)
		
	def select(self, item):
		if item in self.data:
			item = self.data.index(item)
		self.control.SetControlValue(item+1)
		
	def click(self, event=None):
		self.usercallback()
		
	def getselect(self):
		item = self.control.GetControlValue()-1
		if 0 <= item < len(self.data):
			return self.data[item]
		return None
		
class SelectionDialog(DialogWindow):
	def __init__(self, listprompt, selectionprompt, itemlist, default, fixed=0, hascancel=1):
		# First create dialogwindow and set static items
		DialogWindow.__init__(self, ID_SELECT_DIALOG)
		if fixed:
			# The user cannot modify the items, nor cancel
			self._wid.HideDialogItem(ITEM_SELECT_SELECTPROMPT)
			self._wid.HideDialogItem(ITEM_SELECT_ITEM)
		if not hascancel:
			self._wid.HideDialogItem(ITEM_SELECT_CANCEL)
		tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_LISTPROMPT)
		Dlg.SetDialogItemText(h, listprompt)
		tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_SELECTPROMPT)
		Dlg.SetDialogItemText(h, selectionprompt)
		
		# Set defaults
		self._wid.SetDialogDefaultItem(ITEM_SELECT_OK)
		self._wid.SetDialogCancelItem(ITEM_SELECT_CANCEL)

		# Now setup the scrolled list
		self._itemlist = itemlist
		self._listwidget = self.ListWidget(ITEM_SELECT_ITEMLIST, itemlist)
		if default in itemlist:
			num = itemlist.index(default)
			self._listwidget.select(num)
			
		# and the default item
		tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_ITEM)
		Dlg.SetDialogItemText(h, default)
		
		# And show it
		self.show()
	
	def do_itemhit(self, item, event):
		is_ok = 0
		if item == ITEM_SELECT_CANCEL:
			self.CancelCallback()
			self.close()
		elif item == ITEM_SELECT_OK:
			is_ok = 1
		elif item == ITEM_SELECT_ITEMLIST:
			(what, message, when, where, modifiers) = event
			Qd.SetPort(self._wid)
			where = Qd.GlobalToLocal(where)
			item, isdouble = self._listwidget.click(where, modifiers)
			if item is None:
				return
			tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_ITEM)
			Dlg.SetDialogItemText(h, self._itemlist[item])
			is_ok = isdouble
		elif item == ITEM_SELECT_ITEM:
			pass
		else:
			print 'Unknown item', self, item, event
		# Done a bit funny, because of double-clicking
		if is_ok:
			tp, h, rect = self._wid.GetDialogItem(ITEM_SELECT_ITEM)
			rv = Dlg.GetDialogItemText(h)
			self.OkCallback(rv)
			self.close()
			
class SingleSelectionDialog(SelectionDialog):
	def __init__(self, list, title, prompt):
		# XXXX ignore title for now
		self.__dict = {}
		self.__done = 0
		hascancel = 0
		keylist = []
		for item in list:
			if item == None:
				continue
			if item == 'Cancel':
				hascancel = 1
			else:
				k, v = item
				self.__dict[k] = v
				keylist.append(k)
		SelectionDialog.__init__(self, prompt, '', keylist, keylist[0], 
				fixed=1, hascancel=hascancel)

	def OkCallback(self, key):
		if not self.__dict.has_key(key):
			print 'You made an impossible selection??'
			return
		else:
			rtn, args = self.__dict[key]
			apply(rtn, args)
			self.__done = 1
			
	def rungrabbed(self):
		toplevel.grab(self)
		while not self.__done:
			toplevel._eventloop(100)
		toplevel.grab(None)
			
class InputDialog(DialogWindow):
	def __init__(self, prompt, default, cb, cancelCallback = None):
		# First create dialogwindow and set static items
		DialogWindow.__init__(self, ID_INPUT_DIALOG)
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_PROMPT)
		Dlg.SetDialogItemText(h, prompt)
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_TEXT)
		Dlg.SetDialogItemText(h, default)
		self._wid.SetDialogDefaultItem(ITEM_INPUT_OK)
		self._wid.SetDialogCancelItem(ITEM_INPUT_CANCEL)
		self._cb = cb
		self._cancel = cancelCallback

	def do_itemhit(self, item, event):
		if item == ITEM_INPUT_CANCEL:
			if self._cancel:
				apply(apply, self._cancel)
			self.close()
		elif item == ITEM_INPUT_OK:
			self._do_defaulthit()
		elif item == ITEM_INPUT_TEXT:
			pass
		else:
			print 'Unknown item', self, item, event
			
	def _do_defaulthit(self):
		tp, h, rect = self._wid.GetDialogItem(ITEM_INPUT_TEXT)
		rv = Dlg.GetDialogItemText(h)
		self._cb(rv)
		self.close()

[TOP, CENTER, BOTTOM] = range(3)


def Dialog(list, title = '', prompt = None, grab = 1, vertical = 1):
	w = SingleSelectionDialog(list, title, prompt)
	if grab:
		w.rungrabbed()
	return w

_end_loop = '_end_loop'			# exception for ending a loop

class _Question:
	def __init__(self, text):
		self.looping = FALSE
		self.answer = None
		self.text = text

	def run(self):
		try:
			showmessage(self.text, mtype = 'question',
			    callback = (self.callback, (TRUE,)),
			    cancelCallback = (self.callback, (FALSE,)))
		except _end_loop:
			pass
		return self.answer

	def callback(self, answer):
		self.answer = answer
		if self.looping:
			raise _end_loop

def showquestion(text):
	return _Question(text).run()

class _MultChoice:
	def __init__(self, prompt, msg_list, defindex):
		raise 'MultChoice called!'
		self.looping = FALSE
		self.answer = None
		self.msg_list = msg_list
		list = []
		for msg in msg_list:
			list.append(msg, (self.callback, (msg,)))
		self.dialog = Dialog(list, title = None, prompt = prompt,
				     grab = TRUE, vertical = FALSE)

	def run(self):
		try:
			self.looping = TRUE
			Xt.MainLoop()
		except _end_loop:
			pass
		return self.answer

	def callback(self, msg):
		for i in range(len(self.msg_list)):
			if msg == self.msg_list[i]:
				self.answer = i
				if self.looping:
					raise _end_loop
				return

def multchoice(prompt, list, defindex):
	return _MultChoice(prompt, list, defindex).run()

def roundi(x):
	if x < 0:
		return roundi(x + 1024) - 1024
	return int(x + 0.5)

fonts = mac_windowbase.fonts

mac_windowbase.toplevel = toplevel

newwindow = toplevel.newwindow

newcmwindow = toplevel.newcmwindow

windowgroup = toplevel.windowgroup

close = toplevel.close

addclosecallback = toplevel.addclosecallback

setcursor = toplevel.setcursor

getsize = toplevel.getsize

usewindowlock = toplevel.usewindowlock

settimer = toplevel.settimer

select_setcallback = toplevel.select_setcallback

mainloop = toplevel.mainloop

canceltimer = toplevel.canceltimer

getscreensize = toplevel.getscreensize

getscreendepth = toplevel.getscreendepth

lopristarting = toplevel.lopristarting

setidleproc = toplevel.setidleproc

cancelidleproc = toplevel.cancelidleproc

