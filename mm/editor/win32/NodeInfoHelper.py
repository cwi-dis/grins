__version__ = "$Id$"


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


class NodeInfoHelper:

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
			self.maketitle()
			self.getvalues(0)

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
		#name = self.getname()
		#if name != self.name:
		#	self.changed = 1
		#	return 1
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
#		if self.ch_name():
#			self.name = name = self.getname()
#			if name == '':
#				name = None
#			em.setnodeattr(n, 'name', name)
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



	def close(self):
		if self.editmgr is not None:
			self.editmgr.unregister(self)
			#NodeInfoDialog.close(self)
			#del self.node.nodeinfo
			del self.node
			del self.toplevel
			del self.context
			del self.root
		self.editmgr = None

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
	# Callbacks for 'ext' type nodes
	#
	def file_callback_X(self):
		url = self.getfilename()
		if url <> self.url:
			self.ch_url = 1
			self.changed = 1
			self.url = url

	def browserfile_callback(self, pathname):
		if self.type != 'ext':return
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
		#self.setfilename(pathname)





