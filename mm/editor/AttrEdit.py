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

def showattreditor(node):
	try:
		attreditor = node.attreditor
	except AttributeError:
		attreditor = AttrEditor(NodeWrapper(node))
		node.attreditor = attreditor
	attreditor.open()


def hideattreditor(node):
	try:
		attreditor = node.attreditor
	except AttributeError:
		return			# No attribute editor active
	attreditor.hide()

# An additional call to check whether the attribute editor is currently
# active for a node (so the caller can put up a warning "you are already
# editing this node's attributes" instead of just silence).

def hasattreditor(node):
	try:
		attreditor = node.attreditor
	except AttributeError:
		return 0		# No attribute editor active
	return attreditor.is_showing()


# A similar interface for channels (note different arguments!).
# The administration is kept in channel.attreditor,
# which is created here if necessary.

def showchannelattreditor(channel):
	try:
		attreditor = channel.attreditor
	except AttributeError:
		channel.attreditor = attreditor = \
				     AttrEditor(ChannelWrapper(channel))
	attreditor.open()

def hidechannelattreditor(channel):
	try:
		attreditor = channel.attreditor
	except AttributeError:
		return
	attreditor.hide()

def haschannelattreditor(channel):
	try:
		attreditor = channel.attreditor
	except AttributeError:
		return 0
	return attreditor.is_showing()


### And again a similar interface for styles.
### The administration is kept in context.styleattreditors,
### which is created here if necessary.
##
##def showstyleattreditor(context, name):
##	try:
##		dict = context.styleattreditors
##	except AttributeError:
##		dict = context.styleattreditors = {}
##	if not dict.has_key(name):
##		dict[name] = AttrEditor(StyleWrapper(context, name))
##	dict[name].open()
##
##def hidestyleattreditor(context, name):
##	try:
##		dict = context.styleattreditors
##	except AttributeError:
##		return
##	if not dict.has_key(name):
##		return
##	dict[name].hide()
##
##def hasstyleattreditor(context, name):
##	try:
##		dict = context.styleattreditors
##	except AttributeError:
##		return 0
##	if not dict.has_key(name):
##		return 0
##	return dict[name].is_showing()

# The "Wrapper" classes encapsulate the differences between attribute
# editors for nodes and channels.  If you want editors for other
# attribute collections (styles!) you may want to new wrappers.
# All wrappers should support the methods shown here; the __init__()
# method can have different arguments since it is only called from
# the show*() function.  (When introducing a style attr editor
# it should probably be merged with the class attr editor, using
# a common base class implementing most functions.)

class Wrapper: # Base class -- common operations
	def __init__(self, context):
		self.context = context
		self.editmgr = context.geteditmgr()
	def __repr__(self):
		return '<Wrapper instance>'
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
	def parsevalue(self, name, string):
		return MMAttrdefs.parsevalue(name, string, self.context)

class NodeWrapper(Wrapper):
	def __init__(self, node):
		self.node = node
		self.root = node.GetRoot()
		Wrapper.__init__(self, node.GetContext())

	def __repr__(self):
		return '<NodeWrapper instance, node=' + `self.node` + '>'

	def stillvalid(self):
		return self.node.GetRoot() is self.root

	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Attributes for node: ' + name

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
	#
	# Return a list of attribute names that make sense for this node,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = ['name', 'channel', 'comment']
		if self.node.GetType() == 'bag':
			namelist.append('bag_index')
		# Get the channel class (should be a subroutine!)
		ctype = self.node.GetChannelType()
		if channelmap.has_key(ctype):
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.node_attrs
			for name in cclass.chan_attrs:
				if name in namelist: continue
				if MMAttrdefs.getdef(name)[5] == 'channel':
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
	def __init__(self, channel):
		self.channel = channel
		Wrapper.__init__(self, channel.context)

	def __repr__(self):
		return '<ChannelWrapper, name=' + `self.channel.name` + '>'

	def stillvalid(self):
		return self.channel.stillvalid()

	def maketitle(self):
		return 'Attributes for channel: ' + self.channel.name

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
	#
	# Return a list of attribute names that make sense for this channel,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = ['.cname', 'type', 'comment']
		if self.channel.has_key('type'):
			ctype = self.channel['type']
		else:
			ctype = 'unknown'
		if channelmap.has_key(ctype):
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.chan_attrs
			for name in cclass.node_attrs:
				if name in namelist: continue
				if MMAttrdefs.getdef(name)[5] == 'channel':
					namelist.append(name)
		# Merge in nonstandard attributes
		extras = []
		for name in self.channel.keys():
			if name not in namelist and \
					MMAttrdefs.getdef(name)[3] <> 'hidden':
				extras.append(name)
		extras.sort()
		return namelist + extras
	#
	# Override three methods from Wrapper to fake channel name attribute
	#
	def getdef(self, name):
		if name == '.cname':
			# Channelname -- special case
			return (('name', ''), 'none', \
				'Channel name', 'default', \
				'Channel name (not a real attribute)', 'raw')
		return MMAttrdefs.getdef(name)

	def valuerepr(self, name, value):
		if name == '.cname': name = 'name'
		return MMAttrdefs.valuerepr(name, value)

	def parsevalue(self, name, string):
		if name == '.cname': name = 'name'
		return MMAttrdefs.parsevalue(name, string, self.context)


