__version__ = "$Id$"

# These flag bits are used in all grins code
# each bit is corresponding to a specific compatibility
# actualy there 6 flags witch corresponding to:
#
# FLAG_G2_LIGHT: g2 light version
# FLAG_QT_LIGHT: qt light version
# etc ...
#
# Actualy, these flags are used for both menu templates and attrdefs file.
#
# In the menu templates and attrdefs, all flags that are on must be present in the
# set of flags that is returned by curflags().  In other words, the
# test that is done is '(flags & curflags()) != 0'.  This means
# that in the menu templates you should set a combinaison of LIGHT_G2_LIGHT, 
# FLAG_G2_PRO, FLAG_QT_LIGHT, FLAG_QT_PRO, FLAG_CMIF, FLAG_SMIL_1_0, DBG. 
# The predefinated combinaison flags are: 
# FLAG_G2, FLAG_QT and FLAG_ALL
#
# in the attrdefs file, flags are set in the same way for specify the visible attributes in formularies,
# according to the grins version.

FLAG_G2_LIGHT = 0x0001
FLAG_G2_PRO = 0x0002
FLAG_QT_LIGHT = 0x0004
FLAG_QT_PRO = 0x0008
FLAG_CMIF = 0x0010
FLAG_SMIL_1_0 = 0x0020
FLAG_G2 = FLAG_G2_LIGHT | FLAG_G2_PRO
FLAG_QT = FLAG_QT_LIGHT | FLAG_QT_PRO
FLAG_ALL = FLAG_G2 | FLAG_QT | FLAG_CMIF | FLAG_SMIL_1_0

#LIGHT = 0x0001
#SMIL = 0x0002
#CMP_QT = 0x0004
#CMP_G2 = 0x0008
#SMIL_QT = 0x0010
#SMIL_G2 = 0x0020
#CMIF = 0x0040
DBG = 0x8000

def curflags():
	import settings
	import features
	import compatibility
	flags = 0
	if features.compatibility == compatibility.G2:
		if features.lightweight:
			flags = flags | FLAG_G2_LIGHT
		else:
			flags = flags | FLAG_G2_PRO 
			if settings.get('cmif'):
				flags = flags | FLAG_CMIF
	elif features.compatibility == compatibility.QT:
		flags = flags | FLAG_QT_PRO 
		if settings.get('cmif'):
			flags = flags | FLAG_CMIF

	if settings.get('debug'):
		flags = flags | DBG
	return flags

#def curflags():
#	import settings
#	import features
#	import compatibility
#	flags = LIGHT			# always enabled
#	if not features.lightweight:
#		flags = flags | SMIL
#		if settings.get('cmif'):
#			flags = flags | CMIF

#	if compatibility.G2 == features.compatibility:
#		flags = flags | CMP_G2
#		if not features.lightweight:
#			flags = flags | SMIL_G2
#	if compatibility.QT == features.compatibility:
#		flags = flags | CMP_QT
#		if not features.lightweight:
#			flags = flags | SMIL_QT
#	if settings.get('debug'):
#		flags = flags | DBG
#	return flags
