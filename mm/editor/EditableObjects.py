__version__ = "$Id:"

# This file will contain the base objects for the various views.
# There is meant to be one and only one instance of this class;
# All editing classes should be able to share one instance of this class.

# These classes are related to the MMNode hierarchy by association only;
# ideally it would use inheritance but that would interfere too much
# with the rest of the system.

# This module has NOTHING TO DO WITH DRAWING OR INTERACTING with nodes;
# the drawing, clicking and so forth is done in higher-level objects.

# These classes could also form a layer of abstraction with the edit
# manager - the only place the routines in the edit manager need to
# be called from is here.

import MMNode, MMExc
import windowinterface
from usercmd import *

######################################################################
# Editing MMNodes.

class EditableMMNode(MMNode.MMNode):
	# Editable version of an MMNode.
	def __init__(self, type, context, uid):
		MMNode.MMNode.__init__(self, type, context, uid)
		self.showtime = 0

	def GetName(self):
		# I'm used by the event editor dialog.
		# print "DEBUG: GetName"
		try:
			return self.GetAttr('name')
		except MMExc.NoSuchAttrError:
			return "not_yet_defined"
	#def GetType(self) - defined in MMNode.py
	
	# Used for the user interface
	def GetCommands(self):		# returns a list of mapped commands
		print "DEBUG: GetCommands"
		commands = self.__get_commands()
		if not self.IsLeafNode():
			commands = commands + self.__get_interiorcommands() + self.__get_structurecommands()
		if not self is self.context.root:
			commands = commands + self.__get_pastenotatrootcommands() + self.__get_notatrootcommands()
		return commands

	def IsLeafNode(self):
		print "DEBUG: IsLeafNode"
		if self.type in MMNode.interiortypes:
			return 0
		else:
			return 1

	def __get_commands(self):
		print "DEBUG: _get_commands"
		# Non-specific standard commands.
		return [
			COPY(callback = (self.copycall, ())),
			COPYPROPERTIES(callback = (self.copypropertiescall, ())),
			PASTEPROPERTIES(callback = (self.pastepropertiescall, ())),
			ATTRIBUTES(callback = (self.attrcall, ())),
			CONTENT(callback = (self.editcall, ())),
			PLAYNODE(callback = (self.playcall, ())),
			PLAYFROM(callback = (self.playfromcall, ())),
			]
	def __get_interiorcommands(self):
		print "DEBUG: _get_interiorcommands"
		return [
			NEW_UNDER(callback = (self.createundercall, ())),
			NEW_UNDER_SEQ(callback = (self.createunderintcall, ('seq',))),
			NEW_UNDER_PAR(callback = (self.createunderintcall, ('par',))),
			NEW_UNDER_SWITCH(callback = (self.createunderintcall, ('switch',))),
			NEW_UNDER_EXCL(callback = (self.createunderintcall, ('excl',))),
			NEW_UNDER_IMAGE(callback = (self.createundercall, ('image',))),
			NEW_UNDER_SOUND(callback = (self.createundercall, ('sound',))),
			NEW_UNDER_VIDEO(callback = (self.createundercall, ('video',))),
			NEW_UNDER_TEXT(callback = (self.createundercall, ('text',))),
			NEW_UNDER_HTML(callback = (self.createundercall, ('html',))),
			]
	def __get_pastenotatrootcommands(self):
		return [
			PASTE_BEFORE(callback = (self.pastebeforecall, ())),
			PASTE_AFTER(callback = (self.pasteaftercall, ())),
			]
	def __get_notatrootcommands(self):
		return [
			NEW_SEQ(callback = (self.createseqcall, ())),
			NEW_PAR(callback = (self.createparcall, ())),
			# What are these? Excl and Switch? Do them later anyway.
			#NEW_SWITCH(callback = (self.createaltcall, ())),
			DELETE(callback = (self.deletecall, ())),
			CUT(callback = (self.cutcall, ())),
			]
	def __get_structurecommands(self):
		return [
			NEW_BEFORE(callback = (self.createbeforecall, ())),
			NEW_BEFORE_SEQ(callback = (self.createbeforeintcall, ('seq',))),
			NEW_BEFORE_PAR(callback = (self.createbeforeintcall, ('par',))),
			NEW_BEFORE_SWITCH(callback = (self.createbeforeintcall, ('switch',))),
			NEW_AFTER(callback = (self.createaftercall, ())),
			NEW_AFTER_SEQ(callback = (self.createafterintcall, ('seq',))),
			NEW_AFTER_PAR(callback = (self.createafterintcall, ('par',))),
			NEW_AFTER_SWITCH(callback = (self.createafterintcall, ('switch',))),
			]

	# /Not/ system independant.
