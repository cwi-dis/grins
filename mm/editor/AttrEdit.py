__version__ = "$Id$"

import windowinterface
import MMAttrdefs
import ChannelMap
import ChannelMime
from MMExc import *			# exceptions
import MMNode
from MMTypes import *
from Hlinks import DIR_1TO2, TYPE_JUMP, TYPE_FORK, A_SRC_PLAY, A_SRC_STOP, A_DEST_PLAY
import features
import string
import os
import sys
import flags
from fmtfloat import fmtfloat

DEFAULT = 'Default'
UNDEFINED = 'undefined'
NEW_REGION = 'New region...'

# There are two basic calls into this module (but see below for more):
# showattreditor(node) creates an attribute editor form for a node
# and hideattreditor(node) hides it again.  Since the editor may also
# hide itself, spurious hide calls are ignored; also, only one attribute
# editor is allowed per node, and extra show calls are also ignored
# (actually, this pops up the window, to draw the user's attention...).

def getwrapperclass(selvaluelist):
	if len(selvaluelist) != 1:
		return None
	selvalue = selvaluelist[0]
	if not hasattr(selvalue, 'getClassName'):
		print 'Focus items should have getClassName() method'
		return None
	className = selvalue.getClassName()
	if className == 'MMNode':
		ntype = selvalue.GetType()
		if ntype == 'anchor':
			wrapperclass = AnchorWrapper
		elif selvalue.GetChannelType() == 'animate' :
			wrapperclass = AnimationWrapper
		elif selvalue.GetChannelType() == 'prefetch' :
			wrapperclass = PrefetchWrapper
		else:	
			wrapperclass = NodeWrapper
		if selvalue.GetType() == 'ext' and \
			selvalue.GetChannelType() == 'RealPix' and \
			not hasattr(selvalue, 'slideshow'):
			return None
	elif className in ('Region','Viewport'):
		if selvalue.isDefault():
			# don't allow to show/edit default region properties
			return None
		wrapperclass = ChannelWrapper
		
	return wrapperclass
		
def showattreditor(toplevel, node, initattr = None):
	try:
		attreditor = node.attreditor
	except AttributeError:
		# don't use __class__ - it doesn't support inheritance. -mjvdg.
		#if node.__class__ is MMNode.MMNode:
		if isinstance(node, MMNode.MMNode): # supports also EditableObjects.EditableMMNode
			ntype = node.GetType()
			if ntype == 'anchor':
				wrapperclass = AnchorWrapper
			elif ntype == 'animate' :
				wrapperclass = AnimationWrapper
			elif ntype == 'prefetch' :
				wrapperclass = PrefetchWrapper
			else:	
				wrapperclass = NodeWrapper
			if node.GetType() == 'ext' and \
			   node.GetChannelType() == 'RealPix' and \
			   not hasattr(node, 'slideshow'):
				import realnode
				node.slideshow = realnode.SlideShow(node)
		else:
			wrapperclass = SlideWrapper
		attreditor = AttrEditor(wrapperclass(toplevel, node), initattr=initattr)
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
	
# And an attribute editor for transitions
def showtransitionattreditor(toplevel, trname, initattr = None):
	try:
		attreditor = toplevel.context.transitions[trname]['__attreditor']
	except KeyError:
		attreditor = AttrEditor(TransitionWrapper(toplevel, trname), initattr = initattr)
		toplevel.context.transitions[trname]['__attreditor'] = attreditor
	else:
		attreditor.pop()
		
def hastransitionattreditor(toplevel, trname):
	try:
		attreditor = toplevel.context.transitions[trname]['__attreditor']
	except KeyError:
		return 0
	return 1
	
# A similar interface for program preferences (note different arguments!).

prefseditor = None
def showpreferenceattreditor(initattr = None):
	global prefseditor
	if prefseditor is None:
		prefseditor = AttrEditor(PreferenceWrapper(), initattr = initattr)
	else:
		prefseditor.pop()

def haspreferenceattreditor():
	return prefseditor is not None

def closepreferenceattreditor():
	global prefseditor
	if prefseditor is not None:
		prefseditor.close()
		prefseditor = None

# those two method allow to merge the two 'bgcolor' and 'transparent' attributes into on attribute
# it's useful for properties editor which request one attribute by 'unsplitable' graphic control
# those method are used in ChannelWrapper and NodeWrapper
def cmifToCssBgColor(transparent, bgcolor):
	if transparent == 0 and bgcolor != None:
		return 'color', bgcolor
	if transparent == 1:
		return 'transparent', (0, 0, 0)
	
	return 'inherit', (0, 0, 0)

def cssToCmifBgColor(cssbgcolor):
	ctype, color = cssbgcolor
	if ctype == 'transparent':
		transparent = 1
		bgcolor = None
	elif ctype == 'inherit':
		transparent = None
		bgcolor = None
	else:		
		transparent = 0
		bgcolor = color

	return transparent, bgcolor

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
		self.__closing = 0
	def __repr__(self):
		return '<%s instance>' % self.__class__.__name__
	def close(self):
		self.__closing = 1
		del self.context
		del self.toplevel
	def closing(self):
		return self.__closing
	def closesoon(self):
		# we're going to close soon, no more updates to the screen
		self.__closing = 1
	def getcontext(self):
		return self.context
	def register(self, object):
		import settings
		self.editmgr.register(object, want_focus=1)
		settings.register(object)
	def unregister(self, object):
		import settings
		self.editmgr.unregister(object)
		settings.unregister(object)
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
		return MMAttrdefs.valuerepr(name, value).strip()
	def parsevalue(self, name, str):
		return MMAttrdefs.parsevalue(name, str, self.context)
	def canhideproperties(self):
		if not features.ADVANCED_PROPERTIES in features.feature_set:
			# Returning 0 here disables the "advanced" toggle.
			# We've taken care elsewhere that in this case we don't
			# show everything but in stead we show only non-advanced.
			return 0
		return 1
	def canfollowselection(self):
		return 0
	def getselection(self):
		raise 'getselection() called for attreditor not supporting it'
	def setselection(self, selection):
		raise 'setselection() called for attreditor not supporting it'
	def checkconsistency(self, attreditor):
		return 1

class NodeWrapper(Wrapper):
	def __init__(self, toplevel, node):
		self.node = node
		self.root = node.GetRoot()
		Wrapper.__init__(self, toplevel, node.GetContext())

	def __repr__(self):
		return '<NodeWrapper instance, node=' + `self.node` + '>'

	def close(self):
		self.node.attreditor = None
		del self.node.attreditor
		del self.node
		del self.root
		Wrapper.close(self)

	def stillvalid(self):
		return self.node.GetRoot() is self.root
		
	def canfollowselection(self):
		return 1
					
	def maketitle(self):
		# This code should go to MMNode
		name = MMAttrdefs.getattr(self.node, 'name')
		if name:
			return 'Properties of node ' + name
		if self.node.GetType() == 'imm':
			value = ' '.join(self.node.GetValues())
			if value:
				str = ''
				if len(value) > 16:
					value = value[:15] + '...'
				for ch in value:
					if ' ' < ch < chr(0x7f):
						str = str + ch
					else:
						str = str + ' '
				return 'Properties of node "%s"' % str
		url = MMAttrdefs.getattr(self.node, 'file')
		if url and url != '#':
			import urlcache
			import urlparse
			import posixpath
			mimetype = urlcache.mimetype(self.root.context.findurl(url))
			if mimetype:
				mimetype = string.split(mimetype, '/')[0]
			if not mimetype:
				mimetype = ''
			path = urlparse.urlparse(url)[2]
			filename = posixpath.split(path)[1]
			if mimetype and filename:
				return 'Properties of node (%s %s)' % (mimetype, filename)
			if filename:
				return 'Properties of node (%s)' % filename
		return 'Properties of node'

	def getattr(self, name): # Return the attribute or a default
		if name == '.type':
			return self.node.GetType()
		if name == '.values':
			return self.node.GetValues()
		if name == 'cssbgcolor':
			transparent = self.node.GetRawAttrDef('transparent', None)
			bgcolor = self.node.GetRawAttrDef('bgcolor',None)
			return cmifToCssBgColor(transparent, bgcolor)
			
		return MMAttrdefs.getattr(self.node, name)

	def getvalue(self, name): # Return the raw attribute or None
		if name == '.type':
			return self.node.GetType()
		if name == '.values':
			return self.node.GetValues() or None
		if name == 'cssbgcolor':
			transparent = self.node.GetRawAttrDef('transparent', None)
			bgcolor = self.node.GetRawAttrDef('bgcolor',None)
			return cmifToCssBgColor(transparent, bgcolor)
		return self.node.GetRawAttrDef(name, None)

	def getdefault(self, name): # Return the default or None
		if name == '.type':
			return None
		if name == '.values':
			return None
		return MMAttrdefs.getdefattr(self.node, name)

	def setattr(self, name, value):
		if name == '.type':
			if self.node.GetType() == 'imm' and value != 'imm':
				self.editmgr.setnodevalues(self.node, [])
			self.editmgr.setnodetype(self.node, value)
			return
		if name == '.values':
			# ignore value if not immediate or comment node
			if self.node.GetType() in ('imm', 'comment'):
				self.editmgr.setnodevalues(self.node, value)
			return
		if name == 'cssbgcolor':
			transparent, bgcolor = cssToCmifBgColor(value)
			self.editmgr.setnodeattr(self.node, 'transparent', transparent)
			self.editmgr.setnodeattr(self.node, 'bgcolor', bgcolor)
			return
			
		self.editmgr.setnodeattr(self.node, name, value)

	def delattr(self, name):
		if name == '.values':
			self.editmgr.setnodevalues(self.node, [])
			return
		if name == 'cssbgcolor':
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
		return self.node.getallattrnames(1)

	def getdef(self, name):
		if name == '.type':
			return (('enum', alltypes), '',
				'Object type', 'nodetype',
				'Object type', 'raw', flags.FLAG_ALL|flags.FLAG_ADVANCED)
		if name == '.values':
			return (('string', None), '',
				'Content', 'text',
				'Data for node', 'raw', flags.FLAG_ALL)
		return MMAttrdefs.getdef(name)

	def getselection(self):
		return self.node

	def setselection(self, selection):
		self.node = selection
	
