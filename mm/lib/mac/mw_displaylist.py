import Win
import Qd
import Res
import Icn
import App
import Appearance
import string
import QuickDraw
from types import *
import struct
import math
import time

#
# Stuff needed from other mw_ modules:
#
from mw_globals import error
from mw_globals import TRUE, FALSE
from mw_globals import _X, _Y, _WIDTH, _HEIGHT, ICONSIZE_PXL
from mw_globals import ARR_LENGTH, ARR_SLANT, ARR_HALFWIDTH, SIZE_3DBORDER
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
	'bandwidthgood': mw_resources.ID_ICON_BANDWIDTH_OK,
	'bandwidthbad': mw_resources.ID_ICON_BANDWIDTH_ERROR,
	'error': mw_resources.ID_ICON_ERROR,
	'linksrc': mw_resources.ID_ICON_LINKSRC,
	'linkdst': mw_resources.ID_ICON_LINKDST,
	'linksrcdst': mw_resources.ID_ICON_LINKSRCDST,
}

def _get_icon(which):
	if not _icons:
		for name, resid in _icon_ids.items():
			_icons[name] = Icn.GetCIcon(resid)
		_icons[''] = None
	return _icons[which]
	

class _DisplayList:
	def __init__(self, window, bgcolor):
		self.starttime = 0
		self._window = window
		window._displists.append(self)
		self._bgcolor = bgcolor
		self._fgcolor = window._fgcolor
		self._linewidth = 1
		self._buttons = []
		self._list = []
		self._rendered = 0
		if self._window._transparent <= 0:
			self._list.append(('clear',))
		self._optimdict = {}
		self._cloneof = None
		self._clonestart = 0
		self._rendered = FALSE
		self._font = None
		self._old_fontinfo = None
##		self._clonebboxes = []
		self._really_rendered = FALSE	# Set to true after the first real redraw
		
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
		new = _DisplayList(w, self._bgcolor)
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
		Qd.RGBForeColor(fgcolor)
		
	def _setbgcolor(self, bgcolor):
