__version__ = "$Id$"

import MMAttrdefs
from MMTypes import *
from MMExc import *
from SR import *
from AnchorDefs import *
from Hlinks import Hlinks
import MMurl
import settings
import features
from HDTL import HD, TL
import string
import MMStates

debuggensr = 0
debug = 0

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
		self.regpoints = {}
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
		self.metadata = ''

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
		# experimental SMIL Boston layout code
		# now, the user associate a node to a LayoutChannel (SMIL Boston region)
		# so we return all layout existing layout channels
		chlist = []
		for ch in self.channels:
			if ch['type'] == 'layout':
				chlist.append(ch.name)
		chlist.sort()
		return chlist		
		# end experimental
		
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
	# registration points administration
	#
	
	def addRegpoint(self, name, dict, isdefault=0):
		regpoint = MMRegPoint(self,name)
		
		for attr, val in dict.items():
			if attr == 'top' or attr == 'bottom' or \
				attr == 'left' or attr == 'right' or attr == 'regAlign':
				regpoint[attr] = val
		
		regpoint['isdefault'] = isdefault
		self.regpoints[name] = regpoint

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
			title, rendered, allowed, uid = value
			rendered = ['NOT RENDERED', 'RENDERED'][rendered]
			allowed = ['not allowed', 'allowed'][allowed]
			self.usergroups[name] = title, rendered, allowed, uid

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

class MMRegPoint:
	def __init__(self, context, name):
		self.context = context
		self.name = name
		self.isdef = 0
		self.attrdict = {}
		
	def __repr__(self):
		return '<MMRegPoint instance, name=' + `self.name` + '>'
		
	#
	# Emulate the dictionary interface
	#

	def __setitem__(self, key, value):
		if key == 'isdefault':
			self.isdef = value
		else:
			self.attrdict[key] = value
		
	def __getitem__(self, key):
		val = self.attrdict.get(key)
		return val
	
	def isdefault(self):
		return self.isdef
		
	def getregalign(self):
		if self.attrdict.has_key('regAlign'):
			return self.attrdict['regAlign']
		
		return MMAttrdefs.getdefattr(self, 'regAlign')

	# return the point in pixel
	def getx(self, boxwidth):
		if self.attrdict.has_key('left'):
			x = self.attrdict['left']
			if type(x) == type(1.0):
				x = x*boxwidth
		elif self.attrdict.has_key('right'):
			right = self.attrdict['right']
			if type(right) == type(1.0):
				right = right*boxwidth
			x = boxwidth-right
		else:
			x = 0
		
		return x
		
	# return the point in pixel
	def gety(self, boxheight):
		if self.attrdict.has_key('top'):
			y = self.attrdict['top']
			if type(y) == type(1.0):
				y = y*boxheight
		elif self.attrdict.has_key('bottom'):
			bottom = self.attrdict['bottom']
			if type(bottom) == type(1.0):
				bottom = bottom*boxheight
			y = boxheight-bottom
		else:
			y = 0
		
		return y
	
	# return the tuple x,y alignment in pourcent value
	# alignOveride is an optional overide id
	def getxyAlign(self, alignOveride=None):
		alignId = None
		if alignOveride == None:
			alignId = self.getregalign()
		else:
			alignId = alignOveride
			
		from RegpointDefs import alignDef
		xy = alignDef.get(alignId)
		if xy == None:		
			# impossible value, avoid a crash if bug
			xy = (0.0, 0,0)
		return xy
			
	def items(self):
		return self.attrdict.items()
		