class SlideWrapper(NodeWrapper):
	def attrnames(self):
		import realsupport
		tag = self.node.GetAttr('tag')
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

class AnimationWrapper(NodeWrapper):
	animateElements = ['animate', 'set', 'animateMotion', 'animateColor', 'transitionFilter']
	def __init__(self, toplevel, node):
		NodeWrapper.__init__(self, toplevel, node)

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		tag = MMAttrdefs.getattr(self.node, 'atag')
		return 'Properties of %s node ' % tag + name

	def getdef(self, name):
		if name == 'atag':
			return (('enum', self.animateElements), '',
				'Animate type', 'atag',
				'Type of animate object', 'normal', flags.FLAG_ALL)
		return NodeWrapper.getdef(self, name)

		
class PrefetchWrapper(NodeWrapper):
	def __init__(self, toplevel, node):
		NodeWrapper.__init__(self, toplevel, node)

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Properties of prefetch node %s' % name

class AnchorWrapper(NodeWrapper):
	def attrnames(self):
		return self.node.getallattrnames(1) + ['.href']

	def getattr(self, name):
		if name == '.href':
			links = self.context.hyperlinks.findsrclinks(self.node)
			if not links:
				return None
			link = links[0]	# first hyperlink
			return link[1]	# string for external, MMNode instance for internal
		return NodeWrapper.getattr(self, name)

	def getvalue(self, name):
		if name == '.href':
			links = self.context.hyperlinks.findsrclinks(self.node)
			if not links:
				return None
			link = links[0]	# first hyperlink
			return link[1]	# string for external, MMNode instance for internal
		return NodeWrapper.getvalue(self, name)

	def getdefault(self, name):
		if name == '.href':
			return None
		return NodeWrapper.getdefault(self, name)

	def setattr(self, name, value):
		if name == '.href':
			for link in self.context.hyperlinks.findsrclinks(self.node):
				self.editmgr.dellink(link)
			self.editmgr.addlink((self.node, value, DIR_1TO2))
			return
		NodeWrapper.setattr(self, name, value)

	def delattr(self, name):
		if name == '.href':
			for link in self.context.hyperlinks.findsrclinks(self.node):
				self.editmgr.dellink(link)
			return
		NodeWrapper.delattr(self, name)

	def getdef(self, name):
		if name == '.href':
			return (('any', None), None,
				'Hyperlink destination', 'href',
				'Hyperlink destination', 'raw', flags.FLAG_ALL)
		return NodeWrapper.getdef(self, name)

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		if name:
			name = 'anchor %s' % name
		else:
			name = 'nameless anchor'
		nname = MMAttrdefs.getattr(self.node.GetParent(), 'name') or 'nameless node'
		return 'Properties of %s in %s' % (name, nname)

	def checkconsistency(self, attreditor):
		shape = attreditor._findattr('ashape')
		if shape is not None:
			shape = shape.getvalue()
		else:
			shape = 'rect'
		coords = attreditor._findattr('acoords')
		try:
			coords = coords.parsevalue(coords.getvalue())
		except:
			# the error will be found again
			return 1
		if shape == 'rect':
			if len(coords) != 4 and len(coords) != 0:
				attreditor.showmessage('Rectangle anchors need 4 coordinates (or none).', mtype = 'error')
				return 0
		elif shape == 'circle':
			if len(coords) != 3:
				attreditor.showmessage('Circle anchors need 3 coordinates.', mtype = 'error')
				return 0
		else:
			# shape == 'poly'
			if len(coords) % 2 != 0:
				attreditor.showmessage('Polygon anchors need an even number of coordinates.', mtype = 'error')
				return 0
		return 1

class ChannelWrapper(Wrapper):
	def __init__(self, toplevel, channel):
		self.channel = channel
		Wrapper.__init__(self, toplevel, channel.context)

	def __repr__(self):
		return '<ChannelWrapper, name=' + `self.channel.name` + '>'

	def close(self):
		if haschannelattreditor(self.channel):
			del self.channel.attreditor
		del self.channel
		Wrapper.close(self)

	def stillvalid(self):
		return self.channel.stillvalid()

	def canfollowselection(self):
		return 1
					
	def maketitle(self):
		return 'Properties of region ' + self.channel.name

	def getattr(self, name):
		if name == '.cname': return self.channel.name
		if name == 'cssbgcolor': return self.getvalue(name)
		if self.channel.has_key(name):
			return self.channel[name]
		else:
			return MMAttrdefs.getdef(name)[1]

	def getvalue(self, name): # Return the raw attribute or None
		if name == '.cname': return self.channel.name
		if name == 'cssbgcolor':
			transparent = self.channel.get('transparent')
			bgcolor = self.channel.get('bgcolor')
			return cmifToCssBgColor(transparent, bgcolor)
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
		if name == 'cssbgcolor':
			transparent, bgcolor = cssToCmifBgColor(value)
			self.editmgr.setchannelattr(self.channel.name, 'transparent', transparent)
			self.editmgr.setchannelattr(self.channel.name, 'bgcolor', bgcolor)
			return
		if name == '.cname':
			if self.channel.name != value and \
			   self.editmgr.context.getchannel(value):
				self.channel.attreditor.showmessage('Duplicate channel name (not changed).')
				return
			self.editmgr.setchannelname(self.channel.name, value)
		else:
			self.editmgr.setchannelattr(
				self.channel.name, name, value)

	def delattr(self, name):
		if name == '.cname' or name == 'cssbgcolor':
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
		editmgr.delchannel(self.channel)
		editmgr.commit()
	#
	# Return a list of attribute names that make sense for this channel,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = ['.cname', 'title', 'alt', 'longdesc', 'height', 'width', 'cssbgcolor']
		if self.channel.get('base_window') is None:
			# top layout
			namelist.extend(['traceImage', 'open', 'close', 'showEditBgMode', 'resizeBehavior'])
		else:
			# region
			namelist.extend(['regionName', 'fit', 'showBackground', 'top', 'bottom', 'left', 'right', 'z', 'soundLevel'])
			if features.EXPORT_REAL in features.feature_set:
				namelist.append('opacity')
		return namelist
	#
	# Override three methods from Wrapper to fake channel name attribute
	#
	def getdef(self, name):
		if name == '.cname':
			base = self.channel.get('base_window')
			if base is not None:
				# region Id -- special case
				return (('name', ''), 'none',
					'Region ID', 'default',
					'Region ID', 'raw', flags.FLAG_ALL)
			else:
				# viewport Id -- special case
				return (('name', ''), 'none',
					'TopLayout ID', 'default',
					'TopLayout ID', 'raw', flags.FLAG_ALL)
			
		return MMAttrdefs.getdef(name)

	def valuerepr(self, name, value):
		if name == '.cname': name = 'name'
		
		return MMAttrdefs.valuerepr(name, value).strip()

	def parsevalue(self, name, str):
		if name == '.cname': name = 'name'
		return MMAttrdefs.parsevalue(name, str, self.context)

	def getselection(self):
		return self.channel

	def setselection(self, selection):
		self.channel = selection

