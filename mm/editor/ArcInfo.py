# Arc info window (modeless dialog)


import gl
import fl
import FL

import MMExc
import MMAttrdefs

from Dialog import Dialog


form_template = None # Initialized on first use


def showarcinfo(root, snode, sside, delay, dnode, dside):
	context = root.context
	try:
		arcinfos = context.arcinfos
	except AttributeError:
		arcinfos = context.arcinfos = {}
	key = snode.GetUID() + `sside, delay, dside` + dnode.GetUID()
	if not arcinfos.has_key(key):
		arcinfos[key] = ArcInfo().init(root, \
			snode, sside, delay, dnode, dside)
	arcinfos[key].open()


class ArcInfo(Dialog):

	def init(self, root, snode, sside, delay, dnode, dside):
		import flp
		self.root = root
		self.context = root.context
		self.snode = snode
		self.sside = sside
		self.delay = delay
		self.dnode = dnode
		self.dside = dside
		#
		global form_template
		if not form_template:
			form_template = flp.parse_form('ArcInfoForm', 'main')
		#
		width = form_template[0].Width
		height = form_template[0].Height
		title = self.maketitle()
		hint = ''
		self = Dialog.init(self, width, height, title, hint)
		flp.merge_full_form(self, self.form, form_template)
		self.one_sec.set_button(0)
		self.ten_sec.set_button(1)
		self.hundred_sec.set_button(0)
		return self

	def __repr__(self):
		return '<ArcInfo instance for ' + \
	`(self.snode, self.sside, self.delay, self.dnode, self.dside)` + '>'

	def maketitle(self):
		sname = MMAttrdefs.getattr(self.snode, 'name')
		dname = MMAttrdefs.getattr(self.dnode, 'name')
		return 'Sync arc from "' + sname + '" to "' + dname + '"'

	def open(self):
		if self.is_showing():
			self.pop()
		else:
			self.show()
			self.context.editmgr.register(self)
			self.getvalues()

	def close(self):
		self.context.editmgr.unregister(self)
		self.hide()

	# Override event handler

	def winshut(self):
		self.close()

	# Edit manager interface (as dependent client)

	def transaction(self):
		return 1

	def rollback(self):
		pass

	def commit(self):
		if not self.stillvalid():
			self.close()
		else:
			self.settitle(self.maketitle())

	def kill(self):
		self.close()
		self.destroy()

	def stillvalid(self):
		if self.snode.GetRoot() is not self.root or \
			self.dnode.GetRoot() is not self.root:
			return 0
		arc = self.snode.GetUID(), self.sside, self.delay, self.dside
		return arc in MMAttrdefs.getattr(self.dnode, 'synctolist')

	# Standard callbacks (referenced from Dialog)

	def cancel_callback(self, *args):
		self.close()

	def restore_callback(self, *args):
		self.getvalues()

	def apply_callback(self, *args):
		self.setvalues()

	def ok_callback(self, *args):
		self.setvalues()
		self.close()

	def one_sec_callback(self, *args):
		delay = min(1.0, self.delay_slider.get_slider_value())
		self.delay_slider.set_slider_value(delay)
		self.delay_slider.set_slider_bounds(0.0, 1.0)
		self.delay_slider.set_slider_precision(2)

	def ten_sec_callback(self, *args):
		delay = min(10.0, self.delay_slider.get_slider_value())
		self.delay_slider.set_slider_value(delay)
		self.delay_slider.set_slider_bounds(0.0, 10.0)
		self.delay_slider.set_slider_precision(1)

	def hundred_sec_callback(self, *args):
		delay = min(100.0, self.delay_slider.get_slider_value())
		self.delay_slider.set_slider_value(delay)
		self.delay_slider.set_slider_bounds(0.0, 100.0)
		self.delay_slider.set_slider_precision(0)

	# Dummy callback for from/to beginning/end buttons and delay slider

	def dummy_callback(self, *args):
		pass

	# Get/set values

	def getvalues(self):
		if self.delay > 10.0:
			self.hundred_sec.set_button(1)
			self.ten_sec.set_button(0)
			self.one_sec.set_button(0)
		elif self.delay > 1.0 and self.one_sec.get_button():
			self.hundred_sec.set_button(0)
			self.ten_sec.set_button(1)
			self.one_sec.set_button(0)
		if self.hundred_sec.get_button():
			self.delay_slider.set_slider_bounds(0.0, 100.0)
			self.delay_slider.set_slider_precision(0)
		elif self.ten_sec.get_button():
			self.delay_slider.set_slider_bounds(0.0, 10.0)
			self.delay_slider.set_slider_precision(1)
		else:
			self.delay_slider.set_slider_bounds(0.0, 1.0)
			self.delay_slider.set_slider_precision(2)
		self.delay_slider.set_slider_value(self.delay)
		self.from_beginning.set_button(not self.sside)
		self.from_end.set_button(self.sside)
		self.to_beginning.set_button(not self.dside)
		self.to_end.set_button(self.dside)

	def setvalues(self):
		editmgr = self.context.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.delsyncarc(self.snode, self.sside, self.delay, \
			self.dnode, self.dside)
		d = self.delay_slider.get_slider_value()
		p = 100.0 / self.delay_slider.get_slider_bounds()[1]
		self.delay = int(d*p + 0.5) / p
		self.delay_slider.set_slider_value(self.delay)
		self.sside = self.from_end.get_button()
		self.dside = self.to_end.get_button()
		editmgr.addsyncarc(self.snode, self.sside, self.delay, \
			self.dnode, self.dside)
		editmgr.commit()
