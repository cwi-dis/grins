# Modeless dialog base class

import gl, GL, DEVICE
import fl
from FL import *
import glwindow


class Dialog() = (glwindow.glwindow)():
	#
	# Initialization routine
	#
	def init(self, (width, height, title, hint)):
		self.width = width
		self.height = height
		self.title = title
		self.hint = hint
		self.showing = 0
		self.last_origin = self.last_size = None
		self.make_form()
		return self
	#
	# Internal routine to create the form and buttons
	#
	def make_form(self):
		self.form = fl.make_form(FLAT_BOX, self.width, self.height)
		#
		# Add buttons for cancel/restore/apply/OK commands to
		# the bottom of the form, and a hint text between them.
		#
		form = self.form
		width = self.width
		#
		x, y, w, h = 2, 2, 66, 26
		#
		x = 2
		b = form.add_button(NORMAL_BUTTON, x, y, w, h, 'Cancel')
		b.set_call_back(self.cancel_callback, None)
		self.cancel_button = b
		#
		x = x + 70
		b = form.add_button(NORMAL_BUTTON, x, y, w, h, 'Restore')
		b.set_call_back(self.restore_callback, None)
		self.restore_button = b
		#
		x = x + 70
		w1 = width - 4*70 - 4
		b = form.add_text(NORMAL_TEXT, x, y, w1, h, self.hint)
		b.align = ALIGN_CENTER
		self.hint_button = b
		#
		x = width - 70 - 68
		b = form.add_button(RETURN_BUTTON, x, y, w, h, 'Apply')
		b.set_call_back(self.apply_callback, None)
		self.apply_button = b
		#
		x = x + 70
		b = form.add_button(NORMAL_BUTTON, x, y, w, h, 'OK')
		b.set_call_back(self.ok_callback, None)
		self.ok_button = b
		#
	#
	# Standard show/hide/destroy interface
	#
	def show(self):
		if not self.showing:
			if self.last_origin and self.last_size:
				x, y = self.last_origin
				w, h = self.last_size
				gl.prefposition(x, x+w, y, y+h)
				type = PLACE_FREE
			else:
				type = PLACE_SIZE
			fl.qdevice(DEVICE.WINSHUT)
			self.form.show_form(type, TRUE, self.title)
			gl.winset(self.form.window)
			gl.winconstraints()
			self.register(self.form.window)
			self.showing = 1
	#
	def hide(self):
		if self.showing:
			self.unregister()
			gl.winset(self.form.window)
			self.last_origin = gl.getorigin()
			self.last_size = gl.getsize()
			self.form.hide_form()
			self.showing = 0
	#
	def destroy(self):
		self.hide()
		# XXX collect other garbage here
		del self.form
	#
	# Callback for GL event -- equate WINSHUT with cancel button
	#
	def winshut(self):
		self.cancel_callback(self.cancel_button, None)
	#
	# Standard callbacks -- derived classes should override or extend these
	#
	def cancel_callback(self, (obj, arg)):
		self.hide()
	#
	def restore_callback(self, (obj, arg)):
		pass
	#
	def apply_callback(self, (obj, arg)):
		pass
	#
	def ok_callback(self, (obj, arg)):
		self.hide()
	#


# Test function

def test():
	d = Dialog().init(400, 200, 'Dialog.test', 'hint hint')
	d.show()
	n = 5
	while n > 0:
		fl.check_forms()
		if not d.showing:
			n = n-1
			d.show()
