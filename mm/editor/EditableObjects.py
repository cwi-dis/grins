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

	def copypropertiescall(self):
		if not hasattr(windowinterface, 'mmultchoice'):
			windowinterface.beep()
			return
		attrlist = self.getattrnames()
		defattrlist = attrlist[:]
		# Remove ones we don't normally copy
		if 'name' in defattrlist:
			defattrlist.remove('name')
		if 'file' in defattrlist:
			defattrlist.remove('file')
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
		