class MMChannel:
	def __init__(self, context, name):
		self.context = context
		self.name = name
		self.attrdict = {}
		self.d_attrdict = {}

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
	# Set animated attribute
	#
	def SetPresentationAttr(self, name, value):
		if self.attrdict.has_key(name):
			self.d_attrdict[name] = value
		elif name in ('position', 'left', 'top', 'width', 'height','right','bottom') and\
			self.attrdict.has_key('base_winoff'):
			d = self.d_attrdict
			n = 'base_winoff'
			if self.d_attrdict.has_key(n):	
				x, y, w, h = self.d_attrdict[n]
			else:
				x, y, w, h = self.attrdict[n]	
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

	def GetPresentationAttr(self, name):
		if self.d_attrdict.has_key(name):
			return self.d_attrdict[name]
		elif self.attrdict.has_key(name):
			return self.attrdict[name]

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

	def get(self, key, default = None, animated=0):
		if animated and self.d_attrdict.has_key(key):
			return self.d_attrdict[key]
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
	def __init__(self, dstnode, action, srcnode=None, event=None, marker=None, wallclock=None, delay=None):
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
		self.ismin = action == 'min'
		self.srcnode = srcnode	# None if parent; "prev" if previous; else MMNode instance
		self.event = event
		self.marker = marker
		self.wallclock = wallclock
		self.delay = delay
		self.qid = None
		self.timestamp = None
		if debug: print 'MMSyncArc.__init__', `self`

	def __repr__(self):
		if self.wallclock is not None:
			yr,mt,dy,hr,mn,sc,tzsg,tzhr,tzmn = self.wallclock
			if yr is not None:
				date = '%04d-%02d-%02dT' % (yr, mt, dy)
			else:
				date = ''
			time = '%02d:%02d:%05.2f' % (hr, mn, sc)
			if tzhr is not None:
				tz = '%s%02d:%02d' % (tzsg, tzhr, tzmn)
			else:
				tz = ''
			return '<MMSyncArc instance, wallclock=%s%s%s>' % (date, time, tz)
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
		if self.delay is None:
			src = src + '+indefinite'
		elif self.delay > 0:
			src = src + '+%g' % self.delay
		elif self.delay < 0:
			src = src + '%g' % self.delay
		dst = `self.dstnode`
		if self.isstart:
			dst = dst + '.begin'
		else:
			dst = dst + '.end'
			if self.ismin:
				dst = dst + '(min)'
		if self.timestamp is not None:
			ts = ', timestamp = %g' % self.timestamp
		else:
			ts = ''
		return '<MMSyncArc instance, from %s to %s%s>' % (src, dst, ts)

	def refnode(self):
		node = self.dstnode
		if self.wallclock is not None:
			refnode = node.GetSchedParent() or node
			refnode = refnode.looping_body_self or refnode
		elif self.srcnode == 'prev' or (self.srcnode is None and node.GetSchedParent().type == 'seq'):
			refnode = node.GetSchedParent()
			for c in refnode.GetSchedChildren():
				if c is node:
					break
				refnode = c
		elif self.srcnode is None:
			refnode = node.GetSchedParent()
			refnode = refnode.looping_body_self or refnode
		elif self.srcnode is node:
			refnode = node.looping_body_self or node
		else:
			refnode = self.srcnode
		return refnode

	def isresolved(self, timefunc):
		if self.delay is None:
			return 0
		if self.wallclock is not None:
			if timefunc is not None:
				return 1
			return 0
		refnode = self.refnode()
		if self.event is None and self.marker is None:
			return 1
		if self.event in ('begin', 'end'):
			if refnode.playing in (MMStates.PLAYING, MMStates.PAUSED, MMStates.FROZEN, MMStates.PLAYED):
				return 1
			# XXX or maybe if refnode.isscheduled(): return 1
			return 0
		if self.event is not None and refnode.eventhappened(self.event):
			return 1
		if self.marker is not None and refnode.markerhappened(self.marker):
			return 1
		return 0

	def resolvedtime(self, timefunc):
		if self.timestamp is not None:
			return self.timestamp
		if self.wallclock is not None:
			import time, calendar
			t0 = time.time()
			t1 = timefunc()
			localtime = time.localtime(t0)
			yr,mt,dy,hr,mn,sc,tzsg,tzhr,tzmn = self.wallclock
			if tzhr is not None:
				# we want the time in our local time zone
				sc = 3600*hr + 60*mn + sc
				# first convert to UTC
				tzsc = 3600*tzhr + 60*tzmn
				if tzsg == '-':
					tzsc = -tzsc
				sc = sc - tzsc
				# then convert to our own time zone
				sc = sc - time.timezone + localtime[8]*3600
				while sc < 0:
					sc = sc + 86400
					if dy is not None:
						dy = dy - 1
				while dy is not None and dy < 1:
					mn = mn - 1
					while mn < 1:
						yr = yr - 1
						mn = mn + 12
					dy = dy + calendar.monthrange(yr, mn)[1]
				hr,sc = divmod(sc, 3600)
				mn,sc = divmod(sc, 60)
			if yr is None:
				tm = time.mktime((localtime[0],localtime[1],localtime[2],hr,mn,sc,0,0,-1))
				sc = 3600*hr + 60*mn + sc
				t = localtime[3]*3600+localtime[4]*60+localtime[5]
				while sc < t:
					sc = sc + 86400
					tm = tm + 86400
				return tm + t1 - t0 + self.delay
			t = time.mktime((yr,mt,dy,hr,mn,sc,0,0,-1))
			return t + t1 - t0 + self.delay
				
		refnode = self.refnode()
		if self.event == 'begin':
			if refnode.start_time is None:
				return refnode.isresolved() + self.delay
			return refnode.start_time + self.delay
		if self.event is not None:
			return refnode.happenings[('event', self.event)] + self.delay
		if self.marker is not None:
			return refnode.happenings[('marker', self.marker)] + self.delay
		if self.dstnode.GetSchedParent().type == 'seq' and \
		   refnode is not self.dstnode.GetSchedParent():
			# self is previous child in seq, so
			# event is end
			event = 'end'
		else:
			# self is first child of seq, or child
			# of par/excl, so event is begin
			if refnode.start_time is None:
				return refnode.isresolved() + self.delay
			return refnode.start_time + self.delay
		return refnode.happenings[('event', event)] + self.delay
			

