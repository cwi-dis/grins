__version__ = "$Id$"

# Module ColorSelector -- a modal dialog using FORMS and GL (and glwindow).
# Interface:
#	import ColorSelector
#	nrgb = ColorSelector.run(rgb)
# where rgb and nrgb are (r, g, b) triples with r, g, b in the range [0..255].
# If the user cancels, newrgn is the same as rgb.
# There are some provisions for deriving classes with additional
# functionality, e.g. an Apply button, if you need them.


from math import pi, sin, cos, atan2, sqrt
import fl, FL
import gl, GL, DEVICE
import glwindow


MOUSEEVENTS = DEVICE.LEFTMOUSE, DEVICE.MIDDLEMOUSE, DEVICE.RIGHTMOUSE

Done = 'ColorSelector.Done' # Harmless exception

form_template = None


class ColorSelector(glwindow.glwindow):

	def __init__(self):
		self.placed = 0
		self.make_form()

	def __repr__(self):
		return '<ColorSelector instance, form=' + `self.form` + '>'

	def make_form(self):
		global form_template
		import flp
		if form_template is None:
			form_template = \
				flp.parse_form('ColorSelectorForm', 'form')
		flp.create_full_form(self, form_template)

	def run(self, rgb):
		self.save = rgb
		#
		fl.deactivate_all_forms()
		#
		if self.placed:
			place = FL.PLACE_POSITION
		else:
			place = FL.PLACE_SIZE
			self.placed = 1
		#XXX self.form.set_object_focus(self.r_b)
		self.form.show_form(place, FL.TRUE, 'CMIF Color Editor')
		glwindow.register(self, self.form.window)
		#
		wd = self.wheel_dummy
		self.wheel = Wheel(self, wd.x, wd.y, wd.w, wd.h)
		bd = self.box_dummy
		self.box = Box(self, bd.x, bd.y, bd.w, bd.h)
		#
		self.from_rgb(rgb, 1)
		try:
			dummy = fl.do_forms()
		except Done:
			pass
		#
		rgb = self.get_rgb()
		#
		glwindow.unregister(self)
		self.form.hide_form()
		self.wheel.destroy()
		fl.activate_all_forms()
		#
		return rgb

	def ok_callback(self, *dummy):
		# Honor changes to the input fields that we haven't
		# seen yet because the user didn't press TAB
		# (I still think FORMS should do this though)
		for b in self.r_b, self.g_b, self.b_b:
			if b.focus:
				self.rgb_callback((b, None))
		for b in self.h_b, self.s_b, self.v_b:
			if b.focus:
				self.hsv_callback((b, None))
		raise Done

	def cancel_callback(self, *dummy):
		self.from_rgb(self.save, 1)
		raise Done

	def restore_callback(self, *dummy):
		self.from_rgb(self.save, 1)

	def slider_callback(self, *dummy):
		h, s, v = self.get_hsv()
		v = self.slider.get_slider_value()
		self.from_hsv((h, s, v), 1)

	def hsv_callback(self, *dummy):
		self.from_hsv(self.get_hsv(), 1)

	def rgb_callback(self, *dummy):
		self.from_rgb(self.get_rgb(), 1)

	def get_hsv(self):
		h = safe_eval(self.h_b.get_input())
		s = safe_eval(self.s_b.get_input())
		v = safe_eval(self.v_b.get_input())
		h = min(1.0, max(0.0, h))
		s = min(1.0, max(0.0, s))
		v = min(1.0, max(0.0, v))
		return h, s, v

	def get_rgb(self):
		r = safe_eval(self.r_b.get_input())
		g = safe_eval(self.g_b.get_input())
		b = safe_eval(self.b_b.get_input())
		r = min(255, max(0, r))
		g = min(255, max(0, g))
		b = min(255, max(0, b))
		return r, g, b

	def from_hsv(self, hsv, redrawflag):
		rgb = x_hsv_to_rgb(hsv)
		self.from_both(hsv, rgb, redrawflag)

	def from_rgb(self, rgb, redrawflag):
		hsv = x_rgb_to_hsv(rgb)
		self.from_both(hsv, rgb, redrawflag)

	def from_both(self, hsv, rgb, redrawflag):
		self.form.freeze_form()
		self.set_rgb(rgb)
		self.set_hsv(hsv)
		self.form.unfreeze_form()
		#
		self.wheel.setwin()
		if redrawflag:
			self.wheel.render()
		else:
			self.wheel.drawmark()
		#
		self.box.setwin()
		self.box.render()

	def set_hsv(self, hsv):
		h, s, v = hsv
		self.h_b.set_input(`fix(h, 3)`)
		self.s_b.set_input(`fix(s, 3)`)
		self.v_b.set_input(`fix(v, 3)`)
		self.slider.set_slider_value(v)

	def set_rgb(self, rgb):
		r, g, b = rgb
		self.r_b.set_input(`r`)
		self.g_b.set_input(`g`)
		self.b_b.set_input(`b`)

	def winshut(self):
		self.cancel_callback(None)


