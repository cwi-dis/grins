__version__ = "$Id$"


# Public Objects:
# class DisplayList

# Private Objects
# class _Button

# Tuneable: width of 3d border
SIZE_3DBORDER = 2

import math,string

import win32ui, win32con, win32api
Sdk = win32ui.GetWin32Sdk()
from win32ig import win32ig
import grinsRC
import ddraw

from types import *		
from appcon import *	# draw contants
from win32mu import *	# paint utilities
from Font import findfont
from sysmetrics import pixel_per_mm_x,pixel_per_mm_y

# Icon storage
_icons = {}
import IconMixin
_icon_ids = IconMixin.ICONNAME_TO_RESID


def _get_icon(which):
	if not _icons:
		for name, resid in _icon_ids.items():
			if resid is None:
					continue
			_icons[name] = win32ui.GetApp().LoadIcon(resid)
		_icons[''] = None
	return _icons[which]

# The list cloneboxes contains all the bounding boxes
# The union of these boxes is the display region

# Draw cmds from the system including buttons (instances of _Button)
# contain relative coordinates.
# The creator must supply a _canvas i.e (x,y,w,h) to
# convert relative coordinates to pixels for the actual drawing
# The cmds are translated to pixels and inserted in a list


class _DisplayList:
	def __init__(self, window, bgcolor, units):
		self.__units = units	# default for units arg in draw methods
		self.starttime = 0
		self._window = window			
		window._displists.append(self)
		self._canvas = window._canvas
		self._buttons = []
		self._curfg = window._fgcolor
		self._fgcolor = window._fgcolor
		self._bgcolor = bgcolor
		self._linewidth = 1
		self._list = []
		self._list.append(('clear', bgcolor))
		self._optimdict = {}
		self._rendered = 0
		self._font = None
		self._curpos = 0, 0
		self._xpos = 0
		self._win32rgn = None
		self.__mediaBox = None
		self._alphaSensitivity = None

		#cloning support
		self._cloneof = None
		self._clonestart = 0
		self._clonebboxes = []
		self._clonergn=None
		
		# associate cmd names to list indices
		self.__cmddict = {}
		self.__butdict = {}

		# transparent pixel support struct: self.__transparent
		# if not None then media has transparent regions
		# and this will be a tuple of info sufficient to deside
		# at run time whether a pixel is transparent or not
		self.__transparent = None

		# sense direct draw
		self._directdraw = 0
		self._issimple = 0
		if hasattr(window._topwindow,'CreateSurface'):
			self._directdraw = 1
			 
	# Clones this display list
	def clone(self):
		w = self._window
		new = _DisplayList(w, self._bgcolor, units=self.__units)
		# copy all instance variables
		new._list = self._list[:]
		new._font = self._font
		new.__cmddict = self.__cmddict
		new.__butdict = self.__butdict
		if self._win32rgn:
			new._win32rgn=win32ui.CreateRgn()
			new._win32rgn.CopyRgn(self._win32rgn)
		if self._rendered:
			new._cloneof = self
			new._clonestart = len(self._list)
		for key, val in self._optimdict.items():
			new._optimdict[key] = val
		return new

	def __repr__(self):
		str=''
		if self._rendered:str = str+ 'rendered '
		if not hasattr(self,'_list'):return str+'closed'
		for i in range(self._clonestart, len(self._list)):
			str = str + self._list[i][0]+','
		return '<' + str +'>'


##====================================== Rendering
	def isrendered(self):
		# returns true if currently rendered
		return self._window and self._window._active_displist is self

	def render(self):
		import time
		self.starttime = time.time()
		self._issimple = self.isSimple()
		wnd = self._window
		for b in self._buttons:
			b._highlighted = 0 
		wnd._active_displist = self