##class StyleWrapper(Wrapper):
##	def __init__(self, context, name):
##		self.name = name
##		self.attrdict = context.styledict[name]
##		Wrapper.__init__(self, context)
##
##	def __repr__(self):
##		return '<StyleWrapper, name=' + `self.name` + '>'
##
##	def stillvalid(self):
##		return self.context.styledict.has_key(self.name) and \
##			self.context.styledict[self.name] == self.attrdict
##
##	def maketitle(self):
##		return 'Attributes for style: ' + self.name
##
##	def getattr(self, name):
##		if self.attrdict.has_key(name):
##			return self.attrdict[name]
##		else:
##			return MMAttrdefs.getdef(name)[1]
##
##	def getvalue(self, name): # Return the raw attribute or None
##		if self.attrdict.has_key(name):
##			return self.attrdict[name]
##		else:
##			return None
##
##	def getdefault(self, name): # Return the default or None
##		return MMAttrdefs.getdef(name)[1]
##
##	def setattr(self, name, value):
##		self.editmgr.setstyleattr(self.name, name, value)
##
##	def delattr(self, name):
##		self.editmgr.setstyleattr(self.name, name, None)
##	#
##	# Return a list of attribute names that make sense for this style,
##	# in an order that makes sense to the user.
##	#
##	def attrnames(self):
##		namelist = ['type', 'channel', 'comment']
##		# Get the channel class (should be a subroutine!)
##		if self.attrdict.has_key('type'):
##			ctype = self.attrdict['type']
##		else:
##			ctype = 'unknown'
##		if channelmap.has_key(ctype):
##			cclass = channelmap[ctype]
##			# Add the class's declaration of attributes
##			for name in cclass.node_attrs + cclass.chan_attrs:
##				if MMAttrdefs.getdef(name)[5] <> 'raw':
##					namelist.append(name)
##		# Merge in nonstandard attributes
##		extras = []
##		for name in self.attrdict.keys():
##			if name not in namelist and \
##					MMAttrdefs.getdef(name)[3] <> 'hidden':
##				extras.append(name)
##		extras.sort()
##		return namelist + extras


# Attribute editor class.

class AttrEditor:
	def __init__(self, wrapper):
		self.wrapper = wrapper
		self.dialog = None

	def open(self):
		self.show()

	def show(self):
		if self.dialog:
			return		# already showing
		self.wrapper.register(self)
		list = []
		self.namelist = self.wrapper.attrnames()
		for name in self.namelist:
			typedef, defaultvalue, labeltext, displayername, \
				 helptext, inheritance = \
				 self.wrapper.getdef(name)
			type = typedef[0]
			if displayername == 'file':
				C = FileButtonRow
			elif displayername == 'font':
				C = FontButtonRow
			elif displayername == 'color':
				C = ColorButtonRow
			elif displayername == 'channelname':
				C = ChannelnameButtonRow
			elif displayername == 'basechannelname':
				C = BaseChannelnameButtonRow
			elif displayername == 'childnodename':
				C = ChildnodenameButtonRow
			elif displayername == 'channeltype':
				C = ChanneltypeButtonRow
			elif type == 'bool':
				C = BoolButtonRow
			elif type == 'name':
				C = NameButtonRow
			elif type == 'string':
				C = StringButtonRow
			elif type == 'int':
				C = IntButtonRow
			elif type == 'float':
				C = FloatButtonRow
			elif type == 'tuple':
				C = TupleButtonRow
			else:
				C = ButtonRow
			b = C(self, name)
			list.append(b.getlistentry())
		self.dialog = windowinterface.AttrDialog(
			self.wrapper.maketitle(), None, list, self.apply,
			self.finish)

	def settitle(self, title):
		self.dialog.settitle(title)

	def finish(self):
		self.wrapper.unregister(self)
		self.dialog = None

	def hide(self):
		if self.dialog:
			self.dialog.close()
		self.dialog = None

	def is_showing(self):
		return self.dialog is not None

	def apply(self, dict):
		if not dict:
			return
		if not self.wrapper.transaction():
			return
		windowinterface.setcursor('watch')
		for name in dict.keys():
			value = dict[name]
			self.wrapper.delattr(name)
			self.wrapper.setattr(name, value)
		self.wrapper.commit()
		windowinterface.setcursor('')

	#
	# EditMgr interface
	#
	def transaction(self):
		return 1

	def commit(self):
		if not self.wrapper.stillvalid():
			self.hide()
		else:
			namelist = self.wrapper.attrnames()
			if namelist != self.namelist:
				# re-open with possibly different size
				if self.is_showing():
					self.hide()
					self.open()
			else:
##				self.fixvalues()
				self.dialog.restore()
				self.settitle(self.wrapper.maketitle())

	def rollback(self):
		pass

class ButtonRow:
	def __init__(self, attreditor, name):
		self.attreditor = attreditor
		self.name = name
		self.wrapper = attreditor.wrapper

	def __repr__(self):
		return '<ButtonRow instance, name='+`self.name`+'>'

	def getlistentry(self):
		attrdef = self.wrapper.getdef(self.name)
		labeltext = attrdef[2]
		if labeltext == '':
			labeltext = self.name
		helptext = 'attribute: ' + self.name + '\n' + \
			   'default: '+self.valuerepr(self.getdefault())+'\n'+\
			   attrdef[4]
		bclass = windowinterface.AttrString
		return self.name, labeltext, helptext, bclass, self

	def getcurrent(self):
		value = self.wrapper.getvalue(self.name)
		if value is None:
			value = self.wrapper.getdefault(self.name)
		return value

	def getdefault(self):
		return self.wrapper.getdefault(self.name)

	def valuerepr(self, value):
		return self.wrapper.valuerepr(self.name, value)

	def parsevalue(self, string):
		return self.wrapper.parsevalue(self.name, string)

class BoolButtonRow(ButtonRow):
	def __repr__(self):
		return '<BoolButtonRow instance, name='+`self.name`+'>'

	def getlistentry(self):
		name, label, help, bclass, s = ButtonRow.getlistentry(self)
		bclass = windowinterface.AttrOption
		return name, label, help, bclass, self, self.choices()

	def valuerepr(self, value):
		if type(value) == type(''):
			return value
		if value:
			return 'on'
		else:
			return 'off'

	def getcurrent(self):
		return self.valuerepr(ButtonRow.getcurrent(self))

	def getdefault(self):
		return self.valuerepr(ButtonRow.getdefault(self))

	def choices(self):
		return ['off', 'on']

class IntButtonRow(ButtonRow):
	def __repr__(self):
		return '<IntButtonRow instance, name='+`self.name`+'>'

	def getlistentry(self):
		name, label, help, bclass, s = ButtonRow.getlistentry(self)
		return name, label, help, windowinterface.AttrInt, self

	def valuerepr(self, value):
		return `value`

	def getcurrent(self):
		return self.valuerepr(ButtonRow.getcurrent(self))

	def getdefault(self):
		return self.valuerepr(ButtonRow.getdefault(self))

class FloatButtonRow(ButtonRow):
	def __repr__(self):
		return '<FloatButtonRow instance, name='+`self.name`+'>'

	def getlistentry(self):
		name, label, help, bclass, s = ButtonRow.getlistentry(self)
		return name, label, help, windowinterface.AttrFloat, self

	def valuerepr(self, value):
		return `value`

	def getcurrent(self):
		return self.valuerepr(ButtonRow.getcurrent(self))

	def getdefault(self):
		return self.valuerepr(ButtonRow.getdefault(self))

class StringButtonRow(ButtonRow):
	def __repr__(self):
		return '<StringButtonRow instance, name='+`self.name`+'>'

	def getlistentry(self):
		name, label, help, bclass, s = ButtonRow.getlistentry(self)
		return name, label, help, windowinterface.AttrString, self

	def parsevalue(self, string):
		return string

