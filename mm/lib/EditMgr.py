# Edit Manager.
# Amazing as it may seem, this module is not dependent on window software!

import MMExc

class EditMgr():
	#
	# Initialization.
	#
	def init(self, root):
		self.root = root
		self.context = root.GetContext()
		self.busy = 0
		self.history = []
		self.future = []
		self.registry = []
		return self
	#
	# Dependent client interface.
	#
	def register(self, x):
		self.registry.append(x)
	#
	def unregister(self, x):
		self.registry.remove(x)
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
	def addstep(self, step):
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
	def addnode(self, (parent, i, node)):
		self.addstep('addnode', parent, i, node)
		node.AddToTree(parent, i)
	#
	def setnodetype(self, (node, type)):
		oldtype = node.GetType()
		self.addstep('setnodetype', node, oldtype, type)
		node.SetType(type)
	#
	def setnodeattr(self, (node, name, value)):
		if name = 'synctolist':
			raise MMExc.AssertError, 'cannot set synctolist attr'
		oldvalue = node.GetRawAttrDef(name, None)
		self.addstep('setnodeattr', node, name, oldvalue, value)
		if value = None:
			node.DelAttr(name)
		else:
			node.SetAttr(name, value)
	#
	def setnodevalues(self, (node, values)):
		self.addstep('setnodevalues', node, node.GetValues(), values)
		node.SetValues(values)
	#
	# Sync arc operations
	#
	def addsyncarc(self, (xnode, xside, delay, ynode, yside)):
		list = ynode.GetRawAttrDef('synctolist', None)
		if list = None:
			list = []
			ynode.SetAttr('synctolist', list)
		for item in list:
			xn, xs, de, ys = item
			if xn=xnode and (xs,ys) = (xside,yside):
				self.addstep('delsyncarc',xn,xs,de,ynode,ys)
				list.remove(item)
				break
		self.addstep('addsyncarc', xnode, xside, delay, ynode, yside)
		list.append(xnode, xside, delay, yside)
	#
	def delsyncarc(self, (xnode, xside, delay, ynode, yside)):
		list = ynode.GetRawAttrDef('synctolist', [])
		for item in list:
			xn, xs, de, ys = item
			if xn=xnode and (xs,de,ys) = (xside,delay,yside):
				self.addstep('delsyncarc',xn,xs,de,ynode,ys)
				list.remove(item)
				break
		else:
			raise MMExc.AssertError, 'bad delsyncarc call'
	#
	def setsyncarcdelay(self, (xnode, xside, delay, ynode, yside)):
		list = ynode.GetRawAttrDef('synctolist', [])
		for i in range(len(list)):
			xn, xs, de, ys = item = list[i]
			if xn = xnode and (xs, ys) = (xside, yside):
				self.addstep('setsyncarcdelay', \
					xn, xs, delay, ynode, ys)
				list[i] = (xn, xs, delay, ys)
				break
		else:
			raise MMExc.AssertError, 'bad setsyncarcdelay call'
	#
	# Channel operations
	#
	def addchannel(self, (name, i, type)):
		if name in self.context.channelnames:
			raise MMExc.AssertError, \
				'duplicate channel name in addchannel'
		self.addstep('addchannel', name, i, type)
		self.context.channeldict[name] = {'type':type}
		self.context.channelnames.insert(i, name)
	#
	def delchannel(self, name):
		i = self.context.channelnames.index(name)
		attrdict = self.context.channeldict[name]
		self.addstep('delchannel', name, i, attrdict)
		del self.context.channelnames[i]
		del self.context.channeldict[name]
	#
	def setchannelname(self, (name, newname)):
		if newname in self.context.channelnames:
			raise MMExc.AssertError, \
				'duplicate channel name in setchannelname'
		i = self.context.channelnames.index(name)
		attrdict = self.context.channelnames[name]
		self.addstep('setchannelname', name, newname)
		self.context.channeldict[newname] = attrdict
		self.context.channelnames[i] = newname
		del self.context.channeldict[name]
	#
	def setchannelattr(self, (name, attrname, value)):
		attrdict = self.context.channeldict[name]
		if attrdict.has_key(attrname):
			oldvalue = attrdict[attrname]
		else:
			oldvalue = None
		if value = None = oldvalue:
			return
		self.addstep('setchannelattr', name, attrname, oldvalue, value)
		if value = None:
			del attrdict[attrname]
		else:
			attrdict[attrname] = value
	#
	# Style operations
	#
	def addstyle(self, name):
		if self.context.styledict.has_key(name):
			raise MMExc.AssertError, \
				'duplicate style name in addstyle'
		self.addstep('addstyle', name)
		self.context.styledict[name] = {}
	#
	def delstyle(self, name):
		self.addstep('delstyle', name, self.context.styledict[name])
		del self.context.styledict[name]
	#
	def setstylename(self, (name, newname)):
		if self.context.styledict.has_key(newname):
			raise MMExc.AssertError, \
				'duplicate style name in setstylename'
		attrdict = self.context.styledict[name]
		self.addstep('setstylename', name, newname)
		self.context.styledict[newname] = attrdict
		del self.context.styledict[name]
	#
	def setstyleattr(self, (name, attrname, value)):
		attrdict = self.context.styledict[name]
		if attrdict.has_key(attrname):
			oldvalue = attrdict[attrname]
		else:
			oldvalue = None
		if value = None = oldvalue:
			return
		self.addstep('setstyleattr', name, attrname, oldvalue, value)
		if value = None:
			del attrdict[attrname]
		else:
			attrdict[attrname] = value
	#
