__version__ = "$Id$"

# Public Objects:
# class DisplayList

# Private Objects
# class _Button

import math,string

import win32ui, win32con, win32api
from win32modules import imageex

from types import *		
from appcon import *	# draw contants
from win32mu import *	# paint utilities
from Font import findfont
from sysmetrics import pixel_per_mm_x,pixel_per_mm_y

# The list cloneboxes contains all the bounding boxes
# The union of these boxes is the display region

# Draw cmds from the system including buttons (instances of _Button)
# contain relative coordinates.
# The creator must supply a _canvas i.e (x,y,w,h) to
# convert relative coordinates to pixels for the actual drawing
# The cmds are translated to pixels and inserted in a list

class DisplayList:
	def __init__(self, window, bgcolor):
		r, g, b = bgcolor
		self._window = window			
		window._displists.append(self)
		self._buttons = []
		self._curfg = window._fgcolor
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._canvas = window._canvas
		self._linewidth = 1
		self._list = []
		self._optimdict = {}
		self._rendered = 0
		self._font = None
		self._curpos = 0, 0
		self._xpos = 0
		self._win32rgn=None
		if self._canvas[2]==0 or self._canvas[3]==0:
			print 'invalid canvas for wnd',window
			self._canvas=(0,0,10,10)
		self._hfactor = 1.0/(self._canvas[2]/pixel_per_mm_x)
		self._vfactor = 1.0/(self._canvas[3]/pixel_per_mm_y)

		#cloning support
		self._cloneof = None
		self._clonestart = 0
		self._clonebboxes = []
		self._clonergn=None

	def clone(self):
		w = self._window
		new = DisplayList(w, self._bgcolor)
		# copy all instance variables
		new._list = self._list[:]
		new._font = self._font
		if self._win32rgn:
			new._win32rgn=win32ui.CreateRgn()
			new._win32rgn.CopyRgn(self._win32rgn)
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new