class DocumentWrapper(Wrapper):
	# XXX disable temporarly 'project_boston'
	__stdnames = ['title', 'author', 'comment', 'copyright', 'base']
	__publishnames = [
			'project_ftp_host', 'project_ftp_user', 'project_ftp_dir',
			'project_ftp_host_media', 'project_ftp_user_media', 'project_ftp_dir_media',
			'project_smil_url', 'project_web_url']
	__qtnames = ['autoplay', 'qttimeslider', 'qtnext', 'qtchaptermode', 'immediateinstantiation']
	__templatenames = ['template_name', 'template_description', 'template_snapshot']

	def __init__(self, toplevel):
		Wrapper.__init__(self, toplevel, toplevel.context)

	def __repr__(self):
		return '<DocumentWrapper instance, file=%s>' % self.toplevel.filename

	def close(self):
		del self.toplevel.attreditor
		Wrapper.close(self)

	def canhideproperties(self):
		return 0

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
		if name == 'comment':
			return self.context.comment or None
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
		elif name == 'comment':
			self.context.comment = value
		else:
			self.context.attributes[name] = value

	def delattr(self, name):
		if name == 'title':
			self.context.title = None
		elif name == 'base':
			self.context.setbaseurl(None)
		elif name == 'comment':
			self.context.comment = ''
		elif self.context.attributes.has_key(name):
			del self.context.attributes[name]

	def delete(self):
		# shouldn't be called...
		pass

	def attrnames(self):
		attrs = self.context.attributes
		names = attrs.keys()
		# XXX disable temporarly 'project_boston'
		if 'project_boston' in names:
			names.remove('project_boston')
		for name in self.__stdnames + self.__publishnames + self.__qtnames + self.__templatenames:
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
		if features.CREATE_TEMPLATES in features.feature_set:
			names = self.__templatenames + names
		if features.compatibility in (features.Boston, features.G2, features.QT):
			if features.compatibility == features.QT:
				names = self.__qtnames + names
			names = self.__publishnames + names
		names = self.__stdnames + names
		if features.EDIT_BASE not in features.feature_set and 'base' in names:
			names.remove('base')
		return names

	def valuerepr(self, name, value):
		if name in ('title', 'base', 'comment'):
			return MMAttrdefs.valuerepr(name, value).strip()
		else:
			return value

	def parsevalue(self, name, str):
		if name in ('title', 'base', 'comment'):
			return MMAttrdefs.parsevalue(name, str, self.context)
		else:
			return str

class TransitionWrapper(Wrapper):
	# XXXX Should we have the name in here too?
	__stdnames = ['trname', 'trtype', 'subtype', 'dur', 'startProgress', 'endProgress', 'direction',
		      'horzRepeat', 'vertRepeat', 'borderWidth', 'color',
##		      'coordinated', 'clipBoundary',
		      ]

	def __init__(self, toplevel, trname):
		Wrapper.__init__(self, toplevel, toplevel.context)
		self.__trname = trname
		
	def __repr__(self):
		return '<TransitionWrapper instance for %s, file=%s>' % (self.__trname, self.toplevel.filename)

	def close(self):
		try:
			del self.context.transitions[self.__trname]['__attreditor']
		except KeyError:
			pass
		Wrapper.close(self)

	def canhideproperties(self):
		return 0

	def stillvalid(self):
		if not self.toplevel in self.toplevel.main.tops:
			return 0
		return self.context.transitions.has_key(self.__trname)

	def maketitle(self):
		return 'Transition %s properties' % self.__trname

	def getattr(self, name):	# Return the attribute or a default
		return self.getvalue() or ''

	def getvalue(self, name):	# Return the raw attribute or None
		if name == 'trname':
			return self.__trname
		if self.context.transitions[self.__trname].has_key(name):
			return self.context.transitions[self.__trname][name]
		return None		# unrecognized

	def getdefault(self, name):
		attrdef = MMAttrdefs.getdef(name)
		return attrdef[1]
		
	def setattr(self, name, value):
		if name == 'trname':
			if value == self.__trname:
				return
			if self.context.transitions.has_key(value):
				import windowinterface
				windowinterface.showmessage('Duplicate transition name: %s (not changed).'%value)
				return
			self.editmgr.settransitionname(self.__trname, value)
			self.__trname = value
		else:
			self.editmgr.settransitionvalue(self.__trname, name, value)

	def delattr(self, name):
		if name == 'trname':
			return	# Don't do this
		self.editmgr.settransitionvalue(self.__trname, name, None)

	def delete(self):
		# shouldn't be called...
		pass

	def attrnames(self):
		attrs = self.context.transitions[self.__trname]
		names = attrs.keys()
		for name in self.__stdnames:
			if attrs.has_key(name):
				names.remove(name)
		if '__attreditor' in names:
			names.remove('__attreditor')
		return self.__stdnames + names

class PreferenceWrapper(Wrapper):
	__strprefs = {
		'system_language': 'Preferred language',
		}
	__intprefs = {
		'system_bitrate': 'Bitrate of connection with outside world',
		}
	__boolprefs = {
		'system_captions': 'Whether captions are to be shown',
		'system_audiodesc': 'Whether to "show" audio descriptions',
		'cmif': 'Enable CMIF-specific extensions',
		'html_control': 'Choose between Internet Explorer and WebsterPro HTML controls',
		'showhidden': 'Show hidden custom tests',
		'saveopenviews': 'Remember placement of views globally',
		'initial_dialog': 'Show initial dialog on application start',
##		'vertical_icons': 'Show icons vertically in the Structure View',
		'default_sync_behavior_locked': 'Playback will be fully synchronized by default',
		}
	__floatprefs = {
		'default_sync_tolerance': 'Maximum media clock drift for synchronized playback',
	} 
	if features.CREATE_TEMPLATES in features.feature_set:
		__boolprefs['enable_template'] = \
			'Enable features specific to building template documents'
	__specprefs = {
		'system_overdub_or_caption': 'Text captions (subtitles) or overdub',
##		'system_overdub_or_subtitle': 'Overdub or subtitles',
		}

	def __init__(self):
		self.toplevel = None

	def closing(self):
		return 0

	def close(self):
		global prefseditor
		prefseditor = None

	def canhideproperties(self):
		return 0

	def getcontext(self):
		raise RuntimeError, 'getcontext should not be called'

	def setwaiting(self):
		pass

	def register(self, object):
		import settings
		settings.register(object)

	def unregister(self, object):
		import settings
		settings.unregister(object)

	def transaction(self):
		import settings
		return settings.transaction()

	def commit(self):
		import settings
		settings.commit()

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
		elif self.__floatprefs.has_key(name):
			return (('float', None), self.getdefault(name),
				defs[2] or name, 'syncTolerance',
				self.__floatprefs[name], 'raw', flags.FLAG_ALL)
		elif self.__boolprefs.has_key(name):
			return (('bool', None), self.getdefault(name),
				defs[2] or name, 'default',
				self.__boolprefs[name], 'raw', flags.FLAG_ALL)
		elif name == 'system_overdub_or_caption':
			return (('bool', None), self.getdefault(name),
				defs[2] or name, 'captionoverdub',
				self.__specprefs[name], 'raw', flags.FLAG_ALL)

	def stillvalid(self):
		return 1

	def maketitle(self):
