__version__ = "$Id$"

from Carbon import Win
from Carbon import Qd
from Carbon import Res
from Carbon import Icn
from Carbon import App
from Carbon import Appearance
import string
from Carbon import QuickDraw
from types import *
import struct
import math
import time
import CheckInsideArea
#
# Stuff needed from other mw_ modules:
#
from mw_globals import error
from mw_globals import TRUE, FALSE
from mw_globals import _X, _Y, _WIDTH, _HEIGHT, ICONSIZE_PXL
from mw_globals import ARR_LENGTH, ARR_SLANT, ARR_HALFWIDTH, SIZE_3DBORDER, UNIT_PXL
import mw_globals
import mw_fonts
import mw_resources

# Special round function (XXXX needs work).
def _roundi(x):
	if x < 0:
		return _roundi(x + 1024) - 1024
	return int(x + 0.5)
	
def _colormix((r1, g1, b1), (r2, g2, b2)):
	return (r1+r2)/2, (g1+g2)/2, (b1+b2)/2
	
# Icon storage
_icons = {}
_icon_ids = {
	# '' is special: don't draw any icon (needed for removing icons in optimize)
	'closed': mw_resources.ID_ICON_TRIANGLE_RIGHT,
	'open': mw_resources.ID_ICON_TRIANGLE_DOWN,
	'parclosed': mw_resources.ID_ICON_TRIANGLE_RIGHT,
	'paropen': mw_resources.ID_ICON_TRIANGLE_DOWN,
	'seqclosed': mw_resources.ID_ICON_TRIANGLE_RIGHT,
	'seqopen': mw_resources.ID_ICON_TRIANGLE_DOWN,
	'exclclosed': mw_resources.ID_ICON_TRIANGLE_RIGHT,
	'exclopen': mw_resources.ID_ICON_TRIANGLE_DOWN,
	'prioclosed': mw_resources.ID_ICON_TRIANGLE_RIGHT,
	'prioopen': mw_resources.ID_ICON_TRIANGLE_DOWN,
	'switchclosed': mw_resources.ID_ICON_TRIANGLE_RIGHT,
	'switchopen': mw_resources.ID_ICON_TRIANGLE_DOWN,
	'bandwidthgood': mw_resources.ID_ICON_BANDWIDTH_OK,
	'bandwidthbad': mw_resources.ID_ICON_BANDWIDTH_ERROR,
	'error': mw_resources.ID_ICON_ERROR,
	'linksrc': mw_resources.ID_ICON_LINKSRC,
	'linkdst': mw_resources.ID_ICON_LINKDST,
	'danglinganchor': mw_resources.ID_ICON_DANGLINGANCHOR,
##	'linksrcdst': mw_resources.ID_ICON_LINKSRCDST,
	'transin': mw_resources.ID_ICON_TRANSIN,
	'transout': mw_resources.ID_ICON_TRANSOUT,
	'beginevent' : mw_resources.ID_ICON_EVENTIN,
	'endevent' : mw_resources.ID_ICON_EVENTOUT,
	'causeevent' : mw_resources.ID_ICON_CAUSEEVENT,
	'danglingevent' : mw_resources.ID_ICON_DANGLINGEVENT,
	'repeat' : mw_resources.ID_ICON_REPEAT,
	'playing': mw_resources.ID_ICON_PLAYING,	# 
	'waitstop': mw_resources.ID_ICON_WAITSTOP, # 
	'idle': mw_resources.ID_ICON_IDLE,	# 
##	'activateevent' : mw_resources.ID_ICON_ACTIVATEVENT,
##	'animation' : mw_resources.ID_ICON_ANIMATION,
##	'duration' : mw_resources.ID_ICON_DURATION,
##	'focusin' : mw_resources.ID_ICON_FOCUSIN,
##	'happyface' : mw_resources.ID_ICON_HAPPYFACE,
##	'spaceman': mw_resources.ID_ICON_SPACEMAN,
##	'wallclock': mw_resources.ID_ICON_WALLCLOCK,
}

def _get_icon(which):
	if not _icons:
		for name, resid in _icon_ids.items():
			_icons[name] = Icn.GetCIcon(resid)
		_icons[''] = None
	try:
		return _icons[which]
	except KeyError:
		print 'Unknown icon:', which
		return None

class _DisplayList:
	def __init__(self, window, bgcolor, units):
		self.__units = units
		self.starttime = 0
		self._window = window
		window._displists.append(self)
		self._bgcolor = bgcolor
		self._fgcolor = window._fgcolor
		self._linewidth = 1
		self._buttons = []
		self._list = []
		self._rendered = 0
