__version__ = "$Id$"

import windowinterface
import MMAttrdefs
from ChannelMap import channelmap
from MMExc import *			# exceptions

# There are two basic calls into this module (but see below for more):
# showattreditor(node) creates an attribute editor form for a node
# and hideattreditor(node) hides it again.  Since the editor may also
# hide itself, spurious hide calls are ignored; also, only one attribute
# editor is allowed per node, and extra show calls are also ignored
# (actually, this pops up the window, to draw the user's attention...).

def showattreditor(toplevel, node):
	try:
		attreditor = node.attreditor
	except AttributeError:
		attreditor = AttrEditor(NodeWrapper(toplevel, node))
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

def showchannelattreditor(toplevel, channel, new = 0):
	try:
		attreditor = channel.attreditor
	except AttributeError:
		attreditor = AttrEditor(ChannelWrapper(toplevel, channel), new)
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

def showdocumentattreditor(toplevel):
	try:
		attreditor = toplevel.attreditor
	except AttributeError:
		attreditor = AttrEditor(DocumentWrapper(toplevel))
		toplevel.attreditor = attreditor
	else:
		attreditor.pop()

def hasdocumentattreditor(toplevel):
	try:
		attreditor = toplevel.attreditor
	except AttributeError:
		return 0
	return 1

# These routine checks whether we are in CMIF or SMIL mode, and
# whether the given attribute should be shown in the editor.
def cmifmode():
	import settings
	if settings.get('cmif'):
		return 1
	return 0

