# Node info modeless dialog


import os
import windowinterface

import MMAttrdefs

from MMNode import alltypes, leaftypes, interiortypes

cwd = os.getcwd()

def shownodeinfo(toplevel, node, new = 0):
	try:
		nodeinfo = node.nodeinfo
	except AttributeError:
		nodeinfo = NodeInfo(toplevel, node, new)
		node.nodeinfo = nodeinfo
	else:
		nodeinfo.pop()


class NodeInfo:

	def __init__(self, toplevel, node, new):
		self.new = new
		self.toplevel = toplevel
		self.node = node
		self.context = node.GetContext()
		self.editmgr = self.context.geteditmgr()
		self.root = node.GetRoot()
		self.getvalues(1)
		#
		title = self.maketitle()
		self.window = w = windowinterface.Window(title, resizable = 1,
					deleteCallback = (self.close, ()))

		top = w.SubWindow(left = None, right = None, top = None)

		try:
			i = self.allchannelnames.index(self.channelname)
		except ValueError:
			i = 0		# 'undefined'
		self.channel_select = top.OptionMenu('Channel:',
					self.allchannelnames,
					i, (self.channel_callback, ()),
					right = None, top = None)
		self.type_select = top.OptionMenu('Type:', alltypes,
						  alltypes.index(self.type),
						  (self.type_callback, ()),
						  right = self.channel_select,
						  top = None)
		self.name_field = top.TextInput('Name:', self.name, None, None,
						left = None, top = None,
						right = self.type_select)
		butt = w.ButtonRow(
			[('Cancel', (self.cancel_callback, ())),
			 ('Restore', (self.restore_callback, ())),
			 ('Node attr...', (self.attributes_callback, ())),
			 ('Anchors...', (self.anchors_callback, ())),
			 ('Apply', (self.apply_callback, ())),
			 ('OK', (self.ok_callback, ()))],
			bottom = None, left = None, right = None, vertical = 0)

		midd = w.SubWindow(top = top, bottom = butt, left = None,
				   right = None)

		alter = midd.AlternateSubWindow(top = None, bottom = None,
						right = None, left = None)
		self.imm_group = alter.SubWindow()
		self.ext_group = alter.SubWindow()
		self.int_group = alter.SubWindow()

		self.file_input = self.ext_group.TextInput('File:',
				self.filename,
				(self.file_callback, ()), None,
				top = None, left = None, right = None)
		butt = self.ext_group.ButtonRow(
			[('Edit contents...', (self.conteditor_callback, ())),
			 ('Browser...', (self.browser_callback, ()))],
			top = self.file_input, left = None, right = None,
			vertical = 0)

		butt = self.int_group.ButtonRow(
			[('Open...', (self.openchild_callback, ()))],
			left = None, right = None, bottom = None, vertical = 0)
		self.children_browser = self.int_group.List('Children:',
				self.children,
				[None, (self.openchild_callback, ())],
				top = None, left = None, right = None,
				bottom = butt)

		label = self.imm_group.Label('Contents:',
				top = None, left = None, right = None)
		self.text_browser = self.imm_group.TextEdit(self.immtext, None,
					top = label, left = None,
					right = None, bottom = None)

		self.imm_group.hide()
		self.ext_group.hide()
		self.int_group.hide()
		self.cur_group = None
		self.show_correct_group()

		w.show()

		self.editmgr.register(self)

	def __repr__(self):
		return '<NodeInfo instance, node=' + `self.node` + '>'

	def pop(self):
		self.window.pop()

	def settitle(self, title):
		self.window.settitle(title)

	def transaction(self):
		return 1

	def getcontext(self):
		return self.context

	def stillvalid(self):
		return self.node.GetRoot() is self.root

	def maketitle(self):
		return 'Info for node: ' + self.name

	def getattr(self, name): # Return the attribute or a default
		return MMAttrdefs.getattr(self.node, name)

	def getvalue(self, name): # Return the raw attribute or None
		return self.node.GetRawAttrDef(name, None)

	def getdefault(self, name): # Return the default or None
		return MMAttrdefs.getdefattr(self.node, name)

	def setattr(self, name, value):
		if self.editmgr is not None:   # DEBUG
			self.editmgr.setnodeattr(self.node, name, value)

	def delattr(self, name):
		if self.editmgr is not None:   # DEBUG
			self.editmgr.setnodeattr(self.node, name, None)

	def commit(self):
		if not self.stillvalid():
			self.close()
		else:
			self.settitle(self.maketitle())
			self.getvalues(0)
			self.updateform()

	def rollback(self):
		pass

	def getvalues(self, always):
		#
		# First get all values (except those changed, if
		# always is true)
		#
		self.allchannelnames = ['undefined'] + \
				       self.context.channelnames
		if always:
			self.changed = 0
		if always or not self.ch_name():
			self.name = MMAttrdefs.getattr(self.node, 'name')
		if always or not self.ch_channelname:
			self.origchannelname = self.channelname = \
					       self.node.GetChannelName()
			self.ch_channelname = 0
		if always or not self.ch_type:
			self.type = self.node.GetType()
			self.oldtype = self.type
			self.ch_type = 0
		if always or not self.ch_filename:
			self.filename = MMAttrdefs.getattr(self.node, 'file')
			self.ch_filename = 0
		if always or not self.ch_immtext():
			self.immtext = self.node.GetValues()[:]
		self.children_nodes = self.node.GetChildren()
		self.children = []
		for i in self.children_nodes:
			self.children.append(MMAttrdefs.getattr(i, 'name'))

	def ch_immtext(self):
		if self.type != 'imm':
			return 0
		if hasattr(self, 'immtext') and hasattr(self, 'text_browser'):
			immtext = self.text_browser.getlines()
			if len(immtext) != len(self.immtext):
				self.changed = 1
				return 1
			for i in range(len(immtext)):
				if immtext[i] != self.immtext[i]:
					self.changed = 1
					return 1
		return 0

	def ch_name(self):
		if hasattr(self, 'name') and hasattr(self, 'name_field'):
			name = self.name_field.gettext()
			if name != self.name:
				self.changed = 1
				return 1
		return 0

	def setvalues(self):
		em = self.editmgr
		if not em:   # DEBUG
			return 0
		if not em.transaction():
			return 0
		n = self.node