class MMNode_body:
	"""Helper for looping nodes"""
	helpertype = "looping"
	
	def __init__(self, parent):
		self.fullduration = None
		self.scheduled_children = 0
		self.parent = parent
		self.sched_children = []
		self.arcs = []
		self.durarcs = []
		self.time_list = []
		self.has_min = 0
		if debug: print 'MMNode_body.__init__', `self`

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
	
	def cleanup_sched(self, sched):
		self.parent.cleanup_sched(sched, self)

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
		self.setgensr()
		self.looping_body_self = None
		self.realpix_body = None
		self.caption_body = None
		self.curloopcount = 0
		self.infoicon = ''
		self.errormessage = None
		self.force_switch_choice = 0
		self.srdict = {}
		self.events = {}	# events others are interested in
		self.sched_children = [] # arcs that depend on us
		self.scheduled_children = 0
		self.arcs = []
		self.durarcs = []
		self.reset()
		self.time_list = []
		self.fullduration = None
		self.pausestack = []	# used only by excl nodes
		# stuff to do with the min attribute
		self.has_min = 0
		self.delayed_arcs = []
		self.__calcendtimecalled = 0

	#
	# Return string representation of self
	#
	def __repr__(self):
		try:
			import MMAttrdefs
			name = MMAttrdefs.getattr(self, 'name')
		except:
			name = ''
		return '<MMNode instance, type=%s, uid=%s, name=%s, playing=%s>' % \
		       (`self.type`, `self.uid`, `name`, MMStates.states[self.playing])

	# methods that have to do with playback
	def reset(self):
		self.happenings = {}
		self.playing = MMStates.IDLE
		self.sctx = None
		self.start_time = None
		if debug: print 'MMNode.reset', `self`

	def resetall(self, sched):
		if debug: print 'resetall', `self`
		self.reset()
		for c in self.children:
			c.resetall(sched)
		for arc in MMAttrdefs.getattr(self, 'beginlist') + MMAttrdefs.getattr(self, 'endlist') + self.durarcs:
			refnode = self.__find_refnode(arc)
			if arc in refnode.sched_children:
				refnode.sched_children.remove(arc)
			if arc.qid is not None:
				sched.cancel(arc.qid)
				arc.qid = None
			arc.timestamp = None
		self.sched_children = []
		self.looping_body_self = None
		self.realpix_body = None
		self.caption_body = None
		self.curloopcount = 0
		self.srdict = {}
		self.events = {}
		self.scheduled_children = 0
		self.arcs = []
		self.durarcs = []
		self.time_list = []

	def startplay(self, sctx, timestamp):
		if debug: print 'startplay',`self`,timestamp,self.fullduration
		self.playing = MMStates.PLAYING
		self.sctx = sctx
		if self.GetFill() == 'remove' and \
		   self.fullduration is not None and \
		   self.fullduration >= 0:
			endtime = timestamp + self.fullduration
		else:
			endtime = None
		self.time_list.append((timestamp, endtime))

	def stopplay(self, timestamp):
		if debug: print 'stopplay',`self`,timestamp
		self.playing = MMStates.PLAYED
		self.time_list[-1] = self.time_list[-1][0], timestamp
