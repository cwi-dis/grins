# Implementation of Multimedia nodes


from MMExc import *		# Exceptions


# The MMNodeContext class
#
class MMNodeContext():
	#
	def init(self, nodeclass):
		self.nodeclass = nodeclass
		self.nextuid = 1
		self.uidmap = {}
		self.styledict = {}
		self.channelnames = []
		self.channeldict = {}
		self.editmgr = None
		return self
	#
	def newnode(self, type):
		_stat('newnode')
		return self.newnodeuid(type, self.newuid())
	#
	def newnodeuid(self, (type, uid)):
		_stat('newnodeuid')
		node = self.nodeclass().Init(type, self, uid)
		self.knownode(uid, node)
		return node
	#
	def newuid(self):
		_stat('newuid')
		while 1:
			uid = `self.nextuid`
			self.nextuid = self.nextuid + 1
			if not self.uidmap.has_key(uid):
				return uid
	#
	def mapuid(self, uid):
		_stat('mapuid')
		if not self.uidmap.has_key(uid):
			raise NoSuchUIDError, 'in mapuid()'
		return self.uidmap[uid]
	#
	def knownode(self, (uid, node)):
		_stat('knownode')
		if self.uidmap.has_key(uid):
			raise DuplicateUIDError, 'in knownode()'
		self.uidmap[uid] = node
	#
	def forgetnode(self, uid):
		_stat('forgetnode')
		del self.uidmap[uid]
	#
	def addstyles(self, dict):
		_stat('addstyles')
		# XXX How to handle duplicates?
		for key in dict.keys():
			self.styledict[key] = dict[key]
	#
	def addchannels(self, list):
		_stat('addchannels')
		for name, dict in list:
			self.channelnames.append(name)
			self.channeldict[name] = dict
	#
	def seteditmgr(self, editmgr):
		self.editmgr = editmgr
	#
	def geteditmgr(self):
		return self.editmgr
	#
	# Look for an attribute in the style definitions.
	# Raise NoSuchAttrError if the attribute is undefined.
	# This will cause a stack overflow if there are recursive style
	# definitions, and raise an unexpected exception if there are
	# undefined styles.
	#
	# XXX The recursion may be optimized out by expanding definitions;
	# XXX this should also fix the stack overflows...
	#
	def lookinstyles(self, (name, styles)):
		_stat('lookinstyles')
		for style in styles:
			attrdict = self.styledict[style]
			if attrdict.has_key(name):
				return attrdict[name]
			if attrdict.has_key('style'):
				try:
					_stat('lookinstyles recursive call')
					return self.lookinstyles(name, \
						attrdict['style'])
				except NoSuchAttrError:
					pass
		raise NoSuchAttrError, 'in lookinstyles()'
	#


