__version__ = "$Id$"

import windowinterface
import MMAttrdefs
import ChannelMap
import ChannelMime
from MMExc import *			# exceptions
import MMNode
from MMTypes import *
from AnchorDefs import *		# ATYPE_*
from Hlinks import DIR_1TO2, TYPE_JUMP
import features
import string
import os
import sys
import flags

DEFAULT = 'Default'
UNDEFINED = 'undefined'
NEW_CHANNEL = 'New channel...'

# There are two basic calls into this module (but see below for more):
# showattreditor(node) creates an attribute editor form for a node
# and hideattreditor(node) hides it again.  Since the editor may also
# hide itself, spurious hide calls are ignored; also, only one attribute
# editor is allowed per node, and extra show calls are also ignored
# (actually, this pops up the window, to draw the user's attention...).

def showattreditor(toplevel, node, initattr = None, chtype = None):
	try:
		attreditor = node.attreditor
	except AttributeError:
		if node.__class__ is MMNode.MMNode:
			wrapperclass = NodeWrapper
			if node.GetType() == 'ext' and \
			   node.GetChannelType() == 'RealPix' and \
			   not hasattr(node, 'slideshow'):
				import realnode
				node.slideshow = realnode.SlideShow(node)
		else:
			wrapperclass = SlideWrapper
		attreditor = AttrEditor(wrapperclass(toplevel, node), initattr=initattr, chtype=chtype)
		node.attreditor = attreditor
	else:
		attreditor.pop()

# An additional call to check whether the attribute editor is currently
# active for a node (so the caller can put up a warning "you are already
# editing this node's attributes" instead of just silence).

def hasattreditor(node):
	try:
		attreditor = node.attreditor
	except AttributeError:
		return 0		# No attribute editor active
	return 1


# A similar interface for channels (note different arguments!).
# The administration is kept in channel.attreditor,
# which is created here if necessary.

def showchannelattreditor(toplevel, channel, new = 0, initattr = None):
	try:
		attreditor = channel.attreditor
	except AttributeError:
		attreditor = AttrEditor(ChannelWrapper(toplevel, channel), new=new, initattr = initattr)
		channel.attreditor = attreditor
	else:
		attreditor.pop()

def haschannelattreditor(channel):
	try:
		attreditor = channel.attreditor
	except AttributeError:
		return 0
	return 1

# A similar interface for documents (note different arguments!).
# The administration is kept in toplevel.attreditor,
# which is created here if necessary.

def showdocumentattreditor(toplevel, initattr = None):
	try:
		attreditor = toplevel.attreditor
	except AttributeError:
		attreditor = AttrEditor(DocumentWrapper(toplevel), initattr = initattr)
		toplevel.attreditor = attreditor
	else:
		attreditor.pop()

def hasdocumentattreditor(toplevel):
	try:
		attreditor = toplevel.attreditor
	except AttributeError:
		return 0
	return 1

# A similar interface for program preferences (note different arguments!).

prefseditor = None
def showpreferenceattreditor(callback, initattr = None):
	global prefseditor
	if prefseditor is None:
		prefseditor = AttrEditor(PreferenceWrapper(callback), initattr = initattr)
	else:
		prefseditor.pop()

def haspreferenceattreditor():
	return prefseditor is not None

def closepreferenceattreditor():
	global prefseditor
	if prefseditor is not None:
		prefseditor.close()
		prefseditor = None


# This routine checks whether we are in CMIF or SMIL mode, and
# whether the given attribute should be shown in the editor.
def cmifmode():
	import settings
	return settings.get('cmif')

# The "Wrapper" classes encapsulate the differences between attribute
# editors for nodes and channels.  If you want editors for other
# attribute collections (styles!) you may want to new wrappers.
# All wrappers should support the methods shown here; the __init__()
# method can have different arguments since it is only called from
# the show*() function.  (When introducing a style attr editor
# it should probably be merged with the class attr editor, using
# a common base class implementing most functions.)

class Wrapper: # Base class -- common operations
	def __init__(self, toplevel, context):
		self.toplevel = toplevel
		self.context = context
		self.editmgr = context.geteditmgr()
	def __repr__(self):
		return '<%s instance>' % self.__class__.__name__
	def close(self):
		del self.context
		del self.editmgr
		del self.toplevel
	def getcontext(self):
		return self.context
	def register(self, object):
		self.editmgr.register(object)
	def unregister(self, object):
		self.editmgr.unregister(object)
	def transaction(self):
		return self.editmgr.transaction()
	def commit(self):
		self.editmgr.commit()
	def rollback(self):
		self.editmgr.rollback()
	def setwaiting(self):
		self.toplevel.setwaiting()

	def getdef(self, name):
		return MMAttrdefs.getdef(name)
	def valuerepr(self, name, value):
		return MMAttrdefs.valuerepr(name, value)
	def parsevalue(self, name, str):
		return MMAttrdefs.parsevalue(name, str, self.context)