##		wnd.pop()
		wnd.update()

	# Render the display list on dc within the region	
	def _render(self, dc, region=None, clear=1):
		self._rendered = 1
		clonestart = self._clonestart
		if not self._cloneof or self._cloneof is not self._window._active_displist:
			clonestart = 0
		
		if not clear and clonestart==0:
			clonestart = 1

		for i in range(clonestart, len(self._list)):
			self._do_render(self._list[i],dc, region)

		for b in self._buttons:
			if b._highlighted:b._do_highlight()
	
	# Optimized rendering for simple display lists on a direct draw surface	
	# we should and we can implement here what we need for player rendering  
	def _ddsrender(self, dds, dst, rgn, clear=1, mediadisplayrect=None, fit='hidden'):
		self._rendered = 1
		clonestart = self._clonestart
		if not self._cloneof or self._cloneof is not self._window._active_displist:
			clonestart = 0
		
		if not clear and clonestart==0:
			clonestart = 1

		x, y, w, h = dst
		if rgn:
			l, t, r, b = rgn.GetRgnBox()[1]
			xc, yc, wc, hc = l, t, r-l, b-t
		else:
			xc, yc, wc, hc = dst

		for i in range(clonestart, len(self._list)):
			entry = self._list[i]
			cmd = entry[0]
			wnd = self._window
			if cmd == 'clear' and entry[1]:
				r, g, b = entry[1]
				convbgcolor = dds.GetColorMatch((r,g,b))
				dds.BltFill((xc, yc, xc+wc, yc+hc), convbgcolor)
			elif cmd == 'image':
				mask, image, flags, src_x, src_y,dest_x, dest_y, width, height,rcKeep=entry[1:]
				if mediadisplayrect:
					dest_x, dest_y, width, height = mediadisplayrect

				# src rect taking into account fit
				rcSrc = wnd._getmediacliprect(rcKeep[2:], (dest_x, dest_y, width, height), fit=fit)

				# split rects
				ls, ts, rs, bs = wnd.ltrb(rcSrc)
				
				xd, yd, wd, hd = dest_x, dest_y, width, height
				ld, td, rd, bd = x+xd, y+yd, x+xd+wd, y+yd+hd
				
				# destination clip
				ldc, tdc, rdc, bdc = wnd.ltrb( wnd.rectAnd((xc, yc, wc, hc), (ld, td, rd-ld, bd-td)) )
				
				# find src clip ltrb given the destination clip
				lsc, tsc, rsc, bsc =  wnd._getsrcclip((ld, td, rd, bd), (ls, ts, rs, bs), (ldc, tdc, rdc, bdc))
				
				if wnd._canscroll: 	
					dx, dy = wnd._scrollpos
					lsc, tsc, rsc, bsc = lsc+dx, tsc+dy, rsc+dx, bsc+dy

				try:
					#print 'Blt: ',lsc, tsc, rsc, bsc, '->', ldc, tdc, rdc, bdc
					dds.Blt((ldc, tdc, rdc, bdc), image, (lsc, tsc, rsc, bsc), flags)
				except ddraw.error, arg:
 					print arg

			elif cmd == 'fbox':
				dest_x, dest_y, width, height = entry[2]
				width = width - dest_x
				height = height - dest_y
				if mediadisplayrect:
					dest_x, dest_y, width, height = mediadisplayrect
				xdc, ydc, wdc, hdc = wnd.rectAnd((x+dest_x, y+dest_y, width, height), (xc, yc, wc, hc))
				r, g, b = entry[1]
				convcolor = dds.GetColorMatch((r,g,b))
				dds.BltFill((xdc,ydc,xdc+wdc,ydc+hdc), convcolor)
 

	def close(self):
		wnd = self._window
		if wnd is None:
			return
		for b in self._buttons[:]:
			b.close()
		wnd._displists.remove(self)
		self._window = None
		for d in wnd._displists:
			if d._cloneof is self:
				d._cloneof = None
		if wnd._active_displist is self:
			wnd._active_displist = None
			wnd.update()
		if self._win32rgn:
			self._win32rgn.DeleteObject()
			del self._win32rgn
			self._win32rgn=None
		del self._cloneof
		del self._optimdict
		del self._list
		del self._buttons
		del self._font
				
	# Render the entry draw command
	def _do_render(self, entry, dc, region):
		cmd = entry[0]
		w = self._window
		if cmd == 'clear' and entry[1]:
			dc.FillSolidRect(self._canvas,RGB(entry[1]))
		elif cmd == 'fg':
			self._curfg = entry[1]
		elif cmd == 'image':
			mask, image, flags, src_x, src_y,dest_x, dest_y, width, height,rcKeep=entry[1:]
			if region and not self._overlap_xywh(region, (dest_x, dest_y, width, height)):
				return
			if self._directdraw:
				imghdc = image.GetDC()
				if imghdc:
					imgdc = win32ui.CreateDCFromHandle(imghdc)
					dc.BitBlt((dest_x, dest_y),(width, height),imgdc,(0, 0), win32con.SRCCOPY)
					imgdc.Detach()
					image.ReleaseDC(imghdc)				
			else:
				win32ig.render(dc.GetSafeHdc(),self._bgcolor,
					mask, image, src_x, src_y,dest_x, dest_y, width, height,rcKeep, aspect="none" )
		elif cmd == 'video':
			func=entry[1]
			apply(func,(dc,))
		elif cmd== 'obj':
			entry[1].draw(dc)
		elif cmd == 'line':
			fg = entry[1]
			points = entry[2]
			x0, y0 = points[0]
			for x, y in points[1:]:
				DrawLine(dc,(x0, y0, x, y),fg)
				x0, y0 = x, y
		elif cmd == '3dhline':
			color1, color2, x0, x1, y = entry[1:]
			if not self._overlap_xywh(region, (x0, y, x1-x0, 1)):
				return
			DrawLine(dc, (x0, y, x1, y), color1)
			DrawLine(dc, (x0, y+1, x1, y+1), color2)
		elif cmd == 'box':
			# XXXX should we subtract 1 from right and bottom edges
			if not self._overlap_ltrb(region, entry[1]):
				return
			DrawRectangle(dc,entry[1],self._curfg)
		elif cmd == 'anchor':
			if not self._overlap_ltrb(region, entry[1]):
				return
			DrawRectangle(dc,entry[1],self._curfg)
			# debug: DrawRectangle(dc,entry[1],(255,0,0))
		elif cmd == 'fbox':
			if not self._overlap_ltrb(region, entry[2]):
				return
			dc.FillSolidRect(entry[2],RGB(entry[1]))
		elif cmd == 'stipplebox':
			if not self._overlap_ltrb(region, entry[2]):
				return
			brush = entry[1]
			rect = entry[2]
			x, y = rect[:2]
			dx, dy = dc.GetViewportOrg()
			x, y = x + dx, y + dy
			oldmode = dc.SetBkMode(win32con.TRANSPARENT)
			oldpen = dc.SelectStockObject(win32con.NULL_PEN)
			brush.UnrealizeObject()
			oldorg = dc.SetBrushOrg((x % 8, y % 8))
			oldbrush = dc.SelectObject(brush)
			dc.Rectangle(rect)
			if 1: # begin trick for more dense grid pattern 
				brush.UnrealizeObject()
				dc.SetBrushOrg(((x + 4) % 8, y % 8))
				dc.SelectObject(brush)
				dc.Rectangle(rect)
				# end_trick
			oldbrush.UnrealizeObject()
			dc.SetBrushOrg(oldorg)
			dc.SelectObject(oldbrush)
			dc.SelectObject(oldpen)
			dc.SetBkMode(oldmode)
		elif cmd == 'font':
			#dc.SetFont(entry[1])
			pass
		elif cmd == 'linewidth':
			#gc.line_width = entry[1]
			pass			
		elif cmd == 'fpolygon':
			fg = entry[1] 
			FillPolygon(dc,entry[2], fg)
		elif cmd == '3dbox':
			cl, ct, cr, cb = entry[1]
			l, t, w, h = entry[2]
			if not self._overlap_xywh(region, (l, t, w, h)):
				return
			r, b = l + w , t + h 
			# l, r, t, b are the corners
			l1 = l + SIZE_3DBORDER
			t1 = t + SIZE_3DBORDER
			r1 = r - SIZE_3DBORDER
			b1 = b - SIZE_3DBORDER
			# draw left side
			FillPolygon(dc, [(l,t), (l1,t1), (l1,b1), (l,b)], cl)
			# draw top side
			FillPolygon(dc, [(l,t), (r,t), (r1,t1), (l1,t1)], ct)
			# draw right side
			FillPolygon(dc, [(r1,t1), (r,t), (r,b), (r1,b1)], cr)
			# draw bottom side
			FillPolygon(dc, [(l1,b1), (r1,b1), (r,b), (l,b)], cb)
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
##			fg = cl 
##			ls = [(l1,t1),(ll,tt),(ll,bb),(l1,b1)]
##			FillPolygon(dc,ls, fg)
##			fg = ct
##			ls = [(l1,t1),(r1,t1),(rr,tt),(ll,tt)]
##			FillPolygon(dc,ls, fg)
##			fg = cr
##			ls = [(r1,t1),(r1,b1),(rr,bb),(rr,tt)]
##			FillPolygon(dc,ls, fg)
##			fg = cb
##			ls = [(l1,b1),(ll,bb),(rr,bb),(r1,b1)]
##			FillPolygon(dc,ls, fg)
		elif cmd == 'diamond':
			fg = self._fgcolor
			x, y, w, h = entry[1]
			if not self._overlap_xywh(region, (x, y, w, h)):
				return
			
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
			if not self._overlap_xywh(region, (x, y, w, h)):
				return

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
			if not self._overlap_xywh(region, (x, y, w, h)):
				return
			
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
			if not self._overlap_xywh(region, entry[2]):
				return
			DrawLine(dc,entry[2],fg)
			FillPolygon(dc,entry[3], fg)
		elif cmd == 'text':
			modeorg = dc.SetBkMode(win32con.TRANSPARENT)
			dc.SetTextAlign(win32con.TA_BOTTOM)
			clr_org=dc.SetTextColor(RGB(entry[1]))
			horg=dc.SelectObjectFromHandle(entry[2].handle())
			x,y,str=entry[3:]
			dc.TextOut(x,y,str)
			dc.SetTextColor(clr_org)
			dc.SelectObjectFromHandle(horg)
			dc.SetBkMode(modeorg)
		elif cmd == 'icon':
			if entry[2] != None:
				x, y, w, h = entry[1]
				if not self._overlap_xywh(region, (x, y, w, h)):
					return
				dc.DrawIcon((x, y), entry[2])

	# Return true if the ltrb and xywh rectangles have overlap
	def _overlap_xywh(self, region, (x, y, w, h)):
		if not region:
			return 1	# default is overlap
		l, t, r, b = region
		if x>r or x+w < l:
			return 0
		if y>b or y+h < t:
			return 0
		return 1

	def _overlap_ltrb(self, region, (l, t, r, b)):
		return self._overlap_xywh(region, (l, t, r-l, b-t))
		
	# Returns true if this is closed
	def is_closed(self):
		return self._window is None

	# Alias for render
	def render_now(self):
		self.render()	
	
	# Set forground color
	def fgcolor(self, color):
		self._list.append(('fg', color))
		self._fgcolor = color

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
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		image, mask, src_x, src_y, dest_x, dest_y, width, height,rcKeep = \
		       self._window._prepare_image(file, crop, fit, center, coordinates, clip, align, units)
		
		flags = ddraw.DDBLT_WAIT
		if self._directdraw:
			image, flags = self.createDDSImage(image, mask, src_x, src_y, dest_x, dest_y, width, height,rcKeep)
		self._list.append(('image', mask, image, flags, src_x, src_y,
				   dest_x, dest_y, width, height,rcKeep))
		self._optimize((2,))
		self._update_bbox(dest_x, dest_y, dest_x+width, dest_y+height)
		x, y, w, h = self._canvas
		
		mediaBox = float(dest_x - x) / w, float(dest_y - y) / h, \
		       float(width) / w, float(height) / h
		
		if self._directdraw: # XXX: i.e. player, revisit this
			# preset media display rect and scale for animation
			self._window.setmediadisplayrect( (dest_x, dest_y, width, height) )
			self._window.setmediafit(fit)
			self.setMediaBox(mediaBox)

		if units == UNIT_PXL:
			return dest_x - x, dest_y - y, width, height
		else:
			return mediaBox

	# set the area where the media is visible
	# mediaBox is a tuple of: 
	# top, left, width, height
	# all values are expressed in pourcent and relative to the window
	def setMediaBox(self, mediaBox):
		self.__mediaBox = mediaBox
		
	# check if the x/y point is inside the media box. currently, 
	# the method is called from win32window module
	def _insideMedia(self, x, y):
		if self.__mediaBox == None:
			# in this case, assume that the media area fill the display list area
			return 1
			
		left, top, width, height = self.__mediaBox
		if left <= x <= left+width and top <= y <= top+height:
			return 1
			
		return 0

	# set the media sensitivity
	# value is percentage value (0 == 'opaque', 100 == 'transparent')
	def setAlphaSensitivity(self, value):
		self._alphaSensitivity = value
		
	def createDDSImage(self, image, mask, src_x, src_y, dest_x, dest_y, width, height,rcKeep):
		if not self._directdraw: return image
		tw = self._window._topwindow
		x, y, w, h = rcKeep
		dds = tw.CreateSurface(w, h)
		trans_rgb = win32ig.gettransp(image)
		if trans_rgb:
			convbgcolor = dds.GetColorMatch(trans_rgb)
			dds.BltFill((0, 0, w, h), convbgcolor)
			self.__transparent = (dds, convbgcolor, (dest_x, dest_y, width, height))
		try:
			imghdc = dds.GetDC()
		except:
			return dds
		win32ig.render(imghdc, self._bgcolor,
				mask, image, src_x, src_y, 0, 0, w, h, rcKeep, aspect="none" )
		dds.ReleaseDC(imghdc)
		flags = ddraw.DDBLT_WAIT
		if trans_rgb:
			flags = ddraw.DDBLT_WAIT | ddraw.DDBLT_KEYSRC
			dds.SetColorKey(ddraw.DDCKEY_SRCBLT, (convbgcolor, convbgcolor))
		return dds, flags

	def isSimple(self):
		for i in range(0, len(self._list)):
			if self._list[i][0] not in ('image', 'clear', 'fg', 'fbox'):
				return 0
		return 1

	# point x, y coordinates are in px relative to owner wnd
	# point is inside owner wnd
	# sensitivity when not 'opaque' should be set before calling this query method	
	def isTransparent(self, point):
		x, y = point
		xp, yp = self._window._pxl2rel(point)
		# if not in media box then its transparent
		if not self._insideMedia(xp,yp):
			return 1
		if self._alphaSensitivity is None or self._alphaSensitivity == 0:
			return 0
		elif self._alphaSensitivity == 100:
			return 1
		else:
			# point is inside media
			# can be a transparent point?
			if  self.__transparent is None:
				return 0
			# yes, it can.
			# check pixel color
			# offset x, y to media box
			dds, ddcolor, ltrb = self.__transparent
			lm, tm = ltrb[:2]
			pxcolor = dds.GetPixelColor((x-lm, y-tm))
			if pxcolor == ddcolor:
				return 1
			return 0
		assert 0, 'invalid sensitivity value %s' % self._alphaSensitivity
		 
	#############################################
	# draw primitives

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
		if units is None:
			units = self.__units
		if self._rendered:
			raise error, 'displaylist already rendered'
		x, y, w, h = self._convert_coordinates(coordinates, units=units)
		try:
			brush = win32ui.CreateBrush(win32con.BS_HATCHED, 
				RGB(self._convert_color(color)), win32con.HS_DIAGCROSS)
		except win32ui.error, arg:
			print arg
			return
		self._list.append(('stipplebox', brush,
				   (x, y, x+w, y+h)))
		self._optimize((1,))
		self._update_bbox(x, y, x+w, y+h)
