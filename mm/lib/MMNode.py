# Implementation of Multimedia nodes


from MMExc import *		# Exceptions
from Hlinks import Hlinks
import MMAttrdefs

from SR import SCHED, SCHED_DONE, PLAY, PLAY_DONE, \
	  SCHED_STOP, PLAY_STOP, SYNC, SYNC_DONE, PLAY_ARM, ARM_DONE


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
		self.channels = []
		self.channeldict = {}
		self.hyperlinks = Hlinks().init()
		self.editmgr = None
		self.dirname = None
		return self
	#
	def __repr__(self):
		##_stat('__repr__')
		return '<MMNodeContext instance, channelnames=' \
			+ `self.channelnames` + '>'
	#
	def setdirname(self, dirname):
		##_stat('setdirname')
		if not self.dirname:
			self.dirname = dirname
	#
	def findfile(self, filename):
		##_stat('findfile')
		import os
		if os.path.isabs(filename):
			return filename
		if self.dirname:
			altfilename = os.path.join(self.dirname, filename)
			if os.path.exists(altfilename):
				return altfilename
		# As a last resort, search along the cmif search path
		import cmif
		return cmif.findfile(filename)
	#
	def newnode(self, type):
		##_stat('newnode')
		return self.newnodeuid(type, self.newuid())
	#
	def newnodeuid(self, type, uid):
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
	def knownode(self, uid, node):
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
	# Channel administration
	#
	def addchannels(self, list):
		##_stat('addchannels')
		for name, dict in list:
			c = MMChannel().init(self, name)
			for key in dict.keys():
				c[key] = dict[key]
			self.channeldict[name] = c
			self.channelnames.append(name)
			self.channels.append(c)
	#
	def getchannel(self, name):
		##_stat('getchannel')
		if name in self.channelnames:
			return self.channeldict[name]
		else:
			return None
	#
	def addchannel(self, name, i, type):
		##_stat('addchannel')
		if name in self.channelnames:
			raise CheckError, 'addchannel: existing name'
		if not 0 <= i <= len(self.channelnames):
			raise CheckError, 'addchannel: invalid position'
		c = MMChannel().init(self, name)
		c['type'] = type
		self.channeldict[name] = c
		self.channelnames.insert(i, name)
		self.channels.insert(i, c)
	#
	def delchannel(self, name):
		##_stat('delchannel')
		if name not in self.channelnames:
			raise CheckError, 'delchannel: non-existing name'
		i = self.channelnames.index(name)
		c = self.channels[i]
		del self.channels[i]
		del self.channelnames[i]
		del self.channeldict[name]
		c._destroy()
	#
	def setchannelname(self, oldname, newname):
		##_stat('setchannelname')
		if newname == oldname: return # No change
		if newname in self.channelnames:
			raise CheckError, 'setchannelname: duplicate name'
		i = self.channelnames.index(oldname)
		c = self.channeldict[oldname]
		self.channeldict[newname] = c
		c._setname(newname)
		self.channelnames[i] = newname
		del self.channeldict[oldname]
		# Patch references to this channel in nodes
		for uid in self.uidmap.keys():
			n = self.uidmap[uid]
			try:
				if n.GetRawAttr('channel') == oldname:
					n.SetAttr('channel', newname)
			except NoSuchAttrError:
				pass
		# Patch references to this channel in styles
		for stylename in self.styledict.keys():
			s = self.styledict[stylename]
			if s.has_key('channel'):
				if s['channel'] == oldname:
					s['channel'] = newname
	#
	# Hyperlink administration
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
		##_stat('seteditmgr')
		self.editmgr = editmgr
	#
	def geteditmgr(self):
		##_stat('geteditmgr')
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
	def lookinstyles(self, name, styles):
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
	def _isgoodlink(self, link):
		(uid1, aid1), (uid2, aid2), dir, type = link
		return self.uidmap.has_key(uid1) \
		   and self.uidmap.has_key(uid2) \
		   and self.uidmap[uid1].GetRoot() in self._roots \
		   and self.uidmap[uid2].GetRoot() in self._roots