class NodeWrapper(Wrapper):
	def __init__(self, toplevel, node):
		self.node = node
		self.root = node.GetRoot()
		Wrapper.__init__(self, toplevel, node.GetContext())

	def __repr__(self):
		return '<NodeWrapper instance, node=' + `self.node` + '>'

	def close(self):
		del self.node.attreditor
		del self.node
		del self.root
		Wrapper.close(self)

	def commit(self):
		self.root.ResetPlayability()
		Wrapper.commit(self)

	def stillvalid(self):
		return self.node.GetRoot() is self.root

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Properties of node ' + name

	def __findlink(self, new = None):
		# if new == None, just return a link, if any
		# if new == '', remove any existing link
		# otherwise, remove old and set new link
		srcanchor = self.toplevel.links.wholenodeanchor(self.node, notransaction = 1, create = new)
		if not srcanchor:
			# no whole node anchor, and we didn't have to create one
			return None
		links = self.context.hyperlinks.findsrclinks(srcanchor)
		if links and new is not None:
			# there is a link, and we want to replace or delete it
			self.editmgr.dellink(links[0])
			links = []
		if not links:
			if new is None:
				return None
			if not new:
				# remove the anchor since it isn't used
				alist = MMAttrdefs.getattr(self.node, 'anchorlist')[:]
				for i in range(len(alist)):
					if alist[i][A_TYPE] == ATYPE_WHOLE:
						del alist[i]
						break
				self.editmgr.setnodeattr(self.node, 'anchorlist', alist)
				return None
			link = srcanchor, new, DIR_1TO2, TYPE_JUMP
			self.editmgr.addlink(link)
		else:
			link = links[0]
		dstanchor = link[1]
		if type(dstanchor) == type(''):
			# external link
			return dstanchor
		return '<Hyperlink within document>'	# place holder for internal link

	def __findanchors(self):
		alist = MMAttrdefs.getattr(self.node, 'anchorlist')
		anchors = {}
		uid = self.node.GetUID()
		hlinks = self.context.hyperlinks
		for aid, atype, aargs, times in alist:
			links = []
			if atype == ATYPE_DEST:
				# don't show destination-only anchors
				continue
			for a1, a2, ldir, ltype in hlinks.findsrclinks((uid, aid)):
				links.append((a2, ldir, ltype))
			links.sort()
			times = times[0], times[1] - times[0]
			anchors[aid] = atype, aargs, times, links
		return anchors

	def __setanchors(self, newanchors):
		node = self.node
		uid = node.GetUID()
		hlinks = self.context.hyperlinks
		linkview = self.toplevel.links
		editmgr = self.editmgr
		anchorlist = MMAttrdefs.getattr(node, 'anchorlist')[:]
		newlinks = []
		oldanchors = self.__findanchors()
		oldanchonames = oldanchors.keys()
		dstlinks = {}
		for aid in oldanchors.keys():
			anchor = uid, aid
			for i in range(len(anchorlist)):
				if anchorlist[i][A_ID] == aid:
					del anchorlist[i]
					break
			for link in hlinks.findsrclinks(anchor):
				editmgr.dellink(link)
			dstlinks[aid] = hlinks.finddstlinks(anchor)
			for link in dstlinks[aid]:
				editmgr.dellink(link)
			if anchor in linkview.interesting:
				linkview.interesting.remove(anchor)
		rename = {}
		for aid, a in newanchors.items():
			if len(a) > 4 and a[4]:
				rename[a[4]] = aid
		for aid, a in newanchors.items():
			anchor = uid, aid
			oldname = None
			atype, aargs, times, links = a[:4]
			times = times[0], times[0] + times[1]
			if len(a) > 4:
				oldname = a[4]
			anchorlist.append((aid, atype, aargs, times))
			if links:
				if anchor in linkview.interesting:
					linkview.interesting.remove(anchor)
				for link in links:
					editmgr.addlink((anchor,) + link)
			else:
				linkview.set_interesting(anchor)
			for a1, a2, dir, type in dstlinks.get(oldname, []):
				# check whether src anchor renamed
				if a1[0] == uid:
					a1 = uid, rename.get(a1[1], a1[1])
					# check whether src anchor deleted
					if not newanchors.has_key(a1[1]):
						continue
				editmgr.addlink((a1, anchor, dir, type))
		editmgr.setnodeattr(node, 'anchorlist', anchorlist or None)

	def getattr(self, name): # Return the attribute or a default
		if name == '.hyperlink':
			return self.__findlink() or ''
		if name == '.type':
			return self.node.GetType()
		if name == '.values':
			return self.node.GetValues()
		if name == '.anchorlist':
			return self.__findanchors()
		return MMAttrdefs.getattr(self.node, name)

	def getvalue(self, name): # Return the raw attribute or None
		if name == '.hyperlink':
			return self.__findlink()
		if name == '.type':
			return self.node.GetType()
		if name == '.values':
			return self.node.GetValues() or None
		if name == '.anchorlist':
			return self.__findanchors() or None
		return self.node.GetRawAttrDef(name, None)

	def getdefault(self, name): # Return the default or None
		if name == '.hyperlink':
			return None
		if name == '.type':
			return None
		if name == '.values':
			return None
		if name == '.anchorlist':
			return None
		return MMAttrdefs.getdefattr(self.node, name)

	def setattr(self, name, value):
		if name == '.hyperlink':
			self.__findlink(value)
			return
		if name == '.type':
			if self.node.GetType() == 'imm' and value != 'imm':
				self.editmgr.setnodevalues(self.node, [])
			self.editmgr.setnodetype(self.node, value)
			return
		if name == '.values':
			# ignore value if not immediate node
			if self.node.GetType() == 'imm':
				self.editmgr.setnodevalues(self.node, value)
			return
		if name == '.anchorlist':
			self.__setanchors(value)
			return
		self.editmgr.setnodeattr(self.node, name, value)

	def delattr(self, name):
		if name == '.hyperlink':
			self.__findlink('')
			return
		if name == '.values':
			self.editmgr.setnodevalues(self.node, [])
			return
		if name == '.anchorlist':
			self.__setanchors({})
			return
		self.editmgr.setnodeattr(self.node, name, None)

	def delete(self):
		editmgr = self.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.delnode(self.node)
		editmgr.commit()

	#
	# Return a list of attribute names that make sense for this node,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		import settings
		lightweight = features.lightweight
		# Tuples are optional names and will be removed if they
		# aren't set
		namelist = [
			'name', ('file',),	# From nodeinfo window
			'.type',
			('terminator',),
			'begin', ('duration',), 'loop',	# Time stuff
			('clipbegin',), ('clipend',),	# More time stuff
			'title', 'abstract', ('alt',), ('longdesc',), 'author',
			'copyright', 'comment',
			'layout', ('u_group',),
			('mimetype',),	# XXXX Or should this be with file?
			'system_bitrate', 'system_captions',
			'system_language', 'system_overdub_or_caption',
			'system_required', 'system_screen_size',
			'system_screen_depth',
			]
		ntype = self.node.GetType()
		ctype = self.node.GetChannelType()
		if ntype in leaftypes or not lightweight:
			namelist[1:1] = ['channel']
		if ntype == 'bag':
			namelist.append('bag_index')
		if ntype == 'par':
			namelist.append('terminator')
		if ntype in ('par', 'seq'):
			namelist.append('duration')
		if ntype == 'alt':
			namelist.remove('begin')
			namelist.remove('loop')
		if ntype in leaftypes:
			namelist.append('alt')
			namelist.append('longdesc')
			if lightweight and ChannelMap.isvisiblechannel(ctype):
				namelist.append('.hyperlink')
				
			# specific time preference
			namelist.append('immediateinstantiationmedia')
			namelist.append('bitratenecessary')
			namelist.append('systemmimetypesupported')
			namelist.append('attachtimebase')
			namelist.append('qtchapter')
			namelist.append('qtcompositemode')
			
		if ntype == 'imm':
			namelist.append('.values')
		if 'layout' in namelist and not self.context.layouts:
			# no sense bothering the user with an attribute that
			# doesn't do anything...
			namelist.remove('layout')
		# Get the channel class (should be a subroutine!)
		if ChannelMap.channelmap.has_key(ctype):
			cclass = ChannelMap.channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.node_attrs
			if cmifmode():
				for name in cclass.chan_attrs:
					if name in namelist: continue
					defn = MMAttrdefs.getdef(name)
					if defn[5] == 'channel':
						namelist.append(name)
		# Merge in nonstandard attributes (except synctolist!)
		extras = []
		for name in self.node.GetAttrDict().keys():
			if name not in namelist and \
				     MMAttrdefs.getdef(name)[3] <> 'hidden':
				extras.append(name)
		extras.sort()
		namelist = namelist + extras
		retlist = []
		for name in namelist:
			if name in retlist:
				continue
			if type(name) == type(()):
				if name[0] in namelist:
					# It is in the list, insert it here
					retlist.append(name[0])
				else:
					# Not in the list for this node, skip
					pass
			else:
				retlist.append(name)
		if not lightweight and ntype in leaftypes \
		   and sys.platform in ('win32', 'mac'): # XXX until implemented on other platforms
			retlist.append('.anchorlist')
		return retlist

	def getdef(self, name):
		if name == '.hyperlink':
			return (('string', None), '',
				'Hyperlink', 'default',
				'Links within the presentation or to another SMIL document',
				'raw', flags.FLAG_ALL)
		if name == '.type':
			return (('string', None), '',
				'Node type', 'nodetype',
				'Node type', 'raw', flags.FLAG_ALL)
		if name == '.values':
			return (('string', None), '',
				'Content', 'text',
				'Data for node', 'raw', flags.FLAG_ALL)
		if name == '.anchorlist':
			# our own version of the anchorlist:
			# [(AnchorID, AnchorType, AnchorArgs, AnchorTimes, LinkList) ... ]
			# the LinkList is a list of hyperlinks, each a tuple:
			# (Anchor, Dir, Type)
			# where Anchor is either a (NodeID,AnchorID) tuple or
			# a string giving the external destination
			return (('list', ('enclosed', ('tuple', [('any', None), ('int', None), ('enclosed', ('list', ('any', None))), ('enclosed', ('tuple', [('float', 0), ('float', 0)])), ('enclosed', ('list', ('any', None)))]))), [],
				'Anchors', '.anchorlist',
				'List of anchors on this node', 'raw', flags.FLAG_ALL)
		return MMAttrdefs.getdef(name)