NameButtonRow = StringButtonRow

class FileButtonRow(ButtonRow):
	def __repr__(self):
		return '<FileButtonRow instance, name='+`self.name`+'>'

	def getlistentry(self):
		name, label, help, bclass, s = ButtonRow.getlistentry(self)
		return name, label, help, windowinterface.AttrFile, self

	def parsevalue(self, string):
		return string

class TupleButtonRow(ButtonRow):
	def __repr__(self):
		return '<TupleButtonRow instance, name=' + `self.name` + '>'

	def getlistentry(self):
		name, label, help, bclass, s = ButtonRow.getlistentry(self)
		return name, label, help, windowinterface.AttrString, self

	def valuerepr(self, value):
		if type(value) == type(''):
			return value
		return ButtonRow.valuerepr(self, value)

	def getcurrent(self):
		return self.valuerepr(ButtonRow.getcurrent(self))

	def getdefault(self):
		return self.valuerepr(ButtonRow.getdefault(self))

class ColorButtonRow(TupleButtonRow):
	def __repr__(self):
		return '<ColorButtonRow instance, name=' + `self.name` + '>'

	def parsevalue(self, value):
		import string
		value = string.strip(value)
		if value[0] == '#':
			rgb = []
			if len(value) == 4:
				for i in range(1, 4):
					rgb.append(eval('0x' + value[i]) * 16)
			elif len(value) == 7:
				for i in range(1, 6, 2):
					rgb.append(eval('0x' + value[i:i+2]))
			elif len(value) == 13:
				for i in range(1, 13, 4):
					rgb.append(eval('0x' + value[i:i+4])/256)
			else:
				raise RuntimeError, 'Bad color specification'
			value = ''
			for c in rgb:
				value = value + ' ' + `c`
		return TupleButtonRow.parsevalue(self, value)

##ColorButtonRow = TupleButtonRow		# Happens to have the same semantics

class PopupButtonRow(ButtonRow):
	# A choice menu choosing from a list -- base class only
	def __repr__(self):
		return '<PopupButtonRow instance, name=' + `self.name` + '>'

	def getlistentry(self):
		name, label, help, bclass, s = ButtonRow.getlistentry(self)
		bclass = windowinterface.AttrOption
		list = self.choices()
		return name, label, help, bclass, self, list

	def choices(self):
		# derived class overrides this to defince the choices
		return []

class ChannelnameButtonRow(PopupButtonRow):
	# Choose from the current channel names
	def __repr__(self):
		return '<ChannelnameButtonRow instance, name=' \
			+ `self.name` + '>'

	def choices(self):
		list = ['undefined']
		ctx = self.wrapper.context
		for name in ctx.channelnames:
			if ctx.channeldict[name].attrdict['type'] != 'layout':
				list.append(name)
		return list

	def parsevalue(self, value):
		return value

class BaseChannelnameButtonRow(PopupButtonRow):
	# Choose from the current channel names
	def __repr__(self):
		return '<BaseChannelnameButtonRow instance, name=' \
			+ `self.name` + '>'

	def choices(self):
		list = ['undefined']
		ctx = self.wrapper.context
		chname = self.wrapper.channel.name
		for name in ctx.channelnames:
			if name == chname:
				continue
			ch = ctx.channeldict[name]
			if ch.attrdict['type'] == 'layout':
				list.append(name)
		return list

	def parsevalue(self, value):
		return value

class ChildnodenameButtonRow(PopupButtonRow):
	# Choose from the node's children
	def __repr__(self):
		return '<ChildnodenameButtonRow instance, name=' \
			+ `self.name` + '>'

	def choices(self):
		list = ['undefined']
		for child in self.wrapper.node.GetChildren():
			try:
				list.append(child.GetAttr('name'))
			except NoSuchAttrError:
				pass
		return list

	def parsevalue(self, value):
		return value

class ChanneltypeButtonRow(PopupButtonRow):
	# Choose from the standard channel types
	def __repr__(self):
		return '<ChanneltypeButtonRow instance, name=' \
			+ `self.name` + '>'

	def choices(self):
		from ChannelMap import channeltypes
		return channeltypes

class FontButtonRow(PopupButtonRow):
	# Choose from all possible font names
	def __repr__(self):
		return '<FontButtonRow instance, name=' + `self.name` + '>'

	def choices(self):
		fonts = windowinterface.fonts[:]
		fonts.sort()
		return fonts

	def parsevalue(self, string):
		return string
