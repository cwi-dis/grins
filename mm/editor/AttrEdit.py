# Attribute editor using the FORMS library (fl, FL), based upon Dialog.


import fl
from FL import *

import MMExc
import MMAttrdefs
import MMParser
import MMWrite

from ChannelMap import channelmap

from Dialog import Dialog


# There are two basic calls into this module (but see below for more):
# showattreditor(node) creates an attribute editor form for a node
# and hideattreditor(node) hides it again.  Since the editor may also
# hide itself, spurious hide calls are ignored; also, only one attribute
# editor is allowed per node, and extra show calls are also ignored
# (actually, these close and re-open the window to draw attention...).
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


# A similar interface for styles (note different arguments!).
# Note that the administration is in context.styleattreditors,
# which is created here if necessary.
#
def showstyleattreditor(context, name):
	try:
		dict = context.styleattreditors
	except NameError:
		dict = context.styleattreditors = {}
	if not dict.has_key(name):
		dict[name] = \
			AttrEditor().init(StyleWrapper().init(context, name))
	dict[name].open()

def hidestyleattreditor(context, name):
	try:
		dict = context.styleattreditors
	except NameError:
		return
	if not dict.has_key(name):
		return
	dict[name].close()

def hasstyleattreditor(context, name):
	try:
		dict = context.styleattreditors
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

class Wrapper(): # Base class -- common operations
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

class NodeWrapper() = Wrapper():
	#
	def init(self, node):
		self.node = node
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		return self
	#
	def stillvalid(self):
		return self.node.GetRoot() is self.root
	#
	def maketitle(self):
		name = MMAttrdefs.getattr(self.node, 'name')
		return 'Attributes for node: ' + name
	#
	def getattr(self, name): # Return the attribute or a default
		return MMAttrdefs.getattr(self.node, name)
	#
	def getvalue(self, name): # Return the raw attribute or None
		return self.node.GetRawAttrDef(name, None)
	#
	def getdefault(self, name): # Return the default or None
		return MMAttrdefs.getdefattr(self.node, name)
	#
	def setattr(self, (name, value)):
		self.editmgr.setnodeattr(self.node, name, value)
	#
	def delattr(self, name):
		self.editmgr.setnodeattr(self.node, name, None)
	#
	# Return a list of attribute names that make sense for this node,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = ['name', 'channel']
		try:
			# Get the channel class (should be a subroutine!)
			cname = MMAttrdefs.getattr(self.node, 'channel')
			cattrs = self.context.channeldict[cname]
			ctype = cattrs['type']
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.node_attrs
			for name in cclass.chan_attrs:
				if name in namelist: continue
				if MMAttrdefs.getdef(name)[5] = 'channel':
					namelist.append(name)
			namelist = namelist + cclass.node_attrs
		except:
			pass # Ignore errors in the above
		# Merge in nonstandard attributes (except synctolist!)
		extras = []
		for name in self.node.GetAttrDict().keys():
			if name not in namelist and name <> 'synctolist':
				extras.append(name)
		extras.sort()
		return namelist + extras
	#


class ChannelWrapper() = Wrapper():
	#
	def init(self, (context, name)):
		self.context = context
		self.editmgr = context.geteditmgr()
		self.name = name
		self.attrdict = self.context.channeldict[name]
		return self
	#
	def stillvalid(self):
		return self.context.channeldict.has_key(self.name) and \
			self.context.channeldict[self.name] = self.attrdict
	#
	def maketitle(self):
		return 'Attributes for channel: ' + self.name
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
	def getdefault(self, name): # Return the default or None
		return MMAttrdefs.getdef(name)[1]
	#
	def setattr(self, (name, value)):
		self.editmgr.setchannelattr(self.name, name, value)
	#
	def delattr(self, name):
		self.editmgr.setchannelattr(self.name, name, None)
	#
	# Return a list of attribute names that make sense for this channel,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = ['type']
		try:
			ctype = self.attrdict['type']
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			namelist = namelist + cclass.chan_attrs
			for name in cclass.node_attrs:
				if name in namelist: continue
				if MMAttrdefs.getdef(name)[5] = 'channel':
					namelist.append(name)
		except:
			pass # Ignore errors in the above
		# Merge in nonstandard attributes
		extras = []
		for name in self.attrdict.keys():
			if name not in namelist:
				extras.append(name)
		extras.sort()
		return namelist + extras
	#