class SlideWrapper(NodeWrapper):
	def attrnames(self):
		import realsupport
		tag = self.node.GetAttrDict()['tag']
		if tag == 'fill':
			namelist = ['color', 'displayfull', 'subregionxy',
				    'subregionwh', 'start']
		elif tag in ('fadein', 'crossfade', 'wipe'):
			namelist = ['file', 'caption', 'fullimage', 'imgcropxy',
				    'imgcropwh', 'aspect',
				    'displayfull', 'subregionxy',
				    'subregionwh', 'start',
				    'tduration', 'maxfps', 'href',
				    'project_quality', 'project_convert']
			if tag == 'wipe':
				namelist.append('direction')
				namelist.append('wipetype')
			if tag == 'fadein':
				namelist = namelist + \
					   ['fadeout', 'fadeouttime',
					    'fadeoutcolor', 'fadeoutduration']
		elif tag == 'fadeout':
			namelist = ['color', 'subregionxy', 'displayfull',
				    'subregionwh', 'start',
				    'tduration', 'maxfps']
		elif tag == 'viewchange':
			namelist = ['fullimage', 'imgcropxy', 'imgcropwh',
				    'displayfull',
				    'subregionxy', 'subregionwh',
				    'start', 'tduration',
				    'maxfps']
		else:
			namelist = []
		namelist.insert(0, 'tag')
		return namelist

	def getdefault(self, name): # Return the default or None
		if name == 'color':
			return MMAttrdefs.getattr(self.node.GetParent(), 'bgcolor')
		else:
			return NodeWrapper.getdefault(self, name)

	def commit(self):
		node = self.node
		attrdict = node.GetAttrDict()
		if (attrdict.get('displayfull', 1) or
		    attrdict.get('fullimage', 1)) and \
		   attrdict['tag'] in ('fadein', 'crossfade', 'wipe') and \
		   attrdict.get('file'):
			import MMurl, Sizes
			url = attrdict['file']
			url = node.GetContext().findurl(url)
			w,h = Sizes.GetSize(url)
			if w != 0 and h != 0:
				if attrdict.get('displayfull', 1):
					attrdict['subregionwh'] = w, h
				if attrdict.get('fullimage', 1):
					attrdict['imgcropwh'] = w, h
		NodeWrapper.commit(self)


class ChannelWrapper(Wrapper):
	def __init__(self, toplevel, channel):
		self.channel = channel
		Wrapper.__init__(self, toplevel, channel.context)

	def __repr__(self):
		return '<ChannelWrapper, name=' + `self.channel.name` + '>'

	def close(self):
		del self.channel.attreditor
		del self.channel
		Wrapper.close(self)

	def stillvalid(self):
		return self.channel.stillvalid()

	def maketitle(self):
		return 'Properties of channel ' + self.channel.name

	def getattr(self, name):
		if name == '.cname': return self.channel.name
		if self.channel.has_key(name):
			return self.channel[name]
		else:
			return MMAttrdefs.getdef(name)[1]

	def getvalue(self, name): # Return the raw attribute or None
		if name == '.cname': return self.channel.name
		if self.channel.has_key(name):
			return self.channel[name]
		else:
			return None

	def getdefault(self, name): # Return the default or None
		if name == '.cname': return ''
		if name == 'bgcolor' and self.channel.has_key('base_window'):
			# special case code for background color
			ch = self.channel
			pname = ch['base_window']
			pchan = ch.context.channeldict[pname]
			try:
				return pchan['bgcolor']
			except KeyError:
				pass
		return MMAttrdefs.getdef(name)[1]

	def setattr(self, name, value):
		if name == '.cname':
			if self.channel.name != value and \
			   self.editmgr.context.getchannel(value):
				self.channel.attreditor.showmessage('Duplicate channel name (not changed)')
				return
			self.editmgr.setchannelname(self.channel.name, value)
		else:
			self.editmgr.setchannelattr(
				self.channel.name, name, value)

	def delattr(self, name):
		if name == '.cname':
			pass
			# Don't do this:
			# self.editmgr.setchannelname(self.channel.name, '')
		else:
			self.editmgr.setchannelattr( \
				  self.channel.name, name, None)

	def delete(self):
		editmgr = self.editmgr
		if not editmgr.transaction():
			return # Not possible at this time
		editmgr.delchannel(self.channel.name)
		editmgr.commit()
	#
	# Return a list of attribute names that make sense for this channel,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = ['.cname', 'type', 'title', 'comment']
		ctype = self.channel.get('type', 'unknown')
		if ChannelMap.channelmap.has_key(ctype):
			cclass = ChannelMap.channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.chan_attrs
			# And, for CMIF, add attributes that nodes inherit
			# from channel
			if cmifmode():
				for name in cclass.node_attrs:
					if name in namelist: continue
					defn = MMAttrdefs.getdef(name)
					if defn[5] == 'channel':
						namelist.append(name)
##			else:
##				# XXXX hack to get bgcolor included
##				namelist.append('bgcolor')
		# Merge in nonstandard attributes
		extras = []
		for name in self.channel.keys():
			if name not in namelist and \
				    MMAttrdefs.getdef(name)[3] <> 'hidden':
				extras.append(name)
		extras.sort()
		rv = namelist + extras
		# Remove some attributes if we are a base window, or if
		# we're in SMIL mode.
		base = self.channel.get('base_window')
		if base is None:
			if 'z' in rv: rv.remove('z')
			if 'base_winoff' in rv: rv.remove('base_winoff')
			if 'units' in rv: rv.remove('units')
			if 'transparent' in rv: rv.remove('transparent')
##		if not cmifmode():
##			if 'file' in rv: rv.remove('file')
##			if 'scale' in rv: rv.remove('scale')
		if ctype == 'layout' and not cmifmode():
			rv.remove('type')
		return rv
	#
	# Override three methods from Wrapper to fake channel name attribute
	#
	def getdef(self, name):
		if name == '.cname':
			# Channelname -- special case
			return (('name', ''), 'none',
				'Channel name', 'default',
				'Channel name', 'raw', flags.FLAG_ALL)
		return MMAttrdefs.getdef(name)

	def valuerepr(self, name, value):
		if name == '.cname': name = 'name'
		return MMAttrdefs.valuerepr(name, value)

	def parsevalue(self, name, str):
		if name == '.cname': name = 'name'
		return MMAttrdefs.parsevalue(name, str, self.context)



