# this module allows to manage the owner any root node
# different possible values:
# OWNER_NONE: none is owner
# OWNER_DOCUMENT: the node is part of the document
# OWNER_UNDOSTACK: the node is in the 'standard' part of the undo stack
# OWNER_CLIPBOARD: the node is either in the clipboard or in the undo stack (clipboard part)

OWNER_NONE = 0
OWNER_DOCUMENT = 1
OWNER_UNDOSTACK = 2
OWNER_CLIPBOARD = 4

class Owner:
	def __init__(self):
		self.__owner = OWNER_NONE

	# return the owner of a root node
	def getOwner(self):
		return self.__owner

	# add the owner flag without affecting the others
	def addOwner(self, owner):
		self.__owner = self.__owner | owner

	# remove an owner flag without affecting the others
	def removeOwner(self, owner):
		self.__owner = self.__owner &~ owner

	