##		if self._window._transparent <= 0:
##			self._list.append(('clear',))
		self._list.append(('clear',))
		self._optimdict = {}
		self._cloneof = None
		self._clonestart = 0
		self._rendered = FALSE
		self._font = None
		self._old_fontinfo = None
##		self._clonebboxes = []
		self._really_rendered = FALSE	# Set to true after the first real redraw
		self._tmprgn = Qd.NewRgn()
		self._need_convert_coordinates = 1
		
		# associate cmd names with list indices
		# used by animation experimental methods
		self.__cmddict = {}
		self.__butdict = {}

	def close(self):
		if self._window is None:
			return
		win = self._window
		buttons_changed = 0
		for b in self._buttons[:]:
			buttons_changed = 1
			b.close()
		win._displists.remove(self)
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			if self._buttons or buttons_changed:
				win._buttonschanged()
			if win._transparent == -1 and win._parent:
				win._parent._clipchanged()
			win._mac_invalwin()
		self._window = None
		del self._cloneof
		try:
			del self._clonedata
		except AttributeError:
			pass
		del self._optimdict
		del self._list
		del self._buttons
		del self._font

	def is_closed(self):
		return self._window is None

	def clone(self):
		w = self._window
		new = _DisplayList(w, self._bgcolor, self.__units)
		# copy all instance variables
		new._list = self._list[:]
		new.usefont(self._font)
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
			new._clonedata = self._fgcolor, self._font
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new
		
	def _get_button_region(self):
		rgn = Qd.NewRgn()
		for b in self._buttons:
			brgn = b._get_button_region()
			if brgn:
				Qd.UnionRgn(rgn, brgn, rgn)
				Qd.DisposeRgn(brgn)
		return rgn
		
	def _setfgcolor(self, fgcolor):
##		if fgcolor == 'theme_background':
##			depth=16 # XXX
##			App.SetThemePen(Appearance.kThemeBrushDocumentWindowBackground, depth, 1)
##			return
		# XXX Not sure about this:
		if fgcolor == None:
			fgcolor = self._bgcolor
		if fgcolor == None:
			fgcolor = (0,0,0)
		Qd.RGBForeColor(fgcolor)
		
	def _restorecolors(self):
		self._setfgcolor(self._fgcolor)
		bgcolor = self._bgcolor
		if bgcolor is None:
			bgcolor = (0, 0, 0)
		Qd.RGBBackColor(bgcolor)

	def _setblackwhitecolors(self):
		# For image draw
		Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
		Qd.RGBForeColor((0, 0, 0))
		
	def render(self):
		#
		# On the mac, we can only render after a full setup.
		# Hence, we schedule a redraw only
		#
		window = self._window
		self._rendered = 1
		self.starttime = time.time()
		# XXXX buttons?
		oldenv = window._mac_setwin()
		if window._transparent == -1:
			window._parent._clipchanged()
		#
		# Optimize rendering. There are two cases in which we want to draw immedeately:
		# - If we are the topmost window and no update event is pending for us (so things
		#   look a bit more snappy)
		# - If we are a clone and our parent is already rendered we render now, and only
		#   the bits that are needed.
		#
		clonestart = self._clonestart
		if self._cloneof and self._cloneof == window._active_displist and \
				self._cloneof._really_rendered:
			render_now = 1
		else:
			render_now = self._can_render_now()
		if render_now:
			clip = window._mac_getclip()
			saveclip = Qd.NewRgn()
			Qd.GetClip(saveclip)
			Qd.SetClip(clip)
			self._render(clonestart)
			Qd.SetClip(saveclip)
			Qd.DisposeRgn(saveclip)
		else:
			window._mac_invalwin()
		window._mac_unsetwin(oldenv)
		
		window._active_displist = self
		if self._buttons:
			window._buttonschanged()
			self._startbuttontimers()
	
	def _startbuttontimers(self):
		"""Set callbacks to update mouse button region at any time a
		button changes sensitivity"""
		changetimes = {}
		for b in self._buttons:
			if not b._times:
				continue
			t0, t1 = b._times
			changetimes[t0] = changetimes[t1] = 1
		for t in changetimes.keys():
			mw_globals.toplevel.settimer(t, (self._window._buttonschanged, ()))
	
	def _can_render_now(self):
		"""Return true if we can do the render now, in stead of
		scheduling the update event"""
		# First check that no update events are pending.
		window = self._window
		if window._transition:
			return 0
		rgn = Qd.NewRgn()
		window._onscreen_wid.GetWindowUpdateRgn(rgn)
		ok = Qd.EmptyRgn(rgn)
		# Next check that we're topmost
		if ok:
			ok = window._is_on_top()
		Qd.DisposeRgn(rgn)
		return ok
		
	def _getredrawguarantee(self, skipclear=0):
		"""Return a region that we promise we will redraw. Simple implementation,
		only return the initial clear or the first image (good enough for now)"""
		window = self._window
		for entry in self._list:
			cmd = entry[0]
			if cmd == 'clear' and self._bgcolor != None and not skipclear:
				r = Qd.NewRgn()
				Qd.RectRgn(r, window.qdrect())
				return r
			if cmd == 'image':
				xscrolloffset, yscrolloffset = window._scrolloffset()
				mask, image, srcx, srcy, dstx, dsty, w, h, units = entry[1:]
				dstrect = self._convert_coordinates((dstx, dsty, w, h), units=units)
				r = Qd.NewRgn()
				Qd.RectRgn(r, dstrect)
				return r
		return None
		
	def _render(self, clonestart=0, rgn=None):
		# rgn (region to be redrawn, None for everything) ignored for now
