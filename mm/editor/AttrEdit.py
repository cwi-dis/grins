# Attribute editor using the FORMS library (fl, FL)

# XXX This assumes we can create and destroy as many forms as we want.
# That's not actually true: forms never die, they just become inaccessible.
# But there is still hope that we can fix the forms library rather than
# caching old forms here...


import fl
from FL import *

import MMAttrdefs
import MMParser
import MMWrite
from MMExc import *


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
		return # Attribute editor form is already active
	except NameError:
		pass
	#
	attreditor = AttrEditor().init(NodeWrapper().init(node))


def hideattreditor(node):
	try:
		attreditor = node.attreditor
	except NameError:
		return # No attribute editor active
	attreditor.close()
	# XXX What if there are changes?
	# XXX Should ask the user to save them or throw them away.
	# XXX There should be a return value to from hideattreditor()
	# XXX to show if the user wants to cancel whatever caused it...


# An additional call to check whether the attribute editor is currently
# active for a node (so the caller can put up a warning "you are already
# editing this node's attributes" instead of just silence).

def hasattreditor(node):
	try:
		attreditor = node.attreditor
		return 1
	except NameError:
		return 0


# A similar interface for channels (note different arguments!).
# Note that the administration is in context.channelattreditors,
# which is created here if necessary.
#
def showchannelattreditor(context, name):
	try:
		dummy = context.channelattreditors
	except NameError:
		context.channelattreditors = {}
	if context.channelattreditors.has_key(name):
		return
	dummy = AttrEditor().init(ChannelWrapper().init(context, name))

def hidechannelattreditor(context, name):
	try:
		attreditor = context.channelattreditors[name]
	except:
		return
	attreditor.close()

def haschannelattreditor(context, name):
	try:
		attreditor = context.channelattreditors[name]
		return 1
	except:
		return 0


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
		return self
	#
	def maketitle(self):
		return 'Node attributes'
	#
	def link(self, attreditor):
		self.node.attreditor = attreditor
	#
	def unlink(self):
		del self.node.attreditor
	#
	def getcontext(self):
		return self.node.GetContext()
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
	# XXX Should depend on the channel type;
	# XXX currently most known names are returned in alphabetical order.
	#
	def attrnames(self):
		exceptions = ('styledict', 'channellist', 'type')
		namelist = []
		for name in MMAttrdefs.getnames():
			if name not in exceptions:
				namelist.append(name)
		# Merge in any nonstandard attributes
		for name in self.node.GetAttrDict().keys():
			if name not in namelist:
				namelist.append(name)
		namelist.sort()
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
	def link(self, attreditor):
		self.context.channelattreditors[self.name] = attreditor
	#
	def unlink(self):
		del self.context.channelattreditors[self.name]
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
	# XXX Should depend on the channel type;
	# XXX currently most known names are returned in alphabetical order.
	#
	def attrnames(self):
		exceptions = ('styledict', 'channellist', 'channel')
		namelist = []
		for name in MMAttrdefs.getnames():
			if name not in exceptions:
				namelist.append(name)
		# Merge in any nonstandard attributes
		for name in self.attrdict.keys():
			if name not in namelist:
				namelist.append(name)
		namelist.sort()
		return namelist
	#


# Attribute editor class.

class AttrEditor():
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
		itemw3 = 50
		itemw2 = itemwidth/2
		itemw1 = itemwidth - itemw2 - itemw3
		#
		itemx1 = 0
		itemx2 = itemx1 + itemw1
		itemx3 = itemx2 + itemw2
		#
		form = fl.make_form(FLAT_BOX, formwidth, formheight)
		self.form = form
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
		self.makebuttons(formwidth)
		#
		self.getvalues()
		#
		form.show_form(PLACE_SIZE, TRUE, self.wrapper.maketitle())
		# XXX Should have a more meaningful title
		#
		self.wrapper.link(self)
		#
		return self
	#
	def makebuttons(self, width):
		#
		# Add buttons for cancel/restore/apply/OK commands to
		# the bottom of the form, and a hint text between them.
		#
		form = self.form
		#
		x, y, w, h = 2, 2, 66, 26
		#
		x = 2
		cancel = form.add_button(NORMAL_BUTTON, x, y, w, h, 'Cancel')
		cancel.set_call_back(self.cancelcallback, None)
		#
		x = x + 70
		restore = form.add_button(NORMAL_BUTTON, x, y, w, h, 'Restore')
		restore.set_call_back(self.restorecallback, None)
		#
		x = x + 70
		w1 = width - 4*70 - 4
		hint = form.add_text(NORMAL_TEXT, \
			x, y, w1, h, '[Click on labels for help]')
		hint.align = ALIGN_CENTER
		#
		x = width - 70 - 68
		apply = form.add_button(RETURN_BUTTON, x, y, w, h, 'Apply')
		apply.set_call_back(self.applycallback, None)
		#
		x = x + 70
		ok = form.add_button(NORMAL_BUTTON, x, y, w, h, 'OK')
		ok.set_call_back(self.okcallback, None)
		#
		self.globalbuttons = (cancel, restore, hint, apply, ok)
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
		self.form.hide_form()
		self.wrapper.unlink()
		# XXX break circular links...
		# Leave the rest to garbage collection
	#
	def cancelcallback(self, dummy):
		self.close()
	#
	def restorecallback(self, dummy):
		self.getvalues()
	#
	def applycallback(self, dummy):
		self.setvalues()
	#
	def okcallback(self, dummy):
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
		attrdef = MMAttrdefs.getdef(b.name)
		typedef = attrdef[0]
		return MMWrite.valuerepr(value, typedef)
	#
	def parsevalue(b, string):
		attrdef = MMAttrdefs.getdef(b.name)
		typedef = ('enclosed', attrdef[0])
		return MMParser.parsevalue \
			('('+string+')', typedef, b.wrapper.getcontext())
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