#====================================== Rendering
	def render(self):
		wnd = self._window
		if not wnd or not hasattr(wnd,'_obj_')or not hasattr(wnd,'RedrawWindow'):
			return
		for b in self._buttons:
			b._highlighted = 0	
		wnd._active_displist = self

		# we set to not transparent in order to 
		# accomodate windows bug
		# and preserve z-order
		if wnd._transparent in (1,-1):
			wnd.setWndNotTransparent()
		wnd.pop()
		wnd.update()

		
	def _render(self, dc, region, show):
		self._rendered = 1
		w = self._window
		clonestart = self._clonestart
		if not self._cloneof or self._cloneof is not w._active_displist:
			clonestart = 0
		if w._active_displist and self is not w._active_displist and clonestart == 0:
			w._active_displist = None
		if clonestart > 0:
			fg, font = self._clonedata			
		w._active_displist = self
		if show==1:
			for i in range(clonestart, len(self._list)):
				self._do_render(self._list[i], dc, region)
			self._curfg = self._window._fgcolor
			if w.is_showing():
				w.showwindow()
		for b in self._buttons:
			if b._highlighted:
				b._do_highlight()

	def _do_render(self, entry, dc, region):
		cmd = entry[0]
		w = self._window
		if cmd == 'clear':
			dc.FillSolidRect(entry[1],RGB(self._bgcolor))
		elif cmd == 'fg':
			self._curfg = entry[1]
		elif cmd == 'image':
			mask, image, src_x, src_y,dest_x, dest_y, width, height,rcKeep=entry[1:]			
			imageex.render(dc.GetSafeHdc(),self._bgcolor,
				mask, image, src_x, src_y,dest_x, dest_y, width, height,rcKeep)
		elif cmd== 'obj':
			entry[1].draw(dc)
		elif cmd == 'line':
			fg = entry[1]
			points = entry[2]
			x0, y0 = points[0]
			for x, y in points[1:]:
				DrawLine(dc,(x0, y0, x, y),fg)
				x0, y0 = x, y
		elif cmd == 'box':
			DrawRectangle(dc,entry[1], self._curfg, " ")
		elif cmd == 'fbox':
			dc.FillSolidRect(entry[2],RGB(entry[1]))
		elif cmd == 'font':
			#dc.SetFont(entry[1])
			pass
		elif cmd == 'linewidth':
			#gc.line_width = entry[1]
			pass
		elif cmd == 'video':
			func = entry[2]
			apply(func,(entry[1],))
			
		elif cmd == 'fpolygon':
			fg = entry[1] 
			FillPolygon(dc,entry[2], fg)
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
			fg = cl 
			ls = [(l1,t1),(ll,tt),(ll,bb),(l1,b1)]
			FillPolygon(dc,ls, fg)
			fg = ct
			ls = [(l1,t1),(r1,t1),(rr,tt),(ll,tt)]
			FillPolygon(dc,ls, fg)
			fg = cr
			ls = [(r1,t1),(r1,b1),(rr,bb),(rr,tt)]
			FillPolygon(dc,ls, fg)
			fg = cb
			ls = [(l1,b1),(ll,bb),(rr,bb),(r1,b1)]
			FillPolygon(dc,ls, fg)
		elif cmd == 'diamond':
			fg = self._fgcolor
			x, y, w, h = entry[1]
			
			d, m = divmod(w,2)
			if m==1:
				w = w+1

			d, m = divmod(h,2)
			if m==1:
				h = h+1

			ls = [(x, y + h/2), (x + w/2, y), (x + w, y + h/2), (x + w/2, y + h), (x, y + h/2)]
			DrawLines(dc, ls, fg)
		elif cmd == 'fdiamond':
			fg = entry[1] #gc.foreground
			#gc.foreground = entry[1]
			x, y, w, h = entry[2]

			d, m = divmod(w,2)
			if m==1:
				w = w+1

			d, m = divmod(h,2)
			if m==1:
				h = h+1

			ls = [(x, y + h/2), (x + w/2, y), (x + w, y + h/2), (x + w/2, y + h), (x, y + h/2)]
			FillPolygon(dc,ls, fg)

		elif cmd == '3ddiamond':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]
			
			d, m = divmod(w,2)
			if m==1:
				w = w+1
			
			d, m = divmod(h,2)
			if m==1:
				h = h+1
			
			r = l + w
			b = t + h
			x = l + w/2
			y = t + h/2
			n = int(3.0 * w / h + 0.5)
			ll = l + n
			tt = t + 3
			rr = r - n
			bb = b - 3
			fg = cl #gc.foreground
			#gc.foreground = cl
			ls = [(l, y), (x, t), (x, tt), (ll, y)]
			FillPolygon(dc,ls, fg)
			fg = ct
			ls = [(x, t), (r, y), (rr, y), (x, tt)]
			FillPolygon(dc,ls, fg)
			fg = cr
			ls = [(r, y), (x, b), (x, bb), (rr, y)]
			FillPolygon(dc,ls, fg)
			fg = cb
			ls = [(l, y), (ll, y), (x, bb), (x, b)]
			FillPolygon(dc,ls, fg)
		elif cmd == 'arrow':
			fg = entry[1] 
			DrawLine(dc,entry[2],fg)
			FillPolygon(dc,entry[3], fg)
		elif cmd == 'text':
			dc.SetBkMode(win32con.TRANSPARENT)
			dc.SetTextAlign(win32con.TA_BOTTOM)
			clr_org=dc.SetTextColor(RGB(entry[1]))
			horg=dc.SelectObjectFromHandle(entry[2].handle())
			x,y,str=entry[3:]
			dc.TextOut(x,y,str)
			dc.SetTextColor(clr_org)
			dc.SelectObjectFromHandle(horg)

	def close(self):
		if self._window is None:
			return
		win = self._window
		for b in self._buttons[:]:
			b.close()
		if self in win._displists:
			win._displists.remove(self)
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			if win._transparent in (1,-1):
				win.setWndTransparent()
			win.update()
			win.push()
		self._window = None
		if self._win32rgn:
			self._win32rgn.DeleteObject()
			del self._win32rgn
			self._win32rgn=None
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

	def render_now(self):
		self.render()	
	
	def fgcolor(self, color):
		self._list.append('fg', color)
		self._fgcolor = color

	def newbutton(self, coordinates):
		x, y, w, h = self._convert_coordinates(coordinates)
		self._update_bbox(x, y, x+w, y+h)
		return _Button(self, coordinates)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0,
				    center = 1, coordinates = None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, mask, src_x, src_y, dest_x, dest_y, width, height,rcKeep = \
		       w._prepare_image(file, crop, scale, center, coordinates)
		self._list.append('image', mask, image, src_x, src_y,
				  dest_x, dest_y, width, height,rcKeep)
		self._optimize((2,))
		self._update_bbox(dest_x, dest_y, dest_x+width, dest_y+height)
		x, y, w, h = self._canvas
		return float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h


	def _resize_image_buttons(self):
		type = self._list[1]
		if type[0]!='image':
			return


	#############################################
	# draw primitives

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = self._convert_color(color)
		p = []
		xvalues = []
		yvalues = []
		for point in points:
			x, y = self._convert_coordinates(point)
			p.append(x,y)
			xvalues.append(x)
			yvalues.append(y)
		self._list.append('line', color, p)
		self._update_bbox(min(xvalues), min(yvalues), max(xvalues), max(yvalues))


	def drawbox(self, coordinates, do_draw=1):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates)
		if do_draw:
			self._list.append('box',(x, y, x+w, y+h))
			self._optimize()
			self._update_bbox(x, y, x+w, y+h)
		return x, y, x+w, y+h


	def drawfbox(self, color, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates)
		self._list.append('fbox', self._convert_color(color),
				(x, y, x+w, y+h))
		self._optimize((1,))
		self._update_bbox(x, y, x+w, y+h)
		return x, y, x+w, y+h

	def clear(self,coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates)
		self._list.append('clear',(x, y, x+w, y+h))
		self._optimize((1,))
		self._update_bbox(x, y, x+w, y+h)

	def drawfpolygon(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = self._convert_color(color)
		p = []
		for point in points:
			p.append(self._convert_coordinates(point))
		self._list.append('fpolygon', color, p)
		self._optimize((1,))

	def draw3dbox(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		coordinates = self._convert_coordinates(coordinates)
		cl = self._convert_color(cl)
		ct = self._convert_color(ct)
		cr = self._convert_color(cr)
		cb = self._convert_color(cb)
		self._list.append('3dbox', (cl, ct, cr, cb), coordinates)
		self._optimize((1,))
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._convert_coordinates(coordinates)
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
		coordinates = self._convert_coordinates((x, y, w, h))
		color = self._convert_color(color)
		self._list.append('fdiamond', color, coordinates)
		self._optimize((1,))
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

		
	def draw3ddiamond(self, cl, ct, cr, cb, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = self._convert_color(cl)
		ct = self._convert_color(ct)
		cr = self._convert_color(cr)
		cb = self._convert_color(cb)
		coordinates = self._convert_coordinates(coordinates)
		self._list.append('3ddiamond', (cl, ct, cr, cb), coordinates)
		self._optimize((1,))
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	def drawarrow(self, color, src, dst):
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		color = self._convert_color(color)
		nsrc = self._convert_coordinates(src)
		ndst = self._convert_coordinates(dst)
		try:
			nsx, nsy, ndx, ndy, points = window.arrowcache[(nsrc,ndst)]
		except KeyError:
			sx, sy = src
			dx, dy = dst
			nsx, nsy = nsrc 
			ndx, ndy = ndst
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
			window.arrowcache[(nsrc,ndst)] = nsx, nsy, ndx, ndy, points
		self._list.append('arrow', color, (nsx, nsy, ndx, ndy), points)
		self._optimize((1,))
		self._update_bbox(nsx, nsy, ndx, ndy)

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
		return self._font.baseline() * self._vfactor

	def fontheight(self):
		return self._font.fontheight() * self._vfactor

	def pointsize(self):
		return self._font.pointsize()

	def strsize(self, str):
		width, height = self._font.strsize(str)
		return width*self._hfactor,height*self._vfactor

	def setpos(self, x, y):
		self._curpos = x, y
		self._xpos = x

	def writestr(self, str):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		f = self._font
		base = self.baseline()
		height = self.fontheight()
		strlist = string.splitfields(str, '\n')
		oldx, oldy = x, y = self._curpos
		if len(strlist) > 1 and oldx > self._xpos:
			oldx = self._xpos
		oldy = oldy - base
		maxx = oldx
		for str in strlist:
			x0, y0 = self._convert_coordinates((x, y))
			list.append('text', self._convert_color(self._fgcolor),f, x0, y0, str)
			self._optimize((1,))
			width=self._canvas[2]-self._canvas[0]
			if width==0:width=1 
			twidth,theight=f.TextSize(str)
			self._curpos = x + float(twidth) / width, y
			self._update_bbox(x0,y0-theight, x0+twidth,y0)
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

	# Update cloneboxes. 
	# The union of these boxes is the display region
	def _update_bbox(self, minx, miny, maxx, maxy):
		assert type(minx) == type(maxx) == type(miny) == type(maxy) == type(1)
		if minx > maxx:
			minx, maxx = maxx, minx
		if miny > maxy:
			miny, maxy = maxy, miny
		self._clonebboxes.append(minx, miny, maxx, maxy)
		if not self._win32rgn:
			self._win32rgn=win32ui.CreateRgn()
			self._win32rgn.CreateRectRgn((minx, miny, maxx, maxy))
		else:
			addrgn=win32ui.CreateRgn()
			addrgn.CreateRectRgn((minx, miny, maxx, maxy))
			self._win32rgn.CombineRgn(self._win32rgn,addrgn,win32con.RGN_OR)
			addrgn.DeleteObject()
			del addrgn

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


	# convert relative coordinates to (owner wnd) pixel coordinates
	def _convert_coordinates(self, coordinates):
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		
		rx, ry, rw, rh = self._canvas
			
		px = int((rw - 1) * x + 0.5) + rx
		py = int((rh - 1) * y + 0.5) + ry
		if len(coordinates) == 2:
			return px, py

		pw = int((rw - 1) * w + 0.5) 
		ph = int((rh - 1) * h + 0.5)
		return px, py, pw, ph

	# convert (owner wnd) pixel coordinates to relative coordinates
	def _inverse_coordinates(self,coordinates):		
		x, y = coordinates[:2]
		if len(coordinates) > 2:
			w, h = coordinates[2:]
		else:
			w, h = 0, 0
		
		rx, ry, rw, rh = self._canvas

		px = float(x-rx)/rw
		py = float(y-ry)/rh
		if len(coordinates) == 2:
			return px, py
		
		pw = float(w)/rw
		ph = float(h)/rh
		return px, py, pw, ph

	def _convert_color(self, color):
		return color 

		
	# Object support
	def drawobj(self,obj):
		self.AddObj(obj)
	def AddObj(self,obj):
		self._list.append('obj',obj)
		l,t,r,b=obj.getbbox()
		self._update_bbox(l,t,r,b)


####################################################
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

