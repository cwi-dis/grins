import Win
import Qd
import Res
import string
import QuickDraw
from types import *
import struct
import math

#
# Stuff needed from other mw_ modules:
#
from mw_globals import error
from mw_globals import TRUE, FALSE
from mw_globals import _X, _Y, _WIDTH, _HEIGHT
from mw_globals import ARR_LENGTH, ARR_SLANT, ARR_HALFWIDTH, SIZE_3DBORDER
import mw_fonts

# Special round function (XXXX needs work).
def _roundi(x):
	if x < 0:
		return _roundi(x + 1024) - 1024
	return int(x + 0.5)
	
def _colormix((r1, g1, b1), (r2, g2, b2)):
	return (r1+r2)/2, (g1+g2)/2, (b1+b2)/2

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
		
	def close(self):
		if self._window is None:
			return
		win = self._window
		for b in self._buttons[:]:
			b.close()
		win._displists.remove(self)
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			if self._buttons:
				win._buttonschanged()
			if win._transparent == -1 and win._parent:
				win._parent._clipchanged()
			if win._wid:
				Qd.SetPort(win._wid)
				Win.InvalRect(win.qdrect())
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
		new._font = self._font
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
			Qd.UnionRgn(rgn, brgn, rgn)
			Qd.DisposeRgn(brgn)
		return rgn

	def render(self):
		#
		# On the mac, we can only render after a full setup.
		# Hence, we schedule a redraw only
		#
		window = self._window
		self._rendered = 1
		# XXXX buttons?
		Qd.SetPort(window._wid)
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
		Qd.SetPort(window._wid)
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
			Win.InvalRect(window.qdrect())
		
		window._active_displist = self
		if self._buttons:
			window._buttonschanged()

	
	def _can_render_now(self):
		"""Return true if we can do the render now, in stead of
		scheduling the update event"""
		##return 0
		# First check that no update events are pending.
		window = self._window
		rgn = Qd.NewRgn()
		window._wid.GetWindowUpdateRgn(rgn)
		ok = Qd.EmptyRgn(rgn)
		if ok:
			ok = window._is_on_top()
		Qd.DisposeRgn(rgn)
		return ok
		
	def _render(self, clonestart=0):
		self._really_rendered = 1
		self._window._active_displist = self
		Qd.RGBBackColor(self._bgcolor)
		Qd.RGBForeColor(self._fgcolor)
		if clonestart:
			list = self._list[clonestart:]
		else:
			if self._window._transparent <= 0:
				Qd.EraseRect(self._window.qdrect())
			list = self._list
		for i in list:
			self._render_one(i)
			
	def _render_one(self, entry):
		cmd = entry[0]
		window = self._window
		wid = window._wid
		xscrolloffset, yscrolloffset = window._scrolloffset()
		
		if cmd == 'clear':
			Qd.EraseRect(window.qdrect())
		elif cmd == 'fg':
			Qd.RGBForeColor(entry[1])
		elif cmd == 'font':
			entry[1]._setfont(wid)
		elif cmd == 'text':
			Qd.MoveTo(entry[1]+xscrolloffset, entry[2]+yscrolloffset)
			 # XXXX Incorrect for long strings:
			Qd.DrawString(entry[3])
		elif cmd == 'image':
			mask, image, srcx, srcy, dstx, dsty, w, h = entry[1:]
			dstx, dsty = dstx+xscrolloffset, dsty+yscrolloffset
			srcrect = srcx, srcy, srcx+w, srcy+h
			dstrect = dstx, dsty, dstx+w, dsty+h
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBBackColor((0xffff, 0xffff, 0xffff))
			Qd.RGBForeColor((0, 0, 0))
			if mask:
				Qd.CopyMask(image[0], mask[0],
					    wid.GetWindowPort().portBits,
					    srcrect, srcrect, dstrect)
			else:
				Qd.CopyBits(image[0],
				      wid.GetWindowPort().portBits,
				      srcrect, dstrect,
				      QuickDraw.srcCopy+QuickDraw.ditherCopy,
				      None)
			Qd.RGBBackColor(self._bgcolor)
			Qd.RGBForeColor(fgcolor)
		elif cmd == 'line':
			color = entry[1]
			points = entry[2]
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(color)
			x, y = points[0]
			Qd.MoveTo(x+xscrolloffset, y+yscrolloffset)
			for np in points[1:]:
				x, y = np
				Qd.LineTo(x+xscrolloffset, y+yscrolloffset)
			Qd.RGBForeColor(fgcolor)
		elif cmd == '3dhline':
			color1, color2, x0, x1, y = entry[1:]
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(color1)
			Qd.MoveTo(x0+xscrolloffset, y+yscrolloffset)
			Qd.LineTo(x1+xscrolloffset, y+yscrolloffset)
			Qd.RGBForeColor(color2)
			Qd.MoveTo(x0+xscrolloffset, y+yscrolloffset+1)
			Qd.LineTo(x1+xscrolloffset, y+yscrolloffset+1)
			Qd.RGBForeColor(fgcolor)
		elif cmd == 'box':
			x, y, w, h = entry[1]
			x, y = x+xscrolloffset, y+yscrolloffset
			Qd.FrameRect((x, y, x+w, y+h))
		elif cmd == 'fbox':
			color = entry[1]
			x, y, w, h = entry[2]
			x, y = x+xscrolloffset, y+yscrolloffset
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(color)
			Qd.PaintRect((x, y, x+w, y+h))
			Qd.RGBForeColor(fgcolor)
		elif cmd == 'linewidth':
			Qd.PenSize(entry[1], entry[1])
		elif cmd == 'fpolygon':
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(entry[1])
			polyhandle = self._polyhandle(entry[2])
			Qd.PaintPoly(polyhandle)
			Qd.RGBForeColor(fgcolor)
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
			# Save old foreground color
			fgcolor = wid.GetWindowPort().rgbFgColor
			# draw left side
			Qd.RGBForeColor(cl)
			polyhandle = self._polyhandle([(l, t), (l3, t3), (l3, b3), (l, b)])
			Qd.PaintPoly(polyhandle)
			# draw top side
			Qd.RGBForeColor(ct)
			polyhandle = self._polyhandle([(l, t), (r, t), (r3, t3), (l3, t3)])
			Qd.PaintPoly(polyhandle)
			# draw right side
			Qd.RGBForeColor(cr)
			polyhandle = self._polyhandle([(r3, t3), (r, t), (r, b), (r3, b3)])
			Qd.PaintPoly(polyhandle)
			# draw bottom side
			Qd.RGBForeColor(cb)
			polyhandle = self._polyhandle([(l3, b3), (r3, b3), (r, b), (l, b)])
			Qd.PaintPoly(polyhandle)
			# draw topleft
			Qd.RGBForeColor(clt)
			Qd.PaintRect((l+xscrolloffset, t+yscrolloffset, l3+xscrolloffset, t3+yscrolloffset))
			# draw topright
			Qd.RGBForeColor(ctr)
			Qd.PaintRect((r3+xscrolloffset, t+yscrolloffset, r+xscrolloffset, t3+yscrolloffset))
			# draw botright
			Qd.RGBForeColor(crb)
			Qd.PaintRect((r3+xscrolloffset, b3+yscrolloffset, r+xscrolloffset, b+yscrolloffset))
			# draw leftbot
			Qd.RGBForeColor(cbl)
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
			
			Qd.RGBForeColor(fgcolor)
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
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(entry[1])
			polyhandle = self._polyhandle([(x, y + h/2),
					(x + w/2, y),
					(x + w, y + h/2),
					(x + w/2, y + h),
					(x, y + h/2)])
			Qd.PaintPoly(polyhandle)
			Qd.RGBForeColor(fgcolor)
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
		elif cmd == 'arrow':
			color = entry[1]
			points = entry[2]
			fgcolor = wid.GetWindowPort().rgbFgColor
			Qd.RGBForeColor(color)
			x0, y0, x1, y1 = points
			x0, y0 = x0+xscrolloffset, y0+yscrolloffset
			x1, y1 = x1+xscrolloffset, y1+yscrolloffset

			Qd.MoveTo(x0, y0)
			Qd.LineTo(x1, y1)
			polyhandle = self._polyhandle(entry[3])
			Qd.PaintPoly(polyhandle)
			Qd.RGBForeColor(fgcolor)
		else:
			raise 'Unknown displaylist command', cmd
						
	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		color = self._window._convert_color(color)
		self._list.append('fg', color)
		self._fgcolor = color


	def newbutton(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return _Button(self, coordinates)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0,
				    center = 1, coordinates = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		win = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       win._prepare_image(file, crop, scale, center, coordinates)
		self._list.append('image', mask, image, src_x, src_y,
				  dest_x, dest_y, width, height)
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
			p.append(x,y)
			xvalues.append(x)
			yvalues.append(y)
		self._list.append('line', color, p)
##		self._update_bbox(min(xvalues), min(yvalues),
##				  max(xvalues), max(yvalues))

	def draw3dhline(self, color1, color2, x1, x2, y):
		w = self._window
		color1 = w._convert_color(color1)
		color2 = w._convert_color(color2)
		x1, y = w._convert_coordinates((x1, y))
		x2, dummy = w._convert_coordinates((x2, y))
		self._list.append('3dhline', color1, color2, x1, x2, y)

	def drawbox(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._window._convert_coordinates(coordinates)
		self._list.append('box', (x, y, w, h))
		self._optimize()
##		self._update_bbox(x, y, x+w, y+h)

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._window._convert_coordinates(coordinates)
		self._list.append('fbox', self._window._convert_color(color),
				(x, y, w, h))
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
			p.append(x, y)
			xvalues.append(x)
			yvalues.append(y)
		self._list.append('fpolygon', color, p)
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
		self._list.append('3dbox', (cl, ct, cr, cb), coordinates)
		self._optimize(1)
		x, y, w, h = coordinates
##		self._update_bbox(x, y, x+w, y+h)

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		self._list.append('diamond', coordinates)
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
		self._list.append('fdiamond', color, coordinates)
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
		self._list.append('3ddiamond', (cl, ct, cr, cb), coordinates)
		self._optimize(1)
		x, y, w, h = coordinates
##		self._update_bbox(x, y, x+w, y+h)

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
			points.append(_roundi(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
				      _roundi(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos))
			points.append(_roundi(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
				      _roundi(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos))
			window.arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		self._list.append('arrow', color, (nsx, nsy, ndx, ndy), points)
		self._optimize(1)
##		self._update_bbox(nsx, nsy, ndx, ndy)
		
	def _polyhandle(self, pointlist):
		"""Return poligon structure"""
		# XXXX Note: This leaks handles like anything!!
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
		return Res.Resource(data)

	def get3dbordersize(self):
		return self._window._pxl2rel((0,0,SIZE_3DBORDER,SIZE_3DBORDER))[2:4]
		
	def usefont(self, fontobj):
		if fontobj != self._font:
			self._font = fontobj
			self._font._initparams(self._window._wid)
			self._list.append('font', fontobj)
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
		width, height = self._font.strsizePXL(self._window._wid, str)
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
		if self._font._checkfont(w._wid):
			old_fontinfo = mw_fonts._savefontinfo(w._wid)
		self._font._setfont(w._wid)
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
			twidth = Qd.TextWidth(str, 0, len(str))
			self._curpos = x + float(twidth) / w._rect[_WIDTH], y
##			self._update_bbox(x0, y0, x0+twidth,
##					  y0+int(height/self._window._vfactor))
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
##		if old_fontinfo:
##			mw_fonts._restorefontinfo(w._wid, old_fontinfo)
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
##		self._clonebboxes.append(minx, miny, maxx, maxy)
		
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

class _Button:
	def __init__(self, dispobj, coordinates, z=0):
		self._coordinates = coordinates
		self._dispobj = dispobj
		self._z = z
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
		return (bx <= x <= bx+bw and by <= y <= by+bh)
		
	def _get_button_region(self):
		"""Return our region, in global coordinates"""
		x0, y0, w, h = self._dispobj._window._convert_coordinates(self._coordinates) # XXXXSCROLL
		x1, y1 = x0+w, y0+h
		x0, y0 = Qd.LocalToGlobal((x0, y0))
		x1, y1 = Qd.LocalToGlobal((x1, y1))
		box = x0, y0, x1, y1
		rgn = Qd.NewRgn()
		Qd.RectRgn(rgn, box)
		return rgn
		