##		import Evt
##		t0 = Evt.TickCount()
		self._really_rendered = 1
		window = self._window
		self._render_grafport = window._mac_getoswindowport()
		self._render_cliprgn = rgn
		window._active_displist = self
		self._restorecolors()
		if clonestart:
			list = self._list[clonestart:]
		else:
			list = self._list
		self._dbg_did = 0
		if self._window._convert_coordinates((0,0,1,1), units = self.__units) == (0,0,1,1):
			self._need_convert_coordinates = 0
		for entry in list:
			self._render_one(entry)
##		print "Redraw time:", (Evt.TickCount()-t0)/60.0, self._dbg_did, 'of', len(list)
		self._need_convert_coordinates = 1
		self._render_grafport = None
		self._render_cliprgn = None
			
	def _render_one(self, entry):
		cmd = entry[0]
		
		if cmd == 'clear':
			if self._bgcolor != None:
				r = self._getredrawguarantee(skipclear=1)
				if r:
					r2 = Qd.NewRgn()
					Qd.RectRgn(r2, self._window.qdrect())
					Qd.DiffRgn(r2, r, r2)
					Qd.EraseRgn(r2)
					Qd.DisposeRgn(r)
					Qd.DisposeRgn(r2)
				else:
					Qd.EraseRect(self._window.qdrect())
		elif cmd == 'fg':
			self._setfgcolor(entry[1])
		elif cmd == 'font':
			entry[1]._setfont(self._render_grafport)
		elif cmd == 'text':
			x, y, w, h = self._convert_coordinates(entry[1:5])
			if not self._render_overlaprgn((x, y-h, x+w, y)):
				return
			Qd.MoveTo(x, y)
			 # XXXX Incorrect for long strings:
			Qd.DrawText(entry[5], 0, len(entry[5]))
		elif cmd == 'icon':
			icon = entry[2]
			if icon == None:
				return
			rect = self._convert_coordinates(entry[1])
			if not self._render_overlaprgn(rect):
				return
			x0, y0, x1, y1 = rect
			if x1-x0 < ICONSIZE_PXL:
				leftextra = (ICONSIZE_PXL - (x1-x0))/2
				x0 = x0 + leftextra
				x1 = x0 + ICONSIZE_PXL
			if y1-y0 < ICONSIZE_PXL:
				topextra = (ICONSIZE_PXL - (y1-y0))/2
				y0 = y0 + topextra
				y1 = y0 + ICONSIZE_PXL
			Icn.PlotCIcon((x0, y0, x1, y1), icon)
		elif cmd == 'image':
			mask, image, srcx, srcy, dstx, dsty, w, h = entry[1:]
			dstrect = self._convert_coordinates((dstx, dsty, w, h))
			if not self._render_overlaprgn(dstrect):
				return
			w = dstrect[2]-dstrect[0]
			h = dstrect[3]-dstrect[1]
			srcrect = srcx, srcy, srcx+w, srcy+h
			self._setblackwhitecolors()
			clip = self._window._mac_getclip()
			if mask:
				# XXXX We should also take note of the clip here.
				Qd.CopyMask(image[0], mask[0],
					    self._render_grafport.portBits,
					    srcrect, srcrect, dstrect)
			else:
				Qd.CopyBits(image[0],
				      self._render_grafport.portBits,
				      srcrect, dstrect,
				      QuickDraw.srcCopy+QuickDraw.ditherCopy,
				      clip)
			self._restorecolors()
		elif cmd == 'line':
			color = entry[1]
			points = entry[2]
			self._setfgcolor(color)
			x, y = self._convert_coordinates(points[0])
			Qd.MoveTo(x, y)
			for np in points[1:]:
				x, y = self._convert_coordinates(np)
				Qd.LineTo(x, y)
			self._restorecolors()
		elif cmd == '3dhline':
			color1, color2, x0, x1, y = entry[1:]
			fgcolor = self._render_grafport.rgbFgColor
			self._setfgcolor(color1)
			x0, y0 = self._convert_coordinates((x0, y))
			x1, y1 = self._convert_coordinates((x1, y))
			if not self._render_overlaprgn((x0, y0, x1, y1+1)):
				return
			Qd.MoveTo(x0, y0)
			Qd.LineTo(x1, y1)
			self._setfgcolor(color2)
			Qd.MoveTo(x0, y0+1)
			Qd.LineTo(x1, y1+1)
			self._setfgcolor(fgcolor)
			self._restorecolors()
		elif cmd == 'box':
			rect = self._convert_coordinates(entry[1])
			if not self._render_overlaprgn(rect):
				return
			Qd.FrameRect(rect)
		elif cmd == 'fbox':
			color = entry[1]
			units = entry[3]
			rect = self._convert_coordinates(entry[2], units)
			if not self._render_overlaprgn(rect):
				return
			self._setfgcolor(color)
			Qd.PaintRect(rect)
			self._restorecolors()
		elif cmd == 'linewidth':
			Qd.PenSize(entry[1], entry[1])
		elif cmd == 'fpolygon':
			polyhandle = self._polyhandle(entry[2], cliprgn=self._render_cliprgn)
			if not polyhandle:
				return
			self._setfgcolor(entry[1])
			Qd.PaintPoly(polyhandle)
			self._restorecolors()
		elif cmd == '3dbox':
			rect = self._convert_coordinates(entry[2])
			if not self._render_overlaprgn(rect):
				return
			l, t, r, b = rect
			cl, ct, cr, cb = entry[1]
			clt = _colormix(cl, ct)
			ctr = _colormix(ct, cr)
			crb = _colormix(cr, cb)
			cbl = _colormix(cb, cl)
