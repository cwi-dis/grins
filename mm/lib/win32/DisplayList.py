__version__ = "$Id$"

# Public Objects:
# class DisplayList

# Private Objects
# class _Button

import math,string

import win32ui, win32con, win32api
from win32modules import cmifex, imageex

from types import *		
from appcon import *	# draw contants
from win32mu import *	# paint utilities
from Font import findfont


class DisplayList:
	def __init__(self, window, bgcolor):
		r, g, b = bgcolor
		self._window = window
		window._displists.append(self)
		self._buttons = []
		self._curfg = window._fgcolor
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._linewidth = 1
		self._list = []
		if (window._window_type != HTM):
			if window._transparent <= 0:
				self._list.append(('clear',))
				SetWndStyle(window._hWnd, 0)
			else:
				SetWndStyle(window._hWnd, 1)
		self._optimdict = {}
		self._cloneof = None
		self._clonestart = 0
		self._rendered = FALSE
		self._font = None
		self._imagemask = None


	def clone(self):
		w = self._window
		new = DisplayList(w, self._bgcolor)
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

#====================================== Rendering
	def render(self):
		w = self._window			
		for b in self._buttons:
			b._highlighted = 0	
		# draw our bit (indirectly by calling InvalidateRect
		w._active_displist = self
		w._hWnd.InvalidateRect()
		#self._render(w._hWnd.GetDC(),w._hWnd.GetClientRect(), 1)

		if hasattr(w, '_pixmap'):
			x, y, width, height = window._rect
			#w._pixmap.CopyArea(w._form, w._gc,
			#			x, y, width, height, x, y)		
			
	def _render(self, dc, region, show):
		self._rendered = TRUE
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


	def _do_render(self, entry, dc, region):
		cmd = entry[0]
		w = self._window
		if cmd == 'clear':
			dc.FillSolidRect(region,RGB(self._bgcolor))
		elif cmd == 'fg':
			self._curfg = entry[1]
			pass
		elif cmd == 'image':		
			mask = entry[1]
			r, g, b = self._bgcolor
			imageex.PutImage(w._hWnd,dc.GetSafeHdc(),entry[2], r, g, b, w._scale, entry[3])
		elif cmd == 'line':
			fg = entry[1]
			points = entry[2]
			x0, y0 = points[0]
			for x, y in points[1:]:
				DrawLine(dc,(x0, y0, x, y),fg)
				x0, y0 = x, y
		elif cmd == 'box':
			#mcolor = self._fgcolor #255, 0, 0	w._fgcolor
			DrawRectangle(dc,entry[1], self._curfg, " ")
		elif cmd == 'fbox':
			dc.FillSolidRect(entry[2],RGB(entry[1]))
		elif cmd == 'font':
			#gc.SetFont(entry[1])
			pass
		elif cmd == 'text':
			fontname = entry[1]
			pointsize = entry[2]
			id = entry[3]
			str = entry[4]
			x, y = entry[5:]
			fontColor = w._fgcolor
			if (str == None or str==''):
				str =' '
			#print "Calling PutText with", w._hWnd
			cmifex.PutText(id, w._hWnd, str, fontname, pointsize, TRANSPARENT, self._bgcolor, fontColor,w._align,(x,y))
			#self.update_boxes(w._hWnd)
			pass
		elif cmd == 'linewidth':
			#gc.line_width = entry[1]
			pass
		elif cmd == 'video':
			func = entry[2]
			apply(func,(entry[1],))

		elif cmd == 'fpolygon':
			fg = entry[1] #gc.foreground
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
			fg = cl #gc.foreground
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
			#gc.foreground = fg
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
			fg = entry[1] #gc.foreground
			DrawLine(dc,entry[2],fg)
			FillPolygon(dc,entry[3], fg)
			#gc.foreground = fg

	def drawfpolygon(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = w._convert_color(color)
		p = []
		for point in points:
			p.append(w._convert_coordinates(point))
		self._list.append('fpolygon', color, p)
		self._optimize(1)

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

	def drawdiamond(self, coordinates):
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		self._list.append('diamond', coordinates)
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
		coordinates = window._convert_coordinates((x, y, w, h))
		color = window._convert_color(color)
		self._list.append('fdiamond', color, coordinates)
		self._optimize(1)

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
			points.append(int(round(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin)),
				      int(round(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos)))
			points.append(int(round(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin)),
				      int(round(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos)))
			window.arrowcache[(src,dst)] = nsx, nsy, ndx, ndy, points
		self._list.append('arrow', color, (nsx, nsy, ndx, ndy), points)
		self._optimize(1)

	def close(self):
		win = self._window
		if win is None:
			return
		ls = self._list
		for b in self._buttons[:]:
			b.close()
		win._displists.remove(self)

		ls = self._list
		for i in range(len(ls)):
			if ls[i][0]=='image':
				fou = 1
				for dl in win._displists:				
					for y in range(len(dl._list)):
						if dl._list[y][0]=='image':
							if ls[i][2]==dl._list[y][2]:
								fou = 0
								break
					if fou:
						imageex.Destroy(ls[i][2])

		self._window = None
		for d in win._displists:
			if d._cloneof is self:
				d._cloneof = None
		if win._active_displist is self:
			win._active_displist = None
			#win.push()
			if win._transparent == -1:
				SetWndStyle(win._hWnd, 1)
			if win._transparent == 1 or win._transparent == -1:
				f = 0
				if win._topwindow is not win:
					#i = self._parent._subwindows.index(self)
					windows = win._parent._subwindows[:]
					windows.reverse()
					for w in windows:
						if w._active_displist!=None and w._transparent != 1 and w != win and win._z >= w._z:
							rect1 = win._hWnd.GetClientRect()
							rect2 = win._hWnd.ClientToScreen(rect1)
							rect2 = w._hWnd.ScreenToClient(rect2)
							rect1 = w._hWnd.GetClientRect()
							if rect2[0] < 0 and rect2[2] < 0:
								continue
							if rect2[1] < 0 and rect2[3] < 0:
								continue
							if rect2[2] < rect1[0] and rect2[3] < rect1[1]:
								continue
							if rect2[0] > rect1[2] and rect2[1] > rect1[3]:
								continue
							if rect2[0] > rect1[2] and rect2[2] > rect1[2]:
								continue
							if rect2[1] > rect1[3] and rect2[3] > rect1[3]:
								continue
							f = 1
							w._hWnd.PostMessage(win32con.WM_PAINT)
							#w._do_expose(w._hWnd, 1) # args changed

				if f == 0:
					win.hide()
					win.show()
			else:
				#win._do_expose(None)
				dc=win._hWnd.GetDC()
				win._do_expose(dc,win._hWnd.GetClientRect())
				win._hWnd.ReleaseDC(dc)

			#if hasattr(win, '_pixmap'):
			#	x, y, w, h = win._rect
			#	win._gc.SetRegion(win._region)
			#	win._pixmap.CopyArea(win._form, win._gc,
			#			     x, y, w, h, x, y)
		del self._cloneof
		try:
			del self._clonedata
		except AttributeError:
			pass
		del self._optimdict
		del self._list
		del self._buttons
		del self._font
		del self._imagemask

	def is_closed(self):
		return self._window is None

	def render_now(self):
		self.render()	
	
	def clear_back(self, dc, image):
		wx, wy, ww, wh = self._hWnd.GetClientRect()
		il, it, ir, ib = imageex.ImageRect(image)
		tup1 = (0,0,0,ib)
		tup2 = (il,0,ww,it)
		tup3 = (0,ib,ir,wh)
		tup4 = (ir,it,ww,wh)
		dc.FillSolidRect(tup1,RGB(self._bgcolor))
		dc.FillSolidRect(tup2,RGB(self._bgcolor))
		dc.FillSolidRect(tup3,RGB(self._bgcolor))
		dc.FillSolidRect(tup4,RGB(self._bgcolor))

	def update_boxes(self, hWnd):
		if self._window._window_type == TEXT:
			ydif = cmifex.GetScrollPos(hWnd)
		else:
			ydif = 0
		if ydif == 0:
			return
		cmifex.ClearXY(hWnd)
		print "ydif-->", ydif
		#dif = oldscrollpos-scrollpos
		#print "self._buttons[0]->>>", self._buttons[0]
		if self._buttons==[]:
			return
		button = 0
		for i in range(0, len(self._list)):
			l = self._list[i]
			#print "before buttons-->", l
			if l[0] == 'box':				
				tuple = l[1]
				x1 = tuple[0]
				y1 = tuple[1]+ydif
				x2 = tuple[2]
				y2 = tuple[3]+ydif
				temptuple = (x1,y1,x2,y2)
				l = ('box', temptuple)
				self._list[i] = l
				#print tuple
				#if len(self._buttons)<=button:
				#	self._buttons.append('box', (x1,y1,x2,y2))
				self._buttons[button]._setcoords(x1,y1,x2,y2)
				button = button+1
		#print "out of update_boxes"

	def fgcolor(self, color):
		#r, g, b = color
		self._list.append('fg', color)
		self._fgcolor = color

	def newbutton(self, coordinates):
		return _Button(self, coordinates)

	def display_image_from_file(self, file, crop = (0,0,0,0), scale = 0, center = 1, coordinates = None, tras = -1):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		image, l, t, r, b = w._prepare_image(file, crop, scale, center, coordinates, transp = tras)
		dest_x = l
		dest_y = t
		width = r-l
		height = b-t
		mask, src_x, src_y = 0, 0, 0
		#dest_x, dest_y, width, height = w._rect
		self._list.append('image', mask, image, center, src_y,
				  dest_x, dest_y, width, height)
		self._optimize(2)
		#Assume that the image is stretched to the window so there is no conversion needed
		#x, y, w, h = 0, 0, 1, 1
		#return x, y, w, h
		x, y, w, h = w._rect
		#a1 = float(dest_x - x) / w
		#b1 = float(dest_y - y) / h
		a1 = float(dest_x) / w
		b1 = float(dest_y) / h
		c1 = float(width) / w
		d1 = float(height) / h
		return a1, b1, c1, d1

	def _resize_image_buttons(self):
		type = self._list[1]
		if type[0]!='image':
			return

	def drawline(self, color, points):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		#color = w._convert_color(color)
		p = []
		for point in points:
			coordinates = self._window._convert_coordinates(point)
			X, Y, W, H = self._window._rect
			x, y = coordinates 
			x = x - X
			y = y - Y
			coordinates = x, y
			p.append((x, y))
			
		self._list.append('line', color, p)

	def drawbox(self, coordinates, do_draw=1):
		#print "DrawBox Before: ", coordinates
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		#print "DrawBox After: ", coordinates
		#print "Window Rect: ", self._window._rect
		#X, Y, W, H = self._window._rect
		x, y, w, h = coordinates 
		#x = x - X
		#y = y - Y
		w = x + w
		h = y + h
		coordinates = x, y, w, h
		if do_draw:
			self._list.append('box', coordinates)	
			self._optimize()
		return coordinates

	def drawfbox(self, color, coordinates):	
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._window._convert_coordinates(coordinates)
		#X, Y, W, H = self._window._rect
		x, y, w, h = coordinates 
		#x = x - X
		#y = y - Y
		w = x + w
		h = y + h
		coordinates = x, y, w, h
		#6/2A
		#self._list.append('fbox', self._window._convert_color(color),
		#		self._window._convert_coordinates(coordinates))
		self._list.append('fbox', color, coordinates)
		self._optimize(1)
		return coordinates

	def usefont(self, fontobj):
		self._font = fontobj
		return self.baseline(), self.fontheight(), self.pointsize()

	def setfont(self, font, size):
		jnk = self.usefont(findfont(font, size))
		return jnk

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
		self._xpos = x
	
	def writeText(self, font, size, id, str, x, y):
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		list = self._list
		list.append('text', font, size, id, str, x, y)

	def centerstring(self, left, top, right, bottom, str):
		wx, wy, wid, heig = self._window._hWnd.GetClientRect()
		if heig == 0:
			heig = 1
		#fontheight = self.fontheight()
		fontheight = self._font._pointsize
		baseline = self.baseline()
		width = int((right - left)*wid)
		height = int((bottom - top)*heig)
		curlines = [str]
		if height >= 2*fontheight:
			import StringStuff
			curlines = StringStuff.calclines([str], self.strsize, right - left)[0]
		nlines = len(curlines)
		needed = nlines * fontheight
		if nlines > 1 and needed > height:
			nlines = max(1, int(height / fontheight))
			curlines = curlines[:nlines]
			curlines[-1] = curlines[-1] + '...'
		x0 = (left + right) * 0.5	# x center of box
		y0 = (top + bottom) * 0.5	# y center of box
		y = y0 - nlines * fontheight * 0.5/heig
		for i in range(nlines):
			str = string.strip(curlines[i])
			# Get font parameters:
			w = self.strsize(str)[0]	# Width of string
			while str and w > right - left:
				str = str[:-1]
				w = self.strsize(str)[0]
			x = x0 - 0.5*w
			#y = y + baseline
			#y = y + self._font._pointsize/heig
			self.setpos(x, y)
			dstx = int(x * wid + 0.5)
			dsty = int(y * heig + 0.5)+self._font._pointsize*i
			#self.writestr(str)
			self.writeText(self._font._fontname, self._font._pointsize, -1, str, dstx, dsty)

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

####################################################

class _Button:
	def __init__(self, dispobj, coordinates):		
		#print 'NEW _Button to be created -- Coordinates:'
		#print coordinates
		self._dispobj = dispobj
		dispobj._buttons.append(self)
		window = dispobj._window
		self._coordinates = coordinates
		x, y, w, h = coordinates
		self._corners = x, y, x + w, y + h
		self._box = 0, 0, 0, 0
		self._color = self._hicolor = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		self._newdispobj = None
		self._highlighted = 0
		#if self._color == dispobj._bgcolor:
		#	return
		#self._box = dispobj.drawbox(self._coordinates)
		bw = self._coordinates[2] #- self._coordinates[0] 
		bh = self._coordinates[3] #- self._coordinates[1]
		bx = self._coordinates[0]
		by = self._coordinates[1]
		self._box = dispobj.drawbox((bx,by,bw,bh),self._color != dispobj._bgcolor)

	def _resize(self, xfactor, yfactor):
		wnd = self._dispobj._window._hWnd
		list = self._dispobj._list[1]
		if list[0]!='image':
			return
		#wnd.MessageBox("ButtonResize", "Debug", win32con.MB_OK)
		x, y, z, k = self._box
		x = (int)(float(x)*xfactor+0.5)
		y = (int)(float(y)*yfactor+0.5)
		z = (int)(float(z)*xfactor+0.5)
		k = (int)(float(k)*yfactor+0.5)
		self._box = x, y, z, k
	
	def _setcoords(self, x, y, w, h):
		#self._box = x, y, w-x, h-y
		self._box = x, y, w, h

	def close(self):
		#wnd = self._dispobj._window._hWnd
		#print "Buttons.Close!"
		if self._dispobj is None:
			return
		self._dispobj._buttons.remove(self)
		self._dispobj = None
		if self._newdispobj:
			self._newdispobj.close()
			self._newdispobj = None

	def is_closed(self):
		return self._dispobj is None

	def hiwidth(self, width):
		self._hiwidth = width

	def hicolor(self, color):
		self._hicolor = color

	def highlight(self):
		dispobj = self._dispobj
		if dispobj is None:
			return
		window = dispobj._window
		if window._active_displist is not dispobj:
			raise error, 'can only highlight rendered button'
		# if button color and highlight color are all equal to
		# the background color then don't draw the box (and
		# don't highlight).
		if self._color == dispobj._bgcolor and \
		   self._hicolor == dispobj._bgcolor:
			return
		self._highlighted = 1
		self._do_highlight()
#		if hasattr(window, '_pixmap'):
#			x, y, w, h = window._rect
#			window._pixmap.CopyArea(window._form, window._gc,
#						x, y, w, h, x, y)
#		toplevel._main.UpdateDisplay()

	def _do_highlight(self):
		window = self._dispobj._window
	#	gc = window._gc
	#	gc.foreground = window._convert_color(self._hicolor)
	#	gc.line_width = self._hiwidth
	#	gc.SetRegion(window._clip)
	#	apply(gc.DrawRectangle, window._convert_coordinates(self._coordinates))

	def unhighlight(self):
		dispobj = self._dispobj
		if dispobj is None:
			return
		window = dispobj._window
		if window._active_displist is not dispobj:
			return
		if not self._highlighted:
			return
		self._highlighted = 0
		# calculate region to redisplay
		x, y, w, h = window._convert_coordinates(self._coordinates)
		lw = self._hiwidth / 2
	#	r = Xlib.CreateRegion()
	#	r.UnionRectWithRegion(x - lw, y - lw,
	#			      w + 2*lw + 1, h + 2*lw + 1)
	#	r1 = Xlib.CreateRegion()
	#	r1.UnionRectWithRegion(x + lw + 1, y + lw + 1,
	#			       w - 2*lw - 1, h - 2*lw - 1)
	#	r.SubtractRegion(r1)
	#	window._do_expose(r)
	#	if hasattr(window, '_pixmap'):
	#		x, y, w, h = window._rect
	#		window._pixmap.CopyArea(window._form, window._gc,
	#					x, y, w, h, x, y)
	#	toplevel._main.UpdateDisplay()

	def _inside(self, x, y):
		# return 1 if the given coordinates fall within the button
		if (self._corners[0] <= x <= self._corners[2]) and \
			  (self._corners[1] <= y <= self._corners[3]):
			return TRUE
		else:
			return FALSE