class DocumentWrapper(Wrapper):
	__stdnames = ['title', 'author', 'copyright', 'base']
	__publishnames = [
			'project_ftp_host', 'project_ftp_user', 'project_ftp_dir',
			'project_ftp_host_media', 'project_ftp_user_media', 'project_ftp_dir_media',
			'project_smil_url']
	__qtnames = ['autoplay', 'qttimeslider', 'qtnext', 'qtchaptermode', 'immediateinstantiation']

	def __init__(self, toplevel):
 		Wrapper.__init__(self, toplevel, toplevel.context)

	def __repr__(self):
		return '<DocumentWrapper instance, file=%s>' % self.toplevel.filename

	def close(self):
		del self.toplevel.attreditor
		Wrapper.close(self)

	def stillvalid(self):
		return self.toplevel in self.toplevel.main.tops

	def maketitle(self):
		import MMurl
		basename = MMurl.unquote(self.toplevel.basename)
		return 'Properties of document %s' % basename

	def getattr(self, name):	# Return the attribute or a default
		return self.getvalue() or ''

	def getvalue(self, name):	# Return the raw attribute or None
		if name == 'title':
			return self.context.title or None
		if name == 'base':
			return self.context.baseurl or None
		if self.context.attributes.has_key(name):
			return self.context.attributes[name]
		return None		# unrecognized

	def getdefault(self, name):
		attrdef = MMAttrdefs.getdef(name)
		return attrdef[1]
		
	def setattr(self, name, value):
		if name == 'title':
			self.context.title = value
		elif name == 'base':
			self.context.setbaseurl(value)
		else:
			self.context.attributes[name] = value

	def delattr(self, name):
		if name == 'title':
			self.context.title = None
		elif name == 'base':
			self.context.setbaseurl(None)
		elif self.context.attributes.has_key(name):
			del self.context.attributes[name]

	def delete(self):
		# shouldn't be called...
		pass

	def attrnames(self):
		attrs = self.context.attributes
		names = attrs.keys()
		for name in self.__stdnames + self.__publishnames + self.__qtnames:
			if attrs.has_key(name):
				names.remove(name)
		if not features.lightweight and \
		   features.compatibility != features.SMIL10 and \
		   not attrs.has_key('project_html_page'):
			names.append('project_html_page')
		elif (features.lightweight or
		      features.compatibility == features.SMIL10) and \
		     attrs.has_key('project_html_page'):
			names.remove('project_html_page')
		names.sort()
		if features.compatibility in (features.G2, features.QT):
			if features.compatibility == features.QT:
				names = self.__qtnames + names
			names = self.__publishnames + names
		return self.__stdnames + names
		
	def valuerepr(self, name, value):
		if name in ('title', 'base'):
			return MMAttrdefs.valuerepr(name, value)
		else:
			return value

	def parsevalue(self, name, str):
		if name in ('title', 'base'):
			return MMAttrdefs.parsevalue(name, str, self.context)
		else:
			return str


class PreferenceWrapper(Wrapper):
	__strprefs = {
		'system_language': 'Preferred language',
		}
	__intprefs = {
		'system_bitrate': 'Bitrate of connection with outside world',
		}
	__boolprefs = {
		'system_captions': 'Whether captions are to be shown',
		'cmif': 'Enable CMIF-specific extensions',
		'html_control': 'Choose between IE4 and WebsterPro HTML controls',
		}
	__specprefs = {
		'system_overdub_or_caption': 'Audible or visible "captions"',
		}

	def __init__(self, callback):
		self.__callback = callback
		self.toplevel = None

	def close(self):
		global prefseditor
		del self.__callback
		prefseditor = None

	def getcontext(self):
		raise RuntimeError, 'getcontext should not be called'

	def setwaiting(self):
		pass

	def register(self, object):
		pass

	def unregister(self, object):
		pass

	def transaction(self):
		return 1

	def commit(self):
		attr = None
		if prefseditor:
			attr = prefseditor.getcurattr()
		self.__callback()
		if prefseditor and attr:
			prefseditor.setcurattr(attr)

	def rollback(self):
		pass

	def getdef(self, name):
		defs = MMAttrdefs.getdef(name)
		if self.__strprefs.has_key(name):
			return (('string', None), self.getdefault(name),
				defs[2] or name, 'language',
				self.__strprefs[name], 'raw', flags.FLAG_ALL)
		elif self.__intprefs.has_key(name):
			return (('int', None), self.getdefault(name),
				defs[2] or name, 'bitrate',
				self.__intprefs[name], 'raw', flags.FLAG_ALL)
		elif self.__boolprefs.has_key(name):
			return (('bool', None), self.getdefault(name),
				defs[2] or name, 'default',
				self.__boolprefs[name], 'raw', flags.FLAG_ALL)
		elif self.__specprefs.has_key(name):
			return (('bool', None), self.getdefault(name),
				defs[2] or name, 'captionoverdub',
				self.__specprefs[name], 'raw', flags.FLAG_ALL)

	def stillvalid(self):
		return 1

	def maketitle(self):
		return 'GRiNS Preferences'

	def getattr(self, name):	# Return the attribute or a default
		import settings
		return settings.get(name)

	def getvalue(self, name):	# Return the raw attribute or None
		import settings
		return settings.get(name)

	def getdefault(self, name):
		import settings
		return settings.default_settings[name]

	def setattr(self, name, value):
		import settings
		settings.set(name, value)

	def delattr(self, name):
		import settings
		settings.set(name, self.getdefault(name))

	def delete(self):
		# shouldn't be called...
		pass

	def attrnames(self):
		attrs = self.__strprefs.keys() + self.__intprefs.keys() + self.__boolprefs.keys() + self.__specprefs.keys()
		if features.compatibility != features.CMIF:
			attrs.remove('cmif')
			if features.compatibility != features.SMIL10:
				attrs.remove('html_control')
		if os.name in ('posix', 'mac') and 'html_control' in attrs:
			attrs.remove('html_control')
		attrs.sort()
		return attrs

	def valuerepr(self, name, value):
		if self.__strprefs.has_key(name):
			return value
		elif self.__intprefs.has_key(name):
			return `value`
		elif self.__boolprefs.has_key(name):
			return ['off', 'on'][value]
		elif self.__specprefs.has_key(name):
			return value

	def parsevalue(self, name, str):
		if self.__strprefs.has_key(name):
			return value
		elif self.__intprefs.has_key(name):
			return string.atoi(value)
		elif self.__boolprefs.has_key(name):
			if str == 'on': return 1
			return 0
		elif self.__specprefs.has_key(name):
			return str


# Attribute editor class.

from AttrEditDialog import AttrEditorDialog, AttrEditorDialogField

class AttrEditor(AttrEditorDialog):
	def __init__(self, wrapper, new = 0, initattr = None, chtype = None):
		self.__new = new
		self.__chtype = chtype
		self.wrapper = wrapper
		wrapper.register(self)
		self.__open_dialog(initattr)

	def __open_dialog(self, initattr):
		import settings
		import compatibility
		wrapper = self.wrapper
		list = []
		allnamelist = wrapper.attrnames()
		namelist = []
		lightweight = features.lightweight
		if not lightweight:
			cmif = settings.get('cmif')
		else:
			cmif = 0
		for name in allnamelist:
			from flags import curflags
			fl = wrapper.getdef(name)[6]
			if fl & curflags() == 0:
				continue