class Wheel(glwindow.glwindow):

	def __init__(self, parent, x, y, w, h):
		self.parent = parent
		wid = gl.swinopen(parent.form.window)
		glwindow.glwindow.__init__(self, wid)
		x, y, w, h = int(x), int(y), int(w), int(h)
		gl.winposition(x, x+w-1, y, y+h-1)
		gl.doublebuffer()
		gl.RGBmode()
		gl.gconfig()
		gl.ortho2(-1.02, 1.02, -1.02, 1.02)
		#
		for e in MOUSEEVENTS:
			if not fl.isqueued(e):
				fl.qdevice(e)
		#
		glwindow.register(self, wid)

	def __repr__(self):
		return '<Wheel instance, wid=' + `self.wid` + '>'

	def destroy(self):
		glwindow.unregister(self)
		gl.winclose(self.wid)

	def mouse(self, dev, val):
		width, height = gl.getsize()
		h, s, v = self.parent.get_hsv()
		wh, hh = width*0.49, height*0.49
		while gl.getbutton(dev):
			self.setwin()
			mx, my = fl.get_mouse()
			x = (mx - wh) / wh
			y = (my - hh) / hh
			angle = atan2(y, x)
			h = (angle / (2*pi)) % 1.0
			s = min(1.0, sqrt(x*x + y*y))
			self.parent.from_hsv((h, s, v), 0)

	def redraw(self):
		gl.reshapeviewport()
		self.render()

	def render(self):
		# Clear the background to the same gray used by the main form
		c = 170 # XXX Empirically found value...
		gl.RGBcolor(c, c, c)
		gl.clear()
		# Get current hsv setting
		h, s, v = self.parent.get_hsv()
		# Compute center rgb value (depends on v only)
		centercolor = x_hsv_to_rgb((0.0, 0.0, v))
		# Draw the circle as n triangles, using Gouraud shading
		n = 26
		for i in range(n):
			gl.bgnpolygon()
			gl.RGBcolor(centercolor)
			gl.v2f(0, 0)
			a = pi*2*i/n
			h = 1.0 * i / n
			gl.RGBcolor(x_hsv_to_rgb((h, 1.0, v)))
			gl.v2f(cos(a), sin(a))
			i = i+1
			a = pi*2*i/n
			h = 1.0 * i / n
			gl.RGBcolor(x_hsv_to_rgb((h, 1.0, v)))
			gl.v2f(cos(a), sin(a))
			gl.endpolygon()
		#
		gl.swapbuffers()
		#
		self.drawmark()

	def drawmark(self):
		# Draw a mark around current color in the pop-up planes
		# Get current hsv setting
		h, s, v = hsv = self.parent.get_hsv()
		r, g, b = x_hsv_to_rgb(hsv)
		# Compute location of current hsv in the circle
		a = h*pi*2
		x, y = s*cos(a), s*sin(a)
		eps = 0.02
		#
		gl.drawmode(GL.PUPDRAW)
		gl.color(0)
		gl.clear()
		if 0.3*r + 0.59*g + 0.11*b >= 127:
			gl.mapcolor(1, 0, 0, 0)
		else:
			gl.mapcolor(1, 255, 255, 255)
		gl.color(1)
		gl.bgnclosedline()
		gl.v2f(x-eps, y-eps)
		gl.v2f(x-eps, y+eps)
		gl.v2f(x+eps, y+eps)
		gl.v2f(x+eps, y-eps)
		gl.endclosedline()
		gl.drawmode(GL.NORMALDRAW)