#		return 'GRiNS previewer properties'
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
		attrs = self.__strprefs.keys() + self.__intprefs.keys() + \
			self.__boolprefs.keys() + self.__specprefs.keys() + \
			self.__floatprefs.keys()
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
	def __init__(self, wrapper, new = 0, initattr = None):
		if not features.ADVANCED_PROPERTIES in features.feature_set:
			self.show_all_attributes = 0
		elif wrapper.canhideproperties():
			import settings
			self.show_all_attributes = settings.get('show_all_attributes')
		else:
			self.show_all_attributes = 1
		self.follow_selection = 0
		self.__new = new
		self.wrapper = wrapper
		self.__mytransaction = 0
		wrapper.register(self)
		self.__open_dialog(initattr)
		# update the title bar name
		self.settitle(wrapper.maketitle())
		self.__pagechangeChecking = 0
		
	def __open_dialog(self, initattr):
		import settings
		import compatibility
		import flags
		wrapper = self.wrapper
		list = []
		allnamelist = wrapper.attrnames()
		namelist = []
		lightweight = features.lightweight
		if not lightweight:
			cmif = settings.get('cmif')
		else:
			cmif = 0
		curflags = flags.curflags()
		for name in allnamelist:
			fl = wrapper.getdef(name)[6]
			if fl & curflags: # and self.mustshow(fl):
				namelist.append(name)

		self.__namelist = namelist
		initattrinst = None
		for i in range(len(namelist)):
			name = namelist[i]
			typedef, defaultvalue, labeltext, displayername, \
				 helptext, inheritance, flags = \
				 wrapper.getdef(name)
			type = typedef[0]
			if DISPLAYERS.has_key(displayername):
				C = DISPLAYERS[displayername]
			elif TYPEDISPLAYERS.has_key(type):
				C = TYPEDISPLAYERS[type]
			else:
				C = AttrEditorField

			b = C(self, name, labeltext or name) # Instantiate the class.

			if initattr and initattr == name:
				initattrinst = b
			if b != None:
				list.append(b)
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

	def pagechange_allowed(self):
		# avoid a recursive checking
		if self.__pagechangeChecking:
			return 1

		# Optionally save/revert changes made to properties and return 1 if
		# it is OK to change tabs or change the node the dialog points to.
		if not self.is_changed():
			return 1
		
		self.pop()
		# XXX for now, cancel is not allowed. A lot of work to have something reliable:
		# if the user cancel, it would mean that the selection have to be restored
		# as well if followselection is activated, or have a mechanism which allow to
		# check if the selection is possible before selecting (like 'transaction'), etc ...
		# answer = windowinterface.GetYesNoCancel("Save modified properties?")
		answer = windowinterface.GetYesNo("This property dialog has unsaved changes.\nSave these changes?")
		if answer == 0:
			# avoid a recursive checking
			self.__pagechangeChecking = 1
			
			self.apply_callback()
			self.__pagechangeChecking = 0
			return 1
		if answer == 1:
#			self.resetall()
			return 1
		return 1
		#return 0

	def is_changed(self):
		# Return true if any property value has been edited.
		for b in self.attrlist:
			# Special case for empty values:
			value = b.getvalue()
			current = b.getcurrent()
			if not value and not current:
				continue
			if value != current:
				if __debug__:
					print 'DBG changed', b
					print 'VALUE', value
					print 'CURRENT', current
				return 1
		return 0
				
	def showall_callback(self):
#		if not self.pagechange_allowed():
#			self.fixbuttonstate()
#			return
		self.show_all_attributes = not self.show_all_attributes
		self.fixbuttonstate()
		import settings
		settings.set('show_all_attributes', self.show_all_attributes)
		# settings.save()
		#print 'showall', self.show_all_attributes
		self.redisplay(force = 1)

	def followselection_callback(self):
		if not self.pagechange_allowed():
			# restore the button state
			self.fixbuttonstate()
			return
		self.follow_selection = not self.follow_selection
		self.fixbuttonstate()
		if self.wrapper != None:
			object = self.wrapper.editmgr.getglobalfocus()
			self.followselection(object)
		
	def cancel_callback(self):
		self.close()

	def ok_callback(self):
		self.apply_callback(close = 1)

	def apply_callback(self, close = 0):
		# For those of us who can't tell verbs from nouns, apply here means "The Apply button"
		# and this is a callback for when the "Apply button" is pressed - although it gets called
		# from the "Ok" button also.
		if not self.wrapper.checkconsistency(self):
			return 1
		self.__new = 0
		# first collect all changes
		dict = {}
		newchannel = None
		checkType = 0
		for b in self.attrlist:
			name = b.getname()
			str = b.getvalue()
			if str != b.getcurrent():
				if hasattr(b, 'newchannels') and \
					str not in self.wrapper.getcontext().channelnames:
					newchannel = b.parsevalue(str)
					try:
						b.newchannels.remove(str)
					except ValueError:
						# probably shouldn't happen...
						pass
				try:
					value = b.parsevalue(str)
				except MParsingError, message:
					# in this case, the parsing error has been handled by the displayer
					self.showmessage(message, mtype = 'error')
					return 1
				except (ValueError, MTypeError, MSyntaxError), eparam:
					#print "DEBUG: ValueError exception: ", eparam
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
					if name in ('duration', 'loop', 'max', 'syncTolerance', 'syncToleranceDefault'):
						exp = exp + " or `indefinite'"
					self.showmessage('%s: value should be a%s %s.' % (b.getlabel(), n, exp), mtype = 'error')
					return 1
				if name == 'file':
					ntype = self.wrapper.node.GetType()
					if value and value[:5] == 'data:' and ntype == 'ext':
						import MMmimetypes
						mtype = MMmimetypes.guess_type(value)[0]
						if mtype == 'text/plain':
							import MMurl
							# convert data URL to immediate text
							dict['.type'] = 'imm'
							f = MMurl.urlopen(value)
							str = f.read()
							f.close()
							str = '\n'.join(str.split('\r\n')) # CRLF -> LF
							str = '\n'.join(str.split('\r')) # CR -> LF
							dict['.values'] = str.split('\n')
							value = None # delete file attribute
					elif ntype == 'imm':
						# not a data URL, must be ext node
						dict['.type'] = 'ext'
				# if we change any of this attribute, we have to check the consistence,
				# and re, compute the computedMimeType, channel type, ...
				if name in ('file', 'mimetype', '.type', 'channel'):
					checkType = 1
				# for now, assume that url is all the time value
				# Anyway, to filter the valid url according the GRiNS version, you'll have
				# to modify this code
#				if name == 'file' and not self.checkurl(value):
#					self.showmessage('URL not compatible with channel', mtype = 'error')
#					return 1
				if (name == 'href' or (name == '.href' and type(value) is type(''))) and \
				   value not in self.wrapper.getcontext().externalanchors:
					self.wrapper.getcontext().externalanchors.append(value)
				dict[name] = value
		if not dict and not newchannel:
			# nothing to change
			if close:
				self.close()
			return
		# if the transaction is called by this module, the 'transaction callback' has to be
		# a different treatement
		self.__mytransaction = 1
		if not self.wrapper.transaction():
			self.__mytransaction = 0
			# can't do a transaction
			return 1
		self.__mytransaction = 0
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
		if checkType:
			self.checkType(self.wrapper.node)
			
		if close:
			self.wrapper.closesoon()
		self.wrapper.commit()
		if close:
			self.close()

	# but need to check if mimetype compatible, with region type, url, ...
	# for now, do nothing
	def checkType(self, node):
		pass
					
