__version__ = "$Id$"

# These flag bits can be set in the menu templates.
# In the menu templates, all flags that are on must be present in the
# set of flags that is returned by curflags().  In other words, the
# test that is done is `(flags & curflags()) == flags'.  This means
# that in the menu templates you should set one of LIGHT, SMIL, and
# CMIF, and you can add or not add DBG.

LIGHT = 0x0001
SMIL = 0x0002
CMIF = 0x0004
DBG = 0x8000

def curflags():
	import settings
	import features
	flags = LIGHT			# always enabled
	if not features.lightweight:
		flags = flags | SMIL
		if settings.get('cmif'):
			flags = flags | CMIF
	if settings.get('debug'):
		flags = flags | DBG
	return flags
