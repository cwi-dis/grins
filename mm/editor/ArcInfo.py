# Arc info window (modeless dialog)


import windowinterface

import MMExc
import MMAttrdefs


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


class ArcInfo:

	def init(self, root, snode, sside, delay, dnode, dside):
		self.root = root
		self.context = root.context
		self.snode = snode
		self.sside = sside
		self.delay = delay
		self.dnode = dnode
		self.dside = dside

		title = self.maketitle()
		self.window = windowinterface.Window(title,
					{'resizable': 1,
					 'deleteCallback': (self.close, ())})
		self.src_choice = self.window.OptionMenu('From:',
					['dummy name'],
					0, None,
					{'top': None, 'left': None})
		self.dst_choice = self.window.OptionMenu('To:',
					['dummy name'],
					0, None,
					{'top': None, 'left': self.src_choice,
					 'right': None})
		self.delay_slider = self.window.Slider(None, 0, 0, 10, None,
					{'top': self.src_choice, 'left': None})
		self.range_choice = self.window.OptionMenu(None,
					['0-1 sec', '0-10 sec', '0-100 sec'],
					0, (self.range_callback, ()),
					{'top': self.dst_choice,
					 'left': self.delay_slider,
					 'right': None})
		buttons = self.window.ButtonRow(
			[('Cancel', (self.close, ())),
			 ('Restore', (self.getvalues, ())),
			 ('Apply', (self.setvalues, ())),
			 ('OK', (self.ok_callback, ()))],
			{'left': None, 'top': self.delay_slider,
			 'vertical': 0})

		self.window.fix()

		return self

	def __repr__(self):
		return '<ArcInfo instance for ' + \
	`(self.snode, self.sside, self.delay, self.dnode, self.dside)` + '>'

	def show(self):
		self.window.show()

	def hide(self):
		self.window.hide()

	def is_showing(self):
		return self.window.is_showing()

	def settitle(self, title):
		self.window.settitle(title)

	def maketitle(self):
		sname = MMAttrdefs.getattr(self.snode, 'name')
		dname = MMAttrdefs.getattr(self.dnode, 'name')
		return 'Sync arc from "' + sname + '" to "' + dname + '"'

	def open(self):
		if self.is_showing():
			self.window.show()
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
		options = ['*Begin*', '*End*']
		if node.GetChannelType() <> 'sound':
			choice.setoptions(options, 0)
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
		options = ['*Begin* (0.0)']
		for id, pos, name in markers:
			options.append('  %s (%.2g)' % (name, pos))
		options.append('*End* (%.2g)' % duration)
		choice.setoptions(options, 0)
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

	def ok_callback(self):
		self.setvalues()
		self.close()

	def range_callback(self):
		i = self.range_choice.getpos()
		range = float(pow(10, i))
		delay = min(range, self.delay_slider.getvalue())
		self.delay_slider.setvalue(delay)
		self.delay_slider.setrange(0.0, range)

	# Get/set values (get: from object to form; set: from form to object)

	def getvalues(self):
		if self.delay > 10.0:
			self.range_choice.setpos(2)
		elif self.delay > 1.0:
			self.range_choice.setpos(1)
		else:
			self.range_choice.setpos(0)
		self.range_callback()
		self.delay_slider.setvalue(self.delay)
		if self.sside: i = len(self.src_markers) + 1
		else: i = 0
		self.src_choice.setpos(i)
		if self.dside: i = len(self.dst_markers) + 1
		else: i = 0
		self.dst_choice.setpos(i)

	def setvalues(self):
		editmgr = self.context.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.delsyncarc(self.snode, self.sside, self.delay, \
			self.dnode, self.dside)
		d = self.delay_slider.getvalue()
		p = 100.0 / self.delay_slider.getrange()[1]
		self.delay = int(d*p + 0.5) / p
		self.delay_slider.setvalue(self.delay)
		# XXX For now, clip sides to [0, 1]
		self.sside = min(self.src_choice.getpos(), 1)
		self.dside = min(self.dst_choice.getpos(), 1)
		editmgr.addsyncarc(self.snode, self.sside, self.delay, \
			self.dnode, self.dside)
		editmgr.commit()