# The Channel class
#
# XXX This isn't perfect: the link between node and channel is still
# XXX through the channel name rather than through the channel object...
#
class MMChannel:
	#
	def init(self, context, name):
		self.context = context
		self.name = name
		self.attrdict = {}
		return self
	#
	def _setname(self, name): # Only called from context.setchannelname()
		self.name = name
	#
	def _destroy(self):
		self.context = None
	#
	def stillvalid(self):
		return self.context is not None
	#
	def _getdict(self): # Only called from MMWrite.fixroot()
		return self.attrdict
	#
	def __repr__(self):
		return '<MMChannel instance, name=' + `self.name` + '>'
	#
	# Emulate the dictionary interface
	#
	def __getitem__(self, key):
		return self.attrdict[key]
	#
	def __setitem__(self, key, value):
		self.attrdict[key] = value
	#
	def __delitem__(self, key):
		del self.attrdict[key]
	#
	def has_key(self, key):
		return self.attrdict.has_key(key)
	#
	def keys(self):
		return self.attrdict.keys()


# The Sync Arc class
#
# XXX This isn't used yet
#
class MMSyncArc:
	#
	def init(self, context):
		self.context = context
		self.src = None
		self.dst = None
		self.delay = 0.0
		return self
	#
	def __repr__(self):
		return '<MMSyncArc instance, from ' + \
			  `self.src` + ' to ' + `self.dst` + \
			  ', delay ' + `self.delay` + '>'
	#
	def setsrc(self, srcnode, srcend):
		self.src = (srcnode, srcend)
	#
	def setdst(self, dstnode, dstend):
		self.dst = (dstnode, dstend)
	#
	def setdelay(self, delay):
		self.delay = delay


