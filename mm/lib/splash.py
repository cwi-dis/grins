__version__ = "$Id$"

import Xt, Xm, sys, X

def _roundi(x):
	if x < 0:
		return _roundi(x + 1024) - 1024
	return int(x + 0.5)

def _colormask(mask):
	shift = 0
	while (mask & 1) == 0:
		shift = shift + 1
		mask = mask >> 1
	if mask < 0:
		try:
			i = int(0x100000000L)
		except OverflowError:
			width = 32 - shift
		else:
			width = 64 - shift
	else:
		width = 0
		while mask != 0:
			width = width + 1
			mask = mask >> 1
	return shift, (1 << width) - 1

class _Splash:
	def __init__(self):
		self.main = None
		self.__initialized = 0

	def splash(self, file):
		self.wininit()
		if self.visual.depth != 24:
			return 0
		if 1:
			try:
				f = open(file + '.raw', 'rb')
			except IOError:
				return 0
			width = 0
			for i in range(2):
				width = width * 256 + ord(f.read(1))
			height = 0
			for i in range(2):
				height = height * 256 + ord(f.read(1))
			data = f.read()
			f.close()
		else:
			if 0:
				import imgsgi
				try:
					rdr = imgsgi.reader(file + '.rgb')
				except IOError:
					return 0
			else:
				import imgppm
				try:
					rdr = imgppm.reader(file + '.ppm')
				except IOError:
					return 0
			import imgformat
			rdr.format = imgformat.rgb
			data = rdr.read()
			width = rdr.width
			height = rdr.height
		shell = self.main.CreatePopupShell('splash', Xt.TopLevelShell,
						   {'visual': self.visual,
						   'depth': self.visual.depth,
						   'colormap': self.colormap,
						   'mwmDecorations': 0,
						    'x': 300, 'y': 200})
		self.shell = shell
		w = shell.CreateManagedWidget('image', Xm.DrawingArea,
					      {'width': width,
					       'height': height})
		self.main.RealizeWidget()
		shell.Popup(0)
		gc = w.CreateGC({})
		image = self.visual.CreateImage(self.visual.depth, X.ZPixmap,
						0, data, width, height, 32, 0)
		w.AddCallback('exposeCallback', self.expose,
			      (gc.PutImage, (image, 0, 0, 0, 0, width, height)))
##		gc.PutImage(image, 0, 0, 0, 0, width, height)
		import Xtdefs, time
		while Xt.Pending():
			Xt.ProcessEvent(Xtdefs.XtIMAll)
		time.sleep(0.5)
		while Xt.Pending():
			Xt.ProcessEvent(Xtdefs.XtIMAll)
		return 1

	def wininit(self):
		if self.__initialized:
			return
		self.__initialized = 1
		Xt.ToolkitInitialize()
		self.dpy = dpy = Xt.OpenDisplay(None, None, 'Windowinterface',
						[], sys.argv)