# The Node class
#
class MMNode():
	#
	# Create a new node.
	#
	def Init(self, (type, context, uid)):
		# ASSERT type in ('seq', 'par', 'ext', 'imm', 'grp')
		self.type = type
		self.context = context
		self.uid = uid
		self.attrdict = {}
		self.parent = None
		self.children = []
		self.values = []
		self.summaries = {}
		self.widget = None # Used to display traversal XXX temporary!
		return self
	#
	# Private methods to build a tree
	#
	def _addchild(self, child):
		# ASSERT self.type in ('seq', 'par', 'grp')
		child.parent = self
		self.children.append(child)
	#
	def _addvalue(self, value):
		# ASSERT self.type = 'imm'
		self.values.append(value)
	#
	def _setattr(self, (name, value)):
		# ASSERT not self.attrdict.has_key(name)
		self.attrdict[name] = value
	#
	# Public methods for read-only access
	#
	def GetType(self):
		return self.type
	#
	def GetContext(self):
		return self.context
	#
	def GetUID(self):
		return self.uid
	#
	def MapUID(self, uid):
		return self.context.mapuid(uid)
	#
	def GetParent(self):
		_stat('GetParent')
		return self.parent
	#
	def GetRoot(x):
		_stat('GetRoot')
		root = None
		while x:
			root = x
			x = x.parent
		return root
	#
	def GetPath(x):
		_stat('GetPath')
		path = []
		while x:
			path.insert(0, x)
			x = x.parent
		return path
	#
	def IsAncestorOf(self, x):
		_stat('IsAncestorOf')
		while x <> None:
			if self = x: return 1
			x = x.parent
		return 0
	#
	def CommonAncestor(self, x):
		_stat('CommonAncestor')
		p1 = self.GetPath()
		p2 = x.GetPath()
		n = min(len(p1), len(p2))
		i = 0
		while i < n and p1[i] = p2[i]: i = i+1
		if i = 0: return None
		else: return p1[i-1]
	#
	def GetChildren(self):
		_stat('GetChildren')
		return self.children
	#
	def GetChild(self, i):
		_stat('GetChild')
		return self.children[i]
	#
	def GetValues(self):
		_stat('GetValues')
		return self.values
	#
	def GetValue(self, i):
		_stat('GetValue')
		return self.values[i]
	#
	def GetAttrDict(self):
		return self.attrdict
	#
	def GetRawAttr(self, name):
		_stat('GetRawAttr')
		try:
			return self.attrdict[name]
		except RuntimeError:
			raise NoSuchAttrError, 'in GetRawAttr()'
	#
	def GetRawAttrDef(self, (name, default)):
		_stat('GetRawAttrDef')
		try:
			return self.GetRawAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetStyleDict(self):
		_stat('GetStyleDict')
		return self.context.styledict
	#
	def GetAttr(self, name):
		_stat('GetAttr')
		try:
			return self.attrdict[name]
		except RuntimeError:
			return self.GetDefAttr(name)
	#
	def GetDefAttr(self, name):
		_stat('GetDefAttr')
		try:
			styles = self.attrdict['style']
		except RuntimeError:
			raise NoSuchAttrError, 'in GetDefAttr()'
		return self.context.lookinstyles(name, styles)
	#
	def GetAttrDef(self, (name, default)):
		_stat('GetAttrDef')
		try:
			return self.GetAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetInherAttr(x, name):
		_stat('GetInherAttr')
		while x:
			if x.attrdict:
				try:
					return x.GetAttr(name)
				except NoSuchAttrError:
					pass
			x = x.parent
		raise NoSuchAttrError, 'in GetInherAttr()'
	#
	def GetDefInherAttr(self, name):
		_stat('GetInherDefAttr')
		x = self.parent
		while x:
			if x.attrdict:
				try:
					return x.GetAttr(name)
				except NoSuchAttrError:
					pass
			x = x.parent
		raise NoSuchAttrError, 'in GetInherDefAttr()'
	#
	def GetInherAttrDef(self, (name, default)):
		_stat('GetInherAttrDef')
		try:
			return self.GetInherAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetSummary(self, name):
		_stat('GetSummary')
		if not self.summaries.has_key(name):
			self.summaries[name] = self._summarize(name)
		return self.summaries[name]
	#
	def Dump(self):
		print '*** Dump of', self.type, 'node', self, '***'
		attrnames = self.attrdict.keys()
		attrnames.sort()
		for name in attrnames:
			print 'Attr', name + ':', `self.attrdict[name]`
		summnames = self.summaries.keys()
		if summnames:
			summnames.sort()
			print 'Has summaries for attrs:',
			for name in summnames:
				print name,
			print
		if self.type = 'imm' or self.values:
			print 'Values:',
			for value in self.values: print value,
			print
		if self.type in ('seq', 'par') or self.children:
			print 'Children:',
			for child in self.children: print child.GetType(),
			print
	#
	# Make a "deep copy" of a subtree
	#
	def DeepCopy(self):
		_stat('DeepCopy')
		uidremap = {}
		copy = self._deepcopy(uidremap)
		copy._fixuidrefs(uidremap)
		return copy
	#
	# Private methods for DeepCopy
	#
	def _deepcopy(self, uidremap):
		_stat('_deepcopy')
		copy = self.context.newnode(self.type)
		uidremap[self.uid] = copy.uid
		copy.attrdict = _valuedeepcopy(self.attrdict)
		copy.values = _valuedeepcopy(self.values)
		for child in self.children:
			copy._addchild(child._deepcopy(uidremap))
		return copy
	#
	def _fixuidrefs(self, uidremap):
		# XXX Should run through attributes and replace UIDs
		# XXX by remapped UIDs
		for child in self.children:
			child._fixuidrefs(uidremap)
	#
	# Public methods for modifying a tree
	#
	def SetType(self, type):
		if type not in ('seq', 'par', 'grp', 'imm', 'ext'):
			raise CheckError, 'SetType() bad type'
		if type = self.type:
			return
		if self.type in ('seq', 'par') and type in ('seq', 'par'):
			self.type = type
			return
		if self.children <> []: # TEMP! or self.values <> []:
			raise CheckError, 'SetType() on non-empty node'
		self.type = type
	#
	def SetValues(self, values):
		if self.type <> 'imm':
			raise CheckError, 'SetValues() bad node type'
		self.values = values
	#
	def SetAttr(self, (name, value)):
		_stat('SetAttr')
		self.attrdict[name] = value
		self._updsummaries([name])
	#
	def DelAttr(self, name):
		_stat('DelAttr')
		if not self.attrdict.has_key(name):
			raise NoSuchAttrError, 'in DelAttr()'
		del self.attrdict[name]
		self._updsummaries([name])
	#
	def Destroy(self):
		_stat('Destroy')
		if self.parent: raise CheckError, 'Destroy() non-root node'
		self.context.forgetnode(self.uid)
		for child in self.children:
			child.parent = None
			child.Destroy()
	#
	def Extract(self):
		_stat('Extract')
		if not self.parent: raise CheckError, 'Extract() root node'
		parent = self.parent
		self.parent = None
		parent.children.remove(self)
		parent._fixsummaries(self.summaries)
	#
	def AddToTree(self, (parent, i)):
		_stat('AddToTree')
		if self.parent: raise CheckError, 'AddToTree() non-root node'
		if self.context is not parent.context:
			# XXX Decide how to handle this later
			raise CheckError, 'AddToTree() requires same context'
		parent.children.insert(i, self)
		self.parent = parent
		parent._fixsummaries(self.summaries)
		parent._rmsummaries(self.summaries.keys())
	#
	# Private methods for summary management
	#
	def _rmsummaries(x, keep):
		while x:
			changed = 0
			for key in x.summaries.keys():
				if key not in keep:
					del x.summaries[key]
					changed = 1
			if not changed:
				break
			x = x.parent
	#
	def _fixsummaries(self, summaries):
		tofix = summaries.keys()
		for key in tofix[:]:
			if summaries[key] = []:
				tofix.remove(key)
		self._updsummaries(tofix)
	#
	def _updsummaries(x, tofix):
		_stat('_updsummaries')
		while x and tofix:
			for key in tofix[:]:
				if not x.summaries.has_key(key):
					tofix.remove(key)
				else:
					s = x._summarize(key)
					if s = x.summaries[key]:
						tofix.remove(key)
					else:
						x.summaries[key] = s
			x = x.parent
	#
	def _summarize(self, name):
		_stat('_summarize')
		try:
			summary = [self.GetAttr(name)]
		except NoSuchAttrError:
			summary = []
		for child in self.children:
			list = child.GetSummary(name)
			for item in list:
				if item not in summary:
					summary.append(item)
		summary.sort()
		return summary
	#


# Make a "deep copy" of an arbitrary value
#
def _valuedeepcopy(value):
	_stat('_valuedeepcopy')
	if type(value) = type({}):
		copy = {}
		for key in value.keys():
			copy[key] = _valuedeepcopy(value[key])
		return copy
	if type(value) = type([]):
		copy = value[:]
		for i in range(len(copy)):
			copy[i] = _valuedeepcopy(copy[i])
		return copy
	# XXX Assume everything else is immutable.  Not quite true...
	return value


# Keep statistics -- a counter per key.
# Just put calls to _stat() with a unique argument in your code and
# call _prstats() when the program exits.
# (Once such calls are there, they may also be used to save a trace
# of the program...)
#
_stats = {}
#
def _stat(key):
	if _stats.has_key(key):
		_stats[key] = _stats[key] + 1
	else:
		_stats[key] = 1
#
def _prstats():
	from string import rjust
	print '### Statistics ###'
	list = []
	for key in _stats.keys():
		list.append(_stats[key], key)
	list.sort()
	list.reverse()
	for count, key in list:
		print '#', rjust(`count`, 5), key
