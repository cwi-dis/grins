__version__ = "$Id$"

import MMAttrdefs
from MMTypes import *
from MMExc import *
from SR import *
from AnchorDefs import *
import Duration
from Hlinks import Hlinks
import MMurl
import settings
import features
from HDTL import HD, TL
import string
import MMStates

debuggensr = 0

class MMNodeContext:
	def __init__(self, nodeclass):
		self.nodeclass = nodeclass
		self.uidmap = {}
		self.channelnames = []
		self.channels = []
		self.channeldict = {}
		self.hyperlinks = Hlinks()
		self.layouts = {}
		self.usergroups = {}
		self.transitions = {}
		self.baseurl = None
		self.nextuid = 1
		self.editmgr = None
		self.armedmode = None
		self.getchannelbynode = None
		self.title = None
		self.attributes = {}	# unrecognized SMIL meta values
		self.__registers = []
		self.externalanchors = []
		self._ichannelnames = []  # internal channels
		self._ichannels = []
		self._ichanneldict = {}
		self.comment = ''

	def __repr__(self):
		return '<MMNodeContext instance, channelnames=' \
			+ `self.channelnames` + '>'

	def settitle(self, title):
		self.title = title

	def gettitle(self):
		return self.title

	def setbaseurl(self, baseurl):
		if baseurl:
			# delete everything after last slash
			i = string.rfind(baseurl, '/')
			if i >= 0:
				baseurl = baseurl[:i+1]
		self.baseurl = baseurl

	def findurl(self, url):
		"Locate a file given by url-style filename."
		if self.baseurl:
			url = MMurl.basejoin(self.baseurl, url)
		return url

	def relativeurl(self, url):
		"Convert a URL to something that is relative to baseurl."
		url = MMurl.canonURL(url)
		baseurl = MMurl.canonURL(self.baseurl or '')
		if url[:len(baseurl)] == baseurl:
			url = url[len(baseurl):]
		return url

	def newnode(self, type):
		return self.newnodeuid(type, self.newuid())

	def newnodeuid(self, type, uid):
		node = self.nodeclass(type, self, uid)
		self.knownode(uid, node)
		return node

	def newuid(self):
		while 1:
			uid = `self.nextuid`
			self.nextuid = self.nextuid + 1
			if not self.uidmap.has_key(uid):
				return uid

	def mapuid(self, uid):
		if not self.uidmap.has_key(uid):
			raise NoSuchUIDError, 'in mapuid()'
		return self.uidmap[uid]

	def knownode(self, uid, node):
		if self.uidmap.has_key(uid):
			raise DuplicateUIDError, 'in knownode()'
		self.uidmap[uid] = node

	def forgetnode(self, uid):
		del self.uidmap[uid]

	def newanimatenode(self, tagname='animate'):
		node = self.newnodeuid('imm', self.newuid())
		node.attrdict['type'] = 'animate'
		node.attrdict['tag'] = tagname
		node.attrdict['mimetype'] = 'animate/%s' % tagname
		chname = 'animate%s' % node.GetUID()
		node.attrdict['channel'] = chname
		self.addinternalchannels( [(chname, node.attrdict), ] )
		return node

	#
	# Channel administration
	#
	def compatchannels(self, url = None, chtype = None):
		# return a list of channels compatible with the given URL
		if url:
			# ignore chtype if url is set
			import MMmimetypes, ChannelMime
			mtype = MMmimetypes.guess_type(url)[0]
			if not mtype:
				return []
			if mtype == 'application/vnd.rn-realmedia':
				# for RealMedia look inside the file
				import realsupport
				info = realsupport.getinfo(self.findurl(url))
				if info and not info.has_key('width'):
					mtype = 'audio/vnd.rn-realaudio'
				else:
					mtype = 'video/vnd.rn-realvideo'
			chtypes = ChannelMime.MimeChannel.get(mtype, [])
		elif chtype:
			chtypes = [chtype]
		else:
			# no URL and no channel type given
			return []
		chlist = []
		for ch in self.channels:
			if ch['type'] in chtypes:
				chlist.append(ch.name)
		chlist.sort()
		return chlist

	def addchannels(self, list):
		for name, dict in list:
			c = MMChannel(self, name)
##			for key, val in dict.items():
##				c[key] = val
			c.attrdict = dict # we know the internals...
			self.channeldict[name] = c
			self.channelnames.append(name)
			self.channels.append(c)

	def getchannel(self, name):
		try:
			return self.channeldict[name]
		except KeyError:
			return None

	def addchannel(self, name, i, type):
		if name in self.channelnames:
			raise CheckError, 'addchannel: existing name'
		if not 0 <= i <= len(self.channelnames):
			raise CheckError, 'addchannel: invalid position'
		c = MMChannel(self, name)
		c['type'] = type
		self.channeldict[name] = c
		self.channelnames.insert(i, name)
		self.channels.insert(i, c)

	def copychannel(self, name, i, orig):
		if name in self.channelnames:
			raise CheckError, 'copychannel: existing name'
		if not 0 <= i <= len(self.channelnames):
			raise CheckError, 'copychannel: invalid position'
		if not orig in self.channelnames:
			raise CheckError, 'copychannel: non-existing original'
		c = MMChannel(self, name)
		orig_i = self.channelnames.index(orig)
		orig_ch = self.channels[orig_i]
		for attr in orig_ch.keys():
		    c[attr] = eval(repr(orig_ch[attr]))
		self.channeldict[name] = c
		self.channelnames.insert(i, name)
		self.channels.insert(i, c)

	def movechannel(self, name, i):
		if not name in self.channelnames:
			raise CheckError, 'movechannel: non-existing name'
		if not 0 <= i <= len(self.channelnames):
			raise CheckError, 'movechannel: invalid position'
		old_i = self.channelnames.index(name)
		if old_i == i:
		    return
		self.channels.insert(i, self.channels[old_i])
		self.channelnames.insert(i, name)
		if old_i < i:
		    del self.channelnames[old_i]
		    del self.channels[old_i]
		else:
		    del self.channelnames[old_i+1]
		    del self.channels[old_i+1]

	def delchannel(self, name):
		if name not in self.channelnames:
			raise CheckError, 'delchannel: non-existing name'
		i = self.channelnames.index(name)
		c = self.channels[i]
		for channels in self.layouts.values():
			for j in range(len(channels)):
				if c is channels[j]:
					del channels[j]
					break
		del self.channels[i]
		del self.channelnames[i]
		del self.channeldict[name]
		c._destroy()

	def setchannelname(self, oldname, newname):
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
			if n.GetRawAttrDef('channel', None) == oldname:
				n.SetAttr('channel', newname)
		# Patch references to this channel in other channels
		for ch in self.channels:
			if ch.get('base_window') == oldname:
				ch['base_window'] = newname

	def registergetchannelbynode(self, func):
		self.getchannelbynode = func

	def addinternalchannels(self, list):
		for name, dict in list:
			c = MMChannel(self, name)
			c.attrdict = dict
			self._ichanneldict[name] = c
			self._ichannelnames.append(name)
			self._ichannels.append(c)

	#
	# Hyperlink administration
	#
	def addhyperlinks(self, list):
		self.hyperlinks.addlinks(list)

	def addhyperlink(self, link):
		self.hyperlinks.addlink(link)

	def sanitize_hyperlinks(self, roots):
		"""Remove all hyperlinks that aren't contained in the given trees
		   (note that the argument is a *list* of root nodes)"""
		self._roots = roots
		badlinks = self.hyperlinks.selectlinks(self._isbadlink)
		del self._roots
		for link in badlinks:
			self.hyperlinks.dellink(link)

	def get_hyperlinks(self, root):
		"""Return all hyperlinks pertaining to the given tree
		   (note that the argument is a *single* root node)"""
		self._roots = [root]
		links = self.hyperlinks.selectlinks(self._isgoodlink)
		del self._roots
		return links

	def getexternalanchors(self):
		return self.externalanchors

	#
	# Layout administration
	#
	def addlayouts(self, list):
		for name, channels in list:
			chans = []
			for channame in channels:
				chan = self.channeldict.get(channame)
				if chan is None:
					print 'channel %s in layout %s does not exist' % (channame, name)
				else:
					chans.append(chan)
			self.layouts[name] = chans

	def addlayout(self, name):
		if self.layouts.has_key(name):
			raise CheckError, 'addlayout: existing name'
		self.layouts[name] = []

	def dellayout(self, name):
		if not self.layouts.has_key(name):
			raise CheckError, 'dellayout: non-existing name'
		del self.layouts[name]

	def setlayoutname(self, oldname, newname):
		if newname == oldname: return # No change
		if self.layouts.has_key(newname):
			raise CheckError, 'setlayoutname: duplicate name'
		layout = self.layouts.get(oldname)
		if layout is None:
			raise CheckError, 'setlayoutname: unknown layout'
		del self.layouts[oldname]
		self.layouts[newname] = layout
		# Patch references to this layout in nodes
		for uid in self.uidmap.keys():
			n = self.uidmap[uid]
			if n.GetRawAttrDef('layout', None) == oldname:
				n.SetAttr('layout', newname)

	def addlayoutchannel(self, name, channel):
		channels = self.layouts.get(name)
		if channels is None:
			raise CheckError, 'addlayoutchannel: non-existing name'
		for ch in channels:
			if ch is channel:
				raise CheckError, 'addlayoutchannel: channel already in layout'
		channels.append(channel)

	def dellayoutchannel(self, name, channel):
		channels = self.layouts.get(name)
		if channels is None:
			raise CheckError, 'dellayoutchannel: non-existing name'
		for i in range(len(channels)):
			if channels[i] is channel:
				del channels[i]
				return
		raise CheckError, 'dellayoutchannel: channel not in layout'

	#
	# User group administration
	#
	def addusergroups(self, list):
		for name, value in list:
			title, rendered, allowed = value
			rendered = ['NOT RENDERED', 'RENDERED'][rendered]
			allowed = ['not allowed', 'allowed'][allowed]
			self.usergroups[name] = title, rendered, allowed

	def addusergroup(self, name, value):
		if self.usergroups.has_key(name):
			raise CheckError, 'addusergroup: existing name'
		self.usergroups[name] = value

	def delusergroup(self, name):
		if not self.usergroups.has_key(name):
			raise CheckError, 'delusergroup: non-existing name'
		del self.usergroups[name]

	def setusergroupname(self, oldname, newname):
		if newname == oldname: return # No change
		if self.usergroups.has_key(newname):
			raise CheckError, 'setusergroup: existing name'
		if not self.usergroups.has_key(oldname):
			raise CheckError, 'setusergroup: non-existing name'
		self.usergroups[newname] = self.usergroups[oldname]
		del self.usergroups[oldname]
		# Patch references to this usergroup in nodes
		for uid in self.uidmap.keys():
			n = self.uidmap[uid]
			if n.GetRawAttrDef('usergroup', None) == oldname:
				n.SetAttr('usergroup', newname)

	#
	# transition administration
	#
	def addtransitions(self, list):
		for name, valuedict in list:
			self.transitions[name] = valuedict

	def addtransition(self, name, valuedict):
		if self.transitions.has_key(name):
			raise CheckError, 'addtransition: existing name'
		self.transitions[name] = valuedict

	def deltransition(self, name):
		if not self.transitions.has_key(name):
			raise CheckError, 'deltransition: non-existing name'
		del self.transitions[name]

	def settransitionname(self, oldname, newname):
		if newname == oldname: return # No change
		if self.transitions.has_key(newname):
			raise CheckError, 'settransition: existing name'
		if not self.transitions.has_key(oldname):
			raise CheckError, 'settransition: non-existing name'
		self.transitions[newname] = self.transitions[oldname]
		del self.transitions[oldname]
		# Patch references to this transition in nodes
		for uid in self.uidmap.keys():
			n = self.uidmap[uid]
			if n.GetRawAttrDef('transIn', None) == oldname:
				n.SetAttr('transIn', newname)
			if n.GetRawAttrDef('transOut', None) == oldname:
				n.SetAttr('transOut', newname)

	# Internal: predicates to select nodes pertaining to self._roots
	def _isbadlink(self, link):
		return not self._isgoodlink(link)

	def _isgoodlink(self, link):
		a1, a2, dir, ltype = link
		if type(a1) is type(()):
			uid1, aid1 = a1
			srcok = (self.uidmap.has_key(uid1) and
				 self.uidmap[uid1].GetRoot() in self._roots)
		else:
			srcok = 0
		if type(a2) is type(()):
			uid2, aid2 = a2
			dstok = (('/' in uid2) or
				 (self.uidmap.has_key(uid2) and
				  self.uidmap[uid2].GetRoot() in self._roots))
		else:
			dstok = 1
		return (srcok and dstok)

	#
	# Editmanager
	#
	def seteditmgr(self, editmgr):
		self.editmgr = editmgr
		for x in self.__registers:
			editmgr.registerfirst(x)
		self.__registers = []

	def geteditmgr(self):
		return self.editmgr

	def register(self, x):
		if self.editmgr:
			self.editmgr.registerfirst(x)
		else:
			self.__registers.append(x)

