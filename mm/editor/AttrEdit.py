# Attribute editor using the FORMS library (fl, FL), based upon Dialog.


import fl
from FL import *

import MMAttrdefs
import MMParser
import MMWrite
from MMExc import *

from ChannelMap import channelmap

from Dialog import Dialog


# There are two basic calls into this module (but see below for more):
# showattreditor(node) creates an attribute editor form for a node
# and hideattreditor(node) hides it again.  Since the editor may also
# hide itself, spurious hide calls are ignored; also, only one attribute
# editor is allowed per node, and extra show calls are also ignored.
# Hiding the editor when the user has changed part of it may ask the
# user what should be done about this -- this part of the interface
# hasn't been completely thought out yet.
# Likewise, what should be done when the node has changed somehow
# while the attribute editor was active?

def showattreditor(node):
	try:
		attreditor = node.attreditor
	except NameError:
		attreditor = AttrEditor().init(NodeWrapper().init(node))
		node.attreditor = attreditor
	attreditor.open()


def hideattreditor(node):
	try:
		attreditor = node.attreditor
	except NameError:
		return # No attribute editor active
	attreditor.close()


# An additional call to check whether the attribute editor is currently
# active for a node (so the caller can put up a warning "you are already
# editing this node's attributes" instead of just silence).

def hasattreditor(node):
	try:
		attreditor = node.attreditor
	except NameError:
		return 0 # No attribute editor active
	return attreditor.showing


# A similar interface for channels (note different arguments!).
# Note that the administration is in context.channelattreditors,
# which is created here if necessary.
#
def showchannelattreditor(context, name):
	try:
		dict = context.channelattreditors
	except NameError:
		dict = context.channelattreditors = {}
	if not dict.has_key(name):
		dict[name] = \
			AttrEditor().init(ChannelWrapper().init(context, name))
	dict[name].open()

def hidechannelattreditor(context, name):
	try:
		dict = context.channelattreditors
	except NameError:
		return
	if not dict.has_key(name):
		return
	dict[name].close()

def haschannelattreditor(context, name):
	try:
		dict = context.channelattreditors
	except NameError:
		return 0
	if not dict.has_key(name):
		return 0
	return dict[name].showing


# The "Wrapper" classes encapsulate the differences between attribute
# editors for nodes and channels.  If you want editors for other
# attribute collections (styles!) you may want to new wrappers.
# All wrappers should support the methods shown here; the init()
# method can have different arguments since it is only called from
# the show*() function.  (When introducing a style attr editor
# it should probably be merged with the class attr editor, using
# a common base class implementing most functions.)

class NodeWrapper():
	#
	def init(self, node):
		self.node = node
		self.context = node.GetContext()
		return self
	#
	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Node attributes for ' + name
	#
	def getcontext(self):
		return self.context
	#
	def getattr(self, name): # Return the attribute or a default
		return MMAttrdefs.getattr(self.node, name)
	#
	def getvalue(self, name): # Return the raw attribute or None
		return self.node.GetRawAttrDef(name, None)
	#
	def getdefault(self, name):
		try:
			return self.node.GetDefAttr(name)
		except NoSuchAttrError:
			pass
		p = self.node.GetParent()
		if p = None:
			default = None
		else:
			default = p.GetInherAttrDef(name, None)
		if default = None:
			default = MMAttrdefs.getdef(name)[1]
		return default
	#
	def setattr(self, (name, value)):
		self.node.SetAttr(name, value)
	#
	def delattr(self, name):
		try:
			self.node.DelAttr(name)
		except NoSuchAttrError:
			pass
	#
	# Return a list of attribute names that make sense for this node,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = []
		try:
			# Get the channel class (should be a subroutine!)
			cname = MMAttrdefs.getattr(self.node, 'channel')
			cattrs = self.context.channeldict[cname]
			ctype = cattrs['type']
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.node_attrs
		except:
			pass # Ignore errors in the above
		# Merge in nonstandard attributes
		for name in self.node.GetAttrDict().keys():
			if name not in namelist:
				namelist.append(name)
		return namelist
	#


