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

def showchannelattreditor(channel, new = 0):
	try:
		attreditor = channel.attreditor
	except AttributeError:
		channel.attreditor = attreditor = \
				     AttrEditor(ChannelWrapper(channel))
	attreditor.open(new)

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
		self.new = 0
		self.wrapper = wrapper
		self.dialog = None

	def open(self, new = 0):
		self.new = new
		self.show()

	def show(self):
		if self.dialog:
			self.dialog.show()
			return
		self.wrapper.register(self)
		list = []
		self.namelist = self.wrapper.attrnames()
		self.dialog = windowinterface.Window(self.wrapper.maketitle(),
				     resizable = 1,
				     deleteCallback = (self.hide, ()))
		buttons = self.dialog.ButtonRow(
			[('Cancel', (self.hide, ())),
			 ('Restore', (self.restore, ())),
			 ('Apply', (self.apply, ())),
			 ('Ok', (self.apply, (1,)))],
			left = None, right = None, bottom = None, vertical = 0)
		sep = self.dialog.Separator(left = None, right = None,
					    bottom = buttons)
		form = self.dialog.SubWindow(left = None, right = None,
					     bottom = sep, top = None)
		height = 1.0 / len(self.namelist)
		l = r = w = None
		self.list = list
		for i in range(len(self.namelist)):
			name = self.namelist[i]
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
			b = C(self, name, labeltext)
			l = form.Button(labeltext,
					(self.showhelp, (b,)),
					top = l, left = None, right = 0.5,
					bottom = (i+1)*height)
			r = form.Button('Reset', (self.reset, (b,)),
					top = r, right = None,
					bottom = (i+1)*height)
			b.createwidget(form, l, r, w, (i+1)*height)
			w = b.widget
			list.append(b)
		self.dialog.show()

	def settitle(self, title):
		self.dialog.settitle(title)

	def showhelp(self, b):
		windowinterface.showmessage(b.gethelptext())

	def reset(self, b):
		b.setvalue(b.getcurrent())

	def resetall(self):
		for b in self.list:
			b.setvalue(b.getcurrent())

	def restore(self):
		for b in self.list:
			b.setvalue(None)

	def hide(self):
		if self.dialog:
			self.dialog.close()
			self.wrapper.unregister(self)
		self.dialog = None
		self.list = []
		if self.new:
			self.wrapper.delete()

	def apply(self, remove = 0):
		self.new = 0
		# first collect all changes
		dict = {}
		for b in self.list:
			try:
				value = b.getvalue()
			except:
				windowinterface.showmessage(
					'%s: parsing value failed' %
						b.name)
				return
			cur = b.getcurrent()
			if value != cur:
				dict[b.name] = (value, b)
		if not dict:
			# nothing to change
			if remove:
				self.hide()
			return
		if not self.wrapper.transaction():
			# can't do a transaction
			return
		# this may take a while...
		if remove:
			self.hide()
		windowinterface.setcursor('watch')
		for name, (value, b) in dict.items():
			self.wrapper.delattr(name)
			if value is not None:
				self.wrapper.setattr(name, value)
		self.wrapper.commit()
		windowinterface.setcursor('')

	def is_showing(self):
		return self.dialog is not None

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
				self.resetall()
				self.settitle(self.wrapper.maketitle())

	def rollback(self):
		pass

class ButtonRow:
	def __init__(self, attreditor, name, label):
		self.attreditor = attreditor
		self.name = name
		self.label = label
		self.wrapper = attreditor.wrapper
		self.attrdef = self.wrapper.getdef(name)

	def __repr__(self):
		return '<ButtonRow instance, name='+`self.name`+'>'

	def gethelptext(self):
		return 'attribute: ' + self.name + '\n' + \
		       'default: '+self.valuerepr(self.getdefault())+'\n'+\
		       self.attrdef[4]

	def createwidget(self, parent, left, right, top, bottom):
		cur = self.getcurrent()
		if cur is None:
			value = ''
		else:
			value = self.valuerepr(cur)
		self.widget = parent.TextInput(
			None, value, None, None,
			top = top, bottom = bottom, left = left, right = right)

	def getcurrent(self):
		return self.wrapper.getvalue(self.name)

	def getdefault(self):
		return self.wrapper.getdefault(self.name)

	def getvalue(self):
		value = self.widget.gettext()
		if value == '':
			return None
		else:
			return self.parsevalue(value)

	def setvalue(self, value):
		if value is None:
			text = ''
		else:
			text = self.valuerepr(value)
		self.widget.settext(text)

	def valuerepr(self, value):
		return self.wrapper.valuerepr(self.name, value)

	def parsevalue(self, string):
		return self.wrapper.parsevalue(self.name, string)