#			if flags != 'light':
#				if lightweight or \
#				   (not cmif and flags == 'cmif'):
#					continue
			namelist.append(name)
			
		self.__namelist = namelist
		initattrinst = None
		for i in range(len(namelist)):
			name = namelist[i]
			typedef, defaultvalue, labeltext, displayername, \
				 helptext, inheritance, flags = \
				 wrapper.getdef(name)
			type = typedef[0]
			if displayername == 'file':
				C = FileAttrEditorField
			elif displayername == 'font':
				C = FontAttrEditorField
			elif displayername == 'color':
				C = ColorAttrEditorField
			elif displayername == 'layoutname':
				C = LayoutnameAttrEditorField
			elif displayername == 'channelname':
				C = ChannelnameAttrEditorField
			elif displayername == 'captionchannelname':
				C = CaptionChannelnameAttrEditorField
			elif displayername == 'basechannelname':
				C = BaseChannelnameAttrEditorField
			elif displayername == 'childnodename':
				C = ChildnodenameAttrEditorField
			elif displayername == 'channeltype':
				C = ChanneltypeAttrEditorField
			elif displayername == 'units':
				C = UnitsAttrEditorField
			elif displayername == 'termnodename':
				C = TermnodenameAttrEditorField
			elif displayername == 'transparency':
				C = TransparencyAttrEditorField
			elif displayername == 'usergroup':
				C = UsergroupAttrEditorField
			elif displayername == 'transition':
				C = TransitionAttrEditorField
			elif displayername == 'direction':
				C = WipeDirectionAttrEditorField
			elif displayername == 'wipetype':
				C = WipeTypeAttrEditorField
			elif displayername == 'subregionanchor':
				C = AnchorTypeAttrEditorField
			elif displayername == 'targets':
				C = RMTargetsAttrEditorField
			elif displayername == 'audiotype':
				C = RMAudioAttrEditorField
			elif displayername == 'videotype':
				C = RMVideoAttrEditorField
			elif displayername == 'nodetype':
				C = NodeTypeAttrEditorField
			elif displayername == 'text':
				C = TextAttrEditorField
			elif displayername == 'qtchaptermode':
				C = QTChapterModeEditorField
			elif displayername == 'bool3':
				C = BoolAttrEditorFieldWithDefault
			elif displayername == 'captionoverdub':
				C = CaptionOverdubAttrEditorField
			elif displayername == 'captionoverdub3':
				C = CaptionOverdubAttrEditorFieldWithDefault
			elif displayername == 'language':
				C = LanguageAttrEditorField
			elif displayername == 'language3':
				C = LanguageAttrEditorFieldWithDefault
			elif displayername == 'bitrate':
				C = BitrateAttrEditorField
			elif displayername == 'bitrate3':
				C = BitrateAttrEditorFieldWithDefault
			elif displayername == 'quality':
				C = QualityAttrEditorField
			elif displayername == '.anchorlist':
				C = AnchorlistAttrEditorField
			elif displayername == 'scale':
				C = ScaleAttrEditorField
			elif type == 'bool':
				C = BoolAttrEditorField
			elif type == 'name':
				C = NameAttrEditorField
			elif type == 'string':
				C = StringAttrEditorField
			elif type == 'int':
				C = IntAttrEditorField
			elif type == 'float':
				C = FloatAttrEditorField
			elif type == 'tuple':
				C = TupleAttrEditorField
			else:
				C = AttrEditorField
			b = C(self, name, labeltext or name)
			list.append(b)
			if initattr and initattr == name:
				initattrinst = b
		self.attrlist = list
		AttrEditorDialog.__init__(self, wrapper.maketitle(), list, wrapper.toplevel, initattrinst)

	def _findattr(self, attr):
		for b in self.attrlist:
			if b.getname() == attr:
				return b

	def resetall(self):
		for b in self.attrlist:
			b.reset_callback()

	def restore_callback(self):
		for b in self.attrlist:
			b.setvalue(b.valuerepr(None))

	def close(self):
		AttrEditorDialog.close(self)
		for b in self.attrlist:
			b.close()
		self.wrapper.unregister(self)
		if self.__new:
			self.wrapper.delete()
		self.wrapper.close()
		del self.attrlist
		del self.wrapper

	def cancel_callback(self):
		self.close()

	def ok_callback(self):
		if not self.apply_callback():
			self.close()

	def apply_callback(self):
		self.__new = 0
		# first collect all changes
		dict = {}
		newchannel = None
		for b in self.attrlist:
			name = b.getname()
			str = b.getvalue()
			if str != b.getcurrent():
				if hasattr(b, 'newchannels') and \
				   str not in self.wrapper.getcontext().channelnames:
					newchannel = str
					try:
						b.newchannels.remove(str)
					except ValueError:
						# probably shouldn't happen...
						pass
					dict[name] = str
					continue
				try:
					value = b.parsevalue(str)
				except:
					typedef = self.wrapper.getdef(name)[0]
					exp = typedef[0]
					if exp == 'int':
						exp = 'integer'
					if exp == 'tuple':
						exp = 'list of values: '
						for e in typedef[1]:
							exp = exp + ' ' + e[0]
					if exp[0] in 'aeiou':
						n = 'n'
					else:
						n = ''
					if name == 'duration' or name == 'loop':
						exp = exp + " or `indefinite'"
					self.showmessage('%s: value should be a%s %s' % (b.getlabel(), n, exp), mtype = 'error')
					return 1
				if name == 'file' and not self.checkurl(value):
					self.showmessage('URL not compatible with channel', mtype = 'error')
					return 1
				if name == 'href' and value not in self.wrapper.getcontext().externalanchors:
					self.wrapper.getcontext().externalanchors.append(value)
				dict[name] = value
		if not dict and not newchannel:
			# nothing to change
			return
		if not self.wrapper.transaction():
			# can't do a transaction
			return 1
		# this may take a while...
		self.wrapper.setwaiting()
		if newchannel:
			self.newchannel(newchannel)
		# update node type first
		if dict.has_key('.type'):
			value = dict['.type']
			del dict['.type']
			self.wrapper.setattr('.type', value)
		for name, value in dict.items():
			if value is None:
				self.wrapper.delattr(name)
			else:
				self.wrapper.setattr(name, value)
		self.wrapper.commit()

	def checkurl(self, url):
		import settings
		if not features.lightweight:
			return 1
		if self.wrapper.__class__ is SlideWrapper:
			# node is a slide
			import MMmimetypes
			mtype = MMmimetypes.guess_type(url)[0]
			if not mtype:
				# unknown type, not compatible
				return 0
			# compatible if image and not RealPix
			return mtype[:5] == 'image' and string.find(mtype, 'real') < 0
		b = self._findattr('channel')
		if b is not None:
			str = b.getvalue()
			try:
				chan = b.parsevalue(str)
			except:
				chan = ''
			return chan in self.wrapper.getcontext().compatchannels(url)
		# not found, assume compatible
		return 1

	def newchannel(self, channelname):
		em = self.wrapper.editmgr
		context = self.wrapper.getcontext()
		b = self._findattr('file')
		if b:
			url = b.getvalue()
		else:
			url = ''
		root = None
		for key, val in context.channeldict.items():
			if val.get('base_window') is None:
				# we're looking at a top-level channel
				if root is None:
					# first one
					root = key
				else:
					# multiple root windows
					root = ''
		index = len(context.channelnames)
		em.addchannel(channelname, index, self.guesstype(url))
		ch = context.channeldict[channelname]
		if root:
			ch['base_window'] = root
		if ChannelMap.isvisiblechannel(ch['type']):
			units = ch.get('units', windowinterface.UNIT_SCREEN)
			if units == windowinterface.UNIT_PXL:
				if url:
					import Sizes
					w, h = Sizes.GetSize(context.findurl(url))
				else:
					w = h = 0
				if w == 0:
					w = 100 # default size
				if h == 0:
					h = 100 # default size
				ch['base_winoff'] = 0,0,w,h
			elif units == windowinterface.UNIT_SCREEN:
				ch['base_winoff'] = 0,0,.2,.2
		# if the node belongs to a layout, add the new channel
		# to that layouf
		layout = MMAttrdefs.getattr(self.wrapper.node, 'layout')
		if layout != 'undefined' and context.layouts.has_key(layout):
			em.addlayoutchannel(layout, ch)

	def guesstype(self, url):
		# guess channel type from URL
		b = self._findattr('.type')
		if b:
			ntype = b.getvalue()
		else:
			# can't determine node type
			return 'null'
		if ntype == 'imm':
			# assume all immediate nodes are text nodes
			return 'text'
		if ntype != 'ext':
			# interior node, doesn't make much sense
			return 'null'
		if not url:
			return self.__chtype or 'null'
		import MMmimetypes
		mtype = MMmimetypes.guess_type(url)[0]
		if mtype is None:
			# just guessing now...
			# Most often, this is because there was no file name.
			# Webservers will then generally return an HTML page.
			import settings
			if features.compatibility == features.G2 or features.compatibility == features.QT:
				# G2 and QuickTime players don't do HTML
				return 'text'
			return 'html'
		chtypes = ChannelMime.MimeChannel.get(mtype)
		if not chtypes:
			# fallback
			return 'text'
		if len(chtypes) == 1:
			return chtypes[0]
		# Currently the only reason why there might be more than one
		# channel type is because we have a RealMedia file.  We will
		# therefore now check whether the file has video in it or not.
		info = realsupport.getinfo(url)
		if not info:
			return 'video'
		if info.has_key('width'):
			return 'video'
		return 'sound'

	#
	# EditMgr interface
	#
	def transaction(self):
		return 1

	def commit(self):
		if not self.wrapper.stillvalid():
			self.close()
		else:
			namelist = self.wrapper.attrnames()
			if namelist != self.__namelist:
				# re-open with possibly different size
				attr = self.getcurattr()
				if attr:
					attr = attr.getname()
				AttrEditorDialog.close(self)
				for b in self.attrlist:
					b.close()
				del self.attrlist
				self.__open_dialog(attr)
			else:
				a = self.getcurattr()