class MMChannel:
	def __init__(self, context, name):
		self.context = context
		self.name = name
		self.attrdict = {}

	def __repr__(self):
		return '<MMChannel instance, name=' + `self.name` + '>'

	def _setname(self, name): # Only called from context.setchannelname()
		self.name = name

	def _destroy(self):
		self.context = None

	def stillvalid(self):
		return self.context is not None

	def _getdict(self): # Only called from MMWrite.fixroot()
		return self.attrdict

	# new 03-07-2000
	# up in the channel tree until find a layoutchannel.
	# a layout channel can be translated directly in SMIL region
	def GetLayoutChannel(self):
		# actualy the layout channel is directly the parent channel
		cname = self.attrdict.get('base_window')
		if not cname:
			return None
		return self.context.channeldict.get(cname)
	# end new	

	#
	# Emulate the dictionary interface
	#
	def __getitem__(self, key):
		if self.attrdict.has_key(key):
			return self.attrdict[key]
		else:
			# special case for background color
			if key == 'bgcolor' and \
			   self.attrdict.has_key('base_window') and \
			   self.attrdict.get('transparent', 0) <= 0:
				pname = self.attrdict['base_window']
				pchan = self.context.channeldict[pname]
				return pchan['bgcolor']
			raise KeyError, key

	def setvisiblechannelattrs(self):
		from windowinterface import UNIT_PXL
		if not settings.get('cmif'):
			self.attrdict['units'] = UNIT_PXL
			self.attrdict['transparent'] = 1
			self.attrdict['center'] = 0
			self.attrdict['drawbox'] = 0
			self.attrdict['scale'] = 1
		if features.compatibility == features.G2:
			# specialized settings for G2-compatibility
			self.attrdict['units'] = UNIT_PXL
			self.attrdict['transparent'] = -1
			self.attrdict['center'] = 0
			self.attrdict['drawbox'] = 0
			if type in ('image', 'video'):
				self.attrdict['scale'] = 1
			if type in ('text', 'RealText'):
				self.attrdict['bgcolor'] = 255,255,255
			else:
				self.attrdict['bgcolor'] = 0,0,0

	def __setitem__(self, key, value):
		if key == 'type':
			import ChannelMap
			if ChannelMap.isvisiblechannel(value) and (not self.attrdict.has_key(key) or not ChannelMap.isvisiblechannel(self.attrdict[key])):
				self.setvisiblechannelattrs()
		self.attrdict[key] = value

	def __delitem__(self, key):
		del self.attrdict[key]

	def has_key(self, key):
		return self.attrdict.has_key(key)

	def keys(self):
		return self.attrdict.keys()

	def items(self):
		return self.attrdict.items()

	def get(self, key, default = None):
		if self.attrdict.has_key(key):
			return self.attrdict[key]
		if key == 'bgcolor' and \
		   self.attrdict.has_key('base_window') and \
		   self.attrdict.get('transparent', 0) <= 0:
			pname = self.attrdict['base_window']
			pchan = self.context.channeldict.get(pname)
			if pchan:
				return pchan.get('bgcolor', default)
		return default

# The Sync Arc class
#
class MMSyncArc:
	def __init__(self, dstnode, action, srcnode=None, event=None, marker=None, delay=None):
		if __debug__:
			if event is None and marker is None:
				assert srcnode is None
			else:
				assert srcnode is not None
			if srcnode is None:
				assert event is None and marker is None
			else:
				assert event is not None or marker is not None
		self.dstnode = dstnode
		self.isstart = action == 'begin'
		self.srcnode = srcnode	# None if parent; "prev" if previous; else MMNode instance
		self.event = event
		self.marker = marker
		self.delay = delay
		self.qid = None

	def __repr__(self):
		if self.srcnode is None:
			src = 'syncbase'
		elif self.srcnode == 'prev':
			src = 'prev'
		else:
			src = `self.srcnode`
		if self.event is not None:
			src = src + '.' + self.event
		if self.marker is not None:
			src = src + '.marker(%s)' % self.marker
		if self.delay:
			if self.delay > 0:
				src = src + '+%g' % self.delay
			else:
				src = src + '%g' % self.delay
		dst = `self.dstnode`
		if self.isstart:
			dst = dst + '.begin'
		else:
			dst = dst + '.end'
		return '<MMSyncArc instance, from %s to %s>' % (src, dst)

	def refnode(self):
		node = self.dstnode
		if self.srcnode == 'prev' or (self.srcnode is None and node.parent.type == 'seq'):
			refnode = node.parent
			for c in refnode.children:
				if c is node:
					break
				refnode = c
		elif self.srcnode is None:
			refnode = node.parent
			refnode = refnode.looping_body_self or refnode
		elif self.srcnode is node:
			refnode = node.looping_body_self or node
		else:
			refnode = self.srcnode
		return refnode

	def isresolved(self):
		if self.delay is None:
			return 0
		refnode = self.refnode()
		if self.event is None and self.marker is None:
			return 1
		if self.event in ('begin', 'end'):
			if refnode.playing in (MMStates.PLAYING, MMStates.PLAYED):
				return 1
			# XXX or maybe if refnode.isscheduled(): return 1
			return 0
		if self.event is not None and refnode.eventhappened(self.event):
			return 1
		if self.marker is not None and refnode.markerhappened(self.marker):
			return 1
		return 0

	def resolvedtime(self):
		refnode = self.refnode()
		if self.event == 'begin':
			return refnode.start_time + self.delay
##		if self.event == 'end':
##			return refnode.end_time + self.delay
		if self.event is not None:
			return refnode.happenings[('event', self.event)] + self.delay
		if self.marker is not None:
			return refnode.happenings[('marker', self.marker)] + self.delay
		if self.dstnode.parent.type == 'seq':
			event = 'end'
		else:
			event = 'begin'
		return refnode.happenings[('event', event)] + self.delay
			

class MMNode_body:
	"""Helper for looping nodes"""
	helpertype = "looping"
	
	def __init__(self, parent):
		self.parent = parent
		self.sched_children = []
		self.arcs = []
		print 'MMNode_body.__init__', `self`

	def __repr__(self):
		return "<%s body of %s>"%(self.helpertype, self.parent.__repr__())

	def __getattr__(self, name):
		if name == 'attrcache':
			raise AttributeError, 'Not allowed'
		return getattr(self.parent, name)

	def GetUID(self):
		return '%s-%s-%d'%(self.parent.GetUID(), self.helpertype, id(self))

	def stoplooping(self):
		pass
	
	def cleanup_sched(self):
		self.parent.cleanup_sched(self)

	def add_arc(self, arc):
		self.parent.add_arc(arc, self)

