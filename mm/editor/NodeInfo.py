# Node info editor using the FORMS library (fl, FL), based upon Dialog.


import path
import posix
import string
import fl
import gl
from FL import *
import flp

import MMExc
import MMAttrdefs
import MMParser
import MMWrite

import NodeEdit

from MMNode import alltypes, leaftypes, interiortypes

# from ChannelMap import channelmap

from Dialog import Dialog

FORMWIDTH=535
FORMHEIGHT=255

class Struct(): pass
_global = Struct()

_global.cwd = posix.getcwd()+'/'
_global.dir = ''
_global.forms = None


# There are two basic calls into this module (but see below for more):
# shownodeinfo(node) creates an node info form for a node
# and hidenodeinfo(node) hides it again.  Since the editor may also
# hide itself, spurious hide calls are ignored; also, only one node
# info form is allowed per node, and extra show calls are also ignored
# (actually, these close and re-open the window to draw attention...).
# Hiding the form when the user has changed part of it may ask the
# user what should be done about this -- this part of the interface
# hasn't been completely thought out yet.

def _shownodeinfo(node,new):
	try:
		nodeinfo = node.nodeinfo
	except NameError:	# BCOMPAT
		nodeinfo = NodeInfo().init(node)
		node.nodeinfo = nodeinfo
	except AttributeError:
		nodeinfo = NodeInfo().init(node)
		node.nodeinfo = nodeinfo
	nodeinfo.open(new)

def shownodeinfo(node): _shownodeinfo(node,0)

def shownewnodeinfo(node): _shownodeinfo(node,1)

def hidenodeinfo(node):
	try:
		nodeinfo = node.nodeinfo
	except NameError:	# BCOMPAT
		return
	except AttributeError:
		return # No node info form active
	nodeinfo.close()


# An additional call to check whether the node info form is currently
# active for a node (so the caller can put up a warning "you are already
# editing this node's attributes" instead of just silence).

def hasnodeinfo(node):
	try:
		nodeinfo = node.nodeinfo
	except NameError:	# BCOMPAT
		return 0
	except AttributeError:
		return 0 # No node info form active
	return nodeinfo.showing
#
#

