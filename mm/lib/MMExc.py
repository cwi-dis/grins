__version__ = "$Id$"

# This module only defines exceptions.
# Suggested usage:
#       from MMExc import *

MTypeError = 'MMExc.TypeError'          # Invalid type in input file
MSyntaxError = 'MMExc.SyntaxError'      # Invalid syntax in input file
MParsingError = 'MMExc.ParsingError' # The parsing has generated an error

CheckError = 'MMExc.CheckError'         # Invalid call from client
AssertError = 'MMExc.AssertError'       # Internal inconsistency

NoSuchAttrError = 'MMExc.NoSuchAttrError'       # Attribute not found
NoSuchUIDError = 'MMExc.NoSuchUIDError'         # UID not in UID map
DuplicateUIDError = 'MMExc.DuplicateUIDError'   # UID already in UID map

ExitException = 'MMExc.ExitException'   # Exit application,
                                        # Should be caught at outer level.
                                        # Argument is proposed exit status.

UserCancel = 'MMExc.UserCancel'         # called by parser if user after an user abort
