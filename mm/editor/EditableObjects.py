This is not usable yet. Please don''t.

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

def create_MMNode_editable(self, mm):
	# mm : MMNode
	# This returns an editable of that MMNode.
	if __nodes.has_key(mm):
		return __nodes[mm]
	else:
		# create a new node depending on it's type.
		print "TODO: create a MMNode editable."


class EditableMMNode:
	# TODO
	def setup()			# like a constructer, but without parameters.
	def get_iter();
	def set_region();
	def get_region();		# Returns a EditableRegion thing.
	def set_
	def get_

	# Editing this node.. some are callbacks for the commands returned by get_commands()
	def get_cut()			# cuts this node from the tree and returns it.
					# perhaps this should be part of the iterater.
	def get_copy()			# returns a deep copy of this node.
	def delete()			# deletes self from the tree and destroys self.
	def clipboard_cut()		# cuts this node and puts it on the system's clipboard
	def clipboard_copy()		# copies this node and puts it on the system's clipboard
	def set_child(self, newchild, index):
		pass

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
	def get_commands()		# returns a list of mapped commands
	def get_contextmenu()		# returns a context menu that can be used with the windowinterface.
	def show_propertiesDialog()	# Pops up the attribute editor for this node.
	def show_content_editor()	# Shows a system-dependant editor for that node.
	def show_player()		# Pops up the player with this node.

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


class EditableLeafMMNode(EditableNode):
	# TODO. Maybe this class will not be needed.
	pass


class EditableInternalMMNode(EditableNode):
	# TODO. Maybe this class will not be needed.
	def new_par_child(unknown parameters): # creates a new child of this node.
		pass
	def new_seq_child(?)
	def new_leaf_child(?)
	def clipboard_paste(self, index): # pastes from the clipboard to a certain position on this node.
		pass

	# Traversing the tree
	def get_children(self):
		return self.__node.children


#class EditableMMNodeIter:
#	# Used to iterate through the EditableMMNode tree.
#	def get_node()
#	def next()
#	def reset_to_root()
	

######################################################################
# Editing regions.

create_MMChannel_editable(chan):
	# Create a editable representation of chan.
	pass

class EditableRegion:
	pass

class EditableViewport(EditableRegion):
	pass