class MMNode_pseudopar_body(MMNode_body):
	"""Helper for RealPix nodes with captions, common part"""

	def _is_realpix_with_captions(self):
		return 0
	
class MMNode_realpix_body(MMNode_pseudopar_body):
	"""Helper for RealPix nodes with captions, realpix part"""
	helpertype = "realpix"
	
class MMNode_caption_body(MMNode_pseudopar_body):
	"""Helper for RealPix nodes with captions, caption part"""
	helpertype = "caption"

	def GetAttrDict(self):
		raise 'Unimplemented'

	def GetRawAttr(self, name):
		if name == 'channel': name = 'captionchannel'
		return self.parent.GetRawAttr(name)

	def GetRawAttrDef(self, name, default):
		if name == 'channel': name = 'captionchannel'
		return self.parent.GetRawAttrDef(name, default)

	def GetAttr(self, name):
		if name == 'channel': name = 'captionchannel'
		return self.parent.GetAttr(name)

	def GetAttrDef(self, name, default):
		if name == 'channel': name = 'captionchannel'
		return self.parent.GetAttrDef(name, default)

	def GetInherAttr(self, name):
		if name == 'channel': name = 'captionchannel'
		return self.parent.GetInherAttr(name)

	def GetDefInherAttr(self, name):
		if name == 'channel': name = 'captionchannel'
		return self.parent.GetDefInherAttr(name)

	def GetInherAttrDef(self, name, default):
		if name == 'channel': name = 'captionchannel'
		return self.parent.GetInherAttrDef(name, default)
		
class MMNode:
	def __init__(self, type, context, uid):
		# ASSERT type in alltypes
		self.type = type
		self.context = context
		self.uid = uid
		self.attrdict = {}
		self.d_attrdict = {}
		self.values = []
		self.willplay = None
		self.shouldplay = None
		self.canplay = None
		self.parent = None
		self.children = []
##		self.summaries = {}
		self.setgensr()
##		self.isloopnode = 0
##		self.isinfiniteloopnode = 0
		self.looping_body_self = None
		self.realpix_body = None
		self.caption_body = None
		self.curloopcount = 0
		self.infoicon = ''
		self.errormessage = None
		self.force_switch_choice = 0
		self.srdict = {}
		self.events = {}	# events others are interested in
		self.sched_children = []
		self.scheduled_children = 0
		self.arcs = []
		self.reset()

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

	# methods that have to do with playback
	def reset(self):
		self.happenings = {}
		self.playing = MMStates.IDLE
		self.sctx = None

	def startplay(self, sctx):
		self.playing = MMStates.PLAYING
		self.sctx = sctx

	def stopplay(self):
		self.playing = MMStates.PLAYED

	def add_arc(self, arc, body = None):
		if body is None:
			body = self
		#print 'add_arc', `body`, `arc`
		body.sched_children.append(arc)
		if self.playing != MMStates.IDLE and arc.delay is not None:
			# if arc's event has already occurred, trigger it
			if arc.event is not None:
				key = 'event', arc.event
			elif arc.marker is not None:
				key = 'marker', arc.marker
			elif arc.dstnode.parent.type == 'seq' and \
			     self is not arc.dstnode.parent:
				# self is previous child in seq, so
				# event is end
				key = 'event', 'end'
			else:
				# self is first child of seq, or child
				# of par/excl, so event is begin
				key = 'event', 'begin'
			if self.happenings.has_key(key):
				time = self.sctx.parent.timefunc()
				t = self.happenings[key]
				if arc.delay <= time - t:
					self.sctx.trigger(arc, time - t)

	def event(self, time, event):
		self.happenings[('event', event)] = time

	def marker(self, time, marker):
		self.happenngs[('marker', marker)] = time

	def eventhappened(self, event):
		return self.happenings.has_key(('event', event))

	def markerhappened(self, marker):
		return self.happenings.has_key(('marker', marker))

	#
	# Private methods to build a tree
	#
	def _addchild(self, child):
		# ASSERT self.type in interiortypes
		child.parent = self
		self.children.append(child)

	def _addvalue(self, value):
		# ASSERT self.type = 'imm'
		self.values.append(value)

	def _setattr(self, name, value):
		# ASSERT not self.attrdict.has_key(name)
		self.attrdict[name] = value
		MMAttrdefs.flushcache(self)

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

	def GetParent(self):
		return self.parent

	def GetRoot(self):
		root = None
		x = self
		while x is not None:
			root = x
			x = x.parent
		return root

	def GetPath(self):
		path = []
		x = self
		while x is not None:
			path.append(x)
			x = x.parent
		path.reverse()
		return path

	def IsAncestorOf(self, x):
		while x is not None:
			if self is x: return 1
			x = x.parent
		return 0

	def CommonAncestor(self, x):
		p1 = self.GetPath()
		p2 = x.GetPath()
		n = min(len(p1), len(p2))
		i = 0
		while i < n and p1[i] == p2[i]: i = i+1
		if i == 0: return None
		else: return p1[i-1]

	def GetChildren(self):
		return self.children

	def GetChild(self, i):
		return self.children[i]

	def GetChildByName(self, name):
		if self.attrdict.has_key('name') and  self.attrdict['name']==name:
			return self
		for child in self.children:
			return child.GetChildByName(name)
		return None

	def GetValues(self):
		return self.values

	def GetValue(self, i):
		return self.values[i]

	def GetAttrDict(self):
		return self.attrdict

	def GetRawAttr(self, name):
		if self.attrdict.has_key(name):
			return self.attrdict[name]
		raise NoSuchAttrError, 'in GetRawAttr()'

	def GetRawAttrDef(self, name, default):
		return self.attrdict.get(name, default)

	def GetAttr(self, name):
		if self.attrdict.has_key(name):
			return self.attrdict[name]
		raise NoSuchAttrError, 'in GetAttr'

	def GetAttrDef(self, name, default):
		return self.attrdict.get(name, default)

	def GetInherAttr(self, name):
		x = self
		while x is not None:
			if x.attrdict and x.attrdict.has_key(name):
				return x.attrdict[name]
			x = x.parent
		raise NoSuchAttrError, 'in GetInherAttr()'

	def GetDefInherAttr(self, name):
		x = self.parent
		while x is not None:
			if x.attrdict and x.attrdict.has_key(name):
				return x.attrdict[name]
			x = x.parent
		raise NoSuchAttrError, 'in GetInherDefAttr()'

	def GetInherAttrDef(self, name, default):
##		try:
##			return self.GetInherAttr(name)
##		except NoSuchAttrError:
##			return default
		x = self
		while x is not None:
			if x.attrdict and x.attrdict.has_key(name):
				return x.attrdict[name]
			x = x.parent
		return default

	def GetRawAttrDefProduct(self, name, default):
		v = 1.0
		x = self
		while x is not None:
			v = v * x.GetRawAttrDef(name, default)
			x = x.parent
		return v

	def GetAttrDefProduct(self, name, default):
		v = 1.0
		x = self
		while x is not None:
			v = v * x.GetAttrDef(name, default)
			x = x.parent
		return v

##	def GetSummary(self, name):
##		if not self.summaries.has_key(name):
##			self.summaries[name] = self._summarize(name)
##		return self.summaries[name]

	def Dump(self):
		print '*** Dump of', self.type, 'node', self, '***'
		attrnames = self.attrdict.keys()
		attrnames.sort()
		for name in attrnames:
			print 'Attr', name + ':', `self.attrdict[name]`