##				self.fixvalues()
				self.resetall()
				self.settitle(self.wrapper.maketitle())
				self.setcurattr(a)

	def rollback(self):
		pass

	def kill(self):
		self.close()

class AttrEditorField(AttrEditorDialogField):
	type = 'string'
	nodefault = 0

	def __init__(self, attreditor, name, label):
		self.__name = name
		self.label = label
		self.attreditor = attreditor
		self.wrapper = attreditor.wrapper
		self.__attrdef = self.wrapper.getdef(name)

	def __repr__(self):
		return '<%s instance, name=%s>' % (self.__class__.__name__,
						   self.__name)

	def close(self):
		AttrEditorDialogField.close(self)
		del self.attreditor
		del self.wrapper
		del self.__attrdef

	def getname(self):
		return self.__name

	def gettype(self):
		return self.type

	def getlabel(self):
		return self.label

	def gethelptext(self):
		return '%s\ndefault: %s' % (self.__attrdef[4], self.getdefault())
##		return 'atribute: %s\n' \
##		       'default: %s\n' \
##		       '%s' % (self.__name, self.getdefault(),
##			       self.__attrdef[4])

	def gethelpdata(self):
		return self.__name, self.getdefault(), self.__attrdef[4]

	def getcurrent(self):
		return self.valuerepr(self.wrapper.getvalue(self.__name))

	def getdefault(self):
		return self.valuerepr(self.wrapper.getdefault(self.__name))

	def valuerepr(self, value):
		"""Return string representation of value."""
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return ''
		return self.wrapper.valuerepr(self.__name, value)

	def parsevalue(self, str):
		"""Return internal representation of string."""
		if str == '':
			return None
		return self.wrapper.parsevalue(self.__name, str)

	def reset_callback(self):
		self.setvalue(self.getcurrent())

	def help_callback(self):
		self.attreditor.showmessage(self.gethelptext())

class IntAttrEditorField(AttrEditorField):
	type = 'int'

	def valuerepr(self, value):
		if value == 0 and self.getname() == 'loop':
			return 'indefinite'
		return AttrEditorField.valuerepr(self, value)

	def parsevalue(self, str):
		if str == 'indefinite' and self.getname() == 'loop':
			return 0
		return AttrEditorField.parsevalue(self, str)

class FloatAttrEditorField(AttrEditorField):
	type = 'float'

	def valuerepr(self, value):
		if value == -1 and self.getname() == 'duration':
			return 'indefinite'
		return AttrEditorField.valuerepr(self, value)

	def parsevalue(self, str):
		if str == 'indefinite' and self.getname() == 'duration':
			return -1.0
		return AttrEditorField.parsevalue(self, str)

class StringAttrEditorField(AttrEditorField):
	def valuerepr(self, value):
		"""Return string representation of value."""
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return ''
		return value

	def parsevalue(self, str):
		"""Return internal representation of string."""
		if str == '':
			return None
		return str

class NameAttrEditorField(StringAttrEditorField):
	pass

class FileAttrEditorField(StringAttrEditorField):
	type = 'file'

	def browser_callback(self):
		import os, MMurl, urlparse
		cwd = self.wrapper.toplevel.dirname
		if cwd:
			cwd = MMurl.url2pathname(cwd)
			if not os.path.isabs(cwd):
				cwd = os.path.join(os.getcwd(), cwd)
		else:
			cwd = os.getcwd()
		url = self.getvalue()
		if url == '' or url == '/dev/null':
			dir, file = cwd, ''
		else:
			if hasattr(self.wrapper, 'node'):
				node = self.wrapper.node
				url = node.GetContext().findurl(url)
			utype, host, path, params, query, fragment = urlparse.urlparse(url)
			if (utype and utype != 'file') or \
			   (host and host != 'localhost'):
				dir, file = cwd, ''
			else:
				file = MMurl.url2pathname(path)
				file = os.path.join(cwd, file)
				if os.path.isdir(file):
					dir, file = file, ''
				else:
					dir, file = os.path.split(file)
		if self.wrapper.__class__ is SlideWrapper:
			chtype = 'image'
		else:
			chtype = None
			b = self.attreditor._findattr('channel')
			if b is not None:
				ch = self.wrapper.context.getchannel(b.getvalue())
				if ch:
					chtype = ch['type']
		mtypes = ChannelMime.ChannelMime.get(chtype, [])
		if chtype:
			mtypes = ['/%s file' % string.capitalize(chtype)] + mtypes
		windowinterface.FileDialog('Choose File for ' + self.label,
					   dir, mtypes, file, self.setpathname, None,
					   existing=1)

	def setpathname(self, pathname):
		import MMurl
		if not pathname:
			url = ''
		else:
			url = MMurl.pathname2url(pathname)
			url = self.wrapper.context.relativeurl(url)
		if not self.attreditor.checkurl(url):
			self.attreditor.showmessage('file not compatible with channel', mtype = 'error')
			return
		self.setvalue(url)
		if self.wrapper.__class__ is SlideWrapper and url:
			import HierarchyView
			node = self.wrapper.node
			pnode = node.GetParent()
			start, minstart = HierarchyView.slidestart(pnode, url, pnode.children.index(node))
			b = self.attreditor._findattr('start')
			if b is not None:
				str = b.getvalue()
				try:
					value = b.parsevalue(str) or 0
				except:
					value = 0
				if minstart - start > value:
					b.setvalue(b.valuerepr(minstart-start))

class TextAttrEditorField(AttrEditorField):
	type = 'text'

	def valuerepr(self, value):
		"""Return string representation of value."""
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return ''
		return string.join(value, '\n')

	def parsevalue(self, str):
		"""Return internal representation of string."""
		if str == '':
			return None
		return string.split(str, '\n')

class TupleAttrEditorField(AttrEditorField):
	type = 'tuple'

	def valuerepr(self, value):
		if type(value) is type(''):
			return value
		return AttrEditorField.valuerepr(self, value)

from colors import colors
class ColorAttrEditorField(TupleAttrEditorField):
	type = 'color'
	def parsevalue(self, str):
		str = string.lower(string.strip(str))
		if colors.has_key(str):
			return colors[str]
		if str[:1] == '#':
			rgb = []
			if len(str) == 4:
				for i in range(1, 4):
					rgb.append(string.atoi(str[i], 16) * 16)
			elif len(str) == 7:
				for i in range(1, 7, 2):
					rgb.append(string.atoi(str[i:i+2], 16))
			elif len(str) == 13:
				for i in range(1, 13, 4):
					rgb.append(string.atoi(str[i:i+4], 16)/256)
			else:
				raise RuntimeError, 'Bad color specification'
			str = ''
			for c in rgb:
				str = str + ' ' + `c`
		return TupleAttrEditorField.parsevalue(self, str)

	def valuerepr(self, value):
		for name, rgb in colors.items():
			if value == rgb:
				return name
		return TupleAttrEditorField.valuerepr(self, value)

class PopupAttrEditorField(AttrEditorField):
	# A choice menu choosing from a list -- base class only
	type = 'option'

	def getoptions(self):
		# derived class overrides this to defince the choices
		return [DEFAULT]

	def parsevalue(self, str):
		if str == DEFAULT:
			return None
		return str

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return DEFAULT
		return value

