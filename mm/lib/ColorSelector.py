# Module ColorSelector -- a modal dialog using FORMS and GL.
# Interface:
#	from ColorSelector import ColorSelector
#	cw = ColorSelector().init()
#	nrgb = cw.run(rgb)
# where rgb and nrgb are (r, g, b) triples with r, g, b in the range [0..255].
# If the user cancels, newrgn is the same as rgb.
# You may call run() many times for one cw object.
# There are provisions for deriving other classes with additional
# functionality, e.g. an Apply button.

from math import pi, sin, cos, atan2, sqrt
import fl, FL
import gl, GL, DEVICE

MOUSEEVENTS = DEVICE.LEFTMOUSE, DEVICE.MIDDLEMOUSE, DEVICE.RIGHTMOUSE

Done = 'ColorSelector.Done' # Harmless exception

class ColorSelector:

	def init(self):
		self.placed = 0
		self.form = self.make_form()
		self.add_buttons()
		self.add_fields()
		self.add_slider()
		return self

	def make_form(self):
		# Derived classes may override this to change the form size
		return fl.make_form(FL.FLAT_BOX, 550, 400)

	def add_buttons(self):
		# Derived classes may override or extend this
		# to install more or different buttons
		x, y, w, h = 10, 10, 90, 30
		#
		self.ok_b = self.form.add_button(FL.RETURN_BUTTON, \
			x, y, w, h, 'OK')
		self.ok_b.set_call_back(self.ok_callback, None)
		y = y + 35
		#
		self.cancel_b = self.form.add_button(FL.NORMAL_BUTTON, \
			x, y, w, h, 'Cancel')
		self.cancel_b.set_call_back(self.cancel_callback, None)
		y = y + 35
		#
		y = y + 15
		#
		self.restore_b = self.form.add_button(FL.NORMAL_BUTTON, \
			x, y, w, h, 'Restore')
		self.restore_b.set_call_back(self.restore_callback, None)
		y = y + 35

	def add_fields(self):
		# Derived classes may override this function if they want
		# to place the input fields at different locations
		f = self.form
		#
		x, y, w, h = 40, 360, 50, 30
		#
		self.h_b = f.add_input(FL.FLOAT_INPUT, x, y, w, h, 'H')
		self.h_b.set_call_back(self.hsv_callback, None)
		y = y - 40
		#
		self.s_b = f.add_input(FL.FLOAT_INPUT, x, y, w, h, 'S')
		self.s_b.set_call_back(self.hsv_callback, None)
		y = y - 40
		#
		self.v_b = f.add_input(FL.FLOAT_INPUT, x, y, w, h, 'V')
		self.v_b.set_call_back(self.hsv_callback, None)
		y = y - 40
		#
		y = y - 20
		#
		self.r_b = f.add_input(FL.INT_INPUT, x, y, w, h, 'R')
		self.r_b.set_call_back(self.rgb_callback, None)
		y = y - 40
		#
		self.g_b = f.add_input(FL.INT_INPUT, x, y, w, h, 'G')
		self.g_b.set_call_back(self.rgb_callback, None)
		y = y - 40
		#
		self.b_b = f.add_input(FL.INT_INPUT, x, y, w, h, 'B')
		self.b_b.set_call_back(self.rgb_callback, None)
		y = y - 40

	def add_slider(self):
		x, y, w, h = 110, 10, 30, 380
		self.slider = self.form.add_slider(FL.VERT_SLIDER, \
			x, y, w, h, '')
		self.slider.set_call_back(self.slider_callback, None)
		self.slider.set_slider_bounds(0.0, 1.0)

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
		self.form.show_form(place, FL.TRUE, 'Color Selector')
		#
		self.window = gl.swinopen(self.form.window)
		gl.winposition(150, 550, 0, 400)
		gl.doublebuffer()
		gl.RGBmode()
		gl.gconfig()
		gl.ortho2(-1.02, 1.02, -1.02, 1.02)
		#
		unq = []
		for e in MOUSEEVENTS:
			if not fl.isqueued(e):
				unq.append(e)
				fl.qdevice(e)
		#
		self.from_rgb(rgb)
		try:
			self.mainloop()
		except Done:
			pass
		#
		for e in unq:
			fl.unqdevice(e)
		#
		rgb = self.get_rgb()
		#
		self.form.hide_form()
		gl.winclose(self.window)
		fl.activate_all_forms()
		#
		return rgb

	def mainloop(self):
		while 1:
			obj = fl.do_forms()
			if obj == FL.EVENT:
				self.do_event()
			else:
				print 'Color Selector: unexpected', obj

	def do_event(self):
		while fl.qtest():
			dev, val = fl.qread()
			if dev in MOUSEEVENTS:
				self.do_mouse(dev, val)
			elif dev == DEVICE.REDRAW:
				self.do_redraw(dev, val)

	def do_mouse(self, dev, val):
		h, s, v = self.get_hsv()
		gl.winset(self.window)
		width, height = gl.getsize()
		wh, hh = width*0.49, height*0.49
		while gl.getbutton(dev):
			mx, my = fl.get_mouse()
			x = (mx - wh) / wh
			y = (my - hh) / hh
			angle = atan2(y, x)
			h = (angle / (2*pi)) % 1.0
			s = min(1.0, sqrt(x*x + y*y))
			self.from_hsv((h, s, v))
			self.drawmark()

	def do_redraw(self, dev, val):
		if val == self.window:
			gl.winset(val)
			gl.reshapeviewport()
			self.render()

	def ok_callback(self, dummy):
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

	def cancel_callback(self, dummy):
		self.from_rgb(self.save)
		self.render()
		raise Done

	def restore_callback(self, dummy):
		self.from_rgb(self.save)
		self.render()

	def slider_callback(self, dummy):
		h, s, v = self.get_hsv()
		v = self.slider.get_slider_value()
		self.from_hsv((h, s, v))
		self.render()

	def hsv_callback(self, dummy):
		self.from_hsv(self.get_hsv())
		self.render()

	def rgb_callback(self, dummy):
		self.from_rgb(self.get_rgb())
		self.render()

	def get_hsv(self):
		h = safe_eval(self.h_b.get_input())
		s = safe_eval(self.s_b.get_input())
		v = safe_eval(self.v_b.get_input())
		return h, s, v

	def get_rgb(self):
		r = safe_eval(self.r_b.get_input())
		g = safe_eval(self.g_b.get_input())
		b = safe_eval(self.b_b.get_input())
		return r, g, b

	def from_hsv(self, hsv):
		rgb = x_hsv_to_rgb(hsv)
		self.from_both(hsv, rgb)

	def from_rgb(self, rgb):
		hsv = x_rgb_to_hsv(rgb)
		self.from_both(hsv, rgb)

	def from_both(self, hsv, rgb):
		self.form.freeze_form()
		self.set_rgb(rgb)
		self.set_hsv(hsv)
		self.form.unfreeze_form()
		gl.winset(self.window)

	def set_hsv(self, (h, s, v)):
		self.h_b.set_input(`fix(h, 3)`)
		self.s_b.set_input(`fix(s, 3)`)
		self.v_b.set_input(`fix(v, 3)`)
		self.slider.set_slider_value(v)

	def set_rgb(self, (r, g, b)):
		self.r_b.set_input(`r`)
		self.g_b.set_input(`g`)
		self.b_b.set_input(`b`)

	def render(self):
		# Clear the background with the same gra used by the main form
		c = 170
		gl.RGBcolor(c, c, c)
		gl.clear()
		# Get current hsv setting
		h, s, v = self.get_hsv()
		# Compute center rgb value (depends on v only)
		centercolor = x_hsv_to_rgb((0.0, 0.0, v))
		# Draw the circle as n triangles, using Gouraud shading
		n = 30
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
		h, s, v = hsv = self.get_hsv()
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
def x_rgb_to_hsv((r, g, b)):
	return rgb_to_hsv((r/255.0, g/255.0, b/255.0))

# Conversions between two color systems:
# RGB: red, green, blue components
# HSV: hue, saturation, value(?) components, where:
#      H: 0 == pure red ... 0.333 == pure green ... 0.667 == pure blue
#      S: 0 == just white ... 1.0 == maximum color
#      V: 0 == just black ... 1.0 == maximum brightness
# All input and output values are floats in the range [0.0 ... 1.0]

def rgb_to_hsv((r, g, b)):
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

def hsv_to_rgb((h, s, v)):
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

def test():
	cw = ColorSelector().init()
	cw.run(255, 0, 0)

test()
