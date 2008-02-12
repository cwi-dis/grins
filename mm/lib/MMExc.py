__version__ = "$Id$"

# This module only defines exceptions.
# Suggested usage:
#     from MMExc import *

class MTypeError(Exception):            # Invalid type in input file
    pass
class MSyntaxError(Exception):          # Invalid syntax in input file
    pass
class MParsingError(Exception):         # The parsing has generated an error
    pass

class CheckError(Exception):            # Invalid call from client
    pass
class AssertError(Exception):           # Internal inconsistency
    pass

class NoSuchAttrError(Exception):       # Attribute not found
    pass
class NoSuchUIDError(Exception):        # UID not in UID map
    pass
class DuplicateUIDError(Exception):     # UID already in UID map
    pass

class ExitException(Exception):         # Exit application,
    pass                                # Should be caught at outer level.
                                        # Argument is proposed exit status.

class UserCancel(Exception):            # called by parser if user after an user abort
    pass
