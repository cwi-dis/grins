__version__ = "$Id$"

# Node info modeless dialog


import os
import windowinterface

import MMAttrdefs

from MMTypes import alltypes, leaftypes, interiortypes
# make a copy, but replace "bag" and "alt" with "choice" and "switch".  Use this for user interaction.
Alltypes = alltypes[:]
Alltypes[Alltypes.index('bag')] = 'choice'
Alltypes[Alltypes.index('alt')] = 'switch'

NEW_CHANNEL = 'New channel...'

# this *must* be equal to default channel name in MMNode.GetChannelName
UNDEFINED = 'undefined'

def shownodeinfo(toplevel, node, new = 0):
	try:
		nodeinfo = node.nodeinfo
	except AttributeError:
		nodeinfo = NodeInfo(toplevel, node, new)
		node.nodeinfo = nodeinfo
	else:
		nodeinfo.pop()


from NodeInfoDialog import NodeInfoDialog

class NodeInfo(NodeInfoDialog):

	newchannels = []

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
		try:
			i = self.allchannelnames.index(self.channelname)
		except ValueError:
			i = 0		# 'undefined'
		NodeInfoDialog.__init__(self, title, self.allchannelnames, i,
					Alltypes, alltypes.index(self.type),
					self.name, self.url,
					self.children, self.immtext)
		self.show_correct_group()
		self.editmgr.register(self)

	def __repr__(self):
		return '<NodeInfo instance, node=' + `self.node` + '>'

	def transaction(self):
		return 1

	def getcontext(self):
		return self.context

	def stillvalid(self):
		return self.node.GetRoot() is self.root

	def maketitle(self):
		return 'Info for node ' + self.name

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

	def commit(self):
		if not self.stillvalid():
			self.close()
		else:
			self.settitle(self.maketitle())
			self.getvalues(0)
			self.updateform()

	def rollback(self):
		pass

	def kill(self):
		self.close()

	def calcchannelnames(self):
		layout = MMAttrdefs.getattr(self.node, 'layout')
		if layout == 'undefined':
			layoutchannels = []
			channelnames1 = []
			channelnames2 = self.newchannels[:]
		else:
			layoutchannels = self.context.layouts.get(layout, [])
			channelnames1 = self.newchannels[:]
			channelnames2 = []
		for ch in layoutchannels:
			channelnames1.append(ch.name)
		channelnames1.sort()
		for chname in self.context.channelnames:
			if chname not in channelnames1:
				channelnames2.append(chname)
		channelnames2.sort()
		if channelnames1 and channelnames2:
			# add separator between lists
			sep = [None]
		else:
			sep = []
		allchannelnames = channelnames1 + sep + channelnames2
		if allchannelnames:
			sep = [None]
		else:
			sep = []
		self.allchannelnames = [UNDEFINED] + sep + \
				       allchannelnames + \
				       sep + [NEW_CHANNEL]

	def getvalues(self, always):
		#
		# First get all values (except those changed, if
		# always is true)
		#
		self.calcchannelnames()
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
		if always or not self.ch_url:
			self.url = MMAttrdefs.getattr(self.node, 'file')
			self.ch_url = 0
		if always or not self.ch_immtext():
			self.immtext = self.node.GetValues()[:]
		self.children_nodes = self.node.GetChildren()
		self.children = []
		for i in self.children_nodes:
			self.children.append(
				i.GetRawAttrDef('name', '#' + i.GetUID()))

	def ch_immtext(self):
		if self.type != 'imm':
			return 0
		immtext = self.gettextlines()
		if len(immtext) != len(self.immtext):
			self.changed = 1
			return 1
		for i in range(len(immtext)):
			if immtext[i] != self.immtext[i]:
				self.changed = 1
				return 1
		return 0

	def ch_name(self):
		name = self.getname()
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
			self.name = name = self.getname()
			if name == '':
				name = None
			em.setnodeattr(n, 'name', name)
		if self.ch_channelname:
			if self.channelname not in self.context.channelnames:
				# new channel
				self.newchannel()
			em.setnodeattr(n, 'channel', self.channelname)
			self.ch_channelname = 0
		if self.ch_type:
			if self.oldtype == 'imm' and self.type <> 'imm':
				em.setnodevalues(n, [])
			em.setnodetype(n, self.type)
			self.ch_type = 0
		if self.ch_url:
			if self.url:
				em.setnodeattr(n, 'file', self.url)
			else:
				em.setnodeattr(n, 'file', None)
			self.ch_url = 0
		if self.ch_immtext():
			self.immtext = self.gettextlines()
			em.setnodevalues(n, self.immtext)
		self.changed = 0
		em.commit()
		return 1

	def newchannel(self):
		em = self.editmgr
		context = self.context
		channelname = self.channelname
		try:
			self.newchannels.remove(channelname)
		except ValueError:
			# probably shouldn't happen...
			pass
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
		em.addchannel(channelname, index, self.guesstype())
		ch = context.channeldict[channelname]
		if root:
			from windowinterface import UNIT_PXL, UNIT_SCREEN
			ch['base_window'] = root
			units = ch.get('units', UNIT_SCREEN)
			if units == UNIT_PXL:
				ch['base_winoff'] = 0,0,100,100
			elif units == UNIT_SCREEN:
				ch['base_winoff'] = 0,0,.2,.2
		# if the node belongs to a layout, add the new channel
		# to that layouf
		layout = MMAttrdefs.getattr(self.node, 'layout')
		if layout != 'undefined' and context.layouts.has_key(layout):
			em.addlayoutchannel(layout, ch)

	def guesstype(self):
		# guess channel type from URL
		if self.type == 'imm':
			# assume all immediate nodes are text nodes
			return 'text'
		if self.type != 'ext':
			# interior node, doesn't make much sense
			return 'null'
		import mimetypes, string
		mtype = mimetypes.guess_type(self.url)[0]
		if mtype is None:
			# just guessing now...
			return 'html'
		mtype, subtype = string.split(mtype, '/')
		if mtype == 'audio':
			if subtype == 'vnd.rn-realaudio':
				return 'RealAudio'
			return 'sound'
		if mtype == 'image':
			if subtype == 'vnd.rn-realpix':
				return 'RealPix'
			return 'image'
		if mtype == 'video':
			if subtype == 'vnd.rn-realvideo':
				return 'RealVideo'
			return 'video'
		if mtype == 'text':
			if subtype == 'html':
				return 'html'
			if subtype == 'vnd.rn-realtext':
				return 'RealText'
		# fallback
		return 'text'
	#
	# Fill form from local data.  Clear the form beforehand.
	#
	def updateform(self):
		self.setname(self.name)

		self.settypes(Alltypes, alltypes.index(self.type))

		try:
			i = self.allchannelnames.index(self.channelname)
		except ValueError:
			i = 0		# 'undefined'
		self.setchannelnames(self.allchannelnames, i)

		self.settext(self.immtext)

		self.setfilename(self.url)

		self.setchildren(self.children, 0)

		self.show_correct_group()
	#
	# show_correct_group - Show correct type-dependent group of buttons
	#
	def show_correct_group(self):
		if self.type == 'imm':
			self.imm_group_show()
		elif self.type == 'ext':
			self.ext_group_show()
		else:
			self.int_group_show()

	def close(self):
		if self.editmgr is not None:
			self.editmgr.unregister(self)
			NodeInfoDialog.close(self)
			del self.node.nodeinfo
			del self.node
			del self.toplevel
			del self.context
			del self.root
		self.editmgr = None
	#
	# Standard callbacks (from Dialog())
	#
	def restore_callback(self):
		self.getvalues(1)
		self.updateform()

	def cancel_callback(self):
		if self.new:
			editmgr = self.editmgr
			if not editmgr.transaction():
				return # Not possible at this time
			editmgr.delnode(self.node)
			editmgr.commit()
		self.close()

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
		newtype = self.gettype()
		if newtype == 'choice': newtype = 'bag'
		if newtype == 'switch': newtype = 'alt'
		if newtype == self.type:
			return
		# Check that the change is allowed.
		if (self.type in interiortypes) and \
		   (newtype in interiortypes):
			pass	# This is ok.
		elif ((self.type in interiortypes) and \
		      self.children == []) or \
		      (self.type == 'imm' and self.gettext() == '') or \
		      (self.type == 'ext'):
			pass
		else:
			windowinterface.showmessage(
				'Cannot change type on non-empty node')
			self.settype(alltypes.index(self.type))
			return
		self.ch_type = 1
		self.changed = 1
		self.type = newtype
		self.show_correct_group()

	def channel_callback(self):
		self.channelname = self.getchannelname()
		if self.channelname == NEW_CHANNEL:
			base = 'NEW'
			i = 1
			name = base + `i`
			while self.context.channeldict.has_key(name):
				i = i+1
				name = base + `i`
			self.askchannelname(name)
		elif self.origchannelname <> self.channelname:
			self.ch_channelname = 1
			self.changed = 1

	def newchan_callback(self, name = None):
		all = self.allchannelnames
		self.channelname = name or UNDEFINED
		if self.origchannelname <> self.channelname:
			self.ch_channelname = 1
			self.changed = 1
			if self.channelname not in all:
				self.newchannels.append(self.channelname)
				self.calcchannelnames()
				all = self.allchannelnames
		self.setchannelnames(all, all.index(self.channelname))
			
	def attributes_callback(self):
		import AttrEdit
		AttrEdit.showattreditor(self.toplevel, self.node)

	def chattrs_callback(self):
		import AttrEdit
		channel = self.context.channeldict.get(self.channelname)
		if channel is None:
			windowinterface.showmessage(
				'Unknown channel %s' % self.channelname)
			return
		AttrEdit.showchannelattreditor(self.toplevel, channel)

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
		url = self.getfilename()
		if url <> self.url:
			self.ch_url = 1
			self.changed = 1
			self.url = url
	#
	# File browser callback.
	# There's a bit of hacky code ahead to try and get
	# both reasonable pathnames in the cmif file and reasonable
	# defaults. If the url is empty we select the same
	# directory as last time, and we try to remove the current
	# dir from the resulting pathname.
	#
	def browser_callback(self):
		import MMurl, urlparse
		cwd = self.toplevel.dirname
		if cwd:
			utype, host, path, params, query, fragment = urlparse.urlparse(cwd)
			if (not utype or utype == 'file') and \
			   (not host or host == 'localhost'):
				cwd = MMurl.url2pathname(path)
				if not os.path.isabs(cwd):
					cwd = os.path.join(os.getcwd(), cwd)
			else:
				cwd = os.getcwd()
		else:
			cwd = os.getcwd()
		url = self.url
		if url == '' or url == '/dev/null':
			dir, file = cwd, ''
		else:
			utype, host, path, params, query, fragment = urlparse.urlparse(url)
			if (utype and utype != 'file') or (host and host != 'localhost'):
				windowinterface.showmessage('Cannot browse URLs')
				return
			file = MMurl.url2pathname(path)
			file = os.path.join(cwd, file)
			if os.path.isdir(file):
				dir, file = file, ''
			else:
				dir, file = os.path.split(file)
		windowinterface.FileDialog('Select file', dir, '*', file,
					   self.browserfile_callback, None,
					   existing=1)

	def browserfile_callback(self, pathname):
		import MMurl
		if os.path.isabs(pathname):
			cwd = self.toplevel.dirname
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
		pathname = MMurl.pathname2url(pathname)
		self.ch_url = 1
		self.changed = 1
		self.url = pathname
		self.setfilename(pathname)

	def conteditor_callback(self):
		import NodeEdit
		NodeEdit.showeditor(self.node)
	#
	# Callbacks for interior type nodes
	#
	def openchild_callback(self):
		i = self.getchild()
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