def mustshowdisplayer(displayer):
	if displayer[:4] != 'CMIF':
		return 1
	displayer = displayer[4:]
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
		return '<Wrapper instance>'
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

	def stillvalid(self):
		return self.node.GetRoot() is self.root

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Properties of node ' + name

	def getattr(self, name): # Return the attribute or a default
		return MMAttrdefs.getattr(self.node, name)

	def getvalue(self, name): # Return the raw attribute or None
		return self.node.GetRawAttrDef(name, None)

	def getdefault(self, name): # Return the default or None
		return MMAttrdefs.getdefattr(self.node, name)

	def setattr(self, name, value):
		self.editmgr.setnodeattr(self.node, name, value)

	def delattr(self, name):
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
		namelist = ['name', 'title', 'abstract', 'author', 'copyright',
			    'comment', 'layout', 'channel', 'u_group', 'loop',
			    'system_bitrate', 'system_captions',
			    'system_language', 'system_overdub_or_caption',
			    'system_required', 'system_screen_size',
			    'system_screen_depth']
		ntype = self.node.GetType()
		if ntype == 'bag':
			namelist.append('bag_index')
		if ntype == 'par':
			namelist.append('terminator')
		if ntype in ('par', 'seq'):
			namelist.append('duration')
		# Get the channel class (should be a subroutine!)
		ctype = self.node.GetChannelType()
		if channelmap.has_key(ctype):
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.node_attrs
			for name in cclass.chan_attrs:
				if name in namelist: continue
				defn = MMAttrdefs.getdef(name)
				if defn[5] == 'channel':
					namelist.append(name)
			for name in cclass.node_attrs:
				if name in namelist: continue
				namelist.append(name)
		# Merge in nonstandard attributes (except synctolist!)
		extras = []
		for name in self.node.GetAttrDict().keys():
			if name not in namelist and \
				     MMAttrdefs.getdef(name)[3] <> 'hidden':
				extras.append(name)
		extras.sort()
		return namelist + extras


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
			    windowinterface.showmessage('Duplicate channel name (not changed)')
			    return
			self.editmgr.setchannelname(self.channel.name, value)
		else:
			self.editmgr.setchannelattr( \
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
		if channelmap.has_key(ctype):
			cclass = channelmap[ctype]
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
			else:
				# XXXX hack to get bgcolor included
				namelist.append('bgcolor')
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
## 		if not cmifmode():
## 			if 'file' in rv: rv.remove('file')
## 			if 'scale' in rv: rv.remove('scale')
		if ctype == 'layout' and not cmifmode():
			rv.remove('type')
		return rv
	#
	# Override three methods from Wrapper to fake channel name attribute
	#
	def getdef(self, name):
		if name == '.cname':
			# Channelname -- special case
			return (('name', ''), 'none', \
				'Channel name', 'default', \
				'Channel name', 'raw')
		return MMAttrdefs.getdef(name)

	def valuerepr(self, name, value):
		if name == '.cname': name = 'name'
		return MMAttrdefs.valuerepr(name, value)

	def parsevalue(self, name, str):
		if name == '.cname': name = 'name'
		return MMAttrdefs.parsevalue(name, str, self.context)



class DocumentWrapper(Wrapper):
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
		return 'Properties of dcument %s' % self.toplevel.filename

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
		return ''

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
		names = self.context.attributes.keys()
		names.sort()
		return ['title', 'base'] + names

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
	

# Attribute editor class.

from AttrEditDialog import AttrEditorDialog, AttrEditorDialogField

class AttrEditor(AttrEditorDialog):
	def __init__(self, wrapper, new = 0):
		self.__new = new
		self.wrapper = wrapper
		wrapper.register(self)
		self.__open_dialog()

	def __open_dialog(self):
		wrapper = self.wrapper
		list = []
		allnamelist = wrapper.attrnames()
		namelist = []
		for name in allnamelist:
			displayername = wrapper.getdef(name)[3]
			if mustshowdisplayer(displayername):
				namelist.append(name)
		self.__namelist = namelist
		for i in range(len(namelist)):
			name = namelist[i]
			typedef, defaultvalue, labeltext, displayername, \
				 helptext, inheritance = \
				 wrapper.getdef(name)
			if displayername[:4] == 'CMIF':
				displayername = displayername[4:]
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
		self.__list = list
		AttrEditorDialog.__init__(self, wrapper.maketitle(), list)

	def resetall(self):
		for b in self.__list:
			b.reset_callback()

	def restore_callback(self):
		for b in self.__list:
			b.setvalue(b.valuerepr(None))

	def close(self):
		AttrEditorDialog.close(self)
		for b in self.__list:
			b.close()
		self.wrapper.unregister(self)
		if self.__new:
			self.wrapper.delete()
		self.wrapper.close()
		del self.__list
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
		for b in self.__list:
			name = b.getname()
			str = b.getvalue()
			if str != b.getcurrent():
				try:
					value = b.parsevalue(str)
				except:
					windowinterface.showmessage(
						'%s: parsing value failed' % \
							name)
					return 1
				dict[name] = value
		if not dict:
			# nothing to change
			return
		if not self.wrapper.transaction():
			# can't do a transaction
			return 1
		# this may take a while...
		self.wrapper.toplevel.setwaiting()
		for name, value in dict.items():
			self.wrapper.delattr(name)
			if value is not None:
				self.wrapper.setattr(name, value)
		self.wrapper.commit()

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
				AttrEditorDialog.close(self)
				for b in self.__list:
					b.close()
				del self.__list
				self.__open_dialog()
			else:
##				self.fixvalues()
				self.resetall()
				self.settitle(self.wrapper.maketitle())

	def rollback(self):
		pass

	def kill(self):
		self.close()

class AttrEditorField(AttrEditorDialogField):
	type = 'string'

	def __init__(self, attreditor, name, label):
		self.__name = name
		self.label = label
		self.wrapper = attreditor.wrapper
		self.__attrdef = self.wrapper.getdef(name)

	def __repr__(self):
		return '<%s instance, name=%s>' % (self.__class__.__name__,
						   self.__name)

	def getname(self):
		return self.__name

	def gettype(self):
		return self.type

	def getlabel(self):
		return self.label

	def gethelptext(self):
		return 'atribute: %s\n' \
		       'default: %s\n' \
		       '%s' % (self.__name, self.getdefault(),
			       self.__attrdef[4])

	def gethelpdata(self):
		return self.__name, self.getdefault(), self.__attrdef[4]

	def getcurrent(self):
		return self.valuerepr(self.wrapper.getvalue(self.__name))

	def getdefault(self):
		return self.valuerepr(self.wrapper.getdefault(self.__name))

	def valuerepr(self, value):
		"""Return string representation of value."""
		if value is None:
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
		windowinterface.showmessage(self.gethelptext())

class IntAttrEditorField(AttrEditorField):
	type = 'int'

class FloatAttrEditorField(AttrEditorField):
	type = 'float'

class StringAttrEditorField(AttrEditorField):
	def valuerepr(self, value):
		"""Return string representation of value."""
		if value is None:
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
			utype, host, path, params, query, fragment = urlparse.urlparse(url)
			if (utype and utype != 'file') or \
			   (host and host != 'localhost'):
				windowinterface.showmessage('Cannot browse URLs')
				return
			file = MMurl.url2pathname(path)
			file = os.path.join(cwd, file)
			if os.path.isdir(file):
				dir, file = file, ''
			else:
				dir, file = os.path.split(file)
		windowinterface.FileDialog('Choose File for ' + self.label,
					   dir, '*', file, self.__ok_cb, None,
					   existing=1)

	def __ok_cb(self, pathname):
		import MMurl, os
		if os.path.isabs(pathname):
			cwd = self.wrapper.toplevel.dirname
			if cwd:
				cwd = MMurl.url2pathname(cwd)
				if not os.path.isabs(cwd):
					cwd = os.path.join(os.getcwd(), cwd)
			else:
				cwd = os.getcwd()
			if os.path.isdir(pathname):
				dir, file = pathname, os.curdir
			else:
				dir, file = os.path.split(pathname)
			# XXXX maybe should check that dir gets shorter!
			while len(dir) > len(cwd):
				dir, f = os.path.split(dir)
				file = os.path.join(f, file)
			if dir == cwd:
				pathname = file
		self.setvalue(MMurl.pathname2url(pathname))

class TupleAttrEditorField(AttrEditorField):
	type = 'tuple'

	def valuerepr(self, value):
		if type(value) is type(''):
			return value
		return AttrEditorField.valuerepr(self, value)

class ColorAttrEditorField(TupleAttrEditorField):
	type = 'color'
	def parsevalue(self, str):
		import string
		str = string.strip(str)
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

class PopupAttrEditorField(AttrEditorField):
	# A choice menu choosing from a list -- base class only
	type = 'option'

	def getoptions(self):
		# derived class overrides this to defince the choices
		return ['Default']

	def parsevalue(self, str):
		if str == 'Default':
			return None
		return str

	def valuerepr(self, value):
		if value is None:
			return 'Default'
		return value

class PopupAttrEditorFieldWithUndefined(PopupAttrEditorField):
	# This class differs from the one above in that when a value
	# does not occur in the list of options, valuerepr will return
	# 'undefined'.

	def getoptions(self):
		# derived class overrides this to defince the choices
		return ['Default', 'undefined']

	def valuerepr(self, value):
		if value is None:
			return 'Default'
		options = self.getoptions()
		if value not in options:
			return 'undefined'
		return value

	def reset_callback(self):
		self.recalcoptions()

class BoolAttrEditorField(PopupAttrEditorField):
	__offon = ['off', 'on']

	def parsevalue(self, str):
		if str == 'Default':
			return None
		return self.__offon.index(str)

	def valuerepr(self, value):
		if value is None:
			return 'Default'
		return self.__offon[value]

	def getoptions(self):
		return ['Default'] + self.__offon

class UnitsAttrEditorField(PopupAttrEditorField):
	__values = ['mm', 'relative', 'pixels']
	__valuesmap = [windowinterface.UNIT_MM, windowinterface.UNIT_SCREEN,
		       windowinterface.UNIT_PXL]

	# Choose from a list of unit types
	def getoptions(self):
		return ['Default'] + self.__values

	def parsevalue(self, str):
		if str == 'Default':
			return None
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		if value is None:
			return 'Default'
		return self.__values[self.__valuesmap.index(value)]

class TransparencyAttrEditorField(PopupAttrEditorField):
	__values = ['never', 'when empty', 'always']
	__valuesmap = [0, -1, 1]

	# Choose from a list of unit types
	def getoptions(self):
		return ['Default'] + self.__values

	def parsevalue(self, str):
		if str == 'Default':
			return None
		return self.__valuesmap[self.__values.index(str)]

	def valuerepr(self, value):
		if value is None:
			return 'Default'
		return self.__values[self.__valuesmap.index(value)]

class LayoutnameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the current layout names
	def getoptions(self):
		list = self.wrapper.context.layouts.keys()
		list.sort()
		return ['Default', 'undefined'] + list
		
class ChannelnameAttrEditorField(PopupAttrEditorFieldWithUndefined):
	# Choose from the current channel names
	def getoptions(self):
		list = []
		ctx = self.wrapper.context
		for name in ctx.channelnames:
			if ctx.channeldict[name].attrdict['type'] != 'layout':
				list.append(name)
		list.sort()
		return ['Default', 'undefined'] + list

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
		return ['Default', 'undefined'] + list

class UsergroupAttrEditorField(PopupAttrEditorFieldWithUndefined):
	def getoptions(self):
		list = self.wrapper.context.usergroups.keys()
		list.sort()
		return ['Default', 'undefined'] + list

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
		return ['Default', 'undefined'] + list

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
		return ['Default', 'LAST', 'FIRST'] + list

class ChanneltypeAttrEditorField(PopupAttrEditorField):
	# Choose from the standard channel types
	def getoptions(self):
		import ChannelMap
		return ['Default'] + ChannelMap.getvalidchanneltypes()

class FontAttrEditorField(PopupAttrEditorField):
	# Choose from all possible font names
	def getoptions(self):
		fonts = windowinterface.fonts[:]
		fonts.sort()
		return ['Default'] + fonts