##		summnames = self.summaries.keys()
##		if summnames:
##			summnames.sort()
##			print 'Has summaries for attrs:',
##			for name in summnames:
##				print name,
##			print
		if self.type == 'imm' or self.values:
			print 'Values:',
			for value in self.values: print value,
			print
		if self.type in interiortypes or self.children:
			print 'Children:',
			for child in self.children: print child.GetType(),
			print

	#
	# Presentation values management
	#
	def SetPresentationAttr(self, name, value):
		if self.attrdict.has_key(name):
			self.d_attrdict[name] = value
		elif self.attrdict.has_key('base_winoff'):
			# virtual node representing a region
			d = self.d_attrdict
			n = 'base_winoff'
			x, y, w, h = self.attrdict['base_winoff']
			if name == 'left':    d[n] = value, y, w, h
			elif name == 'top':	  d[n] = x, value, w, h
			elif name == 'width': d[n] = x, y, value, h
			elif name == 'height':d[n] = x, y, w, value
			elif name == 'right':
				x = value - w
				d[n] = x, y, w, h
			elif name == 'bottom':
				y = value - h
				d[n] = x, y, w, h
			elif name == 'position':
				x, y = value
				d[n] = x, y, w, h
			elif name == 'size':
				w, h = value
				d[n] = x, y, w, h
			
	#
	# Channel management
	#
	def GetChannel(self, attrname='channel'):
		cname = self.GetInherAttrDef(attrname, None)
		if not cname:		# cname == '' or cname is None
			return None
		return self.context.channeldict.get(cname)

	def GetChannelName(self):
		c = self.GetChannel()
		if c: return c.name
		else: return 'undefined'

	def GetChannelType(self):
		if self.attrdict.get('type')=='animate':
			return 'animate'
		c = self.GetChannel()
		if c and c.has_key('type'):
			return c['type']
		else:
			return ''

	def SetChannel(self, c):
		if c is None:
			self.DelAttr('channel')
		else:
			self.SetAttr('channel', c.name)

	#
	# GetAllChannels - Get a list of all channels used in a tree.
	# If there is overlap between parnode children the node in error
	# is returned.
	def GetAllChannels(self):
		if self.type in bagtypes:
			return [], None
		if self.type in leaftypes:
			list = [MMAttrdefs.getattr(self, 'channel')]
			captionchannel = MMAttrdefs.getattr(self, 'captionchannel')
			if captionchannel and captionchannel != 'undefined':
				list.append(captionchannel)
			# add any animate elements
			for node in self.children:
				if MMAttrdefs.getattr(node, 'type')=='animate':
					list.append(MMAttrdefs.getattr(node, 'channel'))
			return list, None
		errnode = None
		overlap = []
		list = []
		for ch in self.children:
			chlist, cherrnode = ch.GetAllChannels()
			if cherrnode:
				errnode = cherrnode
			list, choverlap = MergeLists(list, chlist)
			if choverlap:
				overlap = overlap + choverlap
		if overlap and self.type == 'par':
			errnode = (self, overlap)
		return list, errnode

	#
	# Make a "deep copy" of a subtree
	#
	def DeepCopy(self):
		uidremap = {}
		copy = self._deepcopy(uidremap, self.context)
		copy._fixuidrefs(uidremap)
		_copyoutgoinghyperlinks(self.context.hyperlinks, uidremap)
		return copy
	#
	# Copy a subtree (deeply) into a new context
	#
	def CopyIntoContext(self, context):
		uidremap = {}
		copy = self._deepcopy(uidremap, context)
		copy._fixuidrefs(uidremap)
		_copyinternalhyperlinks(self.context.hyperlinks,
					copy.context.hyperlinks, uidremap)
		return copy
	#
	# Private methods for DeepCopy
	#
	def _deepcopy(self, uidremap, context):
		nodeclass = context.nodeclass
		context.nodeclass = self.__class__
		copy = context.newnode(self.type)
		context.nodeclass = nodeclass
		uidremap[self.uid] = copy.uid
		copy.attrdict = _valuedeepcopy(self.attrdict)
		copy.values = _valuedeepcopy(self.values)
		children = self.children
		if self.type == 'ext' and self.GetChannelType() == 'RealPix':
			if not hasattr(self, 'slideshow'):
				#print 'MMNode._deepcopy: creating SlideShow'
				import realnode
				self.slideshow = realnode.SlideShow(self)
			self.slideshow.copy(copy)
			if copy.attrdict.has_key('file'):
				del copy.attrdict['file']
			# don't copy children since node collapsed
			children = []
		for child in children:
			copy._addchild(child._deepcopy(uidremap, context))
		return copy

	def _fixuidrefs(self, uidremap):
		# XXX Are there any other attributes that reference uids?
		self._fixsyncarcs(uidremap)
		for child in self.children:
			child._fixuidrefs(uidremap)

	def _fixsyncarcs(self, uidremap):
		# XXX Exception-wise, this function knows about the
		# semantics and syntax of an attribute...
		try:
			arcs = self.GetRawAttr('synctolist')
		except NoSuchAttrError:
			return
		if not arcs:
			self.DelAttr('synctolist')
			return
		newarcs = []
		for xuid, xside, delay, yside in arcs:
			if uidremap.has_key(xuid):
				xuid = uidremap[xuid]
			if yside == HD:
				if self.parent.type == 'seq' and xside == TL:
					prev = None
					for n in self.parent.children:
						if n is self:
							break
						prev = n
					if prev is not None and prev.uid == xuid:
						self.SetAttr('begin', delay)
						continue
				elif xside == HD and self.parent.uid == xuid:
					self.SetAttr('begin', delay)
					continue
			newarcs.append((xuid, xside, delay, yside))
		if newarcs <> arcs:
			if not newarcs:
				self.DelAttr('synctolist')
			else:
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
			self.setgensr()
			return
		if self.children <> []: # TEMP! or self.values <> []:
			raise CheckError, 'SetType() on non-empty node'
		self.type = type
		self.setgensr()

	def SetValues(self, values):
		if self.type <> 'imm':
			raise CheckError, 'SetValues() bad node type'
		self.values = values

	def SetAttr(self, name, value):
		self.attrdict[name] = value
		MMAttrdefs.flushcache(self)
##		self._updsummaries([name])

	def DelAttr(self, name):
		if not self.attrdict.has_key(name):
			return		# nothing to do
		del self.attrdict[name]
		MMAttrdefs.flushcache(self)
##		self._updsummaries([name])

	def Destroy(self):
		if self.parent is not None:
			raise CheckError, 'Destroy() non-root node'

		if hasattr(self, 'slideshow'):
			self.slideshow.destroy()
			del self.slideshow
		# delete hyperlinks referring to anchors here
		alist = MMAttrdefs.getattr(self, 'anchorlist')
		hlinks = self.context.hyperlinks
		for a in alist:
			aid = (self.uid, a[A_ID])
			for link in hlinks.findalllinks(aid, None):
				hlinks.dellink(link)

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
		self.sync_from = None
		self.sync_to = None
		self.wtd_children = None
##		self.summaries = None
		self.looping_body_self = None
		self.realpix_body = None
		self.caption_body = None
		self.srdict = None

	def Extract(self):
		if self.parent is None: raise CheckError, 'Extract() root node'
		parent = self.parent
		self.parent = None
		parent.children.remove(self)
		name = MMAttrdefs.getattr(self, 'name')
		if name and MMAttrdefs.getattr(parent, 'terminator') == name:
			parent.DelAttr('terminator')
##		parent._fixsummaries(self.summaries)

	def AddToTree(self, parent, i):
		if self.parent is not None:
			raise CheckError, 'AddToTree() non-root node'
		if self.context is not parent.context:
			# XXX Decide how to handle this later
			raise CheckError, 'AddToTree() requires same context'
		if i == -1:
			parent.children.append(self)
		else:
			parent.children.insert(i, self)
		self.parent = parent
##		parent._fixsummaries(self.summaries)
##		parent._rmsummaries(self.summaries.keys())

	#
	# Methods for mini-document management
	#
	# Check whether a node is the top of a mini-document
	def IsMiniDocument(self):
		if self.type in bagtypes:
			return 0
		parent = self.parent
		return parent is None or parent.type in bagtypes

	# Find the first mini-document in a tree
	def FirstMiniDocument(self):
		if self.IsMiniDocument():
			return self
		for child in self.children:
			mini = child.FirstMiniDocument()
			if mini is not None:
				return mini
		return None

	# Find the last mini-document in a tree
	def LastMiniDocument(self):
		if self.IsMiniDocument():
			return self
		res = None
		for child in self.children:
			mini = child.LastMiniDocument()
			if mini is not None:
				res = mini
		return res

	# Find the next mini-document in a tree after the given one
	# Return None if this is the last one
	def NextMiniDocument(self):
		node = self
		while 1:
			parent = node.parent
			if parent is None:
				break
			siblings = parent.children
			index = siblings.index(node) # Cannot fail
			while index+1 < len(siblings):
				index = index+1
				mini = siblings[index].FirstMiniDocument()
				if mini is not None:
					return mini
			node = parent
		return None

	# Find the previous mini-document in a tree after the given one
	# Return None if this is the first one
	def PrevMiniDocument(self):
		node = self
		while 1:
			parent = node.parent
			if parent is None:
				break
			siblings = parent.children
			index = siblings.index(node) # Cannot fail
			while index > 0:
				index = index-1
				mini = siblings[index].LastMiniDocument()
				if mini is not None:
					return mini
			node = parent
		return None

	# Find the root of a node's mini-document
	def FindMiniDocument(self):
		node = self
		parent = node.parent
		while parent is not None and parent.type not in bagtypes:
			node = parent
			parent = node.parent
		return node

	# Find the nearest bag given a minidocument
	def FindMiniBag(self):
		bag = self.parent
		if bag is not None and bag.type not in bagtypes:
			raise CheckError, 'FindMiniBag: minidoc not rooted in a choice node!'
		return bag

##	#
##	# Private methods for summary management
##	#
##	def _rmsummaries(self, keep):
##		x = self
##		while x is not None:
##			changed = 0
##			for key in x.summaries.keys():
##				if key not in keep:
##					del x.summaries[key]
##					changed = 1
##			if not changed:
##				break
##			x = x.parent

##	def _fixsummaries(self, summaries):
##		tofix = summaries.keys()
##		for key in tofix[:]:
##			if summaries[key] == []:
##				tofix.remove(key)
##		self._updsummaries(tofix)

##	def _updsummaries(self, tofix):
##		x = self
##		while x is not None and tofix:
##			for key in tofix[:]:
##				if not x.summaries.has_key(key):
##					tofix.remove(key)
##				else:
##					s = x._summarize(key)
##					if s == x.summaries[key]:
##						tofix.remove(key)
##					else:
##						x.summaries[key] = s
##			x = x.parent

