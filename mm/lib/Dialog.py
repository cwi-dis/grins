# Modeless dialog base classes.
#
# Use these classes as bases for your own dialog classes.
#
# BasicDialog creates an empty form and can show and hide it.
# While the form is shown, it is registered with glwindow, so a
# derived class can define event handling methods; by default,
# the winshut() handler hides the window.
# When the form is hidden and then shown again, it appears where
# is was last seen.  The user can always resize the window.
#
# Dialog adds Cancel/Restore/Apply/OK buttons with callbacks and a
# hint string, and has a winshut handler that calls the cancel callback.
#
# Besides their methods, these classes define these instance variables
# that may be used by derived classes:
# form			the form
# showing		true when the form is shown
# width, height		form dimensions
# title			window title (better use settitle() method though)
# border		nonzero (default) if the window has a border
#			(use x.setborder(flag) to change it)
# last_geometry		the window's geometry when last hidden, or None
#
# The Dialog class also defines cancel_button, restore_button,
# hint_button (really a text object), apply_button and ok_button.
#
# Class GLDialog is similar to BasicDialog but uses plain GL windows
# instead of FORMS windows.  It uses self.wid instead of self.form
# self.showing.

import gl, GL, DEVICE
import fl
from FL import *
import glwindow


class BasicDialog(glwindow.glwindow):
	#
	# Initialization.
	# Derived classes must extend this method.
	# XXX Shouldn't have (width, height) argument?
	#
	def init(self, (width, height, title)):
		self.width = int(width)
		self.height = int(height)
		self.title = title
		self.showing = 0
		self.last_geometry = None
		self.border = 1
		self.make_form()
		return self
	#
	# Make the form.
	# Derived classes are expected to override this method.
	#
	def make_form(self):
		self.form = fl.make_form(FLAT_BOX, self.width, self.height)
	#
	# Standard show/hide/destroy interface.
	#
	def show(self):
		if self.showing:
			self.pop()
			return
		self.load_geometry()
		self.fix_geometry()
		glwindow.setgeometry(self.last_geometry)
		self.form.show_form(PLACE_FREE, self.border, self.title)
		glwindow.register(self, self.form.window)
		self.showing = 1
		self.setwin()
		gl.winconstraints()
		fl.qdevice(DEVICE.WINSHUT)
	#
	def hide(self):
		if self.showing:
			self.save_geometry()
			glwindow.unregister(self)
			self.form.hide_form()
			self.showing = 0
	#
	def setwin(self):
		if self.showing:
			gl.winset(self.form.window)
		else:
			print 'BasicDialog: setwin() of hidden window'
	#
	def settitle(self, title):
		if title == self.title:
			return
		self.title = title
		if self.showing:
			self.setwin()
			gl.wintitle(self.title)
	#
	def setborder(self, border):
		if border == self.border:
			return
		self.border = border
		if self.showing:
			self.setwin()
			if not self.border:
				gl.noborder()
			gl.winconstraints()
	#
	def pop(self):
		if self.showing:
			self.setwin()
			gl.winpop()
	#
	def is_showing(self):
		return self.showing
	#
	def get_geometry(self):
		if self.showing:
			self.setwin()
			self.last_geometry = glwindow.getgeometry()
	#
	def destroy(self):
		self.hide()
	#
	def winshut(self):
		self.hide()
	#
	def fix_geometry(self):
		if self.last_geometry <> None:
			x, y, w, h = self.last_geometry
		else:
			x, y, w, h = -1, -1, 0, 0
		if w == 0: w = self.width
		if h == 0: h = self.height
		self.last_geometry = x, y, w, h
	#
	# Clients can override these methods to copy self.last_geometry
	# from/to more persistent storage:
	#
	def load_geometry(self):
		pass
	#
	def save_geometry(self):
		self.get_geometry() # This is needed for hide()


class Dialog(BasicDialog):
	#
	# Initialization routine.
	#
	def init(self, (width, height, title, hint)):
		self.hint = hint
		return BasicDialog.init(self, width, height, title)
	#
	# Internal routine to create the form and buttons.
	#
	def make_form(self):
		self.form = fl.make_form(FLAT_BOX, self.width, self.height)
		#
		# Add buttons for Cancel/Restore/Apply/OK commands near
		# the bottom of the form, and a hint text between them.
		#
		form = self.form
		width = self.width
		#
		x, y, w, h = 0, 0, 66, 26
		#
		x = 0
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
		w1 = width - 4*70
		b = form.add_text(NORMAL_TEXT, x, y, w1, h, self.hint)
		b.align = ALIGN_CENTER
		self.hint_button = b
		#
		x = width - 70 - 70
		b = form.add_button(NORMAL_BUTTON, x, y, w, h, 'Apply')
		b.set_call_back(self.apply_callback, None)
		self.apply_button = b
		#
		x = x + 70
		b = form.add_button(RETURN_BUTTON, x, y, w, h, 'OK')
		b.set_call_back(self.ok_callback, None)
		self.ok_button = b
		#
	#
	# Callback for GL event maps WINSHUT to the cancel button.
	#
	def winshut(self):
		self.cancel_callback(self.cancel_button, None)
	#
	# Standard callbacks.
	# Derived classes should override or extend these methods.
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
	# A standard way of changing the appearance of the
	# Restore, Apply and Cancel buttons.
	#
	def activate_buttons(self, active):
		if active: bt = UP_BOX
		else: bt = FRAME_BOX
		for b in self.ok_button,self.apply_button,self.restore_button:
			b.boxtype = bt
	#


class GLDialog(glwindow.glwindow):
	#
	def init(self, title):
		self.title = title
		self.wid = 0
		self.last_geometry = None
		self.border = 1
		return self
	#
	def show(self):
		if self.wid <> 0:
			self.pop()
			return
		self.load_geometry()
		glwindow.setgeometry(self.last_geometry)
		if not self.border:
			gl.noborder()
		self.wid = gl.winopen(self.title)
		if not self.border:
			gl.noborder()
		gl.winconstraints()
		glwindow.register(self, self.wid)
		fl.qdevice(DEVICE.WINSHUT)
	#
	def hide(self):
		if self.wid <> 0:
			self.save_geometry()
			glwindow.unregister(self)
			gl.winclose(self.wid)
			self.wid = 0
	#
	def setwin(self):
		if self.wid <> 0:
			gl.winset(self.wid)
		else:
			print 'GLDialog: setwin() of hidden window'
	#
	def is_showing(self):
		return self.wid <> 0
	#
	def settitle(self, title):
		self.title = title
		if self.wid <> 0:
			self.setwin()
			gl.wintitle(self.title)
	#
	def setborder(self, border):
		if border == self.border:
			return
		self.border = border
		if self.wid <> 0:
			self.setwin()
			if not self.border:
				gl.noborder()
			gl.winconstraints()
	#
	def pop(self):
		if self.wid <> 0:
			self.setwin()
			gl.winpop()
	#
	def get_geometry(self):
		if self.wid <> 0:
			self.setwin()
			self.last_geometry = glwindow.getgeometry()
	#
	def destroy(self):
		self.hide()
	#
	def winshut(self):
		self.hide()
	#
	# Clients can override these methods to copy self.last_geometry
	# from/to more persistent storage:
	#
	def load_geometry(self):
		pass
	#
	def save_geometry(self):
		self.get_geometry() # This is needed for hide()
	#


# Test function for Dialog()

def test():
	d = Dialog().init(400, 200, 'Dialog.test', 'hint hint')
	d.show()
	n = 5
	while 1:
		fl.check_forms()
		if not d.showing:
			n = n-1
			if n < 0: break
			d.show()
