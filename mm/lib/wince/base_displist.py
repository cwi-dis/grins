__version__ = "$Id$"

# Tuneable: width of 3d border
SIZE_3DBORDER = 2

import math, string

from types import *		
from appcon import *
from winfont import findfont

class DisplayList:
	def __init__(self, window, bgcolor, units):
		self._window = window
		self._bgcolor = bgcolor
		self.__units = units
		window._displists.append(self)

		self._fgcolor = window._fgcolor
		self._canvas = window._canvas
		self._linewidth = 1
		self._font = None
		self._curpos = 0, 0
		self._xpos = 0

		self._list = []
		self._list.append(('clear', bgcolor))
		self._rendered = 0

		self._buttons = []

		self._alphaSensitivity = None

		# associate cmd names to list indices
		self.__cmddict = {}
		self.__butdict = {}

	def render(self):
		wnd = self._window
		for b in self._buttons:
			b._highlighted = 0 
		wnd._active_displist = self
		wnd.update()

	# Alias for render
	def render_now(self):
		self.render()	

	def close(self):
		wnd = self._window
		if wnd is None:
			return
		for b in self._buttons[:]:
			b.close()
		wnd._displists.remove(self)
		self._window = None
		if wnd._active_displist is self:
			wnd._active_displist = None
			wnd.update()
		del self._list
		del self._buttons

	# Returns true if this is closed
	def is_closed(self):
		return self._window is None

	def _render(self, dc, ltrb = None, start = 0):
		self._rendered = 1

		for i in range(start, len(self._list)):
			self._do_render(self._list[i], dc, ltrb)

		for b in self._buttons:
			if b._highlighted:b._do_highlight()

	def _do_render(self, entry, dc, ltrb):
		cmd = entry[0]

	# Define a new button. Coordinates are in window relatives
	def newbutton(self, coordinates, z = 0, sensitive = 1):
		if self._rendered:
			raise error, 'displaylist already rendered'
		
		# Split tuple. It should'n be unified anyway
		shape, coordinates = coordinates[0], coordinates[1:]
		
		return _Button(self, shape, coordinates, z, sensitive)

	# display image from file
	def display_image_from_file(self, file, crop = (0,0,0,0), fit = 'meet',
				    center = 1, coordinates = None, clip = None, align = None,
				    units = None):
		self._list.append(('image', file, coordinates, fit))
		return 0, 0, 100, 100

	def isTransparent(self, point):
		return 0

	# set the media sensitivity
	# value is percentage value (0 == 'opaque', 100 == 'transparent')
	def setAlphaSensitivity(self, value):
		self._alphaSensitivity = value

	#############################################
	# draw primitives

	# Set forground color
	def fgcolor(self, color):
		self._list.append(('fg', color))
		self._fgcolor = color

	# Insert a command to drawline
	def drawline(self, color, points, units = None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = self._convert_color(color)
		p = []
		xvalues = []
		yvalues = []
		for point in points:
			x, y = self._convert_coordinates(point, units=units)
			p.append((x,y))
			xvalues.append(x)
			yvalues.append(y)
		self._list.append(('line', color, p))
		self._update_bbox(min(xvalues), min(yvalues), max(xvalues), max(yvalues))

	# Draw a horizontal gutter
	def draw3dhline(self, color1, color2, x0, x1, y, units = None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color1 = self._convert_color(color1)
		color2 = self._convert_color(color2)
		x0, y = self._convert_coordinates((x0, y), units=units)
		x1, dummy = self._convert_coordinates((x1, y), units=units)
		self._list.append(('3dhline', color1, color2, x0, x1, y))
		self._update_bbox(x0, y, x1, y+1)

	# Insert a command to drawbox
	def drawbox(self,coordinates, clip = None, units = None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates, units=units)
		self._list.append(('box',(x, y, x+w, y+h)))
		self._optimize()
		self._update_bbox(x, y, x+w, y+h)

	def drawboxanchor(self, coordinates, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates, units=units)
		self._list.append(('anchor',(x, y, x+w, y+h)))
		self._optimize()
		self._update_bbox(x, y, x+w, y+h)
##		return x, y, x+w, y+h

	# Insert a command to draw a filled box
	def drawfbox(self, color, coordinates, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates, units=units)
		self._list.append(('fbox', self._convert_color(color),
				   (x, y, x+w, y+h)))
		self._optimize((1,))
		self._update_bbox(x, y, x+w, y+h)
##		return x, y, x+w, y+h

	# Insert a command to draw a filled box
	def drawstipplebox(self, color, coordinates, units=None):
		pass

	# Insert a command to clear box
	def clear(self,coordinates, units=None):
		if units is None:
			units = self.__units
		raise AssertionError, 'obsolete call'
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates, units=units)
		self._list.append(('clear',(x, y, x+w, y+h)))
		self._optimize((1,))
		self._update_bbox(x, y, x+w, y+h)

	# Insert a command to draw a filled polygon
	def drawfpolygon(self, color, points, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		w = self._window
		color = self._convert_color(color)
		p = []
		for point in points:
			p.append(self._convert_coordinates(point, units=units))
		self._list.append(('fpolygon', color, p))
		self._optimize((1,))

	# Insert a command to draw a 3d box
	def draw3dbox(self, cl, ct, cr, cb, coordinates, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		coordinates = self._convert_coordinates(coordinates, units=units)
		cl = self._convert_color(cl)
		ct = self._convert_color(ct)
		cr = self._convert_color(cr)
		cb = self._convert_color(cb)
		self._list.append(('3dbox', (cl, ct, cr, cb), coordinates))
		self._optimize((1,))
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	# Insert a command to draw a diamond
	def drawdiamond(self, coordinates, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		coordinates = self._convert_coordinates(coordinates,units=units)
		self._list.append(('diamond', coordinates))
		self._optimize()
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	# Insert a command to draw a filled diamond
	def drawfdiamond(self, color, coordinates, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		x, y, w, h = coordinates
		if w < 0:
			x, w = x + w, -w
		if h < 0:
			y, h = y + h, -h
		coordinates = self._convert_coordinates((x, y, w, h), units=units)
		color = self._convert_color(color)
		self._list.append(('fdiamond', color, coordinates))
		self._optimize((1,))
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

		
	# Insert a command to draw a 3d diamond
	def draw3ddiamond(self, cl, ct, cr, cb, coordinates, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		cl = self._convert_color(cl)
		ct = self._convert_color(ct)
		cr = self._convert_color(cr)
		cb = self._convert_color(cb)
		coordinates = self._convert_coordinates(coordinates, units=units)
		self._list.append(('3ddiamond', (cl, ct, cr, cb), coordinates))
		self._optimize((1,))
		x, y, w, h = coordinates
		self._update_bbox(x, y, x+w, y+h)

	def drawicon(self, coordinates, icon, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		x, y, w, h = self._convert_coordinates(coordinates, units=units)
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
		self._optimize((2,))
		
	# Insert a command to draw an arrow
	def drawarrow(self, color, src, dst, units=None):
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		window = self._window
		color = self._convert_color(color)
		nsrc = self._convert_coordinates(src, units=units)
		ndst = self._convert_coordinates(dst, units=units)
##		try:
##			nsx, nsy, ndx, ndy, points = window.arrowcache[(nsrc,ndst)]
##		except KeyError:
		if 1:			# keep indentation.
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
			points.append((roundi(ndx + ARR_LENGTH*cos + ARR_HALFWIDTH*sin),
				       roundi(ndy + ARR_LENGTH*sin - ARR_HALFWIDTH*cos)))
			points.append((roundi(ndx + ARR_LENGTH*cos - ARR_HALFWIDTH*sin),
				       roundi(ndy + ARR_LENGTH*sin + ARR_HALFWIDTH*cos)))
#			window.arrowcache[(nsrc,ndst)] = nsx, nsy, ndx, ndy, points
		self._list.append(('arrow', color, (nsx, nsy, ndx, ndy), points))
		self._optimize((1,))
		self._update_bbox(nsx, nsy, ndx, ndy)

	def drawvideo(self,cbf):
		self._list.append(('video',cbf))
		
	def get3dbordersize(self):
		# This is the same "1" as in 3dbox bordersize
		return self._pxl2rel((0,0,SIZE_3DBORDER, SIZE_3DBORDER))[2:4]
		
	# Returns font attributes
	def usefont(self, fontobj):
		if self._rendered:
			raise error, 'displaylist already rendered'
		self._font = fontobj
		return self.baseline(), self.fontheight(), self.pointsize()

	# Returns font attributes
	def setfont(self, font, size):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(font, size))

	# Returns font attributes
	def fitfont(self, fontname, str, margin = 0):
		if self._rendered:
			raise error, 'displaylist already rendered'
		return self.usefont(findfont(fontname, 10))

	# Returns font's  baseline
	def baselinePXL(self):
		return self._font.baselinePXL()

	def baseline(self):
		baseline = self._font.baselinePXL()
		return self._pxl2rel((0,0,0,baseline))[3]

	# Returns font's  height
	def fontheightPXL(self):
		return self._font.fontheightPXL()

	def fontheight(self):
		fontheight = self._font.fontheightPXL()
		return self._pxl2rel((0,0,0,fontheight))[3]

	# Returns font's  pointsize
	def pointsize(self):
		return self._font.pointsize()

	# Returns string's  size
	def strsizePXL(self, str):
		return self._font.strsizePXL(str)

	def strsize(self, str, units = None):
		if units is None:
			units = self.__units
		width, height = self._font.strsizePXL(str)
		if units == UNIT_PXL:
			return width, height
		else:
			return self._pxl2rel((0,0,width,height))[2:4]

	# Set the current position
	def setpos(self, x, y, units=None):
		if units is None:
			units = self.__units
		x, y = self._convert_coordinates((x, y), units=units)
		self._curpos = x, y
		self._xpos = x

	# Insert a write string command
	def writestr(self, str, units=None):
		if self._rendered:
			raise error, 'displaylist already rendered'
		if units is None:
			units = self.__units
		w = self._window
		list = self._list
		f = self._font
		base = self.baselinePXL()
		height = self.fontheightPXL()
		strlist = string.splitfields(str, '\n')
		oldx, oldy = x, y = self._curpos
		if len(strlist) > 1 and oldx > self._xpos:
			oldx = self._xpos
		oldy = oldy - base
		maxx = oldx
		for str in strlist:
			x0, y0 = x, y
			list.append(('text', self._convert_color(self._fgcolor),f, x0, y0, str))
			self._optimize((1,))
			width=self._canvas[2]-self._canvas[0]
			if width==0:width=1 
			twidth,theight=f.TextSize(str)
			self._curpos = x + twidth, y
			self._update_bbox(x0,y0-theight, x0+twidth,y0)
			x = self._xpos
			y = y + height
			if self._curpos[0] > maxx:
				maxx = self._curpos[0]
		newx, newy = self._curpos
		if units == UNIT_PXL:
			return oldx, oldy, maxx - oldx, newy - oldy + height - base
		else:
			return self._pxl2rel((oldx, oldy, maxx - oldx, newy - oldy + height - base))

	# Insert a draw string centered command in a box, breaking lines if necessary
	def centerstring(self, left, top, right, bottom, str, units=None):
		if units is None:
			units = self.__units
		fontheight = self.fontheightPXL()
		baseline = self.baselinePXL()
		width = right - left
		height = bottom - top
		left, top, width, height = self._convert_coordinates((left, top, width, height), units=units)
		curlines = [str]
		if height >= 2*fontheight:
			import StringStuff
			curlines = StringStuff.calclines([str], self.strsizePXL, width)[0]
		nlines = len(curlines)
		needed = nlines * fontheight
		if nlines > 1 and needed > height:
			nlines = max(1, int(height / fontheight))
			curlines = curlines[:nlines]
			curlines[-1] = curlines[-1] + '...'
		x0 = left + width / 2	# x center of box
		y0 = top + height / 2	# y center of box
		y = y0 - nlines * fontheight / 2
		for i in range(nlines):
			str = string.strip(curlines[i])
			# Get font parameters:
			w = self.strsizePXL(str)[0]	# Width of string
			while str and w > width:
				str = str[:-1]
				w = self.strsizePXL(str)[0]
			x = x0 - 0.5*w
			y = y + baseline
			self.setpos(x, y, UNIT_PXL)
			self.writestr(str)

	# Update cloneboxes. 
	# The union of these boxes is the display region
	def _update_bbox(self, minx, miny, maxx, maxy):
		assert type(minx) == type(maxx) == type(miny) == type(maxy) == type(1)
		if minx > maxx:
			minx, maxx = maxx, minx
		if miny > maxy:
			miny, maxy = maxy, miny
		# disable for now
		# self._clonebboxes.append((minx, miny, maxx, maxy))

	def _inside_bbox(self, point):
		return 0

	# List optimizer
	def _optimize(self, ignore = ()):
		# disable for now
		return
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
	def _convert_coordinates(self, coordinates, units = UNIT_SCREEN):
		return self._window._convert_coordinates(coordinates,
					ref_rect = self._canvas, units = units)

	# convert (owner wnd) pixel coordinates to relative coordinates
	def _pxl2rel(self,coordinates):
		return self._window._pxl2rel(coordinates,
					ref_rect = self._canvas)

	# Conver color (does nothing for win32)
	def _convert_color(self, color):
		return color 

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
		if self._list[0][0]!='clear':
			raise AssertionError
		self._list[0] = ('clear',color)

	#
	# End of animation experimental methods
	##########################################

####################################################
import CheckInsideArea

class _Button:
	def __init__(self, dispobj, shape, coordinates, z, sensitive):
		self._dispobj = dispobj
		self._shape = shape
		self._coordinates = coordinates
		self._z = z
		self._sensitive = sensitive

		buttons = dispobj._buttons
		for i in range(len(buttons)):
			if buttons[i]._z <= z:
				buttons.insert(i, self)
				break
		else:
			buttons.append(self)
		self._hicolor = self._color = dispobj._fgcolor
		self._width = self._hiwidth = dispobj._linewidth
		
		if shape == 'rect':
			self._insideshape = self._insideRect
		elif shape == 'poly':
			self._insideshape = self._insidePoly
		elif shape == 'circle':
			self._insideshape = self._insideCircle
		elif shape == 'elipse':
			self._insideshape = self._insideElipse
		else:
			print 'Internal error: invalid shape type'			
			self._insideshape = self._insideRect
		
		# for now, until draw works for circle and poly
		# otherwise : crash
##		if shape == 'rect':
##			if self._color != dispobj._bgcolor:
##				self._dispobj.drawboxanchor((coordinates[0], \
##				coordinates[1],coordinates[2]-coordinates[0], \
##				coordinates[3]-coordinates[1]))

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

	def issensitive(self):
		# returns whether the button is currently sensitive
		return self._dispobj is not None and self._dispobj.isrendered() and self._sensitive

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

	def _inside(self, x, y):
		if not self._sensitive:
			# if not sensitive, no click is inside
			return 0
		return self._insideshape(x, y)

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

	# Returns true if the point is inside the elipse	
	def _insideElipse(self, x, y):
		# for now
		cx, cy, rdx, rdy = self._coordinates
		wx, wy, ww, wh = self._dispobj._window.getgeometry(UNIT_PXL)
		return CheckInsideArea.insideElipse(x*ww, y*wh, cx*ww, cy*wh, rdx*ww, rdy*wh)

	def updatecoordinates(self, coords):
		if self.is_closed(): return		
		self._coordinates = self._dispobj._pxl2rel(coords)
		self._dispobj._window.updateMouseCursor()