##	def _summarize(self, name):
##		try:
##			summary = [self.GetAttr(name)]
##		except NoSuchAttrError:
##			summary = []
##		for child in self.children:
##			list = child.GetSummary(name)
##			for item in list:
##				if item not in summary:
##					summary.append(item)
##		summary.sort()
##		return summary

	#
	# Set the correct method for generating scheduler records.
	def setgensr(self):
		type = self.type
		if type in ('imm', 'ext'):
			self.gensr = self.gensr_leaf
		elif type == 'bag':
			self.gensr = self.gensr_bag
		elif type == 'alt':
			self.gensr = self.gensr_alt
		elif type in ('seq', 'par', 'excl'):
			self.gensr = self.gensr_interior
		else:
			raise CheckError, 'MMNode: unknown type %s' % self.type		 
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
	# Alternatively, call GenAllSR(), and then call EndPruneTree() to clear
	# the garbage.
	def PruneTree(self, seeknode):
		if seeknode is None or seeknode is self:
			self._FastPruneTree()
			return
		if seeknode is not None and not self.IsAncestorOf(seeknode):
			raise CheckError, 'Seeknode not in tree!'
		self.reset()
		self.events = {}
		self.sync_from = ([],[])
		self.sync_to = ([],[])
		self.realpix_body = None
		self.caption_body = None
		self.force_switch_choice = 0
		self.wtd_children = []
		if self.type in playabletypes:
			return
		if self.type == 'seq':
			for c in self.children:
				if seeknode is not None and \
				   c.IsAncestorOf(seeknode):
					self.wtd_children.append(c)
					c.PruneTree(seeknode)
					seeknode = None
				elif seeknode is None:
					self.wtd_children.append(c)
					c._FastPruneTree()
		elif self.type == 'par':
			self.wtd_children = self.children[:]
			for c in self.children:
				if c.IsAncestorOf(seeknode):
					c.PruneTree(seeknode)
				else:
					c._FastPruneTree()
		elif self.type == 'alt':
			for c in self.children:
				c.force_switch_choice = 0
				if c.IsAncestorOf(seeknode):
					self.wtd_children.append(c)
					c.PruneTree(seeknode)
					c.force_switch_choice = 1
		elif self.type == 'excl':
			for c in self.children:
				if c.IsAncestorOf(seeknode):
					self.wtd_children.append(c)
					c.PruneTree(seeknode)
		else:
			raise CheckError, 'Cannot PruneTree() on nodes of this type %s' % self.type
	#
	# PruneTree - The fast lane. Just copy children->wtd_children and
	# create sync_from and sync_to.
	def _FastPruneTree(self):
		self.reset()
		self.sync_from = ([],[])
		self.sync_to = ([],[])
		self.events = {}
		self.realpix_body = None
		self.caption_body = None
		self.force_switch_choice = 0
		self.wtd_children = self.children[:]
		for c in self.children:
			c._FastPruneTree()


	def EndPruneTree(self):
		pass
##		del self.sync_from
##		del self.sync_to
##		if self.type in ('seq', 'par'):
##			for c in self.wtd_children:
##				c.EndPruneTree()
##			del self.wtd_children

	def __find_refnode(self, arc):
		return arc.refnode()

	#
	# Generate schedrecords for leaf nodes.
	# The looping parmeter is only for pseudo-par-nodes implementing RealPix with
	# captions.
	#
	def gensr_leaf(self, looping=0, overrideself=None):
		if overrideself:
			# overrideself is passed for the interior
			self = overrideself
		elif self._is_realpix_with_captions():
			self.realpix_body = MMNode_realpix_body(self)
			self.caption_body = MMNode_caption_body(self)
			return self.gensr_interior(looping)
			
		# Clean up realpix stuff: the node may have been a realpix node in the past
		self.realpix_body = None
		self.caption_body = None
		in0, in1 = self.sync_from
		out0, out1 = self.sync_to
		if settings.noprearm:
			srlist = [([(SCHED, self)] + in0, [(PLAY, self)] + out0)]
		else:
			srlist = [([(SCHED, self), (ARM_DONE, self)] + in0,
				   [(PLAY, self)] + out0)]
		fill = self.attrdict.get('fill')
		if fill is None:
			if not self.attrdict.has_key('duration') and \
			   not self.attrdict.has_key('endlist') and \
			   not self.attrdict.has_key('repeatCount') and \
			   not self.attrdict.has_key('repeatDur'):
				fill = 'freeze'
			else:
				fill = 'remove'
		sched_done = [(SCHED_DONE,self)] + out1
		sched_stop = []
		if fill == 'remove':
			sched_done.append((PLAY_STOP, self))
		else:
			# XXX should be refined
			sched_stop.append((PLAY_STOP, self))
		srlist.append(
			([(PLAY_DONE, self)] + in1,
			 [(SCHED_STOPPING,self)]))
		srlist.append(([(SCHED_STOPPING,self)], sched_done))
		srlist.append(([(SCHED_STOP, self)], sched_stop))

		# XXX: ignoring animate elements timing for now, 
		# just kick animate childs in a parallel envelope	
		for child in self.children:
			if MMAttrdefs.getattr(child, 'type')!='animate':
				continue
			srlist.append(( [(SCHED, self),], 
				[(SCHED,child),(PLAY,self)]  ))

			srlist.append((  [(SCHED_STOPPING,self),], 
				[(SCHED_DONE,self), (PLAY_STOP, self), ]  ))

			srlist.append((  [(SCHED,child),], 
				[(PLAY,child)]  ))

			if settings.noprearm:
				srlist.append((  [(SCHED,child),], 
					[(PLAY,child)]  ))
			else:
				srlist.append((  [(SCHED,child),(ARM_DONE, child),], 
					[(PLAY,child)]  ))

			srlist.append((  [(SCHED_STOP,self),], 
				[(PLAY_STOP,self),(PLAY_STOP,child)]  ))

			srlist.append((  [(SCHED_DONE,child),], 
				[]  ))

			srlist.append((  [(PLAY_DONE,child),], 
				[(PLAY_STOP,child),]  ))

		srdict = {}
		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: self.__dump_srdict('gensr_leaf', srdict)
		return srdict

	def gensr_empty(self):
		# generate SR list for empty interior node, taking
		# sync arcs to the end and duration into account
		in0, in1 = self.sync_from
		out0, out1 = self.sync_to
		duration = MMAttrdefs.getattr(self, 'duration')
		actions = out0[:]
		final = [(SCHED_STOPPING, self)]
		srlist = [([(SCHED, self)] + in0, actions),
			  ([(SCHED_STOP, self)], []),
			  ([(SCHED_STOPPING, self)], [(SCHED_DONE, self)] + out1),
			  ([(TERMINATE, self)], [])]
		endlist = MMAttrdefs.getattr(self, 'endlist')
		for arc in endlist:
			refnode = self.__find_refnode(arc)
			refnode.add_arc(arc)
		if in1:
			# wait for sync arcs
			srlist.append((in1, final))
		elif duration > 0:
			# wait for duration
			actions.append((SYNC, (duration, self)))
			srlist.append(([(SYNC_DONE, self)], []))
		elif duration < 0 or endlist:
			# indefinite duration or end sync arcs
			# wait for something that isn't going to happen
			# i.e., wait until terminated
			srlist.append(([(SYNC_DONE, self)], final))
		else:
			# don't wait
			actions[len(actions):] = final
		srdict = {}
		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: self.__dump_srdict('gensr_empty', srdict)
		return srdict

	# XXXX temporary hack to do at least something on ALT nodes
	def gensr_alt(self):
		if not self.wtd_children:
			return self.gensr_empty()
		selected_child = None
		selected_child = self.ChosenSwitchChild(self.wtd_children)
		if selected_child:
			self.wtd_children = [selected_child]
		else:
			self.wtd_children = []
			return self.gensr_empty()
		in0, in1 = self.sync_from
		out0, out1 = self.sync_to
		srlist = []
		duration = MMAttrdefs.getattr(self, 'duration')
		endlist = MMAttrdefs.getattr(self, 'endlist')
		for arc in endlist:
			refnode = self.__find_refnode(arc)
			refnode.add_arc(arc)
		if duration > 0:
			# if duration set, we must trigger a timeout
			# and we must catch the timeout to terminate
			# the node
			out0 = out0 + [(SYNC, (duration, self))]
			srlist.append(([(SYNC_DONE, self)],
				       [(TERMINATE, self)]))
		prereqs = [(SCHED, self)] + in0
		actions = out0[:]
		tlist = []
		actions.append((SCHED, selected_child))
		srlist.append((prereqs, actions))
		prereqs = [(SCHED_DONE, selected_child)]
		actions = [(SCHED_STOP, selected_child)]
		tlist.append((TERMINATE, selected_child))
		last_actions = actions
		actions = [(SCHED_DONE, self)]
		if duration < 0 or endlist:
			# indefinite duration or end sync arcs
			# wait for something that isn't going to happen
			# i.e., wait until terminated
			prereqs.append((SYNC_DONE, self))
		srlist.append((prereqs, [(SCHED_STOPPING, self)]))
		srlist.append(([(SCHED_STOPPING, self)], actions))
		srlist.append(([(SCHED_STOP, self)],
			       last_actions + out1))