##			print '3Dbox', (l, t, r, b) # DBG
##			print 'window', self._window.qdrect() # DBG
			# l, r, t, b are the corners
			l3 = l + SIZE_3DBORDER
			t3 = t + SIZE_3DBORDER
			r3 = r - SIZE_3DBORDER
			b3 = b - SIZE_3DBORDER
			# draw left side
			self._setfgcolor(cl)
			polyhandle = self._polyhandle([(l, t), (l3, t3), (l3, b3), (l, b)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			# draw top side
			self._setfgcolor(ct)
			polyhandle = self._polyhandle([(l, t), (r, t), (r3, t3), (l3, t3)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			# draw right side
			self._setfgcolor(cr)
			polyhandle = self._polyhandle([(r3, t3), (r, t), (r, b), (r3, b3)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			# draw bottom side
			self._setfgcolor(cb)
			polyhandle = self._polyhandle([(l3, b3), (r3, b3), (r, b), (l, b)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			# draw topleft
			self._setfgcolor(clt)
			Qd.PaintRect((l, t, l3, t3))
			# draw topright
			self._setfgcolor(ctr)
			Qd.PaintRect((r3, t, r, t3))
			# draw botright
			self._setfgcolor(crb)
			Qd.PaintRect((r3, b3, r, b))
			# draw leftbot
			self._setfgcolor(cbl)
			Qd.PaintRect((l, b3, l3, b))
			
			self._restorecolors()
		elif cmd == 'diamond':
			rect = self._convert_coordinates(entry[1])
			if not self._render_overlaprgn(rect):
				return
			x, y, x1, y1 = rect
			w = x1-x
			h = y1-y
			Qd.MoveTo(x, y + h/2)
			Qd.LineTo(x + w/2, y)
			Qd.LineTo(x + w, y + h/2)
			Qd.LineTo(x + w/2, y + h)
			Qd.LineTo(x, y + h/2)
		elif cmd == 'fdiamond':
			rect = self._convert_coordinates(entry[2])
			if not self._render_overlaprgn(rect):
				return
			x, y, x1, y1 = rect
			w = x1-x
			h = y1-y
			self._setfgcolor(entry[1])
			polyhandle = self._polyhandle([(x, y + h/2),
					(x + w/2, y),
					(x + w, y + h/2),
					(x + w/2, y + h),
					(x, y + h/2)])
			if polyhandle: Qd.PaintPoly(polyhandle)
			self._restorecolors()
		elif cmd == '3ddiamond':
			rect = self._convert_coordinates(entry[2])
			if not self._render_overlaprgn(rect):
				return
			l, t, r, b = rect
			cl, ct, cr, cb = entry[1]
			w = r-l
			h = b-t
			r = l + w
			b = t + h
			x = l + w/2
			y = t + h/2
			n = int(3.0 * w / h + 0.5)
			ll = l + n
			tt = t + 3
			rr = r - n
			bb = b - 3


			self._setfgcolor(cl)
			polyhandle = self._polyhandle([(l, y), (x, t), (x, tt), (ll, y)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			
			self._setfgcolor(ct)
			polyhandle = self._polyhandle([(x, t), (r, y), (rr, y), (x, tt)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			
			self._setfgcolor(cr)
			polyhandle = self._polyhandle([(r, y), (x, b), (x, bb), (rr, y)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			
			self._setfgcolor(cb)
			polyhandle = self._polyhandle([(l, y), (ll, y), (x, bb), (x, b)], conv=0)
			if polyhandle: Qd.PaintPoly(polyhandle)
			
			self._restorecolors()
		elif cmd == 'arrow':
			color = entry[1]
			src = entry[2]
			dst = entry[3]
			x0, y0, x1, y1, points = self._arrowdata(src,dst)
			if not self._render_overlaprgn((x0, y0, x1, y1)):
				return

			self._setfgcolor(color)

			Qd.MoveTo(x0, y0)
			Qd.LineTo(x1, y1)
			polyhandle = self._polyhandle(points)
			if polyhandle: Qd.PaintPoly(polyhandle)
			self._restorecolors()
		else:
			raise 'Unknown displaylist command', cmd
		self._dbg_did = self._dbg_did + 1

	def _convert_coordinates(self, coords, units=None):
		"""Convert coordinates from window xywh style to quickdraw style"""
		xscrolloffset, yscrolloffset = self._window._scrolloffset()
		if units is None:
			units = self.__units
		if self._need_convert_coordinates:
			coords = self._window._convert_coordinates(coords, units = units)
		x = coords[0] + xscrolloffset
		y = coords[1] + yscrolloffset
		if len(coords) == 2:
			return x, y
		else:
			w, h = coords[2:]
			return (x, y, x+w, y+h)
	
	def _render_overlaprgn(self, rect):
		"""Return true if there is an overlap between the current rendering region and the rect"""
		if not self._render_cliprgn:
			# Always draw if we have no clipping region (probably just-cloned displaylist)
			return 1
		r2 = self._tmprgn
		Qd.RectRgn(r2, rect)
		Qd.SectRgn(self._render_cliprgn, r2, r2)
		empty = Qd.EmptyRgn(r2)
		return not empty
		
	def _pixel2units(self, coords):
		if self.__units == UNIT_PXL:
			return coords
		return self._window._pxl2rel(coords)
		
	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		if color == None:
			color = self._bgcolor
		else:
			color = self._window._convert_color(color)
		if color != self._fgcolor:
			self._list.append(('fg', color))
			self._fgcolor = color

	# set the media sensitivity
	# value is percentage value (range 0-100); opaque=0, transparent=100
	def setAlphaSensitivity(self, value):
		self._alphaSensitivity = value

	# Define a new button. Coordinates are in window relatives
	def newbutton(self, coordinates, z = 0, times = None, sensitive = 1):
		if self._rendered:
			raise error, 'displaylist already rendered'
		
		# factor out shape type
		shape = coordinates[0]
		coordinates = coordinates[1:]
		return _Button(self, shape, coordinates, z, times, sensitive)

	def display_image_from_file(self, file, crop = (0,0,0,0), fit = 'meet',
				    center = 1, coordinates = None,
				    clip = None, align = None, units = None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		win = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       win._prepare_image(file, crop, fit, center, coordinates, align, units)
		self._list.append(('image', mask, image, src_x, src_y,
				   dest_x, dest_y, width, height, units))
		self._optimize(2)
##		x, y, w, h = win._rect
##		wf, hf = win._scrollsizefactors()
##		w, h = w*wf, h*hf
##		return float(dest_x - x) / w, float(dest_y - y) / h, \
##		       float(width) / w, float(height) / h
		return dest_x, dest_y, width, height

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		self._list.append(('line', color, points[:]))

	def draw3dhline(self, color1, color2, x1, x2, y):
		w = self._window
		color1 = w._convert_color(color1)
		color2 = w._convert_color(color2)
		self._list.append(('3dhline', color1, color2, x1, x2, y))

	def drawbox(self, coordinates, clip = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append(('box', coordinates))
		self._optimize()

	def drawfbox(self, color, coordinates, units=None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append(('fbox', self._window._convert_color(color), coordinates, units))
		self._optimize(1)

	def drawstipplebox(self, color, coordinates, units=None):
		# This should draw a stippled or hatched box
		pass

	def drawmarker(self, color, coordinates):
		pass # XXXX To be implemented

	def drawfpolygon(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		self._list.append(('fpolygon', color, points[:]))
		self._optimize(1)

	def draw3dbox(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append(('3dbox', (cl, ct, cr, cb), coordinates))
		self._optimize(1)

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._list.append(('diamond', coordinates))
		self._optimize()

	def drawfdiamond(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		coordinates = (x, y, w, h)
		color = window._convert_color(color)
		self._list.append(('fdiamond', color, coordinates))
		self._optimize(1)

	def draw3ddiamond(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append(('3ddiamond', (cl, ct, cr, cb), coordinates))
		self._optimize(1)

	def drawicon(self, coordinates, icon):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		data = _get_icon(icon)
		if data:
			self._list.append(('icon', coordinates, data))
			self._optimize(2)
		
	def drawarrow(self, color, src, dst):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		color = self._window._convert_color(color)
		self._list.append(('arrow', color, src, dst))
		self._optimize(1)
##		self._update_bbox(nsx, nsy, ndx, ndy)
		
	def _arrowdata(self, src, dst):
		try:
			nsx, nsy, ndx, ndy, points = self._window.arrowcache[(src,dst)]
		except KeyError:
			sx, sy = src
			dx, dy = dst
			nsx, nsy = self._convert_coordinates((sx, sy))
			ndx, ndy = self._convert_coordinates((dx, dy))
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
			points.append((_roundi(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
				       _roundi(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos)))
			points.append((_roundi(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
				       _roundi(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos)))
			self._window.arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		return nsx, nsy, ndx, ndy, points
	
	def _polyhandle(self, pointlist, conv=1, cliprgn=None):
		"""Return polygon structure"""
		xscrolloffset, yscrolloffset = self._window._scrolloffset()

		# Find the bounding box
		minx = maxx = pointlist[0][0]
		miny = maxy = pointlist[0][1]
		for x, y in pointlist:
			if x < minx: minx = x
			if y < miny: miny = y
			if x > maxx: maxx = x
			if y > maxy: maxy = y
		if conv:
			minx, miny = self._convert_coordinates((minx, miny))
			maxx, maxy = self._convert_coordinates((maxx, maxy))
		if not self._render_overlaprgn((minx, miny, maxx, maxy)):
			return
		# Create structure head
		size = len(pointlist)*4 + 10
		data = struct.pack("hhhhh", size, miny, minx, maxy, maxx)
##		self._update_bbox(minx, miny, maxx, maxy)
		for pt in pointlist:
			if conv:
				x, y = self._convert_coordinates(pt)
			else:
				x, y = pt
			data = data + struct.pack("hh", y, x)
		return Res.Handle(data)

	def get3dbordersize(self):
		return self._pixel2units((0,0,SIZE_3DBORDER,SIZE_3DBORDER))[2:4]
		
	def usefont(self, fontobj):
		if fontobj is None:
			# should only happen during cloning
			self._font = fontobj
			return None
		if fontobj != self._font:
			self._font = fontobj
			# XXXX Or should this be done on the onscreen window?
			self._font._initparams(self._window._mac_getoswindowport())
			self._list.append(('font', fontobj))
			self.__font_size_cache = self.__baseline(), self.__fontheight(), self.__pointsize()
		return self.__font_size_cache

	def setfont(self, font, size):
		return self.usefont(mw_fonts.findfont(font, size))

	def fitfont(self, fontname, str, margin = 0):
		return self.usefont(mw_fonts.findfont(fontname, 10))

	def __baseline(self):
		baseline = self._font.baselinePXL()
		return self._pixel2units((0,0,0,baseline))[3]

	def __fontheight(self):
		fontheight = self._font.fontheightPXL()
		return self._pixel2units((0,0,0,fontheight))[3]

	def __pointsize(self):
		return self._font.pointsize()
		
	def baselinePXL(self):
		return self._font.baselinePXL()

	def baseline(self):
		return self.__font_size_cache[0]

	def fontheightPXL(self):
		return self._font.fontheightPXL()

	def fontheight(self):
		return self.__font_size_cache[1]

	def pointsize(self):
		return self.__font_size_cache[2]

	def strsizePXL(self, str):
		return self._font.strsizePXL(str)

	def strsize(self, str):
		# XXXX Or on the _onscreen_wid??
		width, height = self._font.strsizePXL(str, port=self._window._mac_getoswindowport())
		return self._pixel2units((0,0,width,height))[2:4]

	def setpos(self, x, y):
		self._curpos = x, y
		self._xpos = x

	def writestr(self, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		old_fontinfo = None
		# XXXX Or on the _onscreen_wid??
		port = w._mac_getoswindowport()
		if self._font._checkfont(port):
			old_fontinfo = mw_fonts._savefontinfo(port)
		self._font._setfont(port)
		base = self.baseline()
		height = self.fontheight()
		strlist = string.splitfields(str, '\n')
		oldx, oldy = x, y = self._curpos
		if len(strlist) > 1 and oldx > self._xpos:
			oldx = self._xpos
		oldy = oldy - base
		maxx = oldx
		for str in strlist:
			twidth = Qd.TextWidth(str, 0, len(str))
			if self.__units != UNIT_PXL:
				twidth = float(twidth) / w._rect[_WIDTH]
			list.append(('text', x, y, twidth, height, str))
			self._curpos = x + twidth, y
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		return oldx, oldy, maxx - oldx, newy - oldy + height - base
		
	# Draw a string centered in a box, breaking lines if necessary
	def centerstring(self, left, top, right, bottom, str):
		fontheight = self.fontheight()
		baseline = self.baseline()
		width = right - left
		height = bottom - top
		curlines = [str]
		if height >= 2*fontheight:
			import StringStuff
			curlines = StringStuff.calclines([str], self.strsize,
							 width)[0]
		nlines = len(curlines)
		needed = nlines * fontheight
		if nlines > 1 and needed > height:
			nlines = max(1, int(height / fontheight))
			curlines = curlines[:nlines]
			curlines[-1] = curlines[-1] + '...'
		x0 = (left + right) * 0.5	# x center of box
		y0 = (top + bottom) * 0.5	# y center of box
		y = y0 - nlines * fontheight * 0.5
		for i in range(nlines):
			str = string.strip(curlines[i])
			# Get font parameters:
			w = self.strsize(str)[0]	# Width of string
			while str and w > width:
				str = str[:-1]
				w = self.strsize(str)[0]
			x = x0 - 0.5*w
			y = y + baseline
			self.setpos(x, y)
			self.writestr(str)

	def _optimize(self, ignore = []):
		if type(ignore) is IntType:
			ignore = [ignore]
		entry = self._list[-1]
		x = []
		for i in range(len(entry)):
			if i not in ignore:
				z = entry[i]
				if type(z) is ListType:
					z = tuple(z)
				x.append(z)
		x = tuple(x)
		if self._optimdict.has_key(x):
			i = self._optimdict[x]
			del self._list[i]
			del self._optimdict[x]
			if i < self._clonestart:
				self._clonestart = self._clonestart - 1
			for key, val in self._optimdict.items():
				if val > i:
					self._optimdict[key] = val - 1
		self._optimdict[x] = len(self._list) - 1


	######################################
	# Animation experimental methods
	#

	# Update cmd with name from diff display list
	# we can get also update region from diff dl
	def update(self, name, diffdl):
		newcmd = diffdl.getcmd(name)
		if newcmd and self.__cmddict.has_key(name):
			ix = self.__cmddict[name]
			self._list[ix] = newcmd

	# Update cmd with name
	def updatecmd(self, name, newcmd):
		if self.__cmddict.has_key(name):
			ix = self.__cmddict[name]
			self._list[ix] = newcmd
	
	def getcmd(self, name):
		if self.__cmddict.has_key(name):
			ix = self.__cmddict[name]
			return self._list[ix]
		return None

	def knowcmd(self, name):
		self.__cmddict[name] = len(self._list)-1
				

	# Update background color
	def updatebgcolor(self, color):
		self._bgcolor = self._window._convert_color(color)

	#
	# End of animation experimental methods
	##########################################

class _Button:
	def __init__(self, dispobj, shape, coordinates, z, times, sensitive):
		self._dispobj = dispobj
		self._shape = shape
		self._coordinates = coordinates
		self._z = z
		self._times = times
		self._sensitive = sensitive

		buttons = dispobj._buttons
		for i in range(len(buttons)):
			if buttons[i]._z <= z:
				buttons.insert(i, self)
				break
		else:
			buttons.append(self)
##		self._hicolor = self._color = dispobj._fgcolor
##		self._width = self._hiwidth = dispobj._linewidth
##		if self._color != dispobj._bgcolor:
##			self._dispobj.drawbox(coordinates)

	# Destroy button
	def close(self):
		if self._dispobj is None:
			return
		self._dispobj._buttons.remove(self)
		self._dispobj = None

	# Returns true if it is closed
	def is_closed(self):
		return self._dispobj is None

	def setsensitive(self, sensitive):
		self._sensitive = sensitive

	# Increment height
	def hiwidth(self, width):
		pass

	# Set highlight color
	def hicolor(self, color):
		self._hicolor = color

	# Highlight box
	def highlight(self):
		pass

	# Unhighlight box
	def unhighlight(self):
		pass
		
	def _do_highlight(self):
		pass
		
	def _convert_point(self, point):
		return self._dispobj._window._convert_coordinates(point)

	def _get_button_region(self):
		"""Return our region, in global coordinates, if we are active"""
		# XXXX Only rectangulars for now
		if not self._sensitive:
			return None
		if not self._insidetemporal():
			return None
		rgn = Qd.NewRgn()
		if self._shape == 'rect':
			x0, y0 = self._convert_point(self._coordinates[0:2])
			x1, y1 = self._convert_point(self._coordinates[2:4])
			box = x0, y0, x1, y1
			Qd.RectRgn(rgn, box)
		elif self._shape == 'poly':
			Qd.OpenRgn()
			xl, yl = self._convert_point(self._coordinates[-2:])
			Qd.MoveTo(xl, yl)
			for i in range(0, len(self._coordinates), 2):
				x, y = self._convert_point(self._coordinates[i:i+2])
				Qd.LineTo(x, y)
			Qd.CloseRgn(rgn)
		elif self._shape == 'circle':
			print 'Circle not supported yet'
		elif self._shape == 'ellipse':
			# Note: rx/ry are width/height, not points
			x, y, rx, ry = self._dispobj._window._convert_coordinates(self._coordinates)
			Qd.OpenRgn()
			Qd.FrameOval((x-rx, y-ry, x+rx, y+ry))
			Qd.CloseRgn(rgn)
		else:
			print 'Invalid shape type', self._shape
		return rgn

	def _inside(self, x, y):
		if not self._sensitive:
			return 0
		if not self._insidetemporal():
			return 0		
		if self._shape == 'rect':
			return self._insideRect(x, y)
		elif self._shape == 'poly':
			return self._insidePoly(x, y)
		elif self._shape == 'circle':
			return self._insideCircle(x, y)
		elif self._shape == 'ellipse':
			return self._insideEllipse(x, y)

		print 'Internal error: invalid shape type'			
		return 0
		
	# Returns true if the time is inside the temporal space
	def _insidetemporal(self):
		if self._times:
			import time
			curtime = time.time() - self._dispobj.starttime
			t0, t1 = self._times
			if (not t0 or t0 <= curtime) and \
			   (not t1 or curtime < t1):
				return 1
			return 0
		return 1
	
	# Returns true if the point is inside the box	
	def _insideRect(self, x, y):
		# for now
		bx1, by1, bx2, by2 = self._coordinates
		return CheckInsideArea.insideRect(x, y, bx1, by1, bx2, by2)

	# Warning: this method is called by the window core management every time that you move the mouse
	# in order to change to graphic cursor mouse when the cursor is inside the area. And for each
	# area that you have defined in window.
	# For now, a not very efficient algo is implemented, but it should be better to use a system
	# call later if possible
	# Returns true if the point is inside the polygon	
	def _insidePoly(self, x, y):
		return CheckInsideArea.insidePoly(x, y, self._coordinates)
		

	# Returns true if the point is inside the box	
	def _insideCircle(self, x, y):
		# for now
		cx, cy, rd = self._coordinates
		wx, wy, ww, wh = self._dispobj._window.getgeometry(UNIT_PXL)
		return CheckInsideArea.insideCircle(x*ww, y*wh, cx*ww, cy*wh, rd*ww)

	# Returns true if the point is inside the ellipse	
	def _insideEllipse(self, x, y):
		# for now
		cx, cy, rdx, rdy = self._coordinates
		wx, wy, ww, wh = self._dispobj._window.getgeometry(UNIT_PXL)
		return CheckInsideArea.insideEllipse(x*ww, y*wh, cx*ww, cy*wh, rdx*ww, rdy*wh)

	def updatecoordinates(self, coords):
		if self.is_closed(): return
		# XXXX This is wrong. But it sort-of works if image and region are the
		# same size, and if the user has specified the anchor in pixels, and if the
		# anchor is a square.
		self._coordinates = self._dispobj._window._pxl2rel(coords)
		self._dispobj._window._buttonschanged()

