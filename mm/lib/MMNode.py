# Implementation of Multimedia nodes


from MMExc import *		# Exceptions
from Hlinks import Hlinks


leaftypes = ['imm', 'ext']
interiortypes = ['seq', 'par', 'bag']
alltypes = leaftypes + interiortypes


# The MMNodeContext class
#
class MMNodeContext:
	#
	def init(self, nodeclass):
		##_stat('init')
		self.nodeclass = nodeclass
		self.nextuid = 1
		self.uidmap = {}
		self.styledict = {}
		self.channelnames = []
		self.channeldict = {}
		self.hyperlinks = Hlinks().init()
		self.editmgr = None
		return self
	#
	def __repr__(self):
		##_stat('__repr__')
		return '<MMNodeContext instance, channelnames=' \
			+ `self.channelnames` + '>'
	#
	def newnode(self, type):
		##_stat('newnode')
		return self.newnodeuid(type, self.newuid())
	#
	def newnodeuid(self, (type, uid)):
		##_stat('newnodeuid')
		node = self.nodeclass().Init(type, self, uid)
		self.knownode(uid, node)
		return node
	#
	def newuid(self):
		##_stat('newuid')
		while 1:
			uid = `self.nextuid`
			self.nextuid = self.nextuid + 1
			if not self.uidmap.has_key(uid):
				return uid
	#
	def mapuid(self, uid):
		##_stat('mapuid')
		if not self.uidmap.has_key(uid):
			raise NoSuchUIDError, 'in mapuid()'
		return self.uidmap[uid]
	#
	def knownode(self, (uid, node)):
		##_stat('knownode')
		if self.uidmap.has_key(uid):
			raise DuplicateUIDError, 'in knownode()'
		self.uidmap[uid] = node
	#
	def forgetnode(self, uid):
		##_stat('forgetnode')
		del self.uidmap[uid]
	#
	def addstyles(self, dict):
		##_stat('addstyles')
		# XXX How to handle duplicates?
		for key in dict.keys():
			self.styledict[key] = dict[key]
	#
	def addchannels(self, list):
		##_stat('addchannels')
		for name, dict in list:
			self.channelnames.append(name)
			self.channeldict[name] = dict
	#
	def addhyperlinks(self, list):
		##_stat('addhyperlinks')
		self.hyperlinks.addlinks(list)
	#
	def addhyperlink(self, link):
		##_stat('addhyperlink')
		self.hyperlinks.addlink(link)
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
		##_stat('lookinstyles')
		for style in styles:
			attrdict = self.styledict[style]
			if attrdict.has_key(name):
				return attrdict[name]
			if attrdict.has_key('style'):
				try:
					##_stat('lookinstyles recursive call')
					return self.lookinstyles(name, \
						attrdict['style'])
				except NoSuchAttrError:
					pass
		raise NoSuchAttrError, 'in lookinstyles()'
	#
	# Remove all hyperlinks that aren't contained in the given trees
	# (note that the argument is a *list* of root nodes)
	#
	def sanitize_hyperlinks(self, roots):
		self._roots = roots
		badlinks = self.hyperlinks.selectlinks(self._isbadlink)
		del self._roots
		for link in badlinks:
			self.hyperlinks.dellink(link)
	#
	# Return all hyperlinks pertaining to the given tree
	# (note that the argument is a *single* root node)
	#
	def get_hyperlinks(self, root):
		self._roots = [root]
		links = self.hyperlinks.selectlinks(self._isgoodlink)
		del self._roots
		return links
	#
	# Internal: predicates to select nodes pertaining to self._roots
	#
	def _isbadlink(self, link):
		return not self._isgoodlink(link)
	#
	def _isgoodlink(self, (a1, a2, dir, type)):
		uid1, aid1 = a1
		uid2, aid2 = a2
		return self.uidmap.has_key(uid1) \
		   and self.uidmap.has_key(uid2) \
		   and self.uidmap[uid1].GetRoot() in self._roots \
		   and self.uidmap[uid2].GetRoot() in self._roots