class NodeInfo() = Dialog():
	def init(self, node):
		self.node = node
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		self.getvalues(TRUE)
		#
		title = self.maketitle()
		self = Dialog.init(self, (FORMWIDTH, FORMHEIGHT, title,''))
		if _global.forms = None:
		    _global.forms = flp.parse_forms('NodeInfoForm')
		#
		for i in _global.forms.keys():
		    flp.merge_full_form(self, self.form, _global.forms[i])
		self.text_input.set_input_return(1)
		#
		return self
	#
	def transaction(self):
		self.fixfocus()
		return 1
	#
	def getcontext(self):
		return self.context
	def register(self, object):
		if self.editmgr <> None:   # DEBUG
		    self.editmgr.register(object)
	def unregister(self, object):
		if self.editmgr <> None:   # DEBUG
		    self.editmgr.unregister(object)
	#
	def stillvalid(self):
		return self.node.GetRoot() is self.root
	#
	def maketitle(self):
		return 'Info for node: ' + self.name
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
		if self.editmgr <> None:   # DEBUG
		    self.editmgr.setnodeattr(self.node, name, value)
	#
	def delattr(self, name):
		if self.editmgr <> None:   # DEBUG
		    self.editmgr.setnodeattr(self.node, name, None)
	#
	def commit(self):
		if not self.stillvalid():
			self.close()
		else:
			self.getvalues(FALSE)
			self.updateform()
			gl.winset(self.form.window)
			gl.wintitle(self.maketitle())
	#
	def rollback(self):
		pass
	#
	def open(self,new):
		self.close()
		self.title = self.maketitle()
		self.getvalues(TRUE)
		self.updateform()
		self.register(self)
		self.show()
	#
	def getvalues(self, always):
		#
		# First get all values (except those changed, if
		# always is true)
		#
		self.allchannelnames = ['undefined'] + \
			self.context.channelnames
		self.allstyles = self.context.styledict.keys()
		self.allstyles.sort()
		if always:
		    self.changed = 0
		if always or not self.ch_styles_list:
		    self.styles_list = \
				self.node.GetRawAttrDef('style',[])[:]
		    self.ch_styles_list = 0
		if always or not self.ch_name:
		    self.name = MMAttrdefs.getattr(self.node, 'name')
		    self.ch_name = 0
		if always or not self.ch_channelname:
		    self.origchannelname = self.channelname = \
			    MMAttrdefs.getattr(self.node, 'channel')
		    self.ch_channelname = 0
		if always or not self.ch_type:
		    self.type = self.node.GetType()
		    self.oldtype = self.type
		    self.ch_type = 0
		if always or not self.ch_filename:
		    self.filename = \
				MMAttrdefs.getattr(self.node, 'file')
		    self.ch_filename = 0
		if always or not self.ch_immtext:
		    self.immtext =  \
			self.node.GetValues()[:]
		    self.immtext.append('')
		    self.ch_immtext = 0
		self.children_nodes = self.node.GetChildren()
		self.children = []
		for i in self.children_nodes:
		    self.children.append(MMAttrdefs.getattr(i,'name'))
	#
	def setvalues(self):
		em = self.editmgr
		n = self.node
		if not em.transaction(): return 0
		if self.ch_styles_list:
		    em.setnodeattr(n, 'style', self.styles_list[:])
		    self.ch_styles_list = 0
		if self.ch_name:
		    em.setnodeattr(n, 'name', self.name)
		    self.ch_name = 0
		if self.ch_channelname:
		    em.setnodeattr(n, 'channel', self.channelname)
		    self.ch_channelname = 0
		if self.ch_type:
		    if self.oldtype = 'imm' and self.type <> 'imm':
			em.setnodevalues(n,[])
			self.ch_immtext = 0
		    em.setnodetype(n, self.type)
		    self.ch_type = 0
		if self.ch_filename:
		    if self.filename:
			em.setnodeattr(n, 'file', self.filename)
		    else:
			em.setnodeattr(n, 'file', None)
		    self.ch_filename = 0
		if self.ch_immtext:
		    em.setnodevalues(n, self.immtext[:])
		    self.ch_immtext = 0
		self.changed = 0
		em.commit()
		return 1
	#
	# updateform - Fill form from local data. Will clear the
	# form beforehand.
	#
	def updateform(self):
	    self.form.freeze_form()
	    self.name_field.set_input(self.name)
	    #
	    self.type_select.clear_choice()
	    for i in alltypes:
		self.type_select.addto_choice(i)
	    self.type_select.set_choice(alltypes.index(self.type)+1)
	    #
	    self.channel_select.clear_choice()
	    for i in self.allchannelnames:
		self.channel_select.addto_choice(i)
	    try:
		self.channel_select.set_choice(self.allchannelnames.index(self.channelname)+1)
	    except RuntimeError:	# BCOMPAT
		self.channel_select.set_choice(0)
	    except ValueError:
		self.channel_select.set_choice(0)
	    #
	    self.styles_browser.clear_browser()
	    for i in self.styles_list:
		self.styles_browser.add_browser_line(i)
	    #
	    self.styles_select.clear_choice()
	    for i in self.allstyles:
		self.styles_select.addto_choice(i)
	    if self.allstyles:
		self.styles_select.set_choice(1)
	    #
	    self.text_browser.clear_browser()
	    for i in self.immtext:
		self.text_browser.add_browser_line(i)
	    self.text_browser.select_browser_line(1)
	    self.text_input.set_input(self.immtext[0])
	    #
	    self.file_input.set_input(self.filename)
	    #
	    self.children_browser.clear_browser()
	    for i in self.children:
		self.children_browser.add_browser_line(i)
	    if self.children:
		self.children_browser.select_browser_line(1)
	    #
	    self.imm_group.hide_object()
	    self.ext_group.hide_object()
	    self.int_group.hide_object()
	    self.cur_group = None
	    self.show_correct_group()
	    self.form.unfreeze_form()
	#
	# show_correct_group - Show correct type-dependent group of buttons
	#
	def show_correct_group(self):
	    if self.type = 'imm':
		group = self.imm_group
	    elif self.type = 'ext':
		group = self.ext_group
	    else:
		group = self.int_group
	    if group = self.cur_group:
		return
	    if self.cur_group <> None:
		self.cur_group.hide_object()
	    self.cur_group = group
	    if group <> None:
		group.show_object()
	#
	#
	def close(self):
		if self.showing:
			self.unregister(self)
			self.hide()
	#
	# Standard callbacks (from Dialog())
	#
	def cancel_callback(self, dummy):
		self.close()
	#
	def restore_callback(self, (obj, arg)):
		self.getvalues(TRUE)
		self.updateform()
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
		if self.name_field.focus:
		    self.name_callback(self.name_field,0)
		if self.text_input.focus:
		    self.text_input_callback(self.text_input, 0)
		if self.file_input.focus:
		    self.file_callback(self.file_input, 0)
	#
	#
	# Callbacks that are valid for all types
	#
	def dummy_callback(self, (obj, dummy)): pass
	def name_callback(self, (obj,dummy)):
	    name = obj.get_input()
	    if name <> self.name:
		self.ch_name = 1
		self.changed = 1
		self.name = name
	def type_callback(self, (obj,dummy)):
	    newtype = obj.get_choice_text()
	    self.fixfocus()
	    if newtype = self.type:
		return
	    # Check that the change is allowed.
	    if (self.type in interiortypes) and \
			(newtype in interiortypes):
		pass	# This is ok.
	    elif ((self.type in interiortypes) and \
			self.children = []) or \
		 (self.type = 'imm' and len(self.immtext) = 1) or \
		 (self.type = 'ext'):
		pass
	    else:
		fl.show_message('Cannot change type on', 'non-empty node', '')
		self.type_select.set_choice(alltypes.index(self.type)+1)
		return
	    self.ch_type = 1
	    self.changed = 1
	    self.type = newtype
	    self.show_correct_group()
	def channel_callback(self, (obj,dummy)):
	    self.channelname = obj.get_choice_text()
	    if self.origchannelname <> self.channelname:
		self.ch_channelname = 1
		self.changed = 1
	def styles_add_callback(self, (obj,dummy)):
	    i = self.styles_select.get_choice()
	    if i = 0: return
	    self.ch_styles_list = 1
	    self.changed = 1
	    new = self.allstyles[i-1]
	    if not new in self.styles_list:
		self.styles_list.append(new)
		self.styles_browser.add_browser_line(new)
		self.styles_browser.deselect_browser()
		self.styles_browser.select_browser_line(len(self.styles_list))
	def styles_delete_callback(self, (obj,dummy)):
	    i = self.styles_browser.get_browser()
	    if i:
		self.ch_styles_list = 1
		self.changed = 1
		self.styles_browser.delete_browser_line(i)
		del self.styles_list[i-1]
		self.styles_browser.select_browser_line(1)
	def attributes_callback(self, (obj,dummy)):
		import AttrEdit
		AttrEdit.showattreditor(self.node)
	#
	# Callbacks for 'imm' type nodes
	#
	def text_browser_callback(self, (obj,dummy)):
	    i = obj.get_browser()
	    if i:
		line = obj.get_browser_line(i)
		self.text_input.set_input(line)
	def text_input_callback(self, (obj,dummy)):
	    line = obj.get_input()
	    i = self.text_browser.get_browser()
	    if i:
		if line = self.immtext[i-1]: return
		self.ch_immtext = 1
		self.changed = 1
		self.text_browser.replace_browser_line(i, line)
		self.immtext[i-1] = line
		# Did we change the dummy last line?
		if i = len(self.immtext):
		    self.immtext.append('')
		    self.text_browser.addto_browser('')
	    else:
		print 'HUH? No textline selected?'
	def text_insert_callback(self, (obj,dummy)):
	    i = self.text_browser.get_browser()
	    if i:
		self.ch_immtext = 1
		self.changed = 1
		self.text_browser.insert_browser_line(i, '')
		self.immtext.insert(i, '')
		self.text_input.set_input('')
		self.text_browser.deselect_browser()
		self.text_browser.select_browser_line(i)
	def text_delete_callback(self, (obj,dummy)):
	    i = self.text_browser.get_browser()
	    if i and i <> len(self.immtext):
		self.ch_immtext = 1
		self.changed = 1
		self.text_browser.delete_browser_line(i)
		del self.immtext[i-1]
		self.text_browser.select_browser_line(i)
		line = self.text_browser.get_browser_line(i)
		self.text_input.set_input(line)
	#
	# Callbacks for 'ext' type nodes
	#
	def file_callback(self, (obj,dummy)):
	    filename = obj.get_input()
	    if filename <> self.filename:
		self.ch_filename = 1
		self.changed = 1
		self.filename = filename
	#
	# File browser callback.
	# There's a bit of hacky code ahead to try and get
	# both reasonable pathnames in the cmif file and reasonable
	# defaults. If the filename is empty we select the same
	# directory as last time, and we try to remove the current
	# dir from the resulting pathname.
	def browser_callback(self, (obj,dummy)):
	    dir, file = path.split(self.filename)
	    if file = '' or self.filename = '/dev/null': # YUCK!
		dir = _global.dir
		file = ''
	    result = fl.file_selector('Select file', dir, '*', file)
	    if result:
		try:
		    if string.index(result,_global.cwd) = 0:
			result = result[len(_global.cwd):]
		except string.index_error:
		    pass
		dir, file = path.split(result)
		_global.dir = dir
	    if result and result <> self.filename:
		self.ch_filename = 1
		self.changed = 1
		self.filename = result
		self.file_input.set_input(result)
	def conteditor_callback(self, (obj, dummy)):
	    NodeEdit.showeditor(self.node)
	#
	# Callbacks for interior type nodes
	#
	def openchild_callback(self, (obj, dummy)):
	    i = self.children_browser.get_browser()
	    if i = 0: return
	    shownodeinfo(self.children_nodes[i-1])

# Routine to close all attribute editors in a node and its context.

def hideall(root):
	hidenode(root)

# Recursively close the attribute editor for this node and its subtree.

def hidenode(node):
	hidenodeinfo(node)
	if node.GetType() in interiortypes:
		for child in node.GetChildren():
			hidenode(child)


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
	print 'shownodeinfo ...'
	shownodeinfo(root)
	#
	print 'go ...'
	while 1:
		obj = fl.do_forms()
		if obj = quitbutton:
			hidenodeinfo(root)
			break
		print 'This object should have a callback!', `obj.label`