##		tlist.append((SCHED_STOPPING, self))
		srlist.append(([(TERMINATE, self)], tlist))
		for ev in in1:
			srlist.append(([ev], [(TERMINATE, self)]))
		srdict = selected_child.gensr()
		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: self.__dump_srdict('gensr_alt', srdict)
		return srdict

	def gensr_bag(self):
		if not self.wtd_children:
			return self.gensr_empty()
		in0, in1 = self.sync_from
		out0, out1 = self.sync_to
		duration = MMAttrdefs.getattr(self, 'duration')
		endlist = MMAttrdefs.getattr(self, 'endlist')
		for arc in endlist:
			refnode = self.__find_refnode(arc)
			refnode.add_arc(arc)
		srlist = [([(SCHED_STOPPING, self)],[(SCHED_DONE,self)] + out1),
			  ([(SCHED_STOP, self)],   [(BAG_STOP, self)]),
			  ([(TERMINATE, self)],    [])]
		prereqs = [(BAG_DONE, self)]
		if duration > 0:
			# if duration set, we must trigger a timeout
			# and we must catch the timeout to terminate
			# the node
			out0 = out0 + [(SYNC, (duration, self))]
			srlist.append(([(SYNC_DONE, self)],
				       [(TERMINATE, self)]))
		elif duration < 0 or endlist:
			# indefinite duration or end sync arcs
			# wait for something that isn't going to happen
			# i.e., wait until terminated
			prereqs.append((SYNC_DONE, self))
		srlist.append(([(SCHED, self)] + in0,
			       [(BAG_START, self)] + out0))
		srlist.append((prereqs, [(SCHED_STOPPING, self)]))
		for ev in in1:
			srlist.append(([ev], [(TERMINATE, self)]))
		srdict = {}
		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: self.__dump_srdict('gensr_bag', srdict)
		return srdict

	#
	# There's a lot of common code for par and seq nodes.
	# We attempt to factor that out with a few helper routines.
	# All the helper routines accept at least two arguments
	# - the actions to be taken when the node is "starting"
	# - the actions to be taken when the node is "finished"
	# (or, colloquially, the outgoing head-syncarcs and the SCHED_DONE
	# event) and return 4 items:
	# - actions to be taken upon node starting (SCHED)
	# - actions to be taken upon SCHED_STOP
	# - actions to be taken upon TERMINATE or incoming tail-syncarcs
	# - a list of all (event, action) tuples to be generated
	# 
	def gensr_interior(self, looping=0):
		#
		# If the node is empty there is very little to do.
		#
		is_realpix = 0
		if self.type == 'par' or self.type == 'excl':
			gensr_body = self.gensr_body_parexcl
		elif self._is_realpix_with_captions():
			gensr_body = self.gensr_body_realpix
			is_realpix = 1
		else:
			gensr_body = self.gensr_body_parexcl

		#
		# Select the  generator for the outer code: either non-looping
		# or, for looping nodes, the first or subsequent times through
		# the loop.
		#
		loopcount = self.GetAttrDef('loop', None)
		loopdur = MMAttrdefs.getattr(self, 'repeatdur')
		if loopdur != 0 and loopcount is None:
			# no loop attr and specified repeatdur attr, so loop indefinitely
			# until time's up
			loopcount = 0
		if loopcount == 1 or (loopcount is None and loopdur == 0):
			gensr_envelope = self.gensr_envelope_nonloop
			loopcount = 1
		elif looping == 0:
			# First time loop generation
			gensr_envelope = self.gensr_envelope_firstloop
		else:
			gensr_envelope = self.gensr_envelope_laterloop

		#
		# If the node has a duration we add a syncarc from head
		# to tail. This will terminate the node when needed.
		#
		in0, in1 = self.sync_from
		out0, out1 = self.sync_to
		
		endlist = MMAttrdefs.getattr(self, 'endlist')
		for arc in endlist:
			refnode = self.__find_refnode(arc)
			refnode.add_arc(arc)
		if loopdur != 0:
			if loopdur < 0:
				loopdur = None
			arc = MMSyncArc(self, 'end', srcnode=self, event='begin', delay=loopdur)
			self.arcs.append((self, arc))
			self.add_arc(arc)

##		if is_realpix:
##			duration = 0
##		else:
##			duration = MMAttrdefs.getattr(self, 'duration')
##		if duration > 0:
##			# Implement duration by adding a syncarc from
##			# head to tail.
##			out0 = out0[:] + [(SYNC, (duration, self))]
##			in1 = in1[:] + [(SYNC_DONE, self)]
##		elif duration < 0 or endlist:
##			# Infinite duration, simulate with SYNC_DONE event
##			# for which there is no SYNC action
##			in1 = in1[:] + [(SYNC_DONE, self)]

		fill = self.attrdict.get('fill', 'remove')

		#
		# We are started when we get our SCHED and all our
		# incoming head-syncarcs.
		#
		sched_events = [(SCHED, self)] + in0
		#
		# Once we are started we should fire our outgoing head
		# syncarcs
		#
		sched_actions_arg = out0[:]
		#
		# When we're done we should signal SCHED_DONE to our parent
		# and fire our outgoing tail syncarcs.
		#
		scheddone_actions_arg = [(SCHED_STOPPING, self)]
		#
		# And when the parent is really done with us we get a
		# SCHED_STOP
		#
		schedstop_events = [(SCHED_STOP, self)]

		#
		# And we also tell generating routines about all terminating
		# events.
		terminate_events_arg = in1

		sched_actions, schedstop_actions,  \
			       srdict = gensr_envelope(gensr_body, loopcount,
						       sched_actions_arg,
						       scheddone_actions_arg,
						       terminate_events_arg)
		if not looping:
			#
			# Tie our start-events to the envelope/body
			# start-actions
			#
			action = [len(sched_events), [(SCHED_START, self)]]
			for event in sched_events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict
			self.srdict[(SCHED_START, self)] = [1, sched_actions]
			srdict[(SCHED_START, self)] = self.srdict

			#
			# Tie the envelope/body done events to our done actions
			#
			sched_done = [(SCHED_DONE, self)]+out1
			if fill == 'remove':
				sched_done = sched_done + schedstop_actions
				schedstop_actions = []
			action = [len(schedstop_events), schedstop_actions]
			for event in schedstop_events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
			ev = (SCHED_STOPPING, self)
			self.srdict[ev] = [1, sched_done]
			srdict[ev] = self.srdict
			#
			# And, for our incoming tail syncarcs and a
			# TERMINATE for ourselves we abort everything.
			#
##		if self._is_realpix_with_captions():	#DBG
##			print 'NODE', self # DBG
##			for i in srlist: print i #DBG
##			print 'NODE END' #DBG

		if debuggensr: self.__dump_srdict('gensr_interior', srdict)
		return srdict

	def gensr_envelope_nonloop(self, gensr_body, loopcount, sched_actions,
				   scheddone_actions, terminate_events):
		if loopcount != 1:
			raise 'Looping nonlooping node!'
		self.curloopcount = 0

		sched_actions, schedstop_actions, srdict = \
			       gensr_body(sched_actions, scheddone_actions,
					  terminate_events)
##		for event in in1+[(TERMINATE, self)]:
##			srdict[event] = self.srdict
##			self.srdict[event] = [1, terminate_actions]
		if debuggensr: 
			self.__dump_srdict('gensr_envelope_nonloop', srdict)
		return sched_actions, schedstop_actions, srdict

	def gensr_envelope_firstloop(self, gensr_body, loopcount,
				     sched_actions, scheddone_actions,
				     terminate_events):
		srlist = []
		terminate_actions = []
		#
		# Remember the loopcount.
		#
		if loopcount == 0:
			self.curloopcount = -1
		else:
			self.curloopcount = loopcount

		#
		# We create a helper node, to differentiate between terminates
		# from the inside and the outside (needed for par nodes with
		# endsync, which can generate terminates internally that should
		# not stop the whole loop).
		#
		self.looping_body_self = MMNode_body(self)

		#
		# When we start we do our syncarc stuff, and also LOOPSTART
		# XXXX Note this is incorrect: we should check which of the
		# syncarcs refer to children
		#
		# XXXX We should also do our SCHED_DONE here if we are
		# looping indefinitely.
		#
		sched_actions.append( (LOOPSTART, self) )
		body_sched_actions = []
		body_scheddone_actions = [(SCHED_STOPPING, self.looping_body_self)]
		body_terminate_events = []

		body_sched_actions, body_schedstop_actions, srdict = \
				    gensr_body(body_sched_actions,
					       body_scheddone_actions,
					       body_terminate_events,
					       self.looping_body_self)

		# When the loop has started we start the body
		srlist.append( ([(LOOPSTART_DONE, self)], body_sched_actions) )

		# Terminating the body doesn't terminate the loop,
		# but the other way around it does
##		srlist.append( ([(TERMINATE, self.looping_body_self)],
##				body_terminate_actions) )
		terminate_actions = [(TERMINATE, self.looping_body_self),
				     (SCHED_STOPPING, self)]

		# When the body is done we stop it, and we end/restart the loop
		srlist.append( ([(SCHED_STOPPING, self.looping_body_self)],
				[(SCHED_DONE, self.looping_body_self)]) )
		srlist.append( ([(SCHED_DONE, self.looping_body_self)],
				[(LOOPEND, self),
				 (SCHED_STOP, self.looping_body_self)]) )
		srlist.append( ([(SCHED_STOP, self.looping_body_self)],
				body_schedstop_actions) )

		#
		# Three cases for signalling the parent we're done:
		# 1. Incoming tail sync arcs or an explicit duration:
		#	When these fire we signal SCHED_DONE and TERMINATE
		#	ourselves. No special action on end-of-loop
		# 2. We loop indefinite:
		#	Immedeately tell our parents we are done. No special
		#	actions on end-of-loop.
		# 3. Other cases (fixed loopcount and no duration/tailsync):
		#	End-of-loop signals SCHED_DONE.
		# In all cases a SCHED_STOP is translated to a terminate of
		# ourselves.
		#
		if terminate_events:
			srlist.append((terminate_events, scheddone_actions +
				       [(TERMINATE, self)]))
			terminate_actions.append( (TERMINATE, self) )
			srlist.append( ([(LOOPEND_DONE, self)], []) )
		elif self.curloopcount < 0:
			sched_actions = sched_actions + scheddone_actions
			#terminate_actions.append( (TERMINATE, self) )
			srlist.append( ([(LOOPEND_DONE, self)], []) )
		else:
			srlist.append( ([(LOOPEND_DONE, self)],
					scheddone_actions) )
##		for ev in terminate_events + [(TERMINATE, self)]:
##			srlist.append(( [ev], terminate_actions ))
		srlist.append(([(TERMINATE, self)], terminate_actions))

		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: 
			self.__dump_srdict('gensr_envelope_firstloop', srdict)
		return sched_actions, terminate_actions, srdict


	def gensr_envelope_laterloop(self, gensr_body, loopcount,
				     sched_actions, scheddone_actions,
				     terminate_events):
		srlist = []

		body_sched_actions = []
		body_scheddone_actions = [(SCHED_STOPPING, self.looping_body_self)]
		body_terminate_events = []

		body_sched_actions, body_schedstop_actions, srdict = \
				    gensr_body(body_sched_actions,
					       body_scheddone_actions,
					       body_terminate_events,
					       self.looping_body_self)

		# When the loop has started we start the body
		srlist.append( ([(LOOPSTART_DONE, self)], body_sched_actions) )

		# Terminating the body doesn't terminate the loop,
		# but the other way around it does