## 		dpy.Synchronize(1)
		visuals = dpy.GetVisualInfo({'class': X.TrueColor,
					     'depth': 24})
		if not visuals:
			visuals = dpy.GetVisualInfo({'class': X.TrueColor,
						     'depth': 8})
			if not visuals:
				visuals = dpy.GetVisualInfo(
					{'class': X.PseudoColor,
					 'depth': 8})
				if not visuals:
					raise error, 'no proper visuals available'
		self.visual = visual = visuals[0]
		self.colormap = cmap = visual.CreateColormap(X.AllocNone)
		if visual.c_class == X.PseudoColor:
			import imgformat
			r, g, b = imgformat.xrgb8.descr['comp'][:3]
			red_shift,   red_mask   = r[0], (1 << r[1]) - 1
			green_shift, green_mask = g[0], (1 << g[1]) - 1
			blue_shift,  blue_mask  = b[0], (1 << b[1]) - 1
			(plane_masks, pixels) = cmap.AllocColorCells(1, 8, 1)
			xcolors = []
			for n in range(256):
				# The colormap is set up so that the colormap
				# index has the meaning: rrrbbggg (same as
				# imgformat.xrgb8).
				xcolors.append(
					(n+pixels[0],
					 int(float((n >> red_shift) & red_mask) / red_mask * 65535. + .5),
					 int(float((n >> green_shift) & green_mask) / green_mask * 65535. + .5),
					 int(float((n >> blue_shift) & blue_mask) / blue_mask * 65535. + .5),
					  X.DoRed|X.DoGreen|X.DoBlue))
			cmap.StoreColors(xcolors)
		else:
			red_shift, red_mask = _colormask(visual.red_mask)
			green_shift, green_mask = _colormask(visual.green_mask)
			blue_shift, blue_mask = _colormask(visual.blue_mask)
		if visual.depth == 8:
			import imgcolormap, imgconvert, imgformat
			imgconvert.setquality(0)
			r, g, b = imgformat.xrgb8.descr['comp'][:3]
			xrs, xrm = r[0], (1 << r[1]) - 1
			xgs, xgm = g[0], (1 << g[1]) - 1
			xbs, xbm = b[0], (1 << b[1]) - 1
			c = []
			if (red_mask,green_mask,blue_mask) != (xrm,xgm,xbm):
				# too many locals to use map()
				for n in range(256):
					r = _roundi(((n>>xrs) & xrm) /
						    float(xrm) * red_mask)
					g = _roundi(((n>>xgs) & xgm) /
						    float(xgm) * green_mask)
					b = _roundi(((n>>xbs) & xbm) /
						    float(xbm) * blue_mask)
					c.append((r << red_shift) |
						 (g << green_shift) |
						 (b << blue_shift))
				lossy = 2
			elif (red_shift,green_shift,blue_shift)==(xrs,xgs,xbs):
				# no need for extra conversion
				myxrgb8 = imgformat.xrgb8
			else:
				# too many locals to use map()
				for n in range(256):
					r = (n >> xrs) & xrm
					g = (n >> xgs) & xgm
					b = (n >> xbs) & xbm
					c.append((r << red_shift) |
						 (g << green_shift) |
						 (b << blue_shift))
				lossy = 0
			if c:
				myxrgb8 = imgformat.new('myxrgb8',
					'X 3:3:2 RGB top-to-bottom',
					{'type': 'rgb',
					 'b2t': 0,
					 'size': 8,
					 'align': 8,
					 # the 3,3,2 below are not
					 # necessarily correct, but they
					 # are not used anyway
					 'comp': ((red_shift, 3),
						  (green_shift, 3),
						  (blue_shift, 2))})
				cm = imgcolormap.new(
					reduce(lambda x, y: x + '000' + chr(y),
					       c, ''))
				imgconvert.addconverter(
					imgformat.xrgb8,
					imgformat.myxrgb8,
					lambda d, r, src, dst, m=cm: m.map8(d),
					lossy)
			self.myxrgb8 = myxrgb8
		self.red_shift = red_shift
		self.red_mask = red_mask
		self.green_shift = green_shift
		self.green_mask = green_mask
		self.blue_shift = blue_shift
		self.blue_mask = blue_mask
		main = Xt.CreateApplicationShell('splash', Xt.ApplicationShell,
						 {'visual': visual,
						  'depth': visual.depth,
						  'colormap': cmap,
						  'mappedWhenManaged': X.FALSE,
						  'input': X.TRUE,
						  'x': 500, 'y': 500})
		self.main = main

	def expose(self, w, (func, args), call_data):
		apply(func, args)

	def close(self):
		if not self.main or not hasattr(self, 'shell'):
			return
		self.shell.DestroyWidget()
		del self.shell
		self.main = None

_splash = _Splash()

def init():
	_splash.wininit()
	shell = None
	if hasattr(_splash, 'shell'):
		shell = _splash.shell
		del _splash.shell
	items = _splash.__dict__.items()
	if shell:
		_splash.shell = shell
	return items
	
def splash(file):
	import string
	i = string.rfind(file, '.')
	if i > 0:
		file = file[:i]
	_splash.splash(file)

def unsplash():
	_splash.close()