##		for c in self.GetSchedChildren():
##			c.resetall(self.sctx.parent)

	def add_arc(self, arc, body = None):
		if body is None:
			body = self
		if arc in body.sched_children:
			return
		if debug: print 'add_arc', `body`, `arc`
		body.sched_children.append(arc)
		if self.playing != MMStates.IDLE and \
		   self.playing != MMStates.PLAYED and \
		   self.type in leaftypes:
			getchannelfunc = self.context.getchannelbynode
			if getchannelfunc:
				chan = getchannelfunc(self)
				if chan:
					chan.add_arc(self, arc)
		if self.playing != MMStates.IDLE and arc.delay is not None:
			# if arc's event has already occurred, trigger it
			if arc.wallclock is not None:
				if arc.resolvedtime(self.sctx.parent.timefunc) <= self.sctx.parent.timefunc():
					self.sctx.trigger(arc)
				return
			if arc.event is not None:
				key = 'event', arc.event
			elif arc.marker is not None:
				key = 'marker', arc.marker
			elif arc.dstnode.GetSchedParent().type == 'seq' and \
			     self is not arc.dstnode.GetSchedParent():
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
					self.sctx.trigger(arc)

	def event(self, time, event):
		self.happenings[('event', event)] = time

	def marker(self, time, marker):
		self.happenings[('marker', marker)] = time

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
	def GetFill(self):
		fill = self.attrdict.get('fill')
		if fill is None or fill == 'default':
			fill = self.GetInherAttrDef('fillDefault', None)
		if fill is None or fill == 'inherit' or fill == 'auto':
			if not self.attrdict.has_key('duration') and \
			   not self.attrdict.get('endlist') and \
			   not self.attrdict.has_key('repeatdur') and \
			   not self.attrdict.has_key('loop'):
				fill = 'freeze'
			else:
				fill = 'remove'
		return fill

	def GetSyncBehavior(self):
		syncBehavior = self.attrdict.get('syncBehavior')
		if syncBehavior is None or syncBehavior == 'default':
			syncBehavior = self.GetInherAttrDef('syncBehaviorDefault', None)
		if syncBehavior is None or syncBehavior == 'inherit':
			return None
		return syncBehavior

	def GetRestart(self):
		restart = self.attrdict.get('restart')
		if restart is None or restart == 'default':
			restart = self.GetInherAttrDef('restartDefault', None)
		if restart is None or restart == 'inherit':
			return 'always'
		return restart

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

	def GetSchedParent(self):
		parent = self.parent
		while parent is not None and (parent.type == 'prio' or parent.type == 'alt'):
			parent = parent.parent
		return parent

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

	def GetPathsToCommonAncestor(self, x):
		# Return the paths to the common ancestor of the nodes.
		# Return values include the common ancestor and the
		# nodes themselves.
		p1 = self.GetPath()
		p2 = x.GetPath()
		n = min(len(p1), len(p2))
		i = 0
		while i < n and p1[i] == p2[i]:
			i = i+1
		if i == 0:
			return None, None
		else:
			return p1[i-1:], p2[i-1:] # includes common ancestor

	def PrioCompare(self, other):
		if self is other:
			return 0, [self], [other]
		p1, p2 = self.GetPathsToCommonAncestor(other)
		if p1 is None or p2 is None:
			# "can't happen"
			# this means the nodes are in different trees
			return 0, None, None
		if p1[1].type == 'prio' and p2[1].type == 'prio':
			# nodes are in different priority classes
			i1 = p1[0].children.index(p1[1])
			i2 = p1[0].children.index(p2[1])
			# i1 != i2
			return cmp(i1, i2), p1, p2
		# nodes are in the same priority class
		return 0, p1, p2
		
	def GetChildren(self):
		return self.children

	def GetSchedChildren(self):
		children = []
		for c in self.children:
			if c.type == 'prio':
				children = children + c.GetSchedChildren()
			elif c.type == 'alt':
				c = c.ChosenSwitchChild()
				if c is not None:
					children.append(c)
			else:
				children.append(c)
		return children

	def GetChild(self, i):
		return self.children[i]

	def GetChildByName(self, name):
		if self.attrdict.has_key('name') and  self.attrdict['name']==name:
			return self
		for child in self.children:
			return child.GetChildByName(name)
		return None

	def GetChildWithArea(self, name):
		alist = MMAttrdefs.getattr(self, 'anchorlist')
		for id, type, args, times in alist:
			if id==name:
				return self, id, type, args, times
		for child in self.children:
			return child.GetChildWithArea(name)
		return None

	def GetValues(self):
		return self.values

	def GetValue(self, i):
		return self.values[i]

	def GetAttrDict(self):
		return self.attrdict

	def GetRawAttr(self, name, animated=0):
		if animated and self.d_attrdict.has_key(name):
			return self.d_attrdict[name]
		if self.attrdict.has_key(name):
			return self.attrdict[name]
		raise NoSuchAttrError, 'in GetRawAttr()'

	def GetRawAttrDef(self, name, default, animated=0):
		if animated and self.d_attrdict.has_key(name):
			return self.d_attrdict[name]
		return self.attrdict.get(name, default)

	def GetAttr(self, name, animated=0):
		if animated and self.d_attrdict.has_key(name):
			return self.d_attrdict[name]
		if self.attrdict.has_key(name):
			return self.attrdict[name]
		raise NoSuchAttrError, 'in GetAttr'

	def GetAttrDef(self, name, default, animated=0):
		if animated and self.d_attrdict.has_key(name):
			return self.d_attrdict[name]
		return self.attrdict.get(name, default)

	def GetInherAttr(self, name, animated=0):
		if animated:
			x = self
			while x is not None:
				if x.d_attrdict and x.d_attrdict.has_key(name):
					return x.d_attrdict[name]
				x = x.parent	
		x = self
		while x is not None:
			if x.attrdict and x.attrdict.has_key(name):
				return x.attrdict[name]
			x = x.parent
		raise NoSuchAttrError, 'in GetInherAttr()'

	def GetDefInherAttr(self, name, animated=0):
		if animated:
			x = self
			while x is not None:
				if x.d_attrdict and x.d_attrdict.has_key(name):
					return x.d_attrdict[name]
				x = x.parent	
		x = self.parent
		while x is not None:
			if x.attrdict and x.attrdict.has_key(name):
				return x.attrdict[name]
			x = x.parent
		raise NoSuchAttrError, 'in GetInherDefAttr()'

	def GetInherAttrDef(self, name, default, animated=0):
		if animated:
			x = self
			while x is not None:
				if x.d_attrdict and x.d_attrdict.has_key(name):
					return x.d_attrdict[name]
				x = x.parent	
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

	def GetRegPoint(self):
		regpointname = MMAttrdefs.getattr(self,'regPoint')
		return self.context.regpoints.get(regpointname)

	def GetRegAlign(self, regpoint):
		if self.attrdict.has_key('regAlign'):
			return self.attrdict['regAlign']
		
		return regpoint.getregalign()

	# get default media size in pixel
	# if not defined, return width and height
	def GetDefaultMediaSize(self, defWidth, defHeight):
		try:
			file = self.GetAttr('file')
			url = self.context.findurl(file)
			import Sizes
			media_width, media_height = Sizes.GetSize(url)
		except:
			media_width = defWidth 
			media_height = defHeight

		return media_width, media_height
	

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
##		if self.type in bagtypes:
##			return [], None
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
		return self.GetSchedParent() is None
##		if self.type in bagtypes:
##			return 0
##		parent = self.GetSchedParent()
##		return parent is None or parent.type in bagtypes

	# Find the first mini-document in a tree
	def FirstMiniDocument(self):
		if self.IsMiniDocument():
			return self
		for child in self.GetSchedChildren():
			mini = child.FirstMiniDocument()
			if mini is not None:
				return mini
		return None

	# Find the last mini-document in a tree
	def LastMiniDocument(self):
		if self.IsMiniDocument():
			return self
		res = None
		for child in self.GetSchedChildren():
			mini = child.LastMiniDocument()
			if mini is not None:
				res = mini
		return res

	# Find the next mini-document in a tree after the given one
	# Return None if this is the last one
	def NextMiniDocument(self):
		node = self
		while 1:
			parent = node.GetSchedParent()
			if parent is None:
				break
			siblings = parent.GetSchedChildren()
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
			parent = node.GetSchedParent()
			if parent is None:
				break
			siblings = parent.GetSchedChildren()
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
		return self.GetRoot()
##		node = self
##		parent = node.parent
##		while parent is not None and parent.type not in bagtypes:
##			node = parent
##			parent = node.parent
##		return node

	# Find the nearest bag given a minidocument
	def FindMiniBag(self):
		return None
##		bag = self.parent
##		if bag is not None and bag.type not in bagtypes:
##			raise CheckError, 'FindMiniBag: minidoc not rooted in a choice node!'
##		return bag

	#
	# Set the correct method for generating scheduler records.
	def setgensr(self):
		type = self.type
		if type in ('imm', 'ext'):
			self.gensr = self.gensr_leaf