#	def GetContextMenu(self):	# returns a context menu that can be used with the windowinterface.
#		t = self.GetType()
#		if t in MMNode.interiortypes:
#			return POPUP_HVIEW_STRUCTURE
#		else:
#			return POPUP_HVIEW_LEAF

	# Viewing this node. Helper routines for widgets only.
	def GetThumbnailFile(self):	# returns a thumbnail.
		print "DEBUG: GetThumbNailFile"
		pass
		
	def GetTypeIconFile(self):	# returns a filename for an icon representing the type of node that this is.
		print "DEBUG: GetTypeIconFile"
		channel_type = self.GetChannelType()
		if not channel_type:
			return None
		import os, cmif
		f = os.path.join(cmif.findfile('GRiNS-Icons'), '%s.tiff'%channel_type)
		return f
		
	def GetColor(self):		# returns a default "color" for this type of node.
		print "DEBUG: GetColor"
		pass

	def SetURL(self, url):
		print "DEBUG: SetURL"
		if self.IsLeafNode():
			em = self.context.editmgr
			if not em.transaction():
				return
			self.SetAttr('file',url)
			em.commit()
		else:
			# Add a new node here. This is a structure node.
			em = self.context.editmgr
			#f not em.transaction():
			#	return
			# WORKING HERE.
			# I need a channel also.

	def _insertnode(self, node, index):
		print "DEBUG: _insertnode"
		# insert a node at position index.
		em = self.context.editmgr
		if node is None:
			assert 0
		if len(self.children) < 1:
			em.addnode(self, 0, node)
			return
		elif index == -1:
			# Insert node at end.
			em.addnode(self, len(self.children), node)
			return
		else:
			em.addnode(self, index, node)

#	def _newleafnode(self, name=None, url=None, region=None):
	def _newleafnode(self, url):
		print "DEBUG: _newleafnode"
		# returns a new node with this particular name, url and region
		node = self.context.newnode('ext')
		if url:
			node.SetAttr('file', url)
		#if region:
		#	print "DEBUG: Region is: ", region
		#	assert isinstance(region, type(""))
		#	node.SetAttr('channel', region)
		#if name:
		# Set the name for this node. I don't know how.
		return node

#	def NewLeafNode(self, name='', url='', index = -1, region = ''):
	def NewLeafNode(self, url, channel):
		print "DEBUG: NewLeafNode"
		em = self.context.editmgr
		if not em.transaction():
			return
		newnode = self._newleafnode(url) # Ahh.. this is a bit wrong?
		self._insertnode(newnode, -1)
		print "DEBUG: region is: ", channel
		newnode.SetAttr('channel', channel)
		em.commit()

	def NewBeginEvent(self, othernode, event):
		# I'm called from the HierarchyView
		#print "DEBUG: NewBeginEvent"
		em = self.context.editmgr
		if not em.transaction():
			return
		e = MMNode.MMSyncArc(self, 'begin', srcnode=othernode, event=event, delay=0)
		em.addsyncarc(self, 'beginlist', e)
		em.commit()

	def GetCollapsedParent(self):
		# I'm used by the event editor.
		#print "DEBUG: GetCollapsedParent"
		i = self.parent		# Don't return self if I'm collapsed.
		while i is not None:
			if i.collapsed == 1:
				return i
			else:
				i = i.parent
		return None


######################################################################
	# Commands from the menus.
	# Note that the commands should control the EditMgr - they
	# are essentually macro-level commands that use the methods above. -mjvdg.

	def playcall(self):
		print "DEBUG: playcall"
		self.context.toplevel.player.playsubtree(self)

	def playfromcall(self):
		print "DEBUG: playfromcall"
		self.context.toplevel.player.playfrom(self)

	def attrcall(self):
		print "DEBUG: attrcall"
		windowinterface.setwaiting()
		import AttrEdit
		AttrEdit.showattreditor(self.context.toplevel, self)

	def editcall(self):
		windowinterface.setwaiting()
		import NodeEdit
		NodeEdit.showeditor(self)

	#def anchorcall(self):
	#	if self.focusobj: self.focusobj.anchorcall()

	#def createanchorcall(self):
	#	if self.focusobj: self.focusobj.createanchorcall()

	#def hyperlinkcall(self):
	#	if self.focusobj: self.focusobj.hyperlinkcall()

	def deletecall(self):
		print "TODO: fixsyncarcs (in HierarchyView.py)"
		editmgr = self.context.editmgr
		if not editmgr.transaction(): # Start a transaction.
			return
		windowinterface.setwaiting()
		editmgr.delnode(self)
		editmgr.commit()

	def cutcall(self):
		print "TODO: fixsyncarcs (in HierarchyView.py)"		
		em = self.context.editmgr
		#if not em.transaction():
		#	return
		windowinterface.setwaiting()
		t,n = em.getclip()
		if t == 'node' and n is not None:
			n.Destroy()
		em.setclip('node', self)
		#em.delnode(self)
		#em.commit()

	def copycall(self):
		print "DEBUG: copycall"
		windowinterface.setwaiting()
		em = self.context.editmgr
		t,n = em.getclip()
		if t == 'node' and n is not None:
			n.Destroy()	# Wha ha ha ha. <evil grin>
		copyme = self.DeepCopy()
		em.setclip('node', copyme)