##	def checkurl(self, url):
##		if not features.lightweight:
##			return 1
##		#if self.wrapper.__class__ is SlideWrapper:
##		if isinstance(self.wrapper, SlideWrapper):
##			# node is a slide
##			import MMmimetypes
##			mtype = MMmimetypes.guess_type(url)[0]
##			if not mtype:
##				# unknown type, not compatible
##				return 0
##			# compatible if image and not RealPix
##			return mtype[:5] == 'image' and string.find(mtype, 'real') < 0
##		b = self._findattr('channel')
##		if b is not None:
##			str = b.getvalue()
##			try:
##				chan = b.parsevalue(str)
##			except:
##				chan = ''
##			return chan in self.wrapper.getcontext().compatchannels(url)
##		# not found, assume compatible
##		return 1

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
					break
				else:
					# multiple root windows
					root = ''
		index = len(context.channelnames)
		if root:
			channel = context.newchannel(channelname, index, 'layout')
			parent = context.getchannel(key)
			em.addchannel(parent, index, channel)

	#
	# EditMgr interface
	#
	def transaction(self, type):
		if not self.__mytransaction:
			return self.pagechange_allowed()
		return 1
	
	def commit(self, type):
		if self.wrapper.closing():
			pass
		elif not self.wrapper.stillvalid():
			self.close()
		else:
			self.redisplay()
			
	def globalfocuschanged(self, focuslist):
		if not self.follow_selection:
			return
		if len(focuslist) != 1:
			return
		if focuslist[0] is self.wrapper.getselection():
			return
		if self.pagechange_allowed():
			self.followselection(focuslist)
		else:
			# XXX should restore the focus. But can't be done here
			pass
			
	def followselection(self, focuslist):
		newwrapper = None
		# get the right wrapper according to the selection
		# if the wrapper doesn't exist, do nothing
		wrapperclass = getwrapperclass(focuslist)
		if wrapperclass is None:
			# no wrapper available for this selection type
			return
		# we know here that there is exactly one element in focuslist
		focusobject = focuslist[0]
		if self.wrapper.__class__ is not wrapperclass:
			# the wrapper has to change
			toplevel = self.wrapper.toplevel
			newwrapper = wrapperclass(toplevel, focusobject)

		# update attreditor. 
		selection = self.wrapper.getselection()
		if hasattr(selection, 'attreditor'):
			# remove attreditor on previous node selected
			del selection.attreditor
		focusobject.attreditor = self

		# update selection					
		if not newwrapper:
			self.wrapper.setselection(focusobject)
		else:
			newwrapper.setselection(focusobject)

		self.redisplay(newwrapper)

	def redisplay(self, newwrapper = None, force = 0):
		if newwrapper or force or self.wrapper.attrnames() != self.__namelist:
			# re-open with possibly different size
			attr = self.getcurattr()
			if attr:
				attr = attr.getname()
			AttrEditorDialog.close(self, willreopen=1)
			for b in self.attrlist:
				b.close()
			del self.attrlist
			if newwrapper:
				# if the wrapper has changed, set the new wrapper
				self.wrapper = newwrapper
			self.__open_dialog(attr)
		else:
			a = self.getcurattr()
##				self.fixvalues()
			self.resetall()
			self.setcurattr(a)
		# update the title bar name
		self.settitle(self.wrapper.maketitle())

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
		self.attrdef = self.wrapper.getdef(name)

	def __repr__(self):
		return '<%s instance, name=%s>' % (self.__class__.__name__,
						   self.__name)
						   
##	def earlyclose(self):
##		# Call this close routine if you want to get rid of the object
##		# before the AttrEditorDialogField has been initialized.
##		del self.attreditor
##		del self.wrapper
##		del self.attrdef

	def close(self):
		AttrEditorDialogField.close(self)
		del self.attreditor
		del self.wrapper
		del self.attrdef

	def mustshow(self):
		# Return true if we should show this attribute
		import settings
		advflags = self.attrdef[6]
		can_show_advanced = \
			features.ADVANCED_PROPERTIES in features.feature_set and \
			self.attreditor.show_all_attributes
		can_show_template = can_show_advanced and \
			features.CREATE_TEMPLATES in features.feature_set and \
			settings.get('enable_template')
		if (advflags & flags.FLAG_TEMPLATE):
			# Only show if both "show all" and "template"
			# are enabled
			if can_show_template:
				return 1
			return 0
		elif advflags & flags.FLAG_ADVANCED:
			# Only show is "advanced" is enabled
			if can_show_advanced:
				return 1
			return 0
		# The rest we always show
		return 1

	def getname(self):
		return self.__name

	def gettype(self):
		return self.type

	def getlabel(self):
		return self.label

	def gethelptext(self):
		return '%s\ndefault: %s' % (self.attrdef[4], self.getdefault())

	def gethelpdata(self):
		return self.__name, self.getdefault(), self.attrdef[4]

	def getcurrent(self):
		# self.wrapper is a NodeWrapper instance. -mjvdg.
		return self.valuerepr(self.wrapper.getvalue(self.__name))

	def getdefault(self):
		return self.valuerepr(self.wrapper.getdefault(self.__name))

	def getdefaultvalue(self):
		return self.wrapper.getdefault(self.__name)

	def isdefault(self):
		v = self.wrapper.getvalue(self.__name)
		if v is None or v == self.wrapper.getdefault(self.__name):
			return 1
		return 0

	def valuerepr(self, value):
		# Return string representation of value.
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return ''
		return self.wrapper.valuerepr(self.__name, value)

	def parsevalue(self, str):
		# Return internal representation of string.
		if str == '':
			return None
		return self.wrapper.parsevalue(self.__name, str)

	def reset_callback(self):
		self.setvalue(self.getcurrent())

	def help_callback(self):
		self.attreditor.showmessage(self.gethelptext())

class IntAttrEditorField(AttrEditorField):
	type = 'int'

class FloatAttrEditorField(AttrEditorField):
	type = 'float'

	def valuerepr(self, value):
		if value is None:
			return ''
		if value == -1 and self.getname() in ('duration', 'repeatdur', 'max', 'syncTolerance', 'syncToleranceDefault'):
			return 'indefinite'
		if value == 0 and self.getname() == 'loop':
			return 'indefinite'
		return fmtfloat(value)

	def parsevalue(self, str):
		str = str.strip()
		if str == '':
			return None
		if str == 'indefinite':
			attrname = self.getname()
			if attrname in ('duration', 'repeatdur', 'max', 'syncTolerance', 'syncToleranceDefault'):
				return -1.0
			if attrname == 'loop':
				return 0.0
		return AttrEditorField.parsevalue(self, str)

class PercentAttrEditorField(AttrEditorField):
	def valuerepr(self, value):
		if value is None:
			return ''
		return fmtfloat(value*100, '%')

	def parsevalue(self, str):
		str = str.strip()
		if str[-1:] == '%':
			str = str[:-1]
		if not str:
			return None
		return AttrEditorField.parsevalue(self, str)/100.0

class StringAttrEditorField(AttrEditorField):
	def valuerepr(self, value):
		# Return string representation of value.
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return ''
		return value

	def parsevalue(self, str):
		# Return internal representation of string.
		if str == '':
			return None
		return str

class KeyTimesAttrEditorField(StringAttrEditorField):
	def valuerepr(self, value):
		if value is None:
			return ''
		return ';'.join(map(fmtfloat, value))

	def parsevalue(self, str):
		if str == '':
			return None
		values = []
		for s in str.split(';'):
			try:
				v = float(s)
				if not (0.0 <= v <= 1.0):
					raise 'x'
				if values and v <= values[-1]:
					raise 'x'
			except:
				raise MParsingError, 'keyTimes should be a semicolon (;) separated list of monotonically increasing floating point values in the range 0.0 - 1.0.'
			values.append(v)
		return values

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
			if hasattr(self.wrapper, 'node'):
				chtype = self.wrapper.node.GetChannelType(url = url or None)
			else:
				chtype = None
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
##		if not self.attreditor.checkurl(url):
##			self.attreditor.showmessage('file not compatible with channel', mtype = 'error')
##			return
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
		# Return string representation of value.
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return ''
		return string.join(value, '\n')

	def parsevalue(self, str):
		# Return internal representation of string.
		if str == '':
			return None
		return string.split(str, '\n')

class TupleAttrEditorField(AttrEditorField):
	type = 'tuple'

	def valuerepr(self, value):
		if type(value) is type(''):
			return value
		return AttrEditorField.valuerepr(self, value)

class ScreenSizeAttrEditorField(TupleAttrEditorField):
	def valuerepr(self, tuplevalue):
		if tuplevalue == None:
			return ''
		if tuplevalue[0] <= 0 or tuplevalue[1] <= 0:
			return ''
		if type(tuplevalue) is type(''):
			return tuplevalue
		return AttrEditorField.valuerepr(self, tuplevalue)

	def parsevalue(self, str):
		# Return internal representation of string.
		if str == '':
			return None
		try:
			tuplevalue = TupleAttrEditorField.parsevalue(self, str)
		except (ValueError, MTypeError, MSyntaxError), eparam:
			self.__error()
			
		if tuplevalue[0] <= 0 or tuplevalue[1] <= 0:
			self.__error()
		return tuplevalue

	def __error(self):
		raise MParsingError, 'The screen height and width values have to be pixel values and both greater than 0,\n or leave the field empty if not set.'

