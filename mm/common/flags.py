__version__ = "$Id$"

# These flag bits can be set in the menu templates.
# In the menu templates, all flags that are on must be present in the
# set of flags that is returned by curflags().  In other words, the
# test that is done is `(flags & curflags()) == flags'.  This means
# that in the menu templates you should set one of LIGHT, SMIL, and
# and you can add or not add CMP_QT, CMP_G2, SMIL_QT, SMIL_G2, CMIF and DBG.

LIGHT = 0x0001
SMIL = 0x0002
CMP_QT = 0x0004
CMP_G2 = 0x0008
SMIL_QT = 0x0010
SMIL_G2 = 0x0020
CMIF = 0x0040
DBG = 0x8000

def curflags():
	import settings
	import features
	import compatibility
	flags = LIGHT			# always enabled
	if not features.lightweight:
		flags = flags | SMIL
		if settings.get('cmif'):
			flags = flags | CMIF

	if compatibility.G2 == features.compatibility:
		flags = flags | CMP_G2
		if not features.lightweight:
			flags = flags | SMIL_G2
	if compatibility.QT == features.compatibility:
		flags = flags | CMP_QT
		if not features.lightweight:
			flags = flags | SMIL_QT
	if settings.get('debug'):
		flags = flags | DBG
	return flags
