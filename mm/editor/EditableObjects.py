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

from MMNode import *;

######################################################################
# Editing MMNodes.

__nodes = {}
__editmgr = None
__mmcontext = None

def create_MMNode_editable(node):
	# node : MMNode
	# This returns an editable of that MMNode.
	assert isinstance(node, MMNode)
	if __nodes.has_key(node):
		return __nodes[node]
	else:
		# create a new node depending on it's type.
		if node.type in interiortypes:
			bob = EditableInternalMMNode(node)
			# Insert extra object construction <<here.
			bob.setup()
			return bob
		else:
			bob = EditableLeafMMNode(node)
			bob.setup()
			return bob

class EditableMMNode:
	# Abstract base class. You shouldn't have a concrete instance of this.
	def __init__(self, n):
		self.__node = n
	def setup(self):			# like a constructer, but without parameters.
		pass
	def get_iter(self):
		assert 0
	def set_region(self):
		assert 0
	def get_region(self):		# Returns a EditableRegion thing.
		assert 0
	def get_name(self):
		return self.__node.GetAttr('name')

	# Editing this node.. some are callbacks for the commands returned by get_commands()
	def get_cut(self):		# cuts this node from the tree and returns it.
		assert 0		# perhaps this should be part of the iterater.
	def get_copy(self):		# returns a deep copy of this node.
		assert 0
	def delete(self):		# deletes self from the tree and destroys self.
		assert 0
	def clipboard_cut(self):	# cuts this node and puts it on the system's clipboard
		assert 0
	def clipboard_copy(self):	# copies this node and puts it on the system's clipboard
		assert 0

	# Advanced editing
	# Uncomment only when needed and implemented.
	#def leafnode_to_sequence(self):	# transforms this leafnode to a sequence containing self.
	#	pass
	#def leafnode_to_par(self):	# transforms this leafnode to a par containing self.
	#	pass
	#def move_branch_to(self, newparent):
	#	# Move this whole tree branch (from this node down) to a new location.
	#	pass
	#def 

	# Used for the user interface
	def get_commands(self):		# returns a list of mapped commands
		assert 0
	def get_contextmenu(self):	# returns a context menu that can be used with the windowinterface.
		assert 0
	def show_propertiesDialog(self): # Pops up the attribute editor for this node.
		assert 0
	def show_content_editor(self):	# Shows a system-dependant editor for that node.
		assert 0
	def play_node(self):		# play this node only
		assert 0
	def play_from_node(self):	# play from this node onwards.
		assert 0

	# Viewing this node. Helper routines for widgets only.
	def get_thumbnail(self, coords):	# returns an icon.
		pass
	def get_color(self):		# returns a default "color" for this type of node.
		pass
	def GetTimes(self):
		return self.node.GetTimes() # this is a "callthrough".

	# Traversing the tree
	def get_children(self):		# Virtual function.
		return []


class EditableLeafMMNode(EditableMMNode):
	# An editable representation of a leaf node.
	pass


class EditableInternalMMNode(EditableMMNode):
	# An editable representation of an internal MMNode - seq, par, etc.
	#def new_par_child(self, params): # creates a new child of this node.
	#	pass
	#def new_seq_child(self, params):
	#def new_leaf_child()

	def clipboard_paste(self, index): # pastes from the clipboard to a certain position on this node.
		assert 0
	# Traversing the tree
	def get_children(self):
		return self.__node.GetChildren
	def set_child(self, newchild, index):
		assert 0


######################################################################
# Editing regions.

def create_MMChannel_editable(chan):
	# Create a editable representation of chan.
	pass

class EditableRegion:
	pass

class EditableViewport(EditableRegion):
	pass