##		if self.ch_styles_list:
##			em.setnodeattr(n, 'style', self.styles_list[:])
##			self.ch_styles_list = 0
		if self.ch_name():
			self.name = self.name_field.gettext()
			em.setnodeattr(n, 'name', self.name)
		if self.ch_channelname:
			em.setnodeattr(n, 'channel', self.channelname)
			self.ch_channelname = 0
		if self.ch_type:
			if self.oldtype == 'imm' and self.type <> 'imm':
				em.setnodevalues(n, [])
			em.setnodetype(n, self.type)
			self.ch_type = 0
		if self.ch_filename:
			if self.filename:
				em.setnodeattr(n, 'file', self.filename)
			else:
				em.setnodeattr(n, 'file', None)
			self.ch_filename = 0
		if self.ch_immtext():
			self.immtext = self.text_browser.getlines()
			em.setnodevalues(n, self.immtext)
		self.changed = 0
		em.commit()
		return 1
	#
	# Fill form from local data.  Clear the form beforehand.
	#
	def updateform(self):
		self.name_field.settext(self.name)

		self.type_select.setoptions(alltypes,
					    alltypes.index(self.type))

		try:
			i = self.allchannelnames.index(self.channelname)
		except ValueError:
			i = 0		# 'undefined'
		self.channel_select.setoptions(self.allchannelnames, i)

		self.text_browser.settext(self.immtext)

		self.file_input.settext(self.filename)

		self.children_browser.delalllistitems()
		self.children_browser.addlistitems(self.children, -1)
		if self.children:
			self.children_browser.selectitem(0)

		self.imm_group.hide()
		self.ext_group.hide()
		self.int_group.hide()
		self.cur_group = None
		self.show_correct_group()
	#
	# show_correct_group - Show correct type-dependent group of buttons
	#
	def show_correct_group(self):
		if self.type == 'imm':
			group = self.imm_group
		elif self.type == 'ext':
			group = self.ext_group
		else:
			group = self.int_group
		if group is self.cur_group:
			return
		if self.cur_group is not None:
			self.cur_group.hide()
		self.cur_group = group
		if group is not None:
			group.show()

	def close(self):
		self.editmgr.unregister(self)
		self.window.close()
		del self.node.nodeinfo
		del self.node
		del self.toplevel
		del self.context
		del self.editmgr
		del self.root
		del self.window
		del self.channel_select
		del self.type_select
		del self.name_field
		del self.imm_group
		del self.ext_group
		del self.int_group
		del self.file_input
		del self.children_browser
		del self.text_browser
	#
	# Standard callbacks (from Dialog())
	#
	def restore_callback(self):
		self.getvalues(1)
		self.updateform()

	def cancel_callback(self):
		self.close()
		if self.new:
			editmgr = self.editmgr
			if not editmgr.transaction():
				return # Not possible at this time
			editmgr.delnode(self.node)
			editmgr.commit()

	def apply_callback(self):
		self.new = 0
		if self.changed or self.ch_name() or self.ch_immtext():
			dummy = self.setvalues()

	def ok_callback(self):
		self.new = 0
		ok = 1
		if self.changed or self.ch_name() or self.ch_immtext():
			ok = self.setvalues()
		if ok:
			self.close()

	#
	# Callbacks that are valid for all types
	#
	def type_callback(self):
		newtype = self.type_select.getvalue()
		if newtype == self.type:
			return
		# Check that the change is allowed.
		if (self.type in interiortypes) and \
		   (newtype in interiortypes):
			pass	# This is ok.
		elif ((self.type in interiortypes) and \
		      self.children == []) or \
		      (self.type == 'imm' and self.text_browser.gettext() == '') or \
		      (self.type == 'ext'):
			pass
		else:
			windowinterface.showmessage(
				'Cannot change type on non-empty node')
			self.type_select.setpos(alltypes.index(self.type))
			return
		self.ch_type = 1
		self.changed = 1
		self.type = newtype
		self.show_correct_group()

	def channel_callback(self):
		self.channelname = self.channel_select.getvalue()
		if self.origchannelname <> self.channelname:
			self.ch_channelname = 1
			self.changed = 1

	def attributes_callback(self):
		import AttrEdit
		AttrEdit.showattreditor(self.node)

	def anchors_callback(self):
		import AnchorEdit
		AnchorEdit.showanchoreditor(self.toplevel, self.node)
	#
	# Callbacks for 'imm' type nodes
	#

	#
	# Callbacks for 'ext' type nodes
	#
	def file_callback(self):
		filename = self.file_input.gettext()
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
	#
	def browser_callback(self):
		if self.filename == '' or self.filename == '/dev/null':
			dir, file = '', ''
		else:
			if self.filename[-1] == '/':
				dir, file = self.filename, '.'
			else:
				dir, file = os.path.split(self.filename)
		windowinterface.FileDialog('Select file', dir, '*', file,
					   self.browserfile_callback, None)

	def browserfile_callback(self, pathname):
		if pathname[-1] == '/':
			dir, file = pathname, '.'
		else:
			dir, file = os.path.split(pathname)
		if dir == cwd or dir == '.' or dir == '':
			pathname = file
		self.ch_filename = 1
		self.changed = 1
		self.filename = pathname
		self.file_input.settext(pathname)

	def conteditor_callback(self):
		import NodeEdit
		NodeEdit.showeditor(self.node)
	#
	# Callbacks for interior type nodes
	#
	def openchild_callback(self):
		i = self.children_browser.getselected()
		if i is None:
			return
		shownodeinfo(self.toplevel, self.children_nodes[i])


# Routine to close all attribute editors in a node and its context.

def hideall(root):
	hidenode(root)


# Recursively close the attribute editor for this node and its subtree.

def hidenode(node):
	hidenodeinfo(node)
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
		if obj == quitbutton:
			hidenodeinfo(root)
			break
		print 'This object should have a callback!', `obj.label`