class Box(glwindow.glwindow):

	def __init__(self, parent, x, y, w, h):
		self.parent = parent
		wid = gl.swinopen(parent.form.window)
		glwindow.glwindow.__init__(self, wid)
		x, y, w, h = int(x), int(y), int(w), int(h)
		##gl.winposition(x+5, x+w-6, y+5, y+h-6)
		gl.winposition(x, x+w-1, y, y+h-1)
		gl.RGBmode()
		gl.gconfig()
		gl.ortho2(-1.0, 1.0, -1.0, 1.0)
		#
		glwindow.register(self, wid)

	def __repr__(self):
		return '<Box instance, wid=' + `self.wid` + '>'

	def destroy(self):
		glwindow.unregister(self)
		gl.winclose(self.wid)

	def redraw(self):
		gl.reshapeviewport()
		self.render()

	def render(self):
		gl.RGBcolor(self.parent.save)
		gl.bgnpolygon()
		gl.v2f( 0.0, -1.0)
		gl.v2f( 0.0,  1.0)
		gl.v2f(-1.0,  1.0)
		gl.v2f(-1.0, -1.0)
		gl.endpolygon()
		gl.RGBcolor(self.parent.get_rgb())
		gl.bgnpolygon()
		gl.v2f(0.0, -1.0)
		gl.v2f(0.0,  1.0)
		gl.v2f(1.0,  1.0)
		gl.v2f(1.0, -1.0)
		gl.endpolygon()


# Evaluate a numeric string typed in an input field -- return 0 if problems
def safe_eval(str):
	try:
		return eval(str)
	except:
		return 0

# Truncate a floating point number to the nearest multiple of 10**n
def fix(x, n):
	from math import floor
	if n < 0:
		f = pow(10.0, n)
	else:
		f = float(pow(10, n)) # Make an exact 
	x = x * f
	x = floor(x + 0.5)
	x = x / f
	return x


# Convert hsv to rgb-scaled-to-255
def x_hsv_to_rgb(hsv):
	r, g, b = hsv_to_rgb(hsv)
	return int(r*255), int(g*255), int(b*255)

# Convert rgb-scaled-to-255 to hsv
def x_rgb_to_hsv(rgb):
	r, g, b = rgb
	return rgb_to_hsv((r/255.0, g/255.0, b/255.0))


# Conversions between two color systems:
# RGB: red, green, blue components
# HSV: hue, saturation, value(?) components, where:
#      H: 0 == pure red ... 0.333 == pure green ... 0.667 == pure blue
#      S: 0 == just white ... 1.0 == maximum color
#      V: 0 == just black ... 1.0 == maximum brightness
# All input and output values are floats in the range [0.0 ... 1.0]

def rgb_to_hsv(rgb):
	r, g, b = rgb
	maxc = max(r, g, b)
	minc = min(r, g, b)
	v = maxc
	if minc == maxc:
		return 0.0, 0.0, v
	s = (maxc-minc)/maxc
	rc = (maxc-r)/(maxc-minc)
	gc = (maxc-g)/(maxc-minc)
	bc = (maxc-b)/(maxc-minc)
	if r == maxc:
		h = bc-gc
	elif g == maxc:
		h = 2.0+rc-bc
	else:
		h = 4.0+gc-rc
	h = h/6.0
	if h < 0.0:
		h = h + 1.0
	return h, s, v

def hsv_to_rgb(hsv):
	h, s, v = hsv
	if s == 0.0:
		return v, v, v
	i = int(h*6.0)
	f = (h*6.0)-i
	p = v*(1.0-s)
	q = v*(1.0-s*f)
	t = v*(1.0-s*(1.0-f))
	if i in (0, 6): return v, t, p
	if i == 1: return q, v, p
	if i == 2: return p, v, t
	if i == 3: return p, q, v
	if i == 4: return t, p, v
	if i == 5: return v, p, q
	raise RuntimeError, ('hsv_to_rgb', (h, s, v), '->', (i, h, f))


a_selector = None

def run(rgb):
	global a_selector
	if a_selector is None:
		a_selector = ColorSelector()
	return a_selector.run(rgb)

def test():
	run((255, 255, 255))

import sys
if sys.argv == ['']: test()