class ChannelWrapper():
	#
	def init(self, (context, name)):
		self.context = context
		self.name = name
		self.attrdict = self.context.channeldict[name]
		return self
	#
	def maketitle(self):
		return 'Channel attributes for ' + self.name
	#
	def getcontext(self):
		return self.context
	#
	def getattr(self, name):
		if self.attrdict.has_key(name):
			return self.attrdict[name]
		else:
			return MMAttrdefs.getdef(name)[1]
	#
	def getvalue(self, name): # Return the raw attribute or None
		if self.attrdict.has_key(name):
			return self.attrdict[name]
		else:
			return None
	#
	def getdefault(self, name):
		return MMAttrdefs.getdef(name)[1]
	#
	def setattr(self, (name, value)):
		self.attrdict[name] = value
	#
	def delattr(self, name):
		if self.attrdict.has_key(name):
			del self.attrdict[name]
	#
	# Return a list of attribute names that make sense for this channel,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = []
		try:
			ctype = self.attrdict['type']
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.chan_attrs
			for name in cclass.node_attrs:
				if name in namelist: continue
				attrdef = MMAttrdefs.getdef(name)
				if attrdef[5] = 'channel':
					namelist.append(name)
		except:
			pass # Ignore errors in the above
		# Merge in nonstandard attributes
		for name in self.attrdict.keys():
			if name not in namelist:
				namelist.append(name)
		return namelist
	#


# Attribute editor class.

class AttrEditor() = Dialog():
	#
	def init(self, wrapper):
		#
		self.wrapper = wrapper
		self.namelist = wrapper.attrnames()
		#
		itemwidth = 450
		itemheight = 25
		#
		formwidth = itemwidth
		formheight = len(self.namelist) * itemheight + 30
		#
		title = self.wrapper.maketitle()
		hint = '[Click on labels for help]'
		self = Dialog.init(self, (formwidth, formheight, title, hint))
		#
		itemw3 = 50
		itemw2 = itemwidth/2
		itemw1 = itemwidth - itemw2 - itemw3
		#
		itemx1 = 0
		itemx2 = itemx1 + itemw1
		itemx3 = itemx2 + itemw2
		#
		form = self.form
		#
		self.blist = []
		#
		for i in range(len(self.namelist)):
			itemy = formheight - (i+1)*itemheight
			name = self.namelist[i]
			b = ButtonRow().init(self, name)
			b.makelabeltext(itemx1, itemy, itemw1, itemheight)
			b.makehelpbutton(itemx1, itemy, itemw1, itemheight)
			b.makevalueinput(itemx2, itemy, itemw2, itemheight)
			b.makeresetbutton(itemx3, itemy, itemw3, itemheight)
			self.blist.append(b)
		#
		return self
	#
	def open(self):
		self.close()
		self.getvalues()
		self.show()
	#
	def getvalues(self):
		self.form.freeze_form()
		for b in self.blist: b.getvalue()
		self.form.unfreeze_form()
		self.changed = 0
	#
	def setvalues(self):
		self.form.freeze_form()
		for b in self.blist: b.setvalue()
		self.form.unfreeze_form()
		self.changed = 0
	#
	def close(self):
		self.hide()
	#
	def cancel_callback(self, dummy):
		self.close()
	#
	def restore_callback(self, dummy):
		self.getvalues()
	#
	def apply_callback(self, dummy):
		self.setvalues()
	#
	def ok_callback(self, dummy):
		self.setvalues()
		self.close()
	#


# Class for one attribute definitition.