##		if bgcolor == 'theme_background':
##			depth=16 # XXX
##			App.SetThemeBackground(Appearance.kThemeBrushDocumentWindowBackground, depth, 1)
##			return
		Qd.RGBBackColor(bgcolor)
		
	def _restorecolors(self):
		self._setfgcolor(self._fgcolor)
		self._setbgcolor(self._bgcolor)

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
		window._mac_setwin() # XXXX
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
		window._mac_setwin() # XXXX
		if render_now:
			if not window._clip:
				window._mkclip()
			saveclip = Qd.NewRgn()
			Qd.GetClip(saveclip)
			Qd.SetClip(window._clip)
			self._render(clonestart)
			Qd.SetClip(saveclip)
			Qd.DisposeRgn(saveclip)
		else:
			window._mac_invalwin()
		
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
		rgn = Qd.NewRgn()
		window._onscreen_wid.GetWindowUpdateRgn(rgn)
		ok = Qd.EmptyRgn(rgn)
		# Next check that we're topmost
		if ok:
			ok = window._is_on_top()
		# Finally check that we're not in a transition
		if ok:
			ok = (window._onscreen_wid == window._drawing_wid)
		Qd.DisposeRgn(rgn)
		return ok
		
	def _render(self, clonestart=0):
		self._really_rendered = 1
		window = self._window
		grafport = window._mac_getoswindowport()
		window._active_displist = self
		self._restorecolors()
		if clonestart:
			list = self._list[clonestart:]
		else:
			if window._transparent <= 0:
				# XXXX Or should we erase the onscreen window?
				Qd.EraseRect(window.qdrect())
			list = self._list
		for entry in list:
			self._render_one(entry, window, grafport)
			
	def _render_one(self, entry, window, grafport):
		cmd = entry[0]
		xscrolloffset, yscrolloffset = window._scrolloffset()
		
		if cmd == 'clear':
			Qd.EraseRect(window.qdrect())
		elif cmd == 'fg':
			Qd.RGBForeColor(entry[1])
		elif cmd == 'font':
			entry[1]._setfont(grafport)
		elif cmd == 'text':
			Qd.MoveTo(entry[1]+xscrolloffset, entry[2]+yscrolloffset)
			 # XXXX Incorrect for long strings:
			Qd.DrawText(entry[3], 0, len(entry[3]))
		elif cmd == 'icon':
			if entry[2] != None:
				x, y, w, h = entry[1]
				x = x+xscrolloffset
				y = y+yscrolloffset
				Icn.PlotCIcon((x, y, x+w, y+h), entry[2])
		elif cmd == 'image':
			mask, image, srcx, srcy, dstx, dsty, w, h = entry[1:]
			dstx, dsty = dstx+xscrolloffset, dsty+yscrolloffset
			srcrect = srcx, srcy, srcx+w, srcy+h
			dstrect = dstx, dsty, dstx+w, dsty+h
			self._setblackwhitecolors()
			if mask:
				Qd.CopyMask(image[0], mask[0],
					    grafport.portBits,
					    srcrect, srcrect, dstrect)
			else:
				Qd.CopyBits(image[0],
				      grafport.portBits,
				      srcrect, dstrect,
				      QuickDraw.srcCopy+QuickDraw.ditherCopy,
				      None)
			self._restorecolors()
		elif cmd == 'line':
			color = entry[1]
			points = entry[2]
			self._setfgcolor(color)
			x, y = points[0]
			Qd.MoveTo(x+xscrolloffset, y+yscrolloffset)
			for np in points[1:]:
				x, y = np
				Qd.LineTo(x+xscrolloffset, y+yscrolloffset)
			self._restorecolors()
		elif cmd == '3dhline':
			color1, color2, x0, x1, y = entry[1:]
			fgcolor = grafport.rgbFgColor
			self._setfgcolor(color1)
			Qd.MoveTo(x0+xscrolloffset, y+yscrolloffset)
			Qd.LineTo(x1+xscrolloffset, y+yscrolloffset)
			self._setfgcolor(color2)
			Qd.MoveTo(x0+xscrolloffset, y+yscrolloffset+1)
			Qd.LineTo(x1+xscrolloffset, y+yscrolloffset+1)
			self._setfgcolor(fgcolor)
			self._restorecolors()
		elif cmd == 'box':
			x, y, w, h = entry[1]
			x, y = x+xscrolloffset, y+yscrolloffset
			Qd.FrameRect((x, y, x+w, y+h))
		elif cmd == 'fbox':
			color = entry[1]
			x, y, w, h = entry[2]
			x, y = x+xscrolloffset, y+yscrolloffset
			self._setfgcolor(color)
			Qd.PaintRect((x, y, x+w, y+h))
			self._restorecolors()
		elif cmd == 'linewidth':
			Qd.PenSize(entry[1], entry[1])
		elif cmd == 'fpolygon':
			self._setfgcolor(entry[1])
			polyhandle = self._polyhandle(entry[2])
			Qd.PaintPoly(polyhandle)
			self._restorecolors()
		elif cmd == '3dbox':
			cl, ct, cr, cb = entry[1]
			clt = _colormix(cl, ct)
			ctr = _colormix(ct, cr)
			crb = _colormix(cr, cb)
			cbl = _colormix(cb, cl)
			l, t, w, h = entry[2]
			r, b = l + w, t + h
