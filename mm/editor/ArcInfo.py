# Arc info window (modeless dialog)


import gl
import fl
import FL

import MMExc
import MMAttrdefs

from Dialog import Dialog
import glwindow


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
		width, height = glwindow.pixels2mm(form_template[0].Width, \
			  form_template[0].Height)
		title = self.maketitle()
		hint = ''
		self = Dialog.init(self, width, height, title, hint)
		flp.merge_full_form(self, self.form, form_template)
		self.range_choice.clear_choice()
		self.range_choice.addto_choice('0-1 sec')
		self.range_choice.addto_choice('0-10 sec')
		self.range_choice.addto_choice('0-100 sec')
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
			self.setchoices()
			self.show()
			self.context.editmgr.register(self)
			self.getvalues()

	def close(self):
		self.context.editmgr.unregister(self)
		self.hide()

	def setchoices(self):
		self.src_markers = self.setchoice(self.src_choice, self.snode)
		self.dst_markers = self.setchoice(self.dst_choice, self.dnode)

	def setchoice(self, choice, node):
		choice.clear_choice()
		choice.addto_choice('*Begin*')
		choice.addto_choice('*End*')
		if node.GetChannelType() <> 'sound':
			return []
		# XXX Need to do this more general (i.e. also for video)
		import SoundDuration
		import SoundChannel # XXX hack! for aiffcache only
		duration = 0.0
		markers = []
		filename = MMAttrdefs.getattr(node, 'file')
		filename = node.context.findfile(filename)
		# XXX hack!
		import SoundChannel
		try:
			duration = SoundDuration.get(filename)
			markers = SoundDuration.getmarkers(filename)
		except IOError, msg:
			pass
		choice.clear_choice()
		choice.addto_choice('*Begin* (0.0)')
		for id, pos, name in markers:
			choice.addto_choice('  %s (%.2g)' % (name, pos))
		choice.addto_choice('*End* (%.2g)' % duration)
		return markers

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

	def range_callback(self, *args):
		i = self.range_choice.get_choice()
		range = float(pow(10, i-1))
		delay = min(range, self.delay_slider.get_slider_value())
		self.delay_slider.set_slider_value(delay)
		self.delay_slider.set_slider_bounds(0.0, range)
		self.delay_slider.set_slider_precision(3-i)

	# callbacks for source, destination and delay slider

	def src_callback(self, *args):
		pass

	def dst_callback(self, *args):
		pass

	def slider_callback(self, *args):
		pass

	# Get/set values (get: from object to form; set: from form to object)

	def getvalues(self):
		if self.delay > 10.0:
			self.range_choice.set_choice(3)
		elif self.delay > 1.0:
			self.range_choice.set_choice(2)
		else:
			self.range_choice.set_choice(1)
		self.range_callback()
		self.delay_slider.set_slider_value(self.delay)
		if self.sside: i = len(self.src_markers) + 2
		else: i = 1
		self.src_choice.set_choice(i)
		if self.dside: i = len(self.dst_markers) + 2
		else: i = 1
		self.dst_choice.set_choice(i)

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
		# XXX For now, clip sides to [0, 1]
		self.sside = min(self.src_choice.get_choice() - 1, 1)
		self.dside = min(self.dst_choice.get_choice() - 1, 1)
		editmgr.addsyncarc(self.snode, self.sside, self.delay, \
			self.dnode, self.dside)
		editmgr.commit()