##	def createbeforecall(self, chtype=None):
##		assert 0

##	def createbeforeintcall(self, ntype):
##		assert 0
##		if self.focusobj: self.focusobj.createbeforeintcall(ntype)

##	def createaftercall(self, chtype=None):
##		assert 0
##		if self.focusobj: self.focusobj.createaftercall(chtype)

##	def createafterintcall(self, ntype):
##		assert 0
##		if self.focusobj: self.focusobj.createafterintcall(ntype)

##	def createundercall(self, chtype=None):
##		assert 0
##		if self.focusobj: self.focusobj.createundercall(chtype)

##	def createunderintcall(self, ntype=None):
##		assert 0
##		if self.focusobj: self.focusobj.createunderintcall(ntype)

##	def createseqcall(self):
##		assert 0
##		if self.focusobj: self.focusobj.createseqcall()

##	def createparcall(self):
##		assert 0
##		if self.focusobj: self.focusobj.createparcall()

##	def createexclcall(self):
##		assert 0
##		if self.focusobj: self.focusobj.createexclcall()

	def pastebeforecall(self):
		# Paste before a node.
		print "DEBUG: pastebeforecall"
		if self.parent is None:
			windowinterface.showmessage("You can't paste before the root!")
			return
		em = self.context.editmgr
		pasteme = None
		i = self.parent.children.index(self) - 1
		t,n = em.getclip()
		if t == 'node' and n is not None:
			pasteme = n
		else:
			windowinterface.showmessage("There is nothing on the clipboard!")
			return
		
		if not em.transaction():
			return
		self.parent._insertnode(pasteme, i)
		em.commit()

	def pasteaftercall(self):
		print "DEBUG: pasteaftercall"
		# Paste after a node
		if self.parent is None:
			windowinterface.showmessage("You can't paste after the root!")
			return
		i = self.parent.children.index(self) + 1
		em = self.context.editmgr
		t,n = em.getclip()
		if t == 'node' and n is not None:
			pasteme = n
		else:
			windowinterface.showmessage("There is not a node on the clipboard!")
			return

		if not em.transaction():
			return
		self.parent._insertnode(pasteme, i)
		em.commit()
		
	def pasteundercall(self, index):
		print "DEBUG: pasteundercall"
		# Index is the index of this node.
		if self.IsLeafNode():
			windowinteface.beep()
			return
		else:
			em = self.context.editmgr
			t,n = em.getclip()
			if t == 'node' and n is not None:
				pasteme = n
			else:
				windowinterface.showmessage("There is not a node on the clipboard!")
				return
			if not em.transaction():
				return
			self._insertnode(pasteme, index)
			em.commit()
		
	def copypropertiescall(self):
		if not hasattr(windowinterface, 'mmultchoice'):
			windowinterface.beep()
			return
		attrlist = self.getattrnames()
		defattrlist = attrlist[:]
		# Remove ones we don't normally copy
		if 'name' in defattrlist:
			defattrlist.remove('name')
		copylist = windowinterface.mmultchoice('Select properties to copy', attrlist, defattrlist)
		if not copylist: return
		dict = {}
		for k in copylist:
			dict[k] = self.attrdict[k]
		# XXXX Clear clip
		self.context.editmgr.setclip('properties', dict)

	def pastepropertiescall(self):
		em = self.context.editmgr
		tp, clipvalue = em.getclip()
		if tp != 'properties':
			windowinterface.beep()
			return
		allowedlist = self.getallattrnames()
		allowed = {}
		for k in allowedlist:
			allowed[k] = 1
		prop = {}
		for k, v in clipvalue.items():
			if allowed.has_key(k):
				prop[k] = v
		if not prop:
			windowinterface.beep()
			return
		if not em.transaction():
			return
		for k, v in prop.items():
			em.setnodeattr(self, k, v)
		em.commit()
		
	def take(self, othernode, index):
		print "DEBUG: take"
		# othernode is a leafnode or sub-tree that I'm going to grab and put under me.
		# index is which of my children it will be.
		em = self.context.editmgr
		if isinstance(othernode, EditableMMNode) \
		   and not self.IsAncestorOf(othernode) \
		   and othernode is not self.context.root \
		   and othernode not in self.children \
		   and index < len(self.children) \
		   and em.transaction():
			em.delnode(othernode)
			em.addnode(self, index, othernode)
			em.commit()
			
