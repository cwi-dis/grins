__version__ = "$Id$"

import Xlib, X
import string, math
from types import ListType
RegionType = type(Xlib.CreateRegion())
from XTopLevel import toplevel
from XConstants import *
from XConstants import _WIDTH
from XFont import findfont
from XButton import _Button
from splash import roundi

class _DisplayList:
	def __init__(self, window, bgcolor):
		self._window = window
		window._displists.append(self)
		self._buttons = []
		self._buttonregion = Xlib.CreateRegion()
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._linewidth = 1
		self._gcattr = {'foreground': window._convert_color(self._fgcolor),
				'background': window._convert_color(bgcolor),
				'line_width': 1}
		self._list = []
		if window._transparent <= 0:
			self._list.append(('clear',
					self._window._convert_color(bgcolor)))
		self._optimdict = {}
		self._cloneof = None
		self._clonestart = 0
		self._rendered = FALSE
		self._font = None
		self._imagemask = None

	def close(self):
		win = self._window
		if win is None:
			return
		for b in self._buttons[:]:
			b.close()
		win._displists.remove(self)
		self._window = None
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			win._buttonregion = Xlib.CreateRegion()
			r = win._region
			if win._transparent == -1 and win._parent is not None and \
			   win._topwindow is not win:
				win._parent._mkclip()
				win._parent._do_expose(r)
			else:
				win._do_expose(r)
			if win._pixmap is not None:
				x, y, w, h = win._rect
				win._gc.SetRegion(win._region)
				win._pixmap.CopyArea(win._form, win._gc,
						     x, y, w, h, x, y)
			if win._transparent == 0:
				w = win._parent
				while w is not None and w is not toplevel:
					w._buttonregion.SubtractRegion(
						win._clip)
					w = w._parent
			win._topwindow._setmotionhandler()
		del self._cloneof
		del self._optimdict
		del self._list
		del self._buttons
		del self._font
		del self._imagemask
		del self._buttonregion

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
			new._imagemask = self._imagemask
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def render(self):
		window = self._window
		if window._transparent == -1 and window._active_displist is None:
			window._active_displist = self
			window._parent._mkclip()
			window._active_displist = None
		for b in self._buttons:
			b._highlighted = 0
		region = window._clip
		# draw our bit
		self._render(region)
		# now draw transparent subwindows
		windows = window._subwindows[:]
		windows.reverse()
		for w in windows:
			if w._transparent and w._active_displist:
				w._do_expose(region, 1)
		# now draw transparent windows that lie on top of us
		if window._topwindow is not window:
			i = window._parent._subwindows.index(window)
			windows = window._parent._subwindows[:i]
			windows.reverse()
			for w in windows:
				if w._transparent and w._active_displist:
					w._do_expose(region, 1)
		# finally, re-highlight window
		if window._showing:
			window.showwindow(window._showing)
		if window._pixmap is not None:
			x, y, width, height = window._rect
			window._gc.SetRegion(window._clip)
			window._pixmap.CopyArea(window._form, window._gc,
						x, y, width, height, x, y)
		window._buttonregion = bregion = Xlib.CreateRegion()
		bregion.UnionRegion(self._buttonregion)
		bregion.IntersectRegion(window._clip)
		w = window._parent
		while w is not None and w is not toplevel:
			w._buttonregion.SubtractRegion(window._clip)
			w._buttonregion.UnionRegion(bregion)
			w = w._parent
		window._topwindow._setmotionhandler()
		toplevel._main.UpdateDisplay()

	def _render(self, region):
		self._rendered = TRUE
		w = self._window
		clonestart = self._clonestart
		if not self._cloneof or \
		   self._cloneof is not w._active_displist:
			clonestart = 0
		if w._active_displist and self is not w._active_displist and \
		   w._transparent and clonestart == 0:
			w._active_displist = None
			w._do_expose(region)
		gc = w._gc
		gc.ChangeGC(self._gcattr)
		gc.SetRegion(region)
		if clonestart == 0 and self._imagemask:
			# restrict to drawing outside the image
			if type(self._imagemask) is RegionType:
				r = Xlib.CreateRegion()
				r.UnionRegion(region)
				r.SubtractRegion(self._imagemask)
				gc.SetRegion(r)
			else:
				width, height = w._topwindow._rect[2:]
				r = w._form.CreatePixmap(width, height, 1)
				g = r.CreateGC({'foreground': 0})
				g.FillRectangle(0, 0, width, height)
				g.SetRegion(region)
				g.foreground = 1
				g.FillRectangle(0, 0, width, height)
				g.function = X.GXcopyInverted
				apply(g.PutImage, self._imagemask)
				gc.SetClipMask(r)
		for i in range(clonestart, len(self._list)):
			self._do_render(self._list[i], region)
		w._active_displist = self
		for b in self._buttons:
			if b._highlighted:
				b._do_highlight()

	def _do_render(self, entry, region):
		cmd = entry[0]
		w = self._window
		gc = w._gc
		if cmd == 'clear':
			gc.foreground = entry[1]
			apply(gc.FillRectangle, w._rect)
		elif cmd == 'image':
			mask = entry[1]
			if mask:
				# mask is clip mask for image
				width, height = w._topwindow._rect[2:]
				p = w._form.CreatePixmap(width, height, 1)
				g = p.CreateGC({'foreground': 0})
				g.FillRectangle(0, 0, width, height)
				g.SetRegion(region)
				g.foreground = 1
				g.FillRectangle(0, 0, width, height)
				apply(g.PutImage, (mask,) + entry[3:])
				gc.SetClipMask(p)
			else:
				gc.SetRegion(region)
			apply(gc.PutImage, entry[2:])
			if mask:
				gc.SetRegion(region)
		elif cmd == 'line':
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			points = entry[3]
			x0, y0 = points[0]
			for x, y in points[1:]:
				gc.DrawLine(x0, y0, x, y)
				x0, y0 = x, y
		elif cmd == 'box':
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			apply(gc.DrawRectangle, entry[3])
		elif cmd == 'fbox':
			gc.foreground = entry[1]
			apply(gc.FillRectangle, entry[2])
		elif cmd == 'marker':
			gc.foreground = entry[1]
			x, y = entry[2]
			radius = 5 # XXXX
			gc.FillArc(x-radius, y-radius, 2*radius, 2*radius,
				   0, 360*64)
		elif cmd == 'text':
			gc.foreground = entry[1]
			gc.SetFont(entry[2])
			apply(gc.DrawString, entry[3:])
		elif cmd == 'fpolygon':
			gc.foreground = entry[1]
			gc.FillPolygon(entry[2], X.Convex,
				       X.CoordModeOrigin)
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
			gc.foreground = cl
			gc.FillPolygon([(l1, t1), (ll, tt), (ll, bb), (l1, b1)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = ct
			gc.FillPolygon([(l1, t1), (r1, t1), (rr, tt), (ll, tt)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cr
			gc.FillPolygon([(r1, t1), (r1, b1), (rr, bb), (rr, tt)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cb
			gc.FillPolygon([(l1, b1), (ll, bb), (rr, bb), (r1, b1)],
				       X.Convex, X.CoordModeOrigin)
		elif cmd == 'diamond':
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			x, y, w, h = entry[3]
			gc.DrawLines([(x, y + h/2),
				      (x + w/2, y),
				      (x + w, y + h/2),
				      (x + w/2, y + h),
				      (x, y + h/2)],
				     X.CoordModeOrigin)
		elif cmd == 'fdiamond':
			gc.foreground = entry[1]
			x, y, w, h = entry[2]
			gc.FillPolygon([(x, y + h/2),
					(x + w/2, y),
					(x + w, y + h/2),
					(x + w/2, y + h),
					(x, y + h/2)],
				       X.Convex, X.CoordModeOrigin)
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
			gc.foreground = cl
			gc.FillPolygon([(l, y), (x, t), (x, tt), (ll, y)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = ct
			gc.FillPolygon([(x, t), (r, y), (rr, y), (x, tt)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cr
			gc.FillPolygon([(r, y), (x, b), (x, bb), (rr, y)],
				       X.Convex, X.CoordModeOrigin)
			gc.foreground = cb
			gc.FillPolygon([(l, y), (ll, y), (x, bb), (x, b)],
				       X.Convex, X.CoordModeOrigin)
		elif cmd == 'arrow':
			gc.foreground = entry[1]
			gc.line_width = entry[2]
			apply(gc.DrawLine, entry[3])
			gc.FillPolygon(entry[4], X.Convex,
				       X.CoordModeOrigin)

	def fgcolor(self, color):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._fgcolor = color

	def linewidth(self, width):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._linewidth = width

	def newbutton(self, coordinates, z = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return _Button(self, coordinates, z)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0,
				    center = 1, coordinates = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height = \
		       w._prepare_image(file, crop, scale, center, coordinates)
		if mask:
			self._imagemask = mask, src_x, src_y, dest_x, dest_y, width, height
		else:
			r = Xlib.CreateRegion()
			r.UnionRectWithRegion(dest_x, dest_y, width, height)
			self._imagemask = r
		self._list.append(('image', mask, image, src_x, src_y,
				   dest_x, dest_y, width, height))
		self._optimize((2,))
		x, y, w, h = w._rect
		return float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append(('line', w._convert_color(color),
				   self._linewidth, p))
		self._optimize((1,))

	def drawbox(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		self._list.append(('box', w._convert_color(self._fgcolor),
				   self._linewidth,
				   w._convert_coordinates(coordinates)))
		self._optimize((1,))

	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		self._list.append(('fbox', w._convert_color(color),
				   w._convert_coordinates(coordinates)))
		self._optimize((1,))

	def drawmarker(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		self._list.append(('marker', w._convert_color(color),
				   w._convert_coordinates(coordinates)))

	def usefont(self, fontobj):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
		return self.baseline(), self.fontheight(), self.pointsize()

	def setfont(self, font, size):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(font, size))

	def fitfont(self, fontname, str, margin = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
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
		self._xpos = x

	def writestr(self, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		f = self._font._font
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
			list.append('text', self._window._convert_color(self._fgcolor), self._font._font, x0, y0, str)
			self._optimize((1,))
			self._curpos = x + float(f.TextWidth(str)) / w._rect[_WIDTH], y
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
			curlines = StringStuff.calclines([str], self.strsize, width)[0]
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

	def drawfpolygon(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append(('fpolygon', color, p))
		self._optimize((1,))

	def draw3dbox(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		coordinates = window._convert_coordinates(coordinates)
		cl = window._convert_color(cl)
		ct = window._convert_color(ct)
		cr = window._convert_color(cr)
		cb = window._convert_color(cb)
		self._list.append(('3dbox', (cl, ct, cr, cb), coordinates))
		self._optimize((1,))

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		self._list.append(('diamond',
				   self._window._convert_color(self._fgcolor),
				   self._linewidth, coordinates))
		self._optimize((1,))

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
		self._optimize((1,))

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
		self._optimize((1,))

	def drawarrow(self, color, src, dst):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		color = self._window._convert_color(color)
		if not window._arrowcache.has_key((src,dst)):
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
			window._arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		nsx, nsy, ndx, ndy, points = window._arrowcache[(src,dst)]
		self._list.append(('arrow', color, self._linewidth,
				   (nsx, nsy, ndx, ndy), points))
		self._optimize((1,))

	def _optimize(self, ignore = ()):
		entry = self._list[-1]
		x = []
		for i in range(len(entry)):
			if i not in ignore:
				z = entry[i]
				if type(z) is ListType:
					z = tuple(z)
				x.append(z)
		x = tuple(x)
		try:
			i = self._optimdict[x]
		except KeyError:
			pass
		else:
			del self._list[i]
			del self._optimdict[x]
			if i < self._clonestart:
				self._clonestart = self._clonestart - 1
			for key, val in self._optimdict.items():
				if val > i:
					self._optimdict[key] = val - 1
		self._optimdict[x] = len(self._list) - 1