##			print '3Dbox', (l, t, r, b) # DBG
##			print 'window', window.qdrect() # DBG
			# l, r, t, b are the corners
			l3 = l + SIZE_3DBORDER
			t3 = t + SIZE_3DBORDER
			r3 = r - SIZE_3DBORDER
			b3 = b - SIZE_3DBORDER
			# draw left side
			self._setfgcolor(cl)
			polyhandle = self._polyhandle([(l, t), (l3, t3), (l3, b3), (l, b)])
			Qd.PaintPoly(polyhandle)
			# draw top side
			self._setfgcolor(ct)
			polyhandle = self._polyhandle([(l, t), (r, t), (r3, t3), (l3, t3)])
			Qd.PaintPoly(polyhandle)
			# draw right side
			self._setfgcolor(cr)
			polyhandle = self._polyhandle([(r3, t3), (r, t), (r, b), (r3, b3)])
			Qd.PaintPoly(polyhandle)
			# draw bottom side
			self._setfgcolor(cb)
			polyhandle = self._polyhandle([(l3, b3), (r3, b3), (r, b), (l, b)])
			Qd.PaintPoly(polyhandle)
			# draw topleft
			self._setfgcolor(clt)
			Qd.PaintRect((l+xscrolloffset, t+yscrolloffset, l3+xscrolloffset, t3+yscrolloffset))
			# draw topright
			self._setfgcolor(ctr)
			Qd.PaintRect((r3+xscrolloffset, t+yscrolloffset, r+xscrolloffset, t3+yscrolloffset))
			# draw botright
			self._setfgcolor(crb)
			Qd.PaintRect((r3+xscrolloffset, b3+yscrolloffset, r+xscrolloffset, b+yscrolloffset))
			# draw leftbot
			self._setfgcolor(cbl)
			Qd.PaintRect((l+xscrolloffset, b3+yscrolloffset, l3+xscrolloffset, b+yscrolloffset))
##			l = l+1
##			t = t+1
##			r = r-1
##			b = b-1
##			l1 = l - 1
##			t1 = t - 1
##			r1 = r
##			b1 = b
##			ll = l + 2
##			tt = t + 2
##			rr = r - 2
##			bb = b - 3


##			Qd.RGBForeColor(cl)
##			polyhandle = self._polyhandle([(l1, t1), (ll, tt), (ll, bb), (l1, b1)])
##			Qd.PaintPoly(polyhandle)
			
##			Qd.RGBForeColor(ct)
##			polyhandle = self._polyhandle([(l1, t1), (r1, t1), (rr, tt), (ll, tt)])
##			Qd.PaintPoly(polyhandle)
			
##			Qd.RGBForeColor(cr)
##			polyhandle = self._polyhandle([(r1, t1), (r1, b1), (rr, bb), (rr, tt)])
##			Qd.PaintPoly(polyhandle)
			