class StyleWrapper() = Wrapper():
	#
	def init(self, (context, name)):
		self.context = context
		self.editmgr = context.geteditmgr()
		self.name = name
		self.attrdict = self.context.styledict[name]
		return self
	#
	def stillvalid(self):
		return self.context.styledict.has_key(self.name) and \
			self.context.styledict[self.name] = self.attrdict
	#
	def maketitle(self):
		return 'Attributes for style: ' + self.name
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
	def getdefault(self, name): # Return the default or None
		return MMAttrdefs.getdef(name)[1]
	#
	def setattr(self, (name, value)):
		self.editmgr.setstyleattr(self.name, name, value)
	#
	def delattr(self, name):
		self.editmgr.setstyleattr(self.name, name, None)
	#
	# Return a list of attribute names that make sense for this style,
	# in an order that makes sense to the user.
	#
	def attrnames(self):
		namelist = ['type', 'channel']
		try:
			# Get the channel class (should be a subroutine!)
			ctype = self.attrdict['type']
			cclass = channelmap[ctype]
			# Add the class's declaration of attributes
			for name in cclass.node_attrs + cclass.chan_attrs:
				if MMAttrdefs.getdef(name)[5] <> 'raw':
					namelist.append(name)
		except:
			pass # Ignore errors in the above
		# Merge in nonstandard attributes
		extras = []
		for name in self.attrdict.keys():
			if name not in namelist:
				extras.append(name)
		extras.sort()
		return namelist + extras
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
	def transaction(self):
		return 1
	#
	def commit(self):
		if not self.wrapper.stillvalid():
			self.close()
		else:
			self.fixvalues()
	#
	def rollback(self):
		pass
	#
	def open(self):
		self.close()
		self.title = self.wrapper.maketitle()
		self.getvalues()
		self.wrapper.register(self)
		self.show()
	#
	def getvalues(self):
		self.form.freeze_form()
		for b in self.blist: b.getvalue()
		self.changed = 0
		self.fixbuttons()
		self.form.unfreeze_form()
	#
	def setvalues(self):
		if not self.wrapper.transaction(): return 0
		self.form.freeze_form()
		for b in self.blist: b.setvalue()
		self.changed = 0
		self.fixbuttons()
		self.form.unfreeze_form()
		self.wrapper.commit()
		return 1
	#
	def fixvalues(self):
		self.fixfocus()
		changed = 0
		self.form.freeze_form()
		for b in self.blist:
			b.fixvalue()
			if b.changed: changed = 1
		self.changed = changed
		self.fixbuttons()
		self.form.unfreeze_form()
	#
	def close(self):
		if self.showing:
			self.wrapper.unregister(self)
			self.hide()
	#
	def fixbuttons(self):
		if self.changed:
			boxtype = UP_BOX
		else:
			boxtype = FRAME_BOX
		for b in self.ok_button,self.apply_button,self.restore_button:
			b.boxtype = boxtype
	#
	def cancel_callback(self, dummy):
		self.close()
	#
	def restore_callback(self, (obj, arg)):
		obj.set_button(1)
		self.getvalues()
		obj.set_button(0)
	#
	def apply_callback(self, (obj, arg)):
		obj.set_button(1)
		self.fixfocus()
		if self.changed:
			dummy = self.setvalues()
		obj.set_button(0)
	#
	def ok_callback(self, (obj, arg)):
		obj.set_button(1)
		self.fixfocus()
		if not self.changed or self.setvalues():
			self.close()
		obj.set_button(0)
	#
	def fixfocus(self):
		for b in self.blist:
			if b.value.focus:
				b.valuecallback(b.value, None)
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
		b.label = b.form.add_text(NORMAL_TEXT, x, y, w-1, h, labeltext)
	#
	def makehelpbutton(b, (x, y, w, h)):
		b.help = b.form.add_button(HIDDEN_BUTTON, x, y, w-1, h, '')
		b.help.set_call_back(b.helpcallback, None)
	#
	def makevalueinput(b, (x, y, w, h)):
		b.value = b.form.add_input(NORMAL_INPUT, x, y, w-1, h, '')
		b.value.lstyle = FIXED_STYLE
		b.value.set_call_back(b.valuecallback, None)
	#
	def makeresetbutton(b, (x, y, w, h)):
		b.reset = b.form.add_button(PUSH_BUTTON, x, y, w-1, h, 'reset')
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
		if b.changed:
			if b.isdefault:
				b.wrapper.delattr(b.name)
			else:
				b.wrapper.setattr(b.name, b.currentvalue)
		b.getvalue()
	#
	def fixvalue(b):
		if b.isdefault and b.changed:
			b.currentvalue = b.wrapper.getdefault(b.name)
			b.update()
		elif not b.changed:
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
		except (EOFError, MMExc.SyntaxError, MMExc.TypeError), msg:
			if type(msg) <> type(''):
				found, expected = msg
				if expected = ')':
					expected = ') or EOF'
				msg = 'found ' + `found` + \
					', expected ' + expected
			msg2 = 'for attribute ' + b.name
			fl.show_message('Syntax error', msg2, msg)
			b.update()
			return
		b.changed = b.attreditor.changed = 1
		b.currentvalue = value
		b.isdefault = 0
		b.update()
		b.attreditor.fixbuttons()
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
		b.attreditor.fixbuttons()
	#
	def update(b):
		b.currenttext = b.valuerepr(b.currentvalue)
		b.value.set_input(b.currenttext[:INPUT_MAX-1])
		b.reset.set_button(b.isdefault)
		if b.isdefault and not b.changed:
			b.reset.hide_object()
		else:
			if b.changed:
				b.reset.boxtype = UP_BOX
			else:
				b.reset.boxtype = FRAME_BOX
			b.reset.show_object()
	#
	def valuerepr(b, value):
		return MMAttrdefs.valuerepr(b.name, value)
	#
	def parsevalue(b, string):
		return MMAttrdefs.parsevalue \
			(b.name, string, b.wrapper.getcontext())
	#


# Routine to close all attribute editors in a node and its context.

def closeall(root):
	closenode(root)
	context = root.GetContext()
	for cname in root.GetContext().channeldict.keys():
		hidechannelattreditor(context, cname)
	for cname in root.GetContext().styledict.keys():
		hidestyleattreditor(context, cname)


# Recursively close the attribute editor for this node and its subtree.

def closenode(node):
	hideattreditor(node)
	if node.GetType() in ('seq', 'par'):
		for child in node.GetChildren():
			closenode(child)


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
