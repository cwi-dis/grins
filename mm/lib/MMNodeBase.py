__version__ = "$Id$"

# Implementation of Multimedia nodes


from MMExc import *		# Exceptions
from Hlinks import Hlinks
import MMAttrdefs
import os
import MMurl
import settings

from SR import *


from MMTypes import *


# The MMNodeContext class
#
class MMNodeContext:
	def __init__(self, nodeclass):
		self.nodeclass = nodeclass
		self.uidmap = {}
		self.channelnames = []
		self.channels = []
		self.channeldict = {}
		self.hyperlinks = Hlinks()
		self.dirname = None

	def __repr__(self):
		return '<MMNodeContext instance, channelnames=' \
			+ `self.channelnames` + '>'

	def setdirname(self, dirname):
		if not self.dirname:
			self.dirname = dirname
			if not self.dirname:
				self.dirname = '.'
			if self.dirname[-1] <> '/':
				self.dirname = self.dirname + '/'

	def findurl(self, filename):
		"Locate a file given by url-style filename."
## 		if os.name == 'posix':
## 			# XXXX May also work for msdos, etc. (not for mac)
## 			filename = os.path.expandvars(filename)
## 			filename = os.path.expanduser(filename)
		urltype, urlpath = MMurl.splittype(filename)
		if urltype or filename[:1] == '/':
			return filename
		if self.dirname:
			filename = MMurl.basejoin(self.dirname, filename)
		return filename
		
	def newnodeuid(self, type, uid):
		node = self.nodeclass(type, self, uid)
		self.knownode(uid, node)
		return node

	def mapuid(self, uid):
		if not self.uidmap.has_key(uid):
			raise NoSuchUIDError, 'in mapuid()'
		return self.uidmap[uid]

	def knownode(self, uid, node):
		if self.uidmap.has_key(uid):
			raise DuplicateUIDError, 'in knownode()'
		self.uidmap[uid] = node

	#
	# Channel administration
	#
	def addchannels(self, list):
		import MMNode
		for name, dict in list:
			c = MMNode.MMChannel(self, name)
			for key, val in dict.items():
				c[key] = val
			self.channeldict[name] = c
			self.channelnames.append(name)
			self.channels.append(c)

	def getchannel(self, name):
		try:
			return self.channeldict[name]
		except KeyError:
			return None

	#
	# Hyperlink administration
	#
	def addhyperlinks(self, list):
		self.hyperlinks.addlinks(list)


# The Channel class
#
# XXX This isn't perfect: the link between node and channel is still
# XXX through the channel name rather than through the channel object...
#
class MMChannel:
	def __init__(self, context, name):
		self.context = context
		self.name = name
		self.attrdict = {}

	def __repr__(self):
		return '<MMChannel instance, name=' + `self.name` + '>'
	#
	# Emulate the dictionary interface
	#
	def __getitem__(self, key):
		if self.attrdict.has_key(key):
			return self.attrdict[key]
		else:
			# special case for background color
			if key == 'bgcolor' and self.attrdict.has_key('base_window'):
				pname = self.attrdict['base_window']
				pchan = self.context.channeldict[pname]
				return pchan['bgcolor']
			raise KeyError, key

	def __setitem__(self, key, value):
		self.attrdict[key] = value

	def has_key(self, key):
		return self.attrdict.has_key(key)

	def keys(self):
		return self.attrdict.keys()

	def get(self, key, default = None):
		if self.attrdict.has_key(key):
			return self.attrdict[key]
		if key == 'bgcolor' and self.attrdict.has_key('base_window'):
			pname = self.attrdict['base_window']
			pchan = self.context.channeldict.get(pname)
			if pchan:
				return pchan.get('bgcolor', default)
		return default


# The Sync Arc class
#
# XXX This isn't used yet
#
class MMSyncArc:

	def __init__(self, context):
		self.context = context
		self.src = None
		self.dst = None
		self.delay = 0.0

	def __repr__(self):
		return '<MMSyncArc instance, from ' + \
			  `self.src` + ' to ' + `self.dst` + \
			  ', delay ' + `self.delay` + '>'

	def setsrc(self, srcnode, srcend):
		self.src = (srcnode, srcend)

	def setdst(self, dstnode, dstend):
		self.dst = (dstnode, dstend)

	def setdelay(self, delay):
		self.delay = delay


# The Node class
#
class MMNode:
	#
	# Create a new node.
	#
	def __init__(self, type, context, uid):
		# ASSERT type in alltypes
		self.type = type
		self.context = context
		self.uid = uid
		self.attrdict = {}
		self.values = []
		self.playable = 1
	#
	# Return string representation of self
	#
	def __repr__(self):
		try:
			import MMAttrdefs
			name = MMAttrdefs.getattr(self, 'name')
		except:
			name = ''
		return '<MMNode instance, type=%s, uid=%s, name=%s>' % \
		       (`self.type`, `self.uid`, `name`)

	#
	# Public methods for read-only access
	#
	def GetType(self):
		return self.type

	def GetContext(self):
		return self.context

	def GetUID(self):
		return self.uid

	def MapUID(self, uid):
		return self.context.mapuid(uid)

	def GetValues(self):
		return self.values

	def GetValue(self, i):
		return self.values[i]

	def GetAttrDict(self):
		return self.attrdict

	def GetRawAttr(self, name):
		try:
			return self.attrdict[name]
		except KeyError:
			raise NoSuchAttrError, 'in GetRawAttr()'

	def GetRawAttrDef(self, name, default):
		try:
			return self.GetRawAttr(name)
		except NoSuchAttrError:
			return default

	def GetAttr(self, name):
		try:
			return self.attrdict[name]
		except KeyError:
			raise NoSuchAttrError, 'in GetAttr'

	def GetAttrDef(self, name, default):
		try:
			return self.GetAttr(name)
		except NoSuchAttrError:
			return default

	def GetInherAttrDef(self, name, default):
		try:
			return self.GetInherAttr(name)
		except NoSuchAttrError:
			return default

	#
	# Channel management
	#
	def GetChannel(self):
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

	def GetChannelName(self):
		c = self.GetChannel()
		if c: return c.name
		else: return 'undefined'

	def GetChannelType(self):
		c = self.GetChannel()
		if c and c.has_key('type'):
			return c['type']
		else:
			return ''

	#
	# Playability depending on system/environment parameters
	#
	def SetPlayability(self, playable=1, getchannelfunc=None):
		if playable:
			playable = self._compute_playable()
		if playable and self.type in leaftypes and getchannelfunc:
			# For media nodes check that the channel likes
			# the node
			chan = getchannelfunc(self)
			if not chan or not chan.getaltvalue(self):
				playable = 0
		self.playable = playable
		for child in self.children:
			child.SetPlayability(playable, getchannelfunc)

	def IsPlayable(self):
		return self.playable

	def _compute_playable(self):
		all = settings.getsettings()
		for setting in all:
			if self.attrdict.has_key(setting):
				ok = settings.match(setting,
						    self.attrdict[setting])
				if not ok:
					return 0
		return 1
