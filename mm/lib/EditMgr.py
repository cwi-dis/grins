__version__ = "$Id$"

# Edit Manager.
# Amazing as it may seem, this module is not dependent on window software!

import MMExc
from HDTL import HD, TL

class EditMgr:
	#
	# Initialization.
	#
	def __init__(self, root):
		self.reset()
		self.root = root
		self.context = root.GetContext()
	#
	def __repr__(self):
		return '<EditMgr instance, context=' + `self.context` + '>'
	#
	def reset(self):
		self.root = self.context = None
		self.busy = 0
		self.history = []
		self.future = []
		self.registry = []
	#
	def destroy(self):
		for x in self.registry[:]:
			x.kill()
		self.reset()
	#
	# Dependent client interface.
	#
	def register(self, x):
		self.registry.append(x)

	def registerfirst(self, x):
		self.registry.insert(0, x)

	def unregister(self, x):
		self.registry.remove(x)
	#
	def is_registered(self, x):
		return x in self.registry
	#
	# Mutator client interface -- transactions.
	# This calls the dependent clients' callbacks.
	#
	def transaction(self):
		if self.busy: raise MMExc.AssertError, 'recursive transaction'
		done = []
		for x in self.registry[:]:
			if not x.transaction():
				for x in done:
					x.rollback()
				return 0
			done.append(x)
		self.undostep = []
		self.history.append(self.undostep)
		self.busy = 1
		return 1
	#
	def commit(self):
		if not self.busy: raise MMExc.AssertError, 'invalid commit'
		import MMAttrdefs, Timing
		MMAttrdefs.flushcache(self.root)
		Timing.changedtimes(self.root)
		self.root.clear_infoicon()
		self.root.ResetPlayability()
		for x in self.registry[:]:
			x.commit()
		self.busy = 0
		del self.undostep # To frustrate invalid addstep calls
	#
	def rollback(self):
		if not self.busy: raise MMExc.AssertError, 'invalid rollback'
		# XXX undo changes made in this transaction
		for x in self.registry[:]:
			x.rollback()
		self.busy = 0
		del self.undostep # To frustrate invalid addstep calls
	#
	# UNDO interface -- this code isn't ready yet.
	#
	def undo(self):
		if self.busy: raise MMExc.AssertError, 'undo while busy'
		i = len(self.history) - 1
		if i < 0: return 0 # Nothing to undo
		step = self.history[i]
		XXX # Carry out items in step in reverse order
		self.future.insert(0, step)
		del self.history[i]
		return 1
	#
	def redo(self):
		if self.busy: raise MMExc.AssertError, 'undo while busy'
		if not future: return 0 # Nothing to redo
		step = self.future(0)
		XXX # Carry out items in step in forward order
		self.history.append(step)
		del self.future[0]
		return 1
	# XXX The undo/redo business is unfinished.
	# E.g., What to do if the user undoes a few steps,
	# then makes new changes, then wants to redo?
	# Also the commit/rollback stuff isn't watertight
	# (ideally rollback must be able to roll back even if
	# an arbitrary keyboard interrupt hit).
	#
	def addstep(self, *step):
		# This fails if we're not busy because self.undostep is deleted
		self.undostep.append(step)
	#
	# Mutator client interface -- tree mutations.
	#
	# Node operations
	#
	def delnode(self, node):
		parent = node.GetParent()
		i = parent.GetChildren().index(node)
		self.addstep('delnode', parent, i, node)
		node.Extract()
	#
	def addnode(self, parent, i, node):
		self.addstep('addnode', parent, i, node)
		node.AddToTree(parent, i)
	#
	def setnodetype(self, node, type):
		oldtype = node.GetType()
		self.addstep('setnodetype', node, oldtype, type)
		node.SetType(type)
	#
	def setnodeattr(self, node, name, value):
		if name == 'synctolist':
			raise MMExc.AssertError, 'cannot set synctolist attr'
		oldvalue = node.GetRawAttrDef(name, None)
		self.addstep('setnodeattr', node, name, oldvalue, value)
		if value is not None:
			node.SetAttr(name, value)
		else:
			node.DelAttr(name)
	#
	def setnodevalues(self, node, values):
		self.addstep('setnodevalues', node, node.GetValues(), values)
		node.SetValues(values)
	#
	# Sync arc operations
	#
	def addsyncarc(self, xnode, xside, delay, ynode, yside):
		skip = 0
		if yside == HD:
			if ynode.GetParent().GetType() == 'seq' and xside == TL:
				prev = None
				for n in ynode.GetParent().GetChildren():
					if n is ynode:
						break
					prev = n
				if prev is not None and xnode is prev:
					self.setnodeattr(ynode, 'begin', delay)
					skip = 1
			elif xside == HD and xnode is ynode.GetParent():
				self.setnodeattr(ynode, 'begin', delay)
				skip = 1
		list = ynode.GetRawAttrDef('synctolist', None)
		if list is None and not skip:
			list = []
			ynode.SetAttr('synctolist', list)
		xuid = xnode.GetUID()
		for item in list:
			xn, xs, de, ys = item
			if xn==xuid and (xs,ys) == (xside,yside):
				self.addstep('delsyncarc',xnode,xs,de,ynode,ys)
				list.remove(item)
				break
		if not skip:
			self.addstep('addsyncarc', xnode, xside, delay, ynode, yside)
			list.append((xuid, xside, delay, yside))
	#
	def delsyncarc(self, xnode, xside, delay, ynode, yside):
		if yside == HD:
			if ynode.GetParent().GetType() == 'seq' and xside == TL:
				prev = None
				for n in ynode.GetParent().GetChildren():
					if n is ynode:
						break
					prev = n
				if prev is not None and xnode is prev and ynode.GetAttrDef('begin',None) == delay:
					self.setnodeattr(ynode, 'begin', None)
					return
			elif xside == HD and xnode is ynode.GetParent() and ynode.GetAttrDef('begin',None) == delay:
				self.setnodeattr(ynode, 'begin', None)
				return
		list = ynode.GetRawAttrDef('synctolist', [])
		xuid = xnode.GetUID()
		for item in list:
			xn, xs, de, ys = item
			if xn==xuid and (xs,de,ys) == (xside,delay,yside):
				self.addstep('delsyncarc',xnode,xs,de,ynode,ys)
				list.remove(item)
				if not list:
					# no sync arcs left
					ynode.DelAttr('synctolist')
				break
		else:
			raise MMExc.AssertError, 'bad delsyncarc call'
	#
	# Hyperlink operations
	#
	def addlink(self, link):
		self.addstep('addlink', link)
		self.context.hyperlinks.addlink(link)

	def dellink(self, link):
		self.addstep('dellink', link)
		self.context.hyperlinks.dellink(link)
	#
	# Channel operations
	#
	def addchannel(self, name, i, type):
		c = self.context.getchannel(name)
		if c is not None:
			raise MMExc.AssertError, \
				'duplicate channel name in addchannel'
		self.addstep('addchannel', name, i, type)
		self.context.addchannel(name, i, type)
	#
	def copychannel(self, name, i, orig):
		c = self.context.getchannel(name)
		if c is not None:
			raise MMExc.AssertError, \
				'duplicate channel name in copychannel'
		c = self.context.getchannel(orig)
		if c is None:
			raise MMExc.AssertError, \
				'unknown orig channel name in copychannel'
		self.addstep('copychannel', name, i, orig)
		self.context.copychannel(name, i, orig)
	#
	def movechannel(self, name, i):
		self.addstep('movechannel', name, i)
		self.context.movechannel(name, i)
	#
	def delchannel(self, name):
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in delchannel'
		i = self.context.channels.index(c)
		attrdict = c.attrdict
		self.addstep('delchannel', name, i, attrdict)
		self.context.delchannel(name)
	#
	def setchannelname(self, name, newname):
		if newname == name:
			return # No change
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in setchannelname'
		self.addstep('setchannelname', name, newname)
		self.context.setchannelname(name, newname)
	#
	def setchannelattr(self, name, attrname, value):
		c = self.context.getchannel(name)
		if c is None:
			raise MMExc.AssertError, \
				  'unknown channel name in setchannelattr'
		if c.has_key(attrname):
			oldvalue = c[attrname]
		else:
			oldvalue = None
		if value == oldvalue:
			return
		self.addstep('setchannelattr', name, attrname, oldvalue, value)
		if value is None:
			del c[attrname]
		else:
			c[attrname] = value

	#
	# Layout operations
	#
	def addlayout(self, name):
		if self.context.layouts.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate layout name in addlayout'
		self.addstep('addlayout', name)
		self.context.addlayout(name)

	def dellayout(self, name):
		layout = self.context.layouts.get(name)
		if layout is None:
			raise MMExc.AssertError, 'unknown layout in dellayout'
		self.addstep('dellayout', name, layout)
		self.context.dellayout(name)

	def addlayoutchannel(self, name, channel):
		layout = self.context.layouts.get(name)
		if layout is None:
			raise MMExc.AssertError, \
			      'unknown layout in addlayoutchannel'
		if channel in layout:
			raise MMExc.AssertError, \
			      'channel already in layout in addlayoutchannel'
		self.addstep('addlayoutchannel', name, channel)
		self.context.addlayoutchannel(name, channel)

	def dellayoutchannel(self, name, channel):
		layout = self.context.layouts.get(name)
		if layout is None:
			raise MMExc.AssertError, \
			      'unknown layout in addlayoutchannel'
		if channel not in layout:
			raise MMExc.AssertError, \
			      'channel not in layout in dellayoutchannel'
		self.addstep('dellayoutchannel', name, channel)
		self.context.dellayoutchannel(name, channel)

	def setlayoutname(self, name, newname):
		if newname == name:
			return		# no change
		if not self.context.layouts.has_key(name):
			raise MMExc.AssertError, \
			      'unknown layout name in setlayoutname'
		if self.context.layouts.has_key(newname):
			raise MMExc.AssertError, \
			      'name already in use in setlayoutname'
		self.addstep('setlayoutname', name, newname)
		self.context.setlayoutname(name, newname)

	#
	# User group operations
	#
	def addusergroup(self, name, value):
		if self.context.usergroups.has_key(name):
			raise MMExc.AssertError, \
			      'duplicate usergroup name in addusergroup'
		self.addstep('addusergroup', name)
		self.context.addusergroup(name, value)

	def delusergroup(self, name):
		usergroup = self.context.usergroups.get(name)
		if usergroup is None:
			raise MMExc.AssertError, 'unknown usergroup in delusergroup'
		self.addstep('delusergroup', name, usergroup)
		self.context.delusergroup(name)

	def setusergroupname(self, name, newname):
		if newname == name:
			return		# no change
		if not self.context.usergroups.has_key(name):
			raise MMExc.AssertError, \
			      'unknown usergroup name in setusergroupname'
		if self.context.usergroups.has_key(newname):
			raise MMExc.AssertError, \
			      'name already in use in setusergroupname'
		self.addstep('setusergroupname', name, newname)
		self.context.setusergroupname(name, newname)

##	#
##	# Style operations
##	#
##	def addstyle(self, name):
##		if self.context.styledict.has_key(name):
##			raise MMExc.AssertError, \
##				'duplicate style name in addstyle'
##		self.addstep('addstyle', name)
##		self.context.styledict[name] = {}
##	#
##	def delstyle(self, name):
##		self.addstep('delstyle', name, self.context.styledict[name])
##		del self.context.styledict[name]
##	#
##	def setstylename(self, name, newname):
##		if self.context.styledict.has_key(newname):
##			raise MMExc.AssertError, \
##				'duplicate style name in setstylename'
##		attrdict = self.context.styledict[name]
##		self.addstep('setstylename', name, newname)
##		self.context.styledict[newname] = attrdict
##		del self.context.styledict[name]
##	#
##	def setstyleattr(self, name, attrname, value):
##		attrdict = self.context.styledict[name]
##		if attrdict.has_key(attrname):
##			oldvalue = attrdict[attrname]
##		else:
##			oldvalue = None
##		if value is None is oldvalue:
##			return
##		self.addstep('setstyleattr', name, attrname, oldvalue, value)
##		if value is None:
##			del attrdict[attrname]
##		else:
##			attrdict[attrname] = value
##	#