##		elif type == 'bag':
##			self.gensr = self.gensr_bag
		elif type in ('seq', 'par', 'excl', 'alt', 'bag'):
			self.gensr = self.gensr_interior
		elif type == 'prio':
			self.gensr = None # should never be called
		else:
			raise CheckError, 'MMNode: unknown type %s' % self.type		 
	#
	# Methods for building scheduler records. The interface is as follows:
	# - PruneTree() is called first, with a parameter that specifies the
	#   node to seek to (where we want to start playing). None means 'play
	#   everything'. PruneTree() sets the scope of all the next calls and
	#   initializes a few data structures in the tree nodes.
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
		self.realpix_body = None
		self.caption_body = None
		self.force_switch_choice = 0
		self.wtd_children = []
		if self.type in playabletypes:
			return
		if self.type == 'seq':
			for c in self.GetSchedChildren():
				if seeknode is not None and \
				   c.IsAncestorOf(seeknode):
					self.wtd_children.append(c)
					c.PruneTree(seeknode)
					seeknode = None
				elif seeknode is None:
					self.wtd_children.append(c)
					c._FastPruneTree()
		elif self.type == 'par':
			self.wtd_children = self.GetSchedChildren()[:]
			for c in self.GetSchedChildren():
				if c.IsAncestorOf(seeknode):
					c.PruneTree(seeknode)
				else:
					c._FastPruneTree()
		elif self.type == 'alt':
			for c in self.GetSchedChildren():
				c.force_switch_choice = 0
				if c.IsAncestorOf(seeknode):
					self.wtd_children.append(c)
					c.PruneTree(seeknode)
					c.force_switch_choice = 1
		elif self.type == 'excl':
			for c in self.GetSchedChildren():
				if c.IsAncestorOf(seeknode):
					self.wtd_children.append(c)
					c.PruneTree(seeknode)
		else:
			raise CheckError, 'Cannot PruneTree() on nodes of this type %s' % self.type
	#
	# PruneTree - The fast lane. Just copy GetSchedChildren()->wtd_children.
	def _FastPruneTree(self):
		self.reset()
		self.events = {}
		self.realpix_body = None
		self.caption_body = None
		self.force_switch_choice = 0
		self.wtd_children = self.GetSchedChildren()[:]
		for c in self.GetSchedChildren():
			c._FastPruneTree()


	def EndPruneTree(self):
		pass
##		if self.type in ('seq', 'par'):
##			for c in self.wtd_children:
##				c.EndPruneTree()
##			del self.wtd_children

	def __find_refnode(self, arc):
		return arc.refnode()

	def isresolved(self):
		if self.start_time is not None:
			return self.start_time
		pnode = self.GetSchedParent()
		if pnode is None:
			# XXX is this true with begin="indefinite"?
			return 0	# root node is always resolved
		presolved = pnode.isresolved()
		if presolved is None:
			# if parent not resolved, we're not resolved
			return None
		beginlist = self.attrdict.get('beginlist', [])
		if not beginlist:
			# unless parent is excl, we're resolved if parent is
			if pnode.type == 'excl':
				return None
			if pnode.type == 'seq':
				val = presolved
				for c in pnode.GetSchedChildren():
					if c is self:
						return val
					e, maybecached = c.__calcendtime(val)
					if e is None or e < 0:
						return None
					val = val + e
				raise RuntimeError('cannot happen')
			return presolved
		min = None
		if self.sctx is not None:
			timefunc = self.sctx.parent.timefunc
		else:
			timefunc = None
		for arc in beginlist:
			if arc.isresolved(timefunc):
				v = arc.resolvedtime(timefunc)
				if min is None or v < min:
					min = v
		if min is None:
			# no resolved sync arcs
			return None
		# return earliest resolved time
		return presolved + min

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
		if settings.noprearm:
			srlist = [([(SCHED, self)], [(PLAY, self)])]
		else:
			srlist = [([(SCHED, self), (ARM_DONE, self)],
				   [(PLAY, self)])]
		fill = self.GetFill()

		sched_done = [(SCHED_DONE,self)]
		sched_stop = []
		if fill == 'remove':
			sched_done.append((PLAY_STOP, self))
		else:
			# XXX should be refined
			sched_stop.append((PLAY_STOP, self))
		srlist.append(
			([(PLAY_DONE, self)],
			 [(SCHED_STOPPING,self)]))
		srlist.append(([(SCHED_STOPPING,self)], sched_done))
		srlist.append(([(SCHED_STOP, self)], sched_stop))

		# XXX: ignoring animate elements timing for now, 
		# just kick animate childs in a parallel envelope	
		for child in self.GetSchedChildren():
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
	# - a list of all (event, action) tuples to be generated
	# 
	def gensr_interior(self, looping=0):
		#
		# If the node is empty there is very little to do.
		#
		is_realpix = 0
		if self._is_realpix_with_captions():
			gensr_body = self.gensr_body_realpix
			is_realpix = 1
		else:
			gensr_body = self.gensr_body_interior

		#
		# Select the  generator for the outer code: either non-looping
		# or, for looping nodes, the first or subsequent times through
		# the loop.
		#
		repeatCount = self.attrdict.get('loop', None)
		repeatDur = MMAttrdefs.getattr(self, 'repeatdur')
		if repeatDur != 0 and repeatCount is None:
			# no loop attr and specified repeatdur attr, so loop indefinitely
			# until time's up
			repeatCount = 0
		if (repeatCount is not None and 0 < repeatCount <= 1) or \
		   (repeatCount is None and repeatDur == 0):
			gensr_envelope = self.gensr_envelope_nonloop
			repeatCount = 1
		elif looping == 0:
			# First time loop generation
			gensr_envelope = self.gensr_envelope_firstloop
		else:
			gensr_envelope = self.gensr_envelope_laterloop

		fill = self.GetFill()

		#
		# We are started when we get our SCHED and all our
		# incoming head-syncarcs.
		#
		sched_events = [(SCHED, self)]
		#
		# Once we are started we should fire our outgoing head
		# syncarcs
		#
		sched_actions_arg = []
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

		sched_actions, schedstop_actions,  \
			       srdict = gensr_envelope(gensr_body, repeatCount,
						       sched_actions_arg,
						       scheddone_actions_arg)
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
			sched_done = [(SCHED_DONE, self)]
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

		if debuggensr: self.__dump_srdict('gensr_interior', srdict)
		return srdict

	def gensr_envelope_nonloop(self, gensr_body, repeatCount, sched_actions,
				   scheddone_actions):
		if repeatCount != 1:
			raise 'Looping nonlooping node!'
		self.curloopcount = 0

		sched_actions, schedstop_actions, srdict = \
			       gensr_body(sched_actions, scheddone_actions)
		if debuggensr: 
			self.__dump_srdict('gensr_envelope_nonloop', srdict)
		return sched_actions, schedstop_actions, srdict

	def gensr_envelope_firstloop(self, gensr_body, repeatCount,
				     sched_actions, scheddone_actions):
		srlist = []
		terminate_actions = []
		#
		# Remember the repeatCount.
		#
		if repeatCount == 0:
			self.curloopcount = -1
		else:
			self.curloopcount = repeatCount

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
		body_sched_actions, body_schedstop_actions, srdict = \
				    gensr_body(body_sched_actions,
					       body_scheddone_actions,
					       self.looping_body_self)

		# When the loop has started we start the body
		srlist.append( ([(LOOPSTART_DONE, self)], body_sched_actions) )

		# When the body is done we stop it, and we end/restart the loop
		srlist.append( ([(SCHED_STOPPING, self.looping_body_self)],
				[(SCHED_DONE, self.looping_body_self)]) )
		srlist.append( ([(SCHED_DONE, self.looping_body_self)],
				[(LOOPEND, self),
				 (SCHED_STOP, self.looping_body_self)]) )
		srlist.append( ([(SCHED_STOP, self.looping_body_self)],
				body_schedstop_actions) )

		if self.curloopcount < 0:
##			sched_actions = sched_actions + scheddone_actions
			srlist.append( ([(LOOPEND_DONE, self)], []) )
		else:
			srlist.append( ([(LOOPEND_DONE, self)],
					scheddone_actions) )

		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: 
			self.__dump_srdict('gensr_envelope_firstloop', srdict)
		return sched_actions, terminate_actions, srdict


	def gensr_envelope_laterloop(self, gensr_body, repeatCount,
				     sched_actions, scheddone_actions):
		srlist = []

		body_sched_actions = []
		body_scheddone_actions = [(SCHED_STOPPING, self.looping_body_self)]
		body_sched_actions, body_schedstop_actions, srdict = \
				    gensr_body(body_sched_actions,
					       body_scheddone_actions,
					       self.looping_body_self)

		# When the loop has started we start the body
		srlist.append( ([(LOOPSTART_DONE, self)], body_sched_actions) )

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
		if debug: print 'cleanup', `self`
		self.sched_children = []
		for child in self.children:
			child.cleanup()

	def cleanup_sched(self, sched, body = None):
		if debug: print 'cleanup_sched', `self`, `body`
		if self.type in leaftypes:
			return
		if body is None:
			if self.looping_body_self:
				return
			body = self
		for node, arc in body.arcs:
			#print 'deleting', `arc`
			node.sched_children.remove(arc)
		body.arcs = []
		for arc in body.durarcs:
			refnode = body.__find_refnode(arc)
			refnode.sched_children.remove(arc)
			if arc.qid is not None:
				sched.cancel(arc.qid)
				arc.qid = None
		body.durarcs = []
		for child in self.wtd_children:
			beginlist = MMAttrdefs.getattr(child, 'beginlist')
			if beginlist:
				for arc in beginlist:
					#print 'deleting arc',`arc`
					refnode = child.__find_refnode(arc)
					refnode.sched_children.remove(arc)
					if arc.qid is not None:
						sched.cancel(arc.qid)
						arc.qid = None
##					arc.timestamp = None
			for arc in MMAttrdefs.getattr(child, 'endlist'):
				#print 'deleting arc',`arc`
				refnode = child.__find_refnode(arc)
				refnode.sched_children.remove(arc)
				if arc.qid is not None:
					sched.cancel(arc.qid)
					arc.qid = None
##				arc.timestamp = None

	def gensr_body_interior(self, sched_actions, scheddone_actions,
			       self_body=None):
		srdict = {}
		srlist = []
		schedstop_actions = []
		terminate_actions = []
		terminating_children = []
		scheddone_events = []
		if self_body is None:
			self_body = self

		if self.type in ('par', 'excl'):
			termtype = MMAttrdefs.getattr(self, 'terminator')
		else:
			termtype = 'LAST'

		if self.type == 'alt':
			chosen = self.ChosenSwitchChild(self.wtd_children)
			if chosen:
				wtd_children = [chosen]
			else:
				wtd_children = []
		else:
			wtd_children = self.wtd_children

		if termtype == 'FIRST':
			terminating_children = wtd_children[:]
		elif termtype in ('LAST', 'ALL'):
			terminating_children = []
		else:
			terminating_children = []
			for child in wtd_children:
				if MMAttrdefs.getattr(child, 'name') \
				   == termtype:
					terminating_children.append(child)

		srcnode = self_body
		event = 'begin'
		if self.type == 'excl':
			defbegin = None
		elif self.type == 'bag':
			# defbegin will be set on each iteration
			# here we find out to what
			indexname = MMAttrdefs.getattr(self, 'bag_index')
			bagindex = None
			for child in self.GetSchedChildren():
				chname = MMAttrdefs.getattr(child, 'name')
				if chname and chname == indexname:
					bagindex = child
					break
		else:
			defbegin = 0.0

		duration = self.GetAttrDef('duration', None)
		if duration is not None and self_body is not self:
			if duration < 0:
				delay = None
			else:
				delay = duration
			arc = MMSyncArc(self_body, 'end', srcnode=self_body, event='begin', delay=delay)
			self_body.durarcs.append(arc)