class ScreenDepthAttrEditorField(IntAttrEditorField):
	def valuerepr(self, value):
		if value == None:
			return ''
		return AttrEditorField.valuerepr(self, value)

	def parsevalue(self, str):
		# Return internal representation of string.
		if str == '':
			return None
		try:
			value = IntAttrEditorField.parsevalue(self, str)
		except (ValueError, MTypeError, MSyntaxError), eparam:
			self.__error()
		if value <= 0:
			self.__error()
		return value

	def gethelpdata(self):
		return 'Depth' , 'Not set', self.attrdef[4]

	def __error(self):
		raise MParsingError, 'The depth has to be greater or equal than 0,\n or leave the field empty if not set.'
		
import EventEditor

class TimelistAttrEditorField(AttrEditorField):
	type = 'timelist'

	# Jack: I worked out the reason why I decided to do it this way.
	# valuerepr and parsevalue should be sending and receiving copies or
	# representations of the syncarcs, not the syncarcs themselves.
	# It's a form of encapsulation, and to me it "feels" right.

	def valuerepr(self, listofsyncarcs):
		if listofsyncarcs is None: listofsyncarcs = []
		# converts listofsyncarcs into a list of eventstructs
		#return ['hello', 'world']
		return_me = []
		n = self.wrapper.node
		for i in listofsyncarcs:
			return_me.append(EventEditor.EventStruct(i, n))
		return return_me
#		return (n, return_me)	# The editor (see AttrEditForm.py) needs the node, this is the
					# only way I know to get it there. Possible TODO.

	def parsevalue(self, editorstruct):
		# editorstruct is a tuple of (node, EventStructs[])
		# The node is there for consistancy.
		# Converts editorstruct back into a list of syncarcs.
		return_me = []
		if isinstance(editorstruct, type(())):
			node, value = editorstruct # ignore the node.
		else:
			value = editorstruct
		for i in value:
			if i: return_me.append(i.get_value()) # i could be None.
		return return_me

import colors
class ColorAttrEditorField(TupleAttrEditorField):
	type = 'color'
	def parsevalue(self, str):
		str = string.lower(string.strip(str))
		if colors.colors.has_key(str):
			return colors.colors[str]
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
		if colors.rcolors.has_key(value):
			return colors.rcolors[value]
		return TupleAttrEditorField.valuerepr(self, value)

class CssAttrEditorField(AttrEditorField):
	def getParent(self):
		node = self.wrapper.getselection()
		
		if node.getClassName() == 'MMNode':
			parentNode = node.GetChannel()
		else:
			parentNode = node.GetParent()
		return parentNode
	
class CssColorAttrEditorField(CssAttrEditorField):
# a parsed value is a tuple of:
# colortype, colorspec
# colortype = either transparent inherit or color
# colorspec is a tuple of three integers (rgb values)
#
# a string represented value is either:
#
# - 'transparent'
# - 'inherit'
# - any known string color (red, green, ...)
# - a tuple of three integer values (r,g,b)

	type = 'csscolor'
	def parsevalue(self, str):
		str = string.lower(string.strip(str))
		if str == 'transparent' or str == '':
			nstr = 'transparent 0 0 0'
		elif str == 'inherit':
			nstr = 'inherit 0 0 0'
		else:
			if colors.colors.has_key(str):
				rgb = colors.colors[str]
				nstr = ''
				for c in rgb:
					nstr = nstr + ' ' + `c`
				nstr = 'color'+' '+nstr
			else:
				nstr = 'color'+' '+str
		return AttrEditorField.parsevalue(self, nstr)

	def valuerepr(self, value):
		str = AttrEditorField.valuerepr(self, value)
		import string
		svalue = string.split(str)
		type = svalue[0]
		if type == 'transparent' or type == 'inherit':
			return type

		color = string.atoi(svalue[1]), string.atoi(svalue[2]), string.atoi(svalue[3])
		if colors.rcolors.has_key(color):
			return colors.rcolors[color]
		return svalue[1]+' '+svalue[2]+' '+svalue[3]		

	def getInheritedValue(self):
		parentNode = self.getParent()
		if parentNode is None:
			return None
		
		transparent = parentNode.GetInherAttrDef('transparent', None)
		if transparent:
			bgcolor = None
		else:
			bgcolor = parentNode.GetInherAttrDef('bgcolor', None)

		return bgcolor

class CssPosAttrEditorField(CssAttrEditorField):
# a parsed value is either:
# - a real number (0 to 1) representing a percent value
# - a int number representing a pixel value
# None representing the auto value

# a string representation value is either:
# a string including '%' representing a percent
# a string not including '%' and different of '' representing a pixel value
# '' representing the auto value

	type = 'csspos'
	def parsevalue(self, str):
		import string
		val = None
		if str == '':
			pass
		else:
			if '%' not in str:
				val = int(str)
			else:
				val = float(str[:-1])/100
			attrName = self.getname()
			if attrName in ('width', 'height') and val <0:
				raise MParsingError, attrName+' value cannot be negative'
			
		return val		

	def valuerepr(self, value):
		if value is None or value == '':
			return ''
		elif type(value) == type(0):
			return `value`
		elif type(value) == type(1.0):
			return fmtfloat(value*100, '%', prec=2)
		else:
			print 'unknown value ',value

	def getParentSize(self):
		parentNode = self.getParent()
		if parentNode is None:
			# shoudn't happen
			w,h = 100, 100
		elif parentNode.getClassName() == 'Viewport':
			w,h = parentNode.getPxGeom()
		else:
			x,y,w,h = parentNode.getPxGeom()
		
		attrName = self.getname()
		if attrName in ('left', 'right', 'width'):
			return w
		else:
			return h

	def getCurrentPxValue(self):
		node = self.wrapper.getselection()
		x,y,w,h = node.getPxGeom()
		pSize = self.getParentSize()
		attrName = self.getname()
		if attrName == 'left':
			return x
		elif attrName == 'top':
			return y
		elif attrName == 'width':
			return w
		elif attrName == 'height':
			return h
		elif attrName == 'right':
			return pSize-w-x
		elif attrName == 'bottom':
			return pSize-h-y
		else:
			return 0
		
class PopupAttrEditorField(AttrEditorField):
	# A choice menu choosing from a list -- base class only
	type = 'option'
	default = DEFAULT

	def getoptions(self):
		# derived class overrides this to defince the choices
		self.default = '%s [%s]' % (PopupAttrEditorField.default, self.getdefault())
		return [self.default]

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

	def reset_callback(self):
		if self.type == 'option':
			self.recalcoptions()
		else:
			AttrEditorField.reset_callback(self)

class PopupAttrEditorFieldWithUndefined(PopupAttrEditorField):
	# This class differs from the one above in that when a value
	# does not occur in the list of options, valuerepr will return
	# 'undefined'.

	def getoptions(self):
		# derived class overrides this to defince the choices
		self.default = '%s [%s]' % (PopupAttrEditorFieldWithUndefined.default, self.getdefault())
		return [self.default, UNDEFINED]

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.default
		options = self.getoptions()
		if value not in options:
			return UNDEFINED
		return value

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

	def __init__(self, attreditor, name, label):
		if self.nodefault:
			self.type = 'bool'
		PopupAttrEditorField.__init__(self, attreditor, name, label)

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
#	__values = ['mm', 'relative', 'pixels']
#	__valuesmap = [windowinterface.UNIT_MM, windowinterface.UNIT_SCREEN,
#		       windowinterface.UNIT_PXL]
	__values = ['relative', 'pixels']
	__valuesmap = [windowinterface.UNIT_SCREEN, windowinterface.UNIT_PXL]

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
	__values = ['subtitle', 'overdub']
	nodefault = 1

	def getoptions(self):
		return self.__values

class CaptionOverdubAttrEditorFieldWithDefault(PopupAttrEditorField):
	__values = ['subtitle', 'overdub']
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
	from languages import a2l, l2a
	default = 'Not set'
	nodefault = 1

	def getoptions(self):
		options = self.l2a.keys()
		options.sort()
		return options

	def parsevalue(self, str):
		if str == self.default:
			return None
		return self.l2a.get(str)

	def valuerepr(self, value):
		if not value:
			if self.nodefault:
				return self.getdefault()
			return self.default
		return self.a2l.get(value, self.default)

class LanguageAttrEditorFieldWithDefault(LanguageAttrEditorField):
	nodefault = 0
	def getoptions(self):
		options = LanguageAttrEditorField.getoptions(self)
		return [self.default] + options