# The Node class
#
class MMNode:
	#
	# Create a new node.
	#
	def Init(self, (type, context, uid)):
		# ASSERT type in alltypes
		self.type = type
		self.context = context
		self.uid = uid
		self.attrdict = {}
		self.parent = None
		self.children = []
		self.values = []
		self.summaries = {}
		self.widget = None # Used to display traversal XXX temporary!
		self.setarmedmode = self.setarmedmode_dummy
		self.armedmode = None
		return self
	#
	# Return string representation of self
	#
	def __repr__(self):
		return '<MMNode instance, type=' + `self.type` \
			+ ', uid=' + `self.uid` + '>'
	#
	# Private methods to build a tree
	#
	def _addchild(self, child):
		# ASSERT self.type in interiortypes
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
		##_stat('GetParent')
		return self.parent
	#
	def GetRoot(x):
		##_stat('GetRoot')
		root = None
		while x:
			root = x
			x = x.parent
		return root
	#
	def GetPath(x):
		##_stat('GetPath')
		path = []
		while x:
			path.append(x)
			x = x.parent
		path.reverse()
		return path
	#
	def IsAncestorOf(self, x):
		##_stat('IsAncestorOf')
		while x <> None:
			if self == x: return 1
			x = x.parent
		return 0
	#
	def CommonAncestor(self, x):
		##_stat('CommonAncestor')
		p1 = self.GetPath()
		p2 = x.GetPath()
		n = min(len(p1), len(p2))
		i = 0
		while i < n and p1[i] == p2[i]: i = i+1
		if i == 0: return None
		else: return p1[i-1]
	#
	def GetChildren(self):
		##_stat('GetChildren')
		return self.children
	#
	def GetChild(self, i):
		##_stat('GetChild')
		return self.children[i]
	#
	def GetValues(self):
		##_stat('GetValues')
		return self.values
	#
	def GetValue(self, i):
		##_stat('GetValue')
		return self.values[i]
	#
	def GetAttrDict(self):
		return self.attrdict
	#
	def GetRawAttr(self, name):
		##_stat('GetRawAttr' + '.' + name)
		try:
			return self.attrdict[name]
		except KeyError:
			raise NoSuchAttrError, 'in GetRawAttr()'
	#
	def GetRawAttrDef(self, (name, default)):
		##_stat('GetRawAttrDef' + '.' + name)
		try:
			return self.GetRawAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetStyleDict(self):
		##_stat('GetStyleDict')
		return self.context.styledict
	#
	def GetAttr(self, name):
		##_stat('GetAttr' + '.' + name)
		try:
			return self.attrdict[name]
		except KeyError:
			return self.GetDefAttr(name)
	#
	def GetDefAttr(self, name):
		##_stat('GetDefAttr' + '.' + name)
		try:
			styles = self.attrdict['style']
		except KeyError:
			raise NoSuchAttrError, 'in GetDefAttr()'
		return self.context.lookinstyles(name, styles)
	#
	def GetAttrDef(self, (name, default)):
		##_stat('GetAttrDef' + '.' + name)
		try:
			return self.GetAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetInherAttr(x, name):
		##_stat('GetInherAttr' + '.' + name)
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
		##_stat('GetInherDefAttr' + '.' + name)
		try:
			return self.GetDefAttr(name)
		except NoSuchAttrError:
			pass
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
		##_stat('GetInherAttrDef' + '.' + name)
		try:
			return self.GetInherAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetSummary(self, name):
		##_stat('GetSummary')
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
		if self.type == 'imm' or self.values:
			print 'Values:',
			for value in self.values: print value,
			print
		if self.type in interiortypes or self.children:
			print 'Children:',
			for child in self.children: print child.GetType(),
			print
	#
	# Make a "deep copy" of a subtree
	#
	def DeepCopy(self):
		##_stat('DeepCopy')
		uidremap = {}
		copy = self._deepcopy(uidremap, self.context)
		copy._fixuidrefs(uidremap)
		_copyoutgoinghyperlinks(self.context.hyperlinks, uidremap)
		return copy
	#
	# Copy a subtree (deeply) into a new context
	#
	def CopyIntoContext(self, context):
		##_stat('CopyIntoContext')
		uidremap = {}
		copy = self._deepcopy(uidremap, context)
		copy._fixuidrefs(uidremap)
		_copyinternalhyperlinks(self.context.hyperlinks, \
			copy.context.hyperlinks, uidremap)
		return copy
	#
	# Private methods for DeepCopy
	#
	def _deepcopy(self, uidremap, context):
		##_stat('_deepcopy')
		copy = context.newnode(self.type)
		uidremap[self.uid] = copy.uid
		copy.attrdict = _valuedeepcopy(self.attrdict)
		copy.values = _valuedeepcopy(self.values)
		for child in self.children:
			copy._addchild(child._deepcopy(uidremap, context))
		return copy
	#
	def _fixuidrefs(self, uidremap):
		# XXX Are there any other attributes that reference uids?
		self._fixsyncarcs(uidremap)
		for child in self.children:
			child._fixuidrefs(uidremap)
	#
	def _fixsyncarcs(self, uidremap):
		# XXX Exception-wise, this function knows about the
		# semantics and syntax of an attribute...
		try:
			arcs = self.GetRawAttr('synctolist')
		except NoSuchAttrError:
			return
		if not arcs:
			self.DelAttr('synctolist')
		newarcs = []
		for xuid, xsize, delay, yside in arcs:
			if uidremap.has_key(xuid):
				xuid = uidremap[xuid]
			newarcs.append(xuid, xsize, delay, yside)
		if newarcs <> arcs:
			self.SetAttr('synctolist', newarcs)
		
	#
	# Public methods for modifying a tree
	#
	def SetType(self, type):
		if type not in alltypes:
			raise CheckError, 'SetType() bad type'
		if type == self.type:
			return
		if self.type in interiortypes and type in interiortypes:
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
		##_stat('SetAttr')
		self.attrdict[name] = value
		self._updsummaries([name])
	#
	def DelAttr(self, name):
		##_stat('DelAttr')
		if not self.attrdict.has_key(name):
			raise NoSuchAttrError, 'in DelAttr()'
		del self.attrdict[name]
		self._updsummaries([name])
	#
	def Destroy(self):
		##_stat('Destroy')
		if self.parent: raise CheckError, 'Destroy() non-root node'
		self.context.forgetnode(self.uid)
		for child in self.children:
			child.parent = None
			child.Destroy()
		self.type = None
		self.context = None
		self.uid = None
		self.attrdict = None
		self.parent = None
		self.children = None
		self.values = None
		self.summaries = None
		self.widget = None
	#
	def Extract(self):
		##_stat('Extract')
		if not self.parent: raise CheckError, 'Extract() root node'
		parent = self.parent
		self.parent = None
		parent.children.remove(self)
		parent._fixsummaries(self.summaries)
	#
	def AddToTree(self, (parent, i)):
		##_stat('AddToTree')
		if self.parent: raise CheckError, 'AddToTree() non-root node'
		if self.context is not parent.context:
			# XXX Decide how to handle this later
			raise CheckError, 'AddToTree() requires same context'
		if i == -1:
			parent.children.append(self)
		else:
			parent.children.insert(i, self)
		self.parent = parent
		parent._fixsummaries(self.summaries)
		parent._rmsummaries(self.summaries.keys())
	#
	# Methods for mini-document management
	#
	# Check whether a node is the top of a mini-document

	def IsMiniDocument(node):
		if node.GetType() == 'bag':
			return 0
		parent = node.GetParent()
		return parent == None or parent.GetType() == 'bag'

	# Find the first mini-document in a tree

	def FirstMiniDocument(node):
		if node.GetType() <> 'bag':
			return node
		for child in node.GetChildren():
			mini = child.FirstMiniDocument()
			if mini <> None:
				return mini
		return None

	# Find the last mini-document in a tree

	def LastMiniDocument(node):
		if node.GetType() <> 'bag':
			return node
		res = None
		for child in node.GetChildren():
			mini = child.LastMiniDocument()
			if mini <> None:
				res = mini
		return res

	# Find the next mini-document in a tree after the given one
	# Return None if this is the last one

	def NextMiniDocument(node):
		while 1:
			parent = node.GetParent()
			if not parent:
				break
			siblings = parent.GetChildren()
			index = siblings.index(node) # Cannot fail
			while index+1 < len(siblings):
				index = index+1
				mini = siblings[index].FirstMiniDocument()
				if mini <> None:
					return mini
			node = parent
		return None

	# Find the previous mini-document in a tree after the given one
	# Return None if this is the first one

	def PrevMiniDocument(node):
		while 1:
			parent = node.GetParent()
			if not parent:
				break
			siblings = parent.GetChildren()
			index = siblings.index(node) # Cannot fail
			while index > 0:
				index = index-1
				mini = siblings[index].LastMiniDocument()
				if mini <> None:
					return mini
			node = parent
		return None
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
			if summaries[key] == []:
				tofix.remove(key)
		self._updsummaries(tofix)
	#
	def _updsummaries(x, tofix):
		##_stat('_updsummaries')
		while x and tofix:
			for key in tofix[:]:
				if not x.summaries.has_key(key):
					tofix.remove(key)
				else:
					s = x._summarize(key)
					if s == x.summaries[key]:
						tofix.remove(key)
					else:
						x.summaries[key] = s
			x = x.parent
	#
	def _summarize(self, name):
		##_stat('_summarize')
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
	# method for maintaining armed status when the ChannelView is
	# not active
	#
	def setarmedmode_dummy(self, mode):
		self.armedmode = mode