##		return x, y, x+w, y+h

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
		self._clonebboxes.append((minx, miny, maxx, maxy))
		if not self._win32rgn:
			self._win32rgn=win32ui.CreateRgn()
			self._win32rgn.CreateRectRgn((minx, miny, maxx, maxy))
		else:
			addrgn=win32ui.CreateRgn()
			addrgn.CreateRectRgn((minx, miny, maxx, maxy))
			self._win32rgn.CombineRgn(self._win32rgn,addrgn,win32con.RGN_OR)
			addrgn.DeleteObject()
			del addrgn

	def _inside_bbox(self, point):
		if self._win32rgn:
			return self._win32rgn.PtInRegion(point)
		return 0

	# List optimizer
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

		
	# Object support
	# Insert an obj in the list
	def drawobj(self,obj):
		self.AddObj(obj)
	# Insert an obj in the list
	def AddObj(self,obj):
		self._list.append(('obj',obj))
		l,t,r,b=obj.getbbox()
		self._update_bbox(l,t,r,b)


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

	######################################
	# Animation experimental methods

	def updatecoordinates(self, coords):
		if self.is_closed(): return		
		self._coordinates = self._dispobj._pxl2rel(coords)
		self._dispobj._window.updateMouseCursor()

	# End of animation experimental methods
	##########################################