class IntButtonRow(ButtonRow):
	def __repr__(self):
		return '<IntButtonRow instance, name='+`self.name`+'>'

class FloatButtonRow(ButtonRow):
	def __repr__(self):
		return '<FloatButtonRow instance, name='+`self.name`+'>'

class StringButtonRow(ButtonRow):
	def __repr__(self):
		return '<StringButtonRow instance, name='+`self.name`+'>'

	def parsevalue(self, value):
		return value

	def valuerepr(self, value):
		return value

NameButtonRow = StringButtonRow

class FileButtonRow(ButtonRow):
	def __repr__(self):
		return '<FileButtonRow instance, name='+`self.name`+'>'

	def createwidget(self, parent, left, right, top, bottom):
		but = parent.Button('Brwsr', (self.browser, ()),
				    top = top, bottom = bottom, right = right)
		cur = self.getcurrent()
		if cur is None:
			cur = ''
		self.widget = parent.TextInput(None, cur,
					       None, None,
					       top = top, bottom = bottom,
					       left = left, right = but)

	def browser(self):
		file = self.widget.gettext()
		if file == '' or file == '/dev/null':
			dir, file = '.', ''
		else:
			import os
			if os.path.isdir(file):
				dir, file = file, ''
			else:
				dir, file = os.path.split(file)
		windowinterface.FileDialog('Choose File for ' + self.label,
					   dir, '*', file, self.ok_cb, None)

	def ok_cb(self, filename):
		import os
		cwd = os.getcwd()
		if filename[:len(cwd)] == cwd:
			filename = filename[len(cwd):]
			if filename and filename[0] != '/':
				filename = cwd + filename
			elif filename:
				filename = filename[1:]
			else:
				filename = '.'
		self.widget.settext(filename)

	def parsevalue(self, value):
		return value

	def valuerepr(self, value):
		return value

class TupleButtonRow(ButtonRow):
	def __repr__(self):
		return '<TupleButtonRow instance, name=' + `self.name` + '>'

	def valuerepr(self, value):
		if type(value) is type(''):
			return value
		return ButtonRow.valuerepr(self, value)

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

class PopupButtonRow(ButtonRow):
	# A choice menu choosing from a list -- base class only
	def __repr__(self):
		return '<PopupButtonRow instance, name=' + `self.name` + '>'

	def createwidget(self, parent, left, right, top, bottom):
		choices = ['None'] + self.choices()
		current = self.getcurrent()
		if current is None:
			current = 'None'
			cur = 0
		else:
			try:
				cur = choices.index(self.valuerepr(current))
			except ValueError:
				cur = 0
		if len(choices) > 30:
			but = parent.Button('Choose', (self. choose, ()),
					    top = top, bottom = bottom,
					    right = right)
			self.widget = parent.TextInput(
				None, current, None, None, top = top,
				bottom = bottom, left = left, right = but)
			self.isoption = 0
		else:
			self.widget = parent.OptionMenu(
				None, choices, cur, None, top = top,
				bottom = bottom, left = left, right = right)
			self.isoption = 1

	def choose(self):
		if self.isoption:
			func = self.widget.setvalue
		else:
			func = self.widget.settext
		self.choosewin = SelectionDialog(self.widget.gettext(),
						 ['None'] + self.choices(),
						 func)

	def getvalue(self):
		if self.isoption:
			value = self.widget.getvalue()
		else:
			value = self.widget.gettext()
			if value not in ['None'] + self.choices():
				raise RuntimeError, '%s not a valid option' % value
		if value == 'None':
			return None
		return self.parsevalue(value)

	def setvalue(self, value):
		if value is None:
			value = 'None'
		else:
			value = self.valuerepr(value)
		if self.isoption:
			self.widget.setvalue(value)
		else:
			self.widget.settext(value)

	def choices(self):
		# derived class overrides this to defince the choices
		return []

	def parsevalue(self, value):
		return value

	def valuerepr(self, value):
		return value

class BoolButtonRow(PopupButtonRow):
	offon = ['off', 'on']

	def __repr__(self):
		return '<BoolButtonRow instance, name='+`self.name`+'>'

	def parsevalue(self, value):
		return self.offon.index(value)

	def valuerepr(self, value):
		return self.offon[value]

	def choices(self):
		return self.offon

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

class BaseChannelnameButtonRow(ChannelnameButtonRow):
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

class SelectionDialog(windowinterface.SelectionDialog):
	def __init__(self, default, choices, setfunc):
		self.OkCallback = setfunc
		windowinterface.SelectionDialog.__init__(
			self, 'Channels', None, choices, default)

	def NomatchCallback(self, value):
		return '%s not a valid choice' % value
