# This module only defines exceptions.
# Suggested usage:
#	from MMExc import *

TypeError = 'MMExc.TypeError'		# Invalid type in input file
SyntaxError = 'MMExc.SyntaxError'	# Invalid syntax in input file

CheckError = 'MMExc.CheckError'		# Invalid call from client
AssertError = 'MMExc.AssertError'	# Internal inconsistency

NoSuchAttrError = 'MMExc.NoSuchAttrError'	# Attribute not found
NoSuchUIDError = 'MMExc.NoSuchUIDError'		# UID not in UID map
DuplicateUIDError = 'MMExc.DuplicateUIDError'	# UID already in UID map