# The Node class
#
class MMNode:
	#
	# Create a new node.
	#
	def Init(self, type, context, uid):
		# ASSERT type in alltypes
		self.type = type
		self.context = context
		self.uid = uid
		self.attrdict = {}
		self.parent = None
		self.children = []
		self.values = []
		self.summaries = {}
		self.armedmode = None
		return self
	#
	# Return string representation of self
	#
	def __repr__(self):
		return '<MMNode instance, type=' + `self.type` \
			+ ', uid=' + `self.uid` + '>'
	#
	# Compare two nodes, recursively.
	# This purposely ignores the value of the context.
	# (The uid is compared, so a deep copy will compare different.
	# This is hard to avoid since deep copying may also change
	# attributes that contain uid references.)
	#
	def __cmp__(self, other):
		##_stat('__cmp__')
		i = cmp(self.type, other.type)
		if i: return i
		i = cmp(self.uid, other.uid)
		if i: return i
		i = cmp(self.attrdict, other.attrdict)
		if i: return i
		if self.type in interiortypes:
			return cmp(self.children, other.children)
		elif self.type == 'imm':
			return cmp(self.values, other.values)
		else:
			return 0
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
	def _setattr(self, name, value):
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
		##_stat('GetRawAttr.' + name)
		try:
			return self.attrdict[name]
		except KeyError:
			raise NoSuchAttrError, 'in GetRawAttr()'
	#
	def GetRawAttrDef(self, name, default):
		##_stat('GetRawAttrDef.' + name)
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
		##_stat('GetAttr.' + name)
		try:
			return self.attrdict[name]
		except KeyError:
			return self.GetDefAttr(name)
	#
	def GetDefAttr(self, name):
		##_stat('GetDefAttr.' + name)
		try:
			styles = self.attrdict['style']
		except KeyError:
			raise NoSuchAttrError, 'in GetDefAttr()'
		return self.context.lookinstyles(name, styles)
	#
	def GetAttrDef(self, name, default):
		##_stat('GetAttrDef.' + name)
		try:
			return self.GetAttr(name)
		except NoSuchAttrError:
			return default
	#
	def GetInherAttr(x, name):
		##_stat('GetInherAttr.' + name)
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
		##_stat('GetInherDefAttr.' + name)
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
	def GetInherAttrDef(self, name, default):
		##_stat('GetInherAttrDef.' + name)
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
	# Channel management
	#
	def GetChannel(self):
		##_stat('GetChannel')
		try:
			cname = self.GetInherAttr('channel')
		except NoSuchAttrError:
			return None
		if cname == '':
			return None
		if self.context.channeldict.has_key(cname):
			return self.context.channeldict[cname]
		else:
			return None
	#
	def GetChannelName(self):
		##_stat('GetChannelName')
		c = self.GetChannel()
		if c: return c.name
		else: return 'undefined'
	#
	def GetChannelType(self):
		##_stat('GetChannelType')
		c = self.GetChannel()
		if c and c.has_key('type'):
			return c['type']
		else:
			return ''
	#
	def SetChannel(self, c):
		##_stat('SetChannel')
		if c is None:
			try:
				self.DelAttr('channel')
			except NoSuchAttrError:
				pass
		else:
			self.SetAttr('channel', c.name)
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
	def SetAttr(self, name, value):
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
	#
	def Extract(self):
		##_stat('Extract')
		if not self.parent: raise CheckError, 'Extract() root node'
		parent = self.parent
		self.parent = None
		parent.children.remove(self)
		parent._fixsummaries(self.summaries)
	#
	def AddToTree(self, parent, i):
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
	def set_armedmode(self, mode):
		self.armedmode = mode

	#
	# Methods for building scheduler records. The interface is as follows:
	# - PruneTree() is called first, with a parameter that specifies the
	#   node to seek to (where we want to start playing). None means 'play
	#   everything'. PruneTree() sets the scope of all the next calls and
	#   initializes a few data structures in the tree nodes.
	# - Next GetArcList() should be called to obtain a list of all sync
	#   arcs with destinations in the current tree.
	# - Next FilterArcList() is called to filter out the sync arcs with
	#   a source outside the current tree.
	# - Finally gensr() is called in a loop to obtain a complete list of
	#   scheduler records. (There was a very good reason for the funny
	#   calling sequence of gensr(). I cannot seem to remember it at
	#   the moment, though).
	# - Call EndPruneTree() to clear the garbage.
	def PruneTree(self, seeknode):
		if seeknode == self:
			seeknode = None
		if seeknode and not self.IsAncestorOf(seeknode):
			raise 'Seeknode not in tree!'
		self.sync_from = ([],[])
		self.sync_to = ([],[])
		if self.type in ('imm', 'ext'):
			return
		self.wtd_children = []
		if self.type == 'seq':
			for c in self.children:
				if seeknode and c.IsAncestorOf(seeknode):
					self.wtd_children.append(c)
					c.PruneTree(seeknode)
					seeknode = None
				elif not seeknode:
					self.wtd_children.append(c)
					c.PruneTree(None)
		elif self.type == 'par':
			for c in self.children:
				self.wtd_children.append(c)
				if c.IsAncestorOf(seeknode):
					c.PruneTree(seeknode)
				else:
					c.PruneTree(None)
		else:
			raise 'Cannot PruneTree() on nodes of this type', \
				  self.type
	#
	def EndPruneTree(self):
		del self.sync_from
		del self.sync_to
		if self.type in ('seq', 'par'):
			for c in self.wtd_children:
				c.EndPruneTree()
			del self.wtd_children
	#
	def gensr(self):
		if self.type in ('imm', 'ext'):
			return self.gensr_leaf(), []
		elif self.type == 'seq':
			rv = self.gensr_seq(), self.wtd_children
			return rv
		elif self.type == 'par':
			rv = self.gensr_par(), self.wtd_children
			return rv
		raise 'Cannot gensr() for nodes of this type', self.type

	#
	# Generate schedrecords for leaf nodes.
	#
	# We distinguish 3 cases for when to stop displaying a node:
	# 1. If there's a sync arc to the tail of the node we stop playing
	#    when the sync arc fired
	# 2. If we have inherited timing we stop playing when the parent node
	#    sends us a SCHED_DONE
	# 3. If we have implicit timing we just stop playing immedeately.
	#
	def gensr_leaf(self):
		in0, out0, in1, out1 = self.gensr_arcs()
		arg = self
		if in1:
			return [\
			  ([(SCHED, arg), (ARM_DONE, arg)]+in0,\
			                           [(PLAY, arg)     ]+out0),\
			  ([(PLAY_DONE, arg) ]+in1,[(SCHED_DONE,arg), \
			                            (PLAY_STOP, arg)]+out1),\
			  ([(SCHED_STOP, arg)]    ,[]) ]
		if not MMAttrdefs.getattr(self, 'duration'):
			return [\
			  ([(SCHED, arg), (ARM_DONE, arg)]+in0,\
			                           [(PLAY, arg)     ]+out0),\
			  ([(PLAY_DONE, arg) ]    ,[(SCHED_DONE,arg)]+out1),\
			  ([(SCHED_STOP, arg)]    ,[(PLAY_STOP, arg)]) ]
		else:
			print 'Duration set to',MMAttrdefs.getattr(self, 'duration') 
			return [\
			  ([(SCHED, arg), (ARM_DONE, arg)]+in0,\
			                           [(PLAY, arg)     ]+out0),\
			  ([(PLAY_DONE, arg) ]    ,[(SCHED_DONE,arg), \
			                            (PLAY_STOP, arg)]+out1),\
			  ([(SCHED_STOP, arg)]    ,[]) ]
	#
	# Generate schedrecords for a sequential node
	def gensr_seq(self):
		n_sr = len(self.wtd_children)+1
		sr_list = []
		last_actions = []
		in0, out0, in1, out1 = self.gensr_arcs()
		for i in range(n_sr):
			if i == 0:
				prereq = [(SCHED, self)] + in0
				actions = out0
			else:
				prereq = [(SCHED_DONE, self.wtd_children[i-1])]
				actions = [(SCHED_STOP, self.wtd_children[i-1])]
			if i == n_sr-1:
				last_actions = actions
				actions = [(SCHED_DONE, self)]
			else:
				actions.append((SCHED, self.wtd_children[i]))
			sr_list.append((prereq, actions))
		sr_list.append( ([(SCHED_STOP, self)]+in1, last_actions+out1) )
		return sr_list

	def gensr_par(self):
		in0, out0, in1, out1 = self.gensr_arcs()
		if not self.wtd_children:
			# Empty node needs special code:
			return [ \
			     ([(SCHED, self)]+in0,[(SCHED_DONE, self)]+out0),\
			     ([(SCHED_STOP, self)]+in1,out1) ]
		alist = []
		plist = []
		slist = []
		for i in self.wtd_children:
			arg = i
			alist.append((SCHED, arg))
			plist.append((SCHED_DONE, arg))
			slist.append((SCHED_STOP, arg))
		return [  ([(SCHED, self) ]+in0, alist+out0), \
			  ( plist, [(SCHED_DONE, self)]), \
			  ([(SCHED_STOP, self)]+in1, slist+out1) ]
	#
	# gensr_arcs returns 4 lists of sync arc events: incoming head,
	# outgoing head, incoming tail, outgoing tail.
	#
	def gensr_arcs(self):
		in0 = []
		out0 = []
		in1 = []
		out1 = []
		for i in self.sync_from[0]:
			in0.append((SYNC_DONE, i))
		for i in self.sync_from[1]:
			in1.append((SYNC_DONE, i))
		for i in self.sync_to[0]:
			out0.append((SYNC, i))
		for i in self.sync_to[1]:
			out1.append((SYNC, i))
		return in0, out0, in1, out1
			
	#
	# Methods to handle sync arcs.
	#
	# The GetArcList method recursively gets a list of sync arcs
	# The sync arcs are returned as (n1, s1, n2, s2, delay) tuples.
	# Unused sync arcs are not filtered out of the list yet.
	# As a side effect the members sync_from and sync_to are set empty.
	#
	def GetArcList(self):
		if not self.GetSummary('synctolist'):
			return []
		synctolist = []
		arcs = self.GetAttrDef('synctolist', [])
		for arc in arcs:
			n1uid, s1, delay, s2 = arc
			synctolist.append((self.MapUID(n1uid), s1, \
				  self, s2, delay))
		if self.GetType() in interiortypes:
			for c in self.wtd_children:
				synctolist = synctolist + c.GetArcList()
		return synctolist
	#
	# FilterArcList removes all arcs if they are not part of the
	# subtree rooted at this node.
	#
	def FilterArcList(self, arclist):
		newlist = []
		for arc in arclist:
			n1, s1, n2, s2, delay = arc
			if self.IsWtdAncestorOf(n1) and \
				  self.IsWtdAncestorOf(n2):
				newlist.append(arc)
		return newlist
	#
	def IsWtdAncestorOf(self, x):
		while x <> None:
			if self == x: return 1
			xnew = x.parent
			try:
				if not x in xnew.wtd_children:
					return 0
			except AttributeError:
				return 0
			x = xnew
		return 0
	#
	def GetWtdChildren(self):
		return self.wtd_children
		
	#
	# SetArcSrc sets the source of a sync arc.
	# XXXX This can be done so that gensr_arcs has nothing more to do.
	#
	def SetArcSrc(self, side, delay, aid):
		self.sync_to[side].append((delay, aid))

	#
	# SetArcDst sets the destination of a sync arc.
	#
	def SetArcDst(self, side, aid):
		self.sync_from[side].append(aid)
			
		


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