##		srlist.append( ([(TERMINATE, self.looping_body_self)],
##				body_terminate_actions) )

		# When the body is done we stop it, and we end/restart the loop
		srlist.append( ([(SCHED_STOPPING, self.looping_body_self)],
				[(SCHED_DONE, self.looping_body_self)]) )
		srlist.append( ([(SCHED_DONE, self.looping_body_self)],
				[(LOOPEND, self),
				 (SCHED_STOP, self.looping_body_self)]) )
		srlist.append( ([(SCHED_STOP, self.looping_body_self)],
				body_schedstop_actions) )

		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: 
			self.__dump_srdict('gensr_envelope_laterloop', srdict)
		return [], [], srdict

	def cleanup(self):
		#print 'cleanup', `self`
		self.sched_children = []
		for child in self.children:
			child.cleanup()

	def cleanup_sched(self, body = None):
		if self.type != 'par' and self.type != 'excl':
			return
		if body is None:
			if self.looping_body_self:
				return
			body = self
		for node, arc in body.arcs:
			#print 'deleting', `arc`
			node.sched_children.remove(arc)
		body.arcs = []
		for child in self.wtd_children:
			beginlist = MMAttrdefs.getattr(child, 'beginlist')
			if beginlist:
				for arc in beginlist:
					#print 'deleting arc',`arc`
					refnode = child.__find_refnode(arc)
					refnode.sched_children.remove(arc)
					if arc.qid is not None:
						self.cancel(arc.qid)
						arc.qid = None
			for arc in MMAttrdefs.getattr(child, 'endlist'):
				#print 'deleting arc',`arc`
				refnode = child.__find_refnode(arc)
				refnode.sched_children.remove(arc)
				if arc.qid is not None:
					self.cancel(arc.qid)
					arc.qid = None

	def gensr_body_parexcl(self, sched_actions, scheddone_actions,
			       terminate_events, self_body=None):
		srdict = {}
		srlist = []
		schedstop_actions = []
		terminate_actions = []
		terminating_children = []
		scheddone_events = []
		if self_body is None:
			self_body = self

		termtype = MMAttrdefs.getattr(self, 'terminator')
		if termtype == 'FIRST':
			terminating_children = self.wtd_children[:]
		elif termtype == 'LAST':
			terminating_children = []
		else:
			terminating_children = []
			for child in self.wtd_children:
				if MMAttrdefs.getattr(child, 'name') \
				   == termtype:
					terminating_children.append(child)

		srcnode = self_body
		event = 'begin'
		if self.type == 'par' or self.type == 'seq':
			termtype = MMAttrdefs.getattr(self, 'terminator')
			defbegin = 0.0
		else:
			termtype = 'ALL'
			defbegin = None

		duration = MMAttrdefs.getattr(self, 'duration')
		duration = self.GetAttrDef('duration', None)
		if duration is not None:
			if duration < 0:
				delay = None
			else:
				delay = duration
			arc = MMSyncArc(self_body, 'end', srcnode=self_body, event='begin', delay=delay)
			self_body.arcs.append((self_body, arc))
			self_body.add_arc(arc)

		for child in self.wtd_children:
			chname = MMAttrdefs.getattr(child, 'name')
			beginlist = MMAttrdefs.getattr(child, 'beginlist')
			if not beginlist:
				arc = MMSyncArc(child, 'begin', srcnode = srcnode, event = event, delay = defbegin)
				self_body.arcs.append((srcnode, arc))
				srcnode.add_arc(arc)
				schedule = defbegin is not None
			else:
				schedule = 0
				for arc in beginlist:
					refnode = child.__find_refnode(arc)
					refnode.add_arc(arc)
					if arc.event == 'begin' and \
					   refnode is self_body and \
					   arc.marker is None and \
					   arc.delay is not None:
						schedule = 1
			if termtype in ('FIRST', chname):
				terminating_children.append(child)
				srlist.append(([(SCHED_DONE, child)],
					       [(TERMINATE, self_body)]))
			elif schedule or termtype == 'ALL':
				scheddone_events.append((SCHED_DONE, child))
			for arc in MMAttrdefs.getattr(child, 'endlist'):
				refnode = child.__find_refnode(arc)
				refnode.add_arc(arc)
			if self.type == 'seq':
				srcnode = child
				event = 'end'
			terminate_actions.append((TERMINATE, child))

		#
		# Trickery to handle dur and end correctly:
		#
		if duration is not None:
			scheddone_events.append((SYNC_DONE, self_body))
			terminate_actions.append((SYNC_DONE, self_body))
		if scheddone_events and \
		   (terminate_events or terminating_children):
			# Terminate_events means we have a specified
			# duration. We obey this, and ignore scheddone
			# events from our children.
			# Terminating_children means we have a
			# terminator attribute that points to a child.
			# We obey this also and ignore scheddone
			# events from our other children.
			srlist.append( (scheddone_events, []) )
			scheddone_events = []

		if scheddone_events:
			srlist.append((scheddone_events,
				       scheddone_actions))
		terminate_actions = terminate_actions + scheddone_actions

		for ev in terminate_events+[(TERMINATE, self_body)]:
			srlist.append(( [ev], terminate_actions ))
		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: 
			self.__dump_srdict('gensr_body_parexcl', srdict)
		return sched_actions, schedstop_actions, srdict

	def gensr_body_realpix(self, sched_actions, scheddone_actions,
			       terminate_events, self_body=None):
		srdict = {}
		srlist = []
		schedstop_actions = []
		terminate_actions = []
		scheddone_events = []
		if self_body is None:
			self_body = self

		for child in (self.realpix_body, self.caption_body):
##			print 'gensr for', child
##			print 'func is', child._is_realpix_with_captions(), child._is_realpix_with_captions

			srdict.update(child.gensr(overrideself=child))

			sched_actions.append( (SCHED, child) )
			schedstop_actions.append( (SCHED_STOP, child) )
			terminate_actions.append( (TERMINATE, child) )

			scheddone_events.append( (SCHED_DONE, child) )

		#
		# Trickery to handle dur and end correctly:
		# XXX isn't the dur passed on in the files? Check.
		if terminate_events:
			# Terminate_events means we have a specified
			# duration. We obey this, and ignore scheddone
			# events from our children.
			# Terminating_children means we have a
			# terminator attribute that points to a child.
			# We obey this also and ignore scheddone
			# events from our other children.
			srlist.append( (scheddone_events, []) )
			scheddone_events = []

		if scheddone_events:
			srlist.append((scheddone_events,
				       scheddone_actions))
		else:
			terminate_actions = terminate_actions + \
					    scheddone_actions

		for ev in terminate_events+[(TERMINATE, self_body)]:
			srlist.append(( [ev], terminate_actions ))
		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: 
			self.__dump_srdict('gensr_body_realpix', srdict)
		return sched_actions, schedstop_actions, srdict
			
	def gensr_child(self, child, runchild = 1):
		if runchild:
			srdict = child.gensr()
		else:
			srdict = {}
		body = self.looping_body_self or self
		termtype = MMAttrdefs.getattr(self, 'terminator')
		if not self.srdict.has_key((SCHED_DONE, child)):
			if termtype in ('LAST', 'ALL'):
				# add child to list of children to wait for
				ev = SCHED_STOPPING, body
				for key, val in self.srdict.items():
					if not val:
						# I think this can't happen
						continue
					if key[0] == TERMINATE:
						# we're not interested in this event
						continue
					num, srlist = val
					for sr in srlist:
						if sr == ev:
							val[0] = num + 1
							self.srdict[(SCHED_DONE, child)] = val
							srdict[(SCHED_DONE, child)] = self.srdict
							break
					else:
						# if not yet found, continue searching
						continue
					# if found, stop searching
					break
				else:
					#print 'gensr_child: no SCHED_DONE\'s found'
					srlist = [(SCHED_STOPPING, body)]
					val = [1, srlist]
					self.srdict[(SCHED_DONE, child)] = val
					srdict[(SCHED_DONE, child)] = self.srdict
			else:
				# ignore child's SCHED_DONE
				self.srdict[(SCHED_DONE, child)] = [1, []]
				srdict[(SCHED_DONE, child)] = self.srdict
		if runchild:
			# add child to list of children to terminate
			numsrlist = self.srdict[(TERMINATE, body)]
			srlist = numsrlist[1]
			srlist.insert(len(srlist)-1, (TERMINATE, child))
			numsrlist = self.srdict[(SCHED_STOP, body)]
			srlist = numsrlist[1]
			srlist.append((SCHED_STOP, child))
		if debuggensr: 
			self.__dump_srdict('gensr_child', srdict)
		return srdict

	def _is_realpix_with_captions(self):
		if self.type == 'ext' and self.GetChannelType() == 'RealPix':
			# It is a realpix node. Check whether it has captions
			captionchannel = MMAttrdefs.getattr(self, 'captionchannel')
			if captionchannel and captionchannel != 'undefined':
				return 1
		return 0

	def GenAllSR(self, seeknode):
		self.cleanup()