##			Qd.RGBForeColor(cb)
##			polyhandle = self._polyhandle([(l1, b1), (ll, bb), (rr, bb), (r1, b1)])
##			Qd.PaintPoly(polyhandle)
			
			self._restorecolors()
		elif cmd == 'diamond':
			x, y, w, h = entry[1]
			x, y = x+xscrolloffset, y+yscrolloffset
			Qd.MoveTo(x, y + h/2)
			Qd.LineTo(x + w/2, y)
			Qd.LineTo(x + w, y + h/2)
			Qd.LineTo(x + w/2, y + h)
			Qd.LineTo(x, y + h/2)
		elif cmd == 'fdiamond':
			x, y, w, h = entry[2]
			self._setfgcolor(entry[1])
			polyhandle = self._polyhandle([(x, y + h/2),
					(x + w/2, y),
					(x + w, y + h/2),
					(x + w/2, y + h),
					(x, y + h/2)])
			Qd.PaintPoly(polyhandle)
			self._restorecolors()
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


			self._setfgcolor(cl)
			polyhandle = self._polyhandle([(l, y), (x, t), (x, tt), (ll, y)])
			Qd.PaintPoly(polyhandle)
			
			self._setfgcolor(ct)
			polyhandle = self._polyhandle([(x, t), (r, y), (rr, y), (x, tt)])
			Qd.PaintPoly(polyhandle)
			
			self._setfgcolor(cr)
			polyhandle = self._polyhandle([(r, y), (x, b), (x, bb), (rr, y)])
			Qd.PaintPoly(polyhandle)
			
			self._setfgcolor(cb)
			polyhandle = self._polyhandle([(l, y), (ll, y), (x, bb), (x, b)])
			Qd.PaintPoly(polyhandle)
			
			self._restorecolors()
		elif cmd == 'arrow':
			color = entry[1]
			points = entry[2]
			self._setfgcolor(color)
			x0, y0, x1, y1 = points
			x0, y0 = x0+xscrolloffset, y0+yscrolloffset
			x1, y1 = x1+xscrolloffset, y1+yscrolloffset

			Qd.MoveTo(x0, y0)
			Qd.LineTo(x1, y1)
			polyhandle = self._polyhandle(entry[3])
			Qd.PaintPoly(polyhandle)
			self._restorecolors()
		else:
			raise 'Unknown displaylist command', cmd
						
	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		color = self._window._convert_color(color)
		self._list.append(('fg', color))
		self._fgcolor = color


	def newbutton(self, coordinates, z = 0, times = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return _Button(self, coordinates, z, times)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0,
				    center = 1, coordinates = None,
				    clip = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		win = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       win._prepare_image(file, crop, scale, center, coordinates)
		self._list.append(('image', mask, image, src_x, src_y,
				   dest_x, dest_y, width, height))
		self._optimize(2)
##		self._update_bbox(dest_x, dest_y, dest_x+width, dest_y+height)
		x, y, w, h = win._rect
		wf, hf = win._scrollsizefactors()
		w, h = w*wf, h*hf
		return float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		xvalues = []
		yvalues = []
		for point in points:
			x, y = w._convert_coordinates(point)
			p.append((x,y))
			xvalues.append(x)
			yvalues.append(y)
		self._list.append(('line', color, p))
##		self._update_bbox(min(xvalues), min(yvalues),
##				  max(xvalues), max(yvalues))

	def draw3dhline(self, color1, color2, x1, x2, y):
		w = self._window
		color1 = w._convert_color(color1)
		color2 = w._convert_color(color2)
		x1, y = w._convert_coordinates((x1, y))
		x2, dummy = w._convert_coordinates((x2, y))
		self._list.append(('3dhline', color1, color2, x1, x2, y))

	def drawbox(self, coordinates, clip = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._window._convert_coordinates(coordinates)
		self._list.append(('box', (x, y, w, h)))
		self._optimize()
##		self._update_bbox(x, y, x+w, y+h)

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._window._convert_coordinates(coordinates)
		self._list.append(('fbox', self._window._convert_color(color),
				   (x, y, w, h)))
		self._optimize(1)
##		self._update_bbox(x, y, x+w, y+h)

	def drawmarker(self, color, coordinates):
		pass # XXXX To be implemented

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
			p.append((x, y))
			xvalues.append(x)
			yvalues.append(y)
		self._list.append(('fpolygon', color, p))
		self._optimize(1)
##		self._update_bbox(min(xvalues), min(yvalues), max(xvalues), max(yvalues))

	def draw3dbox(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
##		print '3DBOX orig', coordinates
		coordinates = window._convert_coordinates(coordinates)
##		print 'conv', coordinates
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append(('3dbox', (cl, ct, cr, cb), coordinates))
		self._optimize(1)
		x, y, w, h = coordinates
##		self._update_bbox(x, y, x+w, y+h)

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		self._list.append(('diamond', coordinates))
		self._optimize()
		x, y, w, h = coordinates
##		self._update_bbox(x, y, x+w, y+h)

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
		self._list.append(('fdiamond', color, coordinates))
		self._optimize(1)
		x, y, w, h = coordinates
##		self._update_bbox(x, y, x+w, y+h)


	def draw3ddiamond(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		coordinates = window._convert_coordinates(coordinates)
		self._list.append(('3ddiamond', (cl, ct, cr, cb), coordinates))
		self._optimize(1)
		x, y, w, h = coordinates
##		self._update_bbox(x, y, x+w, y+h)

	def drawicon(self, coordinates, icon):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		x, y, w, h = window._convert_coordinates(coordinates)
		# Keep it square, top it off, center it
		size = min(w, h, ICONSIZE_PXL)
		xextra = w-size
		yextra = h-size
		if xextra > 0:
			x = x + xextra/2
		if yextra > 0:
			y = y + yextra/2
		data = _get_icon(icon)
		self._list.append(('icon', (x, y, size, size), data))
		self._optimize(2)

		
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
			points.append((_roundi(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
				       _roundi(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos)))
			points.append((_roundi(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
				       _roundi(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos)))
			window.arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		self._list.append(('arrow', color, (nsx, nsy, ndx, ndy), points))
		self._optimize(1)
##		self._update_bbox(nsx, nsy, ndx, ndy)
		
	def _polyhandle(self, pointlist):
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
		# Create structure head
		size = len(pointlist)*4 + 10
		data = struct.pack("hhhhh", size, miny+yscrolloffset, minx+xscrolloffset, 
				maxy+yscrolloffset, maxx+xscrolloffset)
##		self._update_bbox(minx, miny, maxx, maxy)
		for x, y in pointlist:
			data = data + struct.pack("hh", y+yscrolloffset, x+xscrolloffset)
		return Res.Handle(data)

	def get3dbordersize(self):
		return self._window._pxl2rel((0,0,SIZE_3DBORDER,SIZE_3DBORDER))[2:4]
		
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
		return self._window._pxl2rel((0,0,0,baseline))[3]

	def __fontheight(self):
		fontheight = self._font.fontheightPXL()
		return self._window._pxl2rel((0,0,0,fontheight))[3]

	def __pointsize(self):
		return self._font.pointsize()
		
	def baseline(self):
		return self.__font_size_cache[0]

	def fontheight(self):
		return self.__font_size_cache[1]

	def pointsize(self):
		return self.__font_size_cache[2]

	def strsize(self, str):
		# XXXX Or on the _onscreen_wid??
		width, height = self._font.strsizePXL(str, port=self._window._mac_getoswindowport())
		return self._window._pxl2rel((0,0,width,height))[2:4]

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
			x0, y0 = w._convert_coordinates((x, y))
			list.append(('text', x0, y0, str))
			twidth = Qd.TextWidth(str, 0, len(str))
			self._curpos = x + float(twidth) / w._rect[_WIDTH], y
##			self._update_bbox(x0, y0, x0+twidth,
##					  y0+int(height/self._window._vfactor))
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

##	def _update_bbox(self, minx, miny, maxx, maxy):
##		assert type(minx) == type(maxx) == \
##		       type(miny) == type(maxy) == type(1)
##		if minx > maxx:
##			minx, maxx = maxx, minx
##		if miny > maxy:
##			miny, maxy = maxy, miny
##		self._clonebboxes.append((minx, miny, maxx, maxy))
		
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
##		try:
##			i = self._optimdict[x]
##		except KeyError:
##			pass
##		else:
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
		self._bgcolor = color

	#
	# End of animation experimental methods
	##########################################

class _Button:
	def __init__(self, dispobj, coordinates, z=0, times=None):
		self._coordinates = coordinates
		self._dispobj = dispobj
		self._z = z
		self._times = times
		buttons = dispobj._buttons
		for i in range(len(buttons)):
			if buttons[i]._z <= z:
				buttons.insert(i, self)
				break
		else:
			buttons.append(self)
		self._hicolor = self._color = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		if self._color == dispobj._bgcolor:
			return
		self._dispobj.drawbox(coordinates)

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
		
	def _inside(self, x, y):
		bx, by, bw, bh = self._coordinates
		if bx <= x < bx+bw and by <= y < by+bh:
			if self._times:
				curtime = time.time() - self._dispobj.starttime
				t0, t1 = self._times
				if (not t0 or t0 <= curtime) and \
				   (not t1 or curtime < t1):
					return 1
				return 0
			return 1
		return 0
		
	def _get_button_region(self):
		"""Return our region, in global coordinates, if we are active"""
##		print 'getbuttonregion', self._dispobj._window._convert_coordinates(self._coordinates), self._times, time.time()-self._dispobj.starttime #DBG
		if self._times:
			curtime = time.time() - self._dispobj.starttime
			# Workaround for the fact that timers seem to fire early, some times:
			curtime = curtime + 0.05
			t0, t1 = self._times
			if curtime < t0 or (t1 and curtime >= t1):
				return None
		x0, y0, w, h = self._dispobj._window._convert_coordinates(self._coordinates)
		x1, y1 = x0+w, y0+h
		x0, y0 = Qd.LocalToGlobal((x0, y0))
		x1, y1 = Qd.LocalToGlobal((x1, y1))
		box = x0, y0, x1, y1
		rgn = Qd.NewRgn()
		Qd.RectRgn(rgn, box)
		return rgn
		
	######################################
	# Animation experimental methods

	def updatecoordinates(self, coords):
		print 'button.updatecoords',coords

	# End of animation experimental methods
	##########################################
