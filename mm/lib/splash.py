__version__ = "$Id$"

import os
if os.environ.has_key('CMIF_USE_DUMMY'):
	raise ImportError('No module named splash')
elif os.name == 'mac':
	raise ImportError('No module named splash')
elif os.name == 'nt':
	raise ImportError('No module named splash')
elif os.environ.has_key('CMIF_USE_GL'):
	raise ImportError('No module named splash')

import Xt, Xm, sys, X, Xcursorfont

error = 'windowinterface.error'

# try these visuals in this order
tryvisuals = [(X.TrueColor, 24),
	      (X.TrueColor, 32),
	      (X.TrueColor, 8),
	      (X.PseudoColor, 8)]

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

	def splash(self):
		self.wininit()
		if self.visual.depth < 24:
			return 0
		try:
			import splashimg
		except ImportError:
			return 0
		import imgconvert
		try:
			rdr = imgconvert.stackreader(self.imgformat, splashimg.reader())
		except imgconvert.unsupported_error:
			return 0
		main = self.main
		data = rdr.read()
		width = rdr.width
		height = rdr.height
		swidth = main.WidthOfScreen()
		sheight = main.HeightOfScreen()
		shell = main.CreatePopupShell('splash', Xt.TopLevelShell,
					      {'visual': self.visual,
					       'depth': self.visual.depth,
					       'colormap': self.colormap,
					       'mwmDecorations': 0,
					       'x': (swidth-width)/2,
					       'y': (sheight-height)/2})
		self.shell = shell
		w = shell.CreateManagedWidget('image', Xm.DrawingArea,
					      {'width': width,
					       'height': height})
		main.RealizeWidget()
		shell.Popup(0)
		gc = w.CreateGC({})
		image = self.visual.CreateImage(self.visual.depth, X.ZPixmap,
						0, data, width, height, 32, 0)
		w.AddCallback('exposeCallback', self.expose,
			      (gc.PutImage, (image, 0, 0, 0, 0, width, height)))
		gc.PutImage(image, 0, 0, 0, 0, width, height)
		self.dpy.Flush()
		import Xtdefs, time
		time.sleep(0.1)
		while Xt.Pending():
			Xt.ProcessEvent(Xtdefs.XtIMAll)
		w.DefineCursor(self.watchcursor)
		return 1

	def wininit(self):
		if self.__initialized:
			return
		import imgformat
		self.__initialized = 1
		Xt.ToolkitInitialize()
		self.dpy = dpy = Xt.OpenDisplay(None, None, 'Windowinterface',
						[], sys.argv)
## 		dpy.Synchronize(1)
		try:
			import glX, glXconst
			visual = dpy.ChooseVisual([glXconst.GLX_RGBA,
						   glXconst.GLX_RED_SIZE, 1,
						   glXconst.GLX_GREEN_SIZE, 1,
						   glXconst.GLX_BLUE_SIZE, 1])
			visuals = [visual]
		except:
			for cl, dp in tryvisuals:
				visuals = dpy.GetVisualInfo({'class': cl,
							     'depth': dp})
				if visuals:
					break
			else:
				raise error, 'no proper visuals available'
		self.visual = visual = visuals[0]
		self.colormap = cmap = visual.CreateColormap(X.AllocNone)
		if visual.c_class == X.PseudoColor:
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
			import imgcolormap, imgconvert
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
			self.imgformat = myxrgb8
		else:
			# find an imgformat that corresponds with our visual
			for name, format in imgformat.__dict__.items():
				if type(format) is not type(imgformat.rgb):
					continue
				descr = format.descr
				if descr['type'] != 'rgb' or \
				   descr['size'] != 32 or \
				   descr['align'] != 32 or \
				   descr['b2t'] != 0:
					continue
				r, g, b = descr['comp'][:3]
				if visual.red_mask   == ((1<<r[1])-1) << r[0] and \
				   visual.green_mask == ((1<<g[1])-1) << g[0] and \
				   visual.blue_mask  == ((1<<b[1])-1) << b[0]:
					break
			else:
				format = imgformat.rgb
			self.imgformat = format
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
		self.watchcursor = dpy.CreateFontCursor(Xcursorfont.watch)

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
	
splash = _splash.splash
unsplash = _splash.close