##		self.SetPlayability()
		if not seeknode:
			seeknode = self
		#
		# First generate arcs
		#
		self.PruneTree(seeknode)
		arcs = self.GetArcList()
		arcs = self.FilterArcList(arcs)
		for i in range(len(arcs)):
			n1, s1, n2, s2, delay = arcs[i]
			n1.SetArcSrc(s1, delay, i)
			n2.SetArcDst(s2, i)
				
		#
		# Now run through the tree
		#
		srdict = self.gensr()
		event, actions = (SCHED_DONE, self), [(SCHED_STOP, self)]
		self.srdict[event] = [1, actions]
		srdict[event] = self.srdict # or just self?
		if debuggensr: self.__dump_srdict('GenAllSR', srdict)
		return srdict

	
	# srdict is a map:  event -> [num, action_list]
	# num: is the number of events associated with the same action_list
	#	==the number of the events that must occure before action_list gets exec
	#	==the number of events in srdict that are mapped to the same list
	# event and action are pairs: (event_or_action_id, node)  --see SR module for ids
	# Explicitly srdict has the form:
	#	srdict: (evid,node) -> [num, [(acid,node),(acid,node),...]]
	def __dump_srdict(self, msg, srd):
		actions = {}
		for ev, srdict in srd.items():
			ac = srdict[ev]
			if ac is None:
				continue
			if not actions.has_key(id(ac)):
				actions[id(ac)] = [ac]
			actions[id(ac)].append(ev)
		print '------------------------------',msg,self
		for l in actions.values():
			num, ac = l[0]
			events = l[1:]
			if num != len(events):
				print 'discrepancy:',
			print evlist2string(events),
			print '-->',
			print evlist2string(ac)
		print '----------------------------------'

	def __dump_srlist(self, msg, srlist):
		print '----------------------------------',msg,self
		for events, actions in srlist:
			print '\t',evlist2string(events), '-->', evlist2string(actions)
		print '----------------------------------'

	#
	# Re-generate SR actions/events for a loop. Called for the
	# second and subsequent times through the loop.
	#
	def GenLoopSR(self):
		# XXXX Try by Jack:
		self.PruneTree(None)
		return self.gensr(looping=1)
	#
	# Check whether the current loop has reached completion.
	#
	def moreloops(self, decrement=0):
		rv = self.curloopcount
		if decrement and self.curloopcount > 0:
			self.curloopcount = self.curloopcount - 1
		return (rv != 0)

	def stoplooping(self):
		self.curloopcount = 0

	# eidtmanager stuff
	def transaction(self):
		return 1

	def rollback(self):
		pass

	def commit(self):
##		print 'MMNode: deleting cached values'
		self.editmgr.unregister(self)
		del self.editmgr

	def kill(self):
		pass

	#
	# Methods to handle sync arcs.
	#
	# The GetArcList method recursively gets a list of sync arcs
	# The sync arcs are returned as (n1, s1, n2, s2, delay) tuples.
	# Unused sync arcs are not filtered out of the list yet.
	#
	def GetArcList(self):
##		if not self.GetSummary('synctolist'):
##			return []
		synctolist = []
		delay = 0
##		if self.parent is None or self.parent.type == 'seq':
##			for arc in MMAttrdefs.getattr(self, 'beginlist'):
##				if arc.srcnode is None and arc.event is None and arc.marker is None:
##					delay = arc.delay
##					break
		if delay > 0:
			if self.parent.type == 'seq':
				xnode = self.parent
				xside = HD
				for n in self.parent.children:
					if n is self:
						break
					xnode = n
					xside = TL
			else:
				xnode = self.parent
				xside = HD
			synctolist.append((xnode, xside, self, HD, delay))
		arcs = self.GetAttrDef('synctolist', [])
		for arc in arcs:
			n1uid, s1, delay, s2 = arc
			try:
				n1 = self.MapUID(n1uid)
			except NoSuchUIDError:
				print 'GetArcList: skipping syncarc with deleted source'
				continue
			synctolist.append((n1, s1, self, s2, delay))
		if self.GetType() in ('seq', 'par', 'excl'):
			for c in self.wtd_children:
				synctolist = synctolist + c.GetArcList()
		elif self.GetType() == 'alt':
			for c in self.wtd_children:
				if c.WillPlay():
					synctolist = synctolist + \
						     c.GetArcList()
					break
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
		while x is not None:
			if self is x: return 1
			xnew = x.parent
			if xnew is None:
				return 0
			try:
				if not x in xnew.wtd_children:
					return 0
			except AttributeError:
				return 0
			x = xnew
		return 0

	def GetWtdChildren(self):
		return self.wtd_children

	def IsWanted(self):
		# This is not very efficient...
		if self.parent is None:
			return 1
		parent = self.parent
		if not hasattr(parent, 'wtd_children'):
			return 1
		return self in parent.wtd_children and parent.IsWanted()

	#
	# SetArcSrc sets the source of a sync arc.
	#
	def SetArcSrc(self, side, delay, aid):
		self.sync_to[side].append((SYNC, (delay, aid)))

	#
	# SetArcDst sets the destination of a sync arc.
	#
	def SetArcDst(self, side, aid):
		self.sync_from[side].append((SYNC_DONE, aid))

	#
	# method for maintaining armed status when the ChannelView is
	# not active
	#
	def set_armedmode(self, mode):
		self.armedmode = mode
		
	#
	# method for maintaining node's info-icon state when the HierarchyView is
	# not active
	#
	def set_infoicon(self, icon, msg=None):
		self.infoicon = icon
		self.errormessage = msg
		
	def clear_infoicon(self):
		self.infoicon = ''
		self.errormessage = None
		for ch in self.children:
			ch.clear_infoicon()

	#
	# Playability depending on system/environment parameters
	# and various other things. There are three concepts:
	# ShouldPlay() - A decision based only on node attributes
	#                and preference settings.
	# _CanPlay()   - Depends on ShouldPlay() and whether the channel
	#                actually can play the node.
	# WillPlay()   - Based on ShouldPlay() and switch items.
	#
	def _CanPlay(self):
		if not self.canplay is None:
			return self.canplay
		self.canplay = self.ShouldPlay()
		if not self.canplay:
			return 0
		# Check that we really can
		getchannelfunc = self.context.getchannelbynode
		if self.type in leaftypes and getchannelfunc:
			# For media nodes check that the channel likes
			# the node
			chan = getchannelfunc(self)
			if not chan or not chan.getaltvalue(self):
				self.canplay = 0
		return self.canplay

	def ShouldPlay(self):
		if not self.shouldplay is None:
			return self.shouldplay
		self.shouldplay = 0
		# If any of the system test attributes don't match
		# we should not play
		all = settings.getsettings()
		for setting in all:
			if self.attrdict.has_key(setting):
				ok = settings.match(setting,
						    self.attrdict[setting])
				if not ok:
					return 0
		# And if our user group doesn't match we shouldn't
		# play either
		u_group = self.GetAttrDef('u_group', 'undefined')
		if u_group != 'undefined':
			val = self.context.usergroups.get(u_group)
			if val is not None and val[1] != 'RENDERED':
				return 0
		# Else we should
		self.shouldplay = 1
		return 1

	def WillPlay(self):
		if not self.willplay is None:
			return self.willplay
		parent = self.parent
		# If our parent won't play we won't play
		if parent and not parent.WillPlay():
			self.willplay = 0
			return 0
		# And if we shouldn't play we won't play either
		if not self.ShouldPlay():
			self.willplay = 0
			return 0
		# And if our parent is a switch we have to check whether
		# we're the Chosen One
		if parent and parent.type == 'alt' and \
		   not parent.ChosenSwitchChild() is self:
			self.willplay = 0
			return 0
		self.willplay = 1
		return 1

	def ChosenSwitchChild(self, childrentopickfrom=None):
		"""For alt nodes, return the child that will be played"""
		if childrentopickfrom is None:
			childrentopickfrom = self.children
		for ch in childrentopickfrom:
			if ch.force_switch_choice:
				return ch
		for ch in childrentopickfrom:
			if ch._CanPlay():
				return ch
		return None

	def ResetPlayability(self):
		self.canplay = self.willplay = self.shouldplay = None
		for child in self.children:
			child.ResetPlayability()

# Make a "deep copy" of an arbitrary value
#
def _valuedeepcopy(value):
	if type(value) is type({}):
		copy = {}
		for key in value.keys():
			copy[key] = _valuedeepcopy(value[key])
		return copy
	if type(value) is type([]):
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
	for a1, a2, dir, ltype in links:
		if type(a1) is not type(()) or type(a2) is not type(()):
			continue
		uid1, aid1 = a1
		uid2, aid2 = a2
		if uidremap.has_key(uid1) and uidremap.has_key(uid2):
			uid1 = uidremap[uid1]
			uid2 = uidremap[uid2]
			a1 = uid1, aid1
			a2 = uid2, aid2
			link = a1, a2, dir, ltype
			newlinks.append(link)
	if newlinks:
		dst_hyperlinks.addlinks(newlinks)

def _copyoutgoinghyperlinks(hyperlinks, uidremap):
	from Hlinks import DIR_1TO2, DIR_2TO1, DIR_2WAY
	links = hyperlinks.getall()
	newlinks = []
	for a1, a2, dir, ltype in links:
		changed = 0
		if type(a1) is type(()):
			uid1, aid1 = a1
			if uidremap.has_key(uid1) and \
			   dir in (DIR_1TO2, DIR_2WAY):
				uid1 = uidremap[uid1]
				a1 = uid1, aid1
				changed = 1
		if type(a2) is type(()):
			uid2, aid2 = a2
			if uidremap.has_key(uid2) and \
			   dir in (DIR_2TO1, DIR_2WAY):
				uid2 = uidremap[uid2]
				a2 = uid2, aid2
				changed = 1
		if changed:
			link = a1, a2, dir, ltype
			newlinks.append(link)
##		uid1, aid1 = a1
##		uid2, aid2 = a2
##		if uidremap.has_key(uid1) and dir in (DIR_1TO2, DIR_2WAY) or \
##			uidremap.has_key(uid2) and dir in (DIR_2TO1, DIR_2WAY):
##			if uidremap.has_key(uid1):
##				uid1 = uidremap[uid1]
##				a1 = uid1, aid1
##			if uidremap.has_key(uid2):
##				uid2 = uidremap[uid2]
##				a2 = uid2, aid2
##			link = a1, a2, dir, ltype
##			newlinks.append(link)
	if newlinks:
		hyperlinks.addlinks(newlinks)

#
# MergeList merges two lists. It also returns a status value to indicate
# whether there was an overlap between the lists.
#
def MergeLists(l1, l2):
	overlap = []
	for i in l2:
		if i in l1:
			overlap.append(i)
		else:
			l1.append(i)
	return l1, overlap