# Make a "deep copy" of an arbitrary value
#
def _valuedeepcopy(value):
	##_stat('_valuedeepcopy')
	if type(value) == type({}):
		copy = {}
		for key in value.keys():
			copy[key] = _valuedeepcopy(value[key])
		return copy
	if type(value) == type([]):
		copy = value[:]
		for i in range(len(copy)):
			copy[i] = _valuedeepcopy(copy[i])
		return copy
	# XXX Assume everything else is immutable.  Not quite true...
	return value


# When a subtree is copied, certain hyperlinks must be copied as well.
# - When copying into another context, all hyperlinks within the copied
#   subtree must be copied.
# - When copying within the same context, all outgoing hyperlinks
#   must be copied as well as all hyperlinks within the copied subtree.
#
# XXX This code knows perhaps more than is good for it about the
# representation of hyperlinks.  However it knows more about anchors
# than would be good for code placed in module Hlinks...
#
def _copyinternalhyperlinks(src_hyperlinks, dst_hyperlinks, uidremap):
	links = src_hyperlinks.getall()
	newlinks = []
	for a1, a2, dir, type in links:
		uid1, aid1 = a1
		uid2, aid2 = a2
		if uidremap.has_key(uid1) and uidremap.has_key(uid2):
			uid1 = uidremap[uid1]
			uid2 = uidremap[uid2]
			a1 = uid1, aid1
			a2 = uid2, aid2
			link = a1, a2, dir, type
			newlinks.append(link)
	if newlinks:
		dst_hyperlinks.addlinks(newlinks)
#
def _copyoutgoinghyperlinks(hyperlinks, uidremap):
	from Hlinks import DIR_1TO2, DIR_2TO1, DIR_2WAY
	links = hyperlinks.getall()
	newlinks = []
	for a1, a2, dir, type in links:
		uid1, aid1 = a1
		uid2, aid2 = a2
		if uidremap.has_key(uid1) and dir in (DIR_1TO2, DIR_2WAY) or \
			uidremap.has_key(uid2) and dir in (DIR_2TO1, DIR_2WAY):
			if uidremap.has_key(uid1):
				uid1 = uidremap[uid1]
				a1 = uid1, aid1
			if uidremap.has_key(uid2):
				uid2 = uidremap[uid2]
				a2 = uid2, aid2
			link = a1, a2, dir, type
			newlinks.append(link)
	if newlinks:
		hyperlinks.addlinks(newlinks)


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

#
# Dummy setarmedmode routine, for use when ChannelView is not active
#
def setarmedmode_dummy(mode):
	node.armedmode = mode