##			self_body.arcs.append((self_body, arc))
			self_body.add_arc(arc)

		for child in wtd_children:
			chname = MMAttrdefs.getattr(child, 'name')
			beginlist = MMAttrdefs.getattr(child, 'beginlist')
			if not beginlist:
				if self.type == 'bag':
					if bagindex is child:
						defbegin = 0.0
					else:
						defbegin = None
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
			if self.type == 'seq':
				pass
			elif termtype in ('FIRST', chname): ## or
##			   (len(wtd_children) == 1 and
##			    (schedule or termtype == 'ALL')):
				arc = MMSyncArc(self_body, 'end', srcnode=child, event='end', delay=0)
				self_body.arcs.append((child, arc))
				child.add_arc(arc)
			elif schedule or termtype == 'ALL':
				scheddone_events.append((SCHED_DONE, child))
			for arc in MMAttrdefs.getattr(child, 'endlist'):
				refnode = child.__find_refnode(arc)
				refnode.add_arc(arc)
			cdur = child.calcfullduration()
			if cdur is not None and child.fullduration is not None:
				if cdur < 0:
					delay = None
				else:
					delay = cdur
				arc = MMSyncArc(child, 'end', srcnode=child, event='begin', delay=delay)
				child.durarcs.append(arc)
##				self_body.arcs.append((child, arc))
				child.add_arc(arc)
			min = child.GetAttrDef('min', 0)
			if min > 0:
				arc = MMSyncArc(child, 'min', srcnode=child, event='begin', delay=min)
				child.has_min = 1
				child.durarcs.append(arc)
				child.add_arc(arc)
			else:
				child.has_min = 0
			max = child.GetAttrDef('max', None)
			if max is not None:
				arc = MMSyncArc(child, 'end', srcnode=child, event='begin', delay=max)
				child.durarcs.append(arc)
				child.add_arc(arc)
			if self.type == 'seq':
				srcnode = child
				event = 'end'

		if self.type == 'seq' and wtd_children:
			# connect last child's end to parent's end
			# if no children, this would connects seq's begin to end
			arc = MMSyncArc(self_body, 'end', srcnode=srcnode, event=event, delay=0)
			self_body.arcs.append((srcnode, arc))
			srcnode.add_arc(arc)
		#
		# Trickery to handle dur and end correctly:
		#
		if scheddone_events and terminating_children:
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

		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: 
			self.__dump_srdict('gensr_body_interior', srdict)
		return sched_actions, schedstop_actions, srdict

	def gensr_body_realpix(self, sched_actions, scheddone_actions,
			       self_body=None):
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

			scheddone_events.append( (SCHED_DONE, child) )

		#
		# Trickery to handle dur and end correctly:
		# XXX isn't the dur passed on in the files? Check.
		if scheddone_events:
			srlist.append((scheddone_events,
				       scheddone_actions))
		else:
			terminate_actions = terminate_actions + \
					    scheddone_actions

		for events, actions in srlist:
			action = [len(events), actions]
			for event in events:
				self.srdict[event] = action # MUST all be same object
				srdict[event] = self.srdict # or just self?
		if debuggensr: 
			self.__dump_srdict('gensr_body_realpix', srdict)
		return sched_actions, schedstop_actions, srdict
			
	def gensr_child(self, child, runchild = 1):
		if debug: print 'gensr_child',`self`,`child`,runchild
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
			numsrlist = self.srdict[(SCHED_STOP, body)]
			srlist = numsrlist[1]
			srlist.append((SCHED_STOP, child))
		if debuggensr: 
			self.__dump_srdict('gensr_child', srdict)
		return srdict

	def __calcendtime(self, syncbase, t0 = None):
		# returns:
		#	None - no resolved begin
		#	-1 - resolved begin, no resolved end
		#	>= 0 - end time
		if self.__calcendtimecalled:
			# recursive call
			print '__calcendtime: breaking recursion'
			return None, 0	# break recursion
		start = None
		beginlist = MMAttrdefs.getattr(self, 'beginlist')
		pnode = self.GetSchedParent()
		if not beginlist:
			if pnode.type == 'excl':
				return None, 1
			start = 0
			maybecached = 1
		else:
			self.__calcendtimecalled = 1
			maybecached = 1
			if self.sctx is not None:
				timefunc = self.sctx.parent.timefunc
			else:
				timefunc = None
			for a in beginlist:
				t = None
				if a.event is not None or a.marker is not None or a.wallclock is not None:
					maybecached = 0
				if a.isresolved(timefunc) and self.start_time is not None:
					t = a.resolvedtime(timefunc) - self.start_time
				elif a.event == 'begin' or a.event == 'end':
					n = a.refnode()
					t0 = n.isresolved()
					if t0 is None:
						continue
					if a.event == 'end':
						d = n.calcfullduration()
						if d is None or d < 0:
							continue
						t = t0 + d
					else:
						t = t0
					if t is not None:
						if syncbase is not None:
							t = t + a.delay - syncbase
						else:
							t = None
				elif a.event is not None or a.marker is not None or a.wallclock is not None:
					continue
				elif a.delay is not None:
					t = a.delay
				if t is None:
					continue
				if start is None or t < start:
					if t0 is None or t >= t0:
						start = t
			self.__calcendtimecalled = 0
		if start is None:
			# no resolved begin time
			return None, maybecached
		self.__calcendtimecalled = 1
		d = self.calcfullduration()
		self.__calcendtimecalled = 0
		if self.fullduration is None:
			maybecached = 0
		if d is None or d < 0:
			# unknown or no resolved duration
			return -1, maybecached
		end = start + d
		if end < 0:
			# find next one
			return self.__calcendtime(syncbase, end)
		return end, maybecached

	def __calcduration(self):
		# internal method to calculate the duration of a node
		# not taking into account the duration/end/repeat* attrs
		maybecached = 1
		if self.type in leaftypes:
			import Duration
			return Duration.get(self, ignoreloop=1), maybecached
		else:
			syncbase = self.isresolved()
			if self.type in ('par', 'excl'):
				termtype = MMAttrdefs.getattr(self, 'terminator')
				if termtype not in ('LAST', 'FIRST', 'ALL'):
					for c in self.GetSchedChildren():
						if MMAttrdefs.getattr(c, 'name') == termtype:
							return c.__calcendtime(syncbase)
					termtype = 'LAST' # fallback
				val = -1
				for c in self.GetSchedChildren():
					e, mc = c.__calcendtime(syncbase)
					if not mc:
						maybecached = 0
					if termtype == 'FIRST':
						if (e is None or e < 0) and val < 0:
							pass
						elif val < 0:
							val = e
						elif e >= 0 and e < val:
							val = e
					elif termtype == 'LAST':
						if e is None:
							continue
						if e < 0:
							return -1, maybecached
						if val < 0 or e > val:
							val = e
					elif termtype == 'ALL':
						if e is None or e < 0:
							return -1, maybecached
						if val < 0 or e > val:
							val = e
				return val, maybecached
			if self.type == 'seq':
				val = 0
				for c in self.GetSchedChildren():
					e, mc = c.__calcendtime(syncbase)
					if not mc:
						maybecached = 0
					if e is None or e < 0:
						return -1, maybecached
					val = val + e
					if syncbase is not None:
						syncbase = syncbase + e
				return val, maybecached
			if self.type == 'alt':
				c = self.ChosenSwitchChild()
				if c is None:
					return 0, maybecached
				return c.__calcduration()

	def calcfullduration(self):
		if self.fullduration is not None:
			return self.fullduration
		maybecached = 1
		duration = self.attrdict.get('duration')
		repeatDur = self.attrdict.get('repeatdur')
		repeatCount = self.attrdict.get('loop')
		endlist = self.attrdict.get('endlist')
		if endlist is not None and duration is None and \
		   repeatCount is None and repeatDur is None:
			# "If an end attribute is specified but none
			# of dur, repeatCount and repeatDur are
			# specified, the simple duration is defined to
			# be indefinite"
			duration = -1
		if repeatDur is not None and \
		   repeatCount is not None:
			if duration is None:
				duration, maybecached = self.__calcduration()
			if duration is not None and duration > 0 and \
			   repeatCount > 0 and repeatDur >= 0:
				duration = min(repeatCount * duration, repeatDur)
			elif duration is not None and duration > 0 and \
			     repeatCount > 0 and repeatDur < 0:
				duration = repeatCount * duration
			# else repeatCount=indefinite or to be ignored
			elif repeatDur >= 0:
				duration = repeatDur
			else:
				duration = -1
		elif repeatDur is not None: # repeatCount is None
			duration = repeatDur
		elif repeatCount is not None: # repeatDur is None
			if duration is None:
				duration, maybecached = self.__calcduration()
			if duration is not None and duration > 0:
				if repeatCount > 0:
					duration = repeatCount * duration
				else:
					duration = -1
		elif duration is None:
			duration, maybecached = self.__calcduration()
		
		# adjust duration when we have time manipulations
		if duration is not None and duration > 0:
			speed = self.attrdict.get('speed')
			if speed:
				duration = duration / speed
			if MMAttrdefs.getattr(self, 'autoReverse'):
				duration = 2.0 * duration
		
		if maybecached:
			self.fullduration = duration
		else:
			self.fullduration = None
		return duration

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
		if self.shouldplay is not None:
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
			childrentopickfrom = self.GetSchedChildren()
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
	for a1, a2, dir, ltype, stype, dtype in links:
		if type(a1) is not type(()) or type(a2) is not type(()):
			continue
		uid1, aid1 = a1
		uid2, aid2 = a2
		if uidremap.has_key(uid1) and uidremap.has_key(uid2):
			uid1 = uidremap[uid1]
			uid2 = uidremap[uid2]
			a1 = uid1, aid1
			a2 = uid2, aid2
			link = a1, a2, dir, ltype, stype, dtype
			newlinks.append(link)
	if newlinks:
		dst_hyperlinks.addlinks(newlinks)

def _copyoutgoinghyperlinks(hyperlinks, uidremap):
	from Hlinks import DIR_1TO2, DIR_2TO1, DIR_2WAY
	links = hyperlinks.getall()
	newlinks = []
	for a1, a2, dir, ltype, stype, dtype in links:
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
			link = a1, a2, dir, ltype, stype, dtype
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