class ButtonRow():
	#
	def init(b, (attreditor, name)):
		b.attreditor = attreditor
		b.name = name
		b.wrapper = attreditor.wrapper
		b.form = attreditor.form
		return b
	#
	def makelabeltext(b, (x, y, w, h)):
		attrdef = MMAttrdefs.getdef(b.name)
		labeltext = attrdef[2]
		if labeltext = '': labeltext = b.name
		b.label = b.form.add_text(NORMAL_TEXT, x, y, w, h, labeltext)
	#
	def makehelpbutton(b, (x, y, w, h)):
		b.help = b.form.add_button(HIDDEN_BUTTON, x, y, w, h, '')
		b.help.set_call_back(b.helpcallback, None)
	#
	def makevalueinput(b, (x, y, w, h)):
		b.value = b.form.add_input(NORMAL_INPUT, x, y, w, h, '')
		b.value.lstyle = FIXED_STYLE
		b.value.set_call_back(b.valuecallback, None)
	#
	def makeresetbutton(b, (x, y, w, h)):
		b.reset = b.form.add_button(PUSH_BUTTON, x, y, w, h, 'reset')
		b.reset.set_call_back(b.resetcallback, None)
	#
	def getvalue(b):
		value = b.wrapper.getvalue(b.name)
		default = b.wrapper.getdefault(b.name)
		b.defaultvalue = default
		if value = None:
			b.currentvalue = default
			b.isdefault = 1
		else:
			b.currentvalue = value
			b.isdefault = 0
		b.lastvalue = b.currentvalue
		b.changed = 0
		b.update()
	#
	def setvalue(b):
		if b.value.focus:
			b.valuecallback(b.value, None)
		if b.changed:
			if b.isdefault:
				b.wrapper.delattr(b.name)
			else:
				b.wrapper.setattr(b.name, b.currentvalue)
		b.getvalue()
	#
	def helpcallback(b, dummy):
		attrdef = MMAttrdefs.getdef(b.name)
		fl.show_message('attribute: ' + b.name, \
			'default: ' + b.valuerepr(b.defaultvalue), \
			attrdef[4])
		# 
	#
	def valuecallback(b, dummy):
		newtext = b.value.get_input()[:INPUT_MAX-1]
		if newtext = b.currenttext[:INPUT_MAX-1]:
			return # No change
		try:
			value = b.parsevalue(newtext)
		except (EOFError, SyntaxError, TypeError), msg:
			if type(msg) <> type(''):
				found, expected = msg
				msg = 'found ' + `found` + \
					', expected ' + expected
			fl.show_message('Type/Syntax error', msg, '')
			b.update()
			return
		b.changed = b.attreditor.changed = 1
		b.currentvalue = value
		b.isdefault = 0
		b.update()
	#
	def resetcallback(b, dummy):
		b.changed = b.attreditor.changed = 1
		b.isdefault = b.reset.get_button()
		if b.isdefault:
			b.lastvalue = b.currentvalue
			b.currentvalue = b.defaultvalue
		else:
			b.currentvalue = b.lastvalue
		b.update()
	#
	def update(b):
		b.currenttext = b.valuerepr(b.currentvalue)
		b.value.set_input(b.currenttext[:INPUT_MAX-1])
		b.reset.set_button(b.isdefault)
	#
	def valuerepr(b, value):
		return MMAttrdefs.valuerepr(b.name, value)
	#
	def parsevalue(b, string):
		return MMAttrdefs.parsevalue \
			(b.name, string, b.wrapper.getcontext())
	#


# Test program -- edit the attributes of the root node.

def test():
	import sys, MMTree
	if sys.argv[1:]:
		filename = sys.argv[1]
	else:
		filename = 'demo.cmif'
	#
	print 'parsing', filename, '...'
	root = MMTree.ReadFile(filename)
	#
	print 'quit button ...'
	quitform = fl.make_form(FLAT_BOX, 50, 50)
	quitbutton = quitform.add_button(NORMAL_BUTTON, 0, 0, 50, 50, 'Quit')
	quitform.set_form_position(600, 10)
	quitform.show_form(PLACE_POSITION, FALSE, 'QUIT')
	#
	print 'showattreditor ...'
	showattreditor(root)
	#
	print 'go ...'
	while 1:
		obj = fl.do_forms()
		if obj = quitbutton:
			hideattreditor(root)
			break
		print 'This object should have a callback!', `obj.label`
