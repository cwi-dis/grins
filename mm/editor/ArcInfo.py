__version__ = "$Id$"

# Arc info window (modeless dialog)


import MMExc
import MMAttrdefs


##def showarcinfo(root, snode, sside, delay, dnode, dside, new = 0):
##	context = root.context
##	try:
##		arcinfos = context.arcinfos
##	except AttributeError:
##		arcinfos = context.arcinfos = {}
##	key = snode.GetUID() + `sside, delay, dside` + dnode.GetUID()
##	if not arcinfos.has_key(key):
##		arcinfos[key] = ArcInfo(root,
##					snode, sside, delay, dnode, dside, new)
##	arcinfos[key].open()


from ArcInfoDialog import ArcInfoDialog

class ArcInfo(ArcInfoDialog):

	def __init__(self, root, snode, sside, delay, dnode, dside, new = 0):
		self.new = new
		self.root = root
		self.context = root.context
		self.snode = snode
		self.sside = sside
		self.delay = delay
		self.dnode = dnode
		self.dside = dside
		self.setchoices()
		if self.sside: src_init = len(self.src_markers) + 1
		else: src_init = 0
		if self.dside: dst_init = len(self.dst_markers) + 1
		else: dst_init = 0

		title = self.maketitle()
		ArcInfoDialog.__init__(self, title, self.src_options, src_init,
				       self.dst_options, dst_init, self.delay)
		self.context.editmgr.register(self)

	def __repr__(self):
		return '<ArcInfo instance for ' + \
	`(self.snode, self.sside, self.delay, self.dnode, self.dside)` + '>'

	def maketitle(self):
		sname = MMAttrdefs.getattr(self.snode, 'name')
		dname = MMAttrdefs.getattr(self.dnode, 'name')
		return 'Sync arc from "' + sname + '" to "' + dname + '"'

	def close(self):
		editmgr = self.context.editmgr
		editmgr.unregister(self)
		ArcInfoDialog.close(self)
		if self.new:
			if not editmgr.transaction():
				return
			editmgr.delsyncarc(self.snode, self.sside, self.delay,
					   self.dnode, self.dside)
			#...cleanup() ?
			editmgr.commit()

	def setchoices(self):
		self.src_options, self.src_markers = self.setchoice(self.snode)
		self.dst_options, self.dst_markers = self.setchoice(self.dnode)

	def setchoice(self, node):
		options = ['*Begin*', '*End*']
		if node.GetChannelType() <> 'sound':
			return options, []
		# XXX Need to do this more general (i.e. also for video)
		import SoundDuration
		import SoundChannel # XXX hack! for aiffcache only
		duration = 0.0
		markers = []
		filename = MMAttrdefs.getattr(node, 'file')
		filename = node.context.findurl(filename)
		# XXX hack!
		import SoundChannel
		try:
			duration = SoundDuration.get(filename)
			markers = SoundDuration.getmarkers(filename)
		except IOError:
			pass
		options = ['*Begin* (0.0)']
		for id, pos, name in markers:
			options.append('  %s (%.2g)' % (name, pos))
		options.append('*End* (%.2g)' % duration)
		return options, markers

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

	def stillvalid(self):
		if self.snode.GetRoot() is not self.root or \
		   self.dnode.GetRoot() is not self.root:
			return 0
		arc = self.snode.GetUID(), self.sside, self.delay, self.dside
		return arc in MMAttrdefs.getattr(self.dnode, 'synctolist')

	# dialog callbacks

	def ok_callback(self):
		self.setvalues()
		self.close()

	def apply_callback(self):
		self.setvalues()

	def cancel_callback(self):
		self.close()

	def restore_callback(self):
		self.getvalues()

	# Get/set values (get: from object to form; set: from form to object)

	def getvalues(self):
		self.delay_setvalue(self.delay)
		if self.sside: i = len(self.src_markers) + 1
		else: i = 0
		self.src_setpos(i)
		if self.dside: i = len(self.dst_markers) + 1
		else: i = 0
		self.dst_setpos(i)

	def setvalues(self):
		changed = 0
		editmgr = self.context.editmgr
		delay = self.delay_getvalue()
		if delay != self.delay:
			changed = 1
		self.delay_setvalue(self.delay)
		# XXX For now, clip sides to [0, 1]
		sside = min(self.src_getpos(), 1)
		if sside != self.sside:
			changed = 1
		dside = min(self.dst_getpos(), 1)
		if dside != self.dside:
			changed = 1
		if changed or self.new:
			self.new = 0
			if not editmgr.transaction():
				return # Not possible at this time
			editmgr.delsyncarc(self.snode, self.sside, self.delay,
					   self.dnode, self.dside)
			self.delay = delay
			self.sside = sside
			self.dside = dside
			editmgr.addsyncarc(self.snode, self.sside, self.delay,
					   self.dnode, self.dside)
			editmgr.commit()

showarcinfo = ArcInfo