class PopupAttrEditorFieldWithUndefined(PopupAttrEditorField):
	# This class differs from the one above in that when a value
	# does not occur in the list of options, valuerepr will return
	# 'undefined'.

	def getoptions(self):
		# derived class overrides this to defince the choices
		return [DEFAULT, UNDEFINED]

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return DEFAULT
		options = self.getoptions()
		if value not in options:
			return UNDEFINED
		return value

	def reset_callback(self):
		self.recalcoptions()

class PopupAttrEditorFieldNoDefault(PopupAttrEditorField):
	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		if val is None:
			return self.getdefault()
		return self.valuerepr(val)

class BoolAttrEditorField(PopupAttrEditorField):
	__offon = ['off', 'on']
	default = 'Not set'
	nodefault = 1

	def parsevalue(self, str):
		if str == self.default:
			return None
		return self.__offon.index(str)

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.default
		return self.__offon[value]

	def getoptions(self):
		return self.__offon

class BoolAttrEditorFieldWithDefault(BoolAttrEditorField):
	nodefault = 0
	def getoptions(self):
		return [self.default] + BoolAttrEditorField.getoptions(self)

class UnitsAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['mm', 'relative', 'pixels']
	__valuesmap = [windowinterface.UNIT_MM, windowinterface.UNIT_SCREEN,
		       windowinterface.UNIT_PXL]

	# Choose from a list of unit types
	def getoptions(self):
		return self.__values

	def parsevalue(self, str):
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		return self.__values[self.__valuesmap.index(value)]

class ScaleAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['actual size', 'show whole image', 'fill whole region']
	__valuesmap = [1, 0, -1]

	# Choose from a list of unit types
	def getoptions(self):
		return self.__values

	def parsevalue(self, str):
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		return self.__values[self.__valuesmap.index(value)]

class QTChapterModeEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['all', 'clip']
	__valuesmap = [0, 1]

	# Choose from a list of unit types
	def getoptions(self):
		return self.__values

	def parsevalue(self, str):
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		return self.__values[self.__valuesmap.index(value)]
		
	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		if val is None:
			return self.wrapper.getdefault(self.getname())
		return self.valuerepr(val)

class CaptionOverdubAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['caption', 'overdub']
	nodefault = 1

	def getoptions(self):
		return self.__values

class CaptionOverdubAttrEditorFieldWithDefault(PopupAttrEditorField):
	__values = ['caption', 'overdub']
	default = 'Not set'
	nodefault = 0

	def parsevalue(self, str):
		if str == self.default:
			return None
		return str

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.default
		return value

	def getoptions(self):
		return [self.default] + self.__values

class LanguageAttrEditorField(PopupAttrEditorField):
	from languages import *
	default = 'Not set'
	nodefault = 1

	def getoptions(self):
		options = self.l2a.keys()
		options.sort()
		return options

	def parsevalue(self, str):
		if str == self.default:
			return None
		return self.l2a[str]

	def valuerepr(self, value):
		if not value:
			if self.nodefault:
				return self.getdefault()
			return self.default
		return self.a2l[value]

class LanguageAttrEditorFieldWithDefault(LanguageAttrEditorField):
	nodefault = 0
	def getoptions(self):
		options = LanguageAttrEditorField.getoptions(self)
		return [self.default] + options

class BitrateAttrEditorField(PopupAttrEditorField):
	__values = [14400, 19200, 28800, 33600, 34400, 57600, 115200, 262200, 307200, 524300, 1544000, 10485800]
	__strings = ['14.4K Modem', '19.2K Connection', '28.8K Modem', '33.6K Modem', '56K Modem', '56K Single ISDN', '112K Dual ISDN', '256Kbps DSL/Cable', '300Kbps DSL/Cable', '512Kbps DSL/Cable', 'T1 / LAN', '10Mbps LAN']
	default = 'Not set'
	nodefault = 1

	def parsevalue(self, str):
		if str == self.default:
			return None
		return self.__values[self.__strings.index(str)]

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.default
		str = self.__strings[0]
		for i in range(len(self.__values)):
			if self.__values[i] <= value:
				str = self.__strings[i]
		return str

	def getoptions(self):
		return self.__strings

	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		if val is None:
			return self.getdefault()
		return self.valuerepr(val)

class BitrateAttrEditorFieldWithDefault(BitrateAttrEditorField):
	nodefault = 0

	def getoptions(self):
		return [self.default] + BitrateAttrEditorField.getoptions(self)

	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		if val is None:
			return self.default
		return self.valuerepr(val)

class QualityAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['low', 'normal', 'high', 'highest']
	__valuesmap = [20, 50, 75, 90]

	# Choose from a list of unit types
	def getoptions(self):
		return self.__values

	def parsevalue(self, str):
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		return self.__values[self.__valuesmap.index(value)]

class TransitionAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['fill', 'fadein', 'fadeout', 'crossfade', 'wipe', 'viewchange']

	def getoptions(self):
		return self.__values

class WipeDirectionAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['left', 'right', 'up', 'down']

	def getoptions(self):
		return self.__values

class WipeTypeAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['normal', 'push']

	def getoptions(self):
		return self.__values

class AnchorTypeAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['top-left', 'top-center', 'top-right',
		    'center-left', 'center', 'center-right',
		    'bottom-left', 'bottom-center', 'bottom-right']

	def getoptions(self):
		return self.__values

class TransparencyAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['never', 'when empty', 'always']
	__valuesmap = [0, -1, 1]

	# Choose from a list of unit types
	def getoptions(self):
		return self.__values

	def parsevalue(self, str):
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		return self.__values[self.__valuesmap.index(value)]

class RMTargetsAttrEditorField(PopupAttrEditorField):
	# Note: these values come from the producer module, but we don't want to import
	# that here
	__values = ['28k8 modem', '56k modem', 
		'Single ISDN', 'Double ISDN', 'Cable modem', 'LAN']

	# Choose from a list of unit types
	def getoptions(self):
##		return [DEFAULT] + self.__values
		return self.__values

	def parsevalue(self, str):
		if str == DEFAULT:
			str = '28k8 modem,56k modem'
		strs = string.split(str, ',')
		rv = 0
		for str in strs:
			rv = rv | (1 << self.__values.index(str))
		return rv

	def valuerepr(self, value):
		if value is None:
			value = 3	# '28k8 modem,56k modem'
		str = self.__values[0]	# XXX use lowest as default
		# XXX just the last one for now
		strs = []
		for i in range(len(self.__values)):
			if value & (1 << i):
				strs.append(self.__values[i])
		str = string.join(strs, ',')
		return str

class RMAudioAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['Voice', 'Voice and background music', 'Music (mono)', 'Music (stereo)']
	__valuesmap = [0, 1, 2, 3]

	# Choose from a list of unit types
	def getoptions(self):
		return self.__values

	def parsevalue(self, str):
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		return self.__values[self.__valuesmap.index(value)]

class RMVideoAttrEditorField(PopupAttrEditorFieldNoDefault):
	__values = ['Normal quality', 'Smoother motion', 'Sharper pictures', 'Slideshow']
	__valuesmap = [0, 1, 2, 3]

	# Choose from a list of unit types
	def getoptions(self):
		return self.__values

	def parsevalue(self, str):
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		return self.__values[self.__valuesmap.index(value)]

class LayoutnameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the current layout names
	def getoptions(self):
		list = self.wrapper.context.layouts.keys()
		list.sort()
		return [DEFAULT, UNDEFINED] + list

class ChannelnameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the current channel names
	def __init__(self, attreditor, name, label):
		self.newchannels = []
		self.__current = None
		PopupAttrEditorFieldWithUndefined.__init__(self, attreditor, name, label)

	def getoptions(self):
		import settings
		# channelnames1 -- compatible channels in node's layout
		# channelnames2 -- new channel
		# channelnames3 -- incompatible channels in node's layout
		# channelnames4 -- compatible channels not in node's layout
		# channelnames5 -- incompatible channels not in node's layout
		# In the lite version there are no layouts, so all channels
		# are in category 1 or 3.  Only channelnames1 is shown.
		ctx = self.wrapper.context
		node = self.wrapper.node
		chtype = node.GetChannelType()
		b = self.attreditor._findattr('file')
		if b is not None:
			url = b.getvalue()
		else:
			url = None
		chlist = ctx.compatchannels(url, chtype)
		lightweight = features.lightweight
		layoutchannels = {}
		if not lightweight:
			layout = MMAttrdefs.getattr(node, 'layout')
			if layout != UNDEFINED:
				for ch in ctx.layouts.get(layout, []):
					layoutchannels[ch.name] = 1
		channelnames1 = []
		channelnames2 = self.newchannels[:]
		channelnames3 = []
		channelnames4 = []
		channelnames5 = []
		for ch in ctx.channels:
			if lightweight or layoutchannels.has_key(ch.name):
				if ch.get('type','') != 'layout' and ch.name in chlist:
					channelnames1.append(ch.name)
				else:
					channelnames3.append(ch.name)
			else:
				if ch.get('type','') != 'layout' and ch.name in chlist:
					channelnames4.append(ch.name)
				else:
					channelnames5.append(ch.name)
		channelnames1.sort()
		channelnames2.sort()
		channelnames3.sort()
		channelnames4.sort()
		channelnames5.sort()
		if lightweight:
			if channelnames1:
				return channelnames1
			allchannelnames = [UNDEFINED]
			if channelnames3:
				allchannelnames.append(None)
				allchannelnames = allchannelnames + channelnames3
			return allchannelnames
		all = [UNDEFINED]
		if channelnames1:
			# add separator between lists
			if all:
				all.append(None)
			all = all + channelnames1
		if channelnames2:
			# add separator between lists
			if all:
				all.append(None)
			all = all + channelnames2
		if channelnames3:
			# add separator between lists
			if all:
				all.append(None)
			all = all + channelnames3
		if channelnames4:
			# add separator between lists
			if all:
				all.append(None)
			all = all + channelnames4
		if channelnames5:
			# add separator between lists
			if all:
				all.append(None)
			all = all + channelnames5
		if not self.newchannels:
			if all:
				all.append(None)
			all = all + [NEW_CHANNEL]
		return all

	def parsevalue(self, str):
		if str == UNDEFINED:
			return None
		return str

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return UNDEFINED
		return value

	def channelprops(self):
		ch = self.wrapper.context.getchannel(self.getvalue())
		if ch is not None:
			showchannelattreditor(self.wrapper.toplevel, ch)
			
	def channelexists(self, name):
		return self.wrapper.context.getchannel(name) is not None

	def newchannelname(self):
		base = 'NEW'
		i = 1
		name = base + `i`
		channeldict = self.wrapper.context.channeldict
		while channeldict.has_key(name):
			i = i+1
			name = base + `i`
		return name

	def getcurrent(self):
		if self.__current:
			return self.__current
		return PopupAttrEditorFieldWithUndefined.getcurrent(self)

	def newchan_callback(self, name = None):
		if not name:
			self.setvalue(self.getcurrent())
			return
		if name != UNDEFINED and name not in self.wrapper.context.channelnames:
			self.newchannels.append(name)
		self.__current = name
		self.recalcoptions()
		self.setvalue(name)
		self.__current = None
			
	def optioncb(self):
		if self.getvalue() == NEW_CHANNEL:
			windowinterface.settimer(0.01, (self.askchannelname, (self.newchannelname(),)))

class CaptionChannelnameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the current RealText channel names
	__nocaptions = 'No captions'

	def getoptions(self):
		import settings
		list = []
		ctx = self.wrapper.context
		chlist = ctx.compatchannels(None, 'RealText')
		chlist.sort()
		return [self.__nocaptions] + chlist

	def parsevalue(self, str):
		if str == self.__nocaptions:
			return None
		return str

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.__nocaptions
		return value

	def channelexists(self, name):
		return self.wrapper.context.getchannel(name) is not None

	def channelprops(self):
		ch = self.wrapper.context.getchannel(self.getvalue())
		if ch is not None:
			showchannelattreditor(self.wrapper.toplevel, ch)

class BaseChannelnameAttrEditorField(ChannelnameAttrEditorField):
	# Choose from the current channel names
	def getoptions(self):
		list = []
		ctx = self.wrapper.context
		chname = self.wrapper.channel.name
		for name in ctx.channelnames:
			if name == chname:
				continue
			ch = ctx.channeldict[name]
##			if ch.attrdict['type'] == 'layout':
			list.append(name)
		list.sort()
		return [DEFAULT, UNDEFINED] + list

	def channelprops(self):
		ch = self.wrapper.context.getchannel(self.getvalue())
		if ch is not None:
			showchannelattreditor(self.wrapper.toplevel, ch)

class UsergroupAttrEditorField(PopupAttrEditorFieldWithUndefined):
	def getoptions(self):
		list = self.wrapper.context.usergroups.keys()
		list.sort()
		return [DEFAULT, UNDEFINED] + list

class ChildnodenameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the node's children
	def getoptions(self):
		list = []
		for child in self.wrapper.node.GetChildren():
			try:
				list.append(child.GetAttr('name'))
			except NoSuchAttrError:
				pass
		list.sort()
		return [DEFAULT, UNDEFINED] + list

class TermnodenameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the node's children or the values LAST or FIRST
	def getoptions(self):
		list = []
		for child in self.wrapper.node.GetChildren():
			try:
				list.append(child.GetAttr('name'))
			except NoSuchAttrError:
				pass
		list.sort()
		return ['LAST', 'FIRST'] + list

	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		if val is None:
			return self.getdefault()
		return self.valuerepr(val)

class ChanneltypeAttrEditorField(PopupAttrEditorFieldNoDefault):
	# Choose from the standard channel types
	def getoptions(self):
		current = self.getcurrent()
		if features.lightweight:
			return [current]
		all = ChannelMap.getvalidchanneltypes()
		if not current in all:
			# Can happen if we open, say, a full-smil document
			# in the G2 editor
			all = all + [current]
		return all

class FontAttrEditorField(PopupAttrEditorField):
	# Choose from all possible font names
	def getoptions(self):
		fonts = windowinterface.fonts[:]
		fonts.sort()
		return [DEFAULT] + fonts

Alltypes = alltypes[:]
Alltypes[Alltypes.index('bag')] = 'choice'
Alltypes[Alltypes.index('alt')] = 'switch'
class NodeTypeAttrEditorField(PopupAttrEditorField):
	def getoptions(self):
		if cmifmode():
			options = Alltypes[:]
		else:
			options = Alltypes[:]
			options.remove('choice')
		ntype = self.wrapper.node.GetType()
		if ntype in interiortypes:
			if self.wrapper.node.GetChildren():
				options.remove('imm')
				options.remove('ext')
		elif ntype == 'imm' and self.wrapper.node.GetValues():
			options = ['imm']
		return options

	def parsevalue(self, str):
		if str == 'choice':
			return 'bag'
		if str == 'switch':
			return 'alt'
		return str

	def valuerepr(self, value):
		if value == 'bag':
			return 'choice'
		if value == 'alt':
			return 'switch'
		return value

class AnchorlistAttrEditorField(AttrEditorField):
	def parsevalue(self, str):
		return str

	def valuerepr(self, value):
		return value

