# Implementation of Multimedia nodes


# Exceptions

CheckError = 'MMNode.CheckError'		# Invalid call
NoSuchAttrError = 'MMNode.NoSuchAttrError'	# Attribute not found


# The Node class
#
class MMNode():
	#
	# Private methods to build a tree
	#
	# XXX Could place the style dictionary in an instance variable
	# XXX instead of in the root's attribute dictionary;
	# XXX could even place (a pointer to) it on each node
	#
	def _init(self, type):
		self.type = type
		self.styledict = None
		self.attrdict = {}
		self.parent = None
		self.children = []
		self.values = []
		self.summaries = {}
		self.widget = None # Used to display traversal
		return self
	#
	def _addchild(self, child):
		child.parent = self
		self.children.append(child)
	#
	def _addvalue(self, value):
		# XXX Only for immediate nodes
		self.values.append(value)
	#
	def _setattr(self, (name, value)):
		# XXX Ought to check for duplicate attribute name?
		self.attrdict[name] = value
	#
	# Public methods for read-only access
	#
	def GetType(self):
		return self.type
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
			raise NoSuchAttrError, 'in GetRawAttr'
	#
	def GetRawAttrDef(self, (name, default)):
		try:
			return self.GetRawAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetStyleDict(self):
		_stat('GetStyleDict')
		if self.styledict = None:
			if self.attrdict.has_key('styledict'):
				self.styledict = self.attrdict['styledict']
			elif self.parent:
				self.styledict = self.parent.GetStyleDict()
		return self.styledict
	#
	def GetAttr(self, name):
		_stat('GetAttr')
		if name = '*':
			list = self.attrdict.keys()
			list.sort()
			return list
		try:
			return self.attrdict[name]
		except RuntimeError:
			try:
				styles = self.attrdict['style']
			except RuntimeError:
				raise NoSuchAttrError, 'in GetAttr'
			styledict = self.GetStyleDict()
			return _lookinstyles(name, styles, styledict)
	#
	def GetAttrDef(self, (name, default)):
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
		raise NoSuchAttrError, 'in GetInherAttr'
	#
	def GetInherAttrDef(self, (name, default)):
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
		if self.attrdict.has_key('styledict'):
			styledict = self.attrdict['styledict']
			stylenames = styledict.keys()
			stylenames.sort()
			for name in stylenames:
				print 'Style', name + ':', `styledict[name]`
		attrnames = self.attrdict.keys()
		attrnames.sort()
		for name in attrnames:
			if name <> 'styledict':
			    print 'Attr', name + ':', `self.attrdict[name]`
		summnames = self.summaries.keys()
		if summnames:
			summnames.sort()
			print 'Summaries for:',
			for name in summnames:
				print name,
			print
		if self.values:
			print 'Values:',
			for value in self.values: print value,
			print
		if self.children:
			print 'Children:',
			for child in self.children: print child.GetType(),
			print
	#
	# Public methods for modifying a tree
	#
	def SetAttr(self, (name, value)):
		_stat('SetAttr')
		self.attrdict[name] = value
		self._updsummaries([name])
	#
	def DelAttr(self, (name, value)):
		_stat('DelAttr')
		if not self.attrdict.has_key(name):
			return NoSuchAttrError, 'in DelAttr()'
		del self.attrdict[name]
		self._updsummaries([name])
	#
	def Destroy(self):
		_stat('Destroy')
		if self.parent: raise CheckError, 'Destroy() non-root node'
		for child in self.children:
			child.parent = None
			child.Destroy()
	#
	def Extract(self):
		_stat('Extract')
		if not self.parent: raise CheckError, 'Extract() root node'
		dummy = self.GetStyleDict() # Copy style dict if possible
		parent = self.parent
		self.parent = None
		parent.children.remove(self)
		parent._fixsummaries(self.summaries)
	#
	def AddToTree(self, (parent, i)):
		_stat('AddToTree')
		if self.parent: raise CheckError, 'AddToTree() non-root node'
		parent.children.insert(i, self)
		self.parent = parent
		if self.styledict is not parent.styledict:
			self._flushstyledict()
		parent._fixsummaries(self.summaries)
		parent._rmsummaries(self.summaries.keys())
	#
	# Private method to flush the style dictionary for a subtree
	#
	def _flushstyledict(self):
		_stat('_flushstyledict')
		self.styledict = None
		for child in self.children:
			child._flushstyledict()
	#
	# Make a "deep copy" of a subtree
	#
	def DeepCopy(self):
		_stat('DeepCopy')
		copy = MMNode()._init(self.type)
		copy.attrdict = _deepcopy(self.attrdict)
		copy.values = _deepcopy(self.values)
		for child in self.children:
			copy._addchild(child.DeepCopy())
		return copy
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
				tofix.remove(tofix)
		self._updsummaries(tofix)
	#
	def _updsummaries(x, tofix):
		_stat('_updsummaries')
		if '*' not in tofix:
			tofix.append('*')
		while x and tofix:
			for key in tofix[:]:
				if not x.summaries.has_key(key):
					tofix.remove(key)
				else:
					s = x._summarize(key)
					if s = x.summaries[key]:
						tofix.remove(key)
					else:
						x.summaries = s
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
def _deepcopy(value):
	_stat('_deepcopy')
	if type(value) = type({}):
		copy = {}
		for key in value.keys():
			copy[key] = _deepcopy(value[key])
		return copy
	if type(value) = type([]):
		copy = value[:]
		for i in range(len(copy)):
			copy[i] = _deepcopy(copy[i])
		return copy
	# XXX Assume everything else is immutable.  Not quite true...
	return value


# Look for an attribute in the style definitions.
# Raise NoSuchAttrError if the attribute is undefined.
# This will cause a stack overflow if there are recursive style definitions,
# and raise an unexpected exception if there are undefined styles
#
# XXX The recursion may be optimized out by expanding style definitions
#
def _lookinstyles(name, styles, styledict):
	_stat('_lookinstyle')
	for style in styles:
		attrdict = styledict[style]
		if attrdict.has_key(name):
			return attrdict[name]
		if attrdict.has_key('style'):
			try:
				_stat('_lookinstyle recursive call')
				return _lookinstyles(name, attrdict['style'], styledict)
			except NoSuchAttrError:
				pass
	raise NoSuchAttrError, 'in _lookinstyles (from GetAttr)'


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
