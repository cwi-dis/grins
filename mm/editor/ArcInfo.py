__version__ = "$Id$"

# Arc info window (modeless dialog)


import MMExc
import MMAttrdefs
from HDTL import HD, TL


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

arcinfodialogs = []

def showarcinfo(cview, root, snode, sside, delay, dnode, dside, new = 0):
	for ai in arcinfodialogs:
		if ai.snode == snode and \
		   ai.sside == sside and \
		   ai.delay == delay and \
		   ai.dnode == dnode and \
		   ai.dside == dside:
			return ai
	return ArcInfo(cview, root, snode, sside, delay, dnode, dside, new)

class ArcInfo(ArcInfoDialog):

	def __init__(self, cview, root, snode, sside, delay, dnode, dside, new = 0):
		self.new = new
		self.root = root
		self.context = root.context
		self.snode = snode
		self.sside = sside
		self.delay = delay
		self.dnode = dnode
		self.dside = dside
		self.cview = cview
		self.setchoices()
		if self.sside: src_init = len(self.src_markers) + 1
		else: src_init = 0
		if self.dside: dst_init = len(self.dst_markers) + 1
		else: dst_init = 0

		title = self.maketitle()
		ArcInfoDialog.__init__(self, title, self.src_options, src_init,
				       self.dst_options, dst_init, self.delay)
		self.context.editmgr.register(self)
		arcinfodialogs.append(self)

	def __repr__(self):
		return '<ArcInfo instance for ' + \
	`(self.snode, self.sside, self.delay, self.dnode, self.dside)` + '>'

	def maketitle(self):
		sname = MMAttrdefs.getattr(self.snode, 'name')
		dname = MMAttrdefs.getattr(self.dnode, 'name')
		return 'Sync arc from "' + sname + '" to "' + dname + '"'

	def close(self):
		try:
			# this shouldn't fail, but just in case we put it
			# inside a try/except 
			arcinfodialogs.remove(self)
		except:
			pass
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
		url = MMAttrdefs.getattr(node, 'file')
		url = node.context.findurl(url)
		# XXX hack!
		import SoundChannel
		try:
			duration = SoundDuration.get(url)
			markers = SoundDuration.getmarkers(url)
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
		if self.dside == HD:
			if self.dnode.GetParent().GetType() == 'seq' and self.sside == TL:
				prev = None
				for n in self.dnode.GetParent().GetChildren():
					if n is self.dnode:
						break
					prev = n
				if prev is not None and self.snode is prev and self.dnode.GetAttrDef('begin',None) == self.delay:
					return 1
			elif self.sside == HD and self.snode is self.dnode.GetParent() and self.dnode.GetAttrDef('begin',None) == self.delay:
				return 1
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
		self.delay_setvalue(self.delay)

	def pushsrcfocus_callback(self):
		top = self.cview.toplevel
		top.setwaiting()
		if top.channelview is not None:
			top.channelview.globalsetfocus(self.snode)
		if top.hierarchyview is not None:
			top.hierarchyview.globalsetfocus(self.snode)

	def pushdstfocus_callback(self):
		top = self.cview.toplevel
		top.setwaiting()
		if top.channelview is not None:
			top.channelview.globalsetfocus(self.dnode)
		if top.hierarchyview is not None:
			top.hierarchyview.globalsetfocus(self.dnode)