import bitrates
class BitrateAttrEditorField(PopupAttrEditorField):
	default = 'Not set'
	nodefault = 1

	def parsevalue(self, str):
		if str == self.default:
			return None
		return bitrates.l2a.get(str)

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.default
		str = bitrates.names[0]
		for val, name in bitrates.bitrates:
			if val <= value:
				str = name
		return str

	def getoptions(self):
		return bitrates.names

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

class EnumAttrEditorField(PopupAttrEditorFieldNoDefault):
	__default = 'default'
	__inherit = 'inherit'

	def __init__(self, attreditor, name, label):
		PopupAttrEditorFieldNoDefault.__init__(self, attreditor, name, label)
		self.__values = self.attrdef[0][1][:]
		for i in range(len(self.__values)):
			v = self.__values[i]
			if v == 'default':
				node = self.attreditor.wrapper.node
				default = None
				if name == 'fill':
					default = node.GetFill('default')
				elif name == 'restart':
					default = node.GetRestart('default')
				elif name == 'syncBehavior':
					default = node.GetSyncBehavior('default')
				if default is not None:
					self.__values[i] = self.__default = 'default [%s]' % default
			elif v == 'inherit':
				pnode = self.attreditor.wrapper.node.GetParent()
				default = None
				if name == 'fillDefault':
					if pnode is None:
						default = 'auto'
					else:
						default = pnode.GetInherAttrDef('fillDefault', 'auto')
				elif name == 'restartDefault':
					if pnode is None:
						default = 'always'
					else:
						default = pnode.GetRestart('default')
				elif name == 'syncBehaviorDefault':
					if pnode is not None:
						default = pnode.GetSyncBehavior('default')
				if default is not None:
					self.__values[i] = self.__inherit = 'inherit [%s]' % default

	def getoptions(self):
		return self.__values

	def valuerepr(self, value):
		if value == 'default':
			return self.__default
		if value == 'inherit':
			return self.__inherit
		return value

	def parsevalue(self, str):
		if str == self.__default:
			return 'default'
		if str == self.__inherit:
			return 'inherit'
		return str

class EnumAttrEditorFieldWithDefault(EnumAttrEditorField):
	default = 'Not set'
	nodefault = 1

	def getoptions(self):
		current = self.getcurrent()
		options = [self.default]+EnumAttrEditorField.getoptions(self)
		if current not in options:
			options.append(current)
		return options

	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		if val is None:
			return self.default
		return self.valuerepr(val)	

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.default
		return EnumAttrEditorField.valuerepr(self, value)

	def parsevalue(self, str):
		if str == self.default:
			return None
		return EnumAttrEditorField.parsevalue(self, str)

class CpuAttrEditorField(EnumAttrEditorFieldWithDefault):
	default = 'Not set'

class OperatingSystemAttrEditorField(EnumAttrEditorFieldWithDefault):
	default = 'Not set'

class RegpointAttrEditorField(PopupAttrEditorFieldNoDefault):
	type = 'regpoint'

	def getoptions(self):
		list = self.wrapper.context.regpoints.keys()
		list.sort()
		return list
		
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

class FitAttrEditorField(PopupAttrEditorField):
	__values = ['meet: whole media', 'hidden: actual size', 'slice: fill whole region', 'scroll: scroll if necessary', 'fill: whole media in whole region']
	__valuesmap = ['meet', 'hidden', 'slice', 'scroll', 'fill']

	# Choose from a list of unit types
	def default(self):
		return 'default [%s]' % self.getdefault()

	def getoptions(self):
		return [self.default()] + self.__values

	def parsevalue(self, str):
		if str[:7] == 'default':
			return None
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		if value is None:
			return self.default()
		return self.__values[self.__valuesmap.index(value)]

	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		return self.valuerepr(val)

class TransitionAttrEditorField(PopupAttrEditorField):
	default = 'No transition'

	def getoptions(self):
		list = self.wrapper.context.transitions.keys()
		list.sort()
		return [self.default] + list
		
	def parsevalue(self, str):
		if str == self.default:
			return None
		if type(str) is type(''):
			return (str,)
		return str
		
	def valuerepr(self, value):
		if not value:
			return self.default
		if type(value) in (type([]), type(())) and len(value):
			if len(value) > 1:
				windowinterface.showmessage("Multiple transitions not supported.")
			return value[0]
		return value

	def transitionprops(self):
		tr = self.getvalue()
		if tr is not None and self.wrapper.context.transitions.has_key(tr):
			showtransitionattreditor(self.wrapper.toplevel, tr)

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
			return self.getdefaultvalue()
		strs = string.split(str, ',')
		rv = 0
		for str in strs:
			rv = rv | (1 << self.__values.index(str))
		return rv

	def valuerepr(self, value):
		if value is None:
			value = self.getdefaultvalue()
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
	def __init__(self, attreditor, name, label, wantnewchannels = 1):
		if wantnewchannels:
			self.newchannels = []
		self.__current = None
		PopupAttrEditorFieldWithUndefined.__init__(self, attreditor, name, label)

	def getoptions(self):
		# for the full version, any region may be selected: for now, it's the only case supported
		# (for other version, we have to test the new 'subtype' channel attribute)
		ctx = self.wrapper.context
		node = self.wrapper.node
		
		regionList = []
		if self.getcurrent() == UNDEFINED:
			regionList.append(UNDEFINED)
			
		for ch in ctx.channels:
			if ch.get('type') == 'layout':
				if ch.get('base_window') != None and not ch.isDefault():
					regionList.append(ch.name)

		if hasattr(self, 'newchannels'):
			regionList = regionList + self.newchannels

			# add the special key which allow to add a new regions
			regionList.append(NEW_REGION)
					
		return regionList

	def parsevalue(self, str):
		if str == UNDEFINED: 
			return None
		# XXXX: Hack: on windows platform, this value correspond to the separator
		# in this case, if the user select this value, we assume it's a undefined value
		elif str == '---':
			return None
		return str

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return UNDEFINED

		# XXXX: HACK:
		# value is either a channel name or a region name (if new)
#		if hasattr(self, 'newchannels'):
#			if len(self.newchannels) > 0:
#				if value == self.newchannels[0]:
#					return value
			
		# experimental SMIL Boston layout code
#		ch = self.wrapper.context.getchannel(value)
#		if ch == None:
#			return UNDEFINED
#		ch = ch.GetLayoutChannel()
#		try:
#			value = ch.name
#		except:
#			pass
		# end experimental	
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
			if name not in self.newchannels:
#				self.newchannels.append(name)
				self.newchannels = [name]
		self.__current = name
		self.recalcoptions()
		self.setvalue(name)
		self.__current = None
			
	def optioncb(self):
		if self.getvalue() == NEW_REGION:
			windowinterface.settimer(0.01, (self.askchannelname, (self.newchannelname(),)))

class RegionDefaultAttrEditorField(PopupAttrEditorFieldWithUndefined):
	def __init__(self, attreditor, name, label, wantnewchannels = 1):
		self.__current = None
		self.__name = name
		self.__inheritedString = None
		PopupAttrEditorFieldWithUndefined.__init__(self, attreditor, name, label)

	def getoptions(self):
		ctx = self.wrapper.context
		node = self.wrapper.node

		regionList = []
		inheritedValue = self.getInheritedValue()
		if inheritedValue != None:
			self.__inheritedString = inheritedValue+' (inherited)'
		else:
			self.__inheritedString = UNDEFINED+' (inherited)'
		regionList.append(self.__inheritedString)
			
		for ch in ctx.channels:
			if ch.get('type') == 'layout':
				if ch.get('base_window') != None and not ch.isDefault():
					regionList.append(ch.name)
					
		return regionList

	def parsevalue(self, str):
		if str == self.__inheritedString: 
			return None
		# XXXX: Hack: on windows plateform, this value correspond to the separator
		# in this case, if the user select this value, we assume it's a undefined value
		elif str == '---':
			return None
		return str

	def valuerepr(self, value):
		if value is None:
			if self.nodefault:
				return self.getdefault()
			return self.__inheritedString
		return value

	def channelprops(self):
		regionName = self.getShowedValue()
		ch = self.wrapper.context.getchannel(regionName)
		if ch is not None:
			showchannelattreditor(self.wrapper.toplevel, ch)
			
	def channelexists(self, name):
		return self.wrapper.context.getchannel(name) is not None

	def getcurrent(self):
		if self.__current:
			return self.__current
		return PopupAttrEditorFieldWithUndefined.getcurrent(self)

	def getShowedValue(self):
		regionName = self.parsevalue(self.getvalue())
		if regionName == None:
			regionName = self.getInheritedValue()
		return regionName
					
	def getInheritedValue(self):
		parentNode = self.wrapper.node.GetParent()
		if parentNode == None:
			return UNDEFINED
		return parentNode.GetInherAttrDef(self.__name, None)
		
class CaptionChannelnameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the current RealText channel names
	__nocaptions = 'No captions'

	def getoptions(self):
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
	def __init__(self, attreditor, name, label):
		ChannelnameAttrEditorField.__init__(self, attreditor, name, label, wantnewchannels = 0)

	# Choose from the current channel names
	def getoptions(self):
		list = []
		ctx = self.wrapper.context
		chname = self.wrapper.channel.name
		for name in ctx.channelnames:
			if name == chname:
				continue
			ch = ctx.channeldict[name]
			# experimental SMIL Boston layout code
			if ch.attrdict['type'] == 'layout':
			# end experimental
				list.append(name)
		list.sort()
		return [DEFAULT, UNDEFINED] + list

	def channelprops(self):
		ch = self.wrapper.context.getchannel(self.getvalue())
		if ch is not None:
			showchannelattreditor(self.wrapper.toplevel, ch)

class ListAttrEditorField(AttrEditorField):
	def valuerepr(self, value):
		if value is None:
			return ''
		return string.join(value)

	def parsevalue(self, str):
		if not str:
			return None
		return string.split(str)

class UsergroupAttrEditorField(ListAttrEditorField):
	pass

class ReqListAttrEditorField(ListAttrEditorField):
	pass

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
		extras = ['LAST', 'FIRST']
		if self.wrapper.context.attributes.get('project_boston', 0):
			extras.append('ALL')
			if self.wrapper.node.GetType() in mediatypes:
				extras.append('MEDIA')
		return extras + list

	def getcurrent(self):
		val = self.wrapper.getvalue(self.getname())
		if val is None:
			if self.wrapper.node.GetType() in mediatypes:
				return 'MEDIA'
			return 'LAST'
		return self.valuerepr(val)

class AssetNameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	def getoptions(self):
		list = []
		for asset in self.wrapper.context.getassets():
			try:
				list.append(asset.GetAttr('name'))
			except NoSuchAttrError:
				pass
		list.sort()
		return [UNDEFINED] + list

	def valuerepr(self, value):
		if not value:
			return UNDEFINED
		options = self.getoptions()
		node = self.wrapper.context.mapuid(value)
		try:
			value = node.GetAttr('name')
		except NoSuchAttrError:
			return UNDEFINED
		if value not in options:
			return UNDEFINED
		return value

	def parsevalue(self, str):
		if str == UNDEFINED:
			return None
		for asset in self.wrapper.context.getassets():
			try:
				if asset.GetAttr('name') == str:
					return asset.GetUID()
			except NoSuchAttrError:
				pass

class ChanneltypeAttrEditorField(PopupAttrEditorFieldNoDefault):
	# Choose from the standard channel types
	def getoptions(self):
		current = self.getcurrent()
		if features.lightweight:
			return [current]
		all = ChannelMap.getvalidchanneltypes(self.wrapper.context)
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

Alltypes = interiortypes+playabletypes
class NodeTypeAttrEditorField(PopupAttrEditorField):
	__valuesmap = {'par':'parallel group',
		       'seq':'sequential group',
		       'excl':'exclusive group',
		       'prio':'priority group',
		       'switch':'switch group',
		       'imm':'immediate object',
		       'ext':'media object',
		       'brush':'brush object',
		       'prefetch':'prefetch object',
		       'animate':'animate object',
		       'anchor':'anchor object',
		       'comment':'comment object',
		       'foreign':'non-GRiNS object'}
	__reversemap = {}
	for k, v in __valuesmap.items():
		__reversemap[v] = k
	del k, v
	def getoptions(self):
		# XXX this needs work: we need to take animate
		# children into account and prio can only be a child
		# of an excl
		options = Alltypes[:]
		ntype = self.wrapper.node.GetType()
		if ntype in interiortypes:
			if self.wrapper.node.GetChildren():
				for tp in playabletypes:
					options.remove(tp)
		elif ntype == 'imm' and self.wrapper.node.GetValues():
			options = ['imm']
		values = []
		for str in options:
			values.append(self.__valuesmap.get(str, str))
		return values

	def parsevalue(self, str):
		return self.__reversemap.get(str, str)

	def valuerepr(self, value):
		return self.__valuesmap.get(value, value)

class AnchorCoordsAttrEditorField(AttrEditorField):
	def valuerepr(self, value):
		if value is None:
			return ''
		strl = []
		for v in value:
			if type(v) is type(0.0):
				strl.append(fmtfloat(100*v, '%', prec = 1))
			else:
				strl.append(`v`)
		return ' '.join(strl)

	def parsevalue(self, str):
		values = []
		for s in str.split():
			try:
				if s[-1] == '%':
					v = float(s[:-1])
				elif '.' in s:
					# assume floating point value is percentage
					v = float(s)
				else:
					v = int(s)
			except ValueError:
				raise MParsingError, 'Coordinates should be a list of integers or percentage values.'
			else:
				if type(v) is type(0.0):
					# convert percentage
					v = v / 100
				values.append(v)
		return values

class HrefAttrEditorField(FileAttrEditorField):
	def valuerepr(self, value):
		return value
	def parsevalue(self, str):
		return str

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
		if url is None or type(url) != type(''):
			url = ''
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
		windowinterface.FileDialog('Choose File for ' + self.label,
					   dir, ['/Html file', 'text/html'], file, self.setpathname, None,
					   existing=1)

DISPLAYERS = {
	'acoords': AnchorCoordsAttrEditorField,
	'assetnodename': AssetNameAttrEditorField,
	'audiotype': RMAudioAttrEditorField,
	'basechannelname': BaseChannelnameAttrEditorField,
	'bitrate': BitrateAttrEditorField,
	'bitrate3': BitrateAttrEditorFieldWithDefault,
	'bool3': BoolAttrEditorFieldWithDefault,
	'captionchannelname': CaptionChannelnameAttrEditorField,
	'captionoverdub': CaptionOverdubAttrEditorField,
	'captionoverdub3': CaptionOverdubAttrEditorFieldWithDefault,
	'channelname': ChannelnameAttrEditorField,
	'channeltype': ChanneltypeAttrEditorField,
	'color': ColorAttrEditorField,
	'cpu': CpuAttrEditorField,
	'csscolor': CssColorAttrEditorField,
	'csspos': CssPosAttrEditorField,
	'file': FileAttrEditorField,
	'fit': FitAttrEditorField,
	'font': FontAttrEditorField,
	'keyTimes': KeyTimesAttrEditorField,
	'language': LanguageAttrEditorField,
	'language3': LanguageAttrEditorFieldWithDefault,
	'layoutname': LayoutnameAttrEditorField,
	'nodetype': NodeTypeAttrEditorField,
	'opsys': OperatingSystemAttrEditorField,
	'percent': PercentAttrEditorField,
	'qtchaptermode': QTChapterModeEditorField,
	'quality': QualityAttrEditorField,
	'regiondefault': RegionDefaultAttrEditorField,
	'regpoint': RegpointAttrEditorField,
	'reqlist': ReqListAttrEditorField,
	'screendepth': ScreenDepthAttrEditorField,
	'screensize': ScreenSizeAttrEditorField	,
	'subregionanchor': AnchorTypeAttrEditorField,
	'targets': RMTargetsAttrEditorField,
	'termnodename': TermnodenameAttrEditorField,
	'text': TextAttrEditorField,
	'timelist': TimelistAttrEditorField,
	'transition': TransitionAttrEditorField,
	'transparency': TransparencyAttrEditorField,
	'units': UnitsAttrEditorField,
	'usergroup': UsergroupAttrEditorField,
	'videotype': RMVideoAttrEditorField,
	'href': HrefAttrEditorField,
}

TYPEDISPLAYERS = {
	'bool': BoolAttrEditorField,
	'name': NameAttrEditorField,
	'string': StringAttrEditorField,
	'int': IntAttrEditorField,
	'float': FloatAttrEditorField,
	'tuple': TupleAttrEditorField,
	'enum': EnumAttrEditorField,
}
